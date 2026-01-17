#!/bin/bash

# V3 Microservices Startup Script
# Starts all services: MongoDB, Centralized API, Web Service, Bot Service

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Detect Python - try venv first, then system python3
if [ -f "$PROJECT_DIR/venv/bin/python" ]; then
    PYTHON_BIN="$PROJECT_DIR/venv/bin/python"
elif command -v python3 &> /dev/null; then
    # Create venv if it doesn't exist
    if [ ! -d "$PROJECT_DIR/venv" ]; then
        echo "📦 Creating virtual environment..."
        python3 -m venv "$PROJECT_DIR/venv"
        echo "📦 Installing dependencies..."
        "$PROJECT_DIR/venv/bin/pip" install --upgrade pip
        "$PROJECT_DIR/venv/bin/pip" install -q -r "$PROJECT_DIR/requirements.txt"
        "$PROJECT_DIR/venv/bin/pip" install -q -r "$PROJECT_DIR/bot/requirements.txt"
        "$PROJECT_DIR/venv/bin/pip" install -q -r "$PROJECT_DIR/api_v2/requirements.txt"
        "$PROJECT_DIR/venv/bin/pip" install -q -r "$PROJECT_DIR/web/requirements.txt"
        echo "✅ Virtual environment ready!"
    fi
    PYTHON_BIN="$PROJECT_DIR/venv/bin/python"
elif command -v python &> /dev/null; then
    PYTHON_BIN="python"
else
    echo "❌ Python not found! Please install Python 3.10+"
    exit 1
fi

TELEGRAM_TOKEN="${TELEGRAM_BOT_TOKEN:-8276429151:AAEWq4nE9hQcRgY4AcuLWFKW_z26Xcmk2gY}"


echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     V3 Microservices Startup - Starting All Services        ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Detect if running on VPS or local machine
# VPS typically uses /opt or /home paths, local uses /Users (Mac) or /home/user (Linux home)
IS_VPS=false
if [[ "$PROJECT_DIR" == /opt/* ]] || [[ "$PROJECT_DIR" == /srv/* ]]; then
    IS_VPS=true
fi

# Only auto-pull on VPS
if [ "$IS_VPS" = true ]; then
    echo -e "${BLUE}🔄 Pulling latest code from git (VPS deployment)...${NC}"
    cd "$PROJECT_DIR" || exit 1
    git pull origin main
    echo -e "${GREEN}✅ Latest code pulled from git.${NC}"
    echo ""
else
    echo -e "${YELLOW}ℹ️  Skipping git pull (local development mode)${NC}"
    echo ""
fi

# Install/update dependencies
echo -e "${BLUE}📦 Installing dependencies...${NC}"
"$PYTHON_BIN" -m pip install -q -r "$PROJECT_DIR/requirements.txt" 2>/dev/null || true
"$PYTHON_BIN" -m pip install -q -r "$PROJECT_DIR/bot/requirements.txt" 2>/dev/null || true
"$PYTHON_BIN" -m pip install -q -r "$PROJECT_DIR/api_v2/requirements.txt" 2>/dev/null || true
"$PYTHON_BIN" -m pip install -q -r "$PROJECT_DIR/web/requirements.txt" 2>/dev/null || true
echo -e "${GREEN}✅ Dependencies installed.${NC}"
echo ""

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

OS_TYPE="$(uname)"
# 1. Start MongoDB (cross-platform)
echo -e "${BLUE}1️⃣  Starting MongoDB on port 27017...${NC}"
mkdir -p /tmp/mongo_data
# Check if mongod is already running on port 27017
if [ "$OS_TYPE" = "Darwin" ]; then
    # macOS: use lsof
    if lsof -i :27017 | grep mongod > /dev/null; then
        echo -e "${YELLOW}⚠️  MongoDB already running on port 27017 (macOS). Skipping start.${NC}"
        MONGO_PID=$(lsof -ti :27017)
    else
        mongod --port 27017 --dbpath /tmp/mongo_data > /tmp/mongod.log 2>&1 &
        MONGO_PID=$!
        echo $MONGO_PID > /tmp/mongo.pid
        sleep 2
        echo -e "${GREEN}✅ MongoDB started (PID: $MONGO_PID)${NC}"
    fi
else
    # Linux: try fuser, then start mongod
    if fuser 27017/tcp > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  MongoDB already running on port 27017 (Linux). Skipping start.${NC}"
        MONGO_PID=$(fuser 27017/tcp 2>/dev/null)
    else
        mongod --port 27017 --dbpath /tmp/mongo_data > /tmp/mongod.log 2>&1 &
        MONGO_PID=$!
        echo $MONGO_PID > /tmp/mongo.pid
        sleep 2
        echo -e "${GREEN}✅ MongoDB started (PID: $MONGO_PID)${NC}"
    fi
fi
echo ""

# 2. Start API V2
echo -e "${BLUE}2️⃣  Starting API V2 on port 8002...${NC}"
cd "$PROJECT_DIR" || exit 1
if [ "$OS_TYPE" = "Darwin" ]; then
    # macOS: use lsof to kill process on port 8002
    lsof -ti :8002 | xargs kill -9 2>/dev/null || true
else
    # Linux: use fuser
    fuser -k 8002/tcp 2>/dev/null || true
fi
sleep 1
export TELEGRAM_BOT_TOKEN="$TELEGRAM_TOKEN"
"$PYTHON_BIN" -m uvicorn api_v2.app:app --host 0.0.0.0 --port 8002 > /tmp/api.log 2>&1 &
API_PID=$!
echo $API_PID > /tmp/api.pid
sleep 3
echo -e "${GREEN}✅ API V2 started (PID: $API_PID)${NC}"
echo ""

# 3. Start Web Service
echo -e "${BLUE}3️⃣  Starting Web Service on port 8003...${NC}"
cd "$PROJECT_DIR" || exit 1
export API_V2_URL="http://localhost:8002"
"$PYTHON_BIN" -m uvicorn web.app:app --host 0.0.0.0 --port 8003 > /tmp/web.log 2>&1 &
WEB_PID=$!
echo $WEB_PID > /tmp/web.pid
sleep 2
echo -e "${GREEN}✅ Web Service started (PID: $WEB_PID)${NC}"
echo ""

# 4. Start Telegram Bot
echo -e "${BLUE}4️⃣  Starting Telegram Bot (polling)...${NC}"
export TELEGRAM_BOT_TOKEN="$TELEGRAM_TOKEN"
export API_V2_URL="http://localhost:8002"
cd "$PROJECT_DIR" || exit 1
"$PYTHON_BIN" bot/main.py > /tmp/bot.log 2>&1 &
BOT_PID=$!
echo $BOT_PID > /tmp/bot.pid
sleep 2
echo -e "${GREEN}✅ Telegram Bot started (PID: $BOT_PID)${NC}"
echo ""

# Summary
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                  ✅ ALL SERVICES STARTED                    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 Service Status:"
echo ""
echo -e "  ${GREEN}MongoDB${NC}             PID: $MONGO_PID   (port 27017)"
echo -e "  ${GREEN}Centralized API${NC}     PID: $API_PID   (port 8001)"
echo -e "  ${GREEN}Web Service${NC}         PID: $WEB_PID   (port 8003)"
echo -e "  ${GREEN}Telegram Bot${NC}        PID: $BOT_PID   (polling)"
echo ""
echo "🔗 Access Points:"
echo "  • Centralized API: http://localhost:8002"
echo "  • Web Service:     http://localhost:8003"
echo "  • API Docs:        http://localhost:8002/docs"
echo "  • Web Docs:        http://localhost:8003/docs"
echo ""
echo "📝 Log Files:"
echo "  • MongoDB:  tail -f /tmp/mongod.log"
echo "  • API:      tail -f /tmp/api.log"
echo "  • Web:      tail -f /tmp/web.log"
echo "  • Bot:      tail -f /tmp/bot.log"
echo ""
echo "🛑 To stop all services, run: ./stop_all_services.sh"
echo ""
