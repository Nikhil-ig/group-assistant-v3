# ✅ DEPLOYMENT CHECKLIST

## Pre-Deployment Verification

- [x] PyMongo import error fixed (api_v2/core/database.py)
- [x] Health check endpoint corrected (bot/main.py)
- [x] execute_action method rewritten for API V2 (bot/main.py)
- [x] get_group_settings endpoint updated (bot/main.py)
- [x] get_user_action_history endpoint updated (bot/main.py)
- [x] check_pre_action_validation endpoint updated (bot/main.py)
- [x] API V2 port configured as 8002 (docker-compose.yml)
- [x] Bot environment variables correct (bot/.env)

## Startup Sequence

### Step 1: Start MongoDB

```bash
# If using local MongoDB
mongod --port 27017

# If using Docker
docker-compose up -d mongo
```

**Verify:**
```bash
mongosh
# Should connect successfully
```

### Step 2: Start Redis (Optional but recommended)

```bash
# Local Redis
redis-server

# Or Docker
docker-compose up -d redis
```

**Verify:**
```bash
redis-cli ping
# Response: PONG
```

### Step 3: Start API V2

```bash
cd "/Users/apple/Documents/Personal/startup/bots/telegram bot/python/main_bot_v2/v3"
python -m uvicorn api_v2.app:app --port 8002 --reload

# Expected output:
# INFO:     Started server process [12345]
# INFO:     Uvicorn running on http://0.0.0.0:8002 (Press CTRL+C to quit)
```

**Verify API is working:**
```bash
curl http://localhost:8002/health
# Response: {"status": "healthy", "service": "api-v2", "version": "2.0.0"}
```

### Step 4: Start Bot

```bash
cd "/Users/apple/Documents/Personal/startup/bots/telegram bot/python/main_bot_v2/v3"
python bot/main.py

# Expected output:
# ✅ Bot initialized successfully
# 🤖 Bot is polling for updates...
```

**Verify Bot connection:**
- No error messages in logs
- No "Health check failed" messages
- No "All connection attempts failed" messages

### Step 5: Start Web UI (Optional)

```bash
cd "/Users/apple/Documents/Personal/startup/bots/telegram bot/python/main_bot_v2/v3"
python web/app.py

# Expected output:
# WARNING:  Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**Verify:**
```bash
curl http://localhost:8000/health
# Should return health status
```

## System Health Checks

### Check 1: API V2 Health
```bash
curl -s http://localhost:8002/health | jq .
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "api-v2",
  "version": "2.0.0"
}
```

### Check 2: Bot Connection Status
```bash
# Watch bot logs for health check success
# grep "health" bot.log

# Or in live logs:
# Should see: "Health check: passed" or similar
```

### Check 3: Database Connection
```bash
# MongoDB
mongosh
# Should connect without errors

# Redis (if using)
redis-cli ping
# Response: PONG
```

### Check 4: API Endpoints
```bash
# Test enforcement endpoint
curl -X POST http://localhost:8002/api/v2/groups/123456789/enforcement/health

# Or test health
curl http://localhost:8002/api/v2/enforcement/health
```

## Functional Tests

### Test 1: Send a Command to Bot
In your test Telegram group:
```
/start
```

**Expected:**
- Bot responds with welcome message
- No errors in bot logs

### Test 2: Test Ban Action
In your test Telegram group (admin only):
```
Reply to a user with: /ban
```

**Expected:**
- Bot responds with success message
- No "endpoint not found" errors
- Action logged in API

### Test 3: Test Mute Action
```
Reply to a user with: /mute 60
```

**Expected:**
- Bot responds with success message
- API processes mute action
- No connection errors

### Test 4: Test Kick Action
```
Reply to a user with: /kick
```

**Expected:**
- Bot responds with success message
- User is kicked from group
- No API errors

## Troubleshooting

### Issue: "ImportError: cannot import name 'DUPLICATED_KEY'"
**Status:** ✅ FIXED in api_v2/core/database.py line 12
**Action:** Already applied, no further action needed

### Issue: "Health check failed: All connection attempts failed"
**Cause:** API V2 not running or not responding on port 8002
**Solution:**
```bash
# Check if API is running
ps aux | grep "uvicorn"

# Check if port 8002 is listening
lsof -i :8002

