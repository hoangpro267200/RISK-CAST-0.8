# RISKCAST Authentication & Authorization System

## Overview

RISKCAST implements a production-grade authentication system designed for enterprise security requirements. The system uses **session-based authentication** with secure cookies as the primary mechanism, with support for **API key authentication** for service-to-service communication.

### Architecture Decision: Session-Based vs JWT

We chose **session-based authentication** over JWT for several reasons:

1. **Revocability**: Sessions can be instantly revoked (logout, security incident)
2. **Security**: Tokens aren't exposed to JavaScript (HttpOnly cookies)
3. **Simplicity**: No token refresh complexity on the client
4. **Control**: Server maintains full control over session lifecycle

For mobile apps or external API clients, **API keys** provide stateless authentication.

## Trust Boundaries

```
┌─────────────────────────────────────────────────────────────┐
│                         CLIENT                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Browser   │  │  Mobile App │  │  Service    │         │
│  │  (Session)  │  │  (API Key)  │  │  (API Key)  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                           │
                    HTTPS + Cookies
                    or API Key Header
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      API GATEWAY                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  Rate Limiting                       │   │
│  │                  CORS Validation                     │   │
│  │                  CSRF Protection                     │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    AUTH MIDDLEWARE                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  Session    │  │  API Key    │  │  Permission │         │
│  │  Validation │  │  Validation │  │  Check      │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    APPLICATION                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Protected Resources                     │   │
│  │              Business Logic                          │   │
│  │              Data Access                             │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Authentication Flows

### 1. User Registration (Signup)

```
Client                    Server                    Database
  │                         │                          │
  │  POST /api/auth/signup  │                          │
  │  {email, password, name}│                          │
  │─────────────────────────>                          │
  │                         │                          │
  │                         │  Validate password       │
  │                         │  strength                │
  │                         │                          │
  │                         │  Check email unique      │
  │                         │─────────────────────────>│
  │                         │<─────────────────────────│
  │                         │                          │
  │                         │  Hash password (Argon2id)│
  │                         │                          │
  │                         │  Create user             │
  │                         │─────────────────────────>│
  │                         │                          │
  │                         │  Create session          │
  │                         │─────────────────────────>│
  │                         │                          │
  │                         │  Generate verification   │
  │                         │  token (if EMAIL_ENABLED)│
  │                         │                          │
  │  Set-Cookie: session    │                          │
  │  Set-Cookie: csrf_token │                          │
  │  {user data}            │                          │
  │<─────────────────────────                          │
```

### 2. User Login

```
Client                    Server                    Database
  │                         │                          │
  │  POST /api/auth/login   │                          │
  │  {email, password}      │                          │
  │─────────────────────────>                          │
  │                         │                          │
  │                         │  Check rate limit        │
  │                         │  (IP + email)            │
  │                         │                          │
  │                         │  Find user by email      │
  │                         │─────────────────────────>│
  │                         │<─────────────────────────│
  │                         │                          │
  │                         │  Verify password         │
  │                         │  (constant time)         │
  │                         │                          │
  │                         │  Check account status    │
  │                         │  (active, not locked)    │
  │                         │                          │
  │                         │  Create session          │
  │                         │─────────────────────────>│
  │                         │                          │
  │                         │  Update last_login       │
  │                         │─────────────────────────>│
  │                         │                          │
  │  Set-Cookie: session    │                          │
  │  Set-Cookie: csrf_token │                          │
  │  {user data}            │                          │
  │<─────────────────────────                          │
