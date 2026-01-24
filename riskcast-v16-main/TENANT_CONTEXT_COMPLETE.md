# ✅ Tenant Context Resolution - Hoàn Thành

## Đã Tạo Thành Công

### 1. TenantContext Dataclass (`app/shared/dependencies.py`)

```python
@dataclass
class TenantContext:
    tenant_id: str
    user_id: Optional[str]
    membership_id: Optional[str]
    role_names: List[str]
    permissions: Set[str]
    actor_type: str  # 'USER' or 'API_KEY'
    actor_id: str
```

### 2. get_current_user() Dependency

**Features:**
- ✅ Checks `Authorization: Bearer <token>` header for session auth
- ✅ Checks `X-API-Key` header for API key auth
- ✅ Validates session token using AuthService
- ✅ Validates API key using AuthService
- ✅ Stores actor info in `request.state`
- ✅ Returns User instance or None
- ✅ Raises UnauthorizedError if invalid

**Flow:**
1. Check Authorization header → validate session token
2. Check X-API-Key header → validate API key
3. Store actor_type and actor_id in request.state
4. Return User (or None for API key auth)

### 3. resolve_tenant_context() Dependency

**For Session Auth:**
1. ✅ Read `X-Tenant-Id` header
2. ✅ Validate tenant exists
3. ✅ Get user's membership in tenant
4. ✅ Validate membership is ACTIVE
5. ✅ Load permissions from membership role
6. ✅ Get role names

**For API Key Auth:**
1. ✅ Get tenant from API key
2. ✅ Get permissions from API key scopes
3. ✅ No user or membership

**Storage:**
- ✅ Stores context in `request.state.tenant_context`
- ✅ Stores individual fields: `tenant_id`, `user_id`, `permissions`, etc.

### 4. Helper Dependencies

#### ✅ require_tenant()
- Dependency that ensures tenant context is resolved
- Returns TenantContext
- Raises errors if context cannot be resolved

#### ✅ require_user()
- Dependency that requires authenticated user
- Returns User instance
- Raises UnauthorizedError if not authenticated

#### ✅ require_permission(permission: str)
- Dependency factory that requires specific permission
- Checks permission in context.permissions
- Raises ForbiddenError if permission not present

#### ✅ get_tenant_context(request)
- Helper function to get context from request state
- Useful when not using dependency injection

## Usage Examples

### Basic Endpoint with Tenant Context

```python
from fastapi import APIRouter, Depends
from app.shared.dependencies import TenantContext, require_tenant

router = APIRouter()

@router.get("/endpoint")
async def my_endpoint(
    context: TenantContext = Depends(require_tenant())
):
    return {
        "tenant_id": context.tenant_id,
        "user_id": context.user_id,
        "permissions": list(context.permissions)
    }
```

### Endpoint Requiring Permission

```python
from app.shared.dependencies import require_permission

@router.get("/risk-assessments")
async def get_risk_assessments(
    context: TenantContext = Depends(require_permission("risk:read"))
):
    # User has risk:read permission
    return {"assessments": []}
```

### Endpoint with User Authentication

```python
from app.shared.dependencies import require_user
from app.modules.tenancy.models import User

@router.get("/profile")
async def get_profile(
    user: User = Depends(require_user())
):
    return {"user_id": user.id, "email": user.email}
```

### Access Context from Request State

```python
from fastapi import Request
from app.shared.dependencies import get_tenant_context

@router.get("/endpoint")
async def my_endpoint(request: Request):
    context = get_tenant_context(request)
    if context:
        return {"tenant_id": context.tenant_id}
```

## Authentication Methods

### Session Auth (Bearer Token)

**Request:**
```
Authorization: Bearer <JWT_TOKEN>
X-Tenant-Id: <tenant_id>
```

**Flow:**
1. Validate JWT token → get User
2. Read X-Tenant-Id header
3. Get user's membership in tenant
4. Load permissions from role
5. Create TenantContext

### API Key Auth

**Request:**
```
X-API-Key: sk_live_<key>
```

**Flow:**
1. Validate API key → get ApiKey and Tenant
2. Get permissions from API key scopes
3. Create TenantContext (no user/membership)

## Request State

After `resolve_tenant_context()` is called, `request.state` contains:

- `tenant_id`: Tenant ID
- `user_id`: User ID (None for API key auth)
- `membership_id`: Membership ID (None for API key auth)
- `actor_type`: 'USER' or 'API_KEY'
- `actor_id`: Actor identifier
- `permissions`: Set of permission strings
- `tenant_context`: Full TenantContext object

## Error Handling

### UnauthorizedError
- No authentication provided
- Invalid token/key
- Expired token/key

### ForbiddenError
- User not member of tenant
- Membership not active
- Missing required permission

### NotFoundError
- Tenant not found
- Membership not found

## Files Created/Updated

1. ✅ `app/shared/dependencies.py` - Complete tenant context resolution
2. ✅ `app/shared/dependencies_example.py` - Usage examples
3. ✅ `TENANT_CONTEXT_COMPLETE.md` - Documentation

## Integration Points

### With Audit Ledger
```python
# In route handler
context = get_tenant_context(request)
await audit_service.log_event(
    tenant_id=context.tenant_id,
    actor_type=context.actor_type,
    actor_id=context.actor_id,
    action="risk_assessment.created",
    ...
)
```

### With Permission Checks
```python
# Using dependency
@router.post("/risk-assessments")
async def create_assessment(
    context: TenantContext = Depends(require_permission("risk:write"))
):
    # User has risk:write permission
    ...
```

## Next Steps

1. **Create Middleware**: Auto-resolve tenant context for all requests
2. **Add Caching**: Cache permissions for performance
3. **Add Logging**: Log tenant context resolution
4. **Add Metrics**: Track tenant context resolution performance

**Tenant Context Resolution hoàn thành và sẵn sàng sử dụng!** 🎉
