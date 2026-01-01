"""
V3 Telegram Moderation Bot - Main Entry Point
Complete system with:
- Telegram bot with moderation commands
- REST API with role-based access control (RBAC)
- MongoDB for persistent storage and audit logs
- JWT authentication
- Superadmin (can control ALL groups) & Group Admin (can control ONLY their groups)
"""

import asyncio
import logging
import importlib
import importlib.util
from typing import Any
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from motor.motor_asyncio import AsyncIOMotorClient
import uvicorn
from contextlib import asynccontextmanager
import inspect
import os
from pathlib import Path

# Dynamically import telegram.ext.Application to avoid static analysis/linter errors
# in environments where python-telegram-bot is not installed.
_application_spec = importlib.util.find_spec("telegram.ext")
if _application_spec is not None:
    _telegram_ext = importlib.import_module("telegram.ext")
    Application = getattr(_telegram_ext, "Application", Any)
else:
    Application = Any

from .config.settings import config
from .services.database import DatabaseService
from .services.auth import AuthService
from .bot.handlers import register_handlers, BotCommandHandlers
from .api.endpoints import router as api_router

# ===== LOGGING SETUP =====


logging.basicConfig(
    level=config.LOG_LEVEL,
    format=config.LOG_FORMAT,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(config.LOG_FILE),
    ],
)
logger = logging.getLogger(__name__)


# ===== GLOBAL INSTANCES =====

db_client: Any = None
db_service: DatabaseService = None
auth_service: AuthService = None
telegram_app: Any = None
fastapi_app: FastAPI = None


# ===== INITIALIZATION FUNCTIONS =====

async def initialize_database():
    """Initialize MongoDB connection."""
    global db_client, db_service
    
    try:
        logger.info("📦 Connecting to MongoDB...")
        db_client = AsyncIOMotorClient(config.MONGODB_URI)
        db = db_client[config.MONGODB_DB_NAME]
        db_service = DatabaseService(db)
        
        # Test connection
        await db_service.health_check()
        
        # Create indexes
        await db_service.create_indexes()
        
        logger.info("✅ MongoDB connected successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to connect to MongoDB: {e}")
        return False


async def initialize_auth():
    """Initialize authentication service."""
    global auth_service
    
    try:
        logger.info("🔐 Initializing authentication service...")
        auth_service = AuthService(db_service, config.JWT_SECRET)
        logger.info("✅ Authentication service initialized")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize auth service: {e}")
        return False


async def initialize_telegram_bot():
    """Initialize Telegram bot application."""
    global telegram_app
    
    try:
        logger.info("🤖 Initializing Telegram bot...")
        telegram_app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
        # Debug: report what kind of Application we got and key attributes
        try:
            app_type = type(telegram_app)
            logger.info(f"Telegram Application instance: {app_type}")
            # Log presence of common attributes without dumping everything
            attrs = []
            for a in ("updater", "run_polling", "initialize", "start", "stop"):
                attrs.append((a, hasattr(telegram_app, a)))
            logger.debug(f"Telegram Application attrs: {attrs}")
        except Exception:
            logger.debug("Could not introspect telegram application instance")
        
        # Register command handlers
        register_handlers(telegram_app, db_service)
        
        logger.info("✅ Telegram bot initialized")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize Telegram bot: {e}")
        return False


