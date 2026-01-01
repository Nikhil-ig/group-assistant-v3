# Bidirectional Integration Complete Implementation Guide

## Overview
Complete bi-directional integration between Telegram Bot, FastAPI Backend, and React Frontend with unified notification control.

---

## Part 1: Backend Architecture

### 1.1 Unified Action Flow

```
┌─────────────────┐         ┌──────────────────────┐         ┌──────────────┐
│  Bot Commands   │         │  API Endpoints       │         │  Frontend    │
│  /ban <user_id> │         │  POST /actions/{...} │         │  Dashboard   │
└────────┬────────┘         └──────────┬───────────┘         └──────┬───────┘
         │                             │                            │
         │         (1) Parse Input     │                            │
         │                             │                            │
         └─────────────────────────────┼────────────────────────────┘
                                       │
                    (2) Create ActionPayload
                    - action: string
                    - user_id: number
                    - source: BOT/WEB
                    - notification_mode: ENUM
                                       │
                                       ▼
                    ┌──────────────────────────────┐
                    │ BidirectionalIntegrationService
                    │ execute_action(payload)      │
                    └──────────────────────────────┘
                                       │
                ┌──────────────────────┼──────────────────────┐
                │                      │                      │
                ▼                      ▼                      ▼
        (3a) Telegram API    (3b) MongoDB        (3c) Redis
        - ban_chat_member    - Audit Log         - Pub/Sub
        - restrict_user      - Full History      - Real-time
        - send_message       - Indexes           - Broadcast
                │                      │                      │
                └──────────────────────┼──────────────────────┘
                                       │
                    (4) Send Notifications
                    - Group Message (if notifyGroup=true)
                    - User DM (if notifyUser=true)
                    - Bot Response (if showInBot=true)
                                       │
                                       ▼
                    (5) Return Result
                    - execution_time_ms
                    - action_id
                    - status
```

### 1.2 Files Created

#### `src/services/bidirectional_integration.py` (450+ lines)

**Key Classes:**

```python
class ActionSource(Enum):
    BOT = "BOT"    # From /ban, /mute, etc.
    WEB = "WEB"    # From frontend dashboard
    API = "API"    # Direct API call

class NotificationMode(Enum):
    SILENT = "SILENT"                    # No notifications
    GROUP_ONLY = "GROUP_ONLY"           # Only group chat
    GROUP_AND_USER = "GROUP_AND_USER"   # Group + user DM
    USER_ONLY = "USER_ONLY"             # Only user DM

@dataclass
class ActionPayload:
    group_id: int
    action: str                      # BAN, UNBAN, MUTE, etc.
    user_id: int
    admin_id: int
    reason: Optional[str]
    duration_hours: Optional[int]
    source: ActionSource
    notification_mode: NotificationMode
    timestamp: datetime
    metadata: Dict[str, Any]
```

**Core Methods:**

1. `execute_action(payload)` - Main workflow orchestration
2. `_execute_telegram_action(payload)` - Calls Telegram Bot API
3. `_store_action_in_db(payload)` - Saves audit log
4. `_send_notifications(payload, action_id)` - Routes notifications
5. `_broadcast_action(payload, action_id)` - Redis pub/sub
6. `get_metrics()` - Performance statistics

#### `src/bot/bidirectional_commands.py` (400+ lines)

**8 Commands Implemented:**

```python
# Each command follows this pattern:
async def ban_command(update, context):
    # 1. Parse arguments
    user_id = int(args[0])
    
    # 2. Create payload
    payload = ActionPayload(
        group_id=chat_id,
        action="BAN",
        user_id=user_id,
        source=ActionSource.BOT,
        notification_mode=NotificationMode.GROUP_AND_USER
    )
    
    # 3. Execute through service
    result = await bidirectional_service.execute_action(payload)
    
    # 4. Reply to group
    if result.ok:
        reply = f"✅ User banned\nTime: {result.execution_time_ms}ms"
    
    await update.message.reply_text(reply)
```

Commands:
- `/ban <user_id> [reason]` - Ban user
- `/unban <user_id>` - Unban user
- `/mute <user_id> [hours] [reason]` - Restrict for hours
- `/unmute <user_id>` - Restore permissions
- `/kick <user_id> [reason]` - Remove user
- `/warn <user_id> [reason]` - Warn user
- `/logs [limit]` - View audit logs
- `/stats` - View statistics

#### `src/web/bidirectional_endpoints.py` (350+ lines)

