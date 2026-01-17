# 🤖 How to Get a Valid Telegram Bot Token

## Problem
Your bot is getting "Unauthorized" error from Telegram servers, which means the token is either:
- Invalid/malformed
- Revoked by Telegram
- From a deleted bot account
- Has wrong permissions

---

## ✅ Solution: Create a New Bot Token

### Step 1: Open Telegram
- Open your Telegram app or web version
- Search for: `@BotFather`

### Step 2: Create New Bot
```
/start
/newbot
```

BotFather will ask:
1. **Bot name** (display name for your bot)
   - Example: "Group Assistant Bot"

2. **Bot username** (must end with "bot", lowercase, no spaces)
   - Example: "group_assistant_bot" or "my_group_bot"

### Step 3: Get Your Token
BotFather will give you a message like:
```
Done! Congratulations on your new bot. 
Here are your bot credentials:

Bot token: 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
```

### Step 4: Update .env File
Replace the token in `bot/.env`:

```properties
TELEGRAM_BOT_TOKEN=YOUR_NEW_TOKEN_HERE
API_V2_URL=http://localhost:8002
API_V2_KEY=shared-api-key
LOG_LEVEL=INFO
```

---

## 🎯 Token Format Reference

### Valid Token Format
```
YOUR_BOT_ID:YOUR_BOT_TOKEN_STRING
```

Example of valid format:
```
123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefgh
```

### Components
- **123456789** = Bot ID (numbers only)
- **:** = Separator
- **ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefgh** = Token (alphanumeric + dash + underscore)

---

## 🔍 Troubleshooting

### If you still get "Unauthorized":
1. **Verify token format** - Make sure it matches: `number:alphanumeric`
2. **No extra spaces** - Check for spaces before/after token in .env
3. **Try a fresh token** - Create a new bot via BotFather
4. **Check bot permissions** - In BotFather, type `/mybots` to see your bots

### If bot still won't start:
1. Stop services: `./stop_all_services.sh`
2. Update token in `bot/.env`
3. Restart: `./start_all_services.sh`

---

## 📝 Current .env File

Location: `bot/.env`

```properties
TELEGRAM_BOT_TOKEN=YOUR_TOKEN_HERE
API_V2_URL=http://localhost:8002
API_V2_KEY=shared-api-key
LOG_LEVEL=INFO
```

---

## ✨ What to do next:

1. ✅ Get new token from @BotFather (Steps 1-3 above)
2. ✅ Update `bot/.env` with new token
3. ✅ Restart services: `./start_all_services.sh`
4. ✅ Bot should start successfully!

---

## 🆘 Still Having Issues?

### Check token is correct:
```bash
# View current token (without full value)
head -1 bot/.env
```

### Verify bot can start:
```bash
# Check logs
tail -f /tmp/bot.log

# Look for:
# ✅ Centralized API is healthy
# ✅ Bot initialized successfully
```

### Common errors:
- **"Unauthorized"** → Token is invalid/revoked → Get new token
- **"Not Found"** → Bot username/ID wrong → Verify with BotFather
- **"Connection refused"** → API not running → Check `./start_all_services.sh`

---

## 📱 After Getting Token

Once your bot is running:

1. **Find your bot on Telegram**
   - Search for your bot username (e.g., `@group_assistant_bot`)

2. **Send /start command**
   - You should see the beautiful welcome screen!

3. **Test commands**
   - `/help` → See commands
   - `/status` → Check system
   - `/ban`, `/mute`, etc. → Test moderation

---

**Need more help?** Check these docs:
- `TESTING_GUIDE.md` - How to test bot features
- `README_ENHANCEMENTS.md` - Feature overview
- `BUTTON_GUIDE.md` - Visual examples

---

**Version:** 3.0.0 Advanced
**Last Updated:** 2026-01-14
