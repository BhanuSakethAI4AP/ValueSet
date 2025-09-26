"""
Updated Router layer using Value Set Library
This router now uses the reusable library functions
File: /routers/value_set_router_updated.py
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, Response
from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime

# Import the library
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from value_set_lib import ValueSetLibrary

from database import get_db
from schemas.value_set_schemas_enhanced import (
    ValueSetCreateSchema, ValueSetUpdateSchema, ValueSetResponseSchema,
    ItemCreateSchema, ItemUpdateSchema,
    AddItemRequestSchema, UpdateItemRequestSchema,
    ReplaceItemCodeSchema, BulkValueSetCreateSchema, BulkValueSetUpdateSchema,
    BulkItemUpdateSchema, ValidateValueSetRequestSchema, ValidationResultSchema,
    ArchiveRestoreRequestSchema, ArchiveRestoreResponseSchema,
    ListValueSetsQuerySchema, SearchItemsQuerySchema, SearchItemsResponseSchema,
    PaginatedValueSetResponse, PaginatedSearchResponse,
    BulkOperationResponseSchema, ErrorResponseSchema,
    StatusEnum, ValueSetListItemSchema
)

router = APIRouter(prefix="/api/v1/value-sets", tags=["Value Sets"])


def get_value_set_library(db: AsyncIOMotorDatabase = Depends(get_db)) -> ValueSetLibrary:
    """
    Dependency to get value set library instance.

    Args:
        db: Database connection

    Returns:
        ValueSetLibrary instance
    """
    return ValueSetLibrary(database=db, collection_name="value_sets")


# ==================== CREATE ENDPOINTS ====================

@router.post("/", response_model=ValueSetResponseSchema)
async def create_value_set(
    create_data: ValueSetCreateSchema = Body(...),
    lib: ValueSetLibrary = Depends(get_value_set_library)
) -> ValueSetResponseSchema:
    """Create a new value set."""
    try:
        result = await lib.create_value_set(
            key=create_data.key,
            status=create_data.status.value,
            module=create_data.module,
            items=[item.model_dump() for item in create_data.items],
            created_by=create_data.createdBy,
            description=create_data.description,
            created_at=create_data.createdAt
        )
        return ValueSetResponseSchema(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/bulk/import", response_model=BulkOperationResponseSchema)
async def bulk_import_value_sets(
    bulk_data: BulkValueSetCreateSchema = Body(...),
    lib: ValueSetLibrary = Depends(get_value_set_library)
) -> BulkOperationResponseSchema:
    """Import multiple value sets in bulk."""
    try:
        value_sets = []
        for vs in bulk_data.valueSets:
            value_sets.append({
                'key': vs.key,
                'status': vs.status.value,
                'module': vs.module,
                'description': vs.description,
                'items': [item.model_dump() for item in vs.items],
                'createdBy': vs.createdBy,
                'createdAt': vs.createdAt
            })

        result = await lib.bulk_create_value_sets(
            value_sets=value_sets,
            skip_existing=bulk_data.skipExisting
        )

        return BulkOperationResponseSchema(
            success=len(result['failed']) == 0,
            processed=result['summary']['total'],
            successful=result['summary']['created'],
            failed=result['summary']['failed'],
            details=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== READ ENDPOINTS ====================

@router.get("/{key}", response_model=ValueSetResponseSchema)
async def get_value_set_by_key(
    key: str = Path(..., description="Value set key"),
    lib: ValueSetLibrary = Depends(get_value_set_library)
) -> ValueSetResponseSchema:
    """Get a value set by its unique key."""
    result = await lib.get_value_set_by_key(key)
    if not result:
        raise HTTPException(status_code=404, detail=f"Value set with key '{key}' not found")
    return ValueSetResponseSchema(**result)


@router.get("/", response_model=PaginatedValueSetResponse)
async def list_value_sets(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    status: Optional[str] = Query(None, description="Filter by status"),
    module: Optional[str] = Query(None, description="Filter by module"),
    search: Optional[str] = Query(None, description="Search in key and description"),
    sort_by: str = Query("key", description="Field to sort by"),
    sort_order: str = Query("asc", description="Sort order (asc/desc)"),
    lib: ValueSetLibrary = Depends(get_value_set_library)
) -> PaginatedValueSetResponse:
    """List value sets with pagination and filtering."""
    try:
        documents, total_count = await lib.list_value_sets(
            skip=skip,
            limit=limit,
            status=status,
            module=module,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order
        )

        # Convert to response models
        value_sets = [ValueSetListItemSchema(**doc) for doc in documents]

        return PaginatedValueSetResponse(
            data=value_sets,
            total=total_count,
            skip=skip,
            limit=limit,
            hasMore=(skip + limit) < total_count
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{key}/export")
async def export_value_set(
    key: str = Path(..., description="Value set key"),
    format: str = Query("json", description="Export format (json/csv)"),
    lib: ValueSetLibrary = Depends(get_value_set_library)
):
    """Export a value set in specified format."""
    try:
        result = await lib.export_value_set(key, format)
        if not result:
            raise HTTPException(status_code=404, detail=f"Value set with key '{key}' not found")

        if format == "csv":
            return Response(
                content=result,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={key}.csv"}
            )
        else:
            return Response(
                content=result,
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename={key}.json"}
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== UPDATE ENDPOINTS ====================

@router.put("/{key}", response_model=ValueSetResponseSchema)
async def update_value_set(
    key: str = Path(..., description="Value set key"),
    update_data: ValueSetUpdateSchema = Body(...),
    lib: ValueSetLibrary = Depends(get_value_set_library)
) -> ValueSetResponseSchema:
    """Update an existing value set."""
    try:
        updates = {}
        if update_data.status:
            updates['status'] = update_data.status.value
        if update_data.description is not None:
            updates['description'] = update_data.description
        if update_data.module:
            updates['module'] = update_data.module
        if update_data.items:
            updates['items'] = [item.model_dump() for item in update_data.items]

        result = await lib.update_value_set(
            key=key,
            updates=updates,
            updated_by=update_data.updatedBy,
            updated_at=update_data.updatedAt
        )

        if not result:
            raise HTTPException(status_code=404, detail=f"Value set with key '{key}' not found")

        return ValueSetResponseSchema(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk/update", response_model=BulkOperationResponseSchema)
async def bulk_update_value_sets(
    bulk_data: BulkValueSetUpdateSchema = Body(...),
    lib: ValueSetLibrary = Depends(get_value_set_library)
) -> BulkOperationResponseSchema:
    """Update multiple value sets in bulk."""
    try:
        updates = []
        for update in bulk_data.updates:
            update_dict = {'key': update.key, 'updates': {}}
            if update.status:
                update_dict['updates']['status'] = update.status.value
            if update.description is not None:
                update_dict['updates']['description'] = update.description
            if update.module:
                update_dict['updates']['module'] = update.module
            updates.append(update_dict)

        result = await lib.bulk_update_value_sets(
            updates=updates,
            updated_by=bulk_data.updatedBy
        )

        return BulkOperationResponseSchema(
            success=len(result['failed']) == 0,
            processed=result['summary']['total'],
            successful=result['summary']['updated'],
            failed=result['summary']['failed'],
            details=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ITEM MANAGEMENT ENDPOINTS ====================

@router.post("/{key}/items", response_model=ValueSetResponseSchema)
async def add_item_to_value_set(
    key: str = Path(..., description="Value set key"),
    add_request: AddItemRequestSchema = Body(...),
    lib: ValueSetLibrary = Depends(get_value_set_library)
) -> ValueSetResponseSchema:
    """Add a single item to a value set."""
    try:
        result = await lib.add_item_to_value_set(
            key=key,
            item=add_request.item.model_dump(),
            updated_by=add_request.updatedBy
        )
        if not result:
            raise HTTPException(status_code=404, detail=f"Value set with key '{key}' not found")
        return ValueSetResponseSchema(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{key}/items/bulk-add", response_model=ValueSetResponseSchema)
async def bulk_add_items(
    key: str = Path(..., description="Value set key"),
    items: List[ItemCreateSchema] = Body(...),
    updated_by: str = Body(...),
    lib: ValueSetLibrary = Depends(get_value_set_library)
) -> ValueSetResponseSchema:
    """Add multiple items to a value set."""
    try:
        items_data = [item.model_dump() for item in items]
        result = await lib.bulk_add_items(
            key=key,
            items=items_data,
            updated_by=updated_by
        )
        if not result:
            raise HTTPException(status_code=404, detail=f"Value set with key '{key}' not found")
        return ValueSetResponseSchema(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{key}/items/{item_code}", response_model=ValueSetResponseSchema)
async def update_item_in_value_set(
    key: str = Path(..., description="Value set key"),
    item_code: str = Path(..., description="Item code"),
    update_request: UpdateItemRequestSchema = Body(...),
    lib: ValueSetLibrary = Depends(get_value_set_library)
) -> ValueSetResponseSchema:
    """Update a specific item in a value set."""
    try:
        updates = {}
        if update_request.updates:
            if update_request.updates.code:
                updates['code'] = update_request.updates.code
            if update_request.updates.labels:
                updates['labels'] = update_request.updates.labels.model_dump(exclude_none=True)

        result = await lib.update_item_in_value_set(
            key=key,
            item_code=item_code,
            updates=updates,
            updated_by=update_request.updatedBy
        )
        if not result:
            raise HTTPException(status_code=404, detail=f"Value set or item not found")
        return ValueSetResponseSchema(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{key}/items/{item_code}", response_model=ValueSetResponseSchema)
async def remove_item_from_value_set(
    key: str = Path(..., description="Value set key"),
    item_code: str = Path(..., description="Item code"),
    updated_by: str = Query(..., description="User removing the item"),
    lib: ValueSetLibrary = Depends(get_value_set_library)
) -> ValueSetResponseSchema:
    """Remove an item from a value set."""
    try:
        result = await lib.remove_item_from_value_set(
            key=key,
            item_code=item_code,
            updated_by=updated_by
        )
        if not result:
            raise HTTPException(status_code=404, detail=f"Value set or item not found")
        return ValueSetResponseSchema(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{key}/items/replace", response_model=ValueSetResponseSchema)
async def replace_item_code(
    key: str = Path(..., description="Value set key"),
    replace_data: ReplaceItemCodeSchema = Body(...),
    lib: ValueSetLibrary = Depends(get_value_set_library)
) -> ValueSetResponseSchema:
    """Replace an item's code and optionally its labels."""
    try:
        new_labels = None
        if replace_data.newLabels:
            new_labels = replace_data.newLabels.model_dump()

        result = await lib.replace_item_code(
            key=key,
            old_code=replace_data.oldCode,
            new_code=replace_data.newCode,
            new_labels=new_labels,
            updated_by=replace_data.updatedBy
        )
        if not result:
            raise HTTPException(status_code=404, detail=f"Value set or item not found")
        return ValueSetResponseSchema(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ARCHIVE/RESTORE ENDPOINTS ====================

@router.post("/{key}/archive", response_model=ArchiveRestoreResponseSchema)
async def archive_value_set(
    key: str = Path(..., description="Value set key"),
    archive_request: ArchiveRestoreRequestSchema = Body(...),
    lib: ValueSetLibrary = Depends(get_value_set_library)
) -> ArchiveRestoreResponseSchema:
    """Archive a value set."""
    try:
        result = await lib.archive_value_set(
            key=key,
            reason=archive_request.reason,
            archived_by=archive_request.updatedBy
        )
        if not result:
            raise HTTPException(status_code=404, detail=f"Value set with key '{key}' not found")

        return ArchiveRestoreResponseSchema(
            success=True,
            key=key,
            status="archived",
            message=f"Value set '{key}' archived successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{key}/restore", response_model=ArchiveRestoreResponseSchema)
async def restore_value_set(
    key: str = Path(..., description="Value set key"),
    restore_request: ArchiveRestoreRequestSchema = Body(...),
    lib: ValueSetLibrary = Depends(get_value_set_library)
) -> ArchiveRestoreResponseSchema:
    """Restore an archived value set."""
    try:
        result = await lib.restore_value_set(
            key=key,
            reason=restore_request.reason,
            restored_by=restore_request.updatedBy
        )
        if not result:
            raise HTTPException(status_code=404, detail=f"Value set with key '{key}' not found")

        return ArchiveRestoreResponseSchema(
            success=True,
            key=key,
            status="active",
            message=f"Value set '{key}' restored successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk/archive")
async def bulk_archive(
    keys: List[str] = Body(...),
    reason: str = Body(...),
    archived_by: str = Body(...),
    lib: ValueSetLibrary = Depends(get_value_set_library)
):
    """Archive multiple value sets."""
    try:
        result = await lib.bulk_archive(
            keys=keys,
            reason=reason,
            archived_by=archived_by
        )
        return {
            "success": True,
            "archived": result['modified'],
            "details": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== SEARCH ENDPOINTS ====================

@router.post("/search/items", response_model=SearchItemsResponseSchema)
async def search_items(
    search_query: SearchItemsQuerySchema = Body(...),
    lib: ValueSetLibrary = Depends(get_value_set_library)
) -> SearchItemsResponseSchema:
    """Search for items across all value sets."""
    try:
        results, total_count = await lib.search_items(
            query=search_query.query,
            language_code=search_query.languageCode,
            skip=search_query.skip,
            limit=search_query.limit
        )

        return SearchItemsResponseSchema(
            results=results,
            total=total_count,
            skip=search_query.skip,
            limit=search_query.limit,
            hasMore=(search_query.skip + search_query.limit) < total_count
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/by-label", response_model=PaginatedValueSetResponse)
async def search_by_label(
    label_text: str = Query(..., description="Label text to search"),
    language_code: str = Query("en", description="Language code"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    lib: ValueSetLibrary = Depends(get_value_set_library)
) -> PaginatedValueSetResponse:
    """Search value sets by label text."""
    try:
        documents, total_count = await lib.search_by_label(
            label_text=label_text,
            language_code=language_code,
            skip=skip,
            limit=limit
        )

        value_sets = [ValueSetListItemSchema(**doc) for doc in documents]

        return PaginatedValueSetResponse(
            data=value_sets,
            total=total_count,
            skip=skip,
            limit=limit,
            hasMore=(skip + limit) < total_count
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== VALIDATION ENDPOINTS ====================

@router.post("/validate", response_model=ValidationResultSchema)
async def validate_value_set(
    value_set_data: ValidateValueSetRequestSchema = Body(...),
    lib: ValueSetLibrary = Depends(get_value_set_library)
) -> ValidationResultSchema:
    """Validate a value set structure."""
    try:
        # Convert to dict for validation
        data_dict = {
            'key': value_set_data.key,
            'status': value_set_data.status.value if value_set_data.status else 'active',
            'module': value_set_data.module,
            'description': value_set_data.description,
            'items': [item.model_dump() for item in value_set_data.items] if value_set_data.items else []
        }

        result = await lib.validate_value_set(data_dict)

        return ValidationResultSchema(
            valid=result['valid'],
            errors=result.get('errors', []),
            warnings=result.get('warnings', [])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== STATISTICS ENDPOINTS ====================

@router.get("/statistics/summary")
async def get_statistics(
    lib: ValueSetLibrary = Depends(get_value_set_library)
):
    """Get value set statistics."""
    try:
        stats = await lib.get_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics/module/{module}")
async def get_module_statistics(
    module: str = Path(..., description="Module name"),
    lib: ValueSetLibrary = Depends(get_value_set_library)
):
    """Get statistics for a specific module."""
    try:
        stats = await lib.get_module_statistics(module)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== DELETE ENDPOINTS (if needed) ====================

@router.delete("/{key}")
async def delete_value_set(
    key: str = Path(..., description="Value set key"),
    lib: ValueSetLibrary = Depends(get_value_set_library)
):
    """Permanently delete a value set."""
    try:
        deleted = await lib.delete_value_set(key)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Value set with key '{key}' not found")
        return {"success": True, "message": f"Value set '{key}' deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))