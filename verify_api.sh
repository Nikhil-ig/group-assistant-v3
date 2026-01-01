#!/bin/bash

# 🚀 API & Web Integration Verification Script
# Verifies all new API endpoints and web integration are working

set -e

echo "🔍 Verifying API & Web Integration Setup..."
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0

# Test function
test_file() {
    local file=$1
    local description=$2
    
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅${NC} $description"
        echo "   Location: $file"
        ((PASSED++))
    else
        echo -e "${RED}❌${NC} $description"
        echo "   Missing: $file"
        ((FAILED++))
    fi
}

test_content() {
    local file=$1
    local search=$2
    local description=$3
    
    if grep -q "$search" "$file" 2>/dev/null; then
        echo -e "${GREEN}✅${NC} $description"
        ((PASSED++))
    else
        echo -e "${RED}❌${NC} $description"
        ((FAILED++))
    fi
}

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "📁 Checking File Structure..."
echo ""

# 1. Check API files
echo "🔌 API Layer:"
test_file "api/endpoints.py" "API endpoints file"
test_content "api/endpoints.py" "class FreeRequest" "FreeRequest model in endpoints.py"
test_content "api/endpoints.py" "class UserIDRequest" "UserIDRequest model in endpoints.py"
test_content "api/endpoints.py" "class SettingsResponse" "SettingsResponse model in endpoints.py"
test_content "api/endpoints.py" "@router.post.*free" "POST /commands/free endpoint"
test_content "api/endpoints.py" "@router.post.*commands/id" "POST /commands/id endpoint"
test_content "api/endpoints.py" "@router.get.*commands/settings" "GET /commands/settings endpoint"
test_content "api/endpoints.py" "@router.post.*promote" "POST /commands/promote endpoint"
test_content "api/endpoints.py" "@router.post.*demote" "POST /commands/demote endpoint"
echo ""

# 2. Check Bot handlers
echo "🤖 Bot Handlers:"
test_file "bot/handlers.py" "Bot handlers file"
test_content "bot/handlers.py" "async def free_user" "free_user() handler"
test_content "bot/handlers.py" "async def user_id" "user_id() handler"
test_content "bot/handlers.py" "async def settings" "settings() handler"
test_content "bot/handlers.py" "async def promote" "promote() handler"
test_content "bot/handlers.py" "async def demote" "demote() handler"
echo ""

# 3. Check Web files
echo "🌐 Web Layer:"
test_file "web/commands.html" "Web UI dashboard"
test_content "web/commands.html" "class ModerationAPI" "API client in HTML"
test_content "web/commands.html" "freeUser" "freeUser method in HTML"
test_content "web/commands.html" "promoteUser" "promoteUser method in HTML"
echo ""

# 4. Check TypeScript service
echo "📱 TypeScript Service:"
test_file "frontend/service.ts" "TypeScript service file"
test_content "frontend/service.ts" "freeUser" "freeUser() method"
test_content "frontend/service.ts" "getUserID" "getUserID() method"
test_content "frontend/service.ts" "getGroupSettings" "getGroupSettings() method"
test_content "frontend/service.ts" "promoteUser" "promoteUser() method"
test_content "frontend/service.ts" "demoteUser" "demoteUser() method"
echo ""

# 5. Check documentation
echo "📚 Documentation:"
test_file "API_DOCUMENTATION.md" "API Documentation"
test_file "API_INTEGRATION_GUIDE.md" "Integration Guide"
test_file "QUICK_START_API.md" "Quick Start Guide"
test_file "QUICK_REF_NEW_COMMANDS.md" "Command Reference"
test_file "NEW_COMMANDS_TEST.md" "Test Guide"
echo ""

# 6. Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Verification Results:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ Passed: $PASSED${NC}"
echo -e "${RED}❌ Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All checks passed! API & Web integration is ready.${NC}"
    echo ""
    echo "📖 Next Steps:"
    echo "1. Start the API server: python main.py"
    echo "2. Test Web UI: http://localhost:8000/web/commands.html"
    echo "3. Read documentation: API_DOCUMENTATION.md"
    echo "4. Test endpoints with: QUICK_START_API.md"
    exit 0
else
    echo -e "${RED}⚠️  Some checks failed. Please review the output above.${NC}"
    exit 1
fi
