# Routers Layer

## Overview
The **Router Layer** is the HTTP interface for the Value Set Management System. It defines all API endpoints, handles HTTP requests/responses, performs request validation, and delegates business logic to the Service Layer.

**Key Responsibilities:**
- Define REST API endpoints with FastAPI decorators
- Parse and validate HTTP request data (path params, query params, body)
- Call service layer methods with validated data
- Transform service responses into HTTP responses
- Handle HTTP-specific errors (400, 404, 500)
- Apply dependency injection for database and service instances
- Generate OpenAPI documentation automatically

**Architecture Position:**
```
HTTP Client → Router Layer → Service Layer → Repository Layer → Database
                  ↓
            (This Layer)
```

## What's in This Folder

### `value_set_router.py`
Contains all 24 API endpoints for value set operations organized by functionality:

**Files:**
- `value_set_router.py` - Main router with all endpoints

## Available Endpoints

### Core CRUD Operations

#### 1. Create Value Set
```python
POST /api/v1/value-sets/
Body: ValueSetCreateSchema
Response: ValueSetResponseSchema
```

**When to Use:**
- Creating a brand new value set from scratch
- Initial population of the system with value sets
- Adding a new standardized code list to the system

**Example:**
```python
import httpx

create_data = {
    "key": "medical_specialties",
    "name": "Medical Specialties",
    "module": "healthcare",
    "description": "List of medical specialties",
    "items": [
        {
            "code": "CARDIO",
            "labels": {"en": "Cardiology", "es": "Cardiología"}
        }
    ],
    "created_by": "user123"
}

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/api/v1/value-sets/",
        json=create_data
    )
    value_set = response.json()
```

#### 2. Get Value Set by Key
```python
GET /api/v1/value-sets/{key}
Response: ValueSetResponseSchema
```

**When to Use:**
- Displaying value set details to users
- Verifying a value set exists before operations
- Retrieving complete value set including all items

**Example:**
```python
async with httpx.AsyncClient() as client:
    response = await client.get(
        "http://localhost:8000/api/v1/value-sets/medical_specialties"
    )
    value_set = response.json()
    print(f"Found {len(value_set['items'])} items")
```

#### 3. Update Value Set
```python
PUT /api/v1/value-sets/{key}
Body: ValueSetUpdateSchema
Response: ValueSetResponseSchema
```

**When to Use:**
- Modifying value set metadata (name, description, status)
- Changing value set configuration without touching items
- Updating module assignment or status

**Example:**
```python
update_data = {
    "name": "Updated Medical Specialties",
    "description": "Comprehensive list of medical specialties",
    "status": "ACTIVE",
    "updated_by": "admin_user"
}

async with httpx.AsyncClient() as client:
    response = await client.put(
        "http://localhost:8000/api/v1/value-sets/medical_specialties",
        json=update_data
    )
```

#### 5. List Value Sets (with Pagination)
```python
GET /api/v1/value-sets/?status={status}&module={module}&skip={skip}&limit={limit}
Response: PaginatedValueSetResponse
```

**When to Use:**
- Displaying value set lists in UI
- Browsing and filtering value sets
- Building selection dropdowns

**Example:**
```python
# Get first 50 active healthcare value sets
async with httpx.AsyncClient() as client:
    response = await client.get(
        "http://localhost:8000/api/v1/value-sets/",
        params={
            "status": "ACTIVE",
            "module": "healthcare",
            "skip": 0,
            "limit": 50
        }
    )
    result = response.json()
    print(f"Total: {result['total']}, Showing: {len(result['items'])}")
```

### Search Operations

#### 6. Search Value Set Items
```python
POST /api/v1/value-sets/search/items
Body: SearchItemsQuerySchema
Response: List[SearchItemsResponseSchema]
```

**When to Use:**
- Implementing autocomplete functionality
- Finding items by code or label across multiple value sets
- Building search interfaces for value set items

