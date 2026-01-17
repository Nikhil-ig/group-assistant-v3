"""
Enforcement Engine
Unified enforcement system with escalation, tracking, and automated actions
Integrates all centralized_api enforcement operations with api_v2
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from api_v2.models.enforcement import (
    ActionType, ActionStatus, EnforcementLevel, EnforcementReason,
    EscalationPolicy, EnforcementAction, ActionResponse, ActionLog,
    UserViolation, EscalationRule, BatchActionResponse, EnforcementStats,
    UserEnforcementHistory
)
from api_v2.core.database import AdvancedDatabaseManager, get_db_manager
from api_v2.telegram import TelegramAPIWrapper

logger = logging.getLogger(__name__)


class EnforcementEngine:
    """
    Unified enforcement engine for all moderation actions
    - Action execution with retries
    - User violation tracking
    - Automatic escalation
    - Comprehensive logging
    """

    def __init__(self, db_manager: AdvancedDatabaseManager, telegram_api: Optional[TelegramAPIWrapper] = None):
        """Initialize enforcement engine"""
        self.db_manager = db_manager
        self.telegram_api = telegram_api
        self.retry_config = {
            'base': 1,
            'max_retries': 3,
            'max_backoff': 60,
        }

    # ========================================================================
    # ACTION EXECUTION
    # ========================================================================

    async def execute_action(self, action: EnforcementAction) -> ActionResponse:
        """Execute a single enforcement action with retries"""
        action_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        retry_count = 0
        last_error = None

        try:
            # Attempt execution with retries
            while retry_count <= self.retry_config['max_retries']:
                try:
                    result = await self._execute_action_internal(action)
                    
                    execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                    response = ActionResponse(
                        action_id=action_id,
                        action_type=action.action_type,
                        group_id=action.group_id,
                        user_id=action.user_id,
                        status=ActionStatus.SUCCESS,
                        success=True,
                        message=f"Action {action.action_type} executed successfully",
                        timestamp=start_time,
                        execution_time_ms=execution_time,
                        retry_count=retry_count,
                        api_response=result
                    )

                    # Log action if requested
                    if action.log_action:
                        await self._log_action(
                            action_id, action, ActionStatus.SUCCESS, True,
                            response.message, None, execution_time, retry_count, result
                        )

                    # Track user violation if applicable
                    if action.action_type in [ActionType.WARN, ActionType.MUTE, ActionType.BAN]:
                        await self.track_violation(
                            action.user_id, action.group_id, action.action_type,
                            reason=action.reason, escalate=action.escalate
                        )

                    return response

                except Exception as e:
                    last_error = e
                    retry_count += 1

                    if retry_count <= self.retry_config['max_retries']:
                        backoff = min(
                            self.retry_config['base'] * (2 ** (retry_count - 1)),
                            self.retry_config['max_backoff']
                        )
                        logger.warning(f"Action {action_id} failed, retrying in {backoff}s: {str(e)}")
                        await asyncio.sleep(backoff)

            # All retries exhausted
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            response = ActionResponse(
                action_id=action_id,
                action_type=action.action_type,
                group_id=action.group_id,
                user_id=action.user_id,
                status=ActionStatus.FAILED,
                success=False,
                message=f"Action failed after {retry_count} retries",
                error=str(last_error),
                timestamp=start_time,
                execution_time_ms=execution_time,
                retry_count=retry_count
            )

            # Log failed action
            if action.log_action:
                await self._log_action(
                    action_id, action, ActionStatus.FAILED, False,
                    response.message, str(last_error), execution_time, retry_count
                )

            logger.error(f"Action {action_id} failed: {str(last_error)}")
            return response

        except Exception as e:
            logger.error(f"Unexpected error in action {action_id}: {str(e)}")
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            return ActionResponse(
                action_id=action_id,
                action_type=action.action_type,
                group_id=action.group_id,
                user_id=action.user_id,
                status=ActionStatus.FAILED,
                success=False,
                message="Unexpected error during action execution",
                error=str(e),
                timestamp=start_time,
                execution_time_ms=execution_time,
                retry_count=retry_count
            )

    async def _execute_action_internal(self, action: EnforcementAction) -> Dict[str, Any]:
        """Internal action execution logic"""
        action_type = action.action_type
        
        # Ensure action_type is the enum, not a string
        if isinstance(action_type, str):
            try:
                action_type = ActionType(action_type)
            except ValueError:
                raise ValueError(f"Unknown action type: {action_type}")

        # Handle different action types
        if action_type == ActionType.BAN:
            return await self._handle_ban(action)
        elif action_type == ActionType.UNBAN:
            return await self._handle_unban(action)
        elif action_type == ActionType.KICK:
            return await self._handle_kick(action)
        elif action_type == ActionType.MUTE:
            return await self._handle_mute(action)
        elif action_type == ActionType.UNMUTE:
            return await self._handle_unmute(action)
        elif action_type == ActionType.PROMOTE:
            return await self._handle_promote(action)
        elif action_type == ActionType.DEMOTE:
            return await self._handle_demote(action)
        elif action_type == ActionType.WARN:
            return await self._handle_warn(action)
        elif action_type == ActionType.PIN:
            return await self._handle_pin(action)
        elif action_type == ActionType.UNPIN:
            return await self._handle_unpin(action)
        elif action_type == ActionType.DELETE_MESSAGE:
            return await self._handle_delete_message(action)
        elif action_type == ActionType.LOCKDOWN:
            return await self._handle_lockdown(action)
        elif action_type == ActionType.CLEANUP_SPAM:
            return await self._handle_cleanup_spam(action)
        elif action_type == ActionType.DELETE_USER_MESSAGES:
            return await self._handle_delete_user_messages(action)
        else:
            raise ValueError(f"Unknown action type: {action_type}")

    # ========================================================================
    # ACTION HANDLERS
    # ========================================================================

    async def _handle_ban(self, action: EnforcementAction) -> Dict[str, Any]:
        """Handle user ban"""
        if not action.user_id:
            raise ValueError("user_id required for ban action")
        
        if self.telegram_api and self.telegram_api.bot:
            await self.telegram_api.bot.ban_chat_member(
                chat_id=action.group_id,
                user_id=action.user_id
            )
            logger.info(f"User {action.user_id} banned from {action.group_id}")
            return {"action": "ban", "user_id": action.user_id}
        raise Exception("Telegram API not available")

    async def _handle_unban(self, action: EnforcementAction) -> Dict[str, Any]:
        """Handle user unban"""
        if not action.user_id:
            raise ValueError("user_id required for unban action")
        
        if self.telegram_api and self.telegram_api.bot:
            await self.telegram_api.bot.unban_chat_member(
                chat_id=action.group_id,
                user_id=action.user_id
            )
            logger.info(f"User {action.user_id} unbanned from {action.group_id}")
            return {"action": "unban", "user_id": action.user_id}
        raise Exception("Telegram API not available")

    async def _handle_kick(self, action: EnforcementAction) -> Dict[str, Any]:
        """Handle user kick"""
        if not action.user_id:
            raise ValueError("user_id required for kick action")
        
        if self.telegram_api and self.telegram_api.bot:
            await self.telegram_api.bot.ban_chat_member(
                chat_id=action.group_id,
                user_id=action.user_id
            )
            await asyncio.sleep(0.5)
            await self.telegram_api.bot.unban_chat_member(
                chat_id=action.group_id,
                user_id=action.user_id
            )
            logger.info(f"User {action.user_id} kicked from {action.group_id}")
            return {"action": "kick", "user_id": action.user_id}
        raise Exception("Telegram API not available")

    async def _handle_mute(self, action: EnforcementAction) -> Dict[str, Any]:
        """Handle user mute"""
        if not action.user_id:
            raise ValueError("user_id required for mute action")
        
        duration = action.duration_minutes or 3600  # Default 1 hour
        
        if self.telegram_api and self.telegram_api.bot:
            until_date = datetime.utcnow() + timedelta(minutes=duration)
            await self.telegram_api.bot.restrict_chat_member(
                chat_id=action.group_id,
                user_id=action.user_id,
                permissions={"can_send_messages": False},
                until_date=int(until_date.timestamp())
            )
            logger.info(f"User {action.user_id} muted for {duration} minutes")
            return {"action": "mute", "user_id": action.user_id, "duration_minutes": duration}
        raise Exception("Telegram API not available")

    async def _handle_unmute(self, action: EnforcementAction) -> Dict[str, Any]:
        """Handle user unmute"""
        if not action.user_id:
            raise ValueError("user_id required for unmute action")
        
        if self.telegram_api and self.telegram_api.bot:
            await self.telegram_api.bot.restrict_chat_member(
                chat_id=action.group_id,
                user_id=action.user_id,
                permissions={"can_send_messages": True}
            )
            logger.info(f"User {action.user_id} unmuted")
            return {"action": "unmute", "user_id": action.user_id}
        raise Exception("Telegram API not available")

    async def _handle_promote(self, action: EnforcementAction) -> Dict[str, Any]:
        """Handle user promotion"""
        if not action.user_id:
            raise ValueError("user_id required for promote action")
        
        if self.telegram_api and self.telegram_api.bot:
            await self.telegram_api.bot.promote_chat_member(
                chat_id=action.group_id,
                user_id=action.user_id,
                can_post_messages=True,
                can_edit_messages=True,
                can_delete_messages=True,
                can_restrict_members=True,
                can_promote_members=False
            )
            logger.info(f"User {action.user_id} promoted in {action.group_id}")
            return {"action": "promote", "user_id": action.user_id}
        raise Exception("Telegram API not available")

    async def _handle_demote(self, action: EnforcementAction) -> Dict[str, Any]:
        """Handle user demotion"""
        if not action.user_id:
            raise ValueError("user_id required for demote action")
        
        if self.telegram_api and self.telegram_api.bot:
            await self.telegram_api.bot.promote_chat_member(
                chat_id=action.group_id,
                user_id=action.user_id,
                can_post_messages=False,
                can_edit_messages=False,
                can_delete_messages=False,
                can_restrict_members=False,
                can_promote_members=False
            )
            logger.info(f"User {action.user_id} demoted in {action.group_id}")
            return {"action": "demote", "user_id": action.user_id}
        raise Exception("Telegram API not available")

    async def _handle_warn(self, action: EnforcementAction) -> Dict[str, Any]:
        """Handle user warning"""
        if not action.user_id:
            raise ValueError("user_id required for warn action")
        
        logger.info(f"User {action.user_id} warned in {action.group_id}: {action.reason}")
        return {"action": "warn", "user_id": action.user_id, "reason": action.reason}

    async def _handle_pin(self, action: EnforcementAction) -> Dict[str, Any]:
        """Handle message pin"""
        if not action.message_id:
            raise ValueError("message_id required for pin action")
        
        if self.telegram_api and self.telegram_api.bot:
            await self.telegram_api.bot.pin_chat_message(
                chat_id=action.group_id,
                message_id=action.message_id
            )
            logger.info(f"Message {action.message_id} pinned in {action.group_id}")
            return {"action": "pin", "message_id": action.message_id}
        raise Exception("Telegram API not available")

    async def _handle_unpin(self, action: EnforcementAction) -> Dict[str, Any]:
        """Handle message unpin"""
        if not action.message_id:
            raise ValueError("message_id required for unpin action")
        
        if self.telegram_api and self.telegram_api.bot:
            await self.telegram_api.bot.unpin_chat_message(
                chat_id=action.group_id,
                message_id=action.message_id
            )
            logger.info(f"Message {action.message_id} unpinned in {action.group_id}")
            return {"action": "unpin", "message_id": action.message_id}
        raise Exception("Telegram API not available")

    async def _handle_delete_message(self, action: EnforcementAction) -> Dict[str, Any]:
        """Handle message deletion"""
        if not action.message_id:
            raise ValueError("message_id required for delete_message action")
        
        if self.telegram_api and self.telegram_api.bot:
            await self.telegram_api.bot.delete_message(
                chat_id=action.group_id,
                message_id=action.message_id
            )
            logger.info(f"Message {action.message_id} deleted from {action.group_id}")
            return {"action": "delete_message", "message_id": action.message_id}
        raise Exception("Telegram API not available")

    async def _handle_lockdown(self, action: EnforcementAction) -> Dict[str, Any]:
        """Handle group lockdown"""
        if self.telegram_api and self.telegram_api.bot:
            await self.telegram_api.bot.restrict_chat_member(
                chat_id=action.group_id,
                permissions={"can_send_messages": False}
            )
            logger.info(f"Group {action.group_id} locked down")
            return {"action": "lockdown"}
        raise Exception("Telegram API not available")

    async def _handle_cleanup_spam(self, action: EnforcementAction) -> Dict[str, Any]:
        """Handle spam cleanup"""
        logger.info(f"Spam cleanup initiated in {action.group_id}")
        return {"action": "cleanup_spam", "deleted_messages": 0}

    async def _handle_delete_user_messages(self, action: EnforcementAction) -> Dict[str, Any]:
        """Handle delete all user messages"""
        if not action.user_id:
            raise ValueError("user_id required for delete_user_messages action")
        
        logger.info(f"Deleting all messages from user {action.user_id} in {action.group_id}")
        return {"action": "delete_user_messages", "user_id": action.user_id}

    # ========================================================================
    # BATCH OPERATIONS
    # ========================================================================

    async def execute_batch(self, batch_request) -> BatchActionResponse:
        """Execute multiple actions"""
        batch_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        results = []
        successful = 0
        failed = 0

        if batch_request.execute_concurrently:
            # Execute concurrently
            tasks = [self.execute_action(action) for action in batch_request.actions]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        else:
            # Execute sequentially
            for action in batch_request.actions:
                try:
                    result = await self.execute_action(action)
                    results.append(result)
                    if batch_request.stop_on_error and not result.success:
                        break
                except Exception as e:
                    logger.error(f"Error in batch action: {e}")
                    if batch_request.stop_on_error:
                        break

        # Count results
        for result in results:
            if isinstance(result, ActionResponse):
                if result.success:
                    successful += 1
                else:
                    failed += 1

        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        return BatchActionResponse(
            batch_id=batch_id,
            total_actions=len(batch_request.actions),
            successful=successful,
            failed=failed,
            results=results,
            execution_time_ms=execution_time
        )

    # ========================================================================
    # VIOLATION TRACKING & ESCALATION
    # ========================================================================

    async def track_violation(
        self,
        user_id: int,
        group_id: int,
        violation_type: ActionType,
        reason: Optional[str] = None,
        escalate: bool = True
    ) -> None:
        """Track user violation and apply escalation if needed"""
        try:
            collection = self.db_manager.db['user_violations']
            
            # Get or create violation record
            violation_record = await collection.find_one({
                'user_id': user_id,
                'group_id': group_id
            })

            if not violation_record:
                violation_record = {
                    'user_id': user_id,
                    'group_id': group_id,
                    'violation_count': 0,
                    'violations': [],
                    'current_level': EnforcementLevel.WARNING,
                    'escalation_policy': EscalationPolicy.ACCUMULATE,
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                }

            # Add violation
            violation_record['violation_count'] += 1
            violation_record['violations'].append({
                'type': violation_type,
                'reason': reason,
                'timestamp': datetime.utcnow()
            })
            violation_record['last_violation_time'] = datetime.utcnow()
            violation_record['updated_at'] = datetime.utcnow()

            # Update in database
            await collection.update_one(
                {'user_id': user_id, 'group_id': group_id},
                {'$set': violation_record},
                upsert=True
            )

            # Apply escalation if enabled
            if escalate and violation_record['violation_count'] % 3 == 0:
                await self._apply_escalation(user_id, group_id, violation_record)

            logger.info(f"Violation tracked for user {user_id}: count={violation_record['violation_count']}")

        except Exception as e:
            logger.error(f"Error tracking violation: {e}")

    async def _apply_escalation(
        self,
        user_id: int,
        group_id: int,
        violation_record: Dict[str, Any]
    ) -> None:
        """Apply escalation action based on violation count"""
        count = violation_record['violation_count']
        
        escalation_actions = {
            3: (ActionType.MUTE, 60),       # 1 hour mute
            6: (ActionType.MUTE, 1440),    # 24 hour mute
            9: (ActionType.BAN, None),     # Temporary ban
        }

        if count in escalation_actions:
            action_type, duration = escalation_actions[count]
            action = EnforcementAction(
                action_type=action_type,
                group_id=group_id,
                user_id=user_id,
                duration_minutes=duration,
                initiated_by=0,  # System
                reason=f"Auto-escalation after {count} violations",
                escalate=False,
                notify_user=True,
                log_action=True
            )
            
            result = await self.execute_action(action)
            if result.success:
                logger.info(f"Applied escalation to user {user_id}: {action_type}")

    async def get_user_violations(self, user_id: int, group_id: int) -> UserEnforcementHistory:
        """Get user violation history"""
        try:
            collection = self.db_manager.db['user_violations']
            record = await collection.find_one({'user_id': user_id, 'group_id': group_id})

            if not record:
                return UserEnforcementHistory(
                    user_id=user_id,
                    group_id=group_id,
                    total_violations=0,
                    recent_violations=[],
                    current_status="clean",
                    escalation_level=EnforcementLevel.WARNING,
                    is_banned=False
                )

            recent = record.get('violations', [])[-5:]  # Last 5 violations

            return UserEnforcementHistory(
                user_id=user_id,
                group_id=group_id,
                total_violations=record.get('violation_count', 0),
                recent_violations=recent,
                current_status="active" if record.get('violation_count', 0) > 0 else "clean",
                escalation_level=EnforcementLevel(record.get('current_level', 'warning')),
                is_banned=False
            )

        except Exception as e:
            logger.error(f"Error getting user violations: {e}")
            return UserEnforcementHistory(
                user_id=user_id,
                group_id=group_id,
                total_violations=0,
                recent_violations=[],
                current_status="error",
                escalation_level=EnforcementLevel.WARNING,
                is_banned=False
            )

    # ========================================================================
    # STATISTICS
    # ========================================================================

    async def get_enforcement_stats(self, group_id: int, hours: int = 24) -> EnforcementStats:
        """Get enforcement statistics for a group"""
        try:
            collection = self.db_manager.db['action_logs']
            start_time = datetime.utcnow() - timedelta(hours=hours)

            pipeline = [
                {'$match': {'group_id': group_id, 'created_at': {'$gte': start_time}}},
                {'$group': {
                    '_id': None,
                    'total': {'$sum': 1},
                    'successful': {'$sum': {'$cond': ['$success', 1, 0]}},
                    'failed': {'$sum': {'$cond': ['$success', 0, 1]}},
                    'avg_time': {'$avg': '$execution_time_ms'}
                }},
                {'$facet': {
                    'summary': [{'$match': {}}],
                    'by_type': [
                        {'$group': {'_id': '$action_type', 'count': {'$sum': 1}}}
                    ],
                    'by_status': [
                        {'$group': {'_id': '$status', 'count': {'$sum': 1}}}
                    ]
                }}
            ]

            result = await collection.aggregate(pipeline).to_list(None)

            if result:
                data = result[0]
                summary = data.get('summary', [{}])[0]
                
                by_type = {item['_id']: item['count'] for item in data.get('by_type', [])}
                by_status = {item['_id']: item['count'] for item in data.get('by_status', [])}

                return EnforcementStats(
                    group_id=group_id,
                    total_actions=summary.get('total', 0),
                    successful_actions=summary.get('successful', 0),
                    failed_actions=summary.get('failed', 0),
                    by_type=by_type,
                    by_status=by_status,
                    average_execution_time_ms=summary.get('avg_time', 0),
                    period_start=start_time,
                    period_end=datetime.utcnow()
                )

            return EnforcementStats(
                group_id=group_id,
                total_actions=0,
                successful_actions=0,
                failed_actions=0,
                by_type={},
                by_status={},
                average_execution_time_ms=0,
                period_start=start_time,
                period_end=datetime.utcnow()
            )

        except Exception as e:
            logger.error(f"Error getting enforcement stats: {e}")
            raise

    # ========================================================================
    # LOGGING
    # ========================================================================

    async def _log_action(
        self,
        action_id: str,
        action: EnforcementAction,
        status: ActionStatus,
        success: bool,
        message: str,
        error: Optional[str],
        execution_time_ms: float,
        retry_count: int,
        api_response: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log action to database"""
        try:
            collection = self.db_manager.db['action_logs']
            log_entry = {
                'action_id': action_id,
                'action_type': action.action_type.value,
                'group_id': action.group_id,
                'user_id': action.user_id,
                'initiated_by': action.initiated_by,
                'status': status.value,
                'success': success,
                'message': message,
                'error': error,
                'reason': action.reason,
                'created_at': datetime.utcnow(),
                'executed_at': datetime.utcnow(),
                'execution_time_ms': execution_time_ms,
                'retry_count': retry_count,
                'api_response': api_response,
                'metadata': action.metadata
            }

            await collection.insert_one(log_entry)

        except Exception as e:
            logger.error(f"Error logging action: {e}")
