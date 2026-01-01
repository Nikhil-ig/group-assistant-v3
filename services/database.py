"""
MongoDB Database Service with Role-Based Access Control (RBAC).

Handles all database operations including:
- User role management (SUPERADMIN, GROUP_ADMIN, USER)
- Group management and access control
- Audit logging for all actions
- Metrics tracking
"""

from __future__ import annotations
from enum import Enum
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)


class UserRole(Enum):
    """User roles in the system."""
    SUPERADMIN = "superadmin"      # Can control ALL groups
    GROUP_ADMIN = "group_admin"    # Can control ONLY their groups
    USER = "user"                  # Can only view logs


class ActionType(Enum):
    """Types of moderation actions."""
    BAN = "ban"
    UNBAN = "unban"
    MUTE = "mute"
    UNMUTE = "unmute"
    KICK = "kick"
    WARN = "warn"


class DatabaseService:
    """Service for all database operations with RBAC."""
    
    def __init__(self, db: Any):
        """Initialize database service.
        
        Args:
            db: AsyncIOMotorDatabase instance from motor
        """
        self.db: Any = db
        self.client = None
        self.config = None
    
    async def health_check(self) -> bool:
        """Check MongoDB connection health."""
        try:
            # Test connection by pinging database
            await self.db.command("ping")
            logger.info("✓ MongoDB connection healthy")
            return True
        except Exception as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            return False
    
    async def create_indexes(self):
        """Create necessary database indexes for performance."""
        try:
            # Groups indexes
            await self.db["groups"].create_index("group_id", unique=True)
            await self.db["groups"].create_index("created_at")
            
            # Admins indexes
            await self.db["admins"].create_index([("user_id", 1), ("group_id", 1)], unique=True, sparse=True)
            await self.db["admins"].create_index("user_id")
            await self.db["admins"].create_index("group_id")
            
            # Audit logs indexes
            await self.db["audit_logs"].create_index("group_id")
            await self.db["audit_logs"].create_index("admin_id")
            await self.db["audit_logs"].create_index("timestamp")
            await self.db["audit_logs"].create_index([("group_id", 1), ("timestamp", -1)])
            
            # Metrics indexes
            await self.db["metrics"].create_index("group_id", unique=True)

            # Members indexes: fast lookup by group+user
            await self.db["members"].create_index([("group_id", 1), ("user_id", 1)], unique=True)
            await self.db["members"].create_index("user_id")
            await self.db["members"].create_index("last_seen")

            # Blacklist / whitelist
            await self.db["blacklist"].create_index([("group_id", 1), ("user_id", 1)], unique=True)
            await self.db["whitelist"].create_index([("group_id", 1), ("user_id", 1)], unique=True)
            
            logger.info("✓ Database indexes created")
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")

    # ===== MEMBER / PRESENCE MANAGEMENT =====

    async def upsert_member(
        self,
        group_id: int,
        user_id: int,
        username: Optional[str],
        first_name: Optional[str],
        is_bot: bool = False,
        status: Optional[str] = None,
        last_seen: Optional[datetime] = None,
        joined_at: Optional[datetime] = None,
        left_at: Optional[datetime] = None,
        permissions: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Insert or update a member record for a group.

        Keeps last_seen, join/leave timestamps and basic profile info. Fast upsert used
        for high throughput from message events.
        """
        try:
            doc = {
                "group_id": group_id,
                "user_id": user_id,
                "username": username or "",
                "first_name": first_name or "",
                "is_bot": bool(is_bot),
                "status": status,
                "permissions": permissions or {},
                "updated_at": datetime.now(timezone.utc),
            }

            if last_seen:
                doc["last_seen"] = last_seen
            if joined_at:
                doc["joined_at"] = joined_at
            if left_at:
                doc["left_at"] = left_at

            await self.db["members"].update_one(
                {"group_id": group_id, "user_id": user_id},
                {"$set": doc, "$setOnInsert": {"created_at": datetime.now(timezone.utc)}},
                upsert=True,
            )
            return True
        except Exception as e:
            logger.error(f"Error upserting member {user_id} in group {group_id}: {e}")
            return False

    async def record_join(self, group_id: int, user: Dict[str, Any], when: Optional[datetime] = None) -> bool:
        """Record a user join event and upsert member record with join timestamp."""
        try:
            when = when or datetime.now(timezone.utc)
            return await self.upsert_member(
                group_id=group_id,
                user_id=user.get("id") or user.get("user_id"),
                username=user.get("username"),
                first_name=user.get("first_name"),
                is_bot=user.get("is_bot", False),
                joined_at=when,
            )
        except Exception as e:
            logger.error(f"Error recording join for {user}: {e}")
            return False

    async def record_leave(self, group_id: int, user_id: int, when: Optional[datetime] = None) -> bool:
        """Record a user leave event (sets left_at) and keeps last_seen."""
        try:
            when = when or datetime.now(timezone.utc)
            await self.db["members"].update_one(
                {"group_id": group_id, "user_id": user_id},
                {"$set": {"left_at": when, "updated_at": datetime.now(timezone.utc)}},
            )
            return True
        except Exception as e:
            logger.error(f"Error recording leave for {user_id} in {group_id}: {e}")
            return False

    async def set_member_permissions(self, group_id: int, user_id: int, permissions: Dict[str, Any]) -> bool:
        """Persist member permissions (admin flags, restrictions)."""
        try:
            await self.db["members"].update_one(
                {"group_id": group_id, "user_id": user_id},
                {"$set": {"permissions": permissions, "updated_at": datetime.now(timezone.utc)}},
                upsert=True,
            )
            return True
        except Exception as e:
            logger.error(f"Error setting permissions for {user_id} in {group_id}: {e}")
            return False

    async def get_member(self, group_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        try:
            return await self.db["members"].find_one({"group_id": group_id, "user_id": user_id})
        except Exception as e:
            logger.error(f"Error getting member {user_id} in {group_id}: {e}")
            return None

    async def get_members(self, group_id: int, limit: int = 100, skip: int = 0) -> List[Dict[str, Any]]:
        """Return a paginated list of members for a group."""
        try:
            cursor = self.db["members"].find({"group_id": group_id}).sort("last_seen", -1).skip(skip).limit(limit)
            members = await cursor.to_list(length=limit)
            return members or []
        except Exception as e:
            logger.error(f"Error getting members for group {group_id}: {e}")
            return []

    async def get_blacklist_entries(self, group_id: int, limit: int = 100, skip: int = 0) -> List[Dict[str, Any]]:
        """Return a paginated list of blacklist entries for a group."""
        try:
            cursor = self.db["blacklist"].find({"group_id": group_id}).sort("added_at", -1).skip(skip).limit(limit)
            entries = await cursor.to_list(length=limit)
            return entries or []
        except Exception as e:
            logger.error(f"Error getting blacklist for group {group_id}: {e}")
            return []

    # ===== BLACKLIST / WHITELIST =====

    async def add_to_blacklist(self, group_id: int, user_id: int, reason: Optional[str] = None, added_by: Optional[int] = None) -> bool:
        try:
            await self.db["blacklist"].update_one(
                {"group_id": group_id, "user_id": user_id},
                {"$set": {"reason": reason or "", "added_by": added_by, "added_at": datetime.now(timezone.utc)}},
                upsert=True,
            )
            return True
        except Exception as e:
            logger.error(f"Error adding to blacklist: {e}")
            return False

    async def remove_from_blacklist(self, group_id: int, user_id: int) -> bool:
        try:
            await self.db["blacklist"].delete_one({"group_id": group_id, "user_id": user_id})
            return True
        except Exception as e:
            logger.error(f"Error removing from blacklist: {e}")
            return False

    async def is_blacklisted(self, group_id: int, user_id: int) -> bool:
        try:
            doc = await self.db["blacklist"].find_one({"group_id": group_id, "user_id": user_id})
            return bool(doc)
        except Exception as e:
            logger.error(f"Error checking blacklist: {e}")
            return False

    async def add_to_whitelist(self, group_id: int, user_id: int, note: Optional[str] = None) -> bool:
        try:
            await self.db["whitelist"].update_one(
                {"group_id": group_id, "user_id": user_id},
                {"$set": {"note": note or "", "added_at": datetime.now(timezone.utc)}},
                upsert=True,
            )
            return True
        except Exception as e:
            logger.error(f"Error adding to whitelist: {e}")
            return False

    async def remove_from_whitelist(self, group_id: int, user_id: int) -> bool:
        try:
            await self.db["whitelist"].delete_one({"group_id": group_id, "user_id": user_id})
            return True
        except Exception as e:
            logger.error(f"Error removing from whitelist: {e}")
            return False

    async def is_whitelisted(self, group_id: int, user_id: int) -> bool:
        try:
            doc = await self.db["whitelist"].find_one({"group_id": group_id, "user_id": user_id})
            return bool(doc)
        except Exception as e:
            logger.error(f"Error checking whitelist: {e}")
            return False

    async def is_user_muted(self, group_id: int, user_id: int) -> bool:
        """Return True if the user currently has an active mute in the group.

        This checks the latest mute/unmute audit log entries for the user and
        respects duration_hours if provided.
        """
        try:
            # Find the most recent mute entry for this user in the group
            last_mute = await self.db["audit_logs"].find_one(
                {"group_id": group_id, "target_user_id": user_id, "action_type": ActionType.MUTE.value},
                sort=[("timestamp", -1)],
            )

            if not last_mute:
                return False

            # If there is any UNMUTE after this mute, user is not muted
            unmute_after = await self.db["audit_logs"].find_one(
                {"group_id": group_id, "target_user_id": user_id, "action_type": ActionType.UNMUTE.value, "timestamp": {"$gt": last_mute["timestamp"]}},
            )
            if unmute_after:
                return False

            # If mute had a duration, check expiry
            dur = last_mute.get("duration_hours")
            if dur:
                expire_at = last_mute["timestamp"] + timedelta(hours=dur)
                return datetime.now(timezone.utc) < expire_at

            # Otherwise, it's a persistent mute until explicitly unmuted
            return True
        except Exception as e:
            logger.error(f"Error checking if user is muted: {e}")
            return False

    # ===== SYNC HELPERS =====

    async def sync_group_admins(self, group_id: int, admins: List[Dict[str, Any]]) -> bool:
        """Sync the admin list for a group with the `admins` collection.

        `admins` is expected to be a list of ChatMember objects or dicts with user info.
        This operation upserts admins and removes stale ones for the group.
        """
        try:
            current_admin_ids = []
            for a in admins:
                # accept either objects or dicts
                user = a.user if hasattr(a, "user") else a.get("user", a)
                uid = user.id if hasattr(user, "id") else user.get("id")
                username = getattr(user, "username", None) or user.get("username")
                first_name = getattr(user, "first_name", None) or user.get("first_name")

                current_admin_ids.append(uid)
                await self.add_group_admin(group_id=group_id, user_id=uid, username=username or "", first_name=first_name or "")

            # remove admins not in current list (for this group)
            await self.db["admins"].delete_many({"group_id": group_id, "user_id": {"$nin": current_admin_ids}, "role": UserRole.GROUP_ADMIN.value})
            return True
        except Exception as e:
            logger.error(f"Error syncing admins for group {group_id}: {e}")
            return False
    
    # ===== ADMIN MANAGEMENT (RBAC) =====
    
    async def add_superadmin(self, user_id: int, username: str, first_name: str) -> bool:
        """Add or update superadmin."""
        try:
            await self.db["admins"].update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "user_id": user_id,
                        "username": username,
                        "first_name": first_name,
                        "role": UserRole.SUPERADMIN.value,
                        "group_id": None,  # Superadmin not tied to specific group
                        "updated_at": datetime.now(timezone.utc),
                    }
                },
                upsert=True
            )
            logger.info(f"✓ Superadmin {username} ({user_id}) set")
            return True
        except Exception as e:
            logger.error(f"Error adding superadmin: {e}")
            return False
    
    async def add_group_admin(self, group_id: int, user_id: int, username: str, first_name: str) -> bool:
        """Add user as admin for specific group."""
        try:
            await self.db["admins"].update_one(
                {"user_id": user_id, "group_id": group_id},
                {
                    "$set": {
                        "user_id": user_id,
                        "username": username,
                        "first_name": first_name,
                        "role": UserRole.GROUP_ADMIN.value,
                        "group_id": group_id,
                        "updated_at": datetime.now(timezone.utc),
                    }
                },
                upsert=True
            )
            logger.info(f"✓ {username} ({user_id}) added as admin for group {group_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding group admin: {e}")
            return False
    
    async def remove_group_admin(self, group_id: int, user_id: int) -> bool:
        """Remove user as admin for specific group."""
        try:
            result = await self.db["admins"].delete_one({
                "user_id": user_id,
                "group_id": group_id
            })
            if result.deleted_count > 0:
                logger.info(f"✓ User {user_id} removed as admin for group {group_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error removing group admin: {e}")
            return False
    
    async def get_user_role(self, user_id: int, group_id: Optional[int] = None) -> UserRole:
        """Get user's role (superadmin, group_admin, or user)."""
        try:
            # Check if superadmin
            superadmin = await self.db["admins"].find_one({
                "user_id": user_id,
                "role": UserRole.SUPERADMIN.value
            })
            if superadmin:
                return UserRole.SUPERADMIN
            
            # Check if group admin (if group_id provided)
            if group_id:
                group_admin = await self.db["admins"].find_one({
                    "user_id": user_id,
                    "group_id": group_id,
                    "role": UserRole.GROUP_ADMIN.value
                })
                if group_admin:
                    return UserRole.GROUP_ADMIN
            
            # Default role
            return UserRole.USER
        except Exception as e:
            logger.error(f"Error getting user role: {e}")
            return UserRole.USER
    
    async def is_superadmin(self, user_id: int) -> bool:
        """Check if user is superadmin."""
        role = await self.get_user_role(user_id)
        return role == UserRole.SUPERADMIN
    
    async def is_group_admin(self, user_id: int, group_id: int) -> bool:
        """Check if user is admin of specific group or superadmin."""
        role = await self.get_user_role(user_id, group_id)
        return role in (UserRole.SUPERADMIN, UserRole.GROUP_ADMIN)
    
    # ===== GROUP MANAGEMENT =====
    
    async def register_group(self, group_id: int, group_name: str) -> bool:
        """Register a new group."""
        try:
            await self.db["groups"].update_one(
                {"group_id": group_id},
                {
                    "$set": {
                        "group_id": group_id,
                        "group_name": group_name,
                        "created_at": datetime.now(timezone.utc),
                        "active": True,
                    }
                },
                upsert=True
            )
            logger.info(f"✓ Group registered: {group_name} ({group_id})")
            return True
        except Exception as e:
            logger.error(f"Error registering group: {e}")
            return False
    
    async def get_group(self, group_id: int) -> Optional[Dict[str, Any]]:
        """Get group information."""
        try:
            return await self.db["groups"].find_one({"group_id": group_id})
        except Exception as e:
            logger.error(f"Error getting group: {e}")
            return None
    
    async def get_groups_for_user(self, user_id: int) -> List[Dict[str, Any]]:
        """Get groups accessible to user (RBAC enforced).
        
        - SUPERADMIN: Returns ALL groups
        - GROUP_ADMIN: Returns ONLY groups they admin
        - USER: Returns empty list (users don't manage groups)
        """
        try:
            role = await self.get_user_role(user_id)
            
            if role == UserRole.SUPERADMIN:
                # Superadmin sees all groups
                groups = await self.db["groups"].find({"active": True}).to_list(None)
                return groups or []
            
            elif role == UserRole.GROUP_ADMIN:
                # Group admin sees only their groups
                admin_groups = await self.db["admins"].find({
                    "user_id": user_id,
                    "role": UserRole.GROUP_ADMIN.value
                }).to_list(None)
                
                group_ids = [admin["group_id"] for admin in admin_groups]
                if not group_ids:
                    return []
                
                groups = await self.db["groups"].find({
                    "group_id": {"$in": group_ids},
                    "active": True
                }).to_list(None)
                return groups or []
            
            else:
                # Regular users don't see groups
                return []
        
        except Exception as e:
            logger.error(f"Error getting groups for user: {e}")
            return []
    
    # ===== AUDIT LOGGING =====
    
    async def log_action(
        self,
        group_id: int,
        action_type: ActionType,
        admin_id: int,
        admin_username: str,
        target_user_id: int,
        target_username: Optional[str] = None,
        reason: Optional[str] = None,
        duration_hours: Optional[int] = None,
    ) -> bool:
        """Log a moderation action to audit log."""
        try:
            # If username not provided, try to enrich from members collection for better human-readable logs
            if not target_username:
                try:
                    member = await self.db["members"].find_one({"group_id": group_id, "user_id": target_user_id})
                    if member:
                        target_username = member.get("username") or member.get("first_name")
                except Exception:
                    # ignore enrichment errors
                    target_username = target_username

            log_entry = {
                "group_id": group_id,
                "action_type": action_type.value if isinstance(action_type, ActionType) else action_type,
                "admin_id": admin_id,
                "admin_username": admin_username,
                "target_user_id": target_user_id,
                "target_username": target_username,
                "reason": reason or "",
                "duration_hours": duration_hours,
                "timestamp": datetime.now(timezone.utc),
            }
            
            result = await self.db["audit_logs"].insert_one(log_entry)
            logger.info(f"✓ Action logged: {action_type.value if isinstance(action_type, ActionType) else action_type} "
                       f"by {admin_username} on {target_user_id}")
            return bool(result.inserted_id)
        except Exception as e:
            logger.error(f"Error logging action: {e}")
            return False
    
    async def get_audit_logs(
        self,
        group_id: int,
        action_type: Optional[str] = None,
        limit: int = 50,
        skip: int = 0,
    ) -> List[Dict[str, Any]]:
        """Get audit logs for group with pagination."""
        try:
            query = {"group_id": group_id}
            if action_type:
                query["action_type"] = action_type
            
            logs = await self.db["audit_logs"].find(query).sort("timestamp", -1).skip(skip).limit(limit).to_list(None)
            return logs or []
        except Exception as e:
            logger.error(f"Error getting audit logs: {e}")
            return []
    
    async def get_audit_logs_count(self, group_id: int, action_type: Optional[str] = None) -> int:
        """Get total count of audit logs for pagination."""
        try:
            query = {"group_id": group_id}
            if action_type:
                query["action_type"] = action_type
            return await self.db["audit_logs"].count_documents(query)
        except Exception as e:
            logger.error(f"Error counting audit logs: {e}")
            return 0
    
    # ===== METRICS =====
    
    async def update_metrics(self, group_id: int, action_type: ActionType) -> bool:
        """Update metrics for action type."""
        try:
            action = action_type.value if isinstance(action_type, ActionType) else action_type
            
            await self.db["metrics"].update_one(
                {"group_id": group_id},
                {
                    "$inc": {
                        f"actions.{action}": 1,
                        "total_actions": 1,
                    },
                    "$set": {
                        "group_id": group_id,
                        "last_action": datetime.now(timezone.utc),
                    }
                },
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")
            return False
    
    async def get_metrics(self, group_id: int) -> Optional[Dict[str, Any]]:
        """Get metrics for a group."""
        try:
            metrics = await self.db["metrics"].find_one({"group_id": group_id})
            return metrics
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return None
    
    async def get_all_metrics(self) -> List[Dict[str, Any]]:
        """Get all metrics (for superadmin dashboard)."""
        try:
            metrics = await self.db["metrics"].find({}).to_list(None)
            return metrics or []
        except Exception as e:
            logger.error(f"Error getting all metrics: {e}")
            return []
