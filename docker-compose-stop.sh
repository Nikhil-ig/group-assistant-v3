#!/bin/bash

# Docker Compose Stop Script for V3 Microservices

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     V3 Microservices Shutdown - Docker Compose              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Determine if we need sudo for docker
DOCKER_CMD="docker"
if ! docker ps &>/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Docker requires sudo, using 'sudo docker'${NC}"
    DOCKER_CMD="sudo docker"
fi

cd "$PROJECT_DIR"

echo -e "${BLUE}Stopping all containers...${NC}"
$DOCKER_CMD compose down

echo ""
echo -e "${GREEN}✅ All services stopped${NC}"
echo ""

echo "📊 Current containers:"
$DOCKER_CMD compose ps
echo ""

echo "💡 To remove all data volumes as well, run:"
echo "   $DOCKER_CMD compose down -v"
echo ""
