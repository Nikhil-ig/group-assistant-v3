#!/bin/bash
################################################################################
# GitHub Webhook Receiver Script
# This script listens for GitHub push events and triggers deployment
# 
# Setup:
# 1. Copy this to: /opt/webhook-receiver.sh
# 2. chmod +x /opt/webhook-receiver.sh
# 3. Set up as systemd service (see webhook.service below)
# 4. Add GitHub webhook: https://github.com/Nikhil-ig/group-assistant-v3/settings/hooks
#    - Payload URL: http://your.vps.ip:9000/webhook
#    - Content type: application/json
#    - Secret: (optional, but recommended)
# 5. sudo systemctl start webhook-receiver
#    sudo systemctl enable webhook-receiver
################################################################################

PORT=9000
PROJECT_DIR="/opt/group-assistant-v3"
DEPLOY_SCRIPT="/opt/group-assistant-v3/deploy-vps.sh"
LOG_FILE="/var/log/webhook-receiver.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Simple HTTP server using bash
run_webhook_server() {
    log "Starting webhook receiver on port $PORT"
    
    while IFS= read -r -t 1 -u 3 line; do
        # Read HTTP request
        [ -z "$line" ] && {
            # Parse POST body
            read -t 1 body
            
            # Check if it's a push event to main branch
            if echo "$body" | grep -q '"ref":"refs/heads/main"'; then
                log "📩 Received webhook for main branch push"
                log "🚀 Triggering deployment..."
                
                # Run deployment in background
                nohup "$DEPLOY_SCRIPT" >> "$LOG_FILE" 2>&1 &
                
                # Send HTTP response
                echo -e "HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nOK" | nc -N localhost $PORT 2>/dev/null || true
            else
                log "⏭️  Webhook received but not for main branch, skipping"
                echo -e "HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nOK" | nc -N localhost $PORT 2>/dev/null || true
            fi
        }
    done < <(nc -l -p $PORT)
}

run_webhook_server
