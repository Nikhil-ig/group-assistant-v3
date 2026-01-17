"""
Whitelist/Blacklist Management Routes
Handles exemptions, moderator assignments, and blocking
"""

import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Body, Query
from pydantic import BaseModel

from api_v2.models.schemas import (
    WhitelistCreate, WhitelistUpdate, WhitelistResponse,
    BlacklistCreate, BlacklistUpdate, BlacklistResponse
)
from api_v2.core.database import get_db_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v2", tags=["whitelist_blacklist"])


# ============================================================================
# WHITELIST MANAGEMENT
# ============================================================================

@router.post("/groups/{group_id}/whitelist", response_model=WhitelistResponse)
async def add_whitelist(group_id: int, entry: WhitelistCreate):
    """
    Add user to whitelist
    
    entry_type:
    - "exemption": User bypasses message restrictions (can send text/stickers/voice even if restricted)
    - "moderator": User gets non-admin powers (mute, unmute, warn, etc)
    
    admin_powers (for moderators):
    - "mute": Can mute users
    - "unmute": Can unmute users
    - "warn": Can warn users
    - "kick": Can kick users
    - "send_link": Can send links (bypass link restrictions)
    - "restrict": Can restrict user permissions
    - "unrestrict": Can unrestrict user permissions
    - "manage_stickers": Can manage sticker blacklist
    - "manage_links": Can manage link blacklist
    """
    try:
        db_manager = await get_db_manager()
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database not available")
        
        db = db_manager.client[db_manager.db_name]
        
        # Check if already whitelisted
        existing = await db.whitelists.find_one({
            "group_id": group_id,
            "user_id": entry.user_id
        })
        
        if existing and existing.get("is_active"):
            raise HTTPException(status_code=400, detail="User already whitelisted")
        
        # Create whitelist entry
        whitelist_doc = {
            "group_id": group_id,
            "user_id": entry.user_id,
            "username": entry.username,
            "entry_type": entry.entry_type,
            "admin_powers": entry.admin_powers or [],
            "reason": entry.reason,
            "added_by": entry.added_by,
            "added_at": datetime.now(),
            "updated_at": datetime.now(),
            "is_active": True
        }
        
        result = await db.whitelists.insert_one(whitelist_doc)
        whitelist_doc["_id"] = result.inserted_id
        
        logger.info(f"✅ Added to whitelist: group={group_id}, user={entry.user_id}, type={entry.entry_type}")
        return whitelist_doc
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding whitelist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/groups/{group_id}/whitelist", response_model=List[WhitelistResponse])
async def list_whitelist(group_id: int, entry_type: Optional[str] = None):
    """List whitelisted users"""
    try:
        db_manager = await get_db_manager()
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database not available")
        
        db = db_manager.client[db_manager.db_name]
        
        query = {"group_id": group_id, "is_active": True}
        if entry_type:
            query["entry_type"] = entry_type
        
        whitelist = await db.whitelists.find(query).to_list(1000)
        return whitelist
        
    except Exception as e:
        logger.error(f"Error listing whitelist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/groups/{group_id}/whitelist/{user_id}")
async def check_whitelist(group_id: int, user_id: int):
    """Check if user is whitelisted and their powers"""
    try:
        db_manager = await get_db_manager()
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database not available")
        
        db = db_manager.client[db_manager.db_name]
        
        entry = await db.whitelists.find_one({
            "group_id": group_id,
            "user_id": user_id,
            "is_active": True
        })
        
        if not entry:
            return {
                "whitelisted": False,
                "entry_type": None,
                "admin_powers": [],
                "reason": None
            }
        
        return {
            "whitelisted": True,
            "entry_type": entry.get("entry_type"),
            "admin_powers": entry.get("admin_powers", []),
            "reason": entry.get("reason"),
            "added_at": entry.get("added_at")
        }
        
    except Exception as e:
        logger.error(f"Error checking whitelist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/groups/{group_id}/whitelist/{user_id}")
