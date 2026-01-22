# 🎯 Quick Start: New Commands & API v2

## What's New? ✨

8 powerful new commands have been added to your bot, all integrated with **API v2**:

1. **CAPTCHA** - Auto-verify new members
2. **AFK** - Set away from keyboard status  
3. **STATS** - Get group/user statistics
4. **BROADCAST** - Send announcements
5. **SLOWMODE** - Limit message frequency
6. **ECHO** - Repeat messages
7. **NOTES** - Manage group notes
8. **VERIFY** - Mark users as verified

---

## 🚀 Running the Bot & API

### Terminal 1: Start API v2
```bash
cd /Users/apple/Documents/Personal/startup/bots/telegram\ bot/python/main_bot_v2/v3
source venv/bin/activate
python -m api_v2.app
```

Expected: `✅ API V2 started successfully on port 8002`

### Terminal 2: Start Bot
```bash
cd /Users/apple/Documents/Personal/startup/bots/telegram\ bot/python/main_bot_v2/v3
source venv/bin/activate
python bot/main.py
```

Expected: `✅ Bot commands registered` + `🤖 Bot is polling for updates...`

---

## 📱 Testing Commands

### 1. CAPTCHA
```
/captcha on medium      ← Enable verification
/captcha off            ← Disable
```

### 2. AFK
```
/afk In a meeting       ← Set status
/afk                    ← Clear status
```

### 3. STATS
```
/stats                  ← Last 7 days
/stats 30d              ← Last 30 days
```

### 4. BROADCAST (Admin)
```
/broadcast Welcome to our group!
```

### 5. SLOWMODE (Admin)
```
/slowmode 5             ← 5 seconds
/slowmode off           ← Disable
```

### 6. ECHO
```
/echo This is important!
```

### 7. NOTES (Admin)
```
/notes                  ← List notes
/notes add Meeting at 3PM
```

### 8. VERIFY (Admin)
```
/verify @username       ← Mark verified
/verify 123456789       ← By ID
```

---

## 🔌 Testing API v2 Endpoints

### Health Check
```bash
curl http://localhost:8002/health
```

### Get Group Stats
```bash
curl -X GET "http://localhost:8002/api/v2/groups/123/stats/group?period=7d"
```

### Broadcast Message
```bash
curl -X POST http://localhost:8002/api/v2/groups/123/broadcast \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": 123,
    "message": "Hello everyone!",
    "parse_mode": "HTML",
    "target": "all"
  }'
```

### Enable Captcha
```bash
curl -X POST http://localhost:8002/api/v2/groups/123/captcha/enable \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": 123,
    "enabled": true,
    "difficulty": "medium",
    "timeout": 300
  }'
```

### Verify User
```bash
curl -X POST http://localhost:8002/api/v2/groups/123/verify \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": 123,
    "user_id": 456,
    "action": "verify",
    "reason": "Active contributor"
  }'
```

---

## 📋 Files Changed/Created

### NEW FILES
✅ `/api_v2/routes/new_commands.py` - All new API endpoints
✅ `00_NEW_COMMANDS_API_V2_COMPLETE.md` - Full documentation

### MODIFIED FILES
✅ `/bot/main.py` - Added 8 new commands + registrations
✅ `/api_v2/app.py` - Registered new routes

---

## 🎨 Features

### Auto-Delete ⏱️
- Commands auto-delete responses after 5-8 seconds
- Keeps chat clean and organized

### Admin Controls 🔐
- Some commands admin-only (broadcast, slowmode, notes, verify, captcha)
- Regular users can use: afk, stats, echo

### Logging 📊
- All commands logged to API for audit trails
- Access via `/groups/{id}/actions` endpoint

### Full API v2 Integration ✅
- Every command has corresponding API endpoints
- Use bot OR API - both work perfectly
- Commands logged and synced via API

---

## ⚙️ Configuration

### Environment Variables (`.env`)
```
TELEGRAM_BOT_TOKEN=your_token_here
API_V2_URL=http://localhost:8002
API_V2_KEY=shared-api-key
MONGODB_URL=mongodb://localhost:27017
PORT=8002
LOG_LEVEL=INFO
```

### Database
- Commands use MongoDB collections
- All data automatically persisted
- No manual setup needed

---

## 🔍 Checking Logs

### Bot Logs
```bash
tail -f logs/bot.log
```

### API Logs
```bash
tail -f logs/api_v2.log
```

### Errors
```bash
grep ERROR logs/*.log
```

---

## 📊 Database Collections

Commands store data in:
- `actions` - All command executions
- `groups` - Group settings
- `users` - User status & verification
- `notes` - Saved notes
- `broadcasts` - Announcement history

Query examples:
```bash
# MongoDB
db.actions.find({"action_type": "broadcast"})
db.users.find({"verified": true})
db.notes.find({"group_id": 123})
```

---

## ✅ Verification Checklist

After starting both services, verify:

- [ ] API health check returns `200 OK`
- [ ] Bot shows commands registered message
- [ ] `/help` shows all commands
- [ ] `/stats` returns data
- [ ] `/captcha on medium` responds
- [ ] `/broadcast test` works (admin group)
- [ ] `/slowmode 5` responds
- [ ] `/notes` lists notes (if any)
- [ ] `/verify @username` works (admin)
- [ ] All responses auto-delete after ~6 seconds

---

## 🛠️ Troubleshooting

### API won't start
```bash
# Check MongoDB
mongosh
> db.runCommand({ping: 1})

# Check port
lsof -i :8002
```

### Bot won't connect
```bash
# Verify token
echo $TELEGRAM_BOT_TOKEN

# Check API is running
curl http://localhost:8002/health
```

### Commands not working
1. Verify bot is in group (not private chat)
2. Check user is admin (for admin commands)
3. Check logs for errors: `tail -f logs/bot.log`
4. Test API directly: `curl http://localhost:8002/api/v2/groups/ID/stats/group`

---

## 📚 Full Documentation

See `00_NEW_COMMANDS_API_V2_COMPLETE.md` for:
- Complete endpoint specifications
- Request/response models
- Usage examples
- Field descriptions
- Error handling
- Future enhancements

---

## 🚀 Next Steps

1. ✅ Start API v2: `python -m api_v2.app`
2. ✅ Start Bot: `python bot/main.py`
3. ✅ Test a command: `/stats`
4. ✅ Test API: `curl http://localhost:8002/health`
5. ✅ Read full docs: `00_NEW_COMMANDS_API_V2_COMPLETE.md`

---

**Status:** ✅ Ready to Deploy
**Total New Commands:** 8
**Total New Endpoints:** 25+
**API Version:** 2.0.0

Enjoy your enhanced bot! 🎉