**6 Endpoints:**

1. **POST `/groups/{group_id}/actions/{action_type}`**
   ```python
   Request:
   {
       "user_id": 123456789,
       "reason": "spam",
       "duration_hours": 24,
       "notify_group": true,
       "notify_user": false,
       "show_in_bot": true
   }
   
   Response:
   {
       "ok": true,
       "action_id": "abc123...",
       "execution_time_ms": 245,
       "timestamp": "2024-01-01T12:00:00Z"
   }
   ```

2. **GET `/groups/{group_id}/logs?limit=50&offset=0`**
   - Returns paginated audit logs
   - Shows action history

3. **GET `/groups/{group_id}/admins`**
   - Returns group administrators
   - Real-time from Telegram

4. **GET `/groups/{group_id}/members`**
   - Returns group members

5. **GET `/groups/{group_id}/metrics`**
   - Total actions, source breakdown
   - Success rates

6. **GET `/health`**
   - Service health check

---

## Part 2: Frontend Integration

### 2.1 Frontend Service

**File:** `frontend/src/services/bidirectionalModerationService.ts`

**Key Features:**

```typescript
// Service methods with notification options
class BidirectionalModerationService {
    
    // Execute action with notification control
    executeAction(
        groupId: number,
        action: EnhancedModerationAction,
        notifications?: NotificationOptions
    ): Promise<ActionResult>
    
    // Specific action methods
    banUser(groupId, userId, reason?, notifications?)
    unbanUser(groupId, userId, notifications?)
    muteUser(groupId, userId, duration?, reason?, notifications?)
    unmuteUser(groupId, userId, notifications?)
    kickUser(groupId, userId, reason?, notifications?)
    warnUser(groupId, userId, reason?, notifications?)
    
    // Data fetching
    getAuditLogs(groupId, limit?, offset?)
    getGroupAdmins(groupId)
    getGroupMetrics(groupId)
    
    // Cache & token management
    setToken(token)
    invalidateCache(groupId)
}

// Notification options
interface NotificationOptions {
    notifyGroup?: boolean      // Send to group (default: true)
    notifyUser?: boolean       // Send DM (default: false)
    showInBot?: boolean        // Show response (default: true)
}
```

### 2.2 Frontend Component

**File:** `frontend/src/components/BidirectionalModerationPanel.tsx`

**Features:**

- **Action Selection:** Dropdown for BAN, UNBAN, MUTE, UNMUTE, KICK, WARN
- **User ID Input:** Required field
- **Reason Input:** Optional explanation (not for UNBAN/UNMUTE)
- **Duration Input:** Hours for MUTE action
- **Notification Controls:** 3 independent checkboxes
  - Notify Group Chat
  - Send Direct Message to User
  - Show in Bot Response
- **Confirmation Dialog:** Review details before execution
- **Result Display:** Success/error with execution time
- **Performance Metrics:** Shows execution_time_ms on success

**Usage Example:**

```typescript
import BidirectionalModerationPanel from '@/components/BidirectionalModerationPanel'

export function DashboardPage() {
    const groupId = 1003447608920
    
    return (
        <BidirectionalModerationPanel 
            groupId={groupId}
            onActionComplete={(result) => {
                if (result.ok) {
                    console.log(`Action completed in ${result.execution_time_ms}ms`)
                } else {
                    console.error(`Action failed: ${result.error}`)
                }
            }}
        />
    )
}
```

---

## Part 3: Real-Time Sync

### 3.1 Redis Pub/Sub Flow

```
Backend Service                      Redis                    Frontend
──────────────────────────────────────────────────────────────────────

(1) Action executes
    execute_action()
    ↓
    _broadcast_action()
    └──→ redis.publish(
             'group:{group_id}:actions',
             {action_id, user_id, action, timestamp}
         )
                                    │
                                    ├─→ Channel: group:1234:actions
                                    │   Message: JSON action data
                                    │
                                    └──→ Frontend listening on
                                         same channel
                                         ↓
                                         WebSocket/SSE
                                         ↓
                                    Update Dashboard:
                                    - Add to audit logs
                                    - Update metrics
                                    - Refresh UI
```

### 3.2 Notification Flow

#### Option A: Bot Command → Frontend

```
1. User sends: /ban 123456 spam
2. Bot handler parses args
3. Creates ActionPayload(source=BOT, ...)
4. Service executes:
   - Telegram: ban_chat_member(123456)
   - DB: Insert audit_log
   - Redis: Publish action
   - Group: Send notification "[via BOT] User banned..."
5. Frontend:
   - Receives Redis message
   - Updates audit logs in real-time
   - Shows new action in dashboard
```

