# Troubleshooting Guide: Phase 4

## Common Issues & Solutions

### Issue 1: Duplicate Actions Still Possible

**Symptoms**:
- User can be banned twice
- User can be muted multiple times
- "Already Banned" alert not showing

**Root Causes & Solutions**:

1. **Status check not being called**
   ```bash
   # Check logs for status check calls
   tail -f logs/bot/bot.log | grep "check_user_current_status"
   
   # Should see: "Checking status for user X, action Y"
   # If nothing, code not executing
   ```
   
   **Fix**: Verify `check_user_current_status()` call exists in callback handler
   ```python
   # Search for this in main.py around line 2456
   status_check = await check_user_current_status(...)
   ```

2. **Stats not fetching correctly**
   ```bash
   # Check if user stats are accessible
   curl "http://api:8000/api/actions/user-stats?user_id=123&group_id=-100"
   
   # Should return 200 OK with stats object
   ```
   
   **Fix**: Verify API is running and accessible

3. **current_ban/mute/restrict flags not set**
   ```bash
   # Check database directly
   docker-compose exec mongodb mongosh
   > use telegram_bot
   > db.actions.findOne({user_id: 123, group_id: -100})
   
   # Check if actions exist for this user
   ```
   
   **Fix**: Verify actions were logged to database

---

### Issue 2: Admin Mention Not Showing in Reply

**Symptoms**:
- Reply message sends but no mention
- Admin name shows as plain text (not clickable)
- User mention missing

**Root Causes & Solutions**:

1. **ParseMode.HTML not set**
   ```python
   # Check this line in callback handler (around 2550)
   await bot.send_message(
       ...,
       parse_mode=ParseMode.HTML,  # ← MUST BE HERE
   )
   ```
   
   **Fix**: Add or verify `parse_mode=ParseMode.HTML`

2. **Mention HTML format incorrect**
   ```python
   # ✅ CORRECT format:
   f"<a href=\"tg://user?id={user_id}\">👤 Name</a>"
   
   # ❌ WRONG formats:
   f"<a href='tg://user?id={user_id}'>Name</a>"  # Wrong quotes
   f"<a href=tg://user?id={user_id}>Name</a>"    # Missing quotes
   f"[@user](tg://user?id={user_id})"            # Markdown (wrong)
   ```
   
   **Fix**: Use exact format with double quotes

3. **Reply message not sending at all**
   ```bash
   # Check logs for send_message errors
   tail -f logs/bot/bot.log | grep "send_message"
   
   # Common errors:
   # - Chat not found (check group_id)
   # - Message not found (check message_id)
   # - Permission denied (bot not admin)
   ```
   
   **Fix**: Verify:
   - `group_id` is correct (negative number)
   - `reply_to_message_id` points to real message
   - Bot is admin in group

---

### Issue 3: API 404 Errors Still Appearing

**Symptoms**:
- Logs show: `"GET /api/actions/history?user_id=... 404 Not Found"`
- User stats not loading
- "Failed to load stats" messages

**Root Causes & Solutions**:

1. **Old code still in use**
   ```bash
   # Verify code was actually updated
   grep -n "params=.*user_id" bot/main.py
   
   # Should show NO matches
   # If matches found, old code still there
   ```
   
   **Fix**: Verify file was saved and changes applied
   ```bash
   git diff bot/main.py | head -50
   # Should show user_id removed from params
   ```

2. **Client-side filtering not working**
   ```python
   # Check this section (around line 323)
   all_actions = response.json()["actions"]
   user_actions = [a for a in all_actions if a.get("user_id") == user_id]
   # ↑ This filtering must exist
   ```
   
   **Fix**: Verify filtering code is present

3. **Cached old version**
   ```bash
   # Restart bot to clear any caches
   docker-compose restart bot
   
   # Check if issue persists
   ```
   
   **Fix**: Rebuild container if needed
   ```bash
   docker-compose build bot
   docker-compose restart bot
   ```

---

### Issue 4: API 422 Errors on Log Command

**Symptoms**:
- Logs show: `"POST /api/advanced/history/log-command 422 Unprocessable Entity"`
- Actions don't get logged
- Command history empty

**Root Causes & Solutions**:

1. **Payload format wrong**
   ```python
   # ❌ WRONG (form data):
   data={
       "group_id": group_id,
       ...
   }
   
   # ✅ CORRECT (JSON):
   json={
       "group_id": group_id,
       ...
   }
   ```
   
   **Fix**: Use `json=payload` instead of `data=payload`

2. **Missing required fields**
   ```python
   # Must include all fields:
   payload = {
       "group_id": group_id,      # ← required
       "user_id": user_id,        # ← required
       "command": command,        # ← required
       "args": args,              # ← required
       "status": status,          # ← required
       "result": result           # optional
   }
   ```
   
   **Fix**: Check all fields are present

3. **Endpoint URL wrong**
   ```python
   # Correct endpoint:
   f"{self.base_url}/api/advanced/history/log-command"
   
   # Common mistakes:
   # - Missing "/api" prefix
   # - Wrong path
   # - Typo in "history" or "command"
   ```
   
   **Fix**: Verify exact endpoint URL

---

### Issue 5: Pop-up Alert Not Showing

**Symptoms**:
- User clicks button
- Alert doesn't appear
- Action still proceeds

**Root Causes & Solutions**:

1. **callback_query.answer() not called**
   ```python
   # Before showing alert, must call:
   await callback_query.answer(status_check, show_alert=True)
   # Missing this line = no popup
   ```
   
   **Fix**: Add answer call before returning

