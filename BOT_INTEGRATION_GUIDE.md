# 🤖 BOT INTEGRATION GUIDE - Enhanced API V2

Complete guide for integrating the enhanced API V2 features with your Telegram bot.

---

## 📋 QUICK START

### Step 1: Install Dependencies

```bash
# Add to bot/requirements.txt
httpx>=0.24.0
aiohttp>=3.8.0
```

### Step 2: Create API Client

```python
# bot/api_client.py

import httpx
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class APIClient:
    """Client for API V2 enhanced features"""
    
    def __init__(self, base_url: str = "http://localhost:8002"):
        self.base_url = base_url
        self.client = None
    
    async def __aenter__(self):
        self.client = httpx.AsyncClient(base_url=self.base_url)
        return self
    
    async def __aexit__(self, *args):
        await self.client.aclose()
    
    # ====================================================================
    # ANALYTICS ENDPOINTS
    # ====================================================================
    
    async def get_dau(self, group_id: int, days: int = 30) -> Dict[str, Any]:
        """Get daily active users"""
        response = await self.client.get(
            f"/api/v2/groups/{group_id}/analytics/dau",
            params={"days": days}
        )
        return response.json()
    
    async def get_retention(self, group_id: int, cohort_days: int = 7) -> Dict[str, Any]:
        """Get retention analytics"""
        response = await self.client.get(
            f"/api/v2/groups/{group_id}/analytics/retention",
            params={"cohort_days": cohort_days}
        )
        return response.json()
    
    async def get_moderation_effectiveness(self, group_id: int, days: int = 30) -> Dict[str, Any]:
        """Get moderation effectiveness"""
        response = await self.client.get(
            f"/api/v2/groups/{group_id}/analytics/moderation-effectiveness",
            params={"days": days}
        )
        return response.json()
    
    async def get_health_score(self, group_id: int) -> Dict[str, Any]:
        """Get group health score with insights"""
        response = await self.client.get(
            f"/api/v2/groups/{group_id}/analytics/health"
        )
        return response.json()
    
    # ====================================================================
    # MODERATION ENDPOINTS
    # ====================================================================
    
    async def analyze_message(
        self,
        group_id: int,
        message_id: int,
        user_id: int,
        content: str
    ) -> Dict[str, Any]:
        """Analyze message for moderation"""
        response = await self.client.post(
            f"/api/v2/groups/{group_id}/moderation/analyze",
            json={
                "message_id": message_id,
                "user_id": user_id,
                "content": content
            }
        )
        return response.json()
    
    async def get_user_profile(self, group_id: int, user_id: int) -> Dict[str, Any]:
        """Get user behavior profile"""
        response = await self.client.get(
            f"/api/v2/groups/{group_id}/moderation/user-profile/{user_id}"
        )
        return response.json()
    
    async def detect_duplicate(self, group_id: int, content_hash: str) -> Dict[str, Any]:
        """Detect duplicate content"""
        response = await self.client.post(
            f"/api/v2/groups/{group_id}/moderation/duplicate-detection",
            json={"content_hash": content_hash}
        )
        return response.json()
    
    # ====================================================================
    # AUTOMATION ENDPOINTS
    # ====================================================================
    
    async def create_automation_rule(
        self,
        group_id: int,
        name: str,
        trigger: Dict[str, Any],
        action: Dict[str, Any],
        condition: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create automation rule"""
        response = await self.client.post(
            f"/api/v2/groups/{group_id}/automation/rules",
            json={
                "name": name,
                "trigger": trigger,
                "action": action,
                "condition": condition
            }
        )
        return response.json()
    
    async def create_scheduled_task(
        self,
        group_id: int,
        name: str,
        schedule_type: str,
        schedule_config: Dict[str, Any],
        action: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create scheduled task"""
        response = await self.client.post(
            f"/api/v2/groups/{group_id}/automation/scheduled-tasks",
            json={
                "name": name,
                "schedule_type": schedule_type,
                "schedule_config": schedule_config,
                "action": action
            }
        )
        return response.json()
    
    async def execute_workflow(
        self,
        group_id: int,
        workflow_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute workflow"""
        response = await self.client.post(
            f"/api/v2/groups/{group_id}/automation/workflows/{workflow_id}/execute",
            json={"context": context}
        )
        return response.json()
```

---

## 🛡️ MESSAGE MODERATION INTEGRATION

### Automatic Message Filtering

```python
# bot/handlers/moderation.py

import hashlib
import logging
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from bot.api_client import APIClient

logger = logging.getLogger(__name__)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all messages with content moderation"""
    
    message = update.message
    if not message or not message.text:
        return
    
    user_id = message.from_user.id
    group_id = message.chat.id
    content = message.text
    message_id = message.message_id
    
    # Calculate content hash for duplicate detection
    content_hash = hashlib.md5(content.encode()).hexdigest()
    
    try:
        async with APIClient() as api:
            # 1. Analyze message
            result = await api.analyze_message(
                group_id, message_id, user_id, content
            )
            
            moderation_result = result.get("result", {})
            severity = moderation_result.get("severity")
            action = moderation_result.get("suggested_action")
            confidence = moderation_result.get("confidence")
            
            # 2. Check for duplicates if flagged
            if moderation_result.get("flagged"):
                dup_result = await api.detect_duplicate(group_id, content_hash)
                is_duplicate = dup_result.get("result", {}).get("is_duplicate")
                
                if is_duplicate:
                    logger.warning(f"Duplicate spam detected from {user_id}")
                    action = "ban_user"
            
            # 3. Take action based on severity
            if severity == "critical":
                await _handle_critical_content(
                    update, context, action, moderation_result
                )
            
            elif severity == "high":
                await _handle_high_severity(
                    update, context, action, moderation_result
                )
            
            elif severity == "medium":
                await _handle_medium_severity(
                    update, context, moderation_result
                )
            
            logger.info(
                f"Message analyzed: user={user_id}, severity={severity}, "
                f"action={action}, confidence={confidence:.2%}"
            )
    
    except Exception as e:
        logger.error(f"Message moderation error: {e}")
        # Fail open - don't break the bot


async def _handle_critical_content(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    action: str,
    result: dict
):
    """Handle critical severity content"""
    
    message = update.message
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # Delete message
    try:
        await context.bot.delete_message(chat_id, message.message_id)
    except:
        pass
    
    # Ban user if needed
    if action == "ban_user":
        try:
            await context.bot.ban_chat_member(chat_id, user_id)
            await message.reply_text(
                f"🚫 {message.from_user.mention_html()} has been banned for: "
                f"{', '.join(result.get('categories', ['policy violation']))}\n\n"
                f"Appeal at: support@example.com",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Ban error: {e}")


async def _handle_high_severity(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    action: str,
    result: dict
):
    """Handle high severity content"""
    
    message = update.message
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # Delete message
    try:
        await context.bot.delete_message(chat_id, message.message_id)
    except:
        pass
    
    # Mute if needed
    if "mute" in action:
        duration_match = result.get("suggested_action", "").split("_")[-1]
        duration_hours = 1
        
        if duration_match == "24h":
            duration_hours = 24
        
        try:
            from datetime import datetime, timedelta
            until_date = datetime.utcnow() + timedelta(hours=duration_hours)
            
            await context.bot.restrict_chat_member(
                chat_id,
                user_id,
                permissions=ChatPermissions(),
                until_date=until_date
            )
            
            await message.reply_text(
                f"⚠️ {message.from_user.mention_html()} has been muted for "
                f"{duration_hours}h due to: {', '.join(result.get('categories', []))}"
            )
        except Exception as e:
            logger.error(f"Mute error: {e}")
    else:
        # Warn user
        await message.reply_text(
            f"⚠️ Warning {message.from_user.mention_html()}: "
            f"This message violates our rules.\n\n"
            f"Reason: {', '.join(result.get('categories', ['policy violation']))}"
        )


async def _handle_medium_severity(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    result: dict
):
    """Handle medium severity content"""
    
    message = update.message
    
    # Delete message silently
    try:
        await context.bot.delete_message(
            message.chat.id,
            message.message_id
        )
    except:
        pass
    
    # Private warning
    try:
        await context.bot.send_message(
            message.from_user.id,
            f"💭 Your message was removed for: "
            f"{', '.join(result.get('categories', []))}\n\n"
            f"Please review group rules.",
            reply_to_message_id=None
        )
    except:
        pass
```

---

## 📊 ANALYTICS & HEALTH CHECK

### Daily Health Report

