# Schemas Layer

## Overview
The **Schemas Layer** defines all data models using Pydantic for the Value Set Management System. These schemas provide validation, serialization, and documentation for data flowing through the API.

**Key Responsibilities:**
- Define data structures with type hints
- Validate input data automatically
- Serialize Python objects to JSON
- Deserialize JSON to Python objects
- Generate OpenAPI documentation
- Enforce business rules at the data level

**Architecture Position:**
```
HTTP Client → Router Layer (validates with Schemas) → Service Layer → Repository Layer
                           ↑
                    (This Layer)
```

## What's in This Folder

### `value_set_schemas_enhanced.py`
Complete collection of Pydantic models organized by purpose:

**Schema Categories:**
1. **Enums** - Status values
2. **Label Schemas** - Multilingual labels
3. **Item Schemas** - Value set items
4. **Value Set Schemas** - Complete value sets
5. **Response Schemas** - API responses
6. **Query Schemas** - Search/filter parameters
7. **Pagination Schemas** - Paginated responses
8. **Item Operation Schemas** - Item CRUD requests
9. **Validation Schemas** - Validation requests/responses
10. **Archive/Restore Schemas** - Archive operations
11. **Bulk Operation Schemas** - Bulk operations
12. **Error Schemas** - Error responses

## Schema Categories

### 1. Enums

#### `StatusEnum`
```python
class StatusEnum(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
```

**When to Use:**
- Setting value set status
- Filtering by status
- Validating status transitions

**Example:**
```python
from schemas.value_set_schemas_enhanced import StatusEnum

status = StatusEnum.ACTIVE
print(status.value)  # "active"
```

### 2. Label Schemas

#### `LabelSchema`
Multilingual display text for items (creation/full labels).

**Fields:**
- `en` (str, required): English label (max 200 chars)
- `hi` (str, optional): Hindi label (max 200 chars)

**When to Use:**
- Creating new items
- Displaying complete item information
- When English label is mandatory

**Example:**
```python
from schemas.value_set_schemas_enhanced import LabelSchema

labels = LabelSchema(
    en="Cardiology",
    hi="हृदय रोग विज्ञान"
)
```

#### `LabelUpdateSchema`
Partial label updates (all fields optional).

**When to Use:**
- Updating item labels
- Adding translations to existing items
- Partial label modifications

**Example:**
```python
from schemas.value_set_schemas_enhanced import LabelUpdateSchema

# Add Hindi translation without changing English
updates = LabelUpdateSchema(hi="हृदय रोग विज्ञान")
```

### 3. Item Schemas

#### `ItemCreateSchema`
Schema for creating new items.

**Fields:**
- `code` (str, required): Unique code within value set (max 50 chars)
- `labels` (LabelSchema, required): Complete labels with English required

**When to Use:**
- Creating new items
- Bulk adding items
- Initial value set population

**Example:**
```python
from schemas.value_set_schemas_enhanced import ItemCreateSchema, LabelSchema

item = ItemCreateSchema(
    code="CARDIO",
    labels=LabelSchema(en="Cardiology", hi="हृदय रोग विज्ञान")
)
```

#### `ItemUpdateSchema`
Schema for updating existing items.

**Fields:**
- `code` (str, optional): Updated code
- `labels` (LabelUpdateSchema, optional): Updated labels

**When to Use:**
- Updating item information
- Partial item modifications
- Adding/changing labels

**Example:**
```python
from schemas.value_set_schemas_enhanced import ItemUpdateSchema, LabelUpdateSchema

updates = ItemUpdateSchema(
    labels=LabelUpdateSchema(en="Cardiology (Updated)")
)
```

#### `ItemSchema`
Complete item representation for responses.

**Fields:**
- `code` (str): Item code
- `labels` (LabelSchema): Complete labels

**When to Use:**
- Returning item data in responses
- Displaying complete item information
- Validating full items

**Example:**
```python
# Typically returned by API, not created manually
# Example structure:
{
    "code": "CARDIO",
    "labels": {
        "en": "Cardiology",
        "hi": "हृदय रोग विज्ञान"
    }
}
```

### 4. Value Set Schemas

#### `ValueSetCreateSchema`
Schema for creating new value sets.

