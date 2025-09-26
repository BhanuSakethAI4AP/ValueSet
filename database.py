import os
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for MongoDB connection
client: Optional[AsyncIOMotorClient] = None
database: Optional[AsyncIOMotorDatabase] = None


async def connect_to_mongodb() -> AsyncIOMotorDatabase:
    """
    Establishes connection to MongoDB database.

    Returns:
        AsyncIOMotorDatabase: Connected database instance

    Raises:
        ConnectionFailure: If connection to MongoDB fails
        ValueError: If required environment variables are missing
    """
    global client, database

    # Get connection details from environment
    connection_string = os.getenv("MONGODB_CONNECTION_STRING")
    db_name = os.getenv("DB_NAME")

    # Validate environment variables
    if not connection_string:
        raise ValueError("MONGODB_CONNECTION_STRING not found in environment variables")
    if not db_name:
        raise ValueError("DB_NAME not found in environment variables")

    # Clean up DB_NAME (remove any trailing semicolon)
    db_name = db_name.rstrip(';')

    try:
        # Create MongoDB client with connection pooling
        client = AsyncIOMotorClient(
            connection_string,
            maxPoolSize=50,
            minPoolSize=10,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000,
            retryWrites=True,
            w='majority'
        )

        # Verify connection
        await client.admin.command('ping')
        logger.info(f"Successfully connected to MongoDB cluster")

        # Get database instance
        database = client[db_name]
        logger.info(f"Connected to database: {db_name}")

        return database

    except ServerSelectionTimeoutError as e:
        logger.error(f"MongoDB server selection timeout: {e}")
        raise ConnectionFailure(f"Could not connect to MongoDB: Server selection timeout")
    except ConnectionFailure as e:
        logger.error(f"MongoDB connection failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error connecting to MongoDB: {e}")
        raise ConnectionFailure(f"Unexpected error: {e}")


async def disconnect_from_mongodb():
    """
    Closes the MongoDB connection.
    """
    global client

    if client:
        client.close()
        logger.info("Disconnected from MongoDB")
        client = None


def get_database() -> AsyncIOMotorDatabase:
    """
    Returns the current database instance.

    Returns:
        AsyncIOMotorDatabase: Current database instance

    Raises:
        RuntimeError: If database is not connected
    """
    if database is None:
        raise RuntimeError("Database not connected. Call connect_to_mongodb() first.")
    return database


def get_collection(collection_name: str):
    """
    Get a specific collection from the database.

    Args:
        collection_name: Name of the collection to retrieve

    Returns:
        AsyncIOMotorCollection: Collection instance

    Raises:
        RuntimeError: If database is not connected
    """
    db = get_database()
    return db[collection_name]


async def check_connection() -> bool:
    """
    Checks if the database connection is alive.

    Returns:
        bool: True if connected, False otherwise
    """
    global client

    if not client:
        return False

    try:
        await client.admin.command('ping')
        return True
    except:
        return False


# FastAPI dependency for database access
async def get_db():
    """
    Dependency injection for FastAPI routes.

    Yields:
        AsyncIOMotorDatabase: Database instance for use in routes
    """
    db = get_database()
    try:
        yield db
    finally:
        # Connection remains open (connection pooling)
        pass


# Value Sets specific collection helper
def get_value_sets_collection():
    """
    Get the value_sets collection.

    Returns:
        AsyncIOMotorCollection: Value sets collection instance
    """
    return get_collection("value_sets")