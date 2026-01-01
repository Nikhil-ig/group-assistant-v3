"""
Telegram Bot Command Handlers for V3 Bot.
Handles all Telegram commands with admin permission checks.

Commands:
- /ban: Ban user from group (SUPERADMIN or GROUP_ADMIN only)
- /unban: Unban user from group
- /kick: Kick user from group
- /warn: Warn user
- /mute: Mute user
- /unmute: Unmute user
- /restrict: Restrict specific permissions
- /free: Remove all restrictions from a user
- /id: Get user ID and info
- /settings: Show group settings
- /promote: Promote user to admin (owner only)
- /demote: Demote admin to regular user (owner only)
- /logs: Show audit logs for group
- /stats: Show moderation statistics
"""

from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes, CommandHandler, CallbackContext, MessageHandler, filters, ChatMemberHandler
import logging
from datetime import datetime, timedelta, timezone
import asyncio

from ..config.settings import config
from ..services.database import DatabaseService, ActionType, UserRole
from ..services.telegram_api import TelegramAPIService

logger = logging.getLogger(__name__)
import inspect


# Minimal in-memory stub DB to allow running handlers when the real
# DatabaseService is not available (useful for debug runner).
class _DummyDB:
    async def log_action(self, *args, **kwargs):
        logger.debug("_DummyDB.log_action called with %s %s", args, kwargs)
        return True

    async def update_metrics(self, *args, **kwargs):
        logger.debug("_DummyDB.update_metrics called with %s %s", args, kwargs)
        return True

    async def get_audit_logs(self, *args, **kwargs):
        logger.debug("_DummyDB.get_audit_logs called with %s %s", args, kwargs)
        return []

    async def get_metrics(self, *args, **kwargs):
        logger.debug("_DummyDB.get_metrics called with %s %s", args, kwargs)
        return {}

    async def is_group_admin(self, *args, **kwargs):
        logger.debug("_DummyDB.is_group_admin called with %s %s", args, kwargs)
        return False
    # Lightweight stubs for member/admin/blacklist APIs used by handlers
    async def upsert_member(self, group_id, user_id, username=None, first_name=None, is_bot=False, **kwargs):
        logger.debug("_DummyDB.upsert_member: %s %s", group_id, user_id)
        return True

    async def record_join(self, group_id, user, when=None):
        logger.debug("_DummyDB.record_join: %s %s", group_id, user)
        return True

    async def record_leave(self, group_id, user_id, when=None):
        logger.debug("_DummyDB.record_leave: %s %s", group_id, user_id)
        return True

    async def add_group_admin(self, group_id, user_id, username, first_name):
        logger.debug("_DummyDB.add_group_admin: %s %s", group_id, user_id)
        return True

    async def sync_group_admins(self, group_id, admins):
        logger.debug("_DummyDB.sync_group_admins: %s admins=%s", group_id, admins)
        return True

    async def get_member(self, group_id, user_id):
        logger.debug("_DummyDB.get_member: %s %s", group_id, user_id)
        return None

    async def add_to_blacklist(self, group_id, user_id, **kwargs):
        logger.debug("_DummyDB.add_to_blacklist: %s %s", group_id, user_id)
        return True

    async def remove_from_blacklist(self, group_id, user_id):
        logger.debug("_DummyDB.remove_from_blacklist: %s %s", group_id, user_id)
        return True

    async def is_blacklisted(self, group_id, user_id):
        logger.debug("_DummyDB.is_blacklisted: %s %s", group_id, user_id)
        return False

    async def add_to_whitelist(self, group_id, user_id, **kwargs):
        logger.debug("_DummyDB.add_to_whitelist: %s %s", group_id, user_id)
        return True

    async def remove_from_whitelist(self, group_id, user_id):
        logger.debug("_DummyDB.remove_from_whitelist: %s %s", group_id, user_id)
        return True

    async def is_whitelisted(self, group_id, user_id):
        logger.debug("_DummyDB.is_whitelisted: %s %s", group_id, user_id)
        return False

    async def is_user_muted(self, group_id, user_id):
        logger.debug("_DummyDB.is_user_muted: %s %s", group_id, user_id)
        return False



class BotCommandHandlers:
    """Command handlers for Telegram bot."""
    
    def __init__(self, db_service: DatabaseService, telegram_api: TelegramAPIService = None):
        """Initialize command handlers.
        
        Args:
            db_service: Database service instance
            telegram_api: Optional Telegram API service for executing actions
        """
        self.db = db_service
        self.telegram_api = telegram_api

    async def _resolve_username_to_id(self, context: CallbackContext, username: str):
        """Try to resolve a Telegram username (@username) to a user id via get_chat.

        Returns tuple (user_id:int, username:str) or (None, None) on failure.
        """
        try:
            uname = username.lstrip("@")
            chat = await context.bot.get_chat(f"@{uname}")
            # chat.id will be the user id for private chats
            return chat.id, getattr(chat, "username", uname)
        except Exception as e:
            logger.debug(f"Could not resolve username @{username}: {e}")
            return None, None

    async def _parse_target(self, update: Update, context: CallbackContext):
        """Parse target user from either a reply or the first command argument.

        Returns (target_user_id:int, target_username:str or None)
        """
        # 1) If the command was sent as a reply, prefer that target
        if update.message.reply_to_message and update.message.reply_to_message.from_user:
            u = update.message.reply_to_message.from_user
            return u.id, u.username or u.first_name

        # 2) Else, look at the first arg
        if context.args and len(context.args) > 0:
            first = context.args[0]
            # username like @user
            if isinstance(first, str) and first.startswith("@"):
                uid, uname = await self._resolve_username_to_id(context, first)
                if uid:
                    return uid, uname
                else:
                    return None, None

            # numeric id
            try:
                return int(first), None
            except Exception:
                return None, None

        return None, None

    def _build_chat_permissions(self, **kwargs) -> ChatPermissions:
        """Build ChatPermissions with only supported keyword args for current PTB.

        Uses inspect.signature to filter unsupported keywords so code works across
        different python-telegram-bot versions.
        """
        try:
            sig = inspect.signature(ChatPermissions.__init__)
            valid = [p for p in sig.parameters.keys() if p not in ("self", "args", "kwargs")]
            usable = {k: v for k, v in kwargs.items() if k in valid}
            return ChatPermissions(**usable)
        except Exception:
            # Fallback: attempt minimal permissions constructor
            try:
                return ChatPermissions(can_send_messages=kwargs.get("can_send_messages", True))
            except Exception:
                # As a last resort, return an empty ChatPermissions()
                return ChatPermissions()
    
    async def _check_admin(self, update: Update, context: CallbackContext, group_id: int) -> bool:
        """Check if user is admin of the group."""
        try:
            user = update.message.from_user
            logger.info(f"🔐 Checking admin status - User {user.id} ({user.username}) in group {group_id}")
            
            # Get admin list from Telegram to verify actual admin status
            try:
                admins = await context.bot.get_chat_administrators(group_id)
                admin_ids = [admin.user.id for admin in admins]
                
                logger.info(f"✅ Group {group_id} admins from Telegram: {admin_ids}")
                logger.info(f"🔍 Checking if user {user.id} is in admin list")
                
                if user.id not in admin_ids:
                    logger.warning(f"❌ User {user.id} ({user.username}) NOT in admin list for group {group_id}")
                    await update.message.reply_text(
                        "❌ You don't have permission to use this command.\n\n"
                        "Only group admins can use moderation commands."
                    )
                    return False
                
                logger.info(f"✅ User {user.id} ({user.username}) IS ADMIN, allowing command")
                return True
            except Exception as e:
                logger.error(f"❌ Error getting admin list from Telegram: {e}", exc_info=True)
                # Fallback to database check
                logger.info(f"⚙️ Falling back to database admin check...")
                is_admin = await self.db.is_group_admin(user.id, group_id)
                logger.info(f"📝 Database admin check result: {is_admin}")
                if not is_admin:
                    await update.message.reply_text(
                        "❌ You don't have permission to use this command."
                    )
                return is_admin
        
        except Exception as e:
            logger.error(f"❌ Error checking admin status: {e}", exc_info=True)
            await update.message.reply_text("❌ Error checking permissions")
            return False
    
    async def ban_command(self, update: Update, context: CallbackContext):
        """Ban user from group: /ban <user_id> [reason]"""
        try:
            if not update.message.chat.type in ["group", "supergroup"]:
                await update.message.reply_text("⚠️ This command can only be used in groups")
                return
            
            group_id = update.message.chat.id
            
            # Check admin permission
            if not await self._check_admin(update, context, group_id):
                return
            # Parse target: supports replying to a message or passing an id/@username
            target_user_id, target_username = await self._parse_target(update, context)
            if not target_user_id:
                await update.message.reply_text("Usage: /ban <user_id|@username> or reply to a user's message with /ban [reason]")
                return

            # Reason handling: if command was a reply, the args are the reason; else args after target are the reason
            if update.message.reply_to_message:
                reason = " ".join(context.args) if context.args else None
            else:
                reason = " ".join(context.args[1:]) if len(context.args) > 1 else None
            
            user = update.message.from_user
            
            # If already blacklisted/banned, inform the admin and skip
            try:
                already_banned = await self.db.is_blacklisted(group_id, target_user_id)
            except Exception:
                already_banned = False

            if already_banned:
                await update.message.reply_text(f"ℹ️ User {target_user_id} is already banned")
                return

            # Execute ban on Telegram (if API service available)
            telegram_success = True
            telegram_error = None
            
            if self.telegram_api:
                logger.info(f"📤 Executing BAN via Telegram API for user {target_user_id}")
                telegram_success, telegram_error = await self.telegram_api.ban_user(
                    group_id=group_id,
                    user_id=target_user_id,
                    reason=reason,
                )
                if not telegram_success:
                    logger.error(f"❌ Ban failed on Telegram: {telegram_error}")
            else:
                logger.warning("⚠️ Telegram API service not available, skipping Telegram execution")
            
            # Log action in database (always, even if Telegram fails)
            db_success = await self.db.log_action(
                group_id=group_id,
                action_type=ActionType.BAN,
                admin_id=user.id,
                admin_username=user.username or user.first_name,
                target_user_id=target_user_id,
                target_username=target_username,
                reason=reason,
            )
            
            if db_success:
                # Persist ban to blacklist collection for future checks
                try:
                    await self.db.add_to_blacklist(group_id, target_user_id, reason=reason, added_by=user.id)
                except Exception:
                    logger.exception("Failed to persist blacklist entry")
                
                await self.db.update_metrics(group_id, ActionType.BAN)
                
                if telegram_success or not self.telegram_api:
                    await update.message.reply_text(f"✅ User {target_user_id} has been banned")
                else:
                    await update.message.reply_text(
                        f"⚠️ User {target_user_id} logged as banned, but Telegram action failed: {telegram_error}"
                    )
            else:
                await update.message.reply_text("❌ Failed to execute ban")
        
        except Exception as e:
            logger.error(f"Error in ban command: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def track_message(self, update: Update, context: CallbackContext):
        """Generic message tracker: upserts member last_seen and basic profile info.

        This handler is intentionally lightweight and optimized for high throughput.
        """
        try:
            if not update.effective_chat or not update.effective_user:
                return

            chat_id = update.effective_chat.id
            user = update.effective_user

            # Best-effort non-blocking upsert; we don't await heavy ops in hot paths.
            await self.db.upsert_member(
                group_id=chat_id,
                user_id=user.id,
                username=getattr(user, "username", None),
                first_name=getattr(user, "first_name", None),
                is_bot=getattr(user, "is_bot", False),
                last_seen=datetime.now(timezone.utc),
            )
        except Exception:
            logger.exception("Failed to track message/member")

    async def chat_member_update(self, update: Update, context: CallbackContext):
        """Track join/leave/admin changes from ChatMember updates.

        Keeps join/leave timestamps and syncs admin list for the group.
        """
        try:
            # PTB exposes the changed chat member in update.chat_member or update.my_chat_member
            chat_member = getattr(update, "chat_member", None) or getattr(update, "my_chat_member", None)
            if not chat_member:
                return

            chat = chat_member.chat
            group_id = chat.id

            old = chat_member.old_chat_member
            new = chat_member.new_chat_member

            # user object
            user = new.user if hasattr(new, "user") else new
            uid = getattr(user, "id", None) or user.get("id")

            # Joined
            try:
                new_status = new.status
            except Exception:
                new_status = None

            # Record join
            if new_status in ("member", "restricted", "administrator", "creator"):
                await self.db.record_join(group_id, {"id": uid, "username": getattr(user, "username", None), "first_name": getattr(user, "first_name", None), "is_bot": getattr(user, "is_bot", False)})

            # Left or kicked
            if new_status in ("left", "kicked"):
                await self.db.record_leave(group_id, uid)

            # If became admin or owner, upsert into admins collection
            if new_status in ("administrator", "creator"):
                await self.db.add_group_admin(group_id=group_id, user_id=uid, username=getattr(user, "username", None) or "", first_name=getattr(user, "first_name", None) or "")

        except Exception:
            logger.exception("Error handling chat_member_update")
    
    async def unban_command(self, update: Update, context: CallbackContext):
        """Unban user from group: /unban <user_id>"""
        try:
            if not update.message.chat.type in ["group", "supergroup"]:
                await update.message.reply_text("⚠️ This command can only be used in groups")
                return
            
            group_id = update.message.chat.id
            
            if not await self._check_admin(update, context, group_id):
                return
            # Support reply or id/@username
            target_user_id, target_username = await self._parse_target(update, context)
            if not target_user_id:
                await update.message.reply_text("Usage: /unban <user_id|@username> or reply to a user's message with /unban")
                return
            
            user = update.message.from_user
            
            # Execute unban on Telegram (if API service available)
            telegram_success = True
            telegram_error = None
            
            if self.telegram_api:
                logger.info(f"📤 Executing UNBAN via Telegram API for user {target_user_id}")
                telegram_success, telegram_error = await self.telegram_api.unban_user(
                    group_id=group_id,
                    user_id=target_user_id,
                )
                if not telegram_success:
                    logger.error(f"❌ Unban failed on Telegram: {telegram_error}")
            else:
                logger.warning("⚠️ Telegram API service not available, skipping Telegram execution")
            
            # Log action in database (always, even if Telegram fails)
            db_success = await self.db.log_action(
                group_id=group_id,
                action_type=ActionType.UNBAN,
                admin_id=user.id,
                admin_username=user.username or user.first_name,
                target_user_id=target_user_id,
                target_username=target_username,
            )
            
            if db_success:
                # Remove from blacklist if present
                try:
                    await self.db.remove_from_blacklist(group_id, target_user_id)
                except Exception:
                    logger.exception("Failed to remove blacklist entry during unban")
                
                await self.db.update_metrics(group_id, ActionType.UNBAN)
                
                if telegram_success or not self.telegram_api:
                    await update.message.reply_text(f"✅ User {target_user_id} has been unbanned")
                else:
                    await update.message.reply_text(
                        f"⚠️ User {target_user_id} logged as unbanned, but Telegram action failed: {telegram_error}"
                    )
            else:
                await update.message.reply_text("❌ Failed to execute unban")
        
        except Exception as e:
            logger.error(f"Error in unban command: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def kick_command(self, update: Update, context: CallbackContext):
        """Kick user from group: /kick <user_id> [reason]"""
        try:
            if not update.message.chat.type in ["group", "supergroup"]:
                await update.message.reply_text("⚠️ This command can only be used in groups")
                return
            
            group_id = update.message.chat.id
            
            if not await self._check_admin(update, context, group_id):
                return
            target_user_id, target_username = await self._parse_target(update, context)
            if not target_user_id:
                await update.message.reply_text("Usage: /kick <user_id|@username> or reply to a user's message with /kick [reason]")
                return

            if update.message.reply_to_message:
                reason = " ".join(context.args) if context.args else None
            else:
                reason = " ".join(context.args[1:]) if len(context.args) > 1 else None
            
            user = update.message.from_user
            
            # Execute kick on Telegram (if API service available)
            telegram_success = True
            telegram_error = None
            
            if self.telegram_api:
                logger.info(f"📤 Executing KICK via Telegram API for user {target_user_id}")
                telegram_success, telegram_error = await self.telegram_api.kick_user(
                    group_id=group_id,
                    user_id=target_user_id,
                    reason=reason,
                )
                if not telegram_success:
                    logger.error(f"❌ Kick failed on Telegram: {telegram_error}")
            else:
                logger.warning("⚠️ Telegram API service not available, skipping Telegram execution")
            
            # Log action in database (always, even if Telegram fails)
            db_success = await self.db.log_action(
                group_id=group_id,
                action_type=ActionType.KICK,
                admin_id=user.id,
                admin_username=user.username or user.first_name,
                target_user_id=target_user_id,
                reason=reason,
            )
            
            if db_success:
                await self.db.update_metrics(group_id, ActionType.KICK)
                
                target_disp = target_username or target_user_id
                if telegram_success or not self.telegram_api:
                    await update.message.reply_text(f"✅ User {target_disp} has been kicked")
                else:
                    await update.message.reply_text(
                        f"⚠️ User {target_disp} logged as kicked, but Telegram action failed: {telegram_error}"
                    )
            else:
                await update.message.reply_text("❌ Failed to execute kick")
        
        except Exception as e:
            logger.error(f"Error in kick command: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def warn_command(self, update: Update, context: CallbackContext):
        """Warn user: /warn <user_id> [reason]"""
        try:
            if not update.message.chat.type in ["group", "supergroup"]:
                await update.message.reply_text("⚠️ This command can only be used in groups")
                return
            
            group_id = update.message.chat.id
            
            if not await self._check_admin(update, context, group_id):
                return
            target_user_id, target_username = await self._parse_target(update, context)
            if not target_user_id:
                await update.message.reply_text("Usage: /warn <user_id|@username> or reply to a user's message with /warn [reason]")
                return

            if update.message.reply_to_message:
                reason = " ".join(context.args) if context.args else None
            else:
                reason = " ".join(context.args[1:]) if len(context.args) > 1 else None
            
            user = update.message.from_user
            
            # Execute warn on Telegram (if API service available)
            if self.telegram_api:
                logger.info(f"📤 Executing WARN via Telegram API for user {target_user_id}")
                await self.telegram_api.warn_user(
                    group_id=group_id,
                    user_id=target_user_id,
                    reason=reason,
                    admin_name=user.username or user.first_name,
                )
            else:
                logger.warning("⚠️ Telegram API service not available, skipping Telegram warning")
            
            # Log action in database (always)
            db_success = await self.db.log_action(
                group_id=group_id,
                action_type=ActionType.WARN,
                admin_id=user.id,
                admin_username=user.username or user.first_name,
                target_user_id=target_user_id,
                reason=reason,
            )
            
            if db_success:
                await self.db.update_metrics(group_id, ActionType.WARN)
                target_disp = target_username or target_user_id
                await update.message.reply_text(f"⚠️ User {target_disp} has been warned")
            else:
                await update.message.reply_text("❌ Failed to execute warn")
        
        except Exception as e:
            logger.error(f"Error in warn command: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def mute_command(self, update: Update, context: CallbackContext):
        """Mute user: /mute <user_id> [hours] [reason]"""
        try:
            if not update.message.chat.type in ["group", "supergroup"]:
                await update.message.reply_text("⚠️ This command can only be used in groups")
                return
            
            group_id = update.message.chat.id
            
            if not await self._check_admin(update, context, group_id):
                return
            # Parse target & optional duration/reason. Support reply usage.
            target_user_id, target_username = await self._parse_target(update, context)
            if not target_user_id:
                await update.message.reply_text("Usage: /mute <user_id|@username> or reply to a user's message with /mute [hours] [reason]")
                return

            duration_hours = None
            reason = None
            if update.message.reply_to_message:
                # args[0] may be duration
                if context.args and len(context.args) > 0:
                    try:
                        duration_hours = int(context.args[0])
                        reason = " ".join(context.args[1:]) if len(context.args) > 1 else None
                    except ValueError:
                        reason = " ".join(context.args)
            else:
                # not a reply: args[1] may be duration
                if context.args and len(context.args) > 1:
                    try:
                        duration_hours = int(context.args[1])
                        reason = " ".join(context.args[2:]) if len(context.args) > 2 else None
                    except ValueError:
                        reason = " ".join(context.args[1:]) if len(context.args) > 1 else None
            
            user = update.message.from_user
            
            # If already muted, inform and skip
            try:
                is_muted = await self.db.is_user_muted(group_id, target_user_id)
            except Exception:
                is_muted = False

            if is_muted:
                target_disp = target_username or target_user_id
                await update.message.reply_text(f"ℹ️ User {target_disp} is already muted")
                return

            # Execute mute on Telegram (if API service available)
            telegram_success = True
            telegram_error = None
            
            if self.telegram_api:
                logger.info(f"📤 Executing MUTE via Telegram API for user {target_user_id}")
                telegram_success, telegram_error = await self.telegram_api.mute_user(
                    group_id=group_id,
                    user_id=target_user_id,
                    duration_hours=duration_hours,
                    reason=reason,
                )
                if not telegram_success:
                    logger.error(f"❌ Mute failed on Telegram: {telegram_error}")
            else:
                logger.warning("⚠️ Telegram API service not available, skipping Telegram execution")
            
            # Log action in database (always, even if Telegram fails)
            db_success = await self.db.log_action(
                group_id=group_id,
                action_type=ActionType.MUTE,
                admin_id=user.id,
                admin_username=user.username or user.first_name,
                target_user_id=target_user_id,
                duration_hours=duration_hours,
                reason=reason,
            )
            
            if db_success:
                await self.db.update_metrics(group_id, ActionType.MUTE)
                
                target_disp = target_username or target_user_id
                msg = f"🔇 User {target_disp} has been muted"
                if duration_hours:
                    msg += f" for {duration_hours} hours"
                
                if telegram_success or not self.telegram_api:
                    await update.message.reply_text(msg)
                else:
                    await update.message.reply_text(
                        f"{msg} (logged), but Telegram action failed: {telegram_error}"
                    )
            else:
                await update.message.reply_text("❌ Failed to execute mute")
        
        except Exception as e:
            logger.error(f"Error in mute command: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def unmute_command(self, update: Update, context: CallbackContext):
        """Unmute user: /unmute <user_id> or reply to a user's message"""
        try:
            if not update.message.chat.type in ["group", "supergroup"]:
                await update.message.reply_text("⚠️ This command can only be used in groups")
                return

            group_id = update.message.chat.id

            if not await self._check_admin(update, context, group_id):
                return

            target_user_id, target_username = await self._parse_target(update, context)
            if not target_user_id:
                await update.message.reply_text("Usage: /unmute <user_id|@username> or reply to a user's message with /unmute")
                return

            user = update.message.from_user

            # Execute unmute on Telegram (if API service available)
            telegram_success = True
            telegram_error = None
            
            if self.telegram_api:
                logger.info(f"📤 Executing UNMUTE via Telegram API for user {target_user_id}")
                telegram_success, telegram_error = await self.telegram_api.unmute_user(
                    group_id=group_id,
                    user_id=target_user_id,
                )
                if not telegram_success:
                    logger.error(f"❌ Unmute failed on Telegram: {telegram_error}")
            else:
                logger.warning("⚠️ Telegram API service not available, skipping Telegram execution")
            
            # Log action in database (always, even if Telegram fails)
            db_success = await self.db.log_action(
                group_id=group_id,
                action_type=ActionType.UNMUTE,
                admin_id=user.id,
                admin_username=user.username or user.first_name,
                target_user_id=target_user_id,
                target_username=target_username,
            )

            if db_success:
                await self.db.update_metrics(group_id, ActionType.UNMUTE)
                
                target_disp = target_username or target_user_id
                if telegram_success or not self.telegram_api:
                    await update.message.reply_text(f"🔊 User {target_disp} has been unmuted")
                else:
                    await update.message.reply_text(
                        f"⚠️ User {target_disp} logged as unmuted, but Telegram action failed: {telegram_error}"
                    )
            else:
                await update.message.reply_text("❌ Failed to execute unmute")

        except Exception as e:
            logger.error(f"Error in unmute command: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def restrict_command(self, update: Update, context: CallbackContext):
        """Restrict specific permissions: 
        - /restrict <user_id|@username> <block_type> [block_type2...] [hours]
        - Reply to message with /restrict <block_type> [block_type2...] [hours]
        """
        try:
            if not update.message.chat.type in ["group", "supergroup"]:
                await update.message.reply_text("⚠️ This command can only be used in groups")
                return

            group_id = update.message.chat.id

            if not await self._check_admin(update, context, group_id):
                return

            # Check if command was used as a reply
            if update.message.reply_to_message:
                # Reply mode: /restrict <block_type> [block_type2...] [hours]
                reply_msg = update.message.reply_to_message
                target_user_id = reply_msg.from_user.id
                target_username = reply_msg.from_user.username
                
                if not context.args or len(context.args) < 1:
                    await update.message.reply_text(
                        "📋 Usage (reply mode): /restrict <block_type> [block_type2...] [hours]\n\n"
                        "Block types:\n"
                        "  • media - Block all media\n"
                        "  • stickers - Block stickers\n"
                        "  • gifs - Block GIFs\n"
                        "  • polls - Block polls\n"
                        "  • links - Block links\n"
                        "  • voice - Block voice messages\n"
                        "  • video - Block videos\n"
                        "  • audio - Block audio\n"
                        "  • documents - Block documents\n"
                        "  • photos - Block photos\n"
                        "  • all_messages - Block all messages\n\n"
                        "Example: /restrict stickers gifs 24"
                    )
                    return
                
                # Parse block types and optional duration (from args directly)
                blocked_types = []
                duration_hours = None
                
                for arg in context.args:
                    if arg.isdigit():
                        duration_hours = int(arg)
                        break
                    else:
                        blocked_types.append(arg.lower())
                
                if not blocked_types:
                    await update.message.reply_text("❌ Please specify at least one permission type to block")
                    return
            else:
                # Direct mode: /restrict <user_id|@username> <block_type> [block_type2...] [hours]
                if not context.args or len(context.args) < 2:
                    await update.message.reply_text(
                        "Usage: /restrict <user_id|@username> <block_type> [block_type2...] [hours]\n\n"
                        "Or reply to a message with: /restrict <block_type> [block_type2...] [hours]\n\n"
                        "Block types:\n"
                        "  • media - Block all media (photos, videos, documents, audio, voice)\n"
                        "  • stickers - Block stickers\n"
                        "  • gifs - Block GIFs/animations\n"
                        "  • polls - Block polls\n"
                        "  • links - Block web page previews\n"
                        "  • voice - Block voice messages\n"
                        "  • video - Block videos\n"
                        "  • audio - Block audio\n"
                        "  • documents - Block documents\n"
                        "  • photos - Block photos\n"
                        "  • all_messages - Block all messages\n\n"
                        "Examples:\n"
                        "  • /restrict @user stickers gifs 24\n"
                        "  • /restrict 123456 media\n"
                        "  • Reply to message then /restrict stickers gifs"
                    )
                    return

                target_user_id, target_username = await self._parse_target(update, context, first_arg_idx=0)
                if not target_user_id:
                    await update.message.reply_text("Usage: /restrict <user_id|@username> <block_type> [block_type2...]")
                    return

                # Parse block types and optional duration
                blocked_types = []
                duration_hours = None
                
                # Start from arg 1 (after user_id)
                for i, arg in enumerate(context.args[1:]):
                    if arg.isdigit():
                        # This is the duration
                        duration_hours = int(arg)
                        break
                    else:
                        # This is a block type
                        blocked_types.append(arg.lower())
                
                if not blocked_types:
                    await update.message.reply_text("❌ Please specify at least one permission type to block")
                    return

            user = update.message.from_user

            # Execute restriction on Telegram
            telegram_success = True
            telegram_error = None
            
            if self.telegram_api:
                logger.info(f"📤 Executing RESTRICT via Telegram API for user {target_user_id}, blocking: {blocked_types}")
                telegram_success, telegram_error = await self.telegram_api.restrict_user_permissions(
                    group_id=group_id,
                    user_id=target_user_id,
                    blocked_types=blocked_types,
                    duration_hours=duration_hours,
                    reason=f"Blocked by {user.username or user.first_name}: {', '.join(blocked_types)}"
                )
                if not telegram_success:
                    logger.error(f"❌ Restrict failed on Telegram: {telegram_error}")
            else:
                logger.warning("⚠️ Telegram API service not available, skipping Telegram execution")

            # Log action in database
            db_success = await self.db.log_action(
                group_id=group_id,
                action_type=ActionType.MUTE,  # Using MUTE as the action type (no RESTRICT action type exists)
                admin_id=user.id,
                admin_username=user.username or user.first_name,
                target_user_id=target_user_id,
                target_username=target_username,
                reason=f"Restrict: {', '.join(blocked_types)}" + (f" for {duration_hours}h" if duration_hours else "")
            )

            if db_success:
                await self.db.update_metrics(group_id, ActionType.MUTE)
                
                target_disp = target_username or target_user_id
                blocked_str = ", ".join(blocked_types)
                duration_str = f" for {duration_hours} hours" if duration_hours else " (permanent)"
                
                if telegram_success or not self.telegram_api:
                    await update.message.reply_text(
                        f"🚫 User {target_disp} restricted\n\n"
                        f"Blocked: {blocked_str}\n"
                        f"Duration: {duration_str}"
                    )
                else:
                    await update.message.reply_text(
                        f"⚠️ User {target_disp} logged as restricted, but Telegram action failed: {telegram_error}"
                    )
            else:
                await update.message.reply_text("❌ Failed to execute restriction")

        except Exception as e:
            logger.error(f"Error in restrict command: {e}", exc_info=True)
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def logs_command(self, update: Update, context: CallbackContext):
        """Show recent audit logs: /logs [limit]"""
        logger.info("🔴 LOGS HANDLER CALLED!")  # DEBUG
        try:
            logger.info(f"📋 /logs command received from {update.message.from_user.username} in group {update.message.chat.id}")
            
            if not update.message.chat.type in ["group", "supergroup"]:
                logger.warning(f"Logs command used in non-group chat type: {update.message.chat.type}")
                await update.message.reply_text("⚠️ This command can only be used in groups")
                return
            
            group_id = update.message.chat.id
            logger.info(f"🔍 Checking admin for /logs in group {group_id}")
            
            if not await self._check_admin(update, context, group_id):
                logger.warning(f"❌ User {update.message.from_user.id} denied /logs - not admin")
                return
            
            logger.info(f"✅ User is admin, fetching logs")
            
            limit = 5
            if context.args and len(context.args) > 0:
                try:
                    limit = int(context.args[0])
                    logger.info(f"📊 Custom limit: {limit}")
                except ValueError:
                    pass
            
            logger.info(f"🔎 Fetching {limit} audit logs for group {group_id}")
            logs = await self.db.get_audit_logs(group_id=group_id, limit=limit)
            
            logger.info(f"✅ Got {len(logs) if logs else 0} logs")
            
            if not logs:
                logger.info(f"ℹ️ No audit logs found for group {group_id}")
                await update.message.reply_text("📋 No audit logs found")
                return
            
            msg = "📋 **Recent Audit Logs:**\n\n"
            for log in logs:
                msg += f"• {log['action_type']} by @{log['admin_username']}\n"
                msg += f"  Target: {log.get('target_username', log['target_user_id'])}\n"
                if log.get('reason'):
                    msg += f"  Reason: {log['reason']}\n"
                msg += f"  Time: {log['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            logger.info(f"📤 Sending logs message to group {group_id}")
            await update.message.reply_text(msg, parse_mode="Markdown")
            logger.info(f"✅ Logs sent successfully")
        
        except Exception as e:
            logger.error(f"❌ Error in logs command: {e}", exc_info=True)
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def stats_command(self, update: Update, context: CallbackContext):
        """Show group statistics: /stats"""
        logger.info("🔴 STATS HANDLER CALLED!")  # DEBUG
        try:
            logger.info(f"📊 /stats command received from {update.message.from_user.username} (ID: {update.message.from_user.id}) in group {update.message.chat.id}")
            
            if not update.message.chat.type in ["group", "supergroup"]:
                logger.warning(f"Stats command used in non-group chat type: {update.message.chat.type}")
                await update.message.reply_text("⚠️ This command can only be used in groups")
                return
            
            group_id = update.message.chat.id
            logger.info(f"🔍 Checking admin status for user {update.message.from_user.id} in group {group_id}")
            
            if not await self._check_admin(update, context, group_id):
                logger.warning(f"❌ User {update.message.from_user.id} denied /stats - not admin")
                return
            
            logger.info(f"✅ User is admin, fetching metrics")
            
            metrics = await self.db.get_metrics(group_id)
            logger.info(f"📊 Retrieved metrics: {metrics}")
            
            if not metrics:
                logger.info(f"ℹ️ No statistics available yet for group {group_id}")
                await update.message.reply_text("📊 No statistics available yet")
                return
            
            total = metrics.get('total_actions', 0)
            actions = metrics.get('actions', {})
            
            msg = f"📊 **Group Statistics for {group_id}:**\n\n"
            msg += f"Total Actions: {total}\n\n"
            msg += "Breakdown:\n"
            for action_type, count in actions.items():
                msg += f"  • {action_type.upper()}: {count}\n"
            
            if metrics.get('last_action_at'):
                msg += f"\nLast Action: {metrics['last_action_at'].strftime('%Y-%m-%d %H:%M:%S')}"
            
            logger.info(f"📤 Sending stats message to group {group_id}")
            await update.message.reply_text(msg, parse_mode="Markdown")
            logger.info(f"✅ Stats sent successfully")
        
        except Exception as e:
            logger.error(f"❌ Error in stats command: {e}", exc_info=True)
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def free_command(self, update: Update, context: CallbackContext):
        """Remove all restrictions from a user: /free <user_id|@username> or reply"""
        try:
            if not update.message.chat.type in ["group", "supergroup"]:
                await update.message.reply_text("⚠️ This command can only be used in groups")
                return

            group_id = update.message.chat.id

            if not await self._check_admin(update, context, group_id):
                return

            target_user_id, target_username = await self._parse_target(update, context)
            if not target_user_id:
                await update.message.reply_text("Usage: /free <user_id|@username> or reply to a user's message with /free")
                return

            user = update.message.from_user

            # Execute unrestriction on Telegram
            telegram_success = True
            telegram_error = None
            
            if self.telegram_api:
                logger.info(f"📤 Executing FREE via Telegram API for user {target_user_id}")
                telegram_success, telegram_error = await self.telegram_api.unmute_user(
                    group_id=group_id,
                    user_id=target_user_id,
                )
                if not telegram_success:
                    logger.error(f"❌ Free failed on Telegram: {telegram_error}")
            else:
                logger.warning("⚠️ Telegram API service not available, skipping Telegram execution")

            # Log action in database
            db_success = await self.db.log_action(
                group_id=group_id,
                action_type=ActionType.UNMUTE,
                admin_id=user.id,
                admin_username=user.username or user.first_name,
                target_user_id=target_user_id,
                target_username=target_username,
                reason="Removed all restrictions"
            )

            if db_success:
                await self.db.update_metrics(group_id, ActionType.UNMUTE)
                
                target_disp = target_username or target_user_id
                if telegram_success or not self.telegram_api:
                    await update.message.reply_text(f"🔓 User {target_disp} has been freed (all restrictions removed)")
                else:
                    await update.message.reply_text(
                        f"⚠️ User {target_disp} logged as freed, but Telegram action failed: {telegram_error}"
                    )
            else:
                await update.message.reply_text("❌ Failed to execute free")

        except Exception as e:
            logger.error(f"Error in free command: {e}", exc_info=True)
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def id_command(self, update: Update, context: CallbackContext):
        """Get user ID and info: /id or reply to a message"""
        try:
            # If replying to a message, get that user's info
            if update.message.reply_to_message:
                user = update.message.reply_to_message.from_user
            else:
                user = update.message.from_user

            msg = f"👤 **User Information:**\n\n"
            msg += f"ID: `{user.id}`\n"
            msg += f"Name: {user.first_name or 'N/A'}"
            if user.last_name:
                msg += f" {user.last_name}"
            msg += "\n"
            if user.username:
                msg += f"Username: @{user.username}\n"
            msg += f"Bot: {'Yes' if user.is_bot else 'No'}\n"
            
            # Add group info if in group
            if update.message.chat.type in ["group", "supergroup"]:
                msg += f"\nGroup ID: `{update.message.chat.id}`\n"
                msg += f"Group: {update.message.chat.title}\n"

            await update.message.reply_text(msg, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Error in id command: {e}", exc_info=True)
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def settings_command(self, update: Update, context: CallbackContext):
        """Show group settings: /settings"""
        try:
            if not update.message.chat.type in ["group", "supergroup"]:
                await update.message.reply_text("⚠️ This command can only be used in groups")
                return

            group_id = update.message.chat.id

            if not await self._check_admin(update, context, group_id):
                return

            # Get group info
            chat = await context.bot.get_chat(group_id)
            admins = await context.bot.get_chat_administrators(group_id)

            msg = f"⚙️ **Group Settings for {chat.title}**\n\n"
            msg += f"Group ID: `{group_id}`\n"
            msg += f"Type: {chat.type.capitalize()}\n"
            msg += f"Members: {chat.get_members_count() if hasattr(chat, 'get_members_count') else 'Unknown'}\n\n"
            
            msg += f"👥 **Admins ({len(admins)}):**\n"
            for admin in admins[:10]:  # Show first 10 admins
                name = admin.user.first_name or "Unknown"
                msg += f"  • {name}"
                if admin.user.username:
                    msg += f" (@{admin.user.username})"
                msg += f" - ID: {admin.user.id}\n"
            
            if len(admins) > 10:
                msg += f"  ... and {len(admins) - 10} more\n"

            msg += f"\n📋 For detailed settings, use /stats or /logs"

            await update.message.reply_text(msg, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Error in settings command: {e}", exc_info=True)
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def promote_command(self, update: Update, context: CallbackContext):
        """Promote user to admin: /promote <user_id|@username> [title]"""
        try:
            if not update.message.chat.type in ["group", "supergroup"]:
                await update.message.reply_text("⚠️ This command can only be used in groups")
                return

            group_id = update.message.chat.id

            # Only owner can promote
            chat_member = await context.bot.get_chat_member(group_id, update.message.from_user.id)
            if chat_member.status != "creator":
                await update.message.reply_text("⚠️ Only group owner can use /promote")
                return

            target_user_id, target_username = await self._parse_target(update, context)
            if not target_user_id:
                await update.message.reply_text("Usage: /promote <user_id|@username> [custom_title] or reply to a user's message with /promote")
                return

            # Get title if provided
            title = None
            if update.message.reply_to_message:
                if context.args and len(context.args) > 0:
                    title = " ".join(context.args)
            else:
                if context.args and len(context.args) > 1:
                    title = " ".join(context.args[1:])

            # Promote on Telegram
            try:
                await context.bot.promote_chat_member(
                    group_id,
                    target_user_id,
                    can_delete_messages=True,
                    can_restrict_members=True,
                    can_promote_members=False,
                    can_change_info=False,
                    can_post_messages=True,
                    can_edit_messages=True,
                    can_pin_messages=True,
                    can_manage_voice_chats=False,
                    can_manage_video_chats=False,
                    can_manage_topics=False
                )
                
                # Set custom title if provided
                if title and len(title) <= 16:
                    try:
                        await context.bot.set_chat_administrator_custom_title(group_id, target_user_id, title)
                    except Exception as e:
                        logger.warning(f"Could not set custom title: {e}")

                user = update.message.from_user
                await self.db.log_action(
                    group_id=group_id,
                    action_type=ActionType.WARN,  # Use WARN as closest action type
                    admin_id=user.id,
                    admin_username=user.username or user.first_name,
                    target_user_id=target_user_id,
                    target_username=target_username,
                    reason=f"Promoted to admin" + (f" with title: {title}" if title else "")
                )

                target_disp = target_username or target_user_id
                msg = f"👑 User {target_disp} has been promoted to admin"
                if title:
                    msg += f" with title: {title}"
                await update.message.reply_text(msg)

            except Exception as e:
                logger.error(f"❌ Promote failed: {e}")
                await update.message.reply_text(f"❌ Failed to promote user: {str(e)}")

        except Exception as e:
            logger.error(f"Error in promote command: {e}", exc_info=True)
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def demote_command(self, update: Update, context: CallbackContext):
        """Demote admin back to user: /demote <user_id|@username>"""
        try:
            if not update.message.chat.type in ["group", "supergroup"]:
                await update.message.reply_text("⚠️ This command can only be used in groups")
                return

            group_id = update.message.chat.id

            # Only owner can demote
            chat_member = await context.bot.get_chat_member(group_id, update.message.from_user.id)
            if chat_member.status != "creator":
                await update.message.reply_text("⚠️ Only group owner can use /demote")
                return

            target_user_id, target_username = await self._parse_target(update, context)
            if not target_user_id:
                await update.message.reply_text("Usage: /demote <user_id|@username> or reply to a user's message with /demote")
                return

            # Demote on Telegram
            try:
                await context.bot.promote_chat_member(
                    group_id,
                    target_user_id,
                    can_delete_messages=False,
                    can_restrict_members=False,
                    can_promote_members=False,
                    can_change_info=False,
                    can_post_messages=False,
                    can_edit_messages=False,
                    can_pin_messages=False,
                    can_manage_voice_chats=False,
                    can_manage_video_chats=False,
                    can_manage_topics=False
                )

                user = update.message.from_user
                await self.db.log_action(
                    group_id=group_id,
                    action_type=ActionType.WARN,
                    admin_id=user.id,
                    admin_username=user.username or user.first_name,
                    target_user_id=target_user_id,
                    target_username=target_username,
                    reason="Demoted from admin"
                )

                target_disp = target_username or target_user_id
                await update.message.reply_text(f"👤 User {target_disp} has been demoted to regular user")

            except Exception as e:
                logger.error(f"❌ Demote failed: {e}")
                await update.message.reply_text(f"❌ Failed to demote user: {str(e)}")

        except Exception as e:
            logger.error(f"Error in demote command: {e}", exc_info=True)
            await update.message.reply_text(f"❌ Error: {str(e)}")


def register_handlers(application, db_service: DatabaseService, telegram_api: TelegramAPIService = None):
    """Register all command handlers.
    
    Args:
        application: Telegram application instance
        db_service: Database service for logging and persistence
        telegram_api: Optional Telegram API service for executing actions
    """
    logger.info("🔴 REGISTER_HANDLERS CALLED!")  # DEBUG
    # If db_service is not provided (e.g., debug runner), use a dummy in-memory
    # implementation so handlers that call `self.db.*` won't crash.
    if db_service is None:
        logger.info("⚙️ No db_service provided — using _DummyDB for debug")
        db_service = _DummyDB()

    # Get telegram_api service from application.bot if not provided
    if telegram_api is None and hasattr(application, 'bot'):
        try:
            telegram_api = TelegramAPIService(application.bot)
            logger.info("✅ Created TelegramAPIService from application.bot")
        except Exception as e:
            logger.warning(f"⚠️ Could not create TelegramAPIService: {e}")
            telegram_api = None
    
    handlers = BotCommandHandlers(db_service, telegram_api)
    logger.info(f"✅ Created BotCommandHandlers instance with Telegram API service")
    
    # Register commands (group=0 runs first, before catch-all message handlers)
    logger.info("📝 Registering /ban handler...")
    application.add_handler(CommandHandler("ban", handlers.ban_command), group=0)
    logger.info("✅ /ban registered")
    
    logger.info("📝 Registering /unban handler...")
    application.add_handler(CommandHandler("unban", handlers.unban_command), group=0)
    logger.info("✅ /unban registered")
    
    logger.info("📝 Registering /kick handler...")
    application.add_handler(CommandHandler("kick", handlers.kick_command), group=0)
    logger.info("✅ /kick registered")
    
    logger.info("📝 Registering /warn handler...")
    application.add_handler(CommandHandler("warn", handlers.warn_command), group=0)
    logger.info("✅ /warn registered")
    
    logger.info("📝 Registering /mute handler...")
    application.add_handler(CommandHandler("mute", handlers.mute_command), group=0)
    logger.info("✅ /mute registered")
    
    logger.info("📝 Registering /unmute handler...")
    application.add_handler(CommandHandler("unmute", handlers.unmute_command), group=0)
    logger.info("✅ /unmute registered")
    
    logger.info("📝 Registering /restrict handler...")
    application.add_handler(CommandHandler("restrict", handlers.restrict_command), group=0)
    logger.info("✅ /restrict registered")
    
    logger.info("📝 Registering /logs handler...")
    application.add_handler(CommandHandler("logs", handlers.logs_command), group=0)
    logger.info("✅ /logs registered")
    
    logger.info("📝 Registering /stats handler...")
    application.add_handler(CommandHandler("stats", handlers.stats_command), group=0)
    logger.info("✅ /stats registered")
    
    logger.info("📝 Registering /free handler...")
    application.add_handler(CommandHandler("free", handlers.free_command), group=0)
    logger.info("✅ /free registered")
    
    logger.info("📝 Registering /id handler...")
    application.add_handler(CommandHandler("id", handlers.id_command), group=0)
    logger.info("✅ /id registered")
    
    logger.info("📝 Registering /settings handler...")
    application.add_handler(CommandHandler("settings", handlers.settings_command), group=0)
    logger.info("✅ /settings registered")
    
    logger.info("📝 Registering /promote handler...")
    application.add_handler(CommandHandler("promote", handlers.promote_command), group=0)
    logger.info("✅ /promote registered")
    
    logger.info("📝 Registering /demote handler...")
    application.add_handler(CommandHandler("demote", handlers.demote_command), group=0)
    logger.info("✅ /demote registered")
    
    logger.info("=" * 60)
    logger.info("✅✅✅ ALL COMMAND HANDLERS REGISTERED SUCCESSFULLY! ✅✅✅")
    logger.info("=" * 60)

    # --- Debug: Catch-all message handler to verify messages are reaching handlers ---
    async def _debug_all_messages(update: Update, context: CallbackContext):
        """Debug handler to log ALL messages"""
        if update.message:
            logger.info(f"🔍 DEBUG: Message received: '{update.message.text}' from {update.message.from_user.username} in {update.message.chat.title}")
        return  # Don't consume the message

    try:
        # Register with very high group (after all others) so it doesn't interfere
        application.add_handler(MessageHandler(filters.ALL, _debug_all_messages), group=99)
        logger.info("📝 Debug message handler registered (group=99)")
    except Exception:
        logger.exception("Failed to register debug message handler")

    # --- Temporary health-check handlers ---
    # Lightweight /ping and /state commands to verify the bot is responding
    async def _ping(update: Update, context: CallbackContext):
        try:
            logger.info(f"✅ /ping command handler called")
            logger.info(f"✅ /ping received from {update.message.from_user.username}")
            await update.message.reply_text("🤖 Pong!")
            logger.info(f"✅ /ping response sent successfully")
        except Exception as e:
            logger.exception(f"❌ Failed to send ping reply: {e}")

    async def _state(update: Update, context: CallbackContext):
        try:
            logger.info(f"✅ /state command handler called")
            logger.info(f"✅ /state received from {update.message.from_user.username}")
            state_msg = (
                f"🤖 Guardian Bot Status\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"✅ Bot is running\n"
                f"✅ Polling active\n"
                f"✅ Handlers registered\n"
                f"Group: {update.message.chat.title}"
            )
            await update.message.reply_text(state_msg)
            logger.info(f"✅ /state response sent successfully")
        except Exception as e:
            logger.exception(f"❌ Failed to send state reply: {e}")

    try:
        application.add_handler(CommandHandler("ping", _ping), group=0)
        logger.info("📝 /ping (test) handler registered")
    except Exception:
        logger.exception("Failed to register /ping test handler")

    try:
        application.add_handler(CommandHandler("state", _state), group=0)
        logger.info("📝 /state (test) handler registered")
    except Exception:
        logger.exception("Failed to register /state test handler")

    # Register lightweight message tracker to keep member info up to date (group=1, after commands)
    try:
        application.add_handler(MessageHandler(filters.ALL, handlers.track_message), group=1)
        logger.info("📝 Message tracking handler registered")
    except Exception:
        logger.exception("Failed to register message tracking handler")

    # Register chat member update handler to track joins/leaves/admin changes (group=1, after commands)
    try:
        application.add_handler(ChatMemberHandler(handlers.chat_member_update, ChatMemberHandler.CHAT_MEMBER), group=1)
        logger.info("📝 Chat member update handler registered")
    except Exception:
        logger.exception("Failed to register chat member update handler")

    # Background admin sync: schedule via the bot JobQueue (safer - started with app)
    try:
        async def _admin_sync_job(context: ContextTypes.DEFAULT_TYPE):
            try:
                # Use the handlers.db instance (may be _DummyDB or a real DatabaseService).
                dbs = handlers.db
                # If we're still using the dummy DB, skip syncing
                if isinstance(dbs, _DummyDB):
                    logger.info("Admin sync skipped: using _DummyDB")
                    return

                # dbs is a real DatabaseService with `db` attribute (motor DB)
                groups = await dbs.db["groups"].find({"active": True}).to_list(None)
                for g in groups:
                    gid = g.get("group_id")
                    try:
                        admins = await application.bot.get_chat_administrators(gid)
                        await dbs.sync_group_admins(gid, admins)
                    except Exception:
                        logger.exception(f"Failed to sync admins for group {gid}")
            except Exception:
                logger.exception("Error in admin sync job")

        # Use job_queue to run every 10 minutes; job_queue will be started by Application
        try:
            application.job_queue.run_repeating(_admin_sync_job, interval=60 * 10, first=30, data={"db_service": db_service})
            logger.info("🟢 Admin sync job scheduled via JobQueue (every 10 minutes)")
        except Exception:
            logger.exception("Failed to schedule admin sync job via job_queue")
    except Exception:
        logger.exception("Failed to prepare admin sync job")

    # --- Deferred DB initialization ---
    # Schedule a one-time job (runs after the Application's event loop is running)
    # to create a real AsyncIOMotorClient/DatabaseService and swap it into
    # the handlers instance so DB-backed handlers work without event-loop issues.
    async def _init_db_once(ctx: ContextTypes.DEFAULT_TYPE):
        try:
            # If db was already provided at register time, skip
            if not isinstance(handlers.db, _DummyDB):
                logger.info("DB service already provided; skipping deferred init")
                return

            logger.info("🔁 Deferred DB init: creating AsyncIOMotorClient and DatabaseService")
            try:
                from motor.motor_asyncio import AsyncIOMotorClient
                from ..services.database import DatabaseService as _DBClass
            except Exception as e:
                logger.exception("Failed to import motor or DatabaseService: %s", e)
                return

            try:
                client = AsyncIOMotorClient(config.MONGODB_URI)
                db = client[config.MONGODB_DB_NAME]
                real_db = _DBClass(db)
                healthy = await real_db.health_check()
                if not healthy:
                    logger.warning("Deferred DB init: health_check failed, continuing with _DummyDB")
                    return

                # Swap DB instance into handlers so future calls use the real DB
                handlers.db = real_db
                logger.info("✅ Deferred DB initialized and attached to handlers")
            except Exception as e:
                logger.exception("Deferred DB initialization failed: %s", e)
        except Exception:
            logger.exception("Unhandled error during deferred DB init")

    try:
        # Run once shortly after startup (first=5 seconds)
        application.job_queue.run_once(_init_db_once, when=5)
        logger.info("🟡 Scheduled one-time deferred DB initialization job")
    except Exception:
        logger.exception("Failed to schedule deferred DB init job")

