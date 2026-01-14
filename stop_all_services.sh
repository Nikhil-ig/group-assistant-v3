#!/bin/bash

# V3 Microservices Stop Script
# Cleanly stops all services using PID files

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     V3 Microservices Shutdown - Stopping All Services       ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Stop Telegram Bot
echo -e "${YELLOW}Stopping Telegram Bot...${NC}"
if [ -f /tmp/bot.pid ]; then
    BOT_PID=$(cat /tmp/bot.pid)
    if kill $BOT_PID 2>/dev/null; then
        echo -e "${GREEN}✅ Bot stopped${NC}"
        rm /tmp/bot.pid
    else
        echo -e "${RED}ℹ️  Bot not running (PID $BOT_PID not found)${NC}"
    fi
else
    echo -e "${RED}ℹ️  Bot not running (no PID file)${NC}"
fi

# Stop Web Service
echo -e "${YELLOW}Stopping Web Service...${NC}"
if [ -f /tmp/web.pid ]; then
    WEB_PID=$(cat /tmp/web.pid)
    if kill $WEB_PID 2>/dev/null; then
        echo -e "${GREEN}✅ Web Service stopped${NC}"
        rm /tmp/web.pid
    else
        echo -e "${RED}ℹ️  Web Service not running (PID $WEB_PID not found)${NC}"
    fi
else
    echo -e "${RED}ℹ️  Web Service not running (no PID file)${NC}"
fi

# Stop Centralized API
echo -e "${YELLOW}Stopping Centralized API...${NC}"
if [ -f /tmp/api.pid ]; then
    API_PID=$(cat /tmp/api.pid)
    if kill $API_PID 2>/dev/null; then
        echo -e "${GREEN}✅ Centralized API stopped${NC}"
        rm /tmp/api.pid
    else
        echo -e "${RED}ℹ️  Centralized API not running (PID $API_PID not found)${NC}"
    fi
else
    echo -e "${RED}ℹ️  Centralized API not running (no PID file)${NC}"
fi

# Stop MongoDB
echo -e "${YELLOW}Stopping MongoDB...${NC}"
if [ -f /tmp/mongo.pid ]; then
    MONGO_PID=$(cat /tmp/mongo.pid)
    if kill $MONGO_PID 2>/dev/null; then
        echo -e "${GREEN}✅ MongoDB stopped${NC}"
        rm /tmp/mongo.pid
    else
        echo -e "${RED}ℹ️  MongoDB not running (PID $MONGO_PID not found)${NC}"
    fi
else
    echo -e "${RED}ℹ️  MongoDB not running (no PID file)${NC}"
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                 ✅ ALL SERVICES STOPPED                     ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
