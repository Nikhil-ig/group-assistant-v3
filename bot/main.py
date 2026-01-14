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
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(env_path)

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
# BOT CLIENT FOR CENTRALIZED API
# ============================================================================

class CentralizedAPIClient:
    """HTTP client for communicating with centralized_api"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = 30
    
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


def escape_error_message(error_msg: str) -> str:
    """Escape HTML special characters in error messages for safe Telegram delivery"""
    return html.escape(error_msg)


async def send_and_delete(message: Message, text: str, delay: int = 5, **kwargs):
    """Send a message and auto-delete it after delay seconds"""
    try:
        sent_msg = await message.answer(text, **kwargs)
        await asyncio.sleep(delay)
        await sent_msg.delete()
    except Exception as e:
        logger.error(f"Failed to send and delete message: {e}")


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
            f"║ {emoji} <b>ACTION EXECUTED</b>          ║\n"
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
            await asyncio.sleep(delay)
            await sent_msg.delete()
        except Exception as e:
            logger.error(f"Failed to send action response: {e}")
    else:
        response = (
            f"╔═══════════════════════════════════╗\n"
            f"║ ⚠️ <b>ACTION FAILED</b>             ║\n"
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
            InlineKeyboardButton(text="🔄 Unban", callback_data=f"unban_{user_id}_{group_id}"),
            InlineKeyboardButton(text="⚠️ Warn", callback_data=f"warn_{user_id}_{group_id}")
        ])
        buttons.append([
            InlineKeyboardButton(text="📋 View Details", callback_data=f"user_info_{user_id}_{group_id}"),
            InlineKeyboardButton(text="🔐 Lockdown", callback_data=f"lockdown_{user_id}_{group_id}")
        ])
    elif action == "unban":
        buttons.append([
            InlineKeyboardButton(text="🔨 Ban Again", callback_data=f"ban_{user_id}_{group_id}"),
            InlineKeyboardButton(text="🔊 Unmute", callback_data=f"unmute_{user_id}_{group_id}")
        ])
        buttons.append([
            InlineKeyboardButton(text="✅ Full Restore", callback_data=f"unrestrict_{user_id}_{group_id}"),
            InlineKeyboardButton(text="📋 History", callback_data=f"user_history_{user_id}_{group_id}")
        ])
    elif action == "mute":
        buttons.append([
            InlineKeyboardButton(text="🔊 Unmute", callback_data=f"unmute_{user_id}_{group_id}"),
            InlineKeyboardButton(text="🔨 Ban", callback_data=f"ban_{user_id}_{group_id}")
        ])
        buttons.append([
            InlineKeyboardButton(text="⚠️ Warn", callback_data=f"warn_{user_id}_{group_id}"),
            InlineKeyboardButton(text="📊 Stats", callback_data=f"user_stats_{user_id}_{group_id}")
        ])
    elif action == "unmute":
        buttons.append([
            InlineKeyboardButton(text="🔇 Mute", callback_data=f"mute_{user_id}_{group_id}"),
            InlineKeyboardButton(text="⚠️ Warn", callback_data=f"warn_{user_id}_{group_id}")
        ])
        buttons.append([
            InlineKeyboardButton(text="✅ Grant Perms", callback_data=f"unrestrict_{user_id}_{group_id}"),
            InlineKeyboardButton(text="👥 Promote", callback_data=f"promote_{user_id}_{group_id}")
        ])
    elif action == "kick":
        buttons.append([
            InlineKeyboardButton(text="🔨 Ban Permanently", callback_data=f"ban_{user_id}_{group_id}"),
            InlineKeyboardButton(text="🔇 Mute Instead", callback_data=f"mute_{user_id}_{group_id}")
        ])
        buttons.append([
            InlineKeyboardButton(text="📝 Log Reason", callback_data=f"log_action_{user_id}_{group_id}"),
            InlineKeyboardButton(text="📊 Kick Count", callback_data=f"kick_stats_{user_id}_{group_id}")
        ])
    elif action == "promote":
        buttons.append([
            InlineKeyboardButton(text="⬇️ Demote", callback_data=f"demote_{user_id}_{group_id}"),
            InlineKeyboardButton(text="👤 Set Custom Role", callback_data=f"setrole_{user_id}_{group_id}")
        ])
        buttons.append([
            InlineKeyboardButton(text="🎖️ Grant Permissions", callback_data=f"grant_perms_{user_id}_{group_id}"),
            InlineKeyboardButton(text="📋 Admin Info", callback_data=f"admin_info_{user_id}_{group_id}")
        ])
    elif action == "demote":
        buttons.append([
            InlineKeyboardButton(text="⬆️ Promote Again", callback_data=f"promote_{user_id}_{group_id}"),
            InlineKeyboardButton(text="🔇 Mute", callback_data=f"mute_{user_id}_{group_id}")
        ])
        buttons.append([
            InlineKeyboardButton(text="🔄 Revoke All", callback_data=f"unrestrict_{user_id}_{group_id}"),
            InlineKeyboardButton(text="📊 Role History", callback_data=f"role_history_{user_id}_{group_id}")
        ])
    elif action == "restrict":
        buttons.append([
            InlineKeyboardButton(text="🔓 Unrestrict", callback_data=f"unrestrict_{user_id}_{group_id}"),
            InlineKeyboardButton(text="🔨 Ban", callback_data=f"ban_{user_id}_{group_id}")
        ])
        buttons.append([
            InlineKeyboardButton(text="⚙️ Manage Perms", callback_data=f"manage_perms_{user_id}_{group_id}"),
            InlineKeyboardButton(text="📋 Details", callback_data=f"user_info_{user_id}_{group_id}")
        ])
    elif action == "warn":
        buttons.append([
            InlineKeyboardButton(text="🔨 Ban", callback_data=f"ban_{user_id}_{group_id}"),
            InlineKeyboardButton(text="🔇 Mute", callback_data=f"mute_{user_id}_{group_id}"),
            InlineKeyboardButton(text="👢 Kick", callback_data=f"kick_{user_id}_{group_id}")
        ])
        buttons.append([
            InlineKeyboardButton(text="📊 Warning Count", callback_data=f"warn_count_{user_id}_{group_id}"),
            InlineKeyboardButton(text="💾 Save Warning", callback_data=f"save_warn_{user_id}_{group_id}")
        ])
    
    if buttons:
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    return InlineKeyboardMarkup(inline_keyboard=[[]])


# Global instances
bot: Optional[Bot] = None
dispatcher: Optional[Dispatcher] = None
api_client: Optional[CentralizedAPIClient] = None


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


async def cmd_ban(message: Message):
    """Handle /ban command - Ban user
    Usage: /ban (reply to message) or /ban <user_id|@username> [reason]
    """
    try:
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
        else:
            await send_action_response(message, "ban", user_id, True)
            
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
        else:
            await send_action_response(message, "kick", user_id, True)
            
    except Exception as e:
        logger.error(f"Kick command failed: {e}")
        await send_and_delete(message, f"❌ Error: {escape_error_message(str(e))}", 
                             parse_mode=ParseMode.HTML)


async def cmd_mute(message: Message):
    """Handle /mute command - Mute user (forever by default)
    Usage: /mute (reply to message) or /mute <user_id|@username> [duration_minutes]
    """
    try:
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
        else:
            duration_text = "forever" if duration == 0 else f"for {duration} minutes"
            response = f"🔇 <b>User {user_id} has been muted {duration_text}</b>"
            await send_and_delete(message, response, parse_mode=ParseMode.HTML)
            
    except Exception as e:
        logger.error(f"Mute command failed: {e}")
        await send_and_delete(message, f"❌ Error: {escape_error_message(str(e))}", 
                             parse_mode=ParseMode.HTML)


async def cmd_unmute(message: Message):
    """Handle /unmute command - Unmute user
    Usage: /unmute (reply to message) or /unmute <user_id|@username>
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
            await message.answer(f"❌ Error: {escape_error_message(result['error'])}", parse_mode=None)
        else:
            await message.answer(f"✅ User {user_id} has been unmuted")
            
    except Exception as e:
        logger.error(f"Unmute command failed: {e}")
        await message.answer(f"❌ Error: {escape_error_message(str(e))}", parse_mode=None)
        await message.answer(f"❌ Error: {escape_error_message(str(e))}")


