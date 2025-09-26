from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


# ==========================
# Enums
# ==========================
class StatusEnum(str, Enum):
    """Allowed status values for value sets."""
    ACTIVE = "active"
    ARCHIVED = "archived"


# ==========================
# Label Schema
# ==========================
class LabelSchema(BaseModel):
    """Multilingual display text for a value set item."""
    en: str = Field(..., max_length=200, description="Required label in English")
    hi: Optional[str] = Field(None, max_length=200, description="Optional label in Hindi")


class LabelUpdateSchema(BaseModel):
    """Schema for updating labels - all fields optional."""
    en: Optional[str] = Field(None, max_length=200, description="English label")
    hi: Optional[str] = Field(None, max_length=200, description="Hindi label")


# ==========================
# Item Schemas
# ==========================
class ItemCreateSchema(BaseModel):
    """Schema to create a single item in a value set."""
    code: str = Field(..., max_length=50, description="Unique code within this value set")
    labels: LabelSchema


class ItemUpdateSchema(BaseModel):
    """Schema to update a single item in a value set."""
    code: Optional[str] = Field(None, max_length=50, description="Updated code for the item")
    labels: Optional[LabelUpdateSchema] = None


class ItemSchema(BaseModel):
    """Complete item schema for responses."""
    code: str = Field(..., max_length=50, description="Item code")
    labels: LabelSchema


# ==========================
# Value Set Create/Update Schemas
# ==========================
class ValueSetCreateSchema(BaseModel):
    """Schema for creating a new value set."""
    key: str = Field(..., max_length=100, description="Globally unique identifier for the value set")
    status: StatusEnum = Field(StatusEnum.ACTIVE, description='Lifecycle status: "active" or "archived"')
    module: str = Field("Core", max_length=50, description="Functional module this value set belongs to")
    description: Optional[str] = Field(None, max_length=500, description="Description of the value set")
    items: List[ItemCreateSchema] = Field(..., min_length=1, max_length=500, description="List of codes and labels")
    createdBy: str = Field(..., description="User creating the value set")
    createdAt: Optional[datetime] = Field(None, description="Optional explicit creation timestamp for migrations")

    @field_validator('items')
    def validate_unique_codes(cls, items):
        codes = [item.code for item in items]
        if len(codes) != len(set(codes)):
            raise ValueError("Item codes must be unique within the value set")
        return items


class ValueSetUpdateSchema(BaseModel):
    """Schema to update an existing value set."""
    status: Optional[StatusEnum] = Field(None, description='Update status: "active" or "archived"')
    description: Optional[str] = Field(None, max_length=500, description="Updated description")
    module: Optional[str] = Field(None, max_length=50, description="Updated module name")
    items: Optional[List[ItemSchema]] = Field(None, min_length=1, max_length=500, description="Complete replacement of items list")
    updatedBy: str = Field(..., description="User updating the value set")
    updatedAt: Optional[datetime] = Field(None, description="Optional explicit update timestamp for migrations")

    @field_validator('items')
    def validate_unique_codes(cls, items):
        if items:
            codes = [item.code for item in items]
            if len(codes) != len(set(codes)):
                raise ValueError("Item codes must be unique within the value set")
        return items


# ==========================
# Response Schemas
# ==========================
class ValueSetResponseSchema(BaseModel):
    """Full value set response including audit fields."""
    id: str = Field(..., alias="_id", description="MongoDB ObjectId")
    key: str = Field(..., description="Globally unique identifier")
    status: str = Field(..., description="Lifecycle status")
    module: str = Field(..., description="Functional module")
    description: Optional[str] = Field(None, description="Value set description")
    items: List[ItemSchema] = Field(..., description="Items in the value set")
    createdAt: datetime = Field(..., description="Creation timestamp")
    createdBy: str = Field(..., description="Creator user ID")
    updatedAt: Optional[datetime] = Field(None, description="Last update timestamp")
    updatedBy: Optional[str] = Field(None, description="Last updater user ID")

    class Config:
        populate_by_name = True


