"""
Core models and enums for bidirectional moderation system.

Easy to understand and customize - clean data structures.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional


class ActionSource(Enum):
    """Where the action originated from."""
    BOT = "BOT"      # From bot command (/ban, /mute, etc.)
    WEB = "WEB"      # From frontend dashboard
    API = "API"      # Direct API call


class ActionType(Enum):
    """Types of moderation actions."""
    BAN = "BAN"           # Permanently ban
    UNBAN = "UNBAN"       # Remove ban
    MUTE = "MUTE"         # Restrict messages
    UNMUTE = "UNMUTE"     # Remove restriction
    KICK = "KICK"         # Remove member
    WARN = "WARN"         # Issue warning


class NotificationMode(Enum):
    """How to notify about action."""
    SILENT = "SILENT"                          # No notifications
    GROUP_ONLY = "GROUP_ONLY"                  # Only to group
    GROUP_AND_USER = "GROUP_AND_USER"          # Group + user DM
    USER_ONLY = "USER_ONLY"                    # Only to user


@dataclass
class ActionPayload:
    """Unified action format used throughout the system."""
    action: ActionType
    group_id: int
    user_id: int
    admin_id: int
    reason: Optional[str] = None
    duration_hours: Optional[int] = None
    source: ActionSource = ActionSource.WEB
    notification_mode: NotificationMode = NotificationMode.GROUP_AND_USER
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'action': self.action.value,
            'group_id': self.group_id,
            'user_id': self.user_id,
            'admin_id': self.admin_id,
            'reason': self.reason,
            'duration_hours': self.duration_hours,
            'source': self.source.value,
            'notification_mode': self.notification_mode.value,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata,
        }


@dataclass
class ActionResult:
    """Standard result format for all actions."""
    ok: bool
    source: ActionSource
    timestamp: datetime
    action_id: Optional[str] = None
    error: Optional[str] = None
    execution_time_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            'ok': self.ok,
            'source': self.source.value,
            'timestamp': self.timestamp.isoformat(),
            'action_id': self.action_id,
            'error': self.error,
            'execution_time_ms': self.execution_time_ms,
            'metadata': self.metadata,
        }
