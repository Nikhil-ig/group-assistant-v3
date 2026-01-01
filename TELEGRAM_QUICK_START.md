# ⚡ Quick Start - Telegram API Integration

## 🚀 Start Here

### 1. Configure Bot Token
```bash
# Edit .env or set environment variable
export TELEGRAM_BOT_TOKEN="your_token_from_botfather"
export MONGODB_URI="your_mongodb_connection"
```

### 2. Start Server
```bash
cd /Users/apple/Documents/Personal/startup/bots/telegram bot/python/main_bot_v2/v3
python -m main
```

✅ Server starts
✅ Connects to MongoDB
✅ Initializes Telegram bot
✅ Ready for actions

### 3. Test Dashboard
```bash
# Open in browser
http://localhost:8000

# Login with superadmin
User ID: 12345
Username: testadmin
First Name: TestAdmin
```

### 4. Ban a User
```
1. Select a group
2. Find user in Members tab
3. Click "Ban" button
4. Confirm
5. ✅ User banned in Telegram!
```

### 5. Check Audit Logs
```
Click "Logs" tab → See all actions with timestamps
```

---

## 📝 API Quick Reference

### Ban User
```bash
curl -X POST http://localhost:8000/api/v1/groups/9999/actions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "BAN",
    "target_user_id": 111,
    "target_username": "@spammer",
    "reason": "Spam"
  }'
```

### Mute User (24 hours)
```bash
curl -X POST http://localhost:8000/api/v1/groups/9999/actions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "MUTE",
    "target_user_id": 111,
    "duration_hours": 24,
    "reason": "Too noisy"
  }'
```

### Unmute User
```bash
curl -X POST http://localhost:8000/api/v1/groups/9999/actions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "UNMUTE",
    "target_user_id": 111
  }'
```

### Kick User
```bash
curl -X POST http://localhost:8000/api/v1/groups/9999/actions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "KICK",
    "target_user_id": 111,
    "reason": "Violation"
  }'
```

### Warn User
```bash
curl -X POST http://localhost:8000/api/v1/groups/9999/actions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "WARN",
    "target_user_id": 111,
    "reason": "First warning"
  }'
```

---

## 🤖 Bot Commands

### In Telegram Group

```
/ban @username [reason]      → Ban user
/unban @username              → Unban user
/mute @username [hours]       → Mute user (optional duration)
/unmute @username             → Unmute user
/kick @username [reason]      → Kick user
/warn @username [reason]      → Warn user
/logs [limit]                 → Show recent actions
/stats                        → Show group statistics
```

**Example**:
```
Admin: /ban @spammer posting links
Bot:   ✅ User 12345 has been banned
Group: [User removed]
```

---

## 🔍 Debug Commands

### Check Server Health
```bash
curl http://localhost:8000/api/v1/health | python -m json.tool
```

Expected:
```json
{
  "status": "healthy",
  "timestamp": "2025-12-31T06:15:30.123456"
}
```

### Check Logs
```bash
# View last 50 lines of API log
tail -50 logs/api.log

# Search for errors
grep "ERROR" logs/api.log

# Watch real-time logs
tail -f logs/api.log
```

### Check Database
```bash
mongosh
use guardian_bot
db.audit_logs.find({}).sort({timestamp: -1}).limit(5).pretty()
```

---

## ⚠️ Common Issues

### Issue: "Telegram API service not available"
**Solution**: Remove `SKIP_TELEGRAM=true` environment variable
```bash
# Bad:
SKIP_TELEGRAM=true python -m main

# Good:
python -m main
```

### Issue: "Bot was blocked by user"
**Cause**: Bot can't DM user or access group  
**Solution**: Add bot to group with correct permissions

### Issue: "NOT_ENOUGH_RIGHTS"
**Cause**: Bot missing permissions  
**Solution**: Check bot permissions in group settings:
- ✅ Restrict members (for mute)
- ✅ Ban members (for ban/kick)
- ✅ Post messages (for replies)

### Issue: "User is an administrator"
**Cause**: Can't ban group admins  
**Solution**: Remove admin status first or ignore

### Issue: Actions logged but not executed
**Cause**: Telegram API call failed (check error message)  
**Solution**: Verify bot token, group ID, permissions

---

## ✅ Verification Checklist

After starting server, verify:

- [ ] Server started without errors
- [ ] MongoDB connected
- [ ] Telegram bot initialized
- [ ] Health endpoint responds
- [ ] Dashboard loads at http://localhost:8000
- [ ] Can login with test credentials
- [ ] Can see test group in dropdown
- [ ] Can see test members in list
- [ ] Can click Ban button
- [ ] User appears in Blacklist tab
- [ ] Action appears in Logs tab

---

## 📊 What Happens When You Ban

```
1. Click "Ban" in dashboard
   ↓
2. Frontend sends: POST /api/v1/groups/{id}/actions
   ↓
3. API checks: Is user authorized?
   ↓
4. API calls: telegram_api.ban_user()
   ↓
5. Telegram API: await bot.ban_chat_member()
   ↓
6. Database: Log action to audit_logs
   ↓
7. Database: Add to blacklist collection
   ↓
8. Database: Update metrics
   ↓
9. Frontend: Gets success response
   ↓
10. User sees: "✅ User banned" message
   ↓
11. In Telegram group: User is removed (banned)
   ↓
12. In Dashboard Logs tab: Action shows with timestamp
```

---

## 🎯 Files to Know

```
Main files:
- v3/services/telegram_api.py     ← Telegram API calls
- v3/api/endpoints.py             ← REST API endpoint
- v3/bot/handlers.py              ← Bot commands
- v3/main.py                      ← Start here

Documentation:
- v3/TELEGRAM_INTEGRATION.md      ← Full guide
- v3/TELEGRAM_INTEGRATION_SUMMARY.md ← Implementation details
- This file!                      ← Quick reference

Config:
- v3/config/settings.py           ← All settings
- v3/.env (create this)           ← Secrets
```

---

## 📞 Need Help?

1. **Check logs**: `tail -f logs/api.log`
2. **Check database**: `mongosh` → `use guardian_bot`
3. **Check health**: `curl localhost:8000/api/v1/health`
4. **Check errors**: Look for `[ERROR]` in logs
5. **Read docs**: See `TELEGRAM_INTEGRATION.md`
6. **Test API**: Use curl commands above

---

## 🚨 Critical Settings

```python
# .env or environment variables

# Required:
TELEGRAM_BOT_TOKEN=your_token_here
MONGODB_URI=mongodb://localhost:27017

# Optional:
DEBUG=false              # Set to true for verbose logs
LOG_LEVEL=INFO          # Set to DEBUG for even more logs
SKIP_TELEGRAM=false     # Only set to true for API-only testing

# Don't change:
JWT_SECRET=your_secret_key_here  # Change to random 32 chars in production
TELEGRAM_UPDATE_MODE=polling      # How bot receives updates
```

---

## 💡 Pro Tips

1. **Test API without bot token**:
   ```bash
   SKIP_TELEGRAM=true python -m main
   # Actions logged to DB, no Telegram calls
   ```

2. **View real-time logs**:
   ```bash
   tail -f logs/api.log | grep -E "📤|❌|✅"
   ```

3. **Test dashboard without Telegram**:
   ```bash
   # Create test data
   python -m v3.tools.seed_test_data
   
   # Start without bot
   SKIP_TELEGRAM=true python -m main
   
   # Use dashboard (no Telegram actions)
   ```

4. **Bulk test actions**:
   ```bash
   for i in {1..5}; do
     curl -X POST http://localhost:8000/api/v1/groups/9999/actions \
       -H "Authorization: Bearer $TOKEN" \
       -H "Content-Type: application/json" \
       -d "{\"action_type\": \"WARN\", \"target_user_id\": $i}"
     sleep 1
   done
   ```

---

## 🎉 Success Indicators

You'll know it's working when:

✅ **In Dashboard**:
- Ban button → User disappears from members
- User appears in Blacklist tab
- Action appears in Logs tab with timestamp
- Metrics show updated action count

✅ **In Telegram Group**:
- User is actually banned/muted
- Can't see group (banned) or can't send messages (muted)
- Bot replies to commands
- Admin sees confirmation messages

✅ **In Logs**:
- `[INFO] 📤 Executing BAN via Telegram API`
- `[INFO] ✅ User 123 banned from group 9999`
- No `[ERROR]` messages

✅ **In Database**:
```javascript
db.audit_logs.findOne({action_type: "BAN"})
// Shows action with timestamp, admin, target, reason
```

---

**Ready to moderate Telegram groups!** 🚀

Start server → Open dashboard → Ban a user → ✅ Done!