**Fields:**
- `key` (str, required): Globally unique identifier (max 100 chars)
- `status` (StatusEnum, default=ACTIVE): Initial status
- `module` (str, default="Core"): Functional module (max 50 chars)
- `description` (str, optional): Description (max 500 chars)
- `items` (List[ItemCreateSchema], required): 1-500 items
- `createdBy` (str, required): User creating the value set
- `createdAt` (datetime, optional): For migrations with specific timestamps

**Validation:**
- Item codes must be unique within the value set
- At least 1 item required
- Maximum 500 items

**When to Use:**
- Creating new value sets
- Importing value sets
- Bulk value set creation

**Example:**
```python
from schemas.value_set_schemas_enhanced import (
    ValueSetCreateSchema, ItemCreateSchema, LabelSchema, StatusEnum
)

value_set = ValueSetCreateSchema(
    key="medical_specialties",
    status=StatusEnum.ACTIVE,
    module="healthcare",
    description="Medical specialty codes",
    items=[
        ItemCreateSchema(
            code="CARDIO",
            labels=LabelSchema(en="Cardiology")
        ),
        ItemCreateSchema(
            code="NEURO",
            labels=LabelSchema(en="Neurology")
        )
    ],
    createdBy="user123"
)
```

#### `ValueSetUpdateSchema`
Schema for updating existing value sets.

**Fields:**
- `status` (StatusEnum, optional): Updated status
- `description` (str, optional): Updated description (max 500 chars)
- `module` (str, optional): Updated module (max 50 chars)
- `items` (List[ItemSchema], optional): Complete replacement of items (1-500)
- `updatedBy` (str, required): User performing update
- `updatedAt` (datetime, optional): For migrations

**Validation:**
- If items provided, codes must be unique
- All fields optional except updatedBy

**When to Use:**
- Updating value set metadata
- Changing status or module
- Complete item replacement (rare)

**Example:**
```python
from schemas.value_set_schemas_enhanced import ValueSetUpdateSchema, StatusEnum

update = ValueSetUpdateSchema(
    status=StatusEnum.ACTIVE,
    description="Updated comprehensive medical specialties",
    module="healthcare_v2",
    updatedBy="admin"
)
```

### 5. Response Schemas

#### `ValueSetResponseSchema`
Complete value set with all fields including audit data.

**Fields:**
- `id` (str, alias="_id"): MongoDB ObjectId
- `key` (str): Unique identifier
- `status` (str): Current status
- `module` (str): Functional module
- `description` (str, optional): Description
- `items` (List[ItemSchema]): All items
- `createdAt` (datetime): Creation timestamp
- `createdBy` (str): Creator user ID
- `updatedAt` (datetime, optional): Last update timestamp
- `updatedBy` (str, optional): Last updater user ID

**When to Use:**
- Returning complete value set data
- API responses for GET/POST/PUT operations
- Displaying full value set details

**Example:**
```python
# API returns this structure:
{
    "_id": "507f1f77bcf86cd799439011",
    "key": "medical_specialties",
    "status": "active",
    "module": "healthcare",
    "description": "Medical specialties",
    "items": [
        {"code": "CARDIO", "labels": {"en": "Cardiology"}}
    ],
    "createdAt": "2024-01-15T10:30:00Z",
    "createdBy": "user123",
    "updatedAt": "2024-01-16T14:20:00Z",
    "updatedBy": "admin"
}
```

#### `ValueSetListItemSchema`
Simplified value set for list responses (without items).

**Fields:**
- `id` (str, alias="_id"): MongoDB ObjectId
- `key` (str): Unique identifier
- `status` (str): Current status
- `module` (str): Functional module
- `description` (str, optional): Description
- `itemCount` (int): Number of items
- `createdAt` (datetime): Creation timestamp
- `updatedAt` (datetime, optional): Last update timestamp

**When to Use:**
- Listing multiple value sets efficiently
- Pagination results
- Overview/summary displays

**Example:**
```python
# API returns this in paginated lists:
{
    "_id": "507f1f77bcf86cd799439011",
    "key": "medical_specialties",
    "status": "active",
    "module": "healthcare",
    "description": "Medical specialties",
    "itemCount": 45,
    "createdAt": "2024-01-15T10:30:00Z",
    "updatedAt": "2024-01-16T14:20:00Z"
}
```

### 6. Query/Filter Schemas

