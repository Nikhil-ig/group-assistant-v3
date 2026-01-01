#!/bin/bash

# V3 Telegram Bot - Quick Setup Script
# This script helps you set up and run the bot

set -e  # Exit on error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║     V3 TELEGRAM MODERATION BOT - SETUP ASSISTANT          ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "✅ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your settings:"
    echo "   - TELEGRAM_BOT_TOKEN (from @BotFather)"
    echo "   - SUPERADMIN_ID (your Telegram user ID)"
    echo "   - SUPERADMIN_USERNAME (your username)"
    echo ""
    echo "   nano .env"
    echo ""
    exit 0
fi

# Check if MongoDB is running
echo "🔍 Checking MongoDB status..."
if ! mongosh --eval "db.version()" > /dev/null 2>&1; then
    echo "❌ MongoDB is not running"
    echo ""
    echo "📌 To start MongoDB:"
    echo "   brew services start mongodb-community"
    echo ""
    echo "Or run in another terminal:"
    echo "   mongod"
    echo ""
    exit 1
fi
echo "✅ MongoDB is running"

# Check if .env has required values
echo ""
echo "🔍 Checking .env configuration..."

TELEGRAM_TOKEN=$(grep -oP 'TELEGRAM_BOT_TOKEN=\K[^[:space:]]*' .env || echo "")
SUPERADMIN_ID=$(grep -oP 'SUPERADMIN_ID=\K[^[:space:]]*' .env || echo "")

if [ -z "$TELEGRAM_TOKEN" ] || [ "$TELEGRAM_TOKEN" = "" ]; then
    echo "❌ TELEGRAM_BOT_TOKEN not set in .env"
    echo "   Get token from: https://t.me/Botfather"
    echo "   Edit: nano .env"
    exit 1
fi
echo "✅ TELEGRAM_BOT_TOKEN configured"

if [ -z "$SUPERADMIN_ID" ] || [ "$SUPERADMIN_ID" = "" ]; then
    echo "❌ SUPERADMIN_ID not set in .env"
    echo "   Get your ID from: https://t.me/userinfobot"
    echo "   Edit: nano .env"
    exit 1
fi
echo "✅ SUPERADMIN_ID configured"

# All checks passed
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║              ✅ ALL CHECKS PASSED                         ║"
echo "║                                                            ║"
echo "║  Starting bot in 3 seconds...                            ║"
echo "║  Press Ctrl+C to cancel                                  ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

sleep 3

# Run the bot
cd ..
python -m v3.main