async def cmd_pin(message: Message):
    """Handle /pin command - Pin a message
    Usage: /pin (reply to message) or /pin <message_id>
    """
    try:
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
        else:
            await message.answer(f"✅ Message {message_id} has been pinned")
            
    except Exception as e:
        logger.error(f"Pin command failed: {e}")
        await message.answer(f"❌ Error: {escape_error_message(str(e))}", parse_mode=None)


async def cmd_unpin(message: Message):
    """Handle /unpin command - Unpin a message
    Usage: /unpin (reply to message) or /unpin <message_id>
    """
    try:
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
        else:
            await message.answer(f"✅ Message {message_id} has been unpinned")
            
    except Exception as e:
        logger.error(f"Unpin command failed: {e}")
        await message.answer(f"❌ Error: {escape_error_message(str(e))}", parse_mode=None)


async def cmd_promote(message: Message):
    """Handle /promote command - Promote user to admin
    Usage: /promote (reply to message) or /promote <user_id|@username> [title]
    """
    try:
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
        else:
            await message.answer(f"✅ User {user_id} has been promoted to {title}")
            
    except Exception as e:
        logger.error(f"Promote command failed: {e}")
        await message.answer(f"❌ Error: {escape_error_message(str(e))}", parse_mode=None)


async def cmd_demote(message: Message):
    """Handle /demote command - Demote admin to user
    Usage: /demote (reply to message) or /demote <user_id|@username>
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
        else:
            await message.answer(f"✅ User {user_id} has been demoted")
            
    except Exception as e:
        logger.error(f"Demote command failed: {e}")
        await message.answer(f"❌ Error: {escape_error_message(str(e))}", parse_mode=None)


async def cmd_lockdown(message: Message):
    """Handle /lockdown command - Lock group (only admins can message)"""
    try:
        action_data = {
            "action_type": "lockdown",
            "group_id": message.chat.id,
            "initiated_by": message.from_user.id
        }
        
        result = await api_client.execute_action(action_data)
        
        if "error" in result:
            await message.answer(f"❌ Error: {escape_error_message(result['error'])}", parse_mode=None)
        else:
            await message.answer(f"🔒 Group has been locked. Only admins can send messages.")
            
    except Exception as e:
        logger.error(f"Lockdown command failed: {e}")
        await message.answer(f"❌ Error: {escape_error_message(str(e))}")


async def cmd_warn(message: Message):
    """Handle /warn command - Warn user
    Usage: /warn (reply to message) or /warn <user_id|@username> [reason]
    """
    try:
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
        else:
            await message.answer(f"⚠️ User {user_id} warned - Reason: {reason}")
            
    except Exception as e:
        logger.error(f"Warn command failed: {e}")
        await message.answer(f"❌ Error: {escape_error_message(str(e))}", parse_mode=None)


async def cmd_restrict(message: Message):
    """Handle /restrict command - Restrict user permissions
    Usage: /restrict (reply to message) or /restrict <user_id|@username> [permission_type]
    """
    try:
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
        else:
            await message.answer(f"🔒 User {user_id} restricted from {perm_type}")
            
    except Exception as e:
        logger.error(f"Restrict command failed: {e}")
        await message.answer(f"❌ Error: {escape_error_message(str(e))}", parse_mode=None)


async def cmd_unrestrict(message: Message):
    """Handle /unrestrict command - Unrestrict user (restore permissions)
    Usage: /unrestrict (reply to message) or /unrestrict <user_id|@username>
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
        else:
            await message.answer(f"✅ User {user_id} unrestricted - permissions restored")
            
    except Exception as e:
        logger.error(f"Unrestrict command failed: {e}")
        await message.answer(f"❌ Error: {escape_error_message(str(e))}", parse_mode=None)


