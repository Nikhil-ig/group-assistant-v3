#!/bin/bash

# ============================================
# Telegram Bot - Monitoring Script
# Monitors application health and performance
# Usage: ./scripts/monitor.sh
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

log_header() { echo -e "\n${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n${CYAN}$1${NC}\n${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"; }
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

cd "$PROJECT_ROOT"

# ============================================
# Service Status
# ============================================

log_header "SERVICE STATUS"

RUNNING=$(docker-compose ps --services --filter "status=running" | wc -l)
TOTAL=$(docker-compose ps --services | wc -l)

echo "Services running: ${GREEN}$RUNNING${NC}/$TOTAL"
echo ""

docker-compose ps --no-trunc

# ============================================
# Container Statistics
# ============================================

log_header "CONTAINER STATISTICS"

docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" || log_warning "Unable to fetch container stats"

# ============================================
# Health Checks
# ============================================

log_header "HEALTH CHECKS"

# API Health
log_info "Checking API health..."
if curl -s http://localhost:8000/health > /dev/null; then
    log_success "API is healthy"
else
    log_error "API health check failed"
fi

# MongoDB Health
log_info "Checking MongoDB health..."
if docker-compose exec -T mongodb mongosh --authenticationDatabase admin -u admin -p changeme --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
    log_success "MongoDB is healthy"
else
    log_error "MongoDB health check failed"
fi

# ============================================
# API Endpoint Tests
# ============================================

log_header "API ENDPOINT TESTS"

log_info "Testing API endpoints..."

# Test health endpoint
log_info "GET /health"
curl -s -w "Status: %{http_code}\n" http://localhost:8000/health | tail -1 || log_error "Failed"

# Test docs
log_info "GET /docs"
DOCS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs)
if [ "$DOCS_STATUS" = "200" ]; then
    log_success "API docs available"
else
    log_warning "API docs returned status $DOCS_STATUS"
fi

# ============================================
# Log Analysis
# ============================================

log_header "RECENT LOGS"

log_info "Last 10 errors in bot logs:"
docker-compose logs telegram-bot 2>&1 | grep -i error | tail -10 || log_success "No errors found"

log_info "Last 5 bot logs:"
docker-compose logs telegram-bot --tail 5

# ============================================
# Database Statistics
# ============================================

log_header "DATABASE STATISTICS"

log_info "Checking MongoDB collections..."
docker-compose exec -T mongodb mongosh --authenticationDatabase admin -u admin -p changeme --eval "
  var dbs = db.adminCommand('listDatabases').databases;
  dbs.forEach(db => {
    if(db.name === 'telegram_bot') {
      var collections = db(db.name).getCollectionNames();
      print('Collections: ' + collections.length);
      collections.forEach(col => {
        var count = db(db.name)[col].countDocuments({});
        print('  ' + col + ': ' + count + ' documents');
      });
    }
  });
" 2>/dev/null || log_warning "Unable to fetch database statistics"

# ============================================
# Disk Usage
# ============================================

log_header "DISK USAGE"

log_info "Project directory:"
du -sh "$PROJECT_ROOT" | awk '{print $1}'

log_info "Docker volumes:"
docker volume ls --filter "label=com.docker.compose.project=v3" --format "table {{.Name}}\t{{.Mountpoint}}"

log_info "Logs directory:"
du -sh logs 2>/dev/null || echo "0B"

# ============================================
# Network Connectivity
# ============================================

log_header "NETWORK CONNECTIVITY"

log_info "Checking inter-service connectivity..."

# Test bot to MongoDB
docker-compose exec -T telegram-bot python -c "
import asyncio
from motor.motor_asyncio import AsyncClient

async def test():
    client = AsyncClient('mongodb://admin:changeme@mongodb:27017/telegram_bot?authSource=admin')
    db = client.telegram_bot
    ping = await db.command('ping')
    print('✅ MongoDB connectivity: OK' if ping.get('ok') == 1 else '❌ MongoDB connectivity: FAILED')
    client.close()

asyncio.run(test())
" 2>/dev/null || log_warning "Unable to test MongoDB connectivity"

# ============================================
# Summary
# ============================================

log_header "MONITORING SUMMARY"

if [ "$RUNNING" = "$TOTAL" ]; then
    log_success "All services running"
else
    log_warning "Some services are not running"
fi

log_info "Monitoring completed at $(date '+%Y-%m-%d %H:%M:%S')"
log_info "For detailed logs, run: docker-compose logs -f [service]"
log_info "Services: mongodb, telegram-bot, nginx"
