# ✅ Individual Permission State Tracking

## What Changed

Instead of all buttons showing the same state together, **each button now shows its INDIVIDUAL permission state**. 

### Before (All Same)
```
[📝 Text: 🔓 Free]    [🎨 Stickers: 🔓 Free]
[🎬 GIFs: 🔓 Free]    [🎤 Voice: 🔓 Free]
```
→ All buttons change together

### After (Individual States) ✅
```
[📝 Text: 🔓 Free]    [🎨 Stickers: 🔒 Lock]
[🎬 GIFs: 🔓 Free]    [🎤 Voice: 🔒 Lock]
```
→ Each button shows its OWN permission state

---

## How It Works

### 1. Get Permission States
When you open the toggle menu or click a button:
```
get_user_permission_states(user_id, group_id)
  ↓
Query Telegram API for user's chat member status
  ↓
Return: {
  "text": True/False,      # Can send messages?
  "stickers": True/False,  # Can send stickers?
  "gifs": True/False,      # Can send GIFs?
  "voice": True/False      # Can send voice?
}
```

### 2. Build Buttons with Actual States
For each permission, determine:
- **Current State**: Is it allowed or blocked?
- **Next Action**: What button action will user click?
- **Button Text**: Show current state with emoji

```python
# Example: Text is FREE, Stickers are LOCKED
for permission in ["text", "stickers", "gifs", "voice"]:
    is_allowed = perm_states[permission]
    
    # Button text shows CURRENT state
    button_text = f"📝 Text: {'🔓 Free' if is_allowed else '🔒 Lock'}"
    
    # Button callback shows NEXT action
    next_action = "lock" if is_allowed else "free"
    callback = f"toggle_text_{next_action}_{user_id}_{group_id}"
```

### 3. Rebuild After Each Toggle
After clicking any button:
1. Execute permission change (lock/free)
2. Query Telegram API for UPDATED states
3. Rebuild ALL buttons showing new individual states
4. Display message with status breakdown

---

## Example Workflow

### Scenario: User has mixed permissions

**Start State:**
```
[📝 Text: 🔓 Free]    [🎨 Stickers: 🔒 Lock]
[🎬 GIFs: 🔓 Free]    [🎤 Voice: 🔒 Lock]
```

**Click "📝 Text: 🔓 Free" to lock it:**
```
✅ 🔒 Locked Text (toast)

Query new states:
text=False, stickers=False, gifs=True, voice=False

Rebuild buttons:
[📝 Text: 🔒 Lock]    [🎨 Stickers: 🔒 Lock]
[🎬 GIFs: 🔓 Free]    [🎤 Voice: 🔒 Lock]
```

**Click "🎬 GIFs: 🔓 Free" to lock it:**
```
✅ 🔒 Locked GIFs (toast)

Query new states:
text=False, stickers=False, gifs=False, voice=False

Rebuild buttons:
[📝 Text: 🔒 Lock]    [🎨 Stickers: 🔒 Lock]
[🎬 GIFs: 🔒 Lock]    [🎤 Voice: 🔒 Lock]
```

---

## Message Display

After each action, you see individual permission breakdown:

```
⚙️ PERMISSION TOGGLES

User ID: 501166051
Group ID: 987654321

Individual Permission Status:
• 📝 Text: 🔒 Locked
• 🎨 Stickers: 🔓 Free
• 🎬 GIFs: 🔒 Locked
• 🎤 Voice: 🔓 Free

Click button to toggle that permission:
```

---

## Implementation Details

### New Helper Function
- **Location**: `bot/main.py` line 2281
- **Function**: `get_user_permission_states(user_id, group_id) -> dict`
- **Purpose**: Query Telegram API and return actual permission states

### Updated Handler
- **Location**: `bot/main.py` line 2309
- **Function**: `handle_toggle_permission_callback()`
- **Key Change**: Get actual states, build individual buttons

### Code Pattern
```python
# Get actual states from Telegram
perm_states = await get_user_permission_states(user_id, group_id)

# For each permission, button text shows CURRENT state
for perm in ["text", "stickers", "gifs", "voice"]:
    is_allowed = perm_states[perm]
    
    # Button shows current state + allows toggle to opposite
    button_text = f"Icon: {'🔓 Free' if is_allowed else '🔒 Lock'}"
    next_action = "lock" if is_allowed else "free"
    
    keyboard.add_button(button_text, f"toggle_{perm}_{next_action}_...")
```

---

## Features

✅ **Real-time State Display** - Shows actual Telegram API permissions
✅ **Independent Toggles** - Each permission tracked separately
✅ **Smart Buttons** - Button action matches what user needs
✅ **Clear Feedback** - Each button shows current state + emoji
✅ **Mixed States** - Text locked, Stickers free, etc.

---

## Test Cases

| Scenario | Expected Button | Clicking It | Result |
|----------|--------|----------|--------|
| All free | 📝 Free, 🎨 Free, 🎬 Free, 🎤 Free | Any button | That perm locks, others stay free |
| Mixed (Text locked, rest free) | 📝 Lock, 🎨 Free, 🎬 Free, 🎤 Free | Click 🎨 | Stickers lock, Text stays locked |
| All locked | 📝 Lock, 🎨 Lock, 🎬 Lock, 🎤 Lock | Any button | That perm frees, others stay locked |

---

## API Integration

Buttons use real Telegram data:

1. **When opening menu** → Query Telegram API
2. **After each toggle** → Execute action, query API again
3. **Display buttons** → Show actual current state from Telegram

No caching = Always accurate permissions!

---

## Files Modified

- ✅ `bot/main.py` - Line 2281: Added `get_user_permission_states()` helper
- ✅ `bot/main.py` - Line 2309: Updated `handle_toggle_permission_callback()` to query and display individual states

---

## Status

✅ **DEPLOYED** - Bot restarted at 17:50:59

Each button now shows its INDIVIDUAL state! Try toggling permissions and see buttons update independently. 🎯
