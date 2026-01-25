# Disaster Recovery Scripts

Production-ready tools for backup, restore, and disaster recovery operations.

---

## 📁 Scripts Overview

| Script | Purpose | Usage |
|--------|---------|-------|
| `backup.py` | Create database and config backups | `python backup.py` |
| `restore.py` | Restore database from backup | `python restore.py --list` |
| `verify.py` | Verify database integrity | `python verify.py` |

---

## 🚀 Quick Start

### Prerequisites

```bash
# Install dependencies
pip install boto3 asyncpg

# Install PostgreSQL client tools
# Ubuntu/Debian:
sudo apt-get install postgresql-client

# macOS:
brew install postgresql

# Configure environment
export DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/dbname"
export BACKUP_S3_BUCKET="riskcast-backups"
export AWS_REGION="us-east-1"
export BACKUP_RETENTION_DAYS="30"
export BACKUP_KMS_KEY_ID="arn:aws:kms:us-east-1:ACCOUNT_ID:key/KEY_ID"  # Optional
```

### Create Backup

```bash
# Automatic backup (full on Monday, incremental other days)
python backup.py

# Force full backup
python backup.py --type full

# Incremental backup
python backup.py --type incremental

# Skip verification (faster, not recommended)
python backup.py --no-verify

# Skip cleanup
python backup.py --no-cleanup
```

### List Backups

```bash
# List available backups
python restore.py --list

# Output:
# Available Backups:
# ────────────────────────────────────────────────────────────────────────────
# #    Created At           Type         Size        Tables   S3 Key
# ────────────────────────────────────────────────────────────────────────────
# 1    2024-01-15T03:00:00  full         450.2 MB    45       database/full/...
# 2    2024-01-14T03:00:00  incremental  120.5 MB    10       database/incr/...
```

### Restore Database

```bash
# Interactive restore (choose from list)
python restore.py

# Restore specific backup
python restore.py --backup-key database/full/20240115_030000/backup.dump

# Restore to different database
python restore.py \
  --backup-key database/full/20240115_030000/backup.dump \
  --target-db riskcast_restored

# Drop and recreate database before restore
python restore.py \
  --backup-key database/full/20240115_030000/backup.dump \
  --drop-existing \
  --yes

# Parallel restore (faster)
python restore.py \
  --backup-key database/full/20240115_030000/backup.dump \
  --parallel-jobs 8
```

### Verify Database

```bash
# Run full verification
python verify.py

# Verify specific database
export DATABASE_URL="postgresql://..."
python verify.py
```

---

## 📊 Features

### backup.py

**Features:**
- ✅ Full and incremental backups
- ✅ PostgreSQL pg_dump (custom format)
- ✅ Maximum compression (-Z 9)
- ✅ Configuration backup (tar.gz)
- ✅ S3 upload with encryption
- ✅ KMS encryption support
- ✅ Automatic verification
- ✅ SHA-256 checksum
- ✅ Metadata tracking
- ✅ Retention management
- ✅ Automatic cleanup

**Backup Types:**
- **Full:** Complete database dump (all tables)
- **Incremental:** Important tables only (lighter, faster)
- **Auto:** Full on Monday, incremental other days

**Storage:**
- S3 with server-side encryption (AES-256 or KMS)
- Standard-IA storage class (cost-effective)
- Retention: 30 days (configurable)

### restore.py

**Features:**
- ✅ List available backups
- ✅ Download from S3
- ✅ Interactive or scripted restore
- ✅ Target database selection
- ✅ Drop/recreate database option
- ✅ Parallel restore (4-8 jobs)
- ✅ Automatic verification
- ✅ Progress reporting
- ✅ Error handling

**Safety:**
- Confirmation prompts (unless --yes)
- Backup listing before restore
- Verification after restore
- Error recovery

### verify.py

**Features:**
- ✅ Connection test
- ✅ Table structure verification
- ✅ Row count checks
- ✅ Index verification
- ✅ Constraint verification
- ✅ Sequence verification
- ✅ Data integrity checks
- ✅ Comprehensive reporting

**Checks:**
- Database connectivity
- PostgreSQL version
- Database size
- Table counts
- Orphaned records detection
- Duplicate primary keys
- Constraint integrity

---

## 🔧 Configuration

### Environment Variables

```bash
# Required
DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/dbname"
BACKUP_S3_BUCKET="riskcast-backups"

# Optional
AWS_REGION="us-east-1"                                              # Default: us-east-1
BACKUP_RETENTION_DAYS="30"                                          # Default: 30
BACKUP_KMS_KEY_ID="arn:aws:kms:us-east-1:ACCOUNT_ID:key/KEY_ID"   # Optional KMS
```

### AWS IAM Permissions

Required permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:ListBucket",
        "s3:DeleteObject"
      ],
      "Resource": [
        "arn:aws:s3:::riskcast-backups",
        "arn:aws:s3:::riskcast-backups/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "kms:Encrypt",
        "kms:Decrypt",
        "kms:GenerateDataKey"
      ],
      "Resource": "arn:aws:kms:us-east-1:ACCOUNT_ID:key/KEY_ID"
    }
  ]
}
```

---

## 📋 Common Workflows

### Daily Operations

```bash
# 1. Run scheduled backup (via cron or K8s CronJob)
0 3 * * * /usr/bin/python3 /path/to/backup.py >> /var/log/backups.log 2>&1

