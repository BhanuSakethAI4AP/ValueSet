# Service Layer Documentation

## 📁 Overview

The **Service Layer** is the **business logic layer** that sits between the API routes and the database. It contains all the validation, business rules, and orchestration logic for value set operations.

## 🎯 Purpose

> **"The service layer is the brain - it thinks, validates, and decides what should happen."**

### Key Responsibilities:
- ✅ Business logic and validation
- ✅ Business rule enforcement
- ✅ Data transformation
- ✅ Audit field management (timestamps, user tracking)
- ✅ Complex operations orchestration
- ✅ Error handling and messaging

### What Service Layer Does NOT Do:
- ❌ HTTP request/response handling
- ❌ Direct database queries
- ❌ Schema validation (that's Pydantic's job)
- ❌ User authentication

---

## 📂 Files in This Folder

```
services/
├── value_set_service.py    # Main business logic for value sets
└── README.md               # This file
```

---

## 🔧 ValueSetService Class

### Location
`services/value_set_service.py`

### Purpose
Implements all business logic for value set management.

### Initialization

```python
from services.value_set_service import ValueSetService
from repositories.value_set_repository import ValueSetRepository

# Initialize with repository
repository = ValueSetRepository(database)
service = ValueSetService(repository)
```

---

## 📚 Available Methods

### 1. CREATE Operations

#### `create_value_set(create_data: ValueSetCreateSchema) -> ValueSetResponseSchema`

Creates a new value set with comprehensive validation.

**Business Rules Enforced:**
- ✅ Key must be unique across all value sets
- ✅ Item codes must be unique within the value set
- ✅ Must have 1-500 items
- ✅ Auto-generates audit fields (createdAt, createdBy)

**When to Use:**
- Creating new value sets
- Initial data setup

**Example:**
```python
from schemas.value_set_schemas_enhanced import (
    ValueSetCreateSchema,
    ItemCreateSchema,
    LabelSchema,
    StatusEnum
)

# Prepare data
items = [
    ItemCreateSchema(
        code="HIGH",
        labels=LabelSchema(en="High Priority", hi="उच्च प्राथमिकता")
    ),
    ItemCreateSchema(
        code="MEDIUM",
        labels=LabelSchema(en="Medium Priority", hi="मध्यम प्राथमिकता")
    )
]

create_data = ValueSetCreateSchema(
    key="PRIORITY_LEVELS",
    status=StatusEnum.ACTIVE,
    module="task_management",
    description="Priority levels for task management",
    items=items,
    createdBy="user123"
)

# Call service
try:
    result = await service.create_value_set(create_data)
    print(f"Created: {result.key} with {len(result.items)} items")
except ValueError as e:
    print(f"Validation error: {e}")
```

**What Happens Behind the Scenes:**
```python
1. Check if key already exists → ValueError if duplicate
2. Validate item codes are unique → ValueError if duplicates
3. Validate item count (1-500) → ValueError if out of range
4. Prepare document with audit fields
5. Call repository.create()
6. Return ValueSetResponseSchema
```

**Raises:**
- `ValueError`: If key exists, duplicate item codes, or invalid item count

---

### 2. READ Operations

#### `get_value_set_by_key(key: str) -> Optional[ValueSetResponseSchema]`

Retrieves a specific value set by its unique key.

**When to Use:**
- Fetching specific value sets
- Detail views
- Verification before updates

**Example:**
```python
value_set = await service.get_value_set_by_key("PRIORITY_LEVELS")

if value_set:
    print(f"Key: {value_set.key}")
    print(f"Status: {value_set.status}")
    print(f"Items: {len(value_set.items)}")
    print(f"Created by: {value_set.createdBy} at {value_set.createdAt}")
else:
    print("Value set not found")
```

**Returns:**
- `ValueSetResponseSchema` if found
- `None` if not found

---

#### `list_value_sets(query_params: ListValueSetsQuerySchema) -> PaginatedValueSetResponse`

