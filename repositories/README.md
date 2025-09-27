# Repository Layer Documentation

## 📁 Overview

The **Repository Layer** is the **data access layer** that handles all direct interactions with MongoDB. It provides a clean abstraction over database operations, allowing the service layer to work with data without knowing the underlying storage mechanism.

## 🎯 Purpose

> **"The repository layer talks to the database, so your business logic doesn't have to."**

### Key Responsibilities:
- ✅ Direct MongoDB queries and updates
- ✅ Data persistence and retrieval
- ✅ Query optimization
- ✅ Database connection management
- ✅ Collection-specific operations
- ✅ ObjectId conversions

### What Repository Layer Does NOT Do:
- ❌ Business logic validation
- ❌ User authentication
- ❌ Complex business rules
- ❌ API request handling
- ❌ Data transformation (beyond DB format)

---

## 📂 Files in This Folder

```
repositories/
├── value_set_repository.py    # Main repository for value set operations
└── README.md                   # This file
```

---

## 🔧 ValueSetRepository Class

### Location
`repositories/value_set_repository.py`

### Purpose
Handles all MongoDB CRUD operations for the `value_sets` collection.

### Initialization

```python
from motor.motor_asyncio import AsyncIOMotorDatabase
from repositories.value_set_repository import ValueSetRepository

# Initialize with database connection
repository = ValueSetRepository(database=db)
```

---

## 📚 Available Methods

### 1. CREATE Operations

#### `create(value_set_data: dict) -> dict`
Creates a new value set document.

**When to Use:**
- Creating new value sets in the database
- Initial data insertion

**Input Format:**
```python
{
    'key': 'COUNTRY_CODES',
    'module': 'geography',
    'status': 'active',
    'description': 'ISO country codes',
    'items': [
        {
            'code': 'US',
            'labels': {'en': 'United States', 'hi': 'संयुक्त राज्य अमेरिका'}
        },
        {
            'code': 'IN',
            'labels': {'en': 'India', 'hi': 'भारत'}
        }
    ],
    'createdAt': datetime(2024, 1, 15, 10, 30, 0),
    'createdBy': 'user123',
    'updatedAt': None,
    'updatedBy': None
}
```

**Output Format:**
```python
{
    '_id': '507f1f77bcf86cd799439011',  # Generated MongoDB ObjectId (as string)
    'key': 'COUNTRY_CODES',
    'module': 'geography',
    'status': 'active',
    'description': 'ISO country codes',
    'items': [
        {
            'code': 'US',
            'labels': {'en': 'United States', 'hi': 'संयुक्त राज्य अमेरिका'}
        },
        {
            'code': 'IN',
            'labels': {'en': 'India', 'hi': 'भारत'}
        }
    ],
    'createdAt': datetime(2024, 1, 15, 10, 30, 0),
    'createdBy': 'user123',
    'updatedAt': None,
    'updatedBy': None
}
```

**Example:**
```python
value_set_data = {
    'key': 'COUNTRY_CODES',
    'module': 'geography',
    'status': 'active',
    'items': [
        {'code': 'US', 'labels': {'en': 'United States'}}
    ],
    'createdAt': datetime.utcnow(),
    'createdBy': 'user123'
}

result = await repository.create(value_set_data)
print(f"Created with ID: {result['_id']}")
```

---

#### `bulk_create(value_sets: List[dict]) -> Dict[str, Any]`
Creates multiple value sets in one operation.

**When to Use:**
- Importing multiple value sets
- Initial system setup
- Data migration

**Example:**
```python
value_sets = [
    {
        'key': 'COUNTRIES',
        'module': 'geography',
        'status': 'active',
        'items': [],
        'createdAt': datetime.utcnow(),
        'createdBy': 'import_script'
    },
    {
        'key': 'LANGUAGES',
        'module': 'localization',
        'status': 'active',
        'items': [],
        'createdAt': datetime.utcnow(),
        'createdBy': 'import_script'
    }
]

result = await repository.bulk_create(value_sets)
print(f"Created {result['successful']} value sets")
print(f"Failed {result['failed']} value sets")
```

**Returns:**
```python
{
    'successful': 2,
    'failed': 0,
    'inserted_ids': ['507f...', '507f...']
}
```

---

### 2. READ Operations

#### `find_by_key(key: str) -> Optional[dict]`
Retrieves a value set by its unique business key.

**When to Use:**
- Looking up value sets by their business identifier
- Most common read operation

