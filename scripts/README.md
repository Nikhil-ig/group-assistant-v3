# Telegram Bot - Scripts Directory

This directory contains all deployment, monitoring, and maintenance scripts for the Telegram bot.

## Overview

```
scripts/
├── deploy.sh                    # Main deployment script
├── rollback.sh                  # Rollback to previous version
├── monitor.sh                   # Real-time monitoring and health checks
├── backup.sh                    # Database and application backup management
├── validate-deployment.sh       # Post-deployment validation checks
└── README.md                    # This file
```

## Quick Start

### First Time Setup

```bash
# Make scripts executable
chmod +x scripts/*.sh

# Create backup directory
mkdir -p backups

# Create logs directory
mkdir -p logs
```

### Deploy to Production

```bash
# Deploy current version
./scripts/deploy.sh

# Deploy to staging
./scripts/deploy.sh staging
```

### Monitor System

```bash
# Real-time monitoring
./scripts/monitor.sh

# Post-deployment validation
./scripts/validate-deployment.sh
```

### Backup & Recovery

```bash
# Create backup
./scripts/backup.sh backup

# List backups
./scripts/backup.sh list

# Restore from backup
./scripts/backup.sh restore telegram_bot_20240115_100000

# Set up automatic daily backups
./scripts/backup.sh schedule

# Clean old backups
./scripts/backup.sh cleanup
```

---

## Detailed Script Documentation

### 1. deploy.sh - Deployment Script

**Purpose**: Automates deployment of the bot to production

**Features**:
- Pre-flight validation checks
- Docker image building
- Service orchestration
- Health check verification
- Automatic cleanup
- Error handling with detailed logging

**Usage**:
```bash
./scripts/deploy.sh [environment]
```

**Arguments**:
- `environment` (optional): `production`, `staging`, `development` (default: `production`)

**What it does**:
1. ✅ Validates Docker and docker-compose installation
2. ✅ Checks .env file exists
3. ✅ Builds Docker image
4. ✅ Stops old containers
5. ✅ Starts new containers with docker-compose
6. ✅ Waits for services to be healthy (max 30 attempts)
7. ✅ Runs database migrations
8. ✅ Cleans up old Docker images
9. ✅ Reports success/failure

**Example output**:
```
ℹ️  Checking Docker installation...
✅ Docker is installed: 20.10.0
✅ docker-compose is installed: 2.0.0
ℹ️  Checking .env file...
✅ .env file exists
...
✅ Deployment completed successfully! 🎉
```

**When to use**:
- Deploying new version to production
- Initial server setup
- CI/CD pipeline automation

---

### 2. rollback.sh - Rollback Script

**Purpose**: Quickly revert to previous application version

**Features**:
- Backs up current state before rollback
- Git version checkout
- Service restart
- Health verification
- Database backup preservation

**Usage**:
```bash
./scripts/rollback.sh [version]
```

**Arguments**:
- `version` (optional): Git tag, branch, or commit hash (default: `latest`)

**What it does**:
1. ✅ Backs up current database
2. ✅ Backs up current logs
3. ✅ Stops all services
4. ✅ Checks out specified Git version
5. ✅ Pulls latest code
6. ✅ Restarts services
7. ✅ Verifies application health
8. ✅ Preserves backup for recovery

**Example usage**:
```bash
# Rollback to latest stable version
./scripts/rollback.sh

# Rollback to specific tag
./scripts/rollback.sh v1.2.0

# Rollback to specific commit
./scripts/rollback.sh abc123def456
```

**When to use**:
- Critical bug in production
- Deployment failure
- Need to go back to known good version

---

### 3. monitor.sh - Monitoring Script

**Purpose**: Real-time system health and performance monitoring

**Features**:
- Service status overview
- Container statistics (CPU, memory)
- API health checks
- Database connectivity validation
- Inter-service communication verification
- Resource usage analysis
- Log analysis for errors

**Usage**:
```bash
./scripts/monitor.sh
```

**What it checks**:
1. **Service Status**
   - Running container count
   - Service health
   - Individual service status

2. **Container Statistics**
   - CPU usage
   - Memory usage
   - Real-time stats

3. **Health Checks**
   - API /health endpoint
   - MongoDB connectivity
   - Service availability

4. **API Endpoints**
   - GET /health
   - GET /docs
   - GET /api/v1/users

5. **Database**
   - MongoDB collections count
   - Document counts per collection
   - Connection status

6. **Network**
   - Inter-service connectivity
   - MongoDB access from bot
   - Port accessibility

