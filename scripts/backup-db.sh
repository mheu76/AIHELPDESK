#!/bin/bash
# Database backup script for IT AI Helpdesk

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/helpdesk_backup_$TIMESTAMP.sql"
CONTAINER_NAME="${DB_CONTAINER:-aihelpdesk-db}"
DB_NAME="${DB_NAME:-helpdesk}"
DB_USER="${DB_USER:-helpdesk}"

# Retention (days)
RETENTION_DAYS="${RETENTION_DAYS:-7}"

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo "Starting database backup..."
echo "Container: $CONTAINER_NAME"
echo "Database: $DB_NAME"
echo "Backup file: $BACKUP_FILE"

# Create backup
docker exec "$CONTAINER_NAME" pg_dump -U "$DB_USER" "$DB_NAME" > "$BACKUP_FILE"

# Compress backup
gzip "$BACKUP_FILE"
echo "Backup compressed: ${BACKUP_FILE}.gz"

# Remove old backups
echo "Removing backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "helpdesk_backup_*.sql.gz" -mtime +"$RETENTION_DAYS" -delete

echo "Backup completed successfully!"
echo "File: ${BACKUP_FILE}.gz"
echo "Size: $(du -h ${BACKUP_FILE}.gz | cut -f1)"
