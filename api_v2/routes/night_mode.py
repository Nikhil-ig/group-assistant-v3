"""
Night Mode System - Scheduled Content Restrictions
Advanced scheduling system that automatically restricts content types during configured hours.
Integrates with whitelist/blacklist and permission systems.
"""

from fastapi import APIRouter, Body, Query, HTTPException, status
from datetime import datetime, time
from typing import List, Optional, Dict, Any
import logging

# Models (imported from schemas)
from api_v2.models.schemas import NightModeSettings, NightModeCreate, NightModeStatus, NightModePermissionCheck
from api_v2.core.database import get_db_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/groups/{group_id}/night-mode", tags=["night-mode"])


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def parse_time_string(time_str: str) -> Optional[time]:
    """Parse 'HH:MM' format to time object"""
    try:
        parts = time_str.split(":")
        return time(int(parts[0]), int(parts[1]))
    except Exception as e:
        logger.warning(f"Could not parse time string '{time_str}': {e}")
        return None


def is_current_time_in_range(start_str: str, end_str: str) -> bool:
    """Check if current time is within night mode window (handles midnight crossing)"""
    try:
        start = parse_time_string(start_str)
        end = parse_time_string(end_str)
        current = datetime.now().time()
        
        if not start or not end:
            return False
        
        # If end time < start time, it crosses midnight
        if end < start:
            # Night mode: 22:00 to 08:00 (crosses midnight)
            return current >= start or current < end
        else:
            # Normal: start to end (doesn't cross midnight)
            return start <= current < end
    except Exception as e:
        logger.error(f"Error checking time range: {e}")
        return False


def get_next_transition_time(start_str: str, end_str: str) -> str:
    """Calculate next transition time (when night mode starts/stops)"""
    try:
        start = parse_time_string(start_str)
        end = parse_time_string(end_str)
        current = datetime.now().time()
        
        if not start or not end:
            return "Unknown"
        
        # Check if currently in night mode
        if end < start:
            # Crosses midnight
            in_night_mode = current >= start or current < end
        else:
            in_night_mode = start <= current < end
        
        if in_night_mode:
            # Will end at end_time
            return f"{end_str} (ends in {end})"
        else:
            # Will start at start_time
            return f"{start_str} (starts in {start})"
    except Exception as e:
        logger.error(f"Error calculating transition: {e}")
        return "Unknown"


async def get_night_mode_settings(group_id: int) -> Optional[Dict[str, Any]]:
    """Fetch night mode settings from database"""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return None
        
        collection = db_manager.db.night_mode_settings
        settings = await collection.find_one({"group_id": group_id})
        return settings
    except Exception as e:
        logger.warning(f"Error fetching night mode settings: {e}")
        return None


async def save_night_mode_settings(group_id: int, settings: dict) -> bool:
    """Save night mode settings to database"""
    try:
        db_manager = get_db_manager()
        if not db_manager:
            return False
        
        collection = db_manager.db.night_mode_settings
        settings["group_id"] = group_id
        settings["updated_at"] = datetime.utcnow()
        
        # If creating new, add created_at
        existing = await collection.find_one({"group_id": group_id})
        if not existing:
            settings["created_at"] = datetime.utcnow()
        
        await collection.update_one(
            {"group_id": group_id},
            {"$set": settings},
            upsert=True
        )
        return True
    except Exception as e:
        logger.error(f"Error saving night mode settings: {e}")
        return False


# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.get("/settings", response_model=Dict[str, Any])
async def get_night_mode_config(group_id: int):
    """Get current night mode settings for group"""
    try:
        settings = await get_night_mode_settings(group_id)
        
        if not settings:
            # Return defaults if not configured
            return {
                "group_id": group_id,
                "enabled": False,
                "start_time": "22:00",
                "end_time": "08:00",
                "restricted_content_types": ["stickers", "gifs", "media", "voice"],
                "exempt_user_ids": [],
                "exempt_roles": [],
                "auto_delete_restricted": True,
                "message": "Night mode not configured. Using defaults."
            }
        
        # Remove MongoDB _id for cleaner response
        settings.pop("_id", None)
        return settings
    except Exception as e:
        logger.error(f"Error getting night mode settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/settings", response_model=Dict[str, Any])
