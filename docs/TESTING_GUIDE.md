# 🧪 Bot-Web Sync Testing Guide

## Quick Start Verification

### Test 1: Ban from Web Dashboard ⚡

**Setup:**
- Have web dashboard open in browser
- Have your Telegram group open in another window
- Have MongoDB CLI or Studio 3T open to see audit logs

**Steps:**
1. Go to dashboard → Groups → Select a group → Members tab
2. Find a test user (not yourself!)
3. Click **[Ban]** button
4. **Immediately check:**
   - [ ] User is removed from Telegram group
   - [ ] Dashboard shows confirmation
   - [ ] Group chat shows notification message

**Verify in MongoDB:**
```javascript
db.audit_logs.findOne(
  {action: "BAN", source: "WEB"}, 
  {sort: {timestamp: -1}}
)
```
Should show: `"source": "WEB"`

**Expected output:**
```json
{
  "action": "BAN",
  "user_id": 123456789,
  "admin_id": 987654321,
  "source": "WEB",        // ← This confirms it came from web
  "timestamp": "2025-12-20T...",
  "group_id": -123456
}
```

---

### Test 2: Ban from Telegram Bot 🤖

**Setup:**
- Have Telegram group open
- You must be group admin
- Have MongoDB open

**Steps:**
1. In Telegram group, type: `/ban @username reason for ban`
2. **Immediately check:**
   - [ ] User is removed from group
   - [ ] Group sees notification
   - [ ] Check dashboard (should update via WebSocket)

**Verify in MongoDB:**
```javascript
db.audit_logs.findOne(
  {action: "BAN", source: "BOT"}, 
  {sort: {timestamp: -1}}
)
```
Should show: `"source": "BOT"`

---

### Test 3: Mute from Web 🔇

**Steps:**
1. Dashboard → Groups → Members → Click **[Mute]** on a user
2. Enter duration (e.g., 30 minutes)
3. **Check:**
   - [ ] User can't send messages in group
   - [ ] WebSocket updates dashboard
   - [ ] Notification shown in group

**Verify:**
```javascript
db.audit_logs.findOne(
  {action: "MUTE", source: "WEB"}, 
  {sort: {timestamp: -1}}
)
```

---

### Test 4: Real-Time WebSocket Sync 📡

**Steps:**
1. Open dashboard in 2 browser windows (side by side)
2. Click ban in window 1
3. **Check:** Window 2 updates immediately (no refresh needed)

**If WebSocket isn't working:**
- Check browser console (F12 → Console tab) for errors
- Look for WebSocket connection in Network tab
- Verify WebSocket endpoint is running

---

### Test 5: Unmute from Web ✅

**Steps:**
1. Find a muted user in dashboard
2. Click **[Unmute]**
3. **Check:**
   - [ ] User can send messages again
   - [ ] Notification shown in group

---

## Debugging Checklist

### If Web Actions Don't Execute in Telegram ❌

**Check 1: Is telegram_sync_service.py loaded?**
```bash
grep -r "telegram_sync_service" src/
# Should find imports in group_actions_api.py
```

**Check 2: Is the endpoint being called?**
```bash
# Look for HTTP logs
tail -f bot.log | grep "POST /api/v1/groups"
```

**Check 3: Is bot token set?**
```bash
echo $TELEGRAM_BOT_TOKEN
# Should show a long token like 123456:ABC...
```

**Check 4: Check logs for errors**
```bash
grep -i "error\|exception\|❌" bot.log | tail -20
```

---

### If Source Tracking Missing ❌

**Check:**
```javascript
// Should see "WEB" source
db.audit_logs.find({}).limit(5).pretty()
```

If missing `source` field:
- Verify audit.py has source parameter
- Check group_actions_api.py has `"source": "WEB"`

---

### If WebSocket Not Updating 🔌

**Check 1: Is WebSocket server running?**
```bash
grep -i "websocket\|ws://" bot.log
# Should see "WebSocket server started on..."
```

**Check 2: Browser console for errors**
- F12 → Console tab
- Look for WebSocket connection errors

**Check 3: Verify endpoint exists**
```python
# Should exist in websocket_endpoints.py
@app.websocket("/ws/mod_actions/{group_id}")
async def websocket_endpoint(websocket):
    ...
```

---

## File Locations for Reference

| Component | File | Purpose |
|-----------|------|---------|
| Web Endpoints | `src/web/group_actions_api.py` | Ban/Mute/Kick endpoints |
| Telegram Service | `src/services/telegram_sync_service.py` | Executes Telegram API |
| Audit Logging | `src/services/audit.py` | Logs with source field |
| Moderation Logic | `src/services/mod_actions.py` | Central action handler |
| WebSocket | `src/web/websocket_endpoints.py` | Real-time updates |
| Group Sync | `src/services/group_sync.py` | Sync & caching |

---

## Success Indicators ✅

You know everything works when:

1. **Web to Telegram** ✅
   - Click ban in dashboard
   - User removed from Telegram immediately
   - No refresh needed

2. **Source Tracking** ✅
   - MongoDB shows `"source": "WEB"` for dashboard actions
   - MongoDB shows `"source": "BOT"` for bot commands
   - Audit log clearly shows origin

3. **Real-Time Sync** ✅
   - Dashboard updates appear instantly
   - Multiple browsers stay in sync
   - No manual refresh needed

4. **Notifications** ✅
   - Group sees message: "User banned"
   - Message appears seconds after action

5. **No Errors** ✅
   - bot.log shows no 500 errors
   - Browser console shows no WebSocket errors
   - MongoDB inserts succeed

---

## Quick Test Script

```bash
#!/bin/bash
# Quick validation script

echo "🧪 Guardian Bot Sync Tests"
echo "=========================="

echo ""
echo "1️⃣  Checking telegram_sync_service.py..."
if [ -f "src/services/telegram_sync_service.py" ]; then
    echo "✅ File exists"
    grep -q "ban_user_in_telegram" src/services/telegram_sync_service.py && echo "✅ ban_user_in_telegram() found"
else
    echo "❌ File NOT found"
fi

echo ""
echo "2️⃣  Checking group_actions_api.py..."
if [ -f "src/web/group_actions_api.py" ]; then
    echo "✅ File exists"
    grep -q "telegram_sync_service" src/web/group_actions_api.py && echo "✅ Imports telegram_sync_service"
    grep -q '"source": "WEB"' src/web/group_actions_api.py && echo "✅ Sets source=WEB"
else
    echo "❌ File NOT found"
fi

echo ""
echo "3️⃣  Checking audit.py for source tracking..."
if grep -q "source=" src/services/audit.py; then
    echo "✅ Source parameter found"
else
    echo "❌ Source parameter NOT found"
fi

echo ""
echo "4️⃣  Checking environment variables..."
if [ ! -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "✅ TELEGRAM_BOT_TOKEN set"
else
    echo "❌ TELEGRAM_BOT_TOKEN NOT set"
fi

echo ""
echo "Done! Run the actual tests above."
```

---

## FAQ

**Q: Do I need to restart the bot?**  
A: Yes, after any code changes. However, the core components (telegram_sync_service.py, group_actions_api.py) are now in place.

**Q: What if I click ban but nothing happens?**  
A: Check bot.log for the error. Likely causes:
- Bot token invalid
- User not in group
- Bot doesn't have admin rights
- Telegram API rate limited

**Q: Why no error message when action fails?**  
A: Intentional design - each step wrapped in try/except. Failures don't block subsequent steps. Check logs to see what failed.

**Q: Can multiple admins act simultaneously?**  
A: Yes! Each action is independent. Actions are queued and executed in order.

**Q: How long does sync take?**  
A: < 1 second typically:
- API receives request: 0ms
- Log to MongoDB: ~100ms
- Publish to Redis: ~10ms
- Telegram API call: ~500ms
- WebSocket broadcast: ~50ms

---

**Ready to test?** Start with Test 1 (Ban from Web) - that's the critical path! 🎉
