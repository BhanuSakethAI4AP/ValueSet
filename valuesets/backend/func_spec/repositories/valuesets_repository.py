from typing import Dict, List, Optional, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError
import pymongo
from .base_repository import BaseRepository


class ValueSetsRepository(BaseRepository):
    """Repository for ValueSets operations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, "valueSets")
    
    async def create_indexes(self):
        """Create required indexes"""
        await self.collection.create_index([("key", pymongo.ASCENDING)], unique=True)
        await self.collection.create_index([("status", pymongo.ASCENDING)])
        await self.collection.create_index([("description", pymongo.TEXT)])
    
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new ValueSet"""
        try:
            # Handle created_by field
            if "created_by" in data and isinstance(data["created_by"], str):
                # Keep as string if not a valid ObjectId format
                if len(data["created_by"]) == 24:
                    try:
                        from bson import ObjectId
                        data["created_by"] = ObjectId(data["created_by"])
                    except:
                        # Keep as string if conversion fails
                        pass
            
            return await super().create(data)
        except DuplicateKeyError:
            raise ValueError(f"ValueSet with key '{data['key']}' already exists")
    
    async def get_by_key(self, key: str) -> Optional[Dict[str, Any]]:
        """Get ValueSet by key"""
        doc = await self.collection.find_one({"key": key})
        return self._serialize_document(doc) if doc else None
    
    async def update_by_key(self, key: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update ValueSet by key"""
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        if not update_data:
            return await self.get_by_key(key)
        
        update_data["update_date_time"] = datetime.utcnow()
        
        result = await self.collection.update_one(
            {"key": key},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            return None
        
        return await self.get_by_key(key)
    
    async def archive_by_key(self, key: str) -> bool:
        """Archive ValueSet by key"""
        result = await self.collection.update_one(
            {"key": key},
            {"$set": {"status": "archived", "update_date_time": datetime.utcnow()}}
        )
        return result.matched_count > 0
    
    async def get_all_active(self) -> List[Dict[str, Any]]:
        """Get all active ValueSets"""
        cursor = self.collection.find({"status": "active"})
        documents = []
        async for doc in cursor:
            documents.append(self._serialize_document(doc))
        return documents
    
    async def list_with_filters(
        self,
        status: Optional[str] = None,
        search_text: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[Dict[str, Any]], int]:
        """List ValueSets with status and text filters"""
        filter_query = {}
        
        if status:
            filter_query["status"] = status
        
        if search_text:
            filter_query["$text"] = {"$search": search_text}
        
        return await self.list(filter_query, skip, limit, "update_date_time", -1)
    
    async def key_exists(self, key: str) -> bool:
        """Check if key exists"""
        return await self.exists({"key": key})