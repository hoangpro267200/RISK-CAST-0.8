# Zero-Downtime Migration Patterns

## 🎯 Principles

### 1. Backward Compatibility
**New code must work with old schema**

The code deployed after a migration must be able to work with the database schema from before the migration. This allows for zero-downtime deployments.

### 2. Forward Compatibility
**Old code must work with new schema**

The code running before a migration must be able to work with the database schema created by the migration. This allows rollback without re-running migrations.

### 3. Expand-Contract Pattern
**Add before remove**

Make additive changes first, wait for deployment, then remove old structures.

```
Phase 1: Expand  → Add new column/table
Phase 2: Migrate → Copy/transform data
Phase 3: Deploy  → Update code to use new structure
Phase 4: Contract → Remove old column/table
```

---

## 📚 Common Patterns

### Pattern 1: Adding a Column

**Safe approach (2 migrations):**

```python
# Migration 1: Add column with default (backward compatible)
def upgrade():
    op.add_column('users', 
        sa.Column('status', sa.String(20), 
                  server_default='active', 
                  nullable=False))

def downgrade():
    op.drop_column('users', 'status')
```

```python
# Migration 2 (after code deployed): Make changes if needed
def upgrade():
    # Optional: Change default or add constraints
    op.alter_column('users', 'status', 
                    server_default=None)

def downgrade():
    op.alter_column('users', 'status', 
                    server_default='active')
```

**Why this works:**
- Old code: Doesn't know about `status`, database provides default
- New code: Can read and write `status`

---

### Pattern 2: Renaming a Column

**Safe approach (3 migrations + 2 deployments):**

```python
# Migration 1: Add new column
def upgrade():
    op.add_column('users', 
        sa.Column('full_name', sa.String(200)))

def downgrade():
    op.drop_column('users', 'full_name')
```

**Deploy code that writes to both columns:**

```python
# Interim code (write to both, read from old)
user.name = full_name
user.full_name = full_name  # Populate new column
db.commit()
```

```python
# Migration 2: Copy existing data
def upgrade():
    op.execute("""
        UPDATE users 
        SET full_name = name 
        WHERE full_name IS NULL
    """)
    
    # Make NOT NULL after data copied
    op.alter_column('users', 'full_name', 
                    nullable=False)

def downgrade():
    op.alter_column('users', 'full_name', 
                    nullable=True)
```

**Deploy code that reads from new column:**

```python
# New code (read from new, write to both for safety)
full_name = user.full_name
user.full_name = full_name
user.name = full_name  # Keep old column in sync temporarily
```

```python
# Migration 3: Drop old column
def upgrade():
    op.drop_column('users', 'name')

def downgrade():
    op.add_column('users', 
        sa.Column('name', sa.String(200)))
    # Copy data back
    op.execute("""
        UPDATE users SET name = full_name
    """)
```

**Timeline:**
1. Migration 1 + Deploy (dual write) → Old code works, new column populates
2. Migration 2 → Backfill data
3. Deploy (read from new) → Switch to new column
4. Migration 3 → Clean up old column

---

### Pattern 3: Changing Column Type

**Safe approach:**

```python
# Migration 1: Add new column with new type
def upgrade():
    op.add_column('orders', 
        sa.Column('amount_cents', sa.Integer()))

def downgrade():
    op.drop_column('orders', 'amount_cents')
```

```python
# Migration 2: Copy and transform data
def upgrade():
    op.execute("""
        UPDATE orders 
        SET amount_cents = (amount_dollars * 100)::INTEGER
        WHERE amount_cents IS NULL
    """)

def downgrade():
    pass
```

**Deploy code using new column**

```python
# Migration 3: Drop old column
def upgrade():
    op.drop_column('orders', 'amount_dollars')

def downgrade():
    op.add_column('orders', 
        sa.Column('amount_dollars', sa.Numeric(10, 2)))
```

---

### Pattern 4: Adding a NOT NULL Column

**Safe approach:**

```python
# Migration 1: Add nullable column
def upgrade():
    op.add_column('users', 
        sa.Column('email', sa.String(255), 
                  nullable=True))

def downgrade():
    op.drop_column('users', 'email')
```

**Deploy code that populates the column**

```python
# Migration 2: Backfill data
def upgrade():
    # Backfill missing values
    op.execute("""
        UPDATE users 
        SET email = username || '@example.com'
        WHERE email IS NULL
    """)
    
    # Now make NOT NULL
    op.alter_column('users', 'email', 
                    nullable=False)

def downgrade():
    op.alter_column('users', 'email', 
                    nullable=True)
```