7. **Logs**
   - Recent errors
   - Application status
   - Service messages

8. **Performance**
   - Disk usage
   - Docker volumes
   - Available space

**Example output**:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        SERVICE STATUS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Services running: 3/3
...
✅ API is healthy
✅ MongoDB is healthy
✅ All services running
```

**When to use**:
- Regular health checks
- Troubleshooting performance issues
- Monitoring during heavy usage
- Alert verification

**Run regularly**:
```bash
# Watch continuously
watch -n 5 ./scripts/monitor.sh

# Or add to cron for periodic checks
*/5 * * * * cd /path/to/v3 && ./scripts/monitor.sh >> logs/monitor.log 2>&1
```

---

### 4. backup.sh - Backup Management Script

**Purpose**: Automated database and application backup management

**Features**:
- Full MongoDB database dumps
- Application source code backup
- Configuration backup (secrets redacted)
- Log file backup
- Automatic retention policy
- Backup verification
- Restore capabilities
- Cron scheduling support

**Usage**:
```bash
./scripts/backup.sh [command] [options]
```

**Commands**:

#### backup - Create new backup
```bash
./scripts/backup.sh backup
```
Creates a new backup with:
- MongoDB database dump
- Application source code
- Configuration (secrets redacted)
- Log files
- Backup info file

Creates in: `backups/telegram_bot_YYYYMMDD_HHMMSS/`

#### list - List available backups
```bash
./scripts/backup.sh list
```
Shows:
- Backup names
- File sizes
- Creation dates
- Quick info

#### restore - Restore from backup
```bash
./scripts/backup.sh restore telegram_bot_20240115_100000
```
Restores:
- Database
- Application files
- Configuration info
- Logs (if available)

**⚠️ Warning**: Overwrites current data! Requires confirmation.

#### verify - Verify backup integrity
```bash
./scripts/backup.sh verify telegram_bot_20240115_100000
```
Checks:
- Archive integrity
- Component presence
- File validity

#### cleanup - Remove old backups
```bash
./scripts/backup.sh cleanup
```
Removes backups older than `BACKUP_RETENTION_DAYS` (default: 30 days)

#### schedule - Set up automated backups
```bash
./scripts/backup.sh schedule
```
Creates daily backup cron job at 2:00 AM

**Environment Variables**:
```bash
BACKUP_RETENTION_DAYS=30    # Keep backups for 30 days
```

**Backup Structure**:
```
backups/
└── telegram_bot_20240115_100000/
    ├── mongodb/                 # MongoDB database dump
    ├── api.tar.gz              # API module backup
    ├── bot.tar.gz              # Bot module backup
    ├── logs.tar.gz             # Application logs
    ├── .env.backup             # Configuration (redacted)
    └── backup_info.txt         # Backup metadata
```

**Backup Schedule Example**:
```bash
# Set up daily backups at 2 AM
./scripts/backup.sh schedule

# Verify it's scheduled
crontab -l

# Remove schedule
crontab -e  # Remove the line

# Manually trigger cleanup weekly
0 3 0 * * cd /path/to/v3 && ./scripts/backup.sh cleanup
```

**When to use**:
- Daily automated backups (via cron)
- Before major updates
- Before experiments
- Disaster recovery
- Compliance requirements

**Retention Strategy**:
- Keep daily backups for 30 days
- Older backups cleaned up automatically
- Critical backups can be moved elsewhere manually

---

### 5. validate-deployment.sh - Post-Deployment Validation

**Purpose**: Comprehensive health and functionality checks after deployment

**Features**:
- 14 different validation categories
- Detailed pass/fail/warning reporting
- Color-coded output
- Summary statistics
- No external dependencies

**Usage**:
```bash
./scripts/validate-deployment.sh
```

**Validation Checks**:

1. **Container Health** (2 checks)
   - All containers running
   - Specific service status

2. **Port Connectivity** (3 checks)
   - API port 8000
   - MongoDB port 27017
   - Nginx port 80

3. **API Health Endpoints** (2 checks)
   - /health endpoint status
   - /docs (Swagger) availability

4. **Database Connectivity** (3 checks)
   - MongoDB ping response
   - telegram_bot database existence
   - Collections present

5. **Environment Configuration** (4 checks)
   - .env file exists
   - Critical variables set
   - Values not using defaults
   - Full configuration validation

6. **Directory Structure** (2 checks)
   - Required directories present
   - Required files exist

7. **Logs & Permissions** (3 checks)
   - logs directory exists
   - Log files being created
   - Directory is writable

8. **Docker Images** (2 checks)
   - telegram-bot image exists
   - Image size info

9. **Network Connectivity** (1 check)
   - Bot can reach MongoDB
   - Service communication works

10. **Resource Usage** (3 checks)
    - Memory usage
    - Disk usage
    - Available space

11. **Backup Status** (3 checks)
    - Backup directory exists
    - Backups found
    - Latest backup age

12. **Service Logs Analysis** (3 checks)
    - Error count per service
    - Log analysis

13. **Security Checks** (3 checks)
    - No exposed secrets
    - .gitignore configuration
    - JWT secret strength

14. **Feature Validation** (3+ checks)
    - API endpoints responding
    - Health checks passing
    - Services functional

**Output Example**:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        1️⃣  CONTAINER HEALTH CHECKS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ All containers running (3/3)
✅ mongodb container is running
✅ telegram-bot container is running
...

VALIDATION SUMMARY
==================
Passed: 42 | Failed: 0 | Warnings: 2
✅ Deployment validation successful!
```

