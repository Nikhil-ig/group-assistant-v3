"""
Advanced Features Routes - FastAPI endpoints for all new features
Analytics, Automation, Moderation, and Advanced Management
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime, timedelta
from api_v2.features import (
    AnalyticsEngine, 
    AutomationEngine, 
    ModerationEngine
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2", tags=["advanced-features"])


# Global engines (will be initialized in app startup)
analytics_engine: Optional[AnalyticsEngine] = None
automation_engine: Optional[AutomationEngine] = None
moderation_engine: Optional[ModerationEngine] = None


def set_engines(analytics, automation, moderation):
    """Initialize engines"""
    global analytics_engine, automation_engine, moderation_engine
    analytics_engine = analytics
    automation_engine = automation
    moderation_engine = moderation


# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@router.get("/groups/{group_id}/analytics/dau")
async def get_daily_active_users(
    group_id: int,
    days: int = Query(30, ge=1, le=365)
):
    """Get daily active users analytics"""
    if not analytics_engine:
        raise HTTPException(status_code=500, detail="Analytics engine not initialized")
    
    try:
        summary = await analytics_engine.calculate_daily_active_users(group_id, days)
        return {
            "status": "success",
            "data": summary.dict()
        }
    except Exception as e:
        logger.error(f"Analytics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/groups/{group_id}/analytics/retention")
async def get_retention_analytics(
    group_id: int,
    cohort_days: int = Query(7, ge=1, le=90)
):
    """Get user retention analytics"""
    if not analytics_engine:
        raise HTTPException(status_code=500, detail="Analytics engine not initialized")
    
    try:
        retention = await analytics_engine.calculate_retention_rate(group_id, cohort_days)
        return {
            "status": "success",
            "retention_rates": retention,
            "cohort_days": cohort_days
        }
    except Exception as e:
        logger.error(f"Retention analytics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/groups/{group_id}/analytics/moderation-effectiveness")
async def get_moderation_effectiveness(
    group_id: int,
    days: int = Query(30, ge=1, le=365)
):
    """Get moderation effectiveness metrics"""
    if not analytics_engine:
        raise HTTPException(status_code=500, detail="Analytics engine not initialized")
    
    try:
        effectiveness = await analytics_engine.calculate_moderation_effectiveness(group_id, days)
        return {
            "status": "success",
            "data": effectiveness
        }
    except Exception as e:
        logger.error(f"Moderation effectiveness error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/groups/{group_id}/analytics/health")
async def get_group_health_score(group_id: int):
    """
    Get comprehensive group health score (0-100)
    Combines DAU, retention, moderation, and rule violations
    """
    if not analytics_engine:
        raise HTTPException(status_code=500, detail="Analytics engine not initialized")
    
    try:
        health = await analytics_engine.get_group_health_score(group_id)
        return {
            "status": "success",
            "health_score": health.health_score,
            "insights": health.insights,
            "recommendations": health.recommendations,
            "alerts": health.alerts
        }
    except Exception as e:
        logger.error(f"Health score error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# AUTOMATION ENDPOINTS
# ============================================================================

@router.post("/groups/{group_id}/automation/rules")
async def create_automation_rule(
    group_id: int,
    name: str,
    trigger: dict,
    action: dict,
    condition: Optional[dict] = None
):
    """Create an automation rule"""
    if not automation_engine:
        raise HTTPException(status_code=500, detail="Automation engine not initialized")
    
    try:
        rule = await automation_engine.create_automation_rule(
            group_id, name, trigger, action, condition
        )
        return {
            "status": "success",
            "rule": rule.dict()
        }
    except Exception as e:
        logger.error(f"Create rule error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/groups/{group_id}/automation/scheduled-tasks")
async def create_scheduled_task(
    group_id: int,
    name: str,
    schedule_type: str,
    schedule_config: dict,
    action: dict
):
    """Create a scheduled task"""
    if not automation_engine:
        raise HTTPException(status_code=500, detail="Automation engine not initialized")
    
    try:
        from api_v2.features.automation import ScheduleType
        
        task = await automation_engine.create_scheduled_task(
            name,
            ScheduleType(schedule_type),
            schedule_config,
            action,
            group_id
        )
        return {
            "status": "success",
            "task": task.dict()
        }
    except Exception as e:
        logger.error(f"Create scheduled task error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/groups/{group_id}/automation/workflows")
async def create_workflow(
    group_id: int,
    name: str,
    steps: List[dict]
):
    """Create a multi-step workflow"""
    if not automation_engine:
        raise HTTPException(status_code=500, detail="Automation engine not initialized")
    
    try:
        workflow = await automation_engine.create_workflow(group_id, name, steps)
        return {
            "status": "success",
            "workflow": workflow
        }
    except Exception as e:
        logger.error(f"Create workflow error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/groups/{group_id}/automation/workflows/{workflow_id}/execute")
async def execute_workflow(
    group_id: int,
    workflow_id: str,
    context: dict
):
    """Execute a workflow"""
    if not automation_engine:
        raise HTTPException(status_code=500, detail="Automation engine not initialized")
    
    try:
        execution = await automation_engine.execute_workflow(workflow_id, context)
        return {
            "status": "success",
            "execution": execution.dict()
        }
    except Exception as e:
        logger.error(f"Execute workflow error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/groups/{group_id}/automation/metrics")
async def get_automation_metrics(group_id: int):
    """Get automation execution metrics"""
    if not automation_engine:
        raise HTTPException(status_code=500, detail="Automation engine not initialized")
    
    try:
        metrics = await automation_engine.get_automation_metrics(group_id)
        return {
            "status": "success",
            "metrics": metrics
        }
    except Exception as e:
        logger.error(f"Get automation metrics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MODERATION ENDPOINTS
# ============================================================================

@router.post("/groups/{group_id}/moderation/analyze")
async def analyze_message(
    group_id: int,
    message_id: int,
    user_id: int,
    content: str
):
    """Analyze a message for content moderation"""
    if not moderation_engine:
        raise HTTPException(status_code=500, detail="Moderation engine not initialized")
    
    try:
        result = await moderation_engine.analyze_message(
            message_id, user_id, group_id, content
        )
        return {
            "status": "success",
            "result": result.dict()
        }
    except Exception as e:
        logger.error(f"Message analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/groups/{group_id}/moderation/user-profile/{user_id}")
async def get_user_behavior_profile(group_id: int, user_id: int):
    """Get user behavior profile and risk assessment"""
    if not moderation_engine:
        raise HTTPException(status_code=500, detail="Moderation engine not initialized")
    
    try:
        profile = await moderation_engine.analyze_user_behavior(user_id, group_id)
        return {
            "status": "success",
            "profile": profile.dict()
        }
    except Exception as e:
        logger.error(f"User profile error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/groups/{group_id}/moderation/duplicate-detection")
async def detect_duplicate_content(
    group_id: int,
    content_hash: str
):
    """Detect duplicate/spam messages"""
    if not moderation_engine:
        raise HTTPException(status_code=500, detail="Moderation engine not initialized")
    
    try:
        result = await moderation_engine.detect_duplicate_content(group_id, content_hash)
        return {
            "status": "success",
            "result": result
        }
    except Exception as e:
        logger.error(f"Duplicate detection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/groups/{group_id}/moderation/stats")
async def get_moderation_stats(group_id: int):
    """Get moderation statistics"""
    if not moderation_engine:
        raise HTTPException(status_code=500, detail="Moderation engine not initialized")
    
    try:
        stats = moderation_engine.get_moderation_stats(group_id)
        return {
            "status": "success",
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Get moderation stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/features/health")
async def check_features_health():
    """Check if all advanced features are initialized"""
    return {
        "status": "ok",
        "analytics": analytics_engine is not None,
        "automation": automation_engine is not None,
        "moderation": moderation_engine is not None,
        "timestamp": datetime.utcnow()
    }
