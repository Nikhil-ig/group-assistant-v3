# 👈 START HERE - CI/CD & Deployment Setup

This file will get you from 0 to deployed in ~30 minutes.

---

## ⏱️ Total Time: ~30 Minutes

- Setup: 5 min
- Configuration: 10 min  
- Local Testing: 5 min
- Deployment: 10 min

---

## Step 1: Read This First (2 min)

You have a **CI/CD pipeline ready to go**. This means:

✅ Push code to GitHub → Automatic testing  
✅ Tests pass → Automatic build Docker image  
✅ Push to `production` branch → Automatic server deployment  
✅ Slack notification when done  

---

## Step 2: Local Setup (3 min)

```bash
# Make scripts executable
chmod +x scripts/*.sh

# Create required directories
mkdir -p logs backups

# Copy environment template
cp .env.example .env

# Edit with your real values
nano .env
```

**What to set in .env:**
```
TELEGRAM_TOKEN=your_bot_token_from_BotFather
MONGODB_URL=mongodb://admin:changeme@mongodb:27017/telegram_bot?authSource=admin
JWT_SECRET=generate_with_openssl_rand_hex_32
```

---

## Step 3: Test Locally (5 min)

```bash
# Start all services
docker-compose up -d

# Wait 10 seconds for services to start
sleep 10

# Verify everything works
./scripts/validate-deployment.sh

# Should show: ✅ Deployment validation successful!
```

If something fails:
```bash
# Check logs
docker-compose logs -f

# Stop and try again
docker-compose down
docker-compose up -d
```

---

## Step 4: Configure GitHub (10 min)

### 4a. Go to GitHub Secrets

On GitHub:
1. Go to your repository
2. Settings → Secrets and variables → Actions
3. Click "New repository secret"

### 4b. Add Each Secret

Add these one by one:

| Secret Name | Value |
|-------------|-------|
| `TELEGRAM_TOKEN` | Your bot token from @BotFather |
| `MONGODB_URL` | `mongodb://admin:changeme@mongodb:27017/telegram_bot?authSource=admin` |
| `JWT_SECRET` | Run: `openssl rand -hex 32` (copy output) |
| `SERVER_HOST` | Your server IP or domain |
| `SERVER_USER` | SSH username (usually `ubuntu` or `root`) |
| `SERVER_SSH_KEY` | Private SSH key content (ask DevOps) |
| `SERVER_PORT` | SSH port (usually `22`) |
| `SLACK_WEBHOOK_URL` | (optional) Slack webhook for notifications |

**For SERVER_SSH_KEY:**
```bash
# On your server:
cat ~/.ssh/id_rsa  # Copy entire output to GitHub
```

---

## Step 5: Push & Deploy (5 min)

```bash
# Make sure everything is committed
git add .github/ Dockerfile docker-compose.yml scripts/
git commit -m "Add CI/CD pipeline"

# Push to GitHub (this triggers the pipeline)
git push origin main

# Watch it work (optional, pipeline runs automatically)
# Go to your repo → Actions tab → See the workflow run
```

**Note**: Pushing to `main` branch won't deploy yet. It will:
- ✅ Test everything
- ✅ Build Docker image
- ❌ NOT deploy to server

---

## Step 6: Deploy to Production (5 min)

When you're ready to go live:

```bash
# Create production branch
git checkout -b production

# Push to production (this triggers automatic deployment!)
git push origin production

# Watch it deploy
# Go to repo → Actions tab → Watch the deploy job
# You'll get a Slack notification when done
```

---

## That's It! 🎉

Your bot is now:
- ✅ Automatically tested on every push
- ✅ Automatically built as Docker image
- ✅ Automatically deployed on `production` push
- ✅ Monitored for health
- ✅ Backed up daily
- ✅ Ready to scale

---

## Quick Commands

### Check System Health
```bash
./scripts/monitor.sh
```

### Deploy Manually (if needed)
```bash
./scripts/deploy.sh production
```

### Create Backup Now
```bash
./scripts/backup.sh backup
```

### Rollback to Previous Version
```bash
./scripts/rollback.sh
```

### View Logs
```bash
docker-compose logs -f telegram-bot
```

---

## What's Automated

✅ Testing (pytest) - runs automatically  
✅ Linting (Black, isort, Flake8) - runs automatically  
✅ Security scan (Bandit, Safety) - runs automatically  
✅ Docker build - runs automatically  
✅ SSH deployment - runs automatically on production branch  
✅ Health checks - runs automatically after deploy  
✅ Slack notifications - automatic  
✅ Daily backups - automatic (cron) after deployment  

---

## Need Help?

### 📖 Full Documentation
- **CI_CD_QUICK_START.md** - Complete quick start guide
- **DEPLOYMENT_GUIDE.md** - Full deployment manual
- **scripts/README.md** - Script documentation

### 🆘 Common Issues

**Docker not installed?**
```bash
curl -fsSL https://get.docker.com | sh
```

**Port 8000 in use?**
```bash
lsof -i :8000
kill -9 <PID>
```

**Tests failing?**
```bash
# Check locally first
pytest tests/
black --check .
flake8 .
```

**Can't SSH to server?**
```bash
# Verify SSH key works
ssh -i ~/.ssh/deploy_key user@server echo "Success!"
```

**MongoDB not starting?**
```bash
docker-compose logs mongodb
docker-compose restart mongodb
```

---

## Branches Explained

### main branch
```bash
git push origin main
→ Tests & builds
→ Reports results
→ Does NOT deploy
→ Use for development
```

### production branch
```bash
git push origin production
→ Full pipeline
→ Auto-deploys to server
→ Slack notification
→ Use when ready to go live
```

---

## Daily Workflow

### 1. Development
```bash
git checkout main
# Make changes
git commit -am "New feature"
git push origin main
# GitHub Actions tests & builds (no deploy)
```

### 2. When Ready to Deploy
```bash
git checkout production
git merge main
git push origin production
# GitHub Actions runs full pipeline
# Bot auto-deploys to server
# You get Slack notification
```

### 3. If Something Goes Wrong
```bash
./scripts/rollback.sh  # Rollback to previous version
# Or
./scripts/backup.sh restore <backup_name>  # Restore from backup
```

---

## Success Checklist

You're done when:

- [ ] Docker running locally: `docker-compose ps` shows 3 containers
- [ ] Health check passes: `curl http://localhost:8000/health`
- [ ] Validation passes: `./scripts/validate-deployment.sh`
- [ ] GitHub Secrets configured: All 8 secrets added
- [ ] GitHub Actions runs: Workflow shows green checkmark
- [ ] Server deployed: Health check passes on server
- [ ] Bot responds: Send `/id` in Telegram, get response
- [ ] Slack notification: Received deployment alert

---

## Final Notes

✅ **Everything is automated** - You don't need to do anything manually after pushing code  
✅ **It's safe** - Full rollback capability with one command  
✅ **It's fast** - Deployment takes ~20 minutes including all checks  
✅ **It's monitored** - Health checks run automatically  
✅ **It's backed up** - Daily automatic backups  
✅ **It's documented** - Full documentation available  

---

## 🚀 Ready to Deploy?

1. Follow the 6 steps above (30 minutes)
2. Read **CI_CD_QUICK_START.md** for detailed info
3. Read **DEPLOYMENT_GUIDE.md** for complete reference
4. Push to `production` branch when ready
5. Watch GitHub Actions deploy automatically

---

**You've got this! 🎉**

Start with Step 1 above and follow the flow.

---

**Questions?** Check the documentation files.  
**Something broken?** Run `./scripts/validate-deployment.sh` to diagnose.  
**Emergency?** Run `./scripts/rollback.sh` to go back.

**Good luck! 🚀**