**Example:**
```python
value_set = await repository.find_by_key('COUNTRY_CODES')

if value_set:
    print(f"Found: {value_set['key']}")
    print(f"Items: {len(value_set['items'])}")
else:
    print("Value set not found")
```

**Returns:**
```python
{
    '_id': '507f1f77bcf86cd799439011',
    'key': 'COUNTRY_CODES',
    'status': 'active',
    'module': 'geography',
    'items': [...],
    'createdAt': datetime(...),
    'createdBy': 'user123'
}
# OR None if not found
```

---

#### `find_by_id(value_set_id: str) -> Optional[dict]`
Retrieves a value set by MongoDB ObjectId.

**When to Use:**
- When you have the MongoDB document ID
- Internal references

**Example:**
```python
doc_id = '507f1f77bcf86cd799439011'
value_set = await repository.find_by_id(doc_id)

if value_set:
    print(f"Key: {value_set['key']}")
```

---

#### `list_value_sets(filter_query: dict, skip: int, limit: int, sort_by: List[tuple]) -> tuple[List[dict], int]`
Lists value sets with pagination and filtering.

**When to Use:**
- Displaying paginated lists
- Filtering by status or module
- Admin dashboards

**Input Format:**
```python
filter_query = {
    'status': 'active',  # Optional filter
    'module': 'healthcare'  # Optional filter
}
skip = 0  # Number of records to skip
limit = 20  # Max records to return
sort_by = [('createdAt', -1)]  # Sort by createdAt descending
```

**Output Format:**
```python
(
    [  # List of document dictionaries
        {
            '_id': '507f1f77bcf86cd799439011',
            'key': 'MEDICAL_SPECIALTIES',
            'status': 'active',
            'module': 'healthcare',
            'description': 'Medical specialties',
            'items': [
                {'code': 'CARDIO', 'labels': {'en': 'Cardiology'}}
            ],
            'createdAt': datetime(2024, 1, 15, 10, 30, 0),
            'createdBy': 'user123',
            'updatedAt': None,
            'updatedBy': None
        },
        {
            '_id': '507f1f77bcf86cd799439012',
            'key': 'DIAGNOSIS_CODES',
            'status': 'active',
            'module': 'healthcare',
            'description': 'Diagnosis codes',
            'items': [...],
            'createdAt': datetime(2024, 1, 14, 9, 15, 0),
            'createdBy': 'admin',
            'updatedAt': None,
            'updatedBy': None
        }
    ],
    45  # Total count matching filter (not just this page)
)
```

**Example:**
```python
# Get active value sets, page 1, 20 per page
filter_query = {'status': 'active'}
documents, total = await repository.list_value_sets(
    filter_query=filter_query,
    skip=0,
    limit=20,
    sort_by=[('createdAt', -1)]  # Newest first
)

print(f"Showing {len(documents)} of {total} total")
for doc in documents:
    print(f"- {doc['key']}: {len(doc['items'])} items")
```

---

#### `get_items_by_key(key: str) -> Optional[List[dict]]`
Retrieves only the items array (performance optimization).

**When to Use:**
- When you only need items, not full value set
- Building dropdown lists
- Faster than fetching entire document

**Example:**
```python
items = await repository.get_items_by_key('COUNTRY_CODES')

if items:
    for item in items:
        print(f"{item['code']}: {item['labels']['en']}")
else:
    print("Value set not found")
```

**Returns:**
```python
[
    {'code': 'US', 'labels': {'en': 'United States'}},
    {'code': 'CA', 'labels': {'en': 'Canada'}},
    # ... more items
]
# OR None if value set not found
```

---

### 3. UPDATE Operations

#### `update_by_key(key: str, update_data: dict) -> Optional[dict]`
Updates specific fields of a value set.

**When to Use:**
- Updating metadata (status, description, etc.)
- Modifying value set properties

**Example:**
```python
updates = {
    'status': 'archived',
    'updatedAt': datetime.utcnow(),
    'updatedBy': 'admin_user'
}

updated = await repository.update_by_key('OLD_CODES', updates)

if updated:
    print(f"Status changed to: {updated['status']}")
else:
    print("Value set not found")
```

**Returns:**
Complete updated document or None.

---

#### `bulk_update(operations: List[Dict[str, Any]]) -> Dict[str, Any]`
Updates multiple value sets in one operation.

**When to Use:**
- Systematic updates across many value sets
- Bulk status changes
- Module reassignments

