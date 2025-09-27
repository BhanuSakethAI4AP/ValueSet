# Value Set Management System

A production-ready, enterprise-grade FastAPI application for managing standardized code lists (value sets) with MongoDB. Built with clean architecture principles, comprehensive validation, and full CRUD + search capabilities.

## What is a Value Set?

A **value set** is a standardized collection of codes and labels used across an application for consistency. Think of it as a centralized dictionary of allowed values.

**Examples:**
- **Medical Specialties**: `CARDIO → Cardiology`, `NEURO → Neurology`
- **Country Codes**: `US → United States`, `IN → India`
- **Status Values**: `ACTIVE → Active`, `INACTIVE → Inactive`

**Benefits:**
- Centralized code management
- Multilingual label support
- Data consistency across systems
- Easy updates without code changes
- Audit trail for all changes

## Architecture Overview

This system follows a **3-layer clean architecture** pattern:

```
┌─────────────────────────────────────────────────────────────┐
│                      HTTP Client                             │
│                  (Browser, API Client, etc.)                 │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    ROUTER LAYER                              │
│  • HTTP Request/Response Handling                            │
│  • Request Validation (Pydantic Schemas)                     │
│  • Dependency Injection                                      │
│  • 24 REST API Endpoints                                     │
│                                                              │
│  Files: routers/value_set_router.py                         │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   SERVICE LAYER                              │
│  • Business Logic                                            │
│  • Validation Rules (uniqueness, state, etc.)               │
│  • Orchestration                                             │
│  • Error Handling                                            │
│                                                              │
│  Files: services/value_set_service.py                       │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                 REPOSITORY LAYER                             │
│  • Database Operations (MongoDB)                             │
│  • Query Construction                                        │
│  • Data Access Abstraction                                   │
│  • No Business Logic                                         │
│                                                              │
│  Files: repositories/value_set_repository.py                │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    MONGODB DATABASE                          │
│  Collection: value_sets                                      │
└─────────────────────────────────────────────────────────────┘
```

**Cross-Cutting:**
```
┌─────────────────────────────────────────────────────────────┐
│                    SCHEMAS LAYER                             │
│  • Pydantic Models for Validation                            │
│  • Request/Response Structures                               │
│  • Type Safety                                               │
│  • OpenAPI Documentation                                     │
│                                                              │
│  Files: schemas/value_set_schemas_enhanced.py               │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
ValueSets/
├── routers/                      # HTTP Layer (API Endpoints)
│   ├── value_set_router.py      # 24 REST API endpoints
│   └── README.md                 # Router documentation
│
├── services/                     # Business Logic Layer
│   ├── value_set_service.py     # Business rules & orchestration
│   └── README.md                 # Service documentation
│
├── repositories/                 # Data Access Layer
│   ├── value_set_repository.py  # MongoDB operations
│   └── README.md                 # Repository documentation
│
├── schemas/                      # Data Models & Validation
│   ├── value_set_schemas_enhanced.py  # Pydantic schemas
│   └── README.md                 # Schema documentation
│
├── tests/                        # Comprehensive Test Suite
│   ├── test.py                   # 21 test cases (100% pass rate)
│   └── TEST_README.md            # Test documentation
│
├── database.py                   # MongoDB connection
├── main.py                       # FastAPI application entry
└── README.md                     # This file
```

## Key Features

### Core Functionality
- ✅ **Full CRUD Operations** - Create, Read, Update, Archive/Restore value sets
- ✅ **Item Management** - Add, update, replace items within value sets
- ✅ **Bulk Operations** - Import, update multiple value sets/items at once
- ✅ **Search & Filter** - Search items by code/label, filter by status/module
- ✅ **Pagination** - Efficient handling of large datasets
- ✅ **Multilingual Support** - Labels in multiple languages (English, Hindi, etc.)

