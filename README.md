# ValueSets Platform Backend

A FastAPI-based backend service for managing platform value sets (enums) with multi-language support, authentication, and role-based access control.

## 🏗️ Architecture

The backend follows a clean architecture pattern:

```
Repository Root/
├── main.py                    # Application entry point
├── README.md                  # This documentation
├── requirements.txt           # Python dependencies
├── .env                      # Environment configuration
├── .gitignore                # Git ignore rules
├── config/                    # Configuration management
│   ├── settings.py           # Application settings
│   └── database.py           # Database connection management
├── auth/                      # Authentication & Authorization
│   ├── jwt_handler.py        # JWT token management
│   └── auth_bearer.py        # Authentication middleware
├── routers/                   # API route definitions
│   ├── __init__.py
│   └── valuesets_router.py   # ValueSets API endpoints
├── func_spec/                 # Business logic layer
│   ├── handlers/             # Request/response handling
│   ├── services/             # Business logic
│   └── repositories/         # Data access layer
├── schema_spec/               # Data models & validation
│   ├── models/               # Database models
│   └── schemas/              # Pydantic schemas
├── src/                       # Database seeding & utilities
│   ├── auth/                 # Auth-related utilities
│   └── database/             # Database seeding scripts
└── tests/                     # Comprehensive test suite
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- MongoDB Atlas account (or local MongoDB)
- pip package manager

### 1. Installation

```bash
git clone https://github.com/BhanuSakethAI4AP/ValueSet.git
cd ValueSet
pip install -r requirements.txt
```

### 2. Environment Setup

Create a `.env` file in the project root directory:

```bash
# MongoDB Configuration
MONGO_URL=mongodb+srv://your-username:your-password@cluster.mongodb.net/
DB_NAME=valuesets_platform

# Security
SECRET_KEY=your-secret-key-here-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# Server Configuration
HOST=0.0.0.0
PORT=8001
DEBUG=true
```

### 3. Database Setup

The application will automatically connect to MongoDB. To seed the database with initial data:

```bash
cd src/database
python seed_merged_data.py
```

This creates:
- **6 Users** with different roles (password: `pass@123`)
- **6 Roles** with permissions (SystemAdmin, Developer, Operator, etc.)
- **8 Sample ValueSets** for testing

### 4. Start the Server

```bash
python main.py
```

The server will start at: http://localhost:8001

## 📚 API Documentation

### Interactive Documentation

- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

### Health Check

```bash
curl http://localhost:8001/health
```

## 🔐 Authentication

### Login

```bash
curl -X POST "http://localhost:8001/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=pass@123"
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "user": {
    "username": "admin",
    "full_name": "System Administrator",
    "role": "SystemAdmin"
  }
}
```

### Using the Token

Include the token in the Authorization header:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  "http://localhost:8001/api/v1/enums"
```

## 📋 API Endpoints

### ValueSets Management

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/enums` | List all ValueSets | Yes |
| GET | `/api/v1/enums/{key}` | Get specific ValueSet | Yes |
| GET | `/api/v1/enums/bootstrap` | Get all active ValueSets for frontend | Yes |
| POST | `/api/v1/enums` | Create new ValueSet | Yes (create permission) |
| PUT | `/api/v1/enums/{key}` | Update ValueSet | Yes (update permission) |
| DELETE | `/api/v1/enums/{key}` | Archive ValueSet | Yes (archive permission) |

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/login` | User login |
| GET | `/api/v1/auth/me` | Get current user info |
| GET | `/api/v1/auth/permissions` | Get user permissions |
| POST | `/api/v1/auth/verify-permission` | Verify specific permission |

## 💡 Usage Examples

### 1. Create a New ValueSet

```bash
curl -X POST "http://localhost:8001/api/v1/enums" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "key": "orderStatus",
    "status": "active",
    "description": "Order status values",
    "items": [
      {
        "code": "PENDING",
        "labels": {
          "en": "Pending",
          "hi": "लंबित"
        }
      },
      {
        "code": "CONFIRMED",
        "labels": {
          "en": "Confirmed",
          "hi": "पुष्ट"
        }
      }
    ]
  }'
```

### 2. Get ValueSet with Language Support

```bash
# English (default)
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8001/api/v1/enums/orderStatus"

# Hindi
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8001/api/v1/enums/orderStatus?lang=hi"
```

