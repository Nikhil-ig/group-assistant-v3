"""
🤖 TELEGRAM BOT V2 - ADVANCED MODERN BOT
========================================
Ultra-advanced modern bot with:
✅ Smart toggle buttons (mute↔unmute, ban↔unban, warn↔unwarn, nightmode, lockdown)
✅ Professional admin panel with easy management
✅ Beautiful formatted messages with user mentions
✅ API V2 integration for all operations
✅ Reply-to-message context preservation
✅ Ultra-fast performance with caching
✅ Fully robust error handling

Author: Advanced Bot Development
Version: 2.0 (Next Generation)
"""

import asyncio
import logging
import os
import html
import time
from typing import Optional, Dict, Tuple, List
from pathlib import Path
from datetime import datetime, timedelta
from enum import Enum

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message, BotCommand, InlineKeyboardMarkup, InlineKeyboardButton, 
    CallbackQuery, ChatMember, User
)
import httpx

# Load environment variables
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

# Bot initialization
bot = Bot(token=TELEGRAM_BOT_TOKEN, parse_mode=ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# ============================================================================
# ENUMS FOR ACTION STATES
# ============================================================================

class ActionState(Enum):
    """State of user actions"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"


class ToggleAction(Enum):
    """Available toggle actions"""
    MUTE = "mute"
    UNMUTE = "unmute"
    BAN = "ban"
    UNBAN = "unban"
    WARN = "warn"
    UNWARN = "unwarn"
    LOCKDOWN = "lockdown"
    FREEDOM = "freedom"  # unlock
    NIGHT_MODE_ON = "night_mode_on"
    NIGHT_MODE_OFF = "night_mode_off"
    RESTRICT = "restrict"
    UNRESTRICT = "unrestrict"


# ============================================================================
# CALLBACK DATA COMPRESSION & CACHE
# ============================================================================

CALLBACK_DATA_CACHE: Dict[str, Dict] = {}
CALLBACK_COUNTER = 0
USER_STATS_CACHE: Dict[Tuple[int, int], Tuple[Dict, float]] = {}
CACHE_TTL = 30  # seconds


def encode_callback_data(action: str, user_id: int, group_id: int) -> str:
    """Encode callback data to fit Telegram's 64-byte limit"""
    global CALLBACK_COUNTER
    
    callback_id = f"cb_{CALLBACK_COUNTER}"
    CALLBACK_DATA_CACHE[callback_id] = {
        "action": action,
        "user_id": user_id,
        "group_id": group_id,
        "timestamp": time.time()
    }
    CALLBACK_COUNTER += 1
    
    # Memory management
    if len(CALLBACK_DATA_CACHE) > 10000:
        old_keys = sorted(CALLBACK_DATA_CACHE.keys(), 
                         key=lambda k: CALLBACK_DATA_CACHE[k].get("timestamp", 0))[:1000]
        for key in old_keys:
            del CALLBACK_DATA_CACHE[key]
    
    return callback_id


def decode_callback_data(callback_id: str) -> Optional[Dict]:
    """Decode callback data from encoded ID"""
    return CALLBACK_DATA_CACHE.get(callback_id)


def cache_user_stats(user_id: int, group_id: int, stats: Dict):
    """Cache user statistics"""
    USER_STATS_CACHE[(user_id, group_id)] = (stats, time.time() + CACHE_TTL)


def get_cached_user_stats(user_id: int, group_id: int) -> Optional[Dict]:
    """Get cached user statistics if not expired"""
    cache_key = (user_id, group_id)
    if cache_key in USER_STATS_CACHE:
        stats, expires = USER_STATS_CACHE[cache_key]
        if time.time() < expires:
            return stats
        else:
            del USER_STATS_CACHE[cache_key]
    return None


# ============================================================================
# API V2 CLIENT - ADVANCED
# ============================================================================

class APIv2ClientV2:
    """Advanced HTTP client for API V2 - optimized for speed and robustness"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = 15
        self._session: Optional[httpx.AsyncClient] = None
    
    async def get_session(self) -> httpx.AsyncClient:
        """Get or create async session"""
        if self._session is None:
            self._session = httpx.AsyncClient(timeout=self.timeout)
        return self._session
    
    async def health_check(self) -> bool:
        """Quick health check"""
        try:
            session = await self.get_session()
            response = await session.get(f"{self.base_url}/health")
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False
    
    async def execute_action(self, 
                           action_type: str, 
                           user_id: int, 
                           group_id: int, 
                           admin_id: int,
                           duration: Optional[int] = None,
                           reason: Optional[str] = None) -> Dict:
        """Execute enforcement action through API"""
        try:
            payload = {
                "action_type": action_type,
                "user_id": user_id,
                "group_id": group_id,
                "admin_id": admin_id,
                "duration": duration,
                "reason": reason or "No reason provided",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            endpoint = f"/api/v2/groups/{group_id}/enforcement/{action_type}"
            
            session = await self.get_session()
            response = await session.post(
                f"{self.base_url}{endpoint}",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            
            response.raise_for_status()
            return {
                "success": True,
                "data": response.json(),
                "message": f"✅ {action_type.capitalize()} executed"
            }
        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"❌ Failed to execute {action_type}"
            }
    
    async def get_user_status(self, user_id: int, group_id: int) -> Dict:
        """Get current user status and restrictions"""
        try:
            session = await self.get_session()
            response = await session.get(
                f"{self.base_url}/api/v2/groups/{group_id}/users/{user_id}/status",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning(f"Failed to get user status: {e}")
            return {}
    
    async def get_group_settings(self, group_id: int) -> Dict:
        """Get group settings"""
        try:
            session = await self.get_session()
            response = await session.get(
                f"{self.base_url}/api/v2/groups/{group_id}/settings",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning(f"Failed to get group settings: {e}")
            return {"group_id": group_id}
    
    async def update_user_action_state(self, 
                                      user_id: int, 
                                      group_id: int,
                                      action: str,
                                      state: str) -> Dict:
        """Update user action state in API"""
        try:
            payload = {
                "user_id": user_id,
                "action": action,
                "state": state,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            session = await self.get_session()
            response = await session.post(
                f"{self.base_url}/api/v2/groups/{group_id}/users/{user_id}/actions",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to update action state: {e}")
            return {"error": str(e)}
    
    async def log_action(self, 
                        group_id: int, 
                        user_id: int, 
                        admin_id: int,
                        action: str, 
                        details: str) -> bool:
        """Log action to API"""
        try:
            payload = {
                "group_id": group_id,
                "user_id": user_id,
                "admin_id": admin_id,
                "action": action,
                "details": details,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            session = await self.get_session()
            response = await session.post(
                f"{self.base_url}/api/v2/logs/actions",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            
            return response.status_code in [200, 201]
        except Exception as e:
            logger.warning(f"Failed to log action: {e}")
            return False
    
    async def close(self):
        """Close async session"""
        if self._session:
            await self._session.aclose()


# Initialize API client
api_client_v2 = APIv2ClientV2(API_V2_URL, API_V2_KEY)


# ============================================================================
# USER & GROUP DATA HELPERS
# ============================================================================

async def get_user_display_name(user: User, bot: Bot, group_id: int) -> Tuple[str, str]:
    """
    Get user display name and mention link.
    Returns: (display_name, mention_html)
    """
    user_id = user.id
    first_name = user.first_name or "User"
    username = user.username
    
    # Try to get full name
    full_name = first_name
    if user.last_name:
        full_name = f"{first_name} {user.last_name}"
    
    # Create mention link (clickable)
    mention_html = f'<a href="tg://user?id={user_id}">👤 {html.escape(full_name)}</a>'
    
    return full_name, mention_html


async def check_is_admin(user_id: int, group_id: int, bot: Bot) -> bool:
    """Check if user is admin in group"""
    try:
        member = await bot.get_chat_member(group_id, user_id)
        return member.status in ("administrator", "creator")
    except Exception:
        return False


async def get_user_info_from_reply(message: Message) -> Optional[Tuple[int, str]]:
    """Extract user info from replied message"""
    if not message.reply_to_message:
        return None
    
    reply_msg = message.reply_to_message
    user_id = reply_msg.from_user.id if reply_msg.from_user else None
    username = reply_msg.from_user.username if reply_msg.from_user else None
    
    return (user_id, username) if user_id else None


# ============================================================================
# MESSAGE FORMATTING - PROFESSIONAL & BEAUTIFUL
# ============================================================================

def format_user_action_message(
    target_user: User,
    action: str,
    admin_user: User,
    details: str = "",
    reply_to_id: Optional[int] = None
) -> str:
    """Format professional action message"""
    
    target_name = target_user.first_name or "User"
    if target_user.last_name:
        target_name = f"{target_name} {target_user.last_name}"
    target_mention = f'<a href="tg://user?id={target_user.id}">👤 {html.escape(target_name)}</a>'
    
    admin_name = admin_user.first_name or "Admin"
    if admin_user.last_name:
        admin_name = f"{admin_name} {admin_user.last_name}"
    admin_mention = f'<a href="tg://user?id={admin_user.id}">🛡️ {html.escape(admin_name)}</a>'
    
    action_icons = {
        "mute": "🔇",
        "unmute": "🔊",
        "ban": "🚫",
        "unban": "✅",
        "warn": "⚠️",
        "unwarn": "🆗",
        "lockdown": "🔒",
        "freedom": "🔓",
        "restrict": "⛔",
        "unrestrict": "✅",
        "night_mode_on": "🌙",
        "night_mode_off": "☀️"
    }
    
    icon = action_icons.get(action, "⚡")
    action_text = action.replace("_", " ").title()
    
    message = f"""
╔═══════════════════════════════════╗
║     {icon} {action_text.upper()}
╚═══════════════════════════════════╝

👤 <b>User:</b> {target_mention}
🛡️ <b>Admin:</b> {admin_mention}
⏰ <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    if details:
        message += f"📝 <b>Details:</b> {html.escape(details)}\n"
    
    message += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    return message.strip()


def format_admin_panel_message(
    target_user: User,
    current_states: Dict[str, bool],
    group_id: int
) -> str:
    """Format beautiful admin panel message"""
    
    target_name = target_user.first_name or "User"
    if target_user.last_name:
        target_name = f"{target_name} {target_user.last_name}"
    target_mention = f'<a href="tg://user?id={target_user.id}">👤 {html.escape(target_name)}</a>'
    
    # Build status indicators
    status_rows = []
    
    actions = [
        ("mute", "🔇 Mute"),
        ("ban", "🚫 Ban"),
        ("warn", "⚠️ Warn"),
        ("restrict", "⛔ Restrict"),
        ("lockdown", "🔒 Lockdown"),
        ("night_mode", "🌙 Night Mode")
    ]
    
    for action_key, action_label in actions:
        is_active = current_states.get(action_key, False)
        state_indicator = "✅ ACTIVE" if is_active else "❌ INACTIVE"
        state_color = "🟢" if is_active else "🔴"
        status_rows.append(f"{state_color} {action_label}: {state_indicator}")
    
    status_text = "\n".join(status_rows)
    
    message = f"""
╔════════════════════════════════════════╗
║    🎛️ ADVANCED ADMIN CONTROL PANEL
╚════════════════════════════════════════╝

📋 <b>User:</b> {target_mention}
🆔 <b>ID:</b> <code>{target_user.id}</code>
📍 <b>Group:</b> <code>{group_id}</code>

{status_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 Use the buttons below to toggle actions
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    return message.strip()


def format_error_message(error: str, context: str = "") -> str:
    """Format error message"""
    return f"""
╔════════════════════════════════╗
║    ❌ ERROR
╚════════════════════════════════╝

{html.escape(error)}

{f"<b>Context:</b> {html.escape(context)}" if context else ""}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""


def format_success_message(action: str, target_user: User, details: str = "") -> str:
    """Format success message"""
    
    target_name = target_user.first_name or "User"
    target_mention = f'<a href="tg://user?id={target_user.id}">👤 {html.escape(target_name)}</a>'
    
    action_icons = {
        "mute": "🔇",
        "unmute": "🔊",
        "ban": "🚫",
        "unban": "✅"
    }
    
    icon = action_icons.get(action, "✅")
    
    message = f"""
╔════════════════════════════════╗
║    {icon} SUCCESS
╚════════════════════════════════╝

✨ <b>Action:</b> {action.upper()}
👤 <b>User:</b> {target_mention}

{f"📝 {html.escape(details)}" if details else ""}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    return message.strip()


# ============================================================================
# KEYBOARD BUILDERS - BEAUTIFUL & RESPONSIVE
# ============================================================================

def build_admin_toggle_keyboard(
    user_id: int,
    group_id: int,
    admin_id: int,
    current_states: Dict[str, bool]
) -> InlineKeyboardMarkup:
    """Build advanced admin control panel keyboard with toggles"""
    
    buttons = []
    
    # Mute toggle
    mute_state = current_states.get("mute", False)
    mute_action = "unmute" if mute_state else "mute"
    mute_label = "🔊 Unmute" if mute_state else "🔇 Mute"
    buttons.append([
        InlineKeyboardButton(
            text=mute_label,
            callback_data=encode_callback_data(mute_action, user_id, group_id)
        )
    ])
    
    # Ban toggle
    ban_state = current_states.get("ban", False)
    ban_action = "unban" if ban_state else "ban"
    ban_label = "✅ Unban" if ban_state else "🚫 Ban"
    buttons.append([
        InlineKeyboardButton(
            text=ban_label,
            callback_data=encode_callback_data(ban_action, user_id, group_id)
        )
    ])
    
    # Warn toggle
    warn_state = current_states.get("warn", False)
    warn_action = "unwarn" if warn_state else "warn"
    warn_label = "🆗 Clear Warn" if warn_state else "⚠️ Warn"
    buttons.append([
        InlineKeyboardButton(
            text=warn_label,
            callback_data=encode_callback_data(warn_action, user_id, group_id)
        )
    ])
    
    # Restrict toggle
    restrict_state = current_states.get("restrict", False)
    restrict_action = "unrestrict" if restrict_state else "restrict"
    restrict_label = "✅ Unrestrict" if restrict_state else "⛔ Restrict"
    buttons.append([
        InlineKeyboardButton(
            text=restrict_label,
            callback_data=encode_callback_data(restrict_action, user_id, group_id)
        )
    ])
    
    # Lockdown toggle
    lockdown_state = current_states.get("lockdown", False)
    lockdown_action = "freedom" if lockdown_state else "lockdown"
    lockdown_label = "🔓 Freedom" if lockdown_state else "🔒 Lockdown"
    buttons.append([
        InlineKeyboardButton(
            text=lockdown_label,
            callback_data=encode_callback_data(lockdown_action, user_id, group_id)
        )
    ])
    
    # Night Mode toggle
    night_mode_state = current_states.get("night_mode", False)
    night_mode_action = "night_mode_off" if night_mode_state else "night_mode_on"
    night_mode_label = "☀️ Day Mode" if night_mode_state else "🌙 Night Mode"
    buttons.append([
        InlineKeyboardButton(
            text=night_mode_label,
            callback_data=encode_callback_data(night_mode_action, user_id, group_id)
        )
    ])
    
    # Cancel/Close button
    buttons.append([
        InlineKeyboardButton(
            text="❌ Close",
            callback_data=encode_callback_data("cancel", user_id, group_id)
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ============================================================================
# COMMAND HANDLERS - FAST & MODERN
# ============================================================================

@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Start command"""
    welcome_text = """
╔════════════════════════════════════════════╗
║  🤖 TELEGRAM BOT V2 - ADVANCED
║      Modern • Powerful • Robust
╚════════════════════════════════════════════╝

🎯 <b>Features:</b>
✅ Smart toggle controls (mute/unmute, ban/unban, etc.)
✅ Advanced admin panel with easy management
✅ Beautiful formatted messages
✅ User mentions and clickable profiles
✅ Reply-to-message context
✅ Ultra-fast performance
✅ Fully API-integrated

📝 <b>Commands:</b>
/settings [@user] - Open admin control panel
/help - Show all commands
/status - Check bot status

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👉 Use /settings to manage users in your group
"""
    
    await message.answer(welcome_text, parse_mode=ParseMode.HTML)


@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Help command"""
    help_text = """
╔════════════════════════════════════════════╗
║  📚 HELP & COMMANDS (17 TOTAL)
╚════════════════════════════════════════════╝

🛡️ <b>USER MANAGEMENT COMMANDS:</b>

<b>Mute/Unmute:</b>
/mute [@user | reply] - Silence a user
/unmute [@user | reply] - Let user speak

<b>Ban/Unban:</b>
/ban [@user | reply] - Permanently ban user
/unban user_id/@user - Restore banned user

<b>Warnings:</b>
/warn [@user | reply] - Give user warning ⚠️
/clear [@user | reply] - Clear all warnings

<b>Restrictions:</b>
/restrict [@user | reply] - Limit permissions
/unrestrict [@user | reply] - Restore permissions
/kick [@user | reply] - Remove user (can rejoin)

🎛️ <b>ADVANCED CONTROL:</b>

/settings [@user | reply]
└─ Open beautiful admin control panel
   with smart toggle buttons

/lockdown
└─ Enable emergency lockdown mode
   (new members restricted)

/unlock
└─ Disable lockdown mode
   (return to normal)

/nightmode on/off
└─ Toggle night mode restrictions

📊 <b>INFORMATION COMMANDS:</b>

/info [@user | reply]
└─ View user information & status

/status
└─ Check bot health & API status

/help
└─ Show this help message

/start
└─ Welcome message & features

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 <b>USAGE TIPS:</b>
✅ All commands work with reply to message
✅ Example: Reply to spammer, then /mute
✅ Use @username or user_id
✅ Admins only in groups
✅ All actions are logged!

🎯 <b>SMART FEATURES:</b>
✨ Admin panel with state detection
✨ Professional formatted messages
✨ Clickable user mentions
✨ Ultra-fast response time
✨ Full API integration
"""
    
    await message.answer(help_text, parse_mode=ParseMode.HTML)


@dp.message(Command("status"))
async def cmd_status(message: Message):
    """Bot status command"""
    
    # Check API health
    api_healthy = await api_client_v2.health_check()
    
    status_text = f"""
╔════════════════════════════════════════════╗
║  🤖 BOT STATUS
╚════════════════════════════════════════════╝

<b>Bot Status:</b> ✅ Online

<b>API V2 Status:</b> {'✅ Healthy' if api_healthy else '❌ Offline'}

<b>Version:</b> 2.0 (Next Generation)

<b>Uptime:</b> Running

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    await message.answer(status_text, parse_mode=ParseMode.HTML)


@dp.message(Command("settings"))
async def cmd_settings(message: Message):
    """Advanced admin panel - settings command"""
    
    if message.chat.type not in ("group", "supergroup"):
        await message.answer("❌ This command works only in groups")
        return
    
    chat_id = message.chat.id
    admin_id = message.from_user.id
    
    # Check admin status
    is_admin = await check_is_admin(admin_id, chat_id, bot)
    if not is_admin:
        await message.answer("❌ You must be an admin to use this command", 
                            parse_mode=ParseMode.HTML)
        return
    
    # Parse arguments to get target user
    args = message.text.split(maxsplit=1)
    target_user_id = None
    target_user = None
    
    # Case 1: Reply to message
    if message.reply_to_message and message.reply_to_message.from_user:
        target_user_id = message.reply_to_message.from_user.id
        target_user = message.reply_to_message.from_user
    
    # Case 2: Arguments provided
    elif len(args) > 1:
        arg = args[1].strip()
        
        try:
            if arg.startswith("@"):
                # Username
                try:
                    user_chat = await bot.get_chat(arg)
                    target_user_id = user_chat.id
                    # Get user object via get_chat_member
                    member = await bot.get_chat_member(chat_id, user_chat.id)
                    target_user = member.user
                except Exception as e:
                    await message.answer(f"❌ User {arg} not found", 
                                        parse_mode=ParseMode.HTML)
                    return
            else:
                # User ID
                target_user_id = int(arg)
                try:
                    member = await bot.get_chat_member(chat_id, target_user_id)
                    target_user = member.user
                except Exception:
                    await message.answer(f"❌ User {target_user_id} not found in group", 
                                        parse_mode=ParseMode.HTML)
                    return
        except ValueError:
            await message.answer("❌ Invalid user format. Use @username or user_id", 
                                parse_mode=ParseMode.HTML)
            return
    
    if not target_user_id or not target_user:
        await message.answer(
            "❌ Please reply to a message or provide a user: /settings @username",
            parse_mode=ParseMode.HTML
        )
        return
    
    # Get user current state from API
    try:
        user_status = await api_client_v2.get_user_status(target_user_id, chat_id)
        
        current_states = {
            "mute": user_status.get("is_muted", False),
            "ban": user_status.get("is_banned", False),
            "warn": user_status.get("has_warnings", False),
            "restrict": user_status.get("is_restricted", False),
            "lockdown": user_status.get("is_locked_down", False),
            "night_mode": user_status.get("night_mode_enabled", False)
        }
    except Exception as e:
        logger.warning(f"Failed to get user status: {e}")
        current_states = {
            "mute": False,
            "ban": False,
            "warn": False,
            "restrict": False,
            "lockdown": False,
            "night_mode": False
        }
    
    # Format message
    admin_message = format_admin_panel_message(target_user, current_states, chat_id)
    
    # Build keyboard
    keyboard = build_admin_toggle_keyboard(
        target_user_id,
        chat_id,
        admin_id,
        current_states
    )
    
    # Send message
    try:
        if message.reply_to_message:
            # Reply to original message
            await message.reply_to_message.reply_text(
                admin_message,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
        else:
            await message.answer(
                admin_message,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
        
        # Delete command message
        try:
            await message.delete()
        except:
            pass
    
    except Exception as e:
        logger.error(f"Error sending admin panel: {e}")
        await message.answer(format_error_message(str(e), "Admin Panel Error"),
                            parse_mode=ParseMode.HTML)


@dp.message(Command("mute"))
async def cmd_mute(message: Message):
    """Mute user command: /mute [@user | reply]"""
    if message.chat.type not in ("group", "supergroup"):
        await message.answer("❌ This command works only in groups")
        return
    
    chat_id = message.chat.id
    admin_id = message.from_user.id
    
    # Check admin
    is_admin = await check_is_admin(admin_id, chat_id, bot)
    if not is_admin:
        await message.answer("❌ You must be an admin", parse_mode=ParseMode.HTML)
        return
    
    # Get target user
    target_user_id = None
    target_user = None
    
    if message.reply_to_message and message.reply_to_message.from_user:
        target_user_id = message.reply_to_message.from_user.id
        target_user = message.reply_to_message.from_user
    else:
        args = message.text.split(maxsplit=1)
        if len(args) > 1:
            arg = args[1].strip()
            try:
                if arg.startswith("@"):
                    user_chat = await bot.get_chat(arg)
                    target_user_id = user_chat.id
                    member = await bot.get_chat_member(chat_id, user_chat.id)
                    target_user = member.user
                else:
                    target_user_id = int(arg)
                    member = await bot.get_chat_member(chat_id, target_user_id)
                    target_user = member.user
            except Exception as e:
                await message.answer(f"❌ User not found: {e}", parse_mode=ParseMode.HTML)
                return
        else:
            await message.answer("❌ Usage: /mute @user or reply to message", parse_mode=ParseMode.HTML)
            return
    
    if not target_user:
        await message.answer("❌ Could not find user", parse_mode=ParseMode.HTML)
        return
    
    # Execute mute
    result = await api_client_v2.execute_action(
        action_type="mute",
        user_id=target_user_id,
        group_id=chat_id,
        admin_id=admin_id,
        reason="Muted via /mute command"
    )
    
    if result.get("success"):
        await api_client_v2.log_action(chat_id, target_user_id, admin_id, "mute", "Via /mute command")
        success_msg = format_success_message("mute", target_user, "User has been muted")
        if message.reply_to_message:
            await message.reply_to_message.reply_text(success_msg, parse_mode=ParseMode.HTML)
        else:
            await message.answer(success_msg, parse_mode=ParseMode.HTML)
    else:
        await message.answer(f"❌ {result.get('message', 'Failed to mute')}", parse_mode=ParseMode.HTML)


@dp.message(Command("unmute"))
async def cmd_unmute(message: Message):
    """Unmute user command: /unmute [@user | reply]"""
    if message.chat.type not in ("group", "supergroup"):
        await message.answer("❌ This command works only in groups")
        return
    
    chat_id = message.chat.id
    admin_id = message.from_user.id
    
    is_admin = await check_is_admin(admin_id, chat_id, bot)
    if not is_admin:
        await message.answer("❌ You must be an admin", parse_mode=ParseMode.HTML)
        return
    
    target_user_id = None
    target_user = None
    
    if message.reply_to_message and message.reply_to_message.from_user:
        target_user_id = message.reply_to_message.from_user.id
        target_user = message.reply_to_message.from_user
    else:
        args = message.text.split(maxsplit=1)
        if len(args) > 1:
            arg = args[1].strip()
            try:
                if arg.startswith("@"):
                    user_chat = await bot.get_chat(arg)
                    target_user_id = user_chat.id
                    member = await bot.get_chat_member(chat_id, user_chat.id)
                    target_user = member.user
                else:
                    target_user_id = int(arg)
                    member = await bot.get_chat_member(chat_id, target_user_id)
                    target_user = member.user
            except Exception:
                await message.answer("❌ User not found", parse_mode=ParseMode.HTML)
                return
        else:
            await message.answer("❌ Usage: /unmute @user or reply to message", parse_mode=ParseMode.HTML)
            return
    
    result = await api_client_v2.execute_action(
        action_type="unmute",
        user_id=target_user_id,
        group_id=chat_id,
        admin_id=admin_id,
        reason="Unmuted via /unmute command"
    )
    
    if result.get("success"):
        await api_client_v2.log_action(chat_id, target_user_id, admin_id, "unmute", "Via /unmute command")
        success_msg = format_success_message("unmute", target_user, "User has been unmuted")
        if message.reply_to_message:
            await message.reply_to_message.reply_text(success_msg, parse_mode=ParseMode.HTML)
        else:
            await message.answer(success_msg, parse_mode=ParseMode.HTML)
    else:
        await message.answer(f"❌ {result.get('message', 'Failed to unmute')}", parse_mode=ParseMode.HTML)


@dp.message(Command("ban"))
async def cmd_ban(message: Message):
    """Ban user command: /ban [@user | reply]"""
    if message.chat.type not in ("group", "supergroup"):
        await message.answer("❌ This command works only in groups")
        return
    
    chat_id = message.chat.id
    admin_id = message.from_user.id
    
    is_admin = await check_is_admin(admin_id, chat_id, bot)
    if not is_admin:
        await message.answer("❌ You must be an admin", parse_mode=ParseMode.HTML)
        return
    
    target_user_id = None
    target_user = None
    
    if message.reply_to_message and message.reply_to_message.from_user:
        target_user_id = message.reply_to_message.from_user.id
        target_user = message.reply_to_message.from_user
    else:
        args = message.text.split(maxsplit=1)
        if len(args) > 1:
            arg = args[1].strip()
            try:
                if arg.startswith("@"):
                    user_chat = await bot.get_chat(arg)
                    target_user_id = user_chat.id
                    member = await bot.get_chat_member(chat_id, user_chat.id)
                    target_user = member.user
                else:
                    target_user_id = int(arg)
                    member = await bot.get_chat_member(chat_id, target_user_id)
                    target_user = member.user
            except Exception:
                await message.answer("❌ User not found", parse_mode=ParseMode.HTML)
                return
        else:
            await message.answer("❌ Usage: /ban @user or reply to message", parse_mode=ParseMode.HTML)
            return
    
    result = await api_client_v2.execute_action(
        action_type="ban",
        user_id=target_user_id,
        group_id=chat_id,
        admin_id=admin_id,
        reason="Banned via /ban command"
    )
    
    if result.get("success"):
        await api_client_v2.log_action(chat_id, target_user_id, admin_id, "ban", "Via /ban command")
        success_msg = format_success_message("ban", target_user, "User has been banned")
        if message.reply_to_message:
            await message.reply_to_message.reply_text(success_msg, parse_mode=ParseMode.HTML)
        else:
            await message.answer(success_msg, parse_mode=ParseMode.HTML)
    else:
        await message.answer(f"❌ {result.get('message', 'Failed to ban')}", parse_mode=ParseMode.HTML)


@dp.message(Command("unban"))
async def cmd_unban(message: Message):
    """Unban user command: /unban [@user | user_id]"""
    if message.chat.type not in ("group", "supergroup"):
        await message.answer("❌ This command works only in groups")
        return
    
    chat_id = message.chat.id
    admin_id = message.from_user.id
    
    is_admin = await check_is_admin(admin_id, chat_id, bot)
    if not is_admin:
        await message.answer("❌ You must be an admin", parse_mode=ParseMode.HTML)
        return
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❌ Usage: /unban @user or /unban user_id", parse_mode=ParseMode.HTML)
        return
    
    arg = args[1].strip()
    target_user_id = None
    
    try:
        if arg.startswith("@"):
            user_chat = await bot.get_chat(arg)
            target_user_id = user_chat.id
        else:
            target_user_id = int(arg)
    except Exception:
        await message.answer("❌ Invalid user", parse_mode=ParseMode.HTML)
        return
    
    result = await api_client_v2.execute_action(
        action_type="unban",
        user_id=target_user_id,
        group_id=chat_id,
        admin_id=admin_id,
        reason="Unbanned via /unban command"
    )
    
    if result.get("success"):
        await api_client_v2.log_action(chat_id, target_user_id, admin_id, "unban", "Via /unban command")
        await message.answer(f"✅ User {target_user_id} has been unbanned", parse_mode=ParseMode.HTML)
    else:
        await message.answer(f"❌ {result.get('message', 'Failed to unban')}", parse_mode=ParseMode.HTML)


@dp.message(Command("warn"))
async def cmd_warn(message: Message):
    """Warn user command: /warn [@user | reply]"""
    if message.chat.type not in ("group", "supergroup"):
        await message.answer("❌ This command works only in groups")
        return
    
    chat_id = message.chat.id
    admin_id = message.from_user.id
    
    is_admin = await check_is_admin(admin_id, chat_id, bot)
    if not is_admin:
        await message.answer("❌ You must be an admin", parse_mode=ParseMode.HTML)
        return
    
    target_user_id = None
    target_user = None
    
    if message.reply_to_message and message.reply_to_message.from_user:
        target_user_id = message.reply_to_message.from_user.id
        target_user = message.reply_to_message.from_user
    else:
        args = message.text.split(maxsplit=1)
        if len(args) > 1:
            arg = args[1].strip()
            try:
                if arg.startswith("@"):
                    user_chat = await bot.get_chat(arg)
                    target_user_id = user_chat.id
                    member = await bot.get_chat_member(chat_id, user_chat.id)
                    target_user = member.user
                else:
                    target_user_id = int(arg)
                    member = await bot.get_chat_member(chat_id, target_user_id)
                    target_user = member.user
            except Exception:
                await message.answer("❌ User not found", parse_mode=ParseMode.HTML)
                return
        else:
            await message.answer("❌ Usage: /warn @user or reply to message", parse_mode=ParseMode.HTML)
            return
    
    result = await api_client_v2.execute_action(
        action_type="warn",
        user_id=target_user_id,
        group_id=chat_id,
        admin_id=admin_id,
        reason="Warning via /warn command"
    )
    
    if result.get("success"):
        await api_client_v2.log_action(chat_id, target_user_id, admin_id, "warn", "Via /warn command")
        success_msg = format_success_message("warn", target_user, "User has been warned ⚠️")
        if message.reply_to_message:
            await message.reply_to_message.reply_text(success_msg, parse_mode=ParseMode.HTML)
        else:
            await message.answer(success_msg, parse_mode=ParseMode.HTML)
    else:
        await message.answer(f"❌ {result.get('message', 'Failed to warn')}", parse_mode=ParseMode.HTML)


@dp.message(Command("restrict"))
async def cmd_restrict(message: Message):
    """Restrict user command: /restrict [@user | reply]"""
    if message.chat.type not in ("group", "supergroup"):
        await message.answer("❌ This command works only in groups")
        return
    
    chat_id = message.chat.id
    admin_id = message.from_user.id
    
    is_admin = await check_is_admin(admin_id, chat_id, bot)
    if not is_admin:
        await message.answer("❌ You must be an admin", parse_mode=ParseMode.HTML)
        return
    
    target_user_id = None
    target_user = None
    
    if message.reply_to_message and message.reply_to_message.from_user:
        target_user_id = message.reply_to_message.from_user.id
        target_user = message.reply_to_message.from_user
    else:
        args = message.text.split(maxsplit=1)
        if len(args) > 1:
            arg = args[1].strip()
            try:
                if arg.startswith("@"):
                    user_chat = await bot.get_chat(arg)
                    target_user_id = user_chat.id
                    member = await bot.get_chat_member(chat_id, user_chat.id)
                    target_user = member.user
                else:
                    target_user_id = int(arg)
                    member = await bot.get_chat_member(chat_id, target_user_id)
                    target_user = member.user
            except Exception:
                await message.answer("❌ User not found", parse_mode=ParseMode.HTML)
                return
        else:
            await message.answer("❌ Usage: /restrict @user or reply to message", parse_mode=ParseMode.HTML)
            return
    
    result = await api_client_v2.execute_action(
        action_type="restrict",
        user_id=target_user_id,
        group_id=chat_id,
        admin_id=admin_id,
        reason="Restricted via /restrict command"
    )
    
    if result.get("success"):
        await api_client_v2.log_action(chat_id, target_user_id, admin_id, "restrict", "Via /restrict command")
        success_msg = format_success_message("restrict", target_user, "User has been restricted")
        if message.reply_to_message:
            await message.reply_to_message.reply_text(success_msg, parse_mode=ParseMode.HTML)
        else:
            await message.answer(success_msg, parse_mode=ParseMode.HTML)
    else:
        await message.answer(f"❌ {result.get('message', 'Failed to restrict')}", parse_mode=ParseMode.HTML)


@dp.message(Command("unrestrict"))
async def cmd_unrestrict(message: Message):
    """Unrestrict user command: /unrestrict [@user | reply]"""
    if message.chat.type not in ("group", "supergroup"):
        await message.answer("❌ This command works only in groups")
        return
    
    chat_id = message.chat.id
    admin_id = message.from_user.id
    
    is_admin = await check_is_admin(admin_id, chat_id, bot)
    if not is_admin:
        await message.answer("❌ You must be an admin", parse_mode=ParseMode.HTML)
        return
    
    target_user_id = None
    target_user = None
    
    if message.reply_to_message and message.reply_to_message.from_user:
        target_user_id = message.reply_to_message.from_user.id
        target_user = message.reply_to_message.from_user
    else:
        args = message.text.split(maxsplit=1)
        if len(args) > 1:
            arg = args[1].strip()
            try:
                if arg.startswith("@"):
                    user_chat = await bot.get_chat(arg)
                    target_user_id = user_chat.id
                    member = await bot.get_chat_member(chat_id, user_chat.id)
                    target_user = member.user
                else:
                    target_user_id = int(arg)
                    member = await bot.get_chat_member(chat_id, target_user_id)
                    target_user = member.user
            except Exception:
                await message.answer("❌ User not found", parse_mode=ParseMode.HTML)
                return
        else:
            await message.answer("❌ Usage: /unrestrict @user or reply to message", parse_mode=ParseMode.HTML)
            return
    
    result = await api_client_v2.execute_action(
        action_type="unrestrict",
        user_id=target_user_id,
        group_id=chat_id,
        admin_id=admin_id,
        reason="Unrestricted via /unrestrict command"
    )
    
    if result.get("success"):
        await api_client_v2.log_action(chat_id, target_user_id, admin_id, "unrestrict", "Via /unrestrict command")
        success_msg = format_success_message("unrestrict", target_user, "User has been unrestricted")
        if message.reply_to_message:
            await message.reply_to_message.reply_text(success_msg, parse_mode=ParseMode.HTML)
        else:
            await message.answer(success_msg, parse_mode=ParseMode.HTML)
    else:
        await message.answer(f"❌ {result.get('message', 'Failed to unrestrict')}", parse_mode=ParseMode.HTML)


@dp.message(Command("lockdown"))
async def cmd_lockdown(message: Message):
    """Lockdown command: /lockdown - Enables lockdown mode"""
    if message.chat.type not in ("group", "supergroup"):
        await message.answer("❌ This command works only in groups")
        return
    
    chat_id = message.chat.id
    admin_id = message.from_user.id
    
    is_admin = await check_is_admin(admin_id, chat_id, bot)
    if not is_admin:
        await message.answer("❌ You must be an admin", parse_mode=ParseMode.HTML)
        return
    
    result = await api_client_v2.execute_action(
        action_type="lockdown",
        user_id=chat_id,
        group_id=chat_id,
        admin_id=admin_id,
        reason="Lockdown enabled via /lockdown"
    )
    
    if result.get("success"):
        await api_client_v2.log_action(chat_id, chat_id, admin_id, "lockdown", "Group lockdown enabled")
        await message.answer("🔒 <b>Lockdown Mode Enabled</b>\n\n Group is now in lockdown mode. New members restricted.", parse_mode=ParseMode.HTML)
    else:
        await message.answer(f"❌ {result.get('message', 'Failed to enable lockdown')}", parse_mode=ParseMode.HTML)


@dp.message(Command("unlock"))
async def cmd_unlock(message: Message):
    """Unlock command: /unlock - Disables lockdown mode"""
    if message.chat.type not in ("group", "supergroup"):
        await message.answer("❌ This command works only in groups")
        return
    
    chat_id = message.chat.id
    admin_id = message.from_user.id
    
    is_admin = await check_is_admin(admin_id, chat_id, bot)
    if not is_admin:
        await message.answer("❌ You must be an admin", parse_mode=ParseMode.HTML)
        return
    
    result = await api_client_v2.execute_action(
        action_type="freedom",
        user_id=chat_id,
        group_id=chat_id,
        admin_id=admin_id,
        reason="Lockdown disabled via /unlock"
    )
    
    if result.get("success"):
        await api_client_v2.log_action(chat_id, chat_id, admin_id, "unlock", "Group lockdown disabled")
        await message.answer("🔓 <b>Lockdown Mode Disabled</b>\n\n Group is back to normal mode.", parse_mode=ParseMode.HTML)
    else:
        await message.answer(f"❌ {result.get('message', 'Failed to disable lockdown')}", parse_mode=ParseMode.HTML)


@dp.message(Command("nightmode"))
async def cmd_nightmode(message: Message):
    """Night mode command: /nightmode on/off"""
    if message.chat.type not in ("group", "supergroup"):
        await message.answer("❌ This command works only in groups")
        return
    
    chat_id = message.chat.id
    admin_id = message.from_user.id
    
    is_admin = await check_is_admin(admin_id, chat_id, bot)
    if not is_admin:
        await message.answer("❌ You must be an admin", parse_mode=ParseMode.HTML)
        return
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❌ Usage: /nightmode on or /nightmode off", parse_mode=ParseMode.HTML)
        return
    
    mode = args[1].strip().lower()
    if mode not in ["on", "off", "enable", "disable"]:
        await message.answer("❌ Usage: /nightmode on/off", parse_mode=ParseMode.HTML)
        return
    
    action = "night_mode_on" if mode in ["on", "enable"] else "night_mode_off"
    
    result = await api_client_v2.execute_action(
        action_type=action,
        user_id=chat_id,
        group_id=chat_id,
        admin_id=admin_id,
        reason=f"Night mode {action.replace('night_mode_', '')} via command"
    )
    
    if result.get("success"):
        await api_client_v2.log_action(chat_id, chat_id, admin_id, action, f"Night mode toggled via command")
        status = "🌙 <b>Night Mode Enabled</b>" if mode in ["on", "enable"] else "☀️ <b>Day Mode Enabled</b>"
        await message.answer(f"{status}\n\n Restrictions adjusted based on time.", parse_mode=ParseMode.HTML)
    else:
        await message.answer(f"❌ {result.get('message', 'Failed to toggle night mode')}", parse_mode=ParseMode.HTML)


@dp.message(Command("kick"))
async def cmd_kick(message: Message):
    """Kick user command: /kick [@user | reply]"""
    if message.chat.type not in ("group", "supergroup"):
        await message.answer("❌ This command works only in groups")
        return
    
    chat_id = message.chat.id
    admin_id = message.from_user.id
    
    is_admin = await check_is_admin(admin_id, chat_id, bot)
    if not is_admin:
        await message.answer("❌ You must be an admin", parse_mode=ParseMode.HTML)
        return
    
    target_user_id = None
    target_user = None
    
    if message.reply_to_message and message.reply_to_message.from_user:
        target_user_id = message.reply_to_message.from_user.id
        target_user = message.reply_to_message.from_user
    else:
        args = message.text.split(maxsplit=1)
        if len(args) > 1:
            arg = args[1].strip()
            try:
                if arg.startswith("@"):
                    user_chat = await bot.get_chat(arg)
                    target_user_id = user_chat.id
                    member = await bot.get_chat_member(chat_id, user_chat.id)
                    target_user = member.user
                else:
                    target_user_id = int(arg)
                    member = await bot.get_chat_member(chat_id, target_user_id)
                    target_user = member.user
            except Exception:
                await message.answer("❌ User not found", parse_mode=ParseMode.HTML)
                return
        else:
            await message.answer("❌ Usage: /kick @user or reply to message", parse_mode=ParseMode.HTML)
            return
    
    result = await api_client_v2.execute_action(
        action_type="kick",
        user_id=target_user_id,
        group_id=chat_id,
        admin_id=admin_id,
        reason="Kicked via /kick command"
    )
    
    if result.get("success"):
        await api_client_v2.log_action(chat_id, target_user_id, admin_id, "kick", "Via /kick command")
        success_msg = format_success_message("kick", target_user, "User has been kicked")
        if message.reply_to_message:
            await message.reply_to_message.reply_text(success_msg, parse_mode=ParseMode.HTML)
        else:
            await message.answer(success_msg, parse_mode=ParseMode.HTML)
    else:
        await message.answer(f"❌ {result.get('message', 'Failed to kick')}", parse_mode=ParseMode.HTML)


@dp.message(Command("clear"))
async def cmd_clear(message: Message):
    """Clear warnings command: /clear [@user | reply]"""
    if message.chat.type not in ("group", "supergroup"):
        await message.answer("❌ This command works only in groups")
        return
    
    chat_id = message.chat.id
    admin_id = message.from_user.id
    
    is_admin = await check_is_admin(admin_id, chat_id, bot)
    if not is_admin:
        await message.answer("❌ You must be an admin", parse_mode=ParseMode.HTML)
        return
    
    target_user_id = None
    target_user = None
    
    if message.reply_to_message and message.reply_to_message.from_user:
        target_user_id = message.reply_to_message.from_user.id
        target_user = message.reply_to_message.from_user
    else:
        args = message.text.split(maxsplit=1)
        if len(args) > 1:
            arg = args[1].strip()
            try:
                if arg.startswith("@"):
                    user_chat = await bot.get_chat(arg)
                    target_user_id = user_chat.id
                    member = await bot.get_chat_member(chat_id, user_chat.id)
                    target_user = member.user
                else:
                    target_user_id = int(arg)
                    member = await bot.get_chat_member(chat_id, target_user_id)
                    target_user = member.user
            except Exception:
                await message.answer("❌ User not found", parse_mode=ParseMode.HTML)
                return
        else:
            await message.answer("❌ Usage: /clear @user or reply to message", parse_mode=ParseMode.HTML)
            return
    
    result = await api_client_v2.execute_action(
        action_type="unwarn",
        user_id=target_user_id,
        group_id=chat_id,
        admin_id=admin_id,
        reason="Warnings cleared via /clear command"
    )
    
    if result.get("success"):
        await api_client_v2.log_action(chat_id, target_user_id, admin_id, "clear_warnings", "Via /clear command")
        success_msg = format_success_message("unwarn", target_user, "All warnings cleared")
        if message.reply_to_message:
            await message.reply_to_message.reply_text(success_msg, parse_mode=ParseMode.HTML)
        else:
            await message.answer(success_msg, parse_mode=ParseMode.HTML)
    else:
        await message.answer(f"❌ {result.get('message', 'Failed to clear warnings')}", parse_mode=ParseMode.HTML)


@dp.message(Command("info"))
async def cmd_info(message: Message):
    """Get user info command: /info [@user | reply]"""
    if message.chat.type not in ("group", "supergroup"):
        await message.answer("❌ This command works only in groups")
        return
    
    target_user_id = None
    target_user = None
    
    if message.reply_to_message and message.reply_to_message.from_user:
        target_user_id = message.reply_to_message.from_user.id
        target_user = message.reply_to_message.from_user
    else:
        args = message.text.split(maxsplit=1)
        if len(args) > 1:
            arg = args[1].strip()
            try:
                if arg.startswith("@"):
                    user_chat = await bot.get_chat(arg)
                    target_user_id = user_chat.id
                    try:
                        member = await bot.get_chat_member(message.chat.id, user_chat.id)
                        target_user = member.user
                    except:
                        target_user = user_chat
                else:
                    target_user_id = int(arg)
                    member = await bot.get_chat_member(message.chat.id, target_user_id)
                    target_user = member.user
            except Exception:
                await message.answer("❌ User not found", parse_mode=ParseMode.HTML)
                return
        else:
            target_user = message.from_user
            target_user_id = message.from_user.id
    
    try:
        user_status = await api_client_v2.get_user_status(target_user_id, message.chat.id)
        
        full_name = target_user.first_name or "Unknown"
        if target_user.last_name:
            full_name = f"{full_name} {target_user.last_name}"
        
        username = target_user.username or "N/A"
        
        info_text = f"""
╔════════════════════════════════════════╗
║    👤 USER INFORMATION
╚════════════════════════════════════════╝

<b>Name:</b> {html.escape(full_name)}
<b>Username:</b> @{html.escape(username)} if username else 'N/A'
<b>ID:</b> <code>{target_user_id}</code>

<b>Status:</b>
🔇 Muted: {'✅ Yes' if user_status.get('is_muted') else '❌ No'}
🚫 Banned: {'✅ Yes' if user_status.get('is_banned') else '❌ No'}
⚠️ Warnings: {user_status.get('has_warnings', 0)}
⛔ Restricted: {'✅ Yes' if user_status.get('is_restricted') else '❌ No'}
🔒 Locked Down: {'✅ Yes' if user_status.get('is_locked_down') else '❌ No'}

<b>Account Info:</b>
📅 Account Created: {target_user.is_bot and 'Bot Account' or 'User Account'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        await message.answer(info_text, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Error getting user info: {e}")
        await message.answer(f"❌ Error getting user info: {e}", parse_mode=ParseMode.HTML)


# ============================================================================
# CALLBACK HANDLERS - SMART TOGGLES
# ============================================================================

@dp.callback_query(F.data.startswith("cb_"))
async def handle_action_callback(callback: CallbackQuery):
    """Handle admin toggle action callbacks"""
    
    # Decode callback data
    callback_data = decode_callback_data(callback.data)
    if not callback_data:
        await callback.answer("❌ Invalid callback data", show_alert=True)
        return
    
    action = callback_data.get("action")
    user_id = callback_data.get("user_id")
    group_id = callback_data.get("group_id")
    
    # Check admin status
    admin_id = callback.from_user.id
    is_admin = await check_is_admin(admin_id, group_id, bot)
    
    if not is_admin:
        await callback.answer("❌ You must be an admin", show_alert=True)
        return
    
    # Handle cancel action
    if action == "cancel":
        await callback.message.delete()
        await callback.answer("Closed ✓", show_alert=False)
        return
    
    try:
        # Get target user info
        member = await bot.get_chat_member(group_id, user_id)
        target_user = member.user
        
        # Show loading state
        await callback.answer("⏳ Processing...", show_alert=False)
        
        # Determine if this is a toggle action
        is_toggle = action in ["unmute", "unban", "unwarn", "unrestrict", "freedom", "night_mode_off"]
        
        # Execute action via API
        result = await api_client_v2.execute_action(
            action_type=action,
            user_id=user_id,
            group_id=group_id,
            admin_id=admin_id,
            reason="Toggle action via admin panel"
        )
        
        if result.get("success"):
            # Log action
            await api_client_v2.log_action(
                group_id=group_id,
                user_id=user_id,
                admin_id=admin_id,
                action=action,
                details="Executed via admin panel toggle"
            )
            
            # Format success message
            success_msg = format_success_message(action, target_user, "Action applied successfully")
            
            # Send notification
            try:
                await callback.message.answer(success_msg, parse_mode=ParseMode.HTML)
            except:
                pass
            
            # Update panel keyboard to reflect new state
            try:
                user_status = await api_client_v2.get_user_status(user_id, group_id)
                current_states = {
                    "mute": user_status.get("is_muted", False),
                    "ban": user_status.get("is_banned", False),
                    "warn": user_status.get("has_warnings", False),
                    "restrict": user_status.get("is_restricted", False),
                    "lockdown": user_status.get("is_locked_down", False),
                    "night_mode": user_status.get("night_mode_enabled", False)
                }
            except:
                current_states = {k: False for k in ["mute", "ban", "warn", "restrict", "lockdown", "night_mode"]}
            
            # Refresh keyboard
            new_keyboard = build_admin_toggle_keyboard(user_id, group_id, admin_id, current_states)
            admin_message = format_admin_panel_message(target_user, current_states, group_id)
            
            try:
                await callback.message.edit_text(
                    admin_message,
                    parse_mode=ParseMode.HTML,
                    reply_markup=new_keyboard
                )
            except:
                pass
            
            await callback.answer("✅ Done!", show_alert=False)
        else:
            error_msg = result.get("message", "Unknown error")
            await callback.answer(f"❌ {error_msg}", show_alert=True)
    
    except Exception as e:
        logger.error(f"Error handling action callback: {e}")
        await callback.answer(f"❌ Error: {str(e)}", show_alert=True)


# ============================================================================
# BOT STARTUP & SHUTDOWN
# ============================================================================

async def on_startup():
    """Startup handler"""
    logger.info("🚀 Bot V2 Starting...")
    
    # Check API health
    health = await api_client_v2.health_check()
    if health:
        logger.info("✅ API V2 is healthy")
    else:
        logger.warning("⚠️ API V2 health check failed")
    
    # Set bot commands
    commands = [
        BotCommand(command="start", description="Start the bot"),
        BotCommand(command="help", description="Show all commands"),
        BotCommand(command="status", description="Check bot status"),
        BotCommand(command="settings", description="Open admin control panel"),
        BotCommand(command="mute", description="Mute user"),
        BotCommand(command="unmute", description="Unmute user"),
        BotCommand(command="ban", description="Ban user"),
        BotCommand(command="unban", description="Unban user"),
        BotCommand(command="warn", description="Warn user"),
        BotCommand(command="clear", description="Clear user warnings"),
        BotCommand(command="kick", description="Kick user"),
        BotCommand(command="restrict", description="Restrict user"),
        BotCommand(command="unrestrict", description="Unrestrict user"),
        BotCommand(command="lockdown", description="Enable lockdown mode"),
        BotCommand(command="unlock", description="Disable lockdown mode"),
        BotCommand(command="nightmode", description="Toggle night mode"),
        BotCommand(command="info", description="Get user information"),
    ]
    
    try:
        await bot.set_my_commands(commands)
        logger.info("✅ Bot commands set (17 total)")
    except Exception as e:
        logger.error(f"Failed to set commands: {e}")


async def on_shutdown():
    """Shutdown handler"""
    logger.info("🛑 Bot V2 Shutting down...")
    await api_client_v2.close()
    logger.info("✅ Cleanup complete")


async def main():
    """Main bot loop"""
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Start polling
    logger.info("🎯 Polling started...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
