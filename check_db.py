#!/usr/bin/env python3
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check_db():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['bot_manager']
    
    count = await db['groups'].count_documents({})
    print(f"Groups: {count}")
    
    if count > 0:
        group = await db['groups'].find_one({})
        print(f"Sample group: {group.get('group_name', 'N/A')}")
    
    client.close()

asyncio.run(check_db())