**Example:**
```python
search_params = {
    "search_text": "cardio",
    "value_set_keys": ["medical_specialties"],
    "language_code": "en",
    "exact_match": False,
    "limit": 50
}

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/api/v1/value-sets/search/items",
        json=search_params
    )
    results = response.json()
```

#### 7. Search Value Sets by Label
```python
GET /api/v1/value-sets/search/by-label?label_text={text}&language_code={lang}&status={status}
Response: List[ValueSetResponseSchema]
```

**When to Use:**
- Finding value sets containing specific terminology
- Locating value sets based on item content
- Content-based value set discovery

**Example:**
```python
async with httpx.AsyncClient() as client:
    response = await client.get(
        "http://localhost:8000/api/v1/value-sets/search/by-label",
        params={
            "label_text": "heart",
            "language_code": "en",
            "status": "ACTIVE"
        }
    )
```

### Item Management

#### 8. Add Item to Value Set
```python
POST /api/v1/value-sets/{key}/items
Body: AddItemRequestSchema
Response: ValueSetResponseSchema
```

**When to Use:**
- Adding a single new item to existing value set
- Extending value sets with new codes
- When bulk operations are not needed

**Example:**
```python
request = {
    "item": {
        "code": "NEUROLOGY",
        "labels": {"en": "Neurology", "es": "Neurología"}
    },
    "updated_by": "user123"
}

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/api/v1/value-sets/medical_specialties/items",
        json=request
    )
```

#### 9. Replace Item Code
```python
PUT /api/v1/value-sets/{key}/items/replace
Body: ReplaceItemCodeSchema
Response: ValueSetResponseSchema
```

**When to Use:**
- Changing an item's code identifier
- Code standardization or migration
- Maintaining item while updating its identifier

**Example:**
```python
replace_request = {
    "old_code": "CARDIO",
    "new_code": "CARDIOLOGY",
    "new_labels": {"en": "Cardiology"},
    "updated_by": "admin"
}

async with httpx.AsyncClient() as client:
    response = await client.put(
        "http://localhost:8000/api/v1/value-sets/medical_specialties/items/replace",
        json=replace_request
    )
```

#### 10. Update Item in Value Set
```python
PUT /api/v1/value-sets/{key}/items/{item_code}
Body: UpdateItemRequestSchema
Response: ValueSetResponseSchema
```

**When to Use:**
- Updating item labels or metadata
- Modifying item information without changing code
- Adding translations to existing items

**Example:**
```python
update_request = {
    "labels": {"en": "Cardiology (Updated)", "fr": "Cardiologie"},
    "metadata": {"specialty_type": "medical"},
    "updated_by": "editor"
}

async with httpx.AsyncClient() as client:
    response = await client.put(
        "http://localhost:8000/api/v1/value-sets/medical_specialties/items/CARDIO",
        json=update_request
    )
```

### Bulk Operations

#### 11. Bulk Add Items
```python
POST /api/v1/value-sets/{key}/items/bulk-add
Body: {items: List[ItemCreateSchema], updated_by: str}
Response: BulkOperationResponseSchema
```

**When to Use:**
- Adding multiple items at once
- Importing or migrating large sets of codes
- Initial value set population

**Example:**
```python
bulk_data = {
    "items": [
        {"code": "NEURO", "labels": {"en": "Neurology"}},
        {"code": "ORTHO", "labels": {"en": "Orthopedics"}},
        {"code": "DERM", "labels": {"en": "Dermatology"}}
    ],
    "updated_by": "admin"
}

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/api/v1/value-sets/medical_specialties/items/bulk-add",
        json=bulk_data
    )
    result = response.json()
    print(f"Success: {result['success_count']}, Failed: {result['failure_count']}")
```

#### 12. Bulk Update Items
```python
PUT /api/v1/value-sets/items/bulk-update
Body: BulkItemUpdateSchema
Response: BulkOperationResponseSchema
```

**When to Use:**
- Updating multiple items across different value sets
- Standardizing labels or metadata
- Global updates to related items