**Example:**
```python
operations = [
    {
        'key': 'OLD_COUNTRIES',
        'updates': {
            'status': 'archived',
            'updatedAt': datetime.utcnow()
        }
    },
    {
        'key': 'DEPRECATED_CODES',
        'updates': {
            'status': 'archived',
            'updatedAt': datetime.utcnow()
        }
    }
]

result = await repository.bulk_update(operations)
print(f"Updated {result['modified']} of {result['matched']} documents")
```

---

### 4. ITEM Management Operations

#### `add_item(key: str, new_item: dict, update_fields: dict) -> Optional[dict]`
Adds a single item to a value set's items array.

**When to Use:**
- Adding one new option to a value set
- Interactive item addition

**Example:**
```python
new_item = {
    'code': 'HIGH',
    'labels': {'en': 'High Priority'},
    'active': True
}

update_fields = {
    'updatedAt': datetime.utcnow(),
    'updatedBy': 'admin_user'
}

result = await repository.add_item('PRIORITY_LEVELS', new_item, update_fields)

if result:
    print(f"Added item, total items: {len(result['items'])}")
```

---

#### `update_item(key: str, item_code: str, item_updates: dict, update_fields: dict) -> Optional[dict]`
Updates specific fields of an item within a value set.

**When to Use:**
- Modifying item labels
- Changing item properties
- Updating individual codes

**Example:**
```python
item_updates = {
    'labels.en': 'Updated Priority Level',
    'active': False
}

update_fields = {
    'updatedAt': datetime.utcnow(),
    'updatedBy': 'admin_user'
}

result = await repository.update_item(
    key='PRIORITY_LEVELS',
    item_code='HIGH',
    item_updates=item_updates,
    update_fields=update_fields
)

if result:
    updated_item = next(item for item in result['items'] if item['code'] == 'HIGH')
    print(f"Updated label: {updated_item['labels']['en']}")
```

---

#### `replace_item_value(key: str, old_code: str, new_item: dict, update_fields: dict) -> Optional[dict]`
Completely replaces an item (removes old, adds new).

**When to Use:**
- Changing item codes
- Complete item restructuring
- Item migrations

**Example:**
```python
old_code = 'TEMP_CODE'
new_item = {
    'code': 'PERMANENT_CODE',
    'labels': {'en': 'Permanent Status'},
    'priority': 1,
    'active': True
}

update_fields = {
    'updatedAt': datetime.utcnow(),
    'updatedBy': 'migration_script'
}

result = await repository.replace_item_value(
    key='STATUS_CODES',
    old_code=old_code,
    new_item=new_item,
    update_fields=update_fields
)

if result:
    codes = [item['code'] for item in result['items']]
    print(f"Updated codes: {codes}")
```

---

#### `bulk_add_items(operations: List[Dict[str, Any]]) -> Dict[str, Any]`
Adds multiple items to multiple value sets efficiently.

**When to Use:**
- Importing data
- Bulk item creation
- Better performance than individual adds

**Example:**
```python
operations = [
    {
        'key': 'COUNTRIES',
        'items': [
            {'code': 'US', 'labels': {'en': 'United States'}},
            {'code': 'CA', 'labels': {'en': 'Canada'}}
        ],
        'update_fields': {
            'updatedAt': datetime.utcnow(),
            'updatedBy': 'import_script'
        }
    }
]

result = await repository.bulk_add_items(operations)
print(f"Modified {result['modified']} value sets")
```

---

#### `bulk_update_items(operations: List[Dict[str, Any]]) -> Dict[str, Any]`
Updates multiple items across different value sets.

**When to Use:**
- Bulk item modifications
- Systematic changes to many items
- Need detailed error reporting

**Example:**
```python
operations = [
    {
        'key': 'USER_ROLES',
        'item_code': 'ADMIN',
        'updates': {'active': False},
        'update_fields': {'updatedAt': datetime.utcnow()}
    },
    {
        'key': 'USER_ROLES',
        'item_code': 'USER',
        'updates': {'active': True},
        'update_fields': {}
    }
]

result = await repository.bulk_update_items(operations)
print(f"Success: {result['successful']}, Failed: {result['failed']}")
for error in result['errors']:
    print(f"Error in {error['key']}.{error['item_code']}: {error['error']}")
```

---

### 5. SEARCH Operations

#### `search_items(search_query: str, value_set_key: Optional[str], language_code: str) -> List[dict]`
Searches for items by code or label text.

**When to Use:**
- Autocomplete functionality
- User search features
- Finding specific items

**Input Format:**
```python
search_query = 'United'  # Text to search for
value_set_key = 'COUNTRY_CODES'  # Optional: specific value set, None for all
language_code = 'en'  # Language to search in labels
```

