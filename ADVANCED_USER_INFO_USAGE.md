# 🎯 ADVANCED USER INFO - IMPLEMENTATION & USAGE GUIDE

## Quick Start

The bot now features an advanced user information system with role indicators, badges, and comprehensive profile data. This guide shows how to use it.

---

## 📌 Core Functions

### 1. Enhanced User Mention

**Function:** `get_user_mention(user_id, group_id)`

**Purpose:** Get a formatted mention link with role emoji

**Returns:** HTML string with role emoji and name

**Example:**
```python
user_mention = await get_user_mention(501166051, -1001234567890)
# Output: "👑 <a href='tg://user?id=501166051'>John Doe</a>"
```

**Usage in Messages:**
```python
await message.answer(f"Action performed by: {user_mention}")
```

**Role Emojis Returned:**
- `👑` = Owner
- `⭐` = Administrator  
- `👤` = Member
- `🔒` = Restricted
- `↪️` = Left
- `❌` = Kicked

---

### 2. Advanced User Information

**Function:** `get_advanced_user_info(user_id, group_id)`

**Purpose:** Fetch comprehensive user profile data

**Returns:** Dictionary with all user details

**Example:**
```python
user_info = await get_advanced_user_info(501166051, -1001234567890)

# Access individual fields
print(user_info['full_name'])        # "John Doe"
print(user_info['role_emoji'])       # "👑"
print(user_info['is_premium'])       # True/False
print(user_info['mention_html'])     # "👑 <a href='...'>John Doe</a>"
print(user_info['custom_title'])     # "Founder" or None
print(user_info['role_text'])        # "👑 Owner"
```

**Dictionary Keys:**
```python
{
    'user_id': 501166051,                    # Telegram user ID
    'first_name': 'John',                    # First name
    'last_name': 'Doe',                      # Last name (or None)
    'username': 'johndoe',                   # Username (or None)
    'is_bot': False,                         # Is bot account
    'role': 'creator',                       # Role in group
    'role_text': '👑 Owner',                 # Formatted role
    'role_emoji': '👑',                      # Role emoji only
    'custom_title': 'Founder',               # Custom title (or None)
    'has_profile_photo': True,               # Has profile picture
    'profile_photo_id': 'AgAD...',          # Photo file ID (or None)
    'is_premium': True,                      # Telegram Premium
    'permissions': {                         # Permission flags
        'can_send_messages': True,
        'can_post_messages': True,
        'can_delete_messages': True,
        'can_restrict_members': True,
        'can_promote_members': True,
        'can_edit_messages': True,
    },
    'mention_html': "👑 <a href='...'>John Doe</a>",  # HTML mention
    'full_name': 'John Doe',                 # First + Last name
    'display_name': '@johndoe',              # Username or name
}
```

---

## 💻 Code Examples

### Example 1: Simple User Display

```python
async def cmd_whoami(message: Message):
    """Show current user's information"""
    try:
        user_id = message.from_user.id
        group_id = message.chat.id
        
        # Get enhanced mention
        user_mention = await get_user_mention(user_id, group_id)
        
        # Send message
        await message.answer(f"You are: {user_mention}")
        
    except Exception as e:
        await send_and_delete(message, f"❌ Error: {e}")
```

---

### Example 2: Detailed User Profile

```python
async def cmd_userinfo(message: Message):
    """Show detailed user profile"""
    try:
        # Get target user (reply or argument)
        if message.reply_to_message:
            target_id = message.reply_to_message.from_user.id
        else:
            args = message.text.split()
            if len(args) < 2:
                await send_and_delete(message, "❌ Reply or provide user ID")
                return
            target_id = int(args[1])
        
        # Get advanced user info
        user_info = await get_advanced_user_info(target_id, message.chat.id)
        
        # Build detailed message
        info_text = f"""
<b>👤 USER PROFILE</b>

<b>IDENTITY:</b>
{user_info['mention_html']}
<b>Full Name:</b> {user_info['full_name']}
<b>User ID:</b> <code>{user_info['user_id']}</code>

<b>ROLE & STATUS:</b>
<b>Role:</b> {user_info['role_text']}
<b>Premium:</b> {'💎 YES' if user_info['is_premium'] else 'NO'}
<b>Bot:</b> {'🤖 YES' if user_info['is_bot'] else 'NO'}

<b>CONTACT:</b>
<b>Username:</b> @{user_info['username'] or 'N/A'}
        """
        
        if user_info['custom_title']:
            info_text += f"\n<b>Custom Title:</b> {user_info['custom_title']}"
        
        await send_message_with_reply(message, info_text, parse_mode=ParseMode.HTML)
        
    except Exception as e:
        await send_and_delete(message, f"❌ Error: {e}")
```

