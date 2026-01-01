# V3 BOT - QUICK START CARD

## 🚀 Run Everything in 3 Commands

```bash
# 1. Copy configuration
cp .env.example .env

# 2. Edit and add your tokens
nano .env
# Add: TELEGRAM_BOT_TOKEN, SUPERADMIN_ID, MONGODB_URI

# 3. Run everything together
python main.py
```

**Done!** Both bot and API are running.

---

## 🌐 What's Running

| Component | Access | Purpose |
|-----------|--------|---------|
| **Telegram Bot** | Your Telegram group | Send commands: /ban, /stats, /logs |
| **REST API** | http://localhost:8000 | Programmatic access |
| **Swagger Docs** | http://localhost:8000/docs | Interactive API explorer |
| **MongoDB** | Configured in .env | Data storage |

---

## 📋 What You Need in `.env`

```ini
TELEGRAM_BOT_TOKEN=your-token-from-@BotFather
SUPERADMIN_ID=your-telegram-user-id
MONGODB_URI=mongodb://localhost:27017
JWT_SECRET=any-random-string-32-chars-long
```

---

## 📱 Telegram Commands (In Group Chat)

```bash
/stats              # Show group statistics
/ban 123456789      # Ban user
/unban 123456789    # Unban user
/kick 123456789     # Kick user
/warn 123456789     # Warn user
/mute 123456789 2   # Mute for 2 hours
/logs 5             # Show last 5 logs
```

---

## 🌐 REST API (curl examples)

### Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"user_id":123,"username":"user","first_name":"Name"}'
```

### Get Groups
```bash
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/v1/groups
```

### Ban User
```bash
curl -X POST http://localhost:8000/api/v1/groups/-123456789/actions \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action_type":"ban","target_user_id":987654321,"reason":"spam"}'
```

### View Logs
```bash
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/api/v1/groups/-123456789/logs?page=1"
```

### Get Stats
```bash
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/api/v1/groups/-123456789/metrics"
```

---

## 🛑 Stop the Bot

```bash
Ctrl + C
```

---

## 🔧 Troubleshooting

| Error | Fix |
|-------|-----|
| "MongoDB connection failed" | Start MongoDB: `brew services start mongodb-community` |
| "TELEGRAM_BOT_TOKEN not found" | Edit .env and add your token |
| "Port 8000 already in use" | Change `API_PORT=8001` in .env |
| "ModuleNotFoundError" | Run: `pip install -r requirements.txt` |
| Bot not responding | Make bot admin in group + run `python validate.py` |

---

## 📚 Full Guides

- **RUN_GUIDE.md** - Complete running instructions
- **SETUP.md** - Detailed setup guide
- **FIXES_APPLIED.md** - What was fixed

---

## ✅ Before Running

- [ ] Python 3.8+
- [ ] .env configured
- [ ] MongoDB running
- [ ] Bot token from @BotFather
- [ ] `pip install -r requirements.txt`
- [ ] Bot added to Telegram group

---

## 🎉 You're Ready!

```bash
python main.py
```

That's it! 🚀
