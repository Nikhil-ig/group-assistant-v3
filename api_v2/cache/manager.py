"""
Advanced Caching System - Redis and In-Memory cache for performance
"""

import json
import logging
from typing import Optional, Any, Dict
from datetime import timedelta
import redis.asyncio as aioredis
from functools import lru_cache

logger = logging.getLogger(__name__)

# Global cache manager
_cache_manager: Optional["CacheManager"] = None


class CacheManager:
    """
    High-performance caching with:
    - Redis for distributed cache
    - In-memory cache for fast access
    - Automatic invalidation
    - TTL support
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis: Optional[aioredis.Redis] = None
        self.in_memory_cache: Dict[str, Any] = {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis = await aioredis.from_url(
                self.redis_url,
                encoding="utf8",
                decode_responses=True
            )
            self.logger.info("✅ Redis connected")
        except Exception as e:
            self.logger.warning(f"Redis connection failed: {e}. Using in-memory only.")
            self.redis = None
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis:
            await self.redis.close()
            self.logger.info("✅ Redis disconnected")
    
    # ========================================================================
    # GET/SET OPERATIONS
    # ========================================================================
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        # Try Redis first
        if self.redis:
            try:
                value = await self.redis.get(key)
                if value:
                    return json.loads(value)
            except Exception as e:
                self.logger.warning(f"Redis get error: {e}")
        
        # Fallback to in-memory
        return self.in_memory_cache.get(key)
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache"""
        json_value = json.dumps(value, default=str)
        
        # Set in Redis if available
        if self.redis and ttl:
            try:
                await self.redis.setex(key, ttl, json_value)
            except Exception as e:
                self.logger.warning(f"Redis set error: {e}")
        elif self.redis:
            try:
                await self.redis.set(key, json_value)
            except Exception as e:
                self.logger.warning(f"Redis set error: {e}")
        
        # Also set in memory
        self.in_memory_cache[key] = value
    
    async def delete(self, key: str):
        """Delete from cache"""
        if self.redis:
            try:
                await self.redis.delete(key)
            except Exception as e:
                self.logger.warning(f"Redis delete error: {e}")
        
        self.in_memory_cache.pop(key, None)
    
    async def clear_pattern(self, pattern: str):
        """Clear all keys matching pattern"""
        if self.redis:
            try:
                keys = await self.redis.keys(pattern)
                if keys:
                    await self.redis.delete(*keys)
            except Exception as e:
                self.logger.warning(f"Redis clear pattern error: {e}")
        
        # Clear from memory too
        to_delete = [k for k in self.in_memory_cache.keys() if pattern.replace("*", "") in k]
        for k in to_delete:
            del self.in_memory_cache[k]
    
    # ========================================================================
    # CACHE KEYS
    # ========================================================================
    
    @staticmethod
    def make_key(*parts: str) -> str:
        """Create cache key from parts"""
        return ":".join(str(p) for p in parts)
    
    def group_key(self, group_id: int, suffix: str = "") -> str:
        """Create group cache key"""
        return self.make_key("group", str(group_id), suffix)
    
    def user_key(self, group_id: int, user_id: int, suffix: str = "") -> str:
        """Create user cache key"""
        return self.make_key("user", str(group_id), str(user_id), suffix)
    
    def role_key(self, group_id: int, role_name: str) -> str:
        """Create role cache key"""
        return self.make_key("role", str(group_id), role_name)
    
    def settings_key(self, group_id: int) -> str:
        """Create settings cache key"""
        return self.make_key("settings", str(group_id))
    
    # ========================================================================
    # GROUP CACHE
    # ========================================================================
    
    async def cache_group(self, group_id: int, group_data: Dict[str, Any]):
        """Cache group data"""
        await self.set(self.group_key(group_id), group_data, ttl=3600)  # 1 hour
    
    async def get_cached_group(self, group_id: int) -> Optional[Dict[str, Any]]:
        """Get cached group"""
        return await self.get(self.group_key(group_id))
    
    async def invalidate_group(self, group_id: int):
        """Invalidate group cache"""
        await self.clear_pattern(f"group:{group_id}:*")
    
    # ========================================================================
    # USER CACHE
    # ========================================================================
    
    async def cache_user(self, group_id: int, user_id: int, user_data: Dict[str, Any]):
        """Cache user data"""
        await self.set(self.user_key(group_id, user_id), user_data, ttl=1800)  # 30 min
    
    async def get_cached_user(self, group_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """Get cached user"""
        return await self.get(self.user_key(group_id, user_id))
    
    async def invalidate_group_users(self, group_id: int):
        """Invalidate all users in group"""
        await self.clear_pattern(f"user:{group_id}:*")
    
    # ========================================================================
    # SETTINGS CACHE
    # ========================================================================
    
    async def cache_settings(self, group_id: int, settings: Dict[str, Any]):
        """Cache group settings"""
        await self.set(self.settings_key(group_id), settings, ttl=3600)  # 1 hour
    
    async def get_cached_settings(self, group_id: int) -> Optional[Dict[str, Any]]:
        """Get cached settings"""
        return await self.get(self.settings_key(group_id))
    
    async def invalidate_settings(self, group_id: int):
        """Invalidate settings cache"""
        await self.delete(self.settings_key(group_id))


async def init_cache_manager(redis_url: str = "redis://localhost:6379") -> CacheManager:
    """Initialize the global cache manager"""
    global _cache_manager
    _cache_manager = CacheManager(redis_url)
    await _cache_manager.connect()
    return _cache_manager


def get_cache_manager() -> Optional[CacheManager]:
    """Get the global cache manager"""
    return _cache_manager


async def close_cache_manager():
    """Close the cache manager"""
    global _cache_manager
    if _cache_manager:
        await _cache_manager.disconnect()
    _cache_manager = None
