"""
Advanced Analytics Engine for Bot Management
Real-time metrics, trends, predictions, and insights
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel
import statistics
from collections import defaultdict

logger = logging.getLogger(__name__)


# ============================================================================
# MODELS
# ============================================================================

class AnalyticsMetric(str, Enum):
    """Available metrics for analysis"""
    DAILY_ACTIVE_USERS = "daily_active_users"
    USER_RETENTION = "user_retention"
    ACTION_FREQUENCY = "action_frequency"
    MODERATION_EFFECTIVENESS = "moderation_effectiveness"
    GROUP_GROWTH_RATE = "group_growth_rate"
    RULE_VIOLATIONS = "rule_violations"
    USER_ENGAGEMENT = "user_engagement"
    ADMIN_ACTIVITY = "admin_activity"


class MetricData(BaseModel):
    """Single metric data point"""
    timestamp: datetime
    value: float
    metadata: Optional[Dict[str, Any]] = None


class AnalyticsSummary(BaseModel):
    """Complete analytics summary"""
    metric: str
    total: float
    average: float
    min: float
    max: float
    trend: str  # "up", "down", "stable"
    change_percentage: float
    period_days: int
    data_points: List[MetricData]


class InsightReport(BaseModel):
    """AI-like insights and recommendations"""
    group_id: int
    timestamp: datetime
    insights: List[str]
    recommendations: List[str]
    alerts: List[Dict[str, Any]]
    health_score: float  # 0-100


# ============================================================================
# ANALYTICS ENGINE
# ============================================================================

class AnalyticsEngine:
    """Advanced analytics and insights generation"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.metrics_cache = defaultdict(list)
        
    async def calculate_daily_active_users(
        self, 
        group_id: int, 
        days: int = 30
    ) -> AnalyticsSummary:
        """Calculate daily active users for a group"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        pipeline = [
            {
                "$match": {
                    "group_id": group_id,
                    "timestamp": {"$gte": start_date}
                }
            },
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$timestamp"
                        }
                    },
                    "unique_users": {"$addToSet": "$user_id"},
                    "count": {"$sum": 1}
                }
            },
            {
                "$project": {
                    "date": "$_id",
                    "active_users": {"$size": "$unique_users"},
                    "actions": "$count"
                }
            },
            {"$sort": {"date": 1}}
        ]
        
        results = await self.db.aggregate_actions(pipeline)
        
        values = [r["active_users"] for r in results]
        if not values:
            values = [0]
        
        return AnalyticsSummary(
            metric="daily_active_users",
            total=sum(values),
            average=statistics.mean(values),
            min=min(values),
            max=max(values),
            trend=self._calculate_trend(values),
            change_percentage=self._calculate_change(values),
            period_days=days,
            data_points=[
                MetricData(
                    timestamp=datetime.fromisoformat(r["date"]),
                    value=r["active_users"]
                )
                for r in results
            ]
        )
    
    async def calculate_retention_rate(
        self,
        group_id: int,
        cohort_days: int = 7
    ) -> Dict[str, float]:
        """Calculate user retention cohort analysis"""
        pipeline = [
            {
                "$match": {"group_id": group_id}
            },
            {
                "$group": {
                    "_id": "$user_id",
                    "first_action": {"$min": "$timestamp"},
                    "last_action": {"$max": "$timestamp"},
                    "action_count": {"$sum": 1}
                }
            }
        ]
        
        users = await self.db.aggregate_actions(pipeline)
        
        # Cohort analysis
        cohorts = defaultdict(list)
        for user in users:
            first_week = user["first_action"].isocalendar()[1]
            cohorts[first_week].append(user)
        
        retention = {}
        for week, cohort_users in cohorts.items():
            # Users still active after cohort_days
            still_active = sum(
                1 for u in cohort_users
                if (u["last_action"] - u["first_action"]).days >= cohort_days
            )
            retention[f"week_{week}"] = (
                still_active / len(cohort_users) * 100
                if cohort_users else 0
            )
        
        return retention
    
    async def calculate_moderation_effectiveness(
        self,
        group_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """Calculate moderation action effectiveness"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        pipeline = [
            {
                "$match": {
                    "group_id": group_id,
                    "action_type": {"$in": ["ban", "mute", "kick", "warn"]},
                    "timestamp": {"$gte": start_date}
                }
            },
            {
                "$group": {
                    "_id": "$action_type",
                    "count": {"$sum": 1},
                    "unique_users": {"$addToSet": "$user_id"}
                }
            }
        ]
        
        results = await self.db.aggregate_actions(pipeline)
        
        return {
            "period_days": days,
            "actions_by_type": {
                r["_id"]: {
                    "count": r["count"],
                    "unique_users": len(r["unique_users"])
                }
                for r in results
            },
            "total_moderation_actions": sum(r["count"] for r in results),
            "effectiveness_score": self._calculate_effectiveness(results)
        }
    
    async def get_group_health_score(
        self,
        group_id: int
    ) -> InsightReport:
        """
        Calculate overall group health (0-100)
        Based on:
        - User retention
        - Rule violations
        - Moderation effectiveness
        - Admin activity
        """
        
        # Gather metrics
        dau = await self.calculate_daily_active_users(group_id, days=7)
        retention = await self.calculate_retention_rate(group_id)
        moderation = await self.calculate_moderation_effectiveness(group_id)
        
        # Calculate health components
        retention_score = (
            statistics.mean(retention.values())
            if retention else 50
        )
        
        # Rule violations score (inverse)
        violations_pipeline = [
            {
                "$match": {
                    "group_id": group_id,
                    "rule_violated": True
                }
            },
            {"$count": "total"}
        ]
        violation_result = await self.db.aggregate_actions(violations_pipeline)
        violation_count = (
            violation_result[0]["total"]
            if violation_result else 0
        )
        violations_score = max(0, 100 - min(violation_count / 10, 50))
        
        # Admin activity score
        admin_score = min(
            moderation["total_moderation_actions"] * 10,
            100
        )
        
        # Combine scores
        health_score = (
            retention_score * 0.3 +
            violations_score * 0.3 +
            admin_score * 0.4
        )
        
        # Generate insights
        insights = self._generate_insights(
            dau, retention, moderation, health_score
        )
        recommendations = self._generate_recommendations(
            insights, health_score
        )
        alerts = self._generate_alerts(
            dau, retention, moderation
        )
        
        return InsightReport(
            group_id=group_id,
            timestamp=datetime.utcnow(),
            insights=insights,
            recommendations=recommendations,
            alerts=alerts,
            health_score=health_score
        )
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Determine if trend is up, down, or stable"""
        if len(values) < 2:
            return "stable"
        
        recent = statistics.mean(values[-3:]) if len(values) >= 3 else values[-1]
        older = statistics.mean(values[:3]) if len(values) >= 3 else values[0]
        
        change = ((recent - older) / (older or 1)) * 100
        
        if change > 10:
            return "up"
        elif change < -10:
            return "down"
        else:
            return "stable"
    
    def _calculate_change(self, values: List[float]) -> float:
        """Calculate percentage change from start to end"""
        if len(values) < 2:
            return 0
        
        if values[0] == 0:
            return 0
        
        return ((values[-1] - values[0]) / values[0]) * 100
    
    def _calculate_effectiveness(self, results: List[Dict]) -> float:
        """Calculate moderation effectiveness score (0-100)"""
        if not results:
            return 0
        
        # More variety in actions = higher effectiveness
        action_types = len(results)
        avg_actions_per_type = statistics.mean(
            [r["count"] for r in results]
        )
        
        return min(
            (action_types / 4) * 50 + (avg_actions_per_type / 10) * 50,
            100
        )
    
    def _generate_insights(
        self,
        dau: AnalyticsSummary,
        retention: Dict,
        moderation: Dict,
        health_score: float
    ) -> List[str]:
        """Generate actionable insights"""
        insights = []
        
        # DAU insights
        if dau.trend == "up":
            insights.append(
                f"✅ Daily active users trending UP ({dau.change_percentage:+.1f}%)"
            )
        elif dau.trend == "down":
            insights.append(
                f"⚠️ Daily active users trending DOWN ({dau.change_percentage:+.1f}%)"
            )
        
        # Retention insights
        avg_retention = (
            statistics.mean(retention.values())
            if retention else 0
        )
        if avg_retention > 70:
            insights.append("🎯 Excellent user retention rate")
        elif avg_retention < 40:
            insights.append("❌ Low user retention - consider engagement initiatives")
        
        # Moderation insights
        total_actions = moderation.get("total_moderation_actions", 0)
        if total_actions > 50:
            insights.append(f"🛡️ High moderation activity ({total_actions} actions)")
        elif total_actions == 0:
            insights.append("⚠️ No moderation activity detected")
        
        # Health insights
        if health_score >= 80:
            insights.append("🌟 Group health is EXCELLENT")
        elif health_score >= 60:
            insights.append("👍 Group health is GOOD")
        elif health_score >= 40:
            insights.append("⚠️ Group health needs IMPROVEMENT")
        else:
            insights.append("🔴 Group health is CRITICAL")
        
        return insights
    
    def _generate_recommendations(
        self,
        insights: List[str],
        health_score: float
    ) -> List[str]:
        """Generate recommendations based on health"""
        recommendations = []
        
        if health_score < 40:
            recommendations.extend([
                "1️⃣ Increase admin presence and activity",
                "2️⃣ Review and enforce group rules more strictly",
                "3️⃣ Engage inactive users with promotions/events",
                "4️⃣ Update group welcome message"
            ])
        elif health_score < 60:
            recommendations.extend([
                "1️⃣ Monitor moderation metrics closely",
                "2️⃣ Consider engaging loyal members as moderators",
                "3️⃣ Plan group activities to boost engagement"
            ])
        else:
            recommendations.append(
                "✅ Maintain current moderation strategy - it's working!"
            )
        
        return recommendations
    
    def _generate_alerts(
        self,
        dau: AnalyticsSummary,
        retention: Dict,
        moderation: Dict
    ) -> List[Dict[str, Any]]:
        """Generate alerts for critical issues"""
        alerts = []
        
        # DAU drop alert
        if dau.trend == "down" and dau.change_percentage < -30:
            alerts.append({
                "severity": "high",
                "title": "⚠️ Significant user drop detected",
                "description": f"DAU decreased by {abs(dau.change_percentage):.1f}%",
                "action": "Investigate recent moderation or policy changes"
            })
        
        # Retention alert
        avg_retention = (
            statistics.mean(retention.values())
            if retention else 0
        )
        if avg_retention < 30:
            alerts.append({
                "severity": "high",
                "title": "❌ Critical retention issue",
                "description": "Less than 30% of users return after first week",
                "action": "Review onboarding process and group culture"
            })
        
        # Inactivity alert
        if dau.average < 5:
            alerts.append({
                "severity": "medium",
                "title": "😴 Group appears inactive",
                "description": f"Average {dau.average:.0f} active users per day",
                "action": "Plan engagement campaign or content update"
            })
        
        return alerts
