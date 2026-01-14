#!/bin/bash

# Docker Cleanup and Reset Script

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     Docker Cleanup and Reset                                ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Determine if we need sudo for docker
DOCKER_CMD="docker"
if ! docker ps &>/dev/null 2>&1; then
    DOCKER_CMD="sudo docker"
fi

cd "$PROJECT_DIR"

echo -e "${BLUE}🛑 Stopping all containers...${NC}"
$DOCKER_CMD compose down 2>/dev/null || true
sleep 2

echo -e "${BLUE}🧹 Removing dangling containers...${NC}"
$DOCKER_CMD container prune -f 2>/dev/null || true

echo -e "${BLUE}🧹 Removing dangling images...${NC}"
$DOCKER_CMD image prune -f 2>/dev/null || true

echo -e "${BLUE}🧹 Removing dangling volumes...${NC}"
$DOCKER_CMD volume prune -f 2>/dev/null || true

echo ""
echo -e "${BLUE}🔍 Checking for processes on port 8000, 8001, 8002, 8003...${NC}"
for PORT in 8000 8001 8002 8003; do
    if netstat -tulpn 2>/dev/null | grep -q ":$PORT "; then
        echo -e "${YELLOW}⚠️  Port $PORT is still in use${NC}"
        PID=$(netstat -tulpn 2>/dev/null | grep ":$PORT " | awk '{print $NF}' | cut -d'/' -f1)
        if [ ! -z "$PID" ] && [ "$PID" != "-" ]; then
            echo -e "${YELLOW}   Killing process $PID${NC}"
            kill -9 $PID 2>/dev/null || true
        fi
    else
        echo -e "${GREEN}✅ Port $PORT is free${NC}"
    fi
done

sleep 2

echo ""
echo -e "${GREEN}✅ Cleanup complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. cd $PROJECT_DIR"
echo "  2. ./docker-compose-start.sh"
echo ""
