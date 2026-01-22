# 🧪 Quick Test Guide

## Test Case 1: Bot Self-Protection
**Command:** `/restrict @YourBotName`
**Expected:** ❌ Cannot restrict the bot itself!
**Status:** ✅ PASS / ❌ FAIL

---

## Test Case 2: Message Length Fix
**Command:** `/restrict @username` (in group)
**Expected:** 
```
🔐 PERMISSIONS
User: [ID]

State:
📝 🔒 🎨 🔒 🎤 🔒

Click buttons to toggle
```
**Status:** ✅ PASS / ❌ FAIL

---

## Test Case 3: Permission Toggle Works
**Steps:**
1. `/restrict @username`
2. Click "📝 Text: 🔓 Free" button
3. Wait for response

**Expected:** User's text permission toggled successfully
**Status:** ✅ PASS / ❌ FAIL

---

## Test Case 4: Unrestrict Protection
**Command:** `/unrestrict @YourBotName`
**Expected:** ❌ Cannot modify permissions for the bot itself!
**Status:** ✅ PASS / ❌ FAIL

---

## Test Case 5: Normal Restrict Works
**Command:** `/restrict @regularuser` (reply or direct)
**Expected:** Permission toggle interface displays
**Status:** ✅ PASS / ❌ FAIL

---

## Test Case 6: API Direct Bot Check
**Test:** Call API directly with bot ID
```bash
curl -X POST http://localhost:8002/api/v2/groups/-1003447608920/enforcement/mute \
  -H "Content-Type: application/json" \
  -d '{"user_id": 8276429151}' \
  -H "Authorization: Bearer shared-api-key"
```

**Expected:** 
```json
{
  "statusCode": 400,
  "detail": "Cannot mute the bot itself"
}
```
**Status:** ✅ PASS / ❌ FAIL

---

## Quick Validation Script

```bash
#!/bin/bash

echo "🧪 Testing Bot Self-Protection Fixes..."
echo ""

# Check if bot is running
echo "1. Checking bot service..."
if ps aux | grep -q "[m]ain.py"; then
    echo "   ✅ Bot running"
else
    echo "   ❌ Bot not running"
    exit 1
fi

# Check if API is running
echo "2. Checking API v2..."
if lsof -i :8002 > /dev/null 2>&1; then
    echo "   ✅ API running on port 8002"
else
    echo "   ❌ API not running on port 8002"
    exit 1
fi

# Check logs for errors
echo "3. Checking recent logs..."
if tail -50 bot.log | grep -q "restrict command failed\|mute.*bot"; then
    echo "   ⚠️  Recent errors detected - check logs"
else
    echo "   ✅ No recent errors"
fi

echo ""
echo "✅ Pre-flight checks complete!"
echo "Ready to test in Telegram group"
```

---

## Command Reference

| Command | Usage | Expected |
|---|---|---|
| `/restrict @user` | Toggle user permissions | Compact permission menu |
| `/restrict [reply]` | Reply to restrict user | Compact permission menu |
| `/unrestrict @user` | Unrestrict user | Compact permission menu |
| `/restrict @bot` | Try to restrict bot | Friendly error message |
| `/mute @bot` | Try to mute bot | API returns 400 error |

---

## Logs to Monitor

**Success Indicators:**
```
INFO - Restrict command: permission toggles displayed
INFO - HTTP Request: POST .../restrict HTTP/1.1 200 OK
```

**Error Indicators (Expected):**
```
INFO - Cannot restrict the bot itself!
400 Bad Request: Cannot mute the bot itself
```

**Problem Indicators:**
```
ERROR - Restrict command failed: MESSAGE_TOO_LONG
ERROR - Telegram server says - Bad Request
500 Internal Server Error
```

---

## Rollback (if needed)

If issues occur:

```bash
# Restore from git
git checkout bot/main.py
git checkout api_v2/routes/enforcement_endpoints.py

# Restart
./start_all_services.sh
```

---

## Questions?

- Check `00_COMPLETE_FIXES_SUMMARY.md` for full details
- Check `00_BOT_SELF_PROTECTION_FIX.md` for bot protection specifics  
- Check `00_MESSAGE_LENGTH_FIX.md` for message optimization details
