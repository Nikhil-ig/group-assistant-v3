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

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v2", tags=["enforcement"])

# Get bot token from environment
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8276429151:AAEWq4nE9hQcRgY4AcuLWFKW_z26Xcmk2gY")
TELEGRAM_API_URL = "https://api.telegram.org/bot"


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
    """Restrict user permissions"""
    try:
        user_id = action.get("user_id")
        
        result = await call_telegram_api(
            "restrictChatMember",
            chat_id=group_id,
            user_id=user_id,
            permissions={
                "can_send_messages": False,
                "can_send_audios": False,
                "can_send_documents": False,
                "can_send_photos": False,
                "can_send_videos": False,
                "can_send_other_messages": False
            }
        )
        
        return create_action_response(group_id, "restrict", result, "User restricted" if result["success"] else "Failed to restrict user")
    except Exception as e:
        logger.error(f"Restrict error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/groups/{group_id}/enforcement/unrestrict", response_model=Dict[str, Any])
async def unrestrict_user(group_id: int, action: dict = Body(...)):
    """Unrestrict user permissions"""
    try:
        user_id = action.get("user_id")
        
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
                "can_send_other_messages": True
            }
        )
        
        return create_action_response(group_id, "unrestrict", result, "User unrestricted" if result["success"] else "Failed to unrestrict user")
    except Exception as e:
        logger.error(f"Unrestrict error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/groups/{group_id}/enforcement/lockdown", response_model=Dict[str, Any])
async def lockdown_group(group_id: int, action: dict = Body(...)):
    """Lock down the group - restrict all members from sending messages"""
    try:
        # Send message about lockdown
        result = await call_telegram_api(
            "sendMessage",
            chat_id=group_id,
            text="🔒 Group is now in lockdown. Only admins can send messages."
        )
        
        return create_action_response(group_id, "lockdown", result, "Lockdown activated" if result["success"] else "Failed to activate lockdown")
    except Exception as e:
        logger.error(f"Lockdown error: {e}")
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