Lists value sets with filtering and pagination.

**Business Logic:**
- Builds filter query from parameters
- Applies status and module filters
- Returns paginated results
- Calculates item counts for each value set

**When to Use:**
- Browse/list interfaces
- Admin dashboards
- Searching with filters

**Example:**
```python
from schemas.value_set_schemas_enhanced import ListValueSetsQuerySchema, StatusEnum

# Query active value sets in task_management module
query = ListValueSetsQuerySchema(
    status=StatusEnum.ACTIVE,
    module="task_management",
    skip=0,
    limit=20
)

response = await service.list_value_sets(query)

print(f"Found {response.total} total value sets")
print(f"Showing {len(response.items)} value sets")
print(f"Has more: {response.hasMore}")

for item in response.items:
    print(f"- {item.key}: {item.itemCount} items")
```

**Returns:**
```python
PaginatedValueSetResponse(
    total=50,           # Total matching records
    skip=0,             # Current skip offset
    limit=20,           # Page size
    items=[...],        # Value set summaries
    hasMore=True        # More pages available
)
```

---

### 3. UPDATE Operations

#### `update_value_set(key: str, update_data: ValueSetUpdateSchema) -> Optional[ValueSetResponseSchema]`

Updates an existing value set with validation.

**Business Rules:**
- ✅ Value set must exist
- ✅ If updating items, validate uniqueness and count
- ✅ Auto-updates audit fields (updatedAt, updatedBy)
- ✅ Partial updates supported

**When to Use:**
- Modifying value set metadata
- Status changes
- Description updates

**Example:**
```python
from schemas.value_set_schemas_enhanced import ValueSetUpdateSchema, StatusEnum

# Prepare updates
update_data = ValueSetUpdateSchema(
    description="Updated priority levels with new categorization",
    status=StatusEnum.ACTIVE,
    updatedBy="admin_user"
)

# Update
result = await service.update_value_set("PRIORITY_LEVELS", update_data)

if result:
    print(f"Updated: {result.key}")
    print(f"New description: {result.description}")
    print(f"Updated at: {result.updatedAt}")
else:
    print("Value set not found")
```

**Partial Update Example:**
```python
# Only update description
update_data = ValueSetUpdateSchema(
    description="New description only",
    updatedBy="user123"
)
# Status, module, items remain unchanged
```

**Raises:**
- `ValueError`: If item validation fails (when updating items)

---

### 4. ITEM MANAGEMENT Operations

#### `add_item_to_value_set(key: str, request: AddItemRequestSchema) -> Optional[ValueSetResponseSchema]`

Adds a single new item to an existing value set.

**Business Rules:**
- ✅ Value set must exist
- ✅ Item code must be unique within value set
- ✅ Must not exceed 500 item limit
- ✅ Updates audit fields

**When to Use:**
- Adding one item at a time
- Interactive item creation
- User-driven additions

**Example:**
```python
from schemas.value_set_schemas_enhanced import AddItemRequestSchema, ItemCreateSchema, LabelSchema

# Prepare new item
new_item = ItemCreateSchema(
    code="LOW",
    labels=LabelSchema(en="Low Priority", hi="कम प्राथमिकता")
)

request = AddItemRequestSchema(
    item=new_item,
    updatedBy="user123"
)

# Add item
result = await service.add_item_to_value_set("PRIORITY_LEVELS", request)

if result:
    print(f"Added item, now has {len(result.items)} items")
else:
    print("Value set not found")
```

**Raises:**
- `ValueError`: If item code already exists or limit exceeded

---

#### `update_item_in_value_set(key: str, request: UpdateItemRequestSchema) -> Optional[ValueSetResponseSchema]`

Updates an existing item within a value set.

**Business Rules:**
- ✅ Value set and item must exist
- ✅ If changing code, new code must be unique
- ✅ Supports partial item updates
- ✅ Updates audit fields

