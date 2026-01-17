# 🗄️ MONGODB VPS FIX GUIDE

## Problem Summary
❌ **MongoDB is not running on VPS**
- Bot cannot connect to database
- Commands fail silently or with connection errors
- Startup script tries to start MongoDB but fails (likely not installed)

---

## Root Causes

### 1. MongoDB Not Installed on VPS
```bash
# Check if mongod exists
which mongod
# On VPS: likely returns: not found
```

### 2. Wrong Database Configuration
- Local machine: MongoDB runs on localhost:27017
- VPS: MongoDB might be running elsewhere OR not installed at all

### 3. .env Database URL Incorrect
```properties
# Current (wrong)
MONGODB_URL=mongodb://root:telegram_bot_password@mongo:27017/telegram_bot?authSource=admin

# Should be (for local Docker)
MONGODB_URL=mongodb://root:telegram_bot_password@localhost:27017/telegram_bot?authSource=admin

# Or (for external database)
MONGODB_URL=mongodb://user:pass@external-host:27017/telegram_bot
```

---

## Solution Options

## Option 1: Install MongoDB Locally on VPS (Recommended for Small Deployments)

### Step 1: Update System
```bash
apt update && apt upgrade -y
```

### Step 2: Install MongoDB Community Edition
```bash
# Add MongoDB repository
wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-7.0.list
apt update

# Install MongoDB
apt install -y mongodb-org

# Start MongoDB service
systemctl start mongod
systemctl enable mongod

# Verify installation
mongod --version
```

### Step 3: Verify MongoDB Running
```bash
systemctl status mongod
# Should show: active (running)

# Check port
netstat -tlnp | grep 27017
# Should show: 127.0.0.1:27017 LISTEN
```

### Step 4: Update .env File
```bash
# Edit .env
nano /v3/.env

# Change MONGODB_URL to:
MONGODB_URL=mongodb://localhost:27017/telegram_bot

# Or if authentication needed:
MONGODB_URL=mongodb://root:your-password@localhost:27017/telegram_bot?authSource=admin
```

### Step 5: Restart Bot Services
```bash
cd /v3
bash stop_all_services.sh
sleep 3
bash start_all_services.sh
```

---

## Option 2: Use MongoDB Atlas (Cloud) - Recommended for Production

### Step 1: Create MongoDB Atlas Account
1. Go to https://www.mongodb.com/cloud/atlas
2. Create free account
3. Create new project and cluster
4. Generate database connection string

### Step 2: Update .env
```bash
# Get your MongoDB Atlas connection string from Atlas dashboard
# It should look like:
MONGODB_URL=mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/telegram_bot?retryWrites=true&w=majority
```

### Step 3: Create Database and Collections
```bash
# In MongoDB Atlas Console, run:
db.createCollection("users")
db.createCollection("groups")
db.createCollection("moderation_logs")
db.createCollection("settings")
```

### Step 4: Restart Services
```bash
cd /v3
bash stop_all_services.sh
sleep 3
bash start_all_services.sh
```

---

## Option 3: Use Docker Container (Best for VPS)

### Step 1: Install Docker
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

### Step 2: Start MongoDB Container
```bash
docker run -d \
  --name telegram-bot-mongodb \
  -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=root \
  -e MONGO_INITDB_ROOT_PASSWORD=your-secure-password \
  -v mongo_data:/data/db \
  mongo:7.0
```

### Step 3: Update .env
```bash
MONGODB_URL=mongodb://root:your-secure-password@localhost:27017/telegram_bot?authSource=admin
```

### Step 4: Verify Connection
```bash
docker exec telegram-bot-mongodb mongosh -u root -p your-secure-password --authenticationDatabase admin
# Should connect successfully
```

### Step 5: Restart Bot Services
```bash
cd /v3
bash stop_all_services.sh
sleep 3
bash start_all_services.sh
```

---

## Quick Test - Verify Database Connection

```bash
# Test MongoDB connection from Python
/v3/venv/bin/python3 << 'EOF'
from pymongo import MongoClient
import os

mongodb_url = os.getenv('MONGODB_URL', 'mongodb://localhost:27017/telegram_bot')
print(f"Testing connection to: {mongodb_url}")

try:
    client = MongoClient(mongodb_url, serverSelectionTimeoutMS=5000)
    # Force connection attempt
    client.admin.command('ping')
    print("✅ MongoDB connection successful!")
    print(f"Connected to: {client.server_info()['version']}")
    client.close()
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
    exit(1)
EOF
```

---

## Troubleshooting MongoDB Issues

### Issue 1: "Connection refused"
```bash
# MongoDB not running
systemctl status mongod

# If not running, start it
sudo systemctl start mongod
```

### Issue 2: "Authentication failed"
```bash
# Wrong password in .env
# Check MongoDB credentials:
sudo grep -r "MONGO_INITDB_ROOT_PASSWORD" /v3/.env

# Or check if authentication is enabled
mongosh --eval "db.getUsers()"
```

### Issue 3: "Cannot start MongoDB"
```bash
# Check if port 27017 is in use
lsof -i :27017

# Check MongoDB logs
tail -50 /var/log/mongodb/mongod.log

# Restart MongoDB service
sudo systemctl restart mongod
```

### Issue 4: "Disk space full"
```bash
# MongoDB data directory running out of space
df -h /data/db/

# Clean old data or expand storage
```

---

## Verify Database is Working

### After fixing MongoDB, run these tests:

#### Test 1: Check Connection
```bash
cd /v3
/v3/venv/bin/python3 -c "
from pymongo import MongoClient
import os
url = os.getenv('MONGODB_URL', 'mongodb://localhost:27017/telegram_bot')
client = MongoClient(url)
print('✅ Connected to MongoDB')
print(f'Databases: {client.list_database_names()}')
"
```

#### Test 2: Check Bot Can Access Database
```bash
# Check bot logs
tail -f /tmp/bot.log

# Should see messages being processed
# Should NOT see "connection error" or "database error"
```

#### Test 3: Test a Command
```bash
# Send /help to bot in Telegram
# Check if command is processed (seen in logs)
tail /tmp/bot.log | grep -i "command\|help"
```

#### Test 4: Check Data Persistence
```bash
# After running commands, check if data is in database
mongosh -u root -p your-password --authenticationDatabase admin << 'EOF'
use telegram_bot
db.moderation_logs.countDocuments()  # Should show count > 0 if commands were run
EOF
```

---

## Recommended MongoDB Setup for VPS

```bash
# Create secure setup script: /v3/setup-mongodb.sh
#!/bin/bash

# Install MongoDB
apt update
apt install -y mongodb-org

# Start and enable
systemctl start mongod
systemctl enable mongod

# Create admin user (if first time)
mongosh << 'EOF'
use admin
db.createUser({
  user: "root",
  pwd: "your-very-secure-password",
  roles: ["root"]
})

// Create database and collections
use telegram_bot
db.createCollection("users")
db.createCollection("groups")
db.createCollection("moderation_logs")
db.createCollection("settings")
db.createCollection("whitelist")
db.createCollection("blacklist")

// Create indexes for performance
db.moderation_logs.createIndex({ "group_id": 1, "user_id": 1 })
db.groups.createIndex({ "group_id": 1 })
db.users.createIndex({ "user_id": 1 })

print("✅ Database setup complete")
EOF
```

---

## Health Check - MongoDB Status

```bash
# Create health check script: /v3/check-mongodb.sh
#!/bin/bash

echo "🔍 MongoDB Health Check"
echo "======================="
echo ""

# Check if running
if systemctl is-active --quiet mongod; then
    echo "✅ MongoDB service is running"
else
    echo "❌ MongoDB service is NOT running"
    exit 1
fi

# Check port
if netstat -tlnp 2>/dev/null | grep 27017; then
    echo "✅ MongoDB listening on port 27017"
else
    echo "❌ MongoDB not listening on port 27017"
    exit 1
fi

# Test connection
mongosh --eval "db.adminCommand('ping')" --quiet && echo "✅ MongoDB responding to ping" || {
    echo "❌ MongoDB not responding"
    exit 1
}

# Check data directory
if [ -d /var/lib/mongodb ]; then
    SPACE=$(df /var/lib/mongodb | tail -1 | awk '{print $4}')
    echo "✅ MongoDB data directory OK ($SPACE KB free)"
fi

echo ""
echo "✅ All MongoDB checks passed!"
```

---

## Complete Fix - One Command

```bash
# For Ubuntu/Debian VPS:
cd /v3 && \
apt update && \
apt install -y mongodb-org && \
systemctl start mongod && \
systemctl enable mongod && \
sleep 2 && \
echo "✅ MongoDB installed and running" && \
ps aux | grep mongod | grep -v grep && \
echo "✅ Process confirmed running"
```

---

## MongoDB Performance Tuning (Optional)

Edit `/etc/mongod.conf`:

```yaml
# Storage configuration
storage:
  dbPath: /var/lib/mongodb
  journal:
    enabled: true
  
# Network configuration  
net:
  port: 27017
  bindIp: 127.0.0.1,::1  # Or 0.0.0.0 for remote access
  
# Security (if needed)
security:
  authorization: "enabled"
  
# Performance
processManagement:
  timeZoneInfo: /usr/share/zoneinfo
```

Then restart:
```bash
systemctl restart mongod
```

---

## Status Check Command

```bash
# Quick check if everything works
echo "Checking MongoDB..." && \
systemctl status mongod | grep active && \
echo "Checking Bot Services..." && \
ps aux | grep -E "uvicorn|bot/main.py" | grep -v grep | wc -l && \
echo "✅ All services operational"
```

---

## Summary

| Step | Action | Command |
|------|--------|---------|
| 1 | Install MongoDB | `apt install -y mongodb-org` |
| 2 | Start MongoDB | `systemctl start mongod` |
| 3 | Update .env | Set `MONGODB_URL` correctly |
| 4 | Restart bot | `cd /v3 && bash start_all_services.sh` |
| 5 | Verify | Test connection with Python script |

**After these steps, MongoDB should be fully operational and bot can process commands!** ✅
