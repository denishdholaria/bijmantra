# 💾 Backup & Restore Runbook

> **Purpose:** Database backup and recovery procedures  
> **Last Updated:** December 26, 2025  
> **Priority:** 🔴 Critical

---

## Prerequisites

- SSH access to production server
- Database credentials
- S3/MinIO access for backup storage
- Sufficient disk space for backup

---

## Backup Procedures

### Manual Full Backup

**When to use:** Before major changes, migrations, or on-demand

```bash
# 1. SSH to production server
ssh user@production-server

# 2. Navigate to project directory
cd /opt/bijmantra

# 3. Create backup with timestamp
BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql.gz"

docker-compose -f compose.prod.yaml exec -T postgres \
  pg_dump -U bijmantra_prod bijmantra_production | gzip > $BACKUP_FILE

# 4. Verify backup was created
ls -lh $BACKUP_FILE

# 5. Upload to remote storage
aws s3 cp $BACKUP_FILE s3://bijmantra-backups/daily/
# Or for MinIO:
# mc cp $BACKUP_FILE minio/bijmantra-backups/daily/

# 6. Verify upload
aws s3 ls s3://bijmantra-backups/daily/$BACKUP_FILE
```

### Automated Daily Backup

**Setup:** Add to crontab

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /opt/bijmantra/scripts/backup.sh >> /var/log/bijmantra-backup.log 2>&1
```

**Backup script** (`/opt/bijmantra/scripts/backup.sh`):

```bash
#!/bin/bash
set -e

# Configuration
BACKUP_DIR="/opt/bijmantra/backups"
S3_BUCKET="s3://bijmantra-backups"
RETENTION_DAYS=30

# Create backup
BACKUP_FILE="$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql.gz"
cd /opt/bijmantra
docker-compose -f compose.prod.yaml exec -T postgres \
  pg_dump -U bijmantra_prod bijmantra_production | gzip > $BACKUP_FILE

# Upload to S3
aws s3 cp $BACKUP_FILE $S3_BUCKET/daily/

# Clean up old local backups
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete

# Clean up old S3 backups
aws s3 ls $S3_BUCKET/daily/ | while read -r line; do
  createDate=$(echo $line | awk '{print $1" "$2}')
  createDate=$(date -d "$createDate" +%s)
  olderThan=$(date -d "-$RETENTION_DAYS days" +%s)
  if [[ $createDate -lt $olderThan ]]; then
    fileName=$(echo $line | awk '{print $4}')
    aws s3 rm $S3_BUCKET/daily/$fileName
  fi
done

echo "Backup completed: $BACKUP_FILE"
```

### Verification

```bash
# Check backup file is valid
gunzip -t $BACKUP_FILE && echo "Backup is valid"

# Check backup size (should be > 0)
ls -lh $BACKUP_FILE

# List tables in backup (sample check)
gunzip -c $BACKUP_FILE | head -100 | grep "CREATE TABLE"
```

---

## Restore Procedures

### ⚠️ WARNING

Restoring a backup will **OVERWRITE** all existing data. Always:
1. Confirm you have the correct backup
2. Test on staging first if possible
3. Notify users of downtime

### Restore to Production

```bash
# 1. SSH to production server
ssh user@production-server
cd /opt/bijmantra

# 2. Download backup if needed
aws s3 cp s3://bijmantra-backups/daily/backup_20251226_020000.sql.gz .

# 3. Stop the application (prevent writes)
docker-compose -f compose.prod.yaml stop backend

# 4. Restore the database
gunzip -c backup_20251226_020000.sql.gz | \
  docker-compose -f compose.prod.yaml exec -T postgres \
  psql -U bijmantra_prod bijmantra_production

# 5. Restart the application
docker-compose -f compose.prod.yaml start backend

# 6. Verify restoration
docker-compose -f compose.prod.yaml exec postgres \
  psql -U bijmantra_prod bijmantra_production -c "SELECT count(*) FROM users;"
```

### Restore to Staging (Recommended First)

```bash
# 1. SSH to staging server
ssh user@staging-server
cd /opt/bijmantra-staging

# 2. Download backup
aws s3 cp s3://bijmantra-backups/daily/backup_20251226_020000.sql.gz .

# 3. Restore to staging database
gunzip -c backup_20251226_020000.sql.gz | \
  docker-compose -f compose.staging.yaml exec -T postgres \
  psql -U bijmantra_staging bijmantra_staging

# 4. Test the application
curl https://staging.bijmantra.org/health

# 5. Verify data
# Login and check data is correct
```

### Point-in-Time Recovery (If WAL Archiving Enabled)

```bash
# Restore to specific timestamp
pg_restore \
  --target-time="2025-12-26 14:30:00" \
  --target-action=promote \
  /path/to/base/backup
```

---

## Rollback Procedure

If restore causes issues:

```bash
# 1. Stop application
docker-compose -f compose.prod.yaml stop backend

# 2. Restore previous backup
gunzip -c backup_previous.sql.gz | \
  docker-compose -f compose.prod.yaml exec -T postgres \
  psql -U bijmantra_prod bijmantra_production

# 3. Restart application
docker-compose -f compose.prod.yaml start backend

# 4. Verify
curl https://bijmantra.org/health
```

---

## Troubleshooting

### Backup Fails

| Issue | Solution |
|-------|----------|
| "No space left on device" | Clean up old backups, expand disk |
| "Connection refused" | Check PostgreSQL is running |
| "Permission denied" | Check user has backup privileges |
| S3 upload fails | Check AWS credentials, bucket policy |

### Restore Fails

| Issue | Solution |
|-------|----------|
| "Database does not exist" | Create database first |
| "Role does not exist" | Create role first |
| "Relation already exists" | Drop database and recreate |
| Corrupted backup | Try different backup file |

### Create Database/Role If Missing

```sql
-- Connect as postgres superuser
CREATE ROLE bijmantra_prod WITH LOGIN PASSWORD 'password';
CREATE DATABASE bijmantra_production OWNER bijmantra_prod;
GRANT ALL PRIVILEGES ON DATABASE bijmantra_production TO bijmantra_prod;
```

---

## Backup Verification Checklist

- [ ] Backup file exists and has reasonable size
- [ ] Backup file is not corrupted (`gunzip -t`)
- [ ] Backup contains expected tables
- [ ] Backup uploaded to remote storage
- [ ] Old backups cleaned up per retention policy
- [ ] Restore tested on staging (monthly)

---

*Test your backups regularly. An untested backup is not a backup.*
