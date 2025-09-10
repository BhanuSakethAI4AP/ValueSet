import asyncio
import os
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from passlib.context import CryptContext
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# MongoDB connection
MONGO_URL = os.getenv("MONGO_URL", "mongodb+srv://pbhanusaketh1602:Bhanu%402002@saketh.qsgehh3.mongodb.net/")
DB_NAME = os.getenv("DB_NAME", "valuesets_platform")

# Seed data for roles with embedded permissions
roles_data = [
    {
        "name": "System Administrator",
        "code": "SystemAdmin",
        "description": "Full system access with all administrative privileges",
        "is_active": True,
        "is_system": True,
        "permissions": [
            {
                "resource": "system",
                "actions": ["*"],
                "description": "Full system administration access"
            },
            {
                "resource": "valuesets",
                "actions": ["create", "read", "update", "delete", "archive", "refresh_cache"],
                "description": "Full access to ValueSets management"
            },
            {
                "resource": "users",
                "actions": ["create", "read", "update", "delete"],
                "description": "Full access to user management"
            },
            {
                "resource": "roles",
                "actions": ["create", "read", "update", "delete"],
                "description": "Full access to role management"
            },
            {
                "resource": "reports",
                "actions": ["read", "create", "export"],
                "description": "Full access to reports"
            }
        ]
    },
    {
        "name": "Developer",
        "code": "Developer",
        "description": "Developer with ValueSets management capabilities",
        "is_active": True,
        "is_system": True,
        "permissions": [
            {
                "resource": "valuesets",
                "actions": ["create", "read", "update", "delete", "archive", "refresh_cache"],
                "description": "Full access to ValueSets management"
            },
            {
                "resource": "reports",
                "actions": ["read"],
                "description": "View reports"
            }
        ]
    },
    {
        "name": "Operator",
        "code": "Operator",
        "description": "Operator with read-only access",
        "is_active": True,
        "is_system": True,
        "permissions": [
            {
                "resource": "valuesets",
                "actions": ["read", "bootstrap"],
                "description": "Read-only access to ValueSets"
            },
            {
                "resource": "reports",
                "actions": ["read"],
                "description": "View reports"
            }
        ]
    },
    {
        "name": "Support",
        "code": "Support",
        "description": "Support staff with read-only access",
        "is_active": True,
        "is_system": True,
        "permissions": [
            {
                "resource": "valuesets",
                "actions": ["read", "bootstrap"],
                "description": "Read-only access to ValueSets"
            },
            {
                "resource": "reports",
                "actions": ["read"],
                "description": "View reports"
            },
            {
                "resource": "users",
                "actions": ["read"],
                "description": "View user information"
            }
        ]
    },
    {
        "name": "Application",
        "code": "Application",
        "description": "Application/UI read-only access for consumption",
        "is_active": True,
        "is_system": False,
        "permissions": [
            {
                "resource": "valuesets",
                "actions": ["read", "bootstrap"],
                "description": "Read-only access to ValueSets for application consumption"
            }
        ]
    },
    {
        "name": "Custom Role",
        "code": "Custom",
        "description": "Template for custom roles",
        "is_active": True,
        "is_system": False,
        "permissions": [
            {
                "resource": "valuesets",
                "actions": ["read"],
                "description": "Basic read access to ValueSets"
            }
        ]
    }
]

# Seed data for users (password: pass@123)
users_data = [
    {
        "username": "admin",
        "email": "admin@platform.com",
        "password": "pass@123",
        "full_name": "System Administrator",
        "role": "SystemAdmin",
        "is_active": True,
        "is_superuser": True
    },
    {
        "username": "developer1",
        "email": "developer1@platform.com",
        "password": "pass@123",
        "full_name": "John Developer",
        "role": "Developer",
        "is_active": True,
        "is_superuser": False
    },
    {
        "username": "developer2",
        "email": "developer2@platform.com",
        "password": "pass@123",
        "full_name": "Jane Developer",
        "role": "Developer",
        "is_active": True,
        "is_superuser": False
    },
    {
        "username": "operator1",
        "email": "operator1@platform.com",
        "password": "pass@123",
        "full_name": "Mike Operator",
        "role": "Operator",
        "is_active": True,
        "is_superuser": False
    },
    {
        "username": "support1",
        "email": "support1@platform.com",
        "password": "pass@123",
        "full_name": "Sarah Support",
        "role": "Support",
        "is_active": True,
        "is_superuser": False
    },
    {
        "username": "app_service",
        "email": "app@platform.com",
        "password": "pass@123",
        "full_name": "Application Service Account",
        "role": "Application",
        "is_active": True,
        "is_superuser": False
    }
]

