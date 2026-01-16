"""
Auto-Registration Routes
API endpoints for automatic group registration when bot joins
"""

from fastapi import APIRouter, HTTPException, Body
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/groups", tags=["groups"])


# Store db reference (set in main app)
db = None


def set_db(database):
    global db
    db = database


@router.post("/auto-register")
async def auto_register_group(
    group_id: int = Body(..., embed=True),
    group_name: str = Body(..., embed=True),
    group_type: str = Body(default="group", embed=True),
    member_count: int = Body(default=0, embed=True),
    admin_count: int = Body(default=0, embed=True),
    description: str = Body(default="", embed=True),
    photo_url: str = Body(default="", embed=True),
):
    """
    Auto-register a new group when bot joins
    
    This endpoint is called by the Telegram bot when:
    - Bot joins a new group
    - Bot encounters a group not in database
    
    Request:
    {
        "group_id": -1001234567890,
        "group_name": "My Group",
        "group_type": "supergroup",
        "member_count": 150,
        "admin_count": 3,
        "description": "Group description",
        "photo_url": "http://..."
    }
    """
    if db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    if not group_id:
        raise HTTPException(status_code=400, detail="group_id is required")
    
    if not group_name:
        raise HTTPException(status_code=400, detail="group_name is required")
    
    try:
        groups_col = db['groups']
        
        # Check if group already exists
        existing = await groups_col.find_one({'group_id': group_id})
        
        if existing:
            # Update metadata
            update_result = await groups_col.update_one(
                {'group_id': group_id},
                {
                    '$set': {
                        'group_name': group_name,
                        'member_count': member_count,
                        'admin_count': admin_count,
                        'updated_at': datetime.utcnow(),
                    }
                }
            )
            
            logger.info(f"Updated group {group_id}: {group_name}")
            
            return {
                "success": True,
                "action": "updated",
                "group_id": group_id,
                "group_name": group_name,
                "message": f"Group {group_name} updated"
            }
        
        # Create new group document
        group_doc = {
            'group_id': group_id,
            'group_name': group_name,
            'group_type': group_type,
            'description': description,
            'member_count': member_count,
            'admin_count': admin_count,
            'photo_url': photo_url,
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
            },
            'stats': {
                'total_actions': 0,
                'total_warnings': 0,
                'total_mutes': 0,
                'total_bans': 0,
            }
        }
        
        insert_result = await groups_col.insert_one(group_doc)
        
        logger.info(f"Registered new group: {group_name} (ID: {group_id})")
        
        # Log the event
        logs_col = db['logs']
        await logs_col.insert_one({
            'event_type': 'group_auto_registered',
            'group_id': group_id,
            'group_name': group_name,
            'member_count': member_count,
            'admin_count': admin_count,
            'timestamp': datetime.utcnow(),
            'source': 'api'
        })
        
        return {
            "success": True,
            "action": "created",
            "group_id": group_id,
            "group_name": group_name,
            "members": member_count,
            "admins": admin_count,
            "message": f"Group {group_name} auto-registered successfully"
        }
        
    except Exception as e:
        logger.error(f"Error auto-registering group: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to register group: {str(e)}")


@router.post("/ensure-exists")
async def ensure_group_exists(
    group_id: int = Body(..., embed=True),
    group_name: str = Body(..., embed=True),
    group_type: str = Body(default="group", embed=True),
    member_count: int = Body(default=0, embed=True),
    admin_count: int = Body(default=0, embed=True),
    description: str = Body(default="", embed=True),
    photo_url: str = Body(default="", embed=True),
):
    """
    Ensure a group exists in database, create if missing
    Safe to call multiple times
    
    This is useful when bot receives messages from unknown groups
    """
    if db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    try:
        groups_col = db['groups']
        
        # Check if exists
        existing = await groups_col.find_one({'group_id': group_id})
        
        if existing:
            return {
                "success": True,
                "action": "exists",
                "group_id": group_id,
                "message": "Group already registered"
            }
        
        # Create new group
        group_doc = {
            'group_id': group_id,
            'group_name': group_name,
            'group_type': group_type,
            'description': description,
            'member_count': member_count,
            'admin_count': admin_count,
            'photo_url': photo_url,
            'is_active': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'metadata': {
                'auto_registered': True,
                'registration_source': 'auto_ensure',
            },
            'settings': {
                'auto_warn_enabled': False,
                'auto_mute_enabled': False,
                'spam_threshold': 5,
                'profanity_filter': False,
            },
            'stats': {
                'total_actions': 0,
                'total_warnings': 0,
                'total_mutes': 0,
                'total_bans': 0,
            }
        }
        
        await groups_col.insert_one(group_doc)
        
        logger.info(f"Ensured group exists: {group_name} (ID: {group_id})")
        
        return {
            "success": True,
            "action": "created",
            "group_id": group_id,
            "group_name": group_name,
            "message": f"Group {group_name} created"
        }
        
    except Exception as e:
        logger.error(f"Error ensuring group exists: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to ensure group: {str(e)}")