**When to use**:
- After every deployment
- Before going live
- Troubleshooting issues
- Verification checklist
- Post-recovery validation

---

## Script Dependencies

### Required Tools
- `bash` (4.0+)
- `docker` (20.10+)
- `docker-compose` (2.0+)
- `curl` (for health checks)
- Standard Unix utilities: `grep`, `sed`, `awk`, `find`

### Optional Tools
- `cron` (for backup scheduling)
- `git` (for rollback)
- `bc` (for time calculations)

### Verify Installation
```bash
docker --version
docker-compose --version
curl --version
git --version
which bash sed awk grep
```

---

## Error Handling

All scripts include:
- ✅ Error detection with `set -e`
- ✅ Trap handlers for cleanup
- ✅ Detailed error messages
- ✅ Exit codes (0 = success, 1 = failure)
- ✅ Recovery suggestions

Example error output:
```
❌ Docker is not installed
Error: Please install Docker first: https://docs.docker.com/get-docker/
```

---

## Logs & Output

### Log Files
- `logs/bot.log` - Application logs
- `logs/api.log` - API server logs
- `logs/backup.log` - Backup operation logs (if scheduled)
- `logs/deploy.log` - Deployment logs

### View Logs
```bash
# Real-time logs
docker-compose logs -f telegram-bot

# Last 100 lines
docker-compose logs --tail 100 telegram-bot

# Specific service
docker-compose logs mongodb

# With timestamps
docker-compose logs --timestamps telegram-bot
```

---

## Best Practices

1. **Deployment**
   - ✅ Always validate after deploy: `./scripts/validate-deployment.sh`
   - ✅ Monitor for errors: `./scripts/monitor.sh`
   - ✅ Have rollback ready: `./scripts/rollback.sh`

2. **Backups**
   - ✅ Set up daily automated backups: `./scripts/backup.sh schedule`
   - ✅ Verify backups monthly: `./scripts/backup.sh verify [name]`
   - ✅ Test restore procedures quarterly
   - ✅ Keep off-site copies of critical backups

3. **Monitoring**
   - ✅ Monitor continuously during peak usage
   - ✅ Check logs daily for errors
   - ✅ Alert on critical failures
   - ✅ Track performance trends

4. **Maintenance**
   - ✅ Schedule deployments during low-usage windows
   - ✅ Always have rollback plan
   - ✅ Document any customizations
   - ✅ Keep Docker images updated

---

## Troubleshooting

### Script won't execute
```bash
# Make scripts executable
chmod +x scripts/*.sh

# Verify permissions
ls -la scripts/
```

### Docker permission denied
```bash
# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

### MongoDB connection fails
```bash
# Check MongoDB container
docker-compose logs mongodb

# Verify network
docker-compose exec telegram-bot ping mongodb

# Check credentials in .env
grep MONGODB backups/.env
```

### Backup fails
```bash
# Check free space
df -h

# Verify MongoDB is running
docker-compose ps mongodb

# Check backup directory permissions
ls -la backups/
```

---

## Support

For issues or questions:
1. Check `DEPLOYMENT_GUIDE.md` for detailed deployment info
2. Review script comments for code details
3. Check application logs: `docker-compose logs`
4. Run validation: `./scripts/validate-deployment.sh`

---

## Version History

- **v1.0** (2024-01-15) - Initial release with 5 core scripts
  - deploy.sh - Deployment automation
  - rollback.sh - Version rollback
  - monitor.sh - Health monitoring
  - backup.sh - Backup management
  - validate-deployment.sh - Post-deployment validation

---

## License

Part of Telegram Bot project
