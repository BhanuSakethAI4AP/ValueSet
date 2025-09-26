"""
Router layer for Value Set API endpoints.
Defines FastAPI routes and calls service functions.
File: /routers/value_set_router.py
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from database import get_db
from services.value_set_service import ValueSetService
from repositories.value_set_repository import ValueSetRepository
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


def get_value_set_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> ValueSetService:
    """
    Dependency to get value set service instance.

    Args:
        db: Database connection

    Returns:
        ValueSetService instance
    """
    repository = ValueSetRepository(db)
    return ValueSetService(repository)


# 1. Create Value Set
@router.post("/", response_model=ValueSetResponseSchema)
async def create_value_set(
    create_data: ValueSetCreateSchema = Body(...),
    service: ValueSetService = Depends(get_value_set_service)
) -> ValueSetResponseSchema:
    """
    Create a new value set.

    Args:
        create_data: Value set creation data
        service: Value set service

    Returns:
        Created value set

    Raises:
        HTTPException: If creation fails
    """
    try:
        return await service.create_value_set(create_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# 2. Get Value Set by Key
@router.get("/{key}", response_model=ValueSetResponseSchema)
async def get_value_set_by_key(
    key: str = Path(..., description="Value set key"),
    service: ValueSetService = Depends(get_value_set_service)
) -> ValueSetResponseSchema:
    """
    Get a value set by its unique key.

    Args:
        key: Value set key
        service: Value set service

    Returns:
        Value set data

    Raises:
        HTTPException: If value set not found
    """
    result = await service.get_value_set_by_key(key)
    if not result:
        raise HTTPException(status_code=404, detail=f"Value set with key '{key}' not found")
    return result


# 3. Update Value Set
@router.put("/{key}", response_model=ValueSetResponseSchema)
async def update_value_set(
    key: str = Path(..., description="Value set key"),
    update_data: ValueSetUpdateSchema = Body(...),
    service: ValueSetService = Depends(get_value_set_service)
) -> ValueSetResponseSchema:
    """
    Update an existing value set.

    Args:
        key: Value set key
        update_data: Update data
        service: Value set service

    Returns:
        Updated value set

    Raises:
        HTTPException: If update fails
    """
    try:
        result = await service.update_value_set(key, update_data)
        if not result:
            raise HTTPException(status_code=404, detail=f"Value set with key '{key}' not found")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# 4. Restore Deleted Value Set - REMOVED
# This functionality has been disabled


# 5. List Value Sets
@router.get("/", response_model=PaginatedValueSetResponse)
async def list_value_sets(
    status: Optional[StatusEnum] = Query(None, description="Filter by status"),
    module: Optional[str] = Query(None, description="Filter by module"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    service: ValueSetService = Depends(get_value_set_service)
) -> PaginatedValueSetResponse:
    """
    List value sets with filtering and pagination.

    Args:
        status: Optional status filter
        module: Optional module filter
        skip: Number of records to skip
        limit: Maximum records to return
        service: Value set service

    Returns:
        Paginated value sets
    """
    query_params = ListValueSetsQuerySchema(
        status=status,
        module=module,
        skip=skip,
        limit=limit
    )
    return await service.list_value_sets(query_params)


# 6. Search Value Set Items
@router.post("/search/items", response_model=List[SearchItemsResponseSchema])
async def search_value_set_items(
    search_params: SearchItemsQuerySchema = Body(...),
    service: ValueSetService = Depends(get_value_set_service)
) -> List[SearchItemsResponseSchema]:
    """
    Search for items within value sets.

    Args:
        search_params: Search parameters
        service: Value set service

    Returns:
        List of search results
    """
    return await service.search_value_set_items(search_params)


# 7. Search Value Sets by Label
@router.get("/search/by-label", response_model=List[ValueSetResponseSchema])
async def search_value_sets_by_label(
    label_text: str = Query(..., description="Text to search in labels"),
    language_code: str = Query("en", description="Language code"),
    status: Optional[str] = Query(None, description="Optional status filter"),
    service: ValueSetService = Depends(get_value_set_service)
) -> List[ValueSetResponseSchema]:
    """
    Search value sets by label text.

    Args:
        label_text: Text to search
        language_code: Language code
        status: Optional status filter
        service: Value set service

    Returns:
        List of matching value sets
    """
    return await service.search_value_sets_by_label(label_text, language_code, status)


# 8. Add Item to Value Set
@router.post("/{key}/items", response_model=ValueSetResponseSchema)
async def add_item_to_value_set(
    key: str = Path(..., description="Value set key"),
    request: AddItemRequestSchema = Body(...),
    service: ValueSetService = Depends(get_value_set_service)
) -> ValueSetResponseSchema:
    """
    Add a new item to an existing value set.

    Args:
        key: Value set key
        request: Add item request
        service: Value set service

    Returns:
        Updated value set

    Raises:
        HTTPException: If addition fails
    """
    try:
        result = await service.add_item_to_value_set(key, request)
        if not result:
            raise HTTPException(status_code=404, detail=f"Value set with key '{key}' not found")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# 9. Replace Value in Item (must come before parameterized route)
@router.put("/{key}/items/replace", response_model=ValueSetResponseSchema)
async def replace_value_in_item(
    key: str = Path(..., description="Value set key"),
    replace_request: ReplaceItemCodeSchema = Body(...),
    service: ValueSetService = Depends(get_value_set_service)
) -> ValueSetResponseSchema:
    """
    Replace an item's code and optionally its labels.

    Args:
        key: Value set key
        replace_request: Replace request
        service: Value set service

    Returns:
        Updated value set

    Raises:
        HTTPException: If replacement fails
    """
    try:
        result = await service.replace_value_in_item(key, replace_request)
        if not result:
            raise HTTPException(status_code=404, detail=f"Value set with key '{key}' not found")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# 10. Update Item in Value Set
@router.put("/{key}/items/{item_code}", response_model=ValueSetResponseSchema)
async def update_item_in_value_set(
    key: str = Path(..., description="Value set key"),
    item_code: str = Path(..., description="Item code"),
    request: UpdateItemRequestSchema = Body(...),
    service: ValueSetService = Depends(get_value_set_service)
) -> ValueSetResponseSchema:
    """
    Update an existing item in a value set.

    Args:
        key: Value set key
        item_code: Item code to update
        request: Update request
        service: Value set service

    Returns:
        Updated value set

    Raises:
        HTTPException: If update fails
    """
    # Ensure item code in path matches request
    request.itemCode = item_code

    try:
        result = await service.update_item_in_value_set(key, request)
        if not result:
            raise HTTPException(status_code=404, detail=f"Value set with key '{key}' not found")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# 10. Delete Item from Value Set - REMOVED
# Delete functionality has been disabled for this endpoint


# 11. Bulk Add Items
@router.post("/{key}/items/bulk-add", response_model=BulkOperationResponseSchema)
async def bulk_add_items(
    key: str = Path(..., description="Value set key"),
    items: List[ItemCreateSchema] = Body(..., description="Items to add"),
    updated_by: str = Body(..., embed=True, description="User performing operation"),
    service: ValueSetService = Depends(get_value_set_service)
) -> BulkOperationResponseSchema:
    """
    Bulk add items to a value set.

    Args:
        key: Value set key
        items: List of items to add
        updated_by: User ID
        service: Value set service

    Returns:
        Bulk operation response
    """
    return await service.bulk_add_items(key, items, updated_by)


# 12. Bulk Update Items
@router.put("/items/bulk-update", response_model=BulkOperationResponseSchema)
async def bulk_update_items(
    updates: BulkItemUpdateSchema = Body(...),
    service: ValueSetService = Depends(get_value_set_service)
) -> BulkOperationResponseSchema:
    """
    Bulk update items across value sets.

    Args:
        updates: Bulk update data
        service: Value set service

    Returns:
        Bulk operation response
    """
    return await service.bulk_update_items(updates)


# 13. Bulk Delete Items - REMOVED
# Bulk delete functionality has been disabled for this endpoint




# 15. Bulk Import Value Sets
@router.post("/bulk/import", response_model=BulkOperationResponseSchema)
async def bulk_import_value_sets(
    import_data: BulkValueSetCreateSchema = Body(...),
    service: ValueSetService = Depends(get_value_set_service)
) -> BulkOperationResponseSchema:
    """
    Bulk import multiple value sets.

    Args:
        import_data: Bulk import data
        service: Value set service

    Returns:
        Bulk operation response
    """
    return await service.bulk_import_value_sets(import_data)


# 16. Bulk Update Value Sets
@router.put("/bulk/update", response_model=BulkOperationResponseSchema)
async def bulk_update_value_sets(
    update_data: BulkValueSetUpdateSchema = Body(...),
    service: ValueSetService = Depends(get_value_set_service)
) -> BulkOperationResponseSchema:
    """
    Bulk update multiple value sets.

    Args:
        update_data: Bulk update data
        service: Value set service

    Returns:
        Bulk operation response
    """
    return await service.bulk_update_value_sets(update_data)


# 17. Validate Value Set
@router.post("/validate", response_model=ValidationResultSchema)
async def validate_value_set(
    validation_request: ValidateValueSetRequestSchema = Body(...),
    service: ValueSetService = Depends(get_value_set_service)
) -> ValidationResultSchema:
    """
    Validate a value set configuration.

    Args:
        validation_request: Validation request
        service: Value set service

    Returns:
        Validation result
    """
    return await service.validate_value_set(validation_request)


# 18. Archive Value Set
@router.post("/{key}/archive", response_model=ArchiveRestoreResponseSchema)
async def archive_value_set(
    key: str = Path(..., description="Value set key"),
    archive_request: ArchiveRestoreRequestSchema = Body(...),
    service: ValueSetService = Depends(get_value_set_service)
) -> ArchiveRestoreResponseSchema:
    """
    Archive a value set.

    Args:
        key: Value set key
        archive_request: Archive request
        service: Value set service

    Returns:
        Archive response
    """
    # Ensure key in path matches request
    archive_request.key = key
    return await service.archive_value_set(archive_request)


# 19. Restore Value Set
@router.post("/{key}/restore", response_model=ArchiveRestoreResponseSchema)
async def restore_value_set(
    key: str = Path(..., description="Value set key"),
    restore_request: ArchiveRestoreRequestSchema = Body(...),
    service: ValueSetService = Depends(get_value_set_service)
) -> ArchiveRestoreResponseSchema:
    """
    Restore an archived value set.

    Args:
        key: Value set key
        restore_request: Restore request
        service: Value set service

    Returns:
        Restore response
    """
    # Ensure key in path matches request
    restore_request.key = key
    return await service.restore_value_set(restore_request)


# 20. Get Value Set Statistics
@router.get("/statistics/summary")
async def get_value_set_statistics(
    service: ValueSetService = Depends(get_value_set_service)
):
    """
    Get statistics about value sets.

    Args:
        service: Value set service

    Returns:
        Statistics dictionary
    """
    return await service.get_value_set_statistics()


# 21. Export Value Set
@router.get("/{key}/export")
async def export_value_set(
    key: str = Path(..., description="Value set key"),
    format: str = Query("json", description="Export format (json, csv)"),
    service: ValueSetService = Depends(get_value_set_service)
):
    """
    Export a value set in specified format.

    Args:
        key: Value set key
        format: Export format
        service: Value set service

    Returns:
        Exported data

    Raises:
        HTTPException: If export fails
    """
    try:
        return await service.export_value_set(key, format)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# 22. Import Value Set
@router.post("/import", response_model=ValueSetResponseSchema)
async def import_value_set(
    import_data: dict = Body(..., description="Value set data to import"),
    format: str = Query("json", description="Import format (json, csv)"),
    created_by: str = Query("system", description="User importing the value set"),
    service: ValueSetService = Depends(get_value_set_service)
) -> ValueSetResponseSchema:
    """
    Import a value set from external source.

    Args:
        import_data: Import data
        format: Import format
        created_by: User ID
        service: Value set service

    Returns:
        Imported value set

    Raises:
        HTTPException: If import fails
    """
    try:
        return await service.import_value_set(import_data, format, created_by)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Additional endpoints for missing functions

# 23. Delete Value Set - REMOVED
# Delete functionality has been disabled. Use archive endpoint instead


# 24. Health Check
@router.get("/health")
async def health_check():
    """
    Health check endpoint for the value set module.

    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "module": "value_sets",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }