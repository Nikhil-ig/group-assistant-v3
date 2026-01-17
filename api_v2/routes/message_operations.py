"""
Message Operations Routes
Provides endpoints for deleting messages, sending messages, and related operations.
All logic centralized in API V2 for robustness and consistency.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Body
from pymongo import MongoClient
import os

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v2", tags=["message-operations"])

# Database connection
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
client = MongoClient(MONGODB_URL)
db = client["group_assistant"]


# ==================== MESSAGE DELETION ====================

@router.post("/groups/{group_id}/messages/delete", response_model=Dict[str, Any])
async def delete_message(
    group_id: int,
    message_data: dict = Body(...)
):
    """
    Delete a message in the group.
    
    Parameters:
    - message_id: ID of the message to delete
    - admin_id: ID of admin performing the action
    - reason: Reason for deletion (optional)
    - target_user_id: ID of user whose message is being deleted (optional, for history)
    
    Returns:
    - success: Boolean indicating operation success
    - message_id: ID of deleted message
    - deleted_at: Timestamp of deletion
    - history_id: ID of action in history
    """
    try:
        message_id = message_data.get("message_id")
        admin_id = message_data.get("admin_id")
        reason = message_data.get("reason", "No reason provided")
        target_user_id = message_data.get("target_user_id")
        
        # Validate inputs
        if not message_id:
            raise ValueError("message_id is required")
        if not admin_id:
            raise ValueError("admin_id is required")
        
        # Get admin info for logging
        admin_collection = db["users"]
        admin_data = admin_collection.find_one({"user_id": admin_id})
        admin_name = admin_data.get("first_name", "Unknown") if admin_data else "Unknown"
        admin_username = admin_data.get("username") if admin_data else None
        
        # Create deletion record in history
        action_id = str(uuid.uuid4())
        deletion_record = {
            "id": action_id,
            "group_id": group_id,
            "action_type": "message_deleted",
            "admin_id": admin_id,
            "admin_name": admin_name,
            "admin_username": admin_username,
            "message_id": message_id,
            "target_user_id": target_user_id,
            "reason": reason,
            "deleted_at": datetime.utcnow(),
            "status": "completed"
        }
        
        # Store in history
        history_collection = db["action_history"]
        history_collection.insert_one(deletion_record)
        
        # Update message collection (mark as deleted)
        messages_collection = db["deleted_messages"]
        messages_collection.insert_one({
            "message_id": message_id,
            "group_id": group_id,
            "deleted_by": admin_id,
            "reason": reason,
            "deleted_at": datetime.utcnow()
        })
        
        logger.info(f"Message {message_id} deleted by admin {admin_id} in group {group_id}")
        
        return {
            "success": True,
            "message_id": message_id,
            "deleted_at": deletion_record["deleted_at"].isoformat(),
            "history_id": action_id,
            "reason": reason,
            "admin": {
                "id": admin_id,
                "name": admin_name,
                "username": admin_username
            },
            "message": f"✅ Message deleted successfully by {admin_name}"
        }
    
    except ValueError as e:
        logger.error(f"Validation error in delete_message: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Delete message error: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting message: {str(e)}")


@router.get("/groups/{group_id}/messages/deleted", response_model=Dict[str, Any])
async def get_deleted_messages(group_id: int, limit: int = 50):
    """
    Get recently deleted messages in a group.
    
    Parameters:
    - limit: Maximum number of records to return (default: 50)
    
    Returns:
    - deleted_messages: List of recently deleted messages
    - total_count: Total count of deleted messages
    """
    try:
        messages_collection = db["deleted_messages"]
        
        deleted_messages = list(
            messages_collection
            .find({"group_id": group_id})
            .sort("deleted_at", -1)
            .limit(limit)
        )
        
        # Convert ObjectId to string and format dates
        formatted_messages = []
        for msg in deleted_messages:
            formatted_messages.append({
                "message_id": msg.get("message_id"),
                "deleted_by": msg.get("deleted_by"),
                "reason": msg.get("reason", "No reason provided"),
                "deleted_at": msg.get("deleted_at").isoformat() if msg.get("deleted_at") else None
            })
        
        return {
            "success": True,
            "group_id": group_id,
            "total_count": len(formatted_messages),
            "deleted_messages": formatted_messages,
            "message": f"Retrieved {len(formatted_messages)} deleted messages"
        }
    
    except Exception as e:
        logger.error(f"Get deleted messages error: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving deleted messages: {str(e)}")


# ==================== MESSAGE SENDING ====================

@router.post("/groups/{group_id}/messages/send", response_model=Dict[str, Any])
async def send_message(
    group_id: int,
    message_data: dict = Body(...)
):
    """
    Send a message via bot to a group.
    
    Parameters:
    - text: Message text to send
    - admin_id: ID of admin sending the message
    - reply_to_message_id: ID of message to reply to (optional)
    - parse_mode: HTML or Markdown (default: HTML)
    - disable_web_page_preview: Boolean (default: True)
    
    Returns:
    - success: Boolean indicating operation success
    - message_id: ID of sent message (from Telegram API)
    - sent_at: Timestamp of when message was sent
    - broadcast_id: ID of broadcast record in database
    """
    try:
        text = message_data.get("text", "").strip()
        admin_id = message_data.get("admin_id")
        reply_to_message_id = message_data.get("reply_to_message_id")
        parse_mode = message_data.get("parse_mode", "HTML")
        disable_web_page_preview = message_data.get("disable_web_page_preview", True)
        
        # Validate inputs
        if not text:
            raise ValueError("Message text is required")
        if not admin_id:
            raise ValueError("admin_id is required")
        if len(text) > 4096:
            raise ValueError("Message text cannot exceed 4096 characters")
        if parse_mode not in ["HTML", "Markdown"]:
            raise ValueError("parse_mode must be HTML or Markdown")
        
        # Get admin info
        admin_collection = db["users"]
        admin_data = admin_collection.find_one({"user_id": admin_id})
        admin_name = admin_data.get("first_name", "Unknown") if admin_data else "Unknown"
        admin_username = admin_data.get("username") if admin_data else None
        
        # Create broadcast record
        broadcast_id = str(uuid.uuid4())
        broadcast_record = {
            "id": broadcast_id,
            "group_id": group_id,
            "action_type": "message_sent",
            "admin_id": admin_id,
            "admin_name": admin_name,
            "admin_username": admin_username,
            "text": text,
            "reply_to_message_id": reply_to_message_id,
            "parse_mode": parse_mode,
            "sent_at": datetime.utcnow(),
            "status": "pending"  # Will be updated by bot after actual send
        }
        
        # Store in history
        history_collection = db["action_history"]
        history_collection.insert_one(broadcast_record)
        
        # Store in broadcasts collection for tracking
        broadcasts_collection = db["broadcasts"]
        broadcasts_collection.insert_one(broadcast_record)
        
        logger.info(f"Message broadcast queued by admin {admin_id} in group {group_id}")
        
        return {
            "success": True,
            "broadcast_id": broadcast_id,
            "group_id": group_id,
            "text_preview": text[:100] + ("..." if len(text) > 100 else ""),
            "sent_at": broadcast_record["sent_at"].isoformat(),
            "admin": {
                "id": admin_id,
                "name": admin_name,
                "username": admin_username
            },
            "reply_to": reply_to_message_id,
            "parse_mode": parse_mode,
            "message": f"✅ Message queued for broadcast"
        }
    
    except ValueError as e:
        logger.error(f"Validation error in send_message: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Send message error: {e}")
        raise HTTPException(status_code=500, detail=f"Error sending message: {str(e)}")


@router.get("/groups/{group_id}/messages/broadcasts", response_model=Dict[str, Any])
async def get_broadcasts(group_id: int, limit: int = 50, status: Optional[str] = None):
    """
    Get broadcast history for a group.
    
    Parameters:
    - limit: Maximum number of records to return (default: 50)
    - status: Filter by status - pending, completed, failed (optional)
    
    Returns:
    - broadcasts: List of broadcast records
    - total_count: Total count of broadcasts
    """
    try:
        broadcasts_collection = db["broadcasts"]
        
        query = {"group_id": group_id}
        if status:
            query["status"] = status
        
        broadcasts = list(
            broadcasts_collection
            .find(query)
            .sort("sent_at", -1)
            .limit(limit)
        )
        
        # Format broadcasts
        formatted_broadcasts = []
        for b in broadcasts:
            formatted_broadcasts.append({
                "id": b.get("id"),
                "admin_id": b.get("admin_id"),
                "admin_name": b.get("admin_name"),
                "text_preview": b.get("text", "")[:100] + ("..." if len(b.get("text", "")) > 100 else ""),
                "sent_at": b.get("sent_at").isoformat() if b.get("sent_at") else None,
                "status": b.get("status", "unknown")
            })
        
        return {
            "success": True,
            "group_id": group_id,
            "total_count": len(formatted_broadcasts),
            "broadcasts": formatted_broadcasts,
            "message": f"Retrieved {len(formatted_broadcasts)} broadcast records"
        }
    
    except Exception as e:
        logger.error(f"Get broadcasts error: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving broadcasts: {str(e)}")


@router.put("/broadcasts/{broadcast_id}/status", response_model=Dict[str, Any])
async def update_broadcast_status(
    broadcast_id: str,
    status_data: dict = Body(...)
):
    """
    Update the status of a broadcast.
    
    Parameters:
    - status: New status (pending, completed, failed)
    - message_id: Telegram message ID (if successfully sent)
    - error: Error message (if failed)
    
    Returns:
    - success: Boolean indicating operation success
    """
    try:
        new_status = status_data.get("status")
        message_id = status_data.get("message_id")
        error = status_data.get("error")
        
        if not new_status:
            raise ValueError("status is required")
        if new_status not in ["pending", "completed", "failed"]:
            raise ValueError("status must be: pending, completed, or failed")
        
        broadcasts_collection = db["broadcasts"]
        
        update_data = {
            "status": new_status,
            "updated_at": datetime.utcnow()
        }
        
        if message_id:
            update_data["message_id"] = message_id
        if error:
            update_data["error"] = error
        
        result = broadcasts_collection.update_one(
            {"id": broadcast_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise ValueError(f"Broadcast {broadcast_id} not found")
        
        logger.info(f"Broadcast {broadcast_id} status updated to {new_status}")
        
        return {
            "success": True,
            "broadcast_id": broadcast_id,
            "status": new_status,
            "updated_at": update_data["updated_at"].isoformat(),
            "message": f"Broadcast status updated to {new_status}"
        }
    
    except ValueError as e:
        logger.error(f"Validation error in update_broadcast_status: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Update broadcast status error: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating broadcast: {str(e)}")


# ==================== MESSAGE FORWARDING ====================

@router.post("/groups/{group_id}/messages/forward", response_model=Dict[str, Any])
async def forward_message(
    group_id: int,
    forward_data: dict = Body(...)
):
    """
    Forward a message from one location to another via bot.
    
    Parameters:
    - from_chat_id: Chat ID where message originated
    - message_id: Message ID to forward
    - to_chat_id: Chat ID where to forward
    - admin_id: ID of admin initiating the forward
    
    Returns:
    - success: Boolean indicating operation success
    - action_id: ID of action in history
    """
    try:
        from_chat_id = forward_data.get("from_chat_id")
        message_id = forward_data.get("message_id")
        to_chat_id = forward_data.get("to_chat_id")
        admin_id = forward_data.get("admin_id")
        
        # Validate inputs
        if not all([from_chat_id, message_id, to_chat_id, admin_id]):
            raise ValueError("from_chat_id, message_id, to_chat_id, and admin_id are required")
        
        # Get admin info
        admin_collection = db["users"]
        admin_data = admin_collection.find_one({"user_id": admin_id})
        admin_name = admin_data.get("first_name", "Unknown") if admin_data else "Unknown"
        
        # Create forward record
        action_id = str(uuid.uuid4())
        forward_record = {
            "id": action_id,
            "group_id": group_id,
            "action_type": "message_forwarded",
            "admin_id": admin_id,
            "admin_name": admin_name,
            "from_chat_id": from_chat_id,
            "message_id": message_id,
            "to_chat_id": to_chat_id,
            "forwarded_at": datetime.utcnow(),
            "status": "completed"
        }
        
        # Store in history
        history_collection = db["action_history"]
        history_collection.insert_one(forward_record)
        
        logger.info(f"Message {message_id} forwarded by admin {admin_id}")
        
        return {
            "success": True,
            "action_id": action_id,
            "message_id": message_id,
            "forwarded_at": forward_record["forwarded_at"].isoformat(),
            "from_chat": from_chat_id,
            "to_chat": to_chat_id,
            "message": "✅ Message forwarded successfully"
        }
    
    except ValueError as e:
        logger.error(f"Validation error in forward_message: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Forward message error: {e}")
        raise HTTPException(status_code=500, detail=f"Error forwarding message: {str(e)}")


# ==================== MESSAGE EDITING ====================

@router.put("/groups/{group_id}/messages/{message_id}", response_model=Dict[str, Any])
async def edit_message(
    group_id: int,
    message_id: int,
    edit_data: dict = Body(...)
):
    """
    Edit a previously sent message.
    
    Parameters:
    - new_text: New message text
    - admin_id: ID of admin performing the edit
    - parse_mode: HTML or Markdown
    
    Returns:
    - success: Boolean indicating operation success
    """
    try:
        new_text = edit_data.get("new_text", "").strip()
        admin_id = edit_data.get("admin_id")
        parse_mode = edit_data.get("parse_mode", "HTML")
        
        # Validate inputs
        if not new_text:
            raise ValueError("new_text is required")
        if not admin_id:
            raise ValueError("admin_id is required")
        if len(new_text) > 4096:
            raise ValueError("Message text cannot exceed 4096 characters")
        
        # Get admin info
        admin_collection = db["users"]
        admin_data = admin_collection.find_one({"user_id": admin_id})
        admin_name = admin_data.get("first_name", "Unknown") if admin_data else "Unknown"
        
        # Create edit record
        action_id = str(uuid.uuid4())
        edit_record = {
            "id": action_id,
            "group_id": group_id,
            "action_type": "message_edited",
            "message_id": message_id,
            "admin_id": admin_id,
            "admin_name": admin_name,
            "new_text": new_text,
            "parse_mode": parse_mode,
            "edited_at": datetime.utcnow(),
            "status": "pending"
        }
        
        # Store in history
        history_collection = db["action_history"]
        history_collection.insert_one(edit_record)
        
        logger.info(f"Message {message_id} edit queued by admin {admin_id}")
        
        return {
            "success": True,
            "action_id": action_id,
            "message_id": message_id,
            "edited_at": edit_record["edited_at"].isoformat(),
            "admin_name": admin_name,
            "message": f"✅ Message edit queued successfully"
        }
    
    except ValueError as e:
        logger.error(f"Validation error in edit_message: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Edit message error: {e}")
        raise HTTPException(status_code=500, detail=f"Error editing message: {str(e)}")
