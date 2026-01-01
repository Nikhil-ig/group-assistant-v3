# 🚀 Quick Reference: Key Code Changes

## New Service: telegram_sync_service.py

### Location
`src/services/telegram_sync_service.py` (352 lines)

### Key Functions

#### Ban User
```python
async def ban_user_in_telegram(group_id: int, user_id: int, reason: str = "") -> Tuple[bool, str]:
    """Ban user from Telegram group."""
    # Returns: (True/False, "success message" or "error message")
```

#### Mute User
```python
async def mute_user_in_telegram(group_id: int, user_id: int, duration_minutes: int, reason: str = "") -> Tuple[bool, str]:
    """Restrict user from sending messages for duration_minutes."""
    # Returns: (True/False, message)
```

#### Kick User
```python
async def kick_user_in_telegram(group_id: int, user_id: int, reason: str = "") -> Tuple[bool, str]:
    """Remove user from group (can rejoin)."""
    # Returns: (True/False, message)
```

#### Unban/Unmute
```python
async def unban_user_in_telegram(group_id: int, user_id: int, reason: str = "") -> Tuple[bool, str]
async def unmute_user_in_telegram(group_id: int, user_id: int, reason: str = "") -> Tuple[bool, str]
```

#### Send Notification
```python
async def send_notification_to_group(group_id: int, message: str) -> Tuple[bool, str]
```

### Usage in Web API

```python
from src.services.telegram_sync_service import ban_user_in_telegram

# In your endpoint:
success, msg = await ban_user_in_telegram(group_id, user_id, reason)
if success:
    return {"ok": True, "source": "WEB"}
else:
    return {"ok": False, "error": msg}
```

---

## Updated: group_actions_api.py

### Location
`src/web/group_actions_api.py` (224 lines)

### Pattern for All Endpoints

```python
@router.post("/groups/{group_id}/actions/ban")
async def ban_user(
    group_id: int = Path(...),
    req: ActionRequest = Body(...),
    user: TokenPayload = Depends(verify_api_token),
):
    """Ban user from web dashboard."""
    try:
        db = get_db()
        
        # STEP 1: Create audit payload
        payload = {
            "group_id": int(group_id),
            "action": "BAN",
            "user_id": int(req.user_id),
            "admin_id": int(user.user_id),
            "source": "WEB",           # ← CRITICAL: Mark as from web
            "reason": req.reason or "",
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        # STEP 2: Log to MongoDB (wrapped, won't block)
        try:
            await db.audit_logs.insert_one(payload)
        except:
            pass
        
        # STEP 3: Publish to Redis (wrapped, won't block)
        try:
            redis = get_redis()
            await redis.publish("guardian:actions", json.dumps(payload))
        except:
            pass
        
        # STEP 4: Execute in Telegram (critical step)
        try:
            from src.services.telegram_sync_service import ban_user_in_telegram
            success, msg = await ban_user_in_telegram(int(group_id), int(req.user_id), req.reason or "")
            logger.info(f"✅ [WEB] BAN executed: {success}")
            return {"ok": success, "source": "WEB"}
        except Exception as e:
            logger.error(f"❌ BAN error: {e}")
            return {"ok": False, "error": str(e)}
    except Exception as e:
        logger.exception(f"Ban failed: {e}")
```

### All 5 Endpoints Use Same Pattern

- `POST /groups/{group_id}/actions/ban` - BAN action
- `POST /groups/{group_id}/actions/unban` - UNBAN action  
- `POST /groups/{group_id}/actions/mute` - MUTE action
- `POST /groups/{group_id}/actions/unmute` - UNMUTE action
- `POST /groups/{group_id}/actions/kick` - KICK action

---

## Updated: audit.py

### Before
```python
async def log_admin_action(group_id, admin_id, action, target_user_id, reason, metadata=None):
    payload = {"action": action, "admin_id": admin_id, ...}
```

### After
```python
async def log_admin_action(group_id, admin_id, action, target_user_id, reason, metadata=None, source="BOT"):
    payload = {"action": action, "admin_id": admin_id, "source": source, ...}
    # source is either "BOT" or "WEB"
```

### Usage

**From Bot:**
```python
await log_admin_action(group_id, admin_id, "BAN", user_id, reason, source="BOT")
```

**From Web:**
```python
await log_admin_action(group_id, admin_id, "BAN", user_id, reason, source="WEB")
```

---

## Updated: mod_actions.py

### Before
```python
async def perform_mod_action(group_id, admin_id, action_type, target_user, reason=None, duration_minutes=None):
    result = {"action_id": id, "action": action_type, ...}
```

