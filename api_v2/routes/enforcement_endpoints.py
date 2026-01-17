"""
Enforcement Endpoints - Execute actual Telegram API actions
These endpoints handle moderation actions by calling Telegram Bot API directly
"""

import os
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Body
import httpx
import json

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v2", tags=["enforcement"])

# Get bot token from environment
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8276429151:AAEWq4nE9hQcRgY4AcuLWFKW_z26Xcmk2gY")
TELEGRAM_API_URL = "https://api.telegram.org/bot"

# In-memory database for permission states (should be MongoDB in production)
# Structure: {group_id: {user_id: {permissions...}}}
PERMISSION_STATES_DB: Dict[int, Dict[int, Dict[str, Any]]] = {}


def save_permission_state(group_id: int, user_id: int, permissions: Dict[str, bool], restricted_by: int = 0, reason: str = ""):
    """Save user permission state to database"""
    if group_id not in PERMISSION_STATES_DB:
        PERMISSION_STATES_DB[group_id] = {}
    
    PERMISSION_STATES_DB[group_id][user_id] = {
        "can_send_messages": permissions.get("can_send_messages", True),
        "can_send_other_messages": permissions.get("can_send_other_messages", True),
        "can_send_audios": permissions.get("can_send_audios", True),
        "can_send_documents": permissions.get("can_send_documents", True),
        "can_send_photos": permissions.get("can_send_photos", True),
        "can_send_videos": permissions.get("can_send_videos", True),
        "is_restricted": not all([permissions.get(k, True) for k in ["can_send_messages", "can_send_other_messages", "can_send_audios"]]),
        "restricted_at": datetime.now().isoformat(),
        "restricted_by": restricted_by,
        "restriction_reason": reason,
        "updated_at": datetime.now().isoformat()
    }
    logger.info(f"✅ Permission state saved: group={group_id}, user={user_id}, permissions={permissions}")


def get_permission_state(group_id: int, user_id: int) -> Dict[str, Any]:
    """Get user permission state from database"""
    if group_id in PERMISSION_STATES_DB and user_id in PERMISSION_STATES_DB[group_id]:
        return PERMISSION_STATES_DB[group_id][user_id]
    
    # Return default (all allowed) if not in DB
    return {
        "can_send_messages": True,
        "can_send_other_messages": True,
        "can_send_audios": True,
        "can_send_documents": True,
        "can_send_photos": True,
        "can_send_videos": True,
        "is_restricted": False,
        "restricted_at": None,
        "restricted_by": None,
        "restriction_reason": None
    }


async def call_telegram_api(method: str, **kwargs) -> Dict[str, Any]:
    """Call Telegram Bot API with proper error handling"""
    url = f"{TELEGRAM_API_URL}{BOT_TOKEN}/{method}"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=kwargs)
            data = response.json()
            
            if not data.get("ok"):
                error_msg = data.get("description", "Unknown error")
                logger.error(f"Telegram API error for {method}: {error_msg}")
                return {"success": False, "error": error_msg}
            
            return {"success": True, "data": data.get("result", {})}
    except Exception as e:
        logger.error(f"Exception calling Telegram API: {str(e)}")
        return {"success": False, "error": str(e)}


def create_action_response(group_id: int, action_type: str, telegram_result: Dict, message: str):
    """Create a standardized action response"""
    success = telegram_result.get("success", False)
    
    return {
        "success": success,
        "data": {
            "id": str(uuid.uuid4()),
            "group_id": group_id,
            "action_type": action_type,
            "status": "completed" if success else "failed",
            "telegram_response": telegram_result.get("data") if success else telegram_result.get("error"),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        },
        "message": message,
        "error": None if success else telegram_result.get("error")
    }


@router.post("/groups/{group_id}/enforcement/ban", response_model=Dict[str, Any])
async def ban_user(group_id: int, action: dict = Body(...)):
    """Ban a user from the group"""
    try:
        user_id = action.get("user_id")
        reason = action.get("reason", "")
        
        result = await call_telegram_api(
            "banChatMember",
            chat_id=group_id,
            user_id=user_id
        )
        
        return create_action_response(group_id, "ban", result, "User banned" if result["success"] else "Failed to ban user")
    except Exception as e:
        logger.error(f"Ban error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/groups/{group_id}/enforcement/unban", response_model=Dict[str, Any])
