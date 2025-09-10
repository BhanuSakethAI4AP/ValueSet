import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from bson import ObjectId
import os
from .seed_data import seed_value_sets


async def load_seed_data(mongo_url: str = None, db_name: str = None):
    mongo_url = mongo_url or os.getenv("MONGO_URL", "mongodb://localhost:27017")
    db_name = db_name or os.getenv("DB_NAME", "platform_db")
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    collection = db.valueSets
    
    await collection.create_index([("key", 1)], unique=True)
    await collection.create_index([("status", 1)])
    
    system_user_id = ObjectId()
    
    loaded_count = 0
    skipped_count = 0
    
    for seed_set in seed_value_sets:
        existing = await collection.find_one({"key": seed_set["key"]})
        
        if existing:
            print(f"ValueSet '{seed_set['key']}' already exists, skipping...")
            skipped_count += 1
            continue
        
        doc = {
            **seed_set,
            "created_by": system_user_id,
            "created_date_time": datetime.utcnow(),
            "update_date_time": datetime.utcnow()
        }
        
        await collection.insert_one(doc)
        print(f"Loaded ValueSet: {seed_set['key']}")
        loaded_count += 1
    
    print(f"\nSeed data loading complete:")
    print(f"  - Loaded: {loaded_count} value sets")
    print(f"  - Skipped: {skipped_count} value sets (already exist)")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(load_seed_data())