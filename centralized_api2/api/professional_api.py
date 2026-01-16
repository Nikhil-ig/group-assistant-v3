"""
Professional Data Management API
Fast, scalable, and easy to manage REST API for all operations
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Depends, Body
from pydantic import BaseModel, Field, validator

from centralized_api.core.database import get_db_manager, DatabaseManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["professional-api"])


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class GroupBase(BaseModel):
    """Base group model"""
    group_id: int
    group_name: str
    group_type: Optional[str] = "group"
    description: Optional[str] = ""
    member_count: int = 0
    admin_count: int = 0
    photo_url: Optional[str] = ""
    is_active: bool = True
    
    class Config:
        json_schema_extra = {
            "example": {
                "group_id": -1001234567890,
                "group_name": "My Group",
                "member_count": 100,
                "admin_count": 3
            }
        }


class GroupResponse(GroupBase):
    """Group response model"""
    id: Optional[str] = Field(None, alias="_id")
    created_at: datetime
    updated_at: datetime


class UserBase(BaseModel):
    """Base user model"""
    user_id: int
    username: str
    role: str = "user"
    is_active: bool = True
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 123456789,
                "username": "john_doe",
                "role": "admin"
            }
        }


class UserResponse(UserBase):
    """User response model"""
    id: Optional[str] = Field(None, alias="_id")
    created_at: datetime
    updated_at: datetime


class ActionBase(BaseModel):
    """Base action model"""
    group_id: int
    user_id: int
    action_type: str
    description: Optional[str] = ""
    status: str = "completed"
    
    class Config:
        json_schema_extra = {
            "example": {
                "group_id": -1001234567890,
                "user_id": 123456789,
                "action_type": "warn",
                "description": "User warned for spam"
            }
        }


class ActionResponse(ActionBase):
    """Action response model"""
    id: Optional[str] = Field(None, alias="_id")
    created_at: datetime
    updated_at: datetime


class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Query(1, ge=1)
    per_page: int = Query(20, ge=1, le=100)


# ============================================================================
# HEALTH & STATUS ENDPOINTS
# ============================================================================

@router.get("/health")
async def health_check(db: DatabaseManager = Depends(get_db_manager)):
    """Check API and database health"""
    try:
        is_healthy = await db.connection.health_check()
        
        if is_healthy:
            return {
                "status": "healthy",
                "database": "connected",
                "timestamp": datetime.utcnow(),
            }
        else:
            raise HTTPException(status_code=503, detail="Database unavailable")
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")


@router.get("/stats")
async def get_stats(db: DatabaseManager = Depends(get_db_manager)):
    """Get dashboard statistics"""
    try:
        stats = await db.get_dashboard_stats()
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")


# ============================================================================
# GROUP ENDPOINTS
# ============================================================================

@router.post("/groups", response_model=Dict[str, Any])
async def create_group(
    group: GroupBase,
    db: DatabaseManager = Depends(get_db_manager)
):
    """Create a new group"""
    try:
        group_id = await db.create_group(group.dict())
        
        if not group_id:
            raise HTTPException(status_code=409, detail="Group already exists")
        
        return {
            "success": True,
            "id": group_id,
            "message": f"Group {group.group_name} created successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating group: {e}")
        raise HTTPException(status_code=500, detail="Failed to create group")


@router.get("/groups", response_model=Dict[str, Any])
async def list_groups(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    active_only: bool = Query(True),
    db: DatabaseManager = Depends(get_db_manager)
):
    """Get all groups with pagination"""
    try:
        result = await db.get_all_groups(
            active_only=active_only,
            page=page,
            per_page=per_page
        )
        
        return {
            "success": True,
            "data": result['items'],
            "pagination": {
                "page": result['page'],
                "per_page": result['per_page'],
                "total": result['total'],
                "pages": result['pages']
            }
        }
    except Exception as e:
        logger.error(f"Error listing groups: {e}")
        raise HTTPException(status_code=500, detail="Failed to list groups")


@router.get("/groups/{group_id}", response_model=Dict[str, Any])
async def get_group(
    group_id: int,
    db: DatabaseManager = Depends(get_db_manager)
):
    """Get a specific group"""
    try:
        group = await db.get_group(group_id)
        
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        
        return {
            "success": True,
            "data": group
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting group: {e}")
        raise HTTPException(status_code=500, detail="Failed to get group")


@router.put("/groups/{group_id}", response_model=Dict[str, Any])
async def update_group(
    group_id: int,
    updates: Dict[str, Any] = Body(...),
    db: DatabaseManager = Depends(get_db_manager)
):
    """Update a group"""
    try:
        # Remove protected fields
        protected_fields = {'group_id', 'created_at', '_id'}
        for field in protected_fields:
            updates.pop(field, None)
        
        success = await db.update_group(group_id, updates)
        
        if not success:
            raise HTTPException(status_code=404, detail="Group not found")
        
        return {
            "success": True,
            "message": "Group updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating group: {e}")
        raise HTTPException(status_code=500, detail="Failed to update group")


@router.delete("/groups/{group_id}", response_model=Dict[str, Any])
async def delete_group(
    group_id: int,
    db: DatabaseManager = Depends(get_db_manager)
):
    """Delete (soft delete) a group"""
    try:
        success = await db.delete_group(group_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Group not found")
        
        return {
            "success": True,
            "message": "Group deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting group: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete group")


@router.get("/groups/{group_id}/stats", response_model=Dict[str, Any])
async def get_group_stats(
    group_id: int,
    db: DatabaseManager = Depends(get_db_manager)
):
    """Get statistics for a group"""
    try:
        stats = await db.get_group_stats(group_id)
        
        if not stats:
            raise HTTPException(status_code=404, detail="Group not found")
        
        return {
            "success": True,
            "data": stats
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting group stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")


# ============================================================================
# USER ENDPOINTS
# ============================================================================

@router.post("/users", response_model=Dict[str, Any])
async def create_user(
    user: UserBase,
    db: DatabaseManager = Depends(get_db_manager)
):
    """Create a new user"""
    try:
        user_id = await db.create_user(user.dict())
        
        if not user_id:
            raise HTTPException(status_code=409, detail="User already exists")
        
        return {
            "success": True,
            "id": user_id,
            "message": f"User {user.username} created successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail="Failed to create user")


@router.get("/users/{user_id}", response_model=Dict[str, Any])
async def get_user(
    user_id: int,
    db: DatabaseManager = Depends(get_db_manager)
):
    """Get a specific user"""
    try:
        user = await db.get_user(user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "success": True,
            "data": user
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user")


@router.get("/users/username/{username}", response_model=Dict[str, Any])
async def get_user_by_username(
    username: str,
    db: DatabaseManager = Depends(get_db_manager)
):
    """Get user by username"""
    try:
        user = await db.get_user_by_username(username)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "success": True,
            "data": user
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user")


# ============================================================================
# ACTION ENDPOINTS
# ============================================================================

@router.post("/actions", response_model=Dict[str, Any])
async def create_action(
    action: ActionBase,
    db: DatabaseManager = Depends(get_db_manager)
):
    """Create a new action"""
    try:
        action_id = await db.create_action(action.dict())
        
        return {
            "success": True,
            "id": action_id,
            "message": "Action created successfully"
        }
    except Exception as e:
        logger.error(f"Error creating action: {e}")
        raise HTTPException(status_code=500, detail="Failed to create action")


@router.get("/actions/group/{group_id}", response_model=Dict[str, Any])
async def get_group_actions(
    group_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    db: DatabaseManager = Depends(get_db_manager)
):
    """Get actions for a group"""
    try:
        result = await db.get_group_actions(
            group_id=group_id,
            page=page,
            per_page=per_page
        )
        
        return {
            "success": True,
            "data": result['items'],
            "pagination": {
                "page": result['page'],
                "per_page": result['per_page'],
                "total": result['total'],
                "pages": result['pages']
            }
        }
    except Exception as e:
        logger.error(f"Error getting actions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get actions")


@router.get("/actions/user/{user_id}", response_model=Dict[str, Any])
async def get_user_actions(
    user_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    db: DatabaseManager = Depends(get_db_manager)
):
    """Get actions by a user"""
    try:
        result = await db.get_user_actions(
            user_id=user_id,
            page=page,
            per_page=per_page
        )
        
        return {
            "success": True,
            "data": result['items'],
            "pagination": {
                "page": result['page'],
                "per_page": result['per_page'],
                "total": result['total'],
                "pages": result['pages']
            }
        }
    except Exception as e:
        logger.error(f"Error getting user actions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get actions")


# ============================================================================
# BULK OPERATIONS ENDPOINTS
# ============================================================================

@router.post("/bulk/groups", response_model=Dict[str, Any])
async def bulk_create_groups(
    groups: List[GroupBase],
    db: DatabaseManager = Depends(get_db_manager)
):
    """Bulk create groups"""
    try:
        result = await db.bulk_insert_groups([g.dict() for g in groups])
        
        return {
            "success": True,
            "inserted": result['inserted'],
            "failed": result['failed'],
            "message": f"Bulk insertion complete: {result['inserted']} inserted, {result['failed']} failed"
        }
    except Exception as e:
        logger.error(f"Error in bulk insert: {e}")
        raise HTTPException(status_code=500, detail="Bulk operation failed")


@router.put("/bulk/groups/stats", response_model=Dict[str, Any])
async def bulk_update_stats(
    updates: List[Dict[str, Any]] = Body(...),
    db: DatabaseManager = Depends(get_db_manager)
):
    """Bulk update group statistics"""
    try:
        # Convert updates to list of tuples
        update_tuples = [
            (u['group_id'], {k: v for k, v in u.items() if k != 'group_id'})
            for u in updates
        ]
        
        result = await db.bulk_update_stats(update_tuples)
        
        return {
            "success": True,
            "modified": result['modified'],
            "message": f"Updated {result['modified']} groups"
        }
    except Exception as e:
        logger.error(f"Error in bulk update: {e}")
        raise HTTPException(status_code=500, detail="Bulk operation failed")


# ============================================================================
# CLEANUP ENDPOINTS
# ============================================================================

@router.post("/maintenance/cleanup-logs", response_model=Dict[str, Any])
async def cleanup_old_logs(
    days: int = Query(30, ge=1),
    db: DatabaseManager = Depends(get_db_manager)
):
    """Clean up old logs"""
    try:
        deleted = await db.cleanup_old_logs(days)
        
        return {
            "success": True,
            "deleted": deleted,
            "message": f"Cleaned up {deleted} logs older than {days} days"
        }
    except Exception as e:
        logger.error(f"Error cleaning up logs: {e}")
        raise HTTPException(status_code=500, detail="Cleanup failed")