**When to Use:**
- Modifying item labels
- Updating item properties
- Correcting item data

**Example:**
```python
from schemas.value_set_schemas_enhanced import (
    UpdateItemRequestSchema,
    ItemUpdateSchema,
    LabelUpdateSchema
)

# Update item labels
updates = ItemUpdateSchema(
    labels=LabelUpdateSchema(
        en="High Priority (Updated)",
        hi="उच्च प्राथमिकता (अपडेट)"
    )
)

request = UpdateItemRequestSchema(
    itemCode="HIGH",
    updates=updates,
    updatedBy="admin_user"
)

result = await service.update_item_in_value_set("PRIORITY_LEVELS", request)

if result:
    # Find updated item
    item = next(i for i in result.items if i.code == "HIGH")
    print(f"Updated label: {item.labels.en}")
```

**Raises:**
- `ValueError`: If item not found or new code conflicts

---

#### `replace_value_in_item(key: str, replace_request: ReplaceItemCodeSchema) -> Optional[ValueSetResponseSchema]`

Completely replaces an item's code and optionally its labels.

**Business Rules:**
- ✅ Old item must exist
- ✅ New code must be unique
- ✅ Preserves existing labels if not provided
- ✅ Atomic operation (old removed, new added)

**When to Use:**
- Changing item codes
- Item code standardization
- Migration scenarios

**Example:**
```python
from schemas.value_set_schemas_enhanced import ReplaceItemCodeSchema, LabelSchema

# Replace item code
replace_request = ReplaceItemCodeSchema(
    oldCode="HIGH",
    newCode="P1",
    newLabels=LabelSchema(
        en="Priority 1 (Critical)",
        hi="प्राथमिकता 1 (महत्वपूर्ण)"
    ),
    updatedBy="admin_user"
)

result = await service.replace_value_in_item("PRIORITY_LEVELS", replace_request)

if result:
    # Verify replacement
    has_old = any(i.code == "HIGH" for i in result.items)
    has_new = any(i.code == "P1" for i in result.items)
    print(f"Old code exists: {has_old}")  # False
    print(f"New code exists: {has_new}")  # True
```

**Raises:**
- `ValueError`: If old item not found or new code conflicts

---

#### `bulk_add_items(key: str, items: List[ItemCreateSchema], updated_by: str) -> BulkOperationResponseSchema`

Adds multiple items to a value set in one operation.

**Business Rules:**
- ✅ Validates value set exists
- ✅ Checks all codes unique against existing
- ✅ Ensures total doesn't exceed 500
- ✅ All or nothing (atomic)

**When to Use:**
- Importing item data
- Initial value set population
- Better performance than individual adds

**Example:**
```python
from schemas.value_set_schemas_enhanced import ItemCreateSchema, LabelSchema

# Prepare multiple items
items = [
    ItemCreateSchema(code="P1", labels=LabelSchema(en="Priority 1")),
    ItemCreateSchema(code="P2", labels=LabelSchema(en="Priority 2")),
    ItemCreateSchema(code="P3", labels=LabelSchema(en="Priority 3"))
]

# Bulk add
result = await service.bulk_add_items(
    key="PRIORITY_LEVELS",
    items=items,
    updated_by="admin_user"
)

print(f"Successful: {result.successful}")
print(f"Failed: {result.failed}")
if result.errors:
    for error in result.errors:
        print(f"Error: {error}")
```

**Returns:**
```python
BulkOperationResponseSchema(
    successful=3,
    failed=0,
    errors=[],
    processedKeys=["PRIORITY_LEVELS"]
)
```

---

#### `bulk_update_items(updates: BulkItemUpdateSchema) -> BulkOperationResponseSchema`

Updates multiple items across one or more value sets.

**Business Rules:**
- ✅ Validates each value set and item exists
- ✅ Continues on individual failures
- ✅ Returns detailed error reporting

