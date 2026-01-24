# ✅ Tenancy Schemas & Repository - Hoàn Thành

## Đã Tạo Thành Công

### 1. Pydantic Schemas (`app/modules/tenancy/schemas.py`)

#### ✅ Tenant Schemas
- **TenantCreate**: Schema để tạo tenant mới
  - `name`: Required, 1-255 chars
  - `status`: Optional, default ACTIVE
  - `subscription_tier`: Optional
  - `features_json`: Optional, default empty dict

- **TenantUpdate**: Schema để update tenant
  - Tất cả fields optional

- **TenantResponse**: Schema response
  - Bao gồm id, timestamps
  - `from_attributes = True` để convert từ SQLAlchemy model

#### ✅ User Schemas
- **UserCreate**: Schema để tạo user mới
  - `email`: Required, validated với EmailStr
  - `password`: Required, min 8 chars (sẽ được hash)
  - `status`: Optional, default ACTIVE
  - Validator: password phải >= 8 chars

- **UserUpdate**: Schema để update user
  - Tất cả fields optional
  - Password validator nếu có

- **UserResponse**: Schema response (không có password)
  - Chỉ có id, email, status, timestamps

#### ✅ Membership Schemas
- **MembershipCreate**: Schema để tạo membership
  - `tenant_id`, `user_id`, `role_id`: Required
  - `status`: Optional, default INVITED

- **MembershipResponse**: Schema response
  - Bao gồm nested objects: tenant, user, role (optional)

#### ✅ Role & Permission Schemas
- **RoleResponse**: Schema response cho role
  - Có thể include permissions list

- **PermissionResponse**: Schema response cho permission
  - id, key, description, timestamps

#### ✅ Additional Schemas
- **TenantFilters**: Filters cho listing tenants
  - status, subscription_tier, search

- **MembershipWithDetails**: Membership với full details

### 2. Repository Classes (`app/modules/tenancy/repository.py`)

#### ✅ TenantRepository

**Methods:**
- `create(db, tenant_data)` → Tenant
  - Check name conflict
  - Raise ConflictError nếu name đã tồn tại

- `get_by_id(db, tenant_id)` → Optional[Tenant]

- `get_by_name(db, name)` → Optional[Tenant]

- `update(db, tenant_id, data)` → Tenant
  - Check name conflict nếu update name
  - Raise NotFoundError nếu không tìm thấy

- `list_all(db, filters, skip, limit)` → List[Tenant]
  - Support filters: status, subscription_tier, search
  - Pagination với skip/limit

#### ✅ UserRepository

**Methods:**
- `create(db, user_data)` → User
  - Check email conflict
  - Raise ConflictError nếu email đã tồn tại

- `get_by_id(db, user_id)` → Optional[User]

- `get_by_email(db, email)` → Optional[User]

- `update(db, user_id, data)` → User
  - Check email conflict nếu update email
  - Raise NotFoundError nếu không tìm thấy

#### ✅ MembershipRepository

**Methods:**
- `create(db, membership_data)` → Membership
  - Check unique constraint (tenant_id, user_id)
  - Raise ConflictError nếu đã tồn tại

- `get_user_memberships(db, user_id)` → List[Membership]
  - Eager load tenant và role

- `get_tenant_members(db, tenant_id, status)` → List[Membership]
  - Optional status filter
  - Eager load user và role

- `get_membership(db, tenant_id, user_id)` → Optional[Membership]
  - Eager load tenant, user, role

- `get_user_permissions(db, tenant_id, user_id)` → Set[str]
  - Get membership → role → permissions
  - Chỉ return permissions nếu membership status = ACTIVE
  - Return Set of permission keys

- `update_membership(db, membership_id, data)` → Membership
  - Update membership fields
  - Raise NotFoundError nếu không tìm thấy

## Usage Examples

### Create Tenant

```python
from app.modules.tenancy.repository import TenantRepository
from app.modules.tenancy.models import TenantStatus

repo = TenantRepository()
tenant = repo.create(db, {
    "name": "Acme Corp",
    "status": TenantStatus.ACTIVE,
    "subscription_tier": "enterprise",
    "features_json": {"risk_engine": True}
})
```

### Create User

```python
from app.modules.tenancy.repository import UserRepository
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

repo = UserRepository()
user = repo.create(db, {
    "email": "admin@acme.com",
    "password_hash": pwd_context.hash("password123"),
    "status": UserStatus.ACTIVE
})
```

### Create Membership

```python
from app.modules.tenancy.repository import MembershipRepository
from app.modules.tenancy.models import MembershipStatus

repo = MembershipRepository()
membership = repo.create(db, {
    "tenant_id": tenant.id,
    "user_id": user.id,
    "role_id": role.id,
    "status": MembershipStatus.ACTIVE
})
```

### Get User Permissions

```python
repo = MembershipRepository()
permissions = repo.get_user_permissions(db, tenant_id, user_id)
# Returns: {'risk:read', 'risk:write', 'audit:read', ...}
```

### List Tenants with Filters

```python
repo = TenantRepository()
tenants = repo.list_all(db, filters={
    "status": TenantStatus.ACTIVE,
    "subscription_tier": "enterprise",
    "search": "Acme"
}, skip=0, limit=10)
```

## Key Features

### ✅ All Repository Methods
- Nhận `db: Session` làm first parameter
- Type hints đầy đủ
- Error handling với NotFoundError và ConflictError
- Eager loading với `joinedload` để tránh N+1 queries

### ✅ Schema Validation
- Email validation với EmailStr
- Password validation (min 8 chars)
- Field length constraints
- Optional fields với defaults

### ✅ Error Handling
- `NotFoundError`: Khi resource không tồn tại
- `ConflictError`: Khi unique constraint violation

### ✅ Performance
- Eager loading cho relationships
- Indexed queries
- Pagination support

## Files Created

1. ✅ `app/modules/tenancy/schemas.py` - All Pydantic schemas
2. ✅ `app/modules/tenancy/repository.py` - All repository classes
3. ✅ `app/modules/tenancy/repository_example.py` - Usage examples

## Next Steps

1. **Create Service Layer**: Business logic layer sử dụng repositories
2. **Create Router**: FastAPI routes sử dụng services
3. **Add Tests**: Unit tests cho repositories và schemas
4. **Add Validation**: Additional business rules validation

**Schemas và Repositories hoàn thành và sẵn sàng sử dụng!** 🎉
