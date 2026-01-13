#!/bin/bash
################################################################################
# VPS Deployment Script
# Run this on VPS to pull latest code and restart services
# Usage: ./deploy-vps.sh or setup cron: */5 * * * * /path/to/deploy-vps.sh
################################################################################

set -e  # Exit on error

# Configuration
PROJECT_DIR="/opt/group-assistant-v3"
REPO_URL="https://github.com/Nikhil-ig/group-assistant-v3.git"
LOG_FILE="/var/log/group-assistant-deploy.log"
LOCK_FILE="/tmp/group-assistant-deploy.lock"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ============================================================================
# FUNCTIONS
# ============================================================================

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ❌ ERROR: $1${NC}" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] ✅ $1${NC}" | tee -a "$LOG_FILE"
}

log_info() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] ℹ️  $1${NC}" | tee -a "$LOG_FILE"
}

# Acquire lock to prevent concurrent deployments
acquire_lock() {
    if [ -f "$LOCK_FILE" ]; then
        log_error "Deployment already in progress (lock file exists)"
        exit 1
    fi
    touch "$LOCK_FILE"
    trap "rm -f $LOCK_FILE" EXIT
}

# ============================================================================
# MAIN DEPLOYMENT
# ============================================================================

main() {
    log "======================================================================"
    log "🚀 Starting VPS Deployment"
    log "======================================================================"
    
    acquire_lock
    
    # Check if project directory exists
    if [ ! -d "$PROJECT_DIR" ]; then
        log_info "Project directory not found. Cloning repository..."
        mkdir -p /opt
        cd /opt
        git clone "$REPO_URL" || {
            log_error "Failed to clone repository"
            exit 1
        }
    fi
    
    cd "$PROJECT_DIR" || {
        log_error "Failed to enter project directory"
        exit 1
    }
    
    # ========================================================================
    # 1. FETCH & PULL LATEST CODE
    # ========================================================================
    log_info "Fetching latest code from GitHub..."
    git fetch origin main || {
        log_error "Failed to fetch from GitHub"
        exit 1
    }
    
    # Check if there are new commits
    LOCAL=$(git rev-parse HEAD)
    REMOTE=$(git rev-parse origin/main)
    
    if [ "$LOCAL" = "$REMOTE" ]; then
        log_success "Already up to date. No deployment needed."
        exit 0
    fi
    
    log_info "New commits detected. Resetting to latest..."
    git reset --hard origin/main || {
        log_error "Failed to reset to origin/main"
        exit 1
    }
    
    log_success "Code updated to latest version"
    
    # ========================================================================
    # 2. VERIFY .env FILES EXIST
    # ========================================================================
    log_info "Checking .env files..."
    
    if [ ! -f "bot/.env" ]; then
        log_error "bot/.env not found! Please create it manually on VPS."
        log_error "Template: bot/.env.example"
        exit 1
    fi
    
    if [ ! -f "centralized_api/.env" ]; then
        log_error "centralized_api/.env not found! Please create it manually on VPS."
        log_error "Template: centralized_api/.env.example"
        exit 1
    fi
    
    log_success ".env files verified"
    
    # ========================================================================
    # 3. PULL DOCKER IMAGES & BUILD
    # ========================================================================
    log_info "Pulling latest Docker images and building..."
    docker compose pull || {
        log_error "Failed to pull Docker images"
        exit 1
    }
    
    docker compose build --no-cache || {
        log_error "Failed to build Docker images"
        exit 1
    }
    
    log_success "Docker images built successfully"
    
    # ========================================================================
    # 4. STOP OLD SERVICES
    # ========================================================================
    log_info "Stopping old services..."
    docker compose down || true  # Don't exit if nothing is running
    
    log_success "Old services stopped"
    
    # ========================================================================
    # 5. START NEW SERVICES
    # ========================================================================
    log_info "Starting services..."
    docker compose up -d || {
        log_error "Failed to start services"
        exit 1
    }
    
    # Wait for services to start
    sleep 5
    
    log_success "Services started successfully"
    
    # ========================================================================
    # 6. VERIFY SERVICES ARE HEALTHY
    # ========================================================================
    log_info "Verifying service health..."
    
    # Check if containers are running
    if docker compose ps | grep -q "Exit"; then
        log_error "Some containers exited. Check logs:"
        docker compose logs
        exit 1
    fi
    
    log_success "All containers are running"
    
    # ========================================================================
    # 7. HEALTH CHECK
    # ========================================================================
    log_info "Running health checks..."
    
    # Wait a bit for API to be ready
    sleep 5
    
    # Try to reach API
    if curl -f http://localhost:8000/api/health >/dev/null 2>&1; then
        log_success "Centralized API is healthy"
    else
        log_error "Centralized API health check failed"
        log_error "Checking logs:"
        docker compose logs centralized_api
    fi
    
    log "======================================================================"
    log_success "✅ DEPLOYMENT COMPLETE!"
    log "======================================================================"
    log "📊 Service Status:"
    docker compose ps
    log ""
    log "📝 View logs:"
    log "  docker compose logs -f          # All services"
    log "  docker compose logs -f bot      # Bot only"
    log "  docker compose logs -f centralized_api"
    log ""
    log "🛑 To stop services: docker compose down"
    log "======================================================================"
}

# ============================================================================
# ERROR HANDLING
# ============================================================================

trap 'log_error "Deployment failed"; exit 1' ERR

# ============================================================================
# RUN MAIN
# ============================================================================

main "$@"
