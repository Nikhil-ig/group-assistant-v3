#!/usr/bin/env python3
"""
Dummy Data Generator for MongoDB
Creates sample data for testing the Bot Manager dashboard
"""

import asyncio
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
env_path = Path(__file__).resolve().parent / "centralized_api" / ".env"
load_dotenv(env_path)

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "bot_manager")

# Sample data
SAMPLE_GROUPS = [
    {
        "group_id": -1001234567890,
        "group_name": "Tech Enthusiasts",
        "description": "A group for tech lovers and programmers",
        "member_count": 1250,
        "admin_count": 5,
        "created_at": datetime.utcnow() - timedelta(days=365),
        "updated_at": datetime.utcnow(),
        "is_active": True,
    },
    {
        "group_id": -1001234567891,
        "group_name": "Digital Marketing",
        "description": "Share and discuss digital marketing strategies",
        "member_count": 892,
        "admin_count": 3,
        "created_at": datetime.utcnow() - timedelta(days=200),
        "updated_at": datetime.utcnow(),
        "is_active": True,
    },
    {
        "group_id": -1001234567892,
        "group_name": "Web Development",
        "description": "Modern web development practices and tools",
        "member_count": 1456,
        "admin_count": 7,
        "created_at": datetime.utcnow() - timedelta(days=150),
        "updated_at": datetime.utcnow(),
        "is_active": True,
    },
    {
        "group_id": -1001234567893,
        "group_name": "Machine Learning",
        "description": "ML and AI discussions",
        "member_count": 654,
        "admin_count": 4,
        "created_at": datetime.utcnow() - timedelta(days=120),
        "updated_at": datetime.utcnow(),
        "is_active": True,
    },
    {
        "group_id": -1001234567894,
        "group_name": "Startup Founders",
        "description": "Connect with other startup founders",
        "member_count": 432,
        "admin_count": 2,
        "created_at": datetime.utcnow() - timedelta(days=90),
        "updated_at": datetime.utcnow(),
        "is_active": True,
    },
]

SAMPLE_USERS = [
    {
        "user_id": 123456789,
        "username": "john_developer",
        "first_name": "John",
        "last_name": "Developer",
        "role": "superadmin",
        "email": "john@example.com",
        "managed_groups": [-1001234567890, -1001234567891, -1001234567892],
        "created_at": datetime.utcnow() - timedelta(days=365),
        "updated_at": datetime.utcnow(),
        "is_active": True,
    },
    {
        "user_id": 123456790,
        "username": "sarah_admin",
        "first_name": "Sarah",
        "last_name": "Admin",
        "role": "admin",
        "email": "sarah@example.com",
        "managed_groups": [-1001234567893],
        "created_at": datetime.utcnow() - timedelta(days=200),
        "updated_at": datetime.utcnow(),
        "is_active": True,
    },
    {
        "user_id": 123456791,
        "username": "mike_moderator",
        "first_name": "Mike",
        "last_name": "Moderator",
        "role": "admin",
        "email": "mike@example.com",
        "managed_groups": [-1001234567894],
        "created_at": datetime.utcnow() - timedelta(days=150),
        "updated_at": datetime.utcnow(),
        "is_active": True,
    },
]

SAMPLE_ACTIONS = []

# Generate sample actions for the past 30 days
action_types = ["mute", "ban", "warn", "unmute", "unban", "kick", "pin_message", "delete_message"]
user_ids = [123456789, 123456790, 123456791]
group_ids = [-1001234567890, -1001234567891, -1001234567892, -1001234567893, -1001234567894]
target_user_ids = [111111111, 222222222, 333333333, 444444444, 555555555]

