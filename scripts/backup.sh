#!/bin/bash

# ============================================
# Telegram Bot - Backup Management Script
# Automated backup and cleanup procedures
# Usage: ./scripts/backup.sh [backup|restore|cleanup|schedule]
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$PROJECT_ROOT/backups"
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

cd "$PROJECT_ROOT"

# ============================================
# BACKUP FUNCTION
# ============================================

backup() {
    log_info "Starting backup..."
    
    # Create backup directory
    BACKUP_NAME="telegram_bot_$(date +%Y%m%d_%H%M%S)"
    BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"
    mkdir -p "$BACKUP_PATH"
    
    # Backup MongoDB
    log_info "Backing up MongoDB..."
    mkdir -p "$BACKUP_PATH/mongodb"
    
    if docker-compose ps mongodb 2>/dev/null | grep -q "Up"; then
        docker-compose exec -T mongodb mongodump \
            --uri="mongodb://admin:changeme@localhost:27017/telegram_bot?authSource=admin" \
            --out="$BACKUP_PATH/mongodb" 2>/dev/null || {
            log_error "MongoDB backup failed"
            rm -rf "$BACKUP_PATH"
            return 1
        }
        log_success "MongoDB backed up"
    else
        log_warning "MongoDB container not running, skipping database backup"
    fi
    
    # Backup application files
    log_info "Backing up application files..."
    for dir in api bot config core services utils; do
        if [ -d "$dir" ]; then
            tar -czf "$BACKUP_PATH/${dir}.tar.gz" "$dir" 2>/dev/null || true
        fi
    done
    log_success "Application files backed up"
    
    # Backup configuration
    log_info "Backing up configuration..."
    if [ -f ".env" ]; then
        # Mask sensitive values for backup
        sed 's/=.*/=***REDACTED***/g' .env > "$BACKUP_PATH/.env.backup"
        log_success "Configuration backed up (secrets redacted)"
    fi
    
    # Backup logs
    log_info "Backing up logs..."
    if [ -d "logs" ]; then
        tar -czf "$BACKUP_PATH/logs.tar.gz" logs/ 2>/dev/null || true
        log_success "Logs backed up"
    fi
    
    # Create backup info file
    cat > "$BACKUP_PATH/backup_info.txt" << EOF
Backup Information
==================

Name: $BACKUP_NAME
Date: $(date '+%Y-%m-%d %H:%M:%S')
Hostname: $(hostname)
User: $(whoami)

Contents:
- MongoDB database dump
- Application source code
- Configuration (secrets redacted)
- Application logs

To restore:
  ./scripts/backup.sh restore $BACKUP_NAME

Size: $(du -sh "$BACKUP_PATH" | awk '{print $1}')
EOF
    
    log_success "Backup completed: $BACKUP_PATH"
    log_info "Backup size: $(du -sh "$BACKUP_PATH" | awk '{print $1}')"
    
    return 0
}

# ============================================
# RESTORE FUNCTION
# ============================================

restore() {
    BACKUP_NAME=$1
    
    if [ -z "$BACKUP_NAME" ]; then
        log_error "Please specify backup name to restore"
        list_backups
        return 1
    fi
    
    BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"
    
    if [ ! -d "$BACKUP_PATH" ]; then
        log_error "Backup not found: $BACKUP_PATH"
        list_backups
        return 1
    fi
    
    log_warning "Restoring from backup: $BACKUP_NAME"
    read -p "Are you sure you want to restore? This will overwrite current data. (yes/no) " -n 3 -r
    echo
    if [[ ! $REPLY =~ ^yes$ ]]; then
        log_info "Restore cancelled"
        return 0
    fi
    
    # Stop services
    log_info "Stopping services..."
    docker-compose down
    
    # Restore MongoDB
    if [ -d "$BACKUP_PATH/mongodb" ]; then
        log_info "Restoring MongoDB..."
        
        # Start MongoDB temporarily
        docker-compose up -d mongodb
        
        # Wait for MongoDB to be ready
        log_info "Waiting for MongoDB to be ready..."
        sleep 5
        
        # Restore
        docker-compose exec -T mongodb mongorestore \
            --uri="mongodb://admin:changeme@localhost:27017/telegram_bot?authSource=admin" \
            "$BACKUP_PATH/mongodb" 2>/dev/null || log_error "MongoDB restore failed"
        
        log_success "MongoDB restored"
    fi
    
    # Restore application files
    log_info "Restoring application files..."
    for dir in api bot config core services utils; do
        if [ -f "$BACKUP_PATH/${dir}.tar.gz" ]; then
            tar -xzf "$BACKUP_PATH/${dir}.tar.gz" 2>/dev/null || true
            log_success "Restored $dir"
        fi
    done
    
    # Restore all services
    log_info "Starting all services..."
    docker-compose up -d
    
    log_success "Restore completed from: $BACKUP_NAME"
    
    return 0
}

# ============================================
# CLEANUP FUNCTION
# ============================================

cleanup() {
    log_info "Cleaning up old backups (retention: $RETENTION_DAYS days)..."
    
    if [ ! -d "$BACKUP_DIR" ]; then
        log_info "No backups directory found"
        return 0
    fi
    
    DELETED_COUNT=0
    
    while IFS= read -r backup_path; do
        BACKUP_NAME=$(basename "$backup_path")
        log_warning "Removing old backup: $BACKUP_NAME"
        rm -rf "$backup_path"
        ((DELETED_COUNT++))
    done < <(find "$BACKUP_DIR" -maxdepth 1 -type d ! -name "backups" -mtime +$RETENTION_DAYS)
    
    if [ $DELETED_COUNT -gt 0 ]; then
        log_success "Removed $DELETED_COUNT old backup(s)"
    else
        log_info "No backups older than $RETENTION_DAYS days found"
    fi
    
    return 0
}

