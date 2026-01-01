# 📝 Reply Mode Commands Guide

## 🎯 Overview

All moderation commands support **reply mode** - you can reply to a user's message and then use a command to take action on that user. This is more intuitive than typing user IDs or mentions!

---

## ✨ Supported Commands with Reply Mode

| Command | Description | Reply Mode | Direct Mode |
|---------|-------------|-----------|------------|
| `/ban` | Ban user | ✅ | ✅ |
| `/kick` | Kick user | ✅ | ✅ |
| `/warn` | Warn user | ✅ | ✅ |
| `/mute` | Mute user | ✅ | ✅ |
| `/unmute` | Unmute user | ✅ | ✅ |
| `/restrict` | Restrict permissions | ✅ | ✅ |

---

## 📖 How to Use Reply Mode

### 1️⃣ Find a message from the user
- Locate any message sent by the user you want to moderate

### 2️⃣ Reply to that message
- Click/tap on the message → Choose "Reply"

### 3️⃣ Type the command
- Use the command without specifying the user
- Command will automatically target the user whose message you replied to

---

## 🔔 Command Examples

### /ban - Ban User

**Reply Mode:**
```
Reply to user's message with:
/ban

Or with a reason:
/ban Spamming advertisements
```

**Direct Mode:**
```
/ban @username
/ban 123456
/ban @user Inappropriate content
```

---

### /kick - Kick User

**Reply Mode:**
```
Reply to user's message with:
/kick

Or with a reason:
/kick Violating rules
```

**Direct Mode:**
```
/kick @username
/kick 123456 Disruptive behavior
```

---

### /warn - Warn User

**Reply Mode:**
```
Reply to user's message with:
/warn

Or with a reason:
/warn First warning for spam
```

**Direct Mode:**
```
/warn @username
/warn 123456 Off-topic discussion
```

---

### /mute - Mute User

**Reply Mode:**
```
Reply to user's message with:
/mute                          (permanent)
/mute 24                       (24 hours)
/mute 12 Too much spam         (12 hours with reason)
```

**Direct Mode:**
```
/mute @username
/mute 123456 24 Excessive messages
/mute @user 48
```

---

### /unmute - Unmute User

**Reply Mode:**
```
Reply to user's message with:
/unmute
```

**Direct Mode:**
```
/unmute @username
/unmute 123456
```

---

### /restrict - Restrict Permissions

**Reply Mode:**
```
Reply to user's message with:
/restrict stickers            (block stickers)
/restrict media gifs          (block media and gifs)
/restrict voice video 24      (block voice & video for 24 hours)
/restrict all_messages        (read-only)
```

**Direct Mode:**
```
/restrict @username stickers
/restrict 123456 media gifs 48
/restrict @user links
/restrict 123456 voice video audio
```

---

## 📋 Block Types for /restrict

When using reply mode with `/restrict`, you can specify any of these block types:

- `media` - Block all media (photos, videos, documents, audio, voice)
- `stickers` - Block stickers
- `gifs` - Block GIFs/animations
- `polls` - Block polls
- `links` - Block web page previews
- `voice` - Block voice messages
- `video` - Block videos
- `audio` - Block audio files
- `documents` - Block documents
- `photos` - Block photos
- `all_messages` - Block all messages (read-only)

---

## 🎬 Real-World Scenarios

### Scenario 1: Quick Spam Response
**Problem:** User sends multiple spam messages
**Solution:**
1. Reply to one of their messages
2. Type: `/mute 24 Spam`
3. Done! ✅

### Scenario 2: Selective Permission Blocking
**Problem:** User keeps sending inappropriate stickers
**Solution:**
1. Reply to the sticker message
2. Type: `/restrict stickers`
3. Done! ✅

### Scenario 3: Temporary Kick
**Problem:** User is being disruptive
**Solution:**
1. Reply to their message
2. Type: `/kick Disruptive behavior`
3. Done! ✅

### Scenario 4: Complete Lockdown
**Problem:** User is trolling with all types of media
**Solution:**
1. Reply to their message
2. Type: `/restrict media stickers gifs 72`
3. Done! ✅

### Scenario 5: Read-Only Mode
**Problem:** User can read but shouldn't send messages
**Solution:**
1. Reply to their message
2. Type: `/restrict all_messages 48`
3. Done! ✅

---

## ⚡ Quick Reference

### Ban/Kick/Warn (No Parameters)
```
Just reply and type the command!
/ban
/kick
/warn
```

### Mute (Optional Duration)
```
/mute              (permanent)
/mute 24           (24 hours)
/mute 12 reason    (12 hours + reason)
```

### Restrict (Block Type Required)
```
/restrict stickers           (single type)
/restrict media gifs         (multiple types)
/restrict voice 24           (with duration)
/restrict stickers gifs 72   (multiple + duration)
```

### Unmute (No Parameters)
```
Just reply and type:
/unmute
```

---

## 💡 Pro Tips

1. **Faster Workflow:** Reply mode is faster than typing user IDs
2. **Context Preservation:** You see exactly which message you're acting on
3. **Mobile Friendly:** Much easier on mobile devices
4. **Less Error-Prone:** No need to type user IDs correctly

---

## ❓ FAQ

**Q: Can I use reply mode in threads?**
A: Yes! Reply mode works in threads and regular channels.

**Q: What if I don't have a message to reply to?**
A: Use direct mode: `/ban @username` or `/ban 123456`

**Q: Can I combine reply mode with direct mode?**
A: No - use either one or the other, not both.

**Q: What if the user deleted their message?**
A: Use direct mode with their username or ID.

**Q: Does reply mode work for /restrict with multiple block types?**
A: Yes! Example: `/restrict stickers gifs 24`

---

## ✅ Status

- ✅ All commands support reply mode
- ✅ All duration and reason parameters work in reply mode
- ✅ Works in groups and supergroups
- ✅ Works in message threads
- ✅ Database logging tracks reply mode actions
- ✅ RBAC controls still enforced

---

**Last Updated:** 2025-12-31  
**Status:** Production Ready 🚀