#### Option B: Frontend Action → Bot

```
1. User clicks "Ban" in dashboard
2. Notification checkboxes:
   ✓ Notify Group Chat
   ☐ Send Direct Message
   ✓ Show in Bot Response
3. Frontend sends POST /groups/.../actions/BAN
4. Service executes:
   - Telegram: ban_chat_member(123456)
   - DB: Insert audit_log
   - Group: Send notification "[via WEB] User banned..."
   - User: ☐ Skip DM (unchecked)
   - Bot: ✓ Respond with confirmation
5. Group sees: "[via WEB] User 123456 banned by Admin"
6. Dashboard shows: ✓ Success, execution_time_ms: 245ms
```

---

## Part 4: Integration Checklist

### Backend Integration

- [ ] Import BidirectionalIntegrationService in main bot file
- [ ] Initialize with: `service = BidirectionalIntegrationService(bot, db, redis)`
- [ ] Register CommandHandlers in bot application
- [ ] Include bidirectional_endpoints router in FastAPI app
- [ ] Create database indexes on:
  - `audit_logs.group_id`
  - `audit_logs.group_id + timestamp`
  - `audit_logs.user_id`

### Frontend Integration

- [ ] Install bidirectionalModerationService in service directory
- [ ] Create BidirectionalModerationPanel component
- [ ] Import component in dashboard page
- [ ] Pass `groupId` prop
- [ ] Implement `onActionComplete` callback
- [ ] Set JWT token: `service.setToken(token)`
- [ ] Add notification option UI controls

### Environment Setup

- [ ] Configure API_BASE_URL in service
- [ ] Ensure JWT token in localStorage
- [ ] Configure CORS on backend for frontend domain
- [ ] Set up Redis connection
- [ ] Configure MongoDB indexes
- [ ] Test Telegram Bot API credentials

---

## Part 5: Testing Procedures

### 1. Bot Command Test

```bash
# Send to group
/ban 123456789 spam

# Expected:
# ✅ Message in group: "[via BOT] User 123456789 banned"
# ✅ Dashboard audit logs updated
# ✅ Execution time < 2 seconds
```

### 2. Frontend Action Test

```typescript
// In browser console
bidirectionalModerationService.banUser(
    groupId,
    123456789,
    "spam",
    {
        notifyGroup: true,
        notifyUser: false,
        showInBot: true
    }
)

// Expected:
// ✅ Group chat notification
// ☐ No user DM
// ✅ Bot response
// ✅ Dashboard shows action immediately
```

### 3. Notification Mode Tests

**Test Case 1: SILENT**
- notifyGroup: false
- notifyUser: false
- showInBot: false
- Expected: No notifications anywhere

**Test Case 2: GROUP_AND_USER**
- notifyGroup: true
- notifyUser: true
- showInBot: true
- Expected: Group message + User DM + Bot response

**Test Case 3: GROUP_ONLY**
- notifyGroup: true
- notifyUser: false
- showInBot: true
- Expected: Only group message + Bot response

### 4. Performance Test

```bash
# Check metrics endpoint
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/groups/1003447608920/metrics

# Expected response:
{
  "total_actions": 42,
  "bot_actions": 28,
  "web_actions": 14,
  "action_breakdown": {
    "BAN": 10,
    "MUTE": 15,
    "WARN": 17
  },
  "success_rate_percent": 98.2
}
```

---

## Part 6: Deployment Steps

### Step 1: Verify Files Exist

```bash
# Backend
✓ src/services/bidirectional_integration.py
✓ src/bot/bidirectional_commands.py
✓ src/web/bidirectional_endpoints.py

# Frontend
✓ frontend/src/services/bidirectionalModerationService.ts
✓ frontend/src/components/BidirectionalModerationPanel.tsx
```

### Step 2: Backend Setup

```python
# In main.py or app.py

from src.services.bidirectional_integration import BidirectionalIntegrationService
from src.bot.bidirectional_commands import register_command_handlers
from src.web.bidirectional_endpoints import router as bidirectional_router

# Initialize service
bidirectional_service = BidirectionalIntegrationService(
    bot=application,
    db=database_client,
    redis=redis_client
)

# Register handlers
register_command_handlers(application, bidirectional_service)

# Include API routes
app.include_router(bidirectional_router, prefix="/api/v1")
```

