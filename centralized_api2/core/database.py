"""
Professional Database Management Layer
Optimized for scalability, performance, and ease of management
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from contextlib import asynccontextmanager
from datetime import datetime
import asyncio

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo import UpdateOne, InsertOne, DeleteOne, ASCENDING, DESCENDING, TEXT
from pymongo.errors import DuplicateKeyError, ConnectionFailure

logger = logging.getLogger(__name__)


class DatabaseIndex:
    """Index configuration for optimal performance"""
    
    @staticmethod
    def get_indexes() -> Dict[str, List[Tuple]]:
        """Get all recommended indexes for collections"""
        return {
            'groups': [
                (('group_id',), {'unique': True}),
                (('is_active',), {}),
                (('created_at',), {}),
                (('updated_at',), {}),
                (('member_count',), {}),
                (('admin_count',), {}),
            ],
            'users': [
                (('user_id',), {'unique': True}),
                (('username',), {}),
                (('role',), {}),
                (('is_active',), {}),
            ],
            'actions': [
                (('group_id',), {}),
                (('user_id',), {}),
                (('action_type',), {}),
                (('created_at',), {}),
                (('status',), {}),
                (('group_id', 'created_at'), {}),  # Composite index
            ],
            'logs': [
                (('event_type',), {}),
                (('timestamp',), {}),
                (('group_id',), {}),
                (('severity',), {}),
            ],
        }


class DatabaseConnection:
    """Manages MongoDB connection with reconnection logic"""
    
    def __init__(
        self,
        uri: str,
        database_name: str,
        max_pool_size: int = 50,
        min_pool_size: int = 10,
        timeout: int = 5000,
    ):
        self.uri = uri
        self.database_name = database_name
        self.max_pool_size = max_pool_size
        self.min_pool_size = min_pool_size
        self.timeout = timeout
        
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self._connected = False
        self._retry_count = 0
        self._max_retries = 5
    
    async def connect(self) -> None:
        """Establish database connection with retry logic"""
        if self._connected:
            return
        
        try:
            logger.info(f"🔗 Connecting to MongoDB: {self.database_name}")
            
            self.client = AsyncIOMotorClient(
                self.uri,
                maxPoolSize=self.max_pool_size,
                minPoolSize=self.min_pool_size,
                serverSelectionTimeoutMS=self.timeout,
                connectTimeoutMS=self.timeout,
                socketTimeoutMS=self.timeout,
            )
            
            self.db = self.client[self.database_name]
            
            # Test connection
            await self.db.command('ping')
            
            # Create indexes
            await self._create_indexes()
            
            self._connected = True
            self._retry_count = 0
            logger.info(f"✅ Connected to {self.database_name}")
            
        except ConnectionFailure as e:
            self._retry_count += 1
            if self._retry_count < self._max_retries:
                logger.warning(f"⚠️ Connection attempt {self._retry_count}/{self._max_retries} failed: {e}")
                await asyncio.sleep(2 ** self._retry_count)  # Exponential backoff
                await self.connect()
            else:
                logger.error(f"❌ Failed to connect after {self._max_retries} attempts")
                raise
        except Exception as e:
            logger.error(f"❌ Connection error: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close database connection"""
        if self.client:
            self.client.close()
            self._connected = False
            logger.info("🔌 Disconnected from MongoDB")
    
    async def _create_indexes(self) -> None:
        """Create all recommended indexes"""
        if not self.db:
            return
        
        try:
            logger.info("📑 Creating database indexes...")
            indexes = DatabaseIndex.get_indexes()
            
            for collection_name, index_list in indexes.items():
                collection = self.db[collection_name]
                
                for keys, options in index_list:
                    await collection.create_index(keys, **options)
                    logger.debug(f"  ✓ Created index on {collection_name}: {keys}")
            
            logger.info("✅ Indexes created successfully")
            
        except Exception as e:
            logger.warning(f"⚠️ Error creating indexes: {e}")
    
    async def health_check(self) -> bool:
        """Check database connection health"""
        try:
            if not self.db:
                return False
            
            await self.db.command('ping')
            return True
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return False


class QueryBuilder:
    """Fluent query builder for MongoDB operations"""
    
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection
        self.filter = {}
        self.sort_spec = []
        self.skip_count = 0
        self.limit_count = 0
        self.projection = None
    
    def where(self, **kwargs) -> 'QueryBuilder':
        """Add filter conditions"""
        self.filter.update(kwargs)
        return self
    
    def where_in(self, field: str, values: List[Any]) -> 'QueryBuilder':
        """Add $in filter"""
        self.filter[field] = {'$in': values}
        return self
    
    def where_gt(self, field: str, value: Any) -> 'QueryBuilder':
        """Add greater than filter"""
        self.filter[field] = {'$gt': value}
        return self
    
    def where_lt(self, field: str, value: Any) -> 'QueryBuilder':
        """Add less than filter"""
        self.filter[field] = {'$lt': value}
        return self
    
    def where_exists(self, field: str, exists: bool = True) -> 'QueryBuilder':
        """Add exists filter"""
        self.filter[field] = {'$exists': exists}
        return self
    
    def sort(self, field: str, direction: int = ASCENDING) -> 'QueryBuilder':
        """Add sort specification"""
        self.sort_spec.append((field, direction))
        return self
    
    def skip(self, count: int) -> 'QueryBuilder':
        """Add skip"""
        self.skip_count = count
        return self
    
    def limit(self, count: int) -> 'QueryBuilder':
        """Add limit"""
        self.limit_count = count
        return self
    
    def select(self, *fields: str) -> 'QueryBuilder':
        """Specify fields to return"""
        self.projection = {field: 1 for field in fields}
        self.projection['_id'] = 1
        return self
    
    async def first(self) -> Optional[Dict]:
        """Get first matching document"""
        query = self.collection.find_one(self.filter, projection=self.projection)
        return await query
    
    async def find_all(self) -> List[Dict]:
        """Get all matching documents"""
        query = self.collection.find(self.filter, projection=self.projection)
        
        if self.sort_spec:
            query = query.sort(self.sort_spec)
        
        if self.skip_count:
            query = query.skip(self.skip_count)
        
        if self.limit_count:
            query = query.limit(self.limit_count)
        
        return await query.to_list(None)
    
    async def count(self) -> int:
        """Count matching documents"""
        return await self.collection.count_documents(self.filter)
    
    async def exists(self) -> bool:
        """Check if any document matches"""
        return await self.collection.count_documents(self.filter) > 0
    
    async def paginate(self, page: int = 1, per_page: int = 20) -> Dict:
        """Get paginated results"""
        skip = (page - 1) * per_page
        
        total = await self.collection.count_documents(self.filter)
        
        query = self.collection.find(self.filter, projection=self.projection)
        
        if self.sort_spec:
            query = query.sort(self.sort_spec)
        
        items = await query.skip(skip).limit(per_page).to_list(None)
        
        return {
            'items': items,
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page,
        }


