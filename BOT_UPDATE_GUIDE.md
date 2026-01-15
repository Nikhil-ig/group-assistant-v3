# 🤖 Bot Update - Remove Auto-Delete & Add Advanced Features

## Summary of Changes

Your bot will be updated to:
1. ✅ **NOT auto-delete messages** - Keep everything
2. ✅ **Add /settings command** - Configure bot features
3. ✅ **Save to database** - All data persisted
4. ✅ **Track members** - User join/leave events
5. ✅ **Track admins** - Admin management
6. ✅ **Track roles** - Moderation roles
7. ✅ **Log everything** - Commands, events, actions
8. ✅ **Provide statistics** - Analytics & reports

---

## Key Changes in bot/main.py

### Change 1: Remove Auto-Delete Function

**OLD:**
```python
async def send_and_delete(message: Message, text: str, delay: int = 5, **kwargs):
    msg = await message.answer(text, **kwargs)
    await asyncio.sleep(delay)
    await msg.delete()
```

**NEW:**
```python
async def send_response(message: Message, text: str, **kwargs):
    """Send response without auto-deleting"""
    return await message.answer(text, **kwargs)


# OLD send_and_delete for compatibility (backward compatible)
async def send_and_delete(message: Message, text: str, delay: int = 0, **kwargs):
    """Legacy function - now just sends message"""
    return await message.answer(text, **kwargs)
```

---

### Change 2: Update All send_and_delete Calls

**Example 1 - Mute Response**

OLD:
```python
response = f"🔇 User {user_id} has been muted {duration_text}"
await send_and_delete(message, response, parse_mode=ParseMode.HTML)
```

NEW:
```python
response = (
    f"╔═══════════════════════════════════╗\n"
    f"║ 🔇 ACTION EXECUTED                ║\n"
    f"╚═══════════════════════════════════╝\n\n"
    f"<b>📌 User ID:</b> <code>{user_id}</code>\n"
    f"<b>⏱️  Duration:</b> <i>{duration_text}</i>\n"
    f"<b>📍 Result:</b> <i>User muted</i>\n\n"
    f"🚀 <b>Next Actions Available Below ↓</b>"
)

keyboard = build_action_keyboard("mute", user_id, message.chat.id)

# Send WITHOUT deleting
sent_msg = await send_response(
    message,
    response,
    parse_mode=ParseMode.HTML,
    reply_markup=keyboard
)

# Log the action
await log_action(
    message.chat.id,
    "mute",
    message.from_user.id,
    target_user_id=user_id,
    data={"duration": duration_text}
)
```

---

### Change 3: Add Logging Functions

```python
async def log_action(
    group_id: int,
    action_type: str,
    triggered_by: int,
    target_user_id: Optional[int] = None,
    data: Optional[dict] = None
):
    """Log action to database"""
    try:
        await api_client.execute_action({
            "action_type": "log_event",
            "group_id": group_id,
            "event_type": action_type,
            "user_id": triggered_by,
            "target_user_id": target_user_id,
            "event_data": data or {}
        })
    except Exception as e:
        logger.error(f"Failed to log action: {e}")


async def log_command_execution(
    group_id: int,
    user_id: int,
    command: str,
    args: Optional[str] = None,
    status: str = "success"
):
    """Log command execution"""
    try:
        await api_client.execute_action({
            "action_type": "log_command",
            "group_id": group_id,
            "user_id": user_id,
            "command": command,
            "args": args,
            "status": status
        })
    except Exception as e:
        logger.error(f"Failed to log command: {e}")
```

---

### Change 4: Add Event Handlers