class ValueSetListItemSchema(BaseModel):
    """Simplified value set for list responses."""
    id: str = Field(..., alias="_id", description="MongoDB ObjectId")
    key: str = Field(..., description="Globally unique identifier")
    status: str = Field(..., description="Lifecycle status")
    module: str = Field(..., description="Functional module")
    description: Optional[str] = Field(None, description="Value set description")
    itemCount: int = Field(..., description="Number of items")
    createdAt: datetime = Field(..., description="Creation timestamp")
    updatedAt: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        populate_by_name = True


# ==========================
# Query/Filter Schemas
# ==========================
class ListValueSetsQuerySchema(BaseModel):
    """Query parameters for listing value sets."""
    status: Optional[StatusEnum] = None
    module: Optional[str] = None
    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(100, ge=1, le=1000, description="Maximum records to return")


class SearchItemsQuerySchema(BaseModel):
    """Schema to search for codes or labels inside value sets."""
    query: str = Field(..., min_length=1, description="Text to search in item codes or labels")
    valueSetKey: Optional[str] = Field(None, description="Optional filter for specific value set key")
    languageCode: Optional[str] = Field("en", description="Language to search in")


class SearchItemsResponseSchema(BaseModel):
    """Response schema for search results."""
    valueSetKey: str = Field(..., description="Parent value set key")
    valueSetModule: str = Field(..., description="Module of the value set")
    matchingItems: List[ItemSchema] = Field(..., description="Items that matched the search")
    totalMatches: int = Field(..., description="Total number of matches found")


# ==========================
# Pagination Schemas
# ==========================
class PaginatedValueSetResponse(BaseModel):
    """Paginated response for value set listings."""
    total: int = Field(..., description="Total number of value sets matching criteria")
    skip: int = Field(..., description="Number of records skipped")
    limit: int = Field(..., description="Maximum records returned")
    items: List[ValueSetListItemSchema] = Field(..., description="List of value sets")
    hasMore: bool = Field(..., description="Whether more results are available")


class PaginatedSearchResponse(BaseModel):
    """Paginated response for item search results."""
    total: int = Field(..., description="Total number of matching items")
    skip: int = Field(..., description="Number of records skipped")
    limit: int = Field(..., description="Maximum records returned")
    results: List[SearchItemsResponseSchema] = Field(..., description="Search results")
    hasMore: bool = Field(..., description="Whether more results are available")


# ==========================
# Item Operation Schemas
# ==========================
class AddItemRequestSchema(BaseModel):
    """Request to add a new item to existing value set."""
    item: ItemCreateSchema = Field(..., description="New item to add")
    updatedBy: str = Field(..., description="User adding the item")


class UpdateItemRequestSchema(BaseModel):
    """Request to update existing item in value set."""
    itemCode: str = Field(..., description="Code of item to update")
    updates: ItemUpdateSchema = Field(..., description="Updates to apply")
    updatedBy: str = Field(..., description="User updating the item")




class ReplaceItemCodeSchema(BaseModel):
    """Schema to replace a code inside a value set."""
    oldCode: str = Field(..., description="Existing code to be replaced")
    newCode: str = Field(..., max_length=50, description="New code to replace the old one")
    newLabels: Optional[LabelSchema] = Field(None, description="Optional new labels")
    updatedBy: str = Field(..., description="User performing replacement")


# ==========================
# Validation Schema
# ==========================
class ValidateValueSetRequestSchema(BaseModel):
    """Request to validate a value set configuration."""
    key: str = Field(..., max_length=100, description="Value set key")
    status: StatusEnum = Field(..., description="Status to validate")
    module: str = Field(..., max_length=50, description="Module to validate")
    items: List[ItemSchema] = Field(..., min_length=1, max_length=500, description="Items to validate")

    @model_validator(mode='after')
    def validate_value_set(self):
        codes = [item.code for item in self.items]
        if len(codes) != len(set(codes)):
            raise ValueError("Item codes must be unique within the value set")
        for item in self.items:
            if not item.labels.en:
                raise ValueError(f"English label required for item {item.code}")
        return self


