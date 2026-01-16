# Telegram Bot v3 - New Features Expansion Plan

**Date**: 2026-01-16  
**Status**: Ready for Implementation

---

## PHASE 1: NEW BOT COMMANDS (10 Commands)

### 1. `/spam` - Mark message as spam
```
Usage: /spam (reply to message)
Purpose: Report spam, trigger auto-delete
API: POST /api/v2/groups/{group_id}/moderation/report-spam
```

### 2. `/slowmode` - Enable/disable slow mode
```
Usage: /slowmode [seconds]
Purpose: Limit message frequency (0 to disable)
API: POST /api/v2/groups/{group_id}/settings/slowmode
```

### 3. `/welcome` - Configure welcome message
```
Usage: /welcome set "Welcome message" or /welcome show
Purpose: Auto-welcome new members
API: POST /api/v2/groups/{group_id}/settings/welcome
```

### 4. `/autorole` - Auto-assign roles to new members
```
Usage: /autorole set member or /autorole show
Purpose: Auto-grant role to joined users
API: POST /api/v2/groups/{group_id}/settings/autorole
```

### 5. `/filter` - Add word filter
```
Usage: /filter add "badword" or /filter list
Purpose: Auto-delete messages with filtered words
API: POST /api/v2/groups/{group_id}/moderation/filters
```

### 6. `/meme` - Get random meme
```
Usage: /meme
Purpose: Fun feature - fetch from API
API: POST /api/v2/entertainment/meme
```

### 7. `/quote` - Get random quote
```
Usage: /quote [category]
Purpose: Fun feature - daily quotes
API: POST /api/v2/entertainment/quote
```

### 8. `/stats` - User/group statistics
```
Usage: /stats or /stats @username
Purpose: Show activity statistics
API: GET /api/v2/groups/{group_id}/stats
```

### 9. `/remind` - Set reminder
```
Usage: /remind "text" 1h
Purpose: Schedule reminders
API: POST /api/v2/reminders/create
```

### 10. `/poll` - Create poll
```
Usage: /poll "Question?" "Option 1" "Option 2" ...
Purpose: Create interactive polls
API: POST /api/v2/groups/{group_id}/polls
```

---

## PHASE 2: NEW API ENDPOINTS (15 Endpoints)

### Moderation Endpoints
- `POST /api/v2/groups/{group_id}/moderation/report-spam` - Report spam
- `POST /api/v2/groups/{group_id}/moderation/filters` - Manage word filters
- `GET /api/v2/groups/{group_id}/moderation/filters` - List filters
- `DELETE /api/v2/groups/{group_id}/moderation/filters/{filter_id}` - Delete filter

### Settings Endpoints
- `POST /api/v2/groups/{group_id}/settings/slowmode` - Set slowmode
- `POST /api/v2/groups/{group_id}/settings/welcome` - Configure welcome
- `GET /api/v2/groups/{group_id}/settings/welcome` - Get welcome settings
- `POST /api/v2/groups/{group_id}/settings/autorole` - Set auto-role

### Statistics Endpoints
- `GET /api/v2/groups/{group_id}/stats` - Group statistics
- `GET /api/v2/users/{user_id}/stats` - User statistics
- `GET /api/v2/groups/{group_id}/stats/messages` - Message statistics
- `GET /api/v2/groups/{group_id}/stats/leaderboard` - User leaderboard

### Entertainment Endpoints
- `GET /api/v2/entertainment/meme` - Get random meme
- `GET /api/v2/entertainment/quote` - Get random quote

### Reminders & Polls
- `POST /api/v2/reminders/create` - Create reminder
- `GET /api/v2/reminders/list` - List reminders
- `POST /api/v2/groups/{group_id}/polls` - Create poll

---

## PHASE 3: ADVANCED FEATURES

### 1. Auto-Moderation System
- Auto-delete spam based on patterns
- Automatic mute escalation
- Smart profanity detection
- Link filtering (configurable)
- Duplicate message detection

### 2. Analytics Dashboard
- Message frequency graphs
- User activity tracking
- Top spammers report
- Command usage statistics
- Admin action logs

### 3. Role-Based Access Control (RBAC)
- Define custom roles
- Assign permissions per role
- Hierarchy system
- Permission inheritance

### 4. Auto-Response System
- Keyword-based responses
- FAQ automation
- Greeting templates
- Custom reactions

### 5. Backup & Restoration
- Export chat logs
- Backup group settings
- Restore from backup
- Message archiving

---

## IMPLEMENTATION PRIORITY

### Week 1 (High Priority)
1. `/stats` - User/group statistics
2. `/filter` - Word filtering
3. `/slowmode` - Slow mode
4. Stats API endpoints
5. Filter management API

### Week 2 (Medium Priority)
1. `/welcome` - Welcome messages
2. `/autorole` - Auto-role assignment
3. `/remind` - Reminders
4. `/poll` - Polls
5. Entertainment APIs

### Week 3 (Nice to Have)
1. `/meme` and `/quote` - Fun features
2. `/spam` - Spam reporting
3. Analytics dashboard
4. Auto-moderation system
5. Backup/restore functionality

---

## TECHNICAL DETAILS

### Database Schema Updates Needed
- `word_filters` table
- `group_settings` table (expanded)
- `user_statistics` table
- `reminders` table
- `polls` table
- `poll_votes` table

### New Dependencies
- `aioscheduler` - For reminders/scheduling
- `APScheduler` - For background tasks
- `requests` - For external APIs (memes, quotes)

### Architecture
- New module: `api_v2/routes/moderation_advanced.py`
- New module: `api_v2/routes/analytics.py`
- New module: `api_v2/routes/entertainment.py`
- New module: `bot/handlers/fun_commands.py`
- New module: `bot/handlers/utility_commands.py`

---

## ESTIMATED EFFORT

| Feature | API Endpoints | Bot Commands | Complexity | Est. Hours |
|---------|---------------|--------------|-----------|-----------|
| Statistics | 4 | 1 | Medium | 8 |
| Filters | 4 | 1 | Medium | 6 |
| Slowmode | 1 | 1 | Low | 3 |
| Welcome | 2 | 1 | Low | 4 |
| Auto-role | 1 | 1 | Low | 3 |
| Reminders | 3 | 1 | Medium | 8 |
| Polls | 2 | 1 | Medium | 7 |
| Entertainment | 2 | 2 | Low | 4 |
| Spam Reporting | 1 | 1 | Low | 3 |
| **TOTAL** | **20** | **10** | - | **46 hours** |

---

## SUCCESS CRITERIA

After implementation, your bot will have:
- ✅ 30+ commands (vs current 20)
- ✅ 35+ API endpoints (vs current 15)
- ✅ Real-time statistics and analytics
- ✅ Advanced auto-moderation
- ✅ User engagement features (polls, reminders)
- ✅ Fun entertainment commands
- ✅ Comprehensive logging
- ✅ RBAC system
- ✅ Backup/restore capability

---

## NEXT STEPS

1. Start with Phase 1 Priority:
   - Implement `/stats` command
   - Implement stats API endpoints
   - Implement `/filter` command
   - Implement filter management API

2. Then move to Phase 2:
   - Implement other high-priority commands
   - Build supporting API endpoints

3. Finally Phase 3:
   - Advanced features and polish
   - Dashboard and analytics