```

### 3. Session Validation (Every Request)

```
Client                    Server                    Database
  │                         │                          │
  │  GET /api/protected     │                          │
  │  Cookie: session_token  │                          │
  │  Cookie: csrf_token     │                          │
  │  X-CSRF-Token: <token>  │                          │
  │─────────────────────────>                          │
  │                         │                          │
  │                         │  Extract session cookie  │
  │                         │                          │
  │                         │  Hash token, lookup      │
  │                         │─────────────────────────>│
  │                         │<─────────────────────────│
  │                         │                          │
  │                         │  Check session valid     │
  │                         │  - Not revoked           │
  │                         │  - Not expired (idle)    │
  │                         │  - Not expired (absolute)│
  │                         │                          │
  │                         │  Verify CSRF token       │
  │                         │  (for state-changing ops)│
  │                         │                          │
  │                         │  Load user               │
  │                         │─────────────────────────>│
  │                         │<─────────────────────────│
  │                         │                          │
  │                         │  Check user active       │
  │                         │                          │
  │                         │  Refresh idle timeout    │
  │                         │  (throttled, every 5 min)│
  │                         │                          │
  │  {response data}        │                          │
  │<─────────────────────────                          │
```

### 4. Session Refresh (Token Rotation)

```
Client                    Server                    Database
  │                         │                          │
  │  POST /api/auth/refresh │                          │
  │  Cookie: session_token  │                          │
  │  X-CSRF-Token: <token>  │                          │
  │─────────────────────────>                          │
  │                         │                          │
  │                         │  Validate current session│
  │                         │─────────────────────────>│
  │                         │<─────────────────────────│
  │                         │                          │
  │                         │  Revoke old session      │
  │                         │  (reason: "rotated")     │
  │                         │─────────────────────────>│
  │                         │                          │
  │                         │  Create new session      │
  │                         │  (link to old via        │
  │                         │   rotated_from_id)       │
  │                         │─────────────────────────>│
  │                         │                          │
  │  Set-Cookie: session    │                          │
  │  Set-Cookie: csrf_token │                          │
  │  {user data}            │                          │
  │<─────────────────────────                          │
```

### 5. Password Reset Flow

```
Client                    Server                    Database           Email
  │                         │                          │                │
  │  POST /forgot-password  │                          │                │
  │  {email}                │                          │                │
  │─────────────────────────>                          │                │
  │                         │                          │                │
  │                         │  Find user (don't reveal │                │
  │                         │  if exists)              │                │
  │                         │─────────────────────────>│                │
  │                         │<─────────────────────────│                │
  │                         │                          │                │
  │                         │  Create reset token      │                │
  │                         │  (1 hour expiry)         │                │
  │                         │─────────────────────────>│                │
  │                         │                          │                │
  │                         │  Send email              │                │
  │                         │─────────────────────────────────────────>│
  │                         │                          │                │
  │  "If email exists..."   │                          │                │
  │<─────────────────────────                          │                │
  │                         │                          │                │
  │  Click link in email    │                          │                │
  │                         │                          │                │
  │  POST /reset-password   │                          │                │
  │  {token, new_password}  │                          │                │
  │─────────────────────────>                          │                │
  │                         │                          │                │
  │                         │  Validate token          │                │
  │                         │─────────────────────────>│                │
  │                         │<─────────────────────────│                │
  │                         │                          │                │
  │                         │  Hash new password       │                │
  │                         │                          │                │
  │                         │  Update password         │                │
  │                         │  Mark token used         │                │
  │                         │─────────────────────────>│                │
  │                         │                          │                │
  │  "Password reset"       │                          │                │
  │<─────────────────────────                          │                │