@router.put("/update-stats/{group_id}")
async def update_group_stats(
    group_id: int,
    member_count: int = Body(default=None, embed=True),
    admin_count: int = Body(default=None, embed=True),
):
    """
    Update group statistics (members, admins)
    
    Called periodically to keep group metadata current
    """
    if db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    try:
        groups_col = db['groups']
        
        # Check if group exists
        existing = await groups_col.find_one({'group_id': group_id})
        
        if not existing:
            raise HTTPException(status_code=404, detail=f"Group {group_id} not found")
        
        update_data = {'updated_at': datetime.utcnow()}
        
        if member_count is not None:
            update_data['member_count'] = member_count
        
        if admin_count is not None:
            update_data['admin_count'] = admin_count
        
        await groups_col.update_one(
            {'group_id': group_id},
            {'$set': update_data}
        )
        
        logger.info(f"Updated stats for group {group_id}")
        
        return {
            "success": True,
            "group_id": group_id,
            "members": member_count,
            "admins": admin_count,
            "message": "Group stats updated"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating group stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update group stats: {str(e)}")


@router.get("/list-unregistered")
async def list_unregistered_groups():
    """
    Get information about groups not yet in database
    Useful for bulk registration
    
    Note: This would need to be populated from your bot's knowledge
    of active groups (e.g., from Redis cache or bot state)
    """
    # This is a placeholder - actual implementation depends on your bot setup
    return {
        "message": "Unregistered groups list endpoint",
        "note": "Implement in your bot to track groups not in database"
    }


@router.post("/bulk-register")
async def bulk_register_groups(
    groups: list = Body(..., embed=True)
):
    """
    Register multiple groups at once
    
    Useful when initializing bot with existing groups
    
    Request:
    {
        "groups": [
            {
                "group_id": -1001234567890,
                "group_name": "Group 1",
                "member_count": 100,
                "admin_count": 2
            },
            ...
        ]
    }
    """
    if db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    if not groups or not isinstance(groups, list):
        raise HTTPException(status_code=400, detail="groups must be a non-empty list")
    
    try:
        groups_col = db['groups']
        
        created = 0
        updated = 0
        failed = 0
        errors = []
        
        for group_data in groups:
            try:
                group_id = group_data.get('group_id')
                group_name = group_data.get('group_name', 'Unknown')
                
                if not group_id:
                    failed += 1
                    errors.append("Missing group_id in one of the entries")
                    continue
                
                # Check if exists
                existing = await groups_col.find_one({'group_id': group_id})
                
                if existing:
                    # Update
                    await groups_col.update_one(
                        {'group_id': group_id},
                        {
                            '$set': {
                                'group_name': group_name,
                                'member_count': group_data.get('member_count', 0),
                                'admin_count': group_data.get('admin_count', 0),
                                'updated_at': datetime.utcnow(),
                            }
                        }
                    )
                    updated += 1
                else:
                    # Create
                    group_doc = {
                        'group_id': group_id,
                        'group_name': group_name,
                        'group_type': group_data.get('group_type', 'group'),
                        'description': group_data.get('description', ''),
                        'member_count': group_data.get('member_count', 0),
                        'admin_count': group_data.get('admin_count', 0),
                        'photo_url': group_data.get('photo_url', ''),
                        'is_active': True,
                        'created_at': datetime.utcnow(),
                        'updated_at': datetime.utcnow(),
                        'metadata': {
                            'auto_registered': True,
                            'registration_source': 'bulk_import',
                        },
                        'settings': {
                            'auto_warn_enabled': False,
                            'auto_mute_enabled': False,
                            'spam_threshold': 5,
                            'profanity_filter': False,
                        },
                        'stats': {
                            'total_actions': 0,
                            'total_warnings': 0,
                            'total_mutes': 0,
                            'total_bans': 0,
                        }
                    }
                    
                    await groups_col.insert_one(group_doc)
                    created += 1
                    
            except Exception as e:
                logger.error(f"Error registering group: {e}")
                failed += 1
                errors.append(f"Error for {group_data.get('group_name')}: {str(e)}")
        
        logger.info(f"Bulk registration: {created} created, {updated} updated, {failed} failed")
        
        return {
            "success": True,
            "created": created,
            "updated": updated,
            "failed": failed,
            "total": len(groups),
            "errors": errors if errors else [],
            "message": f"Bulk registration complete: {created} created, {updated} updated, {failed} failed"
        }
        
    except Exception as e:
        logger.error(f"Error in bulk registration: {e}")
        raise HTTPException(status_code=500, detail=f"Bulk registration failed: {str(e)}")
