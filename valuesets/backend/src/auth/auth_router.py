from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel
from typing import Optional

from .auth_service_merged import AuthService, oauth2_scheme


router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict


class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool
    is_superuser: bool


async def get_database() -> AsyncIOMotorDatabase:
    """Get database connection"""
    from motor.motor_asyncio import AsyncIOMotorClient
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    mongo_url = os.getenv("MONGO_URL", "mongodb+srv://pbhanusaketh1602:Bhanu%402002@saketh.qsgehh3.mongodb.net/")
    db_name = os.getenv("DB_NAME", "valuesets_platform")
    
    client = AsyncIOMotorClient(mongo_url)
    return client[db_name]


async def get_auth_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> AuthService:
    """Get auth service instance"""
    return AuthService(db)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Get current authenticated user"""
    return await auth_service.get_current_user(token)


async def get_current_active_user(current_user: dict = Depends(get_current_user)):
    """Get current active user"""
    if not current_user.get("is_active", True):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def require_permission(resource: str, action: str):
    """Dependency to require specific permission"""
    async def permission_checker(
        current_user: dict = Depends(get_current_active_user),
        auth_service: AuthService = Depends(get_auth_service)
    ):
        await auth_service.verify_permission(current_user, resource, action)
        return current_user
    return permission_checker


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Login endpoint"""
    user = await auth_service.authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    access_token_expires = timedelta(minutes=30)
    access_token = auth_service.create_access_token(
        data={"sub": user["username"]},
        expires_delta=access_token_expires
    )
    
    # Remove sensitive data from user response
    user_data = {
        "id": str(user["_id"]),
        "username": user["username"],
        "email": user["email"],
        "full_name": user["full_name"],
        "role": user["role"],
        "is_active": user["is_active"],
        "is_superuser": user.get("is_superuser", False)
    }
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_data
    }


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_active_user)):
    """Get current user info"""
    return UserResponse(
        id=str(current_user["_id"]),
        username=current_user["username"],
        email=current_user["email"],
        full_name=current_user["full_name"],
        role=current_user["role"],
        is_active=current_user["is_active"],
        is_superuser=current_user.get("is_superuser", False)
    )


@router.get("/permissions")
async def get_my_permissions(
    current_user: dict = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Get current user's permissions from merged role"""
    permissions_summary = await auth_service.get_user_permissions_summary(current_user["role"])
    return {
        "role": permissions_summary["role"],
        "role_code": permissions_summary["role_code"],
        "is_superuser": current_user.get("is_superuser", False),
        "permissions": permissions_summary["permissions"]
    }


@router.post("/verify-permission")
async def verify_permission(
    resource: str,
    action: str,
    current_user: dict = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Verify if current user has specific permission"""
    try:
        await auth_service.verify_permission(current_user, resource, action)
        return {"has_permission": True}
    except HTTPException:
        return {"has_permission": False}