async def update_whitelist(group_id: int, user_id: int, update: WhitelistUpdate):
    """Update whitelist entry"""
    try:
        db_manager = await get_db_manager()
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database not available")
        
        db = db_manager.client[db_manager.db_name]
        
        # Build update doc
        update_doc = {"updated_at": datetime.now()}
        if update.entry_type is not None:
            update_doc["entry_type"] = update.entry_type
        if update.admin_powers is not None:
            update_doc["admin_powers"] = update.admin_powers
        if update.reason is not None:
            update_doc["reason"] = update.reason
        if update.is_active is not None:
            update_doc["is_active"] = update.is_active
        
        result = await db.whitelists.update_one(
            {"group_id": group_id, "user_id": user_id},
            {"$set": update_doc}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Whitelist entry not found")
        
        # Return updated entry
        entry = await db.whitelists.find_one({"group_id": group_id, "user_id": user_id})
        return entry
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating whitelist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/groups/{group_id}/whitelist/{user_id}")
async def remove_whitelist(group_id: int, user_id: int):
    """Remove user from whitelist"""
    try:
        db_manager = await get_db_manager()
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database not available")
        
        db = db_manager.client[db_manager.db_name]
        
        result = await db.whitelists.update_one(
            {"group_id": group_id, "user_id": user_id},
            {"$set": {"is_active": False, "updated_at": datetime.now()}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Whitelist entry not found")
        
        logger.info(f"✅ Removed from whitelist: group={group_id}, user={user_id}")
        return {"success": True, "message": "Removed from whitelist"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing whitelist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# BLACKLIST MANAGEMENT
# ============================================================================

@router.post("/groups/{group_id}/blacklist", response_model=BlacklistResponse)
async def add_blacklist(group_id: int, entry: BlacklistCreate):
    """
    Add item to blacklist
    
    entry_type:
    - "user": Block specific user (user_id)
    - "sticker": Block specific sticker (sticker_id)
    - "gif": Block specific GIF (gif_id)
    - "link": Block specific link (URL)
    - "domain": Block entire domain (domain.com)
    """
    try:
        db_manager = await get_db_manager()
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database not available")
        
        db = db_manager.client[db_manager.db_name]
        
        # Check if already blacklisted
        existing = await db.blacklists.find_one({
            "group_id": group_id,
            "entry_type": entry.entry_type,
            "blocked_item": entry.blocked_item
        })
        
        if existing and existing.get("is_active"):
            raise HTTPException(status_code=400, detail="Item already blacklisted")
        
        # Create blacklist entry
        blacklist_doc = {
            "group_id": group_id,
            "entry_type": entry.entry_type,
            "blocked_item": entry.blocked_item,
            "reason": entry.reason,
            "added_by": entry.added_by,
            "added_at": datetime.now(),
            "updated_at": datetime.now(),
            "is_active": True,
            "auto_delete": entry.auto_delete
        }
        
        result = await db.blacklists.insert_one(blacklist_doc)
        blacklist_doc["_id"] = result.inserted_id
        
        logger.info(f"✅ Added to blacklist: group={group_id}, type={entry.entry_type}, item={entry.blocked_item}")
        return blacklist_doc
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding blacklist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/groups/{group_id}/blacklist", response_model=List[BlacklistResponse])
async def list_blacklist(group_id: int, entry_type: Optional[str] = None):
    """List blacklisted items"""
    try:
        db_manager = await get_db_manager()
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database not available")
        
        db = db_manager.client[db_manager.db_name]
        
        query = {"group_id": group_id, "is_active": True}
        if entry_type:
            query["entry_type"] = entry_type
        
        blacklist = await db.blacklists.find(query).to_list(10000)
        return blacklist
        
    except Exception as e:
        logger.error(f"Error listing blacklist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/groups/{group_id}/blacklist/check/{item_type}/{item_value}")
async def check_blacklist(group_id: int, item_type: str, item_value: str):
    """Check if item is blacklisted"""
    try:
        db_manager = await get_db_manager()
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database not available")
        
        db = db_manager.client[db_manager.db_name]
        
        # For domains, also check if any parent domain is blacklisted
        query = {
            "group_id": group_id,
            "entry_type": item_type,
            "blocked_item": item_value,
            "is_active": True
        }
        
        entry = await db.blacklists.find_one(query)
        
        # If checking a domain-based link, also check domain blacklist
        if item_type == "link" and not entry:
            try:
                from urllib.parse import urlparse
                domain = urlparse(item_value).netloc
                entry = await db.blacklists.find_one({
                    "group_id": group_id,
                    "entry_type": "domain",
                    "blocked_item": domain,
                    "is_active": True
                })
            except:
                pass
        
        if entry:
            return {
                "blacklisted": True,
                "reason": entry.get("reason"),
                "auto_delete": entry.get("auto_delete", True)
            }
        
        return {
            "blacklisted": False,
            "reason": None,
            "auto_delete": False
        }
        
    except Exception as e:
        logger.error(f"Error checking blacklist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/groups/{group_id}/blacklist/{blacklist_id}")
async def update_blacklist(group_id: int, blacklist_id: str, update: BlacklistUpdate):
    """Update blacklist entry"""
    try:
        from bson import ObjectId
        
        db_manager = await get_db_manager()
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database not available")
        
        db = db_manager.client[db_manager.db_name]
        
        update_doc = {"updated_at": datetime.now()}
        if update.reason is not None:
            update_doc["reason"] = update.reason
        if update.is_active is not None:
            update_doc["is_active"] = update.is_active
        if update.auto_delete is not None:
            update_doc["auto_delete"] = update.auto_delete
        
        result = await db.blacklists.update_one(
            {"_id": ObjectId(blacklist_id), "group_id": group_id},
            {"$set": update_doc}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Blacklist entry not found")
        
        entry = await db.blacklists.find_one({"_id": ObjectId(blacklist_id)})
        return entry
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating blacklist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/groups/{group_id}/blacklist/{blacklist_id}")
async def remove_blacklist(group_id: int, blacklist_id: str):
    """Remove item from blacklist"""
    try:
        from bson import ObjectId
        
        db_manager = await get_db_manager()
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database not available")
        
        db = db_manager.client[db_manager.db_name]
        
        result = await db.blacklists.update_one(
            {"_id": ObjectId(blacklist_id), "group_id": group_id},
            {"$set": {"is_active": False, "updated_at": datetime.now()}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Blacklist entry not found")
        
        logger.info(f"✅ Removed from blacklist: group={group_id}, blacklist_id={blacklist_id}")
        return {"success": True, "message": "Removed from blacklist"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing blacklist: {e}")
        raise HTTPException(status_code=500, detail=str(e))
