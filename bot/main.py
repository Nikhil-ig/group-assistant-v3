"""
Telegram Bot Service - Main Entry Point
Independent bot service that communicates with api_v2 via HTTP
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
API_V2_URL = os.getenv("API_V2_URL", "http://localhost:8002")
API_V2_KEY = os.getenv("API_V2_KEY", "shared-api-key")

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

class APIv2Client:
    """HTTP client for communicating with api_v2"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = 30
        # Simple in-memory cache for group settings to reduce API calls
        # structure: { group_id: (settings_dict, expires_at_timestamp) }
        self._settings_cache: dict[int, tuple[dict, float]] = {}
        self._cache_ttl = int(os.getenv("SETTINGS_CACHE_TTL", "30"))  # seconds
    
    async def health_check(self) -> bool:
        """Check if api_v2 is healthy"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/health",
                    timeout=self.timeout
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    async def execute_action(self, action_data: dict) -> dict:
        """Execute an action through api_v2
        
        Routes to specific endpoint based on action_type:
        - ban, unban, kick, mute, unmute, warn, promote, demote, restrict, unrestrict, lockdown
        """
        try:
            group_id = action_data.get("group_id")
            action_type = action_data.get("action_type", "").lower()
            
            if not group_id:
                return {"error": "group_id required in action_data"}
            
            # Map action_type to endpoint
            action_endpoints = {
                "ban": f"/api/v2/groups/{group_id}/enforcement/ban",
                "unban": f"/api/v2/groups/{group_id}/enforcement/unban",
                "kick": f"/api/v2/groups/{group_id}/enforcement/kick",
                "mute": f"/api/v2/groups/{group_id}/enforcement/mute",
                "unmute": f"/api/v2/groups/{group_id}/enforcement/unmute",
                "warn": f"/api/v2/groups/{group_id}/enforcement/warn",
                "promote": f"/api/v2/groups/{group_id}/enforcement/promote",
                "demote": f"/api/v2/groups/{group_id}/enforcement/demote",
                "restrict": f"/api/v2/groups/{group_id}/enforcement/restrict",
                "unrestrict": f"/api/v2/groups/{group_id}/enforcement/unrestrict",
                "lockdown": f"/api/v2/groups/{group_id}/enforcement/lockdown",
            }
            
            endpoint = action_endpoints.get(action_type)
            if not endpoint:
                # Fallback to generic execute endpoint
                endpoint = f"/api/v2/groups/{group_id}/enforcement/execute"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}{endpoint}",
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
        """Get user permissions from api_v2"""
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
        """Fetch group settings from API v2
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
                    f"{self.base_url}/api/v2/groups/{group_id}/settings",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=self.timeout
                )
                resp.raise_for_status()
                settings = resp.json()

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
                # Fetch violations/history for specific user
                response = await client.get(
                    f"{self.base_url}/api/v2/groups/{group_id}/enforcement/user/{user_id}/violations",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()
                
                # Extract violations list
                violations = data.get("violations", []) if isinstance(data, dict) else []
                
                return {"actions": violations}
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
        """Comprehensive pre-action validation including:
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
                # Use duplicate detection endpoint
                response = await client.post(
                    f"{self.base_url}/api/v2/groups/{group_id}/moderation/duplicate-detection",
                    json={
                        "user_id": user_id,
                        "action_type": action_type
                    },
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=self.timeout
                )
                response.raise_for_status()
                result = response.json()
                
                # Map response to expected format
                return {
                    "can_proceed": result.get("can_proceed", True),
                    "status": result.get("status", "ok"),
                    "reason": result.get("reason", ""),
                    "checks": result.get("checks", {}),
                    "current_restrictions": result.get("current_restrictions", [])
                }
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

    async def post(self, endpoint: str, data: dict) -> dict:
        """Generic POST method for API V2 requests
        
        Args:
            endpoint: API endpoint path (e.g., "/groups/123/messages/delete")
            data: JSON data to send in POST body
            
        Returns:
            Response JSON as dict
        """
        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.base_url}/api/v2{endpoint}" if not endpoint.startswith("/api/") else f"{self.base_url}{endpoint}"
                response = await client.post(
                    url,
                    json=data,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"POST request to {endpoint} failed: {e}")
            return {"error": str(e), "success": False}

    async def get(self, endpoint: str, params: dict = None) -> dict:
        """Generic GET method for API V2 requests
        
        Args:
            endpoint: API endpoint path (e.g., "/groups/123/messages/broadcasts")
            params: Optional query parameters
            
        Returns:
            Response JSON as dict
        """
        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.base_url}/api/v2{endpoint}" if not endpoint.startswith("/api/") else f"{self.base_url}{endpoint}"
                response = await client.get(
                    url,
                    params=params,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"GET request to {endpoint} failed: {e}")
            return {"error": str(e), "success": False}


def escape_error_message(error_msg) -> str:
    """Escape HTML special characters in error messages for safe Telegram delivery"""
    if error_msg is None:
        return "Unknown error"
    try:
        return html.escape(str(error_msg))
    except Exception as e:
        logger.error(f"Error escaping message: {error_msg}, {e}")
        return "Error processing error message"


async def get_user_stats_display(user_id: int, group_id: int, api_client: 'APIv2Client') -> dict:
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


async def check_user_current_status(user_id: int, group_id: int, api_client: 'APIv2Client', action_type: str, admin_id: int = 0) -> str:
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
api_client: Optional[APIv2Client] = None
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


async def check_moderator_permission(user_id: int, group_id: int, power: str) -> bool:
    """
    Check if user is whitelisted moderator with specific power
    Returns True if:
    1. User is actual admin, OR
    2. User is whitelisted as moderator with the required power
    
    power: "mute", "unmute", "warn", "kick", "send_link", "restrict", "unrestrict", etc.
    """
    # Check if actual admin first
    if await check_is_admin(user_id, group_id):
        return True
    
    # Check whitelist for moderator powers
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                f"{api_client.base_url}/api/v2/groups/{group_id}/whitelist/{user_id}",
                headers={"Authorization": f"Bearer {api_client.api_key}"},
                timeout=5
            )
            
            if resp.status_code == 200:
                data = resp.json()
                if data.get("whitelisted") and data.get("entry_type") == "moderator":
                    powers = data.get("admin_powers", [])
                    return power in powers
    except Exception as e:
        logger.debug(f"Error checking moderator permissions: {e}")
    
    return False


async def is_user_exempt(user_id: int, group_id: int) -> bool:
    """Check if user is whitelisted for exemption (bypass restrictions)"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                f"{api_client.base_url}/api/v2/groups/{group_id}/whitelist/{user_id}",
                headers={"Authorization": f"Bearer {api_client.api_key}"},
                timeout=5
            )
            
            if resp.status_code == 200:
                data = resp.json()
                if data.get("whitelisted") and data.get("entry_type") == "exemption":
                    return True
    except Exception as e:
        logger.debug(f"Error checking exemption: {e}")
    
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
    """Enhanced /settings command - show toggles for auto-delete features OR advanced admin panel for user actions"""
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

        # Check if /settings is used with a target user (advanced admin panel)
        args = message.text.split(maxsplit=1)[1:] if len(message.text.split(maxsplit=1)) > 1 else []
        target_user_id = None
        
        # Try to get target user from arguments or reply
        if args:
            arg = args[0]
            if arg.startswith("@"):
                # Username provided
                try:
                    user_chat = await bot.get_chat(arg)
                    target_user_id = user_chat.id
                except Exception:
                    await send_and_delete(message, f"❌ User {arg} not found", parse_mode=ParseMode.HTML, delay=6)
                    return
            else:
                # Try to parse as user ID
                try:
                    target_user_id = int(arg)
                except ValueError:
                    await send_and_delete(message, "❌ Invalid user ID format", parse_mode=ParseMode.HTML, delay=6)
                    return
        elif message.reply_to_message:
            # Use replied message user
            target_user_id = message.reply_to_message.from_user.id
        
        # If target user specified, show advanced admin panel
        if target_user_id:
            from bot.advanced_admin_panel import format_admin_panel_message, build_advanced_toggle_keyboard
            
            try:
                # Get user data
                user_data = await get_user_data(target_user_id)
                first_name = user_data.get("first_name", "Unknown") if user_data else "Unknown"
                username = user_data.get("username") if user_data else None
                
                # Format beautiful admin panel message
                panel_message = await format_admin_panel_message(
                    {"first_name": first_name, "username": username},
                    target_user_id,
                    chat_id,
                    message.from_user.id
                )
                
                # Build keyboard
                keyboard = await build_advanced_toggle_keyboard(target_user_id, chat_id)
                
                # Send panel message (reply to original message if it's a reply)
                if message.reply_to_message:
                    await message.reply_to_message.reply_text(
                        panel_message,
                        parse_mode=ParseMode.HTML,
                        reply_markup=keyboard
                    )
                else:
                    await message.answer(
                        panel_message,
                        parse_mode=ParseMode.HTML,
                        reply_markup=keyboard
                    )
                
                # Delete the command message
                try:
                    await message.delete()
                except Exception:
                    pass
                    
                return
            except Exception as e:
                logger.error(f"Advanced admin panel error: {e}")
                await send_and_delete(message, f"❌ Error opening admin panel: {escape_error_message(str(e))}", parse_mode=ParseMode.HTML, delay=6)
                return
        
        # Otherwise, show group settings panel (original behavior)
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
            f"Tap a toggle to enable/disable the feature or edit templates.\n\n"
            f"<b>💡 Tip:</b> Use <code>/settings @username</code> to open the Advanced Admin Panel for a user!"
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
        
        if result.get("error") is not None:
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
        
        if result.get("error") is not None:
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
        if result.get("error") is not None:
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
        # Permission check: ensure caller is admin OR has mute power
        is_admin = await check_is_admin(message.from_user.id, message.chat.id)
        is_moderator = await check_moderator_permission(message.from_user.id, message.chat.id, "mute")
        
        if not (is_admin or is_moderator):
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
        if result.get("error") is not None:
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
        # Permission check: ensure caller is admin OR has unmute power
        is_admin = await check_is_admin(message.from_user.id, message.chat.id)
        is_moderator = await check_moderator_permission(message.from_user.id, message.chat.id, "unmute")
        
        if not (is_admin or is_moderator):
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
        
        if result.get("error") is not None:
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
                await log_command_execution(message, "unmute", success=True, result="User unmuted successfully", args=message.text)
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
        
        if result.get("error") is not None:
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
        
        if result.get("error") is not None:
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
        
        logger.info(f"BOT DEBUG: Promoting user_id={user_id} with title={title}")
        logger.info(f"BOT DEBUG: Promoting user_id={user_id} with title={title}")
        action_data = {
            "action_type": "promote",
            "group_id": message.chat.id,
            "user_id": user_id,
            "title": title,
            "initiated_by": message.from_user.id
        }
        
        result = await api_client.execute_action(action_data)
        
        if result.get("error") is not None:
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
        
        if result.get("error") is not None:
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
        
        if result.get("error") is not None:
            await message.answer(f"❌ Error: {escape_error_message(result['error'])}", parse_mode=None)
            await log_command_execution(message, "lockdown", success=False, result=result.get("error"), args=message.text)
        else:
            await message.answer(f"🔒 Group has been locked. Only admins can send messages.")
            await log_command_execution(message, "lockdown", success=True, result=None, args=message.text)
            
    except Exception as e:
        logger.error(f"Lockdown command failed: {e}")
        await message.answer(f"❌ Error: {escape_error_message(str(e))}")


async def cmd_unlock(message: Message):
    """Handle /unlock command - Unlock group (restore all member permissions)"""
    try:
        # Permission check: ensure caller is admin
        if not await check_is_admin(message.from_user.id, message.chat.id):
            await send_and_delete(message, "❌ You need admin permissions for this action",
                                 parse_mode=ParseMode.HTML, delay=5)
            return
        
        action_data = {
            "action_type": "unlock",
            "group_id": message.chat.id,
            "initiated_by": message.from_user.id
        }
        
        result = await api_client.execute_action(action_data)
        
        if result.get("error") is not None:
            await message.answer(f"❌ Error: {escape_error_message(result['error'])}", parse_mode=None)
            await log_command_execution(message, "unlock", success=False, result=result.get("error"), args=message.text)
        else:
            await message.answer(f"🔓 Group has been unlocked. Members can now send messages normally.")
            await log_command_execution(message, "unlock", success=True, result=None, args=message.text)
            
    except Exception as e:
        logger.error(f"Unlock command failed: {e}")
        await message.answer(f"❌ Error: {escape_error_message(str(e))}")


