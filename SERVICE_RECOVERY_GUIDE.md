# 🚀 SERVICE RECOVERY - QUICK ACTION GUIDE

**Status**: 🟢 Database Fixed ✅  
**Next**: Restart all services  
**Time**: 5 minutes  
**Result**: Full bot functionality restored  

---

## 📋 3-STEP RECOVERY

### Step 1️⃣ : Stop Old Services (1 minute)
```bash
cd /v3
bash stop_all_services.sh
sleep 3
```

**Expected**: All services stopped gracefully

### Step 2️⃣ : Start All Services (1 minute)
```bash
bash start_all_services.sh
```

**Expected output**:
```
✅ MongoDB started successfully
✅ API V2 started on port 8002
✅ Web Service started on port 8003
✅ Bot service started
```

### Step 3️⃣ : Verify Everything (3 minutes)
```bash
# Check all services running
ps aux | grep -E "uvicorn|mongod|bot" | grep -v grep

# Should show 4+ processes:
# - mongod (port 27017)
# - uvicorn api_v2 (port 8002)
# - uvicorn web (port 8003)
# - bot.py

# Check ports are open
lsof -i :27017 && echo "✅ MongoDB"
lsof -i :8002 && echo "✅ API"
lsof -i :8003 && echo "✅ Web"

# Test database
python3 << 'EOF'
from pymongo import MongoClient
client = MongoClient('mongodb://localhost:27017/')
print("✅ Database OK" if client.ping() else "❌ Failed")
EOF

# Test bot (send /help in Telegram)
# Should respond normally
```

---

## ✅ SUCCESS INDICATORS

When services are restored, you should see:

- [x] ✅ All 4 services running (check: ps aux | grep -E "uvicorn|mongod")
- [ ] ✅ MongoDB listening on port 27017 (check: lsof -i :27017)
- [ ] ✅ API listening on port 8002 (check: lsof -i :8002)
- [ ] ✅ Bot responding to commands in Telegram
- [ ] ✅ Database connection working (python connection test)
- [ ] ✅ No errors in logs (tail /tmp/bot.log)

---

## 🔴 If Something Goes Wrong

### Issue: "Port already in use"
```bash
# Kill the process using the port
lsof -i :27017 | grep LISTEN
kill -9 <PID>

# Then restart services
bash start_all_services.sh
```

### Issue: "Connection refused"
```bash
# Check MongoDB is really running
ps aux | grep mongod

# Check port is correct
netstat -tulpn | grep 27017

# If not there, restart MongoDB
mongod --config /usr/local/etc/mongod.conf
```

### Issue: "Services still not starting"
```bash
# Check logs
tail -f /tmp/bot.log
tail -f /tmp/api.log
tail -f /tmp/web.log

# Common issues:
# - Port conflict
# - Database not accessible
# - Missing dependencies
```

---

## 📊 CURRENT STATUS

```
BEFORE FIX:
🤖 Bot: ✅ Running
🔌 API: ❌ UNHEALTHY
💾 DB:  🔴 ERROR

AFTER DATABASE FIX:
🤖 Bot: ✅ Running (ready to connect)
🔌 API: 🟡 Can start now
💾 DB:  ✅ FIXED (listening on 27017)

AFTER SERVICES RESTART:
🤖 Bot: ✅ Running + Connected
🔌 API: ✅ HEALTHY
💾 DB:  ✅ WORKING
```

---

## 🎯 ONE-COMMAND RECOVERY

```bash
# All in one go:
cd /v3 && bash stop_all_services.sh && sleep 3 && bash start_all_services.sh && echo "Done!"
```

---

## ⏱️ TIMELINE

| Step | Duration | Status |
|------|----------|--------|
| Stop services | 2 min | Quick |
| Start services | 1 min | Quick |
| Verify running | 2 min | Check ports |
| Test database | 1 min | Connection test |
| **TOTAL** | **~5 minutes** | ✅ Ready |

---

## 📝 RECOVERY LOG

```
Time: _________
Status Before:  Bot:__  API:__  DB:__
Command 1: bash stop_all_services.sh
Output: ___________

Command 2: bash start_all_services.sh
Output: ___________

Command 3: ps aux | grep -E "uvicorn|mongod" | grep -v grep
Output Count: ____ processes

Database Test: ___________
Bot Response: ___________

Status After: Bot:__  API:__  DB:__
Overall: ✅ Success / ❌ Failed
```

---

**Ready? Run the commands above!**

See: DATABASE_EMERGENCY_FIX_REPORT.md for detailed information
