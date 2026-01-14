#!/bin/bash

# Docker Compose Startup Script for V3 Microservices
# This script starts all services using Docker Compose (recommended for VPS)

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     V3 Microservices Startup - Using Docker Compose         ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Determine if we need sudo for docker
DOCKER_CMD="docker"
if ! docker ps &>/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Docker requires sudo, using 'sudo docker'${NC}"
    DOCKER_CMD="sudo docker"
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed!${NC}"
    echo "Please install Docker from: https://docs.docker.com/engine/install/"
    exit 1
fi

# Check if Docker Compose is installed
if ! $DOCKER_CMD compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed!${NC}"
    echo "Please install Docker Compose from: https://docs.docker.com/compose/install/"
    exit 1
fi

echo -e "${BLUE}🐳 Starting services with Docker Compose...${NC}"
echo ""

cd "$PROJECT_DIR"

# Pull latest images
echo -e "${BLUE}📥 Pulling latest Docker images...${NC}"
$DOCKER_CMD compose pull 2>/dev/null || echo "⚠️  Some images may need to be built"
echo ""

# Start services
echo -e "${BLUE}🚀 Starting all services...${NC}"
$DOCKER_CMD compose up -d

echo -e "${GREEN}✅ Services started!${NC}"
echo ""

# Wait for services to initialize
echo -e "${BLUE}⏳ Waiting for services to initialize (10 seconds)...${NC}"
sleep 10

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                  ✅ ALL SERVICES STARTED                    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Show service status
echo "📊 Service Status:"
echo ""
$DOCKER_CMD compose ps
echo ""

echo "🔗 Access Points:"
echo "  • Centralized API: http://localhost:8000"
echo "  • Web Service:     http://localhost:8002"
echo "  • API Docs:        http://localhost:8000/docs"
echo "  • Web Docs:        http://localhost:8002/docs"
echo ""

echo "📊 Container Information:"
echo "  • Docker Network:  v3-network"
echo "  • MongoDB:         mongodb://root:example@mongo:27017"
echo "  • Redis:           redis://redis:6379"
echo ""

echo "📝 View Logs:"
echo "  • All logs:        $DOCKER_CMD compose logs -f"
echo "  • API logs:        $DOCKER_CMD compose logs -f centralized-api"
echo "  • Web logs:        $DOCKER_CMD compose logs -f web"
echo "  • Bot logs:        $DOCKER_CMD compose logs -f bot"
echo "  • MongoDB logs:    $DOCKER_CMD compose logs -f mongo"
echo "  • Redis logs:      $DOCKER_CMD compose logs -f redis"
echo ""

echo "🛑 To stop all services, run:"
echo "  $DOCKER_CMD compose down"
echo ""

echo "💾 To stop and remove all data, run:"
echo "  $DOCKER_CMD compose down -v"
echo ""