**When to Use:**
- Standardizing labels across multiple items
- Bulk corrections
- System-wide updates

**Example:**
```python
from schemas.value_set_schemas_enhanced import (
    BulkItemUpdateSchema,
    BulkItemUpdateRequestSchema,
    ItemUpdateSchema,
    LabelUpdateSchema
)

# Update multiple items
item_updates = [
    BulkItemUpdateRequestSchema(
        valueSetKey="PRIORITY_LEVELS",
        itemCode="HIGH",
        updates=ItemUpdateSchema(
            labels=LabelUpdateSchema(en="Critical Priority")
        ),
        updatedBy="admin"
    ),
    BulkItemUpdateRequestSchema(
        valueSetKey="PRIORITY_LEVELS",
        itemCode="MEDIUM",
        updates=ItemUpdateSchema(
            labels=LabelUpdateSchema(en="Normal Priority")
        ),
        updatedBy="admin"
    )
]

bulk_updates = BulkItemUpdateSchema(itemUpdates=item_updates)
result = await service.bulk_update_items(bulk_updates)

print(f"Updated {result.successful} items")
if result.errors:
    print("Errors:")
    for error in result.errors:
        print(f"- {error}")
```

---

### 5. SEARCH Operations

#### `search_value_set_items(search_params: SearchItemsQuerySchema) -> List[SearchItemsResponseSchema]`

Searches for items across value sets by text.

**Search Capabilities:**
- Searches item codes
- Searches labels in specified language
- Can filter by specific value set
- Case-insensitive

**When to Use:**
- Autocomplete features
- User search
- Finding specific codes

**Example:**
```python
from schemas.value_set_schemas_enhanced import SearchItemsQuerySchema

# Search for "Priority" in English labels
search_params = SearchItemsQuerySchema(
    query="Priority",
    languageCode="en"
)

results = await service.search_value_set_items(search_params)

for result in results:
    print(f"Value Set: {result.valueSetKey}")
    print(f"Module: {result.valueSetModule}")
    print(f"Matches: {result.totalMatches}")
    for item in result.matchingItems:
        print(f"  - {item.code}: {item.labels.en}")
```

**Returns:**
```python
[
    SearchItemsResponseSchema(
        valueSetKey="PRIORITY_LEVELS",
        valueSetModule="task_management",
        matchingItems=[<matching items>],
        totalMatches=3
    )
]
```

---

#### `search_value_sets_by_label(label_text: str, language_code: str, status: Optional[str]) -> List[ValueSetResponseSchema]`

Searches for value sets containing items with specific label text.

**When to Use:**
- Finding value sets by content
- Content-based discovery

**Example:**
```python
# Find value sets with "Priority" in any item label
results = await service.search_value_sets_by_label(
    label_text="Priority",
    language_code="en",
    status="active"
)

for vs in results:
    print(f"Found: {vs.key} with {len(vs.items)} items")
```

---

### 6. ARCHIVE/RESTORE Operations

#### `archive_value_set(archive_request: ArchiveRestoreRequestSchema) -> ArchiveRestoreResponseSchema`

Archives a value set (soft delete).

**Business Rules:**
- ✅ Value set must exist
- ✅ Cannot archive already archived
- ✅ Changes status to "archived"
- ✅ Updates audit fields

**When to Use:**
- Retiring value sets
- Maintaining history without deletion

**Example:**
```python
from schemas.value_set_schemas_enhanced import ArchiveRestoreRequestSchema

archive_request = ArchiveRestoreRequestSchema(
    key="OLD_PRIORITIES",
    reason="Replaced by new priority system",
    updatedBy="admin_user"
)

response = await service.archive_value_set(archive_request)

if response.success:
    print(f"Archived: {response.key}")
    print(f"Previous status: {response.previousStatus}")
    print(f"Current status: {response.currentStatus}")
    print(f"Message: {response.message}")
else:
    print(f"Failed: {response.message}")
```