```python
# Track bot join/leave
@router.my_chat_member()
async def handle_my_chat_member(update: ChatMemberUpdated):
    """Handle bot join/leave from group"""
    chat = update.chat
    
    if update.new_chat_member.status == "member":
        logger.info(f"✅ Bot added to group {chat.id} ({chat.title})")
        
        # Create default settings
        await api_client.execute_action({
            "action_type": "create_settings",
            "group_id": chat.id,
            "group_name": chat.title or "Group"
        })
        
        # Log event
        await log_action(
            chat.id,
            "bot_joined",
            bot.id,
            data={"group_name": chat.title}
        )
        
        # Send welcome message to admins
        msg = f"🤖 Bot added to group: {chat.title}"
        logger.info(msg)


# Track user join/leave
@router.chat_member()
async def handle_chat_member(update: ChatMemberUpdated):
    """Track user join/leave"""
    chat = update.chat
    user = update.new_chat_member.user
    old_status = update.old_chat_member.status
    new_status = update.new_chat_member.status
    
    if new_status in ["member", "restricted", "creator", "administrator"]:
        # User joined (or permission changed)
        if old_status in ["left", "kicked"]:
            logger.info(f"👤 User {user.id} joined {chat.id}")
            
            # Log join event
            await log_action(
                chat.id,
                "user_joined",
                user.id,
                data={
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name
                }
            )
            
            # Get settings
            settings = await api_client.execute_action({
                "action_type": "get_settings",
                "group_id": chat.id
            })
            
            # Send welcome if enabled
            if settings.get("features_enabled", {}).get("welcome_message", True):
                welcome_text = settings.get("welcome_message", "Welcome!")
                welcome_text = welcome_text.format(group_name=chat.title)
                try:
                    await bot.send_message(chat.id, welcome_text)
                except Exception as e:
                    logger.error(f"Failed to send welcome: {e}")
    
    elif new_status in ["left", "kicked"]:
        # User left or kicked
        if old_status != "left" and old_status != "kicked":
            logger.info(f"👋 User {user.id} left {chat.id}")
            
            # Log leave event
            await log_action(
                chat.id,
                "user_left",
                user.id,
                data={
                    "username": user.username,
                    "reason": "kicked" if new_status == "kicked" else "left"
                }
            )
            
            # Get settings
            settings = await api_client.execute_action({
                "action_type": "get_settings",
                "group_id": chat.id
            })
            
            # Send goodbye if enabled
            if settings.get("features_enabled", {}).get("left_message", True):
                left_text = settings.get("left_message", "{username} left.")
                left_text = left_text.format(
                    username=user.first_name or user.username or "Someone"
                )
                try:
                    await bot.send_message(chat.id, left_text)
                except Exception as e:
                    logger.error(f"Failed to send left message: {e}")
```

---

### Change 5: Add Settings Command

```python
@router.message(Command("settings"))
async def cmd_settings(message: Message):
    """Open settings menu - Configure bot features"""
    try:
        # Check if admin
        member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        if not member.status in ["creator", "administrator"]:
            await send_response(
                message,
                "⛔ Only admins can access settings!",
                parse_mode=ParseMode.HTML
            )
            return
        
        # Create settings menu
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Features", callback_data="set_features")],
            [InlineKeyboardButton(text="👤 Members", callback_data="set_members")],
            [InlineKeyboardButton(text="⚖️ Moderation", callback_data="set_moderation")],
            [InlineKeyboardButton(text="📊 Statistics", callback_data="set_statistics")],
            [InlineKeyboardButton(text="🔐 Roles", callback_data="set_roles")],
            [InlineKeyboardButton(text="ℹ️ Info", callback_data="set_info")],
            [InlineKeyboardButton(text="🏠 Home", callback_data="start")],
        ])
        
        response = """
╔═════════════════════════════════╗
║ ⚙️  BOT SETTINGS                ║
╚═════════════════════════════════╝

Configure your bot:

📋 <b>Features</b> - Enable/disable bot features
👤 <b>Members</b> - View member tracking
⚖️ <b>Moderation</b> - Configure moderation
📊 <b>Statistics</b> - View group statistics
🔐 <b>Roles</b> - Manage roles and permissions
ℹ️ <b>Info</b> - View current configuration

Choose an option:
"""
        
        sent_msg = await send_response(
            message,
            response,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )
        
        # Log
        await log_command_execution(message.chat.id, message.from_user.id, "settings")
        
    except Exception as e:
        logger.error(f"Settings command failed: {e}")
        await send_response(message, f"❌ Error: {e}", parse_mode=ParseMode.HTML)
```

---

### Change 6: Add Settings Callback Handlers

