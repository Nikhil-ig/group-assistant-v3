import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import config
from services.database import DatabaseService

logger = logging.getLogger("db_init")
logging.basicConfig(level=logging.INFO)

async def main():
    uri = config.MONGODB_URI
    dbname = config.MONGODB_DB_NAME
    logger.info(f"Connecting to MongoDB {uri}, db={dbname}")

    client = AsyncIOMotorClient(uri)
    db = client[dbname]
    svc = DatabaseService(db)

    ok = await svc.health_check()
    if not ok:
        logger.error("MongoDB health check failed; aborting index creation")
        return

    await svc.create_indexes()

    # seed superadmin if provided
    if config.SUPERADMIN_ID:
        logger.info(f"Seeding SUPERADMIN {config.SUPERADMIN_ID}")
        await svc.add_superadmin(config.SUPERADMIN_ID, config.SUPERADMIN_USERNAME or "", "")

    logger.info("DB initialization complete")

if __name__ == '__main__':
    asyncio.run(main())
