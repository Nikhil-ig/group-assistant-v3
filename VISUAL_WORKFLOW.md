# Visual Sync Workflow

## 📊 The Complete Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         YOUR MAC (VS Code)                          │
│                                                                     │
│  1. Edit code in VS Code                                           │
│     └─ bot/main.py, centralized_api/app.py, etc.                 │
│                                                                     │
│  2. Commit changes                                                  │
│     └─ git add .                                                   │
│     └─ git commit -m "message"                                     │
│                                                                     │
│  3. Push to GitHub                                                  │
│     └─ git push origin main                                        │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               │ (HTTPS or SSH)
                               ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      GITHUB (Main Branch)                           │
│                                                                     │
│  Your repo: github.com/Nikhil-ig/group-assistant-v3               │
│  ├─ Latest code                                                    │
│  ├─ Deployment scripts (deploy-vps.sh)                           │
│  ├─ Documentation (VPS_DEPLOYMENT.md)                            │
│  └─ .env files are gitignored (not here!)                        │
│                                                                     │
│  GitHub Webhook Events:                                            │
│  └─ Sends POST to: http://your.vps.ip:9000/hooks/...            │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               │ (Webhook - Real-time)
                               │ OR
                               │ (Cron - Every 5 minutes)
                               ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    YOUR VPS (Docker Compose)                        │
│                                                                     │
│  /opt/group-assistant-v3/                                          │
│  ├─ webhook-receiver.sh (listens on port 9000)                   │
│  │  └─ OR cron job (checks every 5 min)                         │
│  │                                                                │
│  └─ deploy-vps.sh (triggered by webhook or cron)                │
│     1. Git fetch origin/main                                     │
│     2. Git reset --hard (pull latest code)                       │
│     3. docker compose pull (update images)                       │
│     4. docker compose down (stop old services)                   │
│     5. docker compose up -d (start new services)                │
│     6. Health check (verify all running)                         │
│                                                                     │
│  Services Running:                                                  │
│  ├─ MongoDB (port 27017)                                          │
│  ├─ Redis (port 6379)                                            │
│  ├─ Centralized API (port 8000)                                  │
│  ├─ Bot (polling Telegram)                                        │
│  └─ Web (port 8003)                                              │
│                                                                     │
│  .env Files (Local Only, Never Committed):                        │
│  ├─ bot/.env (TELEGRAM_BOT_TOKEN)                               │
│  └─ centralized_api/.env (DB passwords)                          │
│                                                                     │
│  Logs:                                                              │
│  ├─ /var/log/group-assistant-deploy.log                          │
│  ├─ docker compose logs -f bot                                   │
│  └─ docker compose logs -f centralized_api                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Step-by-Step Workflow Example

### Example: You add a new command to the bot

```
1️⃣  LOCAL (Mac)
    ┌─────────────────────────────────────┐
    │ Edit bot/main.py in VS Code         │
    │ Add new /greet command              │
    └──────────────┬──────────────────────┘
                   │
                   ↓ git add bot/main.py
                   
    ┌─────────────────────────────────────┐
    │ git commit -m "feat: add /greet"    │
    └──────────────┬──────────────────────┘
                   │
                   ↓ git push origin main
    
    ┌─────────────────────────────────────┐
    │ Pushed to GitHub (main branch)      │
    └──────────────┬──────────────────────┘


2️⃣  GITHUB
    ┌─────────────────────────────────────┐
    │ github.com/Nikhil-ig/...            │
    │ ✅ Code updated on main             │
    │ 🔔 Webhook triggered                │
    │    (POST to VPS webhook receiver)   │
    └──────────────┬──────────────────────┘
                   │
                   ↓ HTTP POST (webhook)
                   │ OR
                   │ (Cron check every 5 min)
    
    ┌─────────────────────────────────────┐
    │ VPS receives event                  │
    │ Runs: /opt/.../deploy-vps.sh       │
    └──────────────┬──────────────────────┘


3️⃣  VPS AUTO-DEPLOYMENT
    ┌─────────────────────────────────────┐
    │ 1. git fetch origin/main            │
    │ 2. git reset --hard                 │
    │    └─ bot/main.py has new /greet   │
    │ 3. docker compose pull              │
    │ 4. docker compose down              │
    │ 5. docker compose up -d             │
    │ 6. Health checks                    │
    │ 7. ✅ NEW /greet COMMAND LIVE!     │
    └─────────────────────────────────────┘


4️⃣  VERIFICATION (you can check)
    ┌─────────────────────────────────────┐
    │ ssh root@your.vps.ip                │
    │ docker compose logs -f bot          │
    │ # See bot running with new code     │
    │                                     │
    │ Or test in Telegram:                │
    │ /greet                              │
    │ ✅ Bot responds!                    │
    └─────────────────────────────────────┘
```

---

## ⚙️ File Locations & Purposes

### Your Mac (Repository Root)
```
/Users/apple/Documents/.../main_bot_v2/v3/
├── bot/
│   ├── main.py (loads bot/.env automatically)
│   ├── requirements.txt
│   └── .env.example (template)
├── centralized_api/
│   ├── app.py
│   ├── requirements.txt
│   └── .env.example (template)
├── docker-compose.yml
├── setup-vps.sh ✨ (auto-setup on VPS)
├── deploy-vps.sh ✨ (deployment automation)
├── VPS_DEPLOYMENT.md ✨ (full guide)
├── SYNC_QUICK_START.md ✨ (quick reference)
└── SYNC_SETUP_COMPLETE.md ✨ (this summary)

.env files are gitignored (safe!)
```

### Your VPS (/opt/group-assistant-v3)
```
/opt/group-assistant-v3/
├── bot/
│   ├── main.py (same as GitHub)
│   ├── requirements.txt
│   └── .env ✨ (YOUR SECRETS - never committed!)
├── centralized_api/
│   ├── app.py (same as GitHub)
│   ├── requirements.txt
│   └── .env ✨ (YOUR SECRETS - never committed!)
├── docker-compose.yml (same as GitHub)
├── deploy-vps.sh (runs on deployment)
└── [other files synced from GitHub]

Logs:
├── /var/log/group-assistant-deploy.log
```

---

## 🔐 Secret Management

```
Your Secrets (VPS Only):
┌─────────────────────────────────────────────┐
│ bot/.env (NOT in GitHub)                    │
│ TELEGRAM_BOT_TOKEN=8366781443:AAH...       │
│ CENTRALIZED_API_URL=http://...             │
│ CENTRALIZED_API_KEY=your_key               │
│ LOG_LEVEL=INFO                             │
└─────────────────────────────────────────────┘

Safe Templates (In GitHub):
┌─────────────────────────────────────────────┐
│ bot/.env.example (no real values)           │
│ TELEGRAM_BOT_TOKEN=your_token_here         │
│ CENTRALIZED_API_URL=http://...             │
│ CENTRALIZED_API_KEY=your_key               │
│ LOG_LEVEL=INFO                             │
└─────────────────────────────────────────────┘
```

---

## 🚀 One Command to Deploy on VPS

```bash
# From your Mac - make changes and push
git push origin main

# On VPS (automatic if webhook enabled):
# OR manually:
/opt/group-assistant-v3/deploy-vps.sh

# Services restart with new code ✅
```

---

## 📈 Scaling & Monitoring

### Check Status Anytime
```bash
# SSH to VPS
ssh root@your.vps.ip

# See all services
docker compose ps

# View real-time logs
docker compose logs -f

# Check specific service
docker compose logs -f bot
```

### Deployment History
```bash
# View deployment logs
tail -f /var/log/group-assistant-deploy.log

# View git history
cd /opt/group-assistant-v3
git log --oneline | head
```

---

## ✨ Features

✅ **Automatic**: Push code, VPS deploys automatically  
✅ **Secure**: .env secrets never in GitHub  
✅ **Fast**: Webhook = instant deployment  
✅ **Reliable**: Cron fallback if webhook fails  
✅ **Observable**: Full logging for debugging  
✅ **Simple**: Just edit, commit, push!  

---

**Everything is ready! Start syncing! 🚀**