def initialize_fastapi():
    """Initialize FastAPI application."""
    global fastapi_app
    
    try:
        logger.info("🌐 Initializing FastAPI...")
        
        # Store polling task reference
        polling_task = None
        
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            """Manage app lifecycle."""
            nonlocal polling_task
            logger.info("🚀 Starting application...")
            
            # Initialize all services on startup
            await initialize_database()
            await initialize_auth()

            # Optionally skip Telegram initialization when running API-only smoke tests
            if os.getenv("SKIP_TELEGRAM", "false").lower() != "true":
                await initialize_telegram_bot()
            else:
                logger.info("⏭️ SKIP_TELEGRAM is set — skipping Telegram initialization (API-only mode)")
            
            # Attach initialized services to app.state so API deps can access them
            try:
                app.state.db_service = db_service
                app.state.auth_service = auth_service
                app.state.telegram_app = telegram_app
            except Exception:
                logger.debug("Could not attach services to app.state")

            # Initialize the telegram app updater (required before polling)
            if telegram_app is not None:
                await telegram_app.initialize()
                await telegram_app.start()  # START THE APPLICATION TO ACTIVATE HANDLERS
                # Some Application builds may not have `updater`
                if hasattr(telegram_app, "updater") and telegram_app.updater is not None:
                    await telegram_app.updater.initialize()
            else:
                logger.info("No telegram_app instance attached; skipping updater initialization")
            
            # Start bot polling as a background task (only if telegram_app was initialized)
            if telegram_app is not None:
                polling_task = asyncio.create_task(run_telegram_bot())
            else:
                polling_task = None
            
            logger.info("✅ Application started successfully")
            yield
            
            # Cleanup on shutdown
            logger.info("🛑 Shutting down...")
            
            # Cancel the polling task
            if polling_task and not polling_task.done():
                polling_task.cancel()
                try:
                    await polling_task
                except asyncio.CancelledError:
                    pass
            
            try:
                await telegram_app.updater.shutdown()
                await telegram_app.stop()
                await telegram_app.shutdown()
            except Exception as e:
                logger.debug(f"Telegram app cleanup: {e}")
            if db_client:
                db_client.close()
            logger.info("✅ Shutdown complete")
        
        fastapi_app = FastAPI(
            title="V3 Telegram Moderation Bot",
            description="Complete moderation system with RBAC",
            version="3.0.0",
            lifespan=lifespan,
        )

        # CORS: use configured origins if provided, otherwise allow all in DEBUG
        if getattr(config, "API_CORS_ORIGINS", ""):
            origins = [o.strip() for o in config.API_CORS_ORIGINS.split(",") if o.strip()]
        else:
            origins = ["*"] if config.DEBUG else []
        # Log configured CORS origins for visibility / tightening guidance
        logger.info(f"CORS origins configured: {origins}")
        fastapi_app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Include API routes
        fastapi_app.include_router(api_router)
        # Serve built frontend (if present)
        try:
            frontend_dist = Path(__file__).resolve().parent / "frontend" / "dist"
            if frontend_dist.exists():
                # Mount frontend under /dashboard so API routes remain at root
                fastapi_app.mount("/dashboard", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
                logger.info(f"✓ Mounted frontend static from: {frontend_dist} at /dashboard")

                # SPA fallback: serve index.html for any deep link under /dashboard
                try:
                    index_path = frontend_dist / "index.html"

                    @fastapi_app.get("/dashboard{full_path:path}", include_in_schema=False)
                    async def dashboard_spa(full_path: str):
                        return FileResponse(str(index_path))

                    logger.info("✓ SPA fallback route registered for /dashboard/*")
                except Exception as e:
                    logger.debug(f"Could not register SPA fallback route: {e}")
        except Exception as e:
            logger.debug(f"Could not mount frontend static files: {e}")
        
        logger.info("✅ FastAPI initialized")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize FastAPI: {e}")
        return False


async def run_telegram_bot():
    """
    Run Telegram bot polling to fetch and process updates.
    This runs concurrently with the FastAPI server.
    
    The bot application was already initialized in the FastAPI lifespan.
    This function starts and manages the polling mechanism.
    """
    try:
        logger.info("🤖 Starting Telegram bot polling...")
        # Start the updater which handles polling
        # It fetches updates from Telegram and dispatches to handlers
        # Be robust to different python-telegram-bot versions/APIs
        if hasattr(telegram_app, "updater") and hasattr(telegram_app.updater, "start_polling"):
            logger.info("Using updater.start_polling() for polling")
            await telegram_app.updater.start_polling(allowed_updates=None)
            logger.info("✅ Telegram bot is now polling for updates (updater)")
        elif hasattr(telegram_app, "run_polling"):
            logger.info("Using Application.run_polling() fallback for polling")
            try:
                # run_polling may be coroutine or blocking function depending on PTB version
                if inspect.iscoroutinefunction(telegram_app.run_polling):
                    await telegram_app.run_polling()
                else:
                    # Run the blocking run_polling in executor so we don't block event loop
                    loop = asyncio.get_running_loop()
                    await loop.run_in_executor(None, telegram_app.run_polling)
                logger.info("✅ Telegram bot is now polling for updates (run_polling)")
            except Exception as e:
                logger.error(f"Failed to start polling via run_polling: {e}", exc_info=True)
                raise
        else:
            logger.error("No polling method found on telegram_app (neither updater.start_polling nor run_polling)")
            raise RuntimeError("No polling method available on telegram application")
        
        # Keep the polling running indefinitely
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        logger.info("🤖 Telegram bot polling task was cancelled")
        raise
    except Exception as e:
        logger.error(f"❌ Telegram bot polling error: {e}", exc_info=True)
        raise
    finally:
        try:
            if hasattr(telegram_app, "updater") and hasattr(telegram_app.updater, "stop"):
                await telegram_app.updater.stop()
            elif hasattr(telegram_app, "stop"):
                # Some Application implementations expose stop()
                if inspect.iscoroutinefunction(telegram_app.stop):
                    await telegram_app.stop()
                else:
                    loop = asyncio.get_running_loop()
                    await loop.run_in_executor(None, telegram_app.stop)
        except Exception:
            pass


async def run_api_server():
    """Run FastAPI server."""
    try:
        logger.info(f"🌐 Starting API server on {config.API_HOST}:{config.API_PORT}...")
        
        config_dict = uvicorn.Config(
            fastapi_app,
            host=config.API_HOST,
            port=config.API_PORT,
            workers=1 if config.DEBUG else config.API_WORKERS,
            reload=config.DEBUG,
        )
        server = uvicorn.Server(config_dict)
        await server.serve()
    except Exception as e:
        logger.error(f"❌ API server error: {e}")


async def main():
    """Main async entry point."""
    try:
        logger.info("=" * 60)
        logger.info("  V3 TELEGRAM MODERATION BOT - STARTING")
        logger.info(f"  Environment: {config.ENV}")
        logger.info(f"  Debug: {config.DEBUG}")
        logger.info("=" * 60)
        
        # Initialize FastAPI
        initialize_fastapi()
        
        # Initialize services
        # Note: FastAPI lifespan will handle these initializations, so we skip them here
        # to avoid double-initialization
        logger.info("✅ Services will be initialized in FastAPI lifespan context")
        
        logger.info("\n" + "=" * 60)
        logger.info("  ✅ ALL SYSTEMS INITIALIZED")
        logger.info("=" * 60)
        logger.info("\n📋 Available Commands:")
        logger.info("  /ban <user_id> [reason] - Ban user")
        logger.info("  /unban <user_id> - Unban user")
        logger.info("  /kick <user_id> [reason] - Kick user")
        logger.info("  /warn <user_id> [reason] - Warn user")
        logger.info("  /mute <user_id> [hours] [reason] - Mute user")
        logger.info("  /logs [limit] - Show audit logs")
        logger.info("  /stats - Show group statistics")
        logger.info("\n🌐 API Endpoints:")
        logger.info(f"  POST   {config.API_PREFIX}/auth/login")
        logger.info(f"  GET    {config.API_PREFIX}/groups")
        logger.info(f"  POST   {config.API_PREFIX}/groups/{{group_id}}/actions")
        logger.info(f"  GET    {config.API_PREFIX}/groups/{{group_id}}/logs")
        logger.info(f"  GET    {config.API_PREFIX}/health")
        logger.info("\n🔐 RBAC (Role-Based Access Control):")
        logger.info("  SUPERADMIN: Can see and control ALL groups")
        logger.info("  GROUP_ADMIN: Can see and control ONLY their groups")
        logger.info("  USER: Can view audit logs only")
        logger.info("\n" + "=" * 60 + "\n")
        
        # Run the API server (bot is managed by FastAPI lifespan)
        # Note: run_telegram_bot() is called inside FastAPI lifespan context
        await run_api_server()
    
    except KeyboardInterrupt:
        logger.info("\n⌨️  Keyboard interrupt received")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
    finally:
        # Cleanup
        if db_client:
            db_client.close()
        logger.info("👋 Bot stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n⌨️  Application stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
