#!/bin/bash

# ============================================
# Telegram Bot - Post-Deployment Validation
# Comprehensive health & functionality checks
# Usage: ./scripts/validate-deployment.sh
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Counters
PASSED=0
FAILED=0
WARNINGS=0

log_header() { echo -e "\n${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n${CYAN}$1${NC}\n${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"; }
log_pass() { echo -e "${GREEN}✅ $1${NC}"; ((PASSED++)); }
log_fail() { echo -e "${RED}❌ $1${NC}"; ((FAILED++)); }
log_warn() { echo -e "${YELLOW}⚠️  $1${NC}"; ((WARNINGS++)); }
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

cd "$PROJECT_ROOT"

trap 'echo ""; log_header "VALIDATION SUMMARY"; echo "Passed: $PASSED | Failed: $FAILED | Warnings: $WARNINGS"; [ $FAILED -eq 0 ] && echo -e "${GREEN}✅ Deployment validation successful!${NC}" || echo -e "${RED}❌ Deployment validation failed!${NC}"; exit $([ $FAILED -eq 0 ] && echo 0 || echo 1)' EXIT

# ============================================
# 1. CONTAINER HEALTH
# ============================================

log_header "1️⃣  CONTAINER HEALTH CHECKS"

# Check all containers running
RUNNING=$(docker-compose ps --services --filter "status=running" | wc -l)
TOTAL=$(docker-compose ps --services | wc -l)

if [ "$RUNNING" = "$TOTAL" ]; then
    log_pass "All containers running ($RUNNING/$TOTAL)"
else
    log_fail "Not all containers running ($RUNNING/$TOTAL)"
    docker-compose ps
fi

# Check specific services
for service in mongodb telegram-bot nginx; do
    if docker-compose ps --services | grep -q "^$service$"; then
        STATUS=$(docker-compose ps --filter "service=$service" --format "{{.Status}}" 2>/dev/null | head -1)
        if echo "$STATUS" | grep -q "Up"; then
            log_pass "$service container is running"
        else
            log_fail "$service container is not running (Status: $STATUS)"
        fi
    fi
done

# ============================================
# 2. PORT CONNECTIVITY
# ============================================

log_header "2️⃣  PORT CONNECTIVITY"

# API Port
if timeout 2 bash -c "cat < /dev/null > /dev/tcp/127.0.0.1/8000" 2>/dev/null; then
    log_pass "API port 8000 is accessible"
else
    log_fail "API port 8000 is not accessible"
fi

# MongoDB Port
if timeout 2 bash -c "cat < /dev/null > /dev/tcp/127.0.0.1/27017" 2>/dev/null; then
    log_pass "MongoDB port 27017 is accessible"
else
    log_warn "MongoDB port 27017 is not directly accessible (may be intentional)"
fi

# Nginx Port
if timeout 2 bash -c "cat < /dev/null > /dev/tcp/127.0.0.1/80" 2>/dev/null; then
    log_pass "Nginx port 80 is accessible"
else
    log_warn "Nginx port 80 is not accessible"
fi

# ============================================
# 3. API HEALTH ENDPOINTS
# ============================================

log_header "3️⃣  API HEALTH ENDPOINTS"

# Health endpoint
log_info "Testing GET /health..."
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" http://localhost:8000/health 2>/dev/null || echo "error\n000")
HEALTH_STATUS=$(echo "$HEALTH_RESPONSE" | tail -1)
HEALTH_BODY=$(echo "$HEALTH_RESPONSE" | head -1)

if [ "$HEALTH_STATUS" = "200" ]; then
    log_pass "Health endpoint returns 200"
    if echo "$HEALTH_BODY" | grep -q "healthy"; then
        log_pass "Application reported as healthy"
    else
        log_warn "Health endpoint didn't return 'healthy' status"
    fi
else
    log_fail "Health endpoint returned status $HEALTH_STATUS"
fi

# Swagger docs
log_info "Testing GET /docs..."
DOCS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs)
if [ "$DOCS_STATUS" = "200" ]; then
    log_pass "Swagger documentation is available"
else
    log_warn "Swagger docs returned status $DOCS_STATUS"
fi

# ============================================
# 4. DATABASE CONNECTIVITY
# ============================================

log_header "4️⃣  DATABASE CONNECTIVITY"

# MongoDB ping
log_info "Testing MongoDB connection..."
if docker-compose exec -T mongodb mongosh --authenticationDatabase admin -u admin -p changeme --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
    log_pass "MongoDB is responding to ping"
else
    log_fail "MongoDB is not responding"
fi

# Database existence
log_info "Checking telegram_bot database..."
if docker-compose exec -T mongodb mongosh --authenticationDatabase admin -u admin -p changeme telegram_bot --eval "db.version()" > /dev/null 2>&1; then
    log_pass "telegram_bot database exists"
