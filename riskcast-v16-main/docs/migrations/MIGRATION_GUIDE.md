# Database Migration Guide

## 📚 Table of Contents

- [Quick Start](#quick-start)
- [Creating Migrations](#creating-migrations)
- [Running Migrations](#running-migrations)
- [Rolling Back](#rolling-back)
- [Zero-Downtime Patterns](#zero-downtime-patterns)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

### Initial Setup

```bash
# Install dependencies
pip install alembic asyncpg

# Initialize database
alembic upgrade head
```

### Check Migration Status

```bash
# Check current status
python scripts/db/check_migrations.py

# Show revision history
python scripts/db/rollback.py --history
```

---

## 📝 Creating Migrations

### Auto-generate from Models

```bash
# Create migration based on model changes
python scripts/db/create_migration.py "add user email column"
```

This will:
1. Compare current database schema with models
2. Generate migration file with changes
3. Create both `upgrade()` and `downgrade()` functions

### Manual Migration

```bash
# Create empty migration for custom SQL
python scripts/db/create_migration.py "custom data migration" --no-autogenerate
```

### Migration File Structure

```python
"""add user email column

Revision ID: abc123def456
Revises: prev_revision
Create Date: 2026-01-24 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'abc123def456'
down_revision = 'prev_revision'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add changes here
    op.add_column('users', 
        sa.Column('email', sa.String(255), nullable=True))


def downgrade() -> None:
    # Reverse changes here
    op.drop_column('users', 'email')
```

---

## 🏃 Running Migrations

### Local Development

```bash
# Run all pending migrations
alembic upgrade head

# Run one migration at a time
alembic upgrade +1

# Run to specific revision
alembic upgrade abc123
```

### Staging/Production

```bash
# Dry run (show what would be applied)
python scripts/db/migrate.py --dry-run

# Run with all safety checks
python scripts/db/migrate.py

# Skip backup (not recommended)
python scripts/db/migrate.py --skip-backup

# Skip pre-flight checks (not recommended)
python scripts/db/migrate.py --skip-checks
```

### What Happens During Migration

1. **Pre-flight checks:**
   - Database connection
   - Pending migrations list
   - Active connections count
   - Long-running queries check

2. **Lock acquisition:**
   - PostgreSQL advisory lock acquired
   - Prevents concurrent migrations

3. **Backup:**
   - pg_dump to S3
   - Safety net for rollback

4. **Migration execution:**
   - Alembic applies changes
   - Transaction per migration

5. **Notification:**
   - Slack notification (if configured)
   - Success/failure status

---

## ⏮️ Rolling Back

### Check Rollback Options

```bash
# Show recent revisions
python scripts/db/rollback.py --history
```

Output:
```
Revision History:
→ abc123: add user email column
  def456: add user status
  ghi789: create orders table
```

### Rollback to Previous Version

```bash
# Rollback one migration
python scripts/db/rollback.py --target def456

# Skip confirmation (use with caution!)
python scripts/db/rollback.py --target def456 --yes
```

### What Happens During Rollback

1. Shows current and target revisions
2. Lists migrations to be rolled back
3. Asks for confirmation
4. Executes downgrade migrations
5. Verifies final state

---

## 🎯 Zero-Downtime Patterns

See [zero-downtime.md](zero-downtime.md) for comprehensive patterns.

### Quick Reference

**Adding Column:**
```python
# Safe: Add with default
op.add_column('users', 
    sa.Column('status', sa.String(20), 
              server_default='active'))
```

**Renaming Column:**
```python
# Step 1: Add new column
op.add_column('users', sa.Column('full_name', sa.String(200)))

# Step 2: Backfill data (after deploy)
op.execute("UPDATE users SET full_name = name WHERE full_name IS NULL")

# Step 3: Drop old column (after another deploy)
op.drop_column('users', 'name')
```

**Adding Index:**
```python
# Safe: Use CONCURRENTLY
op.execute("""
    CREATE INDEX CONCURRENTLY idx_users_email 
    ON users(email)
""")
```

---

## ✅ Best Practices

### 1. Always Test Locally First

```bash
# Test upgrade
alembic upgrade head

# Test downgrade
alembic downgrade -1

# Test upgrade again
alembic upgrade head
```

### 2. Write Reversible Migrations

Every `upgrade()` should have corresponding `downgrade()`:

```python
def upgrade():
    op.add_column('users', sa.Column('email', sa.String(255)))

def downgrade():
    op.drop_column('users', 'email')
```

### 3. Use Transactions Wisely

```python
# Most operations should be in transaction
def upgrade():
    op.add_column('users', sa.Column('email', sa.String(255)))

# CONCURRENTLY operations cannot use transaction
def upgrade():
    # Disable transaction for this migration
    op.get_bind().connection.execution_options(
        isolation_level="AUTOCOMMIT"
    )
    op.execute("CREATE INDEX CONCURRENTLY idx_users_email ON users(email)")
```

### 4. Add Comments

```python
def upgrade():
    # Add email column for user notifications
    # Default value allows existing rows to remain valid
    op.add_column('users',
        sa.Column('email', sa.String(255), 
                  server_default='unknown@example.com'))
```

### 5. Test with Production-Like Data

```bash
# Restore production backup to staging
python scripts/db/restore_backup.py --env staging

# Run migration
python scripts/db/migrate.py

# Verify data integrity
python scripts/db/verify_data.py
```

### 6. Monitor Performance

```sql
-- Check migration progress
SELECT * FROM pg_stat_progress_create_index;

-- Check long-running queries
SELECT pid, now() - query_start as duration, query
FROM pg_stat_activity
WHERE state = 'active'
ORDER BY duration DESC;
```

---

## 🐛 Troubleshooting

### Migration Lock Timeout

**Problem:** Cannot acquire migration lock

**Solution:**
```sql
-- Check who has the lock
SELECT * FROM pg_locks WHERE locktype = 'advisory';

-- Force release (use with caution!)
SELECT pg_advisory_unlock_all();
```

### Migration Stuck

**Problem:** Migration running for too long

**Solution:**
```bash
# Check progress
psql $DATABASE_URL -c "SELECT * FROM pg_stat_progress_create_index"

# If truly stuck, cancel
psql $DATABASE_URL -c "SELECT pg_cancel_backend(pid) FROM pg_stat_activity WHERE query LIKE '%CREATE INDEX%'"
```

### Rollback Failed

**Problem:** Downgrade migration fails

**Solution:**
```bash
# 1. Check error message
python scripts/db/rollback.py --target abc123

# 2. Fix downgrade() function in migration file

# 3. Try again
python scripts/db/rollback.py --target abc123 --yes
```

### Conflicting Migrations

**Problem:** Multiple heads detected

**Solution:**
```bash
# Check heads
alembic heads

# Merge branches
alembic merge heads -m "merge branches"

# Apply merge
alembic upgrade head
```

### Database Out of Sync

**Problem:** Models don't match database

**Solution:**
```bash
# Generate migration to fix
python scripts/db/create_migration.py "sync models with database"

# Review generated migration carefully!

# Apply if correct
python scripts/db/migrate.py
```

---

## 📊 Common Operations

### Add Column

```python
def upgrade():
    op.add_column('users',
        sa.Column('created_at', sa.DateTime(), 
                  server_default=sa.text('NOW()')))

def downgrade():
    op.drop_column('users', 'created_at')
```

### Modify Column

```python
def upgrade():
    op.alter_column('users', 'email',
                    type_=sa.String(500),  # Changed from 255
                    existing_type=sa.String(255))

def downgrade():
    op.alter_column('users', 'email',
                    type_=sa.String(255),
                    existing_type=sa.String(500))
```

### Add Index

```python
def upgrade():
    op.create_index('idx_users_email', 'users', ['email'])

def downgrade():
    op.drop_index('idx_users_email', table_name='users')
```

### Add Foreign Key

```python
def upgrade():
    op.create_foreign_key(
        'fk_orders_customer',
        'orders', 'customers',
        ['customer_id'], ['id']
    )

def downgrade():
    op.drop_constraint('fk_orders_customer', 'orders', type_='foreignkey')
```

### Create Table

```python
def upgrade():
    op.create_table(
        'orders',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('total', sa.Numeric(10, 2), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'))
    )
    
    op.create_index('idx_orders_customer', 'orders', ['customer_id'])

def downgrade():
    op.drop_table('orders')
```

### Run Custom SQL

```python
def upgrade():
    op.execute("""
        UPDATE users 
        SET status = 'active' 
        WHERE last_login > NOW() - INTERVAL '30 days'
    """)

def downgrade():
    # Often not reversible
    pass
```

---

## 🔒 Security

### Environment Variables

```bash
# Required
export DATABASE_URL="postgresql://user:pass@host:5432/dbname"

# Optional
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
export BACKUP_S3_BUCKET="riskcast-backups"
```

### Permissions

Migration scripts need:
- Database: CREATE, ALTER, DROP permissions
- S3: PutObject permission for backups
- Slack: Webhook URL for notifications

---

## 📞 Getting Help

- **Zero-Downtime Patterns:** [zero-downtime.md](zero-downtime.md)
- **Alembic Docs:** https://alembic.sqlalchemy.org/
- **PostgreSQL Docs:** https://www.postgresql.org/docs/

---

**Last Updated:** January 24, 2026  
**Version:** 1.0.0
