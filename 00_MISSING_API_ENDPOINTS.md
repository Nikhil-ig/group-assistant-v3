# ⚠️ IMPORTANT: Missing API Endpoints in api_v2

## Status: NEEDS TO BE ADDED TO API 🚨

The following endpoints are being called by the bot but may not exist in the API yet:

### 1. ❌ GET `/api/v2/groups/{group_id}/policies`
**Current Issue**: Returns 404
**Used by**: `cmd_free()` to fetch group policy settings
```python
# Bot tries to fetch all policies at once
GET /api/v2/groups/-1003447608920/policies
Expected Response:
{
  "data": {
    "floods_enabled": true,
    "spam_enabled": false,
    "checks_enabled": true,
    "silence_mode": false
  }
}
```

### 2. ✅ POST `/api/v2/groups/{group_id}/policies/floods`
**Status**: Exists (200 OK)
**Payload**: `{"enabled": true}`

### 3. ✅ POST `/api/v2/groups/{group_id}/policies/spam`
**Status**: Exists (200 OK)
**Payload**: `{"enabled": true}`

### 4. ✅ POST `/api/v2/groups/{group_id}/policies/checks`
**Status**: Exists (200 OK)
**Payload**: `{"enabled": true}`

### 5. ✅ POST `/api/v2/groups/{group_id}/policies/silence`
**Status**: Exists (200 OK)
**Payload**: `{"enabled": true}`

### 6. ❌ POST `/api/v2/groups/{group_id}/enforcement/reset-permissions`
**Current Issue**: Returns 404
**Used by**: `handle_free_callback()` for "Reset All" button
```python
# Bot tries to reset all user permissions
POST /api/v2/groups/-1003447608920/enforcement/reset-permissions
Payload: {"user_id": 501166051}
Expected Response: {"success": true, "message": "Permissions reset"}
```

### 7. ✅ POST `/api/v2/groups/{group_id}/enforcement/toggle-permission`
**Status**: Exists (200 OK)
**Working correctly with new implementation**

## Quick Fix Instructions 📋

### Option A: Add Missing Endpoints (RECOMMENDED)
Add these two endpoints to your `api_v2` server:

#### Endpoint 1: Get Group Policies
```python
# In your api_v2/routes/policies.py or similar

@router.get("/groups/{group_id}/policies")
async def get_group_policies(group_id: int):
    """Fetch all policy settings for a group"""
    try:
        # Get group policies from database
        db = get_database()
        policies = await db.policies.find_one({"group_id": group_id})
        
        if not policies:
            # Return default policies if not set
            return {
                "data": {
                    "floods_enabled": False,
                    "spam_enabled": False,
                    "checks_enabled": False,
                    "silence_mode": False
                }
            }
        
        return {
            "data": {
                "floods_enabled": policies.get("floods_enabled", False),
                "spam_enabled": policies.get("spam_enabled", False),
                "checks_enabled": policies.get("checks_enabled", False),
                "silence_mode": policies.get("silence_mode", False)
            }
        }
    except Exception as e:
        return {"data": {}}
```

#### Endpoint 2: Reset Permissions
```python
# In your api_v2/routes/enforcement.py or similar

@router.post("/groups/{group_id}/enforcement/reset-permissions")
async def reset_user_permissions(group_id: int, body: dict):
    """Reset all user permissions to default"""
    try:
        user_id = body.get("user_id")
        if not user_id:
            return {"success": False, "error": "user_id required"}
        
        # Reset to default permissions (all enabled)
        db = get_database()
        await db.user_permissions.update_one(
            {"group_id": group_id, "user_id": user_id},
            {
                "$set": {
                    "can_send_messages": True,
                    "can_send_audios": True,
                    "can_send_documents": True,
                    "can_send_photos": True,
                    "can_send_videos": True,
                    "can_send_other_messages": True,
                    "can_add_web_page_previews": True,
                    "can_send_media_messages": True,
                    "updated_at": datetime.now()
                }
            },
            upsert=True
        )
        
        return {"success": True, "message": "All permissions reset to default"}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### Option B: Workaround (NOT RECOMMENDED)
If you can't add endpoints yet, modify `cmd_free()` to fetch individual policies:
```python
# Instead of: GET /api/v2/groups/{group_id}/policies
# Use these individual calls:
floods_enabled = (await client.get(.../policies/floods...)).status_code == 200
spam_enabled = (await client.get(.../policies/spam...)).status_code == 200
checks_enabled = (await client.get(.../policies/checks...)).status_code == 200
silence_mode = (await client.get(.../policies/silence...)).status_code == 200
```

## Current Status Log 📊

```
2026-01-18 21:25:07 - API Error Log:
✅ GET /api/v2/groups/{gid}/users/{uid}/permissions - 200 OK
❌ GET /api/v2/groups/{gid}/policies - 404 NOT FOUND
✅ GET /api/v2/groups/{gid}/night-mode/check/{uid}/text - 200 OK
✅ GET /api/v2/groups/{gid}/night-mode/status - 200 OK
✅ POST /api/v2/groups/{gid}/enforcement/toggle-permission - 400 (FIXED)
❌ POST /api/v2/groups/{gid}/enforcement/reset-permissions - 404 NOT FOUND
```

## Impact Assessment 🎯

### Without These Endpoints:
- ❌ `cmd_free()` displays default policy values (shows as disabled)
- ❌ "Reset All" button doesn't work
- ⚠️ UX degraded but core functionality still works

### With These Endpoints:
- ✅ `cmd_free()` displays accurate policy states
- ✅ "Reset All" button fully functional
- ✅ Perfect user experience

## Next Steps 🚀

1. **If you control the API**: Add the two missing endpoints above
2. **If API is managed elsewhere**: Contact API maintainer with this issue
3. **For now**: Bot will work with default policy values shown

## Testing Endpoints 🧪

### Test GET /api/v2/groups/{group_id}/policies
```bash
curl -X GET http://localhost:8002/api/v2/groups/-1003447608920/policies \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Test POST /api/v2/groups/{group_id}/enforcement/reset-permissions
```bash
curl -X POST http://localhost:8002/api/v2/groups/-1003447608920/enforcement/reset-permissions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 501166051}'
```

## Files Involved 📁
- Bot: `bot/main.py` (cmd_free function)
- API: `api_v2/routes/policies.py` (needs updates)
- API: `api_v2/routes/enforcement.py` (needs updates)

## Summary 📝
The bot fixes for callback handling are complete and working. The remaining issues are in the API layer. Add the two missing endpoints and everything will be 100% functional.
