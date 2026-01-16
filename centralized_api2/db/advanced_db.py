"""
Advanced MongoDB Database Service
Handles all CRUD operations for settings, members, admins, roles, history, and events
"""

from __future__ import annotations

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from bson import ObjectId

logger = logging.getLogger(__name__)


class AdvancedDBService:
    """Advanced MongoDB service for bot data persistence"""
    
    def __init__(self, db: Any):
        self.db = db
        self.settings_collection = db["group_settings"]
        self.members_collection = db["members"]
        self.admins_collection = db["admins"]
        self.roles_collection = db["moderation_roles"]
        self.command_history_collection = db["command_history"]
        self.event_logs_collection = db["event_logs"]
        self.statistics_collection = db["group_statistics"]
    
    # ========================================================================
    # GROUP SETTINGS
    # ========================================================================
    
    async def get_group_settings(self, group_id: int) -> Optional[Dict[str, Any]]:
        """Get settings for a group"""
        return await self.settings_collection.find_one({"group_id": group_id})
    
    async def create_group_settings(self, group_id: int, group_name: str) -> Dict[str, Any]:
        """Create default settings for a group"""
        settings = {
            "group_id": group_id,
            "group_name": group_name,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "features_enabled": {
                "welcome_message": True,
                "left_message": True,
                "pin_message": True,
                "moderation": True,
                "auto_mute": False,
                "auto_ban": False,
                "warnings": True,
                "role_assignment": True,
                "member_tracking": True,
                "command_logging": True,
                "event_logging": True,
            },
            "welcome_message": "👋 Welcome to {group_name}! Please read the rules.",
            "left_message": "👋 {username} left the group.",
            "max_warnings": 3,
            "auto_mute_after_warns": 3,
            "mute_duration": 60,
            "auto_ban_after_mutes": 3,
            "admin_notifications": True,
            "admin_chat_id": None,
            "auto_delete_commands": False,
            "keep_message_history": True,
        }
        result = await self.settings_collection.insert_one(settings)
        settings["_id"] = result.inserted_id
        return settings
    
    async def update_group_settings(self, group_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update group settings"""
        # If caller updated a top-level alias that maps to a feature flag,
        # reflect that change into the nested `features_enabled` map so both
        # places remain consistent.
        updates_to_set = dict(updates)
        # Build reverse mapping top_key -> feature
        reverse_map = {v: k for k, v in self._FEATURE_TO_TOPLEVEL.items()}

        for top_key, value in list(updates.items()):
            if top_key in reverse_map:
                feature = reverse_map[top_key]
                updates_to_set[f"features_enabled.{feature}"] = bool(value)

        updates_to_set["updated_at"] = datetime.utcnow()

        result = await self.settings_collection.find_one_and_update(
            {"group_id": group_id},
            {"$set": updates_to_set},
            return_document=True
        )

        return result
    
    # Mapping of feature keys to potential top-level aliases in settings
    _FEATURE_TO_TOPLEVEL = {
        "auto_delete_commands": "auto_delete_commands",
        "welcome_message": "welcome_message",
        "left_message": "left_message",
        # add more mappings here if you introduce top-level aliases
    }

    async def _sync_feature_to_toplevel(self, group_id: int, feature: str, enabled: bool):
        """Synchronize a feature flag into a top-level key when appropriate."""
        top_key = self._FEATURE_TO_TOPLEVEL.get(feature)
        if not top_key:
            return
        # Set both the nested feature flag and the top-level key atomically
        await self.settings_collection.find_one_and_update(
            {"group_id": group_id},
            {"$set": {f"features_enabled.{feature}": enabled, top_key: enabled, "updated_at": datetime.utcnow()}},
            return_document=False
        )
    async def toggle_feature(self, group_id: int, feature: str, enabled: bool) -> bool:
        """Toggle a feature on/off"""
        result = await self.settings_collection.find_one_and_update(
            {"group_id": group_id},
            {"$set": {f"features_enabled.{feature}": enabled, "updated_at": datetime.utcnow()}},
            return_document=True
        )

        # Keep top-level alias in sync for compatibility with older code
        try:
            await self._sync_feature_to_toplevel(group_id, feature, enabled)
        except Exception:
            # Don't let synchronization errors hide the main result
            logger.debug("Failed to sync feature to top-level key")

        return result is not None
    
    # ========================================================================
    # MEMBERS
    # ========================================================================
    
    async def get_member(self, group_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """Get member info"""
        return await self.members_collection.find_one({"group_id": group_id, "user_id": user_id})
    
    async def create_member(
        self, 
        group_id: int, 
        user_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create new member record"""
        member = {
            "group_id": group_id,
            "user_id": user_id,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "role": "member",
            "joined_at": datetime.utcnow(),
            "is_active": True,
            "messages_count": 0,
            "commands_used": 0,
            "warnings_count": 0,
            "mutes_count": 0,
            "bans_count": 0,
            "is_muted": False,
            "is_banned": False,
            "can_send_messages": True,
            "can_send_media": True,
            "can_add_web_page_preview": True,
            "can_send_other": True,
            "last_activity": datetime.utcnow(),
        }
        result = await self.members_collection.insert_one(member)
        member["_id"] = result.inserted_id
        return member
    
    async def update_member(self, group_id: int, user_id: int, updates: Dict[str, Any]) -> bool:
        """Update member info"""
        result = await self.members_collection.find_one_and_update(
            {"group_id": group_id, "user_id": user_id},
            {"$set": {**updates, "last_activity": datetime.utcnow()}},
            return_document=True
        )
        return result is not None
    
    async def increment_member_stat(self, group_id: int, user_id: int, stat: str, amount: int = 1) -> bool:
        """Increment a member statistic"""
        result = await self.members_collection.find_one_and_update(
            {"group_id": group_id, "user_id": user_id},
            {"$inc": {stat: amount}, "$set": {"last_activity": datetime.utcnow()}},
            return_document=True
        )
        return result is not None
    
    async def get_group_members(self, group_id: int, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all members of a group"""
        query = {"group_id": group_id}
        if active_only:
            query["is_active"] = True
        return await self.members_collection.find(query).to_list(None)
    
    async def record_member_left(self, group_id: int, user_id: int) -> bool:
        """Record member as left"""
        return await self.update_member(
            group_id, 
            user_id,
            {
                "is_active": False,
                "left_at": datetime.utcnow()
            }
        )
    
    # ========================================================================
    # ADMINS
    # ========================================================================
    
    async def get_admin(self, group_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """Get admin info"""
        return await self.admins_collection.find_one({"group_id": group_id, "user_id": user_id})
    
    async def add_admin(
        self,
        group_id: int,
        user_id: int,
        username: Optional[str] = None,
        role: str = "admin",
        added_by: Optional[int] = None
    ) -> Dict[str, Any]:
        """Add new admin"""
        admin = {
            "group_id": group_id,
            "user_id": user_id,
            "username": username,
            "role": role,
            "added_at": datetime.utcnow(),
            "added_by": added_by,
            "is_active": True,
            "permissions": {
                "ban_members": True,
                "kick_members": True,
                "mute_members": True,
                "manage_roles": role == "super_admin",
                "manage_settings": role == "super_admin",
                "view_logs": True,
                "manage_messages": True,
                "manage_admins": role == "super_admin",
            },
            "actions_performed": 0,
        }
        result = await self.admins_collection.insert_one(admin)
        admin["_id"] = result.inserted_id
        return admin
    
    async def update_admin(self, group_id: int, user_id: int, updates: Dict[str, Any]) -> bool:
        """Update admin info"""
        result = await self.admins_collection.find_one_and_update(
            {"group_id": group_id, "user_id": user_id},
            {"$set": updates},
            return_document=True
        )
        return result is not None
    
    async def remove_admin(self, group_id: int, user_id: int) -> bool:
        """Remove admin"""
        return await self.update_admin(
            group_id,
            user_id,
            {
                "is_active": False,
                "removed_at": datetime.utcnow()
            }
        )
    
    async def get_group_admins(self, group_id: int) -> List[Dict[str, Any]]:
        """Get all active admins of a group"""
        return await self.admins_collection.find({
            "group_id": group_id,
            "is_active": True
        }).to_list(None)
    
    # ========================================================================
    # MODERATION ROLES
    # ========================================================================
    
    async def create_role(
        self,
        group_id: int,
        role_name: str,
        role_type: str,
        created_by: Optional[int] = None,
        permissions: Dict[str, bool] = None
    ) -> Dict[str, Any]:
        """Create new moderation role"""
        role = {
            "group_id": group_id,
            "role_name": role_name,
            "role_type": role_type,
            "created_at": datetime.utcnow(),
            "created_by": created_by,
            "can_ban": permissions.get("can_ban", False) if permissions else False,
            "can_kick": permissions.get("can_kick", False) if permissions else False,
            "can_mute": permissions.get("can_mute", False) if permissions else False,
            "can_warn": permissions.get("can_warn", False) if permissions else False,
            "can_promote": permissions.get("can_promote", False) if permissions else False,
            "can_demote": permissions.get("can_demote", False) if permissions else False,
            "can_manage_roles": permissions.get("can_manage_roles", False) if permissions else False,
            "can_view_logs": permissions.get("can_view_logs", False) if permissions else False,
            "can_edit_settings": permissions.get("can_edit_settings", False) if permissions else False,
            "members": []
        }
        result = await self.roles_collection.insert_one(role)
        role["_id"] = result.inserted_id
        return role
    
    async def get_role(self, group_id: int, role_name: str) -> Optional[Dict[str, Any]]:
        """Get role by name"""
        return await self.roles_collection.find_one({"group_id": group_id, "role_name": role_name})
    
    async def get_group_roles(self, group_id: int) -> List[Dict[str, Any]]:
        """Get all roles in a group"""
        return await self.roles_collection.find({"group_id": group_id}).to_list(None)
    
    async def add_member_to_role(self, group_id: int, role_name: str, user_id: int) -> bool:
        """Add member to role"""
        result = await self.roles_collection.find_one_and_update(
            {"group_id": group_id, "role_name": role_name},
            {"$addToSet": {"members": user_id}},
            return_document=True
        )
        return result is not None
    
    async def remove_member_from_role(self, group_id: int, role_name: str, user_id: int) -> bool:
        """Remove member from role"""
        result = await self.roles_collection.find_one_and_update(
            {"group_id": group_id, "role_name": role_name},
            {"$pull": {"members": user_id}},
            return_document=True
        )
        return result is not None
    
    # ========================================================================
    # COMMAND HISTORY
    # ========================================================================
    
    async def log_command(
        self,
        group_id: int,
        user_id: int,
        command: str,
        args: Optional[str] = None,
        status: str = "success",
        result: Optional[str] = None
    ) -> bool:
        """Log command execution"""
        log_entry = {
            "group_id": group_id,
            "user_id": user_id,
            "command": command,
            "args": args,
            "executed_at": datetime.utcnow(),
            "status": status,
            "result": result,
        }
        result_obj = await self.command_history_collection.insert_one(log_entry)
        return result_obj.inserted_id is not None
    
    async def get_command_history(self, group_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent command history"""
        return await self.command_history_collection.find(
            {"group_id": group_id}
        ).sort("executed_at", -1).limit(limit).to_list(None)
    
    # ========================================================================
    # EVENT LOGS
    # ========================================================================
    
    async def log_event(
        self,
        group_id: int,
        event_type: str,
        user_id: int,
        triggered_by: Optional[int] = None,
        target_user_id: Optional[int] = None,
        event_data: Dict[str, Any] = None
    ) -> bool:
        """Log event"""
        log_entry = {
            "group_id": group_id,
            "event_type": event_type,
            "user_id": user_id,
            "triggered_by": triggered_by,
            "target_user_id": target_user_id,
            "event_data": event_data or {},
            "created_at": datetime.utcnow(),
        }
        result = await self.event_logs_collection.insert_one(log_entry)
        return result.inserted_id is not None
    
    async def get_event_logs(self, group_id: int, event_type: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get event logs"""
        query = {"group_id": group_id}
        if event_type:
            query["event_type"] = event_type
        return await self.event_logs_collection.find(query).sort("created_at", -1).limit(limit).to_list(None)
    
    # ========================================================================
    # STATISTICS
    # ========================================================================
    
    async def get_group_statistics(self, group_id: int) -> Optional[Dict[str, Any]]:
        """Get group statistics"""
        return await self.statistics_collection.find_one({"group_id": group_id})
    
    async def create_statistics(self, group_id: int) -> Dict[str, Any]:
        """Create statistics for new group"""
        stats = {
            "group_id": group_id,
            "updated_at": datetime.utcnow(),
            "total_members": 0,
            "active_members": 0,
            "left_members": 0,
            "banned_members": 0,
            "muted_members": 0,
            "total_warnings": 0,
            "total_mutes": 0,
            "total_bans": 0,
            "total_kicks": 0,
            "total_messages": 0,
            "total_commands": 0,
            "total_admins": 0,
            "total_mods": 0,
        }
        result = await self.statistics_collection.insert_one(stats)
        stats["_id"] = result.inserted_id
        return stats
    
    async def update_statistics(self, group_id: int, updates: Dict[str, Any]) -> bool:
        """Update statistics"""
        updates["updated_at"] = datetime.utcnow()
        result = await self.statistics_collection.find_one_and_update(
            {"group_id": group_id},
            {"$set": updates},
            return_document=True
        )
        return result is not None
    
    async def increment_statistic(self, group_id: int, stat: str, amount: int = 1) -> bool:
        """Increment a statistic"""
        result = await self.statistics_collection.find_one_and_update(
            {"group_id": group_id},
            {"$inc": {stat: amount}, "$set": {"updated_at": datetime.utcnow()}},
            return_document=True
        )
        return result is not None
