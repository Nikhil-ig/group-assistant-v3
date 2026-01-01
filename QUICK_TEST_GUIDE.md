# 🧪 Quick Test Guide - Reply Mode Commands

**Test Date:** 2025-12-31  
**Status:** Ready to test

---

## ⚡ Quick Test Commands

### Test 1: Reply Mode - `/ban`
```
1. Send any message as a test user
2. Reply to that message
3. Type: /ban
Expected: User gets banned
```

### Test 2: Reply Mode - `/kick`
```
1. Send any message
2. Reply to it
3. Type: /kick
Expected: User gets kicked
```

### Test 3: Reply Mode - `/warn`
```
1. Send any message
2. Reply to it
3. Type: /warn
Expected: User gets warned
```

### Test 4: Reply Mode - `/mute`
```
1. Send any message
2. Reply to it
3. Type: /mute 24
Expected: User muted for 24 hours
```

### Test 5: Reply Mode - `/unmute`
```
1. Send any message from muted user
2. Reply to it
3. Type: /unmute
Expected: User unmuted
```

### Test 6: Reply Mode - `/restrict` (NEW!)
```
1. Send any message
2. Reply to it
3. Type: /restrict stickers
Expected: User can't send stickers
```

### Test 7: Reply Mode - `/restrict` Multiple Types
```
1. Send any message
2. Reply to it
3. Type: /restrict stickers gifs 12
Expected: User blocked from stickers & gifs for 12 hours
```

### Test 8: Direct Mode - Still Works
```
1. Type: /restrict @user stickers 24
Expected: Works as before
```

### Test 9: Direct Mode - `/ban`
```
1. Type: /ban @user
Expected: User gets banned
```

### Test 10: Reply Mode - With Reason
```
1. Reply to message
2. Type: /ban Spamming
Expected: User banned with reason logged
```

---

## 📋 Expected Behaviors

### ✅ Should Work
- Reply to any message + command
- Direct mode with user ID/username
- Multiple block types
- Optional duration
- Optional reason
- Admin check
- Database logging
- API calls to Telegram

### ❌ Should Fail (By Design)
- Non-admin using commands
- Invalid block types
- Missing required parameters
- No user found (in direct mode)
- Bot not in group

---

## 🔍 What to Check

### Telegram Chat
- [ ] Bot responds with correct message
- [ ] User is actually muted/banned/kicked
- [ ] Block types are applied correctly
- [ ] Duration works (user unmutes after X hours)

### Database Logs
- [ ] Action logged with correct admin
- [ ] Action logged with correct target user
- [ ] Reason is captured
- [ ] Timestamp is correct

### Bot Logs
```bash
tail -f logs/bot.log | grep -i restrict
tail -f logs/bot.log | grep -i ban
tail -f logs/api.log | grep -i mute
```

Look for:
- ✅ User is admin check
- ✅ Telegram API call
- ✅ Database log
- ✅ Response sent

---

## 🎯 Testing Checklist

### Reply Mode Tests
- [ ] Ban via reply
- [ ] Kick via reply
- [ ] Warn via reply
- [ ] Mute via reply
- [ ] Unmute via reply
- [ ] Restrict via reply (single type)
- [ ] Restrict via reply (multiple types)
- [ ] Restrict via reply (with duration)

### Direct Mode Tests
- [ ] Ban with @username
- [ ] Ban with user ID
- [ ] Restrict with multiple types
- [ ] Mute with duration
- [ ] Commands with reasons

### Edge Cases
- [ ] Reply to bot's message
- [ ] Empty arguments
- [ ] Invalid user ID
- [ ] Non-admin user
- [ ] Same user ban twice (should handle gracefully)

### Database Verification
- [ ] Logs appear in database
- [ ] Metrics updated
- [ ] Action type correct
- [ ] Admin ID captured
- [ ] Target user ID captured

---

## 🐛 Debugging Commands

```bash
# View bot logs
tail -f logs/bot.log

# View API logs
tail -f logs/api.log

# Check database entries (from Python)
# (Connect to MongoDB and check audit_logs collection)

# View recent restrictions
# /logs command in Telegram
```

---

## 📸 Expected Responses

### Success - Reply Mode
```
🚫 User @username restricted

Blocked: stickers, gifs
Duration: for 24 hours
```

### Success - Direct Mode
```
🚫 User 123456 restricted

Blocked: stickers
Duration: (permanent)
```

### Error - Not Admin
```
❌ You don't have permission to use this command
```

### Error - No Parameters
```
📋 Usage (reply mode): /restrict <block_type> [block_type2...] [hours]

Block types:
  • media - Block all media
  • stickers - Block stickers
  ...
```

---

## 🚀 Test Execution Steps

1. **Setup Test Group**
   - Create a Telegram test group
   - Add test users (non-admin)
   - Add bot as admin

2. **Test Each Command**
   - Try reply mode
   - Try direct mode
   - Verify both work

3. **Verify Side Effects**
   - Check Telegram restrictions applied
   - Check database logs
   - Check bot logs

4. **Edge Cases**
   - Try commands without admin
   - Try invalid parameters
   - Try with deleted messages

5. **Document Results**
   - Record what works
   - Note any issues
   - Keep for regression testing

---

## ✅ Verification Checklist

```
REPLY MODE:
☐ /ban works via reply
☐ /kick works via reply
☐ /warn works via reply
☐ /mute works via reply (with duration)
☐ /unmute works via reply
☐ /restrict works via reply (single type)
☐ /restrict works via reply (multiple types)

DIRECT MODE:
☐ /ban works with @username
☐ /ban works with user ID
☐ /restrict works with multiple types
☐ /mute works with duration
☐ /kick works with reason

DATABASE:
☐ Actions logged
☐ Admin ID captured
☐ Target user captured
☐ Reason captured (when provided)

TELEGRAM API:
☐ User actually muted
☐ User actually banned
☐ Block types actually applied
☐ Duration actually works
```

---

## 🎓 Common Issues & Solutions

### Issue: Command not recognized
**Solution:** Make sure command is registered in handlers

### Issue: Reply mode not working
**Solution:** Check `update.message.reply_to_message` is not None

### Issue: Duration not parsed
**Solution:** Make sure duration is numeric: `int(arg)`

### Issue: Block types not working
**Solution:** Check block type is in valid set: `media, stickers, gifs, ...`

### Issue: Not admin error
**Solution:** Verify user is actually admin in group

---

**Last Updated:** 2025-12-31  
**Ready to Test:** ✅ YES
