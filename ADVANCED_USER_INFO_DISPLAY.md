# 🎯 ADVANCED USER INFORMATION DISPLAY SYSTEM

## Overview

The bot now features an **enhanced user information display system** that provides comprehensive, visually appealing profiles with advanced styling, role indicators, premium badges, and detailed permission information.

---

## ✨ Key Features

### 1. **Smart Role Indicators with Emojis**
```
👑 Owner          - Group creator with full control
⭐ Administrator  - Admin with restricted permissions
👤 Member         - Regular group member
🔒 Restricted     - User with limited permissions
↪️ Left           - User who left the group
❌ Kicked         - User who was removed
```

### 2. **Enhanced User Mention Format**
Instead of basic mentions:
```
Before: <a href='tg://user?id=501166051'>User 501166051</a>

After:  👑 <a href='tg://user?id=501166051'>John Doe</a>
        ⭐ <a href='tg://user?id=123456'>@username</a>
        🔒 <a href='tg://user?id=789012'>Jane Smith</a>
```

### 3. **Premium & Bot Badges**
- **💎 PREMIUM** - Telegram Premium subscriber
- **🤖 BOT** - Bot account indicator

### 4. **Comprehensive User Profile Information**
```
⚙️ ADVANCED CONTENT & BEHAVIOR MANAGER
───────────────────────────────────────────────────

👤 MEMBER PROFILE:
  👑 John Doe
  Role: 👑 Owner
  ID: 501166051
  Name: John Doe
  Username: @johndoe
  Title: Founder 💎 PREMIUM

📋 CONTENT PERMISSIONS:
  📝 Text: ✅ Allowed
  🎨 Stickers: ✅ Allowed
  🎬 GIFs: ✅ Allowed
  📸 Media: ✅ Allowed
  🎤 Voice: ✅ Allowed
  🔗 Links: ✅ Allowed

💡 Click buttons to toggle individual permissions
```

---

## 🔧 Core Functions

### **`get_user_mention(user_id, group_id) → str`**

**Purpose:** Get enhanced user mention link with role indicator

**Features:**
- Smart role emoji detection (👑, ⭐, 👤, 🔒)
- Username with @ prefix or full name fallback
- HTML formatted mention link
- Graceful error handling

**Example Output:**
```html
⭐ <a href='tg://user?id=123456'>@admin_user</a>
👤 <a href='tg://user?id=789012'>Jane Smith</a>
👑 <a href='tg://user?id=501166051'>John Doe</a>
```

**Usage:**
```python
user_mention = await get_user_mention(user_id, group_id)
await message.answer(f"User: {user_mention}")
```

---

### **`get_advanced_user_info(user_id, group_id) → dict`**

**Purpose:** Fetch comprehensive user information including profile, permissions, and metadata

**Returns Dictionary:**
```python
{
    'user_id': int,                    # Telegram user ID
    'first_name': str,                 # User's first name
    'last_name': str or None,          # User's last name (optional)
    'username': str or None,           # Telegram username (optional)
    'is_bot': bool,                    # Is this a bot account
    'role': str,                       # 'creator', 'administrator', 'member', 'restricted'
    'role_text': str,                  # Formatted role (e.g., "👑 Owner")
    'role_emoji': str,                 # Role emoji (👑, ⭐, 👤, etc.)
    'custom_title': str or None,       # Custom admin title
    'has_profile_photo': bool,         # Does user have profile picture
    'profile_photo_id': str or None,   # Profile photo file ID
    'is_premium': bool,                # Telegram Premium subscriber
    'permissions': dict,               # User permissions object
    'mention_html': str,               # HTML formatted mention with role
    'full_name': str,                  # Full name (first + last)
    'display_name': str,               # Display name (@username or full name)
}
```

**Example Usage:**
```python
user_info = await get_advanced_user_info(user_id, group_id)

# Access information
print(user_info['full_name'])        # "John Doe"
print(user_info['role_emoji'])       # "👑"
print(user_info['mention_html'])     # "👑 <a href='tg://user?id=...'>John Doe</a>"
print(user_info['is_premium'])       # True/False
print(user_info['custom_title'])     # "Founder" or None

# Use in messages
message = f"""
User: {user_info['mention_html']}
Role: {user_info['role_text']}
Username: @{user_info['username'] or 'N/A'}
"""
```

---

## 📊 Permission Status Display

### **Content Permissions**
```
📝 Text      - Send text messages
🎨 Stickers  - Send stickers and emojis
🎬 GIFs      - Send animations/GIFs
📸 Media     - Send photos, videos, documents
🎤 Voice     - Send voice and audio messages
🔗 Links     - Send web previews and links
```

### **Status Indicators**
```
✅ Allowed   - User can perform this action
❌ Blocked   - User cannot perform this action
🔒 Locked    - User restricted (admin action)
```

---

## 🎨 Visual Display Examples

### **Permission Manager Header**
```
⚙️ PERMISSION MANAGER
───────────────────────────────────────────────────

👤 USER INFO:
  👑 John Doe 💎
  Role: 👑 Owner
  ID: 501166051

⚙️ QUICK PERMISSIONS:
  ✅ Management Active

💡 Click section headers to expand detailed settings
```

