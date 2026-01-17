# Web Control API - Deployment Checklist

Complete checklist for deploying and testing the web control API.

---

## ✅ Pre-Deployment Checklist

- [ ] `centralized_api/api/web_control.py` created (740+ lines)
- [ ] `centralized_api/app.py` updated with web router import
- [ ] `centralized_api/app.py` updated with web database initialization
- [ ] `centralized_api/app.py` updated with router registration
- [ ] All syntax checks passed
- [ ] MongoDB is running and accessible
- [ ] Docker containers are healthy
- [ ] No port conflicts (8000 available)

---

## 🚀 Deployment Steps

### Step 1: Verify Files

```bash
# Check web_control.py exists
ls -la centralized_api/api/web_control.py

# Check app.py was updated
grep "web_control" centralized_api/app.py
grep "set_web_database" centralized_api/app.py
```

### Step 2: Syntax Check

```bash
# Verify both files compile
python3 -m py_compile centralized_api/app.py
python3 -m py_compile centralized_api/api/web_control.py

# No output means success ✅
```

### Step 3: Restart API Service

```bash
# Option A: Docker Compose
docker-compose restart centralized_api

# Option B: Manual (if running directly)
pkill -f "uvicorn centralized_api.app:app"
sleep 2

# Activate venv and run
source venv/bin/activate
cd centralized_api
python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### Step 4: Wait for Startup

```bash
# Give API 2-3 seconds to start
sleep 3

# Check if running
curl -s http://localhost:8000/api/web/health | head -20
```

---

## 🧪 Testing Sequence

### Test 1: Health Check ⭐

```bash
curl http://localhost:8000/api/web/health

# Expected: 200 OK with status: "healthy"
```

**Status:** ☐ Pass ☐ Fail

### Test 2: API Info

```bash
curl http://localhost:8000/api/web/info | jq '.api_version'

# Expected: "1.0.0"
```

**Status:** ☐ Pass ☐ Fail

### Test 3: Parse User (Numeric)

```bash
curl -X POST http://localhost:8000/api/web/parse-user \
  -H "Content-Type: application/json" \
  -d '{"user_input": "123456789"}'

# Expected: type: "numeric", user_id: 123456789
```

**Status:** ☐ Pass ☐ Fail

### Test 4: Parse User (Username)

```bash
curl -X POST http://localhost:8000/api/web/parse-user \
  -H "Content-Type: application/json" \
  -d '{"user_input": "@john_doe"}'

# Expected: type: "username", username: "@john_doe"
```

**Status:** ☐ Pass ☐ Fail

### Test 5: Parse User (Invalid)

```bash
curl -X POST http://localhost:8000/api/web/parse-user \
  -H "Content-Type: application/json" \
  -d '{"user_input": ""}'

# Expected: error or empty response handling
```

**Status:** ☐ Pass ☐ Fail

### Test 6: Ban User Action

```bash
curl -X POST http://localhost:8000/api/web/actions/ban \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": -1001234567890,
    "user_input": "987654321",
    "reason": "Testing",
    "initiated_by": 111111
  }' | jq '.success'

# Expected: true
```

**Status:** ☐ Pass ☐ Fail

### Test 7: Mute User Action

```bash
curl -X POST http://localhost:8000/api/web/actions/mute \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": -1001234567890,
    "user_input": "987654321",
    "duration_minutes": 60,
    "initiated_by": 111111
  }' | jq '.success'

# Expected: true
```

**Status:** ☐ Pass ☐ Fail

### Test 8: Batch Actions

```bash
curl -X POST http://localhost:8000/api/web/actions/batch \
  -H "Content-Type: application/json" \
  -d '{
    "actions": [
      {
        "action_type": "ban",
        "group_id": -1001234567890,
        "user_input": "111111",
        "initiated_by": 111111
      },
      {
        "action_type": "ban",
        "group_id": -1001234567890,
        "user_input": "222222",
        "initiated_by": 111111
      }
    ]
  }' | jq '.successful'

# Expected: 2
```

**Status:** ☐ Pass ☐ Fail

### Test 9: All Action Types

```bash
# Test each action endpoint
for action in ban kick mute unmute restrict unrestrict warn promote demote unban; do
  echo "Testing $action..."
  curl -X POST http://localhost:8000/api/web/actions/$action \
    -H "Content-Type: application/json" \
    -d '{
      "group_id": -1001234567890,
      "user_input": "987654321",
      "initiated_by": 111111
    }' -w "\nStatus: %{http_code}\n\n"
done
```

**Status:** ☐ Pass ☐ Fail

### Test 10: Query Endpoints

```bash
# User history
curl "http://localhost:8000/api/web/actions/user-history?group_id=-1001234567890&user_input=987654321" \
  | jq '.success'

# Group stats
curl "http://localhost:8000/api/web/actions/group-stats?group_id=-1001234567890" \
  | jq '.success'

# Group list
curl "http://localhost:8000/api/web/groups/list" \
  | jq '.success'

# Expected: true for all
```

**Status:** ☐ Pass ☐ Fail

---

## 📊 Testing Summary

### All Tests Passed? ✅

```
Total Tests: 10
Passed: __
Failed: __
Success Rate: __%
```

---

## 🔍 Debugging (if needed)

### Check API Logs

```bash
# Docker logs
docker logs -f centralized_api

# Or manual logs
tail -f logs/api/api.log
```

### Check MongoDB Connection

```bash
# Connect to MongoDB
mongosh mongodb://localhost:27017

# List databases
show dbs

# Use bot database
use bot_actions

# Check collections
show collections
```

### Check Port Availability

```bash
# Is port 8000 in use?
lsof -i :8000

# Or
netstat -tlnp | grep 8000
```

### Verify Module Import

```bash
# Test import directly
python3 -c "from centralized_api.api.web_control import web_router; print('✅ Import OK')"
```

---

## 📈 Performance Baseline

Test response times:

```bash
# Time a health check
time curl http://localhost:8000/api/web/health > /dev/null

# Time a ban action
time curl -X POST http://localhost:8000/api/web/actions/ban \
  -H "Content-Type: application/json" \
  -d '{"group_id": -100, "user_input": "123", "initiated_by": 456}' > /dev/null

# Time batch action
time curl -X POST http://localhost:8000/api/web/actions/batch \
  -H "Content-Type: application/json" \
  -d '{"actions": [
    {"action_type": "ban", "group_id": -100, "user_input": "111", "initiated_by": 456},
    {"action_type": "ban", "group_id": -100, "user_input": "222", "initiated_by": 456},
    {"action_type": "ban", "group_id": -100, "user_input": "333", "initiated_by": 456}
  ]}' > /dev/null
```

**Expected Times:**
- Health: <50ms
- Single action: 200-400ms
- Batch (3 items): 300-600ms

---

## 🚨 Rollback Procedure (if needed)

### If API Won't Start

```bash
# Check what's wrong
python3 -m py_compile centralized_api/app.py

# Revert app.py changes
git checkout centralized_api/app.py

# Restart
docker-compose restart centralized_api
```

### If Database Error

```bash
# Check MongoDB
docker logs mongo

# Restart MongoDB
docker-compose restart mongo

# Restart API
docker-compose restart centralized_api
```

### If Port Conflict

```bash
# Kill process on port 8000
lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9

# Restart API
docker-compose restart centralized_api
```

---

## 📋 Production Deployment

Once tested locally:

### Step 1: Push to VPS

```bash
# Commit changes
git add .
git commit -m "Add web control API for bot"
git push origin dev

# OR copy files directly
scp centralized_api/api/web_control.py user@vps:/app/centralized_api/api/
scp centralized_api/app.py user@vps:/app/centralized_api/
```

### Step 2: Deploy on VPS

```bash
# SSH to VPS
ssh user@vps

# Pull latest
cd /app
git pull origin dev

# Restart service
docker-compose restart centralized_api

# Verify
curl http://localhost:8000/api/web/health
```

### Step 3: Monitor

```bash
# Watch logs
docker logs -f centralized_api

# Check CPU/Memory
docker stats centralized_api
```

---

## 📚 Documentation Review

Ensure all documentation is accessible:

- [ ] `WEB_CONTROL_API.md` - Main documentation
- [ ] `WEB_CONTROL_INTEGRATION.md` - Integration guide
- [ ] `WEB_CONTROL_QUICK_REFERENCE.md` - Quick examples
- [ ] `WEB_CONTROL_IMPLEMENTATION_SUMMARY.md` - Summary

---

## ✨ Final Verification

```bash
# Run comprehensive test
echo "Testing all endpoints..."

# 1. Health
echo "1. Health check..."
curl -s http://localhost:8000/api/web/health | jq '.status'

# 2. Parse user
echo "2. Parse user..."
curl -s -X POST http://localhost:8000/api/web/parse-user \
  -H "Content-Type: application/json" \
  -d '{"user_input": "test"}' | jq '.type'

# 3. Ban
echo "3. Ban action..."
curl -s -X POST http://localhost:8000/api/web/actions/ban \
  -H "Content-Type: application/json" \
  -d '{"group_id": -100, "user_input": "123", "initiated_by": 456}' | jq '.success'

# 4. Batch
echo "4. Batch actions..."
curl -s -X POST http://localhost:8000/api/web/actions/batch \
  -H "Content-Type: application/json" \
  -d '{"actions": [{"action_type": "ban", "group_id": -100, "user_input": "111", "initiated_by": 456}]}' | jq '.success'

echo "✅ All basic tests completed!"
```

---

## 🎉 Deployment Complete!

Once all tests pass:

✅ Web Control API is ready for production
✅ All endpoints are functional
✅ Documentation is complete
✅ Ready for integration with web dashboard

---

## 📞 Post-Deployment Support

If issues occur:

1. Check logs: `docker logs centralized_api`
2. Verify MongoDB: `mongosh mongodb://localhost:27017`
3. Test endpoints individually with curl
4. Review WEB_CONTROL_INTEGRATION.md troubleshooting
5. Check WEB_CONTROL_API.md error handling section

---

## 📝 Sign-Off

```
Deployment Checklist: COMPLETE ✅
All Tests: PASSED ✅
Documentation: COMPLETE ✅
Ready for Production: YES ✅

Deployed by: ________________
Date: _____________________
Notes: _____________________
```

