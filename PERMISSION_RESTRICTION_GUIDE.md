# 🚫 Permission Restriction Feature - Complete Guide

---

## 📋 Table of Contents
1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Telegram Commands](#telegram-commands)
4. [REST API](#rest-api)
5. [Permission Types](#permission-types)
6. [Examples](#examples)
7. [Response Formats](#response-formats)
8. [Error Handling](#error-handling)

---

## 🎯 Overview

The Permission Restriction feature allows group admins to **selectively block specific content types** for users while keeping other permissions intact.

### Key Differences:

| Feature | Blocks | Allows |
|---------|--------|--------|
| **Mute** (`/mute`) | ✋ Everything | 📖 Read only |
| **Restrict** (`/restrict`) | 🎯 Specific types | ✅ Everything else |
| **Lock** (`/lock`) | ✋ Everything | 📖 Read only |

### 📊 Supported Block Types:

| Type | Blocks | Example Use Case |
|------|--------|------------------|
| `media` | 📸📹🎥🎵🎤 All media | Reduce spam |
| `stickers` | 🎨 Stickers only | Spam prevention |
| `gifs` | 🎬 GIFs/Animations | Fun spam control |
| `polls` | 📊 Polls only | Manage polling |
| `links` | 🔗 Web page previews | Security |
| `voice` | 🎤 Voice messages | Audio spam |
| `video` | 🎥 Videos only | Bandwidth control |
| `audio` | 🎵 Audio files | Media control |
| `documents` | 📄 Documents | Security |
| `photos` | 📸 Photos only | Image spam |
| `all_messages` | 💬 All text messages | Full lockdown |

---

## ⚡ Quick Start

### Telegram Command
```bash
/restrict @username stickers gifs 24
```

### REST API (cURL)
```bash
curl -X POST http://localhost:8000/api/v1/groups/-1001234567890/restrict \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target_user_id": 123456,
    "blocked_types": ["stickers", "gifs"],
    "duration_hours": 24
  }'
```

---

## 🤖 Telegram Commands

### Command: `/restrict`

**Syntax (Direct Mode):**
```
/restrict <@username or user_id> <block_type1> [block_type2...] [hours]
```

**Syntax (Reply Mode - NEW!):**
```
Reply to user's message, then:
/restrict <block_type1> [block_type2...] [hours]
```

**Required Parameters:**
- `@username or user_id` - Target user (only in direct mode)
- `block_type` - What to block (see Permission Types)

**Optional Parameters:**
- `block_type2, block_type3...` - Multiple block types
- `hours` - Duration (default: permanent)

✨ **NEW FEATURE:** All commands now support reply mode! See [REPLY_MODE_GUIDE.md](./REPLY_MODE_GUIDE.md) for details.

---

### 📝 Command Examples

#### Example 1️⃣: Block Stickers for 24 Hours (Direct)
```
/restrict @spammer stickers 24
```
**Response:**
```
🚫 User @spammer restricted

Blocked: stickers
Duration: for 24 hours
```

#### Example 1b️⃣: Block Stickers for 24 Hours (Reply Mode)
```
(Reply to spammer's message with):
/restrict stickers 24
```
**Response:**
```
🚫 User @spammer restricted

Blocked: stickers
Duration: for 24 hours
```

#### Example 2️⃣: Block Multiple Types Permanently
```
/restrict @user123 stickers gifs polls
```
**Response:**
```
🚫 User user123 restricted

Blocked: stickers, gifs, polls
Duration: (permanent)
```

#### Example 3️⃣: Block All Media for 12 Hours
```
/restrict 987654321 media 12
```
**Response:**
```
🚫 User 987654321 restricted

Blocked: media
Duration: for 12 hours
```

#### Example 4️⃣: Block Voice Messages Permanently
```
/restrict @user voice
```
**Response:**
```
🚫 User @user restricted

Blocked: voice
Duration: (permanent)
```

#### Example 5️⃣: Reply to a Message (Reply Mode - Quickest!)
```
(Reply to user's message with):
/restrict stickers gifs
```
**Response:**
```
🚫 User @user restricted

Blocked: stickers, gifs
Duration: (permanent)
```

---

## 🌐 REST API

### Endpoint: `POST /api/v1/groups/{group_id}/restrict`

**Base URL:** `http://localhost:8000`

**Authentication:** Bearer Token (JWT)

**Content-Type:** `application/json`

---

### Request Body

```json
{
  "target_user_id": 123456,
  "target_username": "optional_username",
  "blocked_types": [
    "stickers",
    "gifs"
  ],
  "duration_hours": 24,
  "reason": "Spam warning"
}
```

**Field Details:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `target_user_id` | `integer` | ✅ Yes | Telegram user ID to restrict |
| `target_username` | `string` | ❌ No | Username (for logging) |
| `blocked_types` | `array` | ✅ Yes | List of permission types to block |
| `duration_hours` | `integer` | ❌ No | Duration (null = permanent) |
| `reason` | `string` | ❌ No | Reason for restriction (logged) |

---

### 🔐 Authorization

**Headers Required:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
```

**RBAC Rules:**
- 🟦 **SUPERADMIN**: Can restrict any user in any group
- 🟩 **GROUP_ADMIN**: Can restrict users only in their group
- 🟥 **USER**: ❌ No access (403 Forbidden)

---

### ✅ Success Response (200 OK)

```json
{
  "ok": true,
  "message": "✅ User 123456 restricted - Blocked: stickers, gifs for 24 hours",
  "timestamp": "2025-12-31T13:07:00Z"
}
```

---

### ❌ Error Responses

#### Unauthorized (401)
```json
{
  "ok": false,
  "message": "❌ Unauthorized",
  "timestamp": "2025-12-31T13:07:00Z"
}
```

#### Forbidden (403)
```json
{
  "ok": false,
  "message": "❌ Not authorized to restrict users in this group",
  "timestamp": "2025-12-31T13:07:00Z"
}
```

#### Invalid Block Type (400)
```json
{
  "ok": false,
  "message": "❌ Invalid block type: invalid_type. Valid types: media, stickers, gifs, polls, links, voice, video, audio, documents, photos, all_messages",
  "timestamp": "2025-12-31T13:07:00Z"
}
```

#### Server Error (500)
```json
{
  "ok": false,
  "message": "❌ Restriction failed: Internal server error",
  "timestamp": "2025-12-31T13:07:00Z"
}
```

---

## 📚 Permission Types

### 🎨 Media Types

#### `media` (Block All)
- 🚫 Blocks: Photos, Videos, Documents, Audio, Voice notes
- ✅ Allows: Text messages, Stickers, GIFs, Polls
- **Use Case:** Heavy spam or NSFW content

```
/restrict @user media
```

#### Individual Media Types

**`photos`** - Just photos
```
/restrict @user photos 24
```

**`video`** - Just videos
```
/restrict @user video
```

**`audio`** - Just audio files
```
/restrict @user audio
```

**`voice`** - Just voice messages
```
/restrict @user voice
```

**`documents`** - Just documents
```
/restrict @user documents
```

---

### 🎭 Content Types

#### `stickers`
- 🚫 Blocks sticker sending
- ✅ Allows: Everything else
- **Use Case:** Sticker spam

```
/restrict @spammer stickers
```

#### `gifs`
- 🚫 Blocks GIF/animation sending
- ✅ Allows: Everything else
- **Use Case:** GIF spam

```
/restrict @user gifs 12
```

#### `polls`
- 🚫 Blocks poll creation
- ✅ Allows: Everything else
- **Use Case:** Poll spam prevention

```
/restrict @user polls
```

#### `links`
- 🚫 Blocks web page preview links
- ✅ Allows: Text, media, etc.
- **Use Case:** Security/phishing prevention

```
/restrict @user links
```

---

### 💬 Special Types

#### `all_messages`
- 🚫 Blocks all text messages
- ✅ Allows: Nothing (read-only)
- **Use Case:** Severe spam

```
/restrict @user all_messages
```

---

## 💡 Examples

### Real-World Scenarios

#### Scenario 1️⃣: Spam Prevention

**Problem:** User spamming stickers and GIFs

**Solution:**
```
/restrict @spammer stickers gifs
```

**Result:** User can still send text and media, but no stickers/GIFs for 24h

---

#### Scenario 2️⃣: Media Spam

**Problem:** User flooding group with photos and videos

**Solution:**
```
/restrict @user media 48
```

**Result:** User blocked from sending photos, videos, audio, documents, voice for 48 hours

---

#### Scenario 3️⃣: Security Issue

**Problem:** User sharing phishing links

**Solution:**
```
/restrict @hacker links
```

**Result:** User's web link previews disabled permanently

---

#### Scenario 4️⃣: Multiple Violations

**Problem:** User spamming stickers, polls, and voice messages

**Solution:**
```
/restrict @user stickers polls voice 72
```

**Result:** 3 specific content types blocked for 72 hours

---

#### Scenario 5️⃣: Complete Lockdown

**Problem:** User being disruptive

**Solution:**
```
/restrict @user all_messages
```

**Result:** User can only read (read-only mode)

---

## 📤 Response Formats

### Telegram Command Response

**Success:**
```
🚫 User @username restricted

Blocked: stickers, gifs, polls
Duration: for 24 hours
```

**Failure:**
```
❌ Failed: User not found
```

**Error:**
```
⚠️ User logged as restricted, but Telegram action failed: Chat not found
```

---

### REST API Response

**Success (200 OK):**
```json
{
  "ok": true,
  "message": "✅ User 123456 restricted - Blocked: stickers, gifs for 24 hours",
  "timestamp": "2025-12-31T13:07:00.123Z"
}
```

**Partial Success (200 OK, but Telegram failed):**
```json
{
  "ok": false,
  "message": "⚠️ Restriction logged but Telegram action failed: Chat not found",
  "timestamp": "2025-12-31T13:07:00.123Z"
}
```

---

## ⚠️ Error Handling

### Common Errors & Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `Not authorized` | User not admin | Grant admin status first |
| `Invalid block type` | Typo in block type | Check spelling from valid list |
| `User not found` | Wrong user ID | Verify correct user ID/username |
| `Chat not found` | Group doesn't exist | Verify correct group ID |
| `Unauthorized` | Invalid/expired token | Refresh JWT token |

### Debug Mode

Check logs for detailed error information:
```bash
tail -f logs/api.log | grep "restrict"
```

---

## 📊 Database Logging

All restrictions are logged to database for audit trail:

```json
{
  "action_type": "MUTE",
  "admin_id": 111111,
  "admin_username": "admin_name",
  "target_user_id": 123456,
  "target_username": "user_name",
  "reason": "Restrict: stickers, gifs for 24h",
  "timestamp": "2025-12-31T13:07:00Z",
  "group_id": -1001234567890
}
```

View logs via API:
```bash
curl -X GET "http://localhost:8000/api/v1/groups/-1001234567890/logs" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🔧 Technical Details

### How It Works

1. **Parse Input** - Extract user, block types, duration
2. **Validate** - Check admin status and block types
3. **Build Permissions** - Create ChatPermissions object
4. **Execute** - Call Telegram API to restrict
5. **Log** - Record action in database
6. **Respond** - Send success/error message

### Version Compatibility

✅ Works with both:
- Old Telegram Bot API (`can_send_media_messages`)
- New Telegram Bot API (granular permissions)

Automatic fallback ensures compatibility!

---

## 🚀 Testing

### Test via Telegram

```
1. Start bot: python -m v3
2. Send command: /restrict @testuser stickers 24
3. Check response in group
```

### Test via API

```bash
curl -X POST http://localhost:8000/api/v1/groups/-1001234567890/restrict \
  -H "Authorization: Bearer JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target_user_id": 123456,
    "blocked_types": ["stickers", "gifs"],
    "duration_hours": 24,
    "reason": "Spam testing"
  }'
```

---

## 📚 Related Commands

| Command | Purpose |
|---------|---------|
| `/mute @user 24` | Block all messages (read-only) |
| `/unmute @user` | Restore all permissions |
| `/restrict @user stickers` | Block specific types |
| `/logs` | View audit logs |
| `/stats` | View moderation stats |

---

## ✅ Feature Status

- ✅ Telegram command: `/restrict`
- ✅ REST API endpoint: `POST /restrict`
- ✅ Database logging
- ✅ RBAC authorization
- ✅ Error handling
- ✅ Duration support
- ✅ Multiple block types
- ✅ Version compatibility
- ✅ Audit trail

---

## 📞 Support

**For issues:**
1. Check logs: `tail -f logs/api.log`
2. Verify permissions: `/logs` command
3. Check block type spelling
4. Verify user ID/group ID

---

**Last Updated:** 2025-12-31  
**Status:** ✅ Production Ready
