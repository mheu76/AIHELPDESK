# Deployment Scripts

Utility scripts for managing IT AI Helpdesk deployment.

## Available Scripts

### Health Check

Verifies all services are running correctly.

**Linux/Mac:**
```bash
./health-check.sh
```

**Windows:**
```cmd
health-check.bat
```

### Database Backup

Creates a timestamped backup of the PostgreSQL database.

**Linux/Mac:**
```bash
./backup-db.sh
```

**Windows:**
```cmd
backup-db.bat
```

Backups are stored in `backups/` directory with format: `helpdesk_backup_YYYYMMDD_HHMMSS.sql`

**Environment Variables (Linux/Mac):**
- `BACKUP_DIR`: Backup directory (default: `./backups`)
- `DB_CONTAINER`: Container name (default: `aihelpdesk-db`)
- `DB_NAME`: Database name (default: `helpdesk`)
- `DB_USER`: Database user (default: `helpdesk`)
- `RETENTION_DAYS`: Keep backups for N days (default: `7`)

### Database Restore

Restores database from a backup file.

**Linux/Mac:**
```bash
./restore-db.sh backups/helpdesk_backup_20260406_120000.sql.gz
```

**Windows:**
```cmd
# Manual restore (Windows)
# 1. Extract the backup file
# 2. Run:
docker exec -i aihelpdesk-db psql -U helpdesk helpdesk < backups\helpdesk_backup_20260406.sql
```

⚠️ **WARNING**: This will overwrite the current database!

### Production Deployment (Linux/Mac only)

Deploys to production with database backup, migration, and health check.

```bash
./deploy-prod.sh
```

**Prerequisites:**
- `backend/.env.production` must exist
- Docker Compose production config (`docker-compose.prod.yml`)

## Setup Instructions

### Linux/Mac

Make scripts executable:
```bash
chmod +x scripts/*.sh
```

### Windows

No setup required for `.bat` files. Just run them directly from Command Prompt.

For `.sh` files on Windows, use Git Bash or WSL:
```bash
# Git Bash
bash scripts/health-check.sh

# WSL
wsl bash scripts/health-check.sh
```

## Scheduled Backups

### Linux/Mac (cron)

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /path/to/AIhelpdesk/scripts/backup-db.sh
```

### Windows (Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (daily at 2:00 AM)
4. Action: Start a program
5. Program: `cmd.exe`
6. Arguments: `/c "C:\path\to\AIhelpdesk\scripts\backup-db.bat"`

## Monitoring

For production monitoring, integrate with:
- **Prometheus + Grafana**: Metrics and dashboards
- **Uptime Kuma**: Health check monitoring
- **Sentry**: Error tracking
- **CloudWatch / Azure Monitor**: Cloud platform monitoring

## Troubleshooting

### Script permission denied (Linux/Mac)
```bash
chmod +x scripts/*.sh
```

### Docker command not found
Ensure Docker is installed and running:
```bash
docker --version
docker compose version
```

### Container not found
Check container name:
```bash
docker ps -a
```

Update `CONTAINER_NAME` if different.

### Backup fails
Check disk space:
```bash
df -h
```

Check database connection:
```bash
docker exec aihelpdesk-db pg_isready -U helpdesk
```
