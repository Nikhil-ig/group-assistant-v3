"""
Dashboard API Endpoints
Provides data for the web dashboard: groups, users, actions stats
"""

from fastapi import APIRouter, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional, List
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from pathlib import Path
from pydantic import BaseModel

# Load environment variables
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "bot_manager")

# Initialize router
router = APIRouter(prefix="/api", tags=["dashboard"])

# Global database instance
_db: Optional[AsyncIOMotorDatabase] = None


def set_database(db: AsyncIOMotorDatabase):
    """Set the database instance"""
    global _db
    _db = db


def get_database() -> AsyncIOMotorDatabase:
    """Get the database instance"""
    global _db
    if _db is None:
        raise HTTPException(status_code=503, detail="Database not initialized")
    return _db


# ============================================================================
# MODELS
# ============================================================================

class GroupResponse(BaseModel):
    """Group data response"""
    group_id: int
    group_name: str
    description: Optional[str] = None
    member_count: int
    admin_count: int
    created_at: datetime
    is_active: bool


class UserResponse(BaseModel):
    """User data response"""
    user_id: int
    username: str
    first_name: str
    last_name: str
    role: str
    email: str
    managed_groups: List[int]
    is_active: bool


class ActionResponse(BaseModel):
    """Action log response"""
    action_id: str
    action_type: str
    group_id: int
    target_username: str
    reason: Optional[str] = None
    status: str
    created_at: datetime


class DashboardStats(BaseModel):
    """Dashboard statistics"""
    total_groups: int
    total_members: int
    total_admins: int
    total_actions: int
    active_users: int
    actions_today: int
    actions_this_week: int


# ============================================================================
# DASHBOARD ENDPOINTS
# ============================================================================

@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    """Get dashboard statistics"""
    db = get_database()
    
    try:
        groups_col = db["groups"]
        users_col = db["users"]
        actions_col = db["actions"]
        
        # Count documents
        total_groups = await groups_col.count_documents({})
        total_users = await users_col.count_documents({})
        total_actions = await actions_col.count_documents({})
        
        # Calculate stats
        total_members = 0
        total_admins = 0
        async for group in groups_col.find({}):
            total_members += group.get("member_count", 0)
            total_admins += group.get("admin_count", 0)
        
        # Active users count
        active_users = await users_col.count_documents({"is_active": True})
        
        # Actions today and this week
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = now - timedelta(days=7)
        
        actions_today = await actions_col.count_documents({
            "created_at": {"$gte": today_start}
        })
        
        actions_this_week = await actions_col.count_documents({
            "created_at": {"$gte": week_start}
        })
        
        return DashboardStats(
            total_groups=total_groups,
            total_members=total_members,
            total_admins=total_admins,
            total_actions=total_actions,
            active_users=active_users,
            actions_today=actions_today,
            actions_this_week=actions_this_week,
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/groups", response_model=List[GroupResponse])
async def get_groups(skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100)):
    """Get list of groups with pagination"""
    db = get_database()
    
    try:
        groups_col = db["groups"]
        groups = await groups_col.find({}).skip(skip).limit(limit).to_list(limit)
        
        return [
            GroupResponse(
                group_id=g["group_id"],
                group_name=g["group_name"],
                description=g.get("description"),
                member_count=g["member_count"],
                admin_count=g["admin_count"],
                created_at=g["created_at"],
                is_active=g.get("is_active", True),
            )
            for g in groups
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/groups/{group_id}", response_model=GroupResponse)
async def get_group(group_id: int):
    """Get specific group details"""
    db = get_database()
    
    try:
        groups_col = db["groups"]
        group = await groups_col.find_one({"group_id": group_id})
        
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        
        return GroupResponse(
            group_id=group["group_id"],
            group_name=group["group_name"],
            description=group.get("description"),
            member_count=group["member_count"],
            admin_count=group["admin_count"],
            created_at=group["created_at"],
            is_active=group.get("is_active", True),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users", response_model=List[UserResponse])
async def get_users(skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100)):
    """Get list of users with pagination"""
    db = get_database()
    
    try:
        users_col = db["users"]
        users = await users_col.find({}).skip(skip).limit(limit).to_list(limit)
        
        return [
            UserResponse(
                user_id=u["user_id"],
                username=u["username"],
                first_name=u["first_name"],
                last_name=u["last_name"],
                role=u["role"],
                email=u["email"],
                managed_groups=u.get("managed_groups", []),
                is_active=u.get("is_active", True),
            )
            for u in users
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/actions", response_model=List[ActionResponse])
async def get_actions(
    group_id: Optional[int] = Query(None),
    action_type: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    """Get list of actions with filtering and pagination"""
    db = get_database()
    
    try:
        actions_col = db["actions"]
        
        # Build filter
        filter_dict = {}
        if group_id:
            filter_dict["group_id"] = group_id
        if action_type:
            filter_dict["action_type"] = action_type
        
        actions = await actions_col.find(filter_dict).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
        
        return [
            ActionResponse(
                action_id=a["action_id"],
                action_type=a["action_type"],
                group_id=a["group_id"],
                target_username=a.get("target_username", "Unknown"),
                reason=a.get("reason"),
                status=a.get("status", "pending"),
                created_at=a["created_at"],
            )
            for a in actions
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/actions/recent", response_model=List[ActionResponse])
async def get_recent_actions(limit: int = Query(10, ge=1, le=50)):
    """Get recent actions"""
    db = get_database()
    
    try:
        actions_col = db["actions"]
        actions = await actions_col.find({}).sort("created_at", -1).limit(limit).to_list(limit)
        
        return [
            ActionResponse(
                action_id=a["action_id"],
                action_type=a["action_type"],
                group_id=a["group_id"],
                target_username=a.get("target_username", "Unknown"),
                reason=a.get("reason"),
                status=a.get("status", "pending"),
                created_at=a["created_at"],
            )
            for a in actions
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    db = get_database()
    
    try:
        # Try to access database
        await db["groups"].count_documents({})
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow(),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow(),
        }
