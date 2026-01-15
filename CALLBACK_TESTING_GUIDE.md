# Callback Testing Guide

## Quick Start

### Prerequisites
1. Bot running with latest `main.py`
2. Centralized API running at configured URL
3. MongoDB with test group data
4. Test group with bot as admin

### Test Group Setup
```bash
# Use your test Telegram group ID
GROUP_ID=-1001234567890  # Replace with your group
ADMIN_USER_ID=123456789  # Your user ID
REGULAR_USER_ID=987654321  # Non-admin user ID
```

## Test Scenarios

### Scenario 1: Settings Callbacks

#### Test 1.1 - Open Settings UI
**Command:** `/settings` (from admin in group)
**Expected:**
- ✅ Message shows all toggle buttons
- ✅ Each toggle shows current state (✅ or ❌)
- ✅ "Edit Template" button visible
- ✅ "Close" button visible

**Verify:**
```
Check message contains:
- Auto-delete Commands: ✅/❌
- Auto-delete Welcome: ✅/❌
- Join/Leave Notifications: ✅/❌
- Edit Templates: [BUTTON]
```

#### Test 1.2 - Toggle Feature
**Action:** Click toggle button (e.g., "Auto-delete Commands")
**Expected:**
- ✅ Button state changes immediately
- ✅ Settings UI refreshes
- ✅ Previous state flipped to new state
- ✅ Success notification shows

**Verify:**
```python
# Check API was called
curl http://localhost:8001/api/advanced/settings/GROUP_ID \
  -H "Authorization: Bearer API_KEY" | jq '.data.features_enabled.auto_delete_commands'
# Should show toggled value
```

#### Test 1.3 - Edit Template
**Action:** Click "Edit Welcome Template" button
**Expected:**
- ✅ Bot sends prompt: "Send your custom welcome message"
- ✅ Shows template variables: {group_name}, {username}, {user_id}
- ✅ Awaits admin response

**Verify:**
```
Prompt message should contain:
📝 Send your custom welcome message
Variables: {group_name}, {username}, {user_id}
```

**Next Step:** Send custom message, e.g.:
```
Welcome to {group_name}! 👋
User: {username} (ID: {user_id})
```

**Expected After Message:**
- ✅ Template saved to database
- ✅ Settings UI shows new template preview
- ✅ Confirmation message sent

### Scenario 2: Action Callbacks

#### Test 2.1 - Ban User
**Prerequisite:** Action buttons visible in message

**Action:** Click "Ban" button on user action message
**Expected:**
- ✅ Admin permission verified
- ✅ User banned via API
- ✅ Message shows: "🔨 ACTION COMPLETED - User banned"
- ✅ New action buttons appear (Unban, Kick, Warn)
- ✅ Action logged to database

**Verify:**
```bash
# Check action was executed
curl http://localhost:8001/api/advanced/history/GROUP_ID \
  -H "Authorization: Bearer API_KEY" | jq '.data[] | select(.action=="ban")'
```

#### Test 2.2 - Permission Denied
**Setup:** Regular (non-admin) user

**Action:** Click action button as non-admin
**Expected:**
- ✅ Alert: "❌ You need admin permissions for this action"
- ✅ No API call executed
- ✅ Message not modified

**Verify:**
```
Toast/Alert should show:
❌ You need admin permissions for this action
```

#### Test 2.3 - Action Error Handling
**Setup:** User already banned or action fails

**Action:** Click action button when action cannot complete
**Expected:**
- ✅ Alert: "❌ [Action] failed!"
- ✅ Error details shown in message
- ✅ Original buttons remain available

**Verify:**
```
Error message format:
⚠️ ACTION FAILED
Action: BAN
Error: User is admin / User already banned
Please check permissions or try again
```

### Scenario 3: Permission Checks on Commands

#### Test 3.1 - Admin Permission Check
**Command:** `/mute @user` (from regular user)
**Expected:**
- ✅ Message: "❌ You need admin permissions for this action"
- ✅ Auto-deleted after 5 seconds
- ✅ No action executed

#### Test 3.2 - All Moderation Commands Protected
**Test each command** as non-admin:
- `/mute @user` → Permission denied
- `/unmute @user` → Permission denied
- `/ban @user` → Permission denied
- `/kick @user` → Permission denied
- `/promote @user` → Permission denied
- `/demote @user` → Permission denied
- `/warn @user` → Permission denied
- `/restrict @user` → Permission denied
- `/unrestrict @user` → Permission denied
- `/pin` → Permission denied
- `/unpin` → Permission denied
- `/lockdown` → Permission denied
- `/purge @user` → Permission denied
- `/setrole @user moderator` → Permission denied
- `/removerole @user moderator` → Permission denied

**Expected:** All show "❌ You need admin permissions for this action"

### Scenario 4: Cache Behavior

#### Test 4.1 - Settings Cache
**Action Sequence:**
1. Admin clicks toggle → state changes
2. Admin clicks same toggle → state changes back
3. Measure response time

**Expected:**
- ✅ First click: ~500-1000ms (API call)
- ✅ Immediate refresh: <100ms (from cache)
- ✅ After 30s timeout: ~500-1000ms (new API call)

#### Test 4.2 - Cache Invalidation
**Action Sequence:**
1. Get settings via API → returns state A
2. Toggle setting via callback → state becomes B
3. Get settings via API → returns state B (not A)

**Expected:**
- ✅ Cache invalidated after toggle
- ✅ Fresh data returned from API
- ✅ No stale cache hits

## API Testing with curl

