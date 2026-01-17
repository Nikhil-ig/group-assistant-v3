# 🚀 BOT V2 - QUICK START GUIDE

Get your advanced bot running in 5 minutes!

---

## ⚡ 5-Minute Setup

### Step 1: Install Dependencies (1 min)

```bash
cd /Users/apple/Documents/Personal/startup/bots/telegram\ bot/python/main_bot_v2/v3/bot

pip install aiogram==3.24.0 httpx==0.25.2 python-dotenv==1.0.0 pydantic==2.5.0
```

### Step 2: Configure Environment (1 min)

Create/edit `.env` file in the `bot/` directory:

```bash
# .env
TELEGRAM_BOT_TOKEN=your_bot_token_here
API_V2_URL=http://localhost:8002
API_V2_KEY=shared-api-key
LOG_LEVEL=INFO
```

Get token from @BotFather on Telegram.

### Step 3: Start Bot V2 (1 min)

```bash
python bot_v2.py
```

You should see:
```
2026-01-17 14:30:45 - __main__ - INFO - 🚀 Bot V2 Starting...
2026-01-17 14:30:46 - __main__ - INFO - ✅ API V2 is healthy
2026-01-17 14:30:47 - __main__ - INFO - ✅ Bot commands set
2026-01-17 14:30:47 - __main__ - INFO - 🎯 Polling started...
```

### Step 4: Add to Group (1 min)

1. Go to @BotFather on Telegram
2. Find your bot
3. Copy bot URL
4. Add to your group
5. Make bot admin

### Step 5: Test (1 min)

In your group:
```
/start          # Should show welcome
/help           # Should show commands
/settings @user # Should show admin panel
```

---

## ✅ Quick Verification

### Health Check

```bash
# In another terminal
curl http://localhost:8002/health
# Should return: {"status": "ok"}
```

### Test Admin Panel

1. Send `/settings @testuser`
2. You should see beautiful admin panel with toggle buttons
3. Click "🔇 Mute" button
4. Should execute and show "✅ SUCCESS"

### Test Different Inputs

```
# By username
/settings @john_doe

# By user ID  
/settings 123456789

# By reply
[Reply to message] /settings
```

---

## 🎯 Features to Try

### 1. Beautiful Messages

Send any command and admire the:
- Professional formatting
- Beautiful emojis
- Clickable user mentions
- Organized layout

### 2. Smart Toggles

Admin panel shows:
- 🔇 Mute ↔ 🔊 Unmute
- 🚫 Ban ↔ ✅ Unban
- ⚠️ Warn ↔ 🆗 Clear Warn
- ⛔ Restrict ↔ ✅ Unrestrict
- 🔒 Lockdown ↔ 🔓 Freedom
- 🌙 Night Mode ↔ ☀️ Day Mode

Current state determines which button shows!

### 3. Reply Context

```
Admin replies to user message
     ↓
Then sends /settings
     ↓
Admin panel appears on that message
     ↓
Reply stays attached to original message
```

### 4. Professional Mentions

All users shown as:
- 👤 John Doe (clickable)
- Not: User 123456789
- Professional appearance

---

## 📊 Example Workflow

### Scenario: Admin wants to mute a spammer

```
1. Admin spots message from spammer
2. Admin clicks reply
3. Admin types: /settings
4. Admin panel appears on spammer's message
5. Admin clicks "🔇 Mute" button
6. Bot confirms: "✅ SUCCESS - Mute executed"
7. Spammer is now muted
8. Admin can see updated state (now shows "🔊 Unmute")
9. Action logged to API V2
```

### Scenario: Need to warn someone

```
1. Admin replies to message: /settings @user
2. Admin panel appears
3. Admin sees: "🟢 ⚠️ Warn: ❌ INACTIVE"
4. Admin clicks "⚠️ Warn" button
5. Bot shows success message
6. User count updates to: "⚠️ Warn: ✅ ACTIVE"
```

---

## 🐛 Quick Troubleshooting

### "Bot not responding"
```bash
# Check token
echo $TELEGRAM_BOT_TOKEN

# Check network
ping google.com

# Restart bot
python bot_v2.py
```

### "Admin panel not showing"
```bash
# Verify you're admin
# Check bot can see the message
# Check API V2 is running
curl http://localhost:8002/health
```

