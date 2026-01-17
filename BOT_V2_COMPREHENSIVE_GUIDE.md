# 🤖 TELEGRAM BOT V2 - ADVANCED MODERN BOT

## 🎯 Overview

**Telegram Bot V2** is a next-generation, ultra-advanced bot featuring:

✅ **Smart Toggle System** - Mute↔Unmute, Ban↔Unban, Warn↔Unwarn, Lockdown↔Freedom
✅ **Advanced Admin Panel** - Easy one-click management via buttons
✅ **Professional Formatting** - Beautiful messages with user mentions
✅ **API V2 Integration** - Fully integrated with centralized API
✅ **Reply Context** - Admin replies go to original message, not admin
✅ **Ultra-Fast Performance** - Optimized with caching and connection pooling
✅ **Fully Robust** - Comprehensive error handling and logging
✅ **Clickable User Mentions** - Professional mention links instead of IDs

---

## 🚀 Features

### 1. **Smart Toggle Buttons**

Intelligently detect current state and offer opposite action:

| Current State | Button Shown |
|---------------|--------------|
| 🔇 Muted | Show: 🔊 Unmute |
| Unmuted | Show: 🔇 Mute |
| 🚫 Banned | Show: ✅ Unban |
| Not Banned | Show: 🚫 Ban |
| ⚠️ Warned | Show: 🆗 Clear Warn |
| No Warnings | Show: ⚠️ Warn |
| ⛔ Restricted | Show: ✅ Unrestrict |
| Not Restricted | Show: ⛔ Restrict |
| 🔒 Locked Down | Show: 🔓 Freedom |
| Normal | Show: 🔒 Lockdown |
| 🌙 Night Mode | Show: ☀️ Day Mode |
| Day Mode | Show: 🌙 Night Mode |

### 2. **Professional Admin Panel**

Beautiful formatted control panel showing:
- Target user with clickable mention
- User ID (for reference)
- Group ID
- Current state of each action
- Easy-to-use toggle buttons

```
╔════════════════════════════════════════╗
║    🎛️ ADVANCED ADMIN CONTROL PANEL
╚════════════════════════════════════════╝

📋 User: 👤 John Doe
🆔 ID: 123456789
📍 Group: 987654321

🟢 🔇 Mute: ❌ INACTIVE
🟢 🚫 Ban: ❌ INACTIVE
🔴 ⚠️ Warn: ✅ ACTIVE
🟢 ⛔ Restrict: ❌ INACTIVE
🟢 🔒 Lockdown: ❌ INACTIVE
🟢 🌙 Night Mode: ❌ INACTIVE

💡 Use the buttons below to toggle actions
```

### 3. **API V2 Integration**

All operations routed through API V2:
- User status checking
- Action execution
- State management
- Action logging
- Caching for performance

### 4. **User Mentions**

Professional clickable mentions instead of IDs:
- `👤 John Doe` (clickable link)
- Preserves user identity
- Mobile-friendly
- Professional appearance

### 5. **Reply Context Preservation**

When admin replies to a message:
```
Admin replies to: "Original message from user"
Bot will send response as:
"Reply to: Original message
[Admin action details]"
```

---

## 📋 Commands

### `/start`
Welcome message with bot introduction and features

### `/settings [@user | reply]`
Open advanced admin control panel

**Usage Examples:**
```
/settings @john_doe          # By username
/settings 123456789          # By user ID
[Reply to message] /settings # Reply mode
```

### `/help`
Show all available commands and features

### `/status`
Check bot status and API health

---

## 🎨 UI/UX Features

### Beautiful Message Formatting

```
╔═══════════════════════════════════╗
║     🔇 MUTE
╚═══════════════════════════════════╝

👤 User: 👤 John Doe
🛡️ Admin: 👤 Admin User
⏰ Time: 2026-01-17 14:30:45
📝 Details: Rule violation

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Icons & Emojis

| Icon | Meaning |
|------|---------|
| 🔇 | Mute |
| 🔊 | Unmute |
| 🚫 | Ban |
| ✅ | Unban/Success |
| ⚠️ | Warn |
| 🆗 | Clear Warning |
| ⛔ | Restrict |
| 🔒 | Lockdown |
| 🔓 | Freedom |
| 🌙 | Night Mode |
| ☀️ | Day Mode |
| 👤 | User |
| 🛡️ | Admin |
| 🎛️ | Control Panel |

---

## ⚡ Performance Optimizations

### 1. **Connection Pooling**
- Reuses HTTP connections
- Reduces latency
- Optimized for high volume

### 2. **Intelligent Caching**
```python
# User stats cached for 30 seconds
USER_STATS_CACHE = {}
# Reduces API calls
# Auto-expires old entries
```

### 3. **Callback Data Compression**
- Encodes callback data to fit Telegram's 64-byte limit
- Short IDs instead of long payloads
- Memory-efficient with automatic cleanup

### 4. **Async/Await Throughout**
- Non-blocking operations
- Can handle thousands of concurrent requests
- Ultra-responsive UI

---

## 🔒 Security & Robustness

### Admin Verification
- Checks admin status before every action
- Falls back to multiple verification methods
- Prevents unauthorized usage

### Error Handling
- Try-catch blocks on all API calls
- Graceful degradation
- Detailed error logging
- User-friendly error messages

### Action Logging
All actions logged via API:
```python
await api_client_v2.log_action(
    group_id=group_id,
    user_id=user_id,
    admin_id=admin_id,
    action=action,
    details="Toggle action via admin panel"
)
```

### Rate Limiting
- Built-in timeout protection (15 seconds)
- Prevents hang-ups
- Graceful error handling

---

## 🔧 Setup & Installation

### 1. **Dependencies**
```bash
pip install aiogram==3.24.0
pip install httpx==0.25.2
pip install python-dotenv==1.0.0
pip install pydantic==2.5.0
```

### 2. **Environment Variables**
```bash
# .env file
TELEGRAM_BOT_TOKEN=your_token_here
API_V2_URL=http://localhost:8002
API_V2_KEY=shared-api-key
LOG_LEVEL=INFO
```

### 3. **Run the Bot**
```bash
python bot/bot_v2.py
```

---

## 📊 Architecture

### Components

```
┌─────────────────────────────────────────────┐
│           TELEGRAM BOT V2                   │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────────────────────────────────┐   │
│  │   Command Handlers                   │   │
│  │  /start, /settings, /help, /status  │   │
│  └──────────────────────────────────────┘   │
│                                             │
│  ┌──────────────────────────────────────┐   │
│  │   Callback Handlers                  │   │
│  │  Button click handlers               │   │
│  │  Toggle logic                        │   │
│  └──────────────────────────────────────┘   │
│                                             │
│  ┌──────────────────────────────────────┐   │
│  │   Message Formatters                 │   │
│  │  Professional UI/UX                  │   │
│  │  Beautiful text styling              │   │
│  └──────────────────────────────────────┘   │
│                                             │
│  ┌──────────────────────────────────────┐   │
│  │   API V2 Client                      │   │
│  │  HTTP communication                  │   │
│  │  Action execution                    │   │
│  │  Logging                             │   │
│  └──────────────────────────────────────┘   │
│                                             │
│  ┌──────────────────────────────────────┐   │
│  │   Cache & State Management           │   │
│  │  User stats caching                  │   │
│  │  Callback data encoding              │   │
│  └──────────────────────────────────────┘   │
│                                             │
└─────────────────────────────────────────────┘
            ↓
     ┌──────────────┐
     │   API V2     │
     └──────────────┘
