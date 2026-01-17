"""
Advanced API Routes for Settings, Members, Admins, Roles, History, and Events
Provides complete REST API for bot management
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
import logging
from bson import ObjectId
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/advanced", tags=["advanced"])


def _sanitize_value(v):
    """Convert BSON types to JSON-serializable Python types."""
    if isinstance(v, ObjectId):
        return str(v)
    if isinstance(v, datetime):
        return v.isoformat()
    return v


def sanitize_doc(doc):
    """Recursively sanitize a document returned from MongoDB."""
    if doc is None:
        return None
    if isinstance(doc, list):
        return [sanitize_doc(x) for x in doc]
    if not isinstance(doc, dict):
        return _sanitize_value(doc)

    out = {}
    for k, v in doc.items():
        if isinstance(v, dict) or isinstance(v, list):
            out[k] = sanitize_doc(v)
        else:
            out[k] = _sanitize_value(v)
    # drop internal _id if present (we already converted it above)
    out.pop("_id", None)
    return out


# ============================================================================
# SETTINGS ENDPOINTS
# ============================================================================

@router.get("/settings/{group_id}")
async def get_group_settings(group_id: int):
    """Get group settings"""
    try:
        from ..db.advanced_db import AdvancedDBService
        from .routes import get_db
        
        db_service = AdvancedDBService(get_db())
        settings = await db_service.get_group_settings(group_id)

        if not settings:
            # Create default settings
            settings = await db_service.create_group_settings(group_id, f"Group {group_id}")

        return {
            "success": True,
            "data": sanitize_doc(settings)
        }
    except Exception as e:
        logger.error(f"Error getting settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/settings/{group_id}/update")
async def update_group_settings(group_id: int, updates: Dict[str, Any]):
    """Update group settings"""
    try:
        from ..db.advanced_db import AdvancedDBService
        from .routes import get_db
        
        db_service = AdvancedDBService(get_db())
        result = await db_service.update_group_settings(group_id, updates)

        if not result:
            raise HTTPException(status_code=404, detail="Group settings not found")

        return {
            "success": True,
            "data": sanitize_doc(result),
            "message": "Settings updated successfully"
        }
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/settings/{group_id}/toggle-feature")
async def toggle_feature(group_id: int, feature: str, enabled: bool):
    """Toggle a feature on/off"""
    try:
        from ..db.advanced_db import AdvancedDBService
        from .routes import get_db
        
        db_service = AdvancedDBService(get_db())
        result = await db_service.toggle_feature(group_id, feature, enabled)
        
        if not result:
            raise HTTPException(status_code=404, detail="Group settings not found")
        
        return {
            "success": True,
            "message": f"Feature '{feature}' is now {'enabled' if enabled else 'disabled'}"
        }
    except Exception as e:
        logger.error(f"Error toggling feature: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MEMBERS ENDPOINTS
# ============================================================================

@router.get("/members/{group_id}/{user_id}")
async def get_member(group_id: int, user_id: int):
    """Get member info"""
    try:
        from ..db.advanced_db import AdvancedDBService
        from .routes import get_db
        
        db_service = AdvancedDBService(get_db())
        member = await db_service.get_member(group_id, user_id)

        if not member:
            # Create new member record
            member = await db_service.create_member(group_id, user_id)

        return {
            "success": True,
            "data": sanitize_doc(member)
        }
    except Exception as e:
        logger.error(f"Error getting member: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/members/{group_id}")
async def get_group_members(group_id: int, active_only: bool = True):
    """Get all members of a group"""
    try:
        from ..db.advanced_db import AdvancedDBService
        from .routes import get_db
        
        db_service = AdvancedDBService(get_db())
        members = await db_service.get_group_members(group_id, active_only)

        return {
            "success": True,
            "data": sanitize_doc(members),
            "count": len(members)
        }
    except Exception as e:
        logger.error(f"Error getting members: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/members/{group_id}/{user_id}/update")
async def update_member(group_id: int, user_id: int, updates: Dict[str, Any]):
    """Update member info"""
    try:
        from ..db.advanced_db import AdvancedDBService
        from .routes import get_db
        
        db_service = AdvancedDBService(get_db())
        result = await db_service.update_member(group_id, user_id, updates)
        
        if not result:
            raise HTTPException(status_code=404, detail="Member not found")
        
        return {
            "success": True,
            "message": "Member updated successfully"
        }
    except Exception as e:
        logger.error(f"Error updating member: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ADMINS ENDPOINTS
# ============================================================================

@router.get("/admins/{group_id}/{user_id}")
async def get_admin(group_id: int, user_id: int):
    """Get admin info"""
    try:
        from ..db.advanced_db import AdvancedDBService
        from .routes import get_db
        
        db_service = AdvancedDBService(get_db())
        admin = await db_service.get_admin(group_id, user_id)

        if not admin:
            raise HTTPException(status_code=404, detail="Admin not found")

        return {
            "success": True,
            "data": sanitize_doc(admin)
        }
    except Exception as e:
        logger.error(f"Error getting admin: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admins/{group_id}")
async def get_group_admins(group_id: int):
    """Get all admins of a group"""
    try:
        from ..db.advanced_db import AdvancedDBService
        from .routes import get_db
        
        db_service = AdvancedDBService(get_db())
        admins = await db_service.get_group_admins(group_id)

        return {
            "success": True,
            "data": sanitize_doc(admins),
            "count": len(admins)
        }
    except Exception as e:
        logger.error(f"Error getting admins: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admins/{group_id}/add")
async def add_admin(
    group_id: int,
    user_id: int,
    username: Optional[str] = None,
    role: str = "admin"
):
    """Add new admin"""
    try:
        from ..db.advanced_db import AdvancedDBService
        from .routes import get_db
        
        db_service = AdvancedDBService(get_db())
        admin = await db_service.add_admin(group_id, user_id, username, role)
        
        return {
            "success": True,
            "data": admin,
            "message": f"User {user_id} added as {role}"
        }
    except Exception as e:
        logger.error(f"Error adding admin: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admins/{group_id}/{user_id}/remove")
async def remove_admin(group_id: int, user_id: int):
    """Remove admin"""
    try:
        from ..db.advanced_db import AdvancedDBService
        from .routes import get_db
        
        db_service = AdvancedDBService(get_db())
        result = await db_service.remove_admin(group_id, user_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Admin not found")
        
        return {
            "success": True,
            "message": f"Admin {user_id} removed"
        }
    except Exception as e:
        logger.error(f"Error removing admin: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ROLES ENDPOINTS
# ============================================================================

@router.get("/roles/{group_id}")
async def get_group_roles(group_id: int):
    """Get all roles in a group"""
    try:
        from ..db.advanced_db import AdvancedDBService
        from .routes import get_db
        
        db_service = AdvancedDBService(get_db())
        roles = await db_service.get_group_roles(group_id)

        return {
            "success": True,
            "data": sanitize_doc(roles),
            "count": len(roles)
        }
    except Exception as e:
        logger.error(f"Error getting roles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/roles/{group_id}/create")
async def create_role(
    group_id: int,
    role_name: str,
    role_type: str,
    permissions: Dict[str, bool]
):
    """Create new moderation role"""
    try:
        from ..db.advanced_db import AdvancedDBService
        from .routes import get_db
        
        db_service = AdvancedDBService(get_db())
        role = await db_service.create_role(group_id, role_name, role_type, permissions=permissions)
        
        return {
            "success": True,
            "data": role,
            "message": f"Role '{role_name}' created"
        }
    except Exception as e:
        logger.error(f"Error creating role: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# COMMAND HISTORY ENDPOINTS
# ============================================================================

@router.post("/history/log-command")
async def log_command(
    group_id: int,
    user_id: int,
    command: str,
    args: Optional[str] = None,
    status: str = "success",
    result: Optional[str] = None
):
    """Log command execution"""
    try:
        from ..db.advanced_db import AdvancedDBService
        from .routes import get_db
        
        db_service = AdvancedDBService(get_db())
        success = await db_service.log_command(group_id, user_id, command, args, status, result)

        return {
            "success": success,
            "message": "Command logged" if success else "Failed to log command"
        }
    except Exception as e:
        logger.error(f"Error logging command: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{group_id}")
async def get_command_history(group_id: int, limit: int = Query(100, le=1000)):
    """Get command history"""
    try:
        from ..db.advanced_db import AdvancedDBService
        from .routes import get_db
        
        db_service = AdvancedDBService(get_db())
        history = await db_service.get_command_history(group_id, limit)

        return {
            "success": True,
            "data": sanitize_doc(history),
            "count": len(history)
        }
    except Exception as e:
        logger.error(f"Error getting history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# EVENT LOGS ENDPOINTS
# ============================================================================

@router.post("/events/log")
async def log_event(
    group_id: int,
    event_type: str,
    user_id: int,
    triggered_by: Optional[int] = None,
    target_user_id: Optional[int] = None,
    event_data: Optional[Dict[str, Any]] = None
):
    """Log event"""
    try:
        from ..db.advanced_db import AdvancedDBService
        from .routes import get_db
        
        db_service = AdvancedDBService(get_db())
        success = await db_service.log_event(
            group_id, event_type, user_id, triggered_by, target_user_id, event_data
        )

        return {
            "success": success,
            "message": "Event logged" if success else "Failed to log event"
        }
    except Exception as e:
        logger.error(f"Error logging event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events/{group_id}")
async def get_event_logs(
    group_id: int,
    event_type: Optional[str] = None,
    limit: int = Query(100, le=1000)
):
    """Get event logs"""
    try:
        from ..db.advanced_db import AdvancedDBService
        from .routes import get_db
        
        db_service = AdvancedDBService(get_db())
        logs = await db_service.get_event_logs(group_id, event_type, limit)

        return {
            "success": True,
            "data": sanitize_doc(logs),
            "count": len(logs)
        }
    except Exception as e:
        logger.error(f"Error getting events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# STATISTICS ENDPOINTS
# ============================================================================

@router.get("/statistics/{group_id}")
async def get_statistics(group_id: int):
    """Get group statistics"""
    try:
        from ..db.advanced_db import AdvancedDBService
        from .routes import get_db
        
        db_service = AdvancedDBService(get_db())
        stats = await db_service.get_group_statistics(group_id)

        if not stats:
            stats = await db_service.create_statistics(group_id)

        return {
            "success": True,
            "data": sanitize_doc(stats)
        }
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/statistics/{group_id}/update")
async def update_statistics(group_id: int, updates: Dict[str, Any]):
    """Update statistics"""
    try:
        from ..db.advanced_db import AdvancedDBService
        from .routes import get_db
        
        db_service = AdvancedDBService(get_db())
        result = await db_service.update_statistics(group_id, updates)
        
        if not result:
            raise HTTPException(status_code=404, detail="Statistics not found")
        
        return {
            "success": True,
            "message": "Statistics updated"
        }
    except Exception as e:
        logger.error(f"Error updating statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
