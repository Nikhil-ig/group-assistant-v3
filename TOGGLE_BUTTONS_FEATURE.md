# ✅ Toggle Button Feature (On/Off - Free/Lock)

## Overview

The new unified toggle button system allows admins to quickly toggle user permissions on/off with a single click. Each button shows the current state and the action it will perform.

---

## UI Display

### `/restrict` or `/lock` Command

Shows all permissions in a **Free state** (ready to lock):

```
⚙️ PERMISSION TOGGLES

User ID: 123456789
Group ID: 987654321

Current Status: 🔓 All Permissions Allowed

Click button to toggle permission (lock/free):
• 📝 Text - Toggle text messages
• 🎨 Stickers - Toggle stickers
• 🎬 GIFs - Toggle GIFs & animations
• 🎤 Voice - Toggle voice/audio
• 🔒 Lock All - Block all permissions
```

**Buttons Layout**:
```
[📝 Text: 🔓 Free]  [🎨 Stickers: 🔓 Free]
[🎬 GIFs: 🔓 Free]  [🎤 Voice: 🔓 Free]
[🔒 Lock All]       [❌ Cancel]
```

---

### `/unrestrict` or `/free` Command

Shows all permissions in a **Locked state** (ready to free):

```
⚙️ PERMISSION TOGGLES

User ID: 123456789
Group ID: 987654321

Current Status: 🔒 All Permissions Blocked

Click button to toggle permission (lock/free):
• 📝 Text - Toggle text messages
• 🎨 Stickers - Toggle stickers
• 🎬 GIFs - Toggle GIFs & animations
• 🎤 Voice - Toggle voice/audio
• 🔓 Free All - Allow all permissions
```

**Buttons Layout**:
```
[📝 Text: 🔒 Lock]      [🎨 Stickers: 🔒 Lock]
[🎬 GIFs: 🔒 Lock]      [🎤 Voice: 🔒 Lock]
[🔓 Free All]           [❌ Cancel]
```

---

## Usage

### Basic Usage

```
/restrict @username         # Show lock toggles for user
/lock @username             # Alias for restrict
/unrestrict @username       # Show free toggles for user
/free @username             # Alias for unrestrict
```

### Reply to Message

```
/restrict                   # Locks the sender of the message you replied to
/lock                       # Alias for restrict
/unrestrict                 # Frees the sender of the message you replied to
/free                       # Alias for unrestrict
```

---

## Toggle Callbacks

### Restrict/Lock Callbacks
- `toggle_text_lock_<user_id>_<group_id>` → Lock text messages
- `toggle_stickers_lock_<user_id>_<group_id>` → Lock stickers
- `toggle_gifs_lock_<user_id>_<group_id>` → Lock GIFs
- `toggle_voice_lock_<user_id>_<group_id>` → Lock voice messages
- `toggle_all_lock_<user_id>_<group_id>` → Lock all permissions
- `toggle_cancel_<user_id>_<group_id>` → Cancel and close menu

### Unrestrict/Free Callbacks
- `toggle_text_free_<user_id>_<group_id>` → Free text messages
- `toggle_stickers_free_<user_id>_<group_id>` → Free stickers
- `toggle_gifs_free_<user_id>_<group_id>` → Free GIFs
- `toggle_voice_free_<user_id>_<group_id>` → Free voice messages
- `toggle_all_free_<user_id>_<group_id>` → Free all permissions
- `toggle_cancel_<user_id>_<group_id>` → Cancel and close menu

---

## Permission Mapping

| Permission | Telegram Parameter | Blocks |
|-----------|-------------------|--------|
| **Text** | `can_send_messages` | Text messages |
| **Stickers** | `can_send_other_messages` | Stickers & animations |
| **GIFs** | `can_send_other_messages` | GIFs & animations |
| **Voice** | `can_send_audios` | Voice messages & audio |

---

## Flow

### When User Clicks a Permission Button

