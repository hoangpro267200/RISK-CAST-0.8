# ✅ Tenancy Service - Hoàn Thành

## Đã Tạo Thành Công

### 1. Custom Exceptions (`app/modules/tenancy/exceptions.py`)

#### ✅ TenantNotFoundError
- Kế thừa từ `NotFoundError`
- Error code: `TENANT_NOT_FOUND`

#### ✅ TenantAlreadyExistsError
- Kế thừa từ `ConflictError`
- Error code: `TENANT_ALREADY_EXISTS`

#### ✅ MembershipNotFoundError
- Kế thừa từ `NotFoundError`
- Error code: `MEMBERSHIP_NOT_FOUND`
- Support tenant_id và user_id trong message

#### ✅ InvalidMembershipError
- Kế thừa từ `RISKCASTException`
- Error code: `INVALID_MEMBERSHIP`
- Status code: 400 Bad Request

#### ✅ Additional Exceptions
- `UserNotFoundError` - User not found
- `RoleNotFoundError` - Role not found

### 2. TenantService (`app/modules/tenancy/service.py`)

#### ✅ create_tenant(data, creator_user_id)
- Validate name uniqueness
- Create tenant
- Create initial admin membership nếu creator_user_id provided
- Placeholder cho audit event
- Raises: `TenantAlreadyExistsError`, `UserNotFoundError`, `RoleNotFoundError`

#### ✅ get_tenant(tenant_id)
- Get tenant với validation
- Raises: `TenantNotFoundError`

#### ✅ update_tenant(tenant_id, data)
- Update với validation
- Check name conflict nếu update name
- Placeholder cho audit event
- Raises: `TenantNotFoundError`, `TenantAlreadyExistsError`

#### ✅ suspend_tenant(tenant_id, reason)
- Change status to SUSPENDED
- Log warning với reason
- Placeholder cho audit event
- Raises: `TenantNotFoundError`

#### ✅ activate_tenant(tenant_id)
- Activate suspended tenant
- Change status to ACTIVE
- Raises: `TenantNotFoundError`

### 3. MembershipService (`app/modules/tenancy/service.py`)

#### ✅ add_member(tenant_id, user_id, role_id)
- Validate tenant, user, role exist
- Check membership không tồn tại
- Create membership với status ACTIVE
- Placeholder cho audit event
- Raises: `TenantNotFoundError`, `UserNotFoundError`, `RoleNotFoundError`, `InvalidMembershipError`

#### ✅ remove_member(tenant_id, user_id)
- Get membership
- Delete membership
- Placeholder cho audit event
- Raises: `MembershipNotFoundError`

#### ✅ change_role(tenant_id, user_id, new_role_id)
- Get membership
- Validate new role exists
- Update role_id
- Placeholder cho audit event
- Raises: `MembershipNotFoundError`, `RoleNotFoundError`

#### ✅ get_user_permissions(tenant_id, user_id)
- Validate tenant và user exist
- Get permissions từ repository
- Return Set[str] of permission keys
- Raises: `TenantNotFoundError`, `UserNotFoundError`

#### ✅ update_membership_status(tenant_id, user_id, status)
- Update membership status
- Support ACTIVE, INVITED, SUSPENDED
- Raises: `MembershipNotFoundError`

## Key Features

### ✅ Async Methods
- Tất cả service methods là async
- Chuẩn bị cho future async operations (audit events, notifications)

### ✅ Validation
- Validate tất cả entities trước khi operations
- Clear error messages

### ✅ Error Handling
- Custom exceptions với error codes
- Proper HTTP status codes
- Detailed error messages

### ✅ Logging
- Log tất cả important operations
- Log warnings cho suspensions
- Log errors cho failures

### ✅ Audit Events (Placeholder)
- TODO comments cho audit events
- Ready để integrate với audit module

### ✅ Business Logic
- Initial admin membership creation
- Status management
- Role changes với validation

## Usage Examples

### Create Tenant with Admin

```python
from app.modules.tenancy.service import TenantService
from app.modules.tenancy.schemas import TenantCreate

service = TenantService(db)
tenant_data = TenantCreate(
    name="Acme Corp",
    subscription_tier="enterprise"
)

tenant = await service.create_tenant(tenant_data, creator_user_id="user_123")
```

### Suspend Tenant

```python
service = TenantService(db)
tenant = await service.suspend_tenant("tenant_id", reason="Payment overdue")
```

### Add Member

```python
from app.modules.tenancy.service import MembershipService

service = MembershipService(db)
membership = await service.add_member(
    tenant_id="tenant_123",
    user_id="user_456",
    role_id="role_789"
)
```

### Get User Permissions

```python
service = MembershipService(db)
permissions = await service.get_user_permissions("tenant_123", "user_456")
# Returns: {'risk:read', 'risk:write', 'audit:read', ...}
```

### Change Role

```python
service = MembershipService(db)
membership = await service.change_role(
    tenant_id="tenant_123",
    user_id="user_456",
    new_role_id="role_new"
)
```

## Error Handling

### TenantNotFoundError
```python
try:
    tenant = await service.get_tenant("invalid_id")
except TenantNotFoundError as e:
    print(f"Error: {e.detail}")  # "Tenant not found: invalid_id"
```

### TenantAlreadyExistsError
```python
try:
    tenant = await service.create_tenant(tenant_data)
except TenantAlreadyExistsError as e:
    print(f"Error: {e.detail}")  # "Tenant with name 'Acme' already exists"
```

### InvalidMembershipError
```python
try:
    membership = await service.add_member(tenant_id, user_id, role_id)
except InvalidMembershipError as e:
    print(f"Error: {e.detail}")  # "User xyz is already a member of tenant abc"
```

## Files Created

1. ✅ `app/modules/tenancy/exceptions.py` - Custom exceptions
2. ✅ `app/modules/tenancy/service.py` - TenantService và MembershipService
3. ✅ `app/modules/tenancy/service_example.py` - Usage examples

## Next Steps

1. **Create Router**: FastAPI routes sử dụng services
2. **Add Audit Integration**: Implement audit event emission
3. **Add Tests**: Unit tests cho services
4. **Add Notifications**: Email notifications cho membership changes

**Service layer hoàn thành và sẵn sàng sử dụng!** 🎉
