"""
Value Set Library - Reusable functions for value set management
This module provides all core functions as a library that can be imported and used in other projects
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from bson import ObjectId
from pymongo import ReturnDocument
import json
import csv
from io import StringIO
import logging

# Configure logging
logger = logging.getLogger(__name__)


class ValueSetLibrary:
    """
    Main library class containing all value set management functions.
    Can be instantiated and used across different projects.
    """

    def __init__(self, database: AsyncIOMotorDatabase = None, collection_name: str = "value_sets"):
        """
        Initialize the Value Set Library.

        Args:
            database: MongoDB database instance
            collection_name: Name of the collection for value sets
        """
        self.db = database
        self.collection_name = collection_name
        self.collection: AsyncIOMotorCollection = database[collection_name] if database else None

    def set_database(self, database: AsyncIOMotorDatabase, collection_name: str = "value_sets"):
        """
        Set or update the database connection.

        Args:
            database: MongoDB database instance
            collection_name: Name of the collection
        """
        self.db = database
        self.collection_name = collection_name
        self.collection = database[collection_name]

    # ==================== CREATE OPERATIONS ====================

    async def create_value_set(
        self,
        key: str,
        status: str,
        module: str,
        items: List[Dict],
        created_by: str,
        description: Optional[str] = None,
        created_at: Optional[datetime] = None
    ) -> Dict:
        """
        Create a new value set.

        Args:
            key: Unique identifier for the value set
            status: Status (active/archived)
            module: Module name
            items: List of items with code and labels
            created_by: User creating the value set
            description: Optional description
            created_at: Optional creation timestamp

        Returns:
            Created value set document

        Raises:
            ValueError: If key already exists or validation fails
        """
        # Check if key already exists
        if await self.check_key_exists(key):
            raise ValueError(f"Value set with key '{key}' already exists")

        # Validate unique item codes
        item_codes = [item.get('code') for item in items]
        if len(item_codes) != len(set(item_codes)):
            raise ValueError("Item codes must be unique within the value set")

        # Validate item count
        if not (1 <= len(items) <= 500):
            raise ValueError("Number of items must be between 1 and 500")

        # Prepare document
        document = {
            "key": key,
            "status": status,
            "module": module,
            "description": description,
            "items": items,
            "createdAt": created_at or datetime.utcnow(),
            "createdBy": created_by,
            "updatedAt": None,
            "updatedBy": None
        }

        # Insert into database
        result = await self.collection.insert_one(document)
        document["_id"] = str(result.inserted_id)
        return document

    async def bulk_create_value_sets(
        self,
        value_sets: List[Dict],
        skip_existing: bool = True
    ) -> Dict:
        """
        Create multiple value sets in bulk.

        Args:
            value_sets: List of value set documents
            skip_existing: Skip if key already exists

        Returns:
            Bulk operation results
        """
        created = []
        failed = []
        skipped = []

        for value_set in value_sets:
            try:
                if await self.check_key_exists(value_set['key']):
                    if skip_existing:
                        skipped.append(value_set['key'])
                        continue
                    else:
                        failed.append({
                            "key": value_set['key'],
                            "error": "Key already exists"
                        })
                        continue

                result = await self.create_value_set(
                    key=value_set['key'],
                    status=value_set.get('status', 'active'),
                    module=value_set.get('module', 'Core'),
                    items=value_set.get('items', []),
                    created_by=value_set.get('createdBy', 'system'),
                    description=value_set.get('description'),
                    created_at=value_set.get('createdAt')
                )
                created.append(result['key'])
            except Exception as e:
                failed.append({
                    "key": value_set.get('key', 'unknown'),
                    "error": str(e)
                })

        return {
            "created": created,
            "failed": failed,
            "skipped": skipped,
            "summary": {
                "total": len(value_sets),
                "created": len(created),
                "failed": len(failed),
                "skipped": len(skipped)
            }
        }

    # ==================== READ OPERATIONS ====================

    async def get_value_set_by_key(self, key: str) -> Optional[Dict]:
        """
        Get a value set by its unique key.

        Args:
            key: Value set key

        Returns:
            Value set document or None
        """
        document = await self.collection.find_one({"key": key})
        if document:
            document["_id"] = str(document["_id"])
        return document

    async def get_value_set_by_id(self, value_set_id: str) -> Optional[Dict]:
        """
        Get a value set by MongoDB ObjectId.

        Args:
            value_set_id: MongoDB ObjectId as string

        Returns:
            Value set document or None
        """
        try:
            document = await self.collection.find_one({"_id": ObjectId(value_set_id)})
            if document:
                document["_id"] = str(document["_id"])
            return document
        except:
            return None

    async def list_value_sets(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        module: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "key",
        sort_order: str = "asc"
    ) -> Tuple[List[Dict], int]:
        """
        List value sets with pagination and filtering.

        Args:
            skip: Number of records to skip
            limit: Maximum records to return
            status: Filter by status
            module: Filter by module
            search: Search in key and description
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)

        Returns:
            Tuple of (value sets list, total count)
        """
        # Build filter query
        filter_query = {}
        if status:
            filter_query["status"] = status
        if module:
            filter_query["module"] = module
        if search:
            filter_query["$or"] = [
                {"key": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}}
            ]

        # Get total count
        total_count = await self.collection.count_documents(filter_query)

        # Build sort
        sort_direction = 1 if sort_order == "asc" else -1
        sort = [(sort_by, sort_direction)]

        # Execute query
        cursor = self.collection.find(filter_query).sort(sort).skip(skip).limit(limit)
        documents = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            documents.append(doc)

        return documents, total_count

    async def check_key_exists(self, key: str) -> bool:
        """
        Check if a value set key already exists.

        Args:
            key: Value set key to check

        Returns:
            True if exists, False otherwise
        """
        count = await self.collection.count_documents({"key": key})
        return count > 0

    # ==================== UPDATE OPERATIONS ====================

    async def update_value_set(
        self,
        key: str,
        updates: Dict,
        updated_by: str,
        updated_at: Optional[datetime] = None
    ) -> Optional[Dict]:
        """
        Update a value set by key.

        Args:
            key: Value set key
            updates: Fields to update
            updated_by: User performing update
            updated_at: Optional update timestamp

        Returns:
            Updated document or None
        """
        # Add audit fields
        updates["updatedBy"] = updated_by
        updates["updatedAt"] = updated_at or datetime.utcnow()

        # Remove None values
        updates = {k: v for k, v in updates.items() if v is not None}

        result = await self.collection.find_one_and_update(
            {"key": key},
            {"$set": updates},
            return_document=ReturnDocument.AFTER
        )
        if result:
            result["_id"] = str(result["_id"])
        return result

    async def bulk_update_value_sets(
        self,
        updates: List[Dict],
        updated_by: str
    ) -> Dict:
        """
        Update multiple value sets in bulk.

        Args:
            updates: List of update operations (each with 'key' and 'updates')
            updated_by: User performing updates

        Returns:
            Bulk update results
        """
        updated = []
        failed = []

        for update_op in updates:
            try:
                result = await self.update_value_set(
                    key=update_op['key'],
                    updates=update_op['updates'],
                    updated_by=updated_by
                )
                if result:
                    updated.append(update_op['key'])
                else:
                    failed.append({
                        "key": update_op['key'],
                        "error": "Value set not found"
                    })
            except Exception as e:
                failed.append({
                    "key": update_op['key'],
                    "error": str(e)
                })

        return {
            "updated": updated,
            "failed": failed,
            "summary": {
                "total": len(updates),
                "updated": len(updated),
                "failed": len(failed)
            }
        }

    # ==================== ITEM OPERATIONS ====================

    async def add_item_to_value_set(
        self,
        key: str,
        item: Dict,
        updated_by: str
    ) -> Optional[Dict]:
        """
        Add a single item to a value set.

        Args:
            key: Value set key
            item: Item to add (with code and labels)
            updated_by: User adding the item

        Returns:
            Updated value set or None
        """
        # Get current value set
        value_set = await self.get_value_set_by_key(key)
        if not value_set:
            raise ValueError(f"Value set with key '{key}' not found")

        # Check if item code already exists
        existing_codes = [i['code'] for i in value_set.get('items', [])]
        if item['code'] in existing_codes:
            raise ValueError(f"Item with code '{item['code']}' already exists")

        # Add item
        result = await self.collection.find_one_and_update(
            {"key": key},
            {
                "$push": {"items": item},
                "$set": {
                    "updatedBy": updated_by,
                    "updatedAt": datetime.utcnow()
                }
            },
            return_document=ReturnDocument.AFTER
        )

        if result:
            result["_id"] = str(result["_id"])
        return result

    async def bulk_add_items(
        self,
        key: str,
        items: List[Dict],
        updated_by: str
    ) -> Optional[Dict]:
        """
        Add multiple items to a value set.

        Args:
            key: Value set key
            items: List of items to add
            updated_by: User adding items

        Returns:
            Updated value set or None
        """
        # Get current value set
        value_set = await self.get_value_set_by_key(key)
        if not value_set:
            raise ValueError(f"Value set with key '{key}' not found")

        # Check for duplicate codes
        existing_codes = [i['code'] for i in value_set.get('items', [])]
        new_codes = [i['code'] for i in items]

        # Check for duplicates within new items
        if len(new_codes) != len(set(new_codes)):
            raise ValueError("Duplicate codes in items to add")

        # Check against existing codes
        duplicates = set(new_codes) & set(existing_codes)
        if duplicates:
            raise ValueError(f"Items with codes {duplicates} already exist")

        # Check total count
        total_items = len(existing_codes) + len(items)
        if total_items > 500:
            raise ValueError(f"Cannot add {len(items)} items. Maximum 500 items allowed, current: {len(existing_codes)}")

        # Add all items
        result = await self.collection.find_one_and_update(
            {"key": key},
            {
                "$push": {"items": {"$each": items}},
                "$set": {
                    "updatedBy": updated_by,
                    "updatedAt": datetime.utcnow()
                }
            },
            return_document=ReturnDocument.AFTER
        )

        if result:
            result["_id"] = str(result["_id"])
        return result

    async def update_item_in_value_set(
        self,
        key: str,
        item_code: str,
        updates: Dict,
        updated_by: str
    ) -> Optional[Dict]:
        """
        Update a specific item in a value set.

        Args:
            key: Value set key
            item_code: Code of item to update
            updates: Updates for the item
            updated_by: User updating the item

        Returns:
            Updated value set or None
        """
        # Build update query
        set_updates = {}
        for field, value in updates.items():
            if field == 'labels':
                for lang, label in value.items():
                    set_updates[f"items.$.labels.{lang}"] = label
            else:
                set_updates[f"items.$.{field}"] = value

        set_updates["updatedBy"] = updated_by
        set_updates["updatedAt"] = datetime.utcnow()

        result = await self.collection.find_one_and_update(
            {"key": key, "items.code": item_code},
            {"$set": set_updates},
            return_document=ReturnDocument.AFTER
        )

        if result:
            result["_id"] = str(result["_id"])
        return result

    async def remove_item_from_value_set(
        self,
        key: str,
        item_code: str,
        updated_by: str
    ) -> Optional[Dict]:
        """
        Remove an item from a value set.

        Args:
            key: Value set key
            item_code: Code of item to remove
            updated_by: User removing the item

        Returns:
            Updated value set or None
        """
        result = await self.collection.find_one_and_update(
            {"key": key},
            {
                "$pull": {"items": {"code": item_code}},
                "$set": {
                    "updatedBy": updated_by,
                    "updatedAt": datetime.utcnow()
                }
            },
            return_document=ReturnDocument.AFTER
        )

        if result:
            result["_id"] = str(result["_id"])
        return result

    async def replace_item_code(
        self,
        key: str,
        old_code: str,
        new_code: str,
        new_labels: Optional[Dict] = None,
        updated_by: str = None
    ) -> Optional[Dict]:
        """
        Replace an item's code and optionally its labels.

        Args:
            key: Value set key
            old_code: Current item code
            new_code: New item code
            new_labels: Optional new labels
            updated_by: User performing replacement

        Returns:
            Updated value set or None
        """
        # Get value set
        value_set = await self.get_value_set_by_key(key)
        if not value_set:
            return None

        # Check if new code already exists
        items = value_set.get('items', [])
        if new_code != old_code and any(i['code'] == new_code for i in items):
            raise ValueError(f"Item with code '{new_code}' already exists")

        # Find and update item
        for i, item in enumerate(items):
            if item['code'] == old_code:
                items[i]['code'] = new_code
                if new_labels:
                    items[i]['labels'] = new_labels
                break
        else:
            raise ValueError(f"Item with code '{old_code}' not found")

        # Update document
        result = await self.collection.find_one_and_update(
            {"key": key},
            {
                "$set": {
                    "items": items,
                    "updatedBy": updated_by,
                    "updatedAt": datetime.utcnow()
                }
            },
            return_document=ReturnDocument.AFTER
        )

        if result:
            result["_id"] = str(result["_id"])
        return result

    # ==================== ARCHIVE/RESTORE OPERATIONS ====================

    async def archive_value_set(
        self,
        key: str,
        reason: str,
        archived_by: str
    ) -> Optional[Dict]:
        """
        Archive a value set.

        Args:
            key: Value set key
            reason: Reason for archiving
            archived_by: User archiving

        Returns:
            Archived value set or None
        """
        result = await self.collection.find_one_and_update(
            {"key": key},
            {
                "$set": {
                    "status": "archived",
                    "archiveReason": reason,
                    "archivedBy": archived_by,
                    "archivedAt": datetime.utcnow(),
                    "updatedBy": archived_by,
                    "updatedAt": datetime.utcnow()
                }
            },
            return_document=ReturnDocument.AFTER
        )

        if result:
            result["_id"] = str(result["_id"])
        return result

    async def restore_value_set(
        self,
        key: str,
        reason: str,
        restored_by: str
    ) -> Optional[Dict]:
        """
        Restore an archived value set.

        Args:
            key: Value set key
            reason: Reason for restoring
            restored_by: User restoring

        Returns:
            Restored value set or None
        """
        result = await self.collection.find_one_and_update(
            {"key": key},
            {
                "$set": {
                    "status": "active",
                    "restoreReason": reason,
                    "restoredBy": restored_by,
                    "restoredAt": datetime.utcnow(),
                    "updatedBy": restored_by,
                    "updatedAt": datetime.utcnow()
                },
                "$unset": {
                    "archiveReason": "",
                    "archivedBy": "",
                    "archivedAt": ""
                }
            },
            return_document=ReturnDocument.AFTER
        )

        if result:
            result["_id"] = str(result["_id"])
        return result

    async def bulk_archive(
        self,
        keys: List[str],
        reason: str,
        archived_by: str
    ) -> Dict:
        """
        Archive multiple value sets.

        Args:
            keys: List of value set keys
            reason: Reason for archiving
            archived_by: User archiving

        Returns:
            Bulk operation results
        """
        result = await self.collection.update_many(
            {"key": {"$in": keys}},
            {
                "$set": {
                    "status": "archived",
                    "archiveReason": reason,
                    "archivedBy": archived_by,
                    "archivedAt": datetime.utcnow(),
                    "updatedBy": archived_by,
                    "updatedAt": datetime.utcnow()
                }
            }
        )

        return {
            "matched": result.matched_count,
            "modified": result.modified_count,
            "keys": keys
        }

    # ==================== SEARCH OPERATIONS ====================

    async def search_items(
        self,
        query: str,
        language_code: str = "en",
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Dict], int]:
        """
        Search for items across all value sets.

        Args:
            query: Search query
            language_code: Language to search in
            skip: Pagination skip
            limit: Pagination limit

        Returns:
            Tuple of (search results, total count)
        """
        # Build search pipeline
        pipeline = [
            {"$match": {"status": "active"}},
            {"$unwind": "$items"},
            {"$match": {
                f"items.labels.{language_code}": {"$regex": query, "$options": "i"}
            }},
            {"$group": {
                "_id": "$key",
                "key": {"$first": "$key"},
                "module": {"$first": "$module"},
                "description": {"$first": "$description"},
                "items": {"$push": "$items"}
            }},
            {"$facet": {
                "data": [
                    {"$skip": skip},
                    {"$limit": limit}
                ],
                "totalCount": [
                    {"$count": "count"}
                ]
            }}
        ]

        result = await self.collection.aggregate(pipeline).to_list(None)

        if result and result[0]:
            data = result[0].get('data', [])
            total = result[0].get('totalCount', [])
            total_count = total[0]['count'] if total else 0
            return data, total_count

        return [], 0

    async def search_by_label(
        self,
        label_text: str,
        language_code: str = "en",
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Dict], int]:
        """
        Search value sets by label text.

        Args:
            label_text: Label text to search
            language_code: Language code
            skip: Pagination skip
            limit: Pagination limit

        Returns:
            Tuple of (value sets, total count)
        """
        filter_query = {
            "status": "active",
            f"items.labels.{language_code}": {"$regex": label_text, "$options": "i"}
        }

        total_count = await self.collection.count_documents(filter_query)

        cursor = self.collection.find(filter_query).skip(skip).limit(limit)
        documents = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            documents.append(doc)

        return documents, total_count

    async def get_items_by_codes(
        self,
        key: str,
        codes: List[str]
    ) -> List[Dict]:
        """
        Get specific items from a value set by their codes.

        Args:
            key: Value set key
            codes: List of item codes

        Returns:
            List of matching items
        """
        value_set = await self.get_value_set_by_key(key)
        if not value_set:
            return []

        items = value_set.get('items', [])
        return [item for item in items if item['code'] in codes]

    # ==================== VALIDATION OPERATIONS ====================

    async def validate_value_set(self, value_set_data: Dict) -> Dict:
        """
        Validate a value set structure.

        Args:
            value_set_data: Value set data to validate

        Returns:
            Validation result with errors if any
        """
        errors = []
        warnings = []

        # Required fields
        required_fields = ['key', 'status', 'items']
        for field in required_fields:
            if field not in value_set_data:
                errors.append(f"Missing required field: {field}")

        if errors:
            return {"valid": False, "errors": errors, "warnings": warnings}

        # Validate key
        key = value_set_data.get('key', '')
        if not key or len(key) > 100:
            errors.append("Key must be between 1 and 100 characters")

        # Validate status
        status = value_set_data.get('status', '')
        if status not in ['active', 'archived']:
            errors.append("Status must be 'active' or 'archived'")

        # Validate items
        items = value_set_data.get('items', [])
        if not items:
            errors.append("At least one item is required")
        elif len(items) > 500:
            errors.append("Maximum 500 items allowed")
        else:
            # Check item structure
            item_codes = []
            for i, item in enumerate(items):
                if 'code' not in item:
                    errors.append(f"Item {i} missing code")
                else:
                    item_codes.append(item['code'])

                if 'labels' not in item:
                    errors.append(f"Item {i} missing labels")
                elif 'en' not in item.get('labels', {}):
                    errors.append(f"Item {i} missing English label")

            # Check for duplicate codes
            if len(item_codes) != len(set(item_codes)):
                errors.append("Duplicate item codes found")

        # Warnings
        if not value_set_data.get('description'):
            warnings.append("No description provided")

        if not value_set_data.get('module'):
            warnings.append("No module specified, will default to 'Core'")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    async def validate_item(self, item: Dict) -> Dict:
        """
        Validate a single item.

        Args:
            item: Item to validate

        Returns:
            Validation result
        """
        errors = []

        if 'code' not in item:
            errors.append("Item missing code")
        elif not item['code'] or len(item['code']) > 50:
            errors.append("Code must be between 1 and 50 characters")

        if 'labels' not in item:
            errors.append("Item missing labels")
        elif 'en' not in item.get('labels', {}):
            errors.append("Item missing English label")

        return {
            "valid": len(errors) == 0,
            "errors": errors
        }

    # ==================== EXPORT/IMPORT OPERATIONS ====================

    async def export_value_set(
        self,
        key: str,
        format: str = "json"
    ) -> Any:
        """
        Export a value set in specified format.

        Args:
            key: Value set key
            format: Export format (json/csv)

        Returns:
            Exported data in specified format
        """
        value_set = await self.get_value_set_by_key(key)
        if not value_set:
            return None

        # Remove MongoDB _id for export
        if '_id' in value_set:
            del value_set['_id']

        if format == "json":
            return json.dumps(value_set, default=str, indent=2)

        elif format == "csv":
            output = StringIO()
            writer = csv.writer(output)

            # Write headers
            writer.writerow([
                'Code', 'English Label', 'Hindi Label',
                'Key', 'Module', 'Status', 'Description'
            ])

            # Write items
            for item in value_set.get('items', []):
                writer.writerow([
                    item['code'],
                    item['labels'].get('en', ''),
                    item['labels'].get('hi', ''),
                    value_set['key'],
                    value_set.get('module', ''),
                    value_set.get('status', ''),
                    value_set.get('description', '')
                ])

            return output.getvalue()

        else:
            raise ValueError(f"Unsupported export format: {format}")

    async def export_all_value_sets(
        self,
        format: str = "json",
        status: Optional[str] = None
    ) -> Any:
        """
        Export all value sets.

        Args:
            format: Export format
            status: Optional status filter

        Returns:
            Exported data
        """
        filter_query = {}
        if status:
            filter_query["status"] = status

        cursor = self.collection.find(filter_query)
        value_sets = []
        async for doc in cursor:
            if '_id' in doc:
                del doc['_id']
            value_sets.append(doc)

        if format == "json":
            return json.dumps(value_sets, default=str, indent=2)
        else:
            raise ValueError(f"Unsupported format for bulk export: {format}")

    async def import_value_set(
        self,
        data: str,
        format: str = "json",
        created_by: str = "import"
    ) -> Dict:
        """
        Import a value set from data.

        Args:
            data: Import data
            format: Data format
            created_by: User performing import

        Returns:
            Import result
        """
        if format == "json":
            value_set_data = json.loads(data)

            # Add audit fields
            value_set_data['createdBy'] = created_by
            value_set_data['createdAt'] = datetime.utcnow()

            # Validate
            validation = await self.validate_value_set(value_set_data)
            if not validation['valid']:
                raise ValueError(f"Validation failed: {validation['errors']}")

            # Create value set
            result = await self.create_value_set(
                key=value_set_data['key'],
                status=value_set_data.get('status', 'active'),
                module=value_set_data.get('module', 'Core'),
                items=value_set_data['items'],
                created_by=created_by,
                description=value_set_data.get('description')
            )

            return {"success": True, "key": result['key']}

        else:
            raise ValueError(f"Unsupported import format: {format}")

    # ==================== STATISTICS OPERATIONS ====================

    async def get_statistics(self) -> Dict:
        """
        Get value set statistics.

        Returns:
            Statistics dictionary
        """
        pipeline = [
            {"$facet": {
                "statusCounts": [
                    {"$group": {
                        "_id": "$status",
                        "count": {"$sum": 1}
                    }}
                ],
                "moduleCounts": [
                    {"$group": {
                        "_id": "$module",
                        "count": {"$sum": 1}
                    }}
                ],
                "totalItems": [
                    {"$unwind": "$items"},
                    {"$count": "count"}
                ],
                "averageItems": [
                    {"$project": {
                        "itemCount": {"$size": "$items"}
                    }},
                    {"$group": {
                        "_id": None,
                        "average": {"$avg": "$itemCount"}
                    }}
                ]
            }}
        ]

        result = await self.collection.aggregate(pipeline).to_list(None)

        if result and result[0]:
            data = result[0]

            # Process status counts
            status_counts = {}
            for item in data.get('statusCounts', []):
                status_counts[item['_id']] = item['count']

            # Process module counts
            module_counts = {}
            for item in data.get('moduleCounts', []):
                module_counts[item['_id']] = item['count']

            # Get total items
            total_items = data.get('totalItems', [])
            total_items_count = total_items[0]['count'] if total_items else 0

            # Get average items
            avg_items = data.get('averageItems', [])
            avg_items_count = avg_items[0]['average'] if avg_items else 0

            return {
                "totalValueSets": sum(status_counts.values()),
                "statusCounts": status_counts,
                "moduleCounts": module_counts,
                "totalItems": total_items_count,
                "averageItemsPerSet": round(avg_items_count, 2)
            }

        return {
            "totalValueSets": 0,
            "statusCounts": {},
            "moduleCounts": {},
            "totalItems": 0,
            "averageItemsPerSet": 0
        }

    async def get_module_statistics(self, module: str) -> Dict:
        """
        Get statistics for a specific module.

        Args:
            module: Module name

        Returns:
            Module statistics
        """
        filter_query = {"module": module}

        total = await self.collection.count_documents(filter_query)
        active = await self.collection.count_documents({**filter_query, "status": "active"})
        archived = await self.collection.count_documents({**filter_query, "status": "archived"})

        # Get item count
        pipeline = [
            {"$match": filter_query},
            {"$unwind": "$items"},
            {"$count": "count"}
        ]
        result = await self.collection.aggregate(pipeline).to_list(None)
        item_count = result[0]['count'] if result else 0

        return {
            "module": module,
            "totalValueSets": total,
            "activeValueSets": active,
            "archivedValueSets": archived,
            "totalItems": item_count,
            "averageItemsPerSet": round(item_count / total, 2) if total > 0 else 0
        }

    # ==================== DELETE OPERATIONS ====================

    async def delete_value_set(self, key: str) -> bool:
        """
        Permanently delete a value set.

        Args:
            key: Value set key

        Returns:
            True if deleted, False otherwise
        """
        result = await self.collection.delete_one({"key": key})
        return result.deleted_count > 0

    async def bulk_delete(self, keys: List[str]) -> Dict:
        """
        Delete multiple value sets.

        Args:
            keys: List of value set keys

        Returns:
            Deletion results
        """
        result = await self.collection.delete_many({"key": {"$in": keys}})
        return {
            "requested": len(keys),
            "deleted": result.deleted_count
        }


# ==================== STANDALONE FUNCTIONS ====================
# These can be imported and used directly without instantiating the class

def create_value_set_document(
    key: str,
    status: str,
    module: str,
    items: List[Dict],
    created_by: str,
    description: Optional[str] = None,
    created_at: Optional[datetime] = None
) -> Dict:
    """
    Create a value set document structure.

    Args:
        key: Unique identifier
        status: Status (active/archived)
        module: Module name
        items: List of items
        created_by: Creator
        description: Optional description
        created_at: Optional timestamp

    Returns:
        Value set document
    """
    return {
        "key": key,
        "status": status,
        "module": module,
        "description": description,
        "items": items,
        "createdAt": created_at or datetime.utcnow(),
        "createdBy": created_by,
        "updatedAt": None,
        "updatedBy": None
    }


def validate_item_structure(item: Dict) -> Tuple[bool, List[str]]:
    """
    Validate an item's structure.

    Args:
        item: Item to validate

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    if 'code' not in item:
        errors.append("Item missing code")
    elif not item['code'] or len(item['code']) > 50:
        errors.append("Code must be between 1 and 50 characters")

    if 'labels' not in item:
        errors.append("Item missing labels")
    elif 'en' not in item.get('labels', {}):
        errors.append("Item missing English label")

    return len(errors) == 0, errors


