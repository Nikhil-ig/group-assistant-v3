V3 TELEGRAM MODERATION BOT - QUICK START GUIDE
================================================

✅ COMPLETE IMPLEMENTATION DELIVERED
=====================================

You now have a complete, production-ready Telegram moderation bot with:
- Role-Based Access Control (RBAC)
- MongoDB database
- REST API with authentication
- Telegram bot with 7 commands
- Comprehensive audit logging
- Full type safety and error handling


📋 WHAT YOU HAVE
================

✅ Complete Backend
   • config/settings.py - Full configuration management
   • services/database.py - MongoDB operations with RBAC
   • services/auth.py - JWT authentication & authorization
   • bot/handlers.py - 7 Telegram commands
   • api/endpoints.py - REST API with 6 endpoints
   • main.py - Complete application startup

✅ All Files Created
   • v3/core/models.py ✅ (Existing from v2)
   • v3/core/__init__.py ✅
   • v3/config/ ✅ (settings.py complete)
   • v3/services/ ✅ (database.py & auth.py complete)
   • v3/bot/ ✅ (handlers.py complete)
   • v3/api/ ✅ (endpoints.py complete)
   • v3/main.py ✅
   • v3/.env.example ✅


🔐 ROLE-BASED ACCESS CONTROL (RBAC)
===================================

Three roles with different permissions:

1️⃣ SUPERADMIN
   ✓ Can see ALL groups
   ✓ Can control ALL groups
   ✓ Can execute any action in any group
   ✓ Can view all audit logs
   → Set SUPERADMIN_ID in .env to your Telegram user ID

2️⃣ GROUP_ADMIN
   ✓ Can see ONLY their own groups
   ✓ Can control ONLY their own groups
   ✓ Can view logs for their groups only
   ✗ Cannot see or control other groups
   → Added via MongoDB admins collection

3️⃣ USER
   ✓ Can view audit logs (limited)
   ✗ Cannot execute moderation actions
   ✗ Cannot manage groups


🚀 QUICK START (5 MINUTES)
==========================

Step 1: Set Up Environment
   a) Copy .env.example to .env
      $ cp v3/.env.example v3/.env
   
   b) Edit v3/.env with:
      - TELEGRAM_BOT_TOKEN (from @BotFather)
      - SUPERADMIN_ID (your Telegram user ID)
      - MONGODB_URI (MongoDB connection)
      - JWT_SECRET (random string)

Step 2: Install Dependencies
   $ pip install -r requirements.txt
   
   Required packages:
   - python-telegram-bot[all]
   - fastapi
   - uvicorn
   - motor (async MongoDB)
   - pydantic
   - pyjwt
   - python-dotenv

Step 3: Run the Bot
   $ cd v3
   $ python main.py
   
   Expected output:
   ✅ MongoDB connected successfully
   ✅ Authentication service initialized
   ✅ Telegram bot initialized
   ✅ ALL SYSTEMS INITIALIZED
   🤖 Starting Telegram bot polling...
   🌐 Starting API server on 0.0.0.0:8000...


💻 TELEGRAM COMMANDS
====================

All commands require admin permission for the group.

/ban <user_id> [reason]
   Ban a user from the group
   Example: /ban 123456789 spam

/unban <user_id>
   Unban a user from the group
   Example: /unban 123456789

/kick <user_id> [reason]
   Kick a user from the group
   Example: /kick 123456789 off-topic

/warn <user_id> [reason]
   Warn a user
   Example: /warn 123456789 first warning

/mute <user_id> [hours] [reason]
   Mute a user for specified hours
   Example: /mute 123456789 24 spam behavior

/logs [limit]
   Show recent audit logs
   Example: /logs 10

/stats
   Show group statistics
   Example: /stats


🌐 REST API ENDPOINTS
=====================

Base URL: http://localhost:8000/api/v1

1. POST /auth/login
   Authenticate user and get JWT token
   
   Request:
   {
     "user_id": 123456789,
     "username": "john_doe",
     "first_name": "John"
   }
   
   Response:
   {
     "ok": true,
     "token": "eyJhbGc...",
     "role": "superadmin",
     "message": "Login successful"
   }

2. GET /groups
   Get groups accessible to user (with RBAC)
   
   Header: Authorization: Bearer {token}
   
   SUPERADMIN: Returns ALL groups
   GROUP_ADMIN: Returns only their groups
   USER: Returns empty list
   
   Response:
   {
     "ok": true,
     "groups": [...],
     "total_count": 5
   }

3. POST /groups/{group_id}/actions
   Execute moderation action
   
   Request:
   {
     "action_type": "ban",
     "target_user_id": 987654321,
     "target_username": "spam_user",
     "reason": "spam behavior",
     "duration_hours": null
   }
   
   Response:
   {
     "ok": true,
     "action_id": "123456",
     "message": "ban action executed successfully",
     "timestamp": "2024-12-29T10:00:00"
   }

4. GET /groups/{group_id}/logs
   Get audit logs for group (paginated)
   
   Query params:
   - page: 1 (default)
   - page_size: 20 (default, max 100)
   
   Response:
   {
     "ok": true,
     "group_id": -123456789,
     "logs": [...],
     "total_count": 45,
     "page": 1,
     "page_size": 20
   }

5. GET /groups/{group_id}/metrics
   Get statistics for group
   
   Response:
   {
     "ok": true,
     "group_id": -123456789,
     "total_actions": 42,
     "actions_breakdown": {
       "ban": 10,
       "kick": 12,
       "warn": 20
     },
     "last_action_at": "2024-12-29T10:00:00"
   }

6. GET /health
   Health check
   
   Response:
   {
     "status": "healthy",
     "timestamp": "2024-12-29T10:00:00"
   }


🗄️ MONGODB COLLECTIONS
======================

5 collections for complete tracking:

1. groups
   - group_id, group_name
   - created_at, updated_at
   - is_active

2. admins
   - user_id, username, first_name
   - group_id (null for superadmin)
   - role (superadmin or group_admin)
   - created_at, updated_at
   - Indexed for fast lookup

3. audit_logs
   - group_id, action_type
   - admin_id, admin_username
   - target_user_id, target_username
   - reason, duration_hours
   - timestamp
   - Indexed by group_id and timestamp for performance

4. metrics
   - group_id, total_actions
   - actions (breakdown by type)
   - last_action_at

5. users (optional, for future use)
   - user_id, username, first_name
   - role, created_at


🔗 ADDING ADMIN ROLES
====================

To add group admin (can control only their group):
   
Python:
   from v3.services.database import DatabaseService
   
   # Connect to MongoDB
   from motor.motor_asyncio import AsyncClient
   client = AsyncClient("mongodb://localhost:27017")
   db = client["telegram_bot_v3"]
   db_service = DatabaseService(db)
   
   # Add group admin
   await db_service.add_group_admin(
       group_id=-123456789,
       user_id=987654321,
       username="john_doe",
       first_name="John"
   )

To add superadmin:
   # Add superadmin
   await db_service.add_superadmin(
       user_id=987654321,
       username="john_doe",
       first_name="John"
   )

MongoDB (direct):
   db.admins.insertOne({
     user_id: 987654321,
     username: "john_doe",
     first_name: "John",
     group_id: -123456789,
     role: "group_admin",
     created_at: new Date(),
     updated_at: new Date()
   })


📊 EXAMPLE WORKFLOW
===================

1. User logs in via API
   POST /api/v1/auth/login
   → Gets JWT token with role

2. User lists their groups
   GET /api/v1/groups
   → SUPERADMIN sees all groups
   → GROUP_ADMIN sees only their groups

3. User bans someone in their group
   POST /api/v1/groups/-123456789/actions
   → RBAC checks user can manage this group
   → Action logged to MongoDB
   → Metrics updated

