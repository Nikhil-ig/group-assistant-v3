# 🚀 Getting Started: VS Code → GitHub → VPS Sync

**Everything is ready!** This guide gets you from zero to synced in 5 minutes.

---

## ⚡ TL;DR (Super Quick Version)

If you want just the essentials:

### 1. VPS First-Time Setup (5 minutes)
```bash
# SSH to your VPS
ssh root@your.vps.ip

# Run this ONE command (handles everything)
bash -c "$(curl -fsSL https://raw.githubusercontent.com/Nikhil-ig/group-assistant-v3/main/setup-vps.sh)"

# Follow the prompts:
# - Enter bot token (from @BotFather)
# - Enter API key
# - Enter MongoDB password
# - Enter Redis password
# - Choose: Webhook (auto) or Cron (every 5 min)
```

### 2. Daily Workflow (Repeat Every Day)
```bash
# On your Mac in VS Code
git add .
git commit -m "your message"
git push origin main

# VPS auto-deploys! ✅
```

### 3. Monitor Deployment
```bash
# SSH and check
ssh root@your.vps.ip
docker compose logs -f
```

**That's it!** You now have:
- ✅ Code synced GitHub → VPS
- ✅ Automatic deployment on every push
- ✅ Services running and updated

---

## 📖 Full Documentation (If You Want Details)

Start with one of these files:

| Want... | Read This |
|---------|-----------|
| Quick reference | `SYNC_QUICK_START.md` |
| Step-by-step guide | `SETUP_CHECKLIST.md` |
| See how it works | `VISUAL_WORKFLOW.md` |
| Complete reference | `VPS_DEPLOYMENT.md` |
| All the details | `SYNC_SETUP_COMPLETE.md` |

---

## 🎯 What Was Set Up For You

### Code Changes
✅ **`bot/main.py`** — Now loads `.env` automatically on startup

### Deployment Scripts (GitHub)
✅ **`setup-vps.sh`** — One-command VPS initialization  
✅ **`deploy-vps.sh`** — Handles git pull & service restart  
✅ **`webhook-receiver.sh`** — Listens for GitHub push events

### Documentation Files
✅ **`SYNC_QUICK_START.md`** — 1-2 min quick reference  
✅ **`VPS_DEPLOYMENT.md`** — Complete setup guide  
✅ **`VISUAL_WORKFLOW.md`** — Diagrams of the sync flow  
✅ **`SYNC_SETUP_COMPLETE.md`** — Summary & next steps  
✅ **`SETUP_CHECKLIST.md`** — Detailed checklist  

### .env Templates (Safe to Commit)
✅ **`bot/.env.example`** — Bot config template  
✅ **`centralized_api/.env.example`** — API config template

### Security
✅ **`.gitignore`** — Ensures `.env` files never committed

---

## 🔐 Important: Your Secrets

### What's on VPS (Secret!)
```
bot/.env                    ← Your bot token (local only!)
centralized_api/.env        ← Your database passwords (local only!)
```

### What's on GitHub (Safe!)
```
bot/.env.example            ← Template (no real values)
centralized_api/.env.example ← Template (no real values)
```

**Rule of thumb**: If it has a real token or password, it's `.env` (local only).

---

## 📋 Setup Checklist

### Step 1: VPS Setup
```bash
ssh root@your.vps.ip
bash -c "$(curl -fsSL https://raw.githubusercontent.com/Nikhil-ig/group-assistant-v3/main/setup-vps.sh)"
```

**What the script does:**
- [ ] Clones repository
- [ ] Creates bot/.env (your secrets)
- [ ] Creates centralized_api/.env (your secrets)
- [ ] Installs webhook service (optional)
- [ ] Runs first deployment
- [ ] Starts all services

### Step 2: Webhook Setup (if you chose webhook mode)
```bash
# 1. Get your VPS IP
hostname -I

# 2. Add GitHub webhook:
# https://github.com/Nikhil-ig/group-assistant-v3/settings/hooks/new
# - Payload URL: http://YOUR.VPS.IP:9000/hooks/group-assistant-deploy
# - Events: Just the push event
# - Click Add webhook
```

### Step 3: Start Using!
```bash
# On your Mac
git add .
git commit -m "your message"
git push origin main

# Watch VPS deploy automatically
ssh root@your.vps.ip && docker compose logs -f
```

---

## 💾 File Structure

```
GitHub (Pushed by You)
├── bot/
│   ├── main.py (loads bot/.env auto)
│   ├── .env.example
│   └── requirements.txt
├── centralized_api/
│   ├── app.py
│   ├── .env.example
│   └── requirements.txt
├── docker-compose.yml
├── setup-vps.sh ← Run this first!
├── deploy-vps.sh
├── VPS_DEPLOYMENT.md
├── SYNC_QUICK_START.md
├── SETUP_CHECKLIST.md
└── VISUAL_WORKFLOW.md

VPS (/opt/group-assistant-v3)
├── [All files from GitHub above]
├── bot/.env ← Your secrets (local only)
└── centralized_api/.env ← Your secrets (local only)
```

---

## 🔄 Daily Workflow

### 1. Make Code Changes
```bash
# Open VS Code on your Mac
# Edit bot/main.py, centralized_api/app.py, etc.
```

### 2. Commit & Push
**Terminal Method:**
```bash
cd "/Users/apple/Documents/Personal/startup/bots/telegram bot/python/main_bot_v2/v3"
git add .
git commit -m "feat: describe what changed"
git push origin main
```

**VS Code Method:**
1. Press `Cmd+Shift+G` (Source Control)
2. Click `+` to stage files
3. Write commit message
4. Click `✓` to commit
5. Click `⤴` to push

### 3. VPS Auto-Deploys
**If Webhook Mode:**
- Instant! Check: `docker compose logs -f`

**If Cron Mode:**
- Within 5 minutes. Check: `docker compose ps`

---

## ✅ Verify It Works

### Test 1: Check Services Running
```bash
ssh root@your.vps.ip
docker compose ps

# Should show all running:
# - mongo
# - redis
# - centralized_api
# - bot
# - web
```

### Test 2: Make a Small Change
```bash
# On Mac - Edit any file
# e.g., add a comment to bot/main.py
git add .
git commit -m "test: trigger deployment"
git push origin main

# On VPS - Watch deployment
ssh root@your.vps.ip && docker compose logs -f
```

### Test 3: Check Logs
```bash
ssh root@your.vps.ip
docker compose logs -f bot
# Should see bot running with your code
```

---

## 🆘 If Something Goes Wrong

### Services won't start
```bash
ssh root@your.vps.ip
docker compose logs          # see what failed
docker compose down
docker compose up -d
```

### Code changes aren't deploying
```bash
ssh root@your.vps.ip
# Run deployment manually
/opt/group-assistant-v3/deploy-vps.sh

# Check deployment log
tail -f /var/log/group-assistant-deploy.log
```

### Webhook not working
```bash
ssh root@your.vps.ip
sudo systemctl status webhook
sudo journalctl -u webhook -f
```

---

## 📚 Next Steps

1. **Read**: `SETUP_CHECKLIST.md` (detailed steps)
2. **Run**: `setup-vps.sh` (one-time VPS setup)
3. **Use**: Daily workflow above
4. **Monitor**: Check logs regularly

---

## 🎓 Learn More

### How It Works
- Read `VISUAL_WORKFLOW.md` — See the flow diagrams
- Read `VPS_DEPLOYMENT.md` — Deep dive into each component

### Quick Reference
- Print `SYNC_QUICK_START.md` — Keep handy for daily use
- Reference `SETUP_CHECKLIST.md` — Troubleshooting guide

---

## ⚡ Quick Commands

```bash
# Mac - Commit and push
git push origin main

# VPS - SSH and check status
ssh root@your.vps.ip
docker compose ps
docker compose logs -f

# VPS - Manual deployment
/opt/group-assistant-v3/deploy-vps.sh

# VPS - View deployment history
tail -f /var/log/group-assistant-deploy.log
```

---

## 🚀 Ready?

```
1. SSH to VPS and run setup-vps.sh ← Do this first!
2. Add GitHub webhook (if webhook mode)
3. Make a change and push
4. Watch VPS auto-deploy ✨
5. Check logs to verify
```

**You're all set! Happy coding! 🎉**

---

## 📞 Support

All documentation is in your GitHub repo. If something isn't clear:

1. Check the relevant guide:
   - `SYNC_QUICK_START.md` — Quick questions
   - `VPS_DEPLOYMENT.md` — Detailed setup
   - `VISUAL_WORKFLOW.md` — How it works

2. Look at logs for clues:
   - VPS logs: `docker compose logs`
   - Deployment logs: `/var/log/group-assistant-deploy.log`
   - Webhook logs: `sudo journalctl -u webhook -f`

3. Run `setup-vps.sh` again if needed (idempotent - safe to re-run)
