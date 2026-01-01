"""
Telegram Bot API Service for Moderation Actions
Executes actual Telegram API calls for ban, mute, kick, etc.

Requires:
- telegram bot.Client instance (from python-telegram-bot)
- Valid bot token with appropriate permissions
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from telegram import ChatPermissions
from telegram.error import TelegramError
import inspect

logger = logging.getLogger(__name__)


class TelegramAPIService:
    """Service for executing moderation actions via Telegram Bot API."""
    
    def __init__(self, bot):
        """Initialize with telegram Bot instance.
        
        Args:
            bot: The telegram.Bot instance
        """
        self.bot = bot
    
    async def ban_user(
        self,
        group_id: int,
        user_id: int,
        reason: Optional[str] = None,
        revoke_messages: bool = True,
    ) -> Tuple[bool, Optional[str]]:
        """Ban user from group.
        
        Args:
            group_id: Telegram group ID
            user_id: Telegram user ID to ban
            reason: Optional reason for logging
            revoke_messages: Whether to delete user messages (default True)
        
        Returns:
            Tuple[success: bool, error_message: Optional[str]]
        """
        try:
            logger.info(f"🚫 Banning user {user_id} from group {group_id}")
            
            await self.bot.ban_chat_member(
                chat_id=group_id,
                user_id=user_id,
                revoke_messages=revoke_messages,
            )
            
            logger.info(f"✅ User {user_id} banned from group {group_id}")
            return True, None
            
        except TelegramError as e:
            error_msg = f"Telegram API error: {str(e)}"
            logger.error(f"❌ Failed to ban user {user_id}: {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"❌ Unexpected error banning user {user_id}: {error_msg}")
            return False, error_msg
    
    async def unban_user(
        self,
        group_id: int,
        user_id: int,
    ) -> Tuple[bool, Optional[str]]:
        """Unban user from group.
        
        Args:
            group_id: Telegram group ID
            user_id: Telegram user ID to unban
        
        Returns:
            Tuple[success: bool, error_message: Optional[str]]
        """
        try:
            logger.info(f"🔓 Unbanning user {user_id} from group {group_id}")
            
            await self.bot.unban_chat_member(
                chat_id=group_id,
                user_id=user_id,
                only_if_banned=True,
            )
            
            logger.info(f"✅ User {user_id} unbanned from group {group_id}")
            return True, None
            
        except TelegramError as e:
            error_msg = f"Telegram API error: {str(e)}"
            logger.error(f"❌ Failed to unban user {user_id}: {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"❌ Unexpected error unbanning user {user_id}: {error_msg}")
            return False, error_msg
    
    async def kick_user(
        self,
        group_id: int,
        user_id: int,
        reason: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """Kick user from group (user can rejoin).
        
        Kicks by temporarily banning then immediately unbanning.
        
        Args:
            group_id: Telegram group ID
            user_id: Telegram user ID to kick
            reason: Optional reason for logging
        
        Returns:
            Tuple[success: bool, error_message: Optional[str]]
        """
        try:
            logger.info(f"👢 Kicking user {user_id} from group {group_id}")
            
            # Ban user
            await self.bot.ban_chat_member(chat_id=group_id, user_id=user_id)
            
            # Immediately unban to allow rejoin
            await self.bot.unban_chat_member(chat_id=group_id, user_id=user_id)
            
            logger.info(f"✅ User {user_id} kicked from group {group_id}")
            return True, None
            
        except TelegramError as e:
            error_msg = f"Telegram API error: {str(e)}"
            logger.error(f"❌ Failed to kick user {user_id}: {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"❌ Unexpected error kicking user {user_id}: {error_msg}")
            return False, error_msg
    
    async def mute_user(
        self,
        group_id: int,
        user_id: int,
        duration_hours: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """Mute user in group (restrict to read-only).
        
        Args:
            group_id: Telegram group ID
            user_id: Telegram user ID to mute
            duration_hours: Duration in hours (None = permanent until unmute)
            reason: Optional reason for logging
        
        Returns:
            Tuple[success: bool, error_message: Optional[str]]
        """
        try:
            logger.info(
                f"🔇 Muting user {user_id} in group {group_id}"
                f"{f' for {duration_hours}h' if duration_hours else ' (permanent)'}"
            )
            
            # Create restricted permissions (can read but not write)
            permissions = self._build_read_only_permissions()
            
            # Calculate until_date if duration specified
            until_date = None
            if duration_hours:
                until_date = datetime.now(timezone.utc) + timedelta(hours=duration_hours)
            
            await self.bot.restrict_chat_member(
                chat_id=group_id,
                user_id=user_id,
                permissions=permissions,
                until_date=until_date,
            )
            
            logger.info(f"✅ User {user_id} muted in group {group_id}")
            return True, None
            
        except TelegramError as e:
            error_msg = f"Telegram API error: {str(e)}"
            logger.error(f"❌ Failed to mute user {user_id}: {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"❌ Unexpected error muting user {user_id}: {error_msg}")
            return False, error_msg
    
    async def unmute_user(
        self,
        group_id: int,
        user_id: int,
        reason: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """Unmute user in group (restore full permissions).
        
        Args:
            group_id: Telegram group ID
            user_id: Telegram user ID to unmute
            reason: Optional reason for logging
        
        Returns:
            Tuple[success: bool, error_message: Optional[str]]
        """
        try:
            logger.info(f"🔊 Unmuting user {user_id} in group {group_id}")
            
            # Restore full permissions - build dynamically to support all Telegram Bot API versions
            permissions = self._build_full_permissions()
            
            await self.bot.restrict_chat_member(
                chat_id=group_id,
                user_id=user_id,
                permissions=permissions,
            )
            
            logger.info(f"✅ User {user_id} unmuted in group {group_id}")
            return True, None
            
        except TelegramError as e:
            error_msg = f"Telegram API error: {str(e)}"
            logger.error(f"❌ Failed to unmute user {user_id}: {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"❌ Unexpected error unmuting user {user_id}: {error_msg}")
            return False, error_msg
    
    async def warn_user(
        self,
        group_id: int,
        user_id: int,
        reason: Optional[str] = None,
        admin_name: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """Send warning message to user (non-restrictive action).
        
        Args:
            group_id: Telegram group ID
            user_id: Telegram user ID to warn
            reason: Warning reason
            admin_name: Name of admin giving warning
        
        Returns:
            Tuple[success: bool, error_message: Optional[str]]
        """
        try:
            logger.info(f"⚠️ Sending warning to user {user_id} in group {group_id}")
            
            # Send warning message mentioning the user
            warning_msg = f"⚠️ **Warning** to user {user_id}"
            if admin_name:
                warning_msg += f" from {admin_name}"
            if reason:
                warning_msg += f": {reason}"
            
            # Try to send message to group mentioning the warning
            await self.bot.send_message(
                chat_id=group_id,
                text=warning_msg,
                parse_mode="Markdown",
            )
            
            logger.info(f"✅ Warning sent to user {user_id}")
            return True, None
            
        except TelegramError as e:
            error_msg = f"Telegram API error: {str(e)}"
            logger.warning(f"⚠️ Failed to send warning: {error_msg}")
            # Warning sending is non-critical, return success anyway
            return True, None
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.warning(f"⚠️ Unexpected error sending warning: {error_msg}")
            return True, None
    
    def _build_read_only_permissions(self) -> ChatPermissions:
        """Build ChatPermissions for read-only (muted) user.
        
        Returns:
            ChatPermissions: Object with only reading permissions enabled
        """
        try:
            # Try to get valid signature from ChatPermissions
            sig = inspect.signature(ChatPermissions.__init__)
            valid = [p for p in sig.parameters.keys() if p not in ("self", "args", "kwargs")]
            
            # Build read-only permissions
            perms = {
                "can_send_messages": False,
                "can_send_media_messages": False,
                "can_send_polls": False,
                "can_send_other_messages": False,
                "can_add_web_page_previews": False,
                "can_change_info": False,
                "can_invite_users": False,
                "can_pin_messages": False,
                "can_manage_topics": False,
            }
            
            # Filter to only valid parameters
            usable = {k: v for k, v in perms.items() if k in valid}
            return ChatPermissions(**usable)
            
        except Exception as e:
            logger.warning(f"Could not build ChatPermissions: {e}")
            # Fallback: empty permissions (safest default)
            try:
                return ChatPermissions(can_send_messages=False)
            except Exception:
                return ChatPermissions()
    
    def _build_full_permissions(self) -> ChatPermissions:
        """Build ChatPermissions for fully unrestricted user.
        
        Dynamically determines valid parameters based on current Telegram Bot API version.
        
        Returns:
            ChatPermissions: Object with all sending permissions enabled
        """
        try:
            # Try to get valid signature from ChatPermissions
            sig = inspect.signature(ChatPermissions.__init__)
            valid = [p for p in sig.parameters.keys() if p not in ("self", "args", "kwargs")]
            
            # Build full permissions (try all possible parameters)
            perms = {
                "can_send_messages": True,
                "can_send_media_messages": True,  # Old versions
                "can_send_audio": True,            # New versions
                "can_send_document": True,         # New versions
                "can_send_photo": True,            # New versions
                "can_send_video": True,            # New versions
                "can_send_video_note": True,       # New versions
                "can_send_polls": True,
                "can_send_other_messages": True,
                "can_add_web_page_previews": True,
                "can_change_info": False,
                "can_invite_users": False,
                "can_pin_messages": False,
                "can_manage_topics": False,
            }
            
            # Filter to only valid parameters for this version
            usable = {k: v for k, v in perms.items() if k in valid}
            return ChatPermissions(**usable)
            
        except Exception as e:
            logger.warning(f"Could not build full ChatPermissions: {e}")
            # Fallback: just enable basic send_messages
            try:
                return ChatPermissions(can_send_messages=True)
            except Exception:
                return ChatPermissions()
    
    def _build_locked_permissions(self) -> ChatPermissions:
        """Build ChatPermissions for completely locked-down (restricted) user.
        
        Only allows reading messages. Blocks:
        - All media (photos, videos, documents, audio, voice notes)
        - Stickers, GIFs, animations
        - Polls
        - Web page previews
        - Any other message types
        
        Dynamically handles both old and new Telegram Bot API versions.
        
        Returns:
            ChatPermissions: Object with minimal permissions (read-only)
        """
        try:
            # Get valid parameters from ChatPermissions signature
            sig = inspect.signature(ChatPermissions.__init__)
            valid_params = [p for p in sig.parameters.keys() if p not in ("self", "args", "kwargs")]
            
            logger.debug(f"Valid ChatPermissions parameters for locked: {valid_params}")
            
            # Build completely locked permissions - ONLY can read messages
            locked_perms = {
                "can_send_messages": False,
                "can_send_media_messages": False,  # Old API - blocks all media
                "can_send_audio": False,           # New API
                "can_send_document": False,        # New API
                "can_send_photo": False,           # New API
                "can_send_video": False,           # New API
                "can_send_video_note": False,      # New API
                "can_send_voice_note": False,      # New API
                "can_send_animation": False,       # GIFs/Animations
                "can_send_polls": False,
                "can_send_other_messages": False,  # Blocks stickers, etc.
                "can_add_web_page_previews": False,
                "can_change_info": False,
                "can_invite_users": False,
                "can_pin_messages": False,
                "can_manage_topics": False,
            }
            
            # Filter to only valid parameters for this API version
            usable_perms = {k: v for k, v in locked_perms.items() if k in valid_params}
            
            logger.debug(f"Using locked permissions: {list(usable_perms.keys())}")
            
            return ChatPermissions(**usable_perms)
            
        except Exception as e:
            logger.warning(f"Could not build locked ChatPermissions: {e}")
            # Fallback: try with basic locked parameters
            try:
                return ChatPermissions(
                    can_send_messages=False,
                    can_send_media_messages=False,
                    can_send_polls=False,
                    can_send_other_messages=False,
                    can_add_web_page_previews=False,
                )
            except Exception as fallback_e:
                logger.warning(f"Fallback locked failed: {fallback_e}")
                # Last resort: restrict all by passing empty
                return ChatPermissions()
    
    async def lock_user(
        self,
        group_id: int,
        user_id: int,
        duration_hours: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """Completely lock down user - can only read, cannot send anything.
        
        Blocks all media (photos, videos, documents, audio, voice notes),
        stickers, GIFs, polls, and web page previews.
        
        Args:
            group_id: Telegram group ID
            user_id: Telegram user ID to lock
            duration_hours: Duration in hours (None = permanent until unlock)
            reason: Optional reason for logging
        
        Returns:
            Tuple[success: bool, error_message: Optional[str]]
        """
        try:
            logger.info(
                f"🔐 LOCKING DOWN user {user_id} in group {group_id}"
                f"{f' for {duration_hours}h' if duration_hours else ' (permanent)'}"
            )
            
            # Get completely restricted permissions
            permissions = self._build_locked_permissions()
            
            # Calculate until_date if duration specified
            until_date = None
            if duration_hours:
                until_date = datetime.now(timezone.utc) + timedelta(hours=duration_hours)
            
            await self.bot.restrict_chat_member(
                chat_id=group_id,
                user_id=user_id,
                permissions=permissions,
                until_date=until_date,
            )
            
            logger.info(f"✅ User {user_id} LOCKED DOWN in group {group_id}")
            return True, None
            
        except TelegramError as e:
            error_msg = f"Telegram API error: {str(e)}"
            logger.error(f"❌ Failed to lock user {user_id}: {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"❌ Unexpected error locking user {user_id}: {error_msg}")
            return False, error_msg
    
    async def unlock_user(
        self,
        group_id: int,
        user_id: int,
        reason: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """Unlock user - restore full permissions.
        
        Args:
            group_id: Telegram group ID
            user_id: Telegram user ID to unlock
            reason: Optional reason for logging
        
        Returns:
            Tuple[success: bool, error_message: Optional[str]]
        """
        try:
            logger.info(f"🔓 UNLOCKING user {user_id} in group {group_id}")
            
            # Restore full permissions
            permissions = self._build_full_permissions()
            
            await self.bot.restrict_chat_member(
                chat_id=group_id,
                user_id=user_id,
                permissions=permissions,
            )
            
            logger.info(f"✅ User {user_id} UNLOCKED in group {group_id}")
            return True, None
            
        except TelegramError as e:
            error_msg = f"Telegram API error: {str(e)}"
            logger.error(f"❌ Failed to unlock user {user_id}: {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"❌ Unexpected error unlocking user {user_id}: {error_msg}")
            return False, error_msg
    
    def _build_custom_permissions(self, blocked_types: list = None) -> ChatPermissions:
        """Build ChatPermissions with selective blocks.
        
        Allows admins to block specific permission types while keeping others enabled.
        
        Args:
            blocked_types: List of permission types to block. Options:
                - "media": Block all media (photos, videos, documents, audio, voice)
                - "stickers": Block stickers
                - "gifs": Block GIFs/animations
                - "polls": Block polls
                - "links": Block web page previews
                - "all_messages": Block all messages
        
        Returns:
            ChatPermissions: Object with custom permissions
        """
        if blocked_types is None:
            blocked_types = []
        
        try:
            # Get valid parameters from ChatPermissions signature
            sig = inspect.signature(ChatPermissions.__init__)
            valid_params = [p for p in sig.parameters.keys() if p not in ("self", "args", "kwargs")]
            
            logger.debug(f"Building custom permissions, blocking: {blocked_types}")
            
            # Start with all permissions enabled
            perms = {
                "can_send_messages": True,
                "can_send_media_messages": True,
                "can_send_audio": True,
                "can_send_document": True,
                "can_send_photo": True,
                "can_send_video": True,
                "can_send_video_note": True,
                "can_send_voice_note": True,
                "can_send_animation": True,
                "can_send_polls": True,
                "can_send_other_messages": True,
                "can_add_web_page_previews": True,
                "can_change_info": False,
                "can_invite_users": False,
                "can_pin_messages": False,
                "can_manage_topics": False,
            }
            
            # Apply blocks based on blocked_types
            for block_type in blocked_types:
                block_type = block_type.lower().strip()
                
                if block_type == "media":
                    # Block all media
                    perms["can_send_media_messages"] = False
                    perms["can_send_audio"] = False
                    perms["can_send_document"] = False
                    perms["can_send_photo"] = False
                    perms["can_send_video"] = False
                    perms["can_send_video_note"] = False
                    perms["can_send_voice_note"] = False
                    logger.debug("Blocking: All media")
                
                elif block_type == "stickers":
                    # Block stickers (part of can_send_other_messages)
                    perms["can_send_other_messages"] = False
                    logger.debug("Blocking: Stickers")
                
                elif block_type == "gifs" or block_type == "animations":
                    # Block GIFs/animations
                    perms["can_send_animation"] = False
                    logger.debug("Blocking: GIFs/Animations")
                
                elif block_type == "polls":
                    # Block polls
                    perms["can_send_polls"] = False
                    logger.debug("Blocking: Polls")
                
                elif block_type == "links":
                    # Block web page previews
                    perms["can_add_web_page_previews"] = False
                    logger.debug("Blocking: Web page previews")
                
                elif block_type == "all_messages":
                    # Block all messages
                    perms["can_send_messages"] = False
                    logger.debug("Blocking: All messages")
                
                elif block_type == "voice":
                    # Block voice messages
                    perms["can_send_voice_note"] = False
                    logger.debug("Blocking: Voice messages")
                
                elif block_type == "video":
                    # Block videos
                    perms["can_send_video"] = False
                    logger.debug("Blocking: Videos")
                
                elif block_type == "audio":
                    # Block audio
                    perms["can_send_audio"] = False
                    logger.debug("Blocking: Audio")
                
                elif block_type == "documents":
                    # Block documents
                    perms["can_send_document"] = False
                    logger.debug("Blocking: Documents")
                
                elif block_type == "photos":
                    # Block photos
                    perms["can_send_photo"] = False
                    logger.debug("Blocking: Photos")
            
            # Filter to only valid parameters for this API version
            usable_perms = {k: v for k, v in perms.items() if k in valid_params}
            
            logger.debug(f"Final custom permissions: {usable_perms}")
            
            return ChatPermissions(**usable_perms)
            
        except Exception as e:
            logger.warning(f"Could not build custom ChatPermissions: {e}")
            # Fallback: allow everything
            try:
                return ChatPermissions(
                    can_send_messages=True,
                    can_send_polls=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True,
                )
            except Exception:
                return ChatPermissions()
    
    async def restrict_user_permissions(
        self,
        group_id: int,
        user_id: int,
        blocked_types: list = None,
        duration_hours: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """Restrict specific permissions for a user.
        
        Admins can selectively block specific content types while allowing others.
        
        Args:
            group_id: Telegram group ID
            user_id: Telegram user ID to restrict
            blocked_types: List of types to block:
                - "media": All media (photos, videos, documents, audio, voice)
                - "stickers": Stickers
                - "gifs": GIFs/animations
                - "polls": Polls
                - "links": Web page previews
                - "voice": Voice messages
                - "video": Videos
                - "audio": Audio files
                - "documents": Documents
                - "photos": Photos
                - "all_messages": All messages
            duration_hours: Duration in hours (None = permanent)
            reason: Optional reason for logging
        
        Returns:
            Tuple[success: bool, error_message: Optional[str]]
        """
        if blocked_types is None:
            blocked_types = []
        
        try:
            blocked_str = ", ".join(blocked_types) if blocked_types else "none"
            logger.info(
                f"🚫 RESTRICTING user {user_id} in group {group_id}"
                f" - Blocked: {blocked_str}"
                f"{f' for {duration_hours}h' if duration_hours else ' (permanent)'}"
            )
            
            # Get custom permissions with selective blocks
            permissions = self._build_custom_permissions(blocked_types)
            
            # Calculate until_date if duration specified
            until_date = None
            if duration_hours:
                until_date = datetime.now(timezone.utc) + timedelta(hours=duration_hours)
            
            await self.bot.restrict_chat_member(
                chat_id=group_id,
                user_id=user_id,
                permissions=permissions,
                until_date=until_date,
            )
            
            logger.info(f"✅ User {user_id} RESTRICTED - Blocked: {blocked_str}")
            return True, None
            
        except TelegramError as e:
            error_msg = f"Telegram API error: {str(e)}"
            logger.error(f"❌ Failed to restrict user {user_id}: {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"❌ Unexpected error restricting user {user_id}: {error_msg}")
            return False, error_msg
    
    async def get_chat_member(
        self,
        group_id: int,
        user_id: int,
    ) -> Optional[dict]:
        """Get chat member info.
        
        Args:
            group_id: Telegram group ID
            user_id: Telegram user ID
        
        Returns:
            Optional[dict]: Member info or None if not found
        """
        try:
            member = await self.bot.get_chat_member(chat_id=group_id, user_id=user_id)
            return {
                "user_id": member.user.id,
                "username": getattr(member.user, "username", None),
                "first_name": getattr(member.user, "first_name", None),
                "status": member.status,
                "is_member": member.status in ("member", "administrator", "creator", "restricted"),
            }
        except TelegramError as e:
            logger.debug(f"Could not get chat member {user_id} from group {group_id}: {e}")
            return None
        except Exception as e:
            logger.debug(f"Unexpected error getting chat member: {e}")
            return None
    
    async def get_chat_administrators(self, group_id: int) -> list:
        """Get list of group administrators.
        
        Args:
            group_id: Telegram group ID
        
        Returns:
            list: List of admin user IDs
        """
        try:
            admins = await self.bot.get_chat_administrators(chat_id=group_id)
            return [admin.user.id for admin in admins]
        except TelegramError as e:
            logger.error(f"Could not get admin list for group {group_id}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting administrators: {e}")
            return []


def get_telegram_api_service(app) -> Optional[TelegramAPIService]:
    """Extract TelegramAPIService from FastAPI app instance.
    
    Args:
        app: FastAPI application instance
    
    Returns:
        TelegramAPIService or None if not available
    """
    try:
        # Check if telegram_app is attached to app.state
        if hasattr(app, "state") and hasattr(app.state, "telegram_app"):
            telegram_app = app.state.telegram_app
            if telegram_app is not None:
                # Get the bot instance from the telegram application
                if hasattr(telegram_app, "bot"):
                    return TelegramAPIService(telegram_app.bot)
        
        logger.debug("Telegram API service not available (telegram_app.bot not found)")
        return None
        
    except Exception as e:
        logger.debug(f"Could not get Telegram API service: {e}")
        return None