---

### Pattern 5: Adding an Index

**Always use CONCURRENTLY to avoid locking:**

```python
def upgrade():
    # Standard approach causes table lock
    # op.create_index('idx_users_email', 'users', ['email'])
    
    # Better: Use CONCURRENTLY (no table lock)
    op.execute("""
        CREATE INDEX CONCURRENTLY idx_users_email 
        ON users(email)
    """)

def downgrade():
    op.execute("""
        DROP INDEX CONCURRENTLY idx_users_email
    """)
```

**For unique indexes:**

```python
def upgrade():
    # Step 1: Create unique index concurrently
    op.execute("""
        CREATE UNIQUE INDEX CONCURRENTLY idx_users_email_unique
        ON users(email)
    """)
    
    # Step 2: Add constraint using existing index
    op.execute("""
        ALTER TABLE users
        ADD CONSTRAINT uq_users_email
        UNIQUE USING INDEX idx_users_email_unique
    """)

def downgrade():
    op.drop_constraint('uq_users_email', 'users')
```

**Important notes:**
- `CONCURRENTLY` cannot run inside a transaction
- Set `transaction_per_migration=False` in migration if using CONCURRENTLY
- Index creation may take time on large tables

---

### Pattern 6: Removing a Column

**Safe approach:**

```python
# Migration 1: Make column nullable (if not already)
def upgrade():
    op.alter_column('users', 'deprecated_field',
                    nullable=True)

def downgrade():
    op.alter_column('users', 'deprecated_field',
                    nullable=False)
```

**Deploy code that doesn't use the column**

```python
# Migration 2: Drop the column
def upgrade():
    op.drop_column('users', 'deprecated_field')

def downgrade():
    op.add_column('users',
        sa.Column('deprecated_field', sa.String(100)))
```

---

### Pattern 7: Adding a Foreign Key

**Safe approach:**

```python
# Migration 1: Add column without FK constraint
def upgrade():
    op.add_column('orders',
        sa.Column('customer_id', sa.Integer(), 
                  nullable=True))

def downgrade():
    op.drop_column('orders', 'customer_id')
```

**Deploy code that populates the column**

```python
# Migration 2: Validate data and add FK
def upgrade():
    # Ensure all values are valid
    op.execute("""
        UPDATE orders
        SET customer_id = NULL
        WHERE customer_id NOT IN (SELECT id FROM customers)
    """)
    
    # Add FK with validation (not concurrently)
    op.create_foreign_key(
        'fk_orders_customer',
        'orders', 'customers',
        ['customer_id'], ['id']
    )

def downgrade():
    op.drop_constraint('fk_orders_customer', 'orders')
```

**For existing column:**

```python
def upgrade():
    # Add FK with NOT VALID (doesn't lock)
    op.execute("""
        ALTER TABLE orders
        ADD CONSTRAINT fk_orders_customer
        FOREIGN KEY (customer_id)
        REFERENCES customers(id)
        NOT VALID
    """)
    
    # Validate in background (may take time)
    op.execute("""
        ALTER TABLE orders
        VALIDATE CONSTRAINT fk_orders_customer
    """)
```

---

### Pattern 8: Changing a Foreign Key (ON DELETE behavior)

**Safe approach:**

```python
# Migration 1: Add new FK with new behavior
def upgrade():
    # Drop old FK
    op.drop_constraint('fk_orders_customer', 'orders')
    
    # Add new FK with different ON DELETE
    op.create_foreign_key(
        'fk_orders_customer',
        'orders', 'customers',
        ['customer_id'], ['id'],
        ondelete='CASCADE'  # Changed from default
    )

def downgrade():
    op.drop_constraint('fk_orders_customer', 'orders')
    op.create_foreign_key(
        'fk_orders_customer',
        'orders', 'customers',
        ['customer_id'], ['id']
    )
```

---

## 🚨 Anti-Patterns (DON'T DO THIS)

### ❌ Anti-Pattern 1: Renaming in One Step

```python
# WRONG: This breaks old code
def upgrade():
    op.alter_column('users', 'name', new_column_name='full_name')
```

**Why it fails:** Old code looks for `name`, gets error

### ❌ Anti-Pattern 2: Adding NOT NULL Without Default

```python
# WRONG: This breaks old code
def upgrade():
    op.add_column('users',
        sa.Column('email', sa.String(255), nullable=False))
```

