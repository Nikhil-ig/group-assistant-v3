# 🔧 MONGODB QUICK TROUBLESHOOTING FOR VPS

## Issue: "MongoDB not running" / "Cannot connect"

### Quick Fix (5 minutes)

**Step 1: Check if MongoDB is installed**
```bash
which mongod
# If NOT found → MongoDB not installed, see Installation below
# If found → Go to Step 2
```

**Step 2: Check if MongoDB service is running**
```bash
systemctl status mongod
# If NOT running:
sudo systemctl start mongod

# If won't start → Check logs:
tail -50 /var/log/mongodb/mongod.log
```

**Step 3: Verify port is open**
```bash
netstat -tlnp | grep 27017
# Should show: 127.0.0.1:27017 LISTEN

# If not showing → MongoDB crashed, restart:
sudo systemctl restart mongod
sleep 2
netstat -tlnp | grep 27017
```

**Step 4: Test connection**
```bash
cd /v3
/v3/venv/bin/python3 << 'EOF'
from pymongo import MongoClient
try:
    client = MongoClient('mongodb://localhost:27017', serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print("✅ MongoDB connection successful!")
except Exception as e:
    print(f"❌ Connection failed: {e}")
EOF
```

**Step 5: Restart bot**
```bash
cd /v3
bash stop_all_services.sh
sleep 3
bash start_all_services.sh
tail -f /tmp/bot.log
```

---

## Installation (if MongoDB not installed)

### One-Command Install
```bash
bash /v3/setup-mongodb-vps.sh
```

### Manual Install (if script doesn't work)
```bash
# Update system
sudo apt update
sudo apt install -y curl gnupg

# Add MongoDB repo
curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list

# Install
sudo apt update
sudo apt install -y mongodb-org

# Start
sudo systemctl start mongod
sudo systemctl enable mongod

# Verify
systemctl status mongod
```

---

## Common Issues & Fixes

### Issue 1: "Address already in use"
```bash
# Another process using port 27017
lsof -i :27017

# Kill the process
sudo kill -9 <PID>

# Or find what's using it
ps aux | grep -E "mongod|mongo" | grep -v grep
```

### Issue 2: "Permission denied"
```bash
# MongoDB directory permissions wrong
sudo chown -R mongodb:mongodb /var/lib/mongodb
sudo chown -R mongodb:mongodb /var/log/mongodb

# Restart MongoDB
sudo systemctl restart mongod
```

### Issue 3: "Out of disk space"
```bash
# Check disk usage
df -h /var/lib/mongodb

# If full, either:
# 1. Delete old data
# 2. Move MongoDB to another drive
# 3. Increase disk size

# Clean MongoDB journal (safe)
sudo systemctl stop mongod
sudo rm -f /var/lib/mongodb/mongod.lock
sudo systemctl start mongod
```

### Issue 4: "Cannot start MongoDB - journal commit interval"
```bash
# MongoDB thinks drive doesn't support journaling
# Fix: Edit MongoDB config

sudo nano /etc/mongod.conf

# Find and modify:
storage:
  journal:
    enabled: true
  # Add this line:
  wiredTiger:
    engineConfig:
      cacheSizeGB: 1

# Save and restart
sudo systemctl restart mongod
```

### Issue 5: "Bot can't connect - timeout"
```bash
# Check MONGODB_URL in .env
cat /v3/.env | grep MONGODB_URL
# Should be: mongodb://localhost:27017/telegram_bot

# If wrong, fix it:
nano /v3/.env

# Then restart bot:
cd /v3
bash stop_all_services.sh && sleep 2 && bash start_all_services.sh
```

---

## Verify Everything Works

```bash
# 1. Check MongoDB running
ps aux | grep mongod | grep -v grep && echo "✅ MongoDB running" || echo "❌ MongoDB not running"

# 2. Check port listening
netstat -tlnp | grep 27017 && echo "✅ Port 27017 open" || echo "❌ Port not open"

# 3. Test Python connection
cd /v3 && /v3/venv/bin/python3 -c "
from pymongo import MongoClient
try:
    MongoClient('mongodb://localhost:27017', serverSelectionTimeoutMS=3000).admin.command('ping')
    print('✅ Database connection works')
except:
    print('❌ Database connection failed')
"

# 4. Check bot logs
tail -5 /tmp/bot.log | grep -i "error\|database" && echo "❌ Errors found" || echo "✅ No errors"

# 5. Test command
# Send /help to bot and check /tmp/bot.log for command processing
```

---

## Emergency Recovery

If everything is broken:

```bash
# Full reset
sudo systemctl stop mongod
sudo rm -rf /var/lib/mongodb/*
sudo systemctl start mongod
sleep 5

# Reinitialize
cd /v3
bash setup-mongodb-vps.sh

# Restart bot
bash stop_all_services.sh && sleep 3 && bash start_all_services.sh

# Verify
ps aux | grep -E "mongod|uvicorn|bot/main" | grep -v grep
```

---

## Performance Check

```bash
# See MongoDB size
du -sh /var/lib/mongodb/

# See if growing
du -sh /var/lib/mongodb/ && sleep 60 && du -sh /var/lib/mongodb/

# If growing too fast, there's a memory leak
# Check: /tmp/bot.log for errors
```

---

## Status Dashboard

```bash
# Create quick status check
cat > /v3/mongodb-status.sh << 'EOF'
#!/bin/bash
echo "=== MONGODB STATUS ==="
systemctl status mongod --no-pager | grep -E "Active|memory|cpu"
echo ""
echo "=== PORT CHECK ==="
netstat -tlnp 2>/dev/null | grep 27017 || echo "❌ Not listening"
echo ""
echo "=== DISK USAGE ==="
du -sh /var/lib/mongodb
echo ""
echo "=== CONNECTION TEST ==="
mongosh --eval "db.adminCommand('ping')" --quiet 2>&1 && echo "✅ Connected" || echo "❌ Failed"
EOF
chmod +x /v3/mongodb-status.sh

# Run status check
bash /v3/mongodb-status.sh
```

---

## Contact Support Info

If MongoDB still not working after all these steps:

1. Share output of:
   ```bash
   systemctl status mongod
   tail -50 /var/log/mongodb/mongod.log
   netstat -tlnp | grep 27017
   ```

2. Check disk space:
   ```bash
   df -h /
   ```

3. Check system resources:
   ```bash
   free -h
   ps aux | head -10
   ```

4. Test directly:
   ```bash
   mongosh
   > db.adminCommand('ping')
   > exit
   ```

---

## MongoDB is Working When:
✅ `systemctl status mongod` shows "active (running)"  
✅ `netstat -tlnp | grep 27017` shows port listening  
✅ Python can connect without errors  
✅ Bot logs don't show "database error" or "connection refused"  
✅ Bot can process commands (seen in logs)  
✅ Data persists (shown in MongoDB collections)