async def unban_user(group_id: int, action: dict = Body(...)):
    """Unban a user from the group"""
    try:
        user_id = action.get("user_id")
        
        result = await call_telegram_api(
            "unbanChatMember",
            chat_id=group_id,
            user_id=user_id
        )
        
        return create_action_response(group_id, "unban", result, "User unbanned" if result["success"] else "Failed to unban user")
    except Exception as e:
        logger.error(f"Unban error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/groups/{group_id}/enforcement/kick", response_model=Dict[str, Any])
async def kick_user(group_id: int, action: dict = Body(...)):
    """Kick a user from the group"""
    try:
        user_id = action.get("user_id")
        
        result = await call_telegram_api(
            "kickChatMember",
            chat_id=group_id,
            user_id=user_id
        )
        
        return create_action_response(group_id, "kick", result, "User kicked" if result["success"] else "Failed to kick user")
    except Exception as e:
        logger.error(f"Kick error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/groups/{group_id}/enforcement/mute", response_model=Dict[str, Any])
async def mute_user(group_id: int, action: dict = Body(...)):
    """Mute a user in the group"""
    try:
        user_id = action.get("user_id")
        duration = action.get("duration", 0)  # 0 = forever
        
        # restrictChatMember with can_send_messages=False
        kwargs = {
            "chat_id": group_id,
            "user_id": user_id,
            "permissions": {
                "can_send_messages": False,
                "can_send_audios": False,
                "can_send_documents": False,
                "can_send_photos": False,
                "can_send_videos": False,
                "can_send_video_notes": False,
                "can_send_voice_notes": False,
                "can_send_polls": False,
                "can_send_other_messages": False,
                "can_add_web_page_previews": False
            }
        }
        
        if duration > 0:
            kwargs["until_date"] = int((datetime.now() + timedelta(minutes=duration)).timestamp())
        
        result = await call_telegram_api("restrictChatMember", **kwargs)
        
        return create_action_response(group_id, "mute", result, "User muted" if result["success"] else "Failed to mute user")
    except Exception as e:
        logger.error(f"Mute error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/groups/{group_id}/enforcement/unmute", response_model=Dict[str, Any])
async def unmute_user(group_id: int, action: dict = Body(...)):
    """Unmute a user in the group"""
    try:
        user_id = action.get("user_id")
        
        # restrictChatMember with all permissions allowed
        result = await call_telegram_api(
            "restrictChatMember",
            chat_id=group_id,
            user_id=user_id,
            permissions={
                "can_send_messages": True,
                "can_send_audios": True,
                "can_send_documents": True,
                "can_send_photos": True,
                "can_send_videos": True,
                "can_send_video_notes": True,
                "can_send_voice_notes": True,
                "can_send_polls": True,
                "can_send_other_messages": True,
                "can_add_web_page_previews": True
            }
        )
        
        return create_action_response(group_id, "unmute", result, "User unmuted" if result["success"] else "Failed to unmute user")
    except Exception as e:
        logger.error(f"Unmute error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/groups/{group_id}/enforcement/warn", response_model=Dict[str, Any])
async def warn_user(group_id: int, action: dict = Body(...)):
    """Warn a user (record warning)"""
    try:
        # For now, just send a message
        user_id = action.get("user_id")
        reason = action.get("reason", "")
        
        result = await call_telegram_api(
            "sendMessage",
            chat_id=group_id,
            text=f"⚠️ Warning for user {user_id}: {reason}"
        )
        
        return create_action_response(group_id, "warn", result, "User warned" if result["success"] else "Failed to warn user")
    except Exception as e:
        logger.error(f"Warn error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/groups/{group_id}/enforcement/promote", response_model=Dict[str, Any])
async def promote_user(group_id: int, action: dict = Body(...)):
    """Promote a user to admin with optional custom title"""
    try:
        user_id = action.get("user_id")
        custom_title = action.get("title", "Admin")  # Get custom title from request
        
        logger.info(f"DEBUG: Promote request - user_id={user_id}, custom_title='{custom_title}'")
        
        # Telegram API has a limit of 16 characters for custom_title
        if custom_title and len(custom_title) > 16:
            custom_title = custom_title[:16]
            logger.info(f"DEBUG: Title truncated to 16 chars: '{custom_title}'")
        
        promote_kwargs = {
            "chat_id": group_id,
            "user_id": user_id,
            "can_change_info": True,
            "can_post_messages": True,
            "can_edit_messages": True,
            "can_delete_messages": True,
            "can_restrict_members": True
        }
        
        # Add custom_title if provided and not default
        if custom_title and custom_title != "":
            promote_kwargs["custom_title"] = custom_title
            logger.info(f"DEBUG: Adding custom_title to kwargs: '{custom_title}'")
        else:
            logger.info(f"DEBUG: NOT adding custom_title (empty or None)")
        
        logger.info(f"DEBUG: Final promote_kwargs: {promote_kwargs}")
        result = await call_telegram_api("promoteChatMember", **promote_kwargs)
        logger.info(f"DEBUG: Telegram response: {result}")
        
        return create_action_response(group_id, "promote", result, "User promoted" if result["success"] else "Failed to promote user")
    except Exception as e:
        logger.error(f"Promote error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/groups/{group_id}/enforcement/demote", response_model=Dict[str, Any])
async def demote_user(group_id: int, action: dict = Body(...)):
    """Demote a user from admin"""
    try:
        user_id = action.get("user_id")
        
        result = await call_telegram_api(
            "promoteChatMember",
            chat_id=group_id,
            user_id=user_id,
            is_anonymous=False,
            can_change_info=False,
            can_post_messages=False,
            can_edit_messages=False,
            can_delete_messages=False,
            can_restrict_members=False
        )
        
        return create_action_response(group_id, "demote", result, "User demoted" if result["success"] else "Failed to demote user")
    except Exception as e:
        logger.error(f"Demote error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/groups/{group_id}/enforcement/restrict", response_model=Dict[str, Any])
async def restrict_user(group_id: int, action: dict = Body(...)):
    """Restrict user permissions - restrict only the specified permission"""
    try:
        user_id = action.get("user_id")
        metadata = action.get("metadata", {})
        permission_type = metadata.get("permission_type")
        
        # Map permission_type to Telegram API field names
        permission_mapping = {
            "can_send_messages": "can_send_messages",
            "can_send_audios": "can_send_audios",
            "can_send_other_messages": "can_send_other_messages"
        }
        
        # Get current member restrictions to preserve other permissions
        member_result = await call_telegram_api(
            "getChatMember",
            chat_id=group_id,
            user_id=user_id
        )
        
        # Start with current permissions (assuming all true if member not restricted)
        current_perms = {}
        if member_result.get("success") and member_result.get("data"):
            member_data = member_result.get("data", {})
            restrictions = member_data.get("user_chat_restrictions", {})
            
            # Extract current permission states (inverted from restrictions)
            current_perms = {
                "can_send_messages": not restrictions.get("can_send_messages", False),
                "can_send_audios": not restrictions.get("can_send_audios", False),
                "can_send_documents": not restrictions.get("can_send_documents", False),
                "can_send_photos": not restrictions.get("can_send_photos", False),
                "can_send_videos": not restrictions.get("can_send_videos", False),
                "can_send_other_messages": not restrictions.get("can_send_other_messages", False)
            }
        else:
            # If we can't get member info, assume all permissions are allowed
            current_perms = {
                "can_send_messages": True,
                "can_send_audios": True,
                "can_send_documents": True,
                "can_send_photos": True,
                "can_send_videos": True,
                "can_send_other_messages": True
            }
        
        # Toggle only the requested permission to False
        if permission_type in permission_mapping:
            current_perms[permission_type] = False
        
        result = await call_telegram_api(
            "restrictChatMember",
            chat_id=group_id,
            user_id=user_id,
            permissions=current_perms
        )
        
        # Save permission state to database on success
        if result.get("success"):
            restricted_by = action.get("initiated_by", 0)
            reason = action.get("reason", f"Restricted {permission_type}")
            save_permission_state(group_id, user_id, current_perms, restricted_by, reason)
        
        return create_action_response(group_id, "restrict", result, "User restricted" if result["success"] else "Failed to restrict user")
    except Exception as e:
        logger.error(f"Restrict error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/groups/{group_id}/enforcement/unrestrict", response_model=Dict[str, Any])
