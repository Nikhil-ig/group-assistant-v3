"""
Bidirectional Integration Service v3

Clean, modular, easy to understand.
Core orchestrator for all moderation actions.
"""

import logging
import time
from typing import Any, Dict, Optional

from core.models import (
    ActionPayload,
    ActionResult,
    ActionSource,
    ActionType,
    NotificationMode,
)
from config.settings import config

logger = logging.getLogger(__name__)


class BidirectionalService:
    """
    Main service for handling all moderation actions.
    
    Handles:
    - Telegram API calls
    - Database storage
    - Notification routing
    - Real-time sync
    - Metrics tracking
    """
    
    def __init__(self, bot: Any = None, db: Any = None, redis: Any = None):
        """
        Initialize the service.
        
        Args:
            bot: Telegram bot application instance
            db: MongoDB database connection (motor)
            redis: Redis client connection
        """
        self.bot = bot
        self.db = db
        self.redis = redis
        self.metrics = {
            'total_actions': 0,
            'bot_actions': 0,
            'web_actions': 0,
            'failed_actions': 0,
            'action_breakdown': {},
        }
    
    async def execute_action(self, payload: ActionPayload) -> ActionResult:
        """
        Execute a moderation action.
        
        This is the main method - everything flows through here.
        
        Args:
            payload: ActionPayload with all action details
            
        Returns:
            ActionResult with status and metrics
        """
        start_time = time.time()
        action_id = self._generate_action_id()
        
        try:
            logger.info(f"Executing {payload.action.value} on user {payload.user_id}")
            
            # Step 1: Validate
            await self._validate(payload)
            
            # Step 2: Execute on Telegram
            await self._execute_telegram_action(payload, action_id)
            
            # Step 3: Store in database
            await self._store_in_database(payload, action_id)
            
            # Step 4: Send notifications
            await self._send_notifications(payload, action_id)
            
            # Step 5: Sync in real-time
            await self._broadcast_action(payload, action_id)
            
            # Step 6: Update metrics
            execution_time = (time.time() - start_time) * 1000  # Convert to ms
            self._update_metrics(payload, True)
            
            logger.info(f"✅ Action {action_id} completed in {execution_time:.0f}ms")
            
            return ActionResult(
                ok=True,
                source=payload.source,
                action_id=action_id,
                execution_time_ms=execution_time,
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"❌ Action failed: {str(e)}")
            self._update_metrics(payload, False)
            
            return ActionResult(
                ok=False,
                source=payload.source,
                action_id=action_id,
                error=str(e),
                execution_time_ms=execution_time,
            )
    
    async def _validate(self, payload: ActionPayload) -> None:
        """Validate action payload."""
        if not payload.user_id or not isinstance(payload.user_id, int):
            raise ValueError("Invalid user_id")
        if not payload.group_id or not isinstance(payload.group_id, int):
            raise ValueError("Invalid group_id")
        if not isinstance(payload.action, ActionType):
            raise ValueError("Invalid action type")
        logger.debug("✓ Validation passed")
    
    async def _execute_telegram_action(self, payload: ActionPayload, action_id: str) -> None:
        """Execute action on Telegram API."""
        if not self.bot:
            logger.warning("Bot not initialized - skipping Telegram action")
            return
        
        try:
            action = payload.action.value
            
            if action == 'BAN':
                await self.bot.ban_chat_member(
                    chat_id=payload.group_id,
                    user_id=payload.user_id
                )
            elif action == 'UNBAN':
                await self.bot.unban_chat_member(
                    chat_id=payload.group_id,
                    user_id=payload.user_id
                )
            elif action == 'MUTE':
                from telegram import ChatPermissions
                await self.bot.restrict_chat_member(
                    chat_id=payload.group_id,
                    user_id=payload.user_id,
                    permissions=ChatPermissions(can_send_messages=False)
                )
            elif action == 'UNMUTE':
                from telegram import ChatPermissions
                await self.bot.restrict_chat_member(
                    chat_id=payload.group_id,
                    user_id=payload.user_id,
                    permissions=ChatPermissions(
                        can_send_messages=True,
                        can_send_media_messages=True,
                        can_send_other_messages=True,
                        can_add_web_page_previews=True
                    )
                )
            elif action == 'KICK':
                await self.bot.ban_chat_member(
                    chat_id=payload.group_id,
                    user_id=payload.user_id,
                    revoke_messages=False
                )
                # Unban immediately so they can rejoin
                await self.bot.unban_chat_member(
                    chat_id=payload.group_id,
                    user_id=payload.user_id
                )
            elif action == 'WARN':
                # Just log it - no Telegram action
                pass
            
            logger.debug(f"✓ Telegram action executed: {action}")
            
        except Exception as e:
            logger.error(f"Telegram action failed: {str(e)}")
            raise
    
    async def _store_in_database(self, payload: ActionPayload, action_id: str) -> None:
        """Store action in MongoDB."""
        if not self.db:
            logger.warning("Database not initialized - skipping storage")
            return
        
        try:
            document = {
                '_id': action_id,
                **payload.to_dict(),
            }
            
            await self.db[config.MONGODB_AUDIT_COLLECTION].insert_one(document)
            logger.debug(f"✓ Stored in database: {action_id}")
            
        except Exception as e:
            logger.error(f"Database storage failed: {str(e)}")
            raise
    
    async def _send_notifications(self, payload: ActionPayload, action_id: str) -> None:
        """Send notifications based on notification mode."""
        if not self.bot:
            logger.warning("Bot not initialized - skipping notifications")
            return
        
        try:
            mode = payload.notification_mode
            
            # Send group notification
            if mode in [NotificationMode.GROUP_ONLY, NotificationMode.GROUP_AND_USER]:
                await self._send_group_notification(payload, action_id)
            
            # Send user notification
            if mode in [NotificationMode.USER_ONLY, NotificationMode.GROUP_AND_USER]:
                await self._send_user_notification(payload, action_id)
            
            logger.debug(f"✓ Notifications sent: {mode.value}")
            
        except Exception as e:
            logger.error(f"Notification failed: {str(e)}")
            # Don't raise - notifications are non-critical
    
    async def _send_group_notification(self, payload: ActionPayload, action_id: str) -> None:
        """Send notification to group chat."""
        source_badge = f"[via {payload.source.value}]"
        action_emoji = self._get_action_emoji(payload.action)
        
        message = (
            f"{action_emoji} *{payload.action.value}* {source_badge}\n"
            f"User: `{payload.user_id}`\n"
            f"Reason: {payload.reason or 'N/A'}\n"
            f"ID: `{action_id}`"
        )
        
        try:
            await self.bot.send_message(
                chat_id=payload.group_id,
                text=message,
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.warning(f"Failed to send group notification: {str(e)}")
    
    async def _send_user_notification(self, payload: ActionPayload, action_id: str) -> None:
        """Send notification to affected user."""
        message = (
            f"⚠️ You have been {payload.action.value.lower()}ed\n\n"
            f"Reason: {payload.reason or 'No reason provided'}\n"
            f"Group: {payload.group_id}\n"
            f"Action ID: {action_id}"
        )
        
        try:
            await self.bot.send_message(
                chat_id=payload.user_id,
                text=message
            )
        except Exception as e:
            logger.warning(f"Failed to send user notification: {str(e)}")
    
    async def _broadcast_action(self, payload: ActionPayload, action_id: str) -> None:
        """Broadcast action via Redis for real-time sync."""
        if not self.redis or not config.ENABLE_REAL_TIME_SYNC:
            logger.debug("Redis not initialized or real-time sync disabled")
            return
        
        try:
            channel = config.REDIS_CHANNEL_PATTERN.format(group_id=payload.group_id)
            message = {
                'action_id': action_id,
                'action': payload.action.value,
                'user_id': payload.user_id,
                'source': payload.source.value,
                'timestamp': payload.timestamp.isoformat(),
            }
            
            await self.redis.publish(channel, str(message))
            logger.debug(f"✓ Published to Redis: {channel}")
            
        except Exception as e:
            logger.warning(f"Redis broadcast failed: {str(e)}")
            # Don't raise - real-time sync is non-critical
    
    def _update_metrics(self, payload: ActionPayload, success: bool) -> None:
        """Update internal metrics."""
        if not config.ENABLE_METRICS_TRACKING:
            return
        
        self.metrics['total_actions'] += 1
        
        if payload.source == ActionSource.BOT:
            self.metrics['bot_actions'] += 1
        elif payload.source == ActionSource.WEB:
            self.metrics['web_actions'] += 1
        
        if not success:
            self.metrics['failed_actions'] += 1
        
        action_name = payload.action.value
        if action_name not in self.metrics['action_breakdown']:
            self.metrics['action_breakdown'][action_name] = 0
        self.metrics['action_breakdown'][action_name] += 1
    
    def _generate_action_id(self) -> str:
        """Generate unique action ID."""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def _get_action_emoji(self, action: ActionType) -> str:
        """Get emoji for action type."""
        emojis = {
            ActionType.BAN: '🚫',
            ActionType.UNBAN: '✅',
            ActionType.MUTE: '🔇',
            ActionType.UNMUTE: '🔊',
            ActionType.KICK: '👢',
            ActionType.WARN: '⚠️',
        }
        return emojis.get(action, '📋')
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        total = self.metrics['total_actions']
        failed = self.metrics['failed_actions']
        success_rate = ((total - failed) / total * 100) if total > 0 else 0
        
        return {
            **self.metrics,
            'success_rate_percent': round(success_rate, 1),
        }
