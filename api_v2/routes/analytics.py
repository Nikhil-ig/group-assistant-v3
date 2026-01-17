"""
Analytics and Statistics Routes
Provides endpoints for group and user statistics
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Query
from pymongo import MongoClient
import os

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v2", tags=["analytics"])

# Database connection
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
client = MongoClient(MONGODB_URL)
db = client["group_assistant"]


@router.get("/groups/{group_id}/stats", response_model=Dict[str, Any])
async def get_group_stats(group_id: int, days: int = Query(7, ge=1, le=365)):
    """Get group statistics for the last N days"""
    try:
        stats_collection = db["statistics"]
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get message count
        messages = db["messages"].count_documents({
            "group_id": group_id,
            "created_at": {"$gte": start_date, "$lte": end_date}
        })
        
        # Get active users
        active_users = len(db["messages"].distinct("user_id", {
            "group_id": group_id,
            "created_at": {"$gte": start_date, "$lte": end_date}
        }))
        
        # Get admin actions count
        actions = db["actions"].count_documents({
            "group_id": group_id,
            "created_at": {"$gte": start_date, "$lte": end_date}
        })
        
        # Get most active user
        pipeline = [
            {"$match": {
                "group_id": group_id,
                "created_at": {"$gte": start_date, "$lte": end_date}
            }},
            {"$group": {
                "_id": "$user_id",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}},
            {"$limit": 1}
        ]
        most_active = list(db["messages"].aggregate(pipeline))
        
        return {
            "success": True,
            "data": {
                "group_id": group_id,
                "period_days": days,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_messages": messages,
                "active_users": active_users,
                "admin_actions": actions,
                "most_active_user": most_active[0]["_id"] if most_active else None,
                "most_active_count": most_active[0]["count"] if most_active else 0
            }
        }
    except Exception as e:
        logger.error(f"Get group stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}/stats", response_model=Dict[str, Any])
async def get_user_stats(user_id: int, group_id: Optional[int] = None, days: int = Query(7, ge=1, le=365)):
    """Get user statistics"""
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        query = {
            "user_id": user_id,
            "created_at": {"$gte": start_date, "$lte": end_date}
        }
        
        if group_id:
            query["group_id"] = group_id
        
        # Get message count
        messages = db["messages"].count_documents(query)
        
        # Get groups active in
        active_groups = db["messages"].distinct("group_id", query)
        
        # Get average messages per day
        avg_per_day = messages / days if days > 0 else 0
        
        # Get mute/ban history
        actions_query = {
            "user_id": user_id,
            "created_at": {"$gte": start_date, "$lte": end_date}
        }
        if group_id:
            actions_query["group_id"] = group_id
            
        actions_taken = db["actions"].count_documents(actions_query)
        
        return {
            "success": True,
            "data": {
                "user_id": user_id,
                "period_days": days,
                "total_messages": messages,
                "active_in_groups": len(active_groups),
                "avg_messages_per_day": round(avg_per_day, 2),
                "actions_against_user": actions_taken,
                "last_message_date": None  # Can be enhanced
            }
        }
    except Exception as e:
        logger.error(f"Get user stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/groups/{group_id}/stats/leaderboard", response_model=Dict[str, Any])
async def get_leaderboard(group_id: int, limit: int = Query(10, ge=1, le=100), days: int = Query(7, ge=1, le=365)):
    """Get top users by message count (leaderboard)"""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        pipeline = [
            {"$match": {
                "group_id": group_id,
                "created_at": {"$gte": start_date, "$lte": end_date}
            }},
            {"$group": {
                "_id": "$user_id",
                "message_count": {"$sum": 1}
            }},
            {"$sort": {"message_count": -1}},
            {"$limit": limit}
        ]
        
        leaderboard = list(db["messages"].aggregate(pipeline))
        
        return {
            "success": True,
            "data": {
                "group_id": group_id,
                "period_days": days,
                "leaderboard": [
                    {
                        "rank": idx + 1,
                        "user_id": item["_id"],
                        "messages": item["message_count"]
                    }
                    for idx, item in enumerate(leaderboard)
                ]
            }
        }
    except Exception as e:
        logger.error(f"Get leaderboard error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/groups/{group_id}/stats/messages", response_model=Dict[str, Any])
async def get_message_stats(group_id: int, days: int = Query(7, ge=1, le=365)):
    """Get detailed message statistics with hourly breakdown"""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        pipeline = [
            {"$match": {
                "group_id": group_id,
                "created_at": {"$gte": start_date, "$lte": end_date}
            }},
            {"$group": {
                "_id": {
                    "day": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                    "hour": {"$hour": "$created_at"}
                },
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]
        
        hourly_stats = list(db["messages"].aggregate(pipeline))
        
        # Get daily totals
        daily_pipeline = [
            {"$match": {
                "group_id": group_id,
                "created_at": {"$gte": start_date, "$lte": end_date}
            }},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]
        
        daily_stats = list(db["messages"].aggregate(daily_pipeline))
        
        return {
            "success": True,
            "data": {
                "group_id": group_id,
                "period_days": days,
                "daily_breakdown": daily_stats,
                "hourly_breakdown": hourly_stats,
                "total_messages": sum(item["count"] for item in daily_stats)
            }
        }
    except Exception as e:
        logger.error(f"Get message stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
