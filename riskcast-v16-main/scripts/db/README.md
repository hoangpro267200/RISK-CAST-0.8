# Database Migration Scripts

Production-ready tools for zero-downtime database migrations.

---

## 📁 Scripts Overview

| Script | Purpose | Usage |
|--------|---------|-------|
| `migrate.py` | Run migrations safely | `python migrate.py` |
| `rollback.py` | Rollback migrations | `python rollback.py --target abc123` |
| `create_migration.py` | Create new migration | `python create_migration.py "message"` |
| `check_migrations.py` | Check status | `python check_migrations.py` |
| `backup.py` | Create backup | `python backup.py` |

---

## 🚀 Quick Start

### Check Status

```bash
python check_migrations.py
```

Output:
```
============================================================
Migration Status Check
============================================================

Current revision: abc123def456
Head revision:    abc123def456

✓ Database is up to date
```

### Create Migration

```bash
# Auto-generate from model changes
python create_migration.py "add user status column"

# Create empty migration
python create_migration.py "custom migration" --no-autogenerate
```

### Run Migrations

```bash
# Dry run (safe, shows what would happen)
python migrate.py --dry-run

# Run with all safety features
python migrate.py

# Skip backup (not recommended)
python migrate.py --skip-backup
```

### Rollback

```bash
# Show history
python rollback.py --history

# Rollback to specific revision
python rollback.py --target abc123def456

# Skip confirmation
python rollback.py --target abc123def456 --yes
```

### Backup

```bash
# Create backup with upload to S3
python backup.py

# Custom name
python backup.py --name pre_major_migration

# Local only (no S3)
python backup.py --no-upload
```

---

## ⚙️ Configuration

### Environment Variables

```bash
# Required
export DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/db"

# Optional
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
export BACKUP_S3_BUCKET="riskcast-backups"
export ENVIRONMENT="production"
```

### AWS Credentials (for backups)

```bash
export AWS_ACCESS_KEY_ID="your-key-id"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"
```

---

## 🔒 Safety Features

### migrate.py

1. **Pre-flight Checks**
   - Database connection
   - Pending migrations
   - Active connections
   - Long-running queries

2. **Locking**
   - PostgreSQL advisory locks
   - Prevents concurrent migrations
   - Auto-timeout (5 minutes)

3. **Backup**
   - Automatic pg_dump
   - S3 upload
   - Restore capability

4. **Notifications**
   - Slack webhook integration
   - Success/failure alerts

### rollback.py

1. **Safety**
   - Shows what will be rolled back
   - Requires confirmation
   - Displays revision history

2. **Verification**
   - Checks current state
   - Validates target
   - Confirms result

---

## 📊 Common Workflows

### Development

```bash
# 1. Create migration
python create_migration.py "add user email"

# 2. Review generated file
cat ../alembic/versions/abc123_add_user_email.py

# 3. Test locally
cd ../..
alembic upgrade head

# 4. Test rollback
alembic downgrade -1

# 5. Test upgrade again
alembic upgrade head

# 6. Commit
git add alembic/versions/abc123_add_user_email.py
git commit -m "Add user email column"
```

### Staging Deployment

```bash
# 1. Check status
python check_migrations.py

# 2. Dry run
python migrate.py --dry-run

# 3. Run migration
python migrate.py

# 4. Verify
python check_migrations.py
```

### Production Deployment

```bash
# 1. Create manual backup
python backup.py --name pre_deployment

# 2. Check status
python check_migrations.py

# 3. Dry run
python migrate.py --dry-run

# 4. Review output carefully

# 5. Run migration
python migrate.py

# 6. Monitor
tail -f /var/log/app.log

# 7. Verify
python check_migrations.py

# 8. If issues, rollback
python rollback.py --target <previous_revision>
```

---

## 🐛 Troubleshooting

### "Cannot acquire migration lock"

**Cause:** Another migration is running or lock wasn't released

**Solution:**
```sql
-- Check locks
SELECT * FROM pg_locks WHERE locktype = 'advisory' AND lockid = 1234567890;

-- Force release (use with caution!)
SELECT pg_advisory_unlock(1234567890);
```

### "Database connection failed"

**Cause:** Incorrect DATABASE_URL or database down

**Solution:**
```bash
# Test connection manually
psql $DATABASE_URL -c "SELECT 1"

# Check DATABASE_URL
echo $DATABASE_URL
```

### "Backup failed"

**Cause:** S3 permissions, AWS credentials, or disk space

**Solution:**
```bash
# Test S3 access
aws s3 ls s3://$BACKUP_S3_BUCKET/

# Check disk space
df -h /tmp

# Skip backup temporarily
python migrate.py --skip-backup
```

### "Migration stuck"

**Cause:** Long-running operation (index creation, data backfill)

**Solution:**
```bash
# Check progress
psql $DATABASE_URL -c "SELECT * FROM pg_stat_progress_create_index"

# If truly stuck, cancel
psql $DATABASE_URL -c "SELECT pg_cancel_backend(<pid>)"
```

---

## 📚 Documentation

- **[Zero-Downtime Patterns](../../docs/migrations/zero-downtime.md)** - Comprehensive patterns
- **[Migration Guide](../../docs/migrations/MIGRATION_GUIDE.md)** - Complete user guide
- **[Summary](../../MIGRATION_STRATEGY_SUMMARY.md)** - Implementation overview

---

## 🔧 Development

### Adding New Features

1. Edit script files
2. Test locally
3. Update this README
4. Commit changes

### Testing Scripts

```bash
# Test with local database
export DATABASE_URL="postgresql://localhost/test_db"

# Run script
python migrate.py --dry-run

# Verify output
```

---

## 📞 Support

Issues or questions? See:
- [Migration Guide](../../docs/migrations/MIGRATION_GUIDE.md)
- [Zero-Downtime Patterns](../../docs/migrations/zero-downtime.md)

---

**Version:** 1.0.0  
**Last Updated:** January 24, 2026