```

## Token Lifecycle

### Session Tokens

| Property | Value | Description |
|----------|-------|-------------|
| Format | `secrets.token_urlsafe(32)` | 256 bits of entropy |
| Storage | SHA-256 hash in DB | Never store plaintext |
| Delivery | HttpOnly cookie | XSS protection |
| Idle Timeout | 48 hours (configurable) | Sliding window |
| Absolute Timeout | 30 days (configurable) | Maximum lifetime |
| Rotation | On refresh | Detect token reuse |

### Password Reset Tokens

| Property | Value | Description |
|----------|-------|-------------|
| Format | `secrets.token_urlsafe(32)` | 256 bits of entropy |
| Storage | SHA-256 hash in DB | Never store plaintext |
| Delivery | Email link | User verification |
| Expiry | 1 hour | Short-lived for security |
| Usage | Single-use | Marked used after reset |

### API Keys

| Property | Value | Description |
|----------|-------|-------------|
| Format | `rk_live_<random>` | Prefixed for identification |
| Storage | SHA-256 hash in DB | Only prefix visible |
| Delivery | Header (Authorization/X-API-Key) | Secure transmission |
| Expiry | Configurable | Optional expiration |
| Revocation | Immediate | Can be revoked anytime |
| Scopes | read/write/admin/webhook/service | Permission levels |

## Security Features

### Password Hashing

- **Algorithm**: Argon2id (memory-hard, GPU-resistant)
- **Fallback**: bcrypt (if Argon2 unavailable)
- **Parameters**:
  - Time cost: 2 iterations
  - Memory cost: 64 MB
  - Parallelism: 4 threads
  - Hash length: 32 bytes
  - Salt length: 16 bytes

### Password Policy

- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- At least one special character

### Rate Limiting

| Endpoint | Limit | Window | Lockout |
|----------|-------|--------|---------|
| Login | 5 attempts | 15 min | 15 min |
| Password Reset | 3 requests | 60 min | 60 min |
| Signup | 5 attempts | 60 min | 60 min |
| API (Free) | 30 req/min | 1 min | N/A |
| API (Pro) | 500 req/min | 1 min | N/A |

### CSRF Protection

- Double-submit cookie pattern
- CSRF token bound to session
- Origin/Referer validation
- Required for all state-changing operations

## Frontend Integration

### Login Flow

```typescript
// Login
const response = await fetch('/api/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  credentials: 'include', // IMPORTANT: Include cookies
  body: JSON.stringify({ email, password }),
});

// Response sets session_token and csrf_token cookies automatically
const user = await response.json();
```

### Making Authenticated Requests

```typescript
// Get CSRF token from cookie
function getCsrfToken(): string {
  const match = document.cookie.match(/csrf_token=([^;]+)/);
  return match ? match[1] : '';
}

// Authenticated request
const response = await fetch('/api/protected', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRF-Token': getCsrfToken(), // Required for POST/PUT/DELETE
  },
  credentials: 'include',
  body: JSON.stringify(data),
});
```

### Session Refresh

```typescript
// Refresh session (recommended before critical operations)
async function refreshSession() {
  const response = await fetch('/api/auth/refresh', {
    method: 'POST',
    headers: {
      'X-CSRF-Token': getCsrfToken(),
    },
    credentials: 'include',
  });
  
  if (!response.ok) {
    // Session expired, redirect to login
    window.location.href = '/login';
  }
}
```

### Logout

```typescript
async function logout() {
  await fetch('/api/auth/logout', {
    method: 'POST',
    headers: {
      'X-CSRF-Token': getCsrfToken(),
    },
    credentials: 'include',
  });
  
  // Redirect to login
  window.location.href = '/login';
}
```

## API Key Usage

### Creating an API Key

```bash
curl -X POST https://api.riskcast.com/api/auth/keys \
  -H "Cookie: session_token=<your_session>" \
  -H "X-CSRF-Token: <csrf_token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Production API Key", "scope": "read"}'
