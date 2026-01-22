"""
Behavior Filters / Policies Routes
Endpoints for managing group behavior filters (floods, spam, etc.)
"""

import logging
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2", tags=["behavior-filters"])

# Database connection
db = None

def set_database(database):
    """Set the database connection"""
    global db
    db = database


# ============================================================================
# POLICIES ENDPOINTS - Get and Update group policies
# ============================================================================

@router.get("/groups/{group_id}/policies", response_model=Dict[str, Any])
async def get_group_policies(group_id: int):
    """Get all behavior filter policies for a group"""
    try:
        if db is None:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        # Get from database
        policies_collection = db["group_policies"]
        policies = await policies_collection.find_one({"group_id": group_id})
        
        # Set default policies
        default_policies = {
            "group_id": group_id,
            "floods_enabled": False,
            "spam_enabled": False,
            "checks_enabled": False,
            "silence_mode": False,
            "links_enabled": False
        }
        
        if not policies:
            return {"status": "success", "data": default_policies}
        
        # Remove MongoDB _id field and merge with defaults to ensure all fields present
        policies.pop("_id", None)
        result = {**default_policies, **policies}
        
        return {"status": "success", "data": result}
    
    except Exception as e:
        logger.error(f"Get policies error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/groups/{group_id}/policies/floods", response_model=Dict[str, Any])
async def toggle_floods_policy(group_id: int, payload: Dict[str, Any] = None):
    """Toggle floods detection policy"""
    try:
        if db is None:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        policies_collection = db["group_policies"]
        
        # Get current state
        current = await policies_collection.find_one({"group_id": group_id})
        if not current:
            current = {
                "group_id": group_id,
                "floods_enabled": False,
                "spam_enabled": False,
                "checks_enabled": False,
                "silence_mode": False,
                "links_enabled": False
            }
        
        # Toggle the setting
        new_state = not current.get("floods_enabled", False)
        
        # Update database - preserve all fields
        update_data = {
            "group_id": group_id,
            "floods_enabled": new_state,
            "spam_enabled": current.get("spam_enabled", False),
            "checks_enabled": current.get("checks_enabled", False),
            "silence_mode": current.get("silence_mode", False),
            "links_enabled": current.get("links_enabled", False),
            "last_updated": datetime.utcnow()
        }
        
        await policies_collection.update_one(
            {"group_id": group_id},
            {"$set": update_data},
            upsert=True
        )
        
        return {
            "status": "success",
            "message": f"Floods detection {'enabled' if new_state else 'disabled'}",
            "floods_enabled": new_state
        }
    
    except Exception as e:
        logger.error(f"Toggle floods error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/groups/{group_id}/policies/spam", response_model=Dict[str, Any])
async def toggle_spam_policy(group_id: int, payload: Dict[str, Any] = None):
    """Toggle spam detection policy"""
    try:
        if db is None:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        policies_collection = db["group_policies"]
        
        # Get current state
        current = await policies_collection.find_one({"group_id": group_id})
        if not current:
            current = {
                "group_id": group_id,
                "floods_enabled": False,
                "spam_enabled": False,
                "checks_enabled": False,
                "silence_mode": False,
                "links_enabled": False
            }
        
        # Toggle the setting
        new_state = not current.get("spam_enabled", False)
        
        # Update database - preserve all fields
        update_data = {
            "group_id": group_id,
            "floods_enabled": current.get("floods_enabled", False),
            "spam_enabled": new_state,
            "checks_enabled": current.get("checks_enabled", False),
            "silence_mode": current.get("silence_mode", False),
            "links_enabled": current.get("links_enabled", False),
            "last_updated": datetime.utcnow()
        }
        
        await policies_collection.update_one(
            {"group_id": group_id},
            {"$set": update_data},
            upsert=True
        )
        
        return {
            "status": "success",
            "message": f"Spam detection {'enabled' if new_state else 'disabled'}",
            "spam_enabled": new_state
        }
    
    except Exception as e:
        logger.error(f"Toggle spam error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/groups/{group_id}/policies/checks", response_model=Dict[str, Any])
