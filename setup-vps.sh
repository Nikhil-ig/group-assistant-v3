#!/bin/bash
################################################################################
# VPS Initial Setup Script - Copy & Run This On Your VPS
# 
# Usage:
#   1. Copy the content of this file
#   2. SSH to VPS: ssh root@your.vps.ip
#   3. Paste into terminal (it will prompt for secrets interactively)
#   4. Or pass secrets as arguments: bash setup-vps.sh "bot_token" "api_key" "mongo_pass" "redis_pass"
#
# This script handles:
#   - Clone repository
#   - Create .env files with your secrets
#   - Set up deployment automation (webhook or cron)
#   - Run first deployment
################################################################################

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
PROJECT_DIR="/opt/group-assistant-v3"
REPO_URL="https://github.com/Nikhil-ig/group-assistant-v3.git"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Group Assistant V3 - VPS Initial Setup                  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# ============================================================================
# STEP 1: VERIFY PREREQUISITES
# ============================================================================

echo -e "${YELLOW}[1/6] Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found. Please install Docker first.${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose not found. Please install Docker Compose first.${NC}"
    exit 1
fi

if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git not found. Please install Git first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All prerequisites met${NC}"
echo ""

# ============================================================================
# STEP 2: GATHER SECRETS (INTERACTIVE OR ARGS)
# ============================================================================

echo -e "${YELLOW}[2/6] Gathering configuration...${NC}"

