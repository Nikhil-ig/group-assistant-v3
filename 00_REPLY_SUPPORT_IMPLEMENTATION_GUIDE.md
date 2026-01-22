# 📋 Reply-to-Message Support - Implementation Guide for All Commands

## Overview

This guide explains how to add **reply-to-message** support to any command. This allows users to reply to a message and use the command, and it will act on the replied message instead.

## Core Concept

**Pattern:**
```
User replies to a message
User types: /command
Bot acts on the replied message
```

**Example:**
```
1. User replies to someone's message
2. User types: /ban
3. Bot bans that user (from the replied message)
```

## Helper Functions Already Available

### 1. `get_user_id_from_reply(message: Message) -> Optional[int]`
**Location:** Line 1047

**Purpose:** Extract user ID from replied message

**Usage:**
```python
# Get the user ID of whoever sent the replied message
replied_user_id = await get_user_id_from_reply(message)
if replied_user_id:
    # Use this user ID for the command action
    pass
```

### 2. `send_message_with_reply(message, text, ...)`
**Location:** Line 732

**Purpose:** Send a response that shows as reply in thread

**Usage:**
```python
# Send message as a reply (shows in thread)
await send_message_with_reply(
    message,
    "User banned!",
    parse_mode=ParseMode.HTML
)
```

## Implementation Pattern

### Step 1: Check for Reply at Command Start

```python
async def cmd_ban(message: Message):
    try:
        # Check if user replied to a message
        if message.reply_to_message:
            # Extract user ID from the replied message
            target_user_id = message.reply_to_message.from_user.id
        else:
            # Try to parse from command arguments
            args = message.text.split()
            if len(args) < 2:
                await send_and_delete(
                    message,
                    "Usage: /ban @username or reply to user + /ban",
                    delay=5
                )
                return
            
            # Parse user ID from args
            target_user_id = int(args[1].lstrip("@"))
        
        # Now use target_user_id for the command action
        # ... rest of command logic ...
```

### Step 2: Make Arguments Optional When Replying

```python
async def cmd_mute(message: Message):
    try:
        # If replying, duration is optional
        if message.reply_to_message:
            target_user_id = message.reply_to_message.from_user.id
            duration = None  # Optional when replying
            
            # Try to get duration from command args if provided
            args = message.text.split()
            if len(args) > 1:
                try:
                    duration = int(args[1])
                except ValueError:
                    pass
        else:
            # Without reply, require both user and duration
            args = message.text.split()
            if len(args) < 3:
                await send_and_delete(
                    message,
                    "Usage: /mute @username <duration_seconds>",
                    delay=5
                )
                return
```

## Commands to Update

Here are the top commands that should have reply support added:

### Admin Commands (High Priority)
1. **`/ban`** - Ban a user
2. **`/unban`** - Unban a user
3. **`/kick`** - Kick a user
4. **`/mute`** - Mute a user
5. **`/unmute`** - Unmute a user
6. **`/promote`** - Promote to admin
7. **`/demote`** - Remove admin (if exists)
8. **`/warn`** - Warn a user
9. **`/pin`** - Pin a message
10. **`/unpin`** - Unpin a message

### Info Commands (Medium Priority)
11. **`/id`** - Show user info
12. **`/stats`** - Show user stats
13. **`/verify`** - Verify a user

### Other Commands (Lower Priority)
14. **`/notes`** - Add notes about user
15. **`/afk`** - Toggle AFK status
16. **`/slowmode`** - Set slowmode
17. **`/send`** - Send as reply (already supports this!)

## Full Implementation Example

### Before (No Reply Support)
```python
async def cmd_ban(message: Message):
    try:
        if not await check_is_admin(message.from_user.id, message.chat.id):
            await send_and_delete(message, "❌ Admin only", delay=5)
            return
        
        args = message.text.split()
        if len(args) < 2:
            await send_and_delete(message, "Usage: /ban @username", delay=5)
            return
        
        target_user_id = int(args[1].lstrip("@"))
        # ... rest of ban logic ...
```

