# Value Set Library - Complete Function Reference

## Table of Contents
1. [Overview](#overview)
2. [Installation & Setup](#installation--setup)
3. [Core Concepts](#core-concepts)
4. [Function Categories](#function-categories)
5. [Detailed Function Reference](#detailed-function-reference)
6. [Use Cases & Examples](#use-cases--examples)
7. [Best Practices](#best-practices)

---

## Overview

The Value Set Library is a comprehensive MongoDB-based solution for managing reusable enumeration lists (value sets) with multilingual support. It's designed for enterprise applications that need centralized management of dropdown lists, lookup tables, and reference data.

### What are Value Sets?
Value sets are collections of code-label pairs used throughout applications for:
- Dropdown menus (countries, states, categories)
- Status codes (active, pending, completed)
- Type classifications (product types, user roles)
- Reference data (currencies, languages, time zones)

### Key Features
- 🌐 **Multilingual Support**: Store labels in multiple languages
- 📦 **Bulk Operations**: Process multiple items efficiently
- 🔍 **Advanced Search**: Search across codes and labels
- 📊 **Statistics**: Track usage and metrics
- ♻️ **Soft Delete**: Archive/restore functionality
- 📁 **Export/Import**: JSON and CSV support
- ✅ **Validation**: Built-in data integrity checks

---

## Installation & Setup

### Basic Setup
```python
from motor.motor_asyncio import AsyncIOMotorClient
from value_set_lib import ValueSetLibrary

# Connect to MongoDB
client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client.your_database

# Initialize the library
lib = ValueSetLibrary(database=db, collection_name="value_sets")
```

### With Environment Variables
```python
import os
from motor.motor_asyncio import AsyncIOMotorClient
from value_set_lib import ValueSetLibrary

# Load from environment
MONGODB_URI = os.getenv("MONGODB_CONNECTION_STRING")
DB_NAME = os.getenv("DB_NAME")

client = AsyncIOMotorClient(MONGODB_URI)
db = client[DB_NAME]
lib = ValueSetLibrary(database=db)
```

---

## Core Concepts

### Value Set Structure
```json
{
    "key": "country_codes",        // Unique identifier
    "status": "active",             // active or archived
    "module": "Geography",          // Logical grouping
    "description": "ISO 3166-1 country codes",
    "items": [                     // Array of code-label pairs
        {
            "code": "US",
            "labels": {
                "en": "United States",
                "hi": "संयुक्त राज्य"
            }
        }
    ],
    "createdAt": "2024-01-01T00:00:00Z",
    "createdBy": "admin",
    "updatedAt": null,
    "updatedBy": null
}
```

### Item Structure
```json
{
    "code": "ACTIVE",              // Unique code within the value set
    "labels": {
        "en": "Active",            // English label (required)
        "hi": "सक्रिय"             // Hindi label (optional)
    }
}
```

---

## Function Categories

### 1. CREATE Operations
Functions for creating new value sets and items

### 2. READ Operations
Functions for retrieving and searching value sets

### 3. UPDATE Operations
Functions for modifying existing value sets and items

### 4. DELETE Operations
Functions for removing value sets and items

### 5. ARCHIVE/RESTORE Operations
Functions for soft deletion and recovery

### 6. VALIDATION Operations
Functions for data integrity checking

### 7. EXPORT/IMPORT Operations
Functions for data portability

### 8. STATISTICS Operations
Functions for metrics and analytics

---

## Detailed Function Reference

## 1. CREATE Operations

### `create_value_set()`
**Purpose**: Create a new value set with validation

**When to Use**:
- Setting up new dropdown lists
- Adding new reference data categories
- Initializing application enumerations

**Input Format**:
```python
await lib.create_value_set(
    key="status_codes",           # string, unique identifier (required)
    status="active",               # string, "active" or "archived" (required)
    module="System",               # string, module/category name (required)
    items=[                        # list of dict, min 1, max 500 (required)
        {
            "code": "NEW",
            "labels": {
                "en": "New",       # English label (required)
                "hi": "नया"        # Hindi label (optional)
            }
        }
    ],
    created_by="admin",            # string, user identifier (required)
    description="Order statuses",   # string, max 500 chars (optional)
    created_at=datetime.utcnow()   # datetime object (optional)
)
```

**Output Format**:
```python
{
    "_id": "507f1f77bcf86cd799439011",
    "key": "status_codes",
    "status": "active",
    "module": "System",
    "description": "Order statuses",
    "items": [...],
    "createdAt": "2024-01-01T00:00:00Z",
    "createdBy": "admin",
    "updatedAt": None,
    "updatedBy": None
}
```

**Example Use Case**:
```python
# Creating product categories for an e-commerce site
categories = await lib.create_value_set(
    key="product_categories",
    status="active",
    module="Products",
    items=[
        {"code": "ELECTRONICS", "labels": {"en": "Electronics", "hi": "इलेक्ट्रॉनिक्स"}},
        {"code": "CLOTHING", "labels": {"en": "Clothing", "hi": "कपड़े"}},
        {"code": "BOOKS", "labels": {"en": "Books", "hi": "किताबें"}}
    ],
    created_by="product_manager",
    description="Main product categories"
)
```

---

### `bulk_create_value_sets()`
**Purpose**: Create multiple value sets in a single operation

**When to Use**:
- Initial data migration
- Importing reference data from external systems
- Batch setup of application configurations

**Input Format**:
```python
await lib.bulk_create_value_sets(
    value_sets=[                   # list of value set dictionaries
        {
            "key": "colors",
            "status": "active",
            "module": "UI",
            "items": [
                {"code": "RED", "labels": {"en": "Red"}},
                {"code": "BLUE", "labels": {"en": "Blue"}}
            ],
            "createdBy": "system"
        },
        {
            "key": "sizes",
            "status": "active",
            "module": "Products",
            "items": [
                {"code": "S", "labels": {"en": "Small"}},
                {"code": "M", "labels": {"en": "Medium"}},
                {"code": "L", "labels": {"en": "Large"}}
            ],
            "createdBy": "system"
        }
    ],
    skip_existing=True              # bool, skip if key exists (default: True)
)
```

**Output Format**:
```python
{
    "created": ["colors", "sizes"],         # Successfully created keys
    "failed": [                              # Failed operations
        {
            "key": "existing_key",
            "error": "Key already exists"
        }
    ],
    "skipped": ["duplicate_key"],           # Skipped due to skip_existing
    "summary": {
        "total": 3,
        "created": 2,
        "failed": 0,
        "skipped": 1
    }
}
```

---

## 2. READ Operations

### `get_value_set_by_key()`
**Purpose**: Retrieve a single value set by its unique key

**When to Use**:
- Loading dropdown options
- Fetching specific reference data
- Validating against allowed values

**Input Format**:
```python
await lib.get_value_set_by_key(
    key="country_codes"            # string, value set key
)
```

**Output Format**:
```python
{
    "_id": "507f1f77bcf86cd799439011",
    "key": "country_codes",
    "status": "active",
    "module": "Geography",
    "items": [
        {"code": "US", "labels": {"en": "United States", "hi": "संयुक्त राज्य"}},
        {"code": "IN", "labels": {"en": "India", "hi": "भारत"}}
    ],
    "createdAt": "2024-01-01T00:00:00Z",
    "createdBy": "admin"
}
# Returns None if not found
```

---

### `list_value_sets()`
**Purpose**: List value sets with pagination, filtering, and sorting

**When to Use**:
- Building admin interfaces
- Displaying available value sets
- Generating reports

**Input Format**:
```python
await lib.list_value_sets(
    skip=0,                        # int, records to skip (pagination)
    limit=100,                     # int, max records to return (1-1000)
    status="active",               # string, filter by status (optional)
    module="Geography",            # string, filter by module (optional)
    search="country",              # string, search in key/description (optional)
    sort_by="key",                 # string, field to sort by (default: "key")
    sort_order="asc"               # string, "asc" or "desc" (default: "asc")
)
```

**Output Format**:
```python
(
    [                              # List of value sets
        {
            "_id": "507f1f77bcf86cd799439011",
            "key": "country_codes",
            "status": "active",
            "module": "Geography",
            "description": "ISO country codes",
            "items": [...],
            "createdAt": "2024-01-01T00:00:00Z"
        }
    ],
    125                            # Total count for pagination
)
```

---

### `search_items()`
**Purpose**: Search for items across all value sets

**When to Use**:
- Global search functionality
- Finding specific codes across categories
- Auto-complete features

**Input Format**:
```python
await lib.search_items(
    query="United",                # string, search text
    language_code="en",            # string, "en" or "hi" (default: "en")
    skip=0,                        # int, pagination skip
    limit=100                      # int, max results
)
```

**Output Format**:
```python
(
    [                              # List of matching value sets with items
        {
            "key": "country_codes",
            "module": "Geography",
            "description": "ISO country codes",
            "items": [              # Only matching items
                {"code": "US", "labels": {"en": "United States"}},
                {"code": "GB", "labels": {"en": "United Kingdom"}}
            ]
        }
    ],
    2                              # Total count
)
```

---

### `search_by_label()`
**Purpose**: Find value sets containing specific label text

**When to Use**:
- Finding value sets by content
- Reverse lookup from label to code
- Content-based discovery

**Input Format**:
```python
await lib.search_by_label(
    label_text="India",            # string, text to search
    language_code="en",            # string, language to search in
    skip=0,                        # int, pagination
    limit=100                      # int, max results
)
```

**Output Format**:
```python
(
    [                              # Value sets containing the label
        {
            "_id": "507f1f77bcf86cd799439011",
            "key": "country_codes",
            "status": "active",
            "items": [...]          # All items in the value set
        }
    ],
    1                              # Total count
)
```

---

### `get_items_by_codes()`
**Purpose**: Get specific items from a value set

**When to Use**:
- Fetching subset of options
- Validating multiple codes
- Building filtered dropdowns

**Input Format**:
```python
await lib.get_items_by_codes(
    key="country_codes",           # string, value set key
    codes=["US", "IN", "GB"]       # list of strings, item codes
)
```

**Output Format**:
```python
[                                  # List of matching items
    {"code": "US", "labels": {"en": "United States"}},
    {"code": "IN", "labels": {"en": "India"}},
    {"code": "GB", "labels": {"en": "United Kingdom"}}
]
```

---

## 3. UPDATE Operations

### `update_value_set()`
**Purpose**: Update value set metadata

**When to Use**:
- Changing descriptions
- Updating module assignments
- Modifying status

**Input Format**:
```python
await lib.update_value_set(
    key="country_codes",           # string, value set to update
    updates={                      # dict, fields to update
        "description": "Updated ISO country codes",
        "module": "Reference",
        "status": "archived"
    },
    updated_by="admin",            # string, user performing update
    updated_at=datetime.utcnow()   # datetime, optional timestamp
)
```

**Output Format**:
```python
{
    "_id": "507f1f77bcf86cd799439011",
    "key": "country_codes",
    "status": "archived",           # Updated fields
    "module": "Reference",
    "description": "Updated ISO country codes",
    "updatedAt": "2024-01-15T10:00:00Z",
    "updatedBy": "admin"
}
# Returns None if not found
```

---

### `add_item_to_value_set()`
**Purpose**: Add a single item to an existing value set

**When to Use**:
- Adding new options to dropdowns
- Expanding reference lists
- Including new codes

**Input Format**:
```python
await lib.add_item_to_value_set(
    key="country_codes",           # string, value set key
    item={                         # dict, new item
        "code": "JP",
        "labels": {
            "en": "Japan",
            "hi": "जापान"
        }
    },
    updated_by="admin"             # string, user adding item
)
```

**Output Format**:
```python
{
    "_id": "507f1f77bcf86cd799439011",
    "key": "country_codes",
    "items": [                     # Updated items array
        {"code": "US", "labels": {"en": "United States"}},
        {"code": "IN", "labels": {"en": "India"}},
        {"code": "JP", "labels": {"en": "Japan"}}  # New item
    ],
    "updatedAt": "2024-01-15T10:00:00Z",
    "updatedBy": "admin"
}
```

**Error Cases**:
- ValueError if item code already exists
- ValueError if value set not found

---

### `bulk_add_items()`
**Purpose**: Add multiple items to a value set at once

**When to Use**:
- Batch imports
- Mass updates
- Efficient bulk additions

**Input Format**:
```python
await lib.bulk_add_items(
    key="country_codes",           # string, value set key
    items=[                        # list of items to add
        {"code": "FR", "labels": {"en": "France", "hi": "फ्रांस"}},
        {"code": "DE", "labels": {"en": "Germany", "hi": "जर्मनी"}},
        {"code": "IT", "labels": {"en": "Italy", "hi": "इटली"}}
    ],
    updated_by="admin"             # string, user adding items
)
```

**Output Format**:
```python
{
    "_id": "507f1f77bcf86cd799439011",
    "key": "country_codes",
    "items": [                     # Updated with all new items
        # ... existing items ...
        {"code": "FR", "labels": {"en": "France"}},
        {"code": "DE", "labels": {"en": "Germany"}},
        {"code": "IT", "labels": {"en": "Italy"}}
    ],
    "updatedAt": "2024-01-15T10:00:00Z"
}
```

**Constraints**:
- Maximum 500 total items per value set
- All item codes must be unique
- Validates against duplicates before adding

---

### `update_item_in_value_set()`
**Purpose**: Update a specific item within a value set

**When to Use**:
- Correcting labels
- Updating translations
- Modifying item codes

**Input Format**:
```python
await lib.update_item_in_value_set(
    key="country_codes",           # string, value set key
    item_code="US",                # string, code of item to update
    updates={                      # dict, fields to update
        "labels": {
            "en": "United States of America",
            "hi": "संयुक्त राज्य अमेरिका"
        }
    },
    updated_by="admin"             # string, user updating
)
```

**Output Format**:
```python
{
    "_id": "507f1f77bcf86cd799439011",
    "key": "country_codes",
    "items": [
        {
            "code": "US",
            "labels": {
                "en": "United States of America",  # Updated
                "hi": "संयुक्त राज्य अमेरिका"      # Updated
            }
        }
    ]
}
```

---

### `replace_item_code()`
**Purpose**: Replace an item's code and optionally its labels

**When to Use**:
- Renaming codes
- Migrating to new coding standards
- Fixing incorrect codes

**Input Format**:
```python
await lib.replace_item_code(
    key="country_codes",           # string, value set key
    old_code="UK",                 # string, current code
    new_code="GB",                 # string, new code
    new_labels={                   # dict, optional new labels
        "en": "United Kingdom",
        "hi": "यूनाइटेड किंगडम"
    },
    updated_by="admin"             # string, user performing replacement
)
```

**Output Format**:
```python
{
    "_id": "507f1f77bcf86cd799439011",
    "key": "country_codes",
    "items": [
        {"code": "GB", "labels": {"en": "United Kingdom"}}  # Code replaced
    ]
}
```

---

### `remove_item_from_value_set()`
**Purpose**: Remove an item from a value set

**When to Use**:
- Removing obsolete options
- Cleaning up unused codes
- Maintaining data quality

**Input Format**:
```python
await lib.remove_item_from_value_set(
    key="country_codes",           # string, value set key
    item_code="XX",                # string, code to remove
    updated_by="admin"             # string, user removing item
)
```

**Output Format**:
```python
{
    "_id": "507f1f77bcf86cd799439011",
    "key": "country_codes",
    "items": [                     # Item removed from array
        {"code": "US", "labels": {"en": "United States"}},
        {"code": "IN", "labels": {"en": "India"}}
        # "XX" removed
    ],
    "updatedAt": "2024-01-15T10:00:00Z"
}
```

---

## 4. ARCHIVE/RESTORE Operations

### `archive_value_set()`
**Purpose**: Soft delete a value set (mark as archived)

**When to Use**:
- Deprecating old value sets
- Temporary removal
- Maintaining audit trail

**Input Format**:
```python
await lib.archive_value_set(
    key="old_statuses",            # string, value set to archive
    reason="Replaced with new status system",  # string, archive reason
    archived_by="admin"            # string, user archiving
)
```

**Output Format**:
```python
{
    "_id": "507f1f77bcf86cd799439011",
    "key": "old_statuses",
    "status": "archived",           # Changed to archived
    "archiveReason": "Replaced with new status system",
    "archivedBy": "admin",
    "archivedAt": "2024-01-15T10:00:00Z"
}
```

---

### `restore_value_set()`
**Purpose**: Restore an archived value set

**When to Use**:
- Reactivating deprecated value sets
- Undoing accidental archives
- Restoring for historical access

**Input Format**:
```python
await lib.restore_value_set(
    key="old_statuses",            # string, value set to restore
    reason="Still needed for legacy system",  # string, restore reason
    restored_by="admin"            # string, user restoring
)
```

**Output Format**:
```python
{
    "_id": "507f1f77bcf86cd799439011",
    "key": "old_statuses",
    "status": "active",             # Changed back to active
    "restoreReason": "Still needed for legacy system",
    "restoredBy": "admin",
    "restoredAt": "2024-01-16T10:00:00Z"
}
```

---

### `bulk_archive()`
**Purpose**: Archive multiple value sets at once

**When to Use**:
- End-of-life for multiple value sets
- Batch cleanup operations
- Module-wide deprecation

**Input Format**:
```python
await lib.bulk_archive(
    keys=["old_colors", "old_sizes", "old_types"],  # list of keys
    reason="Migrated to new system",   # string, common reason
    archived_by="admin"             # string, user archiving
)
```

**Output Format**:
```python
{
    "matched": 3,                   # Number found
    "modified": 3,                  # Number archived
    "keys": ["old_colors", "old_sizes", "old_types"]
}
```

---

## 5. VALIDATION Operations

### `validate_value_set()`
**Purpose**: Validate value set structure and data integrity

**When to Use**:
- Before imports
- Data quality checks
- API input validation

**Input Format**:
```python
await lib.validate_value_set(
    value_set_data={               # dict, value set to validate
        "key": "test_set",
        "status": "active",
        "items": [
            {"code": "A", "labels": {"en": "Option A"}},
            {"code": "B", "labels": {"en": "Option B"}}
        ]
    }
)
```

**Output Format**:
```python
{
    "valid": True,                  # Boolean, overall validity
    "errors": [],                   # List of error messages
    "warnings": [                   # List of warning messages
        "No description provided",
        "No module specified, will default to 'Core'"
    ]
}

# Invalid example:
{
    "valid": False,
    "errors": [
        "Missing required field: key",
        "Duplicate item codes found",
        "Item 2 missing English label"
    ],
    "warnings": []
}
```

---

### `validate_item()`
**Purpose**: Validate a single item's structure

**When to Use**:
- Before adding items
- Input validation
- Data quality checks

**Input Format**:
```python
await lib.validate_item(
    item={                         # dict, item to validate
        "code": "TEST",
        "labels": {
            "en": "Test Item"
        }
    }
)
```

**Output Format**:
```python
{
    "valid": True,
    "errors": []
}

# Invalid example:
{
    "valid": False,
    "errors": [
        "Item missing code",
        "Item missing English label"
    ]
}
```

---

## 6. EXPORT/IMPORT Operations

### `export_value_set()`
**Purpose**: Export a value set in JSON or CSV format

**When to Use**:
- Data backups
- System migrations
- Sharing reference data
- Report generation

**Input Format**:
```python
await lib.export_value_set(
    key="country_codes",           # string, value set to export
    format="json"                  # string, "json" or "csv"
)
```

**Output Format (JSON)**:
```json
{
    "key": "country_codes",
    "status": "active",
    "module": "Geography",
    "description": "ISO country codes",
    "items": [
        {"code": "US", "labels": {"en": "United States", "hi": "संयुक्त राज्य"}},
        {"code": "IN", "labels": {"en": "India", "hi": "भारत"}}
    ],
    "createdAt": "2024-01-01T00:00:00",
    "createdBy": "admin"
}
```

**Output Format (CSV)**:
```csv
Code,English Label,Hindi Label,Key,Module,Status,Description
US,United States,संयुक्त राज्य,country_codes,Geography,active,ISO country codes
IN,India,भारत,country_codes,Geography,active,ISO country codes
```

---

### `export_all_value_sets()`
**Purpose**: Export all value sets at once

**When to Use**:
- Full system backups
- Data migrations
- Bulk transfers

**Input Format**:
```python
await lib.export_all_value_sets(
    format="json",                 # string, export format
    status="active"                # string, optional filter
)
```

**Output Format**:
```json
[
    {
        "key": "country_codes",
        "status": "active",
        "items": [...]
    },
    {
        "key": "status_codes",
        "status": "active",
        "items": [...]
    }
]
```

---

### `import_value_set()`
**Purpose**: Import a value set from JSON data

**When to Use**:
- Restoring backups
- Loading external data
- System migrations

**Input Format**:
```python
await lib.import_value_set(
    data='{"key": "imported_set", "status": "active", ...}',  # JSON string
    format="json",                 # string, data format
    created_by="import_user"       # string, user performing import
)
```

**Output Format**:
```python
{
    "success": True,
    "key": "imported_set"
}

# On error:
{
    "success": False,
    "error": "Validation failed: Missing required field: items"
}
```

---

## 7. STATISTICS Operations

### `get_statistics()`
**Purpose**: Get overall value set statistics

**When to Use**:
- Dashboard displays
- System health monitoring
- Usage reports

**Input Format**:
```python
await lib.get_statistics()        # No parameters
```

**Output Format**:
```python
{
    "totalValueSets": 42,
    "statusCounts": {
        "active": 38,
        "archived": 4
    },
    "moduleCounts": {
        "Geography": 5,
        "System": 10,
        "Products": 15,
        "UI": 12
    },
    "totalItems": 1250,
    "averageItemsPerSet": 29.76
}
```

---

### `get_module_statistics()`
**Purpose**: Get statistics for a specific module

**When to Use**:
- Module-specific reporting
- Performance analysis
- Capacity planning

**Input Format**:
```python
await lib.get_module_statistics(
    module="Geography"             # string, module name
)
```

**Output Format**:
```python
{
    "module": "Geography",
    "totalValueSets": 5,
    "activeValueSets": 4,
    "archivedValueSets": 1,
    "totalItems": 250,
    "averageItemsPerSet": 50.0
}
```

---

## 8. DELETE Operations

### `delete_value_set()`
**Purpose**: Permanently delete a value set

**⚠️ WARNING**: This is permanent deletion. Consider using `archive_value_set()` instead.

**When to Use**:
- Removing test data
- Cleaning up duplicates
- GDPR compliance

**Input Format**:
```python
await lib.delete_value_set(
    key="test_set"                 # string, value set to delete
)
```

**Output Format**:
```python
True   # If deleted successfully
False  # If not found
```

---

### `bulk_delete()`
**Purpose**: Delete multiple value sets permanently

**When to Use**:
- Batch cleanup
- Test data removal
- Major data purges

**Input Format**:
```python
await lib.bulk_delete(
    keys=["test1", "test2", "test3"]  # list of keys to delete
)
```

**Output Format**:
```python
{
    "requested": 3,
    "deleted": 2                    # Actual number deleted
}
```

---

## Use Cases & Examples

### Example 1: E-commerce Product Management
```python
# Setup product-related value sets
async def setup_product_data():
    lib = ValueSetLibrary(database=db)

    # Create categories
    await lib.create_value_set(
        key="product_categories",
        status="active",
        module="Products",
        items=[
            {"code": "ELEC", "labels": {"en": "Electronics", "hi": "इलेक्ट्रॉनिक्स"}},
            {"code": "CLOTH", "labels": {"en": "Clothing", "hi": "कपड़े"}},
            {"code": "FOOD", "labels": {"en": "Food & Beverages", "hi": "खाद्य और पेय"}}
        ],
        created_by="system",
        description="Main product categories"
    )

    # Create size options
    await lib.create_value_set(
        key="product_sizes",
        status="active",
        module="Products",
        items=[
            {"code": "XS", "labels": {"en": "Extra Small"}},
            {"code": "S", "labels": {"en": "Small"}},
            {"code": "M", "labels": {"en": "Medium"}},
            {"code": "L", "labels": {"en": "Large"}},
            {"code": "XL", "labels": {"en": "Extra Large"}}
        ],
        created_by="system",
        description="Standard size options"
    )
```

### Example 2: User Management System
```python
# Manage user roles and statuses
async def manage_user_value_sets():
    lib = ValueSetLibrary(database=db)

    # User roles
    await lib.create_value_set(
        key="user_roles",
        status="active",
        module="Users",
        items=[
            {"code": "ADMIN", "labels": {"en": "Administrator"}},
            {"code": "MOD", "labels": {"en": "Moderator"}},
            {"code": "USER", "labels": {"en": "Regular User"}},
            {"code": "GUEST", "labels": {"en": "Guest"}}
        ],
        created_by="system"
    )

    # User statuses
    await lib.create_value_set(
        key="user_statuses",
        status="active",
        module="Users",
        items=[
            {"code": "ACTIVE", "labels": {"en": "Active", "hi": "सक्रिय"}},
            {"code": "INACTIVE", "labels": {"en": "Inactive", "hi": "निष्क्रिय"}},
            {"code": "SUSPENDED", "labels": {"en": "Suspended", "hi": "निलंबित"}},
            {"code": "DELETED", "labels": {"en": "Deleted", "hi": "हटाया गया"}}
        ],
        created_by="system"
    )
```

### Example 3: Dynamic Form Builder
```python
# Build dynamic forms with value sets
async def get_form_options(field_type):
    lib = ValueSetLibrary(database=db)

    if field_type == "country":
        value_set = await lib.get_value_set_by_key("country_codes")
    elif field_type == "state":
        value_set = await lib.get_value_set_by_key("state_codes")
    elif field_type == "gender":
        value_set = await lib.get_value_set_by_key("gender_options")

    # Convert to dropdown options
    if value_set:
        return [
            {"value": item["code"], "label": item["labels"]["en"]}
            for item in value_set["items"]
        ]
    return []
```

### Example 4: Multi-tenant Application
```python
# Manage value sets per tenant
async def create_tenant_value_sets(tenant_id, tenant_config):
    lib = ValueSetLibrary(database=db)

    # Create tenant-specific value sets
    for vs_config in tenant_config["value_sets"]:
        await lib.create_value_set(
            key=f"{tenant_id}_{vs_config['key']}",
            status="active",
            module=f"Tenant_{tenant_id}",
            items=vs_config["items"],
            created_by=f"tenant_admin_{tenant_id}",
            description=f"Custom value set for tenant {tenant_id}"
        )
```

### Example 5: Data Migration
```python
# Migrate value sets between systems
async def migrate_value_sets(source_db, target_db):
    source_lib = ValueSetLibrary(database=source_db)
    target_lib = ValueSetLibrary(database=target_db)

    # Export from source
    value_sets, _ = await source_lib.list_value_sets(limit=1000)

    # Import to target
    result = await target_lib.bulk_create_value_sets(
        value_sets=value_sets,
        skip_existing=True
    )

    print(f"Migrated {result['summary']['created']} value sets")
    print(f"Skipped {result['summary']['skipped']} existing")
    print(f"Failed {result['summary']['failed']} value sets")
```

---

## Best Practices

### 1. Key Naming Conventions
```python
# Good key names
"country_codes"         # Descriptive, lowercase, underscore-separated
"user_roles"
"product_categories"
"order_statuses"

# Bad key names
"cc"                   # Too short, unclear
"UserRoles"            # Mixed case
"product-categories"   # Uses hyphens
"data1"                # Not descriptive
```

### 2. Module Organization
```python
# Organize by functional area
modules = {
    "Geography": ["country_codes", "state_codes", "city_codes"],
    "Users": ["user_roles", "user_statuses", "permission_levels"],
    "Products": ["product_categories", "product_sizes", "product_colors"],
    "System": ["log_levels", "error_codes", "notification_types"]
}
```

### 3. Error Handling
```python
async def safe_create_value_set(data):
    lib = ValueSetLibrary(database=db)

    try:
        # Validate first
        validation = await lib.validate_value_set(data)
        if not validation["valid"]:
            return {"error": validation["errors"]}

        # Then create
        result = await lib.create_value_set(**data)
        return {"success": True, "data": result}

    except ValueError as e:
        return {"error": f"Validation error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}
```

### 4. Performance Optimization
```python
# Use bulk operations for better performance
async def efficient_updates():
    lib = ValueSetLibrary(database=db)

    # Instead of multiple single updates
    # BAD:
    for item in items:
        await lib.add_item_to_value_set(key, item, user)

    # GOOD: Use bulk operation
    await lib.bulk_add_items(key, items, user)
```

### 5. Audit Trail
```python
# Always track who made changes
async def tracked_update(key, updates, user_context):
    lib = ValueSetLibrary(database=db)

    # Include user information
    result = await lib.update_value_set(
        key=key,
        updates=updates,
        updated_by=user_context["username"],
        updated_at=datetime.utcnow()
    )

    # Log the change
    logging.info(f"User {user_context['username']} updated {key}")
    return result
```

### 6. Backup Strategy
```python
# Regular backups
async def backup_value_sets():
    lib = ValueSetLibrary(database=db)

    # Export all active value sets
    backup_data = await lib.export_all_value_sets(
        format="json",
        status="active"
    )

    # Save to file with timestamp
    filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        f.write(backup_data)

    return filename
```

### 7. Caching Strategy
```python
# Cache frequently used value sets
from functools import lru_cache
import asyncio

class CachedValueSetService:
    def __init__(self, lib):
        self.lib = lib
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes

    async def get_cached_value_set(self, key):
        if key in self._cache:
            cached_time, data = self._cache[key]
            if time.time() - cached_time < self._cache_ttl:
                return data

        # Fetch and cache
        data = await self.lib.get_value_set_by_key(key)
        self._cache[key] = (time.time(), data)
        return data
```

---

## Common Patterns

### Pattern 1: Dropdown Population
```python
async def get_dropdown_options(value_set_key, language="en"):
    lib = ValueSetLibrary(database=db)

    value_set = await lib.get_value_set_by_key(value_set_key)
    if not value_set:
        return []

    return [
        {
            "value": item["code"],
            "label": item["labels"].get(language, item["labels"]["en"])
        }
        for item in value_set["items"]
        if value_set["status"] == "active"
    ]
```

### Pattern 2: Code Validation
```python
async def validate_code(value_set_key, code):
    lib = ValueSetLibrary(database=db)

    value_set = await lib.get_value_set_by_key(value_set_key)
    if not value_set:
        return False, "Value set not found"

    valid_codes = [item["code"] for item in value_set["items"]]
    if code not in valid_codes:
        return False, f"Invalid code. Valid codes: {', '.join(valid_codes)}"

    return True, "Valid"
```

### Pattern 3: Label Resolution
```python
async def get_label(value_set_key, code, language="en"):
    lib = ValueSetLibrary(database=db)

    items = await lib.get_items_by_codes(value_set_key, [code])
    if not items:
        return None

    return items[0]["labels"].get(language, items[0]["labels"]["en"])
```

---

## Troubleshooting

### Common Issues and Solutions

1. **"Key already exists" error**
   - Use `check_key_exists()` before creating
   - Use `bulk_create_value_sets()` with `skip_existing=True`

2. **"Maximum items exceeded" error**
   - Split into multiple value sets
   - Archive unused items
   - Maximum is 500 items per value set

3. **"Duplicate item codes" error**
   - Validate codes before adding
   - Use `replace_item_code()` to rename duplicates

4. **Performance issues**
   - Use bulk operations instead of loops
   - Implement caching for frequently accessed value sets
   - Add indexes on `key`, `status`, and `items.code`

5. **Missing translations**
   - Always provide English labels (required)
   - Use `update_item_in_value_set()` to add missing translations

---

## Database Indexes

Recommended MongoDB indexes for optimal performance:

```javascript
// Single field indexes
db.value_sets.createIndex({ "key": 1 }, { unique: true })
db.value_sets.createIndex({ "status": 1 })
db.value_sets.createIndex({ "module": 1 })

// Compound indexes
db.value_sets.createIndex({ "status": 1, "module": 1 })
db.value_sets.createIndex({ "items.code": 1 })

// Text search index
db.value_sets.createIndex({
    "key": "text",
    "description": "text",
    "items.labels.en": "text"
})
```

---

## Security Considerations

1. **Authentication**: Always track `created_by` and `updated_by`
2. **Authorization**: Implement role-based access control
3. **Validation**: Always validate input data
4. **Audit Trail**: Keep history of all changes
5. **Backup**: Regular automated backups
6. **Encryption**: Consider encrypting sensitive value sets

---

## Version History

- **v1.0.0**: Initial release with full CRUD operations
- Features: Create, Read, Update, Delete, Archive, Export, Import, Validation, Statistics

---

## Support

For issues, questions, or contributions, please refer to the GitHub repository or contact the development team.