async def unrestrict_user(group_id: int, action: dict = Body(...)):
    """Unrestrict user permissions - unrestrict only the specified permission"""
    try:
        user_id = action.get("user_id")
        metadata = action.get("metadata", {})
        permission_type = metadata.get("permission_type")
        
        # Map permission_type to Telegram API field names
        permission_mapping = {
            "can_send_messages": "can_send_messages",
            "can_send_audios": "can_send_audios",
            "can_send_other_messages": "can_send_other_messages"
        }
        
        # Get current member restrictions to preserve other permissions
        member_result = await call_telegram_api(
            "getChatMember",
            chat_id=group_id,
            user_id=user_id
        )
        
        # Start with current permissions (assuming all true if member not restricted)
        current_perms = {}
        if member_result.get("success") and member_result.get("data"):
            member_data = member_result.get("data", {})
            restrictions = member_data.get("user_chat_restrictions", {})
            
            # Extract current permission states (inverted from restrictions)
            current_perms = {
                "can_send_messages": not restrictions.get("can_send_messages", False),
                "can_send_audios": not restrictions.get("can_send_audios", False),
                "can_send_documents": not restrictions.get("can_send_documents", False),
                "can_send_photos": not restrictions.get("can_send_photos", False),
                "can_send_videos": not restrictions.get("can_send_videos", False),
                "can_send_other_messages": not restrictions.get("can_send_other_messages", False)
            }
        else:
            # If we can't get member info, assume all permissions are already allowed
            current_perms = {
                "can_send_messages": True,
                "can_send_audios": True,
                "can_send_documents": True,
                "can_send_photos": True,
                "can_send_videos": True,
                "can_send_other_messages": True
            }
        
        # Toggle only the requested permission to True
        if permission_type in permission_mapping:
            current_perms[permission_type] = True
        
        result = await call_telegram_api(
            "restrictChatMember",
            chat_id=group_id,
            user_id=user_id,
            permissions=current_perms
        )
        
        # Save permission state to database on success
        if result.get("success"):
            restricted_by = action.get("initiated_by", 0)
            reason = action.get("reason", f"Unrestricted {permission_type}")
            save_permission_state(group_id, user_id, current_perms, restricted_by, reason)
        
        return create_action_response(group_id, "unrestrict", result, "User unrestricted" if result["success"] else "Failed to unrestrict user")
    except Exception as e:
        logger.error(f"Unrestrict error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/groups/{group_id}/enforcement/lockdown", response_model=Dict[str, Any])
async def lockdown_group(group_id: int, action: dict = Body(...)):
    """Lock down the group - restrict all members from sending messages"""
    try:
        # Restrict all members' permissions - only admins can send messages
        permissions = {
            "can_send_messages": False,
            "can_send_media_messages": False,
            "can_send_polls": False,
            "can_send_other_messages": False,
            "can_add_web_page_previews": False,
            "can_change_info": False,
            "can_invite_users": False,
            "can_pin_messages": False,
        }
        
        result = await call_telegram_api(
            "setChatPermissions",
            chat_id=group_id,
            permissions=permissions,
            use_independent_chat_permissions=True
        )
        
        if result.get("success"):
            # Send message about lockdown
            await call_telegram_api(
                "sendMessage",
                chat_id=group_id,
                text="🔒 <b>Group is now in LOCKDOWN</b>\nOnly admins can send messages.\n\nUse /unlock to restore normal permissions.",
                parse_mode="HTML"
            )
        
        return create_action_response(group_id, "lockdown", result, "Lockdown activated" if result["success"] else "Failed to activate lockdown")
    except Exception as e:
        logger.error(f"Lockdown error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/groups/{group_id}/enforcement/unlock", response_model=Dict[str, Any])
