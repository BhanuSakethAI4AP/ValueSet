from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class EnumItemSchema(BaseModel):
    code: str
    labels: Dict[str, str]
    
    @field_validator('labels')
    def validate_labels(cls, v):
        if 'en' not in v:
            raise ValueError("English label ('en') is required")
        return v


class ValueSetBase(BaseModel):
    key: str
    status: str = "active"
    description: Optional[str] = None
    items: List[EnumItemSchema]
    
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


class ValueSetCreate(ValueSetBase):
    created_by: Optional[str] = None


class ValueSetUpdate(BaseModel):
    status: Optional[str] = None
    description: Optional[str] = None
    items: Optional[List[EnumItemSchema]] = None
    
    @field_validator('status')
    def validate_status(cls, v):
        if v and v not in ["active", "archived"]:
            raise ValueError("Status must be 'active' or 'archived'")
        return v
    
    @field_validator('items')
    def validate_items(cls, v):
        if v is not None:
            if not v:
                raise ValueError("At least one item is required")
            if len(v) > 500:
                raise ValueError("Maximum 500 items allowed")
            
            codes = [item.code for item in v]
            if len(codes) != len(set(codes)):
                raise ValueError("Duplicate codes found in items")
        
        return v


class ValueSetResponse(ValueSetBase):
    id: str = Field(alias="_id")
    created_by: Optional[str] = None
    created_date_time: datetime
    update_date_time: datetime
    
    model_config = {"populate_by_name": True}


class ValueSetListItem(BaseModel):
    key: str
    status: str
    count: int
    update_date_time: datetime


class ValueSetItemResponse(BaseModel):
    code: str
    label: str


class ValueSetItemsResponse(BaseModel):
    key: str
    status: str
    items: List[ValueSetItemResponse]


class BootstrapResponse(BaseModel):
    data: Dict[str, List[ValueSetItemResponse]]