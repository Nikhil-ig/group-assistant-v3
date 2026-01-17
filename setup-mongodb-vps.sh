#!/bin/bash

# 🚀 MongoDB VPS Installation & Configuration Script
# Automatically installs and configures MongoDB on Ubuntu/Debian VPS
# Usage: bash setup-mongodb-vps.sh

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  MongoDB VPS Setup & Configuration                         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Detect OS
if [ -f /etc/lsb-release ]; then
    . /etc/lsb-release
    DISTRIB=$DISTRIB_ID
elif [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRIB=$ID
else
    echo -e "${RED}❌ Cannot detect OS${NC}"
    exit 1
fi

echo -e "${BLUE}Detected OS: $DISTRIB${NC}"
echo ""

# Step 1: Update system
echo -e "${YELLOW}Step 1: Updating system packages...${NC}"
apt update -qq
apt upgrade -y -qq
echo -e "${GREEN}✅ System updated${NC}"
echo ""

# Step 2: Install MongoDB
echo -e "${YELLOW}Step 2: Installing MongoDB...${NC}"

# Add MongoDB GPG key
if ! command -v gnupg &> /dev/null; then
    apt install -y -qq gnupg
fi

# Add MongoDB repository (for Ubuntu 22.04/20.04)
if grep -q "jammy" /etc/os-release; then
    # Ubuntu 22.04 (Jammy)
    wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | apt-key add -
    echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-7.0.list
elif grep -q "focal" /etc/os-release; then
    # Ubuntu 20.04 (Focal)
    wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | apt-key add -
    echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/7.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-7.0.list
else
    # Generic Debian
    wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | apt-key add -
    echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/debian buster/mongodb-org/7.0 main" | tee /etc/apt/sources.list.d/mongodb-org-7.0.list
fi

apt update -qq
apt install -y -qq mongodb-org

echo -e "${GREEN}✅ MongoDB installed${NC}"
echo ""

# Step 3: Start MongoDB service
echo -e "${YELLOW}Step 3: Starting MongoDB service...${NC}"
systemctl daemon-reload
systemctl enable mongod
systemctl start mongod
sleep 2

if systemctl is-active --quiet mongod; then
    echo -e "${GREEN}✅ MongoDB service started and enabled${NC}"
else
    echo -e "${RED}❌ Failed to start MongoDB${NC}"
    systemctl status mongod
    exit 1
fi
echo ""

# Step 4: Verify MongoDB is running
echo -e "${YELLOW}Step 4: Verifying MongoDB...${NC}"
if netstat -tlnp 2>/dev/null | grep -q 27017; then
    echo -e "${GREEN}✅ MongoDB listening on port 27017${NC}"
else
    echo -e "${RED}❌ MongoDB not listening${NC}"
    exit 1
fi

# Test connection
if mongosh --eval "db.adminCommand('ping')" --quiet 2>/dev/null | grep -q "ok"; then
    echo -e "${GREEN}✅ MongoDB responding to ping${NC}"
else
    echo -e "${YELLOW}⚠️  Could not verify ping (this is OK if mongosh not installed)${NC}"
fi
echo ""

# Step 5: Initialize database
echo -e "${YELLOW}Step 5: Creating database and collections...${NC}"
mongosh << 'EOF' 2>/dev/null || true
use telegram_bot
db.createCollection("users")
db.createCollection("groups")
db.createCollection("moderation_logs")
db.createCollection("settings")
db.createCollection("whitelist")
db.createCollection("blacklist")
db.createCollection("night_mode")
db.createCollection("templates")

// Create indexes for performance
db.moderation_logs.createIndex({ "group_id": 1, "user_id": 1 })
db.moderation_logs.createIndex({ "timestamp": -1 })
db.groups.createIndex({ "group_id": 1 })
db.users.createIndex({ "user_id": 1 })
db.whitelist.createIndex({ "group_id": 1, "user_id": 1 })
db.blacklist.createIndex({ "group_id": 1, "blocked_item": 1 })

print("✅ Database and collections created")
EOF
echo -e "${GREEN}✅ Database initialized${NC}"
echo ""

# Step 6: Check storage and permissions
echo -e "${YELLOW}Step 6: Checking storage and permissions...${NC}"
MONGO_DATA="/var/lib/mongodb"
if [ -d "$MONGO_DATA" ]; then
    SPACE=$(df "$MONGO_DATA" | tail -1 | awk '{print $4}')
    if [ "$SPACE" -gt 1048576 ]; then
        echo -e "${GREEN}✅ Sufficient storage: $((SPACE/1024/1024))GB free${NC}"
    else
        echo -e "${YELLOW}⚠️  Low storage warning: $((SPACE/1024))MB free${NC}"
    fi
    
    # Check permissions
    ls -ld "$MONGO_DATA" | grep -q "mongodb.*mongodb" && echo -e "${GREEN}✅ Correct permissions${NC}" || echo -e "${YELLOW}⚠️  Check permissions${NC}"
fi
echo ""

# Step 7: Configuration summary
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}✅ MongoDB Setup Complete!${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📊 Configuration Summary:${NC}"
echo "  • Status:        $(systemctl is-active mongod)"
echo "  • Port:          27017"
echo "  • Data Path:     $MONGO_DATA"
echo "  • Database:      telegram_bot"
echo "  • Collections:   users, groups, moderation_logs, settings, etc."
echo ""

echo -e "${YELLOW}📝 Next Steps:${NC}"
echo "  1. Update /v3/.env with correct MONGODB_URL (if using auth)"
echo "  2. Restart bot services: cd /v3 && bash start_all_services.sh"
echo "  3. Test bot commands in Telegram"
echo ""

echo -e "${BLUE}🔍 Useful Commands:${NC}"
echo "  • Check status:      systemctl status mongod"
echo "  • View logs:         tail -f /var/log/mongodb/mongod.log"
echo "  • Connect to DB:     mongosh"
echo "  • Stop MongoDB:      systemctl stop mongod"
echo "  • Restart MongoDB:   systemctl restart mongod"
echo ""

echo -e "${YELLOW}✅ Setup complete! MongoDB is ready for the Telegram bot.${NC}"
echo ""