### Test Settings Endpoint
```bash
# Get current settings
curl http://localhost:8001/api/advanced/settings/GROUP_ID \
  -H "Authorization: Bearer API_KEY" | jq

# Expected response:
{
  "success": true,
  "data": {
    "group_id": GROUP_ID,
    "group_name": "Test Group",
    "features_enabled": {
      "auto_delete_commands": true,
      "auto_delete_welcome": false,
      ...
    },
    "welcome_message": "Welcome to {group_name}!",
    "left_message": "Goodbye!",
    ...
  }
}
```

### Test Toggle Feature
```bash
# Toggle a feature
curl -X POST http://localhost:8001/api/advanced/settings/GROUP_ID/toggle-feature \
  -H "Authorization: Bearer API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"feature":"auto_delete_commands","enabled":true}' | jq

# Expected: 200 OK with updated settings
```

### Test Update Settings
```bash
# Update multiple settings
curl -X POST http://localhost:8001/api/advanced/settings/GROUP_ID/update \
  -H "Authorization: Bearer API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "welcome_message":"New welcome!",
    "left_message":"Goodbye!",
    "features_enabled":{"auto_delete_commands":false}
  }' | jq

# Expected: 200 OK with updated data
```

### Test Action Execution
```bash
# Execute action via API
curl -X POST http://localhost:8001/api/actions/execute \
  -H "Authorization: Bearer API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "action_type":"ban",
    "group_id":GROUP_ID,
    "user_id":TARGET_USER_ID,
    "initiated_by":ADMIN_USER_ID
  }' | jq

# Expected: 200 OK with action result
```

## Logging & Debugging

### Check Bot Logs
```bash
# View recent bot logs
tail -f /path/to/logs/bot/bot.log

# Look for:
# - "Settings callbacks" entries
# - "Executing action" entries
# - "Permission check" entries
# - Any exception traces
```

### Check API Logs
```bash
# View API logs
tail -f /path/to/logs/api/api.log

# Look for:
# - POST /api/advanced/settings/.../toggle-feature
# - POST /api/advanced/settings/.../update
# - POST /api/actions/execute
# - Any 4xx/5xx errors
```

### Enable Debug Logging
```bash
# Set log level to DEBUG
export LOG_LEVEL=DEBUG

# Restart bot:
# Bot will now log all callback data, permission checks, API calls
```

## Common Issues & Troubleshooting

### Issue 1: "Invalid callback data"
**Symptom:** Alert shows "Invalid callback data format"
**Cause:** Callback data parsing failed
**Debug:**
```
Check logs for:
- Callback data format
- Parse error details
- Data validation failure
```
**Solution:**
- Verify callback data format matches pattern
- Check button generation code
- Restart bot

### Issue 2: "You need admin permissions" (but you ARE admin)
**Symptom:** Admin sees permission denied message
**Cause:** `check_is_admin()` returned false
**Debug:**
```bash
# Check admin status in Telegram
# Check admin status in centralized API
curl http://localhost:8001/api/advanced/admins/GROUP_ID \
  -H "Authorization: Bearer API_KEY" | jq
```
**Solution:**
- Verify user_id matches actual user ID
- Check centralized API has user as admin
- Sync admins list: `/admins sync`

### Issue 3: Callback not responding
**Symptom:** Click button, no alert or UI change
**Cause:** Callback handler not called or errored
**Debug:**
```bash
# Check handler is registered
grep "register.*on.*" bot/main.py

# Check logs for exceptions
tail -f logs/bot/bot.log | grep "Traceback"
```
**Solution:**
- Verify callback handler registered
- Check dispatcher configuration
- Restart bot with fresh dispatcher

### Issue 4: Settings not persisting
**Symptom:** Toggle setting, but reverts after bot restart
**Cause:** MongoDB not saving or connection lost
**Debug:**
```bash
# Check MongoDB connection
mongo --host MONGO_HOST --port MONGO_PORT --authenticationDatabase admin -u user -p password

# Check collection:
db.group_settings.findOne({group_id: GROUP_ID})
```
**Solution:**
- Verify MongoDB running
- Check connection string
- Verify database permissions

## Performance Benchmarks

### Expected Response Times
| Operation | Time | Notes |
|-----------|------|-------|
| Toggle setting (cached) | <100ms | From cache |
| Toggle setting (new) | 500-1000ms | API call |
| Action execution | 1000-2000ms | Includes API + permission check |
| Settings UI render | 200-500ms | Build UI from cached data |
| Error response | <100ms | Immediate alert |

### Load Testing
```bash
# Simulate rapid callbacks
for i in {1..100}; do
  curl http://localhost:8001/api/advanced/settings/GROUP_ID \
    -H "Authorization: Bearer API_KEY" &
done
wait

# Expected: All requests complete <5 seconds
```

## Checklist for Production Deployment

- [ ] All 15 moderation commands have permission checks
- [ ] All 3 callback handlers implemented and tested
- [ ] API endpoints returning 200 OK
- [ ] Settings persist in MongoDB
- [ ] Cache invalidation working
- [ ] Logs show no errors
- [ ] Bot responds to all commands
- [ ] All callbacks execute without hanging
- [ ] Non-admins cannot execute moderation actions
- [ ] Error messages display correctly
- [ ] No memory leaks (monitor RAM usage)
- [ ] Background refresh loop running
- [ ] Template editing works end-to-end
- [ ] Action buttons appear and respond

## Contact & Support

For issues with callback implementation:
1. Check logs for error details
2. Verify API is running and accessible
3. Check MongoDB connection
4. Verify environment variables set correctly
5. Restart bot and test again

If issues persist, gather:
- Bot logs (last 100 lines)
- API logs (last 100 lines)
- MongoDB query output
- Exact steps to reproduce issue
