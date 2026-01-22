# ✅ `/id` COMMAND - User Information Display

**Status:** ✅ COMPLETE & DEPLOYED  
**Date Created:** January 17, 2026  
**Version:** 1.0

---

## 📋 Overview

The new `/id` command displays comprehensive user information including:
- **User ID** (clickable profile link)
- **Full Name** (First Name + Last Name)
- **Username** (@username)
- **Role in Group** (Member, Administrator, Owner)
- **Custom Title** (if set by admin)
- **Profile Picture** (sent as photo with caption)

---

## 🎯 Features

### 1. **Show Own User Info**
```
/id
```
Displays details about the user running the command.

### 2. **Show Other User's Info (by ID)**
```
/id 123456789
```
Displays details about user with ID `123456789`.

### 3. **Show Other User's Info (by Username)**
```
/id @username
```
Displays details about user `@username`.

### 4. **Show Replied User's Info**
Reply to any message and then use:
```
/id
```
Shows information about the user whose message you replied to.

---

## 📊 Output Format

### Text Information Display:
```
👥 USER INFORMATION

ID: 123456789
First Name: John
Last Name: Doe
Username: @johndoe
Role: ⭐ ADMINISTRATOR
Title: Chat Moderator
```

### Profile Picture:
- If user has a profile picture, it's sent as a **Telegram photo** with the info as caption
- Profile picture is the latest/primary profile photo from Telegram

### Admin/Owner Indicators:
- **👑 GROUP OWNER** - For group creators
- **⭐ ADMINISTRATOR** - For administrators with custom titles shown
- **👤 MEMBER** - For regular members

---

## 🔧 Implementation Details

### Bot Command Handler (`cmd_id` in `bot/main.py`)

```python
async def cmd_id(message: Message):
    """Show user details with profile picture"""
    # Supports 3 input methods:
    # 1. /id (shows self)
    # 2. /id @username or /id user_id (shows target user)
    # 3. Reply to message + /id (shows replied-to user)
    
    # Fetches from Telegram:
    # - User info via bot.get_chat(user_id)
    # - Member info via bot.get_chat_member(chat_id, user_id)
    # - Profile photos via bot.get_user_profile_photos(user_id)
    
    # Returns:
    # - Photo + Caption (if user has profile picture)
    # - Text message (if no profile picture)
    # - All info with clickable user link
```

### API v2 Endpoints (`/api_v2/routes/new_commands.py`)

Two REST endpoints for external access:

#### 1. POST `/users/info`
```json
Request:
{
    "group_id": 123456,
    "user_id": 123456789,
    "include_role": true,
    "include_profile": true
}

Response:
{
    "success": true,
    "data": {
        "user_id": 123456789,
        "group_id": 123456,
        "first_name": "John",
        "last_name": "Doe",
        "username": "johndoe",
        "role": "administrator",
        "custom_title": "Chat Moderator",
        "has_profile_photo": true,
        "is_bot": false,
        "fetched_at": "2026-01-17T22:16:00Z"
    }
}
```

#### 2. GET `/users/{user_id}/info`
```
GET /users/123456789/info?group_id=123456

Response:
{
    "success": true,
    "data": {
        "user_id": 123456789,
        ...
    }
}
```

---

## 📝 Registration

### 1. Command Handler Registration
File: `bot/main.py` (line ~6188)
```python
dispatcher.message.register(cmd_id, Command("id"))
```

### 2. Bot Command Menu Registration
File: `bot/main.py` (line ~6253)
```python
BotCommand(command="id", description="Show user details with profile & role")
```

### 3. API v2 Routes
File: `api_v2/routes/new_commands.py` (lines 597-668)
- Automatically registered in `api_v2/app.py`

---

## 🚀 Usage Examples

### Example 1: Check Own Profile
```
User: /id
Bot: 
[Profile Photo]
👥 USER INFORMATION

ID: 123456789
First Name: John
Last Name: Doe
Username: @johndoe
Role: 👤 MEMBER
```

### Example 2: Check Admin's Profile
```
User: /id 987654321
Bot:
[Admin's Profile Photo]
👥 USER INFORMATION

ID: 987654321
First Name: Admin
Username: @admin_user
Role: ⭐ ADMINISTRATOR
Title: Group Admin
```

### Example 3: Check Group Owner
```
User: /id @owner
Bot:
[Owner's Profile Photo]
👥 USER INFORMATION

ID: 111111111
First Name: Boss
Username: @owner
Role: 👑 GROUP OWNER
```

### Example 4: Reply to Message
```
User: [Reply to John's message]
User: /id
Bot:
[John's Profile Photo]
👥 USER INFORMATION

ID: 123456789
First Name: John
Last Name: Doe
Username: @johndoe
Role: 👤 MEMBER
```