#### `ListValueSetsQuerySchema`
Query parameters for listing/filtering value sets.

**Fields:**
- `status` (StatusEnum, optional): Filter by status
- `module` (str, optional): Filter by module
- `skip` (int, default=0): Records to skip (>=0)
- `limit` (int, default=100): Records to return (1-1000)

**When to Use:**
- Paginated list requests
- Filtering value sets
- Building search interfaces

**Example:**
```python
from schemas.value_set_schemas_enhanced import ListValueSetsQuerySchema, StatusEnum

query = ListValueSetsQuerySchema(
    status=StatusEnum.ACTIVE,
    module="healthcare",
    skip=0,
    limit=50
)
```

#### `SearchItemsQuerySchema`
Schema for searching items within value sets.

**Fields:**
- `query` (str, required): Search text (min 1 char)
- `valueSetKey` (str, optional): Specific value set to search
- `languageCode` (str, default="en"): Language for label search

**When to Use:**
- Searching for specific items
- Autocomplete functionality
- Finding items by code or label

**Example:**
```python
from schemas.value_set_schemas_enhanced import SearchItemsQuerySchema

search = SearchItemsQuerySchema(
    query="cardio",
    valueSetKey="medical_specialties",
    languageCode="en"
)
```

#### `SearchItemsResponseSchema`
Response for item search results.

**Fields:**
- `valueSetKey` (str): Parent value set key
- `valueSetModule` (str): Module of the value set
- `matchingItems` (List[ItemSchema]): Items that matched
- `totalMatches` (int): Number of matches found

**When to Use:**
- Returning search results
- Displaying search matches with context
- Search result aggregation

### 7. Pagination Schemas

#### `PaginatedValueSetResponse`
Paginated response for value set listings.

**Fields:**
- `total` (int): Total matching value sets
- `skip` (int): Records skipped
- `limit` (int): Max records returned
- `items` (List[ValueSetListItemSchema]): Value set summaries
- `hasMore` (bool): Whether more results available

**When to Use:**
- List endpoints
- Paginated displays
- Infinite scroll implementations

**Example:**
```python
# API returns:
{
    "total": 150,
    "skip": 0,
    "limit": 50,
    "items": [...],
    "hasMore": True
}
```

#### `PaginatedSearchResponse`
Paginated response for item search results.

**Fields:**
- `total` (int): Total matching items
- `skip` (int): Records skipped
- `limit` (int): Max records returned
- `results` (List[SearchItemsResponseSchema]): Search results
- `hasMore` (bool): Whether more results available

**When to Use:**
- Search result pagination
- Large search result sets
- Progressive loading

### 8. Item Operation Schemas

#### `AddItemRequestSchema`
Request to add new item to existing value set.

**Fields:**
- `item` (ItemCreateSchema): New item to add
- `updatedBy` (str): User adding the item

**When to Use:**
- Adding single item
- Item creation endpoint
- Extending value sets

**Example:**
```python
from schemas.value_set_schemas_enhanced import (
    AddItemRequestSchema, ItemCreateSchema, LabelSchema
)

request = AddItemRequestSchema(
    item=ItemCreateSchema(
        code="ORTHO",
        labels=LabelSchema(en="Orthopedics")
    ),
    updatedBy="user123"
)
```

#### `UpdateItemRequestSchema`
Request to update existing item in value set.

**Fields:**
- `itemCode` (str): Code of item to update
- `updates` (ItemUpdateSchema): Updates to apply
- `updatedBy` (str): User performing update

**When to Use:**
- Updating item labels/metadata
- Modifying existing items
- Partial item updates

**Example:**
```python
from schemas.value_set_schemas_enhanced import (
    UpdateItemRequestSchema, ItemUpdateSchema, LabelUpdateSchema
)

request = UpdateItemRequestSchema(
    itemCode="CARDIO",
    updates=ItemUpdateSchema(
        labels=LabelUpdateSchema(en="Cardiology (Updated)")
    ),
    updatedBy="editor"
)
```

#### `ReplaceItemCodeSchema`
Schema to replace an item's code identifier.

**Fields:**
- `oldCode` (str): Existing code to replace
- `newCode` (str): New code (max 50 chars)
- `newLabels` (LabelSchema, optional): Optional new labels
- `updatedBy` (str): User performing replacement

