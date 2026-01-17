"""
Enforcement Models and Enums
Unified action types, models for all enforcement operations
Integrates centralized_api enforcement with api_v2 features
"""

from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ============================================================================
# ENUMS
# ============================================================================

class ActionType(str, Enum):
    """All supported action types for enforcement"""
    BAN = "ban"
    UNBAN = "unban"
    KICK = "kick"
    MUTE = "mute"
    UNMUTE = "unmute"
    PROMOTE = "promote"
    DEMOTE = "demote"
    WARN = "warn"
    PIN = "pin"
    UNPIN = "unpin"
    DELETE_MESSAGE = "delete_message"
    RESTRICT = "restrict"
    UNRESTRICT = "unrestrict"
    PURGE = "purge"
    SET_ROLE = "set_role"
    REMOVE_ROLE = "remove_role"
    LOCKDOWN = "lockdown"
    CLEANUP_SPAM = "cleanup_spam"
    DELETE_USER_MESSAGES = "delete_user_messages"


class ActionStatus(str, Enum):
    """Action execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class EnforcementLevel(str, Enum):
    """Escalation levels for enforcement"""
    WARNING = "warning"
    MUTE_SHORT = "mute_short"        # 1 hour
    MUTE_MEDIUM = "mute_medium"      # 24 hours
    MUTE_LONG = "mute_long"          # 7 days
    BAN_TEMPORARY = "ban_temporary"  # 30 days
    BAN_PERMANENT = "ban_permanent"


class EnforcementReason(str, Enum):
    """Common enforcement reasons"""
    SPAM = "spam"
    PROFANITY = "profanity"
    HARASSMENT = "harassment"
    HATE_SPEECH = "hate_speech"
    PHISHING = "phishing"
    BOT_BEHAVIOR = "bot_behavior"
    ADULT_CONTENT = "adult_content"
    OFF_TOPIC = "off_topic"
    DUPLICATE = "duplicate"
    RULE_VIOLATION = "rule_violation"
    MANUAL = "manual"
    AUTO_CLEANUP = "auto_cleanup"


class EscalationPolicy(str, Enum):
    """User escalation tracking policy"""
    ACCUMULATE = "accumulate"      # Violations accumulate
    RESET_DAILY = "reset_daily"    # Reset each day
    RESET_WEEKLY = "reset_weekly"  # Reset each week
    RESET_MONTHLY = "reset_monthly"  # Reset monthly
    NO_RESET = "no_reset"          # Never reset


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class EnforcementAction(BaseModel):
    """Enforcement action request model"""
    action_type: ActionType
    group_id: int
    user_id: Optional[int] = None
    message_id: Optional[int] = None
    reason: Optional[EnforcementReason | str] = None
    duration_minutes: Optional[int] = None
    title: Optional[str] = None
    initiated_by: int
    escalate: bool = False
    notify_user: bool = True
    log_action: bool = True
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        use_enum_values = False


class ActionResponse(BaseModel):
    """Standard action response"""
    action_id: str
    action_type: ActionType
    group_id: int
    user_id: Optional[int] = None
    status: ActionStatus
    success: bool
    message: str
    error: Optional[str] = None
    timestamp: datetime
    execution_time_ms: Optional[float] = None
    retry_count: int = 0
    api_response: Optional[Dict[str, Any]] = None

    class Config:
        use_enum_values = False


class ActionLog(BaseModel):
    """Database action log model"""
    action_id: str
    action_type: ActionType
    group_id: int
    user_id: Optional[int] = None
    initiated_by: int
    status: ActionStatus
    success: bool
    message: str
    error: Optional[str] = None
    reason: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    executed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time_ms: Optional[float] = None
    retry_count: int = 0
    api_response: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        use_enum_values = False


class UserViolation(BaseModel):
    """User violation tracking model"""
    user_id: int
    group_id: int
    violation_count: int = 0
    last_violation_time: Optional[datetime] = None
    violations: List[Dict[str, Any]] = Field(default_factory=list)
    current_level: EnforcementLevel = EnforcementLevel.WARNING
    escalation_policy: EscalationPolicy = EscalationPolicy.ACCUMULATE
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = False


class EscalationRule(BaseModel):
    """Escalation rule for automatic enforcement"""
    group_id: int
    trigger_count: int  # Number of violations to trigger
    action_type: ActionType
    action_duration_minutes: Optional[int] = None
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = False


class BatchActionRequest(BaseModel):
    """Batch action execution request"""
    actions: List[EnforcementAction]
    execute_concurrently: bool = True
    stop_on_error: bool = False


class BatchActionResponse(BaseModel):
    """Batch action execution response"""
    batch_id: str
    total_actions: int
    successful: int
    failed: int
    results: List[ActionResponse]
    execution_time_ms: float


# ============================================================================
# ENFORCEMENT STATISTICS
# ============================================================================

class EnforcementStats(BaseModel):
    """Statistics for enforcement actions"""
    group_id: int
    total_actions: int
    successful_actions: int
    failed_actions: int
    by_type: Dict[str, int]
    by_status: Dict[str, int]
    average_execution_time_ms: float
    period_start: datetime
    period_end: datetime


class UserEnforcementHistory(BaseModel):
    """Enforcement history for a specific user"""
    user_id: int
    group_id: int
    total_violations: int
    recent_violations: List[Dict[str, Any]]
    current_status: str
    last_action: Optional[ActionLog] = None
    escalation_level: EnforcementLevel
    is_banned: bool = False
    ban_expires_at: Optional[datetime] = None