# 2. Verify latest backup
python restore.py --list | head -n 5

# 3. Check backup age
aws s3 ls s3://riskcast-backups/database/full/ --recursive | tail -n 10
```

### Disaster Recovery Test

```bash
# 1. Create test database
createdb riskcast_dr_test

# 2. List available backups
python restore.py --list

# 3. Restore to test database
python restore.py \
  --backup-key database/full/20240115_030000/backup.dump \
  --target-db riskcast_dr_test \
  --yes

# 4. Verify restoration
export DATABASE_URL="postgresql://...riskcast_dr_test"
python verify.py

# 5. Run application tests
pytest tests/integration/ -v

# 6. Cleanup
dropdb riskcast_dr_test
```

### Emergency Restore

```bash
# 1. STOP APPLICATION (prevent further damage)
kubectl scale deployment riskcast-api --replicas=0

# 2. Create emergency backup of current state
python backup.py --type full --no-cleanup

# 3. List backups and select restore point
python restore.py --list

# 4. Restore (DESTRUCTIVE - will drop current database)
python restore.py \
  --backup-key database/full/20240115_030000/backup.dump \
  --drop-existing \
  --yes

# 5. Run migrations (in case schema changed)
alembic upgrade head

# 6. Verify database
python verify.py

# 7. RESTART APPLICATION
kubectl scale deployment riskcast-api --replicas=3

# 8. Monitor
kubectl logs -f deployment/riskcast-api
./scripts/smoke-test.sh https://api.riskcast.io
```

---

## 🐛 Troubleshooting

### "pg_dump not found"

```bash
# Install PostgreSQL client tools
# Ubuntu/Debian:
sudo apt-get install postgresql-client

# macOS:
brew install postgresql

# Verify installation
pg_dump --version
pg_restore --version
```

### "boto3 not installed"

```bash
pip install boto3
```

### "Connection refused"

```bash
# Check database is accessible
psql $DATABASE_URL -c "SELECT 1"

# Check network/firewall rules
# Check security groups (AWS)
# Check database is running
```

### "Permission denied (S3)"

```bash
# Check AWS credentials
aws sts get-caller-identity

# Check bucket exists
aws s3 ls s3://riskcast-backups/

# Check IAM permissions
aws iam simulate-principal-policy \
  --policy-source-arn <role-arn> \
  --action-names s3:PutObject s3:GetObject
```

### "Backup verification failed"

```bash
# Try pg_restore manually
pg_restore -l backup.dump

# If file is corrupted, use previous backup
python restore.py --list

# Check S3 object integrity
aws s3api head-object \
  --bucket riskcast-backups \
  --key database/full/20240115_030000/backup.dump
```

### "Restore warnings/errors"

```bash
# pg_restore often shows warnings that can be ignored:
# - "role xyz does not exist" (use --no-owner)
# - "already exists" (normal for some objects)

# If restore completes but shows errors:
# 1. Check if tables were created
psql $DATABASE_URL -c "\dt"

# 2. Check record counts
psql $DATABASE_URL -c "SELECT COUNT(*) FROM quotes;"

# 3. Run verification
python verify.py
```

---

## 🔒 Security Best Practices

### 1. Encryption

```bash
# Always use KMS encryption for sensitive backups
export BACKUP_KMS_KEY_ID="arn:aws:kms:us-east-1:ACCOUNT_ID:key/KEY_ID"

# Verify encryption
aws s3api head-object \
  --bucket riskcast-backups \
  --key database/full/20240115_030000/backup.dump \
  --query ServerSideEncryption
```

### 2. Access Control

```bash
# Use IAM roles, not access keys
# Rotate credentials regularly
# Use bucket policies to restrict access

# Example bucket policy:
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "AWS": "arn:aws:iam::ACCOUNT_ID:role/backup-role"
    },
    "Action": ["s3:PutObject", "s3:GetObject"],
    "Resource": "arn:aws:s3:::riskcast-backups/*"
  }]
}
```

### 3. Audit Logging

```bash
# Enable S3 access logging
aws s3api put-bucket-logging \
  --bucket riskcast-backups \
  --bucket-logging-status file://logging-config.json

# Enable CloudTrail for S3 operations
```

### 4. Testing

```bash
# Test backups weekly
# Restore to test environment
# Verify data integrity
# Document results
```

---

## 📊 Monitoring

### Backup Monitoring

```bash
# Check backup age
aws s3 ls s3://riskcast-backups/database/full/ \
  --recursive --human-readable | tail -n 5

# Get backup metrics
aws cloudwatch get-metric-statistics \
  --namespace Custom/Backups \
  --metric-name BackupSize \
  --start-time $(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Average
```

### Alerts

Set up CloudWatch alarms:
- Backup age > 24 hours
- Backup size anomalies
- Backup failures
- S3 access errors

---

## 📚 Additional Resources

- **[Disaster Recovery Runbook](../../docs/runbooks/disaster-recovery.md)** - DR procedures
- **[Database Migration Guide](../../docs/migrations/MIGRATION_GUIDE.md)** - Schema changes
- **[Secrets Management](../secrets/README.md)** - Credential rotation

---

**Version:** 1.0.0  
**Last Updated:** January 24, 2026