### Data Integrity
- ✅ **Multi-Layer Validation** - Pydantic schemas + business rules + database constraints
- ✅ **Unique Code Enforcement** - Codes unique within each value set
- ✅ **Status Management** - ACTIVE, ARCHIVED states with transitions
- ✅ **Audit Trail** - Automatic tracking of created/updated timestamps and users

### Architecture
- ✅ **Clean Architecture** - Clear separation of concerns (Router → Service → Repository)
- ✅ **Dependency Injection** - FastAPI's built-in DI system
- ✅ **Type Safety** - Full type hints throughout the codebase
- ✅ **Async/Await** - Non-blocking I/O with MongoDB Motor driver

### Developer Experience
- ✅ **Auto-Generated API Docs** - Interactive Swagger UI and ReDoc
- ✅ **Comprehensive Tests** - 21 test cases covering all functionality
- ✅ **Detailed Documentation** - README for each architectural layer
- ✅ **Error Handling** - Consistent HTTP status codes and error messages

## Quick Start

### Prerequisites
- Python 3.8+
- MongoDB 4.4+
- pip

### Installation

```bash
# Clone or navigate to the project
cd ValueSets

# Install dependencies
pip install fastapi uvicorn motor pydantic

# Start MongoDB (if not already running)
# mongod --dbpath /path/to/data

# Run the application
uvicorn main:app --reload

# Application runs at: http://localhost:8000
```

### Verify Installation

```bash
# Check health endpoint
curl http://localhost:8000/api/v1/value-sets/health

# View API documentation
# Open browser: http://localhost:8000/docs
```

## API Endpoints Overview

### Core CRUD
- `POST /api/v1/value-sets/` - Create value set
- `GET /api/v1/value-sets/{key}` - Get value set by key
- `PUT /api/v1/value-sets/{key}` - Update value set
- `GET /api/v1/value-sets/` - List value sets (paginated)

### Item Management
- `POST /api/v1/value-sets/{key}/items` - Add item
- `PUT /api/v1/value-sets/{key}/items/{code}` - Update item
- `PUT /api/v1/value-sets/{key}/items/replace` - Replace item code

### Search
- `POST /api/v1/value-sets/search/items` - Search items
- `GET /api/v1/value-sets/search/by-label` - Search by label

### Bulk Operations
- `POST /api/v1/value-sets/{key}/items/bulk-add` - Bulk add items
- `PUT /api/v1/value-sets/items/bulk-update` - Bulk update items
- `POST /api/v1/value-sets/bulk/import` - Bulk import value sets
- `PUT /api/v1/value-sets/bulk/update` - Bulk update value sets

### Archive/Restore
- `POST /api/v1/value-sets/{key}/archive` - Archive value set
- `POST /api/v1/value-sets/{key}/restore` - Restore value set

### Utilities
- `POST /api/v1/value-sets/validate` - Validate value set
- `GET /api/v1/value-sets/statistics/summary` - Get statistics
- `GET /api/v1/value-sets/{key}/export` - Export value set
- `POST /api/v1/value-sets/import` - Import value set
- `GET /api/v1/value-sets/health` - Health check

**Full endpoint documentation:** See `routers/README.md` or visit `/docs` endpoint

## Usage Examples

### Create a Value Set

```python
import httpx

async def create_medical_specialties():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/value-sets/",
            json={
                "key": "medical_specialties",
                "module": "healthcare",
                "description": "Medical specialty codes",
                "items": [
                    {
                        "code": "CARDIO",
                        "labels": {"en": "Cardiology", "hi": "हृदय रोग विज्ञान"}
                    },
                    {
                        "code": "NEURO",
                        "labels": {"en": "Neurology", "hi": "तंत्रिका विज्ञान"}
                    }
                ],
                "createdBy": "admin"
            }
        )
        return response.json()
```

### Get Value Set

```python
async def get_value_set():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/api/v1/value-sets/medical_specialties"
        )
        value_set = response.json()
        print(f"Found {len(value_set['items'])} items")
        return value_set
```