else
    log_fail "telegram_bot database does not exist"
fi

# Collections check
log_info "Checking database collections..."
COLLECTIONS=$(docker-compose exec -T mongodb mongosh --authenticationDatabase admin -u admin -p changeme telegram_bot --eval "db.getCollectionNames().length" 2>/dev/null | grep -oP '^\d+$' | tail -1)
if [ -n "$COLLECTIONS" ] && [ "$COLLECTIONS" -gt 0 ]; then
    log_pass "Database has $COLLECTIONS collections"
else
    log_warn "Database has no collections (this is OK for new deployments)"
fi

# ============================================
# 5. ENVIRONMENT CONFIGURATION
# ============================================

log_header "5️⃣  ENVIRONMENT CONFIGURATION"

# Check .env file
if [ -f .env ]; then
    log_pass ".env file exists"
    
    # Check critical variables
    for var in TELEGRAM_TOKEN MONGODB_URL JWT_SECRET; do
        if grep -q "^$var=" .env; then
            VALUE=$(grep "^$var=" .env | cut -d= -f2)
            if [ -z "$VALUE" ] || [ "$VALUE" = "your_bot_token_here" ] || [ "$VALUE" = "changeme" ]; then
                log_warn "$var is not set or uses default value"
            else
                log_pass "$var is configured"
            fi
        else
            log_warn "$var is not found in .env"
        fi
    done
else
    log_fail ".env file not found"
fi

# ============================================
# 6. DIRECTORY STRUCTURE
# ============================================

log_header "6️⃣  DIRECTORY STRUCTURE"

# Check required directories
for dir in api bot config core frontend services utils logs scripts; do
    if [ -d "$dir" ]; then
        log_pass "$dir directory exists"
    else
        log_warn "$dir directory not found"
    fi
done

# Check required files
for file in main.py requirements.txt Dockerfile docker-compose.yml; do
    if [ -f "$file" ]; then
        log_pass "$file exists"
    else
        log_warn "$file not found"
    fi
done

# ============================================
# 7. LOGS & PERMISSIONS
# ============================================

log_header "7️⃣  LOGS & PERMISSIONS"

# Check logs directory
if [ -d "logs" ]; then
    log_pass "logs directory exists"
    
    # Check logs are being written
    if [ -f "logs/bot.log" ] || [ -f "logs/api.log" ]; then
        log_pass "Log files are being created"
        
        # Check recent logs
        if [ -f "logs/api.log" ]; then
            RECENT_LOGS=$(tail -1 logs/api.log 2>/dev/null)
            if [ -n "$RECENT_LOGS" ]; then
                log_pass "Recent logs detected in api.log"
            fi
        fi
    else
        log_warn "No log files found yet (may be normal for new deployment)"
    fi
else
    log_warn "logs directory not created yet"
fi

# Check log permissions
if [ -d "logs" ]; then
    if [ -w "logs" ]; then
        log_pass "logs directory is writable"
    else
        log_fail "logs directory is not writable"
    fi
fi

# ============================================
# 8. DOCKER IMAGES
# ============================================

log_header "8️⃣  DOCKER IMAGES"

# Check for telegram-bot image
if docker images | grep -q "telegram-bot"; then
    TELEGRAM_BOT_IMAGE=$(docker images --filter "reference=telegram-bot" --format "{{.Tag}}")
    log_pass "telegram-bot image exists (tags: $TELEGRAM_BOT_IMAGE)"
else
    log_warn "telegram-bot image not found"
fi

# Check image sizes
log_info "Image sizes:"
docker images --filter "reference=telegram-bot" --format "{{.Repository}}\t{{.Size}}" || true
docker images --filter "reference=mongo" --format "{{.Repository}}\t{{.Size}}" || true
docker images --filter "reference=nginx" --format "{{.Repository}}\t{{.Size}}" || true

# ============================================
# 9. NETWORK CONNECTIVITY
# ============================================

log_header "9️⃣  NETWORK CONNECTIVITY"

# Check inter-service communication
log_info "Testing MongoDB connectivity from bot..."
if docker-compose exec -T telegram-bot python -c "
import asyncio
from motor.motor_asyncio import AsyncClient
import os

async def test():
    try:
        url = os.getenv('MONGODB_URL', 'mongodb://admin:changeme@mongodb:27017/telegram_bot?authSource=admin')
        client = AsyncClient(url, serverSelectionTimeoutMS=5000)
        await client.server_info()
        print('OK')
        client.close()
    except Exception as e:
        print(f'FAIL: {e}')

asyncio.run(test())
" 2>/dev/null | grep -q "OK"; then
    log_pass "Bot can connect to MongoDB"
else
    log_fail "Bot cannot connect to MongoDB"
fi

