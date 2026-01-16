# Quick Reference: VS Code → GitHub → VPS Sync

## 🔄 Daily Workflow

### On Your Mac (VS Code)

```bash
# 1. Make code changes
# Edit files in VS Code

# 2. Commit & push
cd "/Users/apple/Documents/Personal/startup/bots/telegram bot/python/main_bot_v2/v3"
git add .
git commit -m "your message here"
git push origin main

# That's it! VPS auto-deploys...
```

### VS Code GUI (Alternative)

- `Cmd+Shift+G` → Source Control
- Click `+` to stage files
- Write commit message
- Click ✓ to commit
- Click ⤴ to push

---

## 🚀 VPS First-Time Setup (One Command)

```bash
# SSH to your VPS
ssh root@your.vps.ip

# Run this one command (it does everything):
bash -c "
mkdir -p /opt && cd /opt
git clone https://github.com/Nikhil-ig/group-assistant-v3.git
cd group-assistant-v3
chmod +x deploy-vps.sh

# Create bot/.env
cat > bot/.env <<'EOF'
TELEGRAM_BOT_TOKEN=your_actual_token_from_botfather
API_V2_URL=http://api_v2:8002
API_V2_KEY=your_shared_api_key_here
LOG_LEVEL=INFO
EOF

# Create api_v2/.env
cat > api_v2/.env <<'EOF'
MONGODB_URL=mongodb://root:your_password@mongo:27017/telegram_bot?authSource=admin
REDIS_URL=redis://:your_password@redis:6379/0
API_KEY=your_shared_api_key_here
SECRET_KEY=your_secret_key_min_32_chars
ENVIRONMENT=production
DEBUG=false
EOF

# Secure .env files
chmod 600 bot/.env api_v2/.env

# Test deployment
./deploy-vps.sh
"
```

---

## 🪝 Option 1: Auto-Deploy on Every Push (Webhook)

```bash
# On VPS:
sudo apt-get install -y webhook

sudo mkdir -p /etc/webhook
sudo cat > /etc/webhook/hooks.json <<'EOF'
[
  {
    "id": "group-assistant-deploy",
    "execute-command": "/opt/group-assistant-v3/deploy-vps.sh",
    "trigger-rule": {
      "match": {
        "type": "payload",
        "parameter": { "source": "payload", "name": "ref" },
        "value": "refs/heads/main"
      }
    }
  }
]
EOF

sudo cat > /etc/systemd/system/webhook.service <<'EOF'
[Unit]
Description=GitHub Webhook Service
After=network.target
[Service]
Type=simple
ExecStart=/usr/bin/webhook -hooks /etc/webhook/hooks.json -port 9000
Restart=always
RestartSec=10
[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable webhook
sudo systemctl start webhook
```

Then add GitHub webhook: https://github.com/Nikhil-ig/group-assistant-v3/settings/hooks/new
- **URL**: `http://your.vps.ip:9000/hooks/group-assistant-deploy`
- **Events**: Push events only

---

## 🕐 Option 2: Auto-Deploy Every 5 Minutes (Cron)

```bash
# On VPS:
crontab -e

# Add this line:
*/5 * * * * /opt/group-assistant-v3/deploy-vps.sh >> /var/log/group-assistant-deploy.log 2>&1
```

---

## 📊 Monitor VPS

```bash
# SSH to VPS
ssh root@your.vps.ip

# Check services running
docker compose ps

# View bot logs
docker compose logs -f bot

# View all logs
docker compose logs -f

# View deployment log
tail -f /var/log/group-assistant-deploy.log

# View webhook log (if using webhook)
sudo journalctl -u webhook -f
```

---

## 🔧 Troubleshoot

```bash
# VPS: Run deployment manually
/opt/group-assistant-v3/deploy-vps.sh

# VPS: Check if services started
docker compose ps

# VPS: See what went wrong
docker compose logs

# VPS: Check webhook is listening
netstat -tlnp | grep 9000

# Local: Verify code pushed
git log --oneline | head
```

---

## 🔐 Important Files (Never Commit)

These exist ONLY on VPS:
- `bot/.env` ← Your Telegram bot token
- `api_v2/.env` ← Database passwords

These are safe to commit:
- `bot/.env.example` ← Template (no real values)
- `api_v2/.env.example` ← Template (no real values)
- `deploy-vps.sh` ← Deployment script
- `webhook-receiver.sh` ← Webhook listener
- `VPS_DEPLOYMENT.md` ← Full documentation

---

## Full Documentation

See `VPS_DEPLOYMENT.md` for complete setup guide.

---

## Support

| Issue | Command |
|-------|---------|
| Services won't start | `docker compose logs` |
| Bot not responding | `docker compose logs bot` |
| API errors | `docker compose logs api_v2` |
| Deployment failed | `tail -f /var/log/group-assistant-deploy.log` |
| Webhook not working | `sudo journalctl -u webhook -f` |
