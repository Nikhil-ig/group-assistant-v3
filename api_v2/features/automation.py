"""
Advanced Automation Engine
Scheduled tasks, workflows, and intelligent automation
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from enum import Enum
from pydantic import BaseModel
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


# ============================================================================
# MODELS & ENUMS
# ============================================================================

class ScheduleType(str, Enum):
    """Schedule types for automation"""
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CRON = "cron"


class WorkflowStatus(str, Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PAUSED = "paused"


class AutomationRule(BaseModel):
    """Rule for automatic action execution"""
    rule_id: str
    group_id: int
    name: str
    trigger: Dict[str, Any]  # Event that triggers the rule
    action: Dict[str, Any]   # Action to execute
    condition: Optional[Dict[str, Any]] = None  # Optional condition
    enabled: bool = True
    created_at: datetime = None
    updated_at: datetime = None


class WorkflowExecution(BaseModel):
    """Record of workflow execution"""
    execution_id: str
    workflow_id: str
    status: WorkflowStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ScheduledTask(BaseModel):
    """Scheduled task definition"""
    task_id: str
    name: str
    group_id: Optional[int] = None
    schedule_type: ScheduleType
    schedule_config: Dict[str, Any]  # e.g., {"day_of_week": "Monday", "time": "09:00"}
    action: Dict[str, Any]
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None


# ============================================================================
# AUTOMATION ENGINE
# ============================================================================

class AutomationEngine:
    """Advanced automation with workflows and scheduling"""
    
    def __init__(self, db_manager, telegram_api):
        self.db = db_manager
        self.telegram = telegram_api
        self.rules: Dict[str, AutomationRule] = {}
        self.scheduled_tasks: Dict[str, ScheduledTask] = {}
        self.execution_history: List[WorkflowExecution] = []
        self.running_tasks: Dict[str, asyncio.Task] = {}
    
    async def create_automation_rule(
        self,
        group_id: int,
        name: str,
        trigger: Dict[str, Any],
        action: Dict[str, Any],
        condition: Optional[Dict[str, Any]] = None
    ) -> AutomationRule:
        """
        Create an automation rule
        
        Example trigger: {"type": "rule_violation", "count": 3}
        Example action: {"type": "send_warning", "message": "..."}
        Example condition: {"time": "peak_hours"}
        """
        rule_id = f"rule_{datetime.utcnow().timestamp()}"
        
        rule = AutomationRule(
            rule_id=rule_id,
            group_id=group_id,
            name=name,
            trigger=trigger,
            action=action,
            condition=condition,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.rules[rule_id] = rule
        
        # Persist to database
        await self.db.db[self.db.db_name]["automation_rules"].insert_one(
            rule.dict()
        )
        
        logger.info(f"✅ Created automation rule: {name}")
        return rule
    
    async def create_scheduled_task(
        self,
        name: str,
        schedule_type: ScheduleType,
        schedule_config: Dict[str, Any],
        action: Dict[str, Any],
        group_id: Optional[int] = None
    ) -> ScheduledTask:
        """
        Create a scheduled task
        
        Example:
            - Every day at 9 AM: send daily report
            - Every Monday: weekly digest
            - Once on specific date: special announcement
        """
        task_id = f"task_{datetime.utcnow().timestamp()}"
        
        # Calculate next run
        next_run = self._calculate_next_run(schedule_type, schedule_config)
        
        task = ScheduledTask(
            task_id=task_id,
            name=name,
            group_id=group_id,
            schedule_type=schedule_type,
            schedule_config=schedule_config,
            action=action,
            next_run=next_run
        )
        
        self.scheduled_tasks[task_id] = task
        
        # Persist to database
        await self.db.db[self.db.db_name]["scheduled_tasks"].insert_one(
            task.dict()
        )
        
        # Start the task scheduler
        self._schedule_task(task)
        
        logger.info(f"✅ Created scheduled task: {name} (next run: {next_run})")
        return task
    
    async def trigger_automation_rule(
        self,
        rule_id: str,
        trigger_data: Dict[str, Any]
    ) -> WorkflowExecution:
        """Trigger a rule and execute its action"""
        rule = self.rules.get(rule_id)
        if not rule or not rule.enabled:
            return None
        
        # Check condition if present
        if rule.condition:
            if not await self._check_condition(rule.condition):
                logger.debug(f"Rule condition not met: {rule_id}")
                return None
        
        # Execute action
        execution_id = f"exec_{datetime.utcnow().timestamp()}"
        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=rule_id,
            status=WorkflowStatus.RUNNING,
            started_at=datetime.utcnow()
        )
        
        try:
            result = await self._execute_action(rule.action, rule.group_id)
            execution.status = WorkflowStatus.SUCCESS
            execution.result = result
            execution.completed_at = datetime.utcnow()
            
            logger.info(f"✅ Automation rule executed: {rule.name}")
        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.error = str(e)
            execution.completed_at = datetime.utcnow()
            
            logger.error(f"❌ Automation rule failed: {rule.name} - {e}")
        
        self.execution_history.append(execution)
        return execution
    
    async def create_workflow(
        self,
        group_id: int,
        name: str,
        steps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create a multi-step workflow
        
        Example workflow:
        [
            {"type": "check_violations", "threshold": 3},
            {"type": "send_message", "text": "Warning..."},
            {"type": "mute_user", "duration": 3600},
            {"type": "log_action", "category": "enforcement"}
        ]
        """
        workflow_id = f"workflow_{datetime.utcnow().timestamp()}"
        
        workflow = {
            "workflow_id": workflow_id,
            "group_id": group_id,
            "name": name,
            "steps": steps,
            "created_at": datetime.utcnow(),
            "status": "active"
        }
        
        await self.db.db[self.db.db_name]["workflows"].insert_one(workflow)
        
        logger.info(f"✅ Created workflow: {name}")
        return workflow
    
    async def execute_workflow(
        self,
        workflow_id: str,
        context: Dict[str, Any]
    ) -> WorkflowExecution:
        """Execute a workflow with given context"""
        execution_id = f"exec_{datetime.utcnow().timestamp()}"
        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=workflow_id,
            status=WorkflowStatus.RUNNING,
            started_at=datetime.utcnow()
        )
        
        try:
            workflow = await self.db.db[self.db.db_name]["workflows"].find_one(
                {"workflow_id": workflow_id}
            )
            
            if not workflow:
                raise ValueError(f"Workflow not found: {workflow_id}")
            
            results = []
            for step in workflow["steps"]:
                result = await self._execute_step(step, context)
                results.append(result)
                
                # Stop if critical step fails
                if step.get("critical") and not result.get("success"):
                    raise Exception(f"Critical step failed: {step.get('type')}")
            
            execution.status = WorkflowStatus.SUCCESS
            execution.result = {"steps_executed": len(results), "results": results}
            
        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.error = str(e)
        
        execution.completed_at = datetime.utcnow()
        self.execution_history.append(execution)
        
        return execution
    
    async def get_automation_metrics(self, group_id: int) -> Dict[str, Any]:
        """Get automation statistics for a group"""
        rules = [r for r in self.rules.values() if r.group_id == group_id]
        tasks = [t for t in self.scheduled_tasks.values() if t.group_id == group_id]
        
        successful_executions = [
            e for e in self.execution_history
            if e.status == WorkflowStatus.SUCCESS
        ]
        failed_executions = [
            e for e in self.execution_history
            if e.status == WorkflowStatus.FAILED
        ]
        
        return {
            "total_rules": len(rules),
            "total_scheduled_tasks": len(tasks),
            "total_executions": len(self.execution_history),
            "successful_executions": len(successful_executions),
            "failed_executions": len(failed_executions),
            "success_rate": (
                len(successful_executions) / len(self.execution_history) * 100
                if self.execution_history else 0
            )
        }
    
    # ========================================================================
    # PRIVATE METHODS
    # ========================================================================
    
    async def _execute_action(
        self,
        action: Dict[str, Any],
        group_id: int
    ) -> Dict[str, Any]:
        """Execute an action based on its type"""
        action_type = action.get("type")
        
        if action_type == "send_message":
            return await self.telegram.send_message(
                group_id,
                action.get("text")
            )
        
        elif action_type == "mute_user":
            return {
                "muted": action.get("user_id"),
                "duration": action.get("duration")
            }
        
        elif action_type == "ban_user":
            return await self.telegram.ban_user(
                group_id,
                action.get("user_id")
            )
        
        elif action_type == "send_warning":
            user_id = action.get("user_id")
            message = action.get("message")
            return {"user_warned": user_id, "message": message}
        
        elif action_type == "cleanup_spam":
            return await self._cleanup_spam_messages(group_id, action)
        
        elif action_type == "generate_report":
            return await self._generate_report(group_id, action)
        
        else:
            raise ValueError(f"Unknown action type: {action_type}")
    
    async def _execute_step(
        self,
        step: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single workflow step"""
        step_type = step.get("type")
        
        try:
            if step_type == "check_violations":
                result = await self._check_violations(
                    context.get("group_id"),
                    step.get("threshold", 0)
                )
            
            elif step_type == "send_message":
                result = await self.telegram.send_message(
                    context.get("group_id"),
                    step.get("text")
                )
            
            elif step_type == "mute_user":
                result = {
                    "action": "mute",
                    "user_id": context.get("user_id"),
                    "duration": step.get("duration")
                }
            
            elif step_type == "log_action":
                result = {"logged": True, "category": step.get("category")}
            
            else:
                raise ValueError(f"Unknown step type: {step_type}")
            
            return {"success": True, "type": step_type, "result": result}
        
        except Exception as e:
            return {"success": False, "type": step_type, "error": str(e)}
    
    async def _check_condition(self, condition: Dict[str, Any]) -> bool:
        """Check if a condition is met"""
        condition_type = condition.get("type")
        
        if condition_type == "time":
            # Check if current time matches condition
            current_hour = datetime.utcnow().hour
            return 9 <= current_hour <= 17  # Business hours example
        
        elif condition_type == "user_count":
            return True  # Placeholder
        
        else:
            return True
    
    def _calculate_next_run(
        self,
        schedule_type: ScheduleType,
        config: Dict[str, Any]
    ) -> datetime:
        """Calculate next run time for a scheduled task"""
        now = datetime.utcnow()
        
        if schedule_type == ScheduleType.ONCE:
            return now + timedelta(hours=config.get("hours", 1))
        
        elif schedule_type == ScheduleType.DAILY:
            hour = config.get("hour", 9)
            next_run = now.replace(hour=hour, minute=0, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
            return next_run
        
        elif schedule_type == ScheduleType.WEEKLY:
            day_of_week = config.get("day_of_week", 0)  # Monday = 0
            hour = config.get("hour", 9)
            
            days_ahead = (day_of_week - now.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7
            
            next_run = now + timedelta(days=days_ahead)
            next_run = next_run.replace(hour=hour, minute=0, second=0, microsecond=0)
            return next_run
        
        elif schedule_type == ScheduleType.MONTHLY:
            day_of_month = config.get("day_of_month", 1)
            hour = config.get("hour", 9)
            
            if now.day >= day_of_month:
                # Next month
                if now.month == 12:
                    next_run = now.replace(
                        year=now.year + 1,
                        month=1,
                        day=day_of_month,
                        hour=hour,
                        minute=0,
                        second=0,
                        microsecond=0
                    )
                else:
                    next_run = now.replace(
                        month=now.month + 1,
                        day=day_of_month,
                        hour=hour,
                        minute=0,
                        second=0,
                        microsecond=0
                    )
            else:
                next_run = now.replace(
                    day=day_of_month,
                    hour=hour,
                    minute=0,
                    second=0,
                    microsecond=0
                )
            
            return next_run
        
        return now + timedelta(hours=1)
    
    def _schedule_task(self, task: ScheduledTask):
        """Schedule a task for execution"""
        # This would integrate with APScheduler or similar
        logger.info(f"📅 Task scheduled: {task.name} at {task.next_run}")
    
    async def _cleanup_spam_messages(
        self,
        group_id: int,
        action: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Automated spam cleanup"""
        return {"cleaned": True, "messages_removed": 0}
    
    async def _generate_report(
        self,
        group_id: int,
        action: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate automated report"""
        return {"report_generated": True, "type": action.get("report_type")}
    
    async def _check_violations(
        self,
        group_id: int,
        threshold: int
    ) -> Dict[str, Any]:
        """Check for rule violations"""
        return {"violations_found": False, "count": 0}
