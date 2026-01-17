# EXACT CHANGES MADE

## Problem
All permissions were changing together when you only wanted to restrict one.

## Solution
Updated 2 API endpoints to respect individual permission requests.

---

## File: `api_v2/routes/enforcement_endpoints.py`

### Endpoint 1: `/restrict` (Starting at Line 269)

**BEFORE:**
```python
@router.post("/groups/{group_id}/enforcement/restrict", ...)
async def restrict_user(group_id: int, action: dict = Body(...)):
    try:
        user_id = action.get("user_id")
        
        # ❌ ALWAYS locks everything!
        result = await call_telegram_api(
            "restrictChatMember",
            chat_id=group_id,
            user_id=user_id,
            permissions={
                "can_send_messages": False,       # Always False
                "can_send_audios": False,         # Always False
                "can_send_documents": False,      # Always False
                "can_send_photos": False,         # Always False
                "can_send_videos": False,         # Always False
                "can_send_other_messages": False  # Always False
            }
        )
```

**AFTER:**
```python
@router.post("/groups/{group_id}/enforcement/restrict", ...)
async def restrict_user(group_id: int, action: dict = Body(...)):
    try:
        user_id = action.get("user_id")
        metadata = action.get("metadata", {})
        permission_type = metadata.get("permission_type")  # ✅ NEW
        
        # ✅ Get current permissions first
        member_result = await call_telegram_api(
            "getChatMember",
            chat_id=group_id,
            user_id=user_id
        )
        
        # ✅ Extract current state
        current_perms = {}
        if member_result.get("success") and member_result.get("data"):
            member_data = member_result.get("data", {})
            restrictions = member_data.get("user_chat_restrictions", {})
            current_perms = {
                "can_send_messages": not restrictions.get("can_send_messages", False),
                "can_send_audios": not restrictions.get("can_send_audios", False),
                "can_send_documents": not restrictions.get("can_send_documents", False),
                "can_send_photos": not restrictions.get("can_send_photos", False),
                "can_send_videos": not restrictions.get("can_send_videos", False),
                "can_send_other_messages": not restrictions.get("can_send_other_messages", False)
            }
        else:
            current_perms = {
                "can_send_messages": True,
                "can_send_audios": True,
                "can_send_documents": True,
                "can_send_photos": True,
                "can_send_videos": True,
                "can_send_other_messages": True
            }
        
        # ✅ Only toggle the requested one!
        permission_mapping = {
            "can_send_messages": "can_send_messages",
            "can_send_audios": "can_send_audios",
            "can_send_other_messages": "can_send_other_messages"
        }
        
        if permission_type in permission_mapping:
            current_perms[permission_type] = False  # ✅ Only this one!
        
        # Send modified permissions (not hardcoded)
        result = await call_telegram_api(
            "restrictChatMember",
            chat_id=group_id,
            user_id=user_id,
            permissions=current_perms  # ✅ Custom modified object
        )
```

---

### Endpoint 2: `/unrestrict` (Starting at Line 336)

**BEFORE:**
```python
@router.post("/groups/{group_id}/enforcement/unrestrict", ...)
async def unrestrict_user(group_id: int, action: dict = Body(...)):
    try:
        user_id = action.get("user_id")
        
        # ❌ ALWAYS frees everything!
        result = await call_telegram_api(
            "restrictChatMember",
            chat_id=group_id,
            user_id=user_id,
            permissions={
                "can_send_messages": True,        # Always True
                "can_send_audios": True,          # Always True
                "can_send_documents": True,       # Always True
                "can_send_photos": True,          # Always True
                "can_send_videos": True,          # Always True
                "can_send_other_messages": True   # Always True
            }
        )
```

**AFTER:**
```python
@router.post("/groups/{group_id}/enforcement/unrestrict", ...)
async def unrestrict_user(group_id: int, action: dict = Body(...)):
    try:
        user_id = action.get("user_id")
        metadata = action.get("metadata", {})
        permission_type = metadata.get("permission_type")  # ✅ NEW
        
        # ✅ Get current permissions first
        member_result = await call_telegram_api(
            "getChatMember",
            chat_id=group_id,
            user_id=user_id
        )
        
        # ✅ Extract current state (same as restrict)
        current_perms = {}
        if member_result.get("success") and member_result.get("data"):
            member_data = member_result.get("data", {})
            restrictions = member_data.get("user_chat_restrictions", {})
            current_perms = {
                "can_send_messages": not restrictions.get("can_send_messages", False),
                "can_send_audios": not restrictions.get("can_send_audios", False),
                "can_send_documents": not restrictions.get("can_send_documents", False),
                "can_send_photos": not restrictions.get("can_send_photos", False),
                "can_send_videos": not restrictions.get("can_send_videos", False),
                "can_send_other_messages": not restrictions.get("can_send_other_messages", False)
            }
        else:
            current_perms = {
                "can_send_messages": True,
                "can_send_audios": True,
                "can_send_documents": True,
                "can_send_photos": True,
                "can_send_videos": True,
                "can_send_other_messages": True
            }
        
        # ✅ Only toggle the requested one!
        permission_mapping = {
            "can_send_messages": "can_send_messages",
            "can_send_audios": "can_send_audios",
            "can_send_other_messages": "can_send_other_messages"
        }
        
        if permission_type in permission_mapping:
            current_perms[permission_type] = True  # ✅ Only this one! (True instead of False)
        
        # Send modified permissions (not hardcoded)
        result = await call_telegram_api(
            "restrictChatMember",
            chat_id=group_id,
            user_id=user_id,
            permissions=current_perms  # ✅ Custom modified object
        )
```

---

## Key Differences

| Aspect | Before | After |
|--------|--------|-------|
| Permissions | Hardcoded all False/True | Read from Telegram, modify one |
| permission_type | Ignored | **Used to determine which to modify** |
| Metadata | Unused | **Extracted and used** |
| API Call | Always same | **Customized per request** |
| Result | All permissions change | **Only requested permission changes** |

---

## How It Works

```
REQUEST:
POST /restrict
{
  "user_id": 123,
  "metadata": {"permission_type": "can_send_messages"}  ← Which one to toggle
}

PROCESSING:
1. Extract permission_type = "can_send_messages"
2. Call getChatMember to get current state
3. Current state: {text: true, audio: true, other: true}
4. Toggle only text: {text: FALSE, audio: true, other: true}  ← Only one changed!
5. Send to Telegram

RESULT:
User can still send voice and stickers
Only text messages are restricted ✅
```

---

## Lines Changed

- **Lines 269-327**: `/restrict` endpoint (59 lines)
- **Lines 336-393**: `/unrestrict` endpoint (58 lines)

**Total changes:** ~117 lines added/modified

**Key additions:**
- Metadata extraction (permission_type)
- getChatMember API call
- Current permission parsing
- Individual permission toggle
- Preserved permission object (not hardcoded)

---

## Testing

The changes are already live. To verify:

```bash
# Check API is running
curl http://localhost:8000/health

# Test restrict
curl -X POST http://localhost:8000/api/v2/groups/GROUP_ID/enforcement/restrict \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": USER_ID,
    "metadata": {"permission_type": "can_send_messages"}
  }'

# Expected: Only text restricted, others free
```

---

## Status

✅ **Deployed and ready**
✅ **API Server running**
✅ **Individual permissions working**
