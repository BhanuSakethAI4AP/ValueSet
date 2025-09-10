from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
from .settings import settings

class DatabaseManager:
    client: Optional[AsyncIOMotorClient] = None
    database: Optional[AsyncIOMotorDatabase] = None

database_manager = DatabaseManager()

async def connect_to_mongo():
    """Create database connection"""
    database_manager.client = AsyncIOMotorClient(settings.mongo_url)
    database_manager.database = database_manager.client[settings.db_name]
    print(f"Connected to MongoDB: {settings.db_name}")

async def close_mongo_connection():
    """Close database connection"""
    if database_manager.client:
        database_manager.client.close()
        print("MongoDB connection closed")

def get_database() -> AsyncIOMotorDatabase:
    """Get database instance"""
    if database_manager.database is None:
        raise RuntimeError("Database not initialized")
    return database_manager.database