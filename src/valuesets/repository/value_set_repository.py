from datetime import datetime
from typing import Dict, List, Optional, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import pymongo
from pymongo.errors import DuplicateKeyError


class ValueSetRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.valueSets
        # Note: Indexes should be created during initialization/seeding, not here
    
    async def _ensure_indexes(self):
        await self.collection.create_index([("key", pymongo.ASCENDING)], unique=True)
        await self.collection.create_index([("status", pymongo.ASCENDING)])
        await self.collection.create_index([("description", pymongo.TEXT)])
    
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            data["created_date_time"] = datetime.utcnow()
            data["update_date_time"] = datetime.utcnow()
            
            if "created_by" in data and isinstance(data["created_by"], str):
                # Only convert if it's a valid ObjectId string (24 hex chars)
                if len(data["created_by"]) == 24:
                    try:
                        data["created_by"] = ObjectId(data["created_by"])
                    except:
                        # If conversion fails, keep as string
                        pass
            
            result = await self.collection.insert_one(data)
            created_doc = await self.collection.find_one({"_id": result.inserted_id})
            return self._serialize_document(created_doc)
        except DuplicateKeyError:
            raise ValueError(f"ValueSet with key '{data['key']}' already exists")
    
    async def get_by_key(self, key: str) -> Optional[Dict[str, Any]]:
        doc = await self.collection.find_one({"key": key})
        return self._serialize_document(doc) if doc else None
    
    async def update(self, key: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
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
    
    async def archive(self, key: str) -> bool:
        result = await self.collection.update_one(
            {"key": key},
            {"$set": {"status": "archived", "update_date_time": datetime.utcnow()}}
        )
        return result.matched_count > 0
    
    async def list(
        self,
        status: Optional[str] = None,
        search_text: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[Dict[str, Any]], int]:
        filter_query = {}
        
        if status:
            filter_query["status"] = status
        
        if search_text:
            filter_query["$text"] = {"$search": search_text}
        
        total = await self.collection.count_documents(filter_query)
        
        cursor = self.collection.find(filter_query).skip(skip).limit(limit)
        documents = []
        async for doc in cursor:
            documents.append(self._serialize_document(doc))
        
        return documents, total
    
    async def get_all_active(self) -> List[Dict[str, Any]]:
        cursor = self.collection.find({"status": "active"})
        documents = []
        async for doc in cursor:
            documents.append(self._serialize_document(doc))
        return documents
    
    async def exists(self, key: str) -> bool:
        count = await self.collection.count_documents({"key": key})
        return count > 0
    
    async def delete(self, key: str) -> bool:
        result = await self.collection.delete_one({"key": key})
        return result.deleted_count > 0
    
    def _serialize_document(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        if not doc:
            return doc
        
        if "_id" in doc:
            doc["_id"] = str(doc["_id"])
        
        if "created_by" in doc and isinstance(doc["created_by"], ObjectId):
            doc["created_by"] = str(doc["created_by"])
        
        return doc