**Returns:**
```python
ArchiveRestoreResponseSchema(
    success=True,
    key="OLD_PRIORITIES",
    previousStatus="active",
    currentStatus="archived",
    message="Value set archived successfully: Replaced by new priority system"
)
```

---

#### `restore_value_set(restore_request: ArchiveRestoreRequestSchema) -> ArchiveRestoreResponseSchema`

Restores an archived value set back to active.

**Business Rules:**
- ✅ Value set must exist
- ✅ Must be currently archived
- ✅ Changes status to "active"

**When to Use:**
- Reactivating archived value sets
- Undoing accidental archives

**Example:**
```python
restore_request = ArchiveRestoreRequestSchema(
    key="OLD_PRIORITIES",
    reason="Needed for legacy system support",
    updatedBy="project_manager"
)

response = await service.restore_value_set(restore_request)

if response.success:
    print(f"Restored: {response.key}")
```

---

### 7. BULK OPERATIONS

#### `bulk_import_value_sets(import_data: BulkValueSetCreateSchema) -> BulkOperationResponseSchema`

Creates multiple value sets in one operation.

**Business Rules:**
- ✅ Validates all before creating any
- ✅ Checks key uniqueness
- ✅ Validates items for each value set
- ✅ Partial success supported

**When to Use:**
- Initial system setup
- Data migration
- Importing from external systems

**Example:**
```python
from schemas.value_set_schemas_enhanced import BulkValueSetCreateSchema, ValueSetCreateSchema

value_sets = [
    ValueSetCreateSchema(
        key="STATUSES",
        status=StatusEnum.ACTIVE,
        module="core",
        items=[ItemCreateSchema(code="NEW", labels=LabelSchema(en="New"))],
        createdBy="import_script"
    ),
    ValueSetCreateSchema(
        key="CATEGORIES",
        status=StatusEnum.ACTIVE,
        module="core",
        items=[ItemCreateSchema(code="CAT1", labels=LabelSchema(en="Category 1"))],
        createdBy="import_script"
    )
]

bulk_data = BulkValueSetCreateSchema(valueSets=value_sets)
result = await service.bulk_import_value_sets(bulk_data)

print(f"Created: {result.successful}")
print(f"Failed: {result.failed}")
print(f"Processed keys: {result.processedKeys}")
```

---

#### `bulk_update_value_sets(update_data: BulkValueSetUpdateSchema) -> BulkOperationResponseSchema`

Updates metadata for multiple value sets.

**When to Use:**
- Systematic updates
- Module reassignments
- Status changes across multiple sets

**Example:**
```python
from schemas.value_set_schemas_enhanced import (
    BulkValueSetUpdateSchema,
    BulkValueSetUpdateItemSchema,
    StatusEnum
)

updates = [
    BulkValueSetUpdateItemSchema(
        key="OLD_SET_1",
        status=StatusEnum.ARCHIVED,
        description="Deprecated"
    ),
    BulkValueSetUpdateItemSchema(
        key="OLD_SET_2",
        status=StatusEnum.ARCHIVED,
        description="Deprecated"
    )
]

bulk_data = BulkValueSetUpdateSchema(
    updates=updates,
    updatedBy="cleanup_script"
)

result = await service.bulk_update_value_sets(bulk_data)
print(f"Updated: {result.successful} value sets")
```

---

### 8. VALIDATION

#### `validate_value_set(validation_request: ValidateValueSetRequestSchema) -> ValidationResultSchema`

Validates value set configuration without persisting.

**Validation Checks:**
- ✅ Item code uniqueness
- ✅ Item count (1-500)
- ✅ Required English labels
- ✅ Status values
- ✅ Key conflicts (warning)
- ✅ Large item count performance warning

**When to Use:**
- Before creating/updating
- Pre-import validation
- Data quality checks

