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
        """Initialize repository with database connection."""
        self.db = database
        self.collection: AsyncIOMotorCollection = database.value_sets

    async def create(self, value_set_data: dict) -> dict:
        """
        Create a new value set in the database.

        Args:
            value_set_data: Value set data to insert

        Returns:
            Created value set with _id
        """
        result = await self.collection.insert_one(value_set_data)
        value_set_data["_id"] = str(result.inserted_id)
        return value_set_data

    async def find_by_key(self, key: str) -> Optional[dict]:
        """
        Find a value set by its unique key.

        Args:
            key: Unique value set key

        Returns:
            Value set document or None
        """
        document = await self.collection.find_one({"key": key})
        if document:
            document["_id"] = str(document["_id"])
        return document

    async def find_by_id(self, value_set_id: str) -> Optional[dict]:
        """
        Find a value set by its MongoDB ObjectId.

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

    async def update_by_key(self, key: str, update_data: dict) -> Optional[dict]:
        """
        Update a value set by its key.

        Args:
            key: Value set key
            update_data: Fields to update

        Returns:
            Updated document or None
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
        List value sets with pagination and filtering.

        Args:
            filter_query: MongoDB filter query
            skip: Number of documents to skip
            limit: Maximum documents to return
            sort_by: Sort specification

        Returns:
            Tuple of (documents list, total count)
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
        Search for items within value sets.

        Args:
            search_query: Text to search
            value_set_key: Optional specific value set key
            language_code: Language to search in

        Returns:
            List of matching value sets with filtered items
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
        Search value sets by label text.

        Args:
            label_text: Text to search in labels
            language_code: Language code
            status_filter: Optional status filter

        Returns:
            List of matching value sets
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
        Add a new item to a value set.

        Args:
            key: Value set key
            new_item: New item to add
            update_fields: Additional fields to update (timestamps, updatedBy)

        Returns:
            Updated document or None
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
        Update an item within a value set.

        Args:
            key: Value set key
            item_code: Code of item to update
            item_updates: Updates for the item
            update_fields: Additional fields to update

        Returns:
            Updated document or None
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
        Bulk add items to multiple value sets.

        Args:
            operations: List of add operations

        Returns:
            Operation results
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
        Bulk update items across value sets.

        Args:
            operations: List of update operations

        Returns:
            Operation results
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
        Replace an item's value in a value set.

        Args:
            key: Value set key
            old_code: Old item code to replace
            new_item: New item data
            update_fields: Additional update fields

        Returns:
            Updated document or None
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
        Bulk create multiple value sets.

        Args:
            value_sets: List of value set documents

        Returns:
            Operation results
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
        Bulk update multiple value sets.

        Args:
            operations: List of update operations

        Returns:
            Operation results
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
        Archive a value set by setting status to 'archived'.

        Args:
            key: Value set key
            update_fields: Fields to update including status

        Returns:
            Updated document or None
        """
        update_fields["status"] = "archived"
        return await self.update_by_key(key, update_fields)

    async def restore(self, key: str, update_fields: dict) -> Optional[dict]:
        """
        Restore an archived value set by setting status to 'active'.

        Args:
            key: Value set key
            update_fields: Fields to update including status

        Returns:
            Updated document or None
        """
        update_fields["status"] = "active"
        return await self.update_by_key(key, update_fields)

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about value sets in the database.

        Returns:
            Statistics dictionary
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
        Export a value set for backup or transfer.

        Args:
            key: Value set key

        Returns:
            Complete value set document or None
        """
        document = await self.find_by_key(key)
        if document:
            # Remove MongoDB-specific fields for clean export
            document.pop("_id", None)
        return document

    async def import_value_set(self, value_set_data: dict) -> dict:
        """
        Import a value set from external source.

        Args:
            value_set_data: Value set data to import

        Returns:
            Imported value set with _id
        """
        # Remove any existing _id
        value_set_data.pop("_id", None)
        return await self.create(value_set_data)

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

    async def get_items_by_key(self, key: str) -> Optional[List[dict]]:
        """
        Get only the items array from a value set.

        Args:
            key: Value set key

        Returns:
            Items array or None
        """
        document = await self.collection.find_one(
            {"key": key},
            {"items": 1}
        )
        return document["items"] if document else None