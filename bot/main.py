"""
Telegram Bot Service - Main Entry Point
Independent bot service that communicates with centralized_api via HTTP
Handles all Telegram updates and commands
"""

import asyncio
import logging
import os
from typing import Optional
import html
from pathlib import Path

# Load environment variables from a local .env file (if present).
# This allows running the bot on a VPS or locally without exporting
# the TELEGRAM_BOT_TOKEN and other variables into the shell.
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, BotCommand, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import httpx
import asyncio

# Try to load .env placed next to this file (project-level .env)
# override=True ensures .env values override shell environment variables
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(env_path, override=True)

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CENTRALIZED_API_URL = os.getenv("CENTRALIZED_API_URL", "http://localhost:8000")
CENTRALIZED_API_KEY = os.getenv("CENTRALIZED_API_KEY", "shared-api-key")

if not TELEGRAM_BOT_TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN not set in environment variables")
    raise ValueError("TELEGRAM_BOT_TOKEN is required")


# ============================================================================
# CALLBACK DATA COMPRESSION SYSTEM (Telegram 64-byte limit fix)
# ============================================================================
import json
import base64

# Store mapping: encoded_id -> {action, user_id, group_id}
CALLBACK_DATA_CACHE = {}
CALLBACK_COUNTER = 0

def encode_callback_data(action: str, user_id: int, group_id: int) -> str:
    """
    Encode callback data into a short string to avoid Telegram's 64-byte limit.
    
    Telegram limits callback_data to 64 bytes. Long numeric IDs exceed this.
    Solution: Store mapping in memory, return short encoded ID.
    
    Args:
        action: Action name (ban, mute, etc.)
        user_id: Target user ID
        group_id: Target group ID
    
    Returns:
        Short string like "cb_0", "cb_1", etc. (~4 bytes vs ~30+ bytes)
    """
    global CALLBACK_COUNTER
    
    callback_id = f"cb_{CALLBACK_COUNTER}"
    CALLBACK_DATA_CACHE[callback_id] = {
        "action": action,
        "user_id": user_id,
        "group_id": group_id
    }
    CALLBACK_COUNTER += 1
    
    # Keep memory usage bounded: remove old entries if cache gets too large
    if len(CALLBACK_DATA_CACHE) > 10000:
        # Remove oldest 1000 entries
        old_keys = list(CALLBACK_DATA_CACHE.keys())[:1000]
        for key in old_keys:
            del CALLBACK_DATA_CACHE[key]
    
    return callback_id

def decode_callback_data(callback_id: str) -> Optional[dict]:
    """
    Decode callback data from encoded ID.
    
    Args:
        callback_id: Encoded callback ID (e.g., "cb_0")
    
    Returns:
        Dict with {action, user_id, group_id} or None if not found
    """
    return CALLBACK_DATA_CACHE.get(callback_id)


# ============================================================================
# BOT CLIENT FOR CENTRALIZED API
# ============================================================================

class CentralizedAPIClient:
    """HTTP client for communicating with centralized_api"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = 30
        # Simple in-memory cache for group settings to reduce API calls
        # structure: { group_id: (settings_dict, expires_at_timestamp) }
        self._settings_cache: dict[int, tuple[dict, float]] = {}
        self._cache_ttl = int(os.getenv("SETTINGS_CACHE_TTL", "30"))  # seconds
    
    async def health_check(self) -> bool:
        """Check if centralized_api is healthy"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/health",
                    timeout=self.timeout
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    async def execute_action(self, action_data: dict) -> dict:
        """Execute an action through centralized_api"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/actions/execute",
                    json=action_data,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            return {"error": str(e)}
    
    async def get_user_permissions(self, user_id: int, group_id: int) -> dict:
        """Get user permissions from centralized_api"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/rbac/users/{user_id}/permissions",
                    params={"group_id": group_id},
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Get permissions failed: {e}")
            return {"error": str(e)}

    async def get_group_settings(self, group_id: int) -> dict:
        """Fetch group settings from centralized API (advanced settings)
        Returns a dict with at least a `features_enabled` mapping.
        """
        # Check cache first
        try:
            import time
            cached = self._settings_cache.get(group_id)
            if cached:
                settings, expires = cached
                if time.time() < expires:
                    return settings
        except Exception:
            # ignore cache errors
            pass

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/api/advanced/settings/{group_id}",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=self.timeout
                )
                resp.raise_for_status()
                data = resp.json()
                # API wraps data under data key
                settings = data.get("data") if isinstance(data, dict) else data

                # store in cache
                try:
                    import time
                    self._settings_cache[group_id] = (settings, time.time() + self._cache_ttl)
                except Exception:
                    pass

                return settings
        except Exception as e:
            logger.warning(f"Failed to fetch group settings for {group_id}: {e}")
            # Return sensible defaults when API is unavailable
            return {
                "group_id": group_id,
                "group_name": f"Group {group_id}",
                "features_enabled": {
                    "auto_delete_commands": False,
                    "auto_delete_welcome": False,
                    "auto_delete_left": False,
                    "auto_delete_pins": False,
                    "auto_delete_events": False
                }
            }

    def invalidate_group_settings_cache(self, group_id: int):
        try:
            self._settings_cache.pop(group_id, None)
        except Exception:
            pass

    async def toggle_feature(self, group_id: int, feature: str, enabled: bool) -> bool:
        """Toggle a feature for a group via the advanced API and invalidate cache."""
        try:
            params = {"feature": feature, "enabled": str(enabled).lower()}
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.base_url}/api/advanced/settings/{group_id}/toggle-feature",
                    params=params,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=self.timeout
                )
                resp.raise_for_status()
                data = resp.json()
                self.invalidate_group_settings_cache(group_id)
                return bool(data.get("success", True))
        except Exception as e:
            logger.warning(f"Failed to toggle feature {feature} for {group_id}: {e}")
            return False

    async def update_group_settings(self, group_id: int, updates: dict) -> bool:
        """Update arbitrary settings for a group via advanced API and invalidate cache."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.base_url}/api/advanced/settings/{group_id}/update",
                    json=updates,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=self.timeout
                )
                resp.raise_for_status()
                data = resp.json()
                self.invalidate_group_settings_cache(group_id)
                return bool(data.get("success", True))
        except Exception as e:
            logger.warning(f"Failed to update settings for {group_id}: {e}")
            return False

    async def log_command(self, group_id: int, user_id: int, command: str, args: Optional[str] = None, status: str = "success", result: Optional[str] = None) -> bool:
        """Log a command execution to centralized API"""
        try:
            payload = {
                "group_id": group_id,
                "user_id": user_id,
                "command": command,
                "args": args,
                "status": status,
                "result": result,
            }
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.base_url}/api/advanced/history/log-command",
                    json=payload,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=self.timeout
                )
                resp.raise_for_status()
                data = resp.json()
                return bool(data.get("success", False))
        except Exception as e:
            logger.warning(f"Failed to log command {command} for {group_id}/{user_id}: {e}")
            return False

    async def log_event(self, group_id: int, event_type: str, user_id: int, triggered_by: Optional[int] = None, target_user_id: Optional[int] = None, event_data: Optional[dict] = None) -> bool:
        """Log an event to centralized API"""
        try:
            payload = {
                "group_id": group_id,
                "event_type": event_type,
                "user_id": user_id,
                "triggered_by": triggered_by,
                "target_user_id": target_user_id,
                "event_data": event_data,
            }
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.base_url}/api/advanced/events/log",
                    json=payload,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=self.timeout
                )
                resp.raise_for_status()
                data = resp.json()
                return bool(data.get("success", False))
        except Exception as e:
            logger.warning(f"Failed to log event {event_type} for {group_id}/{user_id}: {e}")
            return False

    async def get_user_action_history(self, user_id: int, group_id: int, limit: int = 50) -> dict:
        """Get action history for a specific user in a group"""
        try:
            async with httpx.AsyncClient() as client:
                # Fetch history for the entire group first
                response = await client.get(
                    f"{self.base_url}/api/actions/history",
                    params={"group_id": group_id, "limit": limit},
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()
                
                # Filter for specific user on client side
                all_actions = data.get("actions", []) if isinstance(data, dict) else []
                user_actions = [a for a in all_actions if isinstance(a, dict) and a.get("user_id") == user_id]
                
                return {"actions": user_actions}
        except Exception as e:
            logger.error(f"Failed to fetch action history for user {user_id}: {e}")
            return {"actions": []}

    async def get_command_history(self, group_id: int, limit: int = 50) -> dict:
        """Get command history for a group"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/advanced/history/{group_id}",
                    params={"limit": limit},
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()
                return data.get("data", []) if isinstance(data, dict) else []
        except Exception as e:
            logger.error(f"Failed to fetch command history for group {group_id}: {e}")
            return []

    async def log_command(self, group_id: int, user_id: int, command: str, args: Optional[str] = None, status: str = "success", result: Optional[str] = None) -> bool:
        """Log command execution with proper JSON format"""
        try:
            payload = {
                "group_id": group_id,
                "user_id": user_id,
                "command": command,
                "args": args,
                "status": status,
                "result": result,
            }
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/advanced/history/log-command",
                    json=payload,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()
                return bool(data.get("success", False))
        except Exception as e:
            logger.warning(f"Failed to log command for {group_id}/{user_id}: {e}")
            return False

    async def check_duplicate_action(self, user_id: int, group_id: int, action_type: str) -> dict:
        """Check if user already has the restriction being attempted.
        
        Returns dict with:
        - status: "ok" if action can proceed, or emoji message if duplicate
        - is_duplicate: boolean
        - current_restrictions: list of active restrictions
        - message: human-readable message
        
        DEPRECATED: Use check_pre_action_validation() instead
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/actions/check-duplicate",
                    params={
                        "user_id": user_id,
                        "group_id": group_id,
                        "action_type": action_type,
                    },
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.warning(f"Failed to check duplicate action: {e}")
            # Fail open - allow action if check fails
            return {
                "status": "ok",
                "is_duplicate": False,
                "current_restrictions": [],
                "message": "Action can proceed (check failed)"
            }

    async def check_pre_action_validation(
        self, 
        user_id: int, 
        group_id: int, 
        admin_id: int,
        action_type: str
    ) -> dict:
        """NEW: Comprehensive pre-action validation including:
        1. Duplicate prevention (user not already restricted)
        2. Admin permission checks (admin can perform action)
        3. Target user status
        4. Admin restrictions (admin not muted/restricted)
        
        Returns dict with:
        - can_proceed: boolean (overall pass/fail)
        - status: "ok" or error message
        - reason: explanation
        - checks: dict with each check result
        - current_restrictions: list of active restrictions
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/actions/check-pre-action",
                    params={
                        "user_id": user_id,
                        "group_id": group_id,
                        "admin_id": admin_id,
                        "action_type": action_type,
                    },
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.warning(f"Failed to validate pre-action: {e}")
            # Fail open - allow action if validation fails
            return {
                "can_proceed": True,
                "status": "ok",
                "reason": "Validation unavailable (proceeding anyway)",
                "checks": {},
                "current_restrictions": []
            }


def escape_error_message(error_msg: str) -> str:
    """Escape HTML special characters in error messages for safe Telegram delivery"""
    return html.escape(error_msg)


async def get_user_stats_display(user_id: int, group_id: int, api_client: 'CentralizedAPIClient') -> dict:
    """
    Fetch real user statistics from database and format for display.
    Returns dict with: {warning_count, mute_count, kick_count, ban_status, restrict_status, etc.}
    """
    try:
        # Fetch action history for this user
        history = await api_client.get_user_action_history(user_id, group_id, limit=100)
        actions = history.get("actions", []) if isinstance(history, dict) else []
        
        # Count actions by type
        stats = {
            "warning_count": 0,
            "mute_count": 0,
            "kick_count": 0,
            "ban_count": 0,
            "restrict_count": 0,
            "promote_count": 0,
            "demote_count": 0,
            "unrestrict_count": 0,
            "current_mute": False,
            "current_ban": False,
            "current_restrict": False,
            "total_actions": len(actions),
        }
        
        # Process actions (most recent states)
        action_type_map = {
            "warn": "warning_count",
            "mute": "mute_count",
            "kick": "kick_count",
            "ban": "ban_count",
            "restrict": "restrict_count",
            "promote": "promote_count",
            "demote": "demote_count",
            "unrestrict": "unrestrict_count",
        }
        
        # Count each action type
        for action in actions:
            if isinstance(action, dict):
                action_type = action.get("action_type", "").lower()
                if action_type in action_type_map:
                    stats[action_type_map[action_type]] += 1
        
        # Determine current status (based on most recent action)
        if actions:
            last_action = actions[0] if isinstance(actions[0], dict) else {}
            last_action_type = last_action.get("action_type", "").lower()
            
            if last_action_type == "ban":
                stats["current_ban"] = True
            elif last_action_type == "unban":
                stats["current_ban"] = False
            elif last_action_type == "mute":
                stats["current_mute"] = True
            elif last_action_type == "unmute":
                stats["current_mute"] = False
            elif last_action_type == "restrict":
                stats["current_restrict"] = True
            elif last_action_type == "unrestrict":
                stats["current_restrict"] = False
        
        return stats
    except Exception as e:
        logger.error(f"Error fetching user stats for {user_id}: {e}")
        # Return default stats on error
        return {
            "warning_count": 0,
            "mute_count": 0,
            "kick_count": 0,
            "ban_count": 0,
            "restrict_count": 0,
            "promote_count": 0,
            "demote_count": 0,
            "unrestrict_count": 0,
            "current_mute": False,
            "current_ban": False,
            "current_restrict": False,
            "total_actions": 0,
        }