---

## 🔐 Permissions

- **Public Command**: Any user can use `/id`
- **No Admin Required**: Works for regular members
- **Group & Private**: Works in both group chats and private chats with bot
- **Information Scope**: Shows public Telegram profile information

---

## 🎨 UI Features

### ✨ Visual Elements
- **👥** - User information icon
- **👤** - Regular member indicator
- **⭐** - Administrator indicator
- **👑** - Group owner/creator indicator
- **Profile Photo** - User's primary Telegram profile picture

### Interactive Elements
- **User ID is clickable**: `tg://user?id=123456789` (opens profile in Telegram)
- **Username**: Formatted as `@username` (can be clicked as username)
- **Formatted Text**: HTML formatting for bold headers and clear structure

---

## 📦 Dependencies

### Telegram API Methods Used
- `bot.get_chat(user_id)` - Get user/chat information
- `bot.get_chat_member(chat_id, user_id)` - Get member status and role
- `bot.get_user_profile_photos(user_id, limit=1)` - Get profile pictures
- `bot.send_photo()` - Send photo with caption

### Python Libraries
- `aiogram` - Telegram bot framework
- `asyncio` - Async operations
- `logging` - Error tracking

---

## ⚙️ Configuration

### Parameters
- **Input Methods**: ID, @username, or reply
- **Profile Photo Limit**: 1 (gets latest photo)
- **Parse Mode**: HTML (for formatting)
- **Reply Support**: Yes (replies to original message)

### Optional Parameters (API v2)
```python
include_role: bool = True      # Include role information
include_profile: bool = True   # Include profile photo info
```

---

## 🧪 Testing

### Quick Test Commands
```bash
# In Telegram with bot:

# Test 1: Own profile
/id

# Test 2: Specific user
/id @botusername

# Test 3: Reply test
[Reply to any message]
/id

# Test 4: API test
curl -X POST http://localhost:8002/api/v2/users/info \
  -H "Content-Type: application/json" \
  -d '{"group_id": 123, "user_id": 456, "include_role": true}'
```

---

## 📊 Response Status

| Scenario | Result |
|----------|--------|
| Valid user ID | ✅ Shows info + profile photo |
| Invalid ID | ❌ Error message "Invalid user ID" |
| User not found | ❌ Error message |
| No profile photo | ✅ Shows info as text message |
| Admin in group | ✅ Shows role + custom title |
| User not in group | ✅ Shows user info only |
| Bot in private chat | ✅ Shows info of target user |

---

## 📝 Changes Made

### Files Modified:
1. **`bot/main.py`**
   - Added `cmd_id()` function (120 lines, ~1620-1740)
   - Registered command at line 6188
   - Added to command menu at line 6253

2. **`api_v2/routes/new_commands.py`**
   - Added `UserIDRequest` model
   - Added POST `/users/info` endpoint
   - Added GET `/users/{user_id}/info` endpoint

### Total Implementation:
- **Bot Handler**: ~120 lines
- **API Endpoints**: ~80 lines
- **Code Quality**: Type hints, error handling, logging

---

## 🎯 Integration with Existing Features

### ✅ Compatible With:
- All admin commands (ban, mute, etc.)
- User verification system
- AFK status tracking
- Statistics collection
- Logging system

### 🔗 Uses Same Architecture:
- HTML ParseMode for formatting
- Clickable user links (`tg://user?id=...`)
- Async/await pattern
- Error handling via `send_and_delete()`
- Logging via `log_command_execution()`

---

## 🚀 Deployment Status

| Component | Status |
|-----------|--------|
| Bot Command | ✅ Deployed |
| API v2 Endpoints | ✅ Deployed |
| Command Registration | ✅ Complete |
| Command Menu | ✅ Updated |
| Documentation | ✅ Complete |
| Testing | ✅ Verified |

---

## 📞 Support

### Common Issues:

**Q: "Invalid user ID" error?**  
A: Use correct format: `/id 123456789` or `/id @username`

**Q: Profile picture not showing?**  
A: User may not have a profile photo set. Bot still shows user info as text.

**Q: Can't find user?**  
A: User must exist on Telegram. Check username or ID is correct.

**Q: How to show admin role?**  
A: Admin role is automatic - only shows if user is admin/owner in that group.

---

## 📚 Related Commands

- `/status` - Bot status
- `/stats` - User/group statistics
- `/verify` - Verify users
- `/afk` - Set AFK status
- `/admin commands` - All admin controls

---

**Last Updated:** January 17, 2026  
**Next Version:** v1.1 (Add user message count, join date)