### After
```python
async def perform_mod_action(group_id, admin_id, action_type, target_user, reason=None, duration_minutes=None, source="BOT"):
    result = {"action_id": id, "action": action_type, "source": source, ...}
    # source is either "BOT" or "WEB"
```

### Redis Broadcast Update
```python
# Now includes source in Redis message
event_data = {
    "action": action_type,
    "source": source,  # ← Added
    "admin_id": admin_id,
    "user_id": target_user,
    "timestamp": datetime.utcnow().isoformat()
}
await redis.publish("guardian:actions", json.dumps(event_data))
```

---

## Data Flow Diagram

### Web Dashboard → Telegram

```
Admin clicks [Ban]
        ↓
POST /groups/{id}/actions/ban
        ↓
✓ Log to audit_logs (source="WEB")
✓ Publish to Redis
✓ Call ban_user_in_telegram()
        ↓
Telegram API: bot.ban_chat_member()
        ↓
User removed from group
Group receives notification
Dashboard updates via WebSocket
```

### Bot Command → Dashboard

```
Admin types: /ban @user
        ↓
Bot handler receives command
        ↓
log_admin_action(..., source="BOT")
        ↓
perform_mod_action(..., source="BOT")
        ↓
✓ Log to audit_logs
✓ Publish to Redis (with source="BOT")
        ↓
WebSocket broadcasts to dashboard
Dashboard shows action with source="BOT"
```

---

## Environment Variables Required

```bash
# .env file
TELEGRAM_BOT_TOKEN=123456:ABC...         # Your bot token
MONGODB_URL=mongodb://localhost:27017    # MongoDB connection
REDIS_URL=redis://localhost:6379         # Redis connection
JWT_SECRET=your-secret-key               # For JWT auth
```

---

## Database Collections

### audit_logs
```javascript
{
  "_id": ObjectId,
  "group_id": -123456789,
  "action": "BAN",
  "user_id": 987654321,
  "admin_id": 123456789,
  "reason": "Spam",
  "source": "WEB",           // ← "BOT" or "WEB"
  "timestamp": "2025-12-20T10:30:00.000Z"
}
```

---

## Redis Channel

### Channel: `guardian:actions`

**Message Format:**
```json
{
  "group_id": -123456789,
  "action": "BAN",
  "user_id": 987654321,
  "admin_id": 123456789,
  "source": "WEB",
  "timestamp": "2025-12-20T10:30:00.000Z"
}
```

**Subscribers:**
- WebSocket endpoints (broadcast to connected clients)
- Dashboard (real-time updates)

---

## API Endpoints

### Ban User
```
POST /api/v1/groups/{group_id}/actions/ban
Content-Type: application/json
Authorization: Bearer <token>

{
  "user_id": 987654321,
  "reason": "Spam messages"
}

Response:
{
  "ok": true,
  "source": "WEB"
}
```

### Mute User
```
POST /api/v1/groups/{group_id}/actions/mute
Content-Type: application/json

{
  "user_id": 987654321,
  "reason": "Too loud",
  "duration_hours": 24
}
```

### Kick User
```
POST /api/v1/groups/{group_id}/actions/kick
Content-Type: application/json

{
  "user_id": 987654321,
  "reason": "Breaking rules"
}
```

---

## Logging Output Examples

### Successful Ban from Web
```
✅ [WEB] BAN executed: True
```

### Failed Mute
```
❌ MUTE error: User not found
```

### Redis Broadcast
```
✅ [WEB] Broadcast BAN action
```

---

## Quick Import Reference

```python
# Import telegram sync service
from src.services.telegram_sync_service import (
    ban_user_in_telegram,
    unban_user_in_telegram,
    mute_user_in_telegram,
    unmute_user_in_telegram,
    kick_user_in_telegram,
    send_notification_to_group
)

# Each function returns: Tuple[bool, str]
success, message = await ban_user_in_telegram(group_id, user_id, reason)

# Use in endpoint
return {"ok": success, "source": "WEB"}
```

---

## Common Issues & Fixes

### Issue: Web actions don't execute in Telegram
**Fix:** Ensure `telegram_sync_service.py` is imported and TELEGRAM_BOT_TOKEN is set

### Issue: source field missing from logs
**Fix:** Verify endpoint passes `source="WEB"` in payload dict

### Issue: Dashboard doesn't update
**Fix:** Check WebSocket connection in browser console, verify Redis is running

### Issue: Telegram API error
**Fix:** Check bot has admin rights, user is in group, bot token is valid

---

**Reference this when:**
- Adding new moderation actions
- Fixing integration issues  
- Debugging source tracking
- Implementing new endpoints

Keep this handy! 🚀