4. User views audit logs
   GET /api/v1/groups/-123456789/logs
   → RBAC checks user can view this group
   → Returns paginated audit logs


🧪 TESTING EXAMPLES
===================

Test 1: Login and Get Token
   curl -X POST http://localhost:8000/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": 123456789,
       "username": "test_user",
       "first_name": "Test"
     }'

Test 2: Get Groups (requires authentication)
   TOKEN="eyJhbGc..."
   curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8000/api/v1/groups

Test 3: Ban User
   TOKEN="eyJhbGc..."
   curl -X POST http://localhost:8000/api/v1/groups/-123456789/actions \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "action_type": "ban",
       "target_user_id": 987654321,
       "reason": "spam"
     }'

Test 4: View Logs
   TOKEN="eyJhbGc..."
   curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8000/api/v1/groups/-123456789/logs?page=1&page_size=10

Test 5: Health Check
   curl http://localhost:8000/api/v1/health


📝 CONFIGURATION OPTIONS
=======================

See v3/.env.example for all options:

Essential:
   TELEGRAM_BOT_TOKEN - Required
   MONGODB_URI - Required
   JWT_SECRET - Required
   SUPERADMIN_ID - Recommended

Optional:
   ENV - development or production
   LOG_LEVEL - DEBUG, INFO, WARNING, ERROR
   CORS_ORIGINS - For frontend
   RATE_LIMITING - Enable/disable
   Feature flags - Enable/disable individual features


🐛 TROUBLESHOOTING
=================

"MongoDB connection failed"
   → Check MONGODB_URI in .env
   → Ensure MongoDB is running: mongod
   → Verify connection: mongo "mongodb://localhost:27017"

"Token validation failed"
   → Check JWT_SECRET in .env
   → Ensure token is in Authorization header
   → Check token hasn't expired (24 hours default)

"Not authorized" error on group action
   → Check if user is admin in that group
   → For SUPERADMIN, verify SUPERADMIN_ID is set
   → For GROUP_ADMIN, verify added to admins collection

"Bot not responding to commands"
   → Check bot token is correct
   → Ensure bot is added to group
   → Check bot has admin permissions in group
   → Monitor logs: tail -f logs/v3_bot.log

"API endpoint returns 403"
   → User doesn't have permission for that action
   → SUPERADMIN can access all groups
   → GROUP_ADMIN can only access their groups
   → USER cannot execute actions


📚 NEXT STEPS
=============

1. Configure .env with your settings
2. Set up MongoDB locally or cloud (MongoDB Atlas)
3. Get Telegram bot token from @BotFather
4. Set your user ID as SUPERADMIN
5. Install dependencies
6. Run the bot
7. Test in Telegram
8. Test API endpoints with curl
9. Set up web dashboard (optional)


✨ FEATURES SUMMARY
===================

✅ 7 Bot Commands
   /ban, /unban, /kick, /warn, /mute, /logs, /stats

✅ 6 REST API Endpoints
   login, groups list, execute action, audit logs, metrics, health

✅ Full RBAC
   SUPERADMIN (all groups), GROUP_ADMIN (own groups), USER (view logs)

✅ MongoDB Storage
   Groups, admins, audit logs, metrics, users

✅ JWT Authentication
   Secure token-based auth with 24-hour expiration

✅ Comprehensive Logging
   All actions logged to MongoDB and files

✅ Type Safety
   Full type hints in Python, ready for TypeScript frontend

✅ Error Handling
   Complete error handling with helpful messages

✅ Async/Await
   100% async Python code for performance

✅ Production Ready
   Dev and production configs, validation, health checks


🎉 YOU'RE READY!
===============

The entire system is implemented and ready to run.
Follow the Quick Start section above to get started.

For detailed documentation, see:
   - V3_README.md (complete system overview)
   - V3_ARCHITECTURE.md (technical architecture)
   - V3_IMPLEMENTATION_GUIDE.md (implementation details)

Questions? Check the troubleshooting section above.
Good luck! 🚀