### **Expanded Content Permissions**
```
⚙️ ADVANCED CONTENT & BEHAVIOR MANAGER
───────────────────────────────────────────────────

👤 MEMBER PROFILE:
  ⭐ @admin_user
  Role: ⭐ Administrator
  ID: 123456789
  Name: Admin User
  Username: @admin_user
  Title: Content Moderator

📋 CONTENT PERMISSIONS:
  📝 Text: ✅ Allowed
  🎨 Stickers: ❌ Blocked
  🎬 GIFs: ✅ Allowed
  📸 Media: ✅ Allowed
  🎤 Voice: ❌ Blocked
  🔗 Links: ✅ Allowed

💡 Click buttons to toggle individual permissions
```

---

## 🔄 Integration Points

### **Used in These Commands:**
1. **`/free`** - Advanced content & behavior manager
2. **`/restrict`** & **`/unrestrict`** - Permission toggles
3. **User profile displays** - Inline buttons and callbacks
4. **Admin panel** - Advanced admin management
5. **Permission callbacks** - Real-time permission updates

### **Used in These Callbacks:**
- `free_toggle_*` - Permission toggles
- `handle_permission_toggle_callback` - Permission updates
- `handle_free_callback` - Free menu interactions
- `refresh_free_menu` - Menu refresh
- `refresh_free_expanded_content` - Content expansion

---

## 🛡️ Error Handling

Both functions include graceful error handling:

```python
try:
    member = await bot.get_chat_member(group_id, user_id)
    # Process user data...
except Exception as e:
    logger.warning(f"Could not fetch user info for {user_id}: {e}")
    # Return fallback data with user ID only
    return default_user_info
```

**Fallback Behavior:**
- If member info unavailable → Returns basic user data with user ID
- If profile photo unavailable → `has_profile_photo` = False
- If username unavailable → Uses first name or "User {ID}"

---

## 💡 Best Practices

### **1. Always Use Advanced Info for User Displays**
```python
# ❌ Old Way
user_mention = f"<code>{user_id}</code>"

# ✅ New Way
user_info = await get_advanced_user_info(user_id, group_id)
message = f"User: {user_info['mention_html']}\nRole: {user_info['role_text']}"
```

### **2. Check Role Before Showing Sensitive Info**
```python
user_info = await get_advanced_user_info(user_id, group_id)
if user_info['role'] in ['creator', 'administrator']:
    # Show detailed admin information
    show_admin_panel(user_info)
else:
    # Show limited member information
    show_member_info(user_info)
```

### **3. Use Premium Badge for Special Features**
```python
user_info = await get_advanced_user_info(user_id, group_id)
if user_info['is_premium']:
    # Show premium features
    enable_premium_features(user_info)
else:
    # Show free features only
    enable_free_features(user_info)
```

### **4. Handle Bots Specially**
```python
user_info = await get_advanced_user_info(user_id, group_id)
if user_info['is_bot']:
    bot_badge = " 🤖"
    # Apply bot-specific logic
else:
    bot_badge = ""
    # Apply user-specific logic
```

---

## 🚀 Performance Considerations

- **Caching:** User info is fetched on-demand (no persistent cache)
- **Timeout:** API calls have 5-second timeout limit
- **Fallbacks:** Graceful degradation when info unavailable
- **Batch Operations:** For multiple users, consider batch fetching

---

## 📝 Example Implementation

```python
async def cmd_userinfo(message: Message):
    """Advanced user information command with full profile display"""
    try:
        # Get target user
        if message.reply_to_message:
            target_user_id = message.reply_to_message.from_user.id
        else:
            # Parse args...
            target_user_id = extracted_id
        
        # Fetch advanced user info
        user_info = await get_advanced_user_info(target_user_id, message.chat.id)
        
        # Build message
        info_text = f"""
<b>👤 COMPREHENSIVE USER PROFILE</b>

<b>IDENTITY:</b>
{user_info['mention_html']}
<b>Full Name:</b> {user_info['full_name']}
<b>User ID:</b> <code>{user_info['user_id']}</code>

<b>ROLE & STATUS:</b>
<b>Role:</b> {user_info['role_text']}
<b>Status:</b> {'🤖 BOT' if user_info['is_bot'] else '👤 USER'}
<b>Premium:</b> {'💎 YES' if user_info['is_premium'] else '❌ NO'}

<b>PERMISSIONS:</b>
📝 Messages: {'✅' if user_info['permissions']['can_send_messages'] else '❌'}
📸 Media: {'✅' if user_info['permissions']['can_send_media_messages'] else '❌'}

{user_info['mention_html']}'s detailed profile above.
        """
        
        await send_message_with_reply(message, info_text, parse_mode=ParseMode.HTML)
        
    except Exception as e:
        logger.error(f"User info command failed: {e}")
        await send_and_delete(message, f"❌ Error: {str(e)}")
```

---

## 🔐 Security Notes

- **ID Privacy:** User IDs are only shown to admins
- **Photo Fetching:** Only fetches if user has profile photo
- **Permission Display:** Shows actual Telegram API permissions
- **Role Verification:** Verified through `get_chat_member()` API call

---

## 📚 Related Documentation

- `00_ADVANCED_FEATURES_COMPLETE.md` - Feature overview
- `BOT_V2_ARCHITECTURE_VISUAL.md` - System architecture
- `API_V2_COMPLETE.md` - API V2 integration

---

**Version:** 3.0  
**Last Updated:** January 20, 2026  
**Status:** ✅ Production Ready
