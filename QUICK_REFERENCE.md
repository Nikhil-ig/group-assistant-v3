# 🚀 Quick Reference Card - Permission Restriction

## 🎯 One-Liners

### Telegram Commands

**Direct Mode (with user ID):**
```bash
# Block stickers & GIFs
/restrict @user stickers gifs 24

# Block all media
/restrict @user media

# Block voice messages permanently
/restrict @user voice

# Block multiple types for 12 hours
/restrict @user stickers gifs polls links 12

# Block text messages (read-only)
/restrict @user all_messages
```

**Reply Mode (reply to user's message):**
```bash
# Block stickers & GIFs
/restrict stickers gifs 24

# Block all media
/restrict media

# Block voice messages permanently
/restrict voice

# Block text messages (read-only)
/restrict all_messages
```

✨ **NEW:** See [REPLY_MODE_GUIDE.md](./REPLY_MODE_GUIDE.md) for all commands with reply mode!

---

## 🌐 API Calls

### Basic Restriction
```bash
curl -X POST http://localhost:8000/api/v1/groups/-1001234567890/restrict \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target_user_id": 123456,
    "blocked_types": ["stickers", "gifs"],
    "duration_hours": 24
  }'
```

### With Reason
```bash
curl -X POST http://localhost:8000/api/v1/groups/-1001234567890/restrict \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target_user_id": 123456,
    "target_username": "spammer",
    "blocked_types": ["media"],
    "duration_hours": 48,
    "reason": "Excessive media spam"
  }'
```

### Permanent Restriction (No Duration)
```bash
curl -X POST http://localhost:8000/api/v1/groups/-1001234567890/restrict \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target_user_id": 123456,
    "blocked_types": ["links"]
  }'
```

---

## 📝 Block Types Quick List

```
media            → Block all media (photos, video, audio, voice, documents)
stickers         → Block stickers
gifs             → Block GIFs/animations
polls            → Block polls
links            → Block web page previews
voice            → Block voice messages
video            → Block videos
audio            → Block audio files
documents        → Block documents
photos           → Block photos
all_messages     → Block text messages (read-only)
```

---

## ✅ Response Examples

**✅ Success:**
```json
{
  "ok": true,
  "message": "✅ User 123456 restricted - Blocked: stickers, gifs for 24 hours",
  "timestamp": "2025-12-31T13:07:00Z"
}
```

**❌ Error:**
```json
{
  "ok": false,
  "message": "Invalid block type: invalid_type",
  "timestamp": "2025-12-31T13:07:00Z"
}
```

---

## 🔐 Authorization

**Get Token:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 111111,
    "username": "admin",
    "first_name": "Admin"
  }'
```

**Use Token:**
```bash
Authorization: Bearer YOUR_JWT_TOKEN
```

---

## 📊 Comparison

| Feature | Duration | Multiple Types | Permanent | Reversible |
|---------|----------|-----------------|-----------|-----------|
| Mute | ✅ Yes | ❌ No | ✅ Yes | ✅ Yes |
| Restrict | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| Lock | ✅ Yes | ❌ No | ✅ Yes | ✅ Yes |

---

## 🛠️ Useful Commands

```bash
# View logs
/logs

# View stats
/stats

# Unmute user
/unmute @user

# Check bot status
/state

# Test connection
/ping
```

---

## 📱 Real-World Examples

### Example 1: Sticker Spammer
```
/restrict @spammer stickers gifs 24
```

### Example 2: Media Flooder
```
/restrict @user media 48
```

### Example 3: Phishing Attempts
```
/restrict @hacker links
```

### Example 4: Disruptive User
```
/restrict @user all_messages
```

### Example 5: Multiple Violations
```
/restrict @user stickers gifs polls voice 72
```

---

**Status:** ✅ Ready to Use  
**Last Updated:** 2025-12-31
