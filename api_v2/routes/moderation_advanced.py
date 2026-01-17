"""
Advanced Moderation Routes
Provides endpoints for word filtering, spam detection, slowmode, etc.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Body
from pymongo import MongoClient
import os

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v2", tags=["moderation-advanced"])

# Database connection
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
client = MongoClient(MONGODB_URL)
db = client["group_assistant"]


@router.post("/groups/{group_id}/moderation/filters", response_model=Dict[str, Any])
async def add_word_filter(group_id: int, filter_data: dict = Body(...)):
    """Add a word to the filter list"""
    try:
        word = filter_data.get("word", "").lower().strip()
        action = filter_data.get("action", "delete")  # delete, mute, warn
        
        if not word:
            raise ValueError("Word is required")
        
        if action not in ["delete", "mute", "warn"]:
            raise ValueError("Action must be: delete, mute, or warn")
        
        filters_collection = db["word_filters"]
        
        # Check if already exists
        existing = filters_collection.find_one({
            "group_id": group_id,
            "word": word
        })
        
        if existing:
            return {
                "success": False,
                "error": f"Filter for '{word}' already exists"
            }
        
        # Add filter
        filter_doc = {
            "id": str(uuid.uuid4()),
            "group_id": group_id,
            "word": word,
            "action": action,
            "created_at": datetime.utcnow(),
            "active": True
        }
        
        result = filters_collection.insert_one(filter_doc)
        
        return {
            "success": True,
            "data": {
                "id": filter_doc["id"],
                "word": word,
                "action": action,
                "created_at": filter_doc["created_at"].isoformat()
            },
            "message": f"Filter for '{word}' added successfully"
        }
    
    except Exception as e:
        logger.error(f"Add word filter error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/groups/{group_id}/moderation/filters", response_model=Dict[str, Any])
async def list_word_filters(group_id: int):
    """List all word filters for a group"""
    try:
        filters_collection = db["word_filters"]
        
        filters = list(filters_collection.find({
            "group_id": group_id,
            "active": True
        }).sort("created_at", -1))
        
        return {
            "success": True,
            "data": {
                "group_id": group_id,
                "total_filters": len(filters),
                "filters": [
                    {
                        "id": f["id"],
                        "word": f["word"],
                        "action": f["action"],
                        "created_at": f["created_at"].isoformat()
                    }
                    for f in filters
                ]
            }
        }
    except Exception as e:
        logger.error(f"List word filters error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/groups/{group_id}/moderation/filters/{filter_id}", response_model=Dict[str, Any])
async def remove_word_filter(group_id: int, filter_id: str):
    """Remove a word filter"""
    try:
        filters_collection = db["word_filters"]
        
        result = filters_collection.update_one(
            {"id": filter_id, "group_id": group_id},
            {"$set": {"active": False, "deleted_at": datetime.utcnow()}}
        )
        
        if result.matched_count == 0:
            raise ValueError("Filter not found")
        
        return {
            "success": True,
            "message": "Filter removed successfully"
        }
    except Exception as e:
        logger.error(f"Remove word filter error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/groups/{group_id}/settings/slowmode", response_model=Dict[str, Any])
async def set_slowmode(group_id: int, settings_data: dict = Body(...)):
    """Set slowmode for the group (seconds between messages per user)"""
    try:
        seconds = settings_data.get("seconds", 0)
        
        if seconds < 0:
            raise ValueError("Seconds must be >= 0")
        
        if seconds > 3600:
            raise ValueError("Maximum slowmode is 3600 seconds (1 hour)")
        
        settings_collection = db["group_settings"]
        
        result = settings_collection.update_one(
            {"group_id": group_id},
            {"$set": {
                "slowmode_seconds": seconds,
                "updated_at": datetime.utcnow()
            }},
            upsert=True
        )
        
        return {
            "success": True,
            "data": {
                "group_id": group_id,
                "slowmode_enabled": seconds > 0,
                "slowmode_seconds": seconds,
                "message": "Slowmode" if seconds > 0 else "No slowmode"
            }
        }
    except Exception as e:
        logger.error(f"Set slowmode error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/groups/{group_id}/moderation/report-spam", response_model=Dict[str, Any])
async def report_spam(group_id: int, spam_data: dict = Body(...)):
    """Report a message as spam"""
    try:
        message_id = spam_data.get("message_id")
        user_id = spam_data.get("user_id")
        reason = spam_data.get("reason", "Spam")
        reporter_id = spam_data.get("reporter_id")
        
        if not all([message_id, user_id, reporter_id]):
            raise ValueError("message_id, user_id, and reporter_id are required")
        
        spam_collection = db["spam_reports"]
        
        report_doc = {
            "id": str(uuid.uuid4()),
            "group_id": group_id,
            "message_id": message_id,
            "user_id": user_id,
            "reason": reason,
            "reported_by": reporter_id,
            "created_at": datetime.utcnow(),
            "status": "pending"
        }
        
        result = spam_collection.insert_one(report_doc)
        
        return {
            "success": True,
            "data": {
                "report_id": report_doc["id"],
                "message_id": message_id,
                "reported_user": user_id,
                "reason": reason,
                "status": "pending"
            },
            "message": "Spam reported successfully"
        }
    except Exception as e:
        logger.error(f"Report spam error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/groups/{group_id}/moderation/spam-reports", response_model=Dict[str, Any])
async def get_spam_reports(group_id: int):
    """Get spam reports for a group"""
    try:
        spam_collection = db["spam_reports"]
        
        reports = list(spam_collection.find({
            "group_id": group_id,
            "status": "pending"
        }).sort("created_at", -1))
        
        return {
            "success": True,
            "data": {
                "group_id": group_id,
                "pending_reports": len(reports),
                "reports": [
                    {
                        "id": r["id"],
                        "message_id": r["message_id"],
                        "user_id": r["user_id"],
                        "reason": r["reason"],
                        "reported_by": r["reported_by"],
                        "created_at": r["created_at"].isoformat()
                    }
                    for r in reports
                ]
            }
        }
    except Exception as e:
        logger.error(f"Get spam reports error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