```python
@router.callback_query(F.data.startswith("set_"))
async def handle_settings_callback(callback_query: CallbackQuery):
    """Handle settings menu callbacks"""
    try:
        data = callback_query.data
        group_id = callback_query.message.chat.id
        
        if data == "set_features":
            # Show features toggle
            response = """
╔═════════════════════════════════╗
║ 📋 FEATURES CONFIGURATION       ║
╚═════════════════════════════════╝

Toggle features on/off:

✅ Welcome Messages - Send when user joins
✅ Leave Messages - Send when user leaves  
✅ Member Tracking - Track member info
✅ Moderation - Enable/disable moderation
✅ Roles - Enable/disable role system
✅ Logging - Log all events

Use buttons below to toggle:
"""
            
            # Get current settings
            settings = await api_client.execute_action({
                "action_type": "get_settings",
                "group_id": group_id
            })
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=f"{'✅' if settings.get('features_enabled', {}).get('welcome_message', True) else '❌'} Welcome",
                    callback_data="toggle_welcome"
                )],
                [InlineKeyboardButton(
                    text=f"{'✅' if settings.get('features_enabled', {}).get('left_message', True) else '❌'} Leave",
                    callback_data="toggle_leave"
                )],
                [InlineKeyboardButton(
                    text=f"{'✅' if settings.get('features_enabled', {}).get('member_tracking', True) else '❌'} Members",
                    callback_data="toggle_members"
                )],
                [InlineKeyboardButton(
                    text=f"{'✅' if settings.get('features_enabled', {}).get('moderation', True) else '❌'} Moderation",
                    callback_data="toggle_moderation"
                )],
                [InlineKeyboardButton(
                    text=f"{'✅' if settings.get('features_enabled', {}).get('role_assignment', True) else '❌'} Roles",
                    callback_data="toggle_roles"
                )],
                [InlineKeyboardButton(
                    text=f"{'✅' if settings.get('features_enabled', {}).get('event_logging', True) else '❌'} Logging",
                    callback_data="toggle_logging"
                )],
                [InlineKeyboardButton(text="🔙 Back", callback_data="set_main")],
            ])
            
            await callback_query.message.edit_text(
                response,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
            
        elif data == "set_members":
            # Show members info
            # Similar structure...
            pass
            
        elif data == "set_moderation":
            # Show moderation settings
            pass
            
        elif data == "set_statistics":
            # Show group statistics
            pass
            
        elif data == "set_roles":
            # Show roles configuration
            pass
            
        elif data == "set_info":
            # Show current configuration info
            settings = await api_client.execute_action({
                "action_type": "get_settings",
                "group_id": group_id
            })
            
            features = settings.get("features_enabled", {})
            response = f"""
╔═════════════════════════════════╗
║ ℹ️  CURRENT CONFIGURATION        ║
╚═════════════════════════════════╝

<b>Features Enabled:</b>
✅ Welcome: {'Yes' if features.get('welcome_message') else 'No'}
✅ Leave Msg: {'Yes' if features.get('left_message') else 'No'}
✅ Members: {'Yes' if features.get('member_tracking') else 'No'}
✅ Moderation: {'Yes' if features.get('moderation') else 'No'}
✅ Logging: {'Yes' if features.get('event_logging') else 'No'}

<b>Settings:</b>
🔹 Max Warnings: {settings.get('max_warnings', 3)}
🔹 Mute Duration: {settings.get('mute_duration', 60)} min
🔹 Keep History: {'Yes' if settings.get('keep_message_history') else 'No'}
"""
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Back", callback_data="set_main")],
            ])
            
            await callback_query.message.edit_text(
                response,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
        
        await callback_query.answer()
        
    except Exception as e:
        logger.error(f"Settings callback failed: {e}")
        await callback_query.answer(f"❌ Error: {e}", show_alert=True)
```

---

## Implementation Checklist

- [ ] Remove `send_and_delete` auto-delete logic
- [ ] Create `send_response` function
- [ ] Add `log_action` function
- [ ] Add `log_command_execution` function
- [ ] Add `handle_my_chat_member` handler
- [ ] Add `handle_chat_member` handler
- [ ] Add `cmd_settings` command
- [ ] Add settings callback handlers
- [ ] Update all command responses to not delete
- [ ] Update all command responses to log actions
- [ ] Test all features
- [ ] Deploy and verify

---

## Testing Plan

### Test 1: Message Persistence
- Send `/mute` command
- ✅ Verify message stays (not deleted)
- ✅ Verify buttons work
- ✅ Verify action logged in database

### Test 2: Member Tracking
- Add user to group
- ✅ Verify "user_joined" event logged
- ✅ Verify welcome message sent (if enabled)
- ✅ Verify member record created

### Test 3: Settings Command
- Send `/settings`
- ✅ Verify settings menu appears
- ✅ Verify admin-only check works
- ✅ Verify all buttons respond

### Test 4: Feature Toggle
- Click toggle button
- ✅ Verify setting updated in database
- ✅ Verify next action uses new setting
- ✅ Verify persists across restarts

### Test 5: Logging
- Execute any action
- ✅ Verify event logged to database
- ✅ Verify can retrieve history via API
- ✅ Verify statistics updated

---

**Status:** Ready for implementation  
**Effort:** 6-8 hours  
**Complexity:** Medium

