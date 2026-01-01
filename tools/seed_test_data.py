"""Seed script to create test admin, group, and members for end-to-end smoke tests.

Run with:
    python -m v3.tools.seed_test_data

This script uses the same config as the app (v3.config.settings) and Motor async client.
"""
import asyncio
import logging
from pprint import pprint

from motor.motor_asyncio import AsyncIOMotorClient

from ..config.settings import config
from ..services.database import DatabaseService

logger = logging.getLogger("seed")
logging.basicConfig(level=logging.INFO)


ADMIN_USER_ID = 12345
ADMIN_USERNAME = "testadmin"
ADMIN_FIRST_NAME = "TestAdmin"

TEST_GROUP_ID = 9999
TEST_GROUP_NAME = "Test Group 9999"

MEMBERS = [
    {"user_id": 111, "username": "user_one", "first_name": "User One"},
    {"user_id": 222, "username": "user_two", "first_name": "User Two"},
]


async def main():
    print("Connecting to MongoDB using config:", config.MONGODB_URI, config.MONGODB_DB_NAME)
    client = AsyncIOMotorClient(config.MONGODB_URI)
    db = client[config.MONGODB_DB_NAME]
    svc = DatabaseService(db)

    ok = await svc.create_indexes()
    print("Created indexes (ok may be None if errors were logged)")

    print(f"Upserting superadmin {ADMIN_USERNAME} ({ADMIN_USER_ID})...")
    res = await svc.add_superadmin(ADMIN_USER_ID, ADMIN_USERNAME, ADMIN_FIRST_NAME)
    print("add_superadmin ->", res)

    print(f"Registering group {TEST_GROUP_NAME} ({TEST_GROUP_ID})...")
    res = await svc.register_group(TEST_GROUP_ID, TEST_GROUP_NAME)
    print("register_group ->", res)

    print(f"Adding {ADMIN_USERNAME} as group admin for group {TEST_GROUP_ID} (also superadmin entry exists)...")
    res = await svc.add_group_admin(TEST_GROUP_ID, ADMIN_USER_ID, ADMIN_USERNAME, ADMIN_FIRST_NAME)
    print("add_group_admin ->", res)

    for m in MEMBERS:
        print(f"Upserting member {m['username']} ({m['user_id']}) into group {TEST_GROUP_ID}...")
        res = await svc.upsert_member(
            group_id=TEST_GROUP_ID,
            user_id=m["user_id"],
            username=m.get("username"),
            first_name=m.get("first_name"),
            is_bot=False,
        )
        print("upsert_member ->", res)

    # done
    print("Seed complete. Summary: ")
    groups = await db["groups"].find({"group_id": TEST_GROUP_ID}).to_list(None)
    admins = await db["admins"].find({"user_id": ADMIN_USER_ID}).to_list(None)
    members = await db["members"].find({"group_id": TEST_GROUP_ID}).to_list(None)

    print("groups:")
    pprint(groups)
    print("admins:")
    pprint(admins)
    print("members:")
    pprint(members)

    client.close()


if __name__ == "__main__":
    asyncio.run(main())
