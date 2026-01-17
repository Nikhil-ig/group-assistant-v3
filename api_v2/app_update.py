# This is the updated import section for app.py

from api_v2.core.database import init_db_manager, close_db_manager, get_db_manager
from api_v2.cache import init_cache_manager, close_cache_manager
from api_v2.routes.api_v2 import router as api_v2_router
from api_v2.routes.enforcement_endpoints import router as enforcement_router
from api_v2.routes.history import router as history_router
from api_v2.routes.analytics import router as analytics_router
from api_v2.routes.moderation_advanced import router as moderation_advanced_router
