from typing import Dict, List, Optional
from pydantic import BaseModel, field_validator
from .common import BaseDocument


class EnumItem(BaseModel):
    code: str
    labels: Dict[str, str]
    
    @field_validator('labels')
    def validate_labels(cls, v):
        if 'en' not in v:
            raise ValueError("English label ('en') is required")
        return v


class ValueSet(BaseDocument):
    key: str
    status: str = "active"
    description: Optional[str] = None
    items: List[EnumItem]
    created_by: Optional[str] = None
    
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