### 3. Bootstrap for Frontend

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8001/api/v1/enums/bootstrap"
```

Response:
```json
{
  "data": {
    "orderStatus": [
      {"code": "PENDING", "label": "Pending"},
      {"code": "CONFIRMED", "label": "Confirmed"}
    ],
    "priority": [
      {"code": "HIGH", "label": "High"},
      {"code": "MEDIUM", "label": "Medium"}
    ]
  }
}
```

### 4. Update ValueSet

```bash
curl -X PUT "http://localhost:8001/api/v1/enums/orderStatus" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Updated order status values",
    "items": [
      {
        "code": "PENDING",
        "labels": {"en": "Pending", "hi": "लंबित"}
      },
      {
        "code": "CONFIRMED", 
        "labels": {"en": "Confirmed", "hi": "पुष्ट"}
      },
      {
        "code": "DELIVERED",
        "labels": {"en": "Delivered", "hi": "वितरित"}
      }
    ]
  }'
```

## 👥 User Roles & Permissions

### Default Users

| Username | Role | Password | Permissions |
|----------|------|----------|-------------|
| admin | SystemAdmin | pass@123 | All permissions |
| developer1 | Developer | pass@123 | valuesets: create, read, update |
| operator1 | Operator | pass@123 | valuesets: read, update |
| support1 | Support | pass@123 | valuesets: read |
| viewer1 | Viewer | pass@123 | valuesets: read |
| app_service | Application | pass@123 | valuesets: read |

### Permission System

The system uses resource-action based permissions:
- **Resource**: `valuesets`, `users`, `system`
- **Actions**: `create`, `read`, `update`, `archive`, `admin`

Example permission check:
```bash
curl -X POST "http://localhost:8001/api/v1/auth/verify-permission" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d "resource=valuesets&action=create"
```

## 🧪 Testing

### Run All Tests

```bash
# Run comprehensive CRUD tests
python tests/test_final_crud.py
```

### Test Individual Components

```bash
# Test CRUD operations  
python tests/test_simple_crud.py

# Comprehensive endpoint testing
python tests/test_all_endpoints.py

# Test with dummy data
python tests/test_crud_operations.py
```

### Expected Test Results

```
=== FINAL CRUD TEST ===
1. Logging in...
   Login successful
2. Testing CREATE with key: finalTest7708
   CREATE successful!
3. Testing LIST...
   LIST successful - Found 13 ValueSets
4. Testing GET BY KEY...
   GET successful!
5. Testing BOOTSTRAP...
   BOOTSTRAP successful - 10 active ValueSets
6. Testing UPDATE...
   UPDATE successful!
7. Testing DELETE (Archive)...
   DELETE successful (204 No Content)
8. Verifying archive status...
   CORRECTLY ARCHIVED!
9. Verifying bootstrap excludes archived...
   CORRECT: Archived ValueSet excluded from bootstrap

=== ALL CRUD OPERATIONS TESTED SUCCESSFULLY ===
```

## 🔧 Configuration

### Settings (config/settings.py)

```python
class Settings(BaseSettings):
    # MongoDB
    mongo_url: str = "mongodb://localhost:27017"
    db_name: str = "valuesets_platform"
    
    # Security
    secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440
    
    # Server
    host: str = "0.0.0.0" 
    port: int = 8001
    debug: bool = False
```

### Database Connection

The database connection is managed in `config/database.py`:
- Automatic connection on startup
- Connection pooling with Motor (async MongoDB driver)
- Graceful shutdown handling

## 🚨 Error Handling

The API returns standard HTTP status codes:

- **200**: Success
- **201**: Created
- **204**: No Content (for deletes)
- **400**: Bad Request (validation errors)
- **401**: Unauthorized
- **403**: Forbidden (insufficient permissions)
- **404**: Not Found
- **500**: Internal Server Error

Error response format:
```json
{
  "detail": "Error message description"
}
```

## 🔄 Data Models

### ValueSet Structure

```json
{
  "id": "string",
  "key": "string",
  "status": "active|archived",
  "description": "string",
  "items": [
    {
      "code": "string",
      "labels": {
        "en": "English label",
        "hi": "Hindi label"
      }
    }
  ],
  "created_by": "string",
  "created_date_time": "2024-01-01T00:00:00Z",
  "update_date_time": "2024-01-01T00:00:00Z"
}
```

## 🛠️ Development

### Adding New Endpoints

1. **Define schema** in `schema_spec/schemas/`
2. **Add repository method** in `func_spec/repositories/`
3. **Implement business logic** in `func_spec/services/`
4. **Create handler** in `func_spec/handlers/`
5. **Add route** in `routers/`

### Code Structure Guidelines

- Use async/await for all database operations
- Implement proper error handling and validation
- Follow the repository pattern for data access
- Use Pydantic for request/response validation
- Maintain separation of concerns across layers

## 📖 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [MongoDB Motor Documentation](https://motor.readthedocs.io/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [JWT.io](https://jwt.io/) for token debugging

## 🤝 Contributing

1. Follow the existing architecture patterns
2. Add tests for new functionality
3. Update API documentation
4. Ensure proper error handling
5. Maintain backwards compatibility

## 📝 License

This project is part of the ValueSets Platform. All rights reserved.