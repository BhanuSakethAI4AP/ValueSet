"""
Repository layer for Value Set operations.
Handles all database operations without business logic.
File: /repositories/value_set_repository.py
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from bson import ObjectId
from pymongo import ReturnDocument
import pymongo


class ValueSetRepository:
    """Repository class for value set database operations."""

    def __init__(self, database: AsyncIOMotorDatabase):
        """
        Initialize the ValueSetRepository with a MongoDB database connection.

        LLM Instructions:
        • Use this constructor when creating a new repository instance
        • Always pass a valid AsyncIOMotorDatabase instance
        • Call this before any database operations

        Business Logic:
        • Sets up the connection to the 'value_sets' collection
        • Stores database reference for all repository operations
        • No validation is performed on the database parameter

        Args:
            database (AsyncIOMotorDatabase): Connected MongoDB database instance.
                Must be a valid Motor async database object with access to the
                'value_sets' collection.

        Returns:
            None: Constructor does not return a value.

        Example:
        ```python
        from motor.motor_asyncio import AsyncIOMotorClient

        client = AsyncIOMotorClient("mongodb://localhost:27017")
        database = client.value_sets_db
        repository = ValueSetRepository(database)
        ```
        """
        self.db = database
        self.collection: AsyncIOMotorCollection = database.value_sets

    async def create(self, value_set_data: dict) -> dict:
        """
        Create a new value set document in the MongoDB collection.

        LLM Instructions:
        • Use this when creating a brand new value set
        • Call this after validating the value set data structure
        • Use this for initial value set creation, not updates

        Business Logic:
        • Inserts the document into the value_sets collection
        • Automatically generates a MongoDB ObjectId
        • Converts ObjectId to string for JSON serialization
        • Does not validate data structure or check for duplicates

        Args:
            value_set_data (dict): Complete value set document to create.
                Must contain required fields like 'key', 'module', 'status'.
                Should include 'items' array, 'createdAt', 'createdBy', etc.
                Example structure: {
                    'key': 'COUNTRY_CODES',
                    'module': 'core',
                    'status': 'active',
                    'items': [],
                    'createdAt': datetime.utcnow(),
                    'createdBy': 'user_id'
                }

        Returns:
            dict: The created value set document with '_id' field added as string.
                Original data is modified in-place to include the new _id.

        Example:
        ```python
        new_value_set = {
            'key': 'PRIORITY_LEVELS',
            'module': 'task_management',
            'status': 'active',
            'items': [],
            'createdAt': datetime.utcnow(),
            'createdBy': 'admin'
        }

        created = await repository.create(new_value_set)
        print(created['_id'])  # MongoDB ObjectId as string
        ```
        """
        result = await self.collection.insert_one(value_set_data)
        value_set_data["_id"] = str(result.inserted_id)
        return value_set_data

    async def find_by_key(self, key: str) -> Optional[dict]:
        """
        Retrieve a value set document using its unique key identifier.

        LLM Instructions:
        • Use this when you need to find a specific value set by its business key
        • Prefer this over find_by_id when you have the key string
        • Use this for validation, updates, or data retrieval operations

        Business Logic:
        • Searches for exact match on the 'key' field
        • Key field should be unique across all value sets
        • Converts MongoDB ObjectId to string for JSON compatibility
        • Returns None if no matching document found

        Args:
            key (str): The unique business identifier for the value set.
                Case-sensitive string, typically in UPPER_SNAKE_CASE format.
                Examples: 'COUNTRY_CODES', 'USER_ROLES', 'PRIORITY_LEVELS'.

        Returns:
            Optional[dict]: The complete value set document with '_id' as string,
                or None if no document matches the key.

        Example:
        ```python
        value_set = await repository.find_by_key('COUNTRY_CODES')
        if value_set:
            print(f"Found {len(value_set['items'])} items")
            print(f"Status: {value_set['status']}")
        else:
            print("Value set not found")
        ```
        """
        document = await self.collection.find_one({"key": key})
        if document:
            document["_id"] = str(document["_id"])
        return document

    async def find_by_id(self, value_set_id: str) -> Optional[dict]:
        """
        Retrieve a value set document using its MongoDB ObjectId.

        LLM Instructions:
        • Use this when you have the MongoDB document ID
        • Use this for direct document access from database references
        • Prefer find_by_key when you have the business key instead

        Business Logic:
        • Converts string ID to MongoDB ObjectId for query
        • Handles invalid ObjectId formats gracefully
        • Returns None for any exception (invalid ID format, not found)
        • Converts ObjectId back to string in response

        Args:
            value_set_id (str): MongoDB ObjectId as a 24-character hexadecimal string.
                Must be a valid ObjectId format (e.g., '507f1f77bcf86cd799439011').
                Invalid formats will return None instead of raising exceptions.

        Returns:
            Optional[dict]: The complete value set document with '_id' as string,
                or None if document not found or invalid ID format provided.

        Example:
        ```python
        doc_id = '507f1f77bcf86cd799439011'
        value_set = await repository.find_by_id(doc_id)
        if value_set:
            print(f"Key: {value_set['key']}")
        else:
            print("Document not found or invalid ID")
        ```
        """
        try:
            document = await self.collection.find_one({"_id": ObjectId(value_set_id)})
            if document:
                document["_id"] = str(document["_id"])
            return document
        except:
            return None

    async def update_by_key(self, key: str, update_data: dict) -> Optional[dict]:
        """
        Update specific fields of a value set document identified by key.

        LLM Instructions:
        • Use this for updating value set metadata (status, description, etc.)
        • Use this for bulk field updates rather than individual item changes
        • Call this when you need the updated document returned immediately

        Business Logic:
        • Uses MongoDB $set operator to update only specified fields
        • Returns the document state after the update (not before)
        • Does not create a new document if key doesn't exist
        • Preserves all existing fields not mentioned in update_data

        Args:
            key (str): Unique value set key to identify the document.
                Must match exactly (case-sensitive).
            update_data (dict): Fields and values to update in the document.
                Common fields: 'status', 'updatedAt', 'updatedBy', 'description'.
                Example: {
                    'status': 'inactive',
                    'updatedAt': datetime.utcnow(),
                    'updatedBy': 'admin_user'
                }

        Returns:
            Optional[dict]: The complete updated document with '_id' as string,
                or None if no document matches the key.

        Example:
        ```python
        updates = {
            'status': 'archived',
            'updatedAt': datetime.utcnow(),
            'updatedBy': 'system_admin'
        }

        updated_doc = await repository.update_by_key('OLD_CODES', updates)
        if updated_doc:
            print(f"Status changed to: {updated_doc['status']}")
        ```
        """
        result = await self.collection.find_one_and_update(
            {"key": key},
            {"$set": update_data},
            return_document=ReturnDocument.AFTER
        )
        if result:
            result["_id"] = str(result["_id"])
        return result

    async def list_value_sets(
        self,
        filter_query: dict,
        skip: int = 0,
        limit: int = 100,
        sort_by: List[tuple] = None
    ) -> tuple[List[dict], int]:
        """
        Retrieve paginated list of value sets with filtering and sorting.

        LLM Instructions:
        • Use this for displaying value sets in UI with pagination
        • Use this when implementing search and filter functionality
        • Call this for admin dashboards or value set management interfaces

        Business Logic:
        • Applies MongoDB filter query for advanced filtering
        • Returns both the data and total count for pagination UI
        • Defaults to sorting by creation date (newest first)
        • Converts all ObjectIds to strings for JSON serialization
        • Total count reflects the filtered results, not all documents

        Args:
            filter_query (dict): MongoDB query document for filtering.
                Examples: {}, {'status': 'active'}, {'module': 'core'}.
                Supports complex queries like {'status': {'$in': ['active', 'draft']}}.
            skip (int, optional): Number of documents to skip for pagination.
                Use (page - 1) * limit for page-based pagination. Defaults to 0.
            limit (int, optional): Maximum number of documents to return.
                Should be reasonable (typically 10-100). Defaults to 100.
            sort_by (List[tuple], optional): MongoDB sort specification.
                Format: [('field', direction)]. Direction: 1 for asc, -1 for desc.
                Defaults to [('createdAt', pymongo.DESCENDING)].

        Returns:
            tuple[List[dict], int]: Tuple containing:
                - List of value set documents with '_id' as strings
                - Total count of documents matching the filter (for pagination)

        Example:
        ```python
        # Get active value sets, page 2, 20 per page
        filter_query = {'status': 'active'}
        skip = 1 * 20  # page 2
        limit = 20
        sort_by = [('key', 1)]  # Sort by key A-Z

        documents, total = await repository.list_value_sets(
            filter_query, skip, limit, sort_by
        )

        print(f"Showing {len(documents)} of {total} total")
        ```
        """
        if sort_by is None:
            sort_by = [("createdAt", pymongo.DESCENDING)]

        # Get total count
        total = await self.collection.count_documents(filter_query)

        # Get paginated results
        cursor = self.collection.find(filter_query).sort(sort_by).skip(skip).limit(limit)
        documents = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            documents.append(doc)

        return documents, total

    async def search_items(
        self,
        search_query: str,
        value_set_key: Optional[str] = None,
        language_code: str = "en"
    ) -> List[dict]:
        """
        Search for specific items within value sets using text matching.

        LLM Instructions:
        • Use this when users search for specific values or codes
        • Use this for autocomplete or lookup functionality
        • Call this when implementing item selection interfaces

        Business Logic:
        • Uses MongoDB aggregation pipeline for complex item filtering
        • Searches both item codes and language-specific labels
        • Case-insensitive regex matching for flexible search
        • Returns value sets containing only the matching items
        • Groups results by value set to maintain document structure

        Args:
            search_query (str): Text to search for in item codes and labels.
                Case-insensitive partial matching. Examples: 'US', 'United', 'admin'.
            value_set_key (Optional[str]): Limit search to specific value set.
                If provided, only searches within that value set.
                If None, searches across all value sets.
            language_code (str, optional): Language code for label searching.
                Defaults to 'en'. Must match label structure in items.
                Examples: 'en', 'es', 'fr', 'de'.

        Returns:
            List[dict]: List of value set documents containing only matching items.
                Each document includes: '_id', 'key', 'module', 'matchingItems'.
                'matchingItems' contains only items that matched the search.

        Example:
        ```python
        # Search for countries containing 'United'
        results = await repository.search_items(
            'United',
            value_set_key='COUNTRY_CODES',
            language_code='en'
        )

        for value_set in results:
            print(f"Found {len(value_set['matchingItems'])} matches in {value_set['key']}")
            for item in value_set['matchingItems']:
                print(f"  {item['code']}: {item['labels']['en']}")
        ```
        """
        # Build search pipeline
        pipeline = []

        # Filter by value set key if provided
        if value_set_key:
            pipeline.append({"$match": {"key": value_set_key}})

        # Unwind items array
        pipeline.append({"$unwind": "$items"})

        # Search in items
        search_field = f"items.labels.{language_code}"
        pipeline.extend([
            {
                "$match": {
                    "$or": [
                        {"items.code": {"$regex": search_query, "$options": "i"}},
                        {search_field: {"$regex": search_query, "$options": "i"}}
                    ]
                }
            },
            {
                "$group": {
                    "_id": "$_id",
                    "key": {"$first": "$key"},
                    "module": {"$first": "$module"},
                    "matchingItems": {"$push": "$items"}
                }
            }
        ])

        results = []
        async for doc in self.collection.aggregate(pipeline):
            doc["_id"] = str(doc["_id"])
            results.append(doc)

        return results

    async def search_by_label(
        self,
        label_text: str,
        language_code: str = "en",
        status_filter: Optional[str] = None
    ) -> List[dict]:
        """
        Search for value sets containing items with specific label text.

        LLM Instructions:
        • Use this when searching for value sets by their item content
        • Use this for finding value sets that contain specific terms
        • Call this when implementing global search across value sets

        Business Logic:
        • Searches in item labels using case-insensitive regex
        • Returns entire value set documents, not just matching items
        • Can filter by value set status (active, inactive, archived)
        • Uses simple find query, not aggregation pipeline
        • Returns all items in matching value sets

        Args:
            label_text (str): Text to search for in item labels.
                Case-insensitive partial matching in the specified language.
            language_code (str, optional): Language code for label field.
                Defaults to 'en'. Must exist in item label structure.
            status_filter (Optional[str]): Filter by value set status.
                Common values: 'active', 'inactive', 'archived', 'draft'.
                If None, searches all statuses.

        Returns:
            List[dict]: Complete value set documents that contain items
                with matching labels. All items are included, not just matches.
                Each document has '_id' converted to string.

        Example:
        ```python
        # Find active value sets containing 'Admin' in English labels
        results = await repository.search_by_label(
            'Admin',
            language_code='en',
            status_filter='active'
        )

        for value_set in results:
            print(f"Value set {value_set['key']} contains 'Admin' labels")
            print(f"Total items: {len(value_set['items'])}")
        ```
        """
        query = {
            f"items.labels.{language_code}": {"$regex": label_text, "$options": "i"}
        }

        if status_filter:
            query["status"] = status_filter

        cursor = self.collection.find(query)
        results = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            results.append(doc)

        return results

    async def add_item(self, key: str, new_item: dict, update_fields: dict) -> Optional[dict]:
        """
        Add a single new item to an existing value set's items array.

        LLM Instructions:
        • Use this when adding one new option to a value set
        • Call this after validating the new item structure
        • Use this for interactive item addition in management interfaces

        Business Logic:
        • Uses MongoDB $push to append item to the items array
        • Updates metadata fields like timestamps and user tracking
        • Does not check for duplicate codes within the items array
        • Returns the complete updated document including all items
        • Fails silently if the value set key doesn't exist

        Args:
            key (str): Unique value set key to identify the target document.
            new_item (dict): Complete item object to add to the items array.
                Must include required fields like 'code' and 'labels'.
                Example: {
                    'code': 'NEW_CODE',
                    'labels': {'en': 'New Label', 'es': 'Nueva Etiqueta'},
                    'description': 'Optional description',
                    'active': True
                }
            update_fields (dict): Additional document fields to update.
                Typically includes 'updatedAt', 'updatedBy', 'version'.
                Example: {
                    'updatedAt': datetime.utcnow(),
                    'updatedBy': 'user_id',
                    'version': version + 1
                }

        Returns:
            Optional[dict]: Complete updated value set document with new item,
                or None if the value set key doesn't exist.

        Example:
        ```python
        new_item = {
            'code': 'HIGH',
            'labels': {'en': 'High Priority', 'es': 'Alta Prioridad'},
            'sortOrder': 1,
            'active': True
        }

        update_fields = {
            'updatedAt': datetime.utcnow(),
            'updatedBy': 'admin_user'
        }

        result = await repository.add_item('PRIORITY_LEVELS', new_item, update_fields)
        if result:
            print(f"Added item, total items: {len(result['items'])}")
        ```
        """
        result = await self.collection.find_one_and_update(
            {"key": key},
            {
                "$push": {"items": new_item},
                "$set": update_fields
            },
            return_document=ReturnDocument.AFTER
        )
        if result:
            result["_id"] = str(result["_id"])
        return result

    async def update_item(
        self,
        key: str,
        item_code: str,
        item_updates: dict,
        update_fields: dict
    ) -> Optional[dict]:
        """
        Update specific fields of an item within a value set's items array.

        LLM Instructions:
        • Use this when modifying existing item properties (labels, status, etc.)
        • Call this for individual item edits rather than bulk changes
        • Use this when you need to update metadata alongside item changes

        Business Logic:
        • Uses MongoDB positional operator ($) to update the matched item
        • Requires exact match on both value set key and item code
        • Updates only the specified item fields, preserves others
        • Also updates document-level metadata fields
        • Returns None if value set or item not found

        Args:
            key (str): Value set key to identify the document.
            item_code (str): Code of the specific item to update within the items array.
                Must match exactly (case-sensitive).
            item_updates (dict): Fields to update within the matched item.
                Example: {
                    'labels.en': 'Updated English Label',
                    'active': False,
                    'description': 'New description'
                }
            update_fields (dict): Document-level fields to update.
                Typically includes audit fields like 'updatedAt', 'updatedBy'.

        Returns:
            Optional[dict]: Complete updated value set document,
                or None if value set key or item code not found.

        Example:
        ```python
        item_updates = {
            'labels.en': 'Updated Priority Level',
            'active': False
        }

        update_fields = {
            'updatedAt': datetime.utcnow(),
            'updatedBy': 'admin_user'
        }

        result = await repository.update_item(
            'PRIORITY_LEVELS', 'HIGH', item_updates, update_fields
        )

        if result:
            updated_item = next(item for item in result['items'] if item['code'] == 'HIGH')
            print(f"Updated label: {updated_item['labels']['en']}")
        ```
        """
        # Build update query for nested item
        set_query = update_fields.copy()
        for field, value in item_updates.items():
            set_query[f"items.$.{field}"] = value

        result = await self.collection.find_one_and_update(
            {"key": key, "items.code": item_code},
            {"$set": set_query},
            return_document=ReturnDocument.AFTER
        )
        if result:
            result["_id"] = str(result["_id"])
        return result


    async def bulk_add_items(
        self,
        operations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Efficiently add multiple items to multiple value sets in a single operation.

        LLM Instructions:
        • Use this for importing data or bulk item creation
        • Call this when adding many items across different value sets
        • Use this for better performance than individual add_item calls

        Business Logic:
        • Uses MongoDB bulk_write for efficient batch operations
        • Each operation adds multiple items to one value set
        • Operations are unordered for better performance
        • Updates metadata fields for each affected value set
        • Returns summary statistics, not individual results

        Args:
            operations (List[Dict[str, Any]]): List of add operations.
                Each operation dict must contain:
                - 'key' (str): Target value set key
                - 'items' (List[dict]): Items to add to that value set
                - 'update_fields' (dict): Document metadata to update
                Example: [{
                    'key': 'COUNTRY_CODES',
                    'items': [{'code': 'US', 'labels': {'en': 'United States'}}],
                    'update_fields': {'updatedAt': datetime.utcnow()}
                }]

        Returns:
            Dict[str, Any]: Operation summary with keys:
                - 'modified' (int): Number of documents successfully modified
                - 'matched' (int): Number of documents that matched the query

        Example:
        ```python
        operations = [
            {
                'key': 'COUNTRIES',
                'items': [
                    {'code': 'US', 'labels': {'en': 'United States'}},
                    {'code': 'CA', 'labels': {'en': 'Canada'}}
                ],
                'update_fields': {'updatedAt': datetime.utcnow(), 'updatedBy': 'import_script'}
            },
            {
                'key': 'LANGUAGES',
                'items': [{'code': 'EN', 'labels': {'en': 'English'}}],
                'update_fields': {'updatedAt': datetime.utcnow()}
            }
        ]

        result = await repository.bulk_add_items(operations)
        print(f"Modified {result['modified']} value sets")
        ```
        """
        bulk_ops = []
        for op in operations:
            bulk_ops.append(
                pymongo.UpdateOne(
                    {"key": op["key"]},
                    {
                        "$push": {"items": {"$each": op["items"]}},
                        "$set": op["update_fields"]
                    }
                )
            )

        if bulk_ops:
            result = await self.collection.bulk_write(bulk_ops, ordered=False)
            return {
                "modified": result.modified_count,
                "matched": result.matched_count
            }
        return {"modified": 0, "matched": 0}

    async def bulk_update_items(
        self,
        operations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Update multiple items across different value sets with error tracking.

        LLM Instructions:
        • Use this for bulk item modifications across multiple value sets
        • Call this when applying systematic changes to many items
        • Use this when you need detailed error reporting for each operation

        Business Logic:
        • Processes operations sequentially, not as MongoDB bulk operation
        • Continues processing even if individual operations fail
        • Tracks successful and failed operations separately
        • Provides detailed error information for debugging
        • Uses the update_item method internally for each operation

        Args:
            operations (List[Dict[str, Any]]): List of update operations.
                Each operation dict must contain:
                - 'key' (str): Value set key
                - 'item_code' (str): Code of item to update
                - 'updates' (dict): Item field updates
                - 'update_fields' (dict): Document metadata updates
                Example: [{
                    'key': 'USER_ROLES',
                    'item_code': 'ADMIN',
                    'updates': {'active': False},
                    'update_fields': {'updatedAt': datetime.utcnow()}
                }]

        Returns:
            Dict[str, Any]: Detailed operation results with keys:
                - 'successful' (int): Number of successful updates
                - 'failed' (int): Number of failed updates
                - 'errors' (List[dict]): Detailed error information for failures

        Example:
        ```python
        operations = [
            {
                'key': 'USER_ROLES',
                'item_code': 'ADMIN',
                'updates': {'active': False},
                'update_fields': {'updatedAt': datetime.utcnow()}
            },
            {
                'key': 'INVALID_SET',
                'item_code': 'INVALID_CODE',
                'updates': {'active': True},
                'update_fields': {}
            }
        ]

        result = await repository.bulk_update_items(operations)
        print(f"Success: {result['successful']}, Failed: {result['failed']}")
        for error in result['errors']:
            print(f"Error in {error['key']}.{error['item_code']}: {error['error']}")
        ```
        """
        results = {"successful": 0, "failed": 0, "errors": []}

        for op in operations:
            try:
                result = await self.update_item(
                    op["key"],
                    op["item_code"],
                    op["updates"],
                    op["update_fields"]
                )
                if result:
                    results["successful"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append({
                        "key": op["key"],
                        "item_code": op["item_code"],
                        "error": "Item not found"
                    })
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "key": op["key"],
                    "item_code": op["item_code"],
                    "error": str(e)
                })

        return results


    async def replace_item_value(
        self,
        key: str,
        old_code: str,
        new_item: dict,
        update_fields: dict
    ) -> Optional[dict]:
        """
        Replace an entire item in a value set with completely new data.

        LLM Instructions:
        • Use this when changing an item's code or completely restructuring it
        • Call this for item migrations or major item changes
        • Use update_item for partial updates, this for complete replacement

        Business Logic:
        • Performs two sequential operations: remove old item, add new item
        • Uses MongoDB $pull to remove item by code, then $push for new item
        • Updates document metadata only after successful replacement
        • Returns None if the value set doesn't exist
        • May result in item position change within the array

        Args:
            key (str): Value set key to identify the target document.
            old_code (str): Code of the existing item to remove.
                Must match exactly. If not found, operation continues to add new item.
            new_item (dict): Complete new item object to add.
                Should include all required fields like 'code', 'labels', etc.
                The new code can be the same as old_code or completely different.
            update_fields (dict): Document-level metadata fields to update.
                Applied only after successful item replacement.

        Returns:
            Optional[dict]: Complete updated value set document with replaced item,
                or None if the value set key doesn't exist.

        Example:
        ```python
        # Replace item with new code and structure
        old_code = 'TEMP_CODE'
        new_item = {
            'code': 'PERMANENT_CODE',
            'labels': {'en': 'Permanent Status', 'es': 'Estado Permanente'},
            'priority': 1,
            'active': True
        }

        update_fields = {
            'updatedAt': datetime.utcnow(),
            'updatedBy': 'migration_script'
        }

        result = await repository.replace_item_value(
            'STATUS_CODES', old_code, new_item, update_fields
        )

        if result:
            codes = [item['code'] for item in result['items']]
            print(f"Updated codes: {codes}")
        ```
        """
        # First remove old item, then add new one
        result = await self.collection.find_one_and_update(
            {"key": key},
            {
                "$pull": {"items": {"code": old_code}}
            }
        )

        if result:
            result = await self.collection.find_one_and_update(
                {"key": key},
                {
                    "$push": {"items": new_item},
                    "$set": update_fields
                },
                return_document=ReturnDocument.AFTER
            )
            if result:
                result["_id"] = str(result["_id"])

        return result

    async def bulk_create(self, value_sets: List[dict]) -> Dict[str, Any]:
        """
        Create multiple value set documents in a single efficient operation.

        LLM Instructions:
        • Use this for initial system setup or data migration
        • Call this when importing value sets from external sources
        • Use this for better performance than individual create calls

        Business Logic:
        • Uses MongoDB insert_many with unordered operations
        • Continues inserting even if some documents fail (duplicate keys, etc.)
        • Handles BulkWriteError gracefully with detailed error reporting
        • Returns both successful insertions and failure details
        • Does not validate document structure before insertion

        Args:
            value_sets (List[dict]): List of complete value set documents to create.
                Each document should include all required fields:
                'key', 'module', 'status', 'items', 'createdAt', 'createdBy', etc.
                Example: [{
                    'key': 'COUNTRIES',
                    'module': 'geography',
                    'status': 'active',
                    'items': [],
                    'createdAt': datetime.utcnow()
                }]

        Returns:
            Dict[str, Any]: Operation results with keys:
                - 'successful' (int): Number of documents successfully created
                - 'failed' (int): Number of failed insertions
                - 'inserted_ids' (List[str]): ObjectIds of created documents (success case)
                - 'errors' (List[dict]): Detailed error information (failure case)

        Example:
        ```python
        value_sets = [
            {
                'key': 'COUNTRIES',
                'module': 'geography',
                'status': 'active',
                'items': [],
                'createdAt': datetime.utcnow(),
                'createdBy': 'setup_script'
            },
            {
                'key': 'LANGUAGES',
                'module': 'localization',
                'status': 'active',
                'items': [],
                'createdAt': datetime.utcnow(),
                'createdBy': 'setup_script'
            }
        ]

        result = await repository.bulk_create(value_sets)
        print(f"Created {result['successful']} value sets")
        if result['failed'] > 0:
            print(f"Failed to create {result['failed']} value sets")
        ```
        """
        try:
            result = await self.collection.insert_many(value_sets, ordered=False)
            return {
                "successful": len(result.inserted_ids),
                "failed": 0,
                "inserted_ids": [str(id) for id in result.inserted_ids]
            }
        except pymongo.errors.BulkWriteError as e:
            successful = e.details.get('nInserted', 0)
            errors = e.details.get('writeErrors', [])
            return {
                "successful": successful,
                "failed": len(errors),
                "errors": errors
            }

    async def bulk_update(self, operations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Update multiple value set documents efficiently using bulk operations.

        LLM Instructions:
        • Use this for systematic updates across many value sets
        • Call this when applying configuration changes to multiple value sets
        • Use this for better performance than individual update_by_key calls

        Business Logic:
        • Uses MongoDB bulk_write with UpdateOne operations
        • All operations use $set to update specified fields only
        • Operations are unordered for better performance
        • Returns summary statistics of successful operations
        • Does not provide detailed error information per operation

        Args:
            operations (List[Dict[str, Any]]): List of update operations.
                Each operation dict must contain:
                - 'key' (str): Value set key to identify document
                - 'updates' (dict): Fields and values to update
                Example: [{
                    'key': 'COUNTRY_CODES',
                    'updates': {
                        'status': 'archived',
                        'updatedAt': datetime.utcnow(),
                        'updatedBy': 'system_admin'
                    }
                }]

        Returns:
            Dict[str, Any]: Operation summary with keys:
                - 'modified' (int): Number of documents successfully updated
                - 'matched' (int): Number of documents that matched the queries

        Example:
        ```python
        # Archive multiple old value sets
        operations = [
            {
                'key': 'OLD_COUNTRIES',
                'updates': {
                    'status': 'archived',
                    'updatedAt': datetime.utcnow(),
                    'archivedBy': 'cleanup_script'
                }
            },
            {
                'key': 'DEPRECATED_CODES',
                'updates': {
                    'status': 'archived',
                    'updatedAt': datetime.utcnow()
                }
            }
        ]

        result = await repository.bulk_update(operations)
        print(f"Updated {result['modified']} of {result['matched']} matched documents")
        ```
        """
        bulk_ops = []
        for op in operations:
            bulk_ops.append(
                pymongo.UpdateOne(
                    {"key": op["key"]},
                    {"$set": op["updates"]}
                )
            )

        if bulk_ops:
            result = await self.collection.bulk_write(bulk_ops, ordered=False)
            return {
                "modified": result.modified_count,
                "matched": result.matched_count
            }
        return {"modified": 0, "matched": 0}

    async def archive(self, key: str, update_fields: dict) -> Optional[dict]:
        """
        Mark a value set as archived while preserving data for reference.

        LLM Instructions:
        • Use this when deactivating value sets that shouldn't be deleted
        • Call this for value sets that are no longer actively used
        • Use this instead of deletion to maintain data integrity and history

        Business Logic:
        • Forces status field to 'ARCHIVED' regardless of update_fields content
        • Preserves all existing data and items for reference
        • Uses update_by_key internally for the operation
        • Should include audit fields like archivedAt and archivedBy
        • Archived value sets can be restored later if needed

        Args:
            key (str): Unique value set key to identify the document to archive.
            update_fields (dict): Additional fields to update during archival.
                Commonly includes: 'archivedAt', 'archivedBy', 'archiveReason'.
                The 'status' field will be automatically set to 'archived'.
                Example: {
                    'archivedAt': datetime.utcnow(),
                    'archivedBy': 'admin_user',
                    'archiveReason': 'No longer needed'
                }

        Returns:
            Optional[dict]: Complete updated document with status='archived',
                or None if the value set key doesn't exist.

        Example:
        ```python
        archive_fields = {
            'archivedAt': datetime.utcnow(),
            'archivedBy': 'system_admin',
            'archiveReason': 'Replaced by new version'
        }

        archived_doc = await repository.archive('OLD_COUNTRY_CODES', archive_fields)
        if archived_doc:
            print(f"Archived {archived_doc['key']} with {len(archived_doc['items'])} items")
            print(f"Reason: {archived_doc.get('archiveReason', 'Not specified')}")
        ```
        """
        update_fields["status"] = "archived"
        return await self.update_by_key(key, update_fields)

    async def restore(self, key: str, update_fields: dict) -> Optional[dict]:
        """
        Restore an archived value set back to active status.

        LLM Instructions:
        • Use this when reactivating previously archived value sets
        • Call this when archived data needs to be available again
        • Use this to undo accidental archival operations

        Business Logic:
        • Forces status field to 'ACTIVE' regardless of update_fields content
        • Restores full functionality to the value set
        • Uses update_by_key internally for the operation
        • Should include audit fields like restoredAt and restoredBy
        • Does not validate if the value set is currently archived

        Args:
            key (str): Unique value set key to identify the document to restore.
            update_fields (dict): Additional fields to update during restoration.
                Commonly includes: 'restoredAt', 'restoredBy', 'restoreReason'.
                The 'status' field will be automatically set to 'active'.
                Example: {
                    'restoredAt': datetime.utcnow(),
                    'restoredBy': 'admin_user',
                    'restoreReason': 'Needed for new project'
                }

        Returns:
            Optional[dict]: Complete updated document with status='active',
                or None if the value set key doesn't exist.

        Example:
        ```python
        restore_fields = {
            'restoredAt': datetime.utcnow(),
            'restoredBy': 'project_manager',
            'restoreReason': 'Required for legacy system integration'
        }

        restored_doc = await repository.restore('LEGACY_CODES', restore_fields)
        if restored_doc:
            print(f"Restored {restored_doc['key']} to active status")
            print(f"Reason: {restored_doc.get('restoreReason', 'Not specified')}")
        ```
        """
        update_fields["status"] = "active"
        return await self.update_by_key(key, update_fields)

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Generate comprehensive statistics about all value sets in the database.

        LLM Instructions:
        • Use this for dashboard displays and system monitoring
        • Call this when generating reports about value set usage
        • Use this for administrative overview of the value set system

        Business Logic:
        • Uses MongoDB aggregation pipeline with $facet for multiple statistics
        • Calculates counts by status and module for categorization
        • Generates item-level statistics (total, average, min, max per value set)
        • Handles empty database gracefully with zero values
        • Returns structured data suitable for dashboard visualization

        Args:
            None: This method takes no parameters.

        Returns:
            Dict[str, Any]: Comprehensive statistics with keys:
                - 'total_value_sets' (int): Total number of value sets
                - 'by_status' (dict): Count by status {'active': 10, 'archived': 2}
                - 'by_module' (dict): Count by module {'core': 5, 'geography': 3}
                - 'items_statistics' (dict): Item stats with 'total_items', 'avg_items', 'max_items', 'min_items'

        Example:
        ```python
        stats = await repository.get_statistics()

        print(f"Total Value Sets: {stats['total_value_sets']}")
        print(f"Active: {stats['by_status'].get('active', 0)}")
        print(f"Archived: {stats['by_status'].get('archived', 0)}")

        print("\nBy Module:")
        for module, count in stats['by_module'].items():
            print(f"  {module}: {count}")

        items_stats = stats['items_statistics']
        if items_stats:
            print(f"\nItems: {items_stats.get('total_items', 0)} total")
            print(f"Average per set: {items_stats.get('avg_items', 0):.1f}")
        ```
        """
        pipeline = [
            {
                "$facet": {
                    "total": [{"$count": "count"}],
                    "by_status": [
                        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
                    ],
                    "by_module": [
                        {"$group": {"_id": "$module", "count": {"$sum": 1}}}
                    ],
                    "items_stats": [
                        {
                            "$group": {
                                "_id": None,
                                "total_items": {"$sum": {"$size": "$items"}},
                                "avg_items": {"$avg": {"$size": "$items"}},
                                "max_items": {"$max": {"$size": "$items"}},
                                "min_items": {"$min": {"$size": "$items"}}
                            }
                        }
                    ]
                }
            }
        ]

        result = await self.collection.aggregate(pipeline).to_list(1)

        if result:
            stats = result[0]
            return {
                "total_value_sets": stats["total"][0]["count"] if stats["total"] else 0,
                "by_status": {item["_id"]: item["count"] for item in stats["by_status"]},
                "by_module": {item["_id"]: item["count"] for item in stats["by_module"]},
                "items_statistics": stats["items_stats"][0] if stats["items_stats"] else {}
            }

        return {
            "total_value_sets": 0,
            "by_status": {},
            "by_module": {},
            "items_statistics": {}
        }

    async def export_value_set(self, key: str) -> Optional[dict]:
        """
        Export a clean value set document for backup, transfer, or migration.

        LLM Instructions:
        • Use this when backing up individual value sets
        • Call this before making major changes to preserve current state
        • Use this for transferring value sets between environments

        Business Logic:
        • Retrieves complete value set document using find_by_key
        • Removes MongoDB-specific fields (_id) for clean export
        • Preserves all business data including items, metadata, and audit fields
        • Returns data suitable for JSON serialization and storage
        • Can be used with import_value_set for complete transfer

        Args:
            key (str): Unique value set key to identify the document to export.

        Returns:
            Optional[dict]: Clean value set document without MongoDB-specific fields,
                or None if the value set key doesn't exist.
                Document includes all original fields except '_id'.

        Example:
        ```python
        # Export value set for backup
        exported_data = await repository.export_value_set('COUNTRY_CODES')

        if exported_data:
            # Save to file or transfer to another system
            import json
            with open('country_codes_backup.json', 'w') as f:
                json.dump(exported_data, f, indent=2, default=str)

            print(f"Exported {len(exported_data['items'])} items")
            print(f"Key: {exported_data['key']}")
            print(f"Module: {exported_data['module']}")
        else:
            print("Value set not found for export")
        ```
        """
        document = await self.find_by_key(key)
        if document:
            # Remove MongoDB-specific fields for clean export
            document.pop("_id", None)
        return document

    async def import_value_set(self, value_set_data: dict) -> dict:
        """
        Import a value set document from external source or backup.

        LLM Instructions:
        • Use this when restoring value sets from backups
        • Call this when migrating data between environments
        • Use this for loading value sets from configuration files

        Business Logic:
        • Removes any existing '_id' field to avoid conflicts
        • Uses the create method internally for insertion
        • Generates new MongoDB ObjectId for the imported document
        • Does not check for duplicate keys - may create duplicates
        • Preserves all original data structure and content

        Args:
            value_set_data (dict): Complete value set document to import.
                Should contain all required fields: 'key', 'module', 'status', 'items'.
                Any existing '_id' field will be removed automatically.
                Typically comes from export_value_set or external configuration.

        Returns:
            dict: The imported value set document with new '_id' field added.
                Contains all original data plus the new MongoDB ObjectId.

        Example:
        ```python
        # Import from backup file
        import json
        with open('country_codes_backup.json', 'r') as f:
            backup_data = json.load(f)

        # Ensure proper datetime objects if needed
        from datetime import datetime
        backup_data['createdAt'] = datetime.fromisoformat(backup_data['createdAt'])

        imported_doc = await repository.import_value_set(backup_data)

        print(f"Imported {imported_doc['key']} with new ID: {imported_doc['_id']}")
        print(f"Contains {len(imported_doc['items'])} items")
        ```
        """
        # Remove any existing _id
        value_set_data.pop("_id", None)
        return await self.create(value_set_data)

    async def check_key_exists(self, key: str) -> bool:
        """
        Verify if a value set key already exists in the database.

        LLM Instructions:
        • Use this before creating new value sets to prevent duplicates
        • Call this when validating user input for unique keys
        • Use this for key availability checking in management interfaces

        Business Logic:
        • Uses MongoDB count_documents for efficient existence check
        • More efficient than find_by_key when only checking existence
        • Returns boolean result for simple validation logic
        • Case-sensitive exact match on the key field
        • Does not consider document status (archived vs active)

        Args:
            key (str): Value set key to check for existence.
                Case-sensitive exact match required.

        Returns:
            bool: True if a document with the key exists, False otherwise.
                Does not distinguish between active, archived, or other statuses.

        Example:
        ```python
        # Check before creating new value set
        new_key = 'DEPARTMENT_CODES'

        if await repository.check_key_exists(new_key):
            print(f"Key '{new_key}' already exists, choose a different key")
        else:
            print(f"Key '{new_key}' is available")
            # Proceed with creation
            new_value_set = {
                'key': new_key,
                'module': 'hr',
                'status': 'active',
                'items': [],
                'createdAt': datetime.utcnow()
            }
            created = await repository.create(new_value_set)
        ```
        """
        count = await self.collection.count_documents({"key": key})
        return count > 0

    async def get_items_by_key(self, key: str) -> Optional[List[dict]]:
        """
        Retrieve only the items array from a value set without other metadata.

        LLM Instructions:
        • Use this when you only need the item data, not the full document
        • Call this for better performance when building dropdown lists or options
        • Use this for API endpoints that return just the selectable values

        Business Logic:
        • Uses MongoDB projection to fetch only the 'items' field
        • More efficient than find_by_key when metadata isn't needed
        • Returns the raw items array without document wrapper
        • Preserves original item structure and ordering
        • Returns None if value set doesn't exist

        Args:
            key (str): Unique value set key to identify the document.

        Returns:
            Optional[List[dict]]: The items array from the value set,
                or None if the value set key doesn't exist.
                Each item dict typically contains 'code', 'labels', and other fields.

        Example:
        ```python
        # Get items for a dropdown list
        country_items = await repository.get_items_by_key('COUNTRY_CODES')

        if country_items:
            # Build options for UI
            options = []
            for item in country_items:
                if item.get('active', True):  # Only show active items
                    options.append({
                        'value': item['code'],
                        'label': item['labels'].get('en', item['code'])
                    })

            print(f"Found {len(options)} active countries")
        else:
            print("Country codes value set not found")
        ```
        """
        document = await self.collection.find_one(
            {"key": key},
            {"items": 1}
        )
        return document["items"] if document else None