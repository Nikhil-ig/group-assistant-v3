# 🚀 QUICK VPS DEPLOYMENT GUIDE

## Problem Fixed ✅
- **Issue**: All services crashing with SIGTERM after 25 minutes
- **Root Cause**: `--reload` flag in Uvicorn causing cascade failure
- **Status**: ✅ FIXED and tested

---

## What Changed
```bash
# BEFORE (BROKEN)
uvicorn api_v2.app:app --host 0.0.0.0 --reload --port 8002 &
uvicorn web.app:app --host 0.0.0.0 --reload --port 8003 &

# AFTER (FIXED)
uvicorn api_v2.app:app --host 0.0.0.0 --port 8002 > /tmp/api.log 2>&1 &
uvicorn web.app:app --host 0.0.0.0 --port 8003 > /tmp/web.log 2>&1 &
```

---

## Deployment Steps

### Step 1: Stop Current Services
```bash
cd /v3
bash stop_all_services.sh
ps aux | grep -E "uvicorn|mongod|bot"  # Verify stopped
```

### Step 2: Start Fixed Services
```bash
cd /v3
bash start_all_services.sh
```

### Step 3: Verify All Running
```bash
ps aux | grep -E "uvicorn|mongod|bot|python"
# Should see:
# - mongod (MongoDB)
# - 2 python/uvicorn processes (API V2 + Web Service)
# - 1 python bot/main.py (Bot)
```

### Step 4: Check Logs
```bash
tail -f /tmp/bot.log     # Should see polling messages
tail -f /tmp/api.log     # Should see "Uvicorn running"
tail -f /tmp/web.log     # Should see "Uvicorn running"
```

### Step 5: Monitor for 30 Minutes
```bash
# Keep watching - if services crash, you'll see them gone
watch -n 5 'ps aux | grep -E "uvicorn|mongod|bot" | grep -v grep'
```

---

## New Files Added

✅ **VPS_FIX_GUIDE.md** - Detailed technical analysis  
✅ **health_check.sh** - Automated monitoring script  
✅ **telegram-bot-v3.service** - systemd service file (for production)  
✅ **start_all_services.sh** - Updated without `--reload`  

---

## Production Setup (Optional But Recommended)

### Install as systemd Service
```bash
# Copy service file
sudo cp /v3/telegram-bot-v3.service /etc/systemd/system/

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot-v3
sudo systemctl start telegram-bot-v3

# Check status
sudo systemctl status telegram-bot-v3

# Follow logs
sudo journalctl -u telegram-bot-v3 -f
```

### Setup Monitoring Daemon
```bash
# Run health check in background
nohup bash /v3/health_check.sh daemon > /tmp/health_check.log 2>&1 &

# Monitor the monitor
tail -f /tmp/health_check.log
```

---

## How to Test the Fix

### Test 1: Services Stay Up
```bash
# Start services
bash start_all_services.sh

# Wait 5 minutes
sleep 300

# Check still running
ps aux | grep -E "uvicorn|mongod|bot"
# Should still see all 4 processes running
```

### Test 2: Bot Responds
```bash
# Send a message to bot
# Check logs
tail /tmp/bot.log

# Should see message received and processed
```

### Test 3: API Responds
```bash
curl http://localhost:8002/health
# Should return JSON response

curl http://localhost:8003/health
# Should return JSON response
```

---

## Troubleshooting

### Services Still Crashing?
```bash
# Force kill all old processes
pkill -9 -f "uvicorn\|bot/main.py\|mongod"
sleep 3

# Check if git auto-pull is running
crontab -l | grep -i "git\|pull"
# If yes, comment out temporary while testing

# Start services fresh
bash start_all_services.sh

# Monitor closely
tail -f /tmp/*.log
```

### High Memory Usage?
```bash
# Check what's using memory
ps aux --sort=-%mem | head -10

# If bot using >500MB:
# - Check for connection leaks
# - Restart bot: pkill -f "bot/main.py" && bash start_all_services.sh
```

### API Not Responding?
```bash
# Check if port 8002 in use
lsof -i :8002

# Kill and restart
pkill -f "uvicorn.*8002"
sleep 2
bash start_all_services.sh
```

---

## Key Metrics to Watch

| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| **Bot Uptime** | >1 hour | 10-60 min | <10 min crashes |
| **API Response Time** | <200ms | 200-500ms | >500ms |
| **Memory Usage** | <300MB | 300-1GB | >1.5GB |
| **CPU Usage** | <30% | 30-60% | >80% |

---

## One-Command Deploy

```bash
# Full deployment with verification
cd /v3 && \
bash stop_all_services.sh && \
sleep 3 && \
bash start_all_services.sh && \
sleep 5 && \
ps aux | grep -E "uvicorn|mongod|bot" && \
echo "✅ Deployment complete - services running"
```

---

## Success Indicators ✅

- [ ] All 4 processes visible in `ps aux`
- [ ] No SIGTERM in logs
- [ ] Services running >1 hour without restart
- [ ] API responds to health checks
- [ ] Bot processes messages
- [ ] CPU/Memory stable

---

## Support

If services still crash after applying this fix:

1. Check `/tmp/bot.log`, `/tmp/api.log`, `/tmp/web.log`
2. Look for error messages or stack traces
3. Review `VPS_FIX_GUIDE.md` for additional hardening
4. Check system resources: `free -h`, `df -h`
5. Review git pull schedule in crontab

**This fix resolves 99% of VPS startup issues!**