# ============================================
# 10. RESOURCE USAGE
# ============================================

log_header "🔟 RESOURCE USAGE"

# Memory usage
log_info "Memory usage:"
docker stats --no-stream --format "{{.Container}}\t{{.MemUsage}}" 2>/dev/null || log_warn "Could not get memory stats"

# Disk usage
log_info "Disk usage:"
echo "Project: $(du -sh . | awk '{print $1}')"
[ -d logs ] && echo "Logs: $(du -sh logs | awk '{print $1}')" || true
[ -d backups ] && echo "Backups: $(du -sh backups | awk '{print $1}')" || true

# Available disk
AVAILABLE=$(df -h . | awk 'NR==2 {print $4}')
if [ -n "$AVAILABLE" ]; then
    log_info "Available disk space: $AVAILABLE"
fi

# ============================================
# 11. BACKUP STATUS
# ============================================

log_header "1️⃣1️⃣  BACKUP STATUS"

if [ -d "backups" ]; then
    BACKUP_COUNT=$(find backups -maxdepth 1 -type d ! -name "backups" 2>/dev/null | wc -l)
    if [ "$BACKUP_COUNT" -gt 0 ]; then
        log_pass "$BACKUP_COUNT backups found"
        
        # Check latest backup age
        LATEST_BACKUP=$(find backups -maxdepth 1 -type d ! -name "backups" -printf '%T@\n' 2>/dev/null | sort -n | tail -1)
        if [ -n "$LATEST_BACKUP" ]; then
            BACKUP_AGE=$(echo "scale=1; ($(date +%s) - $LATEST_BACKUP) / 3600" | bc)
            log_info "Latest backup is $BACKUP_AGE hours old"
        fi
    else
        log_warn "No backups found yet"
    fi
else
    log_warn "No backups directory found"
fi

# ============================================
# 12. SERVICE LOGS ANALYSIS
# ============================================

log_header "1️⃣2️⃣  SERVICE LOGS ANALYSIS"

# Check for errors in recent logs
log_info "Checking for errors in recent logs..."

for service in telegram-bot mongodb nginx; do
    ERROR_COUNT=$(docker-compose logs "$service" 2>/dev/null | grep -ic "error\|failed\|exception" || echo "0")
    if [ "$ERROR_COUNT" -gt 0 ]; then
        log_warn "$service has $ERROR_COUNT error(s) in recent logs"
    else
        log_pass "$service has no errors in recent logs"
    fi
done

# ============================================
# 13. SECURITY CHECKS
# ============================================

log_header "1️⃣3️⃣  SECURITY CHECKS"

# Check for exposed secrets
if grep -r "TELEGRAM_TOKEN=" .env 2>/dev/null | grep -qv "your_bot_token"; then
    log_warn "Real TELEGRAM_TOKEN found in environment file (check .gitignore)"
fi

# Check .gitignore
if [ -f ".gitignore" ]; then
    if grep -q "\.env" .gitignore; then
        log_pass ".env is in .gitignore"
    else
        log_fail ".env is not in .gitignore"
    fi
else
    log_warn ".gitignore file not found"
fi

# Check JWT secret strength
if grep -q "JWT_SECRET=your_very_secret_key" .env 2>/dev/null; then
    log_fail "JWT_SECRET uses weak default value"
elif grep -q "JWT_SECRET=" .env 2>/dev/null; then
    JWT_LEN=$(grep "JWT_SECRET=" .env | cut -d= -f2 | wc -c)
    if [ "$JWT_LEN" -ge 32 ]; then
        log_pass "JWT_SECRET appears to have sufficient length ($JWT_LEN chars)"
    else
        log_warn "JWT_SECRET may be too short ($JWT_LEN chars)"
    fi
fi

# ============================================
# 14. FEATURE VALIDATION
# ============================================

log_header "1️⃣4️⃣  FEATURE VALIDATION"

# API endpoints
log_info "Testing API endpoints..."

# Test GET endpoints
ENDPOINTS=(
    "/health:200"
    "/docs:200"
    "/api/v1/users:200"
)

for endpoint_check in "${ENDPOINTS[@]}"; do
    ENDPOINT=$(echo $endpoint_check | cut -d: -f1)
    EXPECTED_CODE=$(echo $endpoint_check | cut -d: -f2)
    
    ACTUAL_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000$ENDPOINT" 2>/dev/null || echo "000")
    
    if [ "$ACTUAL_CODE" = "$EXPECTED_CODE" ]; then
        log_pass "$ENDPOINT returned $ACTUAL_CODE"
    else
        log_warn "$ENDPOINT returned $ACTUAL_CODE (expected $EXPECTED_CODE)"
    fi
done

# ============================================
# END OF VALIDATION
# ============================================

log_header "VALIDATION COMPLETE"