**Output Format:**
```python
[
    {
        '_id': '507f1f77bcf86cd799439011',
        'key': 'COUNTRY_CODES',
        'module': 'geography',
        'matchingItems': [  # Only items that match, not all items
            {
                'code': 'US',
                'labels': {'en': 'United States', 'hi': 'संयुक्त राज्य अमेरिका'}
            },
            {
                'code': 'GB',
                'labels': {'en': 'United Kingdom', 'hi': 'यूनाइटेड किंगडम'}
            }
        ]
    }
]
```

**Example:**
```python
# Search for countries containing 'United'
results = await repository.search_items(
    search_query='United',
    value_set_key='COUNTRY_CODES',
    language_code='en'
)

for value_set in results:
    print(f"Found {len(value_set['matchingItems'])} matches in {value_set['key']}")
    for item in value_set['matchingItems']:
        print(f"  {item['code']}: {item['labels']['en']}")
```

---

#### `search_by_label(label_text: str, language_code: str, status_filter: Optional[str]) -> List[dict]`
Searches for value sets containing items with specific label text.

**When to Use:**
- Finding value sets by content
- Global search across value sets

**Example:**
```python
# Find value sets containing 'Admin' in English labels
results = await repository.search_by_label(
    label_text='Admin',
    language_code='en',
    status_filter='active'
)

for value_set in results:
    print(f"Value set {value_set['key']} contains 'Admin' labels")
    print(f"Total items: {len(value_set['items'])}")
```

---

### 6. ARCHIVE/RESTORE Operations

#### `archive(key: str, update_fields: dict) -> Optional[dict]`
Archives a value set (soft delete).

**When to Use:**
- Retiring value sets without deletion
- Maintaining historical data

**Example:**
```python
archive_fields = {
    'archivedAt': datetime.utcnow(),
    'archivedBy': 'system_admin',
    'archiveReason': 'Replaced by new version'
}

archived = await repository.archive('OLD_COUNTRY_CODES', archive_fields)

if archived:
    print(f"Archived {archived['key']} with {len(archived['items'])} items")
```

---

#### `restore(key: str, update_fields: dict) -> Optional[dict]`
Restores an archived value set back to active.

**When to Use:**
- Reactivating archived value sets
- Undoing accidental archives

**Example:**
```python
restore_fields = {
    'restoredAt': datetime.utcnow(),
    'restoredBy': 'project_manager',
    'restoreReason': 'Required for legacy system'
}

restored = await repository.restore('LEGACY_CODES', restore_fields)

if restored:
    print(f"Restored {restored['key']} to active status")
```

---

### 7. STATISTICS & EXPORT

#### `get_statistics() -> Dict[str, Any]`
Generates comprehensive statistics about value sets.

**When to Use:**
- Admin dashboards
- System monitoring
- Reporting

**Example:**
```python
stats = await repository.get_statistics()

print(f"Total Value Sets: {stats['total_value_sets']}")
print(f"Active: {stats['by_status'].get('active', 0)}")
print(f"Archived: {stats['by_status'].get('archived', 0)}")

print("\nBy Module:")
for module, count in stats['by_module'].items():
    print(f"  {module}: {count}")

items_stats = stats['items_statistics']
if items_stats:
    print(f"\nItems: {items_stats.get('total_items', 0)} total")
    print(f"Average per set: {items_stats.get('avg_items', 0):.1f}")
```

**Returns:**
```python
{
    'total_value_sets': 50,
    'by_status': {'active': 45, 'archived': 5},
    'by_module': {'core': 20, 'geography': 15, 'hr': 15},
    'items_statistics': {
        'total_items': 1250,
        'avg_items': 25.0,
        'max_items': 500,
        'min_items': 5
    }
}
```

---

#### `export_value_set(key: str) -> Optional[dict]`
Exports a clean value set document for backup.

**When to Use:**
- Backups
- Data transfer between environments
- Before major changes

**Example:**
```python
exported = await repository.export_value_set('COUNTRY_CODES')

if exported:
    import json
    with open('country_codes_backup.json', 'w') as f:
        json.dump(exported, f, indent=2, default=str)

    print(f"Exported {len(exported['items'])} items")
```

---

#### `import_value_set(value_set_data: dict) -> dict`
Imports a value set from external source.

**When to Use:**
- Restoring from backup
- Data migration
- Loading from config files

**Example:**
```python
import json
with open('country_codes_backup.json', 'r') as f:
    backup_data = json.load(f)

# Ensure proper datetime objects
from datetime import datetime
backup_data['createdAt'] = datetime.fromisoformat(backup_data['createdAt'])

imported = await repository.import_value_set(backup_data)
print(f"Imported {imported['key']} with new ID: {imported['_id']}")
```

