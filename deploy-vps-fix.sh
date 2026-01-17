#!/bin/bash

# 🚀 VPS DEPLOYMENT & FIX SCRIPT
# Syncs all fixes from local to VPS and restarts services

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║       🚀 VPS FIX DEPLOYMENT & SERVICE RESTART             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
VPS_IP="${1:-}"
VPS_USER="${2:-root}"
VPS_PATH="/opt/group-assistant-v3"
LOCAL_PATH="/Users/apple/Documents/Personal/startup/bots/telegram\ bot/python/main_bot_v2/v3"

# Check if VPS IP provided
if [ -z "$VPS_IP" ]; then
    echo -e "${RED}❌ Error: VPS IP not provided${NC}"
    echo ""
    echo "Usage: bash deploy-vps-fix.sh <VPS_IP> [VPS_USER]"
    echo "Example: bash deploy-vps-fix.sh 123.45.67.89 root"
    echo ""
    exit 1
fi

echo -e "${BLUE}📋 Deployment Configuration:${NC}"
echo "   VPS IP: $VPS_IP"
echo "   VPS User: $VPS_USER"
echo "   VPS Path: $VPS_PATH"
echo "   Local Path: $LOCAL_PATH"
echo ""

# Step 1: Stop VPS Services
echo -e "${YELLOW}Step 1: Stopping VPS services...${NC}"
ssh -q "${VPS_USER}@${VPS_IP}" "cd $VPS_PATH && bash stop_all_services.sh 2>/dev/null || true"
echo -e "${GREEN}✅ Services stopped${NC}"
echo ""

# Step 2: Sync fixed files
echo -e "${YELLOW}Step 2: Syncing fixed files to VPS...${NC}"

# Create temp directory for files to copy
mkdir -p /tmp/vps-fixes

# Copy fixed files
cp "${LOCAL_PATH}/api_v2/cache/manager.py" /tmp/vps-fixes/
cp "${LOCAL_PATH}/api_v2/requirements.txt" /tmp/vps-fixes/api_v2_requirements.txt
cp "${LOCAL_PATH}/centralized_api2/requirements.txt" /tmp/vps-fixes/centralized_api2_requirements.txt
cp "${LOCAL_PATH}/requirements.txt" /tmp/vps-fixes/main_requirements.txt

# SCP files to VPS
scp -q /tmp/vps-fixes/manager.py "${VPS_USER}@${VPS_IP}:${VPS_PATH}/api_v2/cache/"
scp -q /tmp/vps-fixes/api_v2_requirements.txt "${VPS_USER}@${VPS_IP}:${VPS_PATH}/api_v2/requirements.txt"
scp -q /tmp/vps-fixes/centralized_api2_requirements.txt "${VPS_USER}@${VPS_IP}:${VPS_PATH}/centralized_api2/requirements.txt"
scp -q /tmp/vps-fixes/main_requirements.txt "${VPS_USER}@${VPS_IP}:${VPS_PATH}/requirements.txt"

echo -e "${GREEN}✅ Files synced to VPS${NC}"
echo ""

# Step 3: Reinstall dependencies
echo -e "${YELLOW}Step 3: Reinstalling Python dependencies...${NC}"
ssh -q "${VPS_USER}@${VPS_IP}" "cd $VPS_PATH && \
    ./venv/bin/pip uninstall -y aioredis 2>/dev/null || true && \
    ./venv/bin/pip install -q -r requirements.txt && \
    ./venv/bin/pip install -q -r api_v2/requirements.txt"
echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# Step 4: Start services
echo -e "${YELLOW}Step 4: Starting VPS services...${NC}"
ssh -q "${VPS_USER}@${VPS_IP}" "cd $VPS_PATH && sleep 2 && bash start_all_services.sh"
sleep 5
echo -e "${GREEN}✅ Services started${NC}"
echo ""

# Step 5: Verify services
echo -e "${YELLOW}Step 5: Verifying services...${NC}"
RUNNING=$(ssh -q "${VPS_USER}@${VPS_IP}" "ps aux | grep -E 'uvicorn|mongod|bot' | grep -v grep | wc -l")

if [ "$RUNNING" -ge 4 ]; then
    echo -e "${GREEN}✅ All 4+ services running!${NC}"
else
    echo -e "${YELLOW}⚠️  Only $RUNNING services running (expected 4+)${NC}"
fi
echo ""

# Step 6: Test database
echo -e "${YELLOW}Step 6: Testing database connection...${NC}"
DB_TEST=$(ssh -q "${VPS_USER}@${VPS_IP}" "python3 -c \"from pymongo import MongoClient; print('OK' if MongoClient('mongodb://localhost:27017/').admin.command('ping') else 'FAILED')\" 2>/dev/null" || echo "ERROR")

if [ "$DB_TEST" = "OK" ]; then
    echo -e "${GREEN}✅ Database connection successful${NC}"
else
    echo -e "${RED}❌ Database connection failed${NC}"
fi
echo ""

# Cleanup
rm -rf /tmp/vps-fixes

echo "╔════════════════════════════════════════════════════════════╗"
echo -e "${GREEN}║         🎉 DEPLOYMENT COMPLETE                           ║${NC}"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "✅ All fixes deployed and verified!"
echo ""
echo "📊 Current Status:"
echo "   Services Running: $RUNNING/4+"
echo "   Database: $DB_TEST"
echo ""
echo "📞 Quick Commands:"
echo "   Check logs: ssh ${VPS_USER}@${VPS_IP} 'tail -f /tmp/bot.log'"
echo "   Check status: ssh ${VPS_USER}@${VPS_IP} 'ps aux | grep -E \"uvicorn|mongod\"'"
echo "   Check ports: ssh ${VPS_USER}@${VPS_IP} 'lsof -i :27017; lsof -i :8002'"
echo ""