```

Response:
```json
{
  "data": {
    "id": 1,
    "name": "Production API Key",
    "key": "rk_live_abc123...",  // Only shown ONCE!
    "key_prefix": "rk_live_",
    "scope": "read",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

### Using an API Key

```bash
# Via Authorization header
curl https://api.riskcast.com/api/v3/risk/assess \
  -H "Authorization: Bearer rk_live_abc123..."

# Via X-API-Key header
curl https://api.riskcast.com/api/v3/risk/assess \
  -H "X-API-Key: rk_live_abc123..."
```

## Role-Based Access Control

### Built-in Roles

| Role | Level | Description |
|------|-------|-------------|
| `user` | 0 | Standard user |
| `operator` | 1 | Can perform operations |
| `analyst` | 2 | Can view and analyze data |
| `underwriter` | 3 | Can make underwriting decisions |
| `admin` | 4 | Tenant administrator |
| `super_admin` | 5 | Platform administrator |

### Permission Checking

```python
from app.dependencies.auth import require_role, require_permission, UserRole

# Require specific role
@router.get("/admin")
async def admin_only(user = Depends(require_role(UserRole.ADMIN))):
    ...

# Require specific permission
@router.get("/risk")
async def risk_read(ctx = Depends(require_permission("risk:read"))):
    ...
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AUTH_ENABLED` | No | `false` (dev), `true` (prod) | Enable authentication |
| `SESSION_SECRET` | **Yes (prod)** | Generated (dev) | Session signing key |
| `SESSION_EXPIRE_HOURS` | No | 48 | Idle timeout |
| `SESSION_ABSOLUTE_HOURS` | No | 720 | Absolute timeout |
| `COOKIE_SECURE` | No | `true` (prod) | HTTPS-only cookies |
| `COOKIE_SAMESITE` | No | `strict` (prod) | SameSite policy |
| `REDIS_URL` | No | - | Redis for rate limiting |
| `EMAIL_ENABLED` | No | `false` | Enable email sending |
| `SMTP_HOST` | If email | - | SMTP server |

## Database Schema

### auth_users

```sql
CREATE TABLE auth_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid VARCHAR(36) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    status VARCHAR(20) DEFAULT 'active',
    role VARCHAR(20) DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE,
    last_login_at DATETIME,
    last_login_ip VARCHAR(45),
    failed_login_count INTEGER DEFAULT 0,
    locked_until DATETIME,
    tenant_id VARCHAR(36),
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    deleted_at DATETIME
);

CREATE INDEX idx_auth_user_email ON auth_users(email);
CREATE INDEX idx_auth_user_status ON auth_users(status, role);
```

### auth_sessions

```sql
CREATE TABLE auth_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token_hash VARCHAR(64) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL REFERENCES auth_users(id),
    expires_at DATETIME NOT NULL,
    absolute_expires_at DATETIME,
    revoked_at DATETIME,
    revoke_reason VARCHAR(128),
    csrf_token_hash VARCHAR(64),
    last_seen_at DATETIME,
    user_agent VARCHAR(500),
    ip_address VARCHAR(45),
    created_at DATETIME NOT NULL
);

CREATE INDEX idx_session_token ON auth_sessions(token_hash);
CREATE INDEX idx_session_user ON auth_sessions(user_id, expires_at);
```

## Security Checklist

- [ ] `SESSION_SECRET` is set and ≥32 characters
- [ ] `AUTH_ENABLED=true` in production
- [ ] `COOKIE_SECURE=true` in production
- [ ] `COOKIE_SAMESITE=strict` in production
- [ ] HTTPS enforced for all traffic
- [ ] Rate limiting configured (Redis recommended)
- [ ] Audit logging enabled
- [ ] Password policy enforced
- [ ] Session rotation on privilege change
- [ ] All tokens stored as hashes
- [ ] CSRF protection on all forms
- [ ] Error messages don't leak information

## Troubleshooting

### Common Issues

1. **"Not authenticated" error**
   - Check session cookie is being sent (`credentials: 'include'`)
   - Verify session hasn't expired
   - Check `AUTH_ENABLED` is true

2. **"CSRF_INVALID" error**
   - Include `X-CSRF-Token` header
   - Token must match `csrf_token` cookie
   - Check SameSite cookie policy

3. **Session lost on refresh**
   - Ensure cookies are set with correct domain
   - Check `COOKIE_SECURE` matches protocol (HTTPS)

4. **Rate limit exceeded**
   - Wait for lockout period
   - Check Redis connection for distributed limiting
