#!/bin/bash

# Docker Compose Stop Script for V3 Microservices

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     V3 Microservices Shutdown - Docker Compose              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

cd "$PROJECT_DIR"

echo -e "${BLUE}Stopping all containers...${NC}"
docker compose down

echo ""
echo -e "${GREEN}✅ All services stopped${NC}"
echo ""

echo "📊 Current containers:"
docker compose ps
echo ""

echo "💡 To remove all data volumes as well, run:"
echo "   docker compose down -v"
echo ""