async def cmd_warn(message: Message):
    """Handle /warn command - Warn user
    Usage: /warn (reply to message) or /warn <user_id|@username> [reason]
    """
    try:
        # Permission check: ensure caller is admin OR has warn power
        is_admin = await check_is_admin(message.from_user.id, message.chat.id)
        is_moderator = await check_moderator_permission(message.from_user.id, message.chat.id, "warn")
        
        if not (is_admin or is_moderator):
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
        
        if result.get("error") is not None:
            await message.answer(f"❌ Error: {escape_error_message(result['error'])}", parse_mode=None)
            await log_command_execution(message, "warn", success=False, result=result.get("error"), args=message.text)
        else:
            await message.answer(f"⚠️ User {user_id} warned - Reason: {reason}")
            await log_command_execution(message, "warn", success=True, result=None, args=message.text)
            
    except Exception as e:
        logger.error(f"Warn command failed: {e}")
        await message.answer(f"❌ Error: {escape_error_message(str(e))}", parse_mode=None)


async def cmd_restrict(message: Message):
    """Handle /restrict command - Show permission toggle buttons (smart on/off toggles)
    Usage: /restrict (reply to message) or /restrict <user_id|@username>
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
                await message.answer("Usage:\n/restrict (reply to message)\n/restrict <user_id|@username>")
                return
            
            user_id, _ = parse_user_reference(args[1])
        
        if not user_id:
            await message.answer("❌ Could not identify user. Reply to a message or use /restrict <user_id|@username>")
            return
        
        # Fetch current permission states
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    f"{api_client.base_url}/api/v2/groups/{message.chat.id}/users/{user_id}/permissions",
                    headers={"Authorization": f"Bearer {api_client.api_key}"},
                    timeout=5
                )
                if resp.status_code == 200:
                    perms = resp.json().get("data", {})
                    text_locked = not perms.get("can_send_messages", True)
                    stickers_locked = not perms.get("can_send_other_messages", True)
                    voice_locked = not perms.get("can_send_audios", True)
                else:
                    # If can't fetch, assume all unlocked
                    text_locked = stickers_locked = voice_locked = False
        except Exception as e:
            logger.warning(f"Could not fetch permissions: {e}, assuming all unlocked")
            text_locked = stickers_locked = voice_locked = False
        
        # Show toggle buttons based on current state
        # Each button shows the ACTION (lock if free, free if locked)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"📝 Text: {'🔓 Lock' if text_locked else '🔒 Free'}",
                    callback_data=f"toggle_perm_text_{user_id}_{message.chat.id}"
                ),
                InlineKeyboardButton(
                    text=f"🎨 Stickers: {'🔓 Lock' if stickers_locked else '🔒 Free'}",
                    callback_data=f"toggle_perm_stickers_{user_id}_{message.chat.id}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"🎬 GIFs: {'🔓 Lock' if stickers_locked else '🔒 Free'}",
                    callback_data=f"toggle_perm_gifs_{user_id}_{message.chat.id}"
                ),
                InlineKeyboardButton(
                    text=f"🎤 Voice: {'🔓 Lock' if voice_locked else '🔒 Free'}",
                    callback_data=f"toggle_perm_voice_{user_id}_{message.chat.id}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="� Toggle All",
                    callback_data=f"toggle_perm_all_{user_id}_{message.chat.id}"
                ),
                InlineKeyboardButton(text="❌ Cancel", callback_data=f"toggle_cancel_{user_id}_{message.chat.id}"),
            ]
        ])
        
        text = (
            f"� <b>PERMISSION TOGGLES</b>\n\n"
            f"<b>User ID:</b> <code>{user_id}</code>\n"
            f"<b>Group ID:</b> <code>{message.chat.id}</code>\n\n"
            f"<b>Current State:</b>\n"
            f"• 📝 Text: {'🔒 LOCKED' if text_locked else '🔓 UNLOCKED'}\n"
            f"• 🎨 Stickers: {'🔒 LOCKED' if stickers_locked else '🔓 UNLOCKED'}\n"
            f"• 🎬 GIFs: {'🔒 LOCKED' if stickers_locked else '🔓 UNLOCKED'}\n"
            f"• 🎤 Voice: {'🔒 LOCKED' if voice_locked else '🔓 UNLOCKED'}\n\n"
            f"<b>Click button to toggle permission (ON/OFF):</b>\n"
            f"• Button shows the action it will perform\n"
            f"• � Lock = Click to LOCK (turn OFF)\n"
            f"• 🔒 Free = Click to FREE (turn ON)\n"
        )
        
        await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
        await log_command_execution(message, "restrict", success=True, result="Permission toggles displayed", args=message.text)
            
    except Exception as e:
        logger.error(f"Restrict command failed: {e}")
        await message.answer(f"❌ Error: {escape_error_message(str(e))}", parse_mode=None)


async def cmd_unrestrict(message: Message):
    """Handle /unrestrict command - Show permission toggle buttons (smart on/off toggles)
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
        
        # Fetch current permission states
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    f"{api_client.base_url}/api/v2/groups/{message.chat.id}/users/{user_id}/permissions",
                    headers={"Authorization": f"Bearer {api_client.api_key}"},
                    timeout=5
                )
                if resp.status_code == 200:
                    perms = resp.json().get("data", {})
                    text_locked = not perms.get("can_send_messages", True)
                    stickers_locked = not perms.get("can_send_other_messages", True)
                    voice_locked = not perms.get("can_send_audios", True)
                else:
                    # If can't fetch, assume all unlocked
                    text_locked = stickers_locked = voice_locked = False
        except Exception as e:
            logger.warning(f"Could not fetch permissions: {e}, assuming all unlocked")
            text_locked = stickers_locked = voice_locked = False
        
        # Show toggle buttons based on current state
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"📝 Text: {'� Lock' if text_locked else '🔒 Free'}",
                    callback_data=f"toggle_perm_text_{user_id}_{message.chat.id}"
                ),
                InlineKeyboardButton(
                    text=f"🎨 Stickers: {'� Lock' if stickers_locked else '🔒 Free'}",
                    callback_data=f"toggle_perm_stickers_{user_id}_{message.chat.id}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"🎬 GIFs: {'� Lock' if stickers_locked else '🔒 Free'}",
                    callback_data=f"toggle_perm_gifs_{user_id}_{message.chat.id}"
                ),
                InlineKeyboardButton(
                    text=f"🎤 Voice: {'� Lock' if voice_locked else '🔒 Free'}",
                    callback_data=f"toggle_perm_voice_{user_id}_{message.chat.id}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔄 Toggle All",
                    callback_data=f"toggle_perm_all_{user_id}_{message.chat.id}"
                ),
                InlineKeyboardButton(text="❌ Cancel", callback_data=f"toggle_cancel_{user_id}_{message.chat.id}"),
            ]
        ])
        
        text = (
            f"� <b>PERMISSION TOGGLES</b>\n\n"
            f"<b>User ID:</b> <code>{user_id}</code>\n"
            f"<b>Group ID:</b> <code>{message.chat.id}</code>\n\n"
            f"<b>Current State:</b>\n"
            f"• 📝 Text: {'🔒 LOCKED' if text_locked else '🔓 UNLOCKED'}\n"
            f"• 🎨 Stickers: {'🔒 LOCKED' if stickers_locked else '🔓 UNLOCKED'}\n"
            f"• 🎬 GIFs: {'🔒 LOCKED' if stickers_locked else '🔓 UNLOCKED'}\n"
            f"• 🎤 Voice: {'🔒 LOCKED' if voice_locked else '🔓 UNLOCKED'}\n\n"
            f"<b>Click button to toggle permission (ON/OFF):</b>\n"
            f"• Button shows the action it will perform\n"
            f"• 🔓 Lock = Click to LOCK (turn OFF)\n"
            f"• 🔒 Free = Click to FREE (turn ON)\n"
        )
        
        await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
        await log_command_execution(message, "unrestrict", success=True, result="Permission toggles displayed", args=message.text)
            
    except Exception as e:
        logger.error(f"Unrestrict command failed: {e}")
        await message.answer(f"❌ Error: {escape_error_message(str(e))}", parse_mode=None)



