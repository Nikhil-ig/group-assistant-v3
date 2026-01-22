# 🧪 /send Command - Testing & Troubleshooting Guide

## ✅ CURRENT STATUS
- Bot is **RUNNING** and **POLLING**
- Zero errors in logs
- All services operational
- Code is syntactically correct

## 🎯 How to Test /send Command

### Test 1: Send Text Message
```
Step 1: Type in group: /send Hello World
Step 2: Observe: Text message "Hello World" appears in group
Expected: ✅ Message sent and /send command deleted
```

### Test 2: Send Photo (With Caption)
```
Step 1: User shares a photo with caption "My Photo"
Step 2: Admin replies: /send
Step 3: Observe: Photo appears with caption "My Photo"
Expected: ✅ Photo + caption sent
```

### Test 3: Send Photo (Without Caption)
```
Step 1: User shares a photo (no caption)
Step 2: Admin replies: /send
Step 3: Observe: Photo appears (no caption)
Expected: ✅ Photo sent without caption
```

### Test 4: Send Video
```
Step 1: User shares a video with caption "Check this!"
Step 2: Admin replies: /send
Step 3: Observe: Video appears with caption
Expected: ✅ Video + caption sent
```

### Test 5: Send Document
```
Step 1: User shares a document/PDF
Step 2: Admin replies: /send
Step 3: Observe: Document appears
Expected: ✅ Document sent
```

## ❌ If Something Doesn't Work

### Issue: "❌ You need admin permissions to send messages via bot"
**Solution:** Only admins can use `/send`
- Check if you're admin in the group
- Try as a group admin account

### Issue: "❌ Please provide text or reply to a message/media with /send"
**Solution:** Command needs either text or reply
- For text: `/send <your message>`
- For media: Reply to media + `/send`

### Issue: "❌ Error sending media: [error]"
**Solution:** Media sending failed
- Check if media is valid
- Check if bot has permission to send media
- Check Telegram API status

### Issue: Nothing happens when using /send
**Check:**
1. Are you admin? → Yes/No
2. Did you provide text or reply? → Yes/No
3. Check logs: `tail -50 /tmp/bot.log | grep -i send`
4. Restart bot: `./stop_all_services.sh && ./start_all_services.sh`

## 🔍 Debugging Steps

### Step 1: Verify Bot is Running
```bash
ps aux | grep "telegram"
ps aux | grep "python"
```
Expected: Bot process running

### Step 2: Check Bot Logs
```bash
tail -50 /tmp/bot.log
```
Expected: "Bot is polling for updates..." message

### Step 3: Check for Errors
```bash
tail -50 /tmp/bot.log | grep -i error
```
Expected: No error messages

### Step 4: Test Command Manually
```bash
# In your group chat:
/send This is a test message
```
Expected: Message appears in group

### Step 5: Verify Media Support
```bash
# In your group chat:
1. Share a photo
2. Reply with: /send
```
Expected: Photo is forwarded

## 📊 Code Path Analysis

### Text Message Path
```
User: /send <text>
  ↓
cmd_send() called
  ↓
Admin check → PASS
  ↓
message.text exists → YES
  ↓
args = message.text.split()
  ↓
mode = "send"
  ↓
Send text message
  ↓
✅ Success
```

### Media Path
```
User: /send (reply to media)
  ↓
cmd_send() called
  ↓
Admin check → PASS
  ↓
message.text = None
  ↓
Check reply_to_message → EXISTS
  ↓
Detect media type → PHOTO/VIDEO/etc
  ↓
Get caption (if exists)
  ↓
Build kwargs (caption optional)
  ↓
Send media
  ↓
✅ Success
```

## 🛠️ Quick Fixes

### If /send stopped working:
```bash
# Restart services
cd /Users/apple/Documents/Personal/startup/bots/telegram\ bot/python/main_bot_v2/v3
./stop_all_services.sh
sleep 2
./start_all_services.sh
```

### If logs show errors:
```bash
# Check for syntax errors
cd /Users/apple/Documents/Personal/startup/bots/telegram\ bot/python/main_bot_v2/v3
python -m py_compile bot/main.py
```

### If bot won't start:
```bash
# Check all services
tail -20 /tmp/mongod.log
tail -20 /tmp/api.log
tail -20 /tmp/web.log
tail -20 /tmp/bot.log
```

## 📋 Verification Checklist

- [ ] Bot is running (check with `ps aux | grep python`)
- [ ] Bot logs show "Bot is polling for updates..."
- [ ] No errors in `/tmp/bot.log`
- [ ] Can send text with `/send Hello`
- [ ] Can reply to media with `/send`
- [ ] Captions are preserved when present
- [ ] Media sends without caption if not present

## 🚨 Last Resort

If nothing works:
```bash
# Stop everything
./stop_all_services.sh

# Wait
sleep 3

# Start everything
./start_all_services.sh

# Wait for startup
sleep 5

# Check logs
tail -30 /tmp/bot.log
```

---

**Status:** Ready for testing
**Last Updated:** 2026-01-20
**Version:** 3.1.1