1. Button click sends callback with data format: `toggle_PERM_ACTION_user_id_group_id`
2. `handle_callback()` routes to `handle_toggle_permission_callback()`
3. Function verifies admin permissions
4. API is called with appropriate action (restrict/unrestrict)
5. Message is updated with success status
6. User sees toast notification (popup)

### Example: Click "📝 Text: 🔓 Free"

```
Callback Data: toggle_text_lock_123456789_987654321
↓
handle_toggle_permission_callback() called
↓
Parse: permission=text, action=lock, user_id=123456789, group_id=987654321
↓
Check admin: ✅ Yes, proceed
↓
API Call: POST /action/enforce
  - action_type: "restrict"
  - group_id: 987654321
  - user_id: 123456789
  - metadata: {"permission_type": "can_send_messages"}
↓
Response: ✅ Success
↓
Message Updates:
🔒 LOCKED TEXT

User ID: 123456789
Permission: Text
Status: ✅ SUCCESS
```

---

## Handler Functions

### `handle_toggle_permission_callback()`

Located in `bot/main.py` around line 2281

**Responsibilities**:
- Parse callback data (permission, action, user_id, group_id)
- Check admin permissions
- Execute restrict/unrestrict action via API
- Update message with result
- Handle "all" permissions specially (lock all / free all)
- Handle individual permissions with metadata

**Key Features**:
- Unified handler for both lock and free actions
- Supports single permission or "all" bulk actions
- Calls API for actual permission changes
- Updates message inline (no new message)

---

## Configuration

### Commands Registered

```python
dispatcher.message.register(cmd_restrict, Command("restrict"))
dispatcher.message.register(cmd_restrict, Command("lock"))       # Alias
dispatcher.message.register(cmd_unrestrict, Command("unrestrict"))
dispatcher.message.register(cmd_unrestrict, Command("free"))     # Alias
```

### Callbacks Registered

```python
dispatcher.callback_query.register(handle_callback)
```

All callbacks starting with `toggle_` are routed to `handle_toggle_permission_callback()`

---

## Success Indicators

✅ **When working correctly, you should see**:

1. Command triggers toggle menu
2. Buttons show current state (🔓 Free or 🔒 Lock)
3. Clicking button triggers API call
4. Message updates with success status
5. User gets toast notification (✅ or ❌)
6. Permission actually changes in group

---

## Testing Checklist

- [ ] `/restrict @testuser` → Shows Free toggles
- [ ] `/lock @testuser` → Shows Free toggles (alias works)
- [ ] `/unrestrict @testuser` → Shows Lock toggles
- [ ] `/free @testuser` → Shows Lock toggles (alias works)
- [ ] Click individual permission button → Toggles that permission
- [ ] Click "Lock All" → Blocks all permissions
- [ ] Click "Free All" → Allows all permissions
- [ ] Click "Cancel" → Closes menu without changes
- [ ] User receives toast notification for each action
- [ ] Message updates with success/failure status

---

## Files Modified

- ✅ `bot/main.py` - Line 1803: `cmd_restrict()` updated
- ✅ `bot/main.py` - Line 1862: `cmd_unrestrict()` updated
- ✅ `bot/main.py` - Line 2281: `handle_toggle_permission_callback()` added
- ✅ `bot/main.py` - Line 2527: Toggle callback routing added

---

## Status

✅ **IMPLEMENTED AND DEPLOYED**

Bot restarted with new toggle button system at 17:29:18

---

## Next Steps

1. **Test in Telegram**: Try `/restrict @user` or `/lock @user`
2. **Verify Buttons**: Confirm buttons show current state (Free/Lock)
3. **Click Buttons**: Test toggling individual permissions
4. **Confirm Changes**: Verify user permissions actually change in group
5. **Report Issues**: If anything doesn't work, check logs

---

**Date Implemented**: 16 January 2026
**Version**: v3.1
**Status**: ✅ Ready for testing