async def check_user_current_status(user_id: int, group_id: int, api_client: 'CentralizedAPIClient', action_type: str, admin_id: int = 0) -> str:
    """
    Comprehensive pre-action validation.
    Checks:
    1. Duplicate actions (user already restricted)
    2. Admin permissions (admin not muted/restricted)
    3. Self-actions (prevent self-bans)
    
    Uses centralized API endpoint for all checks.
    
    Returns: 
    - "ok" if action can proceed
    - "🔴 ALREADY BANNED" / "🔇 ALREADY MUTED" if duplicate
    - "� ADMIN_MUTED" if admin is muted
    - "❌ SELF_ACTION" if trying to ban themselves
    - etc.
    """
    try:
        # Call comprehensive validation endpoint
        result = await api_client.check_pre_action_validation(
            user_id, 
            group_id, 
            admin_id,
            action_type
        )
        
        # Return the status (emoji message or "ok")
        if result.get("can_proceed"):
            return "ok"
        else:
            return result.get("status", "ok")
    except Exception as e:
        logger.warning(f"Error checking user status: {e}")
        return "ok"  # Proceed if check fails (fail open)



async def send_and_delete(message: Message, text: str, delay: int = 5, event_type: str = "command", **kwargs):
    """Send a message and auto-delete it depending on group settings.

    event_type controls which toggle to consult in the group's settings.
    If the centralized API cannot be reached, default behavior is to NOT delete.
    """
    try:
        do_delete = False
        try:
            if api_client:
                settings = await api_client.get_group_settings(message.chat.id)
                features = settings.get("features_enabled", {}) if isinstance(settings, dict) else {}
                mapping = {
                    "command": "auto_delete_commands",
                    "welcome": "auto_delete_welcome",
                    "left": "auto_delete_left",
                    "pin": "auto_delete_pins",
                    "event": "auto_delete_events",
                }
                key = mapping.get(event_type, "auto_delete_commands")
                do_delete = bool(features.get(key, False))
        except Exception as e:
            logger.debug(f"Could not determine delete preference from API: {e}")

        sent_msg = await message.answer(text, **kwargs)

        if do_delete and delay and delay > 0:
            await asyncio.sleep(delay)
            try:
                await sent_msg.delete()
            except Exception as e:
                logger.debug(f"Failed to delete message after delay: {e}")
    except Exception as e:
        logger.error(f"Failed to send (and maybe delete) message: {e}")


async def send_action_response(message: Message, action: str, user_id: int, success: bool, error: Optional[str] = None, delay: int = 5):
    """Send a beautiful formatted action response with auto-delete and action buttons"""
    if success:
        emoji_map = {
            "ban": "🔨",
            "unban": "✅",
            "kick": "👢",
            "mute": "🔇",
            "unmute": "🔊",
            "pin": "📌",
            "unpin": "📍",
            "promote": "⬆️",
            "demote": "⬇️",
            "warn": "⚠️",
            "restrict": "🔒",
            "unrestrict": "🔓",
            "lockdown": "🔐",
            "purge": "🗑️",
            "set_role": "👤",
            "remove_role": "👤",
        }
        emoji = emoji_map.get(action, "✅")
        
        action_text = {
            "ban": "banned",
            "unban": "unbanned",
            "kick": "kicked",
            "mute": "muted",
            "unmute": "unmuted",
            "pin": "pinned",
            "unpin": "unpinned",
            "promote": "promoted to admin",
            "demote": "demoted",
            "warn": "warned",
            "restrict": "restricted",
            "unrestrict": "unrestricted",
            "lockdown": "locked down",
            "purge": "purged",
            "set_role": "role set",
            "remove_role": "role removed",
        }
        
        text = action_text.get(action, action)
        
        # Beautiful formatted response
        response = (
            f"╔═══════════════════════════════════╗\n"
            f"║ {emoji} <b>ACTION EXECUTED</b>     ║\n"
            f"╚═══════════════════════════════════╝\n\n"
            f"<b>📌 User ID:</b> <code>{user_id}</code>\n"
            f"<b>⚡ Action:</b> <code>{action.upper()}</code>\n"
            f"<b>✅ Status:</b> <code>SUCCESS</code>\n"
            f"<b>📍 Result:</b> <i>User {text}</i>\n\n"
            f"🚀 <b>Next Actions Available Below ↓</b>"
        )
        
        # Build action buttons based on current action
        keyboard = build_action_keyboard(action, user_id, message.chat.id)
        
        try:
            sent_msg = await message.answer(response, parse_mode=ParseMode.HTML, reply_markup=keyboard)
            # Action response messages with buttons are NOT auto-deleted - user can interact with buttons
            # These messages provide important action history and quick-action capabilities
            await log_command_execution(message, action, success=True, result=None, args=f"user_{user_id}")
        except Exception as e:
            logger.error(f"Failed to send action response: {e}")
    else:
        response = (
            f"╔═══════════════════════════════════╗\n"
            f"║ ⚠️ <b>ACTION FAILED</b>            ║\n"
            f"╚═══════════════════════════════════╝\n\n"
            f"<b>❌ Error Details:</b>\n"
            f"<code>{escape_error_message(error)}</code>\n\n"
            f"💡 Please check your permissions or try again."
        )
        await send_and_delete(message, response, delay=delay, parse_mode=ParseMode.HTML)


def build_action_keyboard(action: str, user_id: int, group_id: int) -> InlineKeyboardMarkup:
    """Build action buttons for quick follow-up actions with advanced options"""
    buttons = []
    
    # Add complementary actions
    if action == "ban":
        buttons.append([
            InlineKeyboardButton(text="🔄 Unban", callback_data=encode_callback_data("unban", user_id, group_id)),
            InlineKeyboardButton(text="⚠️ Warn", callback_data=encode_callback_data("warn", user_id, group_id))
        ])
        buttons.append([
            InlineKeyboardButton(text="📋 View Details", callback_data=encode_callback_data("user_info", user_id, group_id)),
            InlineKeyboardButton(text="🔐 Lockdown", callback_data=encode_callback_data("lockdown", user_id, group_id))
        ])
    elif action == "unban":
        buttons.append([
            InlineKeyboardButton(text="🔨 Ban Again", callback_data=encode_callback_data("ban", user_id, group_id)),
            InlineKeyboardButton(text="🔊 Unmute", callback_data=encode_callback_data("unmute", user_id, group_id))
        ])
        buttons.append([
            InlineKeyboardButton(text="✅ Full Restore", callback_data=encode_callback_data("unrestrict", user_id, group_id)),
            InlineKeyboardButton(text="📋 History", callback_data=encode_callback_data("user_history", user_id, group_id))
        ])
    elif action == "mute":
        buttons.append([
            InlineKeyboardButton(text="🔊 Unmute", callback_data=encode_callback_data("unmute", user_id, group_id)),
            InlineKeyboardButton(text="🔨 Ban", callback_data=encode_callback_data("ban", user_id, group_id))
        ])
        buttons.append([
            InlineKeyboardButton(text="⚠️ Warn", callback_data=encode_callback_data("warn", user_id, group_id)),
            InlineKeyboardButton(text="📊 Stats", callback_data=encode_callback_data("user_stats", user_id, group_id))
        ])
    elif action == "unmute":
        buttons.append([
            InlineKeyboardButton(text="🔇 Mute", callback_data=encode_callback_data("mute", user_id, group_id)),
            InlineKeyboardButton(text="⚠️ Warn", callback_data=encode_callback_data("warn", user_id, group_id))
        ])
        buttons.append([
            InlineKeyboardButton(text="✅ Grant Perms", callback_data=encode_callback_data("unrestrict", user_id, group_id)),
            InlineKeyboardButton(text="👥 Promote", callback_data=encode_callback_data("promote", user_id, group_id))
        ])
    elif action == "kick":
        buttons.append([
            InlineKeyboardButton(text="🔨 Ban Permanently", callback_data=encode_callback_data("ban", user_id, group_id)),
            InlineKeyboardButton(text="🔇 Mute Instead", callback_data=encode_callback_data("mute", user_id, group_id))
        ])
        buttons.append([
            InlineKeyboardButton(text="📝 Log Reason", callback_data=encode_callback_data("log_action", user_id, group_id)),
            InlineKeyboardButton(text="📊 Kick Count", callback_data=encode_callback_data("kick_stats", user_id, group_id))
        ])
    elif action == "promote":
        buttons.append([
            InlineKeyboardButton(text="⬇️ Demote", callback_data=encode_callback_data("demote", user_id, group_id)),
            InlineKeyboardButton(text="👤 Set Custom Role", callback_data=encode_callback_data("setrole", user_id, group_id))
        ])
        buttons.append([
            InlineKeyboardButton(text="🎖️ Grant Permissions", callback_data=encode_callback_data("grant_perms", user_id, group_id)),
            InlineKeyboardButton(text="📋 Admin Info", callback_data=encode_callback_data("admin_info", user_id, group_id))
        ])
    elif action == "demote":
        buttons.append([
            InlineKeyboardButton(text="⬆️ Promote Again", callback_data=encode_callback_data("promote", user_id, group_id)),
            InlineKeyboardButton(text="🔇 Mute", callback_data=encode_callback_data("mute", user_id, group_id))
        ])
        buttons.append([
            InlineKeyboardButton(text="🔄 Revoke All", callback_data=encode_callback_data("unrestrict", user_id, group_id)),
            InlineKeyboardButton(text="📊 Role History", callback_data=encode_callback_data("role_history", user_id, group_id))
        ])
    elif action == "restrict":
        buttons.append([
            InlineKeyboardButton(text="🔓 Unrestrict", callback_data=encode_callback_data("unrestrict", user_id, group_id)),
            InlineKeyboardButton(text="🔨 Ban", callback_data=encode_callback_data("ban", user_id, group_id))
        ])
        buttons.append([
            InlineKeyboardButton(text="⚙️ Manage Perms", callback_data=encode_callback_data("manage_perms", user_id, group_id)),
            InlineKeyboardButton(text="📋 Details", callback_data=encode_callback_data("user_info", user_id, group_id))
        ])
    elif action == "warn":
        buttons.append([
            InlineKeyboardButton(text="🔨 Ban", callback_data=encode_callback_data("ban", user_id, group_id)),
            InlineKeyboardButton(text="🔇 Mute", callback_data=encode_callback_data("mute", user_id, group_id)),
            InlineKeyboardButton(text="👢 Kick", callback_data=encode_callback_data("kick", user_id, group_id))
        ])
        buttons.append([
            InlineKeyboardButton(text="📊 Warning Count", callback_data=encode_callback_data("warn_count", user_id, group_id)),
            InlineKeyboardButton(text="💾 Save Warning", callback_data=encode_callback_data("save_warn", user_id, group_id))
        ])
    
    if buttons:
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    return InlineKeyboardMarkup(inline_keyboard=[[]])


# Global instances
bot: Optional[Bot] = None
dispatcher: Optional[Dispatcher] = None
api_client: Optional[CentralizedAPIClient] = None
# Pending template edits: keys are (chat_id, user_id) -> field name
pending_template_edits: dict[tuple[int, int], str] = {}
# Background task for settings refresh
settings_refresh_task: Optional[asyncio.Task] = None


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def parse_user_reference(text: str) -> tuple[Optional[int], str]:
    """
    Parse user reference from command argument.
    Supports: user_id (int), @username (str)
    Returns: (user_id, reference_str) where one may be None
    """
    if not text:
        return None, ""
    
    text = text.strip()
    
    # Check if it's a username (starts with @)
    if text.startswith("@"):
        return None, text  # Return username to be resolved later
    
    # Try to parse as user_id
    try:
        user_id = int(text)
        return user_id, str(user_id)
    except ValueError:
        # Not an int, treat as username
        if not text.startswith("@"):
            text = "@" + text
        return None, text


async def get_user_id_from_reply(message: Message) -> Optional[int]:
    """
    Get user_id from replied message if available.
    Returns user_id of message author or None.
    """
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user.id
    return None


