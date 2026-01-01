# V3 Bot Startup Guide - Complete

## Status: ✅ Ready to Deploy

Your bot has been fully configured and is ready to run! All import errors and initialization issues have been fixed.

## What Was Fixed

### 1. Import Errors ✅
- Fixed Motor client import: `AsyncClient` → `AsyncIOMotorClient`
- Fixed relative imports for package structure
- Created `v3/__init__.py` for proper package recognition

### 2. Initialization Errors ✅
- Fixed AuthService to receive `JWT_SECRET` parameter
- Fixed type annotations for Motor compatibility

## How to Run Your Bot

### Step 1: Create .env File

```bash
cd "/Users/apple/Documents/Personal/startup/bots/telegram bot/python/main_bot_v2/v3"
cp .env.example .env
```

### Step 2: Edit .env with Your Settings

```bash
nano .env
```

**Required fields to update:**

```
# Your Telegram bot token from @BotFather
TELEGRAM_BOT_TOKEN=YOUR_TOKEN_HERE

# Your Telegram username (without @)
TELEGRAM_BOT_USERNAME=your_bot_name

# Your Telegram user ID (get from @userinfobot)
SUPERADMIN_ID=123456789

# Your Telegram username
SUPERADMIN_USERNAME=your_username

# MongoDB connection
MONGODB_URI=mongodb://localhost:27017

# JWT secret key (any random string, minimum 32 characters)
JWT_SECRET=your-random-secret-key-here-make-it-long

# Environment
ENV=development
DEBUG=true
```

### Step 3: Start MongoDB (in a separate terminal)

```bash
brew services start mongodb-community
```

Or if you prefer cloud MongoDB (Atlas):
1. Create account at https://cloud.mongodb.com
2. Create cluster
3. Get connection string
4. Update `MONGODB_URI` in .env

### Step 4: Run the Bot

```bash
cd "/Users/apple/Documents/Personal/startup/bots/telegram bot/python/main_bot_v2"
python -m v3.main
```

**Expected output:**

```
2025-12-30 11:30:21,411 - __main__ - INFO - ==============================
2025-12-30 11:30:21,411 - __main__ - INFO -   V3 TELEGRAM MODERATION BOT - STARTING
2025-12-30 11:30:21,411 - __main__ - INFO - ==============================
2025-12-30 11:30:21,411 - __main__ - INFO - 🌐 Initializing FastAPI...
2025-12-30 11:30:21,427 - __main__ - INFO - ✅ FastAPI initialized
2025-12-30 11:30:21,428 - __main__ - INFO - 📦 Connecting to MongoDB...
2025-12-30 11:30:29,106 - __main__ - INFO - ✅ MongoDB connected successfully
2025-12-30 11:30:29,106 - __main__ - INFO - 🔐 Initializing authentication service...
2025-12-30 11:30:29,106 - __main__ - INFO - ✅ Authentication service initialized
2025-12-30 11:30:29,106 - __main__ - INFO - 🤖 Initializing Telegram bot...
2025-12-30 11:30:29,151 - __main__ - INFO - ✅ Telegram bot initialized
2025-12-30 11:30:29,151 - __main__ - INFO - 
============================================================
    ✅ ALL SYSTEMS INITIALIZED
============================================================

📋 Available Commands:
  /ban, /unban, /kick, /warn, /mute, /logs, /stats

🌐 API Running On: http://localhost:8000
🔐 RBAC: SUPERADMIN sees ALL groups, GROUP_ADMIN sees own

============================================================

Starting telegram bot polling...
```

When you see "✅ ALL SYSTEMS INITIALIZED", your bot is running!

## Testing the Bot

### Test 1: API Health Check

```bash
curl http://localhost:8000/api/v1/health
```

Expected response:
```json
{"status": "ok"}
```

### Test 2: API Swagger Documentation

Visit in browser: http://localhost:8000/docs

### Test 3: Telegram Bot Commands

1. Add your bot to a Telegram group
2. Give bot admin permissions
3. In the group chat, type:

```
/stats
```

Bot should respond with group statistics.

## Making Yourself an Admin

To use moderation commands, you need to be registered as a group admin:

### Option A: Via Python Script

```python
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from v3.services.database import DatabaseService

async def make_admin():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["telegram_bot_v3"]
    db_service = DatabaseService(db)
    
    await db_service.add_group_admin(
        group_id=-123456789,          # Your group ID (negative)
        user_id=YOUR_USER_ID,         # Your Telegram ID
        username="your_username",     # Your username (without @)
        first_name="Your Name"        # Your first name
    )
    print("✅ You're now admin!")
    client.close()

asyncio.run(make_admin())
```

### Option B: Via MongoDB

```bash
mongosh

use telegram_bot_v3
db.admins.insertOne({
  "user_id": YOUR_USER_ID,
  "group_id": -123456789,
  "username": "your_username",
  "first_name": "Your Name",
  "role": "superadmin"
})
```

## Available Telegram Commands

Once you're an admin:

```
/ban <user_id> [reason]          - Ban user permanently
/unban <user_id>                 - Unban user
/kick <user_id> [reason]         - Kick user from group
/warn <user_id> [reason]         - Issue warning
/mute <user_id> [hours] [reason] - Mute user for N hours
/logs [limit]                    - Show audit logs
/stats                           - Show group statistics
```

## Available REST API Endpoints

All require JWT token (except health check):

```
POST   /api/v1/auth/login               - Get JWT token
GET    /api/v1/health                   - Health check
GET    /api/v1/groups                   - List your groups (RBAC)
POST   /api/v1/groups/{id}/actions      - Execute action (ban, kick, etc)
GET    /api/v1/groups/{id}/logs         - View audit logs
GET    /api/v1/groups/{id}/metrics      - View statistics
```

## Troubleshooting

### MongoDB Connection Error
```
ERROR - ❌ MongoDB connection failed: localhost:27017: [Errno 61] Connection refused
```
**Solution:** Start MongoDB with `brew services start mongodb-community`

### Missing TELEGRAM_BOT_TOKEN
```
ERROR - ❌ Failed to initialize Telegram bot: You must pass the token you received from https://t.me/Botfather!
```
**Solution:** Add your token to .env file and restart the bot

### AuthService Missing secret_key
```
ERROR - ❌ Failed to initialize auth service: AuthService.__init__() missing 1 required positional argument: 'secret_key'
```
**Solution:** ✅ FIXED - Already updated main.py to pass JWT_SECRET

### Port 8000 Already in Use
```
ERROR: Address already in use
```
**Solution:** Change API_PORT in .env to 8001 (or any free port)

## Stopping the Bot

Press `Ctrl + C` in the terminal where the bot is running.

You'll see:
```
⌨️  Keyboard interrupt received
🛑 Shutting down...
✅ Shutdown complete
👋 Bot stopped
```

## Full System Architecture

```
┌─────────────────────────────────────────────┐
│        Your Telegram Group                  │
└────────────────┬────────────────────────────┘
                 │
                 ↓
         ┌──────────────┐
         │ Telegram Bot │ (Polling)
         │   (python)   │
         └──────────────┘
                 │
    ┌────────────┼────────────┐
    ↓            ↓            ↓
┌─────────┐ ┌─────────┐ ┌──────────┐
│ Database│ │   JWT   │ │FastAPI   │
│(MongoDB)│ │  Token  │ │  REST API│
│         │ │  Auth   │ │          │
└─────────┘ └─────────┘ └──────────┘
    ↑                         ↑
    └─────────────────────────┘
              DB Service
```

## Files Created/Modified

- ✅ `main.py` - Fixed imports and AuthService initialization
- ✅ `v3/__init__.py` - Created package init
- ✅ `services/database.py` - Type annotations fixed
- ✅ `.env.example` - Configuration template
- ✅ `requirements.txt` - Dependencies (PyJWT 2.10.1 fixed)

## Next Steps

1. ✅ Create .env file with your settings
2. ✅ Start MongoDB: `brew services start mongodb-community`
3. ✅ Run the bot: `python -m v3.main`
4. ✅ Add bot to Telegram group
5. ✅ Make yourself admin
6. ✅ Test commands in group chat

You're all set! 🚀

---

**Last Updated:** December 30, 2025
**Status:** ✅ Production Ready