### "Buttons not working"
```bash
# Check bot is running (no errors)
# Verify admin status
# Check API response in logs
```

### "API errors"
```bash
# Start API V2
cd ../api_v2
python main.py

# Check connectivity
curl http://localhost:8002/health
```

---

## 📱 Commands Reference

| Command | Usage | Example |
|---------|-------|---------|
| `/start` | Welcome message | Just type |
| `/help` | Show all commands | Just type |
| `/settings` | Admin panel | `/settings @user` |
| `/status` | Check bot health | Just type |

---

## 🎮 Button Reference

| Button | Action | Result |
|--------|--------|--------|
| 🔇 Mute | Click to mute user | User can't send messages |
| 🔊 Unmute | Click to unmute | User can send messages |
| 🚫 Ban | Click to ban user | User removed from group |
| ✅ Unban | Click to unban | User can join again |
| ⚠️ Warn | Click to warn | Warning count +1 |
| 🆗 Clear Warn | Click to clear | Warning count 0 |
| ⛔ Restrict | Click to restrict | Limited permissions |
| ✅ Unrestrict | Click to unrestrict | Full permissions |
| 🔒 Lockdown | Click to lock | Emergency mode |
| 🔓 Freedom | Click to unlock | Normal mode |
| 🌙 Night Mode | Enable night mode | Night restrictions |
| ☀️ Day Mode | Disable night mode | Normal restrictions |
| ❌ Close | Close panel | Panel disappears |

---

## 📈 Next Steps

After basic setup:

1. **Add more admins** - They can now use `/settings` too

2. **Monitor logs** - Check what actions are being logged
   ```bash
   tail -f bot.log
   ```

3. **Test with different users** - Try various scenarios

4. **Customize messages** - Edit formatting in bot_v2.py

5. **Add more commands** - Extend functionality as needed

---

## 🔧 Common Customizations

### Change admin panel style

Edit `format_admin_panel_message()` in bot_v2.py:

```python
def format_admin_panel_message(...) -> str:
    # Customize message format here
    message = f"""
╔════════════════════════════════════════╗
║    🎛️ YOUR CUSTOM TITLE
╚════════════════════════════════════════╝
...
"""
    return message
```

### Add new toggle actions

Add to `build_admin_toggle_keyboard()`:

```python
# Your new button
buttons.append([
    InlineKeyboardButton(
        text="🎯 Your Action",
        callback_data=encode_callback_data("your_action", user_id, group_id)
    )
])
```

### Change emoji icons

Edit `format_user_action_message()`:

```python
action_icons = {
    "mute": "🔇",
    "unmute": "🔊",
    # Add yours:
    "your_action": "🎯"
}
```

---

## 💡 Pro Tips

1. **Reply for context** - Always reply to message first, then `/settings`

2. **Check current state** - Panel shows what action will happen when clicked

3. **Bulk actions** - Open panel once, try multiple toggles

4. **Check logs** - All actions logged via API V2

5. **Use usernames** - `/settings @john` is easier than `/settings 123456789`

---

## 🚨 Emergency Commands

### Restart bot
```bash
pkill -f "python bot_v2.py"
python bot_v2.py
```

### View logs
```bash
# Real-time logs
tail -f bot.log

# Last 100 lines
tail -100 bot.log

# Search for errors
grep ERROR bot.log
```

### Clear cache (if needed)
The bot auto-cleans, but restart forces cleanup:
```bash
python bot_v2.py
```

---

## 📞 Support Checklist

If something doesn't work:

- [ ] Bot token is correct
- [ ] API V2 is running (curl health check)
- [ ] Environment variables set
- [ ] Bot has internet access
- [ ] Bot has group admin permissions
- [ ] Group has bot as member
- [ ] No firewall blocking bot↔API
- [ ] Python 3.8+ installed
- [ ] All dependencies installed
- [ ] No syntax errors in bot_v2.py

---

## ✨ You're Ready!

Your advanced Bot V2 is now running with:

✅ Smart toggle buttons
✅ Professional admin panel
✅ Beautiful formatting
✅ Full API integration
✅ User mentions
✅ Reply context
✅ Ultra-fast performance
✅ Fully robust error handling

**Start using it now!**

---

**Version:** 2.0
**Setup Time:** ~5 minutes
**Difficulty:** ⭐ Very Easy
**Status:** ✅ Production Ready
