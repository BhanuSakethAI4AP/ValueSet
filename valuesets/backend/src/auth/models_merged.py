from datetime import datetime
from typing import List, Optional, Dict
from bson import ObjectId
from pydantic import BaseModel, Field


class Permission(BaseModel):
    """Embedded permission within a role"""
    resource: str
    actions: List[str]
    description: Optional[str] = None


class Role(BaseModel):
    """Role with embedded permissions"""
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    name: str
    code: str
    description: Optional[str] = None
    permissions: List[Permission] = []
    is_active: bool = True
    is_system: bool = False  # System roles cannot be deleted
    created_date_time: datetime = Field(default_factory=datetime.utcnow)
    update_date_time: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class User(BaseModel):
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    username: str
    email: str
    password_hash: str
    full_name: str
    role: str  # Role code
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