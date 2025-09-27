"""
Router layer for Value Set API endpoints.
Defines FastAPI routes and calls service functions.
File: /routers/value_set_router.py
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime

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
    Creates and returns a ValueSetService instance with proper dependency injection.

    LLM Instructions:
    • Call this function when you need to inject the ValueSetService into FastAPI route handlers
    • This is a FastAPI dependency function - use it with Depends() in route parameters
    • Do not call this function directly in business logic - it's for FastAPI's dependency injection system

    Business Logic:
    • Creates a new ValueSetRepository instance using the provided database connection
    • Instantiates ValueSetService with the repository for dependency injection
    • Follows FastAPI's dependency injection pattern for clean architecture

    Args:
        db (AsyncIOMotorDatabase): MongoDB database connection instance injected by FastAPI.
            This connection is managed by the get_db() dependency function.

    Returns:
        ValueSetService: Fully configured service instance with repository dependency injected.
            Ready to handle all value set business operations.

    Example:
    ```python
    @router.get("/value-sets")
    async def get_value_sets(service: ValueSetService = Depends(get_value_set_service)):
        return await service.list_value_sets(query_params)
    ```
    """
    repository = ValueSetRepository(db)
    return ValueSetService(repository)


# 0. Health Check (must be before /{key} route)
@router.get("/health")
async def health_check():
    """
    Provides health status information for the value set API module.

    LLM Instructions:
    • Use this endpoint to verify the value set API is operational
    • Call this for monitoring and alerting systems
    • Use this in health check dashboards and status pages
    • Call this during deployment verification and system testing

    Business Logic:
    • Returns basic operational status without database dependency
    • Provides module identification and version information
    • Includes current timestamp for response freshness verification
    • Does not perform deep health checks or database connectivity tests
    • Always returns success unless the service is completely down
    • Suitable for load balancer health checks and basic monitoring

    Args:
        None: This endpoint requires no parameters.

    Returns:
        dict: Health status information containing:
            - status (str): Always "healthy" if service is responsive
            - module (str): Module identifier "value_sets"
            - version (str): API version "1.0.0"
            - timestamp (str): Current UTC timestamp in ISO format

    Example:
    ```python
    health = await health_check()
    # Returns: {
    #     "status": "healthy",
    #     "module": "value_sets",
    #     "version": "1.0.0",
    #     "timestamp": "2024-01-15T10:30:00.000Z"
    # }
    ```
    """
    return {
        "status": "healthy",
        "module": "value_sets",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


# 1. Create Value Set
@router.post("/", response_model=ValueSetResponseSchema)
async def create_value_set(
    create_data: ValueSetCreateSchema = Body(...),
    service: ValueSetService = Depends(get_value_set_service)
) -> ValueSetResponseSchema:
    """
    Creates a new value set with all required metadata and validation.

    LLM Instructions:
    • Use this endpoint when you need to create a brand new value set from scratch
    • Call this when the user wants to add a new value set to the system
    • This is for initial creation only - use update endpoints for modifications
    • Ensure all required fields are provided in the request body

    Business Logic:
    • Validates all required fields (key, name, module, etc.) are present
    • Checks for duplicate value set keys before creation
    • Sets initial status to ACTIVE unless specified otherwise
    • Automatically generates creation timestamp and audit fields
    • Validates item codes are unique within the value set if items are provided
    • Returns the complete created value set with generated metadata

    Args:
        create_data (ValueSetCreateSchema): Complete value set creation data including:
            - key (str): Unique identifier for the value set (required)
            - name (str): Human-readable name (required)
            - module (str): Module/system this value set belongs to (required)
            - description (str): Detailed description (optional)
            - items (List[ItemCreateSchema]): Initial items to include (optional)
            - metadata (dict): Additional metadata fields (optional)
            - created_by (str): User ID of creator (required)
        service (ValueSetService): Injected service for business logic operations.

    Returns:
        ValueSetResponseSchema: Complete created value set with all fields populated:
            - All input fields plus generated _id, created_at, updated_at
            - Status set to ACTIVE
            - Items with validation results

    Example:
    ```python
    create_data = ValueSetCreateSchema(
        key="medical_specialties",
        name="Medical Specialties",
        module="healthcare",
        description="List of medical specialties",
        items=[
            ItemCreateSchema(code="CARDIO", labels={"en": "Cardiology"})
        ],
        created_by="user123"
    )
    result = await create_value_set(create_data, service)
    ```
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
    Retrieves a complete value set by its unique key identifier.

    LLM Instructions:
    • Use this endpoint when you need to fetch a specific value set by its key
    • Call this when displaying value set details to users
    • Use this to verify a value set exists before performing operations on it
    • This returns the complete value set including all items and metadata

    Business Logic:
    • Performs exact key match lookup in the database
    • Returns value sets regardless of status (ACTIVE, ARCHIVED, etc.)
    • Includes all items, labels, and metadata in the response
    • Does not perform any filtering or transformation of data
    • Raises 404 error if no value set found with the specified key

    Args:
        key (str): Unique identifier of the value set to retrieve.
            Must be an exact match (case-sensitive).
            Examples: "medical_specialties", "country_codes", "diagnosis_codes"
        service (ValueSetService): Injected service for database operations.

    Returns:
        ValueSetResponseSchema: Complete value set data including:
            - All metadata (key, name, description, module, status)
            - Full items list with codes and labels
            - Audit fields (created_at, updated_at, created_by, updated_by)
            - Any custom metadata fields

    Example:
    ```python
    # Retrieve a medical specialties value set
    value_set = await get_value_set_by_key("medical_specialties", service)
    print(f"Found value set: {value_set.name} with {len(value_set.items)} items")
    ```
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
    Updates metadata and configuration of an existing value set.

    LLM Instructions:
    • Use this endpoint to modify value set metadata (name, description, status, etc.)
    • Call this when users want to change value set properties but not individual items
    • For item-level changes, use the specific item endpoints instead
    • This does not modify the items collection - only value set-level fields

    Business Logic:
    • Validates the value set exists before attempting updates
    • Only updates fields that are provided in the request (partial updates supported)
    • Cannot change the key field - it's immutable after creation
    • Automatically updates the updated_at timestamp and updated_by field
    • Validates status transitions (e.g., can't update ARCHIVED sets without restoring)
    • Preserves existing items and their relationships
    • Returns the complete updated value set

    Args:
        key (str): Unique identifier of the value set to update.
            Must match an existing value set exactly.
        update_data (ValueSetUpdateSchema): Partial update data containing:
            - name (str, optional): New display name
            - description (str, optional): New description
            - status (StatusEnum, optional): New status (ACTIVE, INACTIVE, ARCHIVED)
            - metadata (dict, optional): Additional metadata to merge
            - updated_by (str, required): User ID performing the update
        service (ValueSetService): Injected service for business operations.

    Returns:
        ValueSetResponseSchema: Complete updated value set with:
            - All original fields plus any updated values
            - New updated_at timestamp
            - Updated updated_by field
            - Unchanged items collection

    Example:
    ```python
    update_data = ValueSetUpdateSchema(
        name="Updated Medical Specialties",
        description="Comprehensive list of medical specialties - updated",
        status=StatusEnum.ACTIVE,
        updated_by="admin_user"
    )
    result = await update_value_set("medical_specialties", update_data, service)
    ```
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
    Retrieves a paginated list of value sets with optional filtering capabilities.

    LLM Instructions:
    • Use this endpoint to display lists of value sets to users
    • Call this when implementing value set browsing or selection interfaces
    • Use filtering parameters to narrow down results by status or module
    • Implement pagination for large datasets using skip and limit parameters

    Business Logic:
    • Returns value sets in descending order by creation date (newest first)
    • Applies status filter if provided (ACTIVE, INACTIVE, ARCHIVED)
    • Applies module filter for exact string match if provided
    • Supports pagination with configurable skip/limit (max 1000 per page)
    • Returns summary information only (excludes full items list for performance)
    • Includes total count for pagination controls
    • Does not include soft-deleted records

    Args:
        status (Optional[StatusEnum]): Filter by value set status.
            Valid values: ACTIVE, INACTIVE, ARCHIVED.
            If None, returns value sets of all statuses.
        module (Optional[str]): Filter by exact module name match.
            Case-sensitive string filter. If None, returns from all modules.
        skip (int): Number of records to skip for pagination.
            Must be >= 0. Default is 0 (start from beginning).
        limit (int): Maximum number of records to return per page.
            Must be between 1 and 1000. Default is 100.
        service (ValueSetService): Injected service for database operations.

    Returns:
        PaginatedValueSetResponse: Paginated response containing:
            - items (List[ValueSetListItemSchema]): Value set summaries (without full items)
            - total (int): Total count matching filters
            - skip (int): Current skip offset
            - limit (int): Current page size
            - has_more (bool): Whether more records exist

    Example:
    ```python
    # Get first 50 active healthcare value sets
    response = await list_value_sets(
        status=StatusEnum.ACTIVE,
        module="healthcare",
        skip=0,
        limit=50,
        service
    )
    print(f"Found {response.total} value sets, showing {len(response.items)}")
    ```
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
    Searches for specific items across one or more value sets using various criteria.

    LLM Instructions:
    • Use this endpoint when users need to find specific items within value sets
    • Call this for implementing autocomplete or search functionality for value set items
    • Use this when you need to locate items by code, label text, or other attributes
    • This searches within items, not value set metadata - use label search for that

    Business Logic:
    • Searches across item codes and labels in multiple languages
    • Supports partial text matching and regex patterns
    • Can search within specific value sets or across all value sets
    • Returns items with their parent value set context
    • Applies status filtering to exclude items from inactive value sets
    • Supports case-insensitive searching
    • Limits results to prevent performance issues

    Args:
        search_params (SearchItemsQuerySchema): Search criteria containing:
            - search_text (str): Text to search for in codes and labels
            - value_set_keys (List[str], optional): Specific value sets to search in
            - language_code (str, optional): Language for label searching (default: "en")
            - exact_match (bool, optional): Whether to use exact matching (default: False)
            - limit (int, optional): Maximum results to return (default: 100)
        service (ValueSetService): Injected service for search operations.

    Returns:
        List[SearchItemsResponseSchema]: List of matching items, each containing:
            - item_code (str): The matching item code
            - labels (dict): All labels for the item
            - value_set_key (str): Parent value set identifier
            - value_set_name (str): Parent value set display name
            - match_context (str): What part matched the search

    Example:
    ```python
    search_params = SearchItemsQuerySchema(
        search_text="cardio",
        value_set_keys=["medical_specialties"],
        language_code="en",
        exact_match=False,
        limit=50
    )
    results = await search_value_set_items(search_params, service)
    ```
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
    Searches for value sets by matching text in their item labels.

    LLM Instructions:
    • Use this endpoint when users want to find value sets containing items with specific labels
    • Call this to locate value sets based on the content of their items rather than metadata
    • Use this for finding value sets that contain specific terminology or concepts
    • This searches within item labels, not value set names - use list endpoint with filters for that

    Business Logic:
    • Searches through all item labels within value sets for the specified text
    • Performs case-insensitive partial text matching
    • Searches in the specified language code (defaults to English)
    • Optionally filters by value set status before searching
    • Returns complete value sets that contain matching items
    • Orders results by relevance (number of matching items)
    • Excludes value sets with no matching items

    Args:
        label_text (str): Text to search for within item labels.
            Supports partial matching, case-insensitive.
            Example: "heart", "cardio", "medical"
        language_code (str): ISO language code for label searching.
            Must match language codes used in item labels.
            Defaults to "en" for English.
        status (Optional[str]): Filter value sets by status before searching.
            Valid values: "ACTIVE", "INACTIVE", "ARCHIVED".
            If None, searches across all statuses.
        service (ValueSetService): Injected service for search operations.

    Returns:
        List[ValueSetResponseSchema]: List of complete value sets containing:
            - All value set metadata and items
            - Only value sets with at least one matching item label
            - Ordered by number of matching items (most relevant first)

    Example:
    ```python
    # Find value sets containing items with "heart" in English labels
    results = await search_value_sets_by_label(
        label_text="heart",
        language_code="en",
        status="ACTIVE",
        service
    )
    ```
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
    Adds a single new item to an existing value set with validation.

    LLM Instructions:
    • Use this endpoint when users want to add one new item to an existing value set
    • Call this for extending value sets with additional codes and labels
    • For adding multiple items at once, use the bulk add endpoint instead
    • Ensure the item code doesn't already exist in the target value set

    Business Logic:
    • Validates the target value set exists and is modifiable
    • Checks that the new item code is unique within the value set
    • Validates all required item fields are provided
    • Adds the item to the value set's items collection
    • Updates the value set's updated_at timestamp and updated_by field
    • Maintains referential integrity and audit trail
    • Returns the complete updated value set with the new item included

    Args:
        key (str): Unique identifier of the target value set.
            Must match an existing, non-archived value set.
        request (AddItemRequestSchema): Item addition request containing:
            - item (ItemCreateSchema): Complete item data with:
                - code (str): Unique identifier within the value set
                - labels (dict): Language-keyed display labels
                - metadata (dict, optional): Additional item metadata
            - updated_by (str): User ID performing the addition
        service (ValueSetService): Injected service for business operations.

    Returns:
        ValueSetResponseSchema: Complete updated value set including:
            - All existing items plus the newly added item
            - Updated audit fields (updated_at, updated_by)
            - All value set metadata unchanged

    Example:
    ```python
    request = AddItemRequestSchema(
        item=ItemCreateSchema(
            code="NEUROLOGY",
            labels={"en": "Neurology", "es": "Neurología"},
            metadata={"category": "specialty"}
        ),
        updated_by="user123"
    )
    result = await add_item_to_value_set("medical_specialties", request, service)
    ```
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
    Replaces an existing item's code and optionally updates its labels and metadata.

    LLM Instructions:
    • Use this endpoint when you need to change an item's code while preserving its identity
    • Call this for code standardization or migration scenarios
    • Use this when the item's meaning stays the same but its identifier changes
    • For label-only changes, use the update item endpoint instead

    Business Logic:
    • Validates the target value set exists and contains the old item code
    • Ensures the new item code doesn't already exist in the value set
    • Replaces the item's code with the new value
    • Optionally updates labels if provided in the request
    • Preserves existing labels if not specified in the replacement
    • Maintains all other item metadata and relationships
    • Updates audit fields for the value set
    • Ensures atomicity - either all changes succeed or none are applied

    Args:
        key (str): Unique identifier of the target value set.
            Must contain the item to be replaced.
        replace_request (ReplaceItemCodeSchema): Replacement specification containing:
            - old_code (str): Current item code to replace
            - new_code (str): New item code (must be unique in value set)
            - new_labels (dict, optional): Updated labels to replace existing ones
            - updated_by (str): User ID performing the replacement
        service (ValueSetService): Injected service for business operations.

    Returns:
        ValueSetResponseSchema: Complete updated value set with:
            - Item code changed from old_code to new_code
            - Updated labels if provided
            - All other items unchanged
            - Updated audit fields

    Example:
    ```python
    replace_request = ReplaceItemCodeSchema(
        old_code="CARDIO",
        new_code="CARDIOLOGY",
        new_labels={"en": "Cardiology", "es": "Cardiología"},
        updated_by="admin_user"
    )
    result = await replace_value_in_item("medical_specialties", replace_request, service)
    ```
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
    Updates labels and metadata of an existing item without changing its code.

    LLM Instructions:
    • Use this endpoint to modify item labels, descriptions, or metadata
    • Call this when users want to update item information but keep the same code
    • For changing item codes, use the replace item endpoint instead
    • This preserves the item's identity while updating its display information

    Business Logic:
    • Validates the target value set exists and contains the specified item
    • Updates only the fields provided in the request (partial updates supported)
    • Preserves the item code - it cannot be changed through this endpoint
    • Merges new labels with existing ones (doesn't replace entire label collection)
    • Updates metadata by merging with existing values
    • Maintains audit trail with updated_at and updated_by fields
    • Does not affect other items in the value set

    Args:
        key (str): Unique identifier of the target value set.
            Must contain the item to update.
        item_code (str): Code of the item to update.
            Must exist within the specified value set.
        request (UpdateItemRequestSchema): Update specification containing:
            - itemCode (str): Automatically set to match path parameter
            - labels (dict, optional): New or updated labels to merge
            - metadata (dict, optional): New or updated metadata to merge
            - updated_by (str): User ID performing the update
        service (ValueSetService): Injected service for business operations.

    Returns:
        ValueSetResponseSchema: Complete updated value set with:
            - Target item updated with new labels/metadata
            - All other items unchanged
            - Updated value set audit fields

    Example:
    ```python
    request = UpdateItemRequestSchema(
        labels={"en": "Cardiology (Updated)", "fr": "Cardiologie"},
        metadata={"specialty_type": "medical", "department": "cardiovascular"},
        updated_by="content_editor"
    )
    result = await update_item_in_value_set(
        "medical_specialties", "CARDIO", request, service
    )
    ```
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
    Adds multiple items to a value set in a single atomic operation.

    LLM Instructions:
    • Use this endpoint when users need to add many items at once to a value set
    • Call this for importing or migrating large sets of codes and labels
    • Use this instead of individual add operations for better performance
    • Ideal for initial value set population or bulk data imports

    Business Logic:
    • Validates the target value set exists and is modifiable
    • Checks all item codes are unique within the existing value set
    • Validates all item codes are unique within the provided items list
    • Performs all validations before adding any items (atomic operation)
    • Adds all items in a single database operation for consistency
    • Provides detailed results showing success/failure for each item
    • Updates value set audit fields only once after all additions
    • Rolls back entire operation if any item fails validation

    Args:
        key (str): Unique identifier of the target value set.
            Must be an existing, non-archived value set.
        items (List[ItemCreateSchema]): List of items to add, each containing:
            - code (str): Unique identifier within the value set
            - labels (dict): Language-keyed display labels
            - metadata (dict, optional): Additional item metadata
        updated_by (str): User ID performing the bulk operation.
            Used for audit trail on the value set.
        service (ValueSetService): Injected service for business operations.

    Returns:
        BulkOperationResponseSchema: Detailed operation results containing:
            - success_count (int): Number of items successfully added
            - failure_count (int): Number of items that failed
            - total_count (int): Total items attempted
            - errors (List[dict]): Details of any failures with item codes and reasons
            - updated_value_set (ValueSetResponseSchema): Complete updated value set

    Example:
    ```python
    items = [
        ItemCreateSchema(code="NEURO", labels={"en": "Neurology"}),
        ItemCreateSchema(code="ORTHO", labels={"en": "Orthopedics"}),
        ItemCreateSchema(code="DERM", labels={"en": "Dermatology"})
    ]
    result = await bulk_add_items("medical_specialties", items, "admin_user", service)
    ```
    """
    return await service.bulk_add_items(key, items, updated_by)


# 12. Bulk Update Items
@router.put("/items/bulk-update", response_model=BulkOperationResponseSchema)
async def bulk_update_items(
    updates: BulkItemUpdateSchema = Body(...),
    service: ValueSetService = Depends(get_value_set_service)
) -> BulkOperationResponseSchema:
    """
    Updates multiple items across one or more value sets in a single operation.

    LLM Instructions:
    • Use this endpoint for updating many items at once across multiple value sets
    • Call this for standardizing labels or metadata across large datasets
    • Use this for applying consistent changes to related items
    • Ideal for global updates or mass label translations

    Business Logic:
    • Validates all target value sets exist and are modifiable
    • Checks all specified items exist within their respective value sets
    • Performs all validations before applying any updates (atomic operation)
    • Updates items across multiple value sets in a coordinated manner
    • Provides detailed results for each update operation
    • Updates audit fields for all affected value sets
    • Maintains referential integrity across all affected data
    • Supports partial success with detailed error reporting

    Args:
        updates (BulkItemUpdateSchema): Bulk update specification containing:
            - updates (List[ItemUpdateSpec]): List of item updates, each with:
                - value_set_key (str): Target value set identifier
                - item_code (str): Item code to update
                - labels (dict, optional): New labels to merge
                - metadata (dict, optional): New metadata to merge
            - updated_by (str): User ID performing the bulk operation
        service (ValueSetService): Injected service for business operations.

    Returns:
        BulkOperationResponseSchema: Comprehensive operation results containing:
            - success_count (int): Number of items successfully updated
            - failure_count (int): Number of items that failed
            - total_count (int): Total update operations attempted
            - errors (List[dict]): Detailed failure information with item identification
            - affected_value_sets (List[str]): Keys of value sets that were modified

    Example:
    ```python
    updates = BulkItemUpdateSchema(
        updates=[
            {
                "value_set_key": "medical_specialties",
                "item_code": "CARDIO",
                "labels": {"en": "Cardiology (Updated)", "es": "Cardiología"}
            },
            {
                "value_set_key": "medical_specialties",
                "item_code": "NEURO",
                "metadata": {"category": "specialty", "active": True}
            }
        ],
        updated_by="bulk_editor"
    )
    result = await bulk_update_items(updates, service)
    ```
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
    Creates multiple value sets from bulk import data in a single operation.

    LLM Instructions:
    • Use this endpoint for importing large numbers of value sets from external sources
    • Call this when migrating value sets from other systems
    • Use this for initial system setup with predefined value sets
    • Ideal for batch creation scenarios with consistent data structure

    Business Logic:
    • Validates all value set keys are unique across the import and existing data
    • Performs comprehensive validation on all value sets before creating any
    • Creates all value sets in a coordinated transaction
    • Validates item codes are unique within each value set
    • Handles partial failures with detailed error reporting
    • Maintains data integrity across the entire import operation
    • Provides comprehensive results for each creation attempt
    • Sets appropriate audit fields for all created value sets

    Args:
        import_data (BulkValueSetCreateSchema): Bulk import specification containing:
            - value_sets (List[ValueSetCreateSchema]): List of complete value sets to create
            - created_by (str): User ID performing the bulk import
            - import_metadata (dict, optional): Additional metadata about the import
        service (ValueSetService): Injected service for business operations.

    Returns:
        BulkOperationResponseSchema: Detailed import results containing:
            - success_count (int): Number of value sets successfully created
            - failure_count (int): Number of value sets that failed
            - total_count (int): Total value sets attempted
            - errors (List[dict]): Detailed failure information with value set keys
            - created_keys (List[str]): Keys of successfully created value sets

    Example:
    ```python
    import_data = BulkValueSetCreateSchema(
        value_sets=[
            ValueSetCreateSchema(
                key="countries",
                name="Country Codes",
                module="geography",
                items=[ItemCreateSchema(code="US", labels={"en": "United States"})]
            ),
            ValueSetCreateSchema(
                key="currencies",
                name="Currency Codes",
                module="finance",
                items=[ItemCreateSchema(code="USD", labels={"en": "US Dollar"})]
            )
        ],
        created_by="import_user"
    )
    result = await bulk_import_value_sets(import_data, service)
    ```
    """
    return await service.bulk_import_value_sets(import_data)


# 16. Bulk Update Value Sets
@router.put("/bulk/update", response_model=BulkOperationResponseSchema)
async def bulk_update_value_sets(
    update_data: BulkValueSetUpdateSchema = Body(...),
    service: ValueSetService = Depends(get_value_set_service)
) -> BulkOperationResponseSchema:
    """
    Updates metadata and configuration for multiple value sets simultaneously.

    LLM Instructions:
    • Use this endpoint for applying consistent changes across multiple value sets
    • Call this when updating status, module assignments, or metadata in bulk
    • Use this for standardization or migration scenarios affecting many value sets
    • Ideal for administrative operations on groups of related value sets

    Business Logic:
    • Validates all target value sets exist before applying any updates
    • Performs updates in a coordinated manner to maintain consistency
    • Updates only the fields specified for each value set (partial updates)
    • Maintains audit trail with updated timestamps and user information
    • Provides detailed success/failure reporting for each value set
    • Does not modify items within value sets - only value set-level metadata
    • Supports different update operations for different value sets in the same request
    • Ensures atomic operations where possible, with rollback on critical failures

    Args:
        update_data (BulkValueSetUpdateSchema): Bulk update specification containing:
            - updates (List[ValueSetUpdateSpec]): List of value set updates, each with:
                - key (str): Value set identifier to update
                - name (str, optional): New display name
                - description (str, optional): New description
                - status (StatusEnum, optional): New status
                - metadata (dict, optional): Metadata to merge
            - updated_by (str): User ID performing the bulk operation
        service (ValueSetService): Injected service for business operations.

    Returns:
        BulkOperationResponseSchema: Comprehensive update results containing:
            - success_count (int): Number of value sets successfully updated
            - failure_count (int): Number of value sets that failed
            - total_count (int): Total update operations attempted
            - errors (List[dict]): Detailed failure information with value set keys
            - updated_keys (List[str]): Keys of successfully updated value sets

    Example:
    ```python
    update_data = BulkValueSetUpdateSchema(
        updates=[
            {
                "key": "medical_specialties",
                "status": StatusEnum.ACTIVE,
                "description": "Updated comprehensive list"
            },
            {
                "key": "country_codes",
                "module": "geography_v2",
                "metadata": {"migrated": True}
            }
        ],
        updated_by="admin_user"
    )
    result = await bulk_update_value_sets(update_data, service)
    ```
    """
    return await service.bulk_update_value_sets(update_data)


# 17. Validate Value Set
@router.post("/validate", response_model=ValidationResultSchema)
async def validate_value_set(
    validation_request: ValidateValueSetRequestSchema = Body(...),
    service: ValueSetService = Depends(get_value_set_service)
) -> ValidationResultSchema:
    """
    Validates value set configuration and data integrity without persisting changes.

    LLM Instructions:
    • Use this endpoint to validate value set data before creating or updating
    • Call this when users want to check data quality without making changes
    • Use this for pre-import validation of external data
    • Call this before bulk operations to catch issues early

    Business Logic:
    • Performs comprehensive validation without database modifications
    • Checks value set metadata completeness and format
    • Validates item code uniqueness within the value set
    • Verifies label structure and language code validity
    • Checks business rules and constraints
    • Validates against schema requirements
    • Identifies potential conflicts with existing data
    • Returns detailed validation results with specific error locations

    Args:
        validation_request (ValidateValueSetRequestSchema): Validation specification containing:
            - value_set_data (ValueSetCreateSchema): Complete value set to validate
            - validation_level (str, optional): Validation depth ("basic", "full", "strict")
            - check_conflicts (bool, optional): Whether to check for existing key conflicts
        service (ValueSetService): Injected service for validation operations.

    Returns:
        ValidationResultSchema: Comprehensive validation results containing:
            - is_valid (bool): Overall validation status
            - errors (List[dict]): Detailed error information with field paths
            - warnings (List[dict]): Non-critical issues found
            - suggestions (List[dict]): Recommendations for improvement
            - validation_summary (dict): Summary statistics and scores

    Example:
    ```python
    validation_request = ValidateValueSetRequestSchema(
        value_set_data=ValueSetCreateSchema(
            key="test_value_set",
            name="Test Value Set",
            module="testing",
            items=[ItemCreateSchema(code="TEST1", labels={"en": "Test Item"})]
        ),
        validation_level="full",
        check_conflicts=True
    )
    result = await validate_value_set(validation_request, service)
    ```
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
    Archives a value set, making it read-only and hiding it from active listings.

    LLM Instructions:
    • Use this endpoint when value sets need to be retired but preserved for historical reference
    • Call this instead of deleting value sets to maintain data integrity
    • Use this when value sets are no longer actively used but may be referenced
    • This is the preferred method for removing value sets from active use

    Business Logic:
    • Changes value set status to ARCHIVED without deleting data
    • Prevents further modifications to the archived value set
    • Maintains referential integrity and audit trail
    • Excludes archived value sets from default listings
    • Allows read access for historical queries
    • Records archive reason and responsible user
    • Updates timestamp to track when archiving occurred
    • Validates user permissions for archiving operations

    Args:
        key (str): Unique identifier of the value set to archive.
            Must be an existing, non-archived value set.
        archive_request (ArchiveRestoreRequestSchema): Archive specification containing:
            - key (str): Automatically set to match path parameter
            - reason (str): Explanation for archiving the value set
            - archived_by (str): User ID performing the archive operation
        service (ValueSetService): Injected service for business operations.

    Returns:
        ArchiveRestoreResponseSchema: Archive operation results containing:
            - success (bool): Whether the archive operation succeeded
            - message (str): Human-readable result description
            - value_set_key (str): Key of the archived value set
            - previous_status (str): Status before archiving
            - new_status (str): Status after archiving (ARCHIVED)
            - timestamp (str): When the operation occurred

    Example:
    ```python
    archive_request = ArchiveRestoreRequestSchema(
        reason="Value set superseded by new version",
        archived_by="admin_user"
    )
    result = await archive_value_set("old_medical_codes", archive_request, service)
    ```
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
    Restores an archived value set back to active status with full functionality.

    LLM Instructions:
    • Use this endpoint to reactivate previously archived value sets
    • Call this when archived value sets need to be returned to active use
    • Use this for recovering accidentally archived value sets
    • This reverses the archive operation and makes the value set modifiable again

    Business Logic:
    • Changes value set status from ARCHIVED back to ACTIVE
    • Restores full read-write access to the value set
    • Includes the value set in active listings again
    • Maintains complete audit trail of archive and restore operations
    • Validates the value set is currently archived before restoring
    • Records restore reason and responsible user
    • Updates timestamp to track when restoration occurred
    • Checks for potential conflicts with existing active value sets

    Args:
        key (str): Unique identifier of the archived value set to restore.
            Must be an existing value set with ARCHIVED status.
        restore_request (ArchiveRestoreRequestSchema): Restore specification containing:
            - key (str): Automatically set to match path parameter
            - reason (str): Explanation for restoring the value set
            - restored_by (str): User ID performing the restore operation
        service (ValueSetService): Injected service for business operations.

    Returns:
        ArchiveRestoreResponseSchema: Restore operation results containing:
            - success (bool): Whether the restore operation succeeded
            - message (str): Human-readable result description
            - value_set_key (str): Key of the restored value set
            - previous_status (str): Status before restoration (ARCHIVED)
            - new_status (str): Status after restoration (ACTIVE)
            - timestamp (str): When the operation occurred

    Example:
    ```python
    restore_request = ArchiveRestoreRequestSchema(
        reason="Value set needed for new project requirements",
        restored_by="project_manager"
    )
    result = await restore_value_set("archived_medical_codes", restore_request, service)
    ```
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
    Retrieves comprehensive statistical information about the value set system.

    LLM Instructions:
    • Use this endpoint to display system-wide value set metrics to administrators
    • Call this for generating reports and dashboards about value set usage
    • Use this for monitoring system health and data quality
    • Call this to understand the scope and scale of value set data

    Business Logic:
    • Aggregates counts across all value sets and statuses
    • Calculates distribution metrics by module and status
    • Computes item density and usage statistics
    • Analyzes data quality metrics and completeness
    • Provides temporal analysis of creation and update patterns
    • Includes performance metrics and system health indicators
    • Groups statistics by meaningful categories for reporting
    • Excludes soft-deleted or corrupted data from calculations

    Args:
        service (ValueSetService): Injected service for statistical operations.

    Returns:
        dict: Comprehensive statistics containing:
            - total_value_sets (int): Total number of value sets
            - by_status (dict): Counts grouped by status (ACTIVE, INACTIVE, ARCHIVED)
            - by_module (dict): Counts grouped by module name
            - total_items (int): Total number of items across all value sets
            - average_items_per_set (float): Mean items per value set
            - largest_value_set (dict): Information about the largest value set
            - creation_stats (dict): Creation date analysis and trends
            - update_stats (dict): Update frequency and recency analysis
            - quality_metrics (dict): Data completeness and validation scores

    Example:
    ```python
    stats = await get_value_set_statistics(service)
    print(f"System contains {stats['total_value_sets']} value sets")
    print(f"Active: {stats['by_status']['ACTIVE']}")
    print(f"Total items: {stats['total_items']}")
    ```
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
    Exports a complete value set in the specified format for external use.

    LLM Instructions:
    • Use this endpoint when users need to extract value set data for external systems
    • Call this for data migration, backup, or integration scenarios
    • Use this when value sets need to be shared with other applications
    • Call this for generating downloadable files of value set content

    Business Logic:
    • Retrieves the complete value set including all items and metadata
    • Formats data according to the specified export format
    • Includes all labels and metadata in the export
    • Maintains data relationships and structure in the output
    • Provides appropriate file headers and formatting for the target format
    • Validates export format is supported before processing
    • Excludes sensitive or system-internal fields from export
    • Generates export in a format suitable for re-import or external consumption

    Args:
        key (str): Unique identifier of the value set to export.
            Must be an existing value set.
        format (str): Export format specification.
            Supported values: "json" (default), "csv"
            JSON includes complete structure, CSV flattens items for tabular format.
        service (ValueSetService): Injected service for export operations.

    Returns:
        Various: Export data in the requested format:
            - JSON format: Complete nested structure with all metadata
            - CSV format: Flattened tabular representation of items
            - Includes appropriate content-type headers for download

    Example:
    ```python
    # Export as JSON
    json_export = await export_value_set("medical_specialties", "json", service)

    # Export as CSV
    csv_export = await export_value_set("medical_specialties", "csv", service)
    ```
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
    Imports a value set from external data sources with format conversion and validation.

    LLM Instructions:
    • Use this endpoint to import value sets from external systems or files
    • Call this for data migration from other value set management systems
    • Use this when integrating with external terminology services
    • Call this for restoring value sets from backup or export files

    Business Logic:
    • Validates and parses the import data according to the specified format
    • Converts external format to internal value set structure
    • Performs comprehensive validation on imported data
    • Checks for key conflicts with existing value sets
    • Validates all required fields are present and properly formatted
    • Creates the value set with appropriate audit and metadata fields
    • Handles format-specific parsing and transformation logic
    • Provides detailed error reporting for validation failures

    Args:
        import_data (dict): Raw import data in the specified format.
            Structure varies by format - JSON expects nested object, CSV expects flattened structure.
        format (str): Format of the import data.
            Supported values: "json" (default), "csv"
            Determines parsing and validation logic.
        created_by (str): User ID responsible for the import operation.
            Defaults to "system" for automated imports.
        service (ValueSetService): Injected service for import operations.

    Returns:
        ValueSetResponseSchema: Complete imported value set with:
            - All imported data converted to internal format
            - Generated metadata and audit fields
            - Validation results and any transformation notes

    Example:
    ```python
    # Import JSON format
    json_data = {
        "key": "imported_codes",
        "name": "Imported Codes",
        "items": [{"code": "IMP1", "labels": {"en": "Imported Item"}}]
    }
    result = await import_value_set(json_data, "json", "import_user", service)
    ```
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