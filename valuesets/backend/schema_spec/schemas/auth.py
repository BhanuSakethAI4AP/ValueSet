from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool
    is_superuser: bool
    last_login: Optional[datetime] = None


class PermissionResponse(BaseModel):
    resource: str
    actions: List[str]
    description: Optional[str] = None


class PermissionsResponse(BaseModel):
    role: str
    role_code: str
    is_superuser: bool
    permissions: List[PermissionResponse]