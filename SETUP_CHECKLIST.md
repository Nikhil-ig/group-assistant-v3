# ✅ VPS Sync Setup Checklist

## Phase 1: Local Setup (Already Done ✨)

- [x] Bot updated to load `.env` automatically
- [x] Created `setup-vps.sh` (one-command VPS setup)
- [x] Created `deploy-vps.sh` (deployment automation)
- [x] Created `.env.example` templates
- [x] Updated `.gitignore` to exclude `.env`
- [x] All code pushed to GitHub
- [x] Documentation written and pushed

**Status: ✅ COMPLETE**

---

## Phase 2: VPS Initial Setup (Do This Once)

### 2.1 SSH to VPS
- [ ] Open terminal
- [ ] Run: `ssh root@your.vps.ip`
- [ ] Enter password

### 2.2 Run Setup Script
Copy and paste ONE of these:

**Option A: Auto-download (requires curl)**
```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/Nikhil-ig/group-assistant-v3/main/setup-vps.sh)"
```

**Option B: Manual copy-paste**
- [ ] Go to: https://github.com/Nikhil-ig/group-assistant-v3/blob/main/setup-vps.sh
- [ ] Click "Raw"
- [ ] Copy all content
- [ ] SSH to VPS
- [ ] Run: `cat > setup-vps.sh << 'EOF'` [paste content] `EOF`
- [ ] Run: `bash setup-vps.sh`

### 2.3 Follow Setup Prompts
- [ ] Enter Telegram Bot Token (from @BotFather)
- [ ] Enter Shared API Key
- [ ] Enter MongoDB password (min 20 characters)
- [ ] Enter Redis password (min 20 characters)
- [ ] Choose deployment method:
  - [ ] **Webhook** (recommended - auto-deploy on push)
  - [ ] **Cron** (simpler - deploy every 5 min)
  - [ ] **Manual** (run `deploy-vps.sh` yourself)

### 2.4 First Deployment
- [ ] Script runs `deploy-vps.sh`
- [ ] Wait for "✅ DEPLOYMENT COMPLETE" message
- [ ] All services start

### 2.5 Verify Services Running
```bash
docker compose ps
# Should show:
# - mongo (Up)
# - redis (Up)
# - centralized_api (Up)
# - bot (Up)
# - web (Up)
```

**Status: After completing setup-vps.sh ✅**

---

## Phase 3: Set Up GitHub Webhook (Only if Webhook Mode)

### 3.1 Get Your VPS IP
```bash
# From VPS, run:
hostname -I
# Copy the IP address
```

### 3.2 Add GitHub Webhook
- [ ] Go to: https://github.com/Nikhil-ig/group-assistant-v3/settings/hooks/new
- [ ] Fill in form:
  - **Payload URL**: `http://YOUR.VPS.IP:9000/hooks/group-assistant-deploy`
  - **Content type**: `application/json`
  - **Secret**: (leave empty or enter a random string)
  - **Events**: ✓ "Just the push event"
  - **Active**: ✓ Checked
- [ ] Click "Add webhook"

### 3.3 Test Webhook
- [ ] Click "Recent Deliveries" tab
- [ ] Should see at least one delivery
- [ ] Click to expand and verify "200 OK" response

**Status: GitHub Webhook Configured ✅**

---

## Phase 4: Daily Workflow (Repeat Every Day)

### 4.1 Make Code Changes
- [ ] Open VS Code on your Mac
- [ ] Edit files (bot/main.py, centralized_api/app.py, etc.)
- [ ] Test locally if needed

### 4.2 Commit & Push
**Option A: Terminal**
```bash
cd "/Users/apple/Documents/Personal/startup/bots/telegram bot/python/main_bot_v2/v3"
git add .
git commit -m "your descriptive message"
git push origin main
```

**Option B: VS Code GUI**
- [ ] Press `Cmd+Shift+G` (Source Control)
- [ ] Click `+` next to each changed file to stage
- [ ] Write commit message in "Message" box
- [ ] Click `✓` (Commit button)
- [ ] Click `⤴` (Push button)

### 4.3 Verify Push
- [ ] See message: "Branch main up-to-date"
- [ ] Open GitHub repo to verify commit appears

### 4.4 VPS Auto-Deploys
- [ ] **Webhook mode**: Instant deployment
  - [ ] SSH: `ssh root@your.vps.ip`
  - [ ] Check: `docker compose logs -f` (should see activity)
  
- [ ] **Cron mode**: Within 5 minutes
  - [ ] SSH: `ssh root@your.vps.ip`
  - [ ] Check: `docker compose ps` (verify all running)

### 4.5 Verify Deployment Success
```bash
ssh root@your.vps.ip

# Check services
docker compose ps

# View logs
docker compose logs -f

# Check specific service
docker compose logs bot

# View deployment log
tail -f /var/log/group-assistant-deploy.log
```

**Status: Code synced and deployed ✅**

---

## Phase 5: Monitoring & Maintenance

### Regular Checks
- [ ] Monitor logs weekly: `ssh root@your.vps.ip && docker compose logs`
- [ ] Check disk space: `df -h`
- [ ] Verify services: `docker compose ps`

### If Services Stop
```bash
ssh root@your.vps.ip
cd /opt/group-assistant-v3

# View error
docker compose logs

# Restart
docker compose down
docker compose up -d

# Verify
docker compose ps
```

### If Deployment Fails
```bash
ssh root@your.vps.ip

# Check deployment log
tail -50 /var/log/group-assistant-deploy.log

# Run manually to see error
/opt/group-assistant-v3/deploy-vps.sh
```

**Status: System monitored ✅**

---

## 🔒 Security Checklist

- [ ] .env files exist ONLY on VPS (never committed)
- [ ] .env files have permissions: `chmod 600`
- [ ] Bot token is from @BotFather (not hardcoded)
- [ ] Database passwords are min 20 characters
- [ ] Secret key is generated with `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- [ ] .gitignore includes: `.env`
- [ ] Never logged secrets in code or configs
- [ ] Backup .env files manually (important!)

---

## 📱 Quick Commands Reference

### On Your Mac (VS Code)
```bash
# View uncommitted changes
git status

# View commit history
git log --oneline | head -10

# Push code
git push origin main

# Pull latest from GitHub
git pull origin main
```

### On VPS
```bash
# SSH to VPS
ssh root@your.vps.ip

# See services running
docker compose ps

# View live logs
docker compose logs -f

# View bot logs only
docker compose logs -f bot

# Stop services
docker compose down

# Start services
docker compose up -d

# Manual deployment
/opt/group-assistant-v3/deploy-vps.sh

# Deployment log
tail -f /var/log/group-assistant-deploy.log

# Exit SSH
exit
```

---

## ❓ Troubleshooting Quick Guide

### "Services won't start"
```bash
ssh root@your.vps.ip
docker compose logs          # see error message
docker compose down -v       # remove volumes
docker compose up -d         # restart
```

### "Webhook not working"
```bash
ssh root@your.vps.ip
sudo systemctl status webhook
sudo journalctl -u webhook -f
# Restart if needed:
sudo systemctl restart webhook
```

### ".env file not found"
```bash
ssh root@your.vps.ip
# Create .env files:
cat > bot/.env <<'EOF'
TELEGRAM_BOT_TOKEN=...
EOF
chmod 600 bot/.env
```

### "Code changes not appearing"
```bash
# Verify pushed locally
git log --oneline | head

# SSH to VPS and check
ssh root@your.vps.ip
cd /opt/group-assistant-v3
git log --oneline | head

# If behind, run manually:
/opt/group-assistant-v3/deploy-vps.sh
```

---

## 📚 Documentation Files

**Read these if you have questions:**

| File | Contents |
|------|----------|
| `SYNC_QUICK_START.md` | Quick 1-2 minute reference |
| `VPS_DEPLOYMENT.md` | Complete setup guide & troubleshooting |
| `VISUAL_WORKFLOW.md` | Diagrams of how everything works |
| `SYNC_SETUP_COMPLETE.md` | Summary & next steps |
| `bot/.env.example` | Bot configuration template |
| `centralized_api/.env.example` | API configuration template |

---

## 🎯 Success Criteria

You're done when:
- [x] VPS setup script runs successfully
- [x] All Docker services running: `docker compose ps`
- [x] Bot responds in Telegram
- [x] API accessible: `curl http://localhost:8000/api/health`
- [x] You can edit code locally, push, and see it update on VPS
- [x] Logs show successful deployments

---

## 🚨 Emergency: Rollback to Previous Version

If you deploy bad code:

```bash
ssh root@your.vps.ip
cd /opt/group-assistant-v3

# Revert to previous commit
git reset --hard HEAD~1

# Rebuild and restart
docker compose build --no-cache
docker compose down
docker compose up -d

# Verify
docker compose ps
```

---

## 📞 Support Resources

- **Bot logs**: `docker compose logs -f bot`
- **API logs**: `docker compose logs -f centralized_api`
- **Deployment logs**: `/var/log/group-assistant-deploy.log`
- **GitHub**: https://github.com/Nikhil-ig/group-assistant-v3
- **Docker Docs**: https://docs.docker.com/compose/

---

## ✨ You're All Set!

```
┌─────────────────────────────────────────┐
│  ✅ VS Code → GitHub → VPS SYNCED      │
│                                         │
│  Edit → Commit → Push → Auto-Deploy    │
└─────────────────────────────────────────┘
```

**Happy coding! 🚀**
