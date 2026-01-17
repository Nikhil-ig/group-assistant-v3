# Quick Reference - Lockdown Command

## ✅ Status: FULLY WORKING

The `/lockdown` command is now fully functional and ready for use.

## How to Use

### In Telegram
```
/lockdown
```

**Permissions**: Admin-only

**Effect**: Locks down the group - only admins can send messages

### What It Does
1. Prevents all non-admin users from sending messages
2. Restricts all users' permissions in the group
3. Only admins and moderators can continue posting
4. Users can still view the group and read messages
5. The lockdown persists until manually lifted (in future versions)

## Technical Details

### Command Flow
```
/lockdown in chat
    ↓
bot/main.py:cmd_lockdown()
    ↓
Check admin permissions
    ↓
Call API: POST /api/v2/groups/{group_id}/enforcement/lockdown
    ↓
Execute Telegram API: ban_chat_member() + set_chat_permissions()
    ↓
✅ Group locked
```

### API Endpoint
```bash
POST /api/v2/groups/{group_id}/enforcement/lockdown
Query Parameters:
  - initiated_by: int (admin user ID)

Headers:
  - Authorization: Bearer {api_key}
```

### Testing the Endpoint
```bash
curl -X POST "http://localhost:8002/api/v2/groups/123/enforcement/lockdown?initiated_by=456" \
  -H "Authorization: Bearer shared-api-key" \
  -H "Content-Type: application/json" \
  -d '{}'
```

## Related Commands
- `/mute` - Mute a specific user
- `/ban` - Ban a user
- `/kick` - Kick a user
- `/warn` - Warn a user
- `/promote` - Promote a user to admin
- `/demote` - Remove admin from user

## Support
For issues or questions, check the logs:
```bash
tail -f logs/bot.log
tail -f logs/api_v2.log
```

## System Status
All services running:
- ✅ Bot: Actively polling
- ✅ API: Responding to requests  
- ✅ Database: Connected and operational
- ✅ All 23 commands: Registered