async def update_night_mode_config(group_id: int, config: NightModeCreate):
    """Update night mode settings"""
    try:
        # Get existing settings
        existing = await get_night_mode_settings(group_id)
        
        # Build update dict (only update provided fields)
        update_dict = {}
        if config.enabled is not None:
            update_dict["enabled"] = config.enabled
        if config.start_time:
            update_dict["start_time"] = config.start_time
        if config.end_time:
            update_dict["end_time"] = config.end_time
        if config.restricted_content_types:
            update_dict["restricted_content_types"] = config.restricted_content_types
        if config.exempt_user_ids is not None:
            update_dict["exempt_user_ids"] = config.exempt_user_ids
        if config.exempt_roles is not None:
            update_dict["exempt_roles"] = config.exempt_roles
        if config.auto_delete_restricted is not None:
            update_dict["auto_delete_restricted"] = config.auto_delete_restricted
        
        # Save updated settings
        success = await save_night_mode_settings(group_id, update_dict)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save settings")
        
        # Return updated settings
        updated = await get_night_mode_settings(group_id)
        updated.pop("_id", None)
        
        return {
            "success": True,
            "message": "Night mode settings updated",
            "data": updated
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating night mode: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enable", response_model=Dict[str, Any])
async def enable_night_mode(group_id: int):
    """Enable night mode for group"""
    try:
        success = await save_night_mode_settings(group_id, {"enabled": True})
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to enable night mode")
        
        settings = await get_night_mode_settings(group_id)
        settings.pop("_id", None)
        
        return {
            "success": True,
            "message": "Night mode enabled",
            "data": settings
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enabling night mode: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/disable", response_model=Dict[str, Any])
async def disable_night_mode(group_id: int):
    """Disable night mode for group"""
    try:
        success = await save_night_mode_settings(group_id, {"enabled": False})
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to disable night mode")
        
        settings = await get_night_mode_settings(group_id)
        settings.pop("_id", None)
        
        return {
            "success": True,
            "message": "Night mode disabled",
            "data": settings
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling night mode: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=NightModeStatus)
async def get_night_mode_status(group_id: int) -> NightModeStatus:
    """
    Check if night mode is currently active
    Returns: {is_active, enabled, current_time, start_time, end_time, next_transition}
    """
    try:
        settings = await get_night_mode_settings(group_id)
        
        if not settings:
            # Not configured = not active
            current_time = datetime.now().strftime("%H:%M")
            return NightModeStatus(
                is_active=False,
                enabled=False,
                current_time=current_time,
                start_time="22:00",
                end_time="08:00",
                next_transition="Not configured"
            )
        
        enabled = settings.get("enabled", False)
        start_time = settings.get("start_time", "22:00")
        end_time = settings.get("end_time", "08:00")
        current_time = datetime.now().strftime("%H:%M")
        
        # Check if currently in night mode
        is_active = enabled and is_current_time_in_range(start_time, end_time)
        next_transition = get_next_transition_time(start_time, end_time)
        
        return NightModeStatus(
            is_active=is_active,
            enabled=enabled,
            current_time=current_time,
            start_time=start_time,
            end_time=end_time,
            next_transition=next_transition
        )
    except Exception as e:
        logger.error(f"Error getting night mode status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add-exemption/{user_id}", response_model=Dict[str, Any])
async def add_exempt_user(group_id: int, user_id: int):
    """Add user to night mode exemption list (can post any content during night mode)"""
    try:
        settings = await get_night_mode_settings(group_id)
        
        if not settings:
            # Create new settings with this exemption
            settings = {
                "enabled": False,
                "start_time": "22:00",
                "end_time": "08:00",
                "restricted_content_types": ["stickers", "gifs", "media", "voice"],
                "exempt_user_ids": [user_id],
                "exempt_roles": [],
                "auto_delete_restricted": True
            }
        else:
            # Add to existing exempt list
            exempt = settings.get("exempt_user_ids", [])
            if user_id not in exempt:
                exempt.append(user_id)
                settings["exempt_user_ids"] = exempt
        
        success = await save_night_mode_settings(group_id, settings)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to add exemption")
        
        return {
            "success": True,
            "message": f"User {user_id} added to night mode exemptions",
            "exempt_users": settings.get("exempt_user_ids", [])
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding exemption: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/remove-exemption/{user_id}", response_model=Dict[str, Any])
async def remove_exempt_user(group_id: int, user_id: int):
    """Remove user from night mode exemption list"""
    try:
        settings = await get_night_mode_settings(group_id)
        
        if not settings:
            raise HTTPException(status_code=404, detail="Night mode not configured")
        
        exempt = settings.get("exempt_user_ids", [])
        if user_id in exempt:
            exempt.remove(user_id)
            settings["exempt_user_ids"] = exempt
        
        success = await save_night_mode_settings(group_id, settings)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to remove exemption")
        
        return {
            "success": True,
            "message": f"User {user_id} removed from night mode exemptions",
            "exempt_users": settings.get("exempt_user_ids", [])
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing exemption: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/check/{user_id}/{content_type}", response_model=NightModePermissionCheck)
async def check_night_mode_permission(group_id: int, user_id: int, content_type: str) -> NightModePermissionCheck:
    """
    Check if user can send specific content type during night mode
    Returns: {can_send, reason, is_exempt, is_admin, content_type}
    """
    try:
        settings = await get_night_mode_settings(group_id)
        
        # If night mode not enabled, everything is allowed
        if not settings or not settings.get("enabled", False):
            return NightModePermissionCheck(
                can_send=True,
                reason="Night mode disabled",
                is_exempt=False,
                is_admin=False,
                content_type=content_type
            )
        
        # Check if currently in night mode window
        start_time = settings.get("start_time", "22:00")
        end_time = settings.get("end_time", "08:00")
        
        if not is_current_time_in_range(start_time, end_time):
            return NightModePermissionCheck(
                can_send=True,
                reason="Not in night mode time window",
                is_exempt=False,
                is_admin=False,
                content_type=content_type
            )
        
        # Check if user is exempt
        exempt_users = settings.get("exempt_user_ids", [])
        if user_id in exempt_users:
            return NightModePermissionCheck(
                can_send=True,
                reason="User is exempt from night mode",
                is_exempt=True,
                is_admin=False,
                content_type=content_type
            )
        
        # Check if this content type is restricted during night mode
        restricted_types = settings.get("restricted_content_types", ["stickers", "gifs", "media", "voice"])
        
        if content_type not in restricted_types:
            return NightModePermissionCheck(
                can_send=True,
                reason=f"{content_type} is allowed during night mode",
                is_exempt=False,
                is_admin=False,
                content_type=content_type
            )
        
        # Content type is restricted
        return NightModePermissionCheck(
            can_send=False,
            reason=f"{content_type} is blocked during night mode ({start_time}-{end_time})",
            is_exempt=False,
            is_admin=False,
            content_type=content_type
        )
    except Exception as e:
        logger.error(f"Error checking night mode permission: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list-exemptions", response_model=Dict[str, Any])
async def list_exemptions(group_id: int):
    """List all users exempt from night mode"""
    try:
        settings = await get_night_mode_settings(group_id)
        
        if not settings:
            return {
                "group_id": group_id,
                "exempt_users": [],
                "exempt_roles": [],
                "message": "Night mode not configured"
            }
        
        return {
            "group_id": group_id,
            "exempt_users": settings.get("exempt_user_ids", []),
            "exempt_roles": settings.get("exempt_roles", [])
        }
    except Exception as e:
        logger.error(f"Error listing exemptions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/toggle-exempt/{user_id}", response_model=Dict[str, Any])
async def toggle_exempt_user(group_id: int, user_id: int):
    """Toggle night mode exemption for a user"""
    try:
        # Get current settings
        settings = await get_night_mode_settings(group_id)
        is_exempt = False
        
        if not settings:
            # Create new settings with user exempt
            settings = {
                "group_id": group_id,
                "enabled": False,
                "start_time": "22:00",
                "end_time": "08:00",
                "restricted_content_types": ["stickers", "gifs", "media", "voice"],
                "exempt_user_ids": [user_id],
                "exempt_roles": []
            }
            is_exempt = True
        else:
            # Toggle exemption status
            exempt_list = settings.get("exempt_user_ids", [])
            if user_id in exempt_list:
                # Remove from exemption
                exempt_list.remove(user_id)
                is_exempt = False
            else:
                # Add to exemption
                exempt_list.append(user_id)
                is_exempt = True
            
            settings["exempt_user_ids"] = exempt_list
        
        # Save updated settings
        db_manager = get_db_manager()
        if db_manager:
            collection = db_manager.db.night_mode_settings
            settings["updated_at"] = datetime.utcnow()
            
            await collection.update_one(
                {"group_id": group_id},
                {"$set": settings},
                upsert=True
            )
        
        return {
            "status": "success",
            "group_id": group_id,
            "user_id": user_id,
            "is_exempt": is_exempt,
            "message": f"User {'added to' if is_exempt else 'removed from'} night mode exemptions"
        }
    except Exception as e:
        logger.error(f"Error toggling exemption: {e}")
        raise HTTPException(status_code=500, detail=str(e))
