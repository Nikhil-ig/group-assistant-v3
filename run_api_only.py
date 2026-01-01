"""Run only the FastAPI app (no Telegram poller) for local API testing.

This script creates a FastAPI instance, attaches a real DatabaseService and AuthService
from configuration, mounts the existing `api.endpoints` router, and runs uvicorn.

Use this for smoke tests without starting the Telegram poller.
"""
import sys
import asyncio
import logging
import os
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
import uvicorn
from fastapi import FastAPI

# Ensure project root is on sys.path so imports like `v3.services` work when
# this module is executed from inside the `v3/` folder (e.g. `python -m run_api_only`).
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.settings import config
from services.database import DatabaseService
from services.auth import AuthService
from api.endpoints import router as api_router

logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)


def build_app() -> FastAPI:
    app = FastAPI(title="V3 API (smoke)")

    # Create DB client and attach a DatabaseService to app.state
    client = AsyncIOMotorClient(config.MONGODB_URI)
    db = client[config.MONGODB_DB_NAME]
    db_service = DatabaseService(db)

    # Attach services
    app.state.db_service = db_service
    app.state.auth_service = AuthService(db_service, config.JWT_SECRET)

    # Include API router
    app.include_router(api_router)
    return app


if __name__ == "__main__":
    app = build_app()
    host = os.getenv("API_HOST", config.API_HOST)
    port = int(os.getenv("API_PORT", config.API_PORT))
    logger.info(f"Starting API-only server on {host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")