```python
# bot/handlers/analytics.py

import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from bot.api_client import APIClient

logger = logging.getLogger(__name__)

async def health_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate group health report - /health"""
    
    message = update.message
    chat_id = message.chat.id
    
    # Only for group admins
    if not await _is_admin(context, chat_id, message.from_user.id):
        await message.reply_text("❌ Admin only command")
        return
    
    try:
        async with APIClient() as api:
            # Get health score
            health = await api.get_health_score(chat_id)
            health_data = health.get("health_score", 0)
            insights = health.get("insights", [])
            recommendations = health.get("recommendations", [])
            alerts = health.get("alerts", [])
            
            # Get DAU
            dau = await api.get_dau(chat_id, days=7)
            dau_avg = dau.get("data", {}).get("average", 0)
            dau_trend = dau.get("data", {}).get("trend", "stable")
            
            # Get moderation stats
            mod_stats = await api.get_moderation_effectiveness(chat_id)
            total_actions = mod_stats.get("data", {}).get("total_moderation_actions", 0)
            
            # Format report
            report = f"""
📊 GROUP HEALTH REPORT

🏥 Health Score: {health_data:.1f}/100 {'🌟' if health_data >= 80 else '👍' if health_data >= 60 else '⚠️'}
👥 Avg Daily Active Users: {dau_avg:.0f} ({dau_trend} trend)
🛡️ Moderation Actions (30d): {total_actions}

📈 INSIGHTS:
"""
            for insight in insights:
                report += f"\n{insight}"
            
            report += "\n\n💡 RECOMMENDATIONS:"
            for i, rec in enumerate(recommendations, 1):
                report += f"\n{i}. {rec}"
            
            if alerts:
                report += "\n\n🚨 ALERTS:"
                for alert in alerts:
                    report += f"\n• {alert.get('title')}: {alert.get('description')}"
            
            await message.reply_text(report)
    
    except Exception as e:
        logger.error(f"Health report error: {e}")
        await message.reply_text(f"❌ Error generating report: {e}")


async def _is_admin(context, chat_id, user_id) -> bool:
    """Check if user is group admin"""
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ["administrator", "creator"]
    except:
        return False
```

---

## ⚙️ AUTOMATION SETUP

### Configure Auto-Rules on Group Join

```python
# bot/handlers/group_management.py

import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.api_client import APIClient

logger = logging.getLogger(__name__)

async def setup_automation_for_group(
    context: ContextTypes.DEFAULT_TYPE,
    group_id: int
):
    """Auto-setup moderation rules for new group"""
    
    try:
        async with APIClient() as api:
            # Rule 1: Delete spam
            await api.create_automation_rule(
                group_id,
                name="Auto-Delete Spam",
                trigger={
                    "type": "spam_detected",
                    "score": 0.8
                },
                action={
                    "type": "delete_message"
                }
            )
            
            # Rule 2: Warn for profanity
            await api.create_automation_rule(
                group_id,
                name="Profanity Warning",
                trigger={
                    "type": "profanity_detected"
                },
                action={
                    "type": "send_warning",
                    "message": "⚠️ Profanity detected. Keep group clean."
                }
            )
            
            # Rule 3: Mute for hate speech
            await api.create_automation_rule(
                group_id,
                name="Mute Hate Speech",
                trigger={
                    "type": "hate_speech_detected"
                },
                action={
                    "type": "mute_user",
                    "duration": 86400
                }
            )
            
            logger.info(f"✅ Automation rules configured for group {group_id}")
    
    except Exception as e:
        logger.error(f"Automation setup error: {e}")
```

---

## 📅 SCHEDULED REPORTS

### Setup Daily Report

```python
# bot/handlers/scheduled_reports.py

from datetime import datetime
from telegram.ext import ContextTypes
from bot.api_client import APIClient
import logging

logger = logging.getLogger(__name__)

async def setup_daily_report(
    context: ContextTypes.DEFAULT_TYPE,
    group_id: int,
    admin_id: int
):
    """Setup daily health report at 9 AM"""
    
    try:
        async with APIClient() as api:
            # Create scheduled task
            await api.create_scheduled_task(
                group_id=group_id,
                name=f"Daily Report for {group_id}",
                schedule_type="daily",
                schedule_config={"hour": 9, "minute": 0},
                action={
                    "type": "send_report",
                    "recipient": admin_id
                }
            )
            
            logger.info(f"Daily report scheduled for group {group_id}")
    
    except Exception as e:
        logger.error(f"Schedule report error: {e}")
```

---

## 🔗 REGISTRATION IN BOT

### Update bot/main.py

```python
# bot/main.py

from bot.handlers.moderation import handle_message
from bot.handlers.analytics import health_command
from bot.handlers.group_management import setup_automation_for_group

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(MessageHandler(filters.TEXT, handle_message))
    application.add_handler(CommandHandler("health", health_command))
    
    # On group join, setup automation
    application.add_handler(GroupHandler(
        setup_automation_for_group
    ))
    
    # ... rest of setup
    application.run_polling()
```

---

## ✅ TESTING CHECKLIST

- [ ] API V2 running on port 8002
- [ ] MongoDB and Redis accessible
- [ ] Bot can call API endpoints
- [ ] Message moderation working
- [ ] Health scores calculating
- [ ] Automation rules executing
- [ ] Scheduled reports running
- [ ] No API timeouts
- [ ] Error handling working
- [ ] Logs showing activity

---

## 🚀 DEPLOYMENT

```bash
# 1. Start all services
docker-compose up -d

# 2. Check health
curl http://localhost:8002/health

# 3. Check features
curl http://localhost:8002/api/v2/features/health

# 4. Start bot
python bot/main.py
```

---

**Ready to integrate! Start with message moderation, then add analytics and automation.**