def validate_value_set_structure(value_set: Dict) -> Tuple[bool, List[str]]:
    """
    Validate a value set's structure.

    Args:
        value_set: Value set to validate

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    # Required fields
    required_fields = ['key', 'status', 'items']
    for field in required_fields:
        if field not in value_set:
            errors.append(f"Missing required field: {field}")

    if 'key' in value_set:
        if not value_set['key'] or len(value_set['key']) > 100:
            errors.append("Key must be between 1 and 100 characters")

    if 'status' in value_set:
        if value_set['status'] not in ['active', 'archived']:
            errors.append("Status must be 'active' or 'archived'")

    if 'items' in value_set:
        items = value_set['items']
        if not items:
            errors.append("At least one item is required")
        elif len(items) > 500:
            errors.append("Maximum 500 items allowed")
        else:
            item_codes = []
            for i, item in enumerate(items):
                is_valid, item_errors = validate_item_structure(item)
                if not is_valid:
                    errors.extend([f"Item {i}: {e}" for e in item_errors])
                if 'code' in item:
                    item_codes.append(item['code'])

            if len(item_codes) != len(set(item_codes)):
                errors.append("Duplicate item codes found")

    return len(errors) == 0, errors


def export_to_json(value_set: Dict) -> str:
    """
    Export a value set to JSON.

    Args:
        value_set: Value set document

    Returns:
        JSON string
    """
    # Remove MongoDB _id if present
    export_data = value_set.copy()
    if '_id' in export_data:
        del export_data['_id']
    return json.dumps(export_data, default=str, indent=2)


def export_to_csv(value_set: Dict) -> str:
    """
    Export a value set to CSV.

    Args:
        value_set: Value set document

    Returns:
        CSV string
    """
    output = StringIO()
    writer = csv.writer(output)

    # Write headers
    writer.writerow([
        'Code', 'English Label', 'Hindi Label',
        'Key', 'Module', 'Status', 'Description'
    ])

    # Write items
    for item in value_set.get('items', []):
        writer.writerow([
            item['code'],
            item['labels'].get('en', ''),
            item['labels'].get('hi', ''),
            value_set['key'],
            value_set.get('module', ''),
            value_set.get('status', ''),
            value_set.get('description', '')
        ])

    return output.getvalue()