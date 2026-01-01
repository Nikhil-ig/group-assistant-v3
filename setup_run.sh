#!/bin/bash

# V3 Bot - Quick Setup & Run
# Detects MongoDB port and sets up .env automatically

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║        V3 TELEGRAM BOT - QUICK SETUP & RUN                ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check MongoDB status
echo "🔍 Checking MongoDB..."
if ! pgrep -x "mongod" > /dev/null; then
    echo "❌ MongoDB not running"
    echo "Start with: brew services start mongodb-community"
    exit 1
fi
echo "✅ MongoDB running"

# Detect MongoDB port
MONGO_PORT=$(cat /usr/local/etc/mongod.conf 2>/dev/null | grep "port:" | awk '{print $2}' || echo "27017")
echo "✅ MongoDB port: $MONGO_PORT"

# Check if .env exists
if [ ! -f .env ]; then
    echo ""
    echo "📝 Creating .env file..."
    cp .env.example .env
    
    # Update MongoDB port if not default
    if [ "$MONGO_PORT" != "27017" ]; then
        sed -i '' "s|mongodb://localhost:27017|mongodb://localhost:$MONGO_PORT|g" .env
        echo "✅ Updated MongoDB URI to port $MONGO_PORT"
    fi
    
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add:"
    echo ""
    echo "   TELEGRAM_BOT_TOKEN=YOUR_TOKEN_FROM_BOTFATHER"
    echo "   SUPERADMIN_ID=YOUR_TELEGRAM_USER_ID"
    echo "   SUPERADMIN_USERNAME=your_username"
    echo ""
    echo "   nano .env"
    echo ""
    exit 0
fi

# Check if .env has required values
echo ""
echo "🔍 Checking .env configuration..."

TELEGRAM_TOKEN=$(grep -E '^TELEGRAM_BOT_TOKEN=' .env | cut -d'=' -f2 || echo "")
SUPERADMIN_ID=$(grep -E '^SUPERADMIN_ID=' .env | cut -d'=' -f2 || echo "")

if [ -z "$TELEGRAM_TOKEN" ] || [ "$TELEGRAM_TOKEN" = "YOUR_TOKEN_FROM_BOTFATHER" ] || [ "$TELEGRAM_TOKEN" = "YOUR_BOT_TOKEN_HERE" ]; then
    echo "❌ TELEGRAM_BOT_TOKEN not configured"
    echo "   Get from: https://t.me/botfather"
    echo "   Edit: nano .env"
    exit 1
fi
echo "✅ TELEGRAM_BOT_TOKEN configured"

if [ -z "$SUPERADMIN_ID" ]; then
    echo "❌ SUPERADMIN_ID not configured"
    echo "   Get from: https://t.me/userinfobot"
    echo "   Edit: nano .env"
    exit 1
fi
echo "✅ SUPERADMIN_ID configured"

# All checks passed
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║              ✅ ALL CHECKS PASSED!                        ║"
echo "║                                                            ║"
echo "║  Starting bot in 3 seconds...                            ║"
echo "║  Press Ctrl+C to cancel                                  ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

sleep 3

# Run the bot from parent directory
cd ..
python -m v3.main
