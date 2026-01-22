# 🔧 Toggle Permission - Backward Compatibility Fix

## Problem
The API was rejecting toggle requests because it was receiving old format requests from the bot:
- **Received:** `{'user_id': 501166051, 'permission_type': 'can_send_messages'}`
- **Expected:** `{'user_id': 501166051, 'metadata': {'permission_type': 'send_messages'}}`

## Root Cause
The bot code had been updated to send the new format, but the bot process was still running with old code (cached/not reloaded).

## Solution
Made the API endpoint backward compatible to accept BOTH formats:

### Old Format (Legacy)
```json
{
  "user_id": 501166051,
  "permission_type": "can_send_messages"
}
```

### New Format (Current)
```json
{
  "user_id": 501166051,
  "metadata": {
    "permission_type": "send_messages"
  }
}
```

## Implementation

### `/api_v2/routes/enforcement_endpoints.py` - toggle_permission endpoint

**1. Enhanced parsing to support both formats:**
```python
# Support both formats
metadata = action.get("metadata", {})
permission_type = metadata.get("permission_type") if metadata else None

# If metadata format didn't work, try direct format (for backward compat)
if not permission_type:
    permission_type = action.get("permission_type")
```

**2. Expanded mapping to handle both permission name formats:**
```python
perm_mapping = {
    # New format (without "can_" prefix)
    "send_messages": "can_send_messages",
    "send_audios": "can_send_audios",
    "send_other_messages": "can_send_other_messages",
    # Old format (with "can_" prefix) - for backward compatibility
    "can_send_messages": "can_send_messages",
    "can_send_audios": "can_send_audios",
    "can_send_other_messages": "can_send_other_messages",
    # ... etc
}
```

## Benefits
- ✅ Works immediately without restarting bot
- ✅ Supports both old and new request formats
- ✅ Handles legacy code seamlessly
- ✅ No breaking changes
- ✅ Gradual migration path

## Testing
The endpoint now accepts:
- Old format: `permission_type` at top level (e.g., `"can_send_messages"`)
- New format: `permission_type` in `metadata` object (e.g., `"send_messages"`)

Both are mapped to the correct Telegram API field.
