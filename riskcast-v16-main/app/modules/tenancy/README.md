# Tenancy Module

Module quản lý tenant, user, role, permission và membership cho multi-tenant system.

## Models

### 1. Tenant
- **id**: ULID (26 chars) - Primary key
- **name**: VARCHAR(255), unique - Tên tenant
- **status**: Enum('ACTIVE', 'SUSPENDED') - Trạng thái tenant
- **subscription_tier**: VARCHAR(100) - Tier đăng ký (free, standard, enterprise)
- **features_json**: JSON - Feature flags per tenant
- **created_at**, **updated_at**: Timestamps

### 2. User
- **id**: ULID (26 chars) - Primary key
- **email**: VARCHAR(255), unique - Email user
- **password_hash**: VARCHAR(255) - Hashed password
- **status**: Enum('ACTIVE', 'DISABLED') - Trạng thái user
- **created_at**, **updated_at**: Timestamps

### 3. Role
- **id**: ULID (26 chars) - Primary key
- **name**: VARCHAR(100) - Tên role (tenant_admin, operator, viewer, underwriter, claims_adjuster, broker, compliance_officer, platform_admin)
- **scope**: Enum('TENANT', 'PLATFORM') - Scope của role
- **created_at**, **updated_at**: Timestamps
- **Unique constraint**: (name, scope)

### 4. Permission
- **id**: ULID (26 chars) - Primary key
- **key**: VARCHAR(100), unique - Permission key (risk:read, risk:write, risk:run, audit:read, evidence:write, underwriting:decide, etc.)
- **description**: VARCHAR(500) - Mô tả permission
- **created_at**, **updated_at**: Timestamps

### 5. RolePermission (Association Table)
- **role_id**: FK → roles.id
- **permission_id**: FK → permissions.id
- **Primary key**: (role_id, permission_id)

### 6. Membership
- **id**: ULID (26 chars) - Primary key
- **tenant_id**: FK → tenants.id
- **user_id**: FK → users.id
- **role_id**: FK → roles.id
- **status**: Enum('ACTIVE', 'INVITED', 'SUSPENDED') - Trạng thái membership
- **created_at**, **updated_at**: Timestamps
- **Unique constraint**: (tenant_id, user_id) - Một user chỉ có một role trong một tenant
- **Indexes**: 
  - (tenant_id, user_id)
  - (tenant_id, role_id)

## Relationships

```
Tenant (1) ──< (N) Membership (N) >── (1) User
                │
                └── (1) Role (N) >── (N) Permission
```

## Usage Examples

### Create Tenant

```python
from app.modules.tenancy.models import Tenant, TenantStatus

tenant = Tenant(
    name="Acme Corp",
    status=TenantStatus.ACTIVE,
    subscription_tier="enterprise",
    features_json={"risk_engine": True, "audit_trail": True}
)
db.add(tenant)
db.commit()
```

### Create User

```python
from app.modules.tenancy.models import User, UserStatus
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

user = User(
    email="admin@acme.com",
    password_hash=pwd_context.hash("password123"),
    status=UserStatus.ACTIVE
)
db.add(user)
db.commit()
```

### Create Role

```python
from app.modules.tenancy.models import Role, RoleScope

role = Role(
    name="tenant_admin",
    scope=RoleScope.TENANT
)
db.add(role)
db.commit()
```

### Create Permission

```python
from app.modules.tenancy.models import Permission

permission = Permission(
    key="risk:read",
    description="Read risk assessments"
)
db.add(permission)
db.commit()
```

### Assign Permission to Role

```python
from app.modules.tenancy.models import RolePermission

role_permission = RolePermission(
    role_id=role.id,
    permission_id=permission.id
)
db.add(role_permission)
db.commit()
```

### Create Membership (User-Tenant-Role)

```python
from app.modules.tenancy.models import Membership, MembershipStatus

membership = Membership(
    tenant_id=tenant.id,
    user_id=user.id,
    role_id=role.id,
    status=MembershipStatus.ACTIVE
)
db.add(membership)
db.commit()
```

## Migration

Migration file: `migrations/versions/001_create_tenancy_models.py`

To apply:
```bash
alembic upgrade head
```

To rollback:
```bash
alembic downgrade -1
```

## Standard Roles

### Tenant Scope
- `tenant_admin` - Full access to tenant
- `operator` - Operational access
- `viewer` - Read-only access
- `underwriter` - Underwriting access
- `claims_adjuster` - Claims processing
- `broker` - Broker access
- `compliance_officer` - Compliance access

### Platform Scope
- `platform_admin` - Full platform access

## Standard Permissions

Format: `{resource}:{action}`

Examples:
- `risk:read` - Read risk assessments
- `risk:write` - Create/update risk assessments
- `risk:run` - Run risk calculations
- `audit:read` - Read audit logs
- `evidence:write` - Upload evidence
- `underwriting:decide` - Make underwriting decisions
- `claims:process` - Process claims
- `tenant:manage` - Manage tenant settings
- `user:manage` - Manage users