**Why it fails:** Old code can't insert rows (no email value)

### ❌ Anti-Pattern 3: Dropping Column Immediately

```python
# WRONG: This breaks old code
def upgrade():
    op.drop_column('users', 'deprecated_field')
```

**Why it fails:** Old code tries to read/write column, gets error

### ❌ Anti-Pattern 4: Creating Index Without CONCURRENTLY

```python
# WRONG: This locks table
def upgrade():
    op.create_index('idx_users_email', 'users', ['email'])
```

**Why it fails:** Table locked during index creation, downtime

---

## ✅ Pre-Deployment Checklist

Before running migrations in production:

- [ ] **Backward Compatibility**
  - [ ] New code works with old schema
  - [ ] Old code works with new schema
  
- [ ] **Migration Safety**
  - [ ] No table locks (use CONCURRENTLY for indexes)
  - [ ] Defaults provided for new NOT NULL columns
  - [ ] No column renames in single step
  - [ ] No immediate column drops
  
- [ ] **Data Integrity**
  - [ ] Backfill scripts tested
  - [ ] No data loss
  - [ ] Foreign key constraints validated
  
- [ ] **Rollback Plan**
  - [ ] Downgrade migration tested
  - [ ] Backup created and verified
  - [ ] Rollback procedure documented
  
- [ ] **Performance**
  - [ ] Migration runtime estimated
  - [ ] Large table operations optimized
  - [ ] Index creation won't timeout
  
- [ ] **Monitoring**
  - [ ] Database metrics dashboard ready
  - [ ] Alerts configured
  - [ ] Slack notifications enabled

---

## 🔧 Testing Migrations

### Local Testing

```bash
# Test upgrade
alembic upgrade head

# Test downgrade
alembic downgrade -1

# Test upgrade again
alembic upgrade head
```

### Staging Testing

```bash
# 1. Restore production data to staging
python scripts/db/restore_backup.py --env staging

# 2. Run migration
python scripts/db/migrate.py --dry-run

# 3. Deploy old code, verify it works
kubectl rollout restart deployment/api

# 4. Run migration for real
python scripts/db/migrate.py

# 5. Deploy new code, verify it works
kubectl set image deployment/api api=new-image
```

### Production Checklist

```bash
# 1. Create backup
python scripts/db/backup.py

# 2. Dry run
python scripts/db/migrate.py --dry-run

# 3. Check active connections
python scripts/db/check_connections.py

# 4. Run migration
python scripts/db/migrate.py

# 5. Verify migration
python scripts/db/verify_migration.py

# 6. Monitor for errors
kubectl logs -f deployment/api
```

---

## 📊 Migration Timeline Example

### Scenario: Rename `user.name` to `user.full_name`

**Week 1: Add New Column**
- Monday: Create Migration 1 (add `full_name`)
- Monday: Deploy PR with dual-write code
- Monitor: Old code works ✓

**Week 2: Backfill Data**
- Monday: Create Migration 2 (backfill + NOT NULL)
- Monday: Run migration in production
- Monitor: Data populated ✓

**Week 3: Switch to New Column**
- Monday: Deploy PR reading from `full_name`
- Monitor: New code works ✓
- No old code in production ✓

**Week 4: Remove Old Column**
- Monday: Create Migration 3 (drop `name`)
- Monday: Run migration in production
- Cleanup complete ✓

**Total time:** 4 weeks for complete safety

---

## 🚀 Quick Reference

| Operation | Migrations | Deployments | Safe? |
|-----------|-----------|-------------|-------|
| Add column | 1 | 1 | ✅ |
| Add column (NOT NULL) | 2 | 2 | ✅ |
| Remove column | 2 | 2 | ✅ |
| Rename column | 3 | 3 | ✅ |
| Change type | 3 | 2 | ✅ |
| Add index | 1 | 1 | ✅ (if CONCURRENTLY) |
| Add FK | 2 | 2 | ✅ |
| Drop table | 2 | 2 | ✅ |

---

## 📚 Additional Resources

- **Alembic Documentation:** https://alembic.sqlalchemy.org/
- **PostgreSQL CONCURRENTLY:** https://www.postgresql.org/docs/current/sql-createindex.html
- **Expand-Contract Pattern:** https://martinfowler.com/bliki/ParallelChange.html
- **Database Refactoring:** https://databaserefactoring.com/

---

**Last Updated:** January 24, 2026  
**Version:** 1.0.0