2. **Alert text too long**
   ```python
   # Telegram limit: ~200 characters for alerts
   alert_text = "🔴 ALREADY BANNED"  # ✅ Short
   alert_text = "🔴 ALREADY BANNED FOR REASON X Y Z..."  # ❌ Too long
   ```
   
   **Fix**: Keep alert text short

3. **callback_query.answer() called after return**
   ```python
   # ❌ Wrong order:
   return
   await callback_query.answer(...)  # Never reached
   
   # ✅ Correct order:
   await callback_query.answer(...)
   return
   ```
   
   **Fix**: Call answer before returning

---

### Issue 6: Status Check Function Not Found

**Symptoms**:
- Error: `NameError: name 'check_user_current_status' is not defined`
- Code won't run

**Root Causes & Solutions**:

1. **Function not defined**
   ```bash
   # Check if function exists
   grep -n "def check_user_current_status" bot/main.py
   
   # Should show match around line 472
   # No match = function missing
   ```
   
   **Fix**: Add function definition or verify file content

2. **Function indentation wrong**
   ```python
   # ❌ Wrong (function not at module level):
   if True:
       def check_user_current_status(...):
           ...
   
   # ✅ Correct (at module level):
   def check_user_current_status(...):
       ...
   ```
   
   **Fix**: Check indentation, function should be module-level

3. **Module not imported**
   ```bash
   # Check if module imports function
   grep "from bot.main import" bot/main.py
   
   # Function should be defined in same file
   ```
   
   **Fix**: Verify function is in main.py

---

### Issue 7: Clicks Not Triggering Actions

**Symptoms**:
- Click button, nothing happens
- No popup, no action, no error
- Button seems dead

**Root Causes & Solutions**:

1. **Callback data corrupted**
   ```bash
   # Check callback data encoding/decoding
   grep -n "decode_callback_data\|encode_callback_data" bot/main.py
   
   # Should show both functions being used
   ```
   
   **Fix**: Verify compression functions work
   ```bash
   python3 -c "from bot.main import encode_callback_data; print(encode_callback_data({'user_id': 123}))"
   # Should return valid callback string
   ```

2. **Button not set to type callback_query**
   ```python
   # ❌ Wrong:
   InlineKeyboardButton(text="Ban", url="...")
   
   # ✅ Correct:
   InlineKeyboardButton(text="Ban", callback_data="...")
   ```
   
   **Fix**: Verify button uses callback_data

3. **Handler not registered**
   ```bash
   # Check if callback handler is registered
   grep -n "@.*callback_query" bot/main.py
   
   # Should show handler decoration
   ```
   
   **Fix**: Verify handler is registered with dispatcher

---

## Verification Checklist

### Before Deployment

- [ ] Code changes applied to `bot/main.py`
- [ ] Syntax verified: `python3 -m py_compile bot/main.py` ✅ No errors
- [ ] Git status clean: `git status` (or committed changes)
- [ ] API running: `curl http://api:8000/health`
- [ ] MongoDB connected: `docker-compose logs mongodb | grep connected`
- [ ] Bot starts without errors: `docker-compose logs bot | grep -i error`

### After Deployment

- [ ] Test duplicate ban prevention
- [ ] Test duplicate mute prevention
- [ ] Test admin mention in reply
- [ ] Test user mention in reply
- [ ] Check logs for 404 errors (should be 0)
- [ ] Check logs for 422 errors (should be 0)
- [ ] Verify real data loading (not mocked)

### Daily Monitoring

```bash
# Watch for API errors
tail -f logs/bot/bot.log | grep -i "error\|404\|422"

# Watch for action history loads
tail -f logs/bot/bot.log | grep "status\|user_actions"

# Monitor API responses
tail -f logs/api/api.log | grep "actions/history\|log-command"
```

---

## Emergency Rollback

If critical issues occur:

```bash
# 1. Stop bot
docker-compose stop bot

# 2. Revert code to previous version
git checkout HEAD~1 bot/main.py

# 3. Restart bot
docker-compose start bot

# 4. Verify working
sleep 5
docker-compose logs bot | tail -20
```

---

## Getting Help

### Check These Files for Reference

1. **DUPLICATE_PREVENTION_ADMIN_MENTION.md** - Overview & examples
2. **PHASE4_QUICK_REFERENCE.md** - Quick guide
3. **IMPLEMENTATION_DETAILS.md** - Technical deep dive
4. **This file** - Troubleshooting

### Test Commands

```bash
# Test Python syntax
python3 -m py_compile bot/main.py

# Test API connection
curl http://api:8000/health

# Test MongoDB
docker-compose exec mongodb mongosh

# View bot logs
docker-compose logs -f bot

# View API logs
docker-compose logs -f centralized_api

# Restart everything
docker-compose restart
```

### Debug Output

**Enable debug logging**:
```bash
# In docker-compose.yml, add DEBUG=1 env var
TELEGRAM_BOT_DEBUG=1

# Then restart:
docker-compose up -d

# Watch detailed logs:
docker-compose logs -f bot | grep -i debug
```

---

## FAQ

**Q: Will duplicate prevention affect admins?**
A: No, only prevents duplicate restriction actions (ban/mute/restrict). Kick and warn always allowed.

**Q: Will mentions work in all languages?**
A: Yes, deep links (tg://user?id=X) work universally in Telegram.

**Q: What if API is down?**
A: Status check fails open - action proceeds. Better to have duplicate than to block legitimate actions.

**Q: Can users see the admin mention?**
A: Yes, reply message is in chat. Users can click admin mention to open their profile.

**Q: Does this require bot restart?**
A: Yes, code changes require restart: `docker-compose restart bot`

---

**Last Updated**: Phase 4 Complete
**Status**: ✅ All issues documented and solved
