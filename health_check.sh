#!/bin/bash

# 🏥 Health Check & Monitoring Script for Telegram Bot V3
# Monitors all microservices and restarts if needed
# Usage: ./health_check.sh (runs once) or nohup ./health_check.sh &

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/tmp/health_check.log"
ALERT_EMAIL="your-email@example.com"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging function
log() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${BLUE}[$timestamp]${NC} $1" | tee -a "$LOG_FILE"
}

# Error function
error() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${RED}[$timestamp] ❌ ERROR:${NC} $1" | tee -a "$LOG_FILE"
}

# Success function  
success() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${GREEN}[$timestamp] ✅ SUCCESS:${NC} $1" | tee -a "$LOG_FILE"
}

# Warning function
warning() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${YELLOW}[$timestamp] ⚠️  WARNING:${NC} $1" | tee -a "$LOG_FILE"
}

# ============================================================================
# SERVICE CHECKS
# ============================================================================

check_mongodb() {
    log "Checking MongoDB..."
    
    if lsof -i :27017 | grep mongod > /dev/null 2>&1; then
        # Check if responsive
        if echo "db.adminCommand('ping')" | mongo --quiet 2>/dev/null | grep -q "1"; then
            success "MongoDB is running and responsive (port 27017)"
            return 0
        else
            error "MongoDB process exists but not responding"
            return 1
        fi
    else
        error "MongoDB is not running"
        return 1
    fi
}

check_api_v2() {
    log "Checking API V2..."
    
    if lsof -i :8002 | grep -E "python|uvicorn" > /dev/null 2>&1; then
        # Check if responsive
        if curl -s http://localhost:8002/health > /dev/null 2>&1; then
            success "API V2 is running and responsive (port 8002)"
            return 0
        else
            warning "API V2 process exists but not responding"
            return 1
        fi
    else
        error "API V2 is not running"
        return 1
    fi
}

check_web_service() {
    log "Checking Web Service..."
    
    if lsof -i :8003 | grep -E "python|uvicorn" > /dev/null 2>&1; then
        # Check if responsive
        if curl -s http://localhost:8003/health > /dev/null 2>&1; then
            success "Web Service is running and responsive (port 8003)"
            return 0
        else
            warning "Web Service process exists but not responding"
            return 1
        fi
    else
        error "Web Service is not running"
        return 1
    fi
}

check_telegram_bot() {
    log "Checking Telegram Bot..."
    
    if pgrep -f "python.*bot/main.py" > /dev/null 2>&1; then
        BOT_PID=$(pgrep -f "python.*bot/main.py")
        
        # Check if process is using CPU/memory (not zombie)
        if ps -p $BOT_PID > /dev/null 2>&1; then
            success "Telegram Bot is running (PID: $BOT_PID)"
            return 0
        else
            error "Telegram Bot is a zombie process (PID: $BOT_PID)"
            return 1
        fi
    else
        error "Telegram Bot is not running"
        return 1
    fi
}

# ============================================================================
# RESTART FUNCTIONS
# ============================================================================

restart_all_services() {
    error "Restarting all services..."
    
    # Kill all processes
    pkill -f "uvicorn"        2>/dev/null || true
    pkill -f "bot/main.py"    2>/dev/null || true
    pkill -f "mongod"         2>/dev/null || true
    
    sleep 3
    
    # Start all services
    cd "$PROJECT_DIR" || exit 1
    bash start_all_services.sh
    
    # Wait for services to start
    sleep 5
    
    # Verify restart was successful
    if check_mongodb && check_api_v2 && check_telegram_bot; then
        success "All services restarted successfully"
        return 0
    else
        error "Services did not start properly after restart"
        return 1
    fi
}

# ============================================================================
# RESOURCE MONITORING
# ============================================================================

check_system_resources() {
    log "Checking system resources..."
    
    # Memory usage
    MEMORY_PERCENT=$(free | grep Mem | awk '{print int($3/$2 * 100)}')
    if [ "$MEMORY_PERCENT" -gt 85 ]; then
        warning "High memory usage: ${MEMORY_PERCENT}% (threshold: 85%)"
    else
        success "Memory usage OK: ${MEMORY_PERCENT}%"
    fi
    
    # Disk usage
    DISK_PERCENT=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ "$DISK_PERCENT" -gt 90 ]; then
        warning "High disk usage: ${DISK_PERCENT}% (threshold: 90%)"
    else
        success "Disk usage OK: ${DISK_PERCENT}%"
    fi
    
    # CPU load
    LOAD=$(uptime | awk -F'load average:' '{print $2}' | cut -d',' -f1 | xargs)
    CORE_COUNT=$(nproc)
    LOAD_PERCENT=$(echo "scale=0; $LOAD * 100 / $CORE_COUNT" | bc)
    if [ "$LOAD_PERCENT" -gt 80 ]; then
        warning "High CPU load: ${LOAD_PERCENT}% (load: $LOAD)"
    else
        success "CPU load OK: ${LOAD_PERCENT}% (load: $LOAD)"
    fi
}

# ============================================================================
# LOG MONITORING
# ============================================================================

check_recent_errors() {
    log "Checking for recent errors in logs..."
    
    # Check for SIGTERM in logs (indicates crashes)
    if grep -l "SIGTERM\|Terminated\|terminated" /tmp/*.log 2>/dev/null; then
        error "Found SIGTERM signals in recent logs (service crashes detected)"
        return 1
    fi
    
    # Check for Python errors
    if grep -l "Error\|Exception\|Traceback" /tmp/*.log 2>/dev/null; then
        warning "Found exceptions in logs (check logs for details)"
        return 1
    fi
    
    success "No critical errors found in logs"
    return 0
}

# ============================================================================
# MAIN MONITORING LOOP
# ============================================================================

run_health_check() {
    log "╔════════════════════════════════════════════════════════════╗"
    log "║  🏥 TELEGRAM BOT V3 HEALTH CHECK                          ║"
    log "║  $(date '+%Y-%m-%d %H:%M:%S')                                   ║"
    log "╚════════════════════════════════════════════════════════════╝"
    log ""
    
    # Track failures
    FAILURES=0
    
    # Check all services
    check_mongodb || ((FAILURES++))
    check_api_v2 || ((FAILURES++))
    check_web_service || ((FAILURES++))
    check_telegram_bot || ((FAILURES++))
    
    log ""
    check_system_resources
    log ""
    check_recent_errors || ((FAILURES++))
    log ""
    
    # Summary
    if [ $FAILURES -eq 0 ]; then
        success "All services healthy! ✅"
        log ""
        return 0
    else
        error "Found $FAILURES issues - attempting restart"
        restart_all_services
        log ""
        return 1
    fi
}

# ============================================================================
# CONTINUOUS MONITORING MODE
# ============================================================================

if [ "$1" = "daemon" ] || [ "$1" = "-d" ]; then
    log "Starting health check daemon (checking every 60 seconds)"
    log "Log: tail -f $LOG_FILE"
    log ""
    
    while true; do
        run_health_check
        sleep 60
    done
else
    # Single check mode
    run_health_check
    exit $?
fi
