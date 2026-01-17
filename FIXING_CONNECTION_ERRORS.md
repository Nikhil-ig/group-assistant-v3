# 🔧 Fix: Connection Failed Issues

## Issues Found & Fixed

### Issue 1: PyMongo Import Error ❌ → ✅ FIXED

**Error**: `ImportError: cannot import name 'DUPLICATED_KEY' from 'pymongo'`

**Cause**: `DUPLICATED_KEY` constant was removed in newer PyMongo versions

**Fix Applied**: 
- Removed `DUPLICATED_KEY` from imports in `api_v2/core/database.py`
- The code uses `DuplicateKeyError` from `pymongo.errors` which is the correct way

**Status**: ✅ FIXED

---

### Issue 2: Bot Connection Failed ❌ → ⚠️ REQUIRES ACTION

**Error**: "All connection attempts failed"

**Root Cause**: 
1. API V2 was started on **port 8001** instead of **8002**
2. Bot expects API on **port 8002** (from `API_V2_URL` env var)

**What Happened**:
```
Bot tried to connect to:  http://localhost:8002
But API was running on:   http://localhost:8001
Result: Connection failed ❌
```

**Solution**:

### ✅ How to Fix

**Step 1: Stop Current API V2**
```bash
# If running in terminal, press Ctrl+C
# Or if running in background:
pkill -f "uvicorn api_v2"
```

**Step 2: Start API V2 on Correct Port (8002)**
```bash
cd /Users/apple/Documents/Personal/startup/bots/telegram\ bot/python/main_bot_v2/v3
python -m uvicorn api_v2.app:app --port 8002 --reload

# You should see: "Uvicorn running on http://0.0.0.0:8002"
```

**Step 3: Verify Configuration**
```bash
# Check bot .env has correct port
cat bot/.env | grep API_V2_URL
# Should show: API_V2_URL=http://localhost:8002

# Test API is running
curl http://localhost:8002/api/v2/enforcement/health
# Should return: {"status": "ok"}
```

**Step 4: Restart Bot**
```bash
cd bot
python main.py

# Check logs for: "✅ Bot initialized successfully"
```

---

## 🚀 Correct Startup Sequence

### Terminal 1: MongoDB
```bash
mongod --port 27017
```

### Terminal 2: Redis
```bash
redis-server
```

### Terminal 3: API V2 (on port 8002) ⭐ IMPORTANT
```bash
cd "/Users/apple/Documents/Personal/startup/bots/telegram bot/python/main_bot_v2/v3"
python -m uvicorn api_v2.app:app --port 8002 --reload

# Expected output:
# INFO:     Uvicorn running on http://0.0.0.0:8002
```

### Terminal 4: Bot
```bash
cd "/Users/apple/Documents/Personal/startup/bots/telegram bot/python/main_bot_v2/v3"
python bot/main.py

# Expected output:
# ✅ Bot initialized successfully
# 🤖 Bot is polling for updates...
```

### Terminal 5: Web (Optional)
```bash
cd "/Users/apple/Documents/Personal/startup/bots/telegram bot/python/main_bot_v2/v3"
python web/app.py
```

### Terminal 6: Frontend (Optional)
```bash
cd "/Users/apple/Documents/Personal/startup/bots/telegram bot/python/main_bot_v2/v3/web/frontend"
npm run dev
```

---

## 🔍 Verification Checklist

- [ ] **MongoDB**: Running on port 27017
  ```bash
  # Test: mongosh
  ```

- [ ] **Redis**: Running on default port
  ```bash
  # Test: redis-cli ping
  # Response: PONG
  ```

- [ ] **API V2**: Running on port 8002 ⭐
  ```bash
  # Test: curl http://localhost:8002/api/v2/enforcement/health
  # Response: {"status": "ok"}
  ```

- [ ] **Bot**: Connected to API V2
  ```bash
  # Check logs for: "Action execution failed" should NOT appear
  # After fix, should see: "✅ Bot initialized successfully"
  ```

- [ ] **Web** (Optional): Running on port 8000
  ```bash
  # Test: curl http://localhost:8000/health
  ```

- [ ] **Frontend** (Optional): Running on port 5173
  ```bash
  # Test: open http://localhost:5173
  ```

---

## 🐛 Troubleshooting

### Still Getting Connection Errors?

**Check 1: Is API V2 really on port 8002?**
```bash
lsof -i :8002
# Should show uvicorn process

# If port 8001 is used instead:
lsof -i :8001
# Kill it: kill -9 <PID>
```

**Check 2: Is MongoDB running?**
```bash
mongosh
# If fails, start MongoDB:
mongod --port 27017
```

**Check 3: Is Redis running?**
```bash
redis-cli ping
# If fails, start Redis:
redis-server
```

**Check 4: Check bot .env**
```bash
cat bot/.env
# Must show:
# API_V2_URL=http://localhost:8002
# API_V2_KEY=shared-api-key
```

**Check 5: Test API directly**
```bash
# Test health endpoint
curl http://localhost:8002/api/v2/enforcement/health

# Test with verbose output
curl -v http://localhost:8002/api/v2/enforcement/health
```

**Check 6: Check bot logs for details**
```bash
# Look for: "All connection attempts failed"
# This means bot can't reach the API

# Look for: "Health check failed"
# This confirms API connection issue
```

---

## ✅ What Was Fixed

### api_v2/core/database.py
- ✅ Removed invalid `DUPLICATED_KEY` import
- ✅ Uses correct `DuplicateKeyError` from pymongo.errors
- ✅ No more import errors

### Configuration
- ✅ Bot configured for port 8002
- ✅ Web configured for port 8000
- ✅ API V2 should run on port 8002

---

## 🎯 Next Steps

1. **Apply the import fix** ✅ (Already done)
2. **Start services in correct order** (Follow startup sequence above)
3. **Verify API on port 8002** (Use curl test)
4. **Check bot logs** (Should not see connection errors)
5. **Use Swagger UI** (http://localhost:8002/docs)

---

## 📋 Summary

| Issue | Status | Fix |
|-------|--------|-----|
| PyMongo DUPLICATED_KEY | ✅ Fixed | Removed invalid import |
| API on wrong port | ⚠️ Action Required | Start API on 8002 |
| Bot connection | ⚠️ Will fix when API on 8002 | Restart bot after API fix |

---

## 🚀 Quick Fix Command

```bash
# One-liner to start everything correctly:

# Terminal 1
mongod --port 27017 &

# Terminal 2
redis-server &

# Terminal 3 - API V2 on CORRECT PORT 8002
cd "/Users/apple/Documents/Personal/startup/bots/telegram bot/python/main_bot_v2/v3" && \
python -m uvicorn api_v2.app:app --port 8002 --reload

# Terminal 4 - Once API is running
cd "/Users/apple/Documents/Personal/startup/bots/telegram bot/python/main_bot_v2/v3" && \
python bot/main.py
```

---

## ✨ Expected Result After Fix

```
API V2 Logs:
  ✅ Uvicorn running on http://0.0.0.0:8002

Bot Logs:
  ✅ Bot initialized successfully
  ✅ Bot is polling for updates...
  ✅ Action execution should work

No more:
  ❌ "All connection attempts failed"
  ❌ "Health check failed"
  ❌ ImportError
```

---

**Last Updated**: 2024-01-16  
**Status**: Ready to test  
**Action Required**: Start API V2 on port 8002 (NOT 8001)