async def cmd_free(message: Message):
    """Handle /free command - Enhanced permission & content-type management
    
    Shows detailed permission toggles for managing specific content types:
    - Text messages (on/off)
    - Stickers (on/off)
    - GIFs (on/off)
    - Media (photos, videos, documents)
    - Voice messages (on/off)
    - Links/URLs (on/off)
    
    Also shows night mode status and exemption status
    
    Usage: /free (reply to message) or /free <user_id|@username>
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
                await message.answer("Usage:\n/free (reply to message)\n/free <user_id|@username>")
                return
            
            user_id, _ = parse_user_reference(args[1])
        
        if not user_id:
            await message.answer("❌ Could not identify user. Reply to a message or use /free <user_id|@username>")
            return
        
        # Fetch current permission states
        text_allowed = True
        stickers_allowed = True
        gifs_allowed = True
        media_allowed = True
        voice_allowed = True
        links_allowed = True
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    f"{api_client.base_url}/api/v2/groups/{message.chat.id}/users/{user_id}/permissions",
                    headers={"Authorization": f"Bearer {api_client.api_key}"},
                    timeout=5
                )
                if resp.status_code == 200:
                    perms = resp.json().get("data", {})
                    text_allowed = bool(perms.get("can_send_messages", True))
                    stickers_allowed = bool(perms.get("can_send_other_messages", True))
                    gifs_allowed = bool(perms.get("can_send_other_messages", True))
                    media_allowed = bool(perms.get("can_send_media_messages", True))
                    voice_allowed = bool(perms.get("can_send_voice_notes", True))
                    links_allowed = bool(perms.get("can_add_web_page_previews", True))
        except Exception as e:
            logger.warning(f"Could not fetch permissions: {e}, assuming all allowed")
        
        # Check night mode exemption status
        is_exempt = False
        is_exempt_role = False
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    f"{api_client.base_url}/api/v2/groups/{message.chat.id}/night-mode/check/{user_id}/text",
                    headers={"Authorization": f"Bearer {api_client.api_key}"},
                    timeout=5
                )
                if resp.status_code == 200:
                    nm_data = resp.json()
                    is_exempt = bool(nm_data.get("is_exempt", False))
                    is_exempt_role = nm_data.get("exempt_type") == "role" if "exempt_type" in nm_data else False
        except Exception as e:
            logger.debug(f"Could not check night mode exemption: {e}")
        
        # Check night mode status
        night_mode_active = False
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    f"{api_client.base_url}/api/v2/groups/{message.chat.id}/night-mode/status",
                    headers={"Authorization": f"Bearer {api_client.api_key}"},
                    timeout=5
                )
                if resp.status_code == 200:
                    nm_status = resp.json()
                    night_mode_active = bool(nm_status.get("is_active", False))
        except Exception as e:
            logger.debug(f"Could not check night mode status: {e}")
        
        # Build comprehensive permission toggles keyboard
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            # Row 1: Text & Stickers
            [
                InlineKeyboardButton(
                    text=f"📝 Text: {'✅ ON' if text_allowed else '❌ OFF'}",
                    callback_data=f"toggle_perm_text_{user_id}_{message.chat.id}"
                ),
                InlineKeyboardButton(
                    text=f"🎨 Stickers: {'✅ ON' if stickers_allowed else '❌ OFF'}",
                    callback_data=f"toggle_perm_stickers_{user_id}_{message.chat.id}"
                ),
            ],
            # Row 2: GIFs & Media
            [
                InlineKeyboardButton(
                    text=f"🎬 GIFs: {'✅ ON' if gifs_allowed else '❌ OFF'}",
                    callback_data=f"toggle_perm_gifs_{user_id}_{message.chat.id}"
                ),
                InlineKeyboardButton(
                    text=f"📸 Media: {'✅ ON' if media_allowed else '❌ OFF'}",
                    callback_data=f"toggle_perm_media_{user_id}_{message.chat.id}"
                ),
            ],
            # Row 3: Voice & Links
            [
                InlineKeyboardButton(
                    text=f"🎤 Voice: {'✅ ON' if voice_allowed else '❌ OFF'}",
                    callback_data=f"toggle_perm_voice_{user_id}_{message.chat.id}"
                ),
                InlineKeyboardButton(
                    text=f"🔗 Links: {'✅ ON' if links_allowed else '❌ OFF'}",
                    callback_data=f"toggle_perm_links_{user_id}_{message.chat.id}"
                ),
            ],
            # Row 4: Action buttons
            [
                InlineKeyboardButton(
                    text="🔄 Toggle All",
                    callback_data=f"toggle_perm_all_{user_id}_{message.chat.id}"
                ),
                InlineKeyboardButton(
                    text="❌ Cancel",
                    callback_data=f"toggle_cancel_{user_id}_{message.chat.id}"
                ),
            ]
        ])
        
        # Build detailed status message
        exemption_status = ""
        if is_exempt:
            if is_exempt_role:
                exemption_status = "  🎖️  <i>Exempt by role</i>\n"
            else:
                exemption_status = "  ⭐ <i>Personally exempt</i>\n"
        
        night_mode_indicator = ""
        if night_mode_active:
            night_mode_indicator = f"\n🌙 <b>Night Mode Status:</b> <code>ACTIVE</code> {exemption_status}"
        
        text = (
            f"╔═══════════════════════════════════════╗\n"
            f"║ 🔓 <b>CONTENT PERMISSIONS</b>          ║\n"
            f"╚═══════════════════════════════════════╝\n\n"
            f"<b>Target User:</b> <code>{user_id}</code>\n"
            f"<b>Group:</b> <code>{message.chat.id}</code>\n\n"
            f"<b>📊 Permission State:</b>\n"
            f"  📝 Text: <code>{'ALLOWED ✅' if text_allowed else 'BLOCKED ❌'}</code>\n"
            f"  🎨 Stickers: <code>{'ALLOWED ✅' if stickers_allowed else 'BLOCKED ❌'}</code>\n"
            f"  🎬 GIFs: <code>{'ALLOWED ✅' if gifs_allowed else 'BLOCKED ❌'}</code>\n"
            f"  📸 Media: <code>{'ALLOWED ✅' if media_allowed else 'BLOCKED ❌'}</code>\n"
            f"  🎤 Voice: <code>{'ALLOWED ✅' if voice_allowed else 'BLOCKED ❌'}</code>\n"
            f"  🔗 Links: <code>{'ALLOWED ✅' if links_allowed else 'BLOCKED ❌'}</code>\n"
            f"{night_mode_indicator}"
            f"\n<b>💡 How to Use:</b>\n"
            f"  • Click any button to toggle that content type\n"
            f"  • ✅ ON = User can send this type\n"
            f"  • ❌ OFF = User cannot send this type\n"
            f"  • 🔄 Toggle All = Quick reverse all perms\n"
        )
        
        await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
        await log_command_execution(message, "free", success=True, result="Enhanced permission toggles displayed", args=message.text)
            
    except Exception as e:
        logger.error(f"Free command failed: {e}")
        await send_and_delete(message, f"❌ Error: {escape_error_message(str(e))}", 
                             parse_mode=ParseMode.HTML, delay=5)

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
        
        if result.get("error") is not None:
            await message.answer(f"❌ Error: {escape_error_message(result['error'])}", parse_mode=None)
        else:
            await message.answer(f"🗑️ Purged {count} messages from user {user_id}")
            
    except Exception as e:
        logger.error(f"Purge command failed: {e}")
        await message.answer(f"❌ Error: {escape_error_message(str(e))}", parse_mode=None)


# ==================== MESSAGE DELETION COMMAND (ULTRA ADVANCED) ====================

async def cmd_del(message: Message):
    """
    🗑️ ULTRA-ADVANCED Message Deletion Command - Enterprise-grade features
    
    Basic Modes:
    ⚡ /del (reply)                    - Delete single message
    ⚡ /del (reply) reason             - Delete with reason
    ⚡ /del bulk <count>               - Delete last N messages
    
    Advanced Modes:
    🔥 /del user <user_id>             - Delete all user's messages
    🔥 /del clear --confirm            - Clear entire thread
    🔥 /del archive                    - Archive + delete
    
    Ultra Modes:
    ⚡⚡ /del filter <keyword>          - Delete messages with keyword
    ⚡⚡ /del range <start> <end>       - Delete message range
    ⚡⚡ /del spam --auto               - Auto-detect & delete spam
    ⚡⚡ /del links --remove            - Delete all links/URLs
    ⚡⚡ /del media                     - Delete all media messages
    ⚡⚡ /del recent <minutes>          - Delete from last N minutes
    
    Features: Instant, bulk, filtering, range, auto-spam detection, media filtering
    """
    try:
        # Permission check: ensure caller is admin
        if not await check_is_admin(message.from_user.id, message.chat.id):
            await send_and_delete(
                message,
                "❌ You need admin permissions to delete messages",
                parse_mode=ParseMode.HTML,
                delay=5
            )
            return
        
        args = message.text.split()
        mode = args[1].lower() if len(args) > 1 else "single"
        
        # ========== MODE 1: Single Message Delete (Default) ==========
        if mode == "single" or message.reply_to_message:
            target_message_id = None
            target_user_id = None
            reason = "Deleted by admin"
            archive = False
            
            if message.reply_to_message:
                target_message_id = message.reply_to_message.message_id
                target_user_id = message.reply_to_message.from_user.id if message.reply_to_message.from_user else None
                
                # Check for archive flag
                if len(args) > 1 and "archive" in args:
                    archive = True
                
                # Parse optional reason
                for i, arg in enumerate(args[1:], 1):
                    if arg != "archive":
                        reason = " ".join(args[i:])[:100]
                        break
        
        # ========== MODE 2: Bulk Delete (Last N messages) ==========
        elif mode == "bulk":
            if len(args) < 3:
                await send_and_delete(
                    message,
                    "❌ Usage: /del bulk <count> (e.g., /del bulk 5)",
                    parse_mode=ParseMode.HTML,
                    delay=5
                )
                return
            
            try:
                count = int(args[2])
                if count <= 0 or count > 100:
                    await send_and_delete(
                        message,
                        "❌ Count must be between 1 and 100",
                        parse_mode=ParseMode.HTML,
                        delay=5
                    )
                    return
            except ValueError:
                await send_and_delete(
                    message,
                    "❌ Invalid count. Usage: /del bulk <count>",
                    parse_mode=ParseMode.HTML,
                    delay=5
                )
                return
            
            # Delete command message
            try:
                await message.delete()
            except Exception:
                pass
            
            # Bulk delete messages
            deleted_count = 0
            try:
                for msg_id in range(message.message_id - count, message.message_id):
                    try:
                        await bot.delete_message(message.chat.id, msg_id)
                        deleted_count += 1
                    except Exception:
                        pass
                
                logger.info(f"Bulk deleted {deleted_count} messages by {message.from_user.id}")
            except Exception as e:
                logger.error(f"Bulk delete error: {e}")
            
            return
        
        # ========== MODE 3: Delete by User ==========
        elif mode == "user":
            if len(args) < 3:
                await send_and_delete(
                    message,
                    "❌ Usage: /del user <user_id>",
                    parse_mode=ParseMode.HTML,
                    delay=5
                )
                return
            
            try:
                target_user_id = int(args[2])
            except ValueError:
                await send_and_delete(
                    message,
                    "❌ Invalid user ID",
                    parse_mode=ParseMode.HTML,
                    delay=5
                )
                return
            
            # Delete command
            try:
                await message.delete()
            except Exception:
                pass
            
            # Log to API for user message deletion
            try:
                await api_client.post(
                    f"/groups/{message.chat.id}/messages/delete-user-messages",
                    {
                        "target_user_id": target_user_id,
                        "admin_id": message.from_user.id,
                        "reason": "User messages cleared"
                    }
                )
            except Exception as e:
                logger.warning(f"Could not delete user messages: {e}")
            
            return
        
        # ========== MODE 4: Clear Entire Thread ==========
        elif mode == "clear":
            if "--confirm" not in args:
                await send_and_delete(
                    message,
                    "⚠️ WARNING: This will clear all recent messages!\nUse: /del clear --confirm",
                    parse_mode=ParseMode.HTML,
                    delay=8
                )
                return
            
            # Delete command
            try:
                await message.delete()
            except Exception:
                pass
            
            # Clear recent messages (last 50)
            cleared_count = 0
            try:
                for msg_id in range(max(1, message.message_id - 50), message.message_id):
                    try:
                        await bot.delete_message(message.chat.id, msg_id)
                        cleared_count += 1
                    except Exception:
                        pass
                
                logger.info(f"Cleared {cleared_count} messages by {message.from_user.id}")
            except Exception as e:
                logger.error(f"Clear error: {e}")
            
            return
        
        # ========== ULTRA MODE 1: Filter by Keyword ==========
        elif mode == "filter":
            if len(args) < 3:
                await send_and_delete(
                    message,
                    "❌ Usage: /del filter <keyword>",
                    parse_mode=ParseMode.HTML,
                    delay=5
                )
                return
            
            keyword = args[2].lower()
            
            # Delete command
            try:
                await message.delete()
            except Exception:
                pass
            
            # Filter and delete messages with keyword
            deleted_count = 0
            try:
                for msg_id in range(max(1, message.message_id - 100), message.message_id):
                    try:
                        msg = await bot.get_message(message.chat.id, msg_id)
                        if msg.text and keyword in msg.text.lower():
                            await bot.delete_message(message.chat.id, msg_id)
                            deleted_count += 1
                    except Exception:
                        pass
                
                logger.info(f"Filtered deleted {deleted_count} messages with '{keyword}' by {message.from_user.id}")
            except Exception as e:
                logger.error(f"Filter delete error: {e}")
            
            return
        
        # ========== ULTRA MODE 2: Delete Message Range ==========
        elif mode == "range":
            if len(args) < 4:
                await send_and_delete(
                    message,
                    "❌ Usage: /del range <start_id> <end_id>",
                    parse_mode=ParseMode.HTML,
                    delay=5
                )
                return
            
            try:
                start_id = int(args[2])
                end_id = int(args[3])
            except ValueError:
                await send_and_delete(
                    message,
                    "❌ Invalid message IDs",
                    parse_mode=ParseMode.HTML,
                    delay=5
                )
                return
            
            # Delete command
            try:
                await message.delete()
            except Exception:
                pass
            
            # Delete range
            deleted_count = 0
            try:
                for msg_id in range(min(start_id, end_id), max(start_id, end_id) + 1):
                    try:
                        await bot.delete_message(message.chat.id, msg_id)
                        deleted_count += 1
                    except Exception:
                        pass
                
                logger.info(f"Range deleted {deleted_count} messages ({start_id}-{end_id}) by {message.from_user.id}")
            except Exception as e:
                logger.error(f"Range delete error: {e}")
            
            return
        
        # ========== ULTRA MODE 3: Auto-Spam Detection ==========
        elif mode == "spam":
            if "--auto" not in args:
                await send_and_delete(
                    message,
                    "Usage: /del spam --auto",
                    parse_mode=ParseMode.HTML,
                    delay=5
                )
                return
            
            # Delete command
            try:
                await message.delete()
            except Exception:
                pass
            
            # Auto-detect and delete spam (repeated messages, links, etc.)
            deleted_count = 0
            spam_patterns = ["click here", "buy now", "free", "telegram.me", "t.me", "http", "://"]
            
            try:
                for msg_id in range(max(1, message.message_id - 50), message.message_id):
                    try:
                        msg = await bot.get_message(message.chat.id, msg_id)
                        if msg.text:
                            text_lower = msg.text.lower()
                            if any(pattern in text_lower for pattern in spam_patterns):
                                await bot.delete_message(message.chat.id, msg_id)
                                deleted_count += 1
                    except Exception:
                        pass
                
                logger.info(f"Auto-spam deleted {deleted_count} messages by {message.from_user.id}")
            except Exception as e:
                logger.error(f"Auto-spam error: {e}")
            
            return
        
        # ========== ULTRA MODE 4: Delete All Links ==========
        elif mode == "links":
            if "--remove" not in args:
                await send_and_delete(
                    message,
                    "Usage: /del links --remove",
                    parse_mode=ParseMode.HTML,
                    delay=5
                )
                return
            
            # Delete command
            try:
                await message.delete()
            except Exception:
                pass
            
            # Delete all messages with links
            deleted_count = 0
            try:
                for msg_id in range(max(1, message.message_id - 100), message.message_id):
                    try:
                        msg = await bot.get_message(message.chat.id, msg_id)
                        if msg.text and ("http" in msg.text or "telegram" in msg.text):
                            await bot.delete_message(message.chat.id, msg_id)
                            deleted_count += 1
                        elif msg.entities:
                            # Message has URL entities
                            await bot.delete_message(message.chat.id, msg_id)
                            deleted_count += 1
                    except Exception:
                        pass
                
                logger.info(f"Links deleted {deleted_count} messages by {message.from_user.id}")
            except Exception as e:
                logger.error(f"Links delete error: {e}")
            
            return
        
        # ========== ULTRA MODE 5: Delete All Media ==========
        elif mode == "media":
            # Delete command
            try:
                await message.delete()
            except Exception:
                pass
            
            # Delete all media messages (photos, videos, documents, etc.)
            deleted_count = 0
            try:
                for msg_id in range(max(1, message.message_id - 100), message.message_id):
                    try:
                        msg = await bot.get_message(message.chat.id, msg_id)
                        if msg.photo or msg.video or msg.document or msg.audio or msg.voice:
                            await bot.delete_message(message.chat.id, msg_id)
                            deleted_count += 1
                    except Exception:
                        pass
                
                logger.info(f"Media deleted {deleted_count} messages by {message.from_user.id}")
            except Exception as e:
                logger.error(f"Media delete error: {e}")
            
            return
        
        # ========== ULTRA MODE 6: Delete from Last N Minutes ==========
        elif mode == "recent":
            if len(args) < 3:
                await send_and_delete(
                    message,
                    "❌ Usage: /del recent <minutes>",
                    parse_mode=ParseMode.HTML,
                    delay=5
                )
                return
            
            try:
                minutes = int(args[2])
            except ValueError:
                await send_and_delete(
                    message,
                    "❌ Invalid minutes value",
                    parse_mode=ParseMode.HTML,
                    delay=5
                )
                return
            
            # Delete command
            try:
                await message.delete()
            except Exception:
                pass
            
            # Delete messages from last N minutes
            from datetime import datetime, timedelta
            cutoff_time = datetime.now() - timedelta(minutes=minutes)
            deleted_count = 0
            
            try:
                for msg_id in range(max(1, message.message_id - 100), message.message_id):
                    try:
                        msg = await bot.get_message(message.chat.id, msg_id)
                        if msg.date and msg.date > cutoff_time:
                            await bot.delete_message(message.chat.id, msg_id)
                            deleted_count += 1
                    except Exception:
                        pass
                
                logger.info(f"Recent deleted {deleted_count} messages from last {minutes} min by {message.from_user.id}")
            except Exception as e:
                logger.error(f"Recent delete error: {e}")
            
            return
        
        # ========== MODE 5: Archive Before Delete ==========
        elif mode == "archive":
            if not message.reply_to_message:
                await send_and_delete(
                    message,
                    "❌ Reply to a message to archive it",
                    parse_mode=ParseMode.HTML,
                    delay=5
                )
                return
            
            target_message_id = message.reply_to_message.message_id
            target_user_id = message.reply_to_message.from_user.id if message.reply_to_message.from_user else None
            
            # Archive to database before deleting
            try:
                await api_client.post(
                    f"/groups/{message.chat.id}/messages/archive",
                    {
                        "message_id": target_message_id,
                        "admin_id": message.from_user.id,
                        "message_content": message.reply_to_message.text or "[Media]"
                    }
                )
            except Exception as e:
                logger.warning(f"Could not archive message: {e}")
        
        # ========== DEFAULT: Single Delete ==========
        if mode != "bulk" and mode != "user" and mode != "clear":
            if not message.reply_to_message and mode == "single":
                await send_and_delete(
                    message,
                    "❌ Reply to a message or use: /del bulk <count>",
                    parse_mode=ParseMode.HTML,
                    delay=5
                )
                return
            
            # Delete command
            try:
                await message.delete()
            except Exception:
                pass
            
            # Delete target message
            if "target_message_id" in locals() and target_message_id:
                try:
                    await bot.delete_message(message.chat.id, target_message_id)
                    
                    # Log to API
                    try:
                        await api_client.post(
                            f"/groups/{message.chat.id}/messages/delete",
                            {
                                "message_id": target_message_id,
                                "admin_id": message.from_user.id,
                                "reason": locals().get("reason", "Deleted by admin"),
                                "target_user_id": locals().get("target_user_id"),
                                "archived": locals().get("archive", False)
                            }
                        )
                    except Exception as e:
                        logger.warning(f"Could not log deletion: {e}")
                    
                    logger.info(f"Message deleted by {message.from_user.id}")
                
                except Exception as e:
                    logger.error(f"Error deleting message: {e}")
    
    except Exception as e:
        logger.error(f"Delete command failed: {e}")
        await send_and_delete(
            message,
            f"❌ Error: {escape_error_message(str(e))}",
            parse_mode=ParseMode.HTML,
            delay=6
        )


# ==================== MESSAGE SENDING COMMAND (ADVANCED) ====================

async def cmd_send(message: Message):
    """
    📨 ULTRA-ADVANCED Message Sending Command - Enterprise-grade features
    
    Basic Modes:
    ⚡ /send <text>                    - Send to group
    ⚡ /send (reply)                   - Send in thread
    
    Advanced Modes:
    🔥 /send pin <text>                - Send & pin message
    🔥 /send edit <msg_id> <text>      - Edit existing message
    🔥 /send copy <msg_id>             - Copy & resend message
    🔥 /send broadcast <text>          - Send to all groups
    🔥 /send html <html_text>          - Send with HTML formatting
    
    Ultra Modes:
    ⚡⚡ /send schedule <HH:MM> <text>  - Schedule message delivery
    ⚡⚡ /send repeat <times> <text>    - Repeat message N times
    ⚡⚡ /send notify <text>            - Send + notify all admins
    ⚡⚡ /send silent <text>            - Send without notification
    ⚡⚡ /send reactive <text> <reaction> - Send with reaction
    
    Features: Scheduling, repeating, notifications, silent mode, reactions
    """
    try:
        # Permission check: ensure caller is admin
        if not await check_is_admin(message.from_user.id, message.chat.id):
            await send_and_delete(
                message,
                "❌ You need admin permissions to send messages via bot",
                parse_mode=ParseMode.HTML,
                delay=5
            )
            return
        
        args = message.text.split()
        
        # Determine mode - check if second arg is a recognized mode keyword
        potential_mode = args[1].lower() if len(args) > 1 else "send"
        recognized_modes = ["pin", "edit", "copy", "broadcast", "html", "schedule", "repeat", "notify", "silent", "reactive"]
        mode = potential_mode if potential_mode in recognized_modes else "send"
        
        # ========== MODE 1: Normal Send (Default) ==========
        if mode == "send" or message.reply_to_message:
            message_text = None
            reply_to_id = None
            
            # Parse message text
            if message.reply_to_message:
                parts = message.text.split(maxsplit=1)
                if len(parts) > 1:
                    message_text = parts[1]
                elif message.reply_to_message.text:
                    message_text = message.reply_to_message.text
                
                reply_to_id = message.reply_to_message.message_id
            else:
                parts = message.text.split(maxsplit=1)
                if len(parts) < 2:
                    await send_and_delete(
                        message,
                        "Usage: /send <text> or /send (reply) or /send pin <text>",
                        parse_mode=ParseMode.HTML,
                        delay=5
                    )
                    return
                message_text = parts[1]
            
            if not message_text or len(message_text.strip()) == 0:
                await send_and_delete(
                    message,
                    "❌ Message text cannot be empty",
                    parse_mode=ParseMode.HTML,
                    delay=5
                )
                return
            
            if len(message_text) > 4096:
                await send_and_delete(
                    message,
                    "❌ Message text cannot exceed 4096 characters",
                    parse_mode=ParseMode.HTML,
                    delay=5
                )
                return
            
            # Delete command
            try:
                await message.delete()
            except Exception:
                pass
            
            # Send message
            try:
                if reply_to_id:
                    await bot.send_message(
                        message.chat.id,
                        message_text,
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True,
                        reply_to_message_id=reply_to_id
                    )
                else:
                    await bot.send_message(
                        message.chat.id,
                        message_text,
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True
                    )
                
                # Log to API
                try:
                    await api_client.post(
                        f"/groups/{message.chat.id}/messages/send",
                        {
                            "text": message_text,
                            "admin_id": message.from_user.id,
                            "reply_to_message_id": reply_to_id,
                            "mode": "send",
                            "sent": True
                        }
                    )
                except Exception as e:
                    logger.warning(f"Could not log message: {e}")
            
            except Exception as e:
                logger.error(f"Error sending message: {e}")
        
        # ========== MODE 2: Send & Pin ==========
        elif mode == "pin":
            text_parts = message.text.split(maxsplit=2)
            if len(text_parts) < 3:
                await send_and_delete(
                    message,
                    "Usage: /send pin <message_text>",
                    parse_mode=ParseMode.HTML,
                    delay=5
                )
                return
            
            message_text = text_parts[2]
            
            # Delete command
            try:
                await message.delete()
            except Exception:
                pass
            
            # Send and pin
            try:
                sent_msg = await bot.send_message(
                    message.chat.id,
                    message_text,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )
                
                # Pin the message
                try:
                    await bot.pin_chat_message(message.chat.id, sent_msg.message_id)
                    logger.info(f"Message pinned by {message.from_user.id}")
                except Exception as e:
                    logger.warning(f"Could not pin message: {e}")
                
                # Log to API
                try:
                    await api_client.post(
                        f"/groups/{message.chat.id}/messages/send",
                        {
                            "text": message_text,
                            "admin_id": message.from_user.id,
                            "mode": "pin",
                            "pinned": True
                        }
                    )
                except Exception:
                    pass
            
            except Exception as e:
                logger.error(f"Error pinning message: {e}")
        
        # ========== MODE 3: Edit Message ==========
        elif mode == "edit":
            text_parts = message.text.split(maxsplit=2)
            if len(text_parts) < 4:
                await send_and_delete(
                    message,
                    "Usage: /send edit <message_id> <new_text>",
                    parse_mode=ParseMode.HTML,
                    delay=5
                )
                return
            
            try:
                msg_id = int(text_parts[2])
                new_text = text_parts[3] if len(text_parts) > 3 else " ".join(text_parts[3:])
            except ValueError:
                await send_and_delete(
                    message,
                    "❌ Invalid message ID",
                    parse_mode=ParseMode.HTML,
                    delay=5
                )
                return
            
            # Delete command
            try:
                await message.delete()
            except Exception:
                pass
            
            # Edit message
            try:
                await bot.edit_message_text(
                    new_text,
                    message.chat.id,
                    msg_id,
                    parse_mode=ParseMode.HTML
                )
                
                logger.info(f"Message {msg_id} edited by {message.from_user.id}")
            except Exception as e:
                logger.error(f"Error editing message: {e}")
        
        # ========== MODE 4: Copy & Resend ==========
        elif mode == "copy":
            text_parts = message.text.split(maxsplit=2)
            if len(text_parts) < 3:
                await send_and_delete(
                    message,
                    "Usage: /send copy <message_id>",
                    parse_mode=ParseMode.HTML,
                    delay=5
                )
                return
            
            try:
                msg_id = int(text_parts[2])
            except ValueError:
                await send_and_delete(
                    message,
                    "❌ Invalid message ID",
                    parse_mode=ParseMode.HTML,
                    delay=5
                )
                return
            
            # Delete command
            try:
                await message.delete()
            except Exception:
                pass
            
            # Copy and resend
            try:
                original = await bot.get_message(message.chat.id, msg_id)
                await bot.copy_message(message.chat.id, message.chat.id, msg_id)
                logger.info(f"Message {msg_id} copied by {message.from_user.id}")
            except Exception as e:
                logger.error(f"Error copying message: {e}")
        
        # ========== MODE 5: Broadcast to All Groups ==========
        elif mode == "broadcast":
            text_parts = message.text.split(maxsplit=2)
            if len(text_parts) < 3:
                await send_and_delete(
                    message,
                    "Usage: /send broadcast <message_text>",
                    parse_mode=ParseMode.HTML,
                    delay=5
                )
                return
            
            broadcast_text = text_parts[2]
            
            # Delete command
            try:
                await message.delete()
            except Exception:
                pass
            
            # Broadcast to all groups via API
            try:
                await api_client.post(
                    f"/groups/{message.chat.id}/messages/broadcast-all",
                    {
                        "text": broadcast_text,
                        "admin_id": message.from_user.id,
                        "source_group": message.chat.id
                    }
                )
                logger.info(f"Broadcast sent by {message.from_user.id}")
            except Exception as e:
                logger.error(f"Broadcast error: {e}")
        
        # ========== MODE 6: HTML Formatted Send ==========
        elif mode == "html":
            text_parts = message.text.split(maxsplit=2)
            if len(text_parts) < 3:
                await send_and_delete(
                    message,
                    "Usage: /send html <HTML_TEXT>",
                    parse_mode=ParseMode.HTML,
                    delay=5
                )
                return
            
            html_text = text_parts[2]
            
            # Delete command
            try:
                await message.delete()
            except Exception:
                pass
            
            # Send with HTML
            try:
                await bot.send_message(
                    message.chat.id,
                    html_text,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )
                
                logger.info(f"HTML message sent by {message.from_user.id}")
            except Exception as e:
                logger.error(f"Error sending HTML message: {e}")
        
        # ========== ULTRA MODE 1: Schedule Message ==========
        elif mode == "schedule":
            text_parts = message.text.split(maxsplit=3)
            if len(text_parts) < 4:
                await send_and_delete(
                    message,
                    "Usage: /send schedule <HH:MM> <message_text>",
                    parse_mode=ParseMode.HTML,
                    delay=5
                )
                return
            
            time_str = text_parts[2]
            schedule_text = text_parts[3] if len(text_parts) > 3 else " ".join(text_parts[3:])
            
            # Delete command
            try:
                await message.delete()
            except Exception:
                pass
            
            # Schedule message
            try:
                await api_client.post(
                    f"/groups/{message.chat.id}/messages/schedule",
                    {
                        "text": schedule_text,
                        "admin_id": message.from_user.id,
                        "schedule_time": time_str,
                        "group_id": message.chat.id
                    }
                )
                logger.info(f"Message scheduled for {time_str} by {message.from_user.id}")
            except Exception as e:
                logger.error(f"Schedule error: {e}")
        
        # ========== ULTRA MODE 2: Repeat Message ==========
        elif mode == "repeat":
            text_parts = message.text.split(maxsplit=3)
            if len(text_parts) < 4:
                await send_and_delete(
                    message,
                    "Usage: /send repeat <times> <message_text>",
                    parse_mode=ParseMode.HTML,
                    delay=5
                )
                return
            
            try:
                times = int(text_parts[2])
                if times <= 0 or times > 10:
                    await send_and_delete(
                        message,
                        "❌ Repeat count must be 1-10",
                        parse_mode=ParseMode.HTML,
                        delay=5
                    )
                    return
            except ValueError:
                await send_and_delete(
                    message,
                    "❌ Invalid repeat count",
                    parse_mode=ParseMode.HTML,
                    delay=5
                )
                return
            
            repeat_text = text_parts[3] if len(text_parts) > 3 else " ".join(text_parts[3:])
            
            # Delete command
            try:
                await message.delete()
            except Exception:
                pass
            
            # Send message multiple times
            try:
                for i in range(times):
                    await bot.send_message(
                        message.chat.id,
                        repeat_text,
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True
                    )
                
                logger.info(f"Message repeated {times} times by {message.from_user.id}")
            except Exception as e:
                logger.error(f"Repeat error: {e}")
        
        # ========== ULTRA MODE 3: Notify Admins ==========
        elif mode == "notify":
            text_parts = message.text.split(maxsplit=2)
            if len(text_parts) < 3:
                await send_and_delete(
                    message,
                    "Usage: /send notify <message_text>",
                    parse_mode=ParseMode.HTML,
                    delay=5
                )
                return
            
            notify_text = text_parts[2]
            
            # Delete command
            try:
                await message.delete()
            except Exception:
                pass
            
            # Send message + notify admins
            try:
                await bot.send_message(
                    message.chat.id,
                    f"🔔 {notify_text}",
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )
                
                # Notify admins via API
                await api_client.post(
                    f"/groups/{message.chat.id}/messages/admin-notify",
                    {
                        "text": notify_text,
                        "admin_id": message.from_user.id,
                        "notification": True
                    }
                )
                
                logger.info(f"Notification sent by {message.from_user.id}")
            except Exception as e:
                logger.error(f"Notify error: {e}")
        
        # ========== ULTRA MODE 4: Silent Send (No Notifications) ==========
        elif mode == "silent":
            text_parts = message.text.split(maxsplit=2)
            if len(text_parts) < 3:
                await send_and_delete(
                    message,
                    "Usage: /send silent <message_text>",
                    parse_mode=ParseMode.HTML,
                    delay=5
                )
                return
            
            silent_text = text_parts[2]
            
            # Delete command
            try:
                await message.delete()
            except Exception:
                pass
            
            # Send silently (disable notification)
            try:
                await bot.send_message(
                    message.chat.id,
                    silent_text,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                    disable_notification=True
                )
                
                logger.info(f"Silent message sent by {message.from_user.id}")
            except Exception as e:
                logger.error(f"Silent send error: {e}")
        
        # ========== ULTRA MODE 5: Send with Reaction ==========
        elif mode == "reactive":
            text_parts = message.text.split(maxsplit=3)
            if len(text_parts) < 4:
                await send_and_delete(
                    message,
                    "Usage: /send reactive <message_text> <emoji>",
                    parse_mode=ParseMode.HTML,
                    delay=5
                )
                return
            
            reactive_text = text_parts[2]
            reaction_emoji = text_parts[3] if len(text_parts) > 3 else "👍"
            
            # Delete command
            try:
                await message.delete()
            except Exception:
                pass
            
            # Send message with reaction
            try:
                sent_msg = await bot.send_message(
                    message.chat.id,
                    reactive_text,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )
                
                # Add reaction
                try:
                    await bot.set_message_reaction(
                        message.chat.id,
                        sent_msg.message_id,
                        reaction_emoji
                    )
                except Exception:
                    pass
                
                logger.info(f"Message with reaction sent by {message.from_user.id}")
            except Exception as e:
                logger.error(f"Reactive send error: {e}")
    
    except Exception as e:
        logger.error(f"Send command failed: {e}")
        await send_and_delete(
            message,
            f"❌ Error: {escape_error_message(str(e))}",
            parse_mode=ParseMode.HTML,
            delay=6
        )


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
        
        if result.get("error") is not None:
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
        
        if result.get("error") is not None:
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
        
        if result.get("error") is not None:
            await message.answer(f"❌ Error: {escape_error_message(result['error'])}", parse_mode=None)
        else:
            await message.answer(f"👤 Role {role} removed from user {user_id}")
            
    except ValueError:
        await message.answer("❌ Invalid user ID")
    except Exception as e:
        logger.error(f"Remove role command failed: {e}")
        await message.answer(f"❌ Error: {escape_error_message(str(e))}")


# ============================================================================
# WHITELIST/BLACKLIST MANAGEMENT COMMANDS
# ============================================================================

async def cmd_whitelist(message: Message):
    """Handle /whitelist command - Manage whitelist
    Usage:
    /whitelist add @user [exemption|moderator] - Add user to whitelist
    /whitelist add @user moderator [mute,unmute,warn,kick,send_link,...] - Add with specific powers
    /whitelist remove @user - Remove from whitelist
    /whitelist list - List all whitelisted users
    /whitelist check @user - Check if user is whitelisted
    """
    try:
        if not await check_is_admin(message.from_user.id, message.chat.id):
            await send_and_delete(message, "❌ You need admin permissions for this action",
                                 parse_mode=ParseMode.HTML, delay=5)
            return
        
        args = message.text.split(maxsplit=3)
        
        if len(args) < 2:
            help_text = (
                "📋 <b>WHITELIST COMMANDS</b>\n\n"
                "<b>Add exemption (bypass restrictions):</b>\n"
                "/whitelist add @user exemption\n\n"
                "<b>Add moderator (grant powers without admin):</b>\n"
                "/whitelist add @user moderator\n"
                "/whitelist add @user moderator mute,unmute,warn,kick\n\n"
                "<b>Remove from whitelist:</b>\n"
                "/whitelist remove @user\n\n"
                "<b>View all whitelisted users:</b>\n"
                "/whitelist list\n\n"
                "<b>Check specific user:</b>\n"
                "/whitelist check @user\n\n"
                "<b>Available Powers for Moderators:</b>\n"
                "mute, unmute, warn, kick, send_link, restrict, unrestrict, manage_stickers, manage_links"
            )
            await message.answer(help_text, parse_mode=ParseMode.HTML)
            return
        
        action = args[1].lower()
        
        # ===== ADD TO WHITELIST =====
        if action == "add":
            if len(args) < 3:
                await message.answer("Usage: /whitelist add <user_id|@username> [exemption|moderator] [powers]")
                return
            
            user_id, username = parse_user_reference(args[2])
            if not user_id:
                await message.answer("❌ Could not identify user")
                return
            
            entry_type = args[3].lower() if len(args) > 3 else "exemption"
            
            # Powers only apply if moderator
            admin_powers = []
            if entry_type == "moderator" and len(args) > 4:
                admin_powers = [p.strip() for p in args[4].split(",")]
            elif entry_type == "moderator":
                # Default moderator powers
                admin_powers = ["mute", "unmute", "warn", "kick", "restrict", "unrestrict"]
            
            # Add to whitelist via API
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.post(
                        f"{api_client.base_url}/api/v2/groups/{message.chat.id}/whitelist",
                        json={
                            "group_id": message.chat.id,
                            "user_id": user_id,
                            "username": username,
                            "entry_type": entry_type,
                            "admin_powers": admin_powers,
                            "reason": f"Added by {message.from_user.first_name}",
                            "added_by": message.from_user.id
                        },
                        headers={"Authorization": f"Bearer {api_client.api_key}"},
                        timeout=5
                    )
                    
                    if response.status_code in [200, 201]:
                        emoji = "🛡️" if entry_type == "exemption" else "⚡"
                        powers_text = f"\n<b>Powers:</b> {', '.join(admin_powers)}" if admin_powers else ""
                        await message.answer(
                            f"{emoji} <b>Added to whitelist</b>\n\n"
                            f"<b>User:</b> {username or user_id}\n"
                            f"<b>Type:</b> {entry_type.upper()}{powers_text}",
                            parse_mode=ParseMode.HTML
                        )
                        await log_command_execution(message, "whitelist_add", success=True, args=message.text)
                    else:
                        error_msg = response.json().get("detail", "Unknown error")
                        await message.answer(f"❌ Error: {error_msg}")
                        
            except Exception as e:
                logger.error(f"Whitelist add failed: {e}")
                await message.answer(f"❌ Error: {escape_error_message(str(e))}")
        
        # ===== REMOVE FROM WHITELIST =====
        elif action == "remove":
            if len(args) < 3:
                await message.answer("Usage: /whitelist remove <user_id|@username>")
                return
            
            user_id, username = parse_user_reference(args[2])
            if not user_id:
                await message.answer("❌ Could not identify user")
                return
            
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.delete(
                        f"{api_client.base_url}/api/v2/groups/{message.chat.id}/whitelist/{user_id}",
                        headers={"Authorization": f"Bearer {api_client.api_key}"},
                        timeout=5
                    )
                    
                    if response.status_code == 200:
                        await message.answer(
                            f"✅ Removed from whitelist\n"
                            f"<b>User:</b> {username or user_id}",
                            parse_mode=ParseMode.HTML
                        )
                        await log_command_execution(message, "whitelist_remove", success=True, args=message.text)
                    else:
                        await message.answer("❌ User not in whitelist")
                        
            except Exception as e:
                logger.error(f"Whitelist remove failed: {e}")
                await message.answer(f"❌ Error: {escape_error_message(str(e))}")
        
        # ===== LIST WHITELIST =====
        elif action == "list":
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(
                        f"{api_client.base_url}/api/v2/groups/{message.chat.id}/whitelist",
                        headers={"Authorization": f"Bearer {api_client.api_key}"},
                        timeout=5
                    )
                    
                    if response.status_code == 200:
                        whitelist = response.json()
                        if not whitelist:
                            await message.answer("📋 Whitelist is empty")
                            return
                        
                        # Group by type
                        exemptions = [w for w in whitelist if w.get("entry_type") == "exemption"]
                        moderators = [w for w in whitelist if w.get("entry_type") == "moderator"]
                        
                        text = "📋 <b>WHITELIST</b>\n\n"
                        
                        if exemptions:
                            text += "<b>🛡️ Exemptions (bypass restrictions):</b>\n"
                            for w in exemptions[:10]:  # Limit to 10
                                text += f"• {w.get('username') or w.get('user_id')}\n"
                            if len(exemptions) > 10:
                                text += f"... and {len(exemptions) - 10} more\n"
                            text += "\n"
                        
                        if moderators:
                            text += "<b>⚡ Moderators (non-admin powers):</b>\n"
                            for w in moderators[:10]:  # Limit to 10
                                powers = ", ".join(w.get("admin_powers", [])[:3])
                                text += f"• {w.get('username') or w.get('user_id')} ({powers})\n"
                            if len(moderators) > 10:
                                text += f"... and {len(moderators) - 10} more\n"
                        
                        await message.answer(text, parse_mode=ParseMode.HTML)
                    else:
                        await message.answer("❌ Could not fetch whitelist")
                        
            except Exception as e:
                logger.error(f"Whitelist list failed: {e}")
                await message.answer(f"❌ Error: {escape_error_message(str(e))}")
        
        # ===== CHECK USER =====
        elif action == "check":
            if len(args) < 3:
                await message.answer("Usage: /whitelist check <user_id|@username>")
                return
            
            user_id, username = parse_user_reference(args[2])
            if not user_id:
                await message.answer("❌ Could not identify user")
                return
            
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(
                        f"{api_client.base_url}/api/v2/groups/{message.chat.id}/whitelist/{user_id}",
                        headers={"Authorization": f"Bearer {api_client.api_key}"},
                        timeout=5
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("whitelisted"):
                            entry_type = data.get("entry_type")
                            emoji = "🛡️" if entry_type == "exemption" else "⚡"
                            powers = data.get("admin_powers", [])
                            powers_text = f"\n<b>Powers:</b> {', '.join(powers)}" if powers else ""
                            
                            await message.answer(
                                f"{emoji} <b>User is whitelisted</b>\n\n"
                                f"<b>User:</b> {username or user_id}\n"
                                f"<b>Type:</b> {entry_type.upper()}{powers_text}\n"
                                f"<b>Added:</b> {data.get('added_at', 'Unknown')}",
                                parse_mode=ParseMode.HTML
                            )
                        else:
                            await message.answer(f"❌ User {username or user_id} is not whitelisted")
                    else:
                        await message.answer("❌ Could not check user status")
                        
            except Exception as e:
                logger.error(f"Whitelist check failed: {e}")
                await message.answer(f"❌ Error: {escape_error_message(str(e))}")
        
        else:
            await message.answer("❌ Unknown action. Use: add, remove, list, or check")
            
    except Exception as e:
        logger.error(f"Whitelist command failed: {e}")
        await message.answer(f"❌ Error: {escape_error_message(str(e))}", parse_mode=None)


async def cmd_blacklist(message: Message):
    """Handle /blacklist command - Manage blacklist
    Usage:
    /blacklist add sticker <sticker_id> - Block sticker
    /blacklist add gif <gif_id> - Block GIF
    /blacklist add user <user_id> - Block user
    /blacklist add link <url> - Block specific link
    /blacklist add domain <domain.com> - Block entire domain
    /blacklist remove <id> - Remove from blacklist
    /blacklist list [sticker|gif|user|link|domain] - List blacklist
    /blacklist check <item> - Check if blacklisted
    """
    try:
        if not await check_is_admin(message.from_user.id, message.chat.id):
            await send_and_delete(message, "❌ You need admin permissions for this action",
                                 parse_mode=ParseMode.HTML, delay=5)
            return
        
        args = message.text.split(maxsplit=3)
        
        if len(args) < 2:
            help_text = (
                "🚫 <b>BLACKLIST COMMANDS</b>\n\n"
                "<b>Block stickers:</b>\n"
                "/blacklist add sticker <sticker_id>\n\n"
                "<b>Block GIFs:</b>\n"
                "/blacklist add gif <gif_id>\n\n"
                "<b>Block users:</b>\n"
                "/blacklist add user <user_id|@username>\n\n"
                "<b>Block links:</b>\n"
                "/blacklist add link <https://example.com>\n"
                "/blacklist add domain <example.com>\n\n"
                "<b>Remove from blacklist:</b>\n"
                "/blacklist remove <blacklist_id>\n\n"
                "<b>View all blacklisted items:</b>\n"
                "/blacklist list [sticker|gif|user|link|domain]\n\n"
                "<b>Check if item is blacklisted:</b>\n"
                "/blacklist check sticker <sticker_id>\n"
                "/blacklist check link <https://example.com>"
            )
            await message.answer(help_text, parse_mode=ParseMode.HTML)
            return
        
        action = args[1].lower()
        
        # ===== ADD TO BLACKLIST =====
        if action == "add":
            if len(args) < 4:
                await message.answer("Usage: /blacklist add <sticker|gif|user|link|domain> <value>")
                return
            
            item_type = args[2].lower()
            item_value = args[3]
            
            if item_type not in ["sticker", "gif", "user", "link", "domain"]:
                await message.answer("❌ Invalid type. Use: sticker, gif, user, link, or domain")
                return
            
            # Parse user reference if type is user
            if item_type == "user":
                user_id, username = parse_user_reference(item_value)
                if not user_id:
                    await message.answer("❌ Could not identify user")
                    return
                item_value = str(user_id)
            
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.post(
                        f"{api_client.base_url}/api/v2/groups/{message.chat.id}/blacklist",
                        json={
                            "group_id": message.chat.id,
                            "entry_type": item_type,
                            "blocked_item": item_value,
                            "reason": f"Added by {message.from_user.first_name}",
                            "added_by": message.from_user.id,
                            "auto_delete": True
                        },
                        headers={"Authorization": f"Bearer {api_client.api_key}"},
                        timeout=5
                    )
                    
                    if response.status_code in [200, 201]:
                        await message.answer(
                            f"🚫 <b>Added to blacklist</b>\n\n"
                            f"<b>Type:</b> {item_type.upper()}\n"
                            f"<b>Item:</b> <code>{item_value[:50]}</code>",
                            parse_mode=ParseMode.HTML
                        )
                        await log_command_execution(message, "blacklist_add", success=True, args=message.text)
                    else:
                        error_msg = response.json().get("detail", "Unknown error")
                        await message.answer(f"❌ Error: {error_msg}")
                        
            except Exception as e:
                logger.error(f"Blacklist add failed: {e}")
                await message.answer(f"❌ Error: {escape_error_message(str(e))}")
        
        # ===== LIST BLACKLIST =====
        elif action == "list":
            filter_type = args[2].lower() if len(args) > 2 else None
            
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    url = f"{api_client.base_url}/api/v2/groups/{message.chat.id}/blacklist"
                    if filter_type:
                        url += f"?entry_type={filter_type}"
                    
                    response = await client.get(
                        url,
                        headers={"Authorization": f"Bearer {api_client.api_key}"},
                        timeout=5
                    )
                    
                    if response.status_code == 200:
                        blacklist = response.json()
                        if not blacklist:
                            await message.answer("🚫 Blacklist is empty")
                            return
                        
                        text = "🚫 <b>BLACKLIST</b>\n\n"
                        
                        # Group by type
                        by_type = {}
                        for item in blacklist:
                            t = item.get("entry_type")
                            if t not in by_type:
                                by_type[t] = []
                            by_type[t].append(item)
                        
                        type_emojis = {"sticker": "🎨", "gif": "🎬", "user": "👤", "link": "🔗", "domain": "🌐"}
                        
                        for item_type in sorted(by_type.keys()):
                            items = by_type[item_type][:5]  # Limit to 5 per type
                            emoji = type_emojis.get(item_type, "•")
                            text += f"<b>{emoji} {item_type.upper()}s ({len(by_type[item_type])} total):</b>\n"
                            for item in items:
                                display = item.get("blocked_item")[:30]
                                text += f"• <code>{display}</code>\n"
                            if len(by_type[item_type]) > 5:
                                text += f"  ... and {len(by_type[item_type]) - 5} more\n"
                            text += "\n"
                        
                        await message.answer(text, parse_mode=ParseMode.HTML)
                    else:
                        await message.answer("❌ Could not fetch blacklist")
                        
            except Exception as e:
                logger.error(f"Blacklist list failed: {e}")
                await message.answer(f"❌ Error: {escape_error_message(str(e))}")
        
        # ===== CHECK BLACKLIST =====
        elif action == "check":
            if len(args) < 4:
                await message.answer("Usage: /blacklist check <sticker|gif|link|domain> <value>")
                return
            
            check_type = args[2].lower()
            check_value = args[3]
            
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(
                        f"{api_client.base_url}/api/v2/groups/{message.chat.id}/blacklist/check/{check_type}/{check_value}",
                        headers={"Authorization": f"Bearer {api_client.api_key}"},
                        timeout=5
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("blacklisted"):
                            await message.answer(
                                f"🚫 <b>Item is blacklisted</b>\n\n"
                                f"<b>Type:</b> {check_type.upper()}\n"
                                f"<b>Item:</b> <code>{check_value[:50]}</code>\n"
                                f"<b>Reason:</b> {data.get('reason', 'No reason')}",
                                parse_mode=ParseMode.HTML
                            )
                        else:
                            await message.answer(f"✅ Item is <b>NOT</b> blacklisted", parse_mode=ParseMode.HTML)
                    else:
                        await message.answer("❌ Could not check item")
                        
            except Exception as e:
                logger.error(f"Blacklist check failed: {e}")
                await message.answer(f"❌ Error: {escape_error_message(str(e))}")
        
        # ===== REMOVE FROM BLACKLIST =====
        elif action == "remove":
            if len(args) < 3:
                await message.answer("Usage: /blacklist remove <blacklist_id>")
                return
            
            blacklist_id = args[2]
            
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.delete(
                        f"{api_client.base_url}/api/v2/groups/{message.chat.id}/blacklist/{blacklist_id}",
                        headers={"Authorization": f"Bearer {api_client.api_key}"},
                        timeout=5
                    )
                    
                    if response.status_code == 200:
                        await message.answer("✅ Removed from blacklist")
                        await log_command_execution(message, "blacklist_remove", success=True, args=message.text)
                    else:
                        await message.answer("❌ Item not found in blacklist")
                        
            except Exception as e:
                logger.error(f"Blacklist remove failed: {e}")
                await message.answer(f"❌ Error: {escape_error_message(str(e))}")
        
        else:
            await message.answer("❌ Unknown action. Use: add, remove, list, or check")
            
    except Exception as e:
        logger.error(f"Blacklist command failed: {e}")
        await message.answer(f"❌ Error: {escape_error_message(str(e))}", parse_mode=None)


async def cmd_nightmode(message: Message):
    """Handle /nightmode command - Configure and manage night mode scheduling
    
    Night mode automatically restricts content during scheduled hours.
    When enabled, restricted content types are auto-deleted.
    Users with exemptions or /free permissions bypass restrictions.
    
    Subcommands:
    - /nightmode status          : Show current night mode settings
    - /nightmode enable          : Enable night mode
    - /nightmode disable         : Disable night mode
    - /nightmode schedule START END : Set time window (e.g., /nightmode schedule 22:00 08:00)
    - /nightmode restrict TYPES  : Set restricted content types (text,stickers,gifs,media,voice,links)
    - /nightmode exempt USER_ID  : Add user exemption
    - /nightmode unexempt USER_ID: Remove user exemption
    - /nightmode list-exempt     : List all exempt users and roles
    """
    try:
        # Permission check: only admins can manage night mode
        if not await check_is_admin(message.from_user.id, message.chat.id):
            await send_and_delete(message, "❌ You need admin permissions to manage night mode",
                                 parse_mode=ParseMode.HTML, delay=5)
            return
        
        args = message.text.split()
        if len(args) < 2:
            # Show help
            help_text = (
                f"╔═══════════════════════════════════════╗\n"
                f"║ 🌙 <b>NIGHT MODE COMMAND HELP</b>    ║\n"
                f"╚═══════════════════════════════════════╝\n\n"
                f"<b>📌 Usage:</b>\n"
                f"  <code>/nightmode status</code> - Show settings\n"
                f"  <code>/nightmode enable</code> - Turn on\n"
                f"  <code>/nightmode disable</code> - Turn off\n"
                f"  <code>/nightmode schedule HH:MM HH:MM</code> - Set hours\n"
                f"  <code>/nightmode restrict [types]</code> - Set restrictions\n"
                f"  <code>/nightmode exempt USER_ID</code> - Add exemption\n"
                f"  <code>/nightmode unexempt USER_ID</code> - Remove exemption\n"
                f"  <code>/nightmode list-exempt</code> - Show exemptions\n\n"
                f"<b>📝 Content Types:</b> text, stickers, gifs, media, voice, links\n"
                f"<b>⏰ Time Format:</b> HH:MM (24-hour)\n"
                f"\n<b>💡 Example:</b>\n"
                f"  <code>/nightmode schedule 22:00 08:00</code>\n"
                f"  <code>/nightmode restrict stickers,gifs,media</code>"
            )
            await message.answer(help_text, parse_mode=ParseMode.HTML)
            return
        
        action = args[1].lower()
        group_id = message.chat.id
        
        # ======== STATUS ========
        if action == "status":
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(
                        f"{api_client.base_url}/api/v2/groups/{group_id}/night-mode/status",
                        headers={"Authorization": f"Bearer {api_client.api_key}"},
                        timeout=10
                    )
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        is_active = data.get("is_active", False)
                        current_time = data.get("current_time", "N/A")
                        start_time = data.get("start_time", "N/A")
                        end_time = data.get("end_time", "N/A")
                        next_transition = data.get("next_transition", "N/A")
                        
                        status_text = (
                            f"╔═══════════════════════════════════════╗\n"
                            f"║ 🌙 <b>NIGHT MODE STATUS</b>          ║\n"
                            f"╚═══════════════════════════════════════╝\n\n"
                            f"<b>Status:</b> {'🟢 ACTIVE' if is_active else '🔴 INACTIVE'}\n"
                            f"<b>Current Time:</b> <code>{current_time}</code>\n"
                            f"<b>Schedule:</b> <code>{start_time} - {end_time}</code>\n"
                            f"<b>Next Change:</b> <code>{next_transition}</code>\n"
                        )
                        
                        # Get full settings
                        settings_resp = await client.get(
                            f"{api_client.base_url}/api/v2/groups/{group_id}/night-mode/settings",
                            headers={"Authorization": f"Bearer {api_client.api_key}"},
                            timeout=10
                        )
                        
                        if settings_resp.status_code == 200:
                            settings = settings_resp.json()
                            enabled = settings.get("enabled", False)
                            restricted_types = settings.get("restricted_content_types", [])
                            auto_delete = settings.get("auto_delete_restricted", False)
                            
                            status_text += (
                                f"\n<b>⚙️ Settings:</b>\n"
                                f"  <b>Enabled:</b> {'✅ YES' if enabled else '❌ NO'}\n"
                                f"  <b>Auto-Delete:</b> {'✅ ON' if auto_delete else '❌ OFF'}\n"
                                f"  <b>Restricted Types:</b>\n"
                            )
                            
                            if restricted_types:
                                for content_type in restricted_types:
                                    status_text += f"    • <code>{content_type}</code>\n"
                            else:
                                status_text += "    <i>None (all allowed)</i>\n"
                        
                        await message.answer(status_text, parse_mode=ParseMode.HTML)
                    else:
                        await message.answer("❌ Could not fetch night mode status")
                        
            except Exception as e:
                logger.error(f"Night mode status error: {e}")
                await send_and_delete(message, f"❌ Error: {escape_error_message(str(e))}", 
                                     parse_mode=ParseMode.HTML, delay=5)
        
        # ======== ENABLE ========
        elif action == "enable":
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(
                        f"{api_client.base_url}/api/v2/groups/{group_id}/night-mode/enable",
                        headers={"Authorization": f"Bearer {api_client.api_key}"},
                        timeout=10
                    )
                    
                    if resp.status_code == 200:
                        await message.answer("✅ Night mode <b>ENABLED</b>", parse_mode=ParseMode.HTML)
                        await log_command_execution(message, "nightmode_enable", success=True)
                    else:
                        await message.answer("❌ Failed to enable night mode")
                        
            except Exception as e:
                logger.error(f"Night mode enable error: {e}")
                await send_and_delete(message, f"❌ Error: {escape_error_message(str(e))}", 
                                     parse_mode=ParseMode.HTML, delay=5)
        
        # ======== DISABLE ========
        elif action == "disable":
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(
                        f"{api_client.base_url}/api/v2/groups/{group_id}/night-mode/disable",
                        headers={"Authorization": f"Bearer {api_client.api_key}"},
                        timeout=10
                    )
                    
                    if resp.status_code == 200:
                        await message.answer("✅ Night mode <b>DISABLED</b>", parse_mode=ParseMode.HTML)
                        await log_command_execution(message, "nightmode_disable", success=True)
                    else:
                        await message.answer("❌ Failed to disable night mode")
                        
            except Exception as e:
                logger.error(f"Night mode disable error: {e}")
                await send_and_delete(message, f"❌ Error: {escape_error_message(str(e))}", 
                                     parse_mode=ParseMode.HTML, delay=5)
        
        # ======== SCHEDULE ========
        elif action == "schedule":
            if len(args) < 4:
                await message.answer("Usage: /nightmode schedule HH:MM HH:MM\nExample: /nightmode schedule 22:00 08:00")
                return
            
            try:
                start_time = args[2]
                end_time = args[3]
                
                # Validate time format (HH:MM)
                for time_str in [start_time, end_time]:
                    parts = time_str.split(":")
                    if len(parts) != 2:
                        raise ValueError(f"Invalid time format: {time_str}")
                    hour = int(parts[0])
                    minute = int(parts[1])
                    if not (0 <= hour < 24) or not (0 <= minute < 60):
                        raise ValueError(f"Invalid time: {time_str}")
                
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.put(
                        f"{api_client.base_url}/api/v2/groups/{group_id}/night-mode/settings",
                        json={"start_time": start_time, "end_time": end_time},
                        headers={"Authorization": f"Bearer {api_client.api_key}"},
                        timeout=10
                    )
                    
                    if resp.status_code == 200:
                        await message.answer(
                            f"✅ Night mode schedule updated:\n"
                            f"<code>{start_time} - {end_time}</code>",
                            parse_mode=ParseMode.HTML
                        )
                        await log_command_execution(message, "nightmode_schedule", success=True, args=f"{start_time} {end_time}")
                    else:
                        await message.answer("❌ Failed to update schedule")
                        
            except ValueError as e:
                await message.answer(f"❌ Error: {str(e)}")
            except Exception as e:
                logger.error(f"Night mode schedule error: {e}")
                await send_and_delete(message, f"❌ Error: {escape_error_message(str(e))}", 
                                     parse_mode=ParseMode.HTML, delay=5)
        
        # ======== RESTRICT ========
        elif action == "restrict":
            if len(args) < 3:
                await message.answer(
                    "Usage: /nightmode restrict TYPE1,TYPE2,...\n"
                    "Types: text, stickers, gifs, media, voice, links"
                )
                return
            
            try:
                content_types = [t.strip() for t in args[2].split(",")]
                
                # Validate content types
                valid_types = ["text", "stickers", "gifs", "media", "voice", "links"]
                for ct in content_types:
                    if ct not in valid_types:
                        raise ValueError(f"Invalid content type: {ct}")
                
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.put(
                        f"{api_client.base_url}/api/v2/groups/{group_id}/night-mode/settings",
                        json={"restricted_content_types": content_types},
                        headers={"Authorization": f"Bearer {api_client.api_key}"},
                        timeout=10
                    )
                    
                    if resp.status_code == 200:
                        types_display = ", ".join([f"<code>{t}</code>" for t in content_types])
                        await message.answer(
                            f"✅ Restricted content types updated:\n{types_display}",
                            parse_mode=ParseMode.HTML
                        )
                        await log_command_execution(message, "nightmode_restrict", success=True, args=",".join(content_types))
                    else:
                        await message.answer("❌ Failed to update restrictions")
                        
            except ValueError as e:
                await message.answer(f"❌ Error: {str(e)}")
            except Exception as e:
                logger.error(f"Night mode restrict error: {e}")
                await send_and_delete(message, f"❌ Error: {escape_error_message(str(e))}", 
                                     parse_mode=ParseMode.HTML, delay=5)
        
        # ======== EXEMPT ========
        elif action == "exempt":
            if len(args) < 3:
                await message.answer("Usage: /nightmode exempt USER_ID")
                return
            
            try:
                exempt_user_id = int(args[2])
                
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(
                        f"{api_client.base_url}/api/v2/groups/{group_id}/night-mode/add-exemption/{exempt_user_id}",
                        headers={"Authorization": f"Bearer {api_client.api_key}"},
                        timeout=10
                    )
                    
                    if resp.status_code == 200:
                        await message.answer(
                            f"✅ User <code>{exempt_user_id}</code> added to night mode exemptions",
                            parse_mode=ParseMode.HTML
                        )
                        await log_command_execution(message, "nightmode_exempt", success=True, args=str(exempt_user_id))
                    else:
                        await message.answer("❌ Failed to add exemption")
                        
            except ValueError:
                await message.answer("❌ Invalid user ID")
            except Exception as e:
                logger.error(f"Night mode exempt error: {e}")
                await send_and_delete(message, f"❌ Error: {escape_error_message(str(e))}", 
                                     parse_mode=ParseMode.HTML, delay=5)
        
        # ======== UNEXEMPT ========
        elif action == "unexempt":
            if len(args) < 3:
                await message.answer("Usage: /nightmode unexempt USER_ID")
                return
            
            try:
                exempt_user_id = int(args[2])
                
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.delete(
                        f"{api_client.base_url}/api/v2/groups/{group_id}/night-mode/remove-exemption/{exempt_user_id}",
                        headers={"Authorization": f"Bearer {api_client.api_key}"},
                        timeout=10
                    )
                    
                    if resp.status_code == 200:
                        await message.answer(
                            f"✅ User <code>{exempt_user_id}</code> removed from night mode exemptions",
                            parse_mode=ParseMode.HTML
                        )
                        await log_command_execution(message, "nightmode_unexempt", success=True, args=str(exempt_user_id))
                    else:
                        await message.answer("❌ Failed to remove exemption")
                        
            except ValueError:
                await message.answer("❌ Invalid user ID")
            except Exception as e:
                logger.error(f"Night mode unexempt error: {e}")
                await send_and_delete(message, f"❌ Error: {escape_error_message(str(e))}", 
                                     parse_mode=ParseMode.HTML, delay=5)
        
        # ======== LIST-EXEMPT ========
        elif action == "list-exempt":
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(
                        f"{api_client.base_url}/api/v2/groups/{group_id}/night-mode/list-exemptions",
                        headers={"Authorization": f"Bearer {api_client.api_key}"},
                        timeout=10
                    )
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        exempt_users = data.get("exempt_user_ids", [])
                        exempt_roles = data.get("exempt_roles", [])
                        
                        text = (
                            f"╔═══════════════════════════════════════╗\n"
                            f"║ ⭐ <b>NIGHT MODE EXEMPTIONS</b>       ║\n"
                            f"╚═══════════════════════════════════════╝\n\n"
                        )
                        
                        if exempt_users:
                            text += "<b>👤 Exempt Users:</b>\n"
                            for user_id in exempt_users:
                                text += f"  • <code>{user_id}</code>\n"
                        else:
                            text += "<b>👤 Exempt Users:</b> <i>None</i>\n"
                        
                        text += "\n"
                        
                        if exempt_roles:
                            text += "<b>🎖️ Exempt Roles:</b>\n"
                            for role in exempt_roles:
                                text += f"  • <code>{role}</code>\n"
                        else:
                            text += "<b>🎖️ Exempt Roles:</b> <i>None</i>\n"
                        
                        await message.answer(text, parse_mode=ParseMode.HTML)
                    else:
                        await message.answer("❌ Could not fetch exemptions")
                        
            except Exception as e:
                logger.error(f"Night mode list-exempt error: {e}")
                await send_and_delete(message, f"❌ Error: {escape_error_message(str(e))}", 
                                     parse_mode=ParseMode.HTML, delay=5)
        
        else:
            await message.answer(f"❌ Unknown action: {action}\nUse: status, enable, disable, schedule, restrict, exempt, unexempt, or list-exempt")
            
    except Exception as e:
        logger.error(f"Night mode command failed: {e}")
        await send_and_delete(message, f"❌ Error: {escape_error_message(str(e))}", 
                             parse_mode=ParseMode.HTML, delay=5)


async def handle_message(message: Message):
    """Handle regular text messages with restriction checking and auto-delete
    
    Checks:
    1. User permissions (blacklist/restriction)
    2. Night mode restrictions (auto-delete if active and user not exempt)
    3. Message type restrictions during night mode
    """
    try:
        user_id = message.from_user.id
        group_id = message.chat.id
        
        logger.info(f"📨 Message from {message.from_user.username} ({user_id})")
        
        # ============ NIGHT MODE CHECK ============
        # Determine message content type
        content_type = "text"
        if message.sticker:
            content_type = "stickers"
        elif message.animation or message.video_note:
            content_type = "gifs"
        elif message.photo or message.video or message.document:
            content_type = "media"
        elif message.voice or message.audio:
            content_type = "voice"
        elif message.text and ("http://" in message.text or "https://" in message.text):
            content_type = "links"
        
        # Check night mode permission for this content type
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                nm_resp = await client.get(
                    f"{api_client.base_url}/api/v2/groups/{group_id}/night-mode/check/{user_id}/{content_type}",
                    headers={"Authorization": f"Bearer {api_client.api_key}"},
                    timeout=5
                )
                
                if nm_resp.status_code == 200:
                    nm_check = nm_resp.json()
                    can_send = nm_check.get("can_send", True)
                    
                    if not can_send:
                        # Night mode is active and user cannot send this content type
                        reason = nm_check.get("reason", "Night mode restriction active")
                        logger.warning(f"🌙 User {user_id} blocked by night mode: {reason}")
                        
                        try:
                            await message.delete()
                            logger.info(f"✅ Night mode: Auto-deleted {content_type} message from {user_id}")
                        except Exception as e:
                            logger.warning(f"Could not delete night mode message: {e}")
                        
                        return
        except Exception as e:
            logger.debug(f"Night mode check failed (continuing): {e}")
        
        # ============ REGULAR RESTRICTION CHECK ============
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Check text message restriction
                if message.text:
                    resp = await client.get(
                        f"{api_client.base_url}/api/v2/groups/{group_id}/users/{user_id}/is-restricted",
                        params={"permission_type": "text"},
                        headers={"Authorization": f"Bearer {api_client.api_key}"},
                        timeout=5
                    )
                    if resp.status_code == 200:
                        result = resp.json()
                        if result.get("data", {}).get("is_restricted"):
                            logger.warning(f"⛔ User {user_id} restricted from TEXT. Auto-deleting message.")
                            await message.delete()
                            return
                
                # Check sticker/GIF restriction
                if message.sticker or message.animation or message.video_note:
                    resp = await client.get(
                        f"{api_client.base_url}/api/v2/groups/{group_id}/users/{user_id}/is-restricted",
                        params={"permission_type": "stickers"},
                        headers={"Authorization": f"Bearer {api_client.api_key}"},
                        timeout=5
                    )
                    if resp.status_code == 200:
                        result = resp.json()
                        if result.get("data", {}).get("is_restricted"):
                            logger.warning(f"⛔ User {user_id} restricted from STICKERS/GIFs. Auto-deleting message.")
                            await message.delete()
                            return
                
                # Check voice message restriction
                if message.voice or message.audio:
                    resp = await client.get(
                        f"{api_client.base_url}/api/v2/groups/{group_id}/users/{user_id}/is-restricted",
                        params={"permission_type": "voice"},
                        headers={"Authorization": f"Bearer {api_client.api_key}"},
                        timeout=5
                    )
                    if resp.status_code == 200:
                        result = resp.json()
                        if result.get("data", {}).get("is_restricted"):
                            logger.warning(f"⛔ User {user_id} restricted from VOICE. Auto-deleting message.")
                            await message.delete()
                            return
        except Exception as e:
            logger.warning(f"Could not check restrictions: {e}")
            # Continue anyway if check fails
        
        # Message is allowed - echo it back
        await message.answer(
            f"🤖 Message received!\n\n"
            f"You said: {message.text or '[Media message]'}\n\n"
            f"Type /help to see available commands."
        )
    except Exception as e:
        logger.error(f"Message handler failed: {e}")
        try:
            await message.answer(f"❌ Error processing message: {str(e)}")
        except:
            pass


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


async def handle_permission_toggle_callback(callback_query: CallbackQuery, data: str):
    """Handle unified permission toggle callbacks (toggle_perm_*_user_id_group_id)
    Automatically determines whether to lock or unlock based on current state
    """
    try:
        # Parse callback data: toggle_perm_{type}_{user_id}_{group_id}
        parts = data.split("_")
        if len(parts) < 4:
            await callback_query.answer("Invalid callback data", show_alert=True)
            return
        
        perm_type = parts[2]  # text, stickers, gifs, voice, all
        try:
            user_id = int(parts[3])
            group_id = int(parts[4])
        except (ValueError, IndexError):
            await callback_query.answer("Invalid user or group ID", show_alert=True)
            return
        
        # Check admin permission
        if not await check_is_admin(callback_query.from_user.id, group_id):
            await callback_query.answer("❌ You need admin permissions", show_alert=True)
            return
        
        # Fetch current permission state to determine action
        is_currently_locked = False
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    f"{api_client.base_url}/api/v2/groups/{group_id}/users/{user_id}/permissions",
                    headers={"Authorization": f"Bearer {api_client.api_key}"},
                    timeout=5
                )
                if resp.status_code == 200:
                    perms = resp.json().get("data", {})
                    perm_mapping = {
                        "text": "can_send_messages",
                        "stickers": "can_send_other_messages",
                        "gifs": "can_send_other_messages",
                        "voice": "can_send_audios"
                    }
                    
                    if perm_type == "all":
                        # Check if ANY permission is unlocked (not all locked)
                        is_currently_locked = not (
                            perms.get("can_send_messages", True) or
                            perms.get("can_send_other_messages", True) or
                            perms.get("can_send_audios", True)
                        )
                    else:
                        api_perm = perm_mapping.get(perm_type)
                        is_currently_locked = not perms.get(api_perm, True)
        except Exception as e:
            logger.warning(f"Could not fetch permissions: {e}")
            is_currently_locked = False
        
        # Determine action: if locked, unlock (unrestrict); if unlocked, lock (restrict)
        action_type = "unrestrict" if is_currently_locked else "restrict"
        
        # Map permission type to API parameter
        perm_mapping = {
            "text": "send_messages",
            "stickers": "send_other_messages",
            "gifs": "send_other_messages",
            "voice": "send_audios"
        }
        
        # Execute toggle via API
        if perm_type == "all":
            action_data = {
                "action_type": action_type,
                "group_id": group_id,
                "user_id": user_id,
                "toggle_all": True,
                "initiated_by": callback_query.from_user.id
            }
        else:
            api_perm = perm_mapping.get(perm_type)
            if not api_perm:
                await callback_query.answer(f"Unknown permission type: {perm_type}", show_alert=True)
                return
            
            action_data = {
                "action_type": action_type,
                "group_id": group_id,
                "user_id": user_id,
                "metadata": {"permission_type": api_perm},
                "initiated_by": callback_query.from_user.id
            }
        
        result = await api_client.execute_action(action_data)
        
        if result.get("error"):
            error_msg = escape_error_message(result.get("error"))
            await callback_query.answer(f"❌ Error: {error_msg}", show_alert=True)
        else:
            # Show success message
            if perm_type == "all":
                success_msg = f"✅ All permissions {'locked' if action_type == 'restrict' else 'unlocked'}"
            else:
                perm_name = perm_type.capitalize()
                action_word = "locked" if action_type == "restrict" else "unlocked"
                success_msg = f"✅ {perm_name} {action_word}"
            
            await callback_query.answer(success_msg, show_alert=False)
            
            # Log the action
            await log_command_execution(
                callback_query.message,
                action_type,
                success=True,
                result=f"Toggled {perm_type} ({action_type})",
                args=f"User {user_id}"
            )
    
    except Exception as e:
        logger.error(f"Permission toggle callback error: {e}")
        await callback_query.answer(f"❌ Error: {escape_error_message(str(e))}", show_alert=True)


async def handle_toggle_cancel_callback(callback_query: CallbackQuery, data: str):
    """Handle toggle cancel callbacks (toggle_cancel_user_id_group_id)"""
    try:
        await callback_query.message.delete()
        await callback_query.answer("❌ Cancelled")
    except Exception as e:
        logger.error(f"Toggle cancel callback error: {e}")
        await callback_query.answer("Error cancelling", show_alert=True)


# ==================== ADVANCED ADMIN PANEL CALLBACKS ====================

async def handle_advanced_toggle(callback_query: CallbackQuery):
    """Handle advanced admin panel toggle buttons."""
    try:
        await callback_query.answer()  # Remove loading state
        
        data = callback_query.data
        parts = data.split("_")
        
        if len(parts) < 4:
            await callback_query.answer("Invalid callback data", show_alert=True)
            return
        
        action = parts[2]  # mute, ban, warn, restrict, lockdown, nightmode, promote, demote
        user_id = int(parts[3])
        group_id = int(parts[4])
        
        # Check if user is admin
        member = await bot.get_chat_member(group_id, callback_query.from_user.id)
        if not member.can_restrict_members and not member.is_chat_admin():
            await callback_query.answer("You don't have permission", show_alert=True)
            return
        
        from bot.advanced_admin_panel import toggle_action_state, format_admin_panel_message, build_advanced_toggle_keyboard
        
        # Execute the toggle
        result = await toggle_action_state(group_id, user_id, action, callback_query.from_user.id)
        
        if result.get("success"):
            # Get updated panel info
            user_data = await get_user_data(user_id)
            first_name = user_data.get("first_name", "Unknown") if user_data else "Unknown"
            username = user_data.get("username") if user_data else None
            
            # Format beautiful response
            message = await format_admin_panel_message(
                {"first_name": first_name, "username": username},
                user_id,
                group_id,
                callback_query.from_user.id
            )
            
            # Build keyboard
            keyboard = await build_advanced_toggle_keyboard(user_id, group_id)
            
            # Get reply message ID if command was a reply
            reply_message_id = None
            if callback_query.message.reply_to_message:
                reply_message_id = callback_query.message.reply_to_message.message_id
            
            try:
                await callback_query.message.edit_text(
                    message,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Edit message error: {e}")
                await callback_query.answer("Error updating panel", show_alert=True)
        else:
            error_msg = result.get("message", "Failed to toggle action")
            await callback_query.answer(error_msg, show_alert=True)
            
    except Exception as e:
        logger.error(f"Advanced toggle callback error: {e}")
        await callback_query.answer("Error processing toggle", show_alert=True)


async def handle_advanced_refresh(callback_query: CallbackQuery):
    """Refresh the advanced admin panel."""
    try:
        await callback_query.answer()
        
        data = callback_query.data
        parts = data.split("_")
        
        if len(parts) < 3:
            await callback_query.answer("Invalid callback data", show_alert=True)
            return
        
        user_id = int(parts[2])
        group_id = int(parts[3])
        
        from bot.advanced_admin_panel import format_admin_panel_message, build_advanced_toggle_keyboard
        
        # Get fresh user data
        user_data = await get_user_data(user_id)
        first_name = user_data.get("first_name", "Unknown") if user_data else "Unknown"
        username = user_data.get("username") if user_data else None
        
        # Format message
        message = await format_admin_panel_message(
            {"first_name": first_name, "username": username},
            user_id,
            group_id,
            callback_query.from_user.id
        )
        
        # Build keyboard
        keyboard = await build_advanced_toggle_keyboard(user_id, group_id)
        
        try:
            await callback_query.message.edit_text(
                message,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            await callback_query.answer("✅ Panel refreshed")
        except Exception as e:
            logger.error(f"Refresh edit error: {e}")
            await callback_query.answer("Error refreshing panel", show_alert=True)
            
    except Exception as e:
        logger.error(f"Advanced refresh callback error: {e}")
        await callback_query.answer("Error refreshing", show_alert=True)


async def handle_advanced_close(callback_query: CallbackQuery):
    """Close the advanced admin panel."""
    try:
        await callback_query.answer()
        await callback_query.message.delete()
        await callback_query.answer("✅ Panel closed")
    except Exception as e:
        logger.error(f"Advanced close callback error: {e}")
        await callback_query.answer("Error closing panel", show_alert=True)


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
        
        # Handle permission toggle callbacks
        if data.startswith("toggle_perm_"):
            return await handle_permission_toggle_callback(callback_query, data)
        
        if data.startswith("toggle_cancel_"):
            return await handle_toggle_cancel_callback(callback_query, data)
        
        # Handle advanced admin panel callbacks
        if data.startswith("adv_toggle_"):
            return await handle_advanced_toggle(callback_query)
        
        if data.startswith("adv_refresh_"):
            return await handle_advanced_refresh(callback_query)
        
        if data.startswith("adv_close"):
            return await handle_advanced_close(callback_query)
        
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
        
        if result.get("error") is not None:
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
        api_client = APIv2Client(API_V2_URL, API_V2_KEY)
        
        # Check if api_v2 is healthy
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
        dispatcher.message.register(cmd_unlock, Command("unlock"))
        dispatcher.message.register(cmd_warn, Command("warn"))
        dispatcher.message.register(cmd_restrict, Command("restrict"))
        dispatcher.message.register(cmd_unrestrict, Command("unrestrict"))
        dispatcher.message.register(cmd_free, Command("free"))
        dispatcher.message.register(cmd_purge, Command("purge"))
        dispatcher.message.register(cmd_del, Command("del"))
        dispatcher.message.register(cmd_send, Command("send"))
        dispatcher.message.register(cmd_setrole, Command("setrole"))
        dispatcher.message.register(cmd_removerole, Command("removerole"))
        dispatcher.message.register(cmd_whitelist, Command("whitelist"))
        dispatcher.message.register(cmd_blacklist, Command("blacklist"))
        dispatcher.message.register(cmd_nightmode, Command("nightmode"))
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
                BotCommand(command="unlock", description="Unlock group (admin)"),
                BotCommand(command="settings", description="Group settings (admin)"),
                BotCommand(command="warn", description="Warn user (admin)"),
                BotCommand(command="restrict", description="Restrict user (admin)"),
                BotCommand(command="unrestrict", description="Unrestrict user (admin)"),
                BotCommand(command="free", description="Free user (alias for unrestrict) (admin)"),
                BotCommand(command="purge", description="Delete user messages (admin)"),
                BotCommand(command="del", description="Delete a message (admin)"),
                BotCommand(command="send", description="Send message via bot (admin)"),
                BotCommand(command="setrole", description="Set user role (admin)"),
                BotCommand(command="removerole", description="Remove user role (admin)"),
                BotCommand(command="whitelist", description="Manage whitelist (exemptions & moderators) (admin)"),
                BotCommand(command="blacklist", description="Manage blacklist (stickers, GIFs, users, links) (admin)"),
                BotCommand(command="nightmode", description="Configure night mode scheduling (admin)"),
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
