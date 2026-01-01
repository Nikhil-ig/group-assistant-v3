#!/bin/bash

# ============================================
# Telegram Bot - Rollback Script
# Usage: ./scripts/rollback.sh [version]
# ============================================

set -e

VERSION=${1:-latest}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

trap 'log_error "Rollback failed at line $LINENO"; exit 1' ERR

log_info "Starting rollback to version: $VERSION"

cd "$PROJECT_ROOT"

# ============================================
# Backup current state
# ============================================

log_info "Backing up current configuration..."
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup database
docker-compose exec -T mongodb mongodump --uri="mongodb://admin:changeme@localhost:27017/telegram_bot?authSource=admin" --out="$BACKUP_DIR/mongodb_backup" || true
log_success "Database backed up to $BACKUP_DIR"

# Backup logs
cp -r logs "$BACKUP_DIR/logs" || true
log_success "Logs backed up"

# ============================================
# Stop current containers
# ============================================

log_info "Stopping current containers..."
docker-compose down
log_success "Containers stopped"

# ============================================
# Rollback to previous version
# ============================================

log_info "Rolling back to version: $VERSION"

# Get the previous version from Git
git fetch origin
git checkout $VERSION
git pull origin $VERSION

log_success "Rolled back to version: $VERSION"

# ============================================
# Start services with previous version
# ============================================

log_info "Starting services with previous version..."
docker-compose up -d
log_success "Services started"

# ============================================
# Verify rollback
# ============================================

log_info "Verifying rollback..."

MAX_ATTEMPTS=30
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if curl -s http://localhost:8000/health > /dev/null; then
        log_success "Application is healthy"
        break
    fi
    ATTEMPT=$((ATTEMPT + 1))
    if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
        log_error "Application failed to become healthy"
        docker-compose logs telegram-bot
        exit 1
    fi
    sleep 2
done

# ============================================
# Rollback complete
# ============================================

log_success "Rollback completed successfully! 🎉"
log_info "Previous version is now running"
log_info "Backup saved to: $BACKUP_DIR"
log_warning "Please review the rollback and verify everything is working correctly"
log_info "Logs: docker-compose logs -f telegram-bot"
