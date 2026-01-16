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
    

class SettingsUpdate(BaseModel):
    """Update settings request"""
    welcome_message_enabled: Optional[bool] = None
    welcome_message: Optional[str] = None
    goodbye_message_enabled: Optional[bool] = None
    goodbye_message: Optional[str] = None
    auto_delete_commands: Optional[bool] = None
    logging_enabled: Optional[bool] = None
    moderation_enabled: Optional[bool] = None
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
