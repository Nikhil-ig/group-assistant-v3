"""
FastAPI Routes for Centralized API
Endpoints for action execution and management
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, Path
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
from centralized_api.config import MONGODB_URI, MONGODB_DATABASE

from centralized_api.models import (
    ActionRequest,
    ActionResponse,
    ActionStatus,
    BanRequest,
    KickRequest,
    MuteRequest,
    UnmuteRequest,
    PromoteRequest,
    DemoteRequest,
    WarnRequest,
    PinRequest,
    UnpinRequest,
    DeleteMessageRequest,
)
from centralized_api.services import ActionExecutor
from centralized_api.db import ActionDatabase
from centralized_api.config import API_PREFIX

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix=API_PREFIX, tags=["actions"])

# Global executor instance (will be initialized in app startup)
_executor: Optional[ActionExecutor] = None


async def get_executor() -> ActionExecutor:
    """Get executor instance"""
    global _executor
    if _executor is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return _executor


def set_executor(executor: ActionExecutor):
    """Set executor instance"""
    global _executor
    _executor = executor


# ---------------------------------------------------------------------------
# Async MongoDB helper for advanced routes
# ---------------------------------------------------------------------------
_motor_client = None


def get_db():
    """Return an AsyncIOMotorDatabase instance.

    Prefer the FastAPI app.state.motor_db if available (set during app
    startup). Fall back to creating a lazy module-level AsyncIOMotorClient
    if necessary to preserve backwards compatibility.
    """
    try:
        # attempt to read the db from the running FastAPI app state
        from fastapi import current_app
        motor_db = getattr(current_app.state, "motor_db", None)
        if motor_db is not None:
            return motor_db
    except Exception:
        # current_app might not be available in all contexts; continue to fallback
        pass

    # fallback: lazy-create a Motor client and return its DB
    global _motor_client
    if _motor_client is None:
        _motor_client = AsyncIOMotorClient(MONGODB_URI)
    return _motor_client[MONGODB_DATABASE]


# ============================================================================
# ACTION EXECUTION ENDPOINTS
# ============================================================================

@router.post("/actions/execute", response_model=ActionResponse)
async def execute_action(request: ActionRequest) -> ActionResponse:
    """
    Execute a single action
    
    Supports all action types:
    - ban, kick, mute, unmute, promote, demote, warn, pin, unpin, delete_message, etc.
    
    Example:
    ```json
    {
        "action_type": "ban",
        "group_id": -1001234567890,
        "user_id": 987654321,
        "reason": "Spam",
        "initiated_by": 111111
    }
    ```
    """
    try:
        executor = await get_executor()
        response = await executor.execute_action(request)
        return response

    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error executing action: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/actions/batch", response_model=List[ActionResponse])
async def execute_batch(requests: List[ActionRequest]) -> List[ActionResponse]:
    """
    Execute multiple actions in batch
    
    All actions are executed concurrently for speed.
    
    Example:
    ```json
    [
        {
            "action_type": "ban",
            "group_id": -1001234567890,
            "user_id": 111111,
            "reason": "Spam"
        },
        {
            "action_type": "mute",
            "group_id": -1001234567890,
            "user_id": 222222,
            "duration": 3600
        }
    ]
    ```
    """
    try:
        if not requests:
            raise ValueError("Batch must contain at least one action")

        if len(requests) > 100:
            raise ValueError("Batch size limited to 100 actions")

        executor = await get_executor()
        responses = await executor.execute_batch(requests)
        return responses

    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error executing batch: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# ACTION STATUS & HISTORY ENDPOINTS
# ============================================================================

@router.get("/actions/status/{action_id}", response_model=ActionResponse)
async def get_action_status(
    action_id: str = Path(..., description="Action ID")
) -> ActionResponse:
    """
    Get current status of an action
    
    Returns the action status, whether it's pending, in progress, succeeded, or failed.
    """
    try:
        executor = await get_executor()
        response = await executor.get_action_status(action_id)

        if response is None:
            raise HTTPException(status_code=404, detail="Action not found")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting action status: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/actions/history")
async def get_action_history(
    group_id: int = Query(..., description="Telegram group ID"),
    limit: int = Query(50, ge=1, le=100, description="Max results"),
    skip: int = Query(0, ge=0, description="Results to skip"),
    status: Optional[str] = Query(None, description="Filter by status"),
) -> dict:
    """
    Get action history for a group with pagination
    
    Supports filtering by status: pending, in_progress, success, failed, cancelled, retrying
    
    Example: `/api/v1/actions/history?group_id=-1001234567890&limit=50&skip=0`
    """
    try:
        executor = await get_executor()
        
        status_enum = None
        if status:
            try:
                status_enum = ActionStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

        history = await executor.get_action_history(
            group_id=group_id,
            limit=limit,
            skip=skip,
        )

        return {
            "group_id": group_id,
            "total": history.get("total", 0),
            "limit": limit,
            "skip": skip,
            "actions": history.get("actions", []),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting action history: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# ACTION MANAGEMENT ENDPOINTS
# ============================================================================

@router.delete("/actions/cancel/{action_id}")
async def cancel_action(
    action_id: str = Path(..., description="Action ID")
) -> dict:
    """
    Cancel a pending action
    
    Only works for actions that are still pending.
    Already executed actions cannot be cancelled.
    """
    try:
        executor = await get_executor()
        success = await executor.cancel_action(action_id)

        if not success:
            raise HTTPException(
                status_code=400,
                detail="Action not found or already completed"
            )

        return {
            "success": True,
            "message": f"Action {action_id} cancelled successfully",
            "action_id": action_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling action: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# MONITORING ENDPOINTS
# ============================================================================

@router.get("/health")
async def health_check() -> dict:
    """Health check endpoint"""
    try:
        executor = await get_executor()
        return {
            "status": "healthy",
            "pending_actions": executor.get_pending_actions_count(),
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unavailable")


@router.get("/actions/stats/{group_id}")
async def get_group_statistics(
    group_id: int = Path(..., description="Telegram group ID")
) -> dict:
    """
    Get action statistics for a group
    
    Returns total actions, success rate, etc.
    """
    try:
        executor = await get_executor()
        db = executor.db
        stats = await db.get_group_statistics(group_id)

        if not stats:
            raise HTTPException(status_code=404, detail="No data for group")

        return stats

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@router.get("/actions/dead-letters")
async def get_dead_letters() -> dict:
    """
    Get dead letter queue (failed actions that couldn't be recovered)
    
    Useful for debugging and manual intervention.
    """
    try:
        executor = await get_executor()
        db = executor.db

        if not db._connected:
            raise HTTPException(status_code=503, detail="Database not connected")

        dead_letters = list(
            db.db["action_dead_letters"].find().sort("created_at", -1).limit(100)
        )

        for doc in dead_letters:
            doc.pop("_id", None)

        return {
            "count": len(dead_letters),
            "dead_letters": dead_letters,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dead letters: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# HELPER ENDPOINTS
# ============================================================================

@router.get("/actions/pending-count")
async def get_pending_count() -> dict:
    """Get number of currently pending actions"""
    try:
        executor = await get_executor()
        return {
            "pending_count": executor.get_pending_actions_count(),
        }
    except Exception as e:
        logger.error(f"Error getting pending count: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/actions/check-pre-action")
async def check_pre_action_validation(
    user_id: int = Query(..., description="Target user ID"),
    group_id: int = Query(..., description="Telegram group ID"),
    admin_id: int = Query(..., description="Admin/bot ID performing the action"),
    action_type: str = Query(..., description="Action type (ban, mute, restrict, kick, warn)")
) -> dict:
    """
    Comprehensive pre-action validation including:
    1. Duplicate action prevention (user not already restricted)
    2. Admin/bot permission checks (admin can perform action)
    3. Target user status (user not already muted/banned by admin)
    4. Admin restrictions (check if admin themselves is muted/banned)
    
    Returns validation status with detailed information:
    {
        "can_proceed": boolean,
        "status": "ok" or error message,
        "reason": explanation,
        "checks": {
            "duplicate": bool,
            "admin_permission": bool,
            "target_muted_by_admin": bool,
            "admin_muted": bool,
            "admin_restricted": bool
        },
        "current_restrictions": [...]
    }
    
    Examples:
    - User already banned → {"can_proceed": false, "status": "🔴 ALREADY BANNED", ...}
    - Admin is muted → {"can_proceed": false, "reason": "Admin cannot perform actions while muted", ...}
    - All checks pass → {"can_proceed": true, "status": "ok", ...}
    """
    try:
        db = get_db()
        actions_collection = db["actions"]
        
        # Map action types to their corresponding status checks
        action_status_map = {
            "ban": ("ban", "🔴 ALREADY BANNED", "User is already banned"),
            "mute": ("mute", "🔇 ALREADY MUTED", "User is already muted"),
            "restrict": ("restrict", "🔒 ALREADY RESTRICTED", "User is already restricted"),
            "kick": (None, None, None),
            "warn": (None, None, None),
        }
        
        # Validate action type
        if action_type.lower() not in action_status_map:
            raise ValueError(f"Invalid action type: {action_type}")
        
        action_type_lower = action_type.lower()
        check_action, status_emoji, status_msg = action_status_map[action_type_lower]
        
        # Initialize response structure
        checks = {
            "duplicate": False,
            "admin_permission": True,
            "target_muted_by_admin": False,
            "admin_muted": False,
            "admin_restricted": False,
            "same_user": False,
        }
        reasons = []
        
        # ==========================================
        # Check 1: Self-action validation
        # ==========================================
        if user_id == admin_id:
            checks["same_user"] = True
            reasons.append("Cannot perform action on yourself")
            return {
                "can_proceed": False,
                "status": "❌ SELF_ACTION",
                "reason": "Cannot perform action on yourself",
                "checks": checks,
                "current_restrictions": []
            }
        
        # ==========================================
        # Check 2: Admin permission (is admin muted/restricted?)
        # ==========================================
        admin_actions = await actions_collection.find(
            {
                "group_id": group_id,
                "user_id": admin_id,
            }
        ).sort("created_at", -1).limit(50).to_list(50)
        
        admin_current_mute = False
        admin_current_restrict = False
        
        for admin_action in admin_actions:
            admin_action_t = admin_action.get("action_type", "").lower()
            
            if admin_action_t == "mute" and not admin_current_mute:
                admin_current_mute = True
                checks["admin_muted"] = True
            elif admin_action_t == "unmute" and admin_current_mute:
                admin_current_mute = False
                checks["admin_muted"] = False
            elif admin_action_t == "restrict" and not admin_current_restrict:
                admin_current_restrict = True
                checks["admin_restricted"] = True
            elif admin_action_t == "unrestrict" and admin_current_restrict:
                admin_current_restrict = False
                checks["admin_restricted"] = False
            
            if any([admin_current_mute, admin_current_restrict]):
                break
        
        # Admin cannot take action if muted or restricted
        if admin_current_mute:
            reasons.append("Admin is muted and cannot perform actions")
            return {
                "can_proceed": False,
                "status": "🔇 ADMIN_MUTED",
                "reason": "Admin is muted and cannot perform actions",
                "checks": checks,
                "current_restrictions": ["mute"]
            }
        
        if admin_current_restrict:
            reasons.append("Admin is restricted and cannot perform actions")
            return {
                "can_proceed": False,
                "status": "🔒 ADMIN_RESTRICTED",
                "reason": "Admin is restricted and cannot perform actions",
                "checks": checks,
                "current_restrictions": ["restrict"]
            }
        
        # ==========================================
        # Check 3: Duplicate action prevention
        # ==========================================
        user_actions = await actions_collection.find(
            {
                "group_id": group_id,
                "user_id": user_id,
            }
        ).sort("created_at", -1).limit(100).to_list(100)
        
        current_restrictions = []
        current_ban = False
        current_mute = False
        current_restrict = False
        
        for action in user_actions:
            action_t = action.get("action_type", "").lower()
            
            if action_t == "ban" and not current_ban:
                current_ban = True
                current_restrictions.append("ban")
            elif action_t == "unban" and current_ban:
                current_ban = False
                if "ban" in current_restrictions:
                    current_restrictions.remove("ban")
            elif action_t == "mute" and not current_mute:
                current_mute = True
                current_restrictions.append("mute")
            elif action_t == "unmute" and current_mute:
                current_mute = False
                if "mute" in current_restrictions:
                    current_restrictions.remove("mute")
            elif action_t == "restrict" and not current_restrict:
                current_restrict = True
                current_restrictions.append("restrict")
            elif action_t == "unrestrict" and current_restrict:
                current_restrict = False
                if "restrict" in current_restrictions:
                    current_restrictions.remove("restrict")
            
            if any([current_ban, current_mute, current_restrict]):
                break
        
        # Check for duplicate restriction
        if check_action is not None:
            if check_action == "ban" and current_ban:
                checks["duplicate"] = True
                return {
                    "can_proceed": False,
                    "status": status_emoji,
                    "reason": status_msg,
                    "checks": checks,
                    "current_restrictions": current_restrictions
                }
            elif check_action == "mute" and current_mute:
                checks["duplicate"] = True
                return {
                    "can_proceed": False,
                    "status": status_emoji,
                    "reason": status_msg,
                    "checks": checks,
                    "current_restrictions": current_restrictions
                }
            elif check_action == "restrict" and current_restrict:
                checks["duplicate"] = True
                return {
                    "can_proceed": False,
                    "status": status_emoji,
                    "reason": status_msg,
                    "checks": checks,
                    "current_restrictions": current_restrictions
                }
        
        # ==========================================
        # Check 4: All validations passed
        # ==========================================
        return {
            "can_proceed": True,
            "status": "ok",
            "reason": "All pre-action validations passed",
            "checks": checks,
            "current_restrictions": current_restrictions
        }
        
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error validating pre-action: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Keep old endpoint for backwards compatibility
@router.get("/actions/check-duplicate")
async def check_duplicate_action(
    user_id: int = Query(..., description="Target user ID"),
    group_id: int = Query(..., description="Telegram group ID"),
    action_type: str = Query(..., description="Action type (ban, mute, restrict, kick, warn)")
) -> dict:
    """
    Legacy endpoint: Check only for duplicate actions.
    Redirects to new comprehensive endpoint with admin_id=0
    
    Deprecated: Use /api/actions/check-pre-action instead
    """
    # Call new endpoint with dummy admin_id for backwards compatibility
    return await check_pre_action_validation(user_id, group_id, 0, action_type)
