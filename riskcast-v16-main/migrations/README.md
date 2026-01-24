# Database Migrations

This directory contains Alembic database migrations for RISKCAST V3.

## Setup

1. **Configure database URL** in `.env`:
   ```
   DATABASE_URL=mysql+pymysql://user:password@localhost:3306/riskcast_v3
   ```

2. **Initialize database** (first time only):
   ```bash
   # Create database
   mysql -u root -p
   CREATE DATABASE riskcast_v3 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

3. **Create initial migration**:
   ```bash
   alembic revision --autogenerate -m "Initial schema"
   ```

4. **Apply migrations**:
   ```bash
   alembic upgrade head
   ```

## Common Commands

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply all pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Show current revision
alembic current

# Show migration history
alembic history

# Show pending migrations
alembic heads
```

## Migration Files

Migration files are stored in `migrations/versions/` and follow the pattern:
- `{revision}_description.py`

Each migration file contains:
- `upgrade()`: Apply migration
- `downgrade()`: Rollback migration

## Notes

- All models are imported in `env.py` for autogenerate
- Database URL is read from `app.config.settings.DATABASE_URL`
- MySQL charset is set to `utf8mb4` for full Unicode support
- Foreign keys are enabled by default