**Example:**
```python
updates = {
    "updates": [
        {
            "value_set_key": "medical_specialties",
            "item_code": "CARDIO",
            "labels": {"en": "Cardiology (Updated)"}
        },
        {
            "value_set_key": "medical_specialties",
            "item_code": "NEURO",
            "metadata": {"active": True}
        }
    ],
    "updated_by": "bulk_editor"
}

async with httpx.AsyncClient() as client:
    response = await client.put(
        "http://localhost:8000/api/v1/value-sets/items/bulk-update",
        json=updates
    )
```

#### 15. Bulk Import Value Sets
```python
POST /api/v1/value-sets/bulk/import
Body: BulkValueSetCreateSchema
Response: BulkOperationResponseSchema
```

**When to Use:**
- Importing many value sets from external systems
- Initial system setup with predefined value sets
- Migration from other value set management systems

**Example:**
```python
import_data = {
    "value_sets": [
        {
            "key": "countries",
            "name": "Country Codes",
            "module": "geography",
            "items": [{"code": "US", "labels": {"en": "United States"}}],
            "created_by": "system"
        },
        {
            "key": "currencies",
            "name": "Currency Codes",
            "module": "finance",
            "items": [{"code": "USD", "labels": {"en": "US Dollar"}}],
            "created_by": "system"
        }
    ],
    "created_by": "import_user"
}

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/api/v1/value-sets/bulk/import",
        json=import_data
    )
```

#### 16. Bulk Update Value Sets
```python
PUT /api/v1/value-sets/bulk/update
Body: BulkValueSetUpdateSchema
Response: BulkOperationResponseSchema
```

**When to Use:**
- Applying consistent changes to multiple value sets
- Updating status, module, or metadata in bulk
- Administrative operations on groups of value sets

**Example:**
```python
bulk_update = {
    "updates": [
        {
            "key": "medical_specialties",
            "status": "ACTIVE",
            "description": "Updated list"
        },
        {
            "key": "country_codes",
            "module": "geography_v2"
        }
    ],
    "updated_by": "admin"
}

async with httpx.AsyncClient() as client:
    response = await client.put(
        "http://localhost:8000/api/v1/value-sets/bulk/update",
        json=bulk_update
    )
```

### Validation & Quality

#### 17. Validate Value Set
```python
POST /api/v1/value-sets/validate
Body: ValidateValueSetRequestSchema
Response: ValidationResultSchema
```

**When to Use:**
- Pre-validating data before creation/update
- Checking data quality without making changes
- Pre-import validation of external data

**Example:**
```python
validation_request = {
    "value_set_data": {
        "key": "test_value_set",
        "name": "Test Value Set",
        "module": "testing",
        "items": [{"code": "TEST1", "labels": {"en": "Test"}}],
        "created_by": "user"
    },
    "validation_level": "full",
    "check_conflicts": True
}

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/api/v1/value-sets/validate",
        json=validation_request
    )
    result = response.json()
    if result["is_valid"]:
        print("Validation passed!")
```

### Archive & Restore

#### 18. Archive Value Set
```python
POST /api/v1/value-sets/{key}/archive
Body: ArchiveRestoreRequestSchema
Response: ArchiveRestoreResponseSchema
```

**When to Use:**
- Retiring value sets while preserving historical data
- Removing value sets from active use
- Preferred alternative to deletion

**Example:**
```python
archive_request = {
    "reason": "Value set superseded by new version",
    "archived_by": "admin_user"
}

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/api/v1/value-sets/old_medical_codes/archive",
        json=archive_request
    )
```

#### 19. Restore Value Set
```python
POST /api/v1/value-sets/{key}/restore
Body: ArchiveRestoreRequestSchema
Response: ArchiveRestoreResponseSchema
```

**When to Use:**
- Reactivating archived value sets
- Recovering accidentally archived value sets
- Returning value sets to active use

**Example:**
```python
restore_request = {
    "reason": "Value set needed again",
    "restored_by": "admin_user"
}

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/api/v1/value-sets/archived_codes/restore",
        json=restore_request
    )
```

