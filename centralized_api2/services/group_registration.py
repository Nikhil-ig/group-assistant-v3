"""
Group Registration Service
Automatically registers new groups when bot joins or encounters new groups
Captures members, admins, and other group metadata
"""

from datetime import datetime
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)


class GroupRegistrationService:
    """Handles automatic group registration and updates"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.groups_col = db['groups']
        self.users_col = db['users']
        self.logs_col = db['logs']

    async def register_group(
        self,
        group_id: int,
        group_name: str,
        group_type: str = 'group',
        description: Optional[str] = None,
        member_count: int = 0,
        admin_count: int = 0,
        photo_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Register a new group in the database
        Called when bot joins a new group or discovers a new group
        
        Args:
            group_id: Telegram group ID (negative number)
            group_name: Name of the group
            group_type: 'group', 'supergroup', 'channel'
            description: Group description
            member_count: Number of members
            admin_count: Number of administrators
            photo_url: Group photo URL
            
        Returns:
            Dictionary with registration result
        """
        try:
            # Check if group already exists
            existing = await self.groups_col.find_one({'group_id': group_id})
            
            if existing:
                logger.info(f"Group {group_id} already registered, updating metadata")
                # Update existing group with new data
                update_data = {
                    'group_name': group_name,
                    'member_count': member_count,
                    'admin_count': admin_count,
                    'updated_at': datetime.utcnow(),
                }
                
                if description:
                    update_data['description'] = description
                if photo_url:
                    update_data['photo_url'] = photo_url
                
                result = await self.groups_col.update_one(
                    {'group_id': group_id},
                    {'$set': update_data}
                )
                
                logger.info(f"Updated group {group_id}: {result.modified_count} documents")
                
                return {
                    'success': True,
                    'group_id': group_id,
                    'action': 'updated',
                    'message': f'Group {group_name} metadata updated'
                }
            
            # Create new group document
            group_doc = {
                'group_id': group_id,
                'group_name': group_name,
                'group_type': group_type,
                'description': description or '',
                'member_count': member_count,
                'admin_count': admin_count,
                'photo_url': photo_url or '',
                'is_active': True,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'metadata': {
                    'auto_registered': True,
                    'registration_source': 'bot_join',
                },
                'settings': {
                    'auto_warn_enabled': False,
                    'auto_mute_enabled': False,
                    'spam_threshold': 5,
                    'profanity_filter': False,
                }
            }
            
            result = await self.groups_col.insert_one(group_doc)
            
            logger.info(f"Registered new group {group_name} (ID: {group_id})")
            
            # Log the registration
            await self._log_event(
                event_type='group_registered',
                group_id=group_id,
                details={
                    'group_name': group_name,
                    'member_count': member_count,
                    'admin_count': admin_count,
                }
            )
            
            return {
                'success': True,
                'group_id': group_id,
                'group_name': group_name,
                'action': 'created',
                'message': f'Group {group_name} registered successfully',
                'data': {
                    'members': member_count,
                    'admins': admin_count,
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to register group {group_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to register group'
            }

    async def update_group_stats(
        self,
        group_id: int,
        member_count: Optional[int] = None,
        admin_count: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Update group statistics (member count, admin count)
        Called periodically or when changes detected
        
        Args:
            group_id: Telegram group ID
            member_count: Updated member count
            admin_count: Updated admin count
            
        Returns:
            Update result
        """
        try:
            update_data = {'updated_at': datetime.utcnow()}
            
            if member_count is not None:
                update_data['member_count'] = member_count
            
            if admin_count is not None:
                update_data['admin_count'] = admin_count
            
            result = await self.groups_col.update_one(
                {'group_id': group_id},
                {'$set': update_data}
            )
            
            if result.matched_count == 0:
                logger.warning(f"Group {group_id} not found for stats update")
                return {
                    'success': False,
                    'message': f'Group {group_id} not found'
                }
            
            logger.info(f"Updated stats for group {group_id}")
            
            return {
                'success': True,
                'group_id': group_id,
                'members': member_count,
                'admins': admin_count,
            }
            
        except Exception as e:
            logger.error(f"Failed to update group stats: {e}")
            return {
                'success': False,
                'error': str(e),
            }

    async def ensure_group_exists(
        self,
        group_id: int,
        group_name: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Ensure a group exists in database, create if not
        Safe to call multiple times
        
        Args:
            group_id: Telegram group ID
            group_name: Group name
            **kwargs: Additional group metadata
            
        Returns:
            Result indicating if group was created or already existed
        """
        try:
            # Check if exists
            existing = await self.groups_col.find_one({'group_id': group_id})
            
            if existing:
                return {
                    'success': True,
                    'action': 'exists',
                    'group_id': group_id,
                    'message': 'Group already registered'
                }
            
            # Create new group
            return await self.register_group(
                group_id=group_id,
                group_name=group_name,
                **kwargs
            )
            
        except Exception as e:
            logger.error(f"Error ensuring group exists: {e}")
            return {
                'success': False,
                'error': str(e),
            }

    async def get_group_info(self, group_id: int) -> Optional[Dict[str, Any]]:
        """
        Get complete group information from database
        
        Args:
            group_id: Telegram group ID
            
        Returns:
            Group document or None if not found
        """
        try:
            group = await self.groups_col.find_one({'group_id': group_id})
            return group
        except Exception as e:
            logger.error(f"Error fetching group info: {e}")
            return None

    async def list_registered_groups(self, active_only: bool = True) -> list:
        """
        List all registered groups
        
        Args:
            active_only: Only return active groups
            
        Returns:
            List of group documents
        """
        try:
            query = {'is_active': True} if active_only else {}
            groups = await self.groups_col.find(query).to_list(None)
            return groups
        except Exception as e:
            logger.error(f"Error listing groups: {e}")
            return []

    async def deactivate_group(self, group_id: int) -> Dict[str, Any]:
        """
        Deactivate a group (bot removed from group)
        
        Args:
            group_id: Telegram group ID
            
        Returns:
            Update result
        """
        try:
            result = await self.groups_col.update_one(
                {'group_id': group_id},
                {
                    '$set': {
                        'is_active': False,
                        'deactivated_at': datetime.utcnow(),
                    }
                }
            )
            
            if result.matched_count == 0:
                return {
                    'success': False,
                    'message': f'Group {group_id} not found'
                }
            
            logger.info(f"Deactivated group {group_id}")
            
            await self._log_event(
                event_type='group_deactivated',
                group_id=group_id,
            )
            
            return {
                'success': True,
                'group_id': group_id,
                'message': 'Group deactivated'
            }
            
        except Exception as e:
            logger.error(f"Error deactivating group: {e}")
            return {
                'success': False,
                'error': str(e),
            }

    async def _log_event(
        self,
        event_type: str,
        group_id: int,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log a group-related event
        
        Args:
            event_type: Type of event (group_registered, etc)
            group_id: Group ID
            details: Event details
        """
        try:
            log_doc = {
                'event_type': event_type,
                'group_id': group_id,
                'details': details or {},
                'timestamp': datetime.utcnow(),
            }
            
            await self.logs_col.insert_one(log_doc)
        except Exception as e:
            logger.error(f"Failed to log event: {e}")

    async def bulk_register_groups(self, groups: list) -> Dict[str, Any]:
        """
        Register multiple groups at once
        
        Args:
            groups: List of group dictionaries
                    {group_id, group_name, member_count, admin_count, ...}
                    
        Returns:
            Bulk registration result
        """
        if not groups:
            return {
                'success': False,
                'message': 'No groups provided'
            }
        
        created = 0
        updated = 0
        failed = 0
        
        for group_data in groups:
            try:
                result = await self.register_group(
                    group_id=group_data.get('group_id'),
                    group_name=group_data.get('group_name', 'Unknown'),
                    group_type=group_data.get('group_type', 'group'),
                    description=group_data.get('description'),
                    member_count=group_data.get('member_count', 0),
                    admin_count=group_data.get('admin_count', 0),
                    photo_url=group_data.get('photo_url'),
                )
                
                if result['success']:
                    if result['action'] == 'created':
                        created += 1
                    else:
                        updated += 1
                else:
                    failed += 1
                    
            except Exception as e:
                logger.error(f"Error registering group: {e}")
                failed += 1
        
        logger.info(f"Bulk registration: {created} created, {updated} updated, {failed} failed")
        
        return {
            'success': True,
            'created': created,
            'updated': updated,
            'failed': failed,
            'total': len(groups),
            'message': f'Bulk registration complete: {created} created, {updated} updated'
        }


# Example usage in bot handlers
async def handle_bot_join(
    db: AsyncIOMotorDatabase,
    chat_id: int,
    chat_name: str,
    chat_type: str,
    member_count: int,
    admin_count: int,
) -> Dict[str, Any]:
    """
    Handle bot joining a new group
    Called from bot's on_my_chat_member handler
    
    Example:
        @bot.on_message(filters.status_update.new_chat_members)
        async def on_bot_join(client, message):
            if message.from_user.is_self:  # Bot joined
                result = await handle_bot_join(
                    db,
                    message.chat.id,
                    message.chat.title,
                    message.chat.type,
                    member_count,  # Get from group info
                    admin_count    # Get from group info
                )
    """
    service = GroupRegistrationService(db)
    return await service.register_group(
        group_id=chat_id,
        group_name=chat_name,
        group_type=chat_type,
        member_count=member_count,
        admin_count=admin_count,
    )
