#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting API Reference Replacement (centralized_api → api_v2)${NC}\n"

# Files to replace
files_to_process=(
    "bot/.env.example"
    "bot/.env"
    "bot/main.py"
    "bot/README.md"
    "web/app.py"
    "web/README.md"
    "web/frontend/src/types/index.ts"
    ".env.template"
    "start_all_services.sh"
    "BOT_TOKEN_SETUP.md"
    "docker-compose.yml"
    "docker-compose.prod.yml"
    "SYNC_QUICK_START.md"
    "setup-vps.sh"
    "deploy-vps.sh"
    "QUICK_START.md"
    "QUICK_REFERENCE.txt"
    "README.md"
    "START_GUIDE.md"
    "CALLBACK_IMPLEMENTATION_SUMMARY.md"
    "VISUAL_WORKFLOW.md"
    "VPS_DEPLOYMENT.md"
    "DASHBOARD_LAUNCH_GUIDE.md"
)

count=0

for file in "${files_to_process[@]}"; do
    if [ -f "$file" ]; then
        # Replace CENTRALIZED_API_URL with API_V2_URL
        sed -i '' 's/CENTRALIZED_API_URL/API_V2_URL/g' "$file"
        
        # Replace CENTRALIZED_API_KEY with API_V2_KEY
        sed -i '' 's/CENTRALIZED_API_KEY/API_V2_KEY/g' "$file"
        
        # Replace centralized_api with api_v2 in comments and text
        sed -i '' 's/centralized_api/api_v2/g' "$file"
        
        # Replace centralized-api with api-v2 in URLs/hostnames
        sed -i '' 's/centralized-api/api-v2/g' "$file"
        
        # Replace :8000 with :8002 (old API port → new API port)
        sed -i '' 's/:8000/:8002/g' "$file"
        sed -i '' 's/:8001/:8002/g' "$file"
        
        echo -e "${GREEN}✅${NC} $file"
        ((count++))
    fi
done

echo -e "\n${BLUE}Processed ${count} files${NC}"
echo -e "\n${BLUE}Additional replacements:${NC}"

# Replace in CentralizedAPIClient class references
echo "Searching for class name references..."
grep -r "CentralizedAPIClient" . --include="*.py" 2>/dev/null | head -5 | cut -d: -f1 | sort -u | while read file; do
    if [ -n "$file" ]; then
        sed -i '' 's/CentralizedAPIClient/APIv2Client/g' "$file"
        echo -e "${GREEN}✅${NC} Updated class name in $file"
    fi
done

echo -e "\n${GREEN}✅ Replacement Complete!${NC}"
