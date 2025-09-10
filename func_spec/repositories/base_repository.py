from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Type
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from bson import ObjectId
from pymongo.errors import DuplicateKeyError


class BaseRepository(ABC):
    """Base repository with common CRUD operations"""
    
    def __init__(self, db: AsyncIOMotorDatabase, collection_name: str):
        self.db = db
        self.collection: AsyncIOMotorCollection = db[collection_name]
        self.collection_name = collection_name
    
    def _serialize_document(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize MongoDB document for API response"""
        if not doc:
            return doc
        
        if "_id" in doc:
            doc["_id"] = str(doc["_id"])
        
        # Handle ObjectId fields
        for key, value in doc.items():
            if isinstance(value, ObjectId):
                doc[key] = str(value)
        
        return doc
    
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new document"""
        data["created_date_time"] = datetime.utcnow()
        data["update_date_time"] = datetime.utcnow()
        
        result = await self.collection.insert_one(data)
        created_doc = await self.collection.find_one({"_id": result.inserted_id})
        return self._serialize_document(created_doc)
    
    async def get_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID"""
        try:
            object_id = ObjectId(doc_id)
            doc = await self.collection.find_one({"_id": object_id})
            return self._serialize_document(doc) if doc else None
        except:
            return None
    
    async def update(self, doc_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update document by ID"""
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        if not update_data:
            return await self.get_by_id(doc_id)
        
        update_data["update_date_time"] = datetime.utcnow()
        
        try:
            object_id = ObjectId(doc_id)
            result = await self.collection.update_one(
                {"_id": object_id},
                {"$set": update_data}
            )
            
            if result.matched_count == 0:
                return None
            
            return await self.get_by_id(doc_id)
        except:
            return None
    
    async def delete(self, doc_id: str) -> bool:
        """Delete document by ID"""
        try:
            object_id = ObjectId(doc_id)
            result = await self.collection.delete_one({"_id": object_id})
            return result.deleted_count > 0
        except:
            return False
    
    async def list(
        self,
        filter_query: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: int = 100,
        sort_field: str = "created_date_time",
        sort_direction: int = -1
    ) -> tuple[List[Dict[str, Any]], int]:
        """List documents with pagination"""
        filter_query = filter_query or {}
        
        total = await self.collection.count_documents(filter_query)
        
        cursor = self.collection.find(filter_query).skip(skip).limit(limit).sort(sort_field, sort_direction)
        documents = []
        async for doc in cursor:
            documents.append(self._serialize_document(doc))
        
        return documents, total
    
    async def exists(self, filter_query: Dict[str, Any]) -> bool:
        """Check if document exists"""
        count = await self.collection.count_documents(filter_query)
        return count > 0