### Statistics & Monitoring

#### 20. Get Value Set Statistics
```python
GET /api/v1/value-sets/statistics/summary
Response: dict with comprehensive stats
```

**When to Use:**
- Generating admin dashboards
- Monitoring system health
- Understanding value set distribution and usage

**Example:**
```python
async with httpx.AsyncClient() as client:
    response = await client.get(
        "http://localhost:8000/api/v1/value-sets/statistics/summary"
    )
    stats = response.json()
    print(f"Total value sets: {stats['total_value_sets']}")
    print(f"Total items: {stats['total_items']}")
```

### Import & Export

#### 21. Export Value Set
```python
GET /api/v1/value-sets/{key}/export?format={json|csv}
Response: Exported data in specified format
```

**When to Use:**
- Extracting data for external systems
- Creating backups
- Data migration or integration

**Example:**
```python
async with httpx.AsyncClient() as client:
    # Export as JSON
    response = await client.get(
        "http://localhost:8000/api/v1/value-sets/medical_specialties/export",
        params={"format": "json"}
    )

    # Export as CSV
    csv_response = await client.get(
        "http://localhost:8000/api/v1/value-sets/medical_specialties/export",
        params={"format": "csv"}
    )
```

#### 22. Import Value Set
```python
POST /api/v1/value-sets/import?format={json|csv}&created_by={user}
Body: dict (import data)
Response: ValueSetResponseSchema
```

**When to Use:**
- Importing from external systems
- Restoring from backup
- Data migration scenarios

**Example:**
```python
import_data = {
    "key": "imported_codes",
    "name": "Imported Codes",
    "module": "imported",
    "items": [{"code": "IMP1", "labels": {"en": "Item 1"}}]
}

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/api/v1/value-sets/import",
        params={"format": "json", "created_by": "import_user"},
        json=import_data
    )
```

#### 24. Health Check
```python
GET /api/v1/value-sets/health
Response: {"status": "healthy", "module": "value_sets", ...}
```

**When to Use:**
- Monitoring API availability
- Load balancer health checks
- System status verification

**Example:**
```python
async with httpx.AsyncClient() as client:
    response = await client.get(
        "http://localhost:8000/api/v1/value-sets/health"
    )
    health = response.json()
    assert health["status"] == "healthy"
```

## How to Use the Router Layer

### In Your Application

**1. Register the Router in Your FastAPI App:**
```python
from fastapi import FastAPI
from routers.value_set_router import router as value_set_router

app = FastAPI()
app.include_router(value_set_router)

# Router is now available at /api/v1/value-sets/*
```

**2. Make HTTP Requests from Client Code:**
```python
import httpx

# Using httpx for async requests
async with httpx.AsyncClient() as client:
    # Create
    response = await client.post(
        "http://localhost:8000/api/v1/value-sets/",
        json={"key": "test", "name": "Test", "module": "test", "created_by": "user"}
    )

    # Read
    response = await client.get("http://localhost:8000/api/v1/value-sets/test")

    # Update
    response = await client.put(
        "http://localhost:8000/api/v1/value-sets/test",
        json={"name": "Updated Test", "updated_by": "user"}
    )
```

**3. Using FastAPI's Dependency Injection:**
```python
# The router already handles dependency injection internally
# You don't need to manually inject the service when making HTTP calls
# Just call the endpoints and they'll work automatically
```

### Testing with FastAPI TestClient

```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_value_set():
    response = client.post(
        "/api/v1/value-sets/",
        json={
            "key": "test_set",
            "name": "Test Set",
            "module": "testing",
            "created_by": "tester"
        }
    )
    assert response.status_code == 200
    assert response.json()["key"] == "test_set"
```

## Common Patterns