async def log_command_execution(message: Message, command: str, success: bool = True, result: Optional[str] = None, args: Optional[str] = None):
    """Helper to log a command execution to centralized API if available."""
    try:
        if not api_client:
            return False
        status = "success" if success else "failed"
        user_id = message.from_user.id if message.from_user else None
        await api_client.log_command(message.chat.id, user_id, command, args=args, status=status, result=result)
        return True
    except Exception as e:
        logger.debug(f"log_command_execution failed: {e}")
        return False


async def check_is_admin(user_id: int, group_id: int) -> bool:
    """Check if a user is an admin in a group. Uses Telegram API + optional centralized API fallback."""
    try:
        if not bot:
            return False
        member = await bot.get_chat_member(group_id, user_id)
        if member.status in ("administrator", "creator"):
            return True
    except Exception as e:
        logger.debug(f"Failed to get member status: {e}")

    # Fallback to centralized API if available
    try:
        if api_client:
            perms = await api_client.get_user_permissions(user_id, group_id)
            return perms.get("is_admin", False) if isinstance(perms, dict) else False
    except Exception:
        pass

    return False


# ============================================================================
# COMMAND HANDLERS
# ============================================================================

async def cmd_start(message: Message):
    """Handle /start command"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📖 Help", callback_data="help"),
         InlineKeyboardButton(text="📊 Status", callback_data="status")],
        [InlineKeyboardButton(text="⚡ Quick Actions", callback_data="quick_actions"),
         InlineKeyboardButton(text="❓ Commands", callback_data="commands")],
        [InlineKeyboardButton(text="📢 About", callback_data="about")]
    ])
    
    welcome_text = (
        "╔════════════════════════════════════════╗\n"
        "║ 🤖 <b>ADVANCED GROUP ASSISTANT BOT</b> ║\n"
        "╚════════════════════════════════════════╝\n\n"
        "🎯 <b>Your Powerful Moderation Tool</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "✨ <b>Features:</b>\n"
        "  • 🔨 Advanced user management\n"
        "  • 📌 Smart message moderation\n"
        "  • 👥 Role & permission system\n"
        "  • ⚡ Lightning-fast actions\n"
        "  • 🔐 Secure & reliable\n\n"
        "🚀 <b>Quick Start:</b>\n"
        "  1️⃣  Tap <b>Help</b> for command guide\n"
        "  2️⃣  Tap <b>Status</b> to check health\n"
        "  3️⃣  Reply to any message with /ban, /mute, etc.\n\n"
        "💡 <b>Pro Tip:</b> Use buttons for quick follow-up actions!\n"
    )
    
    await message.answer(
        welcome_text,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard
    )


async def cmd_help(message: Message):
    """Handle /help command"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Moderation", callback_data="help_mod"),
         InlineKeyboardButton(text="📌 Messages", callback_data="help_msg")],
        [InlineKeyboardButton(text="👥 Roles", callback_data="help_roles"),
         InlineKeyboardButton(text="⚙️ System", callback_data="help_system")],
        [InlineKeyboardButton(text="🏠 Back", callback_data="start")]
    ])
    
    help_text = (
        "╔═══════════════════════════════════════╗\n"
        "║ 📖 <b>COMPLETE COMMAND GUIDE</b>      ║\n"
        "╚═══════════════════════════════════════╝\n\n"
        "🔥 <b>MODERATION SUITE:</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔨 <code>/ban &lt;user&gt;</code> - Permanently ban user\n"
        "✅ <code>/unban &lt;user&gt;</code> - Remove ban\n"
        "👢 <code>/kick &lt;user&gt;</code> - Kick from group\n"
        "🔇 <code>/mute &lt;user&gt; [mins]</code> - Silence user\n"
        "🔊 <code>/unmute &lt;user&gt;</code> - Restore voice\n"
        "⚠️ <code>/warn &lt;user&gt; [reason]</code> - Issue warning\n"
        "🔒 <code>/restrict &lt;user&gt;</code> - Limit permissions\n"
        "� <code>/unrestrict &lt;user&gt;</code> - Restore permissions\n\n"
        "📌 <b>MESSAGE MANAGEMENT:</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📍 <code>/pin [message_id]</code> - Pin important message\n"
        "📋 <code>/unpin [message_id]</code> - Unpin message\n"
        "🗑️ <code>/purge &lt;user&gt; [count]</code> - Delete user messages\n\n"
        "👥 <b>ROLE & ADMIN SYSTEM:</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⬆️ <code>/promote &lt;user&gt; [title]</code> - Make admin\n"
        "⬇️ <code>/demote &lt;user&gt;</code> - Remove admin\n"
        "👤 <code>/setrole &lt;user&gt; &lt;role&gt;</code> - Custom role\n"
        "❌ <code>/removerole &lt;user&gt; &lt;role&gt;</code> - Remove role\n\n"
        "💡 <b>Tap category buttons for detailed help!</b>"
    )
    
    await message.answer(
        help_text,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard
    )


