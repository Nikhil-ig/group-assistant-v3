# VPS Deployment Setup Guide

Complete guide to sync your code from GitHub to VPS with automatic restarts.

## Prerequisites

- VPS with Ubuntu/Debian
- Docker & Docker Compose installed
- Git installed
- SSH access to VPS
- GitHub repository (Nikhil-ig/group-assistant-v3)

## Step 1: Initial VPS Setup (One-Time)

### 1.1 SSH to VPS and prepare directories

```bash
ssh root@your.vps.ip

# Create deployment directory
mkdir -p /opt
cd /opt

# Clone repository
git clone https://github.com/Nikhil-ig/group-assistant-v3.git
cd group-assistant-v3

# Verify structure
ls -la
# Should show: docker-compose.yml, deploy-vps.sh, bot/, centralized_api/, web/, etc.
```

### 1.2 Create .env files on VPS (NEVER commit these)

These files contain secrets and should only exist on VPS.

```bash
# Create bot/.env
cat > bot/.env <<'EOF'
TELEGRAM_BOT_TOKEN=your_actual_token_from_botfather
CENTRALIZED_API_URL=http://centralized_api:8000
CENTRALIZED_API_KEY=your_shared_api_key_here
LOG_LEVEL=INFO
EOF

# Create centralized_api/.env
cat > centralized_api/.env <<'EOF'
MONGODB_URL=mongodb://root:your_secure_password@mongo:27017/telegram_bot?authSource=admin
REDIS_URL=redis://:your_secure_redis_password@redis:6379/0
API_KEY=your_shared_api_key_here
SECRET_KEY=your_secret_key_minimum_32_chars
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
EOF

# Secure the files (only root can read)
chmod 600 bot/.env centralized_api/.env

# Verify they're gitignored
cat .gitignore | grep "\.env"
# If not present, add them:
echo "bot/.env" >> .gitignore
echo "centralized_api/.env" >> .gitignore
git add .gitignore
git commit -m "chore: ensure .env files are ignored"
git push origin main
```

### 1.3 Make deployment script executable

```bash
chmod +x deploy-vps.sh
chmod +x webhook-receiver.sh
```

### 1.4 Test manual deployment

```bash
# Run deployment manually
./deploy-vps.sh

# Watch the output
tail -f /var/log/group-assistant-deploy.log

# Check services are running
docker compose ps

# View logs
docker compose logs -f
```

---

## Step 2: Set Up Automatic Deployment

### Option A: Webhook (Real-Time, Recommended)

Automatically deploy when you push to GitHub.

**2A.1 Install webhook package**

```bash
sudo apt-get update
sudo apt-get install -y webhook
```

**2A.2 Create webhook configuration**

```bash
sudo mkdir -p /etc/webhook
sudo cat > /etc/webhook/hooks.json <<'EOF'
[
  {
    "id": "group-assistant-deploy",
    "execute-command": "/opt/group-assistant-v3/deploy-vps.sh",
    "command-working-directory": "/opt/group-assistant-v3",
    "trigger-rule": {
      "match": {
        "type": "payload",
        "parameter": {
          "source": "payload",
          "name": "ref"
        },
        "value": "refs/heads/main"
      }
    }
  }
]
EOF

sudo chown webhook:webhook /etc/webhook/hooks.json
sudo chmod 600 /etc/webhook/hooks.json
```

**2A.3 Set up webhook as systemd service**

```bash
sudo cat > /etc/systemd/system/webhook.service <<'EOF'
[Unit]
Description=GitHub Webhook Service
After=network.target

[Service]
Type=simple
User=webhook
WorkingDirectory=/etc/webhook
ExecStart=/usr/bin/webhook -hooks /etc/webhook/hooks.json -port 9000 -verbose
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable webhook
sudo systemctl start webhook
sudo systemctl status webhook

# Check it's listening
netstat -tlnp | grep 9000
```

**2A.4 Add webhook to GitHub**

1. Go to: https://github.com/Nikhil-ig/group-assistant-v3/settings/hooks/new
2. Fill in the form:
   - **Payload URL**: `http://your.vps.ip:9000/hooks/group-assistant-deploy`
   - **Content type**: `application/json`
   - **Secret**: (optional but recommended - generate a strong random string)
   - **Events**: "Just the push event"
   - **Active**: ✅ Check this

3. Click "Add webhook"

4. Test it by making a small change in VS Code and pushing:
   ```bash
   # From your Mac
   cd "/Users/apple/Documents/Personal/startup/bots/telegram bot/python/main_bot_v2/v3"
   echo "# Test" >> README.md
   git add README.md
   git commit -m "test: webhook trigger"
   git push origin main
   
   # On VPS, watch deployment
   tail -f /var/log/group-assistant-deploy.log
   ```

---

### Option B: Cron Job (Every 5 Minutes)

Simple alternative if webhook is too complex.

```bash
# Edit crontab
crontab -e

# Add this line (runs every 5 minutes)
*/5 * * * * /opt/group-assistant-v3/deploy-vps.sh >> /var/log/group-assistant-deploy.log 2>&1

# Verify it's added
crontab -l
```

**⚠️ Note**: With cron, there's a 5-minute delay between push and deployment.

---

## Step 3: Daily Workflow (VS Code → GitHub → VPS)

### 3.1 Make changes locally

```bash
# On your Mac
cd "/Users/apple/Documents/Personal/startup/bots/telegram bot/python/main_bot_v2/v3"

# Make code changes
# Edit files as needed
```

### 3.2 Commit and Push

**Option 1: Using Terminal**
```bash
git add .
git commit -m "feat: description of changes"
git push origin main
```

**Option 2: Using VS Code UI**
- Press `Cmd+Shift+G` (Source Control)
- Click "+" to stage changes
- Write commit message
- Click checkmark to commit
- Click "⤴" to push

### 3.3 VPS Auto-Deploys

- **Webhook mode**: Deploys immediately
- **Cron mode**: Deploys within 5 minutes

Verify on VPS:
```bash
# SSH to VPS
ssh root@your.vps.ip

# Check deployment status
tail -f /var/log/group-assistant-deploy.log

# View services
docker compose ps

# View bot logs
docker compose logs -f bot
```

---

## Troubleshooting

### Webhook not triggering?

```bash
# Check webhook service
sudo systemctl status webhook
sudo systemctl restart webhook

# Check logs
sudo journalctl -u webhook -f

# Verify listening on port 9000
sudo netstat -tlnp | grep 9000

# Test webhook manually
curl -X POST http://localhost:9000/hooks/group-assistant-deploy
```

### Deployment script errors?

```bash
# Run manually
/opt/group-assistant-v3/deploy-vps.sh

# View detailed logs
cat /var/log/group-assistant-deploy.log

# Check Docker
docker compose logs
docker compose ps
```

### Services won't start?

```bash
# Check .env files exist
ls -la bot/.env centralized_api/.env

# Rebuild from scratch
cd /opt/group-assistant-v3
docker compose down -v  # Remove volumes
docker compose build --no-cache
docker compose up -d

# Check for errors
docker compose logs
```

### SSH key authentication issues?

If webhook needs to pull but can't authenticate:

```bash
# Generate SSH key on VPS
ssh-keygen -t ed25519 -f /root/.ssh/github -C "vps-deploy"

# Add to GitHub
# 1. Copy public key
cat /root/.ssh/github.pub

# 2. Go to: https://github.com/settings/keys
# 3. Click "New SSH key"
# 4. Paste the public key
# 5. Title: "VPS Webhook"

# 6. Configure git to use SSH key
git config --global core.sshCommand "ssh -i /root/.ssh/github"

# Or update the repo URL to use SSH
cd /opt/group-assistant-v3
git remote set-url origin git@github.com:Nikhil-ig/group-assistant-v3.git
```

---

## Monitoring & Logs

### View real-time logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f bot
docker compose logs -f centralized_api

# Deployment log
tail -f /var/log/group-assistant-deploy.log
```

### Check service status

```bash
docker compose ps

# Expected output:
# NAME                  STATUS
# mongo                 Up X minutes
# redis                 Up X minutes
# centralized_api       Up X minutes
# bot                   Up X minutes
# web                   Up X minutes (optional)
```

### Restart services manually

```bash
# Restart all
docker compose restart

# Restart specific service
docker compose restart bot

# Stop and start fresh
docker compose down
docker compose up -d
```

---

## Security Best Practices

1. **Never commit `.env` files**
   ```bash
   # Verify in .gitignore
   cat .gitignore | grep "\.env"
   ```

2. **Use strong passwords**
   - TELEGRAM_BOT_TOKEN: From @BotFather
   - MONGO passwords: min 20 characters
   - REDIS password: min 20 characters
   - SECRET_KEY: Use `python -c "import secrets; print(secrets.token_urlsafe(32))"`

3. **Restrict file permissions**
   ```bash
   chmod 600 bot/.env centralized_api/.env
   ```

4. **Use SSH for git (not HTTPS)**
   - Reduces token exposure
   - See "SSH key authentication" in troubleshooting

5. **Enable GitHub branch protection**
   - https://github.com/Nikhil-ig/group-assistant-v3/settings/branches
   - Require reviews before merge
   - Require status checks to pass

---

## Next Steps

1. ✅ Clone repo on VPS
2. ✅ Create `.env` files (secrets)
3. ✅ Make `deploy-vps.sh` executable
4. ✅ Test manual deployment
5. ✅ Set up webhook or cron
6. ✅ Add GitHub webhook URL
7. ✅ Test full cycle: edit code → push → auto-deploy

## Quick Checklist

- [ ] VPS has Docker & Docker Compose
- [ ] Repository cloned to `/opt/group-assistant-v3`
- [ ] `bot/.env` and `centralized_api/.env` created with actual tokens
- [ ] `.env` files have `chmod 600` permissions
- [ ] `deploy-vps.sh` is executable
- [ ] Manual deployment works: `./deploy-vps.sh`
- [ ] Webhook service installed and running (or cron job added)
- [ ] GitHub webhook configured (if using webhook mode)
- [ ] Test: push a change and verify auto-deployment

---

## Support

- **Bot logs**: `docker compose logs -f bot`
- **API logs**: `docker compose logs -f centralized_api`
- **Deployment logs**: `tail -f /var/log/group-assistant-deploy.log`
- **Webhook logs**: `sudo journalctl -u webhook -f`
