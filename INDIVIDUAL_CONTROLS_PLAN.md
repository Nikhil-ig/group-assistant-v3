# 📋 Individual Permission Controls - Implementation Plan

## What You Want

1. ✅ **Individual button toggles** - Only lock what you click
2. ✅ **Remove GIFs button** - Show "Stickers & GIFs" (same permission)
3. ✅ **Use API v2 + DB** - Don't query Telegram each time
4. ✅ **Auto-delete restricted messages** - Delete messages from restricted users

---

## Implementation Strategy

### 1. Button Layout (Corrected)
```
📝 Text         🎨 Stickers & GIFs
🎤 Voice        🔒 Lock All
                ❌ Cancel
```

**NOT:**
```
❌ DON'T DO:
📝 Text         🎨 Stickers
🎬 GIFs         🎤 Voice  ← Wrong! They share same permission
```

### 2. Permission Mapping (Telegram API)
```
can_send_messages        → 📝 Text Messages (individual)
can_send_other_messages  → 🎨 Stickers & GIFs (TOGETHER)
can_send_audios          → 🎤 Voice Messages (individual)
```

**Why Stickers & GIFs together?**
- Telegram API field `can_send_other_messages` controls both
- Cannot be split - it's Telegram's limitation
- When you lock Stickers → GIFs also locked (API limitation)

### 3. Database Storage (via API v2)

**Store in DB:**
```json
{
  "group_id": 123456,
  "user_id": 789012,
  "permissions": {
    "can_send_messages": true,      ← Individual
    "can_send_other_messages": true, ← Individual  
    "can_send_audios": true         ← Individual
  },
  "restricted_at": "2026-01-16T10:30:00Z",
  "is_restricted": false
}
```

### 4. Auto-Delete Restricted Messages

**When user is restricted from TEXT:**
- User tries to send text message
- Bot detects: `can_send_messages=false`
- Bot deletes message immediately
- **But allows:** Stickers, GIFs, Voice messages

**When user is restricted from STICKERS & GIFS:**
- User tries to send sticker
- Bot detects: `can_send_other_messages=false`
- Bot deletes message immediately
- **But allows:** Text, Voice messages

---

## Code Changes Needed

### File 1: `bot/main.py`

#### Change 1: Remove GIFs Button
```python
# BEFORE (Wrong):
keyboard = [
    [Text, Stickers],
    [GIFs, Voice],     ← Remove this line
    [Lock All, Cancel]
]

# AFTER (Correct):
keyboard = [
    [Text, Stickers & GIFs],
    [Voice, Lock All],
    [Cancel]
]
```

#### Change 2: Update Permission Map
```python
perm_map = {
    "text": ("can_send_messages", "Text Messages"),
    "stickers": ("can_send_other_messages", "Stickers & GIFs"),  # Combined!
    "voice": ("can_send_audios", "Voice Messages"),
    # "gifs" removed - not separate
}
```

#### Change 3: Query DB Instead of Telegram
```python
# BEFORE:
perms = await get_user_permission_states(user_id, group_id)  # Queries Telegram

# AFTER:
# Call API v2 to get from DB
perms = await api_client.get_user_permissions(user_id, group_id)
```

#### Change 4: Add Message Auto-Delete
```python
async def handle_message(message: Message):
    """Check if user is restricted and delete message if needed"""
    
    # Get user's restrictions from DB
    restrictions = await api_client.get_user_restrictions(
        message.from_user.id,
        message.chat.id
    )
    
    if restrictions:
        # Determine if this message type is restricted
        if message.text and not restrictions.get("can_send_messages"):
            await message.delete()  # Delete restricted text message
            return
        
        if (message.sticker or message.animation) and not restrictions.get("can_send_other_messages"):
            await message.delete()  # Delete restricted sticker/GIF
            return
        
        if message.voice and not restrictions.get("can_send_audios"):
            await message.delete()  # Delete restricted voice message
            return
```

### File 2: `api_v2/routes/enforcement_endpoints.py`

#### Add Database Methods
```python
# Save permission state to DB when restricted
async def save_permission_state(group_id, user_id, permissions, is_restricted):
    """Save to database"""
    # Store in DB
    
# Retrieve permission state from DB
async def get_permission_state(group_id, user_id):
    """Retrieve from database"""
    # Get from DB
```

---

## API Endpoints Needed

### 1. Get User Permissions (from DB)
```
GET /api/v2/groups/{group_id}/users/{user_id}/permissions
Response:
{
  "can_send_messages": true,
  "can_send_other_messages": true,
  "can_send_audios": true,
  "is_restricted": false
}
```

### 2. Get User Restrictions (from DB)
```
GET /api/v2/groups/{group_id}/users/{user_id}/restrictions
Response:
{
  "is_restricted": true,
  "restrictions": {
    "can_send_messages": false,    ← Cannot send text
    "can_send_other_messages": true, ← Can send stickers
    "can_send_audios": true
  }
}
```

### 3. Update Permission State (to DB)
```
POST /api/v2/groups/{group_id}/users/{user_id}/permissions
Body:
{
  "permission_type": "can_send_messages",
  "allowed": false
}
```

---

## Flow Diagram

### Scenario 1: Lock Only Text Messages
```
User clicks: "📝 Text: Lock"
  ↓
Bot sends: {permission_type: "can_send_messages", value: false}
  ↓
API saves to DB: {can_send_messages: false, can_send_other_messages: true, can_send_audios: true}
  ↓
User sends TEXT → ❌ Deleted (restricted)
User sends STICKER → ✅ Allowed (not restricted)
User sends VOICE → ✅ Allowed (not restricted)
```

### Scenario 2: Lock Stickers & GIFs
```
User clicks: "🎨 Stickers & GIFs: Lock"
  ↓
Bot sends: {permission_type: "can_send_other_messages", value: false}
  ↓
API saves to DB: {can_send_messages: true, can_send_other_messages: false, can_send_audios: true}
  ↓
User sends TEXT → ✅ Allowed (not restricted)
User sends STICKER → ❌ Deleted (restricted)
User sends VOICE → ✅ Allowed (not restricted)
```

### Scenario 3: Lock All Permissions
```
User clicks: "🔒 Lock All"
  ↓
Bot sends: {lock_all: true}
  ↓
API saves to DB: {can_send_messages: false, can_send_other_messages: false, can_send_audios: false}
  ↓
User sends TEXT → ❌ Deleted
User sends STICKER → ❌ Deleted
User sends VOICE → ❌ Deleted
```

---

## Benefits

✅ **Individual Control**: Each button locks only its permission
✅ **No Telegram Queries**: Use database instead (faster)
✅ **Auto-Delete**: Messages deleted immediately based on restrictions
✅ **Accurate State**: DB always has current state
✅ **Scalable**: Works for thousands of users

---

## Status

🟠 **Ready to Implement**

The plan is clear. Need to:
1. Update button layout (remove GIFs)
2. Add DB query methods to API v2
3. Add message deletion logic to handle_message()
4. Store restriction states in database

Would you like me to start implementing?
