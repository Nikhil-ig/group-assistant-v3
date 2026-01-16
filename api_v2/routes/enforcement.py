"""
Enforcement Routes
API endpoints for action execution, violation tracking, and escalation
Unified enforcement operations from centralized_api + api_v2 features
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from api_v2.models.enforcement import (
    EnforcementAction, ActionResponse, BatchActionRequest, BatchActionResponse,
    EnforcementStats, UserEnforcementHistory
)

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/v2", tags=["enforcement"])

# Global engine instances
_enforcement_engine = None


def set_enforcement_engine(engine):
    """Set enforcement engine instance"""
    global _enforcement_engine
    _enforcement_engine = engine


async def get_enforcement_engine():
    """Get enforcement engine instance"""
    global _enforcement_engine
    if _enforcement_engine is None:
        raise HTTPException(status_code=503, detail="Enforcement engine not initialized")
    return _enforcement_engine


# ============================================================================
# SINGLE ACTION ENDPOINTS
# ============================================================================

@router.post("/groups/{group_id}/enforcement/execute", response_model=ActionResponse)
async def execute_enforcement_action(
    group_id: int,
    action: EnforcementAction
) -> ActionResponse:
    """
    Execute a single enforcement action
    
    Supported actions:
    - ban, unban, kick, mute, unmute
    - promote, demote, warn
    - pin, unpin, delete_message
    - lockdown, cleanup_spam
    
    Example:
    ```json
    {
        "action_type": "mute",
        "user_id": 987654321,
        "duration_minutes": 60,
        "reason": "spam",
        "initiated_by": 111111
    }
    ```
    """
    try:
        # Override group_id from path
        action.group_id = group_id
        
        engine = await get_enforcement_engine()
        response = await engine.execute_action(action)
        
        if not response.success:
            raise HTTPException(status_code=400, detail=response.error)
        
        return response

    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing enforcement action: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/groups/{group_id}/enforcement/batch", response_model=BatchActionResponse)
async def execute_batch_enforcement(
    group_id: int,
    batch_request: BatchActionRequest
) -> BatchActionResponse:
    """
    Execute multiple enforcement actions
    
    Supports concurrent and sequential execution.
    
    Example:
    ```json
    {
        "actions": [
            {"action_type": "mute", "user_id": 111111, "duration_minutes": 60},
            {"action_type": "ban", "user_id": 222222}
        ],
        "execute_concurrently": true
    }
    ```
    """
    try:
        if not batch_request.actions:
            raise ValueError("Batch must contain at least one action")

        # Set group_id for all actions
        for action in batch_request.actions:
            action.group_id = group_id

        engine = await get_enforcement_engine()
        response = await engine.execute_batch(batch_request)
        
        return response

    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error executing batch enforcement: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# ACTION TYPE SPECIFIC ENDPOINTS
# ============================================================================

@router.post("/groups/{group_id}/enforcement/ban")
async def ban_user(
    group_id: int,
    user_id: int = Query(..., description="User ID to ban"),
    reason: Optional[str] = Query(None, description="Ban reason"),
    initiated_by: int = Query(..., description="Admin user ID")
) -> ActionResponse:
    """Ban a user from the group"""
    action = EnforcementAction(
        action_type="ban",
        group_id=group_id,
        user_id=user_id,
        reason=reason,
        initiated_by=initiated_by
    )
    engine = await get_enforcement_engine()
    return await engine.execute_action(action)


@router.post("/groups/{group_id}/enforcement/unban")
async def unban_user(
    group_id: int,
    user_id: int = Query(..., description="User ID to unban"),
    initiated_by: int = Query(..., description="Admin user ID")
) -> ActionResponse:
    """Unban a user from the group"""
    action = EnforcementAction(
        action_type="unban",
        group_id=group_id,
        user_id=user_id,
        initiated_by=initiated_by
    )
    engine = await get_enforcement_engine()
    return await engine.execute_action(action)


@router.post("/groups/{group_id}/enforcement/kick")
async def kick_user(
    group_id: int,
    user_id: int = Query(..., description="User ID to kick"),
    reason: Optional[str] = Query(None, description="Kick reason"),
    initiated_by: int = Query(..., description="Admin user ID")
) -> ActionResponse:
    """Kick a user from the group"""
    action = EnforcementAction(
        action_type="kick",
        group_id=group_id,
        user_id=user_id,
        reason=reason,
        initiated_by=initiated_by
    )
    engine = await get_enforcement_engine()
    return await engine.execute_action(action)


@router.post("/groups/{group_id}/enforcement/mute")
async def mute_user(
    group_id: int,
    user_id: int = Query(..., description="User ID to mute"),
    duration_minutes: int = Query(60, description="Mute duration in minutes"),
    reason: Optional[str] = Query(None, description="Mute reason"),
    initiated_by: int = Query(..., description="Admin user ID")
) -> ActionResponse:
    """Mute a user for specified duration"""
    action = EnforcementAction(
        action_type="mute",
        group_id=group_id,
        user_id=user_id,
        duration_minutes=duration_minutes,
        reason=reason,
        initiated_by=initiated_by
    )
    engine = await get_enforcement_engine()
    return await engine.execute_action(action)


@router.post("/groups/{group_id}/enforcement/unmute")
async def unmute_user(
    group_id: int,
    user_id: int = Query(..., description="User ID to unmute"),
    initiated_by: int = Query(..., description="Admin user ID")
) -> ActionResponse:
    """Unmute a user"""
    action = EnforcementAction(
        action_type="unmute",
        group_id=group_id,
        user_id=user_id,
        initiated_by=initiated_by
    )
    engine = await get_enforcement_engine()
    return await engine.execute_action(action)


@router.post("/groups/{group_id}/enforcement/warn")
async def warn_user(
    group_id: int,
    user_id: int = Query(..., description="User ID to warn"),
    reason: Optional[str] = Query(None, description="Warning reason"),
    initiated_by: int = Query(..., description="Admin user ID")
) -> ActionResponse:
    """Issue a warning to a user"""
    action = EnforcementAction(
        action_type="warn",
        group_id=group_id,
        user_id=user_id,
        reason=reason,
        initiated_by=initiated_by
    )
    engine = await get_enforcement_engine()
    return await engine.execute_action(action)


@router.post("/groups/{group_id}/enforcement/promote")
async def promote_user(
    group_id: int,
    user_id: int = Query(..., description="User ID to promote"),
    title: Optional[str] = Query(None, description="Admin title"),
    initiated_by: int = Query(..., description="Admin user ID")
) -> ActionResponse:
    """Promote a user to admin"""
    action = EnforcementAction(
        action_type="promote",
        group_id=group_id,
        user_id=user_id,
        title=title,
        initiated_by=initiated_by
    )
    engine = await get_enforcement_engine()
    return await engine.execute_action(action)


@router.post("/groups/{group_id}/enforcement/demote")
async def demote_user(
    group_id: int,
    user_id: int = Query(..., description="User ID to demote"),
    initiated_by: int = Query(..., description="Admin user ID")
) -> ActionResponse:
    """Demote an admin user"""
    action = EnforcementAction(
        action_type="demote",
        group_id=group_id,
        user_id=user_id,
        initiated_by=initiated_by
    )
    engine = await get_enforcement_engine()
    return await engine.execute_action(action)


@router.post("/groups/{group_id}/enforcement/lockdown")
async def lockdown_group(
    group_id: int,
    initiated_by: int = Query(..., description="Admin user ID")
) -> ActionResponse:
    """Lock down the group"""
    action = EnforcementAction(
        action_type="lockdown",
        group_id=group_id,
        initiated_by=initiated_by
    )
    engine = await get_enforcement_engine()
    return await engine.execute_action(action)


# ============================================================================
# VIOLATION TRACKING ENDPOINTS
# ============================================================================

@router.get("/groups/{group_id}/enforcement/user/{user_id}/violations", response_model=UserEnforcementHistory)
async def get_user_violations(
    group_id: int,
    user_id: int
) -> UserEnforcementHistory:
    """Get violation history for a user"""
    try:
        engine = await get_enforcement_engine()
        history = await engine.get_user_violations(user_id, group_id)
        return history

    except Exception as e:
        logger.error(f"Error getting user violations: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/groups/{group_id}/enforcement/user/{user_id}/violations/track")
async def track_user_violation(
    group_id: int,
    user_id: int,
    violation_type: str = Query(..., description="Violation type"),
    reason: Optional[str] = Query(None, description="Violation reason"),
    escalate: bool = Query(True, description="Apply escalation")
) -> dict:
    """Manually track a violation for a user"""
    try:
        engine = await get_enforcement_engine()
        await engine.track_violation(user_id, group_id, violation_type, reason, escalate)
        
        return {
            "success": True,
            "message": f"Violation tracked for user {user_id}",
            "user_id": user_id,
            "group_id": group_id,
            "violation_type": violation_type
        }

    except Exception as e:
        logger.error(f"Error tracking violation: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# STATISTICS ENDPOINTS
# ============================================================================

@router.get("/groups/{group_id}/enforcement/stats", response_model=EnforcementStats)
async def get_enforcement_statistics(
    group_id: int,
    hours: int = Query(24, description="Hours of history to retrieve")
) -> EnforcementStats:
    """Get enforcement statistics for a group"""
    try:
        if hours < 1 or hours > 720:  # Max 30 days
            raise ValueError("Hours must be between 1 and 720")

        engine = await get_enforcement_engine()
        stats = await engine.get_enforcement_stats(group_id, hours)
        return stats

    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting enforcement stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/enforcement/health")
async def enforcement_health() -> dict:
    """Check enforcement engine health"""
    try:
        engine = await get_enforcement_engine()
        return {
            "status": "healthy",
            "engine": "enforcement",
            "db_connected": True if engine.db_manager else False,
            "telegram_api_ready": True if engine.telegram_api else False
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "engine": "enforcement",
            "error": str(e)
        }
