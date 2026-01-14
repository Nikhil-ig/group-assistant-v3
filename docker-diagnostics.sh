#!/bin/bash

# Docker Diagnostic Script

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     Docker Diagnostic Report                                ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Determine if we need sudo for docker
DOCKER_CMD="docker"
if ! docker ps &>/dev/null 2>&1; then
    DOCKER_CMD="sudo docker"
fi

cd "$PROJECT_DIR"

echo -e "${BLUE}📊 Docker Compose Status:${NC}"
$DOCKER_CMD compose ps
echo ""

echo -e "${BLUE}🔴 Failed Containers:${NC}"
$DOCKER_CMD compose ps | grep -i "error\|exit\|unhealthy" || echo "No failed containers found"
echo ""

echo -e "${BLUE}📋 Centralized API Logs (last 100 lines):${NC}"
echo "================================="
$DOCKER_CMD compose logs centralized-api 2>&1 | tail -100
echo ""
echo "================================="
echo ""

echo -e "${BLUE}📋 Web Service Logs (last 50 lines):${NC}"
echo "================================="
$DOCKER_CMD compose logs web 2>&1 | tail -50
echo ""
echo "================================="
echo ""

echo -e "${BLUE}📋 Bot Logs (last 50 lines):${NC}"
echo "================================="
$DOCKER_CMD compose logs bot 2>&1 | tail -50
echo ""
echo "================================="
echo ""

echo -e "${BLUE}📊 Network Information:${NC}"
$DOCKER_CMD network ls
echo ""

echo -e "${BLUE}📊 Container Details:${NC}"
$DOCKER_CMD compose ps -a
echo ""

echo -e "${BLUE}💾 Volume Information:${NC}"
$DOCKER_CMD volume ls | grep -i "v3\|group" || echo "No v3 volumes found"
echo ""
