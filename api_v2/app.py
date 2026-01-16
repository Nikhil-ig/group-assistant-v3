"""
API V2 Main Application
Professional & Scalable Data Management System
"""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(env_path, override=True)

from api_v2.core.database import init_db_manager, close_db_manager, get_db_manager
from api_v2.cache import init_cache_manager, close_cache_manager
from api_v2.routes.api_v2 import router as api_v2_router
from api_v2.routes.enforcement_endpoints import router as enforcement_router
from api_v2.routes.history import router as history_router
# Advanced features disabled for now - have circular dependencies
# from api_v2.routes.advanced_features import router as advanced_features_router, set_engines
# from api_v2.routes.enforcement import router as enforcement_router, set_enforcement_engine
# from api_v2.features import AnalyticsEngine, AutomationEngine, ModerationEngine, EnforcementEngine
# from api_v2.telegram import TelegramAPIWrapper

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "bot_manager")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for startup and shutdown"""
    # Startup
    logger.info("🚀 Starting API V2...")
    
    try:
        # Initialize MongoDB (with short timeout to avoid blocking)
        motor_client = AsyncIOMotorClient(MONGODB_URI, serverSelectionTimeoutMS=2000)
        app.state.motor_client = motor_client
        app.state.motor_db = None
        
        try:
            # Test connection briefly
            await motor_client.admin.command('ping')
            app.state.motor_db = motor_client[MONGODB_DB]
            logger.info("✅ MongoDB connected")
            # Initialize DB manager in background to avoid blocking
            try:
                await init_db_manager(app.state.motor_db)
                logger.info("✅ Database indexes created")
            except Exception as e:
                logger.warning(f"⚠️ Could not initialize indexes: {e}")
        except Exception as e:
            logger.warning(f"⚠️ MongoDB not available: {e}. API will work in read-only mode.")
        
        # Initialize Redis cache (non-blocking)
        try:
            await init_cache_manager(REDIS_URL)
            logger.info("✅ Redis connected")
        except Exception as e:
            logger.warning(f"⚠️ Redis not available: {e}. Using in-memory cache only.")
        
        logger.info("✅ API V2 started successfully on port 8002")
    except Exception as e:
        logger.warning(f"⚠️ Startup warning: {e}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down API V2...")
    try:
        await close_db_manager()
        await close_cache_manager()
        if hasattr(app.state, "motor_client"):
            app.state.motor_client.close()
        logger.info("✅ API V2 shut down successfully")
    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")


# Create FastAPI app
app = FastAPI(
    title="API V2 - Professional Data Management",
    description="Enterprise-grade multi-group management system",
    version="2.0.0",
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
# HEALTH ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "API V2",
        "version": "2.0.0",
        "status": "running",
        "documentation": "/docs"
    }


@app.get("/health")
async def health_check():
    """Global health check"""
    return {
        "status": "healthy",
        "service": "api-v2",
        "version": "2.0.0"
    }


# ============================================================================
# INCLUDE ROUTERS
# ============================================================================

app.include_router(api_v2_router)
app.include_router(enforcement_router)
app.include_router(history_router)
# Advanced features disabled for now - have circular dependencies
# app.include_router(advanced_features_router)
# app.include_router(enforcement_router)
app.include_router(history_router)


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "details": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8002)),
        reload=True,
        log_level="info"
    )