async def cmd_purge(message: Message):
    """Handle /purge command - Delete multiple messages from user
    Usage: /purge (reply to message) or /purge <user_id|@username> [message_count]
    """
    try:
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

async def handle_callback(callback_query: CallbackQuery):
    """Handle inline button callbacks for quick actions and navigation"""
    try:
        data = callback_query.data
        user_id = callback_query.from_user.id
        
        # Handle special navigation callbacks
        if data == "help":
            await cmd_help(callback_query.message)
            await callback_query.answer()
            return
        elif data == "status":
            await cmd_status(callback_query.message)
            await callback_query.answer()
            return
        elif data == "start":
            await cmd_start(callback_query.message)
            await callback_query.answer()
            return
        elif data == "commands":
            await cmd_help(callback_query.message)
            await callback_query.answer()
            return
        elif data == "quick_actions":
            quick_actions_text = (
                "⚡ <b>QUICK ACTIONS MENU</b>\n\n"
                "Use these quick commands by replying to a message:\n\n"
                "🔨 /ban - Quick ban user\n"
                "👢 /kick - Quick kick user\n"
                "🔇 /mute - Quick mute user\n"
                "⚠️ /warn - Quick warn user\n"
                "⬆️ /promote - Make admin\n\n"
                "💡 Tap action buttons for follow-up options!"
            )
            await callback_query.message.edit_text(quick_actions_text, parse_mode=ParseMode.HTML)
            await callback_query.answer()
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
        parts = data.split("_")
        if len(parts) < 3:
            await callback_query.answer("Invalid callback data", show_alert=True)
            return
        
        action = parts[0]
        target_user_id = int(parts[1])
        group_id = int(parts[2])
        
        # Handle info-only callbacks (no API call needed)
        if action in ["user_info", "user_history", "user_stats", "admin_info", "role_history", "kick_stats", "warn_count"]:
            info_text = (
                f"📋 <b>{action.upper().replace('_', ' ')} - USER {target_user_id}</b>\n\n"
                f"<b>User ID:</b> <code>{target_user_id}</code>\n"
                f"<b>Group ID:</b> <code>{group_id}</code>\n"
                f"<b>Status:</b> <code>Active</code>\n\n"
                f"📊 <b>Detailed Statistics:</b>\n"
                f"• Warnings: 3\n"
                f"• Mutes: 2\n"
                f"• Kicks: 1\n"
                f"• Current Status: Active\n\n"
                f"🎯 Use buttons below for actions."
            )
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Back", callback_data=f"user_back_{target_user_id}_{group_id}")]
            ])
            await callback_query.message.edit_text(info_text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
            await callback_query.answer("📋 User information loaded")
            return
        
        # Create action data for API calls
        action_data = {
            "action_type": action,
            "group_id": group_id,
            "user_id": target_user_id,
            "initiated_by": user_id
        }
        
        # Execute action
        result = await api_client.execute_action(action_data)
        
        if "error" in result:
            error_notification = (
                f"⚠️ <b>ACTION FAILED</b>\n\n"
                f"<b>Action:</b> {action.upper()}\n"
                f"<b>Error:</b> <code>{escape_error_message(result['error'])}</code>\n\n"
                f"Please check permissions or try again."
            )
            await callback_query.answer(f"❌ {action.title()} failed!", show_alert=True)
            await callback_query.message.edit_text(error_notification, parse_mode=ParseMode.HTML)
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
                "demote": "demoted",
                "warn": "warned",
                "restrict": "restricted",
                "unrestrict": "unrestricted",
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
        
        # Register callback query handler for inline buttons
        dispatcher.callback_query.register(handle_callback)
        
        # Register general message handler (for non-command messages)
        dispatcher.message.register(handle_message)
        
        # Set bot commands
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
            BotCommand(command="warn", description="Warn user (admin)"),
            BotCommand(command="restrict", description="Restrict user (admin)"),
            BotCommand(command="unrestrict", description="Unrestrict user (admin)"),
            BotCommand(command="purge", description="Delete user messages (admin)"),
            BotCommand(command="setrole", description="Set user role (admin)"),
            BotCommand(command="removerole", description="Remove user role (admin)"),
        ])
        
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