**Example:**
```python
from schemas.value_set_schemas_enhanced import (
    ValidateValueSetRequestSchema,
    ItemSchema,
    LabelSchema,
    StatusEnum
)

items = [
    ItemSchema(code="TEST1", labels=LabelSchema(en="Test 1")),
    ItemSchema(code="TEST2", labels=LabelSchema(en="Test 2"))
]

validation_request = ValidateValueSetRequestSchema(
    key="TEST_VALUE_SET",
    status=StatusEnum.ACTIVE,
    module="testing",
    items=items
)

result = await service.validate_value_set(validation_request)

if result.isValid:
    print("✅ Validation passed")
    if result.warnings:
        print("Warnings:")
        for warning in result.warnings:
            print(f"  - {warning}")
else:
    print("❌ Validation failed")
    print("Errors:")
    for error in result.errors:
        print(f"  - {error}")
```

**Returns:**
```python
ValidationResultSchema(
    key="TEST_VALUE_SET",
    isValid=True,
    errors=[],
    warnings=["Key 'TEST_VALUE_SET' already exists"]
)
```

---

### 9. STATISTICS

#### `get_value_set_statistics() -> Dict[str, Any]`

Retrieves comprehensive system statistics.

**Statistics Included:**
- Total value sets
- Count by status
- Count by module
- Item statistics (total, average, min, max)
- Capacity metrics

**When to Use:**
- Admin dashboards
- Monitoring
- Reporting

**Example:**
```python
stats = await service.get_value_set_statistics()

print(f"Total Value Sets: {stats['total_value_sets']}")
print(f"Active: {stats['by_status']['active']}")
print(f"Archived: {stats['by_status']['archived']}")

print("\nBy Module:")
for module, count in stats['by_module'].items():
    print(f"  {module}: {count}")

items_stats = stats['items_statistics']
print(f"\nTotal Items: {items_stats['total_items']}")
print(f"Average per Set: {items_stats['avg_items']:.1f}")
print(f"Capacity Used: {items_stats['capacity_used_percent']:.2f}%")
```

---

### 10. IMPORT/EXPORT

#### `export_value_set(key: str, format: str) -> Dict[str, Any]`

Exports value set in specified format.

**Supported Formats:**
- `json`: Complete structured data
- `csv`: Tabular format with items

**When to Use:**
- Backups
- Data transfer
- External integrations

**Example:**
```python
# Export as JSON
json_export = await service.export_value_set("PRIORITY_LEVELS", "json")
print(json_export)

# Export as CSV
csv_export = await service.export_value_set("PRIORITY_LEVELS", "csv")
print(f"Format: {csv_export['format']}")
print(f"Content:\n{csv_export['content']}")
print(f"Metadata: {csv_export['metadata']}")
```

**Raises:**
- `ValueError`: If value set not found or format unsupported

---

#### `import_value_set(import_data: dict, format: str, created_by: str) -> ValueSetResponseSchema`

Imports value set from external data.

**Supported Formats:**
- `json`: Structured data
- `csv`: Not yet implemented

**When to Use:**
- Restoring from backup
- Data migration
- External system integration

**Example:**
```python
import_data = {
    "key": "IMPORTED_SET",
    "status": "active",
    "module": "imported",
    "description": "Imported from backup",
    "items": [
        {"code": "IMP1", "labels": {"en": "Imported 1"}}
    ]
}

result = await service.import_value_set(
    import_data=import_data,
    format="json",
    created_by="import_user"
)

print(f"Imported: {result.key}")
```

**Raises:**
- `ValueError`: If key exists or invalid format
- `NotImplementedError`: If CSV import attempted

---

## 🔄 Common Usage Patterns

### Pattern 1: Complete CRUD Workflow
```python
# Create
create_data = ValueSetCreateSchema(...)
created = await service.create_value_set(create_data)

# Read
value_set = await service.get_value_set_by_key(created.key)

# Update
update_data = ValueSetUpdateSchema(description="Updated", updatedBy="user")
updated = await service.update_value_set(created.key, update_data)

# Archive (soft delete)
archive_request = ArchiveRestoreRequestSchema(key=created.key, updatedBy="user")
await service.archive_value_set(archive_request)
```