**When to Use:**
- Changing item codes
- Code standardization
- Migration scenarios

**Example:**
```python
from schemas.value_set_schemas_enhanced import ReplaceItemCodeSchema, LabelSchema

replace = ReplaceItemCodeSchema(
    oldCode="CARDIO",
    newCode="CARDIOLOGY",
    newLabels=LabelSchema(en="Cardiology"),
    updatedBy="admin"
)
```

### 9. Validation Schemas

#### `ValidateValueSetRequestSchema`
Request to validate value set configuration.

**Fields:**
- `key` (str): Value set key (max 100 chars)
- `status` (StatusEnum): Status to validate
- `module` (str): Module (max 50 chars)
- `items` (List[ItemSchema]): Items to validate (1-500)

**Validation:**
- Item codes must be unique
- All items must have English labels
- 1-500 items required

**When to Use:**
- Pre-validating data before creation
- Data quality checks
- Import validation

**Example:**
```python
from schemas.value_set_schemas_enhanced import (
    ValidateValueSetRequestSchema, ItemSchema, LabelSchema, StatusEnum
)

validation_request = ValidateValueSetRequestSchema(
    key="test_set",
    status=StatusEnum.ACTIVE,
    module="testing",
    items=[
        ItemSchema(code="TEST1", labels=LabelSchema(en="Test 1"))
    ]
)
```

#### `ValidationResultSchema`
Response containing validation results.

**Fields:**
- `key` (str): Value set key validated
- `isValid` (bool): Whether validation passed
- `errors` (List[str]): Error messages
- `warnings` (List[str]): Warning messages

**When to Use:**
- Returning validation results
- Displaying validation feedback
- Pre-submission checks

### 10. Archive/Restore Schemas

#### `ArchiveRestoreRequestSchema`
Request for archive or restore operations.

**Fields:**
- `key` (str): Value set key
- `reason` (str, optional): Reason for operation (max 500 chars)
- `updatedBy` (str): User performing operation

**When to Use:**
- Archiving value sets
- Restoring archived value sets
- Audit trail for status changes

**Example:**
```python
from schemas.value_set_schemas_enhanced import ArchiveRestoreRequestSchema

archive_request = ArchiveRestoreRequestSchema(
    key="old_codes",
    reason="Superseded by new version",
    updatedBy="admin"
)
```

#### `ArchiveRestoreResponseSchema`
Response for archive/restore operations.

**Fields:**
- `success` (bool): Operation success
- `key` (str): Affected value set key
- `previousStatus` (str): Status before operation
- `currentStatus` (str): Status after operation
- `message` (str): Operation message

**When to Use:**
- Confirming archive/restore operations
- Displaying operation results
- Audit logging

### 11. Bulk Operation Schemas

#### `BulkValueSetCreateSchema`
Schema for bulk creating multiple value sets.

**Fields:**
- `valueSets` (List[ValueSetCreateSchema]): 1-100 value sets to create

**Validation:**
- Value set keys must be unique within the bulk

**When to Use:**
- Importing multiple value sets
- Initial system population
- Migration scenarios

**Example:**
```python
from schemas.value_set_schemas_enhanced import (
    BulkValueSetCreateSchema, ValueSetCreateSchema,
    ItemCreateSchema, LabelSchema
)

bulk_create = BulkValueSetCreateSchema(
    valueSets=[
        ValueSetCreateSchema(
            key="countries",
            items=[ItemCreateSchema(code="US", labels=LabelSchema(en="USA"))],
            createdBy="admin"
        ),
        ValueSetCreateSchema(
            key="currencies",
            items=[ItemCreateSchema(code="USD", labels=LabelSchema(en="Dollar"))],
            createdBy="admin"
        )
    ]
)
```

#### `BulkValueSetUpdateItemSchema`
Single update item for bulk updates.

**Fields:**
- `key` (str): Value set key to update
- `status` (StatusEnum, optional): New status
- `module` (str, optional): New module (max 50 chars)
- `description` (str, optional): New description (max 500 chars)

**When to Use:**
- Defining single update in bulk operation
- Part of bulk update requests
- Grouped modifications

#### `BulkValueSetUpdateSchema`
Schema for bulk updating multiple value sets.

**Fields:**
- `updates` (List[BulkValueSetUpdateItemSchema]): 1-100 updates
- `updatedBy` (str): User performing bulk update

