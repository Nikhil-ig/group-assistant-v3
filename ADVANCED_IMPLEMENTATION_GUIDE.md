# 🚀 Advanced Bot Implementation Guide

## Overview
Transform your bot from basic to **ADVANCED** with:
- ✅ No auto-delete (messages stay)
- ✅ Settings command with toggles
- ✅ Everything saved to database
- ✅ Member tracking
- ✅ Admin management
- ✅ Moderation roles
- ✅ Command history
- ✅ Event logging
- ✅ Statistics & Analytics

---

## Phase 1: Database Integration (COMPLETED ✅)

### Files Created:
1. **centralized_api/models/advanced_models.py**
   - GroupSettingsModel
   - MemberModel
   - AdminModel
   - ModerationRoleModel
   - CommandHistoryModel
   - EventLogModel
   - GroupStatisticsModel

2. **centralized_api/db/advanced_db.py**
   - AdvancedDBService with CRUD operations
   - Methods for all models
   - Query optimization

3. **centralized_api/api/advanced_routes.py**
   - REST API endpoints for all features
   - Settings management
   - Member tracking
   - Admin management
   - Role management
   - History logging
   - Event logging
   - Statistics

---

## Phase 2: Bot Updates (IN PROGRESS)

### Changes Needed in bot/main.py:

#### 1. Remove Auto-Delete
**Current:**
```python
async def send_and_delete(message: Message, text: str, delay: int = 5, **kwargs):
    msg = await message.answer(text, **kwargs)
    await asyncio.sleep(delay)
    await msg.delete()
```

**New:**
```python
async def send_response(message: Message, text: str, **kwargs):
    """Send response without deleting"""
    return await message.answer(text, **kwargs)
```

#### 2. Update All send_and_delete() Calls
Replace all instances of:
```python
await send_and_delete(message, response, parse_mode=ParseMode.HTML)
```

With:
```python
# Option A: Keep message permanently
sent_msg = await send_response(message, response, parse_mode=ParseMode.HTML)

# Option B: Keep message with buttons
sent_msg = await send_response(
    message, 
    response,
    parse_mode=ParseMode.HTML,
    reply_markup=keyboard
)
```

#### 3. Add Settings Command
```python
@router.message(Command("settings"))
async def cmd_settings(message: Message):
    """Open settings menu"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔔 Welcome Messages", callback_data="set_welcome")],
        [InlineKeyboardButton(text="👤 Member Tracking", callback_data="set_members")],
        [InlineKeyboardButton(text="⚖️ Moderation", callback_data="set_moderation")],
        [InlineKeyboardButton(text="📊 Statistics", callback_data="set_stats")],
        [InlineKeyboardButton(text="🔐 Roles", callback_data="set_roles")],
        [InlineKeyboardButton(text="🏠 Back", callback_data="start")],
    ])
    
    response = """
╔═════════════════════════════════╗
║ ⚙️  BOT SETTINGS                ║
╚═════════════════════════════════╝

Configure your bot with:
• Welcome/Leave messages
• Member tracking
• Moderation rules
• Statistics collection
• Custom roles

Choose an option below:
"""
    
    await send_response(
        message,
        response,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard
    )
    
    # Log this action
    await api_client.execute_action({
        "action_type": "log_command",
        "group_id": message.chat.id,
        "user_id": message.from_user.id,
        "command": "settings",
        "status": "success"
    })
```

#### 4. Add Event Logging
```python
async def log_event(
    group_id: int,
    event_type: str,
    user_id: int,
    triggered_by: Optional[int] = None,
    event_data: Optional[dict] = None
):
    """Log event to database via API"""
    try:
        await api_client.execute_action({
            "action_type": "log_event",
            "group_id": group_id,
            "event_type": event_type,
            "user_id": user_id,
            "triggered_by": triggered_by,
            "event_data": event_data or {}
        })
    except Exception as e:
        logger.error(f"Failed to log event: {e}")
```

#### 5. Track Member Join
```python
@router.my_chat_member()
async def handle_my_chat_member(update: ChatMemberUpdated):
    """Handle bot join/leave"""
    chat = update.chat
    
    if update.new_chat_member.status == "member":
        # Bot added to group - create default settings
        logger.info(f"Bot added to group {chat.id}")
        
        # Create settings in API
        await api_client.execute_action({
            "action_type": "create_settings",
            "group_id": chat.id,
            "group_name": chat.title
        })
        
        # Log event
        await log_event(
            chat.id,
            "bot_added",
            bot.id,
            event_data={"group": chat.title}
        )
```