### After (With Reply Support)
```python
async def cmd_ban(message: Message):
    try:
        if not await check_is_admin(message.from_user.id, message.chat.id):
            await send_and_delete(message, "❌ Admin only", delay=5)
            return
        
        # ✅ NEW: Check if replying to a message
        if message.reply_to_message:
            target_user_id = message.reply_to_message.from_user.id
        else:
            # ✅ EXISTING: Parse from arguments
            args = message.text.split()
            if len(args) < 2:
                await send_and_delete(
                    message,
                    "Usage: /ban @username or reply to message + /ban",
                    delay=5
                )
                return
            target_user_id = int(args[1].lstrip("@"))
        
        # ... rest of ban logic remains the same ...
        
        # ✅ NEW: Use send_message_with_reply for professional response
        user_info = await get_advanced_user_info(target_user_id, message.chat.id)
        await send_message_with_reply(
            message,
            f"❌ Banned: {user_info['mention_html']}",
            parse_mode=ParseMode.HTML
        )
```

## Quick Checklist for Each Command

When adding reply support to a command:

- [ ] Check `message.reply_to_message` at start
- [ ] Extract user ID using `message.reply_to_message.from_user.id`
- [ ] Make arguments optional when replying (if applicable)
- [ ] Update usage message to mention reply option
- [ ] Use `send_message_with_reply()` for responses
- [ ] Get user info for professional display
- [ ] Test with reply AND without reply scenarios

## Benefits

✅ **More intuitive** - Users can just reply instead of typing user IDs
✅ **Faster** - Less typing required
✅ **Cleaner** - Shows replies in thread context
✅ **Professional** - Looks organized and structured
✅ **Flexible** - Works WITH or WITHOUT arguments

## Testing

For each updated command:

```
Test 1: Reply method
1. Reply to user's message
2. Type: /command
3. Verify action on replied user

Test 2: Arguments method
1. Type: /command @username [args]
2. Verify action on specified user

Test 3: Error handling
1. Type: /command (no reply, no args)
2. Verify helpful error message
```

## Examples of Perfect Reply Support

### /ban Example
```
Reply to @john's message → /ban
Bot: "❌ Banned: @john"
John is now banned
```

### /mute Example
```
Reply to @jane's message → /mute 3600
Bot: "🔇 Muted: @jane for 1 hour"
Jane is muted for 3600 seconds
```

### /id Example
```
Reply to any message → /id
Bot: Shows info of message author
(no arguments needed!)
```

### /promote Example
```
Reply to @bob's message → /promote
Bot: "⭐ Promoted: @bob to Administrator"
Bob is now admin
```

## Implementation Priority

**Phase 1 (Critical Admin Commands):**
- /ban, /unban, /kick
- /mute, /unmute
- /pin, /unpin

**Phase 2 (Info Commands):**
- /id, /stats, /verify

**Phase 3 (Other Commands):**
- /promote, /notes, /afk

## Code Pattern Summary

```python
async def cmd_example(message: Message):
    try:
        # Admin check
        if not await check_is_admin(message.from_user.id, message.chat.id):
            return
        
        # ✅ KEY PATTERN: Check reply first
        if message.reply_to_message:
            target_user_id = message.reply_to_message.from_user.id
        else:
            # Parse arguments
            args = message.text.split()
            if len(args) < 2:
                await send_and_delete(message, "Usage: /cmd or reply + /cmd")
                return
            target_user_id = int(args[1].lstrip("@"))
        
        # ✅ Perform action on target_user_id
        
        # ✅ Send response as reply
        await send_message_with_reply(message, "Action complete")
        
    except Exception as e:
        logger.error(f"Error: {e}")
```

---

**Current Status:** Ready for implementation
**Priority:** High (improves UX significantly)
**Impact:** 15+ commands will support reply method
**Time to Implement:** ~2-3 hours for all commands

Start with /ban, /kick, /mute - they are most commonly used! 🚀
