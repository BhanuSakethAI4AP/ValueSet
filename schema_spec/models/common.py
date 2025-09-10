from datetime import datetime
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, Field


class BaseDocument(BaseModel):
    """Base document model with common fields"""
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    created_date_time: datetime = Field(default_factory=datetime.utcnow)
    update_date_time: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }