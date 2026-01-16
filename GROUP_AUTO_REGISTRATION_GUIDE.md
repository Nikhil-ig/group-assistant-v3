# Group Auto-Registration Integration Guide

## Overview

The Group Auto-Registration system automatically registers new groups in the database when:
1. The bot joins a new group
2. The bot encounters a group not yet in the database
3. Group data needs to be synced

This system captures and stores:
- Group ID and name
- Member count
- Admin count  
- Group type (group, supergroup, channel)
- Photo URL and description
- Creation timestamps
- Group settings and statistics

## API Endpoints

### 1. Auto-Register a Group
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

**Response:**
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

### 2. Ensure Group Exists
**POST** `/api/groups/ensure-exists`

Safe endpoint - creates group only if it doesn't exist. Idempotent (safe to call multiple times).

```bash
curl -X POST http://localhost:8001/api/groups/ensure-exists \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": -1001234567890,
    "group_name": "My Group"
  }'
```

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

### 4. Bulk Register Groups
**POST** `/api/groups/bulk-register`

Register multiple groups at once (useful for initialization).

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

## Python Telegram Bot Integration

### Using Pyrogram

```python
from pyrogram import Client, filters
from datetime import datetime
import httpx

async def ensure_group_registered(client: Client, group_id: int):
    """Ensure group is registered in database"""
    try:
        # Get group info
        chat = await client.get_chat(group_id)
        
        # Get member count
        members_count = await client.get_chat_members_count(group_id)
        
        # Get admin count (approximate)
        admin_count = 0
        async for member in client.get_chat_members(group_id, filter="administrators"):
            admin_count += 1
        
        # Register via API
        async with httpx.AsyncClient() as http:
            response = await http.post(
                'http://localhost:8001/api/groups/auto-register',
                json={
                    'group_id': group_id,
                    'group_name': chat.title,
                    'group_type': chat.type,
                    'member_count': members_count,
                    'admin_count': admin_count,
                    'description': chat.description or '',
                    'photo_url': chat.photo.big_file_id if chat.photo else '',
                }
            )
            
            result = response.json()
            print(f"Group registration: {result}")
            
    except Exception as e:
        print(f"Error registering group: {e}")


# Handler: Bot joined a new group
@app.on_message(filters.status_update.new_chat_members)
async def on_bot_join(client: Client, message):
    """Called when bot joins a new group"""
    # Check if bot was the one added
    for member in message.new_chat_members:
        if member.is_bot and member.is_self:
            print(f"Bot joined group: {message.chat.title}")
            
            # Auto-register the group
            await ensure_group_registered(client, message.chat.id)
            
            # Send welcome message
            await message.reply("Hello! I've been added to this group. 👋")
            break


# Handler: Bot receives any message
@app.on_message(filters.group)
async def on_group_message(client: Client, message):
    """Ensure every group is registered (backup)"""
    # This ensures groups are registered even if bot was added before
    await ensure_group_registered(client, message.chat.id)


# Handler: Bot removed from group
@app.on_message(filters.status_update.left_chat_members)
async def on_bot_removed(client: Client, message):
    """Called when bot is removed from a group"""
    for member in message.left_chat_members:
        if member.is_self:
            print(f"Bot removed from group: {message.chat.title}")
            
            # Deactivate in database
            async with httpx.AsyncClient() as http:
                await http.put(
                    f'http://localhost:8001/api/groups/deactivate/{message.chat.id}'
                )
```

### Using python-telegram-bot

```python
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import httpx

async def ensure_group_registered(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    """Ensure group is registered in database"""
    try:
        chat = await context.bot.get_chat(chat_id)
        chat_members_count = await context.bot.get_chat_member_count(chat_id)
        
        # Count administrators
        admins = await context.bot.get_chat_administrators(chat_id)
        admin_count = len(admins)
        
        # Register via API
        async with httpx.AsyncClient() as http:
            response = await http.post(
                'http://localhost:8001/api/groups/auto-register',
                json={
                    'group_id': chat_id,
                    'group_name': chat.title,
                    'group_type': chat.type,
                    'member_count': chat_members_count,
                    'admin_count': admin_count,
                    'description': chat.description or '',
                }
            )
            
            print(f"Group registration result: {response.json()}")
            
    except Exception as e:
        print(f"Error registering group: {e}")


async def on_bot_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Called when bot joins a new group"""
    if update.message.new_chat_members:
        for member in update.message.new_chat_members:
            if member.is_bot and member.id == context.bot.id:
                print(f"Bot joined group: {update.message.chat.title}")
                
                # Auto-register the group
                await ensure_group_registered(context, update.message.chat_id)
                
                # Send welcome message
                await update.message.reply_text("Hello! I've been added to this group. 👋")


async def on_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ensure every group is registered (backup)"""
    if update.message.chat.type in ['group', 'supergroup']:
        await ensure_group_registered(context, update.message.chat_id)


async def on_bot_removed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Called when bot is removed from a group"""
    if update.message.left_chat_member:
        if update.message.left_chat_member.id == context.bot.id:
            print(f"Bot removed from group: {update.message.chat.title}")
            
            # Deactivate in database
            async with httpx.AsyncClient() as http:
                await http.put(
                    f'http://localhost:8001/api/groups/deactivate/{update.message.chat_id}'
                )


# Setup
def main():
    application = Application.builder().token("YOUR_BOT_TOKEN").build()
    
    # Handlers
    application.add_handler(MessageHandler(
        filters.StatusUpdate.NEW_CHAT_MEMBERS,
        on_bot_join
    ))
    
    application.add_handler(MessageHandler(
        filters.ChatType.GROUPS,
        on_group_message
    ))
    
    application.add_handler(MessageHandler(
        filters.StatusUpdate.LEFT_CHAT_MEMBERS,
        on_bot_removed
    ))
    
    # Run
    application.run_polling()


if __name__ == '__main__':
    main()
```

## Database Schema

Groups are stored with this structure:

```json
{
  "_id": ObjectId(...),
  "group_id": -1001234567890,
  "group_name": "My Group",
  "group_type": "supergroup",
  "description": "Group description",
  "member_count": 150,
  "admin_count": 3,
  "photo_url": "https://example.com/photo.jpg",
  "is_active": true,
  "created_at": ISODate("2024-01-15T10:00:00Z"),
  "updated_at": ISODate("2024-01-15T10:00:00Z"),
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

## Best Practices

1. **Call on Bot Join**: Always call auto-register when bot joins a new group
2. **Periodic Updates**: Update stats periodically (every hour or when members join/leave)
3. **Handle Duplicates**: The API safely handles duplicate registrations (idempotent)
4. **Error Handling**: Wrap API calls in try-catch blocks
5. **Bulk Import**: Use bulk-register endpoint when initializing with existing groups
6. **Monitor**: Check the logs collection for registration events

## Testing

```bash
# Test auto-register
curl -X POST http://localhost:8001/api/groups/auto-register \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": -100123456789,
    "group_name": "Test Group",
    "member_count": 50,
    "admin_count": 2
  }' | jq

# Test ensure exists (idempotent)
curl -X POST http://localhost:8001/api/groups/ensure-exists \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": -100123456789,
    "group_name": "Test Group"
  }' | jq

# Check if group was registered
curl http://localhost:8001/api/dashboard/groups | jq '.[] | select(.group_id == -100123456789)'
```

## Troubleshooting

### Group Not Registering
1. Verify API is running: `curl http://localhost:8001/api/health`
2. Check backend logs for errors
3. Verify group_id is correct (negative number for Telegram groups)
4. Check MongoDB connection

### Duplicate Groups
- The system prevents duplicates automatically
- Updates existing group metadata if already registered

### Member Count Not Updating
- Ensure you're calling `/api/groups/update-stats` periodically
- Or call `/api/groups/auto-register` again with new counts
