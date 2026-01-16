"""
Advanced Database Manager - High-performance MongoDB operations
Multi-group support with advanced querying and aggregation
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING, UpdateOne, InsertOne
from pymongo.errors import DuplicateKeyError, BulkWriteError

logger = logging.getLogger(__name__)

# Global database manager instance
_db_manager: Optional["AdvancedDatabaseManager"] = None


class DatabaseIndexManager:
    """Manages indexes for optimal performance across all collections"""
    
    INDEXES = {
        "groups": [
            {"spec": [("group_id", ASCENDING)], "unique": True, "name": "group_id_unique"},
            {"spec": [("is_active", ASCENDING), ("updated_at", DESCENDING)]},
            {"spec": [("name", "text")], "name": "name_text"},
        ],
        "users": [
            {"spec": [("user_id", ASCENDING)], "unique": True},
            {"spec": [("group_id", ASCENDING), ("user_id", ASCENDING)], "unique": True},
            {"spec": [("role", ASCENDING)]},
            {"spec": [("is_active", ASCENDING)]},
        ],
        "roles": [
            {"spec": [("group_id", ASCENDING), ("name", ASCENDING)], "unique": True},
            {"spec": [("permissions", ASCENDING)]},
        ],
        "rules": [
            {"spec": [("group_id", ASCENDING), ("rule_name", ASCENDING)], "unique": True},
            {"spec": [("is_active", ASCENDING)]},
        ],
        "settings": [
            {"spec": [("group_id", ASCENDING)], "unique": True},
            {"spec": [("setting_key", ASCENDING)]},
        ],
        "actions": [
            {"spec": [("group_id", ASCENDING), ("created_at", DESCENDING)]},
            {"spec": [("user_id", ASCENDING), ("created_at", DESCENDING)]},
            {"spec": [("action_type", ASCENDING)]},
            {"spec": [("status", ASCENDING)]},
        ],
        "logs": [
            {"spec": [("group_id", ASCENDING), ("timestamp", DESCENDING)]},
            {"spec": [("event_type", ASCENDING)]},
            {"spec": [("severity", ASCENDING)]},
            {"spec": [("timestamp", DESCENDING)], "expireAfterSeconds": 2592000},  # 30 days TTL
        ],
    }
    
    @staticmethod
    async def create_indexes(db: AsyncIOMotorDatabase):
        """Create all indexes asynchronously"""
        for collection_name, indexes in DatabaseIndexManager.INDEXES.items():
            collection = db[collection_name]
            for index_spec in indexes:
                try:
                    await collection.create_index(
                        index_spec["spec"],
                        unique=index_spec.get("unique", False),
                        name=index_spec.get("name"),
                        **{k: v for k, v in index_spec.items() if k not in ["spec", "unique", "name"]}
                    )
                    logger.info(f"✅ Index created: {collection_name}.{index_spec.get('name', 'auto')}")
                except Exception as e:
                    logger.warning(f"Index creation: {collection_name} - {e}")


class AdvancedDatabaseManager:
    """
    High-performance database manager with:
    - Connection pooling
    - Advanced querying
    - Aggregation pipelines
    - Batch operations
    - Transaction support
    - Multi-group optimization
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def initialize(self):
        """Initialize database (create indexes)"""
        await DatabaseIndexManager.create_indexes(self.db)
        self.logger.info("✅ Database initialized")
    
    # ========================================================================
    # GROUP MANAGEMENT
    # ========================================================================
    
    async def create_group(self, group_data: Dict[str, Any]) -> str:
        """Create a new group"""
        try:
            group_id = group_data.get("group_id")
            if not group_id:
                raise ValueError("group_id required")
            
            group_data.update({
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_active": True,
            })
            
            result = await self.db.groups.insert_one(group_data)
            return str(result.inserted_id)
        except DuplicateKeyError:
            return await self.update_group(group_data["group_id"], group_data)
        except Exception as e:
            self.logger.error(f"Error creating group: {e}")
            raise
    
    async def get_group(self, group_id: int) -> Optional[Dict[str, Any]]:
        """Get group by ID"""
        return await self.db.groups.find_one({"group_id": group_id})
    
    async def get_groups(self, page: int = 1, per_page: int = 20, 
                        active_only: bool = True) -> Dict[str, Any]:
        """Get paginated groups"""
        query = {"is_active": True} if active_only else {}
        total = await self.db.groups.count_documents(query)
        skip = (page - 1) * per_page
        
        groups = await self.db.groups.find(query)\
            .sort("updated_at", DESCENDING)\
            .skip(skip)\
            .limit(per_page)\
            .to_list(per_page)
        
        return {
            "items": groups,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page
        }
    
    async def update_group(self, group_id: int, updates: Dict[str, Any]) -> str:
        """Update group"""
        updates["updated_at"] = datetime.utcnow()
        result = await self.db.groups.update_one(
            {"group_id": group_id},
            {"$set": updates},
            upsert=True
        )
        return str(group_id)
    
    async def delete_group(self, group_id: int) -> bool:
        """Soft delete group"""
        result = await self.db.groups.update_one(
            {"group_id": group_id},
            {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0
    
    # ========================================================================
    # USER MANAGEMENT
    # ========================================================================
    
    async def add_user_to_group(self, group_id: int, user_data: Dict[str, Any]) -> str:
        """Add user to group"""
        try:
            user_data.update({
                "group_id": group_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_active": True,
            })
            
            result = await self.db.users.insert_one(user_data)
            return str(result.inserted_id)
        except DuplicateKeyError:
            # User already exists, update
            return await self.update_user(group_id, user_data["user_id"], user_data)
        except Exception as e:
            self.logger.error(f"Error adding user: {e}")
            raise
    
    async def get_user(self, group_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user in group"""
        return await self.db.users.find_one({
            "group_id": group_id,
            "user_id": user_id
        })
    
    async def get_group_users(self, group_id: int, page: int = 1, 
                             per_page: int = 50) -> Dict[str, Any]:
        """Get all users in group (paginated)"""
        total = await self.db.users.count_documents({"group_id": group_id})
        skip = (page - 1) * per_page
        
        users = await self.db.users.find({"group_id": group_id})\
            .sort("role", ASCENDING)\
            .skip(skip)\
            .limit(per_page)\
            .to_list(per_page)
        
        return {
            "items": users,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page
        }
    
    async def update_user(self, group_id: int, user_id: int, 
                         updates: Dict[str, Any]) -> str:
        """Update user in group"""
        updates["updated_at"] = datetime.utcnow()
        await self.db.users.update_one(
            {"group_id": group_id, "user_id": user_id},
            {"$set": updates},
            upsert=True
        )
        return str(user_id)
    
    # ========================================================================
    # ROLE MANAGEMENT
    # ========================================================================
    
    async def create_role(self, group_id: int, role_data: Dict[str, Any]) -> str:
        """Create custom role in group"""
        try:
            role_data.update({
                "group_id": group_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            })
            
            result = await self.db.roles.insert_one(role_data)
            return str(result.inserted_id)
        except DuplicateKeyError:
            return await self.update_role(group_id, role_data["name"], role_data)
        except Exception as e:
            self.logger.error(f"Error creating role: {e}")
            raise
    
    async def get_role(self, group_id: int, role_name: str) -> Optional[Dict[str, Any]]:
        """Get role by name"""
        return await self.db.roles.find_one({
            "group_id": group_id,
            "name": role_name
        })
    
    async def get_group_roles(self, group_id: int) -> List[Dict[str, Any]]:
        """Get all roles in group"""
        return await self.db.roles.find({"group_id": group_id})\
            .sort("priority", DESCENDING)\
            .to_list(None)
    
    async def update_role(self, group_id: int, role_name: str, 
                         updates: Dict[str, Any]) -> str:
        """Update role"""
        updates["updated_at"] = datetime.utcnow()
        await self.db.roles.update_one(
            {"group_id": group_id, "name": role_name},
            {"$set": updates},
            upsert=True
        )
        return role_name
    
    # ========================================================================
    # RULES MANAGEMENT
    # ========================================================================
    
    async def create_rule(self, group_id: int, rule_data: Dict[str, Any]) -> str:
        """Create group rule"""
        try:
            rule_data.update({
                "group_id": group_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_active": True,
            })
            
            result = await self.db.rules.insert_one(rule_data)
            return str(result.inserted_id)
        except DuplicateKeyError:
            return await self.update_rule(group_id, rule_data["rule_name"], rule_data)
        except Exception as e:
            self.logger.error(f"Error creating rule: {e}")
            raise
    
    async def get_group_rules(self, group_id: int, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all rules in group"""
        query = {"group_id": group_id}
        if active_only:
            query["is_active"] = True
        
        return await self.db.rules.find(query)\
            .sort("priority", DESCENDING)\
            .to_list(None)
    
    async def update_rule(self, group_id: int, rule_name: str, 
                         updates: Dict[str, Any]) -> str:
        """Update rule"""
        updates["updated_at"] = datetime.utcnow()
        await self.db.rules.update_one(
            {"group_id": group_id, "rule_name": rule_name},
            {"$set": updates},
            upsert=True
        )
        return rule_name
    
    # ========================================================================
    # SETTINGS MANAGEMENT
    # ========================================================================
    
    async def get_group_settings(self, group_id: int) -> Dict[str, Any]:
        """Get all settings for group"""
        settings = await self.db.settings.find_one({"group_id": group_id})
        return settings or {}
    
    async def update_group_settings(self, group_id: int, 
                                   settings: Dict[str, Any]) -> str:
        """Update group settings"""
        settings.update({
            "group_id": group_id,
            "updated_at": datetime.utcnow(),
        })
        
        await self.db.settings.update_one(
            {"group_id": group_id},
            {"$set": settings},
            upsert=True
        )
        return str(group_id)
    
    # ========================================================================
    # ACTION LOGGING
    # ========================================================================
    
    async def log_action(self, action_data: Dict[str, Any]) -> str:
        """Log an action"""
        action_data.update({
            "created_at": datetime.utcnow(),
            "status": "completed",
        })
        
        result = await self.db.actions.insert_one(action_data)
        return str(result.inserted_id)
    
    async def get_group_actions(self, group_id: int, page: int = 1, 
                               per_page: int = 50) -> Dict[str, Any]:
        """Get actions for group (paginated)"""
        total = await self.db.actions.count_documents({"group_id": group_id})
        skip = (page - 1) * per_page
        
        actions = await self.db.actions.find({"group_id": group_id})\
            .sort("created_at", DESCENDING)\
            .skip(skip)\
            .limit(per_page)\
            .to_list(per_page)
        
        return {
            "items": actions,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page
        }
    
    # ========================================================================
    # ADVANCED ANALYTICS
    # ========================================================================
    
    async def get_group_statistics(self, group_id: int) -> Dict[str, Any]:
        """Get comprehensive statistics for group"""
        pipeline = [
            {"$match": {"group_id": group_id}},
            {"$facet": {
                "total_actions": [{"$count": "count"}],
                "by_type": [
                    {"$group": {"_id": "$action_type", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}}
                ],
                "by_user": [
                    {"$group": {"_id": "$user_id", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}},
                    {"$limit": 10}
                ],
                "recent": [
                    {"$sort": {"created_at": -1}},
                    {"$limit": 5}
                ]
            }}
        ]
        
        result = await self.db.actions.aggregate(pipeline).to_list(None)
        if result:
            return result[0]
        return {}
    
    async def get_user_statistics(self, group_id: int, user_id: int) -> Dict[str, Any]:
        """Get statistics for user in group"""
        pipeline = [
            {"$match": {"group_id": group_id, "user_id": user_id}},
            {"$group": {
                "_id": "$action_type",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}}
        ]
        
        stats = await self.db.actions.aggregate(pipeline).to_list(None)
        
        action_counts = {stat["_id"]: stat["count"] for stat in stats}
        return {
            "user_id": user_id,
            "group_id": group_id,
            "action_counts": action_counts,
            "total_actions": sum(action_counts.values())
        }
    
    # ========================================================================
    # BULK OPERATIONS
    # ========================================================================
    
    async def bulk_add_users(self, group_id: int, users: List[Dict[str, Any]]) -> Dict[str, int]:
        """Bulk add users to group"""
        try:
            operations = []
            for user in users:
                user["group_id"] = group_id
                user["created_at"] = datetime.utcnow()
                user["updated_at"] = datetime.utcnow()
                user["is_active"] = True
                operations.append(InsertOne(user))
            
            result = await self.db.users.bulk_write(operations, ordered=False)
            return {
                "inserted": result.inserted_count,
                "failed": len(users) - result.inserted_count
            }
        except BulkWriteError as e:
            self.logger.warning(f"Bulk write partial error: {e.details}")
            return {"inserted": e.details.get("nInserted", 0), "failed": len(users)}
        except Exception as e:
            self.logger.error(f"Error in bulk add users: {e}")
            raise
    
    # ========================================================================
    # TRANSACTION SUPPORT
    # ========================================================================
    
    @asynccontextmanager
    async def transaction(self):
        """Context manager for transactions"""
        async with await self.db.client.start_session() as session:
            async with session.start_transaction():
                yield session
    
    # ========================================================================
    # CLEANUP & MAINTENANCE
    # ========================================================================
    
    async def cleanup_old_logs(self, days: int = 30) -> int:
        """Remove logs older than specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        result = await self.db.logs.delete_many({
            "timestamp": {"$lt": cutoff_date}
        })
        return result.deleted_count


# ============================================================================
# Global Functions
# ============================================================================

async def init_db_manager(motor_db: AsyncIOMotorDatabase) -> AdvancedDatabaseManager:
    """Initialize the global database manager"""
    global _db_manager
    _db_manager = AdvancedDatabaseManager(motor_db)
    await _db_manager.initialize()
    return _db_manager


def get_db_manager() -> AdvancedDatabaseManager:
    """Get the global database manager"""
    if _db_manager is None:
        raise RuntimeError("Database manager not initialized. Call init_db_manager first.")
    return _db_manager


async def close_db_manager():
    """Close the database manager"""
    global _db_manager
    _db_manager = None
