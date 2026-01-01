"""
Bot command handlers for v3.

Clean, simple command implementations.
Each command follows the same easy pattern.
"""

import logging
from typing import Any

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from core.models import (
    ActionPayload,
    ActionSource,
    ActionType,
    NotificationMode,
)
from services.bidirectional import BidirectionalService

logger = logging.getLogger(__name__)


class Commands:
    """Bot command handlers."""
    
    def __init__(self, service: BidirectionalService):
        """Initialize with service instance."""
        self.service = service
    
    # ===== BAN COMMAND =====
    async def ban(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Ban a user.
        Usage: /ban <user_id> [reason]
        """
        if not await self._check_admin(update, context):
            return
        
        args = context.args
        if not args:
            await update.message.reply_text("❌ Usage: /ban <user_id> [reason]")
            return
        
        try:
            user_id = int(args[0])
            reason = " ".join(args[1:]) if len(args) > 1 else None
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID")
            return
        
        payload = ActionPayload(
            action=ActionType.BAN,
            group_id=update.effective_chat.id,
            user_id=user_id,
            admin_id=update.effective_user.id,
            reason=reason,
            source=ActionSource.BOT,
            notification_mode=NotificationMode.GROUP_AND_USER,
        )
        
        result = await self.service.execute_action(payload)
        
        if result.ok:
            reply = (
                f"🚫 *Ban executed*\n"
                f"User: `{user_id}`\n"
                f"Reason: {reason or 'N/A'}\n"
                f"⚡ {result.execution_time_ms:.0f}ms"
            )
        else:
            reply = f"❌ Ban failed: {result.error}"
        
        await update.message.reply_text(reply, parse_mode="Markdown")
    
    # ===== UNBAN COMMAND =====
    async def unban(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Unban a user.
        Usage: /unban <user_id>
        """
        if not await self._check_admin(update, context):
            return
        
        args = context.args
        if not args:
            await update.message.reply_text("❌ Usage: /unban <user_id>")
            return
        
        try:
            user_id = int(args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID")
            return
        
        payload = ActionPayload(
            action=ActionType.UNBAN,
            group_id=update.effective_chat.id,
            user_id=user_id,
            admin_id=update.effective_user.id,
            source=ActionSource.BOT,
            notification_mode=NotificationMode.GROUP_ONLY,
        )
        
        result = await self.service.execute_action(payload)
        
        if result.ok:
            reply = f"✅ User {user_id} unbanned\n⚡ {result.execution_time_ms:.0f}ms"
        else:
            reply = f"❌ Unban failed: {result.error}"
        
        await update.message.reply_text(reply, parse_mode="Markdown")
    
    # ===== MUTE COMMAND =====
    async def mute(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Mute a user.
        Usage: /mute <user_id> [hours] [reason]
        """
        if not await self._check_admin(update, context):
            return
        
        args = context.args
        if not args:
            await update.message.reply_text("❌ Usage: /mute <user_id> [hours] [reason]")
            return
        
        try:
            user_id = int(args[0])
            duration = int(args[1]) if len(args) > 1 else 24
            reason = " ".join(args[2:]) if len(args) > 2 else None
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID or duration")
            return
        
        payload = ActionPayload(
            action=ActionType.MUTE,
            group_id=update.effective_chat.id,
            user_id=user_id,
            admin_id=update.effective_user.id,
            reason=reason,
            duration_hours=duration,
            source=ActionSource.BOT,
            notification_mode=NotificationMode.GROUP_AND_USER,
        )
        
        result = await self.service.execute_action(payload)
        
        if result.ok:
            reply = (
                f"🔇 *Mute executed*\n"
                f"User: `{user_id}`\n"
                f"Duration: {duration}h\n"
                f"⚡ {result.execution_time_ms:.0f}ms"
            )
        else:
            reply = f"❌ Mute failed: {result.error}"
        
        await update.message.reply_text(reply, parse_mode="Markdown")
    
    # ===== UNMUTE COMMAND =====
    async def unmute(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Unmute a user.
        Usage: /unmute <user_id>
        """
        if not await self._check_admin(update, context):
            return
        
        args = context.args
        if not args:
            await update.message.reply_text("❌ Usage: /unmute <user_id>")
            return
        
        try:
            user_id = int(args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID")
            return
        
        payload = ActionPayload(
            action=ActionType.UNMUTE,
            group_id=update.effective_chat.id,
            user_id=user_id,
            admin_id=update.effective_user.id,
            source=ActionSource.BOT,
            notification_mode=NotificationMode.GROUP_ONLY,
        )
        
        result = await self.service.execute_action(payload)
        
        if result.ok:
            reply = f"🔊 User {user_id} unmuted\n⚡ {result.execution_time_ms:.0f}ms"
        else:
            reply = f"❌ Unmute failed: {result.error}"
        
        await update.message.reply_text(reply, parse_mode="Markdown")
    
    # ===== KICK COMMAND =====
    async def kick(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Kick a user.
        Usage: /kick <user_id> [reason]
        """
        if not await self._check_admin(update, context):
            return
        
        args = context.args
        if not args:
            await update.message.reply_text("❌ Usage: /kick <user_id> [reason]")
            return
        
        try:
            user_id = int(args[0])
            reason = " ".join(args[1:]) if len(args) > 1 else None
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID")
            return
        
        payload = ActionPayload(
            action=ActionType.KICK,
            group_id=update.effective_chat.id,
            user_id=user_id,
            admin_id=update.effective_user.id,
            reason=reason,
            source=ActionSource.BOT,
            notification_mode=NotificationMode.GROUP_ONLY,
        )
        
        result = await self.service.execute_action(payload)
        
        if result.ok:
            reply = f"👢 User {user_id} kicked\n⚡ {result.execution_time_ms:.0f}ms"
        else:
            reply = f"❌ Kick failed: {result.error}"
        
        await update.message.reply_text(reply, parse_mode="Markdown")
    
    # ===== WARN COMMAND =====
    async def warn(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Warn a user.
        Usage: /warn <user_id> [reason]
        """
        if not await self._check_admin(update, context):
            return
        
        args = context.args
        if not args:
            await update.message.reply_text("❌ Usage: /warn <user_id> [reason]")
            return
        
        try:
            user_id = int(args[0])
            reason = " ".join(args[1:]) if len(args) > 1 else None
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID")
            return
        
        payload = ActionPayload(
            action=ActionType.WARN,
            group_id=update.effective_chat.id,
            user_id=user_id,
            admin_id=update.effective_user.id,
            reason=reason,
            source=ActionSource.BOT,
            notification_mode=NotificationMode.USER_ONLY,
        )
        
        result = await self.service.execute_action(payload)
        
        if result.ok:
            reply = f"⚠️ Warning issued\n⚡ {result.execution_time_ms:.0f}ms"
        else:
            reply = f"❌ Warning failed: {result.error}"
        
        await update.message.reply_text(reply, parse_mode="Markdown")
    
    # ===== LOGS COMMAND =====
    async def logs(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Show recent action logs.
        Usage: /logs [limit]
        """
        if not await self._check_admin(update, context):
            return
        
        limit = 10
        if context.args:
            try:
                limit = int(context.args[0])
            except ValueError:
                pass
        
        # Fetch from database
        if not self.service.db:
            await update.message.reply_text("❌ Database not available")
            return
        
        try:
            logs = await self.service.db['audit_logs'].find(
                {'group_id': update.effective_chat.id}
            ).sort('_id', -1).limit(limit).to_list(None)
            
            if not logs:
                await update.message.reply_text("No logs found")
                return
            
            message = f"📋 Recent actions ({len(logs)})\n\n"
            for log in logs:
                message += (
                    f"• {log['action']} → {log['user_id']}\n"
                    f"  Reason: {log.get('reason', 'N/A')}\n"
                    f"  Source: {log.get('source', 'unknown')}\n\n"
                )
            
            await update.message.reply_text(message[:4000])  # Telegram limit
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    # ===== STATS COMMAND =====
    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Show moderation statistics.
        Usage: /stats
        """
        if not await self._check_admin(update, context):
            return
        
        metrics = self.service.get_metrics()
        
        message = (
            f"📊 *Moderation Statistics*\n\n"
            f"Total Actions: {metrics['total_actions']}\n"
            f"Bot: {metrics['bot_actions']}\n"
            f"Web: {metrics['web_actions']}\n"
            f"Success Rate: {metrics['success_rate_percent']}%\n\n"
            f"*Breakdown:*\n"
        )
        
        for action, count in metrics['action_breakdown'].items():
            message += f"• {action}: {count}\n"
        
        await update.message.reply_text(message, parse_mode="Markdown")
    
    # ===== HELPER METHODS =====
    async def _check_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Check if user is admin."""
        try:
            member = await context.bot.get_chat_member(
                update.effective_chat.id,
                update.effective_user.id
            )
            if member.status not in ["administrator", "creator"]:
                await update.message.reply_text("❌ Only admins can use this command")
                return False
            return True
        except Exception as e:
            logger.error(f"Admin check failed: {str(e)}")
            return False


def register_commands(application: Any, service: BidirectionalService) -> None:
    """
    Register all commands with the bot application.
    
    Usage:
        register_commands(application, service)
    """
    commands = Commands(service)
    
    application.add_handler(CommandHandler('ban', commands.ban))
    application.add_handler(CommandHandler('unban', commands.unban))
    application.add_handler(CommandHandler('mute', commands.mute))
    application.add_handler(CommandHandler('unmute', commands.unmute))
    application.add_handler(CommandHandler('kick', commands.kick))
    application.add_handler(CommandHandler('warn', commands.warn))
    application.add_handler(CommandHandler('logs', commands.logs))
    application.add_handler(CommandHandler('stats', commands.stats))
    
    logger.info("✓ All commands registered")