### Pattern 2: Error Handling
```python
try:
    result = await service.create_value_set(create_data)
    print(f"Success: {result.key}")
except ValueError as e:
    # Business rule violation
    print(f"Validation error: {e}")
except Exception as e:
    # Unexpected error
    print(f"System error: {e}")
```

### Pattern 3: Batch Operations
```python
# Validate first
validation_result = await service.validate_value_set(validation_request)
if not validation_result.isValid:
    print("Validation failed:", validation_result.errors)
    return

# Then import in bulk
bulk_result = await service.bulk_import_value_sets(bulk_data)
print(f"Imported {bulk_result.successful} value sets")
```

---

## ⚠️ Important Notes

### Business Rule Enforcement
The service layer is responsible for ALL business rules:
```python
# ✅ Service enforces: Key uniqueness
if await self.repository.check_key_exists(create_data.key):
    raise ValueError(f"Key '{create_data.key}' already exists")

# ✅ Service enforces: Item limits
if not (1 <= len(create_data.items) <= 500):
    raise ValueError("Items must be between 1 and 500")
```

### Audit Trail Management
Service automatically manages audit fields:
```python
# On create:
document['createdAt'] = create_data.createdAt or datetime.utcnow()
document['createdBy'] = create_data.createdBy
document['updatedAt'] = None
document['updatedBy'] = None

# On update:
update_fields['updatedAt'] = update_data.updatedAt or datetime.utcnow()
update_fields['updatedBy'] = update_data.updatedBy
```

### Exception Handling
Service raises specific exceptions:
- `ValueError`: Business rule violations
- Returns `None`: When resource not found (not an exception)

---

## 🚫 What NOT to Do

### ❌ Don't Skip Service Layer
```python
# ❌ WRONG - Router calling repository directly
@router.post("/")
async def create(data, repo: ValueSetRepository):
    return await repo.create(data)  # No validation!

# ✅ RIGHT - Router calling service
@router.post("/")
async def create(data, service: ValueSetService):
    return await service.create_value_set(data)  # With validation!
```

### ❌ Don't Put HTTP Logic in Service
```python
# ❌ WRONG - HTTP concerns in service
async def create_value_set(self, data):
    result = await self.repository.create(data)
    return JSONResponse(content=result)  # HTTP response in service!

# ✅ RIGHT - Return data only
async def create_value_set(self, data):
    result = await self.repository.create(data)
    return ValueSetResponseSchema(**result)  # Schema object
```

### ❌ Don't Put Database Queries in Service
```python
# ❌ WRONG - Direct DB query in service
async def get_value_set(self, key):
    result = await self.db.value_sets.find_one({'key': key})  # Direct query!

# ✅ RIGHT - Use repository
async def get_value_set_by_key(self, key):
    result = await self.repository.find_by_key(key)  # Through repository
```

---

## 🔗 Integration with Other Layers

### Called By: Router Layer
```python
# routers/value_set_router.py
@router.post("/")
async def create_value_set(
    create_data: ValueSetCreateSchema,
    service: ValueSetService = Depends(get_value_set_service)
):
    return await service.create_value_set(create_data)
```

### Calls: Repository Layer
```python
# services/value_set_service.py
class ValueSetService:
    def __init__(self, repository: ValueSetRepository):
        self.repository = repository

    async def create_value_set(self, data):
        # Business logic
        if await self.repository.check_key_exists(data.key):
            raise ValueError("Key exists")
        # Call repository
        return await self.repository.create(document)
```

---

## 📖 Further Reading

- Clean Architecture: https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html
- Domain-Driven Design Service Layer
- Business Logic Patterns

---

**Last Updated:** 2025-09-27
**Maintained By:** Value Set Development Team