---

### Example 3: Permission Manager with User Context

```python
async def refresh_permissions_menu(callback_query: CallbackQuery, user_id: int, group_id: int):
    """Refresh permission menu with detailed user context"""
    try:
        # Get comprehensive user info
        user_info = await get_advanced_user_info(user_id, group_id)
        
        # Build header with full context
        premium_badge = " 💎 PREMIUM" if user_info['is_premium'] else ""
        bot_badge = " 🤖 BOT" if user_info['is_bot'] else ""
        
        header = f"""
<b>⚙️ PERMISSION MANAGER</b>
───────────────────────────────────────────────

<b>👤 USER:</b> {user_info['mention_html']}{premium_badge}{bot_badge}
<b>Role:</b> {user_info['role_text']}
<b>ID:</b> <code>{user_id}</code>
<b>Name:</b> {user_info['full_name']}
        """
        
        if user_info['username']:
            header += f"\n<b>Username:</b> @{user_info['username']}"
        
        if user_info['custom_title']:
            header += f"\n<b>Title:</b> <i>{user_info['custom_title']}</i>"
        
        # Build permission toggles
        buttons = [
            [InlineKeyboardButton(text=f"📝 Text", callback_data=f"toggle_text_{user_id}_{group_id}")],
            [InlineKeyboardButton(text=f"🎨 Stickers", callback_data=f"toggle_stickers_{user_id}_{group_id}")],
            [InlineKeyboardButton(text="❌ Close", callback_data=f"close_{user_id}_{group_id}")],
        ]
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        
        # Update message
        await callback_query.message.edit_text(header, parse_mode=ParseMode.HTML, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        await callback_query.answer("❌ Failed to refresh", show_alert=True)
```

---

### Example 4: Admin Action with User Context

```python
async def cmd_ban(message: Message):
    """Ban user with detailed context"""
    try:
        # Permission check
        if not await check_is_admin(message.from_user.id, message.chat.id):
            return
        
        # Get target user
        if not message.reply_to_message:
            await send_and_delete(message, "❌ Reply to user to ban")
            return
        
        target_id = message.reply_to_message.from_user.id
        
        # Get user info for context
        user_info = await get_advanced_user_info(target_id, message.chat.id)
        admin_mention = await get_user_mention(message.from_user.id, message.chat.id)
        
        # Check if already banned
        if user_info['role'] == 'kicked':
            await send_message_with_reply(
                message,
                f"⚠️ {user_info['mention_html']} is already banned!",
                parse_mode=ParseMode.HTML
            )
            return
        
        # Perform ban
        try:
            await message.chat.ban_member(target_id)
            
            # Notify with context
            response = f"""
✅ <b>BAN SUCCESSFUL</b>

<b>Banned User:</b> {user_info['mention_html']}
<b>ID:</b> <code>{target_id}</code>
<b>Role:</b> {user_info['role_text']}

<b>Admin:</b> {admin_mention}
<b>Action:</b> Ban
<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            await send_message_with_reply(message, response, parse_mode=ParseMode.HTML)
            
        except Exception as ban_error:
            await send_and_delete(message, f"❌ Ban failed: {ban_error}")
        
    except Exception as e:
        await send_and_delete(message, f"❌ Error: {e}")
```

---

### Example 5: Conditional Logic Based on User Type

```python
async def cmd_advanced_action(message: Message):
    """Perform different actions based on user role"""
    try:
        if not message.reply_to_message:
            await send_and_delete(message, "❌ Reply to a user")
            return
        
        user_id = message.reply_to_message.from_user.id
        group_id = message.chat.id
        
        # Get comprehensive user info
        user_info = await get_advanced_user_info(user_id, group_id)
        
        # Different logic based on role
        if user_info['role'] == 'creator':
            response = f"🛡️ Cannot perform action on {user_info['mention_html']} - Group owner!"
        
        elif user_info['role'] == 'administrator':
            response = f"⚠️ Action limited for {user_info['mention_html']} - Admin detected"
        
        elif user_info['is_bot']:
            response = f"🤖 Special handling for bot: {user_info['mention_html']}"
        
        elif user_info['is_premium']:
            response = f"💎 Premium user detected: {user_info['mention_html']}"
        
        elif user_info['role'] == 'restricted':
            response = f"🔒 Already restricted: {user_info['mention_html']}"
        
        else:
            response = f"✅ Regular member: {user_info['mention_html']}"
        
        await send_message_with_reply(message, response, parse_mode=ParseMode.HTML)
        
    except Exception as e:
        await send_and_delete(message, f"❌ Error: {e}")
```

