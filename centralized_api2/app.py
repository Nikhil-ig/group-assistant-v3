"""
Centralized API - FastAPI Application
Core business logic service for RBAC, permissions, and audit logging
All bot and web services communicate through this API
"""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Load environment variables from .env file
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(env_path, override=True)

from centralized_api.config import API_PREFIX
from centralized_api.db.mongodb import ActionDatabase
from centralized_api.api.routes import router as action_router
from centralized_api.api.simple_actions import router as simple_actions_router, set_executor
from centralized_api.api.advanced_rbac_routes import register_advanced_rbac_routes
from centralized_api.api.advanced_routes import router as advanced_router
from centralized_api.api.web_control import web_router, set_database as set_web_database
from centralized_api.api.dashboard_routes import router as dashboard_router, set_database as set_dashboard_database
from centralized_api.api.group_auto_register_routes import router as group_auto_register_router, set_db as set_auto_register_db
from centralized_api.api.professional_api import router as professional_api_router, set_db_manager
from centralized_api.core.database import init_db_manager, close_db_manager
from centralized_api.services.executor import ActionExecutor
from centralized_api.services.superadmin_service import SuperadminService
from centralized_api.services.group_admin_service import GroupAdminService
from centralized_api.config import MONGODB_URI, MONGODB_DATABASE
from motor.motor_asyncio import AsyncIOMotorClient

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global instances
_db: Optional[ActionDatabase] = None
_executor: Optional[ActionExecutor] = None
_superadmin_service: Optional[SuperadminService] = None
_group_admin_service: Optional[GroupAdminService] = None


async def init_services(app: FastAPI):
    """Initialize all services on startup"""
    global _db, _executor, _superadmin_service, _group_admin_service
    
    try:
        logger.info("🚀 Initializing Centralized API services...")
        
        # Initialize database (synchronous ActionDatabase wrapper)
        _db = ActionDatabase()
        await _db.connect()
        logger.info("✅ MongoDB connected")

        # Initialize an async Motor client and attach to app.state so
        # other modules (advanced routes) can reuse it via app.state.motor_db
        try:
            motor_client = AsyncIOMotorClient(MONGODB_URI)
            app.state.motor_client = motor_client
            app.state.motor_db = motor_client[MONGODB_DATABASE]
            logger.info("✅ Motor async MongoDB client initialized and attached to app.state")
        except Exception as e:
            logger.warning(f"Could not initialize motor client: {e}")
        
        # Initialize professional DatabaseManager (for v1 API)
        try:
            await init_db_manager(app.state.motor_db)
            logger.info("✅ Professional DatabaseManager initialized")
        except Exception as e:
            logger.warning(f"Could not initialize DatabaseManager: {e}")
        
        
        # Initialize services (bot is optional for centralized API)
        _executor = ActionExecutor(bot=None, db=_db)
        _superadmin_service = SuperadminService(db=_db)
        _group_admin_service = GroupAdminService(db=_db)
        
        # Initialize simple actions executor (for bot compatibility)
        set_executor(_executor)
        
        # Initialize web control database (for web API)
        set_web_database(_db)
        
        # Initialize dashboard database (for dashboard API)
        set_dashboard_database(app.state.motor_db)
        
        # Initialize auto-registration database (for group auto-registration)
        set_auto_register_db(app.state.motor_db)
        
        logger.info("✅ All services initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {e}")
        raise


async def close_services():
    """Close all services on shutdown"""
    global _db
    
    try:
        logger.info("🛑 Shutting down services...")
        
        if _db:
            await _db.disconnect()
            logger.info("✅ MongoDB disconnected")
        # Close motor client if present on app.state
        try:
            # app may not be available here; try to close any global motor client
            # attached earlier to the app.state
            # We check globals in case close_services is called without app context.
            from fastapi import current_app
            motor_client = getattr(current_app.state, "motor_client", None)
            if motor_client:
                motor_client.close()
                logger.info("✅ Motor client closed")
        except Exception:
            # If current_app isn't available, attempt to find motor client global
            pass
            
        logger.info("✅ All services closed successfully")
        
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    # Startup
    await init_services(app)
    yield
    # Shutdown
    await close_services()


# Create FastAPI app
app = FastAPI(
    title="Centralized API",
    description="Core API service for bot and web services",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# HEALTH CHECK ENDPOINT
# ============================================================================

@app.get("/api/health")
async def health_check():
    """Health check endpoint for Docker and orchestration"""
    try:
        if _db is None:
            return JSONResponse(
                status_code=503,
                content={"status": "unhealthy", "reason": "Database not initialized"}
            )
        
        # Check database connection using the _connected flag
        if not _db._connected:
            return JSONResponse(
                status_code=503,
                content={"status": "unhealthy", "reason": "Database connection failed"}
            )
        
        return {
            "status": "healthy",
            "service": "centralized_api",
            "version": "1.0.0",
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "reason": str(e)}
        )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Centralized API",
        "version": "1.0.0",
        "status": "running",
        "documentation": "/docs"
    }


# ============================================================================
# INCLUDE ROUTERS
# ============================================================================

# Dashboard routes (Port 8000/api/dashboard/...)
app.include_router(dashboard_router)

# Group auto-registration routes (Port 8000/api/groups/...)
app.include_router(group_auto_register_router)

# Action execution routes (Port 8000/api/actions/...)
app.include_router(action_router)

# Simple actions routes (Port 8000/api/actions/execute)
app.include_router(simple_actions_router)

# Web control routes (Port 8000/api/web/...)
app.include_router(web_router)

# RBAC routes (Port 8000/api/rbac/...)
register_advanced_rbac_routes(app)

# Advanced routes (Port 8000/api/advanced/...)
app.include_router(advanced_router)


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    logger.error(f"HTTP Exception: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )


# ============================================================================
# STARTUP/SHUTDOWN EVENTS (Alternative to lifespan)
# ============================================================================

@app.on_event("startup")
async def startup():
    """Called on startup (for compatibility)"""
    logger.info("FastAPI startup event")


@app.on_event("shutdown")
async def shutdown():
    """Called on shutdown (for compatibility)"""
    logger.info("FastAPI shutdown event")


if __name__ == "__main__":
    import uvicorn
    
    # Run with: python -m uvicorn app:app --reload
    # Or: python app.py
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
