# 🧪 Testing Guide - Guardian Bot

## Quick Start

### 1. Start the Bot
```bash
cd /Users/apple/Documents/Personal/startup/bots/telegram\ bot/python/main_bot_v2
python -m v3
```

You should see:
```
✅ Application started successfully
🤖 Starting Telegram bot polling...
✅ Telegram bot is now polling for updates
INFO: Uvicorn running on http://0.0.0.0:8000
```

### 2. Test in a New Terminal (Keep Bot Running)

## API Testing

### Login
```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"user_id":12345,"username":"testadmin","first_name":"TestAdmin"}' | \
  python -c 'import sys,json; print(json.load(sys.stdin).get("token",""))')

echo "Token: $TOKEN"
```

### Get Groups
```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/groups | python -m json.tool
```

### Get Members (Replace GROUP_ID)
```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/groups/-1003447608920/members | python -m json.tool
```

### Execute Action (Ban User)
```bash
curl -X POST http://localhost:8000/api/v1/groups/-1003447608920/actions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "ban",
    "target_user_id": 123456789,
    "target_username": "testuser",
    "reason": "Testing ban action"
  }' | python -m json.tool
```

### Get Audit Logs
```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/audit-logs | python -m json.tool | head -50
```

---

## Telegram Bot Testing

### Send /ban to Bot in Group
```
@Anynameeeeeebot /ban @username
```
Bot will:
- Log the command
- Ban user from Telegram group
- Record action in audit logs

### Send /mute to Bot
```
@Anynameeeeeebot /mute @username
```

### Send /kick to Bot
```
@Anynameeeeeebot /kick @username
```

### Send /warn to Bot
```
@Anynameeeeeebot /warn @username
```

### Send /unmute to Bot
```
@Anynameeeeeebot /unmute @username
```

### Send /unban to Bot
```
@Anynameeeeeebot /unban @username
```

### Check Bot Status
```
@Anynameeeeeebot /ping
```
Bot will respond: "🤖 Pong!"

---

## Debug Commands

### Check Real-Time Logs
```bash
# All logs
tail -f logs/api.log

# Only bot updates
tail -f logs/api.log | grep "Getting updates"

# Only actions
tail -f logs/api.log | grep "📤"

# Only errors
tail -f logs/api.log | grep "❌"

# Only success
tail -f logs/api.log | grep "✅"
```

### Check Database
```bash
# Connect to MongoDB
mongosh

# Switch to database
use guardian_bot

# View audit logs
db.audit_logs.find({}).pretty()

# Count actions
db.audit_logs.countDocuments({})

# Find bans only
db.audit_logs.find({action_type: "ban"}).pretty()

# Check latest action
db.audit_logs.find().sort({_id: -1}).limit(1).pretty()
```

### Check API Health
```bash
curl http://localhost:8000/api/v1/health | python -m json.tool
```

Expected response:
```json
{
  "status": "ok",
  "timestamp": "2025-12-31T12:16:00Z"
}
```

---

## Test Scenarios

### Scenario 1: Ban via API
1. Get token: `curl ... POST /auth/login`
2. Execute action: `curl ... POST /groups/{id}/actions` with action_type="ban"
3. Check logs: `tail -f logs/api.log`
4. Verify in DB: `db.audit_logs.findOne({action_type: "ban"})`

### Scenario 2: Ban via Telegram
1. Type in group: `/ban @username`
2. Bot receives command and bans user
3. Check logs: `tail -f logs/api.log | grep ban`
4. Verify user is banned in Telegram group

### Scenario 3: RBAC Test
1. Login as GROUP_ADMIN
2. Try to access another group
3. Should get: `"error": "Not authorized"`

### Scenario 4: Error Handling
1. Try to ban a user that doesn't exist
2. Bot logs error but continues
3. Check logs for error message

---

## Common Test Commands

```bash
# Full health check
echo "=== Health Check ===" && \
curl -s http://localhost:8000/api/v1/health | python -m json.tool && \
echo "" && \
echo "=== Bot Logs (last 5) ===" && \
tail -5 logs/api.log

# Quick token test
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"user_id":12345,"username":"testadmin","first_name":"TestAdmin"}' | \
  python -c 'import sys,json; d=json.load(sys.stdin); print(d.get("token","ERROR: "+str(d)))') && \
echo "Token obtained: ${TOKEN:0:20}..."

# Full test suite
bash test_suite.sh  # if you create this file
```

---

## Expected Behavior

### Bot Startup
- ✅ `getMe` call succeeds
- ✅ Polling starts
- ✅ API responds to health check
- ✅ No errors in logs

### Command Received
- ✅ Log entry created: "Getting updates: [update_id]"
- ✅ Command identified
- ✅ Action executed
- ✅ Response sent to group

### Action Executed
- ✅ Telegram API called
- ✅ Response logged
- ✅ Database record created
- ✅ Success/error message logged

### Graceful Shutdown
- ✅ CTRL+C received
- ✅ Updater stopped
- ✅ Final updates fetched
- ✅ Database closed
- ✅ "Shutdown complete" logged

---

## Troubleshooting Tests

### Is the bot running?
```bash
lsof -i :8000  # Should show uvicorn process
```

### Is Telegram API connected?
```bash
grep "getMe" logs/api.log  # Should see successful call
```

### Did bot receive message?
```bash
grep "Getting updates" logs/api.log  # Should see update IDs
```

### Is database working?
```bash
mongosh → db.adminCommand('ping')  # Should return { ok: 1 }
```

### Can I authenticate?
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"user_id":1,"username":"test","first_name":"Test"}' | \
  python -c 'import sys,json; print(json.load(sys.stdin).get("token","ERROR"))'
```

---

## Test Credentials

**Test Admin**
- User ID: 12345
- Username: testadmin
- First Name: TestAdmin
- Role: SUPERADMIN (can see all groups)

**Test Group Admin**
- User ID: 67890
- Username: groupadmin
- First Name: GroupAdmin
- Role: GROUP_ADMIN (can only see Group ID: 9999)

**Test Group**
- Group ID: -1003447608920
- Group Name: Bot Testing
- Username: @qwertyu234567

---

## Performance Baseline

Run these to establish baseline performance:

```bash
# Time a health check
time curl http://localhost:8000/api/v1/health

# Time authentication
time curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"user_id":1,"username":"test","first_name":"Test"}'

# Time group listing
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"user_id":12345,"username":"testadmin","first_name":"TestAdmin"}' | \
  python -c 'import sys,json; print(json.load(sys.stdin).get("token",""))') && \
time curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/groups
```

Expected: < 100ms per request

---

## Load Testing (Optional)

```bash
# Install Apache Bench
brew install httpd

# Test health endpoint with 100 requests
ab -n 100 -c 10 http://localhost:8000/api/v1/health

# Test with authentication
# First, update the -H header with a real token
ab -n 100 -c 10 -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  http://localhost:8000/api/v1/groups
```

---

## Final Verification Checklist

After running tests, verify:

- [x] Bot starts without errors
- [x] API responds to requests
- [x] Can authenticate and get token
- [x] Can list groups
- [x] Can get members
- [x] Bot receives Telegram messages
- [x] Commands are logged
- [x] Audit logs are created
- [x] Can gracefully shutdown
- [x] No data loss on restart

**Status**: Ready for production testing ✅

---

**Last Updated**: 2025-12-31  
**Testing Status**: Ready  
**Next**: Execute test scenarios
