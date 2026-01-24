# Database Setup Guide - RISKCAST V3

## Overview

RISKCAST V3 uses **MySQL** with **SQLAlchemy 2.0+** and **Alembic** for database migrations.

## Database URL Format

```
mysql+pymysql://user:password@host:port/database_name
```

Example:
```
mysql+pymysql://riskcast:password@localhost:3306/riskcast_v3
```

## Setup Steps

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `sqlalchemy>=2.0.0`
- `alembic>=1.12.0`
- `pymysql>=1.1.0`
- `cryptography>=41.0.0`

### 2. Create Database

```bash
mysql -u root -p
```

```sql
CREATE DATABASE riskcast_v3 
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci;

-- Create user (optional)
CREATE USER 'riskcast'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON riskcast_v3.* TO 'riskcast'@'localhost';
FLUSH PRIVILEGES;
```

### 3. Configure Environment

Create `.env` file:

```env
DATABASE_URL=mysql+pymysql://riskcast:password@localhost:3306/riskcast_v3
DATABASE_ECHO=false
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
```

### 4. Initialize Alembic (if not already done)

```bash
# Already initialized, but if you need to reinit:
alembic init migrations
```

### 5. Create Initial Migration

```bash
# Generate migration from models
alembic revision --autogenerate -m "Initial schema"

# Review the generated migration file in migrations/versions/
```

### 6. Apply Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Check current revision
alembic current
```

## Model Mixins

### BaseMixin

Provides common fields for all models:

```python
from app.shared.models import BaseMixin
from app.database import Base

class MyModel(Base, BaseMixin):
    __tablename__ = "my_models"
    
    name = Column(String(255))
    
    # Automatically gets:
    # - id: ULID primary key
    # - created_at: Creation timestamp
    # - updated_at: Auto-updated timestamp
```

### TenantScopedMixin

For multi-tenant models:

```python
from app.shared.models import BaseMixin, TenantScopedMixin

class TenantModel(Base, BaseMixin, TenantScopedMixin):
    __tablename__ = "tenant_models"
    
    name = Column(String(255))
    
    # Automatically gets:
    # - tenant_id: Foreign key to tenants
    # - __tenant_scoped__: Marker for tenant isolation
```

### SoftDeleteMixin

For soft-deletable models:

```python
from app.shared.models import BaseMixin, SoftDeleteMixin

class DeletableModel(Base, BaseMixin, SoftDeleteMixin):
    __tablename__ = "deletable_models"
    
    # Usage:
    # model.soft_delete()  # Mark as deleted
    # model.restore()      # Restore
    # if model.is_deleted: # Check status
```

## ULID Primary Keys

All models using `BaseMixin` get ULID primary keys:

```python
from app.shared.utils import generate_ulid, parse_ulid

# Generate ULID
ulid = generate_ulid()  # e.g., "01ARZ3NDEKTSV4RRFFQ69G5FAV"

# Parse ULID
info = parse_ulid(ulid)
# Returns: {'timestamp': datetime, 'random': bytes}
```

**ULID Benefits:**
- Sortable by creation time
- URL-safe
- 26 characters (shorter than UUID)
- Contains timestamp information

## Connection Pooling

SQLAlchemy connection pool settings (in `app/config.py`):

- `DATABASE_POOL_SIZE`: 10 (default)
- `DATABASE_MAX_OVERFLOW`: 20 (default)
- `pool_pre_ping`: True (verify connections)
- `pool_recycle`: 3600 seconds (1 hour)

## MySQL-Specific Settings

On connection, MySQL settings are automatically applied:

- Timezone: UTC (`SET time_zone = '+00:00'`)
- Foreign keys: Enabled (`SET FOREIGN_KEY_CHECKS = 1`)
- Charset: `utf8mb4` (`SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci`)

## Common Alembic Commands

```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Show current revision
alembic current

# Show history
alembic history

# Show pending migrations
alembic heads
```

## Troubleshooting

### Connection Issues

1. **Check MySQL is running:**
   ```bash
   mysqladmin -u root -p status
   ```

2. **Test connection:**
   ```python
   from app.database import engine
   with engine.connect() as conn:
       print("Connected!")
   ```

3. **Check database exists:**
   ```sql
   SHOW DATABASES;
   ```

### Migration Issues

1. **If autogenerate misses changes:**
   - Manually create migration: `alembic revision -m "Description"`
   - Edit migration file manually

2. **If migration fails:**
   - Check migration file syntax
   - Verify database state: `alembic current`
   - Rollback if needed: `alembic downgrade -1`

### Import Errors

If models aren't detected by Alembic:

1. Check `migrations/env.py` imports all models
2. Verify `app.database.Base` is used by all models
3. Check for circular imports

## Production Considerations

1. **Use connection pooling** (already configured)
2. **Set appropriate pool sizes** based on load
3. **Enable query logging** for debugging (set `DATABASE_ECHO=true`)
4. **Use read replicas** for read-heavy workloads
5. **Backup strategy** for production database
6. **Monitor connection pool** metrics

## Next Steps

1. Review generated migration files
2. Test migrations on development database
3. Set up database backups
4. Configure connection pooling for production
5. Add database monitoring/alerting
