# Value Set Library

A reusable Python library for managing value sets with MongoDB. This library provides comprehensive functionality for creating, managing, and querying value sets with multilingual support.

## Features

- **Complete CRUD Operations**: Create, Read, Update, and Delete value sets
- **Bulk Operations**: Handle multiple value sets or items at once
- **Multilingual Support**: Built-in support for English and Hindi labels
- **Archive/Restore**: Soft delete functionality with restore capability
- **Search & Filter**: Advanced search across items and labels
- **Export/Import**: Support for JSON and CSV formats
- **Validation**: Built-in validation for value set structures
- **Statistics**: Get insights about your value sets
- **Async Support**: Built with async/await for high performance

## Installation

### As a Package

```bash
pip install value-set-lib
```

### From Source

```bash
git clone https://github.com/yourusername/value-set-lib.git
cd value-set-lib
pip install -e .
```

### For Development

```bash
pip install -e ".[dev]"
```

### With FastAPI Support

```bash
pip install -e ".[fastapi]"
```

## Quick Start

### Basic Usage

```python
from motor.motor_asyncio import AsyncIOMotorClient
from value_set_lib import ValueSetLibrary

# Connect to MongoDB
client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client.your_database

# Initialize the library
lib = ValueSetLibrary(database=db, collection_name="value_sets")

# Create a value set
result = await lib.create_value_set(
    key="country_codes",
    status="active",
    module="Geography",
    items=[
        {"code": "US", "labels": {"en": "United States", "hi": "संयुक्त राज्य"}},
        {"code": "IN", "labels": {"en": "India", "hi": "भारत"}},
        {"code": "GB", "labels": {"en": "United Kingdom", "hi": "यूनाइटेड किंगडम"}}
    ],
    created_by="admin",
    description="ISO country codes"
)
```

### Using with FastAPI

```python
from fastapi import FastAPI, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from value_set_lib import ValueSetLibrary

app = FastAPI()

async def get_db():
    # Your database connection logic
    pass

def get_library(db: AsyncIOMotorDatabase = Depends(get_db)):
    return ValueSetLibrary(database=db)

@app.post("/value-sets")
async def create_value_set(data: dict, lib: ValueSetLibrary = Depends(get_library)):
    return await lib.create_value_set(**data)
```

## Core Functions

### Create Operations

```python
# Create single value set
await lib.create_value_set(key="test", status="active", module="Core", items=[...], created_by="user")

# Bulk create
await lib.bulk_create_value_sets(value_sets=[...], skip_existing=True)
```

### Read Operations

```python
# Get by key
value_set = await lib.get_value_set_by_key("country_codes")

# List with pagination
results, total = await lib.list_value_sets(skip=0, limit=100, status="active")

# Search items
results, total = await lib.search_items(query="United", language_code="en")
```

### Update Operations

```python
# Update value set
await lib.update_value_set(key="test", updates={"description": "Updated"}, updated_by="user")

# Add item
await lib.add_item_to_value_set(key="test", item={...}, updated_by="user")

# Update item
await lib.update_item_in_value_set(key="test", item_code="US", updates={...}, updated_by="user")
```

### Archive/Restore

```python
# Archive
await lib.archive_value_set(key="test", reason="No longer needed", archived_by="user")

# Restore
await lib.restore_value_set(key="test", reason="Needed again", restored_by="user")
```

### Export/Import

```python
# Export to JSON
json_data = await lib.export_value_set(key="test", format="json")

# Export to CSV
csv_data = await lib.export_value_set(key="test", format="csv")

# Import from JSON
await lib.import_value_set(data=json_string, format="json", created_by="user")
```

### Validation

```python
# Validate structure
result = await lib.validate_value_set(value_set_data)
if result['valid']:
    print("Valid!")
else:
    print(f"Errors: {result['errors']}")
```

### Statistics

```python
# Get overall statistics
stats = await lib.get_statistics()

# Get module-specific statistics
module_stats = await lib.get_module_statistics("Geography")
```

## Standalone Functions

The library also provides standalone utility functions:

```python
from value_set_lib import (
    create_value_set_document,
    validate_item_structure,
    validate_value_set_structure,
    export_to_json,
    export_to_csv
)

# Create document structure
doc = create_value_set_document(key="test", status="active", ...)

# Validate structures
is_valid, errors = validate_item_structure(item)
is_valid, errors = validate_value_set_structure(value_set)

# Export utilities
json_string = export_to_json(value_set)
csv_string = export_to_csv(value_set)
```

## Data Structure

### Value Set

```python
{
    "key": "country_codes",          # Unique identifier
    "status": "active",               # active or archived
    "module": "Geography",            # Module name
    "description": "ISO codes",       # Optional description
    "items": [...],                   # List of items
    "createdAt": datetime,
    "createdBy": "user",
    "updatedAt": datetime,
    "updatedBy": "user"
}
```

### Item

```python
{
    "code": "US",
    "labels": {
        "en": "United States",        # Required
        "hi": "संयुक्त राज्य"          # Optional
    }
}
```

## Configuration

### Database Connection

```python
from motor.motor_asyncio import AsyncIOMotorClient

# Basic connection
client = AsyncIOMotorClient("mongodb://localhost:27017")

# With authentication
client = AsyncIOMotorClient(
    "mongodb://username:password@host:port/database",
    maxPoolSize=50,
    minPoolSize=10
)

db = client.your_database
lib = ValueSetLibrary(database=db)
```

### Custom Collection Name

```python
lib = ValueSetLibrary(database=db, collection_name="custom_collection")
```

## Error Handling

```python
try:
    result = await lib.create_value_set(...)
except ValueError as e:
    print(f"Validation error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Testing

```python
import pytest
from value_set_lib import ValueSetLibrary

@pytest.mark.asyncio
async def test_create_value_set():
    lib = ValueSetLibrary(database=test_db)
    result = await lib.create_value_set(...)
    assert result['key'] == 'test'
```

## Best Practices

1. **Always validate before creating**: Use `validate_value_set()` before creating
2. **Use bulk operations**: When dealing with multiple items, use bulk functions
3. **Archive instead of delete**: Use archive/restore for soft deletes
4. **Implement proper error handling**: Always catch and handle exceptions
5. **Use appropriate indexes**: Create indexes on `key`, `status`, and `items.code`

## Performance Tips

1. **Connection pooling**: Configure appropriate pool sizes in MongoDB client
2. **Batch operations**: Use bulk operations for multiple updates
3. **Pagination**: Always use pagination for large result sets
4. **Indexing**: Create indexes on frequently queried fields

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please use the GitHub issues page.