### Error Handling
All endpoints return appropriate HTTP status codes:
- **200**: Success
- **400**: Bad Request (validation error, business rule violation)
- **404**: Not Found (value set doesn't exist)
- **500**: Internal Server Error

**Example:**
```python
try:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/api/v1/value-sets/nonexistent"
        )
        response.raise_for_status()
except httpx.HTTPStatusError as e:
    if e.response.status_code == 404:
        print("Value set not found")
    elif e.response.status_code == 400:
        print(f"Validation error: {e.response.json()['detail']}")
```

### Pagination Pattern
```python
async def get_all_value_sets():
    all_items = []
    skip = 0
    limit = 100

    async with httpx.AsyncClient() as client:
        while True:
            response = await client.get(
                "http://localhost:8000/api/v1/value-sets/",
                params={"skip": skip, "limit": limit}
            )
            data = response.json()
            all_items.extend(data["items"])

            if not data["has_more"]:
                break
            skip += limit

    return all_items
```

### Bulk Operations Pattern
```python
# Instead of this (slow):
for item in items:
    await client.post(f"/api/v1/value-sets/{key}/items", json={...})

# Do this (fast):
await client.post(
    f"/api/v1/value-sets/{key}/items/bulk-add",
    json={"items": items, "updated_by": "user"}
)
```

## Integration with Other Layers

### Router → Service → Repository Flow
```python
# 1. HTTP Request arrives at Router
@router.post("/")
async def create_value_set(
    create_data: ValueSetCreateSchema,
    service: ValueSetService = Depends(get_value_set_service)
):
    # 2. Router validates request (Pydantic)
    # 3. Router calls Service Layer
    return await service.create_value_set(create_data)

# Service Layer handles business logic
# Repository Layer handles database operations
# Response flows back through the same path
```

### Dependency Injection
```python
# Database connection is injected automatically
def get_value_set_service(db: AsyncIOMotorDatabase = Depends(get_db)):
    repository = ValueSetRepository(db)
    return ValueSetService(repository)

# FastAPI handles the injection chain:
# get_db() → get_value_set_service() → endpoint handler
```

## What NOT to Do

❌ **Don't call repository methods directly from routers**
```python
# Bad
@router.get("/{key}")
async def get_value_set(key: str, db = Depends(get_db)):
    repo = ValueSetRepository(db)
    return await repo.find_by_key(key)  # Bypasses business logic!
```

✅ **Do use the service layer**
```python
# Good
@router.get("/{key}")
async def get_value_set(key: str, service = Depends(get_value_set_service)):
    return await service.get_value_set_by_key(key)
```

❌ **Don't implement business logic in routers**
```python
# Bad
@router.post("/")
async def create_value_set(data: ValueSetCreateSchema, service = Depends(...)):
    if len(data.items) > 1000:  # Business logic in router!
        raise HTTPException(400, "Too many items")
    return await service.create_value_set(data)
```

✅ **Do keep routers focused on HTTP concerns**
```python
# Good - business logic is in service layer
@router.post("/")
async def create_value_set(data: ValueSetCreateSchema, service = Depends(...)):
    try:
        return await service.create_value_set(data)
    except ValueError as e:
        raise HTTPException(400, detail=str(e))
```

❌ **Don't parse ObjectIds in routers**
```python
# Bad
@router.get("/by-id/{id}")
async def get_by_id(id: str):
    object_id = ObjectId(id)  # Domain logic in router!
    ...
```

## Interactive API Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

These interfaces allow you to:
- View all endpoints and their schemas
- Test endpoints directly from the browser
- See request/response examples
- Understand validation requirements

## Summary

**Router Layer Purpose:**
- HTTP interface to the value set system
- Request validation and response formatting
- Dependency injection and service orchestration
- API documentation generation

**Key Files:**
- `value_set_router.py` - All 24 REST endpoints

**When to Use:**
- Making HTTP API calls from client applications
- Building web/mobile interfaces for value set management
- Integrating with external systems via REST API
- Testing with HTTP clients or FastAPI TestClient

**Integration:**
- Depends on Service Layer for business logic
- Uses Pydantic schemas for request/response validation
- Leverages FastAPI's dependency injection system
- Generates OpenAPI documentation automatically