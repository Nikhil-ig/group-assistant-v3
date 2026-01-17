"""
Pydantic Models - Type-safe schemas for all API operations
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator


# ============================================================================
# GROUP MODELS
# ============================================================================

class GroupBase(BaseModel):
    """Base group data"""
    group_id: int = Field(..., description="Telegram group ID")
    name: str = Field(..., description="Group name")
    description: Optional[str] = None
    member_count: int = Field(default=0)
    admin_count: int = Field(default=0)
    photo_url: Optional[str] = None
    is_active: bool = Field(default=True)


class GroupCreate(GroupBase):
    """Create group request"""
    pass


class GroupUpdate(BaseModel):
    """Update group request"""
    name: Optional[str] = None
    description: Optional[str] = None
    member_count: Optional[int] = None
    admin_count: Optional[int] = None
    photo_url: Optional[str] = None
    is_active: Optional[bool] = None


class GroupResponse(GroupBase):
    """Group response"""
    id: Optional[str] = Field(None, alias="_id")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True


# ============================================================================
# USER MODELS
# ============================================================================

class UserBase(BaseModel):
    """Base user data"""
    user_id: int
    username: Optional[str] = None
    first_name: str
    role: str = Field(default="member")
    is_active: bool = Field(default=True)


class UserCreate(UserBase):
    """Add user to group request"""
    group_id: int


class UserUpdate(BaseModel):
    """Update user request"""
    username: Optional[str] = None
    first_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """User response"""
    group_id: int
    id: Optional[str] = Field(None, alias="_id")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True


# ============================================================================
# ROLE MODELS
# ============================================================================

class Permission(BaseModel):
    """Individual permission"""
    name: str
    description: Optional[str] = None


class RoleBase(BaseModel):
    """Base role data"""
    name: str = Field(..., description="Role name")
    description: Optional[str] = None
    priority: int = Field(default=0, description="Priority level (higher = more powerful)")
    permissions: List[str] = Field(default_factory=list)
    color: Optional[str] = None


class RoleCreate(RoleBase):
    """Create role request"""
    group_id: int


class RoleUpdate(BaseModel):
    """Update role request"""
    description: Optional[str] = None
    priority: Optional[int] = None
    permissions: Optional[List[str]] = None
    color: Optional[str] = None


class RoleResponse(RoleBase):
    """Role response"""
    group_id: int
    id: Optional[str] = Field(None, alias="_id")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True


# ============================================================================
# RULE MODELS
# ============================================================================

class RuleBase(BaseModel):
    """Base rule data"""
    rule_name: str
    description: str
    penalty: str = Field(..., description="Penalty type (warn, mute, kick, ban)")
    penalty_duration: Optional[int] = None
    priority: int = Field(default=0)
    is_active: bool = Field(default=True)


class RuleCreate(RuleBase):
    """Create rule request"""
    group_id: int


class RuleUpdate(BaseModel):
    """Update rule request"""
    description: Optional[str] = None
    penalty: Optional[str] = None
    penalty_duration: Optional[int] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None


class RuleResponse(RuleBase):
    """Rule response"""
    group_id: int
    id: Optional[str] = Field(None, alias="_id")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True


# ============================================================================
# SETTINGS MODELS
# ============================================================================

class SettingsBase(BaseModel):
    """Base group settings"""
    welcome_message_enabled: bool = Field(default=True)
    welcome_message: Optional[str] = None
    goodbye_message_enabled: bool = Field(default=True)
    goodbye_message: Optional[str] = None
    auto_delete_commands: bool = Field(default=False)
    logging_enabled: bool = Field(default=True)
    moderation_enabled: bool = Field(default=True)
    slowmode_seconds: int = Field(default=0, ge=0, le=3600)
    

class SettingsUpdate(BaseModel):
    """Update settings request"""
    welcome_message_enabled: Optional[bool] = None
    welcome_message: Optional[str] = None
    goodbye_message_enabled: Optional[bool] = None
    goodbye_message: Optional[str] = None
    auto_delete_commands: Optional[bool] = None
    logging_enabled: Optional[bool] = None
    moderation_enabled: Optional[bool] = None
    slowmode_seconds: Optional[int] = None
    custom_settings: Optional[Dict[str, Any]] = None


class SettingsResponse(SettingsBase):
    """Settings response"""
    group_id: int
    id: Optional[str] = Field(None, alias="_id")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True


# ============================================================================
# ACTION MODELS
# ============================================================================

class ActionBase(BaseModel):
    """Base action data"""
    group_id: int
    user_id: int
    admin_id: Optional[int] = None
    action_type: str = Field(..., description="ban, kick, mute, warn, etc.")
    reason: Optional[str] = None
    duration: Optional[int] = None
    status: str = Field(default="completed")


class ActionCreate(ActionBase):
    """Create action request"""
    pass


class ActionResponse(ActionBase):
    """Action response"""
    id: Optional[str] = Field(None, alias="_id")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True


# ============================================================================
# PAGINATION MODELS
# ============================================================================

class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)


class PaginatedResponse(BaseModel):
    """Paginated response wrapper"""
    items: List[Dict[str, Any]]
    total: int
    page: int
    per_page: int
    pages: int


# ============================================================================
# STATISTICS MODELS
# ============================================================================

class GroupStatistics(BaseModel):
    """Group statistics"""
    group_id: int
    total_members: int
    total_actions: int
    actions_by_type: Dict[str, int]
    top_users: List[Dict[str, Any]]
    recent_actions: List[Dict[str, Any]]


class UserStatistics(BaseModel):
    """User statistics"""
    group_id: int
    user_id: int
    total_actions: int
    action_counts: Dict[str, int]
    last_action_time: Optional[datetime] = None


# ============================================================================
# ERROR MODELS
# ============================================================================

class ErrorResponse(BaseModel):
    """Error response"""
    success: bool = False
    error: str
    details: Optional[Dict[str, Any]] = None


class SuccessResponse(BaseModel):
    """Success response"""
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None


# ============================================================================
# PERMISSION STATE MODELS
# ============================================================================

class UserPermissionState(BaseModel):
    """User permission state for a group"""
    group_id: int
    user_id: int
    can_send_messages: bool = True
    can_send_other_messages: bool = True  # Stickers & GIFs
    can_send_audios: bool = True          # Voice messages
    can_send_documents: bool = True
    can_send_photos: bool = True
    can_send_videos: bool = True
    is_restricted: bool = False
    restricted_at: Optional[datetime] = None
    restricted_by: Optional[int] = None
    restriction_reason: Optional[str] = None
    restrictions_until: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True


class UserPermissionUpdate(BaseModel):
    """Update user permission"""
    permission_type: str  # "can_send_messages", "can_send_other_messages", "can_send_audios"
    allowed: bool
    reason: Optional[str] = None
    restricted_by: Optional[int] = None


class UserPermissionResponse(BaseModel):
    """Permission response"""
    group_id: int
    user_id: int
    can_send_messages: bool
    can_send_other_messages: bool
    can_send_audios: bool
    is_restricted: bool
    restriction_reason: Optional[str] = None


# ============================================================================
# WHITELIST/BLACKLIST MODELS
# ============================================================================

class WhitelistEntry(BaseModel):
    """Whitelist entry - exempts from restrictions OR grants non-admin powers"""
    group_id: int
    user_id: int
    username: Optional[str] = None
    entry_type: str = Field(default="exemption", description="exemption (bypass restrictions) or moderator (grant admin powers)")
    admin_powers: List[str] = Field(default_factory=list, description="Powers granted: mute, unmute, warn, kick, send_link, restrict, unrestrict, etc.")
    reason: Optional[str] = None
    added_by: int  # Admin who added this entry
    added_at: datetime
    updated_at: datetime
    is_active: bool = True


class BlacklistEntry(BaseModel):
    """Blacklist entry - block users, stickers, GIFs, or links"""
    group_id: int
    entry_type: str = Field(..., description="user, sticker, gif, link, domain")
    blocked_item: str  # user_id, sticker_id, gif_id, link, or domain
    reason: Optional[str] = None
    added_by: int  # Admin who added this entry
    added_at: datetime
    updated_at: datetime
    is_active: bool = True
    auto_delete: bool = True  # Auto-delete messages with this item


class WhitelistCreate(BaseModel):
    """Create whitelist entry"""
    group_id: int
    user_id: int
    username: Optional[str] = None
    entry_type: str = Field(default="exemption")
    admin_powers: List[str] = Field(default_factory=list)
    reason: Optional[str] = None
    added_by: int


class WhitelistUpdate(BaseModel):
    """Update whitelist entry"""
    entry_type: Optional[str] = None
    admin_powers: Optional[List[str]] = None
    reason: Optional[str] = None
    is_active: Optional[bool] = None


class BlacklistCreate(BaseModel):
    """Create blacklist entry"""
    group_id: int
    entry_type: str
    blocked_item: str
    reason: Optional[str] = None
    added_by: int


# ============================================================================
# NIGHT MODE MODELS
# ============================================================================

class NightModeSettings(BaseModel):
    """Night mode settings - scheduled content restrictions"""
    group_id: int
    enabled: bool = Field(default=False, description="Is night mode enabled?")
    start_time: str = Field(default="22:00", description="Start time in HH:MM format (24-hour)")
    end_time: str = Field(default="08:00", description="End time in HH:MM format (24-hour)")
    restricted_content_types: List[str] = Field(
        default_factory=lambda: ["stickers", "gifs", "media", "voice"],
        description="Content types to restrict: text, stickers, gifs, media, voice, links"
    )
    exempt_user_ids: List[int] = Field(default_factory=list, description="User IDs exempt from night mode")
    exempt_roles: List[str] = Field(default_factory=list, description="Roles exempt from night mode (admin, moderator, vip)")
    auto_delete_restricted: bool = Field(default=True, description="Auto-delete restricted content?")
    created_at: datetime
    updated_at: datetime


class NightModeCreate(BaseModel):
    """Create/update night mode settings"""
    enabled: Optional[bool] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    restricted_content_types: Optional[List[str]] = None
    exempt_user_ids: Optional[List[int]] = None
    exempt_roles: Optional[List[str]] = None
    auto_delete_restricted: Optional[bool] = None


class NightModeUpdate(BaseModel):
    """Update night mode settings"""
    enabled: Optional[bool] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    restricted_content_types: Optional[List[str]] = None
    exempt_user_ids: Optional[List[int]] = None
    exempt_roles: Optional[List[str]] = None
    auto_delete_restricted: Optional[bool] = None


class NightModeStatus(BaseModel):
    """Night mode status check response"""
    is_active: bool  # Is it currently night mode time?
    enabled: bool  # Is night mode feature enabled?
    current_time: str  # Current time HH:MM
    start_time: str
    end_time: str
    next_transition: str  # When does it change next?


class NightModePermissionCheck(BaseModel):
    """Check if user can send specific content type during night mode"""
    can_send: bool
    reason: str  # Why can/cannot send
    is_exempt: bool
    is_admin: bool
    content_type: str
    auto_delete: bool = True


class BlacklistUpdate(BaseModel):
    """Update blacklist entry"""
    reason: Optional[str] = None
    is_active: Optional[bool] = None
    auto_delete: Optional[bool] = None


class WhitelistResponse(BaseModel):
    """Whitelist entry response"""
    id: Optional[str] = Field(None, alias="_id")
    group_id: int
    user_id: int
    username: Optional[str] = None
    entry_type: str
    admin_powers: List[str]
    reason: Optional[str] = None
    added_by: int
    added_at: datetime
    is_active: bool
    
    class Config:
        populate_by_name = True


class BlacklistResponse(BaseModel):
    """Blacklist entry response"""
    id: Optional[str] = Field(None, alias="_id")
    group_id: int
    entry_type: str
    blocked_item: str
    reason: Optional[str] = None
    added_by: int
    added_at: datetime
    is_active: bool
    auto_delete: bool
    
    class Config:
        populate_by_name = True

