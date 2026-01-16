"""
Business Logic Services - Groups, Users, Roles, Rules, Settings management
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

from api_v2.core.database import get_db_manager
from api_v2.cache import get_cache_manager
from api_v2.models.schemas import *

logger = logging.getLogger(__name__)


class GroupService:
    """Group management service"""
    
    def __init__(self):
        self.db = None
        self.cache = None
    
    def _ensure_initialized(self):
        """Lazily initialize db and cache on first use"""
        if self.db is None:
            try:
                self.db = get_db_manager()
            except RuntimeError:
                logger.debug("Database manager not yet initialized")
        if self.cache is None:
            try:
                self.cache = get_cache_manager()
            except Exception:
                logger.debug("Cache manager not yet initialized")
    
    async def create_group(self, group_data: GroupCreate) -> GroupResponse:
        """Create new group"""
        self._ensure_initialized()
        logger.info(f"Creating group {group_data.group_id}: {group_data.name}")
        
        group_id = await self.db.create_group(group_data.dict())
        
        # Cache it
        if self.cache:
            await self.cache.cache_group(group_data.group_id, group_data.dict())
        
        return GroupResponse(**group_data.dict(), id=group_id)
    
    async def get_group(self, group_id: int) -> Optional[GroupResponse]:
        """Get group by ID"""
        self._ensure_initialized()
        # Try cache first
        if self.cache:
            cached = await self.cache.get_cached_group(group_id)
            if cached:
                return GroupResponse(**cached)
        
        # Get from DB
        group = await self.db.get_group(group_id)
        if group:
            if self.cache:
                await self.cache.cache_group(group_id, group)
            return GroupResponse(**group)
        return None
    
    async def update_group(self, group_id: int, updates: GroupUpdate):
        """Update group"""
        self._ensure_initialized()
        logger.info(f"Updating group {group_id}")
        
        await self.db.update_group(group_id, updates.dict(exclude_none=True))
        
        # Invalidate cache
        if self.cache:
            await self.cache.invalidate_group(group_id)
    
    async def get_group_statistics(self, group_id: int) -> GroupStatistics:
        """Get comprehensive group statistics"""
        self._ensure_initialized()
        logger.info(f"Getting statistics for group {group_id}")
        
        stats = await self.db.get_group_statistics(group_id)
        
        return GroupStatistics(
            group_id=group_id,
            total_members=0,  # Can be fetched from Telegram API
            total_actions=stats.get("total_actions", [{}])[0].get("count", 0),
            actions_by_type={s["_id"]: s["count"] for s in stats.get("by_type", [])},
            top_users=stats.get("by_user", []),
            recent_actions=stats.get("recent", [])
        )


class RoleService:
    """Role management service"""
    
    def __init__(self):
        self.db = None
        self.cache = None
    
    def _ensure_initialized(self):
        """Lazily initialize db and cache on first use"""
        if self.db is None:
            try:
                self.db = get_db_manager()
            except RuntimeError:
                logger.debug("Database manager not yet initialized")
        if self.cache is None:
            try:
                self.cache = get_cache_manager()
            except Exception:
                logger.debug("Cache manager not yet initialized")
    
    async def create_role(self, role_data: RoleCreate) -> RoleResponse:
        """Create role in group"""
        self._ensure_initialized()
        logger.info(f"Creating role {role_data.name} in group {role_data.group_id}")
        
        role_id = await self.db.create_role(role_data.group_id, role_data.dict(exclude={"group_id"}))
        
        return RoleResponse(**role_data.dict(), id=role_id)
    
    async def get_role(self, group_id: int, role_name: str) -> Optional[RoleResponse]:
        """Get role"""
        self._ensure_initialized()
        # Try cache
        if self.cache:
            cached_key = self.cache.role_key(group_id, role_name)
            cached = await self.cache.get(cached_key)
            if cached:
                return RoleResponse(**cached)
        
        role = await self.db.get_role(group_id, role_name)
        if role and self.cache:
            await self.cache.set(self.cache.role_key(group_id, role_name), role, ttl=3600)
        
        return RoleResponse(**role) if role else None
    
    async def get_group_roles(self, group_id: int) -> List[RoleResponse]:
        """Get all roles in group"""
        self._ensure_initialized()
        roles = await self.db.get_group_roles(group_id)
        return [RoleResponse(**role) for role in roles]


class RuleService:
    """Rule management service"""
    
    def __init__(self):
        self.db = None
    
    def _ensure_initialized(self):
        """Lazily initialize db on first use"""
        if self.db is None:
            try:
                self.db = get_db_manager()
            except RuntimeError:
                logger.debug("Database manager not yet initialized")
    
    async def create_rule(self, rule_data: RuleCreate) -> RuleResponse:
        """Create rule"""
        self._ensure_initialized()
        logger.info(f"Creating rule {rule_data.rule_name} in group {rule_data.group_id}")
        
        rule_id = await self.db.create_rule(rule_data.group_id, rule_data.dict(exclude={"group_id"}))
        
        return RuleResponse(**rule_data.dict(), id=rule_id)
    
    async def get_group_rules(self, group_id: int, active_only: bool = True) -> List[RuleResponse]:
        """Get all rules in group"""
        self._ensure_initialized()
        rules = await self.db.get_group_rules(group_id, active_only)
        return [RuleResponse(**rule) for rule in rules]


class SettingsService:
    """Settings management service"""
    
    def __init__(self):
        self.db = None
        self.cache = None
    
    def _ensure_initialized(self):
        """Lazily initialize db and cache on first use"""
        if self.db is None:
            try:
                self.db = get_db_manager()
            except RuntimeError:
                logger.debug("Database manager not yet initialized")
        if self.cache is None:
            try:
                self.cache = get_cache_manager()
            except Exception:
                logger.debug("Cache manager not yet initialized")
    
    async def get_group_settings(self, group_id: int) -> SettingsResponse:
        """Get group settings"""
        self._ensure_initialized()
        # Try cache
        if self.cache:
            cached = await self.cache.get_cached_settings(group_id)
            if cached:
                return SettingsResponse(**cached)
        
        settings = await self.db.get_group_settings(group_id)
        
        if self.cache:
            await self.cache.cache_settings(group_id, settings or {})
        
        return SettingsResponse(
            group_id=group_id,
            **settings or {},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    async def update_settings(self, group_id: int, updates: SettingsUpdate):
        """Update group settings"""
        self._ensure_initialized()
        logger.info(f"Updating settings for group {group_id}")
        
        await self.db.update_group_settings(group_id, updates.dict(exclude_none=True))
        
        # Invalidate cache
        if self.cache:
            await self.cache.invalidate_settings(group_id)


class ActionService:
    """Action logging and retrieval service"""
    
    def __init__(self):
        self.db = None
    
    def _ensure_initialized(self):
        """Lazily initialize db on first use"""
        if self.db is None:
            try:
                self.db = get_db_manager()
            except RuntimeError:
                logger.debug("Database manager not yet initialized")
    
    async def log_action(self, action_data: ActionCreate) -> ActionResponse:
        """Log an action"""
        self._ensure_initialized()
        logger.info(
            f"Logging action: {action_data.action_type} on user {action_data.user_id} "
            f"in group {action_data.group_id}"
        )
        
        action_id = await self.db.log_action(action_data.dict())
        
        return ActionResponse(**action_data.dict(), id=action_id)
    
    async def get_group_actions(self, group_id: int, page: int = 1, 
                               per_page: int = 50) -> PaginatedResponse:
        """Get actions for group"""
        self._ensure_initialized()
        result = await self.db.get_group_actions(group_id, page, per_page)
        
        return PaginatedResponse(**result)
    
    async def get_user_statistics(self, group_id: int, user_id: int) -> UserStatistics:
        """Get user statistics"""
        self._ensure_initialized()
        stats = await self.db.get_user_statistics(group_id, user_id)
        
        return UserStatistics(**stats)
