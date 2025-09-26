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
    """Service class for value set business logic."""

    def __init__(self, repository: ValueSetRepository):
        """Initialize service with repository."""
        self.repository = repository

    async def create_value_set(self, create_data: ValueSetCreateSchema) -> ValueSetResponseSchema:
        """
        Create a new value set with validation.

        Args:
            create_data: Value set creation data

        Returns:
            Created value set

        Raises:
            ValueError: If key already exists or validation fails
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
        Get a value set by its unique key.

        Args:
            key: Value set key

        Returns:
            Value set or None if not found
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
        Update an existing value set.

        Args:
            key: Value set key
            update_data: Update data

        Returns:
            Updated value set or None

        Raises:
            ValueError: If validation fails
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
        List value sets with filtering and pagination.

        Args:
            query_params: Query parameters

        Returns:
            Paginated response
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
        Search for items within value sets.

        Args:
            search_params: Search parameters

        Returns:
            List of search results
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
        Search value sets by label text.

        Args:
            label_text: Text to search
            language_code: Language code
            status: Optional status filter

        Returns:
            List of matching value sets
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
        Add a new item to an existing value set.

        Args:
            key: Value set key
            request: Add item request

        Returns:
            Updated value set or None

        Raises:
            ValueError: If item code already exists or limit exceeded
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
        Update an existing item in a value set.

        Args:
            key: Value set key
            request: Update item request

        Returns:
            Updated value set or None

        Raises:
            ValueError: If new code conflicts with existing
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
        Bulk add items to a value set.

        Args:
            key: Value set key
            items: List of items to add
            updated_by: User performing operation

        Returns:
            Bulk operation response
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
        Bulk update items across value sets.

        Args:
            updates: Bulk item update schema

        Returns:
            Bulk operation response
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
        Replace an item's code and optionally its labels.

        Args:
            key: Value set key
            replace_request: Replace request

        Returns:
            Updated value set or None
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
        Bulk import multiple value sets.

        Args:
            import_data: Bulk value set creation data

        Returns:
            Bulk operation response
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
        Bulk update multiple value sets.

        Args:
            update_data: Bulk update data

        Returns:
            Bulk operation response
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
        Validate a value set configuration.

        Args:
            validation_request: Validation request

        Returns:
            Validation result
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
        Archive a value set.

        Args:
            archive_request: Archive request

        Returns:
            Archive response
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
        Restore an archived value set.

        Args:
            restore_request: Restore request

        Returns:
            Restore response
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
        Get statistics about value sets.

        Returns:
            Statistics dictionary
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
        Export a value set in specified format.

        Args:
            key: Value set key
            format: Export format (json, csv)

        Returns:
            Exported data dictionary
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
        Import a value set from external source.

        Args:
            import_data: Import data
            format: Import format
            created_by: User importing the value set

        Returns:
            Imported value set
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