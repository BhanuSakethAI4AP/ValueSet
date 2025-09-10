from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel

T = TypeVar('T')

class ResponseModel(BaseModel, Generic[T]):
    """Generic response model"""
    success: bool = True
    message: Optional[str] = None
    data: Optional[T] = None

class ListResponse(BaseModel, Generic[T]):
    """Generic list response model"""
    items: List[T]
    total: int
    page: Optional[int] = None
    limit: Optional[int] = None

class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    message: str
    error_code: Optional[str] = None