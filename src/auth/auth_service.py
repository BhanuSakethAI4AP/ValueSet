from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from motor.motor_asyncio import AsyncIOMotorDatabase
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


class AuthService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.users_collection = db.users
        self.roles_collection = db.roles
        self.permissions_collection = db.permissions
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    async def authenticate_user(self, username: str, password: str):
        """Authenticate a user and return user data if valid"""
        user = await self.users_collection.find_one({"username": username})
        if not user:
            return False
        if not self.verify_password(password, user["password_hash"]):
            return False
        
        # Update last login
        await self.users_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        
        return user
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Create a JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    async def get_current_user(self, token: str):
        """Get current user from JWT token"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception
        
        user = await self.users_collection.find_one({"username": username})
        if user is None:
            raise credentials_exception
        
        if not user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled"
            )
        
        return user
    
    async def get_user_permissions(self, user_role: str):
        """Get all permissions for a user's role"""
        role = await self.roles_collection.find_one({"code": user_role})
        if not role:
            return []
        
        permissions = []
        for perm_code in role.get("permissions", []):
            perm = await self.permissions_collection.find_one({"code": perm_code})
            if perm:
                permissions.append(perm)
        
        return permissions
    
    def check_permission(self, user_permissions: list, resource: str, action: str) -> bool:
        """Check if user has permission for resource and action"""
        for perm in user_permissions:
            if perm["resource"] == resource or perm["resource"] == "system":
                if "*" in perm["actions"] or action in perm["actions"]:
                    return True
        return False
    
    async def verify_permission(self, user: dict, resource: str, action: str):
        """Verify user has required permission, raise exception if not"""
        if user.get("is_superuser"):
            return True
        
        permissions = await self.get_user_permissions(user.get("role"))
        
        if not self.check_permission(permissions, resource, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied for {resource}:{action}"
            )
        
        return True