if [ $# -eq 4 ]; then
    # Secrets passed as arguments
    BOT_TOKEN="$1"
    API_KEY="$2"
    MONGO_PASSWORD="$3"
    REDIS_PASSWORD="$4"
    echo -e "${GREEN}✅ Secrets provided via arguments${NC}"
else
    # Interactive input
    echo -e "${BLUE}Enter your secrets (they won't be echoed):${NC}"
    echo ""
    
    read -sp "Telegram Bot Token (from @BotFather): " BOT_TOKEN
    echo ""
    [ -z "$BOT_TOKEN" ] && { echo -e "${RED}❌ Bot token is required${NC}"; exit 1; }
    
    read -sp "Shared API Key: " API_KEY
    echo ""
    [ -z "$API_KEY" ] && { echo -e "${RED}❌ API key is required${NC}"; exit 1; }
    
    read -sp "MongoDB Root Password (min 20 chars): " MONGO_PASSWORD
    echo ""
    [ ${#MONGO_PASSWORD} -lt 20 ] && { echo -e "${RED}❌ MongoDB password must be at least 20 characters${NC}"; exit 1; }
    
    read -sp "Redis Password (min 20 chars): " REDIS_PASSWORD
    echo ""
    [ ${#REDIS_PASSWORD} -lt 20 ] && { echo -e "${RED}❌ Redis password must be at least 20 characters${NC}"; exit 1; }
fi

# Generate SECRET_KEY
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || openssl rand -base64 32)

echo -e "${GREEN}✅ Secrets gathered${NC}"
echo ""

# ============================================================================
# STEP 3: CLONE REPOSITORY
# ============================================================================

echo -e "${YELLOW}[3/6] Setting up repository...${NC}"

if [ ! -d "$PROJECT_DIR" ]; then
    mkdir -p /opt
    git clone "$REPO_URL" "$PROJECT_DIR" || {
        echo -e "${RED}❌ Failed to clone repository${NC}"
        exit 1
    }
    echo -e "${GREEN}✅ Repository cloned${NC}"
else
    echo -e "${BLUE}ℹ️  Directory already exists, updating...${NC}"
    cd "$PROJECT_DIR"
    git fetch origin
    git reset --hard origin/main
    echo -e "${GREEN}✅ Repository updated${NC}"
fi

cd "$PROJECT_DIR"

# ============================================================================
# STEP 4: CREATE .ENV FILES
# ============================================================================

echo -e "${YELLOW}[4/6] Creating .env files...${NC}"

# Create bot/.env
cat > bot/.env <<EOF
TELEGRAM_BOT_TOKEN=$BOT_TOKEN
CENTRALIZED_API_URL=http://centralized_api:8000
CENTRALIZED_API_KEY=$API_KEY
LOG_LEVEL=INFO
EOF

chmod 600 bot/.env

# Create centralized_api/.env
cat > centralized_api/.env <<EOF
MONGODB_URL=mongodb://root:$MONGO_PASSWORD@mongo:27017/telegram_bot?authSource=admin
MONGO_ROOT_USERNAME=root
MONGO_ROOT_PASSWORD=$MONGO_PASSWORD
REDIS_PASSWORD=$REDIS_PASSWORD
REDIS_URL=redis://:$REDIS_PASSWORD@redis:6379/0
API_KEY=$API_KEY
SECRET_KEY=$SECRET_KEY
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
EOF

chmod 600 centralized_api/.env

echo -e "${GREEN}✅ .env files created and secured${NC}"
echo ""

# ============================================================================
# STEP 5: MAKE DEPLOYMENT SCRIPT EXECUTABLE
# ============================================================================

echo -e "${YELLOW}[5/6] Setting up deployment scripts...${NC}"

chmod +x deploy-vps.sh

# Test deployment script
if [ ! -x deploy-vps.sh ]; then
    echo -e "${RED}❌ Failed to make deploy-vps.sh executable${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Deployment script ready${NC}"
echo ""

# ============================================================================
# STEP 6: OPTIONAL - SET UP AUTOMATION
# ============================================================================

echo -e "${YELLOW}[6/6] Setting up auto-deployment...${NC}"

read -p "Choose deployment method:
  1) Webhook (auto-deploy on every push, needs setup in GitHub)
  2) Cron (auto-deploy every 5 minutes, simpler)
  3) Manual (I'll run ./deploy-vps.sh myself)
  
Enter 1, 2, or 3: " deployment_choice

case $deployment_choice in
    1)
        echo -e "${BLUE}Setting up webhook...${NC}"
        
        if ! command -v webhook &> /dev/null; then
            echo -e "${YELLOW}Installing webhook package...${NC}"
            apt-get update -qq && apt-get install -y webhook >/dev/null 2>&1 || {
                echo -e "${RED}❌ Failed to install webhook${NC}"
                echo "Install manually: sudo apt-get install webhook"
                exit 1
            }
        fi
        
        mkdir -p /etc/webhook
        cat > /etc/webhook/hooks.json <<'WEBHOOK_EOF'
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
WEBHOOK_EOF
        
        chmod 600 /etc/webhook/hooks.json
        
        cat > /etc/systemd/system/webhook.service <<'SERVICE_EOF'
[Unit]
Description=GitHub Webhook Service
After=network.target
[Service]
Type=simple
User=webhook
ExecStart=/usr/bin/webhook -hooks /etc/webhook/hooks.json -port 9000 -verbose
Restart=always
RestartSec=10
[Install]
WantedBy=multi-user.target
SERVICE_EOF
        
        systemctl daemon-reload
        systemctl enable webhook
        systemctl start webhook
        
        echo -e "${GREEN}✅ Webhook service started${NC}"
        echo ""
        echo -e "${BLUE}Next: Add GitHub webhook${NC}"
        echo "  1. Go to: https://github.com/Nikhil-ig/group-assistant-v3/settings/hooks/new"
        echo "  2. Payload URL: http://your.vps.ip:9000/hooks/group-assistant-deploy"
        echo "  3. Events: Push events only"
        echo "  4. Click Add webhook"
        ;;
    2)
        echo -e "${BLUE}Setting up cron job...${NC}"
        
        # Add cron job (for root since we're running as sudo)
        # Add to root's crontab
        (sudo crontab -l 2>/dev/null || true; echo "*/5 * * * * /opt/group-assistant-v3/deploy-vps.sh >> /var/log/group-assistant-deploy.log 2>&1") | sudo crontab -
        
        echo -e "${GREEN}✅ Cron job added (runs every 5 minutes)${NC}"
        ;;
    3)
        echo -e "${BLUE}Manual mode selected${NC}"
        echo "  Run deployment manually: /opt/group-assistant-v3/deploy-vps.sh"
        ;;
    *)
        echo -e "${RED}❌ Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""

# ============================================================================
# FINAL: RUN FIRST DEPLOYMENT
# ============================================================================

echo -e "${YELLOW}Running first deployment...${NC}"
echo ""

if ./deploy-vps.sh; then
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║           ✅ SETUP COMPLETE - SERVICES RUNNING           ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}📊 Current Status:${NC}"
    docker compose ps
    echo ""
    echo -e "${BLUE}📝 View Logs:${NC}"
    echo "  docker compose logs -f          # All services"
    echo "  docker compose logs -f bot      # Bot only"
    echo "  tail -f /var/log/group-assistant-deploy.log"
    echo ""
    echo -e "${BLUE}🔄 Sync Workflow:${NC}"
    echo "  1. Make changes on your Mac (VS Code)"
    echo "  2. Commit & push: git push origin main"
    echo "  3. VPS auto-deploys (webhook) or deploys every 5 min (cron)"
    echo ""
    echo -e "${BLUE}📚 Full Docs:${NC}"
    echo "  /opt/group-assistant-v3/VPS_DEPLOYMENT.md"
    echo "  /opt/group-assistant-v3/SYNC_QUICK_START.md"
    echo ""
else
    echo -e "${RED}❌ First deployment failed. Check logs: docker compose logs${NC}"
    exit 1
fi
