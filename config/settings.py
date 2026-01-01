"""
V3 Configuration Settings with Environment Management and Validation

Supports development and production environments with full validation.
Easy to customize and understand.
"""

import os
from pathlib import Path
from enum import Enum
from typing import Optional
from datetime import datetime
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load .env file from the v3 directory (same directory as this file)
ENV_FILE = Path(__file__).parent.parent / ".env"
load_dotenv(str(ENV_FILE))


class EnvironmentType(Enum):
    """Environment types."""
    DEVELOPMENT = "development"
    PRODUCTION = "production"


class Config:
    """Base configuration class with all options."""
    
    # ===== Environment =====
    ENV: str = os.getenv("ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # ===== Telegram Bot =====
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_BOT_USERNAME: str = os.getenv("TELEGRAM_BOT_USERNAME", "")
    
    # ===== MongoDB =====
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "telegram_bot_v3")
    MONGODB_GROUPS_COLLECTION: str = "groups"
    MONGODB_ADMINS_COLLECTION: str = "admins"
    MONGODB_AUDIT_LOGS_COLLECTION: str = "audit_logs"
    MONGODB_METRICS_COLLECTION: str = "metrics"
    MONGODB_USERS_COLLECTION: str = "users"
    
    # ===== Redis (Optional) =====
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    USE_REDIS: bool = os.getenv("USE_REDIS", "false").lower() == "true"
    
    # ===== API Server =====
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_WORKERS: int = int(os.getenv("API_WORKERS", "4"))
    API_PREFIX: str = "/api/v1"
    # Comma-separated list of allowed CORS origins. If empty and DEBUG=True, allow all.
    API_CORS_ORIGINS: str = os.getenv("API_CORS_ORIGINS", "")
    
    # ===== JWT & Security =====
    JWT_SECRET: str = os.getenv("JWT_SECRET", "change-this-in-production")
    JWT_EXPIRATION_HOURS: int = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
    
    # ===== Role-Based Access Control (RBAC) =====
    SUPERADMIN_ID: Optional[int] = None
    SUPERADMIN_USERNAME: str = os.getenv("SUPERADMIN_USERNAME", "")
    
    # Load SUPERADMIN_ID from environment
    _superadmin_id = os.getenv("SUPERADMIN_ID")
    if _superadmin_id:
        try:
            SUPERADMIN_ID = int(_superadmin_id)
        except ValueError:
            logger.warning(f"Invalid SUPERADMIN_ID: {_superadmin_id}")
    
    # ===== Logging =====
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "DEBUG")
    LOG_DIR: str = os.getenv("LOG_DIR", "logs")
    LOG_FILE: str = os.path.join(LOG_DIR, "bot.log")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Create logs directory if it doesn't exist
    os.makedirs(LOG_DIR, exist_ok=True)
    
    # ===== Feature Flags =====
    ENABLE_AUDIT_LOGGING: bool = os.getenv("ENABLE_AUDIT_LOGGING", "true").lower() == "true"
    ENABLE_METRICS: bool = os.getenv("ENABLE_METRICS", "true").lower() == "true"
    ENABLE_WEB_DASHBOARD: bool = os.getenv("ENABLE_WEB_DASHBOARD", "true").lower() == "true"
    ENABLE_API: bool = os.getenv("ENABLE_API", "true").lower() == "true"
    
    # ===== Bot Features =====
    ENABLE_BAN: bool = os.getenv("ENABLE_BAN", "true").lower() == "true"
    ENABLE_UNBAN: bool = os.getenv("ENABLE_UNBAN", "true").lower() == "true"
    ENABLE_MUTE: bool = os.getenv("ENABLE_MUTE", "true").lower() == "true"
    ENABLE_UNMUTE: bool = os.getenv("ENABLE_UNMUTE", "true").lower() == "true"
    ENABLE_KICK: bool = os.getenv("ENABLE_KICK", "true").lower() == "true"
    ENABLE_WARN: bool = os.getenv("ENABLE_WARN", "true").lower() == "true"
    
    def validate(self) -> bool:
        """Validate configuration. Override in subclasses."""
        if not self.TELEGRAM_BOT_TOKEN:
            logger.warning("TELEGRAM_BOT_TOKEN not set")
        if not self.MONGODB_URI:
            logger.warning("MONGODB_URI not set")
        return True


class DevelopmentConfig(Config):
    """Development configuration with lenient validation."""
    
    DEBUG = True
    ENV = "development"
    
    def validate(self) -> bool:
        """Development validation (lenient)."""
        logger.info("✓ Development configuration loaded")
        return True


class ProductionConfig(Config):
    """Production configuration with strict validation."""
    
    DEBUG = False
    ENV = "production"
    
    def validate(self) -> bool:
        """Production validation (strict)."""
        errors = []
        
        if not self.TELEGRAM_BOT_TOKEN or self.TELEGRAM_BOT_TOKEN == "":
            errors.append("TELEGRAM_BOT_TOKEN is required in production")
        
        if not self.MONGODB_URI or self.MONGODB_URI == "mongodb://localhost:27017":
            errors.append("MONGODB_URI must be configured for production (not localhost)")
        
        if not self.JWT_SECRET or self.JWT_SECRET == "change-this-in-production":
            errors.append("JWT_SECRET must be changed from default in production")
        
        if self.SUPERADMIN_ID is None:
            errors.append("SUPERADMIN_ID must be set in production")
        
        if errors:
            for error in errors:
                logger.error(f"❌ {error}")
            return False
        
        logger.info("✓ Production configuration validated")
        return True


def get_config() -> Config:
    """Get configuration instance based on environment."""
    env = os.getenv("ENV", "development").lower()
    
    if env == "production":
        return ProductionConfig()
    else:
        return DevelopmentConfig()


# Create global config instance
config = get_config()

# Validate configuration
if not config.validate():
    logger.warning("Configuration validation had warnings/errors")