for i in range(100):
    days_ago = i % 30
    hour_offset = (i * 13) % 24
    
    SAMPLE_ACTIONS.append({
        "action_id": f"action_{i:04d}",
        "action_type": action_types[i % len(action_types)],
        "group_id": group_ids[i % len(group_ids)],
        "user_id": user_ids[i % len(user_ids)],
        "target_user_id": target_user_ids[i % len(target_user_ids)],
        "target_username": f"user_{i}",
        "reason": f"Sample action reason #{i+1}",
        "status": "completed",
        "duration": 60 if i % 3 == 0 else None,  # Some actions have duration
        "created_at": datetime.utcnow() - timedelta(days=days_ago, hours=hour_offset),
        "updated_at": datetime.utcnow() - timedelta(days=days_ago, hours=hour_offset),
        "executed_by": user_ids[i % len(user_ids)],
    })


async def populate_database():
    """Populate MongoDB with dummy data"""
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[MONGODB_DATABASE]
    
    try:
        print(f"Connecting to MongoDB at {MONGODB_URI}...")
        print(f"Database: {MONGODB_DATABASE}\n")
        
        # Clear existing collections
        collections = ["groups", "users", "actions", "logs"]
        for collection_name in collections:
            await db[collection_name].delete_many({})
            print(f"✓ Cleared '{collection_name}' collection")
        
        print("\n" + "="*60)
        print("INSERTING DUMMY DATA")
        print("="*60 + "\n")
        
        # Insert groups
        print("📍 Inserting Groups...")
        result = await db["groups"].insert_many(SAMPLE_GROUPS)
        print(f"   ✓ Inserted {len(result.inserted_ids)} groups")
        for group in SAMPLE_GROUPS:
            print(f"   - {group['group_name']} (ID: {group['group_id']}, Members: {group['member_count']})")
        
        # Insert users
        print("\n👥 Inserting Users...")
        result = await db["users"].insert_many(SAMPLE_USERS)
        print(f"   ✓ Inserted {len(result.inserted_ids)} users")
        for user in SAMPLE_USERS:
            print(f"   - {user['first_name']} {user['last_name']} (@{user['username']}, Role: {user['role']})")
        
        # Insert actions
        print("\n⚡ Inserting Actions...")
        result = await db["actions"].insert_many(SAMPLE_ACTIONS)
        print(f"   ✓ Inserted {len(result.inserted_ids)} actions")
        action_counts = {}
        for action in SAMPLE_ACTIONS:
            action_type = action["action_type"]
            action_counts[action_type] = action_counts.get(action_type, 0) + 1
        
        for action_type, count in sorted(action_counts.items()):
            print(f"   - {action_type}: {count}")
        
        # Print statistics
        print("\n" + "="*60)
        print("DATABASE STATISTICS")
        print("="*60)
        
        group_count = await db["groups"].count_documents({})
        user_count = await db["users"].count_documents({})
        action_count = await db["actions"].count_documents({})
        
        print(f"Groups:  {group_count}")
        print(f"Users:   {user_count}")
        print(f"Actions: {action_count}")
        print(f"Total:   {group_count + user_count + action_count} documents")
        
        # Print sample dashboard stats
        print("\n" + "="*60)
        print("SAMPLE DASHBOARD STATS")
        print("="*60)
        
        total_members = sum(g["member_count"] for g in SAMPLE_GROUPS)
        total_admins = sum(g["admin_count"] for g in SAMPLE_GROUPS)
        
        print(f"Total Groups:     {group_count}")
        print(f"Total Members:    {total_members}")
        print(f"Total Admins:     {total_admins}")
        print(f"Total Actions:    {action_count}")
        print(f"Active Users:     {user_count}")
        
        # Recent actions
        recent_actions = await db["actions"].find({}).sort("created_at", -1).limit(5).to_list(5)
        print(f"\nRecent Actions (last 5):")
        for idx, action in enumerate(recent_actions, 1):
            print(f"   {idx}. {action['action_type'].upper()} - {action['target_username']} ({action['status']})")
        
        print("\n" + "="*60)
        print("✅ DUMMY DATA CREATED SUCCESSFULLY!")
        print("="*60)
        print("\nYou can now:")
        print("1. Start the API: uvicorn centralized_api.app:app --host 0.0.0.0 --port 8001")
        print("2. Open frontend: http://localhost:5174")
        print("3. Login with Demo account to see the data")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        raise
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(populate_database())