# If not running, start it:
python -m uvicorn api_v2.app:app --port 8002 --reload

# If port in use, kill the process:
kill -9 <PID>
```

### Issue: "Connection refused"
**Cause:** Services not running
**Solution:** Follow startup sequence above in order

### Issue: "No such file or directory: bot/.env"
**Cause:** Running from wrong directory
**Solution:**
```bash
cd "/Users/apple/Documents/Personal/startup/bots/telegram bot/python/main_bot_v2/v3"
# Verify bot/.env exists
ls -la bot/.env
```

### Issue: Bot sends "Connection failed" messages
**Cause:** API V2 port mismatch
**Check:**
```bash
# Verify bot .env
cat bot/.env | grep API_V2_URL
# Should show: API_V2_URL=http://localhost:8002

# Verify API running on 8002
lsof -i :8002
# Should show uvicorn process
```

## Performance Monitoring

### Check Bot Memory Usage
```bash
# Watch process memory
watch 'ps aux | grep python | grep -E "bot|api_v2"'
```

### Check API Response Times
```bash
# Measure health check time
time curl http://localhost:8002/health

# Should complete in < 100ms
```

### Check MongoDB Connection Pool
```bash
mongosh
> db.adminCommand('connectionStatus')
```

## Logging

### View API Logs
```bash
# Terminal where API is running, or:
# tail -f logs/api_v2.log (if log file is configured)
```

### View Bot Logs
```bash
# Terminal where bot is running, or:
# tail -f logs/bot.log (if log file is configured)
```

## Emergency Stop

To cleanly shut down all services:

```bash
# In each terminal running a service, press:
Ctrl+C

# If processes won't stop:
pkill -f "python -m uvicorn"
pkill -f "python bot/main.py"
pkill -f "redis-server"
pkill -f "mongod"
```

## Post-Deployment Validation

- [ ] API V2 starts without import errors
- [ ] Bot initializes successfully
- [ ] Health check endpoint responds
- [ ] Bot can execute ban action
- [ ] Bot can execute mute action
- [ ] Bot can execute kick action
- [ ] No "endpoint not found" errors
- [ ] No "connection failed" errors
- [ ] All logs show normal operation
- [ ] Telegram commands work as expected

## Rollback Plan

If something goes wrong:

1. **Stop all services:**
   ```bash
   Ctrl+C in each terminal
   ```

2. **Check logs for error messages**

3. **Verify configuration:**
   - bot/.env has correct API_V2_URL
   - API_V2_URL points to localhost:8002
   - PORT 8002 is not in use by other processes

4. **Restart services in order:**
   - MongoDB first
   - Redis (optional)
   - API V2
   - Bot
   - Web UI (optional)

## Quick Command Reference

```bash
# Navigate to project
cd "/Users/apple/Documents/Personal/startup/bots/telegram bot/python/main_bot_v2/v3"

# Start API V2 (Terminal 1)
python -m uvicorn api_v2.app:app --port 8002 --reload

# Start Bot (Terminal 2)
python bot/main.py

# Start Web UI (Terminal 3, optional)
python web/app.py

# Test health (Another terminal)
curl http://localhost:8002/health

# View logs (Terminal 4)
tail -f logs/*.log
```

## Success Indicators

✅ System is working when you see:

1. **API V2 Console:**
   ```
   INFO:     Uvicorn running on http://0.0.0.0:8002
   ```

2. **Bot Console:**
   ```
   ✅ Bot initialized successfully
   🤖 Bot is polling for updates...
   ```

3. **Health Check:**
   ```json
   {
     "status": "healthy",
     "service": "api-v2",
     "version": "2.0.0"
   }
   ```

4. **Bot Logs:**
   - No "Health check failed" errors
   - No "Connection refused" errors
   - No "ImportError" errors

5. **Bot Functionality:**
   - /start command works
   - /ban command works
   - /mute command works
   - Actions execute through API without errors

## Final Status

✅ All critical fixes applied
✅ System ready for deployment
✅ Verified configuration
✅ Ready for production testing

**Next Action:** Follow startup sequence above, monitor logs, and test basic functionality.

---

**Last Updated:** 2024-01-16  
**Status:** Ready for Deployment ✅  
**Confidence Level:** High ✅
