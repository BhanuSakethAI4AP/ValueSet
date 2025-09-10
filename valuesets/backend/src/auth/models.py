from datetime import datetime
from typing import List, Optional
from bson import ObjectId
from pydantic import BaseModel, Field


class Permission(BaseModel):
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    name: str
    code: str
    resource: str
    actions: List[str]
    description: Optional[str] = None
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class Role(BaseModel):
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    name: str
    code: str
    permissions: List[str]
    description: Optional[str] = None
    is_active: bool = True
    created_date_time: datetime = Field(default_factory=datetime.utcnow)
    update_date_time: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class User(BaseModel):
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    username: str
    email: str
    password_hash: str
    full_name: str
    role: str
    is_active: bool = True
    is_superuser: bool = False
    created_date_time: datetime = Field(default_factory=datetime.utcnow)
    update_date_time: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }