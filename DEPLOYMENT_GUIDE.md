# Telegram Bot - Complete Deployment Guide

This guide covers everything needed to deploy your Telegram bot to production.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Setup](#local-setup)
3. [Docker Setup](#docker-setup)
4. [Server Deployment](#server-deployment)
5. [GitHub Secrets Configuration](#github-secrets-configuration)
6. [Monitoring & Maintenance](#monitoring--maintenance)
7. [Troubleshooting](#troubleshooting)
8. [Rollback Procedures](#rollback-procedures)

---

## Prerequisites

### For Local Development

- Python 3.10+
- MongoDB 5.0+ (or Docker)
- Docker & Docker Compose
- Git
- Node.js 18+ (for frontend development)

### For Production Server

- Ubuntu 22.04 LTS (recommended)
- Docker 20.10+
- Docker Compose 2.0+
- 2GB RAM minimum
- 20GB disk space
- 64-bit processor

### Required Credentials

1. **Telegram Bot Token**: Get from [@BotFather](https://t.me/BotFather)
2. **Telegram User ID**: Use `/id` command in bot chat
3. **MongoDB Credentials**: Or use included Docker MongoDB
4. **JWT Secret**: Generate with `openssl rand -hex 32`
5. **GitHub Secrets** (for CI/CD deployment)

---

## Local Setup

### 1. Clone Repository

```bash
git clone <your-repo-url>
cd v3
```

### 2. Create Environment File

```bash
cp .env.example .env
# Edit .env with your values
nano .env
```

### 3. Install Python Dependencies

```bash
python3.10 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Run Locally (Without Docker)

```bash
python main.py
```

The application will start with:
- API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs
- Telegram Bot: Connected and polling

---

## Docker Setup

### 1. Verify Docker Installation

```bash
docker --version
docker-compose --version
```

### 2. Build Docker Image

```bash
docker build -t telegram-bot:latest .
```

### 3. Start All Services

```bash
docker-compose up -d
```

### 4. Verify Services

```bash
docker-compose ps
docker-compose logs -f telegram-bot
```

### 5. Test Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00",
  "services": {
    "api": "ok",
    "database": "ok",
    "bot": "connected"
  }
}
```

### 6. Stop Services

```bash
docker-compose down
```

### 7. Rebuild After Code Changes

```bash
docker-compose down
docker build -t telegram-bot:latest .
docker-compose up -d
```

---

## Server Deployment

### Step 1: Server Preparation

```bash
# SSH into server
ssh user@your-server-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Create deployment directory
mkdir -p ~/telegram-bot
cd ~/telegram-bot
```

### Step 2: Clone Repository

```bash
git clone <your-repo-url> .
```

### Step 3: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with production values
nano .env
```

Key production settings:
```bash
ENVIRONMENT=production
DEBUG=false
ENABLE_RATE_LIMITING=true
LOG_LEVEL=WARNING
```

### Step 4: Set Permissions

```bash
# Make scripts executable
chmod +x scripts/*.sh

# Create logs directory
mkdir -p logs
sudo chown -R $USER:$USER logs
```

### Step 5: Start Services

```bash
# Start with docker-compose
docker-compose up -d

# Monitor startup
docker-compose logs -f telegram-bot

# Verify health
curl http://localhost:8000/health
```

### Step 6: Configure Firewall

```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP
sudo ufw allow 80/tcp

# Allow HTTPS
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable
```

### Step 7: Setup SSL (Let's Encrypt)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Generate certificate
sudo certbot certonly --standalone -d your-domain.com

# Update docker-compose.yml with SSL paths
```

### Step 8: Configure Nginx (Optional)

The `nginx` service in `docker-compose.yml` provides reverse proxy:

```bash
# Check Nginx status
docker-compose logs nginx

# Reload Nginx configuration
docker-compose exec nginx nginx -t
docker-compose exec nginx nginx -s reload
```

---

## GitHub Secrets Configuration

### For CI/CD Automatic Deployment

1. Go to GitHub repository → Settings → Secrets and variables → Actions
2. Click "New repository secret" and add:

| Secret Name | Value | Notes |
|------------|-------|-------|
| `TELEGRAM_TOKEN` | Your bot token | From @BotFather |
| `MONGODB_URL` | MongoDB connection string | Should be remote for production |
| `JWT_SECRET` | Random 32-char string | Use `openssl rand -hex 32` |
| `SERVER_HOST` | Server IP or domain | For SSH deployment |
| `SERVER_USER` | SSH username | Usually `ubuntu` or `root` |
| `SERVER_SSH_KEY` | Private SSH key | Generated on server |
| `SERVER_PORT` | SSH port | Usually `22` |
| `SLACK_WEBHOOK` | Slack webhook URL | For deployment notifications |
| `GHCR_TOKEN` | GitHub token | For Docker registry access |

### Generate SSH Key for Deployment

On your server:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/deploy_key -N ""
cat ~/.ssh/deploy_key
```

Copy the output and add to GitHub Secrets as `SERVER_SSH_KEY`.

Then authorize it:

```bash
cat ~/.ssh/deploy_key.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

---

## Monitoring & Maintenance

### View Logs

```bash
# All services
docker-compose logs

# Specific service
docker-compose logs telegram-bot
docker-compose logs mongodb

# Follow logs
docker-compose logs -f telegram-bot

# Last 100 lines
docker-compose logs --tail 100 telegram-bot
```

### Monitor Performance

```bash
# Run monitoring script
./scripts/monitor.sh

# Check container stats
docker stats

# Check disk usage
df -h
du -sh logs/
```

### Database Backup

```bash
# Manual backup
docker-compose exec mongodb mongodump --uri="mongodb://admin:changeme@localhost:27017/telegram_bot?authSource=admin" --out=backups/$(date +%Y%m%d_%H%M%S)

# Automated backups happen daily (check docker-compose.yml)
```

### Database Restore

```bash
# Restore from backup
docker-compose exec mongodb mongorestore backups/BACKUP_NAME/mongodb

# Or from backup directory on host
docker-compose exec -T mongodb mongorestore -d telegram_bot backups/BACKUP_NAME/mongodb/telegram_bot
```

---

## Troubleshooting

### Issue: Services won't start

```bash
# Check logs
docker-compose logs

# Verify ports aren't in use
lsof -i :8000
lsof -i :27017

# Check disk space
df -h

# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Issue: Database connection fails

```bash
# Test MongoDB connection
docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')"

# Check MongoDB logs
docker-compose logs mongodb

# Verify network connectivity
docker-compose exec telegram-bot ping mongodb
```

### Issue: API returns 500 errors

```bash
# Check application logs
docker-compose logs telegram-bot

# Verify database has required collections
docker-compose exec mongodb mongosh telegram_bot --eval "db.getCollectionNames()"

# Check API health
curl -v http://localhost:8000/health
```

### Issue: Bot not responding

```bash
# Verify bot token is set
docker-compose exec telegram-bot echo $TELEGRAM_TOKEN

# Check bot connection status
docker-compose logs telegram-bot | grep -i "connected\|error"

# Restart just the bot
docker-compose restart telegram-bot
```

### Issue: High memory/CPU usage

```bash
# Check container resources
docker stats

# Check application logs for infinite loops
docker-compose logs telegram-bot | tail -50

# Restart service
docker-compose restart telegram-bot

# Check for memory leaks
docker-compose exec telegram-bot python -m memory_profiler
```

---

## Rollback Procedures

### Automatic Rollback (via GitHub Actions)

If deployment fails, GitHub Actions automatically:
1. Rolls back to previous image
2. Sends Slack notification
3. No manual intervention needed

### Manual Rollback to Previous Version

```bash
# View available versions
git log --oneline | head -10

# Rollback to specific commit
./scripts/rollback.sh v1.2.0

# Or use Git directly
git revert <commit-hash>
git push origin main
```

### Rollback MongoDB Data

```bash
# List available backups
ls -la backups/

# Restore from specific backup
docker-compose exec -T mongodb mongorestore -d telegram_bot backups/BACKUP_NAME/mongodb/telegram_bot

# Verify restoration
docker-compose exec mongodb mongosh telegram_bot --eval "db.users.countDocuments()"
```

---

## Deployment Checklist

Before deploying to production, verify:

- [ ] All environment variables set in `.env`
- [ ] MongoDB credentials configured
- [ ] JWT secret generated (not using defaults)
- [ ] Telegram bot token obtained from @BotFather
- [ ] Server firewall configured
- [ ] SSL certificates installed (if using HTTPS)
- [ ] Backup strategy configured
- [ ] GitHub Secrets configured
- [ ] Monitoring alerts set up
- [ ] Slack webhook configured (optional)
- [ ] Database backups working
- [ ] Health check endpoint responding
- [ ] API endpoints tested locally
- [ ] Bot commands working in Telegram
- [ ] Web dashboard accessible
- [ ] Logs rotating properly
- [ ] Rate limiting enabled (production)
- [ ] Debug mode disabled (production)
- [ ] Database reset flag disabled (production)

---

## Quick Start Commands

### Development

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production

```bash
# Deploy new version
./scripts/deploy.sh production

# Monitor system
./scripts/monitor.sh

# Rollback if needed
./scripts/rollback.sh previous-version
```

### Maintenance

```bash
# Backup database
docker-compose exec mongodb mongodump --uri="mongodb://admin:changeme@localhost:27017/telegram_bot?authSource=admin" --out=backups/$(date +%Y%m%d_%H%M%S)

# View health status
curl http://localhost:8000/health

# Restart all services
docker-compose restart
```

---

## Support & Documentation

- **API Docs**: http://localhost:8000/docs
- **Bot Commands**: `/help` in Telegram
- **Logs**: `logs/` directory
- **Configuration**: `.env` file
- **Database**: MongoDB on port 27017

---

## Production Best Practices

1. **Security**
   - Use strong JWT secrets
   - Enable rate limiting
   - Use HTTPS only
   - Keep Docker images updated
   - Use environment variables for secrets

2. **Reliability**
   - Enable automated backups
   - Set up health checks
   - Configure monitoring/alerts
   - Plan rollback procedures
   - Use persistent volumes

3. **Performance**
   - Set appropriate log levels (WARNING in production)
   - Use connection pooling
   - Enable caching where appropriate
   - Monitor resource usage
   - Optimize database queries

4. **Maintenance**
   - Keep system packages updated
   - Rotate logs regularly
   - Clean old Docker images
   - Regular security audits
   - Document any customizations

---

Last Updated: 2024
Version: 1.0
