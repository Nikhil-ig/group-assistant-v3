# Complete Sync Workflow: VS Code → GitHub → VPS

**Everything is now set up for you to sync code from your Mac to VPS with automatic deployment!**

---

## 📋 What Was Set Up

### Files Created
✅ **`setup-vps.sh`** — One-command VPS initialization (handles everything)
✅ **`deploy-vps.sh`** — Deployment script (pulls code, restarts services)
✅ **`webhook-receiver.sh`** — GitHub webhook listener
✅ **`VPS_DEPLOYMENT.md`** — Complete VPS setup guide
✅ **`SYNC_QUICK_START.md`** — Quick reference for daily workflow
✅ **`bot/.env.example`** — Template for bot secrets
✅ **`centralized_api/.env.example`** — Template for API secrets
✅ **`bot/main.py`** — Updated to load `.env` file automatically

### What's Pushed to GitHub
- ✅ Code changes (bot updated to load `.env`)
- ✅ All deployment automation scripts
- ✅ Documentation and templates
- ✅ `.env` files are NOT committed (safe!)

---

## 🚀 Quick Start: Set Up VPS in 2 Minutes

### SSH to VPS and Run One Command

```bash
ssh root@your.vps.ip

bash -c "$(curl -fsSL https://raw.githubusercontent.com/Nikhil-ig/group-assistant-v3/main/setup-vps.sh)"
```

Or copy the setup script manually:
```bash
ssh root@your.vps.ip
# Then paste the content of setup-vps.sh and press Enter
```

**The script will:**
1. ✅ Clone the repository
2. ✅ Prompt you for secrets (bot token, API key, passwords)
3. ✅ Create `.env` files on VPS (never committed to git)
4. ✅ Offer choice: Webhook (auto-deploy) or Cron (deploy every 5 min)
5. ✅ Run first deployment
6. ✅ Start all services

That's it!

---

## 📱 Daily Workflow

### 1️⃣ Make Changes on Your Mac

```bash
# In VS Code - edit files as needed
# bot/main.py, centralized_api/app.py, etc.
```

### 2️⃣ Commit & Push

**Via Terminal:**
```bash
cd "/Users/apple/Documents/Personal/startup/bots/telegram bot/python/main_bot_v2/v3"
git add .
git commit -m "your message"
git push origin main
```

**Via VS Code UI:**
- Press `Cmd+Shift+G` (Source Control)
- Stage changes (click `+`)
- Write commit message
- Click `✓` to commit
- Click `⤴` to push

### 3️⃣ VPS Auto-Deploys

**If Webhook Mode:**
- ✅ Deploys immediately when you push
- Check status: `ssh root@your.vps.ip && docker compose ps`

**If Cron Mode:**
- ✅ Deploys within 5 minutes
- Check status: `ssh root@your.vps.ip && tail -f /var/log/group-assistant-deploy.log`

---

## 🔐 Security Notes

### .env Files (VPS ONLY, Never Commit)
```
bot/.env                  ← Bot token (secret!)
centralized_api/.env      ← Database passwords (secret!)
```

### Safe to Commit
```
bot/.env.example          ← Template (no real values)
centralized_api/.env.example  ← Template (no real values)
setup-vps.sh              ← Setup automation
deploy-vps.sh             ← Deployment script
VPS_DEPLOYMENT.md         ← Documentation
```

**Verify .env is ignored:**
```bash
cat .gitignore | grep "\.env"
# Should show: .env and bot/.env
```

---

## 🛠️ Troubleshooting

### Check if VPS services are running
```bash
ssh root@your.vps.ip
docker compose ps
```

### View live logs
```bash
ssh root@your.vps.ip
docker compose logs -f bot          # Bot logs
docker compose logs -f centralized_api  # API logs
docker compose logs                 # All logs
```

### Run deployment manually
```bash
ssh root@your.vps.ip
/opt/group-assistant-v3/deploy-vps.sh
```

### Check deployment status
```bash
ssh root@your.vps.ip
tail -f /var/log/group-assistant-deploy.log
```

### Webhook not working?
```bash
ssh root@your.vps.ip
sudo journalctl -u webhook -f
sudo systemctl status webhook
```

---

## 📚 Documentation Files

All available in your repo:

| File | Purpose |
|------|---------|
| `SYNC_QUICK_START.md` | Daily quick reference |
| `VPS_DEPLOYMENT.md` | Complete setup & troubleshooting |
| `setup-vps.sh` | Auto-setup script |
| `deploy-vps.sh` | Deployment automation |
| `bot/.env.example` | Bot config template |
| `centralized_api/.env.example` | API config template |

---

## ✅ Checklist: Everything is Set Up

- [x] Bot code updated to load `.env` automatically
- [x] Deployment scripts created (`deploy-vps.sh`, `setup-vps.sh`)
- [x] Webhook listener created (`webhook-receiver.sh`)
- [x] Documentation complete (`VPS_DEPLOYMENT.md`, `SYNC_QUICK_START.md`)
- [x] `.env` templates provided (`.env.example` files)
- [x] All files pushed to GitHub
- [x] `.env` files properly gitignored

---

## 🎯 Next Steps

1. **SSH to VPS:**
   ```bash
   ssh root@your.vps.ip
   ```

2. **Run setup script:**
   ```bash
   bash -c "$(curl -fsSL https://raw.githubusercontent.com/Nikhil-ig/group-assistant-v3/main/setup-vps.sh)"
   ```
   Or copy-paste the content of `setup-vps.sh`

3. **Follow prompts:**
   - Enter bot token (from @BotFather)
   - Enter shared API key
   - Enter MongoDB password (min 20 chars)
   - Enter Redis password (min 20 chars)
   - Choose deployment method (webhook or cron)

4. **Add GitHub Webhook (if webhook mode):**
   - https://github.com/Nikhil-ig/group-assistant-v3/settings/hooks/new
   - URL: `http://your.vps.ip:9000/hooks/group-assistant-deploy`
   - Events: Push events only

5. **Start using:**
   ```bash
   # On your Mac
   git push origin main
   
   # VPS auto-deploys!
   ```

---

## 🔗 Repository Links

- **GitHub Repo**: https://github.com/Nikhil-ig/group-assistant-v3
- **Main Branch**: https://github.com/Nikhil-ig/group-assistant-v3/tree/main
- **Add Webhook**: https://github.com/Nikhil-ig/group-assistant-v3/settings/hooks/new

---

## 💡 Tips

- **Make scripts executable first:**
  ```bash
  chmod +x setup-vps.sh deploy-vps.sh webhook-receiver.sh
  ```

- **Generate secret key:**
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  ```

- **Test webhook manually:**
  ```bash
  curl -X POST http://your.vps.ip:9000/hooks/group-assistant-deploy
  ```

- **Monitor deployment:**
  ```bash
  ssh root@your.vps.ip
  while true; do docker compose ps; sleep 5; done
  ```

---

**Your sync workflow is complete! Edit code → Push → VPS auto-deploys 🚀**
