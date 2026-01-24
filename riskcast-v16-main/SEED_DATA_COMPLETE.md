# ✅ Seed Data for Roles and Permissions - Hoàn Thành

## Đã Tạo Thành Công

### 1. Seed Data Module (`migrations/seed_data.py`)

**Functions:**
- ✅ `seed_roles_and_permissions(session)` - Seeds all roles and permissions
- ✅ `clear_roles_and_permissions(session)` - Clears all roles and permissions (for downgrade)

**Features:**
- ✅ Creates all permissions from `Permissions` class
- ✅ Creates roles from `DEFAULT_ROLE_PERMISSIONS`
- ✅ Assigns permissions to roles based on mappings
- ✅ Handles wildcard `*` for tenant_admin (all tenant permissions)
- ✅ Handles `PLATFORM_ADMIN` for platform_admin role
- ✅ Idempotent (can be run multiple times safely)
- ✅ Skips existing records (no duplicates)

### 2. Alembic Migration (`migrations/versions/006_seed_roles_and_permissions.py`)

**Features:**
- ✅ Calls seed function in `upgrade()`
- ✅ Calls clear function in `downgrade()`
- ✅ Proper error handling with rollback
- ✅ Uses Alembic's connection binding

## Roles Created

### Tenant Roles (Scope: TENANT)

1. **viewer**
   - Permissions: `risk:read`, `audit:read`, `evidence:read`, `claims:read`, `parametric:read`
   - Description: Read-only access to view data

2. **operator**
   - Permissions: `risk:read`, `risk:write`, `risk:run`, `audit:read`, `evidence:read`, `evidence:write`, `claims:read`, `claims:write`, `parametric:read`
   - Description: Can create and run risk assessments, manage evidence and claims

3. **tenant_admin**
   - Permissions: `*` (all tenant permissions except `platform:admin`)
   - Description: Full tenant administration access

4. **underwriter**
   - Permissions: `risk:read`, `risk:export`, `audit:read`, `evidence:read`, `evidence:export`, `underwriting:read`, `underwriting:write`, `underwriting:decide`, `policy:bind`, `model:read`
   - Description: Underwriting decision-making access

5. **claims_adjuster**
   - Permissions: `risk:read`, `audit:read`, `evidence:read`, `evidence:write`, `claims:read`, `claims:write`, `claims:act`, `payout:approve`
   - Description: Claims processing and payout approval

6. **broker**
   - Permissions: `risk:read`, `risk:export`, `audit:read`, `evidence:read`, `underwriting:read`, `claims:read`
   - Description: Broker access for viewing and exporting data

7. **compliance_officer**
   - Permissions: `risk:read`, `audit:read`, `audit:export`, `evidence:read`, `claims:read`
   - Description: Compliance and audit access

### Platform Role (Scope: PLATFORM)

8. **platform_admin**
   - Permissions: `platform:admin`
   - Description: Full platform administration access

## Permissions Created

All permissions from `Permissions` class are created:

### Risk Permissions
- `risk:read` - Read risk assessments and runs
- `risk:write` - Create risk assessments
- `risk:run` - Execute risk runs
- `risk:export` - Export risk data

### Audit Permissions
- `audit:read` - Read audit logs
- `audit:export` - Export audit logs

### Evidence Permissions
- `evidence:read` - Read evidence
- `evidence:write` - Upload evidence
- `evidence:delete` - Delete evidence
- `evidence:export` - Export evidence bundles

### Model Permissions
- `model:read` - Read model versions
- `model:write` - Create model versions
- `model:publish` - Publish model versions
- `model:activate` - Activate models for tenants

### Underwriting Permissions
- `underwriting:read` - Read underwriting submissions
- `underwriting:write` - Create underwriting submissions
- `underwriting:decide` - Make underwriting decisions
- `policy:bind` - Bind policies

### Claims Permissions
- `claims:read` - Read claims
- `claims:write` - Create claims
- `claims:act` - Take actions on claims
- `payout:approve` - Approve payouts

### Parametric Permissions
- `parametric:read` - Read parametric data
- `parametric:write` - Write parametric data
- `parametric:monitor` - Monitor parametric triggers

### Tenant Permissions
- `tenant:read` - Read tenant information
- `tenant:manage` - Manage tenant settings
- `tenant:users` - Manage tenant users
- `tenant:admin` - Tenant administration

### User Permissions
- `user:read` - Read user information
- `user:manage` - Manage users
- `user:invite` - Invite users

### Role Permissions
- `role:read` - Read roles
- `role:manage` - Manage roles

### Platform Permissions
- `platform:admin` - Platform administration

## Usage

### Run Migration

```bash
# Upgrade (seed data)
alembic upgrade head

# Downgrade (clear data)
alembic downgrade -1
```

### Run Seed Function Directly

```python
from app.database import SessionLocal
from migrations.seed_data import seed_roles_and_permissions

session = SessionLocal()
try:
    seed_roles_and_permissions(session)
    print("✅ Seed data created successfully")
except Exception as e:
    session.rollback()
    print(f"❌ Error: {e}")
finally:
    session.close()
```

### Verify Seed Data

```python
from app.database import SessionLocal
from app.modules.tenancy.models import Role, Permission, RolePermission

session = SessionLocal()

# Count permissions
permission_count = session.query(Permission).count()
print(f"Permissions: {permission_count}")

# Count roles
role_count = session.query(Role).count()
print(f"Roles: {role_count}")

# Count role-permission associations
rp_count = session.query(RolePermission).count()
print(f"Role-Permission associations: {rp_count}")

# List roles with permissions
for role in session.query(Role).all():
    perm_count = session.query(RolePermission).filter(
        RolePermission.role_id == role.id
    ).count()
    print(f"  {role.name} ({role.scope.value}): {perm_count} permissions")

session.close()
```

## Idempotency

The seed function is idempotent:
- ✅ Checks for existing permissions before creating
- ✅ Checks for existing roles before creating
- ✅ Checks for existing role-permission associations before creating
- ✅ Can be run multiple times safely
- ✅ No duplicate records

## Files Created

1. ✅ `migrations/seed_data.py` - Seed data functions
2. ✅ `migrations/versions/006_seed_roles_and_permissions.py` - Alembic migration
3. ✅ `SEED_DATA_COMPLETE.md` - This documentation

## Migration Order

The migration depends on:
- `001_create_tenancy_models.py` - Creates roles, permissions, role_permissions tables

Run migrations in order:
```bash
alembic upgrade head
```

## Notes

1. **Wildcard Handling**: The `*` permission in `tenant_admin` role grants all tenant permissions (excluding `platform:admin`)

2. **Platform Admin**: The `platform_admin` role only gets `platform:admin` permission, which grants all permissions via the permission checking logic

3. **Reseeding**: If you need to reseed (e.g., after adding new permissions), you can:
   - Run the migration again (it's idempotent)
   - Or manually call `seed_roles_and_permissions()` again

4. **Downgrade**: The downgrade function clears ALL roles and permissions. Use with caution in production.

**Seed data system hoàn thành và sẵn sàng sử dụng!** 🎉
