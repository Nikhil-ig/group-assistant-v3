# 🚫 Permission Restriction Feature

## Overview
Admins can now selectively block specific permissions for users while allowing others. This is more flexible than a full mute.

## Features Added

### 1. **Telegram API Service** (`v3/services/telegram_api.py`)

#### `_build_custom_permissions(blocked_types: list)`
- Dynamically builds ChatPermissions with selective blocks
- Supports both old and new Telegram Bot API versions
- Supports filtering individual permission types

#### `restrict_user_permissions(group_id, user_id, blocked_types, duration_hours, reason)`
- Main API method to restrict specific permissions
- Logs action to database
- Returns success/error status

#### Valid Block Types:
- `"media"` - Block all media (photos, videos, documents, audio, voice notes)
- `"stickers"` - Block stickers
- `"gifs"` - Block GIFs/animations
- `"polls"` - Block polls
- `"links"` - Block web page previews
- `"voice"` - Block voice messages
- `"video"` - Block videos
- `"audio"` - Block audio files
- `"documents"` - Block documents
- `"photos"` - Block photos
- `"all_messages"` - Block all messages

---

## 2. **Telegram Command** (`v3/bot/handlers.py`)

### `/restrict` Command Handler

**Usage:**
```
/restrict @username <block_type> [block_type2...] [hours]
```

**Examples:**
```
# Block stickers and GIFs for 24 hours
/restrict @spammer stickers gifs 24

# Permanently block media
/restrict @user123 media

# Block voice messages, links, and polls for 12 hours
/restrict @user voice links polls 12

# Block stickers permanently
/restrict @user stickers
```

**Response:**
```
🚫 User @spammer restricted

Blocked: stickers, gifs
Duration: for 24 hours
```

---

## 3. **REST API Endpoint** (`v3/api/endpoints.py`)

### POST `/api/v1/groups/{group_id}/restrict`

**Request Body:**
```json
{
  "target_user_id": 123456,
  "target_username": "spammer",
  "blocked_types": ["stickers", "gifs"],
  "duration_hours": 24,
  "reason": "Spam warning"
}
```

**Response (Success):**
```json
{
  "ok": true,
  "message": "✅ User 123456 restricted - Blocked: stickers, gifs for 24 hours",
  "timestamp": "2025-12-31T13:07:00Z"
}
```

**Response (Failure):**
```json
{
  "ok": false,
  "message": "⚠️ Restriction logged but Telegram action failed: Chat not found",
  "timestamp": "2025-12-31T13:07:00Z"
}
```

### Authorization:
- **SUPERADMIN**: Can restrict any user in any group
- **GROUP_ADMIN**: Can restrict users only in their own groups
- **USER**: No access (401 Unauthorized)

### Validation:
- Block types must be from the valid list
- At least one block type required
- User must have admin permission in the group

---

## 4. **How It Works**

### Telegram Command Flow:
```
/restrict @user stickers gifs 24
    ↓
Parse: user_id, blocked_types, duration
    ↓
Check admin status
    ↓
Call telegram_api.restrict_user_permissions()
    ↓
Log to database
    ↓
Send response to group
```

### API Flow:
```
POST /api/v1/groups/{group_id}/restrict
    ↓
Verify JWT token & RBAC
    ↓
Validate blocked_types
    ↓
Call telegram_api.restrict_user_permissions()
    ↓
Log to database
    ↓
Return JSON response
```

### Permission Building:
```
1. Get valid parameters from ChatPermissions signature (version-aware)
2. Start with all permissions enabled
3. For each blocked_type, disable specific permissions
4. Filter to only valid parameters for this API version
5. Create ChatPermissions object
6. Call restrict_chat_member() with custom permissions
```

---

## 5. **API Version Compatibility**

The feature automatically handles:
- **Old Telegram Bot API**: `can_send_media_messages` parameter
- **New Telegram Bot API**: Granular media parameters (`can_send_audio`, `can_send_photo`, etc.)
- **Mixed versions**: Graceful fallback to available parameters

---

## 6. **Database Logging**

All restrictions are logged as `MUTE` actions with the format:
```
{
  "action_type": "MUTE",
  "admin_username": "admin_name",
  "target_user_id": 123456,
  "target_username": "spammer",
  "reason": "Restrict: stickers, gifs for 24h",
  "timestamp": "2025-12-31T13:07:00Z"
}
```

---

## 7. **Testing**

### Test in Telegram Group:
```bash
# Test: Block stickers
/restrict @testuser stickers

# Test: Block multiple types
/restrict @testuser stickers gifs polls 12

# Test: Block media for 24 hours
/restrict @testuser media 24
```

### Test via API (cURL):
```bash
curl -X POST http://localhost:8000/api/v1/groups/-1001234567890/restrict \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target_user_id": 123456,
    "target_username": "spammer",
    "blocked_types": ["stickers", "gifs"],
    "duration_hours": 24,
    "reason": "Spam warning"
  }'
```

---

## 8. **Related Features**

- `/mute` - Mute user (read-only mode, blocks everything)
- `/unmute` - Restore full permissions
- `/lock` - Completely lock down a user (read-only)
- `/unlock` - Unlock a user

---

## 9. **Implementation Notes**

- ✅ Telegram command handler added and registered
- ✅ REST API endpoint added with RBAC
- ✅ Pydantic models for request/response validation
- ✅ Database logging integrated
- ✅ Error handling with graceful fallbacks
- ✅ Support for optional duration (permanent if not specified)
- ✅ Support for optional reason (logged to database)
- ✅ Version-aware permission building

---

## 10. **Files Modified**

1. `v3/services/telegram_api.py`
   - Added: `_build_custom_permissions()`
   - Added: `restrict_user_permissions()`

2. `v3/bot/handlers.py`
   - Added: `restrict_command()` method
   - Added: Command handler registration

3. `v3/api/endpoints.py`
   - Added: `RestrictPermissionsRequest` model
   - Added: `POST /groups/{group_id}/restrict` endpoint

---

## Status: ✅ READY FOR TESTING