# ValueSets seed data (same as before)
valuesets_data = [
    {
        "key": "errorSeverity",
        "status": "active",
        "description": "Severity levels for errors",
        "items": [
            {"code": "CRITICAL", "labels": {"en": "Critical", "hi": "गंभीर"}},
            {"code": "HIGH", "labels": {"en": "High", "hi": "उच्च"}},
            {"code": "MEDIUM", "labels": {"en": "Medium", "hi": "मध्यम"}},
            {"code": "LOW", "labels": {"en": "Low", "hi": "कम"}}
        ]
    },
    {
        "key": "errorType",
        "status": "active",
        "description": "Types of errors in the system",
        "items": [
            {"code": "Business", "labels": {"en": "Business Error", "hi": "व्यावसायिक त्रुटि"}},
            {"code": "System", "labels": {"en": "System Error", "hi": "सिस्टम त्रुटि"}},
            {"code": "Integration", "labels": {"en": "Integration Error", "hi": "एकीकरण त्रुटि"}}
        ]
    },
    {
        "key": "sourceType",
        "status": "active",
        "description": "Source types for errors and events",
        "items": [
            {"code": "api", "labels": {"en": "API", "hi": "एपीआई"}},
            {"code": "function", "labels": {"en": "Function", "hi": "फंक्शन"}},
            {"code": "screen", "labels": {"en": "Screen", "hi": "स्क्रीन"}},
            {"code": "job", "labels": {"en": "Background Job", "hi": "पृष्ठभूमि कार्य"}}
        ]
    },
    {
        "key": "environment",
        "status": "active",
        "description": "Application environment types",
        "items": [
            {"code": "prod", "labels": {"en": "Production", "hi": "उत्पादन"}},
            {"code": "stg", "labels": {"en": "Staging", "hi": "स्टेजिंग"}},
            {"code": "dev", "labels": {"en": "Development", "hi": "विकास"}}
        ]
    },
    {
        "key": "otpChannel",
        "status": "active",
        "description": "OTP delivery channels",
        "items": [
            {"code": "sms", "labels": {"en": "SMS", "hi": "एसएमएस"}},
            {"code": "email", "labels": {"en": "Email", "hi": "ईमेल"}},
            {"code": "whatsapp", "labels": {"en": "WhatsApp", "hi": "व्हाट्सएप"}}
        ]
    },
    {
        "key": "userStatus",
        "status": "active",
        "description": "User account status",
        "items": [
            {"code": "active", "labels": {"en": "Active", "hi": "सक्रिय"}},
            {"code": "inactive", "labels": {"en": "Inactive", "hi": "निष्क्रिय"}},
            {"code": "suspended", "labels": {"en": "Suspended", "hi": "निलंबित"}},
            {"code": "deleted", "labels": {"en": "Deleted", "hi": "हटाया गया"}}
        ]
    },
    {
        "key": "notificationType",
        "status": "active",
        "description": "Types of notifications",
        "items": [
            {"code": "info", "labels": {"en": "Information", "hi": "जानकारी"}},
            {"code": "warning", "labels": {"en": "Warning", "hi": "चेतावनी"}},
            {"code": "error", "labels": {"en": "Error", "hi": "त्रुटि"}},
            {"code": "success", "labels": {"en": "Success", "hi": "सफलता"}}
        ]
    },
    {
        "key": "auditAction",
        "status": "active",
        "description": "Audit log action types",
        "items": [
            {"code": "CREATE", "labels": {"en": "Create", "hi": "बनाएं"}},
            {"code": "UPDATE", "labels": {"en": "Update", "hi": "अपडेट"}},
            {"code": "DELETE", "labels": {"en": "Delete", "hi": "हटाएं"}},
            {"code": "ARCHIVE", "labels": {"en": "Archive", "hi": "संग्रह"}},
            {"code": "LOGIN", "labels": {"en": "Login", "hi": "लॉगिन"}},
            {"code": "LOGOUT", "labels": {"en": "Logout", "hi": "लॉगआउट"}}
        ]
    }
]


