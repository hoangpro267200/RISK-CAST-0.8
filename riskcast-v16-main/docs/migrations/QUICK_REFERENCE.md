# Database Migrations - Quick Reference Card

## 🚀 Common Commands

### Check Status
```bash
python scripts/db/check_migrations.py
alembic current
make migration-check
```

### Create Migration
```bash
python scripts/db/create_migration.py "message"
make migration-create
```

### Run Migration
```bash
python scripts/db/migrate.py
python scripts/db/migrate.py --dry-run
make migration-up
```

### Rollback
```bash
python scripts/db/rollback.py --target abc123
python scripts/db/rollback.py --history
make migration-down
```

### Backup
```bash
python scripts/db/backup.py
make backup
```

---

## 📋 Safe Migration Patterns

### Add Column (1 migration)
```python
def upgrade():
    op.add_column('users',
        sa.Column('status', sa.String(20), server_default='active'))
```

### Add NOT NULL Column (2 migrations)
```python
# Migration 1: Add nullable
def upgrade():
    op.add_column('users', sa.Column('email', sa.String(255)))

# Migration 2: Make NOT NULL
def upgrade():
    op.execute("UPDATE users SET email = 'unknown' WHERE email IS NULL")
    op.alter_column('users', 'email', nullable=False)
```

### Rename Column (3 migrations)
```python
# Migration 1: Add new
op.add_column('users', sa.Column('full_name', sa.String(200)))

# Migration 2: Backfill
op.execute("UPDATE users SET full_name = name WHERE full_name IS NULL")

# Migration 3: Drop old
op.drop_column('users', 'name')
```

### Add Index
```python
# Use CONCURRENTLY!
op.execute("CREATE INDEX CONCURRENTLY idx_users_email ON users(email)")
```

---

## 🔒 Safety Checklist

Before production:
- [ ] Tested locally (up and down)
- [ ] Backward compatible
- [ ] No table locks (CONCURRENTLY)
- [ ] Backup created
- [ ] Rollback plan ready

---

## 🐛 Troubleshooting

### Lock Timeout
```sql
SELECT pg_advisory_unlock(1234567890);
```

### Check Progress
```sql
SELECT * FROM pg_stat_progress_create_index;
```

### Cancel Stuck Query
```sql
SELECT pg_cancel_backend(<pid>);
```

---

## 📊 Migration Timeline

| Phase | Action | Duration |
|-------|--------|----------|
| Week 1 | Add new column | Immediate |
| Week 2 | Backfill data | Minutes |
| Week 3 | Deploy new code | Hours |
| Week 4 | Remove old column | Immediate |

---

## 🚨 Anti-Patterns

❌ Don't rename in one step  
❌ Don't add NOT NULL immediately  
❌ Don't drop columns immediately  
❌ Don't create indexes without CONCURRENTLY  

✅ Use expand-contract pattern  
✅ Add defaults for new columns  
✅ Wait between migrations  
✅ Always use CONCURRENTLY  

---

## 📚 Docs

- [Full Guide](MIGRATION_GUIDE.md)
- [Zero-Downtime](zero-downtime.md)
- [Summary](../../MIGRATION_STRATEGY_SUMMARY.md)

---

**Print this for quick reference! 📋**
