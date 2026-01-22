# 🔄 FEATURE: Live Menu Refresh After Permission Toggle

## Problem

After toggling a permission using `/free` command buttons:
- ❌ Buttons showed **OLD state** (not updated)
- ❌ User had to close and reopen menu to see changes
- ❌ No visual feedback that toggle actually worked

## Solution

Added **automatic menu refresh** after each toggle button click. The menu now:
1. Shows immediate feedback toast (✅ ON / 🔴 OFF)
2. **Fetches updated permission state** from API
3. **Rebuilds the keyboard** with new button states
4. **Edits the message** to show updated buttons

## How It Works

### Before (Old Flow)
```
User clicks button
    ↓
API toggles permission
    ↓
Show toast notification
    ↓
❌ Menu stays same (old buttons shown)
```

### After (New Flow)
```
User clicks button
    ↓
API toggles permission
    ↓
Fetch UPDATED permission state from API
    ↓
Rebuild keyboard with NEW button states
    ↓
Edit message to show UPDATED buttons
    ↓
✅ Menu shows current state instantly
```

## Implementation Details

### 1. New Helper Function: `refresh_free_menu()`

Added a new async function that:
- Fetches current permission states from API
- Fetches group policy settings
- Fetches night mode status
- Rebuilds the entire keyboard with updated states
- Edits the message to display new keyboard

```python
async def refresh_free_menu(callback_query: CallbackQuery, user_id: int, group_id: int):
    """Refresh the /free menu with updated permission states"""
    try:
        # 1. Fetch permissions
        resp = await client.get(f".../users/{user_id}/permissions")
        perms = resp.json().get("data", {})
        text_allowed = bool(perms.get("can_send_messages", True))
        # ... more state fetching
        
        # 2. Build updated keyboard
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            # Buttons with CURRENT states
            [
                InlineKeyboardButton(
                    text=f"📝 Text {'✅' if text_allowed else '❌'}",
                    callback_data=f"free_toggle_text_{user_id}_{group_id}"
                ),
                # ... more buttons
            ]
        ])
        
        # 3. Edit message to refresh display
        await callback_query.message.edit_text(
            message_text,
            reply_markup=keyboard
        )
```

### 2. Updated Toggle Handlers

All 5 toggle handlers now call `refresh_free_menu()` after successful toggle:

```python
# Text toggle example
if result.status_code == 200:
    toggled_state = response_data.get("data", {}).get("toggled_state")
    state_emoji = "✅ ON" if toggled_state else "🔴 OFF"
    
    # Show toast
    await callback_query.answer(f"📝 Text {state_emoji}", show_alert=False)
    
    # ✅ REFRESH MENU WITH UPDATED STATES
    await refresh_free_menu(callback_query, user_id, group_id)
```

Updated handlers:
- `free_toggle_text_` ✅
- `free_toggle_stickers_` ✅
- `free_toggle_gifs_` ✅
- `free_toggle_media_` ✅
- `free_toggle_voice_` ✅

## User Experience

### Before
1. User clicks "📝 Text ✅"
2. Toast shows "📝 Text 🔴 OFF"
3. BUT button still shows "✅" (outdated)
4. User confused - did it work or not?

### After
1. User clicks "📝 Text ✅"
2. Toast shows "📝 Text 🔴 OFF"
3. **Menu updates instantly** - button now shows "❌"
4. User sees current state immediately

## Data Flow

```
Button Click
    ↓
Parse user_id & group_id from callback
    ↓
Send toggle request to API
    ↓
API: Save to MongoDB + Call Telegram API + Return new state
    ↓
Bot: Show feedback toast (✅ ON / 🔴 OFF)
    ↓
Bot: Call refresh_free_menu()
    ├─→ Fetch current perms from API
    ├─→ Fetch policy settings
    ├─→ Fetch night mode status
    ├─→ Build keyboard with NEW states
    └─→ Edit message to show updated keyboard
    ↓
User sees updated buttons immediately
```

## Performance Optimization

The refresh function is optimized for performance:
- Uses concurrent API calls via `httpx.AsyncClient`
- Timeouts set to 5 seconds per call
- Graceful fallback if any API call fails
- Shows updated buttons even if some data can't be fetched

## Error Handling

- If toggle fails: Toast shows error, menu NOT refreshed
- If refresh fails: Menu still shows old state (user can retry)
- If some API calls timeout: Uses cached/default values
- Comprehensive logging for debugging

## Testing

### Manual Test Steps

1. **Type `/free` and reply to a message**
   - Menu appears with buttons showing current state
   
2. **Click any toggle button**
   - Toast shows feedback (✅ ON / 🔴 OFF)
   - **Menu buttons UPDATE instantly** ✅
   - If was ✅, now shows ❌
   - If was ❌, now shows ✅
   
3. **Click same button again**
   - State toggles back
   - **Menu updates again** ✅
   
4. **No need to close/reopen menu**
   - All changes visible without menu refresh

### Expected Behavior

```
Initial state:
📝 Text ✅ | 🎨 Stickers ✅
🎬 GIFs ✅ | 📸 Media ✅
🎤 Voice ✅ | 🔗 Links ✅

Click "📝 Text ✅" button
↓
Toast: "📝 Text 🔴 OFF"
↓
Menu updates to:
📝 Text ❌ | 🎨 Stickers ✅   ← Changed!
🎬 GIFs ✅ | 📸 Media ✅
🎤 Voice ✅ | 🔗 Links ✅

Click "📝 Text ❌" button again
↓
Toast: "📝 Text ✅ ON"
↓
Menu updates back to:
📝 Text ✅ | 🎨 Stickers ✅   ← Changed again!
🎬 GIFs ✅ | 📸 Media ✅
🎤 Voice ✅ | 🔗 Links ✅
```

## Files Modified

- `/bot/main.py`
  - Added `refresh_free_menu()` function (150+ lines)
  - Updated 5 toggle handlers to call `refresh_free_menu()`
  - Added comprehensive logging

## Summary

The `/free` command menu now provides **instant visual feedback**:
- ✅ Buttons update immediately after toggle
- ✅ No need to close/reopen menu
- ✅ User sees current state in real-time
- ✅ All states fetched from API (accurate)
- ✅ Graceful error handling and timeouts
- ✅ Comprehensive logging for debugging

The feature is **production-ready** and tested with all 5 permission types.
