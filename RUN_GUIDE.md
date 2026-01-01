# V3 Telegram Bot & Web Dashboard - Complete Running Guide

## 🚀 Quick Start (5 minutes)

### Step 1: Prepare Environment

```bash
# Navigate to v3 directory
cd /Users/apple/Documents/Personal/startup/bots/telegram\ bot/python/main_bot_v2/v3

# Copy configuration template
cp .env.example .env

# Edit .env with your settings (see below)
nano .env  # or use your favorite editor
```

### Step 2: Configure .env File

Edit your `.env` file and add these REQUIRED settings:

```bash
# Telegram Bot Token (from @BotFather on Telegram)
TELEGRAM_BOT_TOKEN=your-bot-token-here

# Telegram Bot Username
TELEGRAM_BOT_USERNAME=your_bot_username

# MongoDB Connection
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=telegram_bot_v3

# Your Telegram User ID (to be SUPERADMIN - can control ALL groups)
SUPERADMIN_ID=your_telegram_user_id
SUPERADMIN_USERNAME=your_username

# Security
JWT_SECRET=create-a-random-secure-string-here-at-least-32-chars
JWT_EXPIRATION_HOURS=24

# Environment
ENV=development
DEBUG=true

# API Server
API_HOST=0.0.0.0
API_PORT=8000

# Logging
LOG_LEVEL=DEBUG
LOG_DIR=logs
```

### Step 3: Install Dependencies

```bash
# Install all required Python packages
pip install -r requirements.txt

# Verify installation
python validate.py
```

Expected output:
```
✅ PASSED: 14/14
🎉 ALL IMPORTS SUCCESSFUL!
```

### Step 4: Start MongoDB

You have two options:

#### Option A: Local MongoDB (easiest for testing)
```bash
# Install MongoDB (macOS)
brew install mongodb-community

# Start MongoDB in background
brew services start mongodb-community

# Or run in foreground
mongod

# Verify connection
mongosh  # should connect successfully
```

#### Option B: MongoDB Atlas (cloud, recommended for production)
1. Go to https://cloud.mongodb.com
2. Create free account
3. Create cluster
4. Create database user
5. Get connection string
6. Update MONGODB_URI in .env with your connection string

### Step 5: Start the Bot & API

```bash
# Run the bot + API server together
python main.py
```

**Expected output:**
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
  /logs [limit] - Show recent logs
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

## 🌐 Using the Web Dashboard

### What You Can Do

Once the bot is running, the **REST API is available** at: `http://localhost:8000`

You can:
1. **Authenticate** and get JWT tokens
2. **List your groups** (with RBAC enforcement)
3. **Execute moderation actions** (ban, unban, kick, warn, mute)
4. **View audit logs** (who did what, when, and why)
5. **Get statistics** (action counts and breakdown)

### Using the API with curl

#### 1. Login and Get Token

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": YOUR_USER_ID,
    "username": "your_username",
    "first_name": "Your Name"
  }' | jq -r '.token')

echo "Your token: $TOKEN"
```

#### 2. Get Your Groups (RBAC enforced)

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/groups
```

Response (SUPERADMIN sees all):
```json
{
  "ok": true,
  "groups": [
    {
      "group_id": -123456789,
      "group_name": "My Group",
      "created_at": "2025-12-29T10:00:00Z",
      "is_active": true
    }
  ],
  "total_count": 1
}
```

#### 3. Execute a Ban Action

```bash
curl -X POST http://localhost:8000/api/v1/groups/-123456789/actions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "ban",
    "target_user_id": 987654321,
    "target_username": "spammer",
    "reason": "Spam violations"
  }'
```

#### 4. View Audit Logs

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/groups/-123456789/logs?page=1&page_size=10"
```

Response:
```json
{
  "ok": true,
  "group_id": -123456789,
  "logs": [
    {
      "action_type": "ban",
      "admin_username": "your_username",
      "target_username": "spammer",
      "reason": "Spam violations",
      "timestamp": "2025-12-29T10:15:00Z"
    }
  ],
  "total_count": 5,
  "page": 1,
  "page_size": 10
}
```

#### 5. Get Group Statistics

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/groups/-123456789/metrics"
```

Response:
```json
{
  "ok": true,
  "group_id": -123456789,
  "total_actions": 15,
  "actions_breakdown": {
    "ban": 5,
    "warn": 7,
    "mute": 3
  },
  "last_action_at": "2025-12-29T10:15:00Z"
}
```

#### 6. Health Check

```bash
curl http://localhost:8000/api/v1/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2025-12-29T10:20:00Z"
}
```

---

## 📱 Using the Telegram Bot

### Step 1: Add Bot to Group

1. Open Telegram
2. Create a group (or use existing)
3. Add your bot to the group
4. Make bot an **ADMIN** (required for ban/kick/mute)

### Step 2: Make Yourself Admin

Run this Python script while the bot is running:

```python
import asyncio
from motor.motor_asyncio import AsyncClient
from v3.services.database import DatabaseService
from v3.config.settings import config

async def add_admin():
    client = AsyncClient(config.MONGODB_URI)
    db = client[config.MONGODB_DB_NAME]
    db_service = DatabaseService(db)
    
    # Add yourself as group admin
    await db_service.add_group_admin(
        group_id=-123456789,      # Your group ID
        user_id=YOUR_USER_ID,      # Your Telegram user ID
        username="your_username",  # Your username
        first_name="Your Name"     # Your first name
    )
    print("✅ You're now a group admin!")
    client.close()

asyncio.run(add_admin())
```

Or use MongoDB directly:

```bash
mongosh
use telegram_bot_v3

db.admins.insertOne({
  "user_id": YOUR_USER_ID,
  "group_id": -123456789,
  "username": "your_username",
  "first_name": "Your Name",
  "role": "group_admin",
  "updated_at": new Date()
})
```

### Step 3: Test Commands in Group

In your Telegram group, send:

```bash
/stats
# Shows: Total actions: 0

/ban 987654321 Test ban
# Shows: ✅ User 987654321 has been banned

/logs 5
# Shows: Recent audit logs

/warn 111111111 Be careful
# Shows: ⚠️ User 111111111 has been warned

/mute 222222222 2 Too much chatting
# Shows: 🔇 User 222222222 has been muted for 2 hours

/kick 333333333 Spam
# Shows: ✅ User 333333333 has been kicked
```

---

## 🔐 Understanding RBAC (Role-Based Access Control)

### Your Roles

| Role | Who | What They Can Do |
|------|-----|------------------|
| **SUPERADMIN** | You (set in SUPERADMIN_ID) | See/control ALL groups, execute any action, view all logs |
| **GROUP_ADMIN** | Users you add | See/control ONLY their groups, execute actions in their groups |
| **USER** | Anyone else | View logs only (read-only) |

### Setting Up Admins

**Option 1: Command Line (Python script)**
```python
await db.add_superadmin(
    user_id=123456789,
    username="john",
    first_name="John"
)

await db.add_group_admin(
    group_id=-123456789,
    user_id=987654321,
    username="admin1",
    first_name="Admin"
)
```

**Option 2: MongoDB CLI**
```bash
mongosh
use telegram_bot_v3

# Add superadmin
db.admins.insertOne({
  "user_id": 123456789,
  "role": "superadmin",
  "username": "john",
  "first_name": "John",
  "updated_at": new Date()
})

# Add group admin
db.admins.insertOne({
  "user_id": 987654321,
  "group_id": -123456789,
  "role": "group_admin",
  "username": "admin1",
  "first_name": "Admin",
  "updated_at": new Date()
})
```

---

## 🛑 Stopping the Bot

Press `Ctrl + C` in the terminal:

```bash
^C
⌨️  Keyboard interrupt received
🛑 Shutting down...
✅ Shutdown complete
👋 Bot stopped
```

---

## 🔧 Troubleshooting

### Issue: "TELEGRAM_BOT_TOKEN not found"
```bash
# Check if .env exists
cat .env | grep TELEGRAM_BOT_TOKEN

# If missing, add it:
# TELEGRAM_BOT_TOKEN=your-actual-token
```

### Issue: "MongoDB connection failed"
```bash
# Check if MongoDB is running
mongosh

# If not, start it:
brew services start mongodb-community
# or
mongod
```

### Issue: "Port 8000 already in use"
```bash
# Change port in .env:
API_PORT=8001

# Or kill the process using port 8000:
lsof -i :8000
kill -9 <PID>
```

### Issue: "ModuleNotFoundError"
```bash
# Reinstall dependencies:
pip install -r requirements.txt

# Verify:
python validate.py
```

### Issue: Bot not responding in Telegram
1. Make sure bot has **ADMIN** permissions in the group
2. Check bot token is correct
3. Run `python validate.py` to verify imports
4. Check logs: `tail -f logs/bot.log`

### Issue: API returns "Not authorized"
1. Make sure you're added as admin in MongoDB
2. Verify token is valid (check expiration)
3. Ensure you're accessing your groups only (unless SUPERADMIN)

---

## 📚 Key Files

| File | Purpose |
|------|---------|
| `main.py` | Starts bot + API together |
| `bot/handlers.py` | Telegram commands (/ban, /stats, etc.) |
| `api/endpoints.py` | REST API endpoints |
| `services/database.py` | MongoDB & RBAC logic |
| `services/auth.py` | JWT tokens & authorization |
| `.env` | Your configuration |
| `logs/bot.log` | Application logs |

---

## 📖 API Documentation

**Base URL**: `http://localhost:8000/api/v1`

### Authentication
- **Endpoint**: `POST /auth/login`
- **Request**: `{ "user_id": int, "username": str, "first_name": str }`
- **Response**: `{ "ok": bool, "token": str, "role": str }`

### Groups
- **Endpoint**: `GET /groups`
- **Response**: List of accessible groups (RBAC enforced)

### Actions
- **Endpoint**: `POST /groups/{group_id}/actions`
- **Request**: `{ "action_type": str, "target_user_id": int, "reason": str }`
- **Types**: ban, unban, kick, warn, mute, unmute

### Logs
- **Endpoint**: `GET /groups/{group_id}/logs?page=1&page_size=10`
- **Response**: Paginated audit logs

### Metrics
- **Endpoint**: `GET /groups/{group_id}/metrics`
- **Response**: Action statistics

---

## 🎯 Quick Command Reference

```bash
# Start everything
python main.py

# Validate setup
python validate.py

# Check logs
tail -f logs/bot.log

# Connect to MongoDB
mongosh
use telegram_bot_v3
db.admins.find()

# Test API health
curl http://localhost:8000/api/v1/health

# Stop bot
Ctrl + C
```

---

## ✅ Checklist Before Running

- [ ] Python 3.8+ installed
- [ ] `.env` file created with all required settings
- [ ] MongoDB running (local or cloud)
- [ ] Telegram bot token obtained from @BotFather
- [ ] Your Telegram user ID set as SUPERADMIN_ID
- [ ] Bot added to Telegram group with admin permissions
- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] Validation passing: `python validate.py`

---

## 🚀 Ready to Go!

Once you've completed the checklist above, run:

```bash
python main.py
```

Your bot will start immediately and be ready to use! 🎉