### Step 3: Frontend Setup

```typescript
// In main app file
import { bidirectionalModerationService } from '@/services/bidirectionalModerationService'

// On login/auth
const token = getJWTToken()
bidirectionalModerationService.setToken(token)

// In dashboard
<BidirectionalModerationPanel 
    groupId={currentGroupId}
    onActionComplete={handleActionComplete}
/>
```

### Step 4: Database Setup

```python
# Create indexes for fast queries
await db.audit_logs.create_index([("group_id", 1)])
await db.audit_logs.create_index([("group_id", 1), ("timestamp", -1)])
await db.audit_logs.create_index([("user_id", 1)])
```

---

## Part 7: Performance Metrics

### Execution Times (Expected)

| Action | Time | Notes |
|--------|------|-------|
| Ban User | 150-300ms | Includes DB write + notification |
| Unban User | 100-200ms | DB write only |
| Mute User | 200-400ms | Includes restrictions |
| Kick User | 150-250ms | Removes member |
| Warn User | 100-200ms | Lightweight |
| Fetch Logs | 50-150ms | Cached after first request |
| Get Metrics | 30-100ms | In-memory calculation |

### Caching Strategy

```typescript
// Frontend service caches audit logs
- Cache Duration: 5 minutes
- Invalidates on: new action executed
- Cache Key: logs-{groupId}-{limit}-{offset}

// Manual invalidation
bidirectionalModerationService.invalidateCache(groupId)
```

### Scalability Features

✅ **Async Operations:** Non-blocking I/O throughout
✅ **Database Indexes:** Fast query performance
✅ **Redis Pub/Sub:** Distributed real-time sync
✅ **Stateless Service:** Can run multiple instances
✅ **Message Queuing:** Ready for asyncio.Queue
✅ **Connection Pooling:** Database and Redis pooling

---

## Part 8: Troubleshooting

### Issue: Actions not showing in group

**Check:**
1. `notify_group` parameter is `true`
2. Bot has permission to send messages in group
3. Group notification mode includes GROUP_ONLY or GROUP_AND_USER
4. Check bot logs: `logger.error()` statements

### Issue: Frontend not updating in real-time

**Check:**
1. Redis connection is active
2. Frontend listening to Redis channel: `group:{group_id}:actions`
3. WebSocket/SSE connection is open
4. Check browser console for network errors

### Issue: Slow execution times

**Check:**
1. Database indexes exist on audit_logs collection
2. Telegram API rate limits not exceeded
3. Redis connection healthy
4. Check network latency to Telegram servers

### Issue: Notification options not working

**Check:**
1. `NotificationMode` enum matches between frontend and backend
2. `get_notification_mode()` function correctly converts booleans
3. `_send_notifications()` respects notification_mode parameter
4. Check service logs for notification errors

---

## Part 9: Security Considerations

### Authentication
- All endpoints require JWT token
- Token extracted from Authorization header
- Token validated on every request

### Authorization
- Verify user is group admin
- Check Telegram group membership
- Validate user_id format before API call

### Rate Limiting
- Implement rate limiter on action endpoints
- Max 10 actions per minute per admin
- Telegram API rate limits: 30 msgs/sec per bot

### Input Validation
- Validate user_id is valid integer
- Sanitize reason text
- Validate duration_hours (1-720)
- Check action type against enum

---

## Part 10: Monitoring & Logging

### Logging Points

```python
# In BidirectionalIntegrationService
logger.info(f"Action executed: {action} user:{user_id} time:{time}ms")
logger.warning(f"Action failed: {error}")
logger.error(f"Critical error in {method}: {exception}")

# Metrics tracking
logger.info(f"Metrics: {total_actions} total, {success_rate}% success")
```

### Monitoring Dashboard

```bash
# Check service health
curl http://localhost:8000/api/v1/groups/health

# Check group metrics
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/groups/{group_id}/metrics

# Check audit logs
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/groups/{group_id}/logs
```

### Alerting Rules

- Alert if success_rate < 90%
- Alert if avg execution_time > 5 seconds
- Alert if Redis connection lost
- Alert if database connection lost

---

## Summary

✅ **Complete bi-directional integration implemented**
✅ **All 8 bot commands wired to unified service**
✅ **6 REST API endpoints with notification control**
✅ **Frontend component with UI controls**
✅ **Real-time sync via Redis pub/sub**
✅ **Performance tracking and metrics**
✅ **Production-ready error handling**

**Ready to deploy!**
