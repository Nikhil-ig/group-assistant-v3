# V3 Telegram Moderation Bot - Complete Setup Guide

## 📋 Table of Contents
1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Running the Bot](#running-the-bot)
5. [Testing](#testing)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements
- **Python**: 3.8 or higher (Recommended: 3.10+)
- **MongoDB**: 4.0 or higher (local or MongoDB Atlas cloud)
- **OS**: macOS, Linux, or Windows

### Accounts Needed
1. **Telegram Bot Token**: Get from [@BotFather](https://t.me/BotFather)
2. **MongoDB Connection**: 
   - Local: `mongodb://localhost:27017`
   - Cloud: MongoDB Atlas free tier

### Telegram Setup
1. Open [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow the steps
3. Copy your bot token
4. Send `/setcommands` to set the command descriptions

---

## Installation

### Step 1: Navigate to V3 Directory
```bash
cd /Users/apple/Documents/Personal/startup/bots/telegram\ bot/python/main_bot_v2/v3
```

### Step 2: Create Virtual Environment (Recommended)
```bash
# Using venv
python3 -m venv venv
source venv/bin/activate

# Or using conda
conda create -n telegram_bot python=3.10
conda activate telegram_bot
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Verify Installation
```bash
python -c "import telegram, fastapi, motor; print('✅ All dependencies installed')"
```

---

## Configuration

### Step 1: Copy Environment Template
```bash
cp .env.example .env
```

### Step 2: Edit `.env` File

Required settings:

```bash
# ===== TELEGRAM BOT =====
TELEGRAM_BOT_TOKEN=your-bot-token-from-botfather
TELEGRAM_BOT_USERNAME=your_bot_username

# ===== MONGODB =====
# Local MongoDB
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=telegram_bot_v3

# OR MongoDB Atlas (cloud)
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/telegram_bot_v3?retryWrites=true&w=majority

# ===== RBAC - IMPORTANT! =====
SUPERADMIN_ID=your_telegram_user_id  # Your personal Telegram user ID
SUPERADMIN_USERNAME=your_username

# ===== JWT & SECURITY =====
JWT_SECRET=create-a-random-secure-string-here
JWT_EXPIRATION_HOURS=24

# ===== API SERVER =====
API_HOST=0.0.0.0
API_PORT=8000

# ===== LOGGING =====
LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR
LOG_DIR=logs

# ===== ENVIRONMENT =====
ENV=development  # Or 'production' for strict validation
DEBUG=true       # Set to false in production
```

### Step 3: Get Your Telegram User ID
```bash
# Option 1: Use @userinfobot in Telegram to get your ID

# Option 2: Send a message to the bot and check logs (see ID in error message)

# Option 3: Go to https://web.telegram.org and inspect your profile
```

### Step 4: Get MongoDB Connection String

#### Local MongoDB (easiest for testing)
```bash
# Install MongoDB locally (macOS)
brew install mongodb-community

# Start MongoDB service
mongod

# Use connection string
MONGODB_URI=mongodb://localhost:27017
```

#### MongoDB Atlas (cloud, recommended for production)
1. Go to [MongoDB Atlas](https://cloud.mongodb.com)
2. Create free account
3. Create cluster
4. Create database user
5. Get connection string
6. Add your IP address to whitelist
7. Use connection string in `.env`

---

## Running the Bot

### Step 1: Ensure Dependencies Are Ready
```bash
# Activate virtual environment if using one
source venv/bin/activate

# Or conda
conda activate telegram_bot
```

### Step 2: Start MongoDB (if using local)
```bash
mongod
```

### Step 3: Run the Bot
```bash
python main.py
```

### Expected Output
```
============================================================
  V3 TELEGRAM MODERATION BOT - STARTING
  Environment: development
  Debug: true
============================================================
📦 Connecting to MongoDB...
✓ MongoDB connection healthy
✓ Database indexes created
🔐 Initializing authentication service...
✅ Authentication service initialized
🤖 Initializing Telegram bot...
✅ Telegram bot initialized
🌐 Initializing FastAPI...
✅ FastAPI initialized

============================================================
  ✅ ALL SYSTEMS INITIALIZED
============================================================

📋 Available Commands:
  /ban <user_id> [reason] - Ban user
  /unban <user_id> - Unban user
  /kick <user_id> [reason] - Kick user
  /warn <user_id> [reason] - Warn user
  /mute <user_id> [hours] [reason] - Mute user
  /logs [limit] - Show audit logs
  /stats - Show group statistics

🌐 API Endpoints:
  POST   /api/v1/auth/login
  GET    /api/v1/groups
  POST   /api/v1/groups/{group_id}/actions
  GET    /api/v1/groups/{group_id}/logs
  GET    /api/v1/groups/{group_id}/metrics
  GET    /api/v1/health

🔐 RBAC (Role-Based Access Control):
  SUPERADMIN: Can see and control ALL groups
  GROUP_ADMIN: Can see and control ONLY their groups
  USER: Can view audit logs only

============================================================
```

---

## Testing

### Test 1: Telegram Bot Commands

1. Add bot to a group
2. Give bot admin permissions
3. Test commands:

```bash
# In Telegram group:
/stats                          # View statistics
/ban 123456789 spam            # Ban user 123456789 with reason "spam"
/logs 10                        # Show last 10 logs
```

### Test 2: API Endpoints

```bash
# 1. Authenticate
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": YOUR_USER_ID,
    "username": "your_username",
    "first_name": "Your Name"
  }' | jq -r '.token')

echo "Token: $TOKEN"

# 2. Get your groups
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/groups

# 3. Get health status
curl http://localhost:8000/api/v1/health

# 4. Execute action (ban user)
curl -X POST http://localhost:8000/api/v1/groups/-123456789/actions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "ban",
    "target_user_id": 987654321,
    "reason": "spam"
  }'

# 5. Get audit logs
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/groups/-123456789/logs?page=1&page_size=10"

# 6. Get metrics
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/groups/-123456789/metrics"
```

### Test 3: RBAC (Role-Based Access Control)

**Test Superadmin Access:**
```bash
# Superadmin should see ALL groups
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"user_id\": $SUPERADMIN_ID, ...}" | jq -r '.token')

curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/groups
# Result: Shows ALL groups
```

**Test Group Admin Access:**
```bash
# Group admin should see ONLY their groups
curl -H "Authorization: Bearer $GROUP_ADMIN_TOKEN" \
  http://localhost:8000/api/v1/groups
# Result: Shows ONLY groups where they're admin
```

**Test Regular User Access:**
```bash
# Regular user should see empty list
curl -H "Authorization: Bearer $USER_TOKEN" \
  http://localhost:8000/api/v1/groups
# Result: Empty list (users don't manage groups)
```

---

## Adding Group Admins

### Method 1: Python Script (While Bot is Running)
```python
import asyncio
from motor.motor_asyncio import AsyncClient
from services.database import DatabaseService
from config.settings import config

async def add_admin():
    client = AsyncClient(config.MONGODB_URI)
    db = client[config.MONGODB_DB_NAME]
    db_service = DatabaseService(db)
    
    # Add group admin
    await db_service.add_group_admin(
        group_id=-123456789,      # Your group ID
        user_id=987654321,        # User's Telegram ID
        username="john",          # User's username
        first_name="John"         # User's first name
    )
    print("✅ Group admin added")
    client.close()

asyncio.run(add_admin())
```

### Method 2: MongoDB CLI
```bash
# Connect to MongoDB
mongosh

# Use your database
use telegram_bot_v3

# Add group admin
db.admins.insertOne({
  "user_id": 987654321,
  "group_id": -123456789,
  "username": "john",
  "first_name": "John",
  "role": "group_admin",
  "updated_at": new Date()
})

# Verify
db.admins.find({"role": "group_admin"})
```

---

## Troubleshooting

### ❌ Error: "TELEGRAM_BOT_TOKEN not found"
**Solution:**
```bash
# Make sure .env file exists and has the token
cat .env | grep TELEGRAM_BOT_TOKEN

# If missing, edit .env and add your token
TELEGRAM_BOT_TOKEN=your-actual-token
```

### ❌ Error: "MongoDB connection failed"
**Solution:**
```bash
# Check if MongoDB is running
mongosh  # If this connects, MongoDB is running

# Check MONGODB_URI is correct
cat .env | grep MONGODB_URI

# Test connection
python -c "from motor.motor_asyncio import AsyncClient; print('✅ Motor installed')"
```

### ❌ Error: "ModuleNotFoundError"
**Solution:**
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Or install specific package
pip install python-telegram-bot
```

### ❌ Bot not responding in Telegram
**Solution:**
1. Check bot has admin permissions in group
2. Verify bot token is correct
3. Check logs for errors: `tail -f logs/bot.log`
4. Ensure no firewall blocking connection

### ❌ API returns "Not authorized"
**Solution:**
1. Verify JWT token is valid: `curl http://localhost:8000/api/v1/health`
2. Check user is added as group admin: `db.admins.find({"user_id": YOUR_ID})`
3. Verify token has correct role: decode JWT at jwt.io

### ❌ "Port 8000 already in use"
**Solution:**
```bash
# Change API_PORT in .env to different port
API_PORT=8001

# Or kill process using port 8000
lsof -i :8000
kill -9 <PID>
```

---

## Production Deployment

### Before Going Live
1. ✅ Set `ENV=production` in `.env`
2. ✅ Set `DEBUG=false` in `.env`
3. ✅ Change `JWT_SECRET` to secure random string
4. ✅ Use MongoDB Atlas (not local)
5. ✅ Add all admin IDs to database
6. ✅ Test all commands thoroughly
7. ✅ Set up proper logging
8. ✅ Configure backups

### Deployment Options
- **VPS**: DigitalOcean, Linode, AWS EC2
- **Serverless**: AWS Lambda, Google Cloud Functions
- **Docker**: Containerize for easy deployment
- **Cloud**: Heroku, Railway, Render

---

## Common Commands Reference

```bash
# Start bot
python main.py

# Stop bot
Ctrl + C

# Check logs
tail -f logs/bot.log

# View database
mongosh
use telegram_bot_v3
db.admins.find()

# Reset database
db.dropDatabase()

# View environment
cat .env

# Test API
curl http://localhost:8000/api/v1/health
```

---

## File Structure
```
v3/
├── config/              # Configuration
│   ├── __init__.py
│   └── settings.py      # All settings
├── services/            # Business logic
│   ├── __init__.py
│   ├── database.py      # MongoDB + RBAC
│   └── auth.py          # JWT + Auth
├── bot/                 # Telegram bot
│   ├── __init__.py
│   └── handlers.py      # Commands
├── api/                 # FastAPI
│   ├── __init__.py
│   └── endpoints.py     # REST endpoints
├── core/                # Data models
│   ├── __init__.py
│   └── models.py        # Enums and dataclasses
├── utils/               # Utilities
│   ├── __init__.py
│   └── helpers.py       # Helper functions
├── frontend/            # Frontend client
│   └── service.ts       # TypeScript service
├── main.py              # Entry point
├── .env                 # Configuration (COPY FROM .env.example)
├── .env.example         # Template
├── requirements.txt     # Dependencies
└── logs/                # Log files (auto-created)
```

---

## Getting Help

- Check `logs/bot.log` for detailed error messages
- Review code comments in each file
- Look at examples in this guide
- Test with health endpoint: `curl http://localhost:8000/api/v1/health`

---

## Next Steps

1. ✅ Complete setup above
2. ✅ Add test users as group admins
3. ✅ Test all 7 bot commands
4. ✅ Test all 6 API endpoints
5. ✅ Monitor `logs/bot.log`
6. ✅ Deploy to production

Good luck! 🚀
