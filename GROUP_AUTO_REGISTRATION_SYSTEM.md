# 🤖 Group Auto-Registration System

## Overview

The Group Auto-Registration system automatically registers Telegram groups in the database when:

1. **Bot joins a new group** - Triggered by `on_my_chat_member` or `new_chat_members` event
2. **Bot receives messages from unknown groups** - Automatic backup registration
3. **Group data doesn't exist** - Ensures all active groups are in database

When a group is registered, the following data is captured:
- ✅ Group ID (Telegram unique identifier)
- ✅ Group name
- ✅ Member count
- ✅ Admin count
- ✅ Group type (group, supergroup, channel)
- ✅ Description
- ✅ Photo URL
- ✅ Timestamps
- ✅ Auto-generated settings and statistics

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Telegram Groups                            │
│          (bot joins or sends message)                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Telegram Bot Handler                            │
│  (on_bot_join, on_message, on_bot_removed)                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│         Group Auto-Registration API                          │
│         (FastAPI routes on port 8001)                        │
│                                                              │
│  POST   /api/groups/auto-register                           │
│  POST   /api/groups/ensure-exists                           │
│  PUT    /api/groups/update-stats/{group_id}                 │
│  POST   /api/groups/bulk-register                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              MongoDB Database                                │
│  (bot_manager.groups collection)                             │
└─────────────────────────────────────────────────────────────┘
```

## API Endpoints

### 1. Auto-Register Group
**POST** `/api/groups/auto-register`

Registers a new group or updates existing group metadata.

```bash
curl -X POST http://localhost:8001/api/groups/auto-register \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": -1001234567890,
    "group_name": "My Awesome Group",
    "group_type": "supergroup",
    "member_count": 150,
    "admin_count": 3,
    "description": "A great group for discussions",
    "photo_url": "https://example.com/photo.jpg"
  }'
```

**Response (Created):**
```json
{
  "success": true,
  "action": "created",
  "group_id": -1001234567890,
  "group_name": "My Awesome Group",
  "members": 150,
  "admins": 3,
  "message": "Group My Awesome Group auto-registered successfully"
}
```

---

### 2. Ensure Group Exists
**POST** `/api/groups/ensure-exists`

Safe idempotent endpoint - creates group only if it doesn't exist. Safe to call multiple times.

```bash
curl -X POST http://localhost:8001/api/groups/ensure-exists \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": -1001234567890,
    "group_name": "My Group"
  }'
```

**Response (Already Exists):**
```json
{
  "success": true,
  "action": "exists",
  "group_id": -1001234567890,
  "message": "Group already registered"
}
```

---

### 3. Update Group Statistics
**PUT** `/api/groups/update-stats/{group_id}`

Update member count, admin count, and other statistics.

```bash
curl -X PUT http://localhost:8001/api/groups/update-stats/-1001234567890 \
  -H "Content-Type: application/json" \
  -d '{
    "member_count": 155,
    "admin_count": 4
  }'
```

**Response:**
```json
{
  "success": true,
  "group_id": -1001234567890,
  "members": 155,
  "admins": 4,
  "message": "Group stats updated"
}
```

---

### 4. Bulk Register Groups
**POST** `/api/groups/bulk-register`

Register multiple groups at once. Useful for initialization.

```bash
curl -X POST http://localhost:8001/api/groups/bulk-register \
  -H "Content-Type: application/json" \
  -d '{
    "groups": [
      {
        "group_id": -1001234567890,
        "group_name": "Group 1",
        "member_count": 100,
        "admin_count": 2
      },
      {
        "group_id": -1001234567891,
        "group_name": "Group 2",
        "member_count": 250,
        "admin_count": 5
      }
    ]
  }'
```

**Response:**
```json
{
  "success": true,
  "created": 2,
  "updated": 0,
  "failed": 0,
  "total": 2,
  "errors": [],
  "message": "Bulk registration complete: 2 created, 0 updated, 0 failed"
}
```

---

### 5. List All Groups
**GET** `/api/groups`

Get all registered groups (from dashboard routes).

```bash
curl http://localhost:8001/api/groups | python3 -m json.tool
```

## Database Schema

Groups are stored with this structure:

```json
{
  "_id": ObjectId("507f1f77bcf86cd799439011"),
  "group_id": -1001234567890,
  "group_name": "My Group",
  "group_type": "supergroup",
  "description": "Group description",
  "member_count": 150,
  "admin_count": 3,
  "photo_url": "https://example.com/photo.jpg",
  "is_active": true,
  "created_at": "2026-01-15T10:00:00.000000",
  "updated_at": "2026-01-15T10:00:00.000000",
  "metadata": {
    "auto_registered": true,
    "registration_source": "bot_join"
  },
  "settings": {
    "auto_warn_enabled": false,
    "auto_mute_enabled": false,
    "spam_threshold": 5,
    "profanity_filter": false
  },
  "stats": {
    "total_actions": 0,
    "total_warnings": 0,
    "total_mutes": 0,
    "total_bans": 0
  }
}
```

## Bot Integration

### Using python-telegram-bot

```python
from telegram.ext import Application, MessageHandler, filters
from bot_handlers import setup_bot_handlers

def main():
    application = Application.builder().token("YOUR_BOT_TOKEN").build()
    
    # Setup auto-registration handlers
    setup_bot_handlers(application)
    
    # Run the bot
    application.run_polling()

if __name__ == '__main__':
    main()
```

### Using Pyrogram

```python
from pyrogram import Client, filters
from bot_handlers import on_bot_join_pyrogram, on_bot_removed_pyrogram

app = Client("my_bot", api_id=12345, api_hash="...")

@app.on_message(filters.status_update.new_chat_members)
async def on_bot_join(client, message):
    for member in message.new_chat_members:
        if member.is_bot and member.is_self:
            await on_bot_join_pyrogram(client, message)
            break

app.run()
```

## Features

### ✅ Automatic Detection
- Detects new groups automatically when bot joins
- Backup automatic detection on every message
- No manual registration needed

### ✅ Data Capture
- Group name and ID
- Member and admin counts
- Description and photo
- Auto-generated settings and stats

### ✅ Idempotent Operations
- Safe to call multiple times
- No duplicate entries created
- Automatic updates if group exists

### ✅ Bulk Operations
- Register multiple groups at once
- Useful for initialization
- Efficient batch processing

### ✅ Periodic Updates
- Update statistics on schedule
- Keep member counts current
- Track changes over time

### ✅ Event Logging
- Log registration events
- Track which groups are active
- Monitor bot activity

## Configuration

Edit `bot_handlers.py` to customize:

```python
# Enable/disable auto-registration
AUTO_REGISTER_ENABLED = True

# Enable/disable periodic stats updates
PERIODIC_STATS_UPDATE_ENABLED = True

# API base URL (change if backend runs elsewhere)
API_BASE_URL = "http://localhost:8001/api"
```

## Testing

### Test Auto-Register
```bash
curl -X POST http://localhost:8001/api/groups/auto-register \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": -100123456789,
    "group_name": "Test Group",
    "member_count": 50,
    "admin_count": 2
  }' | jq
```

### Test Ensure Exists (Idempotent)
```bash
# First call - creates group
curl -X POST http://localhost:8001/api/groups/ensure-exists \
  -H "Content-Type: application/json" \
  -d '{"group_id": -100123456789, "group_name": "Test Group"}' | jq

# Second call - returns exists
curl -X POST http://localhost:8001/api/groups/ensure-exists \
  -H "Content-Type: application/json" \
  -d '{"group_id": -100123456789, "group_name": "Test Group"}' | jq
```

### Test Update Stats
```bash
curl -X PUT http://localhost:8001/api/groups/update-stats/-100123456789 \
  -H "Content-Type: application/json" \
  -d '{"member_count": 100, "admin_count": 3}' | jq
```

### Test Bulk Register
```bash
curl -X POST http://localhost:8001/api/groups/bulk-register \
  -H "Content-Type: application/json" \
  -d '{
    "groups": [
      {"group_id": -100111111111, "group_name": "Group 1", "member_count": 25},
      {"group_id": -100222222222, "group_name": "Group 2", "member_count": 40}
    ]
  }' | jq
```

### View All Registered Groups
```bash
curl http://localhost:8001/api/groups | jq '.' | head -50
```

## Troubleshooting

### ❌ Groups Not Registering
1. Check backend is running: `curl http://localhost:8001/api/health`
2. Check logs for errors
3. Verify group_id is correct (negative for Telegram groups)
4. Ensure MongoDB is connected

### ❌ "Database not initialized" Error
- Backend not running properly
- MongoDB connection failed
- API server crashed

### ❌ Duplicate Groups
- System prevents duplicates automatically
- Existing group metadata is updated
- No manual cleanup needed

### ❌ Member Count Not Updating
- Call `/api/groups/update-stats` periodically
- Or call `/api/groups/auto-register` again with new counts
- Setup periodic job for automatic updates

## Performance Considerations

### Database Queries
- Groups indexed by `group_id` for fast lookups
- Bulk operations use batch inserts
- Stats updates are atomic

### API Rate Limits
- No rate limiting on auto-register endpoints
- Consider adding if bot joins thousands of groups
- Batch operations recommended for bulk imports

### Memory Usage
- Lightweight group documents (~500 bytes each)
- Async operations for better throughput
- Bulk operations don't load all groups into memory

## Best Practices

1. **Call on Bot Join** ✅
   - Always call when bot joins new group
   - Use the event handler patterns

2. **Periodic Updates** ✅
   - Update stats every hour or as needed
   - Use scheduled jobs (e.g., job_queue)

3. **Error Handling** ✅
   - Wrap API calls in try-catch
   - Log failures for debugging
   - Implement retry logic if needed

4. **Bulk Operations** ✅
   - Use bulk-register for initialization
   - More efficient than individual requests
   - Better for large migrations

5. **Monitoring** ✅
   - Monitor registration events
   - Track failed registrations
   - Check database size periodically

## Files Created

1. **`group_auto_register_routes.py`** - FastAPI routes for auto-registration
2. **`bot_handlers.py`** - Bot event handlers for both Pyrogram and python-telegram-bot
3. **`GROUP_AUTO_REGISTRATION_GUIDE.md`** - Detailed integration guide
4. **`GROUP_AUTO_REGISTRATION_SYSTEM.md`** - This file (feature overview)

## Next Steps

1. ✅ Integrate bot handlers in your Telegram bot
2. ✅ Test with demo groups
3. ✅ Monitor auto-registration in logs
4. ✅ Setup periodic stats updates
5. ✅ View groups in dashboard
6. ✅ Implement any custom business logic

## Examples

### Python-Telegram-Bot Full Example
See `bot_handlers.py` - Contains complete working examples for both bot frameworks.

### Pyrogram Full Example
See `bot_handlers.py` - Includes Pyrogram-specific implementations.

### Dashboard Integration
Auto-registered groups automatically appear in the dashboard at:
- http://localhost:5174/dashboard
- Groups tab shows all registered groups
- Stats update in real-time

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the integration guide
3. Check backend logs: `curl http://localhost:8001/api/health`
4. Verify MongoDB data: `python3 check_db.py`
