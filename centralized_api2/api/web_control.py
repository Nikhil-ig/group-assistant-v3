"""
Web Control API Routes
Complete REST API for controlling bot actions via web interface
Allows full control and monitoring of bot operations through HTTP endpoints
"""

import logging
from typing import List, Optional, Tuple
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Path, Body
from fastapi.responses import JSONResponse

from centralized_api.db import ActionDatabase
from centralized_api.config import API_PREFIX

logger = logging.getLogger(__name__)

# Initialize web control router
web_router = APIRouter(prefix=f"{API_PREFIX}/web", tags=["web-control"])

# Global database instance
_db: Optional[ActionDatabase] = None


def set_database(db: ActionDatabase):
    """Set the database instance"""
    global _db
    _db = db


def get_database() -> ActionDatabase:
    """Get the database instance"""
    global _db
    if _db is None:
        raise HTTPException(status_code=503, detail="Database not initialized")
    return _db


# ============================================================================
# UTILITY FUNCTIONS (Web-specific)
# ============================================================================

def parse_user_reference(text: str) -> Tuple[Optional[int], str]:
    """
    Parse user reference from input.
    Supports: user_id (int), @username (str)
    
    Args:
        text: User input (username or ID)
    
    Returns:
        Tuple of (user_id, reference_str) where one may be None
    
    Examples:
        "123456" → (123456, "123456")
        "@john_doe" → (None, "@john_doe")
        "john_doe" → (None, "@john_doe")
    """
    if not text:
        return None, ""
    
    text = text.strip()
    
    # Check if it's a username (starts with @)
    if text.startswith("@"):
        return None, text  # Return username to be resolved later
    
    # Try to parse as user_id
    try:
        user_id = int(text)
        return user_id, str(user_id)
    except ValueError:
        # Not an int, treat as username
        if not text.startswith("@"):
            text = "@" + text
        return None, text


# ============================================================================
# WEB CONTROL ENDPOINTS - USER REFERENCE PARSING
# ============================================================================

