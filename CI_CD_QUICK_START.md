# CI/CD Quick Reference Guide

Quick reference for setting up and managing your Telegram bot's CI/CD pipeline.

## 🚀 Quick Start (5 minutes)

### 1. Prepare GitHub Secrets (2 min)

Go to: **Settings → Secrets and variables → Actions → New repository secret**

Add these secrets:

```
TELEGRAM_TOKEN          = Your bot token from @BotFather
MONGODB_URL            = mongodb://admin:password@host:27017/telegram_bot
JWT_SECRET             = $(openssl rand -hex 32)  # Generate once
SERVER_HOST            = your-server-ip-or-domain
SERVER_USER            = ubuntu  # or your SSH user
SERVER_SSH_KEY         = Your private SSH key content
SERVER_PORT            = 22
SLACK_WEBHOOK_URL      = Your Slack webhook (optional)
```

### 2. Test Locally (1 min)

```bash
docker-compose up -d
./scripts/validate-deployment.sh
```

### 3. Push Code (1 min)

```bash
git add .github/workflows/deploy.yml Dockerfile docker-compose.yml scripts/
git commit -m "Add CI/CD pipeline"
git push origin main
```

### 4. Monitor Deployment (1 min)

Go to: **Actions → Latest workflow → Watch execution**

Done! 🎉

---

## 📋 Pre-Deployment Checklist

- [ ] All GitHub Secrets configured
- [ ] SSH key pair generated on server
- [ ] Server firewall configured (ports 22, 80, 443)
- [ ] .env file created with real values
- [ ] Docker installed on server
- [ ] Backups enabled (`./scripts/backup.sh schedule`)
- [ ] Monitoring configured
- [ ] Slack webhook added (optional)

---

## 🔄 GitHub Actions Workflow

### When Workflows Run

| Trigger | Runs Jobs | Result |
|---------|-----------|--------|
| `git push origin main` | test → lint → security → build | Builds image, doesn't deploy |
| `git push origin production` | test → lint → security → build → deploy | Full deployment to server |
| **Manual trigger** | All | Full deployment (use Actions tab) |
| **Pull request** | test → lint → security | Checks only, no deployment |

### Job Pipeline

```
Push Code
  ↓
[test] (pytest + coverage)
  ↓ (if passed)
[lint] (Black, isort, Flake8)
  ↓ (if passed)
[security] (Bandit, Safety)
  ↓ (if passed)
[build] (Docker image)
  ↓ (if pushing to production)
[deploy] (SSH to server)
  ↓
Slack notification
```

---

## 🚢 Deployment Branches

### Development Workflow

```bash
# For testing (doesn't deploy)
git checkout -b feature/new-feature
git push origin feature/new-feature
# Goes through: test → lint → security → build
# Does NOT deploy

# When ready for production
git checkout production
git merge feature/new-feature
git push origin production
# Goes through: test → lint → security → build → deploy
# Automatically deploys to server!
```

### Quick Production Push

```bash
# Direct push to production (for hotfixes)
git checkout production
git cherry-pick <commit>  # Or make changes
git push origin production
# Auto-deploys immediately
```

---

## 🔑 SSH Key Setup (One-time)

### On Your Server

```bash
# Generate deployment key
ssh-keygen -t ed25519 -f ~/.ssh/deploy_key -N ""

# Show public key (to add to authorized_keys)
cat ~/.ssh/deploy_key.pub

# Add to authorized keys
cat ~/.ssh/deploy_key.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

### In GitHub Secrets

```bash
# Show private key content
cat ~/.ssh/deploy_key

# Copy entire output and paste into GitHub Secrets as SERVER_SSH_KEY
```

### Verify Connection

```bash
# On your local machine
ssh -i ~/.ssh/deploy_key <SERVER_USER>@<SERVER_HOST> echo "Success!"
```

---

## 📊 Monitoring Deployments

### GitHub Actions Dashboard

```
1. Go to repository → Actions
2. See all workflow runs
3. Click on a run to see details
4. Click on a job to see logs
5. Red ❌ = Failed, Green ✅ = Success
```

### Check Deployment Status

```bash
# SSH to server
ssh user@server

# Check running containers
docker-compose ps

# View logs
docker-compose logs -f telegram-bot

# Health check
curl http://localhost:8000/health
```

### Slack Notifications

Deployment status sent automatically to Slack:

```
✅ Deployment successful on 2024-01-15 10:30:00
   Commit: abc123def456
   Branch: production
   Image: ghcr.io/your-org/telegram-bot:production
```

Failed deployment:

```
❌ Deployment failed on 2024-01-15 10:35:00
   Job: test
   Error: Test suite failed
   Check: https://github.com/your-org/repo/actions/run/12345
```

---

## 🆘 Troubleshooting

### Workflow Stuck in "Queued"

**Problem**: Actions tab shows job waiting

**Solution**:
```bash
# Check GitHub Actions quota
# Go to: Settings → Actions → General → Job execution settings
# Or try re-running
```

### Build Fails: "Docker login failed"

**Problem**: `Error: Failed to authenticate to registry`

**Solution**:
```bash
# Check GHCR_TOKEN in secrets
# Should be a GitHub token with `write:packages` permission
# Generate new one: Settings → Developer settings → Personal access tokens
```

### Deployment Fails: "SSH: connection refused"

**Problem**: Cannot connect to server

**Solution**:
```bash
# Check SERVER_SSH_KEY is complete (including -----BEGIN etc)
# Verify SERVER_HOST and SERVER_PORT
# Check firewall: sudo ufw allow 22/tcp
# Test locally: ssh -i key user@host
```

### Tests Fail But Should Pass

**Problem**: Local tests pass, GitHub fails

**Solution**:
```bash
# GitHub uses Python 3.10 (check requirements.txt)
python3.10 --version

# MongoDB may not be available in test
# Check .github/workflows/deploy.yml for MongoDB service config
```

### Deployed But Services Don't Start

**Problem**: Deployment succeeds but bot doesn't work

**Solution**:
```bash
# Check server logs
docker-compose logs -f telegram-bot

# Validate deployment
./scripts/validate-deployment.sh

# Check environment variables
docker-compose config | grep TELEGRAM_TOKEN

# Restart services
docker-compose restart
```

---

## 🔧 Customizing CI/CD

### Change Test Command

Edit `.github/workflows/deploy.yml`:

```yaml
- name: Run Tests
  run: |
    pytest tests/ --cov=. --cov-report=xml
    # Change this line ↑
```

### Add Lint Tool

```yaml
- name: Run Custom Lint
  run: |
    pip install custom-linter
    custom-linter check
```

### Change Deployment Target

```yaml
deploy:
  if: github.ref == 'refs/heads/production'  # Change this
```

### Add Pre-deployment Hook

```yaml
- name: Run Pre-deployment Script
  if: github.ref == 'refs/heads/production'
  run: |
    ./scripts/pre-deploy.sh
```

---

## 📈 Performance Tips

### Speed Up Builds

1. **Use Docker cache**
   - Already in Dockerfile (multi-stage)
   - Keep dependencies stable

2. **Parallel jobs**
   - test, lint, security run in parallel
   - They don't depend on each other

3. **GitHub Actions cache**
   - pip cache configured
   - Docker layer cache enabled

### Reduce Image Size

```dockerfile
# In Dockerfile - already optimized:
- Use python:3.10-slim (not full python)
- Multi-stage build (removes build dependencies)
- Only copy needed files
```

Current image size: ~300MB (reasonable for Python app)

### Database Performance

In docker-compose.yml:
```yaml
mongodb:
  # Index on common fields
  environment:
    MONGODB_OPLOG_SIZE_MB: 100  # Increase if needed
```

---

## 🔒 Security Best Practices

### Secrets Management

```bash
# ✅ DO: Store in GitHub Secrets
TELEGRAM_TOKEN=****** (in GitHub Secrets)

# ❌ DON'T: Hardcode in code
TELEGRAM_TOKEN=abc123  # NEVER!

# ❌ DON'T: Commit .env to git
# Use .env.example instead
```

### Access Control

```bash
# Only production branch can deploy
# See: .github/workflows/deploy.yml
if: github.ref == 'refs/heads/production'

# Other branches only build, don't deploy
```

### Keep Images Updated

```bash
# Docker images automatically pulled latest
# python:3.10-slim → latest patch version
# mongo:latest → latest MongoDB version

# To use specific versions:
# Change Dockerfile to: FROM python:3.10.12
# Change docker-compose.yml to: image: mongo:6.0.5
```

---

## 📝 Workflow File Reference

### Key Sections

```yaml
name: Deploy                          # Workflow name
on:
  push:
    branches: [main, production]      # When to run
  pull_request:
    branches: [main]
  workflow_dispatch:                  # Manual trigger

jobs:
  test:
    runs-on: ubuntu-latest            # Runner OS
    services:
      mongodb: ...                    # Services for tests
    steps:
      - uses: actions/checkout@v3     # Get code
      - uses: actions/setup-python@v4 # Setup Python
      - run: pytest                   # Run tests

  deploy:                             # Only on production
    if: github.ref == 'refs/heads/production'
    needs: [test, lint, security, build]  # Dependencies
```

---

## 🎯 Common Tasks

### Manual Deployment

```bash
# Option 1: Push to production branch
git push origin production

# Option 2: Manual trigger in GitHub Actions
# Actions tab → Deploy (workflow) → Run workflow → Branch: production
```

### Skip Deployment (Just Build)

```bash
# Push to main (not production)
git push origin main
# Builds and tests, but doesn't deploy
```

### Deploy Specific Commit

```bash
git tag v1.2.3 <commit>
git push origin v1.2.3
# Edit workflow to add: tags: [v*]
```

### Check Deployment History

```bash
# GitHub: Actions → Filter by branch/status
# Server: git log --oneline
# Docker: docker image ls telegram-bot
```

---

## 📚 Full Documentation

For detailed information, see:

- **DEPLOYMENT_GUIDE.md** - Complete deployment guide
- **scripts/README.md** - Script documentation
- **.github/workflows/deploy.yml** - GitHub Actions config
- **Dockerfile** - Docker build configuration
- **docker-compose.yml** - Service orchestration

---

## 🆘 Getting Help

1. **Check logs**: Actions tab → Workflow run → Job logs
2. **Validate locally**: `./scripts/validate-deployment.sh`
3. **Monitor system**: `./scripts/monitor.sh`
4. **Check documentation**: See links above
5. **Debug deployment**: `ssh user@server && docker-compose logs`

---

## ✅ Checklist for Production

Before going live:

- [ ] GitHub Secrets all configured
- [ ] SSH keys working
- [ ] Local docker-compose test passing
- [ ] Backup strategy configured
- [ ] Monitoring alerts enabled
- [ ] Slack notifications working
- [ ] Rollback procedure tested
- [ ] SSL certificates ready
- [ ] Database backups working
- [ ] Production branch protection enabled

---

**Last Updated**: 2024-01-15  
**Version**: 1.0
