"""
Advanced MongoDB Models for Settings, Members, Admins, and Moderation
Handles all persistence for the advanced bot system
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class ModerationRole(str, Enum):
    """Available moderation roles"""
    MEMBER = "member"
    MODERATOR = "moderator"
    SENIOR_MOD = "senior_mod"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class FeatureType(str, Enum):
    """Bot features that can be enabled/disabled"""
    WELCOME_MESSAGE = "welcome_message"
    LEFT_MESSAGE = "left_message"
    PIN_MESSAGE = "pin_message"
    MODERATION = "moderation"
    AUTO_MUTE = "auto_mute"
    AUTO_BAN = "auto_ban"
    WARNINGS = "warnings"
    ROLE_ASSIGNMENT = "role_assignment"
    MEMBER_TRACKING = "member_tracking"
    COMMAND_LOGGING = "command_logging"
    EVENT_LOGGING = "event_logging"


# ============================================================================
# SETTINGS MODEL
# ============================================================================

class GroupSettingsModel(BaseModel):
    """Settings for a group"""
    group_id: int
    group_name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Feature toggles
    features_enabled: Dict[str, bool] = Field(default_factory=lambda: {
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
    })
    
    # Customizable messages
    welcome_message: Optional[str] = "👋 Welcome to {group_name}! Please read the rules."
    left_message: Optional[str] = "👋 {username} left the group."
    
    # Moderation settings
    max_warnings: int = 3
    auto_mute_after_warns: int = 3
    mute_duration: int = 60  # minutes
    auto_ban_after_mutes: int = 3
    
    # Admin settings
    admin_notifications: bool = True
    admin_chat_id: Optional[int] = None
    
    # Advanced settings
    auto_delete_commands: bool = False  # NEW: Don't delete by default
    keep_message_history: bool = True  # NEW: Keep history
    
    class Config:
        json_schema_extra = {
            "example": {
                "group_id": -1001234567890,
                "group_name": "My Group",
                "features_enabled": {
                    "welcome_message": True,
                    "moderation": True,
                },
                "welcome_message": "Welcome to {group_name}!",
                "max_warnings": 3,
            }
        }


# ============================================================================
# MEMBERS MODEL
# ============================================================================

class MemberModel(BaseModel):
    """Member information and tracking"""
    group_id: int
    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: ModerationRole = ModerationRole.MEMBER
    
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    left_at: Optional[datetime] = None
    is_active: bool = True
    
    # Statistics
    messages_count: int = 0
    commands_used: int = 0
    warnings_count: int = 0
    mutes_count: int = 0
    bans_count: int = 0
    
    # Status
    is_muted: bool = False
    muted_until: Optional[datetime] = None
    is_banned: bool = False
    banned_reason: Optional[str] = None
    
    # Permissions
    can_send_messages: bool = True
    can_send_media: bool = True
    can_add_web_page_preview: bool = True
    can_send_other: bool = True
    
    # Last activity
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "group_id": -1001234567890,
                "user_id": 123456789,
                "username": "john_doe",
                "role": "member",
                "warnings_count": 1,
                "is_active": True,
            }
        }


# ============================================================================
# ADMIN MODEL
# ============================================================================

class AdminModel(BaseModel):
    """Admin information and permissions"""
    group_id: int
    user_id: int
    username: Optional[str] = None
    role: ModerationRole = ModerationRole.ADMIN
    
    added_at: datetime = Field(default_factory=datetime.utcnow)
    added_by: Optional[int] = None  # Who added this admin
    removed_at: Optional[datetime] = None
    is_active: bool = True
    
    # Permissions
    permissions: Dict[str, bool] = Field(default_factory=lambda: {
        "ban_members": True,
        "kick_members": True,
        "mute_members": True,
        "manage_roles": True,
        "manage_settings": True,
        "view_logs": True,
        "manage_messages": True,
        "manage_admins": False,
    })
    
    # Activity tracking
    actions_performed: int = 0
    last_action_at: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "group_id": -1001234567890,
                "user_id": 123456789,
                "role": "admin",
                "permissions": {
                    "ban_members": True,
                    "manage_settings": True,
                }
            }
        }


# ============================================================================
# MODERATION ROLE MODEL
# ============================================================================

class ModerationRoleModel(BaseModel):
    """Custom moderation roles"""
    group_id: int
    role_name: str
    role_type: ModerationRole
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[int] = None
    
    # Permissions for this role
    can_ban: bool = False
    can_kick: bool = False
    can_mute: bool = False
    can_warn: bool = False
    can_promote: bool = False
    can_demote: bool = False
    can_manage_roles: bool = False
    can_view_logs: bool = False
    can_edit_settings: bool = False
    
    # Members with this role
    members: List[int] = Field(default_factory=list)
    
    class Config:
        json_schema_extra = {
            "example": {
                "group_id": -1001234567890,
                "role_name": "Moderator",
                "role_type": "moderator",
                "can_mute": True,
                "can_warn": True,
                "can_view_logs": True,
            }
        }


# ============================================================================
# COMMAND HISTORY MODEL
# ============================================================================

class CommandHistoryModel(BaseModel):
    """Track all command usage"""
    group_id: int
    user_id: int
    command: str
    args: Optional[str] = None
    
    executed_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "success"  # success, error, pending
    result: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "group_id": -1001234567890,
                "user_id": 123456789,
                "command": "mute",
                "args": "501166051",
                "status": "success",
            }
        }


# ============================================================================
# EVENT LOG MODEL
# ============================================================================

class EventLogModel(BaseModel):
    """Log all events (join, leave, mute, ban, etc.)"""
    group_id: int
    event_type: str  # join, leave, mute, unmute, ban, unban, warn, etc.
    user_id: int
    
    triggered_by: Optional[int] = None  # Who triggered (for admin actions)
    target_user_id: Optional[int] = None  # Who it affected
    
    event_data: Dict[str, Any] = Field(default_factory=dict)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "group_id": -1001234567890,
                "event_type": "mute",
                "user_id": 123456789,
                "triggered_by": 987654321,
                "event_data": {
                    "duration": 30,
                    "reason": "Spam"
                }
            }
        }


# ============================================================================
# STATISTICS MODEL
# ============================================================================

class GroupStatisticsModel(BaseModel):
    """Group statistics and analytics"""
    group_id: int
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Member stats
    total_members: int = 0
    active_members: int = 0
    left_members: int = 0
    banned_members: int = 0
    muted_members: int = 0
    
    # Action stats
    total_warnings: int = 0
    total_mutes: int = 0
    total_bans: int = 0
    total_kicks: int = 0
    
    # Message stats
    total_messages: int = 0
    total_commands: int = 0
    
    # Role stats
    total_admins: int = 0
    total_mods: int = 0
    
    class Config:
        json_schema_extra = {
            "example": {
                "group_id": -1001234567890,
                "total_members": 150,
                "active_members": 120,
                "total_warnings": 5,
            }
        }