**When to Use:**
- Updating multiple value sets at once
- Standardization operations
- Administrative bulk changes

**Example:**
```python
from schemas.value_set_schemas_enhanced import (
    BulkValueSetUpdateSchema, BulkValueSetUpdateItemSchema, StatusEnum
)

bulk_update = BulkValueSetUpdateSchema(
    updates=[
        BulkValueSetUpdateItemSchema(
            key="medical_specialties",
            status=StatusEnum.ACTIVE
        ),
        BulkValueSetUpdateItemSchema(
            key="country_codes",
            module="geography_v2"
        )
    ],
    updatedBy="admin"
)
```

#### `BulkItemUpdateRequestSchema`
Schema for updating specific items across value sets.

**Fields:**
- `valueSetKey` (str): Value set containing the item
- `itemCode` (str): Code of item to update
- `updates` (ItemUpdateSchema): Updates to apply
- `updatedBy` (str): User performing update

**When to Use:**
- Single item update in bulk context
- Part of bulk item update requests
- Cross-value-set item updates

#### `BulkItemUpdateSchema`
Schema for bulk updating items across value sets.

**Fields:**
- `itemUpdates` (List[BulkItemUpdateRequestSchema]): 1-100 item updates

**Validation:**
- No duplicate (value_set_key, item_code) pairs

**When to Use:**
- Updating multiple items across value sets
- Label standardization
- Global item updates

**Example:**
```python
from schemas.value_set_schemas_enhanced import (
    BulkItemUpdateSchema, BulkItemUpdateRequestSchema,
    ItemUpdateSchema, LabelUpdateSchema
)

bulk_item_update = BulkItemUpdateSchema(
    itemUpdates=[
        BulkItemUpdateRequestSchema(
            valueSetKey="medical_specialties",
            itemCode="CARDIO",
            updates=ItemUpdateSchema(
                labels=LabelUpdateSchema(en="Cardiology (Updated)")
            ),
            updatedBy="editor"
        )
    ]
)
```

#### `BulkOperationResponseSchema`
Response for all bulk operations.

**Fields:**
- `successful` (int): Count of successful operations
- `failed` (int): Count of failed operations
- `errors` (List[Dict[str, str]]): Error details
- `processedKeys` (List[str]): Successfully processed keys

**When to Use:**
- Returning bulk operation results
- Displaying success/failure statistics
- Error reporting for bulk operations

### 12. Error Response Schemas

#### `ErrorResponseSchema`
Standard error response for API errors.

**Fields:**
- `error` (str): Error type
- `message` (str): Error message
- `details` (Dict[str, Any], optional): Additional error details

**When to Use:**
- Returning general errors
- HTTP error responses
- Standardized error format

#### `ValidationErrorResponseSchema`
Validation error response with field-specific details.

**Fields:**
- `error` (str, default="ValidationError"): Error type
- `message` (str): Main error message
- `field_errors` (Dict[str, List[str]]): Field-specific errors

**When to Use:**
- Pydantic validation errors
- Form validation responses
- Detailed field-level error reporting

## How to Use Schemas

### Creating Data with Schemas

```python
from schemas.value_set_schemas_enhanced import (
    ValueSetCreateSchema, ItemCreateSchema, LabelSchema, StatusEnum
)

# Create a value set
value_set = ValueSetCreateSchema(
    key="medical_specialties",
    status=StatusEnum.ACTIVE,
    module="healthcare",
    description="List of medical specialties",
    items=[
        ItemCreateSchema(
            code="CARDIO",
            labels=LabelSchema(en="Cardiology", hi="हृदय रोग विज्ञान")
        ),
        ItemCreateSchema(
            code="NEURO",
            labels=LabelSchema(en="Neurology")
        )
    ],
    createdBy="user123"
)

# Schema automatically validates:
# - key is provided and <= 100 chars
# - items has 1-500 items
# - all item codes are unique
# - all items have English labels
```

### Validation Happens Automatically

```python
# This will raise ValidationError
try:
    value_set = ValueSetCreateSchema(
        key="medical_specialties",
        items=[
            ItemCreateSchema(code="CARDIO", labels=LabelSchema(en="Cardiology")),
            ItemCreateSchema(code="CARDIO", labels=LabelSchema(en="Duplicate"))
            # Duplicate code!
        ],
        createdBy="user123"
    )
except ValueError as e:
    print(e)  # "Item codes must be unique within the value set"
```

