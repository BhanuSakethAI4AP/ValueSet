from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from .common import BaseDocument


class Permission(BaseModel):
    """Embedded permission within a role"""
    resource: str
    actions: List[str]
    description: Optional[str] = None


class Role(BaseDocument):
    """Role with embedded permissions"""
    name: str
    code: str
    description: Optional[str] = None
    permissions: List[Permission] = []
    is_active: bool = True
    is_system: bool = False


class User(BaseDocument):
    username: str
    email: str
    password_hash: str
    full_name: str
    role: str  # Role code
    is_active: bool = True
    is_superuser: bool = False
    last_login: Optional[datetime] = None