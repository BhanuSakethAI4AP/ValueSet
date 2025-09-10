from datetime import datetime
from typing import Dict, List, Optional
from bson import ObjectId
from pydantic import BaseModel, Field, field_validator


class EnumItem(BaseModel):
    code: str
    labels: Dict[str, str]
    
    @field_validator('labels')
    def validate_labels(cls, v):
        if 'en' not in v:
            raise ValueError("English label ('en') is required")
        return v


class ValueSet(BaseModel):
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    key: str
    status: str = "active"
    description: Optional[str] = None
    items: List[EnumItem]
    created_by: Optional[ObjectId] = None
    created_date_time: datetime = Field(default_factory=datetime.utcnow)
    update_date_time: datetime = Field(default_factory=datetime.utcnow)
    
    @field_validator('status')
    def validate_status(cls, v):
        if v not in ["active", "archived"]:
            raise ValueError("Status must be 'active' or 'archived'")
        return v
    
    @field_validator('items')
    def validate_items(cls, v):
        if not v:
            raise ValueError("At least one item is required")
        if len(v) > 500:
            raise ValueError("Maximum 500 items allowed")
        
        codes = [item.code for item in v]
        if len(codes) != len(set(codes)):
            raise ValueError("Duplicate codes found in items")
        
        return v
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }