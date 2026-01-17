# 🚀 MANUAL VPS DEPLOYMENT - Step by Step

**Time Required**: ~10 minutes  
**Status**: All fixes are ready

---

## ⚡ QUICK DEPLOYMENT (If you have SSH access)

### Option 1: Automated Script (Easiest)
```bash
cd /Users/apple/Documents/Personal/startup/bots/telegram\ bot/python/main_bot_v2/v3
bash deploy-vps-fix.sh YOUR_VPS_IP root
```

**Example:**
```bash
bash deploy-vps-fix.sh 123.45.67.89 root
```

---

## 📋 MANUAL DEPLOYMENT (Step-by-Step)

### Step 1: SSH to Your VPS
```bash
ssh root@YOUR_VPS_IP
```

### Step 2: Stop All Services
```bash
cd /opt/group-assistant-v3
bash stop_all_services.sh
sleep 3
```

### Step 3: Backup Old Files (Optional)
```bash
cp api_v2/cache/manager.py api_v2/cache/manager.py.backup
cp requirements.txt requirements.txt.backup
cp api_v2/requirements.txt api_v2/requirements.txt.backup
```

### Step 4: Update Files on VPS

**Option A: Using nano editor (Easiest)**

Edit `/opt/group-assistant-v3/api_v2/cache/manager.py`:
```bash
nano /opt/group-assistant-v3/api_v2/cache/manager.py
```

Find this line (around line 9):
```python
import aioredis
```

Replace with:
```python
import redis.asyncio as aioredis
```

Save: `Ctrl+X → Y → Enter`

---

**Option B: Using sed command (Fastest)**

```bash
# Fix manager.py import
sed -i 's/import aioredis/import redis.asyncio as aioredis/' /opt/group-assistant-v3/api_v2/cache/manager.py

# Fix requirements.txt (replace aioredis with redis)
sed -i 's/aioredis==2.0.1/redis>=5.0.0/' /opt/group-assistant-v3/requirements.txt
sed -i 's/aioredis==2.0.1/redis>=5.0.0/' /opt/group-assistant-v3/api_v2/requirements.txt

# Fix centralized_api2 (remove aioredis line if present)
sed -i '/aioredis==2.0.1/d' /opt/group-assistant-v3/centralized_api2/requirements.txt
```

### Step 5: Verify Changes
```bash
# Check manager.py
grep -n "import redis" /opt/group-assistant-v3/api_v2/cache/manager.py

# Check requirements
grep "redis\|aioredis" /opt/group-assistant-v3/requirements.txt
grep "redis\|aioredis" /opt/group-assistant-v3/api_v2/requirements.txt
grep "redis\|aioredis" /opt/group-assistant-v3/centralized_api2/requirements.txt
```

**Expected output:**
```
✅ api_v2/cache/manager.py has: import redis.asyncio as aioredis
✅ requirements.txt has: redis>=5.0.0 (no aioredis)
✅ api_v2/requirements.txt has: redis>=5.0.0 (no aioredis)
✅ centralized_api2/requirements.txt has: redis==5.0.1 only
```

### Step 6: Reinstall Dependencies
```bash
cd /opt/group-assistant-v3

# Remove old aioredis
./venv/bin/pip uninstall -y aioredis 2>/dev/null || true

# Install updated dependencies
./venv/bin/pip install -q -r requirements.txt
./venv/bin/pip install -q -r api_v2/requirements.txt

# Verify redis is installed
./venv/bin/pip list | grep redis
```

**Expected output:**
```
redis                    5.0.1
```

### Step 7: Start Services
```bash
bash start_all_services.sh
sleep 5
```

### Step 8: Verify Running
```bash
ps aux | grep -E "uvicorn|mongod|bot" | grep -v grep
```

**Expected:** 4+ processes running

### Step 9: Test Database
```bash
python3 << 'EOF'
from pymongo import MongoClient
try:
    client = MongoClient('mongodb://localhost:27017/')
    result = client.admin.command('ping')
    print("✅ Database OK")
except Exception as e:
    print(f"❌ Database Error: {e}")
EOF
```

### Step 10: Check Logs
```bash
# Watch logs for 30 seconds
timeout 30 tail -f /tmp/api.log /tmp/bot.log 2>/dev/null || true

# Should see: No distutils errors, normal operation
```

---

## ✅ VERIFICATION CHECKLIST

After deployment:

- [ ] All 4 services running (ps aux)
- [ ] MongoDB on port 27017 (lsof -i :27017)
- [ ] API on port 8002 (lsof -i :8002)
- [ ] Web on port 8003 (lsof -i :8003)
- [ ] Database connection works (python test)
- [ ] No distutils errors in logs
- [ ] No aioredis errors in logs
- [ ] Bot responds to /help command

---

## 🔍 TROUBLESHOOTING

### Issue: "Connection refused" after deployment
```bash
# Check if MongoDB is listening
lsof -i :27017

# If not, restart it
mongod --config /usr/local/etc/mongod.conf > /tmp/mongod.log 2>&1 &
sleep 2

# Then restart services
bash stop_all_services.sh
sleep 3
bash start_all_services.sh
```

### Issue: Still seeing distutils error
```bash
# Verify redis is installed
./venv/bin/pip list | grep redis

# If not, install it
./venv/bin/pip install redis>=5.0.0

# Then restart services
bash stop_all_services.sh && sleep 3 && bash start_all_services.sh
```

### Issue: Services won't start
```bash
# Check logs
tail -50 /tmp/api.log
tail -50 /tmp/bot.log

# Common issues:
# 1. Port already in use: lsof -i :8002; kill -9 <PID>
# 2. Database not ready: wait 5 seconds, then restart
# 3. Missing dependencies: reinstall requirements
```

---

## 📞 QUICK COMMANDS

```bash
# After SSH to VPS, use these:

# Check all services
ps aux | grep -E "uvicorn|mongod|bot" | grep -v grep

# Check all ports
lsof -i :27017; lsof -i :8002; lsof -i :8003

# View logs real-time
tail -f /tmp/api.log /tmp/bot.log /tmp/web.log

# Restart everything
cd /opt/group-assistant-v3 && bash stop_all_services.sh && sleep 3 && bash start_all_services.sh

# Test database
python3 -c "from pymongo import MongoClient; MongoClient('mongodb://localhost:27017/').admin.command('ping'); print('✅ OK')"
```

---

## 📊 WHAT WAS CHANGED

### Local Files (Already Fixed ✅)
- ✅ `/v3/api_v2/cache/manager.py` - Changed import to `redis.asyncio`
- ✅ `/v3/requirements.txt` - Replaced `aioredis` with `redis>=5.0.0`
- ✅ `/v3/api_v2/requirements.txt` - Replaced `aioredis` with `redis>=5.0.0`
- ✅ `/v3/centralized_api2/requirements.txt` - Removed `aioredis`

### VPS Files (Need to be updated)
- 🟡 `/opt/group-assistant-v3/api_v2/cache/manager.py` - PENDING
- 🟡 `/opt/group-assistant-v3/requirements.txt` - PENDING
- 🟡 `/opt/group-assistant-v3/api_v2/requirements.txt` - PENDING
- 🟡 `/opt/group-assistant-v3/centralized_api2/requirements.txt` - PENDING

---

## ⏱️ TIMELINE

| Step | Duration | Task |
|------|----------|------|
| SSH to VPS | 1 min | Connect to server |
| Stop services | 2 min | Kill processes gracefully |
| Update files | 2 min | Edit 4 files |
| Reinstall deps | 3 min | pip install packages |
| Start services | 2 min | Start all processes |
| Verify | 2 min | Check status and logs |
| **TOTAL** | **~14 minutes** | Full deployment |

---

## 🎯 SUCCESS INDICATORS

Your deployment worked when you see:

```
✅ 4+ processes running (mongod, api_v2, web, bot)
✅ MongoDB listening on 127.0.0.1:27017
✅ API listening on 0.0.0.0:8002
✅ Web listening on 0.0.0.0:8003
✅ Database connection test returns: ✅ Database OK
✅ Logs show no distutils errors
✅ Bot responds to /help in Telegram
```

---

## 🚀 READY TO DEPLOY

Choose one:

**Option 1 (Automated):**
```bash
bash deploy-vps-fix.sh YOUR_VPS_IP root
```

**Option 2 (Manual):**
- SSH to VPS
- Follow steps 1-10 above
- Done!

**Time to complete**: ~14 minutes  
**Expected result**: Full system operational ✅
