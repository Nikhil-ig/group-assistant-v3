#!/usr/bin/env python3
"""
Quick test script to verify dashboard API endpoints
Run this after starting the backend to test the API
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_dashboard_api():
    """Test dashboard API endpoints"""
    print("🧪 Testing Dashboard API Endpoints...\n")
    
    try:
        # Import after adding to path
        from motor.motor_asyncio import AsyncIOMotorClient
        from centralized_api.config import MONGODB_URI, MONGODB_DATABASE
        import json
        
        # Connect to MongoDB
        print(f"📡 Connecting to MongoDB: {MONGODB_URI}...")
        client = AsyncIOMotorClient(MONGODB_URI)
        db = client[MONGODB_DATABASE]
        print("✅ Connected to MongoDB\n")
        
        # Test collections
        collections = ['groups', 'users', 'actions', 'logs']
        
        for collection_name in collections:
            col = db[collection_name]
            count = await col.count_documents({})
            print(f"📊 {collection_name.upper()}: {count} documents")
            
            # Show sample
            sample = await col.find_one({})
            if sample:
                print(f"   Sample: {json.dumps({k: str(v)[:50] for k, v in list(sample.items())[:3]}, indent=6)}")
        
        print("\n✅ All collections accessible!")
        
        # Test statistics calculation
        print("\n📈 Calculating Statistics...")
        
        groups_col = db['groups']
        users_col = db['users']
        actions_col = db['actions']
        
        total_groups = await groups_col.count_documents({})
        total_users = await users_col.count_documents({})
        total_actions = await actions_col.count_documents({})
        
        total_members = 0
        total_admins = 0
        async for group in groups_col.find({}):
            total_members += group.get('member_count', 0)
            total_admins += group.get('admin_count', 0)
        
        active_users = await users_col.count_documents({'is_active': True})
        
        print(f"""
        Groups: {total_groups}
        Members: {total_members}
        Admins: {total_admins}
        Users: {total_users}
        Active Users: {active_users}
        Actions: {total_actions}
        """)
        
        print("✅ Dashboard API is ready!")
        print("\n📝 Next steps:")
        print("  1. Start backend: python -m uvicorn centralized_api.app:app --reload")
        print("  2. Start frontend: cd web/frontend && npm run dev")
        print("  3. Open browser: http://localhost:5174")
        print("  4. Login and view dashboard")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        try:
            client.close()
        except:
            pass
    
    return True

if __name__ == '__main__':
    result = asyncio.run(test_dashboard_api())
    sys.exit(0 if result else 1)