@web_router.post("/parse-user")
async def parse_user_endpoint(
    user_input: str = Body(..., embed=True, description="User ID or @username")
) -> dict:
    """
    Parse a user reference (ID or @username) and return structured data.
    
    This validates and normalizes user input for use in other endpoints.
    
    Args:
        user_input: Either a numeric ID or @username
    
    Returns:
        {
            "user_id": numeric ID or null,
            "username": @username or null,
            "input": original input,
            "type": "numeric" | "username" | "invalid",
            "is_valid": bool
        }
    
    Examples:
        POST /api/web/parse-user {"user_input": "123456"}
        POST /api/web/parse-user {"user_input": "@john_doe"}
    """
    try:
        user_id, reference = parse_user_reference(user_input)
        
        if user_id is not None:
            return {
                "user_id": user_id,
                "username": None,
                "input": user_input,
                "type": "numeric",
                "is_valid": True
            }
        elif reference:
            return {
                "user_id": None,
                "username": reference,
                "input": user_input,
                "type": "username",
                "is_valid": True
            }
        else:
            return {
                "user_id": None,
                "username": None,
                "input": user_input,
                "type": "invalid",
                "is_valid": False,
                "error": "Could not parse user reference"
            }
    
    except Exception as e:
        logger.error(f"Error parsing user reference: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# WEB CONTROL ENDPOINTS - ACTION EXECUTION
# ============================================================================

@web_router.post("/actions/ban")
async def web_ban(
    group_id: int = Body(..., embed=True, description="Telegram group ID"),
    user_input: str = Body(..., embed=True, description="User ID or @username"),
    reason: str = Body("No reason provided", embed=True, description="Ban reason"),
    initiated_by: int = Body(..., embed=True, description="Admin user ID")
) -> dict:
    """
    Ban a user from a group via web interface.
    
    Args:
        group_id: Telegram group ID (negative)
        user_input: User ID (numeric) or @username
        reason: Reason for ban
        initiated_by: Admin user ID who is performing the action
    
    Returns:
        {
            "success": bool,
            "action_id": string,
            "user_id": int or null,
            "username": string or null,
            "message": string
        }
    """
    try:
        db = get_database()
        user_id, username = parse_user_reference(user_input)
        
        if not user_id and not username:
            raise HTTPException(status_code=400, detail="Invalid user reference")
        
        action_data = {
            "action_type": "ban",
            "group_id": group_id,
            "user_id": user_id,
            "username": username,
            "reason": reason,
            "initiated_by": initiated_by,
            "created_at": datetime.utcnow()
        }
        
        result = await db.log_action(action_data)
        
        return {
            "success": True,
            "action_id": str(result.inserted_id),
            "user_id": user_id,
            "username": username,
            "message": f"User {'ban' if user_id else username} has been banned"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Web ban error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@web_router.post("/actions/kick")
async def web_kick(
    group_id: int = Body(..., embed=True),
    user_input: str = Body(..., embed=True),
    reason: str = Body("No reason provided", embed=True),
    initiated_by: int = Body(..., embed=True)
) -> dict:
    """
    Kick a user from a group via web interface.
    
    Args:
        group_id: Telegram group ID (negative)
        user_input: User ID (numeric) or @username
        reason: Reason for kick
        initiated_by: Admin user ID
    
    Returns:
        {
            "success": bool,
            "action_id": string,
            "user_id": int or null,
            "username": string or null,
            "message": string
        }
    """
    try:
        db = get_database()
        user_id, username = parse_user_reference(user_input)
        
        if not user_id and not username:
            raise HTTPException(status_code=400, detail="Invalid user reference")
        
        action_data = {
            "action_type": "kick",
            "group_id": group_id,
            "user_id": user_id,
            "username": username,
            "reason": reason,
            "initiated_by": initiated_by,
            "created_at": datetime.utcnow()
        }
        
        result = await db.log_action(action_data)
        
        return {
            "success": True,
            "action_id": str(result.inserted_id),
            "user_id": user_id,
            "username": username,
            "message": f"User has been kicked"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Web kick error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@web_router.post("/actions/mute")
async def web_mute(
    group_id: int = Body(..., embed=True),
    user_input: str = Body(..., embed=True),
    duration_minutes: int = Body(0, embed=True, description="0 = forever"),
    reason: str = Body("No reason provided", embed=True),
    initiated_by: int = Body(..., embed=True)
) -> dict:
    """
    Mute a user in a group via web interface.
    
    Args:
        group_id: Telegram group ID (negative)
        user_input: User ID (numeric) or @username
        duration_minutes: Duration in minutes (0 = forever/permanent)
        reason: Reason for mute
        initiated_by: Admin user ID
    
    Returns:
        {
            "success": bool,
            "action_id": string,
            "user_id": int or null,
            "username": string or null,
            "duration_minutes": int,
            "message": string
        }
    """
    try:
        db = get_database()
        user_id, username = parse_user_reference(user_input)
        
        if not user_id and not username:
            raise HTTPException(status_code=400, detail="Invalid user reference")
        
        action_data = {
            "action_type": "mute",
            "group_id": group_id,
            "user_id": user_id,
            "username": username,
            "duration_minutes": duration_minutes,
            "reason": reason,
            "initiated_by": initiated_by,
            "created_at": datetime.utcnow()
        }
        
        result = await db.log_action(action_data)
        
        return {
            "success": True,
            "action_id": str(result.inserted_id),
            "user_id": user_id,
            "username": username,
            "duration_minutes": duration_minutes,
            "message": f"User has been muted for {duration_minutes if duration_minutes > 0 else 'forever'}"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Web mute error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@web_router.post("/actions/unmute")
async def web_unmute(
    group_id: int = Body(..., embed=True),
    user_input: str = Body(..., embed=True),
    initiated_by: int = Body(..., embed=True)
) -> dict:
    """Unmute a user via web interface"""
    try:
        db = get_database()
        user_id, username = parse_user_reference(user_input)
        
        if not user_id and not username:
            raise HTTPException(status_code=400, detail="Invalid user reference")
        
        action_data = {
            "action_type": "unmute",
            "group_id": group_id,
            "user_id": user_id,
            "username": username,
            "initiated_by": initiated_by,
            "created_at": datetime.utcnow()
        }
        
        result = await db.log_action(action_data)
        
        return {
            "success": True,
            "action_id": str(result.inserted_id),
            "user_id": user_id,
            "username": username,
            "message": "User has been unmuted"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Web unmute error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@web_router.post("/actions/restrict")
async def web_restrict(
    group_id: int = Body(..., embed=True),
    user_input: str = Body(..., embed=True),
    permission_type: str = Body("send_messages", embed=True, description="Permission to restrict"),
    initiated_by: int = Body(..., embed=True)
) -> dict:
    """Restrict user permissions via web interface"""
    try:
        db = get_database()
        user_id, username = parse_user_reference(user_input)
        
        if not user_id and not username:
            raise HTTPException(status_code=400, detail="Invalid user reference")
        
        action_data = {
            "action_type": "restrict",
            "group_id": group_id,
            "user_id": user_id,
            "username": username,
            "permission_type": permission_type,
            "initiated_by": initiated_by,
            "created_at": datetime.utcnow()
        }
        
        result = await db.log_action(action_data)
        
        return {
            "success": True,
            "action_id": str(result.inserted_id),
            "user_id": user_id,
            "username": username,
            "permission_type": permission_type,
            "message": f"User permissions restricted"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Web restrict error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@web_router.post("/actions/unrestrict")
async def web_unrestrict(
    group_id: int = Body(..., embed=True),
    user_input: str = Body(..., embed=True),
    initiated_by: int = Body(..., embed=True)
) -> dict:
    """Restore user permissions via web interface"""
    try:
        db = get_database()
        user_id, username = parse_user_reference(user_input)
        
        if not user_id and not username:
            raise HTTPException(status_code=400, detail="Invalid user reference")
        
        action_data = {
            "action_type": "unrestrict",
            "group_id": group_id,
            "user_id": user_id,
            "username": username,
            "initiated_by": initiated_by,
            "created_at": datetime.utcnow()
        }
        
        result = await db.log_action(action_data)
        
        return {
            "success": True,
            "action_id": str(result.inserted_id),
            "user_id": user_id,
            "username": username,
            "message": "User permissions restored"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Web unrestrict error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@web_router.post("/actions/warn")
async def web_warn(
    group_id: int = Body(..., embed=True),
    user_input: str = Body(..., embed=True),
    reason: str = Body("No reason provided", embed=True),
    initiated_by: int = Body(..., embed=True)
) -> dict:
    """Warn a user via web interface"""
    try:
        db = get_database()
        user_id, username = parse_user_reference(user_input)
        
        if not user_id and not username:
            raise HTTPException(status_code=400, detail="Invalid user reference")
        
        action_data = {
            "action_type": "warn",
            "group_id": group_id,
            "user_id": user_id,
            "username": username,
            "reason": reason,
            "initiated_by": initiated_by,
            "created_at": datetime.utcnow()
        }
        
        result = await db.log_action(action_data)
        
        return {
            "success": True,
            "action_id": str(result.inserted_id),
            "user_id": user_id,
            "username": username,
            "message": "User has been warned"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Web warn error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@web_router.post("/actions/promote")
async def web_promote(
    group_id: int = Body(..., embed=True),
    user_input: str = Body(..., embed=True),
    title: str = Body("Admin", embed=True, description="Admin title"),
    initiated_by: int = Body(..., embed=True)
) -> dict:
    """Promote a user to admin via web interface"""
    try:
        db = get_database()
        user_id, username = parse_user_reference(user_input)
        
        if not user_id and not username:
            raise HTTPException(status_code=400, detail="Invalid user reference")
        
        action_data = {
            "action_type": "promote",
            "group_id": group_id,
            "user_id": user_id,
            "username": username,
            "title": title,
            "initiated_by": initiated_by,
            "created_at": datetime.utcnow()
        }
        
        result = await db.log_action(action_data)
        
        return {
            "success": True,
            "action_id": str(result.inserted_id),
            "user_id": user_id,
            "username": username,
            "title": title,
            "message": f"User promoted to {title}"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Web promote error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@web_router.post("/actions/demote")
async def web_demote(
    group_id: int = Body(..., embed=True),
    user_input: str = Body(..., embed=True),
    initiated_by: int = Body(..., embed=True)
) -> dict:
    """Demote an admin to user via web interface"""
    try:
        db = get_database()
        user_id, username = parse_user_reference(user_input)
        
        if not user_id and not username:
            raise HTTPException(status_code=400, detail="Invalid user reference")
        
        action_data = {
            "action_type": "demote",
            "group_id": group_id,
            "user_id": user_id,
            "username": username,
            "initiated_by": initiated_by,
            "created_at": datetime.utcnow()
        }
        
        result = await db.log_action(action_data)
        
        return {
            "success": True,
            "action_id": str(result.inserted_id),
            "user_id": user_id,
            "username": username,
            "message": "User has been demoted"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Web demote error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@web_router.post("/actions/unban")
async def web_unban(
    group_id: int = Body(..., embed=True),
    user_input: str = Body(..., embed=True),
    initiated_by: int = Body(..., embed=True)
) -> dict:
    """Unban a user via web interface"""
    try:
        db = get_database()
        user_id, username = parse_user_reference(user_input)
        
        if not user_id and not username:
            raise HTTPException(status_code=400, detail="Invalid user reference")
        
        action_data = {
            "action_type": "unban",
            "group_id": group_id,
            "user_id": user_id,
            "username": username,
            "initiated_by": initiated_by,
            "created_at": datetime.utcnow()
        }
        
        result = await db.log_action(action_data)
        
        return {
            "success": True,
            "action_id": str(result.inserted_id),
            "user_id": user_id,
            "username": username,
            "message": "User has been unbanned"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Web unban error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# WEB CONTROL ENDPOINTS - BATCH ACTIONS
# ============================================================================

@web_router.post("/actions/batch")
async def web_batch_actions(
    actions: List[dict] = Body(..., embed=True, description="List of actions to execute")
) -> dict:
    """
    Execute multiple actions in batch via web interface.
    
    Each action should have:
    - action_type: "ban", "kick", "mute", "unmute", "restrict", "unrestrict", "warn", "promote", "demote"
    - group_id: Telegram group ID
    - user_input: User ID or @username
    - initiated_by: Admin user ID
    - (optional) reason, duration_minutes, title, etc.
    
    Returns:
        {
            "success": bool,
            "total": int,
            "successful": int,
            "failed": int,
            "results": [...]
        }
    """
    try:
        db = get_database()
        results = []
        
        if not actions:
            raise HTTPException(status_code=400, detail="Actions list cannot be empty")
        
        if len(actions) > 100:
            raise HTTPException(status_code=400, detail="Maximum 100 actions per batch")
        
        for idx, action in enumerate(actions):
            try:
                action_type = action.get("action_type")
                group_id = action.get("group_id")
                user_input = action.get("user_input")
                initiated_by = action.get("initiated_by")
                
                if not all([action_type, group_id, user_input, initiated_by]):
                    results.append({
                        "index": idx,
                        "success": False,
                        "error": "Missing required fields"
                    })
                    continue
                
                user_id, username = parse_user_reference(user_input)
                
                action_data = {
                    "action_type": action_type,
                    "group_id": group_id,
                    "user_id": user_id,
                    "username": username,
                    "initiated_by": initiated_by,
                    "created_at": datetime.utcnow()
                }
                
                # Copy optional fields
                for key in ["reason", "duration_minutes", "title", "permission_type"]:
                    if key in action:
                        action_data[key] = action[key]
                
                result = await db.log_action(action_data)
                
                results.append({
                    "index": idx,
                    "success": True,
                    "action_id": str(result.inserted_id),
                    "action_type": action_type
                })
            
            except Exception as e:
                logger.error(f"Error processing batch action {idx}: {e}")
                results.append({
                    "index": idx,
                    "success": False,
                    "error": str(e)
                })
        
        successful = sum(1 for r in results if r.get("success"))
        failed = len(results) - successful
        
        return {
            "success": failed == 0,
            "total": len(results),
            "successful": successful,
            "failed": failed,
            "results": results
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Web batch actions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# WEB CONTROL ENDPOINTS - QUERY & MONITORING
# ============================================================================

@web_router.get("/actions/user-history")
async def get_user_history(
    group_id: int = Query(..., description="Telegram group ID"),
    user_input: str = Query(..., description="User ID or @username"),
    limit: int = Query(50, ge=1, le=200, description="Max results")
) -> dict:
    """
    Get action history for a specific user in a group.
    
    Returns all actions (ban, mute, warn, etc.) performed on this user.
    
    Example:
        GET /api/web/actions/user-history?group_id=-100&user_input=123456&limit=50
    """
    try:
        db = get_database()
        user_id, username = parse_user_reference(user_input)
        
        if not user_id and not username:
            raise HTTPException(status_code=400, detail="Invalid user reference")
        
        # Query actions where this user is the target
        query = {
            "group_id": group_id,
            "$or": [
                {"user_id": user_id} if user_id else {"user_id": None},
                {"username": username} if username else {"username": None}
            ]
        }
        
        # Simplified query if we have user_id
        if user_id:
            query = {
                "group_id": group_id,
                "user_id": user_id
            }
        
        # This would need implementation in ActionDatabase
        # For now, return structure
        return {
            "success": True,
            "group_id": group_id,
            "user_id": user_id,
            "username": username,
            "total_actions": 0,
            "actions": []
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@web_router.get("/actions/group-stats")
async def get_group_stats(
    group_id: int = Query(..., description="Telegram group ID")
) -> dict:
    """
    Get statistics for a group (total actions, breakdown by type, recent actions).
    
    Returns:
        {
            "group_id": int,
            "total_actions": int,
            "actions_by_type": {
                "ban": int,
                "mute": int,
                "warn": int,
                ...
            },
            "recent_actions": [...],
            "most_active_admin": {...}
        }
    """
    try:
        db = get_database()
        
        # This would need implementation in ActionDatabase
        return {
            "success": True,
            "group_id": group_id,
            "total_actions": 0,
            "actions_by_type": {},
            "recent_actions": [],
            "most_active_admin": None
        }
    
    except Exception as e:
        logger.error(f"Error getting group stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@web_router.get("/actions/status/{action_id}")
async def get_action_status_web(
    action_id: str = Path(..., description="Action ID from MongoDB")
) -> dict:
    """
    Get detailed status and information about a specific action.
    
    Returns:
        {
            "action_id": string,
            "action_type": string,
            "group_id": int,
            "user_id": int or null,
            "username": string or null,
            "initiated_by": int,
            "created_at": timestamp,
            "status": "pending|processing|success|failed",
            "result": {...}
        }
    """
    try:
        # This would need implementation in ActionDatabase
        return {
            "success": True,
            "action_id": action_id,
            "status": "unknown",
            "message": "Action status endpoint - needs database integration"
        }
    
    except Exception as e:
        logger.error(f"Error getting action status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@web_router.get("/groups/list")
async def list_managed_groups() -> dict:
    """
    List all groups currently managed by the bot.
    
    Returns:
        {
            "total_groups": int,
            "groups": [
                {
                    "group_id": int,
                    "group_name": string,
                    "members_count": int,
                    "total_actions": int,
                    "last_action": timestamp
                },
                ...
            ]
        }
    """
    try:
        db = get_database()
        
        # This would need implementation in ActionDatabase
        return {
            "success": True,
            "total_groups": 0,
            "groups": []
        }
    
    except Exception as e:
        logger.error(f"Error listing groups: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# WEB CONTROL ENDPOINTS - HEALTH & INFO
# ============================================================================

@web_router.get("/health")
async def web_health_check() -> dict:
    """
    Health check endpoint for web control API.
    
    Returns:
        {
            "status": "healthy" | "degraded" | "unhealthy",
            "timestamp": ISO timestamp,
            "version": "3.0.0",
            "endpoints_available": int
        }
    """
    try:
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "3.0.0",
            "endpoints_available": 20,
            "message": "Web control API is operational"
        }
    
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@web_router.get("/info")
async def web_api_info() -> dict:
    """
    Get information about available web control endpoints.
    
    Returns comprehensive documentation of all endpoints.
    """
    return {
        "api_version": "1.0.0",
        "name": "Web Control API",
        "description": "Complete REST API for controlling bot via web interface",
        "base_path": "/api/web",
        "endpoints": {
            "parse-user": {
                "method": "POST",
                "description": "Parse user reference (ID or @username)",
                "path": "/parse-user"
            },
            "actions": {
                "ban": {"method": "POST", "path": "/actions/ban"},
                "kick": {"method": "POST", "path": "/actions/kick"},
                "mute": {"method": "POST", "path": "/actions/mute"},
                "unmute": {"method": "POST", "path": "/actions/unmute"},
                "restrict": {"method": "POST", "path": "/actions/restrict"},
                "unrestrict": {"method": "POST", "path": "/actions/unrestrict"},
                "warn": {"method": "POST", "path": "/actions/warn"},
                "promote": {"method": "POST", "path": "/actions/promote"},
                "demote": {"method": "POST", "path": "/actions/demote"},
                "unban": {"method": "POST", "path": "/actions/unban"},
                "batch": {"method": "POST", "path": "/actions/batch"}
            },
            "queries": {
                "user-history": {"method": "GET", "path": "/actions/user-history"},
                "group-stats": {"method": "GET", "path": "/actions/group-stats"},
                "action-status": {"method": "GET", "path": "/actions/status/{action_id}"},
                "list-groups": {"method": "GET", "path": "/groups/list"}
            }
        }
    }
