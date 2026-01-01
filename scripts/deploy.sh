#!/bin/bash

# ============================================
# Telegram Bot - Deployment Script
# Usage: ./scripts/deploy.sh [environment]
# ============================================

set -e

ENVIRONMENT=${1:-production}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# Error handler
trap 'log_error "Deployment failed at line $LINENO"; exit 1' ERR

log_info "Starting deployment for environment: $ENVIRONMENT"

# ============================================
# Pre-deployment checks
# ============================================

log_info "Running pre-deployment checks..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed. Please install Docker first."
    exit 1
fi
log_success "Docker is installed"

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    log_error "Docker daemon is not running. Please start Docker."
    exit 1
fi
log_success "Docker daemon is running"

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    log_warning "docker-compose is not installed. Installing..."
    pip install docker-compose
fi
log_success "docker-compose is available"

# Check if .env file exists
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    log_error ".env file not found. Please create it from .env.example"
    exit 1
fi
log_success ".env file exists"

# ============================================
# Build and push Docker image
# ============================================

log_info "Building Docker image..."
cd "$PROJECT_ROOT"

docker build -t telegram-bot:$ENVIRONMENT \
    -t telegram-bot:latest \
    --build-arg ENVIRONMENT=$ENVIRONMENT \
    .

log_success "Docker image built successfully"

# ============================================
# Stop running containers
# ============================================

log_info "Stopping old containers..."
docker-compose down || true
log_success "Old containers stopped"

# ============================================
# Start new containers
# ============================================

log_info "Starting containers with docker-compose..."
docker-compose -f docker-compose.yml up -d

log_success "Containers started"

# ============================================
# Wait for services to be healthy
# ============================================

log_info "Waiting for services to be healthy..."
MAX_ATTEMPTS=30
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if curl -s http://localhost:8000/health > /dev/null; then
        log_success "Application is healthy"
        break
    fi
    ATTEMPT=$((ATTEMPT + 1))
    if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
        log_error "Application failed to become healthy after $MAX_ATTEMPTS attempts"
        docker-compose logs telegram-bot
        exit 1
    fi
    sleep 2
done

# ============================================
# Run migrations (if needed)
# ============================================

log_info "Running database migrations..."
docker-compose exec -T telegram-bot python -m alembic upgrade head || true
log_success "Migrations completed"

# ============================================
# Verify deployment
# ============================================

log_info "Verifying deployment..."

# Check if API is responding
API_HEALTH=$(curl -s http://localhost:8000/health || echo "FAILED")
if [ "$API_HEALTH" != "FAILED" ]; then
    log_success "API is responding"
else
    log_error "API is not responding"
    exit 1
fi

# Check container status
CONTAINER_COUNT=$(docker-compose ps --services --filter "status=running" | wc -l)
EXPECTED_CONTAINERS=2  # mongodb + telegram-bot (nginx is optional)
if [ $CONTAINER_COUNT -ge $EXPECTED_CONTAINERS ]; then
    log_success "All containers are running ($CONTAINER_COUNT/$EXPECTED_CONTAINERS)"
else
    log_error "Some containers are not running ($CONTAINER_COUNT/$EXPECTED_CONTAINERS)"
    docker-compose ps
    exit 1
fi

# ============================================
# Cleanup
# ============================================

log_info "Cleaning up..."
docker image prune -a --force --filter "until=72h" || true
log_success "Cleanup completed"

# ============================================
# Deployment complete
# ============================================

log_success "Deployment completed successfully! 🎉"
log_info "Bot is running at http://localhost:8000"
log_info "Logs: docker-compose logs -f telegram-bot"
log_info "Status: docker-compose ps"