async def toggle_checks_policy(group_id: int, payload: Dict[str, Any] = None):
    """Toggle checks policy"""
    try:
        if db is None:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        policies_collection = db["group_policies"]
        
        # Get current state
        current = await policies_collection.find_one({"group_id": group_id})
        if not current:
            current = {
                "group_id": group_id,
                "floods_enabled": False,
                "spam_enabled": False,
                "checks_enabled": False,
                "silence_mode": False,
                "links_enabled": False
            }
        
        # Toggle the setting
        new_state = not current.get("checks_enabled", False)
        
        # Update database - preserve all fields
        update_data = {
            "group_id": group_id,
            "floods_enabled": current.get("floods_enabled", False),
            "spam_enabled": current.get("spam_enabled", False),
            "checks_enabled": new_state,
            "silence_mode": current.get("silence_mode", False),
            "links_enabled": current.get("links_enabled", False),
            "last_updated": datetime.utcnow()
        }
        
        await policies_collection.update_one(
            {"group_id": group_id},
            {"$set": update_data},
            upsert=True
        )
        
        return {
            "status": "success",
            "message": f"Checks {'enabled' if new_state else 'disabled'}",
            "checks_enabled": new_state
        }
    
    except Exception as e:
        logger.error(f"Toggle checks error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/groups/{group_id}/policies/silence", response_model=Dict[str, Any])
async def toggle_silence_policy(group_id: int, payload: Dict[str, Any] = None):
    """Toggle silence mode policy"""
    try:
        if db is None:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        policies_collection = db["group_policies"]
        
        # Get current state
        current = await policies_collection.find_one({"group_id": group_id})
        if not current:
            current = {
                "group_id": group_id,
                "floods_enabled": False,
                "spam_enabled": False,
                "checks_enabled": False,
                "silence_mode": False,
                "links_enabled": False
            }
        
        # Toggle the setting
        new_state = not current.get("silence_mode", False)
        
        # Update database - preserve all fields
        update_data = {
            "group_id": group_id,
            "floods_enabled": current.get("floods_enabled", False),
            "spam_enabled": current.get("spam_enabled", False),
            "checks_enabled": current.get("checks_enabled", False),
            "silence_mode": new_state,
            "links_enabled": current.get("links_enabled", False),
            "last_updated": datetime.utcnow()
        }
        
        await policies_collection.update_one(
            {"group_id": group_id},
            {"$set": update_data},
            upsert=True
        )
        
        return {
            "status": "success",
            "message": f"Silence mode {'enabled' if new_state else 'disabled'}",
            "silence_mode": new_state
        }
    
    except Exception as e:
        logger.error(f"Toggle silence error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/groups/{group_id}/policies/links", response_model=Dict[str, Any])
async def toggle_links_policy(group_id: int, payload: Dict[str, Any] = None):
    """Toggle links policy"""
    try:
        if db is None:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        policies_collection = db["group_policies"]
        
        # Get current state
        current = await policies_collection.find_one({"group_id": group_id})
        if not current:
            current = {
                "group_id": group_id,
                "floods_enabled": False,
                "spam_enabled": False,
                "checks_enabled": False,
                "silence_mode": False,
                "links_enabled": False
            }
        
        # Toggle the setting
        new_state = not current.get("links_enabled", False)
        
        # Update database - preserve all fields
        update_data = {
            "group_id": group_id,
            "floods_enabled": current.get("floods_enabled", False),
            "spam_enabled": current.get("spam_enabled", False),
            "checks_enabled": current.get("checks_enabled", False),
            "silence_mode": current.get("silence_mode", False),
            "links_enabled": new_state,
            "last_updated": datetime.utcnow()
        }
        
        await policies_collection.update_one(
            {"group_id": group_id},
            {"$set": update_data},
            upsert=True
        )
        
        return {
            "status": "success",
            "message": f"Links policy {'enabled' if new_state else 'disabled'}",
            "links_enabled": new_state
        }
    
    except Exception as e:
        logger.error(f"Toggle links error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
