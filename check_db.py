import asyncio
import motor.motor_asyncio
import os
import json

import sys

async def main():
    sys.stdout.reconfigure(encoding='utf-8')
    mongo_url = "mongodb://root:root@localhost:27017/?authSource=admin"
    client = motor.motor_asyncio.AsyncIOMotorClient(mongo_url)
    
    # 1. Show all databases
    dbs = await client.list_database_names()
    print("Databases:", dbs)
    
    # 2. Query Resume DB in Postgres (Wait, let's query MongoDB first)
    db = client["CVIntelligenceDB"]
    cols = await db.list_collection_names()
    print("Collections in CVIntelligenceDB:", cols)
    
    # Let's see what documents are in resume_analyses
    col = db["resume_analyses"]
    cursor = col.find({})
    docs = await cursor.to_list(length=10)
    print(f"\nFound {len(docs)} documents in resume_analyses:")
    for doc in docs:
        doc["_id"] = str(doc["_id"])
        # convert any datetime objects to string
        for k, v in doc.items():
            if hasattr(v, "isoformat"):
                doc[k] = v.isoformat()
        print(json.dumps(doc, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())
