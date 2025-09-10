from typing import Dict, Any
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .jwt_handler import JWTHandler
from config.database import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase

security = HTTPBearer()

class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, credentials: HTTPAuthorizationCredentials = Depends(security)):
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid authentication scheme."
                )
            
            if not self.verify_jwt(credentials.credentials):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid token or expired token."
                )
            
            return credentials.credentials
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid authorization code."
            )

    def verify_jwt(self, token: str) -> bool:
        """Verify JWT token"""
        try:
            JWTHandler.decode_token(token)
            return True
        except ValueError:
            return False

# Dependency to get current user
async def get_current_user(
    token: str = Depends(JWTBearer()),
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> Dict[str, Any]:
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        username = JWTHandler.extract_username(token)
        if username is None:
            raise credentials_exception
    except ValueError:
        raise credentials_exception
    
    user = await db.users.find_one({"username": username})
    if user is None:
        raise credentials_exception
    
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    return user

# Permission checker
def require_permission(resource: str, action: str):
    """Dependency to require specific permission"""
    async def permission_checker(
        current_user: Dict[str, Any] = Depends(get_current_user),
        db: AsyncIOMotorDatabase = Depends(get_database)
    ):
        # Superusers have all permissions
        if current_user.get("is_superuser"):
            return current_user
        
        # Get role with permissions
        role = await db.roles.find_one({"code": current_user.get("role")})
        
        if not role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role not found: {current_user.get('role')}"
            )
        
        # Check permissions
        has_permission = False
        for perm in role.get("permissions", []):
            if perm["resource"] == resource or perm["resource"] == "system":
                if "*" in perm["actions"] or action in perm["actions"]:
                    has_permission = True
                    break
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied for {resource}:{action}"
            )
        
        return current_user
    
    return permission_checker