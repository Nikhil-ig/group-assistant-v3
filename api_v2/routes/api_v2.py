"""
API V2 Routes - Professional REST API for all operations
"""

import uuid
import logging
import os
from pymongo import MongoClient
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query, Depends, Body
from typing import List, Dict, Any

from api_v2.models.schemas import *
from api_v2.services.business_logic import *
from api_v2.core.database import get_db_manager


# Database connection
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
client = MongoClient(MONGODB_URL)

router = APIRouter(prefix="/api/v2", tags=["api-v2"])

# Lazy-loaded services - initialized on first use
_group_service = None
_role_service = None
_rule_service = None
_settings_service = None
_action_service = None


def get_group_service() -> GroupService:
    global _group_service
    if _group_service is None:
        _group_service = GroupService()
    return _group_service


def get_role_service() -> RoleService:
    global _role_service
    if _role_service is None:
        _role_service = RoleService()
    return _role_service


def get_rule_service() -> RuleService:
    global _rule_service
    if _rule_service is None:
        _rule_service = RuleService()
    return _rule_service


def get_settings_service() -> SettingsService:
    global _settings_service
    if _settings_service is None:
        _settings_service = SettingsService()
    return _settings_service


def get_action_service() -> ActionService:
    global _action_service
    if _action_service is None:
        _action_service = ActionService()
    return _action_service


# ============================================================================
# HEALTH & STATUS
# ============================================================================

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "api-v2",
        "version": "2.0.0"
    }


# ============================================================================
# GROUP ENDPOINTS
# ============================================================================

@router.post("/groups", response_model=Dict[str, Any])
async def create_group(group: GroupCreate):
    """Create a new group"""
    try:
        group_service = get_group_service()
        result = await group_service.create_group(group)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/groups/{group_id}", response_model=Dict[str, Any])
async def get_group(group_id: int):
    """Get a group by ID"""
    try:
        group_service = get_group_service()
        result = await group_service.get_group(group_id)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/groups/{group_id}", response_model=Dict[str, Any])
async def update_group(group_id: int, group: GroupUpdate):
    """Update a group"""
    try:
        group_service = get_group_service()
        result = await group_service.update_group(group_id, group)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/groups/{group_id}/stats", response_model=Dict[str, Any])
async def get_group_stats(group_id: int, days: int = 7):
    """Get group statistics for the last N days"""
    try:
        # Access database directly
        db = client["group_assistant"]
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=min(max(days, 1), 365))
        
        # Get message count
        messages = db["messages"].count_documents({
            "group_id": group_id,
            "created_at": {"$gte": start_date, "$lte": end_date}
        })
        
        # Get active users
        active_users = len(db["messages"].distinct("user_id", {
            "group_id": group_id,
            "created_at": {"$gte": start_date, "$lte": end_date}
        }))
        
        # Get admin actions count
        actions = db["actions"].count_documents({
            "group_id": group_id,
            "created_at": {"$gte": start_date, "$lte": end_date}
        })
        
        # Get most active user
        pipeline = [
            {"$match": {
                "group_id": group_id,
                "created_at": {"$gte": start_date, "$lte": end_date}
            }},
            {"$group": {
                "_id": "$user_id",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}},
            {"$limit": 1}
        ]
        most_active = list(db["messages"].aggregate(pipeline))
        
        return {
            "success": True,
            "data": {
                "group_id": group_id,
                "period_days": days,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_messages": messages,
                "active_users": active_users,
                "admin_actions": actions,
                "most_active_user": most_active[0]["_id"] if most_active else None,
                "most_active_count": most_active[0]["count"] if most_active else 0
            }
        }
    except Exception as e:
        logger.error(f"Get group stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ROLE ENDPOINTS
# ============================================================================

@router.post("/groups/{group_id}/roles", response_model=Dict[str, Any])
async def create_role(group_id: int, role: RoleCreate):
    """Create a new role"""
    try:
        role_service = get_role_service()
        result = await role_service.create_role(group_id, role)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/groups/{group_id}/roles", response_model=Dict[str, Any])
async def list_roles(group_id: int):
    """List roles for a group"""
    try:
        role_service = get_role_service()
        result = await role_service.list_roles(group_id)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/groups/{group_id}/roles/{role_name}", response_model=Dict[str, Any])
async def get_role(group_id: int, role_name: str):
    """Get a role by name"""
    try:
        role_service = get_role_service()
        result = await role_service.get_role(group_id, role_name)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# RULE ENDPOINTS
# ============================================================================

@router.post("/groups/{group_id}/rules", response_model=Dict[str, Any])
async def create_rule(group_id: int, rule: RuleCreate):
    """Create a new rule"""
    try:
        rule_service = get_rule_service()
        result = await rule_service.create_rule(group_id, rule)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/groups/{group_id}/rules", response_model=Dict[str, Any])
async def get_rules(group_id: int):
    """Get rules for a group"""
    try:
        rule_service = get_rule_service()
        result = await rule_service.get_rules(group_id)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SETTINGS ENDPOINTS
# ============================================================================

@router.get("/groups/{group_id}/settings", response_model=Dict[str, Any])
async def get_settings(group_id: int):
    """Get settings for a group"""
    try:
        settings_service = get_settings_service()
        result = await settings_service.get_group_settings(group_id)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Settings endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/groups/{group_id}/settings", response_model=Dict[str, Any])
async def update_settings(group_id: int, settings: SettingsUpdate):
    """Update settings for a group"""
    try:
        settings_service = get_settings_service()
        result = await settings_service.update_settings(group_id, settings)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ACTION ENDPOINTS
# ============================================================================

@router.post("/groups/{group_id}/actions", response_model=Dict[str, Any])
async def log_action(group_id: int, action: ActionCreate):
    """Log an action"""
    try:
        action.group_id = group_id
        result = await get_action_service().log_action(action)
        return {
            "success": True,
            "data": result,
            "message": "Action logged"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/groups/{group_id}/actions", response_model=Dict[str, Any])
async def get_group_actions(
    group_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100)
):
    """Get actions for group"""
    try:
        result = await get_action_service().get_group_actions(group_id, page, per_page)
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/groups/{group_id}/users/{user_id}/stats", response_model=Dict[str, Any])
async def get_user_stats(group_id: int, user_id: int):
    """Get user statistics in group"""
    try:
        stats = await get_action_service().get_user_statistics(group_id, user_id)
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


