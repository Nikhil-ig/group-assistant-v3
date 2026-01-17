# 🚀 Test Bot Now - Quick Guide

## Current Status
✅ API V2 is running on port 8002
✅ All enforcement endpoints available
✅ Bot is configured to communicate with API
⏳ Ready for Telegram bot testing

## Quick Test Steps

### 1. Start the Bot (if not already running)
```bash
cd "/Users/apple/Documents/Personal/startup/bots/telegram bot/python/main_bot_v2/v3"
python bot/main.py
```

### 2. In Telegram, send commands to your bot:
```
/start                 # Should connect successfully
/ban @username         # Should trigger ban endpoint
/kick @username        # Should trigger kick endpoint
/mute @username        # Should trigger mute endpoint
/warn @username spam   # Should trigger warn endpoint
```

### 3. Monitor bot logs for success messages
Look for lines showing:
- API requests being made to `http://localhost:8002`
- Successful responses from enforcement endpoints
- No "connection attempts failed" errors

### 4. If everything works:
- ✅ Bot receives command
- ✅ Bot calls API endpoint
- ✅ API returns successful response
- ✅ Bot acknowledges user

## Expected Log Output

When you send `/ban @user` to the bot, you should see:

**Bot logs:**
```
INFO: Executing action: ban for user 123 in group 456
INFO: API Call: POST /api/v2/groups/456/enforcement/ban
INFO: Response: {success: true, message: "User banned"}
```

**API logs:**
```
INFO: POST /api/v2/groups/123/enforcement/ban HTTP/1.1 200 OK
```

## Troubleshooting

### If bot says "All connection attempts failed"
- Check if API is still running: `curl http://localhost:8002/health`
- Check if bot has correct API_V2_URL in .env
- Restart bot with: `pkill -f "python bot/main.py" && python bot/main.py`

### If endpoint returns 404
- API router not loaded - restart API: `pkill -f uvicorn` then restart
- Check: `curl http://localhost:8002/api/v2/groups/123/enforcement/ban` returns endpoint

### If timeout errors
- Increase timeout in bot/main.py if needed
- Check network connectivity: `curl -v http://localhost:8002/health`

## Available Test Endpoints

All these should work now:

```bash
# Test ban
curl -X POST http://localhost:8002/api/v2/groups/123/enforcement/ban \
  -H "Content-Type: application/json" \
  -d '{"user_id": 456, "reason": "test"}'

# Test mute
curl -X POST http://localhost:8002/api/v2/groups/123/enforcement/mute \
  -H "Content-Type: application/json" \
  -d '{"user_id": 456, "duration": 3600}'

# Test kick
curl -X POST http://localhost:8002/api/v2/groups/123/enforcement/kick \
  -H "Content-Type: application/json" \
  -d '{"user_id": 456}'
```

## Success Indicators

✅ All of these indicate success:
- Bot responds to /start with welcome message
- Bot receives action commands (/ban, /kick, /mute)
- API endpoint URLs show in bot logs
- API returns JSON with success:true
- User sees confirmation messages in Telegram

## Next Actions

After confirming bot works:
1. Test all action types (ban, kick, mute, warn, promote, demote, etc.)
2. Verify action parameters are correct
3. Monitor for any edge cases or errors
4. Log results for documentation

---

**Status**: Ready for testing
**Date**: 2026-01-15
**API Port**: 8002
**Bot State**: Configured and waiting for commands
