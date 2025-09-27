"""
Service layer for Value Set business logic.
Handles validation, business rules, and audit fields.
File: /services/value_set_service.py
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from repositories.value_set_repository import ValueSetRepository
from schemas.value_set_schemas_enhanced import (
    ValueSetCreateSchema, ValueSetUpdateSchema, ValueSetResponseSchema,
    ItemCreateSchema, ItemUpdateSchema, ItemSchema,
    AddItemRequestSchema, UpdateItemRequestSchema,
    ReplaceItemCodeSchema, BulkValueSetCreateSchema, BulkValueSetUpdateSchema,
    BulkItemUpdateSchema, ValidateValueSetRequestSchema, ValidationResultSchema,
    ArchiveRestoreRequestSchema, ArchiveRestoreResponseSchema,
    ListValueSetsQuerySchema, SearchItemsQuerySchema, SearchItemsResponseSchema,
    PaginatedValueSetResponse, PaginatedSearchResponse,
    BulkOperationResponseSchema, ErrorResponseSchema,
    ValueSetListItemSchema
)
import json
from io import StringIO
import csv


class ValueSetService:
    """
    Service class providing business logic operations for value set management.

    LLM Instructions:
    • Use this service class to perform all value set CRUD operations with proper validation
    • Always instantiate with a ValueSetRepository to handle database operations
    • This class handles business rules, validation, and audit field management
    • Call appropriate methods based on the specific operation needed (create, update, search, etc.)

    Business Logic:
    • Enforces unique value set keys across the system
    • Validates item codes are unique within each value set
    • Maintains item count limits (1-500 items per value set)
    • Manages audit fields (createdAt, createdBy, updatedAt, updatedBy)
    • Handles status transitions between ACTIVE and ARCHIVED states
    • Provides bulk operations for efficient data processing

    Args:
        repository: ValueSetRepository instance for database operations

    Returns:
        Service instance ready to handle value set operations

    Example:
    ```python
    from repositories.value_set_repository import ValueSetRepository
    from services.value_set_service import ValueSetService

    repository = ValueSetRepository(database_connection)
    service = ValueSetService(repository)

    # Now ready to perform value set operations
    value_set = await service.create_value_set(create_data)
    ```
    """

    def __init__(self, repository: ValueSetRepository):
        """
        Initialize the ValueSetService with a repository for database operations.

        LLM Instructions:
        • Call this constructor first before using any service methods
        • Always pass a valid ValueSetRepository instance
        • This sets up the service to handle all value set business operations
        • Required for dependency injection pattern

        Business Logic:
        • Stores repository reference for all database operations
        • No validation performed at initialization
        • Service remains stateless except for repository dependency

        Args:
            repository (ValueSetRepository): Repository instance for database operations.
                Must be properly initialized with database connection.
                Handles all CRUD operations at the data layer.

        Returns:
            None: Constructor does not return a value

        Example:
        ```python
        from repositories.value_set_repository import ValueSetRepository

        repo = ValueSetRepository(db_connection)
        service = ValueSetService(repo)
        ```
        """
        self.repository = repository

    async def create_value_set(self, create_data: ValueSetCreateSchema) -> ValueSetResponseSchema:
        """
        Create a new value set with comprehensive validation and business rule enforcement.

        LLM Instructions:
        • Use this method to create new value sets in the system
        • Ensure the ValueSetCreateSchema is properly populated before calling
        • Handle ValueError exceptions for validation failures
        • This is the primary entry point for value set creation
        • Always check if key exists before attempting creation

        Business Logic:
        • Validates value set key uniqueness across the entire system
        • Enforces unique item codes within the value set (no duplicates)
        • Validates item count is between 1 and 500 (inclusive)
        • Sets audit fields: createdAt, createdBy (updatedAt/updatedBy remain null)
        • Converts status enum to string value for storage
        • Transforms ItemCreateSchema objects to dictionaries for persistence

        Args:
            create_data (ValueSetCreateSchema): Complete value set creation data including:
                - key (str): Unique identifier for the value set
                - status (ValueSetStatus): Status enum (ACTIVE or ARCHIVED)
                - module (str): Module/category classification
                - description (str): Human-readable description
                - items (List[ItemCreateSchema]): List of 1-500 items with codes and labels
                - createdBy (str): Username/ID of creator
                - createdAt (Optional[datetime]): Creation timestamp (auto-generated if None)

        Returns:
            ValueSetResponseSchema: Newly created value set with generated ID and audit fields.
                Contains all input data plus database-generated fields.

        Raises:
            ValueError: If key already exists, item codes are not unique, or item count is invalid

        Example:
        ```python
        from schemas.value_set_schemas_enhanced import ValueSetCreateSchema, ItemCreateSchema

        items = [ItemCreateSchema(code="001", labels={"en": "Item One"})]
        create_data = ValueSetCreateSchema(
            key="test-value-set",
            status=ValueSetStatus.ACTIVE,
            module="test",
            description="Test value set",
            items=items,
            createdBy="user123"
        )

        value_set = await service.create_value_set(create_data)
        ```
        """
        # Check if key already exists
        if await self.repository.check_key_exists(create_data.key):
            raise ValueError(f"Value set with key '{create_data.key}' already exists")

        # Validate unique item codes
        item_codes = [item.code for item in create_data.items]
        if len(item_codes) != len(set(item_codes)):
            raise ValueError("Item codes must be unique within the value set")

        # Validate item count
        if not (1 <= len(create_data.items) <= 500):
            raise ValueError("Number of items must be between 1 and 500")

        # Prepare document
        document = {
            "key": create_data.key,
            "status": create_data.status.value,
            "module": create_data.module,
            "description": create_data.description,
            "items": [item.model_dump() for item in create_data.items],
            "createdAt": create_data.createdAt or datetime.utcnow(),
            "createdBy": create_data.createdBy,
            "updatedAt": None,
            "updatedBy": None
        }

        # Create in database
        result = await self.repository.create(document)
        return ValueSetResponseSchema(**result)

    async def get_value_set_by_key(self, key: str) -> Optional[ValueSetResponseSchema]:
        """
        Retrieve a specific value set by its unique key identifier.

        LLM Instructions:
        • Use this method to fetch a single value set when you know the exact key
        • Always check if return value is None before using the result
        • This is the most efficient way to get a specific value set
        • Use for read operations where key is known

        Business Logic:
        • Performs direct key lookup in the database
        • Returns complete value set data including all items
        • No filtering or validation applied
        • Case-sensitive key matching

        Args:
            key (str): The unique key identifier for the value set.
                Must be an exact match (case-sensitive).
                Examples: "country-codes", "user-roles", "status-types"

        Returns:
            Optional[ValueSetResponseSchema]: Complete value set data if found, None if not found.
                Contains all fields: key, status, module, description, items, audit fields.

        Example:
        ```python
        value_set = await service.get_value_set_by_key("country-codes")
        if value_set:
            print(f"Found value set: {value_set.key} with {len(value_set.items)} items")
        else:
            print("Value set not found")
        ```
        """
        document = await self.repository.find_by_key(key)
        if document:
            return ValueSetResponseSchema(**document)
        return None

    async def update_value_set(
        self,
        key: str,
        update_data: ValueSetUpdateSchema
    ) -> Optional[ValueSetResponseSchema]:
        """
        Update an existing value set with validation and audit trail management.

        LLM Instructions:
        • Use this method to modify existing value sets
        • Provide only the fields you want to update in the ValueSetUpdateSchema
        • Always handle None return value (indicates value set not found)
        • Use for partial updates - only specified fields are modified
        • Handles validation for item uniqueness and count limits

        Business Logic:
        • Validates value set exists before attempting update
        • Enforces unique item codes within value set if items are updated
        • Validates item count (1-500) if items are provided
        • Updates audit fields: updatedAt (current time), updatedBy (from request)
        • Only updates fields that are explicitly provided (partial update)
        • Preserves existing data for fields not in update request

        Args:
            key (str): Unique identifier of the value set to update.
                Must match an existing value set exactly.
            update_data (ValueSetUpdateSchema): Update data containing only fields to modify:
                - status (Optional[ValueSetStatus]): New status if changing
                - description (Optional[str]): New description (can be empty string)
                - module (Optional[str]): New module classification
                - items (Optional[List[ItemUpdateSchema]]): Complete new item list
                - updatedBy (str): Username/ID performing the update
                - updatedAt (Optional[datetime]): Update timestamp (auto-generated if None)

        Returns:
            Optional[ValueSetResponseSchema]: Updated value set data if successful, None if not found.
                Contains all current data with applied updates.

        Raises:
            ValueError: If item codes are not unique or item count exceeds limits (1-500)

        Example:
        ```python
        from schemas.value_set_schemas_enhanced import ValueSetUpdateSchema

        update_data = ValueSetUpdateSchema(
            description="Updated description",
            status=ValueSetStatus.ARCHIVED,
            updatedBy="admin123"
        )

        updated_vs = await service.update_value_set("test-key", update_data)
        if updated_vs:
            print(f"Updated value set: {updated_vs.key}")
        ```
        """
        # Check if value set exists
        existing = await self.repository.find_by_key(key)
        if not existing:
            return None

        # Validate items if provided
        if update_data.items:
            item_codes = [item.code for item in update_data.items]
            if len(item_codes) != len(set(item_codes)):
                raise ValueError("Item codes must be unique within the value set")

            if not (1 <= len(update_data.items) <= 500):
                raise ValueError("Number of items must be between 1 and 500")

        # Prepare update fields
        update_fields = {
            "updatedAt": update_data.updatedAt or datetime.utcnow(),
            "updatedBy": update_data.updatedBy
        }

        if update_data.status:
            update_fields["status"] = update_data.status.value
        if update_data.description is not None:
            update_fields["description"] = update_data.description
        if update_data.module:
            update_fields["module"] = update_data.module
        if update_data.items:
            update_fields["items"] = [item.model_dump() for item in update_data.items]

        # Update in database
        result = await self.repository.update_by_key(key, update_fields)
        if result:
            return ValueSetResponseSchema(**result)
        return None


    async def list_value_sets(
        self,
        query_params: ListValueSetsQuerySchema
    ) -> PaginatedValueSetResponse:
        """
        Retrieve a paginated list of value sets with optional filtering capabilities.

        LLM Instructions:
        • Use this method to get multiple value sets with pagination support
        • Apply filters for status and module to narrow results
        • Handle pagination using skip and limit parameters
        • Check hasMore flag to determine if additional pages exist
        • Use for listing, browsing, and administrative views

        Business Logic:
        • Builds filter query based on optional status and module parameters
        • Applies pagination with skip/limit for performance
        • Transforms documents to include calculated itemCount field
        • Returns lightweight list items (not full value set data)
        • Calculates hasMore flag based on total count and current page

        Args:
            query_params (ListValueSetsQuerySchema): Query parameters containing:
                - status (Optional[ValueSetStatus]): Filter by status (ACTIVE, ARCHIVED)
                - module (Optional[str]): Filter by module/category
                - skip (int): Number of records to skip (default: 0, for pagination)
                - limit (int): Maximum records to return (default: 50, max: 100)

        Returns:
            PaginatedValueSetResponse: Paginated response containing:
                - total (int): Total count of matching records
                - skip (int): Number of records skipped
                - limit (int): Maximum records per page
                - hasMore (bool): Whether more pages are available
                - items (List[ValueSetListItemSchema]): List of value set summaries with itemCount

        Example:
        ```python
        from schemas.value_set_schemas_enhanced import ListValueSetsQuerySchema

        query = ListValueSetsQuerySchema(
            status=ValueSetStatus.ACTIVE,
            module="countries",
            skip=0,
            limit=20
        )

        response = await service.list_value_sets(query)
        print(f"Found {response.total} value sets, showing {len(response.items)}")
        ```
        """
        # Build filter query
        filter_query = {}
        if query_params.status:
            filter_query["status"] = query_params.status.value
        if query_params.module:
            filter_query["module"] = query_params.module

        # Get results from repository
        documents, total = await self.repository.list_value_sets(
            filter_query,
            skip=query_params.skip,
            limit=query_params.limit
        )

        # Transform to response schema
        items = []
        for doc in documents:
            items.append(ValueSetListItemSchema(
                **doc,
                itemCount=len(doc.get("items", []))
            ))

        return PaginatedValueSetResponse(
            total=total,
            skip=query_params.skip,
            limit=query_params.limit,
            items=items,
            hasMore=(query_params.skip + query_params.limit) < total
        )

    async def search_value_set_items(
        self,
        search_params: SearchItemsQuerySchema
    ) -> List[SearchItemsResponseSchema]:
        """
        Search for specific items across value sets using text matching.

        LLM Instructions:
        • Use this method to find items by label text across multiple value sets
        • Specify valueSetKey to limit search to a single value set
        • Use languageCode to search in specific language labels
        • Returns matching items with their parent value set context
        • Ideal for autocomplete, lookup, and search features

        Business Logic:
        • Performs text search on item labels across value sets
        • Supports language-specific search (defaults to English)
        • Can search globally or within a specific value set
        • Returns items with their parent value set metadata
        • Groups results by value set for organized presentation

        Args:
            search_params (SearchItemsQuerySchema): Search parameters containing:
                - query (str): Text to search for in item labels (case-insensitive)
                - valueSetKey (Optional[str]): Limit search to specific value set
                - languageCode (str): Language code for label search (default: "en")
                Supported language codes: "en" (English), "hi" (Hindi)

        Returns:
            List[SearchItemsResponseSchema]: List of search results grouped by value set:
                - valueSetKey (str): Key of the value set containing matches
                - valueSetModule (str): Module of the value set
                - matchingItems (List[ItemSchema]): Items that matched the search
                - totalMatches (int): Count of matching items in this value set

        Example:
        ```python
        from schemas.value_set_schemas_enhanced import SearchItemsQuerySchema

        search_params = SearchItemsQuerySchema(
            query="united",
            languageCode="en"
        )

        results = await service.search_value_set_items(search_params)
        for result in results:
            print(f"Found {result.totalMatches} matches in {result.valueSetKey}")
        ```
        """
        results = await self.repository.search_items(
            search_params.query,
            search_params.valueSetKey,
            search_params.languageCode
        )

        response_items = []
        for result in results:
            response_items.append(SearchItemsResponseSchema(
                valueSetKey=result["key"],
                valueSetModule=result.get("module", ""),
                matchingItems=[ItemSchema(**item) for item in result["matchingItems"]],
                totalMatches=len(result["matchingItems"])
            ))

        return response_items

    async def search_value_sets_by_label(
        self,
        label_text: str,
        language_code: str = "en",
        status: Optional[str] = None
    ) -> List[ValueSetResponseSchema]:
        """
        Search for value sets containing items with specific label text.

        LLM Instructions:
        • Use this method to find value sets by searching item label content
        • Searches across all items within value sets to find text matches
        • Apply status filter to limit results to ACTIVE or ARCHIVED value sets
        • Returns complete value set data (not just summaries)
        • Use for content-based discovery of relevant value sets

        Business Logic:
        • Performs text search on item labels across all value sets
        • Searches in specified language (defaults to English)
        • Optionally filters results by value set status
        • Returns full value set data including all items
        • Case-insensitive text matching

        Args:
            label_text (str): Text to search for in item labels.
                Searches within label content using case-insensitive matching.
                Examples: "country", "active", "pending"
            language_code (str): Language code for label search (default: "en").
                Supported values: "en" (English), "hi" (Hindi)
            status (Optional[str]): Filter by value set status.
                Valid values: "active", "archived", None (no filter)

        Returns:
            List[ValueSetResponseSchema]: Complete value sets containing matching items.
                Each contains full data: key, status, module, description, all items, audit fields.

        Example:
        ```python
        # Find value sets containing country-related items
        value_sets = await service.search_value_sets_by_label(
            label_text="country",
            language_code="en",
            status="active"
        )

        for vs in value_sets:
            print(f"Found value set: {vs.key} with {len(vs.items)} items")
        ```
        """
        results = await self.repository.search_by_label(
            label_text,
            language_code,
            status
        )

        return [ValueSetResponseSchema(**doc) for doc in results]

    async def add_item_to_value_set(
        self,
        key: str,
        request: AddItemRequestSchema
    ) -> Optional[ValueSetResponseSchema]:
        """
        Add a single new item to an existing value set with validation.

        LLM Instructions:
        • Use this method to add one item at a time to existing value sets
        • Ensure item code is unique within the target value set
        • Check that value set exists before attempting to add items
        • Handle ValueError for duplicate codes or limit violations
        • Use bulk_add_items for multiple items to improve performance

        Business Logic:
        • Validates value set exists before attempting addition
        • Checks item code uniqueness within the target value set
        • Enforces 500-item limit per value set
        • Updates audit fields: updatedAt (current time), updatedBy (from request)
        • Preserves all existing items while adding the new one
        • Maintains item order (new item appended to end)

        Args:
            key (str): Unique identifier of the target value set.
                Must match an existing value set exactly.
            request (AddItemRequestSchema): Add item request containing:
                - item (ItemCreateSchema): New item with code and labels
                - updatedBy (str): Username/ID performing the operation
                Item must have unique code and valid label structure.

        Returns:
            Optional[ValueSetResponseSchema]: Updated value set with new item if successful,
                None if value set not found. Contains all existing items plus the new one.

        Raises:
            ValueError: If item code already exists in value set or 500-item limit exceeded

        Example:
        ```python
        from schemas.value_set_schemas_enhanced import AddItemRequestSchema, ItemCreateSchema

        new_item = ItemCreateSchema(
            code="NEW001",
            labels={"en": "New Item", "hi": "नया आइटम"}
        )
        request = AddItemRequestSchema(item=new_item, updatedBy="user123")

        updated_vs = await service.add_item_to_value_set("test-key", request)
        if updated_vs:
            print(f"Added item, now has {len(updated_vs.items)} items")
        ```
        """
        # Get current items
        current_items = await self.repository.get_items_by_key(key)
        if current_items is None:
            return None

        # Check if code already exists
        existing_codes = [item["code"] for item in current_items]
        if request.item.code in existing_codes:
            raise ValueError(f"Item with code '{request.item.code}' already exists")

        # Check item limit
        if len(current_items) >= 500:
            raise ValueError("Maximum number of items (500) reached")

        # Add item
        update_fields = {
            "updatedAt": datetime.utcnow(),
            "updatedBy": request.updatedBy
        }

        result = await self.repository.add_item(
            key,
            request.item.model_dump(),
            update_fields
        )

        if result:
            return ValueSetResponseSchema(**result)
        return None

    async def update_item_in_value_set(
        self,
        key: str,
        request: UpdateItemRequestSchema
    ) -> Optional[ValueSetResponseSchema]:
        """
        Update an existing item within a value set with conflict validation.

        LLM Instructions:
        • Use this method to modify existing items within value sets
        • Specify the current item code to identify which item to update
        • Provide only the fields you want to change in the updates object
        • Handle code changes carefully to avoid duplicates
        • Returns None if value set or item not found

        Business Logic:
        • Validates value set and target item exist
        • Checks for code conflicts if updating item code
        • Supports partial updates (code and/or labels)
        • Updates audit fields: updatedAt (current time), updatedBy (from request)
        • Preserves existing item data for fields not being updated
        • Maintains item order within the value set

        Args:
            key (str): Unique identifier of the value set containing the item.
                Must match an existing value set exactly.
            request (UpdateItemRequestSchema): Update request containing:
                - itemCode (str): Current code of the item to update
                - updates (ItemUpdateSchema): Fields to update (partial):
                  * code (Optional[str]): New code if changing
                  * labels (Optional[LabelsSchema]): New labels if changing
                - updatedBy (str): Username/ID performing the update

        Returns:
            Optional[ValueSetResponseSchema]: Updated value set if successful,
                None if value set not found. Contains all items with updates applied.

        Raises:
            ValueError: If target item not found or new code conflicts with existing item

        Example:
        ```python
        from schemas.value_set_schemas_enhanced import UpdateItemRequestSchema, ItemUpdateSchema

        updates = ItemUpdateSchema(
            code="UPDATED001",
            labels={"en": "Updated Label"}
        )
        request = UpdateItemRequestSchema(
            itemCode="OLD001",
            updates=updates,
            updatedBy="user123"
        )

        updated_vs = await service.update_item_in_value_set("test-key", request)
        ```
        """
        # Get current items to validate
        current_items = await self.repository.get_items_by_key(key)
        if current_items is None:
            return None

        # Check if item exists
        item_exists = any(item["code"] == request.itemCode for item in current_items)
        if not item_exists:
            raise ValueError(f"Item with code '{request.itemCode}' not found")

        # If updating code, check for conflicts
        if request.updates.code:
            existing_codes = [item["code"] for item in current_items if item["code"] != request.itemCode]
            if request.updates.code in existing_codes:
                raise ValueError(f"Item with code '{request.updates.code}' already exists")

        # Prepare updates
        item_updates = {}
        if request.updates.code:
            item_updates["code"] = request.updates.code
        if request.updates.labels:
            labels_update = {}
            if request.updates.labels.en:
                labels_update["en"] = request.updates.labels.en
            if request.updates.labels.hi is not None:
                labels_update["hi"] = request.updates.labels.hi
            if labels_update:
                item_updates["labels"] = labels_update

        update_fields = {
            "updatedAt": datetime.utcnow(),
            "updatedBy": request.updatedBy
        }

        result = await self.repository.update_item(
            key,
            request.itemCode,
            item_updates,
            update_fields
        )

        if result:
            return ValueSetResponseSchema(**result)
        return None


    async def bulk_add_items(
        self,
        key: str,
        items: List[ItemCreateSchema],
        updated_by: str
    ) -> BulkOperationResponseSchema:
        """
        Add multiple items to a value set in a single efficient operation.

        LLM Instructions:
        • Use this method for adding multiple items at once to improve performance
        • Check duplicate codes across both existing and new items
        • Monitor bulk operation response for success/failure counts
        • Prefer this over multiple add_item_to_value_set calls
        • All items are added or none are added (atomic operation)

        Business Logic:
        • Validates value set exists before processing items
        • Checks for duplicate codes between existing and new items
        • Enforces 500-item total limit (existing + new items)
        • Performs atomic bulk addition (all succeed or all fail)
        • Updates audit fields: updatedAt (current time), updatedBy (provided)
        • Maintains performance by using single database operation

        Args:
            key (str): Unique identifier of the target value set.
                Must match an existing value set exactly.
            items (List[ItemCreateSchema]): List of items to add, each containing:
                - code (str): Unique code within the value set
                - labels (LabelsSchema): Label translations (en required, hi optional)
                All codes must be unique among themselves and against existing items.
            updated_by (str): Username/ID of user performing the bulk operation.
                Used for audit trail in updatedBy field.

        Returns:
            BulkOperationResponseSchema: Operation result containing:
                - successful (int): Number of items successfully added
                - failed (int): Number of items that failed to add
                - errors (List[Dict]): Error details if any failures occurred
                - processedKeys (List[str]): Keys of value sets that were modified

        Example:
        ```python
        from schemas.value_set_schemas_enhanced import ItemCreateSchema

        items = [
            ItemCreateSchema(code="BULK001", labels={"en": "Bulk Item 1"}),
            ItemCreateSchema(code="BULK002", labels={"en": "Bulk Item 2"})
        ]

        response = await service.bulk_add_items("test-key", items, "admin123")
        print(f"Added {response.successful} items, {response.failed} failed")
        ```
        """
        # Get current items
        current_items = await self.repository.get_items_by_key(key)
        if current_items is None:
            return BulkOperationResponseSchema(
                successful=0,
                failed=len(items),
                errors=[{"key": key, "error": "Value set not found"}]
            )

        # Check for duplicate codes
        existing_codes = set(item["code"] for item in current_items)
        new_codes = [item.code for item in items]

        duplicates = [code for code in new_codes if code in existing_codes]
        if duplicates:
            return BulkOperationResponseSchema(
                successful=0,
                failed=len(items),
                errors=[{"codes": duplicates, "error": "Duplicate codes found"}]
            )

        # Check item limit
        if len(current_items) + len(items) > 500:
            return BulkOperationResponseSchema(
                successful=0,
                failed=len(items),
                errors=[{"error": f"Adding {len(items)} items would exceed 500 item limit"}]
            )

        # Perform bulk add
        operations = [{
            "key": key,
            "items": [item.model_dump() for item in items],
            "update_fields": {
                "updatedAt": datetime.utcnow(),
                "updatedBy": updated_by
            }
        }]

        result = await self.repository.bulk_add_items(operations)

        return BulkOperationResponseSchema(
            successful=result["modified"],
            failed=len(items) - result["modified"],
            errors=[],
            processedKeys=[key] if result["modified"] > 0 else []
        )

    async def bulk_update_items(
        self,
        updates: BulkItemUpdateSchema
    ) -> BulkOperationResponseSchema:
        """
        Update multiple items across different value sets in a single operation.

        LLM Instructions:
        • Use this method to update items across multiple value sets efficiently
        • Each update specifies valueSetKey, itemCode, and the changes to apply
        • Monitor response for success/failure counts per update
        • Use for batch operations across the entire system
        • More efficient than individual update calls

        Business Logic:
        • Processes updates across multiple value sets in batch
        • Validates each item exists before updating
        • Supports partial updates (code and/or labels)
        • Updates audit fields for each modified value set
        • Continues processing even if some updates fail
        • Returns detailed success/failure statistics

        Args:
            updates (BulkItemUpdateSchema): Bulk update configuration containing:
                - itemUpdates (List[ItemUpdateRequestSchema]): List of individual updates:
                  * valueSetKey (str): Target value set identifier
                  * itemCode (str): Current code of item to update
                  * updates (ItemUpdateSchema): Fields to change
                  * updatedBy (str): User performing this specific update
                Each update is processed independently.

        Returns:
            BulkOperationResponseSchema: Operation results containing:
                - successful (int): Number of items successfully updated
                - failed (int): Number of items that failed to update
                - errors (List[Dict]): Detailed error information for failures
                - processedKeys (List[str]): Empty list (not applicable for item updates)

        Example:
        ```python
        from schemas.value_set_schemas_enhanced import BulkItemUpdateSchema, ItemUpdateRequestSchema

        updates = BulkItemUpdateSchema(
            itemUpdates=[
                ItemUpdateRequestSchema(
                    valueSetKey="set1",
                    itemCode="ITEM001",
                    updates=ItemUpdateSchema(labels={"en": "Updated Label"}),
                    updatedBy="admin123"
                )
            ]
        )

        response = await service.bulk_update_items(updates)
        ```
        """
        operations = []
        for update in updates.itemUpdates:
            item_updates = {}
            if update.updates.code:
                item_updates["code"] = update.updates.code
            if update.updates.labels:
                labels_update = {}
                if update.updates.labels.en:
                    labels_update["en"] = update.updates.labels.en
                if update.updates.labels.hi is not None:
                    labels_update["hi"] = update.updates.labels.hi
                if labels_update:
                    item_updates["labels"] = labels_update

            operations.append({
                "key": update.valueSetKey,
                "item_code": update.itemCode,
                "updates": item_updates,
                "update_fields": {
                    "updatedAt": datetime.utcnow(),
                    "updatedBy": update.updatedBy
                }
            })

        result = await self.repository.bulk_update_items(operations)

        return BulkOperationResponseSchema(
            successful=result["successful"],
            failed=result["failed"],
            errors=result.get("errors", []),
            processedKeys=[]
        )


    async def replace_value_in_item(
        self,
        key: str,
        replace_request: ReplaceItemCodeSchema
    ) -> Optional[ValueSetResponseSchema]:
        """
        Replace an item's code and optionally update its labels in a single operation.

        LLM Instructions:
        • Use this method when you need to change an item's code identifier
        • Optionally provide new labels or keep existing ones
        • Handles validation to prevent code conflicts
        • This is different from update - it's a complete code replacement
        • Returns None if value set or original item not found

        Business Logic:
        • Validates value set and original item exist
        • Checks new code doesn't conflict with other items
        • Replaces item code while preserving or updating labels
        • Uses existing labels if new labels not provided
        • Updates audit fields: updatedAt (current time), updatedBy (from request)
        • Maintains item position within the value set

        Args:
            key (str): Unique identifier of the value set containing the item.
                Must match an existing value set exactly.
            replace_request (ReplaceItemCodeSchema): Replacement request containing:
                - oldCode (str): Current code of the item to replace
                - newCode (str): New code to assign to the item
                - newLabels (Optional[LabelsSchema]): New labels (optional, keeps existing if None)
                - updatedBy (str): Username/ID performing the replacement
                New code must not conflict with existing items.

        Returns:
            Optional[ValueSetResponseSchema]: Updated value set if successful,
                None if value set not found. Contains all items with replacement applied.

        Raises:
            ValueError: If original item not found or new code conflicts with existing item

        Example:
        ```python
        from schemas.value_set_schemas_enhanced import ReplaceItemCodeSchema, LabelsSchema

        replace_request = ReplaceItemCodeSchema(
            oldCode="OLD001",
            newCode="NEW001",
            newLabels=LabelsSchema(en="New Label", hi="नया लेबल"),
            updatedBy="admin123"
        )

        updated_vs = await service.replace_value_in_item("test-key", replace_request)
        ```
        """
        # Get current items to validate
        current_items = await self.repository.get_items_by_key(key)
        if current_items is None:
            return None

        # Find old item
        old_item = None
        for item in current_items:
            if item["code"] == replace_request.oldCode:
                old_item = item
                break

        if not old_item:
            raise ValueError(f"Item with code '{replace_request.oldCode}' not found")

        # Check new code doesn't conflict
        if replace_request.newCode != replace_request.oldCode:
            existing_codes = [item["code"] for item in current_items if item["code"] != replace_request.oldCode]
            if replace_request.newCode in existing_codes:
                raise ValueError(f"Item with code '{replace_request.newCode}' already exists")

        # Prepare new item
        new_item = {
            "code": replace_request.newCode,
            "labels": replace_request.newLabels.model_dump() if replace_request.newLabels else old_item["labels"]
        }

        update_fields = {
            "updatedAt": datetime.utcnow(),
            "updatedBy": replace_request.updatedBy
        }

        result = await self.repository.replace_item_value(
            key,
            replace_request.oldCode,
            new_item,
            update_fields
        )

        if result:
            return ValueSetResponseSchema(**result)
        return None

    async def bulk_import_value_sets(
        self,
        import_data: BulkValueSetCreateSchema
    ) -> BulkOperationResponseSchema:
        """
        Import multiple value sets in a single bulk operation with validation.

        LLM Instructions:
        • Use this method to create multiple value sets at once efficiently
        • All value sets are validated before any are created
        • Monitor response for detailed success/failure statistics
        • Failed imports don't affect successful ones
        • Ideal for data migration and initial system setup

        Business Logic:
        • Validates all value sets before creating any (fail-fast approach)
        • Checks for duplicate keys across existing and new value sets
        • Validates item uniqueness within each value set
        • Creates audit fields for each value set
        • Performs atomic bulk creation for validated value sets
        • Returns detailed error information for failed validations

        Args:
            import_data (BulkValueSetCreateSchema): Bulk import data containing:
                - valueSets (List[ValueSetCreateSchema]): List of value sets to create:
                  * Each must have unique key, valid items, and proper structure
                  * Item codes must be unique within each value set
                  * All required fields must be populated
                Validation occurs before any database operations.

        Returns:
            BulkOperationResponseSchema: Import results containing:
                - successful (int): Number of value sets successfully created
                - failed (int): Number of value sets that failed validation/creation
                - errors (List[Dict]): Detailed error info with index, key, and error message
                - processedKeys (List[str]): Keys of successfully created value sets

        Example:
        ```python
        from schemas.value_set_schemas_enhanced import BulkValueSetCreateSchema, ValueSetCreateSchema

        value_sets = [
            ValueSetCreateSchema(
                key="import-set-1",
                status=ValueSetStatus.ACTIVE,
                module="import",
                description="Imported set 1",
                items=[ItemCreateSchema(code="001", labels={"en": "Item 1"})],
                createdBy="import-user"
            )
        ]

        import_data = BulkValueSetCreateSchema(valueSets=value_sets)
        response = await service.bulk_import_value_sets(import_data)
        ```
        """
        # Validate all value sets first
        documents = []
        errors = []

        for idx, vs in enumerate(import_data.valueSets):
            # Check if key exists
            if await self.repository.check_key_exists(vs.key):
                errors.append({
                    "index": idx,
                    "key": vs.key,
                    "error": f"Key '{vs.key}' already exists"
                })
                continue

            # Validate items
            item_codes = [item.code for item in vs.items]
            if len(item_codes) != len(set(item_codes)):
                errors.append({
                    "index": idx,
                    "key": vs.key,
                    "error": "Duplicate item codes"
                })
                continue

            # Prepare document
            documents.append({
                "key": vs.key,
                "status": vs.status.value,
                "module": vs.module,
                "description": vs.description,
                "items": [item.model_dump() for item in vs.items],
                "createdAt": vs.createdAt or datetime.utcnow(),
                "createdBy": vs.createdBy,
                "updatedAt": None,
                "updatedBy": None
            })

        if documents:
            result = await self.repository.bulk_create(documents)
            return BulkOperationResponseSchema(
                successful=result["successful"],
                failed=result["failed"] + len(errors),
                errors=errors + result.get("errors", []),
                processedKeys=[doc["key"] for doc in documents[:result["successful"]]]
            )

        return BulkOperationResponseSchema(
            successful=0,
            failed=len(import_data.valueSets),
            errors=errors,
            processedKeys=[]
        )

    async def bulk_update_value_sets(
        self,
        update_data: BulkValueSetUpdateSchema
    ) -> BulkOperationResponseSchema:
        """
        Update multiple value sets in a single bulk operation for efficiency.

        LLM Instructions:
        • Use this method to update metadata across multiple value sets
        • Each update can modify different fields (status, module, description)
        • Monitor response for success/failure counts
        • More efficient than individual update calls
        • Does not modify items - use bulk_update_items for item changes

        Business Logic:
        • Processes updates for multiple value sets in batch
        • Supports partial updates (only specified fields are changed)
        • Updates audit fields for each modified value set
        • Continues processing even if some updates fail
        • Optimized for metadata changes across many value sets

        Args:
            update_data (BulkValueSetUpdateSchema): Bulk update configuration containing:
                - updates (List[ValueSetBulkUpdateSchema]): List of value set updates:
                  * key (str): Target value set identifier
                  * status (Optional[ValueSetStatus]): New status if changing
                  * module (Optional[str]): New module if changing
                  * description (Optional[str]): New description if changing
                - updatedBy (str): User performing all updates (applied to all)

        Returns:
            BulkOperationResponseSchema: Operation results containing:
                - successful (int): Number of value sets successfully updated
                - failed (int): Number of value sets that failed to update
                - errors (List[Dict]): Error details for any failures
                - processedKeys (List[str]): Keys of successfully updated value sets

        Example:
        ```python
        from schemas.value_set_schemas_enhanced import BulkValueSetUpdateSchema, ValueSetBulkUpdateSchema

        updates = [
            ValueSetBulkUpdateSchema(
                key="set1",
                status=ValueSetStatus.ARCHIVED,
                description="Updated description"
            )
        ]

        update_data = BulkValueSetUpdateSchema(updates=updates, updatedBy="admin123")
        response = await service.bulk_update_value_sets(update_data)
        ```
        """
        operations = []
        for update in update_data.updates:
            update_fields = {
                "updatedAt": datetime.utcnow(),
                "updatedBy": update_data.updatedBy
            }

            if update.status:
                update_fields["status"] = update.status.value
            if update.module:
                update_fields["module"] = update.module
            if update.description is not None:
                update_fields["description"] = update.description

            operations.append({
                "key": update.key,
                "updates": update_fields
            })

        result = await self.repository.bulk_update(operations)

        return BulkOperationResponseSchema(
            successful=result["modified"],
            failed=len(operations) - result["modified"],
            errors=[],
            processedKeys=[op["key"] for op in operations[:result["modified"]]]
        )

    async def validate_value_set(
        self,
        validation_request: ValidateValueSetRequestSchema
    ) -> ValidationResultSchema:
        """
        Validate a value set configuration against business rules and constraints.

        LLM Instructions:
        • Use this method to validate value sets before creation or major updates
        • Check validation result before proceeding with actual operations
        • Review both errors (blocking issues) and warnings (recommendations)
        • Essential for data quality and system integrity
        • Does not modify data - only validates configuration

        Business Logic:
        • Validates item code uniqueness within the value set
        • Checks item count limits (1-500 items)
        • Ensures required English labels are present
        • Validates status values against allowed enum
        • Checks for existing key conflicts (warning only)
        • Generates performance warnings for large value sets (>100 items)

        Args:
            validation_request (ValidateValueSetRequestSchema): Validation data containing:
                - key (str): Proposed value set key
                - status (ValueSetStatus): Proposed status
                - items (List[ItemCreateSchema]): Items to validate
                - All fields that would be used in actual creation
                Complete value set structure for comprehensive validation.

        Returns:
            ValidationResultSchema: Validation results containing:
                - key (str): The validated key
                - isValid (bool): Whether validation passed (no errors)
                - errors (List[str]): Blocking validation errors
                - warnings (List[str]): Non-blocking recommendations
                Use isValid to determine if operation should proceed.

        Example:
        ```python
        from schemas.value_set_schemas_enhanced import ValidateValueSetRequestSchema

        validation_request = ValidateValueSetRequestSchema(
            key="test-validation",
            status=ValueSetStatus.ACTIVE,
            items=[ItemCreateSchema(code="001", labels={"en": "Test Item"})]
        )

        result = await service.validate_value_set(validation_request)
        if result.isValid:
            print("Validation passed!")
        else:
            print(f"Validation failed: {result.errors}")
        ```
        """
        errors = []
        warnings = []

        # Check unique item codes
        item_codes = [item.code for item in validation_request.items]
        if len(item_codes) != len(set(item_codes)):
            errors.append("Item codes must be unique within the value set")

        # Check item count
        if not (1 <= len(validation_request.items) <= 500):
            errors.append(f"Number of items must be between 1 and 500 (got {len(validation_request.items)})")

        # Check required English labels
        for item in validation_request.items:
            if not item.labels.en:
                errors.append(f"English label required for item '{item.code}'")

        # Check status value
        if validation_request.status.value not in ["active", "archived"]:
            errors.append(f"Invalid status: {validation_request.status.value}")

        # Warnings
        if len(validation_request.items) > 100:
            warnings.append(f"Large number of items ({len(validation_request.items)}) may impact performance")

        # Check if key already exists (warning only)
        if await self.repository.check_key_exists(validation_request.key):
            warnings.append(f"Value set with key '{validation_request.key}' already exists")

        return ValidationResultSchema(
            key=validation_request.key,
            isValid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    async def archive_value_set(
        self,
        archive_request: ArchiveRestoreRequestSchema
    ) -> ArchiveRestoreResponseSchema:
        """
        Archive a value set by changing its status to ARCHIVED with audit trail.

        LLM Instructions:
        • Use this method to deactivate value sets without deleting them
        • Check response.success before assuming operation completed
        • Handle cases where value set is already archived
        • Archived value sets remain in system but are typically hidden from active use
        • Use restore_value_set to reverse this operation

        Business Logic:
        • Validates value set exists before archiving
        • Prevents archiving already archived value sets
        • Changes status from any state to ARCHIVED
        • Updates audit fields: updatedAt (current time), updatedBy (from request)
        • Preserves all value set data and items
        • Includes optional reason in response message

        Args:
            archive_request (ArchiveRestoreRequestSchema): Archive request containing:
                - key (str): Unique identifier of value set to archive
                - updatedBy (str): Username/ID performing the archive operation
                - reason (Optional[str]): Optional reason for archiving
                Used for audit trail and operational transparency.

        Returns:
            ArchiveRestoreResponseSchema: Archive operation result containing:
                - success (bool): Whether operation completed successfully
                - key (str): Value set key that was processed
                - previousStatus (str): Status before archiving
                - currentStatus (str): Status after archiving ("archived" if successful)
                - message (str): Descriptive message including reason if provided

        Example:
        ```python
        from schemas.value_set_schemas_enhanced import ArchiveRestoreRequestSchema

        archive_request = ArchiveRestoreRequestSchema(
            key="obsolete-codes",
            updatedBy="admin123",
            reason="No longer used in current system"
        )

        response = await service.archive_value_set(archive_request)
        if response.success:
            print(f"Archived: {response.message}")
        ```
        """
        # Get current value set
        current = await self.repository.find_by_key(archive_request.key)
        if not current:
            return ArchiveRestoreResponseSchema(
                success=False,
                key=archive_request.key,
                previousStatus="unknown",
                currentStatus="unknown",
                message=f"Value set with key '{archive_request.key}' not found"
            )

        previous_status = current["status"]

        if previous_status == "archived":
            return ArchiveRestoreResponseSchema(
                success=False,
                key=archive_request.key,
                previousStatus=previous_status,
                currentStatus=previous_status,
                message="Value set is already archived"
            )

        # Archive the value set
        update_fields = {
            "updatedAt": datetime.utcnow(),
            "updatedBy": archive_request.updatedBy
        }

        result = await self.repository.archive(archive_request.key, update_fields)

        if result:
            return ArchiveRestoreResponseSchema(
                success=True,
                key=archive_request.key,
                previousStatus=previous_status,
                currentStatus="archived",
                message=f"Value set archived successfully{f': {archive_request.reason}' if archive_request.reason else ''}"
            )

        return ArchiveRestoreResponseSchema(
            success=False,
            key=archive_request.key,
            previousStatus=previous_status,
            currentStatus=previous_status,
            message="Failed to archive value set"
        )

    async def restore_value_set(
        self,
        restore_request: ArchiveRestoreRequestSchema
    ) -> ArchiveRestoreResponseSchema:
        """
        Restore an archived value set by changing its status back to ACTIVE.

        LLM Instructions:
        • Use this method to reactivate previously archived value sets
        • Check response.success before assuming operation completed
        • Handle cases where value set is already active
        • Restored value sets become available for normal use again
        • Use archive_value_set to reverse this operation

        Business Logic:
        • Validates value set exists before restoring
        • Prevents restoring already active value sets
        • Changes status from ARCHIVED to ACTIVE
        • Updates audit fields: updatedAt (current time), updatedBy (from request)
        • Preserves all value set data and items
        • Includes optional reason in response message

        Args:
            restore_request (ArchiveRestoreRequestSchema): Restore request containing:
                - key (str): Unique identifier of value set to restore
                - updatedBy (str): Username/ID performing the restore operation
                - reason (Optional[str]): Optional reason for restoration
                Used for audit trail and operational transparency.

        Returns:
            ArchiveRestoreResponseSchema: Restore operation result containing:
                - success (bool): Whether operation completed successfully
                - key (str): Value set key that was processed
                - previousStatus (str): Status before restoring ("archived")
                - currentStatus (str): Status after restoring ("active" if successful)
                - message (str): Descriptive message including reason if provided

        Example:
        ```python
        from schemas.value_set_schemas_enhanced import ArchiveRestoreRequestSchema

        restore_request = ArchiveRestoreRequestSchema(
            key="needed-codes",
            updatedBy="admin123",
            reason="Required for new feature implementation"
        )

        response = await service.restore_value_set(restore_request)
        if response.success:
            print(f"Restored: {response.message}")
        ```
        """
        # Get current value set
        current = await self.repository.find_by_key(restore_request.key)
        if not current:
            return ArchiveRestoreResponseSchema(
                success=False,
                key=restore_request.key,
                previousStatus="unknown",
                currentStatus="unknown",
                message=f"Value set with key '{restore_request.key}' not found"
            )

        previous_status = current["status"]

        if previous_status == "active":
            return ArchiveRestoreResponseSchema(
                success=False,
                key=restore_request.key,
                previousStatus=previous_status,
                currentStatus=previous_status,
                message="Value set is already active"
            )

        # Restore the value set
        update_fields = {
            "updatedAt": datetime.utcnow(),
            "updatedBy": restore_request.updatedBy
        }

        result = await self.repository.restore(restore_request.key, update_fields)

        if result:
            return ArchiveRestoreResponseSchema(
                success=True,
                key=restore_request.key,
                previousStatus=previous_status,
                currentStatus="active",
                message=f"Value set restored successfully{f': {restore_request.reason}' if restore_request.reason else ''}"
            )

        return ArchiveRestoreResponseSchema(
            success=False,
            key=restore_request.key,
            previousStatus=previous_status,
            currentStatus=previous_status,
            message="Failed to restore value set"
        )

    async def get_value_set_statistics(self) -> Dict[str, Any]:
        """
        Retrieve comprehensive statistics about the value set system.

        LLM Instructions:
        • Use this method to get system-wide metrics and statistics
        • Provides insights into value set usage, capacity, and distribution
        • Useful for monitoring, reporting, and system analysis
        • Returns calculated metrics in addition to raw counts
        • No parameters required - analyzes entire system

        Business Logic:
        • Retrieves base statistics from repository layer
        • Calculates additional derived metrics (capacity usage, percentages)
        • Provides total capacity based on 500-item limit per value set
        • Computes capacity utilization percentages
        • Aggregates data across all value sets in the system

        Args:
            None: No parameters required, analyzes entire system

        Returns:
            Dict[str, Any]: Comprehensive statistics dictionary containing:
                - total_value_sets (int): Total count of value sets
                - status_distribution (Dict): Count by status (active, archived)
                - module_distribution (Dict): Count by module/category
                - items_statistics (Dict): Item-related metrics including:
                  * total_items (int): Total items across all value sets
                  * average_items_per_set (float): Mean items per value set
                  * total_capacity (int): Maximum possible items (sets * 500)
                  * capacity_used_percent (float): Percentage of capacity used
                - recent_activity (Dict): Recent creation/update activity

        Example:
        ```python
        stats = await service.get_value_set_statistics()
        print(f"Total value sets: {stats['total_value_sets']}")
        print(f"Capacity used: {stats['items_statistics']['capacity_used_percent']:.1f}%")
        print(f"Active sets: {stats['status_distribution'].get('active', 0)}")
        ```
        """
        stats = await self.repository.get_statistics()

        # Add calculated statistics
        if stats["items_statistics"]:
            items_stats = stats["items_statistics"]
            stats["items_statistics"]["total_capacity"] = stats["total_value_sets"] * 500
            stats["items_statistics"]["capacity_used_percent"] = (
                (items_stats.get("total_items", 0) / (stats["total_value_sets"] * 500 * 100))
                if stats["total_value_sets"] > 0 else 0
            )

        return stats

    async def export_value_set(self, key: str, format: str = "json") -> Dict[str, Any]:
        """
        Export a value set in the specified format for external use or backup.

        LLM Instructions:
        • Use this method to extract value set data for external systems
        • Choose format based on target system requirements (JSON for APIs, CSV for spreadsheets)
        • Handle ValueError if value set not found or format unsupported
        • JSON format preserves complete structure, CSV format is simplified
        • Use for data migration, reporting, and integration scenarios

        Business Logic:
        • Retrieves complete value set data from repository
        • Formats data according to specified export format
        • JSON format: Returns complete structured data
        • CSV format: Creates tabular representation with metadata
        • Includes metadata for context and identification
        • Handles missing optional fields gracefully

        Args:
            key (str): Unique identifier of the value set to export.
                Must match an existing value set exactly.
            format (str): Export format specification (default: "json").
                Supported values: "json" (structured data), "csv" (tabular format)
                Case-sensitive format specification.

        Returns:
            Dict[str, Any]: Export result dictionary with format-specific structure:
                - JSON format: Complete value set data structure
                - CSV format: Dictionary containing:
                  * format (str): "csv"
                  * content (str): CSV content with headers
                  * metadata (Dict): Key, module, status, itemCount

        Raises:
            ValueError: If value set not found or unsupported format specified

        Example:
        ```python
        # Export as JSON
        json_data = await service.export_value_set("country-codes", "json")

        # Export as CSV
        csv_data = await service.export_value_set("country-codes", "csv")
        csv_content = csv_data["content"]
        metadata = csv_data["metadata"]
        ```
        """
        # Get value set
        value_set = await self.repository.export_value_set(key)
        if not value_set:
            raise ValueError(f"Value set with key '{key}' not found")

        if format == "json":
            return value_set

        elif format == "csv":
            # Convert to CSV format
            output = StringIO()
            writer = csv.writer(output)

            # Write header
            writer.writerow(["Code", "English Label", "Hindi Label"])

            # Write items
            for item in value_set.get("items", []):
                writer.writerow([
                    item["code"],
                    item["labels"].get("en", ""),
                    item["labels"].get("hi", "")
                ])

            return {
                "format": "csv",
                "content": output.getvalue(),
                "metadata": {
                    "key": value_set["key"],
                    "module": value_set["module"],
                    "status": value_set["status"],
                    "itemCount": len(value_set.get("items", []))
                }
            }

        else:
            raise ValueError(f"Unsupported export format: {format}")

    async def import_value_set(
        self,
        import_data: dict,
        format: str = "json",
        created_by: str = "system"
    ) -> ValueSetResponseSchema:
        """
        Import a value set from external data source with format conversion.

        LLM Instructions:
        • Use this method to import value sets from external systems or backups
        • Ensure import_data structure matches the specified format requirements
        • Handle ValueError for existing keys or format issues
        • JSON format is fully supported, CSV format is not yet implemented
        • Use for data migration, system integration, and restoration scenarios

        Business Logic:
        • Validates key uniqueness before importing
        • Sets audit fields for import tracking
        • JSON format: Direct structure validation and import
        • CSV format: Not yet implemented (raises NotImplementedError)
        • Creates complete value set with all items and metadata
        • Preserves original structure while adding audit fields

        Args:
            import_data (dict): External data to import with structure dependent on format.
                For JSON format: Complete value set dictionary with key, status, module,
                description, items array. Must have valid structure.
            format (str): Import format specification (default: "json").
                Supported values: "json" (structured data)
                Unsupported: "csv" (raises NotImplementedError)
            created_by (str): Username/ID of user performing the import (default: "system").
                Used for audit trail in createdBy field.

        Returns:
            ValueSetResponseSchema: Imported value set with generated ID and audit fields.
                Contains all imported data plus database-generated fields.

        Raises:
            ValueError: If key already exists or unsupported format specified
            NotImplementedError: If CSV format is requested

        Example:
        ```python
        import_data = {
            "key": "imported-set",
            "status": "active",
            "module": "import",
            "description": "Imported value set",
            "items": [{"code": "001", "labels": {"en": "Item 1"}}]
        }

        value_set = await service.import_value_set(import_data, "json", "admin123")
        ```
        """
        if format == "json":
            # Validate the import data
            if await self.repository.check_key_exists(import_data["key"]):
                raise ValueError(f"Value set with key '{import_data['key']}' already exists")

            # Set audit fields
            import_data["createdAt"] = datetime.utcnow()
            import_data["createdBy"] = created_by
            import_data["updatedAt"] = None
            import_data["updatedBy"] = None

            # Import to database
            result = await self.repository.import_value_set(import_data)
            return ValueSetResponseSchema(**result)

        elif format == "csv":
            # Parse CSV format
            # This would require additional parsing logic
            raise NotImplementedError("CSV import not yet implemented")

        else:
            raise ValueError(f"Unsupported import format: {format}")