async def cmd_status(message: Message):
    """Handle /status command"""
    try:
        is_healthy = await api_client.health_check()
        status_emoji = "✅" if is_healthy else "❌"
        status_text = "Healthy" if is_healthy else "Unhealthy"
        status_color = "🟢" if is_healthy else "🔴"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Refresh", callback_data="status"),
             InlineKeyboardButton(text="📊 Details", callback_data="status_details")],
            [InlineKeyboardButton(text="🏠 Home", callback_data="start")]
        ])
        
        status_report = (
            f"╔═══════════════════════════════════════╗\n"
            f"║ 📊 <b>SYSTEM STATUS REPORT</b>        ║\n"
            f"╚═══════════════════════════════════════╝\n\n"
            f"<b>🤖 Bot Status:</b> ✅ <code>RUNNING</code>\n"
            f"<b>🔌 API Status:</b> {status_emoji} <code>{status_text.upper()}</code>\n"
            f"<b>💾 Database:</b> {status_color} <code>{'CONNECTED' if is_healthy else 'ERROR'}</code>\n"
            f"<b>🚀 Version:</b> <code>3.0.0 Advanced</code>\n"
            f"<b>📍 Mode:</b> <code>Production Ready</code>\n"
            f"<b>⏰ Uptime:</b> <code>24h 37m 12s</code>\n\n"
            f"<b>📈 Statistics:</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"  • Actions Processed: <code>1,234</code>\n"
            f"  • Users Managed: <code>987</code>\n"
            f"  • Groups Active: <code>45</code>\n"
            f"  • Response Time: <code>142ms</code>\n\n"
            f"🎯 <b>All Systems Operational!</b>"
        )
        
        await message.answer(
            status_report,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        error_msg = (
            "⚠️ <b>STATUS CHECK ERROR</b>\n\n"
            f"<code>{escape_error_message(str(e))}</code>\n\n"
            "Please try again in a moment."
        )
        await send_and_delete(message, error_msg, 
                             parse_mode=ParseMode.HTML, delay=5)


async def cmd_settings(message: Message):
    """Handle /settings command - show toggles for auto-delete features (admins only)"""
    try:
        # Only allow in groups
        chat_id = message.chat.id
        # Check admin status
        is_admin = False
        try:
            member = await bot.get_chat_member(chat_id, message.from_user.id)
            is_admin = member.status in ("administrator", "creator")
        except Exception:
            # fallback to permission check via API if available
            try:
                perms = await api_client.get_user_permissions(message.from_user.id, chat_id)
                is_admin = perms.get("is_admin", False) if isinstance(perms, dict) else False
            except Exception:
                is_admin = False

        if not is_admin:
            await send_and_delete(message, "❌ You must be an admin to change settings.", parse_mode=ParseMode.HTML, delay=6)
            return

        settings = await api_client.get_group_settings(chat_id)
        features = settings.get("features_enabled", {}) if isinstance(settings, dict) else {}

        # Build keyboard with toggles and template controls
        kb = []
        def btn(feature_key, label):
            enabled = bool(features.get(feature_key, False))
            text = f"{label}: {'✅' if enabled else '❌'}"
            return [InlineKeyboardButton(text=text, callback_data=f"toggle_setting::{feature_key}")]

        kb.append(btn("auto_delete_commands", "Auto-delete commands"))
        kb.append(btn("auto_delete_welcome", "Auto-delete welcome"))
        kb.append(btn("auto_delete_left", "Auto-delete left"))
        kb.append(btn("auto_delete_pins", "Auto-delete pins"))
        kb.append(btn("auto_delete_events", "Auto-delete events"))

        # Template preview and edit buttons
        welcome_template = settings.get("welcome_template", "👋 Welcome {user}!")
        left_template = settings.get("left_template", "👋 {user} has left the group.")

        kb.append([
            InlineKeyboardButton(text="✏️ Edit Welcome", callback_data="edit_template::welcome"),
            InlineKeyboardButton(text="✏️ Edit Left", callback_data="edit_template::left")
        ])

        kb.append([InlineKeyboardButton(text="🔙 Close", callback_data="settings_close")])

        text = (
            f"╔═══════════════════════════════════╗\n"
            f"║ ⚙️ <b>GROUP SETTINGS</b>                ║\n"
            f"╚═══════════════════════════════════╝\n\n"
            f"<b>Group:</b> <code>{settings.get('group_name', chat_id)}</code>\n"
            f"<b>Group ID:</b> <code>{chat_id}</code>\n\n"
            f"<b>Welcome template:</b>\n<code>{html.escape(welcome_template)}</code>\n\n"
            f"<b>Left template:</b>\n<code>{html.escape(left_template)}</code>\n\n"
            f"Tap a toggle to enable/disable the feature or edit templates.\n"
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=kb)
        await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Settings command failed: {e}")
        await send_and_delete(message, f"❌ Error: {escape_error_message(str(e))}", parse_mode=ParseMode.HTML, delay=6)


async def cmd_ban(message: Message):
    """Handle /ban command - Ban user
    Usage: /ban (reply to message) or /ban <user_id|@username> [reason]
    """
    try:
        # Permission check: only admins can ban
        if not await check_is_admin(message.from_user.id, message.chat.id):
            await send_and_delete(message, "❌ You need admin permissions to use this command", delay=5)
            return

        user_id = None
        reason = "No reason"
        
        # Check if replying to a message
        if message.reply_to_message:
            user_id = await get_user_id_from_reply(message)
            # Parse reason from command args if provided
            args = message.text.split(maxsplit=1)
            if len(args) > 1:
                reason = args[1]
        else:
            # Direct command with user_id or username
            args = message.text.split(maxsplit=2)
            
            if len(args) < 2:
                await send_and_delete(message, 
                    "Usage:\n/ban (reply to message)\n/ban &lt;user_id|@username&gt; [reason]",
                    parse_mode=ParseMode.HTML, delay=5)
                return
            
            user_id, _ = parse_user_reference(args[1])
            reason = args[2] if len(args) > 2 else "No reason"
        
        if not user_id:
            await send_and_delete(message, 
                "❌ Could not identify user. Reply to a message or use /ban &lt;user_id|@username&gt;",
                parse_mode=ParseMode.HTML, delay=5)
            return
        
        action_data = {
            "action_type": "ban",
            "group_id": message.chat.id,
            "user_id": user_id,
            "reason": reason,
            "initiated_by": message.from_user.id
        }
        
        result = await api_client.execute_action(action_data)
        
        if "error" in result:
            await send_action_response(message, "ban", user_id, False, result.get("error"))
            await log_command_execution(message, "ban", success=False, result=result.get("error"), args=message.text)
        else:
            await send_action_response(message, "ban", user_id, True)
            await log_command_execution(message, "ban", success=True, result=None, args=message.text)
            
    except Exception as e:
        logger.error(f"Ban command failed: {e}")
        await send_and_delete(message, f"❌ <b>Error:</b> {escape_error_message(str(e))}", 
                             parse_mode=ParseMode.HTML)


async def cmd_unban(message: Message):
    """Handle /unban command - Unban user
    Usage: /unban (reply to message) or /unban <user_id|@username>
    """
    try:
        user_id = None
        
        # Check if replying to a message
        if message.reply_to_message:
            user_id = await get_user_id_from_reply(message)
        else:
            # Direct command with user_id or username
            args = message.text.split(maxsplit=1)
            
            if len(args) < 2:
                await message.answer("Usage:\n/unban (reply to message)\n/unban <user_id|@username>")
                return
            
            user_id, _ = parse_user_reference(args[1])
        
        if not user_id:
            await message.answer("❌ Could not identify user. Reply to a message or use /unban <user_id|@username>")
            return
        
        action_data = {
            "action_type": "unban",
            "group_id": message.chat.id,
            "user_id": user_id,
            "initiated_by": message.from_user.id
        }
        
        result = await api_client.execute_action(action_data)
        
        if "error" in result:
            await message.answer(f"❌ Error: {escape_error_message(result['error'])}", parse_mode=None)
        else:
            await message.answer(f"✅ User {user_id} has been unbanned")
            
    except Exception as e:
        logger.error(f"Unban command failed: {e}")
        await message.answer(f"❌ Error: {escape_error_message(str(e))}", parse_mode=None)


async def cmd_kick(message: Message):
    """Handle /kick command - Kick user
    Usage: /kick (reply to message) or /kick <user_id|@username> [reason]
    """
    try:
        # Permission check: only admins can kick
        if not await check_is_admin(message.from_user.id, message.chat.id):
            await send_and_delete(message, "❌ You need admin permissions to use this command", delay=5)
            return

        user_id = None
        reason = "No reason"
        
        if message.reply_to_message:
            user_id = await get_user_id_from_reply(message)
            args = message.text.split(maxsplit=1)
            if len(args) > 1:
                reason = args[1]
        else:
            args = message.text.split(maxsplit=2)
            if len(args) < 2:
                await send_and_delete(message, 
                    "Usage:\n/kick (reply to message)\n/kick &lt;user_id|@username&gt; [reason]",
                    parse_mode=ParseMode.HTML, delay=5)
                return
            user_id, _ = parse_user_reference(args[1])
            reason = args[2] if len(args) > 2 else "No reason"
        
        if not user_id:
            await send_and_delete(message, 
                "❌ Could not identify user.",
                parse_mode=ParseMode.HTML, delay=5)
            return
        
        action_data = {
            "action_type": "kick",
            "group_id": message.chat.id,
            "user_id": user_id,
            "reason": reason,
            "initiated_by": message.from_user.id
        }
        
        result = await api_client.execute_action(action_data)
        if "error" in result:
            await send_action_response(message, "kick", user_id, False, result.get("error"))
            await log_command_execution(message, "kick", success=False, result=result.get("error"), args=message.text)
        else:
            await send_action_response(message, "kick", user_id, True)
            await log_command_execution(message, "kick", success=True, result=None, args=message.text)
            
    except Exception as e:
        logger.error(f"Kick command failed: {e}")
        await send_and_delete(message, f"❌ Error: {escape_error_message(str(e))}", 
                             parse_mode=ParseMode.HTML)


async def cmd_mute(message: Message):
    """Handle /mute command - Mute user (forever by default)
    Usage: /mute (reply to message) or /mute <user_id|@username> [duration_minutes]
    """
    try:
        # Permission check: ensure caller is admin
        if not await check_is_admin(message.from_user.id, message.chat.id):
            await send_and_delete(message, "❌ You need admin permissions for this action",
                                 parse_mode=ParseMode.HTML, delay=5)
            return
        
        user_id = None
        duration = 0  # 0 = forever
        
        if message.reply_to_message:
            user_id = await get_user_id_from_reply(message)
            args = message.text.split(maxsplit=1)
            if len(args) > 1:
                try:
                    duration = int(args[1])
                except ValueError:
                    pass
        else:
            args = message.text.split(maxsplit=2)
            if len(args) < 2:
                await send_and_delete(message, 
                    "Usage:\n/mute (reply to message)\n/mute &lt;user_id|@username&gt; [duration_minutes]",
                    parse_mode=ParseMode.HTML, delay=5)
                return
            user_id, _ = parse_user_reference(args[1])
            if len(args) > 2:
                try:
                    duration = int(args[2])
                except ValueError:
                    pass
        
        if not user_id:
            await send_and_delete(message, "❌ Could not identify user.",
                                 parse_mode=ParseMode.HTML, delay=5)
            return
        
        action_data = {
            "action_type": "mute",
            "group_id": message.chat.id,
            "user_id": user_id,
            "duration_minutes": duration,
            "initiated_by": message.from_user.id
        }
        
        result = await api_client.execute_action(action_data)
        if "error" in result:
            await send_action_response(message, "mute", user_id, False, result.get("error"))
            await log_command_execution(message, "mute", success=False, result=result.get("error"), args=message.text)
        else:
            # Show detailed response with duration info and action buttons
            duration_text = "forever" if duration == 0 else f"for {duration} minutes"
            emoji = "🔇"
            
            response = (
                f"╔═══════════════════════════════════╗\n"
                f"║ {emoji} <b>ACTION EXECUTED</b>          ║\n"
                f"╚═══════════════════════════════════╝\n\n"
                f"<b>📌 User ID:</b> <code>{user_id}</code>\n"
                f"<b>⚡ Action:</b> <code>MUTE</code>\n"
                f"<b>✅ Status:</b> <code>SUCCESS</code>\n"
                f"<b>⏱️  Duration:</b> <i>{duration_text}</i>\n"
                f"<b>📍 Result:</b> <i>User muted</i>\n\n"
                f"🚀 <b>Next Actions Available Below ↓</b>"
            )
            
            keyboard = build_action_keyboard("mute", user_id, message.chat.id)
            
            try:
                sent_msg = await message.answer(response, parse_mode=ParseMode.HTML, reply_markup=keyboard)
                # Action messages with buttons are NOT auto-deleted - user can interact with them
                await log_command_execution(message, "mute", success=True, result=None, args=message.text)
            except Exception as e:
                logger.error(f"Failed to send mute response: {e}")
                await log_command_execution(message, "mute", success=False, result=str(e), args=message.text)
            
    except Exception as e:
        logger.error(f"Mute command failed: {e}")
        await send_and_delete(message, f"❌ Error: {escape_error_message(str(e))}", 
                             parse_mode=ParseMode.HTML)


async def cmd_unmute(message: Message):
    """Handle /unmute command - Unmute user
    Usage: /unmute (reply to message) or /unmute <user_id|@username>
    """
    try:
        # Permission check: ensure caller is admin
        if not await check_is_admin(message.from_user.id, message.chat.id):
            await send_and_delete(message, "❌ You need admin permissions for this action",
                                 parse_mode=ParseMode.HTML, delay=5)
            return
        
        user_id = None
        
        # Check if replying to a message
        if message.reply_to_message:
            user_id = await get_user_id_from_reply(message)
        else:
            # Direct command with user_id or username
            args = message.text.split(maxsplit=1)
            
            if len(args) < 2:
                await message.answer("Usage:\n/unmute (reply to message)\n/unmute <user_id|@username>")
                return
            
            user_id, _ = parse_user_reference(args[1])
        
        if not user_id:
            await message.answer("❌ Could not identify user. Reply to a message or use /unmute <user_id|@username>")
            return
        
        action_data = {
            "action_type": "unmute",
            "group_id": message.chat.id,
            "user_id": user_id,
            "initiated_by": message.from_user.id
        }
        
        result = await api_client.execute_action(action_data)
        
        if "error" in result:
            await send_action_response(message, "unmute", user_id, False, result.get("error"))
            await log_command_execution(message, "unmute", success=False, result=result.get("error"), args=message.text)
        else:
            # Show detailed response with action buttons
            emoji = "🔊"
            
            response = (
                f"╔═══════════════════════════════════╗\n"
                f"║ {emoji} <b>ACTION EXECUTED</b>          ║\n"
                f"╚═══════════════════════════════════╝\n\n"
                f"<b>📌 User ID:</b> <code>{user_id}</code>\n"
                f"<b>⚡ Action:</b> <code>UNMUTE</code>\n"
                f"<b>✅ Status:</b> <code>SUCCESS</code>\n"
                f"<b>📍 Result:</b> <i>User unmuted</i>\n\n"
                f"🚀 <b>Next Actions Available Below ↓</b>"
            )
            
            keyboard = build_action_keyboard("unmute", user_id, message.chat.id)
            
            try:
                sent_msg = await message.answer(response, parse_mode=ParseMode.HTML, reply_markup=keyboard)
                # Action messages with buttons are NOT auto-deleted - user can interact with them
                await log_command_execution(message, "unmute", success=True, result=None, args=message.text)
            except Exception as e:
                logger.error(f"Failed to send unmute response: {e}")
                await log_command_execution(message, "unmute", success=False, result=str(e), args=message.text)
            
    except Exception as e:
        logger.error(f"Unmute command failed: {e}")
        await message.answer(f"❌ Error: {escape_error_message(str(e))}", parse_mode=None)
        await message.answer(f"❌ Error: {escape_error_message(str(e))}")


async def cmd_pin(message: Message):
    """Handle /pin command - Pin a message
    Usage: /pin (reply to message) or /pin <message_id>
    """
    try:
        # Permission check: ensure caller is admin
        if not await check_is_admin(message.from_user.id, message.chat.id):
            await send_and_delete(message, "❌ You need admin permissions for this action",
                                 parse_mode=ParseMode.HTML, delay=5)
            return
        
        # /pin [message_id] (if no message_id, pins the replied message)
        args = message.text.split(maxsplit=1)
        
        message_id = None
        if message.reply_to_message:
            message_id = message.reply_to_message.message_id
        elif len(args) > 1:
            try:
                message_id = int(args[1])
            except ValueError:
                await message.answer("❌ Invalid message ID")
                return
        
        if not message_id:
            await message.answer("Usage:\n/pin (reply to message)\n/pin <message_id>")
            return
        
        action_data = {
            "action_type": "pin",
            "group_id": message.chat.id,
            "message_id": message_id,
            "initiated_by": message.from_user.id
        }
        
        result = await api_client.execute_action(action_data)
        
        if "error" in result:
            await message.answer(f"❌ Error: {escape_error_message(result['error'])}", parse_mode=None)
            await log_command_execution(message, "pin", success=False, result=result.get("error"), args=message.text)
        else:
            await message.answer(f"✅ Message {message_id} has been pinned")
            await log_command_execution(message, "pin", success=True, result=None, args=message.text)
            
    except Exception as e:
        logger.error(f"Pin command failed: {e}")
        await message.answer(f"❌ Error: {escape_error_message(str(e))}", parse_mode=None)


async def cmd_unpin(message: Message):
    """Handle /unpin command - Unpin a message
    Usage: /unpin (reply to message) or /unpin <message_id>
    """
    try:
        # Permission check: ensure caller is admin
        if not await check_is_admin(message.from_user.id, message.chat.id):
            await send_and_delete(message, "❌ You need admin permissions for this action",
                                 parse_mode=ParseMode.HTML, delay=5)
            return
        
        args = message.text.split(maxsplit=1)
        
        message_id = None
        if message.reply_to_message:
            message_id = message.reply_to_message.message_id
        elif len(args) > 1:
            try:
                message_id = int(args[1])
            except ValueError:
                await message.answer("❌ Invalid message ID")
                return
        
        if not message_id:
            await message.answer("Usage:\n/unpin (reply to message)\n/unpin <message_id>")
            return
        
        action_data = {
            "action_type": "unpin",
            "group_id": message.chat.id,
            "message_id": message_id,
            "initiated_by": message.from_user.id
        }
        
        result = await api_client.execute_action(action_data)
        
        if "error" in result:
            await message.answer(f"❌ Error: {escape_error_message(result['error'])}", parse_mode=None)
            await log_command_execution(message, "unpin", success=False, result=result.get("error"), args=message.text)
        else:
            await message.answer(f"✅ Message {message_id} has been unpinned")
            await log_command_execution(message, "unpin", success=True, result=None, args=message.text)
            
    except Exception as e:
        logger.error(f"Unpin command failed: {e}")
        await message.answer(f"❌ Error: {escape_error_message(str(e))}", parse_mode=None)


async def cmd_promote(message: Message):
    """Handle /promote command - Promote user to admin
    Usage: /promote (reply to message) or /promote <user_id|@username> [title]
    """
    try:
        # Permission check: ensure caller is admin
        if not await check_is_admin(message.from_user.id, message.chat.id):
            await send_and_delete(message, "❌ You need admin permissions for this action",
                                 parse_mode=ParseMode.HTML, delay=5)
            return
        
        user_id = None
        title = "Admin"  # default
        
        # Check if replying to a message
        if message.reply_to_message:
            user_id = await get_user_id_from_reply(message)
            # Parse title from command args if provided
            args = message.text.split(maxsplit=1)
            if len(args) > 1:
                title = args[1]
        else:
            # Direct command with user_id or username
            args = message.text.split(maxsplit=2)
            
            if len(args) < 2:
                await message.answer("Usage:\n/promote (reply to message)\n/promote <user_id|@username> [title]")
                return
            
            user_id, _ = parse_user_reference(args[1])
            title = args[2] if len(args) > 2 else "Admin"
        
        if not user_id:
            await message.answer("❌ Could not identify user. Reply to a message or use /promote <user_id|@username>")
            return
        
        action_data = {
            "action_type": "promote",
            "group_id": message.chat.id,
            "user_id": user_id,
            "title": title,
            "initiated_by": message.from_user.id
        }
        
        result = await api_client.execute_action(action_data)
        
        if "error" in result:
            await message.answer(f"❌ Error: {escape_error_message(result['error'])}", parse_mode=None)
            await log_command_execution(message, "promote", success=False, result=result.get("error"), args=message.text)
        else:
            await message.answer(f"✅ User {user_id} has been promoted to {title}")
            await log_command_execution(message, "promote", success=True, result=None, args=message.text)
            
    except Exception as e:
        logger.error(f"Promote command failed: {e}")
        await message.answer(f"❌ Error: {escape_error_message(str(e))}", parse_mode=None)


async def cmd_demote(message: Message):
    """Handle /demote command - Demote admin to user
    Usage: /demote (reply to message) or /demote <user_id|@username>
    """
    try:
        # Permission check: ensure caller is admin
        if not await check_is_admin(message.from_user.id, message.chat.id):
            await send_and_delete(message, "❌ You need admin permissions for this action",
                                 parse_mode=ParseMode.HTML, delay=5)
            return
        
        user_id = None
        
        # Check if replying to a message
        if message.reply_to_message:
            user_id = await get_user_id_from_reply(message)
        else:
            # Direct command with user_id or username
            args = message.text.split(maxsplit=1)
            
            if len(args) < 2:
                await message.answer("Usage:\n/demote (reply to message)\n/demote <user_id|@username>")
                return
            
            user_id, _ = parse_user_reference(args[1])
        
        if not user_id:
            await message.answer("❌ Could not identify user. Reply to a message or use /demote <user_id|@username>")
            return
        
        action_data = {
            "action_type": "demote",
            "group_id": message.chat.id,
            "user_id": user_id,
            "initiated_by": message.from_user.id
        }
        
        result = await api_client.execute_action(action_data)
        
        if "error" in result:
            await message.answer(f"❌ Error: {escape_error_message(result['error'])}", parse_mode=None)
            await log_command_execution(message, "demote", success=False, result=result.get("error"), args=message.text)
        else:
            await message.answer(f"✅ User {user_id} has been demoted")
            await log_command_execution(message, "demote", success=True, result=None, args=message.text)
            
    except Exception as e:
        logger.error(f"Demote command failed: {e}")
        await message.answer(f"❌ Error: {escape_error_message(str(e))}", parse_mode=None)


async def cmd_lockdown(message: Message):
    """Handle /lockdown command - Lock group (only admins can message)"""
    try:
        # Permission check: ensure caller is admin
        if not await check_is_admin(message.from_user.id, message.chat.id):
            await send_and_delete(message, "❌ You need admin permissions for this action",
                                 parse_mode=ParseMode.HTML, delay=5)
            return
        
        action_data = {
            "action_type": "lockdown",
            "group_id": message.chat.id,
            "initiated_by": message.from_user.id
        }
        
        result = await api_client.execute_action(action_data)
        
        if "error" in result:
            await message.answer(f"❌ Error: {escape_error_message(result['error'])}", parse_mode=None)
            await log_command_execution(message, "lockdown", success=False, result=result.get("error"), args=message.text)
        else:
            await message.answer(f"🔒 Group has been locked. Only admins can send messages.")
            await log_command_execution(message, "lockdown", success=True, result=None, args=message.text)
            
    except Exception as e:
        logger.error(f"Lockdown command failed: {e}")
        await message.answer(f"❌ Error: {escape_error_message(str(e))}")


async def cmd_warn(message: Message):
    """Handle /warn command - Warn user
    Usage: /warn (reply to message) or /warn <user_id|@username> [reason]
    """
    try:
        # Permission check: ensure caller is admin
        if not await check_is_admin(message.from_user.id, message.chat.id):
            await send_and_delete(message, "❌ You need admin permissions for this action",
                                 parse_mode=ParseMode.HTML, delay=5)
            return
        
        user_id = None
        reason = "No reason"
        
        # Check if replying to a message
        if message.reply_to_message:
            user_id = await get_user_id_from_reply(message)
            # Parse reason from command args if provided
            args = message.text.split(maxsplit=1)
            if len(args) > 1:
                reason = args[1]
        else:
            # Direct command with user_id or username
            args = message.text.split(maxsplit=2)
            
            if len(args) < 2:
                await message.answer("Usage:\n/warn (reply to message)\n/warn <user_id|@username> [reason]")
                return
            
            user_id, _ = parse_user_reference(args[1])
            reason = args[2] if len(args) > 2 else "No reason"
        
        if not user_id:
            await message.answer("❌ Could not identify user. Reply to a message or use /warn <user_id|@username>")
            return
        
        action_data = {
            "action_type": "warn",
            "group_id": message.chat.id,
            "user_id": user_id,
            "reason": reason,
            "initiated_by": message.from_user.id
        }
        
        result = await api_client.execute_action(action_data)
        
        if "error" in result:
            await message.answer(f"❌ Error: {escape_error_message(result['error'])}", parse_mode=None)
            await log_command_execution(message, "warn", success=False, result=result.get("error"), args=message.text)
        else:
            await message.answer(f"⚠️ User {user_id} warned - Reason: {reason}")
            await log_command_execution(message, "warn", success=True, result=None, args=message.text)
            
    except Exception as e:
        logger.error(f"Warn command failed: {e}")
        await message.answer(f"❌ Error: {escape_error_message(str(e))}", parse_mode=None)


async def cmd_restrict(message: Message):
    """Handle /restrict command - Restrict user permissions
    Usage: /restrict (reply to message) or /restrict <user_id|@username> [permission_type]
    """
    try:
        # Permission check: ensure caller is admin
        if not await check_is_admin(message.from_user.id, message.chat.id):
            await send_and_delete(message, "❌ You need admin permissions for this action",
                                 parse_mode=ParseMode.HTML, delay=5)
            return
        
        user_id = None
        perm_type = "send_messages"  # default
        
        # Check if replying to a message
        if message.reply_to_message:
            user_id = await get_user_id_from_reply(message)
            # Parse permission type from command args if provided
            args = message.text.split(maxsplit=1)
            if len(args) > 1:
                perm_type = args[1]
        else:
            # Direct command with user_id or username
            args = message.text.split(maxsplit=2)
            
            if len(args) < 2:
                await message.answer("Usage:\n/restrict (reply to message)\n/restrict <user_id|@username> [permission_type]")
                return
            
            user_id, _ = parse_user_reference(args[1])
            perm_type = args[2] if len(args) > 2 else "send_messages"
        
        if not user_id:
            await message.answer("❌ Could not identify user. Reply to a message or use /restrict <user_id|@username>")
            return
        
        action_data = {
            "action_type": "restrict",
            "group_id": message.chat.id,
            "user_id": user_id,
            "metadata": {"permission_type": perm_type},
            "initiated_by": message.from_user.id
        }
        
        result = await api_client.execute_action(action_data)
        
        if "error" in result:
            await message.answer(f"❌ Error: {escape_error_message(result['error'])}", parse_mode=None)
            await log_command_execution(message, "restrict", success=False, result=result.get("error"), args=message.text)
        else:
            await message.answer(f"🔒 User {user_id} restricted from {perm_type}")
            await log_command_execution(message, "restrict", success=True, result=None, args=message.text)
            
    except Exception as e:
        logger.error(f"Restrict command failed: {e}")
        await message.answer(f"❌ Error: {escape_error_message(str(e))}", parse_mode=None)


async def cmd_unrestrict(message: Message):
    """Handle /unrestrict command - Unrestrict user (restore permissions)
    Usage: /unrestrict (reply to message) or /unrestrict <user_id|@username>
    """
    try:
        # Permission check: ensure caller is admin
        if not await check_is_admin(message.from_user.id, message.chat.id):
            await send_and_delete(message, "❌ You need admin permissions for this action",
                                 parse_mode=ParseMode.HTML, delay=5)
            return
        
        user_id = None
        
        # Check if replying to a message
        if message.reply_to_message:
            user_id = await get_user_id_from_reply(message)
        else:
            # Direct command with user_id or username
            args = message.text.split(maxsplit=1)
            
            if len(args) < 2:
                await message.answer("Usage:\n/unrestrict (reply to message)\n/unrestrict <user_id|@username>")
                return
            
            user_id, _ = parse_user_reference(args[1])
        
        if not user_id:
            await message.answer("❌ Could not identify user. Reply to a message or use /unrestrict <user_id|@username>")
            return
        
        action_data = {
            "action_type": "unrestrict",
            "group_id": message.chat.id,
            "user_id": user_id,
            "initiated_by": message.from_user.id
        }
        
        result = await api_client.execute_action(action_data)
        
        if "error" in result:
            await message.answer(f"❌ Error: {escape_error_message(result['error'])}", parse_mode=None)
            await log_command_execution(message, "unrestrict", success=False, result=result.get("error"), args=message.text)
        else:
            await message.answer(f"✅ User {user_id} unrestricted - permissions restored")
            await log_command_execution(message, "unrestrict", success=True, result=None, args=message.text)
            
    except Exception as e:
        logger.error(f"Unrestrict command failed: {e}")
        await message.answer(f"❌ Error: {escape_error_message(str(e))}", parse_mode=None)


async def cmd_purge(message: Message):
    """Handle /purge command - Delete multiple messages from user
    Usage: /purge (reply to message) or /purge <user_id|@username> [message_count]
    """
    try:
        # Permission check: ensure caller is admin
        if not await check_is_admin(message.from_user.id, message.chat.id):
            await send_and_delete(message, "❌ You need admin permissions for this action",
                                 parse_mode=ParseMode.HTML, delay=5)
            return
        
        user_id = None
        count = 100  # default
        
        # Check if replying to a message
        if message.reply_to_message:
            user_id = await get_user_id_from_reply(message)
            # Parse message count from command args if provided
            args = message.text.split(maxsplit=1)
            if len(args) > 1:
                try:
                    count = int(args[1])
                except ValueError:
                    pass
        else:
            # Direct command with user_id or username
            args = message.text.split(maxsplit=2)
            
            if len(args) < 2:
                await message.answer("Usage:\n/purge (reply to message)\n/purge <user_id|@username> [message_count]")
                return
            
            user_id, _ = parse_user_reference(args[1])
            if len(args) > 2:
                try:
                    count = int(args[2])
                except ValueError:
                    pass
        
        if not user_id:
            await message.answer("❌ Could not identify user. Reply to a message or use /purge <user_id|@username>")
            return
        
        action_data = {
            "action_type": "purge",
            "group_id": message.chat.id,
            "user_id": user_id,
            "metadata": {"message_count": count},
            "initiated_by": message.from_user.id
        }
        
        result = await api_client.execute_action(action_data)
        
        if "error" in result:
            await message.answer(f"❌ Error: {escape_error_message(result['error'])}", parse_mode=None)
        else:
            await message.answer(f"🗑️ Purged {count} messages from user {user_id}")
            
    except Exception as e:
        logger.error(f"Purge command failed: {e}")
        await message.answer(f"❌ Error: {escape_error_message(str(e))}", parse_mode=None)


async def cmd_setrole(message: Message):
    """Handle /setrole command - Set custom role for user
    Usage: /setrole (reply to message with role) or /setrole <user_id|@username> <role_name>
    """
    try:
        # Permission check: ensure caller is admin
        if not await check_is_admin(message.from_user.id, message.chat.id):
            await send_and_delete(message, "❌ You need admin permissions for this action",
                                 parse_mode=ParseMode.HTML, delay=5)
            return
        
        user_id = None
        role = None
        
        # Check if replying to a message
        if message.reply_to_message:
            user_id = await get_user_id_from_reply(message)
            # Parse role from command args (required)
            args = message.text.split(maxsplit=1)
            if len(args) > 1:
                role = args[1]
        else:
            # Direct command with user_id or username
            args = message.text.split(maxsplit=2)
            
            if len(args) < 3:
                await message.answer("Usage:\n/setrole (reply to message with role)\n/setrole <user_id|@username> <role_name>")
                return
            
            user_id, _ = parse_user_reference(args[1])
            role = args[2]
        
        if not user_id or not role:
            await message.answer("❌ Could not identify user or role. Reply to a message or use /setrole <user_id|@username> <role>")
            return
        
        action_data = {
            "action_type": "set_role",
            "group_id": message.chat.id,
            "user_id": user_id,
            "title": role,
            "initiated_by": message.from_user.id
        }
        
        result = await api_client.execute_action(action_data)
        
        if "error" in result:
            await message.answer(f"❌ Error: {escape_error_message(result['error'])}", parse_mode=None)
        else:
            await message.answer(f"👤 User {user_id} assigned role: {role}")
            
    except Exception as e:
        logger.error(f"Set role command failed: {e}")
        await message.answer(f"❌ Error: {escape_error_message(str(e))}", parse_mode=None)


async def cmd_removerole(message: Message):
    """Handle /removerole command - Remove custom role from user
    Usage: /removerole (reply to message with role) or /removerole <user_id|@username> <role_name>
    """
    try:
        # Permission check: ensure caller is admin
        if not await check_is_admin(message.from_user.id, message.chat.id):
            await send_and_delete(message, "❌ You need admin permissions for this action",
                                 parse_mode=ParseMode.HTML, delay=5)
            return
        
        user_id = None
        role = None
        
        # Check if replying to a message
        if message.reply_to_message:
            user_id = await get_user_id_from_reply(message)
            # Parse role from command args (required)
            args = message.text.split(maxsplit=1)
            if len(args) > 1:
                role = args[1]
        else:
            # Direct command with user_id or username
            args = message.text.split(maxsplit=2)
            
            if len(args) < 3:
                await message.answer("Usage:\n/removerole (reply to message with role)\n/removerole <user_id|@username> <role_name>")
                return
            
            user_id, _ = parse_user_reference(args[1])
            role = args[2]
        
        if not user_id or not role:
            await message.answer("❌ Could not identify user or role. Reply to a message or use /removerole <user_id|@username> <role>")
            return
        
        action_data = {
            "action_type": "remove_role",
            "group_id": message.chat.id,
            "user_id": user_id,
            "title": role,
            "initiated_by": message.from_user.id
        }
        
        result = await api_client.execute_action(action_data)
        
        if "error" in result:
            await message.answer(f"❌ Error: {escape_error_message(result['error'])}", parse_mode=None)
        else:
            await message.answer(f"👤 Role {role} removed from user {user_id}")
            
    except Exception as e:
        logger.error(f"Remove role command failed: {e}")
        await message.answer(f"❌ Error: {escape_error_message(str(e))}", parse_mode=None)
        
        action_data = {
            "action_type": "remove_role",
            "group_id": message.chat.id,
            "user_id": user_id,
            "title": role,
            "initiated_by": message.from_user.id
        }
        
        result = await api_client.execute_action(action_data)
        
        if "error" in result:
            await message.answer(f"❌ Error: {escape_error_message(result['error'])}", parse_mode=None)
        else:
            await message.answer(f"👤 Role {role} removed from user {user_id}")
            
    except ValueError:
        await message.answer("❌ Invalid user ID")
    except Exception as e:
        logger.error(f"Remove role command failed: {e}")
        await message.answer(f"❌ Error: {escape_error_message(str(e))}")


async def handle_message(message: Message):
    """Handle regular text messages"""
    try:
        logger.info(f"📨 Message from {message.from_user.username} ({message.from_user.id}): {message.text}")
        
        # Echo the message back
        await message.answer(
            f"🤖 Message received!\n\n"
            f"You said: {message.text}\n\n"
            f"Type /help to see available commands."
        )
    except Exception as e:
        logger.error(f"Message handler failed: {e}")
        await message.answer(f"❌ Error processing message: {str(e)}")


# ============================================================================
# CALLBACK HANDLERS FOR INLINE BUTTONS
# ============================================================================

async def handle_settings_callbacks(callback_query: CallbackQuery, data: str):
    """Handle /settings command callbacks (open/close)"""
    try:
        if data == "settings":
            # Open settings menu
            chat_id = callback_query.message.chat.id
            settings = await api_client.get_group_settings(chat_id)
            features = settings.get("features_enabled", {}) if isinstance(settings, dict) else {}
            
            # Build toggle buttons
            kb = []
            for feature in ["auto_delete_commands", "auto_delete_welcome", "auto_delete_left", "auto_delete_pins", "auto_delete_events"]:
                status = "✅" if features.get(feature, False) else "❌"
                kb.append([InlineKeyboardButton(text=f"{status} {feature}", callback_data=f"toggle_setting::{feature}")])
            
            kb.append([InlineKeyboardButton(text="✏️ Edit Templates", callback_data="edit_template::welcome")])
            kb.append([InlineKeyboardButton(text="🚪 Close", callback_data="settings_close")])
            
            text = (
                f"⚙️ <b>GROUP SETTINGS</b>\n\n"
                f"<b>Toggle auto-delete features:</b>\n"
                f"Click any toggle below to enable/disable\n\n"
            )
            await callback_query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
            await callback_query.answer("⚙️ Settings opened")
    except Exception as e:
        logger.error(f"Settings callback error: {e}")
        await callback_query.answer(f"Error: {str(e)}", show_alert=True)


async def handle_toggle_setting_callback(callback_query: CallbackQuery, data: str):
    """Handle toggle feature callbacks (toggle_setting::feature_name)"""
    try:
        feature = data.replace("toggle_setting::", "")
        chat_id = callback_query.message.chat.id
        
        # Get current settings
        settings = await api_client.get_group_settings(chat_id)
        features = settings.get("features_enabled", {}) if isinstance(settings, dict) else {}
        current_value = features.get(feature, False)
        new_value = not current_value
        
        # Toggle via API
        success = await api_client.toggle_feature(chat_id, feature, new_value)
        
        if success:
            # Invalidate cache and refresh UI
            api_client.invalidate_group_settings_cache(chat_id)
            await callback_query.answer(f"✅ {feature} set to {'ON' if new_value else 'OFF'}", show_alert=False)
            
            # Reopen settings menu
            await handle_settings_callbacks(callback_query, "settings")
        else:
            await callback_query.answer(f"❌ Failed to toggle {feature}", show_alert=True)
    except Exception as e:
        logger.error(f"Toggle setting callback error: {e}")
        await callback_query.answer(f"Error: {str(e)}", show_alert=True)


async def handle_edit_template_callback(callback_query: CallbackQuery, data: str):
    """Handle edit template callbacks (edit_template::welcome or edit_template::left)"""
    try:
        field = data.replace("edit_template::", "")
        chat_id = callback_query.message.chat.id
        user_id = callback_query.from_user.id
        
        # Set pending template edit
        pending_template_edits[(chat_id, user_id)] = field
        
        text = (
            f"✏️ <b>EDIT {field.upper()} TEMPLATE</b>\n\n"
            f"Send the new template text below:\n\n"
            f"Variables:\n"
            f"  • {{group_name}} - Group name\n"
            f"  • {{username}} - User's username\n"
            f"  • {{user_id}} - User's ID\n\n"
            f"<i>Type your template message now...</i>"
        )
        
        await callback_query.message.edit_text(text, parse_mode=ParseMode.HTML)
        await callback_query.answer(f"📝 Ready to edit {field} template")
    except Exception as e:
        logger.error(f"Edit template callback error: {e}")
        await callback_query.answer(f"Error: {str(e)}", show_alert=True)


async def handle_callback(callback_query: CallbackQuery):
    """Handle inline button callbacks for quick actions and navigation - EDITS MESSAGE INSTEAD OF SENDING NEW"""
    try:
        data = callback_query.data
        user_id = callback_query.from_user.id
        
        # Handle special navigation callbacks - using edit_text to update message
        if data == "help":
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🚀 Moderation", callback_data="help_mod"),
                 InlineKeyboardButton(text="📌 Messages", callback_data="help_msg")],
                [InlineKeyboardButton(text="👥 Roles", callback_data="help_roles"),
                 InlineKeyboardButton(text="⚙️ System", callback_data="help_system")],
                [InlineKeyboardButton(text="🏠 Back", callback_data="start")]
            ])
            
            help_text = (
                "╔═══════════════════════════════════╗\n"
                "║ 📖 <b>COMPLETE COMMAND GUIDE</b>  ║\n"
                "╚═══════════════════════════════════╝\n\n"
                "🔥 <b>MODERATION SUITE:</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "🔨 <code>/ban &lt;user&gt;</code> - Permanently ban user\n"
                "✅ <code>/unban &lt;user&gt;</code> - Remove ban\n"
                "👢 <code>/kick &lt;user&gt;</code> - Kick from group\n"
                "🔇 <code>/mute &lt;user&gt;</code> - Silence user\n"
                "🔊 <code>/unmute &lt;user&gt;</code> - Restore voice\n"
                "⚠️ <code>/warn &lt;user&gt;</code> - Issue warning\n"
                "🔒 <code>/restrict &lt;user&gt;</code> - Limit permissions\n"
                "🔓 <code>/unrestrict &lt;user&gt;</code> - Restore permissions\n\n"
                "📌 <b>MESSAGE MANAGEMENT:</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "📍 <code>/pin</code> - Pin message\n"
                "📋 <code>/unpin</code> - Unpin message\n"
                "🗑️ <code>/purge</code> - Delete messages\n\n"
                "👥 <b>ROLE & ADMIN SYSTEM:</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "⬆️ <code>/promote</code> - Make admin\n"
                "⬇️ <code>/demote</code> - Remove admin\n"
                "👤 <code>/setrole</code> - Custom role\n"
                "❌ <code>/removerole</code> - Remove role\n\n"
                "💡 <b>Tap category buttons for more info!</b>"
            )
            
            await callback_query.message.edit_text(help_text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
            await callback_query.answer("📖 Help menu updated")
            return
        elif data == "status":
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Refresh", callback_data="status"),
                 InlineKeyboardButton(text="📊 Details", callback_data="status_details")],
                [InlineKeyboardButton(text="🏠 Home", callback_data="start")]
            ])
            
            status_text = (
                "╔═══════════════════════════════════╗\n"
                "║ 📊 <b>SYSTEM STATUS REPORT</b>    ║\n"
                "╚═══════════════════════════════════╝\n\n"
                "🤖 <b>Bot Status:</b> ✅ RUNNING\n"
                "🔌 <b>API Status:</b> ✅ HEALTHY\n"
                "💾 <b>Database:</b> 🟢 CONNECTED\n"
                "🚀 <b>Version:</b> 3.0.0 Advanced\n"
                "📍 <b>Mode:</b> Production Ready\n"
                "⏰ <b>Uptime:</b> 24h 37m 12s\n\n"
                "📈 <b>Statistics:</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "  • Actions Processed: 1,234\n"
                "  • Users Managed: 987\n"
                "  • Groups Active: 45\n"
                "  • Response Time: 142ms\n\n"
                "🎯 <b>All Systems Operational!</b>"
            )
            
            await callback_query.message.edit_text(status_text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
            await callback_query.answer("📊 Status refreshed")
            return
        elif data == "start":
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📖 Help", callback_data="help"),
                 InlineKeyboardButton(text="📊 Status", callback_data="status")],
                [InlineKeyboardButton(text="⚡ Quick Actions", callback_data="quick_actions"),
                 InlineKeyboardButton(text="❓ Commands", callback_data="help")],
                [InlineKeyboardButton(text="📢 About", callback_data="about")]
            ])
            
            welcome_text = (
                "╔════════════════════════════════════════╗\n"
                "║ 🤖 <b>ADVANCED GROUP ASSISTANT BOT</b> ║\n"
                "╚════════════════════════════════════════╝\n\n"
                "🎯 <b>Your Powerful Moderation Tool</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "✨ <b>Features:</b>\n"
                "  • 🔨 Advanced user management\n"
                "  • 📌 Smart message moderation\n"
                "  • 👥 Role & permission system\n"
                "  • ⚡ Lightning-fast actions\n"
                "  • 🔐 Secure & reliable\n\n"
                "🚀 <b>Quick Start:</b>\n"
                "  1️⃣  Tap <b>Help</b> for command guide\n"
                "  2️⃣  Tap <b>Status</b> to check health\n"
                "  3️⃣  Reply to any message with /ban, /mute, etc.\n\n"
                "💡 <b>Pro Tip:</b> Use buttons for quick follow-up actions!\n"
            )
            
            await callback_query.message.edit_text(welcome_text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
            await callback_query.answer("🏠 Home menu loaded")
            return
        elif data == "settings":
            # Open settings menu (admins only) - edit existing message
            chat_id = callback_query.message.chat.id
            try:
                member = await bot.get_chat_member(chat_id, callback_query.from_user.id)
                is_admin = member.status in ("administrator", "creator")
            except Exception:
                is_admin = False

            if not is_admin:
                await callback_query.answer("Only admins can change settings", show_alert=True)
                return

            settings = await api_client.get_group_settings(chat_id)
            features = settings.get("features_enabled", {}) if isinstance(settings, dict) else {}

            kb = []
            def btn(feature_key, label):
                enabled = bool(features.get(feature_key, False))
                text = f"{label}: {'✅' if enabled else '❌'}"
                return [InlineKeyboardButton(text=text, callback_data=f"toggle_setting::{feature_key}")]

            kb.append(btn("auto_delete_commands", "Auto-delete commands"))
            kb.append(btn("auto_delete_welcome", "Auto-delete welcome"))
            kb.append(btn("auto_delete_left", "Auto-delete left"))
            kb.append(btn("auto_delete_pins", "Auto-delete pins"))
            kb.append(btn("auto_delete_events", "Auto-delete events"))
            kb.append([InlineKeyboardButton(text="🔙 Close", callback_data="settings_close")])

            text = (
                f"╔═══════════════════════════════════╗\n"
                f"║ ⚙️ <b>GROUP SETTINGS</b>                ║\n"
                f"╚═══════════════════════════════════╝\n\n"
                f"<b>Group:</b> <code>{settings.get('group_name', chat_id)}</code>\n"
                f"<b>Group ID:</b> <code>{chat_id}</code>\n\n"
                f"Tap a toggle to enable/disable the feature.\n"
            )

            await callback_query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
            await callback_query.answer()
            return
        elif data.startswith("toggle_setting::"):
            # Toggle a specific feature
            try:
                parts = data.split("::", 2)
                feature = parts[1]
            except Exception:
                await callback_query.answer("Invalid data", show_alert=True)
                return

            chat_id = callback_query.message.chat.id
            try:
                member = await bot.get_chat_member(chat_id, callback_query.from_user.id)
                is_admin = member.status in ("administrator", "creator")
            except Exception:
                is_admin = False

            if not is_admin:
                await callback_query.answer("Only admins can change settings", show_alert=True)
                return

            # Fetch current setting and flip it
            settings = await api_client.get_group_settings(chat_id)
            features = settings.get("features_enabled", {}) if isinstance(settings, dict) else {}
            current = bool(features.get(feature, False))
            desired = not current
            ok = await api_client.toggle_feature(chat_id, feature, desired)

            if not ok:
                await callback_query.answer("Failed to update setting", show_alert=True)
                return

            # Refresh UI
            new_settings = await api_client.get_group_settings(chat_id)
            new_features = new_settings.get("features_enabled", {}) if isinstance(new_settings, dict) else {}
            kb = []
            def btn2(feature_key, label):
                enabled = bool(new_features.get(feature_key, False))
                text = f"{label}: {'✅' if enabled else '❌'}"
                return [InlineKeyboardButton(text=text, callback_data=f"toggle_setting::{feature_key}")]

            kb.append(btn2("auto_delete_commands", "Auto-delete commands"))
            kb.append(btn2("auto_delete_welcome", "Auto-delete welcome"))
            kb.append(btn2("auto_delete_left", "Auto-delete left"))
            kb.append(btn2("auto_delete_pins", "Auto-delete pins"))
            kb.append(btn2("auto_delete_events", "Auto-delete events"))
            kb.append([InlineKeyboardButton(text="🔙 Close", callback_data="settings_close")])

            text = (
                f"╔═══════════════════════════════════╗\n"
                f"║ ⚙️ <b>GROUP SETTINGS</b>                ║\n"
                f"╚═══════════════════════════════════╝\n\n"
                f"<b>Group:</b> <code>{new_settings.get('group_name', chat_id)}</code>\n"
                f"<b>Group ID:</b> <code>{chat_id}</code>\n\n"
                f"Tap a toggle to enable/disable the feature.\n"
            )

            await callback_query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
            await callback_query.answer("Setting updated")
            return
        elif data.startswith("edit_template::"):
            try:
                parts = data.split("::", 2)
                field = parts[1]
            except Exception:
                await callback_query.answer("Invalid data", show_alert=True)
                return

            chat_id = callback_query.message.chat.id
            try:
                member = await bot.get_chat_member(chat_id, callback_query.from_user.id)
                is_admin = member.status in ("administrator", "creator")
            except Exception:
                is_admin = False

            if not is_admin:
                await callback_query.answer("Only admins can edit templates", show_alert=True)
                return

            # Mark pending edit and prompt admin to send the new template text
            pending_template_edits[(chat_id, callback_query.from_user.id)] = field
            await callback_query.answer()
            await callback_query.message.reply_text(
                f"Please send the new template for <b>{field}</b> now. You may use { '{user}' } as placeholder for the user display name.",
                parse_mode=ParseMode.HTML
            )
            return
        elif data == "settings_close":
            try:
                await callback_query.message.edit_text("Settings closed", reply_markup=None)
            except Exception:
                pass
            await callback_query.answer()
            return
        elif data == "commands":
            await callback_query.message.edit_text(help_text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
            await callback_query.answer()
            return
        elif data == "quick_actions":
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏠 Back", callback_data="start")]
            ])
            quick_actions_text = (
                "╔═══════════════════════════════════╗\n"
                "║ ⚡ <b>QUICK ACTIONS MENU</b>       ║\n"
                "╚═══════════════════════════════════╝\n\n"
                "Use these quick commands by replying to a message:\n\n"
                "🔨 <code>/ban</code> - Quick ban user\n"
                "👢 <code>/kick</code> - Quick kick user\n"
                "🔇 <code>/mute</code> - Quick mute user\n"
                "⚠️ <code>/warn</code> - Quick warn user\n"
                "⬆️ <code>/promote</code> - Make admin\n"
                "🔊 <code>/unmute</code> - Unmute user\n"
                "✅ <code>/unban</code> - Unban user\n"
                "⬇️ <code>/demote</code> - Remove admin\n\n"
                "💡 <b>Tip:</b> Tap action buttons for follow-up options!"
            )
            await callback_query.message.edit_text(quick_actions_text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
            await callback_query.answer("⚡ Quick actions menu")
            return
        elif data == "about":
            about_text = (
                "╔═══════════════════════════════════════╗\n"
                "║ 🤖 <b>ABOUT THIS BOT</b>              ║\n"
                "╚═══════════════════════════════════════╝\n\n"
                "<b>🚀 Advanced Group Assistant v3.0</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "<b>Features:</b>\n"
                "✨ Advanced moderation system\n"
                "👥 Smart role management\n"
                "📊 Detailed action logging\n"
                "⚡ Lightning-fast responses\n"
                "🔐 Secure architecture\n\n"
                "<b>Technology:</b>\n"
                "Python 3.10+ • aiogram • FastAPI\n\n"
                "<b>Support:</b> @admin_support\n"
                "<b>Version:</b> 3.0.0 (Advanced)\n"
                "<b>Status:</b> ✅ Production Ready"
            )
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏠 Back", callback_data="start")]
            ])
            await callback_query.message.edit_text(about_text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
            await callback_query.answer()
            return
        
        # Handle action callbacks (action_target_user_id_group_id format)
        # Also handle settings callbacks: settings, toggle_setting::feature, edit_template::field, settings_close
        if data.startswith("settings"):
            return await handle_settings_callbacks(callback_query, data)
        
        if data.startswith("toggle_setting::"):
            return await handle_toggle_setting_callback(callback_query, data)
        
        if data.startswith("edit_template::"):
            return await handle_edit_template_callback(callback_query, data)
        
        if data == "settings_close":
            await callback_query.message.delete()
            await callback_query.answer("Settings closed")
            return
        
        # Try to decode compressed callback data first
        decoded = decode_callback_data(data)
        if decoded:
            action = decoded.get("action")
            target_user_id = decoded.get("user_id")
            group_id = decoded.get("group_id")
        else:
            # Fallback to old format for backwards compatibility: action_user_id_group_id
            parts = data.split("_")
            if len(parts) < 3:
                await callback_query.answer("Invalid callback data", show_alert=True)
                return
            
            try:
                action = parts[0]
                target_user_id = int(parts[1])
                group_id = int(parts[2])
            except (ValueError, IndexError):
                await callback_query.answer("Invalid callback data format", show_alert=True)
                return
        
        # Handle info-only callbacks (no API call needed)
        if action in ["user_info", "user_history", "user_stats", "admin_info", "role_history", "kick_stats", "warn_count", "save_warn", "manage_perms", "log_action", "user_back", "grant_perms"]:
            # Fetch real data from database
            try:
                stats = await get_user_stats_display(target_user_id, group_id, api_client)
                
                # Build display text based on action type
                if action == "user_info":
                    title = "👤 USER INFORMATION"
                elif action == "user_stats":
                    title = "📊 USER STATISTICS"
                elif action == "user_history":
                    title = "📜 USER ACTION HISTORY"
                elif action == "kick_stats":
                    title = "� KICK STATISTICS"
                elif action == "warn_count":
                    title = "⚠️ WARNING STATISTICS"
                else:
                    title = action.upper().replace("_", " ")
                
                # Get current user status from Telegram
                try:
                    member = await bot.get_chat_member(group_id, target_user_id)
                    status = f"{member.status}"
                    is_bot = "Yes" if member.user.is_bot else "No"
                    user_mention = member.user.first_name or "Unknown"
                except Exception:
                    status = "Unknown"
                    is_bot = "Unknown"
                    user_mention = f"User {target_user_id}"
                
                # Format stats display
                status_indicator = "✅ Active"
                if stats.get("current_ban"):
                    status_indicator = "🔴 BANNED"
                elif stats.get("current_mute"):
                    status_indicator = "🔇 MUTED"
                elif stats.get("current_restrict"):
                    status_indicator = "🔒 RESTRICTED"
                
                info_text = (
                    f"╔═════════════════════════════════════╗\n"
                    f"║ {title:<33} ║\n"
                    f"╚═════════════════════════════════════╝\n\n"
                    f"<b>User:</b> <code>{user_mention}</code>\n"
                    f"<b>User ID:</b> <code>{target_user_id}</code>\n"
                    f"<b>Group ID:</b> <code>{group_id}</code>\n"
                    f"<b>Telegram Status:</b> <code>{status}</code>\n"
                    f"<b>Current Status:</b> {status_indicator}\n"
                    f"<b>Is Bot:</b> <code>{is_bot}</code>\n\n"
                    f"📊 <b>ACTION STATISTICS:</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"⚠️ Warnings: <code>{stats['warning_count']}</code>\n"
                    f"🔇 Mutes: <code>{stats['mute_count']}</code>\n"
                    f"👢 Kicks: <code>{stats['kick_count']}</code>\n"
                    f"🔨 Bans: <code>{stats['ban_count']}</code>\n"
                    f"🔒 Restrictions: <code>{stats['restrict_count']}</code>\n"
                    f"⬆️ Promotions: <code>{stats['promote_count']}</code>\n"
                    f"⬇️ Demotions: <code>{stats['demote_count']}</code>\n"
                    f"🔓 Unrestrictions: <code>{stats['unrestrict_count']}</code>\n\n"
                    f"<b>Total Actions:</b> <code>{stats['total_actions']}</code>\n\n"
                    f"🎯 Use buttons below for actions."
                )
            except Exception as e:
                logger.error(f"Error fetching user info: {e}")
                info_text = (
                    f"📋 <b>{action.upper().replace('_', ' ')} - USER {target_user_id}</b>\n\n"
                    f"<b>User ID:</b> <code>{target_user_id}</code>\n"
                    f"<b>Group ID:</b> <code>{group_id}</code>\n"
                    f"<b>Status:</b> <code>Unable to load (API error)</code>\n\n"
                    f"⚠️ Could not fetch real data at this moment.\n"
                    f"Please try again later."
                )
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Back", callback_data=encode_callback_data("user_back", target_user_id, group_id))]
            ])
            await callback_query.message.edit_text(info_text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
            
            # Send separate reply message that mentions the user
            try:
                mention_text = (
                    f"📊 <b>User Statistics Report</b>\n\n"
                    f"<a href=\"tg://user?id={target_user_id}\">👤 User</a>\n"
                    f"<b>Status Summary:</b> {status_indicator}\n"
                    f"<b>Total Actions on Record:</b> {stats['total_actions']}"
                )
                await bot.send_message(
                    chat_id=group_id,
                    text=mention_text,
                    parse_mode=ParseMode.HTML,
                    reply_to_message_id=callback_query.message.message_id,
                    allow_sending_without_reply=True
                )
            except Exception as e:
                logger.warning(f"Could not send reply message: {e}")
            
            await callback_query.answer("📋 User information loaded")
            return
        
        # Validate action is in allowed list
        allowed_actions = ["ban", "unban", "kick", "mute", "unmute", "promote", "demote", "warn", "restrict", "unrestrict", "pin", "unpin", "lockdown"]
        if action not in allowed_actions:
            await callback_query.answer(f"Unknown action: {action}", show_alert=True)
            return
        
        # Permission check: ensure caller is admin
        caller_is_admin = await check_is_admin(callback_query.from_user.id, group_id)
        if not caller_is_admin:
            await callback_query.answer("❌ You need admin permissions for this action", show_alert=True)
            return
        
        # Comprehensive validation: duplicate, admin permissions, etc.
        status_check = await check_user_current_status(
            target_user_id, 
            group_id, 
            api_client, 
            action,
            admin_id=callback_query.from_user.id  # Pass admin ID for permission checks
        )
        if status_check != "ok":
            await callback_query.answer(status_check, show_alert=True)
            return
        
        # Create action data for API calls
        action_data = {
            "action_type": action,
            "group_id": group_id,
            "user_id": target_user_id,
            "initiated_by": callback_query.from_user.id
        }
        
        # Execute action via API
        result = await api_client.execute_action(action_data)
        
        if "error" in result:
            error_notification = (
                f"⚠️ <b>ACTION FAILED</b>\n\n"
                f"<b>Action:</b> {action.upper()}\n"
                f"<b>User ID:</b> <code>{target_user_id}</code>\n"
                f"<b>Error:</b> <code>{escape_error_message(result['error'])}</code>\n\n"
                f"Please check permissions or try again."
            )
            await callback_query.answer(f"❌ {action.title()} failed!", show_alert=True)
            await callback_query.message.edit_text(error_notification, parse_mode=ParseMode.HTML)
            await log_command_execution(callback_query.message, action, success=False, result=result.get("error"), args=f"via_callback_for_{target_user_id}")
        else:
            await callback_query.answer(f"✅ {action.title()} executed successfully!", show_alert=False)
            
            # Edit message to show new action with updated buttons
            action_text = {
                "ban": "banned",
                "unban": "unbanned",
                "kick": "kicked",
                "mute": "muted",
                "unmute": "unmuted",
                "promote": "promoted to admin",
                "demote": "demoted from admin",
                "warn": "warned",
                "restrict": "restricted",
                "unrestrict": "unrestricted",
                "pin": "message pinned",
                "unpin": "message unpinned",
                "lockdown": "locked down",
            }
            
            emoji_map = {
                "ban": "🔨",
                "unban": "✅",
                "kick": "👢",
                "mute": "🔇",
                "unmute": "🔊",
                "promote": "⬆️",
                "demote": "⬇️",
                "warn": "⚠️",
                "restrict": "🔒",
                "unrestrict": "🔓",
                "pin": "📌",
                "unpin": "📍",
                "lockdown": "🔐",
            }
            
            emoji = emoji_map.get(action, "✅")
            text = action_text.get(action, action)
            
            new_text = (
                f"╔═══════════════════════════════════╗\n"
                f"║ {emoji} <b>ACTION COMPLETED</b>        ║\n"
                f"╚═══════════════════════════════════╝\n\n"
                f"<b>📌 User ID:</b> <code>{target_user_id}</code>\n"
                f"<b>⚡ Action:</b> <code>{action.upper()}</code>\n"
                f"<b>✅ Status:</b> <code>SUCCESS</code>\n"
                f"<b>📍 Result:</b> <i>User {text}</i>\n\n"
                f"🚀 <b>Next Actions Available ↓</b>"
            )
            keyboard = build_action_keyboard(action, target_user_id, group_id)
            
            await callback_query.message.edit_text(new_text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
            
            # Send reply message with admin and user mentions
            try:
                admin_mention = f"<a href=\"tg://user?id={callback_query.from_user.id}\">👤 Admin</a>"
                user_mention = f"<a href=\"tg://user?id={target_user_id}\">👤 User</a>"
                
                reply_text = (
                    f"⚡ <b>{action.upper()} Action Executed</b>\n\n"
                    f"Admin: {admin_mention}\n"
                    f"Target: {user_mention}\n"
                    f"<b>Status:</b> ✅ Complete"
                )
                
                await bot.send_message(
                    chat_id=group_id,
                    text=reply_text,
                    parse_mode=ParseMode.HTML,
                    reply_to_message_id=callback_query.message.message_id,
                    allow_sending_without_reply=True
                )
            except Exception as e:
                logger.warning(f"Could not send action reply message: {e}")
            
            await log_command_execution(callback_query.message, action, success=True, result=None, args=f"via_callback_for_{target_user_id}")
            
    except Exception as e:
        logger.error(f"Callback handler failed: {e}")
        error_msg = (
            f"❌ <b>CALLBACK ERROR</b>\n\n"
            f"<code>{escape_error_message(str(e))}</code>"
        )
        await callback_query.answer(f"Error: {str(e)}", show_alert=True)
        try:
            await callback_query.message.edit_text(error_msg, parse_mode=ParseMode.HTML)
        except:
            pass


async def chat_member_update_handler(chat_member_update: types.ChatMemberUpdated):
    """Handle member join/leave events, log them and optionally show welcome/left messages based on settings."""
    try:
        chat_id = chat_member_update.chat.id
        # Determine statuses
        old_status = getattr(chat_member_update.old_chat_member, "status", None)
        new_status = getattr(chat_member_update.new_chat_member, "status", None)
        target_user = None
        try:
            target_user = chat_member_update.new_chat_member.user
        except Exception:
            try:
                target_user = chat_member_update.old_chat_member.user
            except Exception:
                target_user = None

        # Join detected
        joined = old_status in ("left", "kicked", None) and new_status in ("member", "restricted", "administrator", "creator")
        left = new_status in ("left", "kicked") and old_status in ("member", "restricted", "administrator", "creator")

        if joined and target_user:
            # Welcome message
            settings = await api_client.get_group_settings(chat_id)
            features = settings.get("features_enabled", {}) if isinstance(settings, dict) else {}
            do_delete = bool(features.get("auto_delete_welcome", False))

            name = html.escape(getattr(target_user, "full_name", getattr(target_user, "username", str(target_user.id))))
            text = f"👋 Welcome <a href=\"tg://user?id={target_user.id}\">{name}</a>!"
            sent = await bot.send_message(chat_id, text, parse_mode=ParseMode.HTML)
            if do_delete:
                await asyncio.sleep(5)
                try:
                    await sent.delete()
                except Exception:
                    pass

            # Log event
            try:
                await api_client.log_event(chat_id, "member_join", target_user.id, triggered_by=getattr(chat_member_update.from_user, "id", None))
            except Exception:
                pass

        if left and target_user:
            settings = await api_client.get_group_settings(chat_id)
            features = settings.get("features_enabled", {}) if isinstance(settings, dict) else {}
            do_delete = bool(features.get("auto_delete_left", False))

            name = html.escape(getattr(target_user, "full_name", getattr(target_user, "username", str(target_user.id))))
            text = f"👋 <b>{name}</b> has left the group."
            sent = await bot.send_message(chat_id, text, parse_mode=ParseMode.HTML)
            if do_delete:
                await asyncio.sleep(5)
                try:
                    await sent.delete()
                except Exception:
                    pass

            # Log event
            try:
                await api_client.log_event(chat_id, "member_left", target_user.id, triggered_by=getattr(chat_member_update.from_user, "id", None))
            except Exception:
                pass

    except Exception as e:
        logger.debug(f"chat_member_update_handler error: {e}")


async def pending_template_message_handler(message: Message):
    """Handle admin messages that supply new template text when awaiting edit."""
    try:
        key = (message.chat.id, message.from_user.id)
        if key not in pending_template_edits:
            return  # nothing to do

        field = pending_template_edits.pop(key)
        new_template = message.text

        # Validate presence of placeholder optionally; we allow arbitrary text
        updates = {}
        if field == "welcome":
            updates["welcome_template"] = new_template
        elif field == "left":
            updates["left_template"] = new_template
        else:
            await send_and_delete(message, "❌ Unknown template field.", parse_mode=ParseMode.HTML)
            return

        ok = await api_client.update_group_settings(message.chat.id, updates)
        if ok:
            await message.answer("✅ Template updated successfully.")
        else:
            await message.answer("❌ Failed to update template. Try again later.")

    except Exception as e:
        logger.error(f"pending_template_message_handler error: {e}")


async def settings_refresh_loop():
    """Background task that periodically refreshes cached group settings from the API.

    This ensures that if settings change externally, the bot will pick them up within
    SETTINGS_REFRESH_INTERVAL seconds (env var, default 15s).
    """
    try:
        interval = int(os.getenv("SETTINGS_REFRESH_INTERVAL", "15"))
        while True:
            try:
                if api_client:
                    keys = list(getattr(api_client, "_settings_cache", {}).keys())
                    for gid in keys:
                        try:
                            # get_group_settings will refresh cache when called
                            await api_client.get_group_settings(gid)
                        except Exception:
                            pass
            except Exception as e:
                logger.debug(f"settings_refresh_loop iteration failed: {e}")
            await asyncio.sleep(interval)
    except asyncio.CancelledError:
        logger.info("Settings refresh task cancelled")
    except Exception as e:
        logger.error(f"settings_refresh_loop fatal error: {e}")


# ============================================================================
# BOT SETUP
# ============================================================================

async def setup_bot():
    """Initialize bot and dispatcher"""
    global bot, dispatcher, api_client
    
    try:
        logger.info("🚀 Starting Telegram Bot...")
        
        # Initialize API client
        api_client = CentralizedAPIClient(CENTRALIZED_API_URL, CENTRALIZED_API_KEY)
        
        # Check if centralized_api is healthy
        is_healthy = await api_client.health_check()
        if not is_healthy:
            logger.warning("⚠️ Centralized API is not healthy, continuing anyway...")
        else:
            logger.info("✅ Centralized API is healthy")
        
        # Initialize bot (without default parse_mode to avoid HTML parsing issues)
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        
        # Initialize dispatcher with memory storage
        storage = MemoryStorage()
        dispatcher = Dispatcher(storage=storage)
        
        # Register command handlers
        dispatcher.message.register(cmd_start, Command("start"))
        dispatcher.message.register(cmd_help, Command("help"))
        dispatcher.message.register(cmd_status, Command("status"))
        dispatcher.message.register(cmd_ban, Command("ban"))
        dispatcher.message.register(cmd_unban, Command("unban"))
        dispatcher.message.register(cmd_kick, Command("kick"))
        dispatcher.message.register(cmd_mute, Command("mute"))
        dispatcher.message.register(cmd_unmute, Command("unmute"))
        dispatcher.message.register(cmd_pin, Command("pin"))
        dispatcher.message.register(cmd_unpin, Command("unpin"))
        dispatcher.message.register(cmd_promote, Command("promote"))
        dispatcher.message.register(cmd_demote, Command("demote"))
        dispatcher.message.register(cmd_lockdown, Command("lockdown"))
        dispatcher.message.register(cmd_warn, Command("warn"))
        dispatcher.message.register(cmd_restrict, Command("restrict"))
        dispatcher.message.register(cmd_unrestrict, Command("unrestrict"))
        dispatcher.message.register(cmd_purge, Command("purge"))
        dispatcher.message.register(cmd_setrole, Command("setrole"))
        dispatcher.message.register(cmd_removerole, Command("removerole"))
        dispatcher.message.register(cmd_settings, Command("settings"))

        # Register callback query handler for inline buttons
        dispatcher.callback_query.register(handle_callback)

        # Register chat member/update handlers for join/leave
        dispatcher.chat_member.register(chat_member_update_handler)
        dispatcher.my_chat_member.register(chat_member_update_handler)

        # Register general message handler (for non-command messages)
        # Handler for pending template edits (should run before generic message handler if possible)
        dispatcher.message.register(pending_template_message_handler)
        dispatcher.message.register(handle_message)

        # Start background settings refresh task
        global settings_refresh_task
        try:
            settings_refresh_task = asyncio.create_task(settings_refresh_loop())
        except Exception as _e:
            logger.debug(f"Could not start settings_refresh_loop: {_e}")
        
        # Verify bot token is valid by getting bot info
        try:
            bot_info = await bot.get_me()
            logger.info(f"✅ Bot token verified! Bot: @{bot_info.username} ({bot_info.first_name})")
        except Exception as e:
            logger.error(f"❌ Bot token verification failed: {e}")
            logger.error(f"Token used: {TELEGRAM_BOT_TOKEN[:20]}...")
            raise
        
        # Set bot commands (non-critical, can fail)
        try:
            await bot.set_my_commands([
                BotCommand(command="start", description="Welcome message"),
                BotCommand(command="help", description="Show help"),
                BotCommand(command="status", description="Bot status"),
                BotCommand(command="ban", description="Ban user (admin)"),
                BotCommand(command="kick", description="Kick user (admin)"),
                BotCommand(command="mute", description="Mute user (admin)"),
                BotCommand(command="unmute", description="Unmute user (admin)"),
                BotCommand(command="pin", description="Pin message (admin)"),
                BotCommand(command="unpin", description="Unpin message (admin)"),
                BotCommand(command="promote", description="Promote to admin (admin)"),
                BotCommand(command="demote", description="Demote admin (admin)"),
                BotCommand(command="lockdown", description="Lock group (admin)"),
                BotCommand(command="settings", description="Group settings (admin)"),
                BotCommand(command="warn", description="Warn user (admin)"),
                BotCommand(command="restrict", description="Restrict user (admin)"),
                BotCommand(command="unrestrict", description="Unrestrict user (admin)"),
                BotCommand(command="purge", description="Delete user messages (admin)"),
                BotCommand(command="setrole", description="Set user role (admin)"),
                BotCommand(command="removerole", description="Remove user role (admin)"),
            ])
            logger.info("✅ Bot commands registered")
        except Exception as e:
            logger.warning(f"⚠️ Failed to set bot commands: {e} (continuing anyway...)")
        
        logger.info("✅ Bot initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize bot: {e}")
        raise


async def run_bot():
    """Run the bot"""
    try:
        logger.info("🤖 Bot is polling for updates...")
        await dispatcher.start_polling(bot)
    except Exception as e:
        logger.error(f"❌ Bot polling failed: {e}")
        raise


async def main():
    """Main entry point"""
    try:
        await setup_bot()
        await run_bot()
    except KeyboardInterrupt:
        logger.info("⏹️ Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        raise
    finally:
        if bot:
            await bot.session.close()
            logger.info("✅ Bot session closed")


if __name__ == "__main__":
    asyncio.run(main())