#### 6. Track User Join/Leave
```python
@router.chat_member()
async def handle_chat_member(update: ChatMemberUpdated):
    """Track user join/leave"""
    chat = update.chat
    user = update.new_chat_member.user
    
    if update.new_chat_member.status in ["member", "restricted"]:
        # User joined
        logger.info(f"User {user.id} joined {chat.id}")
        
        await log_event(
            chat.id,
            "user_joined",
            user.id,
            event_data={
                "username": user.username,
                "first_name": user.first_name
            }
        )
    
    elif update.new_chat_member.status in ["left", "kicked"]:
        # User left
        logger.info(f"User {user.id} left {chat.id}")
        
        await log_event(
            chat.id,
            "user_left",
            user.id,
            event_data={"username": user.username}
        )
```

#### 7. Update Command Functions
Remove delays from all command handlers:

**Current Mute:**
```python
sent_msg = await message.answer(response, parse_mode=ParseMode.HTML, reply_markup=keyboard)
await asyncio.sleep(5)
await sent_msg.delete()
```

**New Mute:**
```python
# Keep message permanently
sent_msg = await message.answer(response, parse_mode=ParseMode.HTML, reply_markup=keyboard)

# Log the action
await log_event(
    message.chat.id,
    "mute",
    user_id,
    triggered_by=message.from_user.id,
    event_data={"duration": duration_text}
)
```

---

## Phase 3: API Integration (COMPLETED ✅)

### New API Endpoints Available:

#### Settings
- `GET /api/advanced/settings/{group_id}`
- `POST /api/advanced/settings/{group_id}/update`
- `POST /api/advanced/settings/{group_id}/toggle-feature`

#### Members
- `GET /api/advanced/members/{group_id}/{user_id}`
- `GET /api/advanced/members/{group_id}`
- `POST /api/advanced/members/{group_id}/{user_id}/update`

#### Admins
- `GET /api/advanced/admins/{group_id}/{user_id}`
- `GET /api/advanced/admins/{group_id}`
- `POST /api/advanced/admins/{group_id}/add`
- `POST /api/advanced/admins/{group_id}/{user_id}/remove`

#### Roles
- `GET /api/advanced/roles/{group_id}`
- `POST /api/advanced/roles/{group_id}/create`

#### History
- `POST /api/advanced/history/log-command`
- `GET /api/advanced/history/{group_id}`

#### Events
- `POST /api/advanced/events/log`
- `GET /api/advanced/events/{group_id}`

#### Statistics
- `GET /api/advanced/statistics/{group_id}`
- `POST /api/advanced/statistics/{group_id}/update`

---

## Phase 4: Implementation Steps

### Step 1: Update API App
Update `centralized_api/app.py` to include advanced routes:
```python
from .api.advanced_routes import router as advanced_router

app.include_router(advanced_router)
```

### Step 2: Update Bot Config
Update bot constants for advanced features:
```python
ADVANCED_MODE = True
KEEP_MESSAGES = True
AUTO_DELETE = False
LOG_EVERYTHING = True
```

### Step 3: Replace send_and_delete
Replace all `send_and_delete()` calls with `send_response()`

### Step 4: Add New Handlers
- `handle_my_chat_member` - Group join/leave
- `handle_chat_member` - User join/leave
- `cmd_settings` - Settings management
- Settings callback handlers

### Step 5: Update Existing Handlers
- Remove deletion logic
- Add logging
- Add database persistence

---

## Database Schema

### Collections Created:
1. **group_settings** - Settings per group
2. **members** - Member tracking
3. **admins** - Admin management
4. **moderation_roles** - Custom roles
5. **command_history** - Command logs
6. **event_logs** - Event tracking
7. **group_statistics** - Analytics

---

## Settings Available

### Feature Toggles:
- `welcome_message` - Send welcome when user joins
- `left_message` - Send message when user leaves
- `pin_message` - Pin important messages
- `moderation` - Enable/disable moderation
- `auto_mute` - Auto-mute after warnings
- `auto_ban` - Auto-ban after mutes
- `warnings` - Enable warnings system
- `role_assignment` - Enable role system
- `member_tracking` - Track member info
- `command_logging` - Log all commands
- `event_logging` - Log all events

### Customizable Options:
- Welcome message text
- Left message text
- Max warnings before mute
- Mute duration
- Admin notification chat
- Auto-delete toggle
- Message history retention

---

## Next Steps

1. ✅ Database models created
2. ✅ API endpoints created
3. ⏳ Update bot.py (in progress)
4. ⏳ Test all features
5. ⏳ Deploy and verify

---

**Estimated Time to Complete:** 2-3 hours

**Complexity:** Medium-High

**Skills Required:** Python, FastAPI, MongoDB, Telegram API

**Status:** PHASE 2 IN PROGRESS