### Search Items

```python
async def search_items():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/value-sets/search/items",
            json={
                "query": "cardio",
                "languageCode": "en"
            }
        )
        results = response.json()
        for result in results:
            print(f"Found in: {result['valueSetKey']}")
            print(f"Matches: {result['totalMatches']}")
```

### Bulk Add Items

```python
async def bulk_add_specialties():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/value-sets/medical_specialties/items/bulk-add",
            json={
                "items": [
                    {"code": "ORTHO", "labels": {"en": "Orthopedics"}},
                    {"code": "DERM", "labels": {"en": "Dermatology"}},
                    {"code": "PEDS", "labels": {"en": "Pediatrics"}}
                ],
                "updated_by": "admin"
            }
        )
        result = response.json()
        print(f"Added {result['successful']} items")
```

## Testing

The system includes a comprehensive test suite with 21 test cases covering all functionality.

```bash
# Run all tests
python tests/test.py

# Expected output:
# ✅ Test 1: Create Value Set - PASS
# ✅ Test 2: Get Value Set by Key - PASS
# ... (21 total tests)
#
# Final Results: 21/21 passed (100%)
```

**Test Coverage:**
- CREATE operations (4 tests)
- READ operations (3 tests)
- UPDATE operations (2 tests)
- ITEM management (4 tests)
- SEARCH operations (2 tests)
- ARCHIVE/RESTORE (2 tests)
- BULK operations (1 test)
- VALIDATION (2 tests)
- STATISTICS (1 test)

See `tests/TEST_README.md` for detailed test documentation.

## Data Model

### Value Set Structure

```json
{
  "_id": "507f1f77bcf86cd799439011",
  "key": "medical_specialties",
  "status": "active",
  "module": "healthcare",
  "description": "Medical specialty codes",
  "items": [
    {
      "code": "CARDIO",
      "labels": {
        "en": "Cardiology",
        "hi": "हृदय रोग विज्ञान"
      }
    },
    {
      "code": "NEURO",
      "labels": {
        "en": "Neurology",
        "hi": "तंत्रिका विज्ञान"
      }
    }
  ],
  "createdAt": "2024-01-15T10:30:00Z",
  "createdBy": "admin",
  "updatedAt": "2024-01-16T14:20:00Z",
  "updatedBy": "editor"
}
```

### Status Values
- `active` - Value set is in active use
- `archived` - Value set is retired but preserved for historical reference

## Architecture Deep Dive

### Router Layer (`routers/`)
**Responsibility:** HTTP interface to the system

- Defines REST API endpoints
- Validates HTTP requests with Pydantic schemas
- Handles HTTP-specific concerns (status codes, headers)
- Delegates business logic to Service Layer
- Generates OpenAPI documentation

**See:** `routers/README.md` for detailed endpoint documentation

### Service Layer (`services/`)
**Responsibility:** Business logic and orchestration

- Enforces business rules (uniqueness, state transitions, etc.)
- Coordinates operations across repositories
- Handles complex workflows
- Implements validation beyond schema validation
- Provides transaction boundaries

**See:** `services/README.md` for method documentation

### Repository Layer (`repositories/`)
**Responsibility:** Data access abstraction

- Performs MongoDB CRUD operations
- Constructs database queries
- Handles ObjectId conversions
- Provides clean data access API
- No business logic

**See:** `repositories/README.md` for method documentation

### Schemas Layer (`schemas/`)
**Responsibility:** Data models and validation

- Defines Pydantic models for all data structures
- Automatic request/response validation
- Type safety throughout application
- Powers OpenAPI documentation
- Serialization/deserialization

**See:** `schemas/README.md` for schema documentation

## Validation Strategy

The system implements **defense in depth** with multiple validation layers:

### Layer 1: Pydantic Schema Validation
```python
# Automatic validation on request
@router.post("/")
async def create_value_set(data: ValueSetCreateSchema):
    # data is already validated:
    # - Required fields present
    # - Types correct
    # - Field constraints (max_length, etc.)
    # - Item codes unique within value set
    pass
```

### Layer 2: Service Layer Validation
```python
# Business rule validation
async def create_value_set(self, data: ValueSetCreateSchema):
    # Check if key already exists (uniqueness in database)
    existing = await self.repository.find_by_key(data.key)
    if existing:
        raise ValueError(f"Value set with key '{data.key}' already exists")

    # Proceed with creation
    return await self.repository.create(data.model_dump())
```

### Layer 3: Database Constraints
```python
# MongoDB unique index on 'key' field
await collection.create_index("key", unique=True)
```

This multi-layer approach ensures:
- Fast failure (Pydantic catches issues before service layer)
- Comprehensive validation (business rules + data rules)
- Data integrity (database enforces constraints)
- Better error messages (specific to validation layer)

## Common Use Cases

### Use Case 1: Dropdown Lists
**Problem:** Need consistent dropdown values across application

**Solution:**
```python
# Fetch active value sets for dropdown
response = await client.get(
    "/api/v1/value-sets/",
    params={"status": "ACTIVE", "module": "core"}
)

# Use items for dropdown options
for value_set in response.json()["items"]:
    for item in value_set["items"]:
        print(f"{item['code']}: {item['labels']['en']}")
```

### Use Case 2: Data Standardization
**Problem:** Different systems use different codes

**Solution:**
```python
# Centralize codes in value sets
# All systems query the same source
medical_specialty = await get_value_set("medical_specialties")

# Map incoming codes to standard codes
def standardize_code(input_code):
    for item in medical_specialty["items"]:
        if item["code"] == input_code:
            return item["labels"]["en"]
    return "Unknown"
```

### Use Case 3: Multilingual Applications
**Problem:** Need labels in multiple languages

**Solution:**
```python
# Fetch value set
value_set = await get_value_set("medical_specialties")

# Display in user's language
user_language = "hi"  # Hindi
for item in value_set["items"]:
    label = item["labels"].get(user_language, item["labels"]["en"])
    print(f"{item['code']}: {label}")
```

### Use Case 4: Data Migration
**Problem:** Need to import codes from legacy system

**Solution:**
```python
# Bulk import value sets
response = await client.post(
    "/api/v1/value-sets/bulk/import",
    json={
        "value_sets": [
            {
                "key": "legacy_codes_1",
                "items": [...],  # Imported items
                "created_by": "migration_script"
            }
        ],
        "created_by": "migration_script"
    }
)

print(f"Imported {response.json()['successful']} value sets")
```

## Error Handling

All endpoints return consistent HTTP status codes:

- **200 OK** - Successful operation
- **400 Bad Request** - Validation error, business rule violation
- **404 Not Found** - Resource doesn't exist
- **500 Internal Server Error** - Unexpected server error

**Error Response Format:**
```json
{
  "detail": "Value set with key 'medical_specialties' already exists"
}
```

## Performance Considerations

### Pagination
Always use pagination for large datasets:
```python
# Good - paginated
response = await client.get(
    "/api/v1/value-sets/",
    params={"skip": 0, "limit": 100}
)

# Bad - no pagination (could load thousands of records)
response = await client.get("/api/v1/value-sets/")
```

### Bulk Operations
Use bulk endpoints instead of loops:
```python
# Good - single request
await client.post(
    "/api/v1/value-sets/key/items/bulk-add",
    json={"items": [...], "updated_by": "user"}
)

# Bad - multiple requests
for item in items:
    await client.post(f"/api/v1/value-sets/key/items", json=item)
```

### Indexes
MongoDB indexes on:
- `key` (unique) - Fast key lookups
- `status` - Fast status filtering
- `module` - Fast module filtering
- `items.code` - Fast item searches

## Best Practices