---

#### `check_key_exists(key: str) -> bool`
Checks if a value set key already exists.

**When to Use:**
- Before creating new value sets
- Validation
- Key availability checking

**Example:**
```python
new_key = 'DEPARTMENT_CODES'

if await repository.check_key_exists(new_key):
    print(f"Key '{new_key}' already exists")
else:
    print(f"Key '{new_key}' is available")
    # Proceed with creation
```

---

## 🔄 Common Usage Patterns

### Pattern 1: Create and Retrieve
```python
# Create
new_value_set = {
    'key': 'PRIORITIES',
    'module': 'task_management',
    'status': 'active',
    'items': [],
    'createdAt': datetime.utcnow(),
    'createdBy': 'admin'
}
created = await repository.create(new_value_set)

# Retrieve
value_set = await repository.find_by_key('PRIORITIES')
print(value_set['_id'])
```

### Pattern 2: List with Pagination
```python
page = 1
page_size = 20
skip = (page - 1) * page_size

documents, total = await repository.list_value_sets(
    filter_query={'status': 'active'},
    skip=skip,
    limit=page_size,
    sort_by=[('key', 1)]
)

total_pages = (total + page_size - 1) // page_size
print(f"Page {page} of {total_pages}")
```

### Pattern 3: Update with Audit Trail
```python
updates = {
    'description': 'Updated description',
    'updatedAt': datetime.utcnow(),
    'updatedBy': request.user.id
}
await repository.update_by_key('MY_VALUE_SET', updates)
```

---

## ⚠️ Important Notes

### ObjectId Conversion
The repository automatically converts MongoDB `ObjectId` to string for JSON serialization:
```python
# MongoDB stores: ObjectId('507f1f77bcf86cd799439011')
# Repository returns: '_id': '507f1f77bcf86cd799439011'
```

### Null Handling
Methods return `None` when documents are not found (not exceptions):
```python
result = await repository.find_by_key('NONEXISTENT')
if result is None:
    print("Not found")
```

### Bulk Operations Performance
Use bulk operations when possible for better performance:
```python
# ❌ Slow - 100 database calls
for item in items:
    await repository.add_item(key, item, update_fields)

# ✅ Fast - 1 database call
await repository.bulk_add_items([{
    'key': key,
    'items': items,
    'update_fields': update_fields
}])
```

---

## 🚫 What NOT to Do

### ❌ Don't Use Repository for Business Logic
```python
# ❌ WRONG - Business logic in repository
async def create(self, data):
    if len(data['items']) > 500:
        raise ValueError("Too many items")  # This belongs in SERVICE layer
    return await self.collection.insert_one(data)
```

### ❌ Don't Access Database Directly
```python
# ❌ WRONG - Bypassing repository
from database import get_database
db = get_database()
result = await db.value_sets.find_one({'key': 'TEST'})

# ✅ RIGHT - Use repository
result = await repository.find_by_key('TEST')
```

### ❌ Don't Mix Concerns
```python
# ❌ WRONG - HTTP concerns in repository
async def create(self, data):
    result = await self.collection.insert_one(data)
    return JSONResponse(content=result)  # This belongs in ROUTER layer

# ✅ RIGHT - Return data only
async def create(self, data):
    result = await self.collection.insert_one(data)
    return result
```

---

## 🔗 Integration with Other Layers

### Used By: Service Layer
```python
# services/value_set_service.py
class ValueSetService:
    def __init__(self, repository: ValueSetRepository):
        self.repository = repository

    async def create_value_set(self, data):
        # Business logic here
        if await self.repository.check_key_exists(data.key):
            raise ValueError("Key exists")

        # Call repository
        return await self.repository.create(document)
```

### Not Used By: Routers (should go through service)
```python
# ❌ WRONG
@router.post("/")
async def create(data, repo: ValueSetRepository = Depends(...)):
    return await repo.create(data)

# ✅ RIGHT
@router.post("/")
async def create(data, service: ValueSetService = Depends(...)):
    return await service.create_value_set(data)
```

---

## 📖 Further Reading

- MongoDB Motor Documentation: https://motor.readthedocs.io/
- MongoDB Query Documentation: https://docs.mongodb.com/manual/tutorial/query-documents/
- Repository Pattern: https://martinfowler.com/eaaCatalog/repository.html

---

**Last Updated:** 2025-09-27
**Maintained By:** Value Set Development Team