async def seed_database():
    """Seed the database with merged roles/permissions structure"""
    print("Starting database seeding with merged roles/permissions...")
    print(f"Connecting to MongoDB Atlas...")
    print(f"Database: {DB_NAME}")
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    try:
        # Drop old permissions collection if exists
        print("\nCleaning up old collections...")
        if "permissions" in await db.list_collection_names():
            await db.permissions.drop()
            print("Dropped old permissions collection")
        
        # Create indexes
        print("\nCreating indexes...")
        
        # ValueSets indexes
        await db.valueSets.create_index([("key", 1)], unique=True)
        await db.valueSets.create_index([("status", 1)])
        
        # Users indexes
        await db.users.create_index([("username", 1)], unique=True)
        await db.users.create_index([("email", 1)], unique=True)
        
        # Roles indexes (with embedded permissions)
        await db.roles.create_index([("code", 1)], unique=True)
        await db.roles.create_index([("is_system", 1)])
        
        print("Indexes created successfully")
        
        # Seed Roles with embedded permissions
        print("\nSeeding roles with embedded permissions...")
        roles_count = 0
        for role in roles_data:
            existing = await db.roles.find_one({"code": role["code"]})
            if not existing:
                role["created_date_time"] = datetime.utcnow()
                role["update_date_time"] = datetime.utcnow()
                await db.roles.insert_one(role)
                roles_count += 1
                perm_count = len(role["permissions"])
                print(f"  [OK] Created role: {role['name']} with {perm_count} permissions")
            else:
                # Update existing role with new permissions structure
                await db.roles.update_one(
                    {"code": role["code"]},
                    {"$set": {
                        "permissions": role["permissions"],
                        "is_system": role.get("is_system", False),
                        "update_date_time": datetime.utcnow()
                    }}
                )
                print(f"  [UPDATE] Updated role: {role['name']} with new permissions")
        
        # Seed Users
        print("\nSeeding users...")
        users_count = 0
        admin_id = None
        for user in users_data:
            existing = await db.users.find_one({"username": user["username"]})
            if not existing:
                # Hash the password
                user["password_hash"] = pwd_context.hash(user["password"])
                del user["password"]  # Remove plain password
                
                user["created_date_time"] = datetime.utcnow()
                user["update_date_time"] = datetime.utcnow()
                
                result = await db.users.insert_one(user)
                if user["username"] == "admin":
                    admin_id = result.inserted_id
                users_count += 1
                print(f"  [OK] Created user: {user['username']} (role: {user['role']})")
            else:
                if user["username"] == "admin":
                    admin_id = existing["_id"]
                print(f"  [SKIP] User already exists: {user['username']}")
        
        # Seed ValueSets
        print("\nSeeding ValueSets...")
        valuesets_count = 0
        for valueset in valuesets_data:
            existing = await db.valueSets.find_one({"key": valueset["key"]})
            if not existing:
                valueset["created_by"] = admin_id or ObjectId()
                valueset["created_date_time"] = datetime.utcnow()
                valueset["update_date_time"] = datetime.utcnow()
                await db.valueSets.insert_one(valueset)
                valuesets_count += 1
                print(f"  [OK] Created ValueSet: {valueset['key']} ({len(valueset['items'])} items)")
            else:
                print(f"  [SKIP] ValueSet already exists: {valueset['key']}")
        
        # Print summary
        print("\n" + "="*60)
        print("SEEDING SUMMARY (MERGED MODEL)")
        print("="*60)
        print(f"Roles created/updated: {len(roles_data)}")
        print(f"Users created: {users_count}/{len(users_data)}")
        print(f"ValueSets created: {valuesets_count}/{len(valuesets_data)}")
        print("="*60)
        
        # Print role permissions summary
        print("\nROLE PERMISSIONS SUMMARY")
        print("="*60)
        for role in roles_data:
            print(f"\n{role['name']} ({role['code']}):")
            for perm in role['permissions']:
                actions = ", ".join(perm['actions']) if perm['actions'] != ["*"] else "ALL"
                print(f"  - {perm['resource']}: {actions}")
        
        print("\n" + "="*60)
        print("USER CREDENTIALS")
        print("="*60)
        print("All users have the password: pass@123")
        print("\nAvailable users:")
        for user in users_data:
            print(f"  - {user['username']} ({user['role']})")
        print("="*60)
        
        print("\nDatabase seeding completed successfully!")
        
    except Exception as e:
        print(f"\nError during seeding: {str(e)}")
        raise
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(seed_database())