---

## 🎨 Building Rich UI with User Info

### Pattern 1: User Card

```python
async def show_user_card(message: Message, user_id: int):
    """Display a beautiful user card"""
    try:
        user_info = await get_advanced_user_info(user_id, message.chat.id)
        
        card = f"""
╔═══════════════════════════════════╗
║        👤 USER PROFILE            ║
╠═══════════════════════════════════╣
║ {user_info['mention_html']}
║
║ Role: {user_info['role_text']}
║ ID: {user_info['user_id']}
║ Premium: {'💎' if user_info['is_premium'] else '❌'}
║ Bot: {'🤖' if user_info['is_bot'] else '❌'}
║
╚═══════════════════════════════════╝
        """
        
        await send_message_with_reply(message, card, parse_mode=ParseMode.HTML)
        
    except Exception as e:
        logger.error(f"Error: {e}")
```

---

### Pattern 2: User List with Status

```python
async def show_admin_list(message: Message, group_id: int):
    """Show all admins with detailed info"""
    try:
        chat = await bot.get_chat(group_id)
        admins = await chat.get_administrators()
        
        admin_list = "<b>👨‍💼 ADMINISTRATOR LIST</b>\n\n"
        
        for admin in admins:
            user_info = await get_advanced_user_info(admin.user.id, group_id)
            
            admin_list += f"• {user_info['mention_html']}"
            if user_info['custom_title']:
                admin_list += f" - <i>{user_info['custom_title']}</i>"
            admin_list += "\n"
        
        await message.answer(admin_list, parse_mode=ParseMode.HTML)
        
    except Exception as e:
        await send_and_delete(message, f"❌ Error: {e}")
```

---

## 🔧 Error Handling

### Safe Usage Pattern

```python
try:
    user_info = await get_advanced_user_info(user_id, group_id)
    
    # All fields are guaranteed to exist (with fallbacks)
    if user_info['role'] == 'creator':
        # Safe to use any field
        print(user_info['mention_html'])
        print(user_info['role_text'])
        print(user_info['full_name'])
    
except Exception as e:
    logger.error(f"Failed to get user info: {e}")
    # Fallback to basic ID only
    await message.answer(f"User: <code>{user_id}</code>")
```

---

## 📊 Quick Reference

### When to Use What?

| Task | Function | Returns |
|------|----------|---------|
| Quick mention in message | `get_user_mention()` | HTML string |
| Display user profile | `get_advanced_user_info()` | Full dict |
| Check if premium | `get_advanced_user_info()['is_premium']` | Boolean |
| Check if bot | `get_advanced_user_info()['is_bot']` | Boolean |
| Get role emoji | `get_advanced_user_info()['role_emoji']` | String |
| Check permissions | `get_advanced_user_info()['permissions']` | Dict |

---

### Emoji Quick Reference

```
👑  Owner                  💎  Premium User
⭐  Administrator          🤖  Bot Account
👤  Member                ❌  Kicked
🔒  Restricted            ↪️   Left
✅  Permission allowed     ❌  Permission denied
```

---

## 🚀 Performance Tips

1. **Cache user info when possible:** If you need the same user info multiple times, store it
   ```python
   user_info = await get_advanced_user_info(user_id, group_id)
   # Use user_info multiple times in same function
   ```

2. **Batch operations:** For multiple users, consider fetching in sequence
   ```python
   user_infos = []
   for uid in user_ids:
       info = await get_advanced_user_info(uid, group_id)
       user_infos.append(info)
   ```

3. **Graceful degradation:** Handle failures gracefully
   ```python
   try:
       user_info = await get_advanced_user_info(user_id, group_id)
   except:
       # Fall back to simple ID display
       display = f"<code>{user_id}</code>"
   ```

---

## 🎯 Common Patterns

### Pattern: Admin-Only Display
```python
user_info = await get_advanced_user_info(user_id, group_id)

# Only show full details to admins
if await check_is_admin(requester_id, group_id):
    detailed = True  # Show all info
else:
    detailed = False  # Show limited info
```

### Pattern: Role-Based Restrictions
```python
user_info = await get_advanced_user_info(user_id, group_id)

if user_info['role'] == 'creator':
    await message.answer("Cannot act on group owner")
elif user_info['role'] == 'administrator':
    await message.answer("Limited actions available for admin")
else:
    await message.answer("Full action available")
```

### Pattern: Premium Feature
```python
user_info = await get_advanced_user_info(user_id, group_id)

if user_info['is_premium']:
    premium_features = True
else:
    premium_features = False
```

---

**Status:** ✅ Ready to Use  
**Version:** 3.0  
**Last Updated:** January 20, 2026