class DatabaseManager:
    """High-level database operations manager"""
    
    def __init__(self, connection: DatabaseConnection):
        self.connection = connection
        self.db = None
    
    async def initialize(self) -> None:
        """Initialize the manager"""
        await self.connection.connect()
        self.db = self.connection.db
    
    async def close(self) -> None:
        """Close the manager"""
        await self.connection.disconnect()
    
    # ==================== GROUP OPERATIONS ====================
    
    async def create_group(self, group_data: Dict[str, Any]) -> Optional[str]:
        """Create a new group"""
        try:
            group_data['created_at'] = datetime.utcnow()
            group_data['updated_at'] = datetime.utcnow()
            
            result = await self.db['groups'].insert_one(group_data)
            logger.info(f"✓ Created group: {group_data.get('group_name')}")
            return str(result.inserted_id)
        except DuplicateKeyError:
            logger.warning(f"⚠️ Group already exists: {group_data.get('group_id')}")
            return None
        except Exception as e:
            logger.error(f"❌ Error creating group: {e}")
            raise
    
    async def update_group(self, group_id: int, updates: Dict[str, Any]) -> bool:
        """Update group data"""
        try:
            updates['updated_at'] = datetime.utcnow()
            
            result = await self.db['groups'].update_one(
                {'group_id': group_id},
                {'$set': updates}
            )
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"❌ Error updating group: {e}")
            raise
    
    async def get_group(self, group_id: int) -> Optional[Dict]:
        """Get group by ID"""
        return await QueryBuilder(self.db['groups']).where(group_id=group_id).first()
    
    async def get_all_groups(self, active_only: bool = True, page: int = 1, per_page: int = 20) -> Dict:
        """Get paginated groups"""
        query = QueryBuilder(self.db['groups'])
        
        if active_only:
            query.where(is_active=True)
        
        query.sort('created_at', DESCENDING)
        
        return await query.paginate(page, per_page)
    
    # ==================== USER OPERATIONS ====================
    
    async def create_user(self, user_data: Dict[str, Any]) -> Optional[str]:
        """Create a new user"""
        try:
            user_data['created_at'] = datetime.utcnow()
            user_data['updated_at'] = datetime.utcnow()
            
            result = await self.db['users'].insert_one(user_data)
            logger.info(f"✓ Created user: {user_data.get('username')}")
            return str(result.inserted_id)
        except DuplicateKeyError:
            logger.warning(f"⚠️ User already exists: {user_data.get('user_id')}")
            return None
        except Exception as e:
            logger.error(f"❌ Error creating user: {e}")
            raise
    
    async def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        return await QueryBuilder(self.db['users']).where(user_id=user_id).first()
    
    async def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        return await QueryBuilder(self.db['users']).where(username=username).first()
    
    # ==================== ACTION OPERATIONS ====================
    
    async def create_action(self, action_data: Dict[str, Any]) -> Optional[str]:
        """Create a new action"""
        try:
            action_data['created_at'] = datetime.utcnow()
            action_data['updated_at'] = datetime.utcnow()
            
            result = await self.db['actions'].insert_one(action_data)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"❌ Error creating action: {e}")
            raise
    
    async def get_group_actions(self, group_id: int, page: int = 1, per_page: int = 50) -> Dict:
        """Get actions for a group"""
        query = QueryBuilder(self.db['actions'])
        query.where(group_id=group_id)
        query.sort('created_at', DESCENDING)
        
        return await query.paginate(page, per_page)
    
    async def get_user_actions(self, user_id: int, page: int = 1, per_page: int = 50) -> Dict:
        """Get actions by a user"""
        query = QueryBuilder(self.db['actions'])
        query.where(user_id=user_id)
        query.sort('created_at', DESCENDING)
        
        return await query.paginate(page, per_page)
    
    # ==================== STATISTICS OPERATIONS ====================
    
    async def get_group_stats(self, group_id: int) -> Dict:
        """Get statistics for a group"""
        try:
            group = await self.get_group(group_id)
            
            if not group:
                return {}
            
            actions_query = QueryBuilder(self.db['actions'])
            actions_query.where(group_id=group_id)
            total_actions = await actions_query.count()
            
            return {
                'group_id': group_id,
                'group_name': group.get('group_name'),
                'members': group.get('member_count', 0),
                'admins': group.get('admin_count', 0),
                'total_actions': total_actions,
                'created_at': group.get('created_at'),
                'last_updated': group.get('updated_at'),
            }
        except Exception as e:
            logger.error(f"❌ Error getting group stats: {e}")
            return {}
    
    async def get_dashboard_stats(self) -> Dict:
        """Get overall dashboard statistics"""
        try:
            groups_query = QueryBuilder(self.db['groups'])
            groups_query.where(is_active=True)
            total_groups = await groups_query.count()
            
            users_query = QueryBuilder(self.db['users'])
            users_query.where(is_active=True)
            total_users = await users_query.count()
            
            actions_query = QueryBuilder(self.db['actions'])
            total_actions = await actions_query.count()
            
            return {
                'total_groups': total_groups,
                'total_users': total_users,
                'total_actions': total_actions,
                'timestamp': datetime.utcnow(),
            }
        except Exception as e:
            logger.error(f"❌ Error getting dashboard stats: {e}")
            return {}
    
    # ==================== BULK OPERATIONS ====================
    
    async def bulk_insert_groups(self, groups: List[Dict]) -> Dict:
        """Bulk insert groups"""
        try:
            operations = []
            for group in groups:
                group['created_at'] = datetime.utcnow()
                group['updated_at'] = datetime.utcnow()
                operations.append(InsertOne(group))
            
            if not operations:
                return {'inserted': 0, 'failed': 0}
            
            result = await self.db['groups'].bulk_write(operations, ordered=False)
            
            logger.info(f"✓ Bulk inserted {result.inserted_count} groups")
            
            return {
                'inserted': result.inserted_count,
                'failed': len(groups) - result.inserted_count,
            }
        except Exception as e:
            logger.error(f"❌ Error in bulk insert: {e}")
            raise
    
    async def bulk_update_stats(self, updates: List[Tuple[int, Dict]]) -> Dict:
        """Bulk update group statistics"""
        try:
            operations = []
            for group_id, update_data in updates:
                update_data['updated_at'] = datetime.utcnow()
                operations.append(
                    UpdateOne({'group_id': group_id}, {'$set': update_data})
                )
            
            if not operations:
                return {'modified': 0}
            
            result = await self.db['groups'].bulk_write(operations, ordered=False)
            
            return {'modified': result.modified_count}
        except Exception as e:
            logger.error(f"❌ Error in bulk update: {e}")
            raise
    
    # ==================== TRANSACTION OPERATIONS ====================
    
    @asynccontextmanager
    async def transaction(self):
        """Async context manager for transactions"""
        session = self.connection.client.start_session()
        try:
            async with session.start_transaction():
                yield session
            logger.info("✓ Transaction committed")
        except Exception as e:
            logger.error(f"❌ Transaction failed: {e}")
            raise
        finally:
            await session.end_session()
    
    # ==================== CLEANUP OPERATIONS ====================
    
    async def delete_group(self, group_id: int) -> bool:
        """Soft delete a group"""
        try:
            result = await self.db['groups'].update_one(
                {'group_id': group_id},
                {
                    '$set': {
                        'is_active': False,
                        'deleted_at': datetime.utcnow(),
                    }
                }
            )
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"❌ Error deleting group: {e}")
            raise
    
    async def cleanup_old_logs(self, days: int = 30) -> int:
        """Delete logs older than specified days"""
        try:
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            result = await self.db['logs'].delete_many(
                {'timestamp': {'$lt': cutoff_date}}
            )
            
            logger.info(f"✓ Cleaned up {result.deleted_count} old logs")
            return result.deleted_count
        except Exception as e:
            logger.error(f"❌ Error cleaning up logs: {e}")
            raise


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


async def get_db_manager() -> DatabaseManager:
    """Get or create global database manager"""
    global _db_manager
    if _db_manager is None:
        raise RuntimeError("Database manager not initialized")
    return _db_manager


async def init_db_manager(uri: str, database_name: str) -> DatabaseManager:
    """Initialize global database manager"""
    global _db_manager
    
    connection = DatabaseConnection(uri, database_name)
    _db_manager = DatabaseManager(connection)
    await _db_manager.initialize()
    
    return _db_manager


async def close_db_manager() -> None:
    """Close global database manager"""
    global _db_manager
    if _db_manager:
        await _db_manager.close()
        _db_manager = None
