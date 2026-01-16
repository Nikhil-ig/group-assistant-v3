#!/bin/bash
# Quick Commands for Bot API v3 System
# Usage: Run commands from project root directory

# ============================================================================
# NAVIGATION
# ============================================================================
cd_project() {
    cd "/Users/apple/Documents/Personal/startup/bots/telegram bot/python/main_bot_v2/v3"
}

# ============================================================================
# START SERVICES
# ============================================================================
start_api() {
    echo "🚀 Starting API V2 on port 8002..."
    cd_project
    python -m uvicorn api_v2.app:app --port 8002
}

start_bot() {
    echo "🤖 Starting Telegram Bot..."
    cd_project
    python bot/main.py
}

start_all() {
    echo "🚀 Starting all services..."
    start_api &
    sleep 3
    start_bot &
    echo "✅ All services started"
}

# ============================================================================
# STOP SERVICES
# ============================================================================
stop_api() {
    echo "🛑 Stopping API..."
    pkill -f "uvicorn api_v2"
    echo "✅ API stopped"
}

stop_bot() {
    echo "🛑 Stopping Bot..."
    pkill -f "python bot/main.py"
    echo "✅ Bot stopped"
}

stop_all() {
    echo "🛑 Stopping all services..."
    stop_api
    stop_bot
    echo "✅ All services stopped"
}

# ============================================================================
# RESTART SERVICES
# ============================================================================
restart_api() {
    stop_api
    sleep 1
    start_api
}

restart_bot() {
    stop_bot
    sleep 1
    start_bot
}

restart_all() {
    stop_all
    sleep 2
    start_all
}

# ============================================================================
# TESTING
# ============================================================================
test_api_health() {
    echo "🏥 Testing API health..."
    curl -s http://localhost:8002/health | jq .
}

test_ban_endpoint() {
    echo "🔨 Testing ban endpoint..."
    curl -s -X POST http://localhost:8002/api/v2/groups/123/enforcement/ban \
      -H "Content-Type: application/json" \
      -d '{"user_id": 456, "admin_id": 789, "reason": "spam"}' | jq .
}

test_mute_endpoint() {
    echo "🔇 Testing mute endpoint..."
    curl -s -X POST http://localhost:8002/api/v2/groups/123/enforcement/mute \
      -H "Content-Type: application/json" \
      -d '{"user_id": 456, "duration": 3600}' | jq .
}

test_kick_endpoint() {
    echo "👢 Testing kick endpoint..."
    curl -s -X POST http://localhost:8002/api/v2/groups/123/enforcement/kick \
      -H "Content-Type: application/json" \
      -d '{"user_id": 456}' | jq .
}

test_all_endpoints() {
    echo "🧪 Running all endpoint tests..."
    test_api_health
    echo ""
    test_ban_endpoint
    echo ""
    test_mute_endpoint
    echo ""
    test_kick_endpoint
    echo ""
    echo "✅ All tests completed"
}

# ============================================================================
# STATUS CHECKS
# ============================================================================
check_api_status() {
    echo "📊 API Status:"
    if curl -s http://localhost:8002/health > /dev/null 2>&1; then
        echo "  ✅ API is running"
        curl -s http://localhost:8002/health | jq .
    else
        echo "  ❌ API is NOT running"
    fi
}

check_bot_status() {
    echo ""
    echo "📊 Bot Status:"
    if ps aux | grep -v grep | grep "python bot/main.py" > /dev/null; then
        echo "  ✅ Bot is running"
        ps aux | grep "python bot/main.py" | grep -v grep
    else
        echo "  ❌ Bot is NOT running"
    fi
}

check_all_status() {
    echo "�� System Status Check"
    echo "====================="
    check_api_status
    check_bot_status
    echo ""
    echo "📝 Endpoint Status:"
    if curl -s http://localhost:8002/api/v2/groups/123/enforcement/ban > /dev/null 2>&1; then
        echo "  ✅ Enforcement endpoints available"
    else
        echo "  ❌ Enforcement endpoints NOT available"
    fi
}

# ============================================================================
# LOGS & DEBUGGING
# ============================================================================
show_api_log() {
    echo "📋 API Log:"
    if [ -f "/tmp/api.log" ]; then
        tail -50 /tmp/api.log
    else
        echo "  ❌ API log file not found"
    fi
}

clear_port() {
    port=$1
    echo "🧹 Clearing port $port..."
    lsof -i :$port | grep -v COMMAND | awk '{print $2}' | xargs kill -9 2>/dev/null
    echo "✅ Port $port cleared"
}

# ============================================================================
# INFO & HELP
# ============================================================================
show_help() {
    cat << 'HELP'
Bot API v3 - Quick Commands

START:
  start_api          - Start API V2
  start_bot          - Start Telegram Bot
  start_all          - Start all services

STOP:
  stop_api           - Stop API V2
  stop_bot           - Stop Bot
  stop_all           - Stop all services

RESTART:
  restart_api        - Restart API
  restart_bot        - Restart Bot
  restart_all        - Restart all services

TEST:
  test_api_health    - Test API health endpoint
  test_ban_endpoint  - Test ban enforcement
  test_mute_endpoint - Test mute enforcement
  test_kick_endpoint - Test kick enforcement
  test_all_endpoints - Test all endpoints

STATUS:
  check_api_status   - Check API status
  check_bot_status   - Check Bot status
  check_all_status   - Check all systems

DEBUG:
  show_api_log       - Show API logs
  clear_port 8002    - Clear specific port

INFO:
  show_help          - Show this help

EXAMPLES:
  # Start everything
  start_all

  # Test in Telegram
  # In Telegram: /start
  # In Telegram: /ban @username

  # Monitor API
  check_all_status

  # Kill and restart
  restart_all

HELP
}

# ============================================================================
# MAIN - Run function if provided
# ============================================================================
if [ $# -eq 0 ]; then
    show_help
else
    "$@"
fi