class ValidationResultSchema(BaseModel):
    """Schema for validation result of a value set."""
    key: str = Field(..., description="Value set key being validated")
    isValid: bool = Field(..., description="True if all validation rules pass")
    errors: List[str] = Field(default_factory=list, description="List of validation error messages")
    warnings: List[str] = Field(default_factory=list, description="List of warnings")


# ==========================
# Archive/Restore Schema
# ==========================
class ArchiveRestoreRequestSchema(BaseModel):
    """Schema for archive or restore operations."""
    key: str = Field(..., description="Key of the value set to archive or restore")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for operation")
    updatedBy: str = Field(..., description="User performing the operation")


class ArchiveRestoreResponseSchema(BaseModel):
    """Response for archive/restore operations."""
    success: bool = Field(..., description="Operation success status")
    key: str = Field(..., description="Affected value set key")
    previousStatus: str = Field(..., description="Status before operation")
    currentStatus: str = Field(..., description="Status after operation")
    message: str = Field(..., description="Operation message")


# ==========================
# Bulk Operation Schemas
# ==========================
class BulkValueSetCreateSchema(BaseModel):
    """Schema to bulk create multiple value sets."""
    valueSets: List[ValueSetCreateSchema] = Field(..., min_length=1, max_length=100)

    @field_validator('valueSets')
    def validate_unique_keys(cls, value_sets):
        keys = [vs.key for vs in value_sets]
        if len(keys) != len(set(keys)):
            raise ValueError("Value set keys must be unique in bulk import")
        return value_sets


class BulkValueSetUpdateItemSchema(BaseModel):
    """Single update item for bulk update."""
    key: str = Field(..., description="Value set key to update")
    status: Optional[StatusEnum] = None
    module: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=500)


class BulkValueSetUpdateSchema(BaseModel):
    """Schema to bulk update multiple value sets."""
    updates: List[BulkValueSetUpdateItemSchema] = Field(..., min_length=1, max_length=100)
    updatedBy: str = Field(..., description="User performing bulk update")


class BulkItemUpdateRequestSchema(BaseModel):
    """Schema for updating specific items across multiple value sets."""
    valueSetKey: str = Field(..., description="Value set containing the item")
    itemCode: str = Field(..., description="Code of the item to update")
    updates: ItemUpdateSchema = Field(..., description="Updates to apply to the item")
    updatedBy: str = Field(..., description="User performing the update")


class BulkItemUpdateSchema(BaseModel):
    """Schema to bulk update items across value sets."""
    itemUpdates: List[BulkItemUpdateRequestSchema] = Field(..., min_length=1, max_length=100)

    @field_validator('itemUpdates')
    def validate_unique_updates(cls, updates):
        update_keys = [(u.valueSetKey, u.itemCode) for u in updates]
        if len(update_keys) != len(set(update_keys)):
            raise ValueError("Duplicate item updates not allowed in bulk operation")
        return updates


class BulkOperationResponseSchema(BaseModel):
    """Response for bulk operations."""
    successful: int = Field(..., description="Count of successful operations")
    failed: int = Field(..., description="Count of failed operations")
    errors: List[Dict[str, str]] = Field(default_factory=list, description="Error details")
    processedKeys: List[str] = Field(default_factory=list, description="Successfully processed keys")




# ==========================
# Error Response Schemas
# ==========================
class ErrorResponseSchema(BaseModel):
    """Standard error response."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class ValidationErrorResponseSchema(BaseModel):
    """Validation error response with field details."""
    error: str = Field("ValidationError", description="Error type")
    message: str = Field(..., description="Main error message")
    field_errors: Dict[str, List[str]] = Field(..., description="Field-specific errors")