### Do's ✅
- Use the Service Layer for all business operations
- Validate data with Pydantic schemas
- Use bulk operations for multiple items
- Archive instead of delete
- Provide meaningful audit fields (createdBy, updatedBy)
- Use pagination for lists
- Handle errors gracefully
- Follow the 3-layer architecture

### Don'ts ❌
- Don't call Repository directly from Routers (bypass business logic)
- Don't implement business logic in Routers or Repositories
- Don't hard-delete data (use archive instead)
- Don't skip validation by using plain dicts
- Don't mix concerns between layers
- Don't create duplicate schemas for same purpose
- Don't ignore pagination for large datasets

## API Documentation

The system provides interactive API documentation:

- **Swagger UI:** http://localhost:8000/docs
  - Interactive API testing
  - Request/response examples
  - Schema definitions

- **ReDoc:** http://localhost:8000/redoc
  - Clean, readable documentation
  - Code samples
  - Comprehensive schema reference

## Troubleshooting

### MongoDB Connection Failed
```bash
# Ensure MongoDB is running
mongod --dbpath /path/to/data

# Check connection string in database.py
MONGO_URL = "mongodb://localhost:27017"
```

### Import Error: Module not found
```bash
# Install dependencies
pip install fastapi uvicorn motor pydantic

# Verify Python version
python --version  # Should be 3.8+
```

### Validation Error on Create
```json
{
  "detail": [
    {
      "loc": ["body", "items"],
      "msg": "Item codes must be unique within the value set",
      "type": "value_error"
    }
  ]
}
```
**Solution:** Ensure all item codes are unique within the value set

### Port Already in Use
```bash
# Use different port
uvicorn main:app --port 8001

# Or kill process on port 8000
# On Unix: lsof -ti:8000 | xargs kill -9
# On Windows: netstat -ano | findstr :8000
```

## Future Enhancements

Potential additions to the system:
- Versioning for value sets (track changes over time)
- Import/export to Excel/CSV
- Role-based access control (RBAC)
- Change history and rollback
- Value set dependencies and relationships
- Custom validation rules per value set
- Caching layer (Redis) for frequently accessed value sets
- GraphQL API alongside REST
- Webhooks for value set changes

## Contributing

To extend this system:

1. **Adding New Endpoints:**
   - Add schema to `schemas/value_set_schemas_enhanced.py`
   - Add service method to `services/value_set_service.py`
   - Add repository method to `repositories/value_set_repository.py` (if needed)
   - Add router endpoint to `routers/value_set_router.py`
   - Add test case to `tests/test.py`

2. **Adding New Fields:**
   - Update Pydantic schemas in `schemas/`
   - Update service logic if business rules change
   - Update repository queries if database changes needed
   - Update tests

3. **Follow the Pattern:**
   - Router handles HTTP → calls Service
   - Service handles logic → calls Repository
   - Repository handles database → returns data
   - Schemas validate everywhere

## License

This is a demonstration/educational project. Adapt as needed for your use case.

## Summary

**Value Set Management System** is a production-ready FastAPI application that provides:
- Centralized management of standardized code lists
- RESTful API with 24 endpoints
- Clean 3-layer architecture
- Comprehensive validation and error handling
- Full CRUD + search + bulk operations
- Multilingual support
- Complete test coverage
- Auto-generated API documentation

**Perfect for:**
- Healthcare systems (diagnosis codes, procedure codes, etc.)
- E-commerce (product categories, attributes)
- Government applications (standardized codes)
- Any system requiring consistent dropdown/lookup values

**Get Started:**
```bash
cd ValueSets
pip install fastapi uvicorn motor pydantic
uvicorn main:app --reload
# Visit: http://localhost:8000/docs
```

For detailed documentation on each layer:
- **Routers:** `routers/README.md`
- **Services:** `services/README.md`
- **Repositories:** `repositories/README.md`
- **Schemas:** `schemas/README.md`
- **Tests:** `tests/TEST_README.md`