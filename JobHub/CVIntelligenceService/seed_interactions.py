import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

MONGO_URL = os.getenv("MONGO_URL", "mongodb://root:root@mongodb:27017/?authSource=admin")
MONGO_DB = os.getenv("MONGO_DB", "CVIntelligenceDB")

async def seed_data():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[MONGO_DB]
    col = db["job_view_histories"]
    
    print("Clearing old interactions...")
    await col.delete_many({})
    
    test_records = [
        # User A (target)
        {
            "customer_id": "68fbcac8-fef5-478c-9c57-3d56907353ae",
            "job_id": "c48cfc14-e38e-4535-aa43-b5e73effed2e",
            "interaction_type": "APPLY",
            "interaction_score": 5.0,
            "timestamp": datetime.utcnow()
        },
        # User B
        {
            "customer_id": "user-id-2",
            "job_id": "c48cfc14-e38e-4535-aa43-b5e73effed2e",
            "interaction_type": "APPLY",
            "interaction_score": 5.0,
            "timestamp": datetime.utcnow()
        },
        {
            "customer_id": "user-id-2",
            "job_id": "job-id-3",
            "interaction_type": "SAVE",
            "interaction_score": 3.0,
            "timestamp": datetime.utcnow()
        },
        {
            "customer_id": "user-id-2",
            "job_id": "job-id-4",
            "interaction_type": "VIEW",
            "interaction_score": 1.0,
            "timestamp": datetime.utcnow()
        },
        # User C
        {
            "customer_id": "user-id-3",
            "job_id": "c48cfc14-e38e-4535-aa43-b5e73effed2e",
            "interaction_type": "SAVE",
            "interaction_score": 3.0,
            "timestamp": datetime.utcnow()
        },
        {
            "customer_id": "user-id-3",
            "job_id": "job-id-3",
            "interaction_type": "APPLY",
            "interaction_score": 5.0,
            "timestamp": datetime.utcnow()
        },
        {
            "customer_id": "user-id-3",
            "job_id": "job-id-5",
            "interaction_type": "CLICK",
            "interaction_score": 2.0,
            "timestamp": datetime.utcnow()
        }
    ]
    
    print(f"Seeding {len(test_records)} mock interaction logs to {MONGO_URL}...")
    await col.insert_many(test_records)
    print("Seeding finished successfully.")

if __name__ == "__main__":
    asyncio.run(seed_data())