async def unlock_group(group_id: int, action: dict = Body(...)):
    """Unlock the group - restore full member permissions"""
    try:
        # Restore all members' permissions
        permissions = {
            "can_send_messages": True,
            "can_send_media_messages": True,
            "can_send_polls": True,
            "can_send_other_messages": True,
            "can_add_web_page_previews": True,
            "can_change_info": True,
            "can_invite_users": True,
            "can_pin_messages": True,
        }
        
        result = await call_telegram_api(
            "setChatPermissions",
            chat_id=group_id,
            permissions=permissions,
            use_independent_chat_permissions=True
        )
        
        if result.get("success"):
            # Send message about unlock
            await call_telegram_api(
                "sendMessage",
                chat_id=group_id,
                text="🔓 <b>Group lockdown has been lifted</b>\nMembers can now send messages normally.",
                parse_mode="HTML"
            )
        
        return create_action_response(group_id, "unlock", result, "Lockdown lifted" if result["success"] else "Failed to lift lockdown")
    except Exception as e:
        logger.error(f"Unlock error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/groups/{group_id}/enforcement/execute", response_model=Dict[str, Any])
async def execute_action(group_id: int, action: dict = Body(...)):
    """Generic action execution endpoint - handles pin, unpin, and other actions"""
    try:
        action_type = action.get("action_type", "").lower()
        
        if action_type == "pin":
            message_id = action.get("message_id")
            if not message_id:
                raise ValueError("message_id required for pin action")
            
            result = await call_telegram_api(
                "pinChatMessage",
                chat_id=group_id,
                message_id=message_id,
                disable_notification=True
            )
            
            return create_action_response(group_id, "pin", result, "Message pinned" if result["success"] else "Failed to pin message")
        
        elif action_type == "unpin":
            message_id = action.get("message_id")
            if not message_id:
                # Unpin all messages
                result = await call_telegram_api(
                    "unpinAllChatMessages",
                    chat_id=group_id
                )
            else:
                # Unpin specific message
                result = await call_telegram_api(
                    "unpinChatMessage",
                    chat_id=group_id,
                    message_id=message_id
                )
            
            return create_action_response(group_id, "unpin", result, "Message unpinned" if result["success"] else "Failed to unpin message")
        
        else:
            error_msg = f"Unknown action type: {action_type}"
            return {
                "success": False,
                "error": error_msg,
                "data": {
                    "id": str(uuid.uuid4()),
                    "group_id": group_id,
                    "action_type": action_type,
                    "status": "failed",
                    "created_at": datetime.now().isoformat()
                }
            }

    except Exception as e:
        logger.error(f"Execute action error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PERMISSION STATE ENDPOINTS
# ============================================================================

@router.get("/groups/{group_id}/users/{user_id}/permissions")
async def get_user_permissions(group_id: int, user_id: int):
    """Get user permission state from database"""
    try:
        perms = get_permission_state(group_id, user_id)
        return {
            "success": True,
            "data": {
                "group_id": group_id,
                "user_id": user_id,
                "can_send_messages": perms.get("can_send_messages", True),
                "can_send_other_messages": perms.get("can_send_other_messages", True),
                "can_send_audios": perms.get("can_send_audios", True),
                "is_restricted": perms.get("is_restricted", False),
                "restriction_reason": perms.get("restriction_reason"),
                "restricted_at": perms.get("restricted_at"),
                "restricted_by": perms.get("restricted_by")
            }
        }
    except Exception as e:
        logger.error(f"Get permissions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/groups/{group_id}/users/{user_id}/is-restricted")
async def is_user_restricted(group_id: int, user_id: int, permission_type: str = "all"):
    """Check if user is restricted from sending a specific type of message"""
    try:
        perms = get_permission_state(group_id, user_id)
        
        # Check specific permission type
        if permission_type == "text":
            is_restricted = not perms.get("can_send_messages", True)
        elif permission_type == "stickers":  # Stickers & GIFs
            is_restricted = not perms.get("can_send_other_messages", True)
        elif permission_type == "voice":
            is_restricted = not perms.get("can_send_audios", True)
        elif permission_type == "all":
            # Check if ANY permission is restricted
            is_restricted = perms.get("is_restricted", False)
        else:
            return {
                "success": False,
                "error": f"Unknown permission type: {permission_type}"
            }
        
        return {
            "success": True,
            "data": {
                "group_id": group_id,
                "user_id": user_id,
                "permission_type": permission_type,
                "is_restricted": is_restricted,
                "reason": perms.get("restriction_reason") if is_restricted else None
            }
        }
    except Exception as e:
        logger.error(f"Check restriction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    