# ============================================
# LIST BACKUPS FUNCTION
# ============================================

list_backups() {
    echo ""
    echo "Available backups:"
    echo "=================="
    
    if [ ! -d "$BACKUP_DIR" ] || [ -z "$(ls -A "$BACKUP_DIR")" ]; then
        echo "No backups found"
        return 0
    fi
    
    while IFS= read -r backup_path; do
        BACKUP_NAME=$(basename "$backup_path")
        SIZE=$(du -sh "$backup_path" | awk '{print $1}')
        DATE=$(stat -f %Sm -t "%Y-%m-%d %H:%M:%S" "$backup_path" 2>/dev/null || echo "Unknown")
        
        echo "  - $BACKUP_NAME ($SIZE) [$DATE]"
        
        if [ -f "$backup_path/backup_info.txt" ]; then
            head -3 "$backup_path/backup_info.txt" | sed 's/^/      /'
        fi
    done < <(find "$BACKUP_DIR" -maxdepth 1 -type d ! -name "backups" | sort -r)
    
    echo ""
}

# ============================================
# SCHEDULE FUNCTION
# ============================================

schedule() {
    log_info "Setting up automated backups..."
    
    # Check if crontab exists
    if [ -f "/etc/cron.d/telegram-bot-backup" ]; then
        log_warning "Backup schedule already exists"
        cat /etc/cron.d/telegram-bot-backup
        return 0
    fi
    
    # Create cron job (daily at 2 AM)
    log_info "Creating daily backup schedule (2:00 AM)..."
    
    CRON_ENTRY="0 2 * * * cd $PROJECT_ROOT && $SCRIPT_DIR/backup.sh backup >> logs/backup.log 2>&1"
    
    # Try to add to crontab
    (crontab -l 2>/dev/null | grep -v "telegram-bot-backup"; echo "$CRON_ENTRY") | crontab - || {
        log_warning "Could not set up crontab (you may need sudo)"
        log_info "Suggested cron entry:"
        echo "  $CRON_ENTRY"
        return 1
    }
    
    log_success "Automated backup scheduled for daily at 2:00 AM"
    log_info "To view schedule: crontab -l"
    log_info "To remove schedule: crontab -e (and delete the line)"
    
    return 0
}

# ============================================
# VERIFY BACKUP FUNCTION
# ============================================

verify_backup() {
    BACKUP_NAME=$1
    
    if [ -z "$BACKUP_NAME" ]; then
        log_error "Please specify backup name to verify"
        list_backups
        return 1
    fi
    
    BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"
    
    if [ ! -d "$BACKUP_PATH" ]; then
        log_error "Backup not found: $BACKUP_PATH"
        return 1
    fi
    
    log_info "Verifying backup: $BACKUP_NAME"
    
    # Check components
    VALID=true
    
    if [ -d "$BACKUP_PATH/mongodb" ]; then
        log_success "MongoDB data found"
    else
        log_warning "MongoDB data not found"
    fi
    
    if [ -f "$BACKUP_PATH/.env.backup" ]; then
        log_success "Configuration backup found"
    fi
    
    if [ -f "$BACKUP_PATH/logs.tar.gz" ]; then
        log_success "Logs backup found"
    fi
    
    # Check integrity
    log_info "Checking archive integrity..."
    for archive in "$BACKUP_PATH"/*.tar.gz; do
        if [ -f "$archive" ]; then
            if tar -tzf "$archive" > /dev/null 2>&1; then
                log_success "Archive valid: $(basename "$archive")"
            else
                log_error "Archive corrupted: $(basename "$archive")"
                VALID=false
            fi
        fi
    done
    
    # Display backup info
    if [ -f "$BACKUP_PATH/backup_info.txt" ]; then
        echo ""
        cat "$BACKUP_PATH/backup_info.txt"
    fi
    
    if [ "$VALID" = true ]; then
        log_success "Backup verification passed"
        return 0
    else
        log_error "Backup verification failed"
        return 1
    fi
}

# ============================================
# MAIN
# ============================================

COMMAND=${1:-list}

case "$COMMAND" in
    backup)
        backup
        ;;
    restore)
        restore "$2"
        ;;
    cleanup)
        cleanup
        ;;
    schedule)
        schedule
        ;;
    list)
        list_backups
        ;;
    verify)
        verify_backup "$2"
        ;;
    *)
        cat << EOF
Telegram Bot - Backup Management Script

Usage: ./scripts/backup.sh [command] [options]

Commands:
  backup                 Create a new backup
  restore [name]        Restore from a backup
  cleanup               Remove old backups (older than $RETENTION_DAYS days)
  schedule              Set up automated daily backups (requires cron)
  list                  List all available backups (default)
  verify [name]         Verify backup integrity

Examples:
  ./scripts/backup.sh backup                          # Create backup now
  ./scripts/backup.sh list                            # List all backups
  ./scripts/backup.sh restore telegram_bot_20240115_100000  # Restore specific backup
  ./scripts/backup.sh schedule                        # Set up daily backups at 2 AM
  ./scripts/backup.sh verify telegram_bot_20240115_100000   # Verify backup

Environment Variables:
  BACKUP_RETENTION_DAYS   Days to keep backups (default: $RETENTION_DAYS)

For more help, see DEPLOYMENT_GUIDE.md
EOF
        ;;
esac