```

### Data Flow

```
User clicks button
    ↓
Telegram sends callback
    ↓
Bot verifies admin status
    ↓
Bot executes action via API V2
    ↓
API V2 processes and logs
    ↓
Bot updates UI
    ↓
User sees confirmation
```

---

## 🧪 Testing

### Test Admin Panel
```
1. Send /settings @testuser
2. Should show admin control panel
3. Click a toggle button
4. Should execute action
```

### Test Reply Mode
```
1. Reply to a user message
2. Send /settings
3. Should show admin panel for that user
```

### Test Direct User ID
```
1. Send /settings 123456789
2. Should show admin panel
```

---

## 📈 Scaling

Bot is optimized for scale:

✅ Async operations (handle 1000+ concurrent requests)
✅ Connection pooling (reuse connections)
✅ Smart caching (reduce API calls)
✅ Memory management (auto cleanup of old data)
✅ Error resilience (graceful degradation)

---

## 🔄 State Management

### Current States Tracked

```python
current_states = {
    "mute": bool,              # Is user muted?
    "ban": bool,               # Is user banned?
    "warn": bool,              # Does user have warnings?
    "restrict": bool,          # Is user restricted?
    "lockdown": bool,          # Is user locked down?
    "night_mode": bool         # Night mode enabled?
}
```

All states fetched from API V2 and kept in sync.

---

## 🎓 Best Practices

### 1. Always Check Admin Status
```python
is_admin = await check_is_admin(admin_id, chat_id, bot)
if not is_admin:
    return error
```

### 2. Use Professional Formatting
```python
mention_html = f'<a href="tg://user?id={user_id}">👤 {name}</a>'
```

### 3. Cache User Data
```python
cached = get_cached_user_stats(user_id, group_id)
if not cached:
    cached = await api_client_v2.get_user_status(...)
    cache_user_stats(user_id, group_id, cached)
```

### 4. Log All Actions
```python
await api_client_v2.log_action(
    group_id, user_id, admin_id,
    action, details
)
```

---

## 🐛 Troubleshooting

### Bot not responding
- Check `TELEGRAM_BOT_TOKEN` in `.env`
- Verify bot internet connection
- Check bot permissions in group

### API V2 errors
- Verify `API_V2_URL` is correct
- Check `API_V2_KEY` matches API
- Ensure API V2 is running

### Admin panel not showing
- Ensure user is admin in group
- Check API returns correct user status
- Verify callback data encoding

### Buttons not working
- Check callback_query handler is registered
- Verify admin status before action
- Check API V2 enforcement endpoints

---

## 📝 Logging

Detailed logging for debugging:

```
2026-01-17 14:30:45,123 - __main__ - INFO - 🚀 Bot V2 Starting...
2026-01-17 14:30:46,234 - __main__ - INFO - ✅ API V2 is healthy
2026-01-17 14:30:47,345 - __main__ - INFO - ✅ Bot commands set
2026-01-17 14:31:12,456 - __main__ - INFO - 🎯 Polling started...
```

---

## 🚀 Next Steps

1. **Start Bot V2**
   ```bash
   python bot/bot_v2.py
   ```

2. **Add to Group**
   - Get bot URL from @BotFather
   - Add to your group
   - Make bot admin

3. **Test Commands**
   - Send `/start`
   - Send `/settings @testuser`
   - Click toggle buttons

4. **Monitor Logs**
   - Watch for errors
   - Verify actions logged
   - Check API integration

---

## 📞 Support

For issues or questions:
1. Check logs for error messages
2. Verify API V2 connectivity
3. Ensure admin permissions
4. Review command syntax

---

**Version:** 2.0 (Next Generation)
**Last Updated:** 2026-01-17
**Status:** ✅ Production Ready
