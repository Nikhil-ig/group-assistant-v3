# 🔄 Bot → API V2 Migration Guide

## The Problem

The bot (`bot/main.py`) is trying to call endpoints that don't exist in API V2:
- Old: `/api/actions/execute` 
- Old: `/api/actions/history`
- Old: `/api/advanced/settings/{group_id}/toggle-feature`
- etc.

But API V2 has completely different routes structure:
- New: `/api/v2/groups/{group_id}/enforcement/execute`
- New: `/api/v2/groups/{group_id}/enforcement/ban`
- New: `/api/v2/groups/{group_id}/enforcement/mute`
- New: `/api/v2/groups/{group_id}/enforcement/user/{user_id}/violations`
- etc.

## Solution Overview

We need to **rewrite the bot's `APIv2Client` class** to use the correct API V2 routes instead of the old centralized API routes.

## API V2 Route Structure

### 1. Health Check
```
GET /health → {"status": "healthy", "service": "api-v2", "version": "2.0.0"}
```

### 2. Enforcement Routes (Main Actions)
```
POST /api/v2/groups/{group_id}/enforcement/execute
  - Generic action endpoint

POST /api/v2/groups/{group_id}/enforcement/ban
POST /api/v2/groups/{group_id}/enforcement/unban
POST /api/v2/groups/{group_id}/enforcement/kick
POST /api/v2/groups/{group_id}/enforcement/mute
POST /api/v2/groups/{group_id}/enforcement/unmute
POST /api/v2/groups/{group_id}/enforcement/warn
POST /api/v2/groups/{group_id}/enforcement/promote
POST /api/v2/groups/{group_id}/enforcement/demote
POST /api/v2/groups/{group_id}/enforcement/lockdown
POST /api/v2/groups/{group_id}/enforcement/restrict
POST /api/v2/groups/{group_id}/enforcement/unrestrict

GET /api/v2/groups/{group_id}/enforcement/user/{user_id}/violations
  - Get user enforcement history

GET /api/v2/groups/{group_id}/enforcement/stats
  - Get enforcement statistics
```

### 3. Group Management Routes
```
POST /api/v2/groups
GET /api/v2/groups/{group_id}
PUT /api/v2/groups/{group_id}
GET /api/v2/groups/{group_id}/settings
PUT /api/v2/groups/{group_id}/settings
GET /api/v2/groups/{group_id}/stats
GET /api/v2/groups/{group_id}/users/{user_id}/stats
```

### 4. Advanced Features Routes
```
POST /api/v2/groups/{group_id}/moderation/duplicate-detection
GET /api/v2/groups/{group_id}/moderation/user-profile/{user_id}
GET /api/v2/groups/{group_id}/analytics/health
```

## Required Bot Code Changes

### File: `bot/main.py`

**Location: Lines 111-450 (APIv2Client class)**

The `APIv2Client` class needs to be completely rewritten to use the new routes.

#### Key Changes Needed:

1. **Health Check** (Line 123)
   - ✅ ALREADY FIXED (changed from `/api/health` to `/health`)

2. **execute_action()** (Line 136) - NEEDS REWRITE
   - Old: POST `/api/actions/execute`
   - New: POST `/api/v2/groups/{group_id}/enforcement/execute`
   - Need to extract `group_id` from action_data

3. **get_user_permissions()** (Line 150) - NEEDS REWRITE
   - Old: GET `/api/rbac/users/{user_id}/permissions`
   - New: GET `/api/v2/groups/{group_id}/moderation/user-profile/{user_id}`

4. **All endpoint references** - Need to add `/api/v2` prefix and restructure paths

#### Critical Issue: Group ID Required

**The fundamental change:** API V2 requires `group_id` in all paths!

Old system: `/api/actions/execute` (implicit group context)  
New system: `/api/v2/groups/{group_id}/enforcement/execute` (explicit group_id)

This means:
- ✅ The action_data already includes group_id
- ✅ We just need to extract it and use it in URLs

## Action Data Structure

The bot's `action_data` dict typically includes:
```python
{
    "group_id": 123456789,
    "user_id": 987654321,
    "action_type": "mute",  # or ban, kick, unmute, promote, demote, warn, restrict, unrestrict
    "duration": 3600,  # optional, in seconds
    "reason": "spam",  # optional
    "admin_id": 111111111,  # optional
    # ... other fields
}
```

## Implementation Plan

### Step 1: Update `execute_action()` method
- Extract group_id from action_data
- Extract action_type from action_data
- Route to specific endpoint based on action_type
- Map: `action_type` → endpoint path

Example mapping:
```
"ban" → POST /api/v2/groups/{group_id}/enforcement/ban
"mute" → POST /api/v2/groups/{group_id}/enforcement/mute
"kick" → POST /api/v2/groups/{group_id}/enforcement/kick
"unmute" → POST /api/v2/groups/{group_id}/enforcement/unmute
"unban" → POST /api/v2/groups/{group_id}/enforcement/unban
"warn" → POST /api/v2/groups/{group_id}/enforcement/warn
"promote" → POST /api/v2/groups/{group_id}/enforcement/promote
"demote" → POST /api/v2/groups/{group_id}/enforcement/demote
"restrict" → POST /api/v2/groups/{group_id}/enforcement/restrict
"unrestrict" → POST /api/v2/groups/{group_id}/enforcement/unrestrict
"lockdown" → POST /api/v2/groups/{group_id}/enforcement/lockdown
```

### Step 2: Update other endpoint calls
- `get_group_settings()` → `/api/v2/groups/{group_id}/settings` ✅ (uses group_id)
- `check_duplicate_action()` → `/api/v2/groups/{group_id}/moderation/duplicate-detection`
- `get_user_action_history()` → `/api/v2/groups/{group_id}/enforcement/user/{user_id}/violations`
- etc.

### Step 3: Update all API endpoint references in the bot
- Search for all `/api/` references
- Replace with `/api/v2/` + proper path structure

## Files to Modify

1. **bot/main.py** - CRITICAL (APIv2Client class, all endpoint calls)
2. **bot/.env** - ALREADY CORRECT ✅
3. **bot/.env.example** - ALREADY CORRECT ✅

## Testing After Migration

1. Start API V2 on port 8002
2. Start Bot
3. Check logs for:
   - ✅ "✅ Bot initialized successfully"
   - ✅ "Health check: OK" or similar
4. Test actions:
   - /ban <user>
   - /mute <user>
   - /kick <user>
5. Verify no errors in logs

## Next Steps

The bot client needs significant rewriting to match API V2's new route structure. This is the primary blocker for system operation.

**Recommendation:** Rewrite the `APIv2Client` class to use the correct API V2 endpoints and test the bot connection.