### Parsing JSON to Schema

```python
import json

json_data = {
    "key": "medical_specialties",
    "module": "healthcare",
    "items": [
        {"code": "CARDIO", "labels": {"en": "Cardiology"}}
    ],
    "createdBy": "user123"
}

# Parse and validate
value_set = ValueSetCreateSchema(**json_data)
```

### Converting Schema to JSON

```python
# Convert to dict
data_dict = value_set.model_dump()

# Convert to JSON string
json_string = value_set.model_dump_json()

# Convert to dict with aliases (_id instead of id)
response_dict = value_set.model_dump(by_alias=True)
```

### Partial Updates

```python
# Only update description
update = ValueSetUpdateSchema(
    description="Updated description",
    updatedBy="admin"
)

# Other fields remain unchanged in database
```

## Common Patterns

### Request/Response Cycle

```python
# 1. Request arrives with JSON
request_json = {
    "key": "test",
    "items": [...],
    "createdBy": "user"
}

# 2. FastAPI + Pydantic validate and parse
create_data = ValueSetCreateSchema(**request_json)

# 3. Service layer processes
result = await service.create_value_set(create_data)

# 4. Response schema formats output
response = ValueSetResponseSchema(**result)

# 5. FastAPI serializes to JSON
return response  # Automatically becomes JSON
```

### Validation in Layers

```
1. Pydantic Schema Validation (Type, Format, Business Rules)
   ↓
2. Service Layer Validation (Uniqueness, State, Logic)
   ↓
3. Repository Layer (Database Operations)
```

### Alias Handling

```python
# MongoDB uses "_id", but Python prefers "id"
class ValueSetResponseSchema(BaseModel):
    id: str = Field(..., alias="_id")

    class Config:
        populate_by_name = True

# Accept both "_id" and "id" in input
# Always output as "_id" with model_dump(by_alias=True)
```

## Integration with Other Layers

### With Router Layer

```python
# Router uses schemas for type hints and validation
@router.post("/", response_model=ValueSetResponseSchema)
async def create_value_set(
    create_data: ValueSetCreateSchema,  # Auto-validated
    service: ValueSetService = Depends(...)
):
    return await service.create_value_set(create_data)
```

### With Service Layer

```python
# Service receives validated schema objects
async def create_value_set(self, create_data: ValueSetCreateSchema):
    # No need to re-validate, already done by Pydantic
    data_dict = create_data.model_dump()
    return await self.repository.create(data_dict)
```

### With Repository Layer

```python
# Repository works with dicts, not schemas
async def create(self, data: dict):
    result = await self.collection.insert_one(data)
    return await self.find_by_id(result.inserted_id)
```

## What NOT to Do

❌ **Don't skip validation by using dicts everywhere**
```python
# Bad
def create_value_set(data: dict):  # No validation!
    return await repo.create(data)
```

✅ **Do use schemas for validation**
```python
# Good
def create_value_set(data: ValueSetCreateSchema):
    return await repo.create(data.model_dump())
```

❌ **Don't create schemas for internal-only data**
```python
# Bad - unnecessary schema
class RepositoryInternalData(BaseModel):
    temp_var: str
```

❌ **Don't mix create and update schemas**
```python
# Bad
async def update(key: str, data: ValueSetCreateSchema):  # Wrong schema!
    ...
```

✅ **Do use appropriate schema for each operation**
```python
# Good
async def create(data: ValueSetCreateSchema): ...
async def update(key: str, data: ValueSetUpdateSchema): ...
```

## Summary

**Schemas Layer Purpose:**
- Define all data structures with validation
- Automatic request/response validation
- Type safety throughout the application
- Self-documenting API with OpenAPI

**Key Files:**
- `value_set_schemas_enhanced.py` - All Pydantic models

**When to Use:**
- Defining API request/response structures
- Validating incoming data
- Serializing/deserializing JSON
- Generating API documentation
- Type hinting in all layers

**Integration:**
- Used by Router Layer for automatic validation
- Passed to Service Layer as typed objects
- Converted to dicts for Repository Layer
- Powers FastAPI's OpenAPI documentation