# RISKCAST Auth System - Implementation Plan

**Date**: 2025-01-27  
**Status**: Phase 0 - Discovery Complete

---

## 📊 Current Architecture

### Tech Stack
- **Backend**: FastAPI (Python 3.x)
- **Frontend**: React 18.3 + TypeScript + Vite
- **Database**: MySQL (with SQLite fallback) via SQLAlchemy ORM
- **Session**: Starlette SessionMiddleware (already configured)
- **Existing Auth Utilities**: JWT helpers in `app/core/utils/auth.py` (for API keys, not user auth)

### Project Structure
```
riskcast-v16-main/
├── app/
│   ├── main.py              # FastAPI app entry
│   ├── models/              # SQLAlchemy models
│   │   ├── base.py         # Base schema classes
│   │   ├── api_key.py      # API key model (exists)
│   │   └── shipment.py     # Shipment model (exists)
│   ├── database/           # DB connection & session
│   ├── core/utils/auth.py  # JWT utilities (exists, for API keys)
│   ├── routers/            # API routers (to be created)
│   └── config/             # Configuration
├── src/                    # React frontend
│   ├── App.tsx             # Main app (path-based routing)
│   ├── pages/              # Page components
│   └── components/         # Reusable components
└── tests/                  # Test directory
```

### Existing Routes
- `/` - Home page (home.html template)
- `/input_react` - React Input page
- `/results` - React Results page
- `/overview` - Overview page (redirects to /summary)
- `/api/*` - API endpoints

### Database Setup
- **ORM**: SQLAlchemy 2.0+
- **Connection**: `app/config/database.py` (MySQL) + `app/database/__init__.py` (SQLite fallback)
- **Session Factory**: `SessionLocal` available via `get_db()` dependency
- **Base Model**: `app.models.Base` (declarative_base)

---

## 🔍 Existing Auth Analysis

### What Exists
1. **JWT Utilities** (`app/core/utils/auth.py`):
   - `create_jwt()` - Create JWT tokens
   - `verify_jwt()` - Verify JWT tokens
   - `require_auth` decorator - Protect routes
   - Uses `SECRET_KEY` from environment
   - **Purpose**: Currently used for API key authentication, not user auth

2. **Session Middleware** (`app/main.py`):
   - Starlette SessionMiddleware configured
   - Uses `SESSION_SECRET_KEY` from environment
   - Currently stores shipment data in session

3. **API Key Model** (`app/models/api_key.py`):
   - Full API key management system
   - Scopes, expiration, revocation
   - **Not related to user authentication**

### What's Missing
- ❌ User model (email, password_hash, etc.)
- ❌ Session model (for tracking active sessions)
- ❌ Password reset token model
- ❌ Auth API endpoints (`/api/auth/*`)
- ❌ Frontend auth state management
- ❌ Protected route components
- ❌ Login/signup UI
- ❌ Account overview page

---

## 🎯 Auth Flow Design

### Authentication Method Decision: **Cookie-Based Sessions**

**Decision**: Use **HttpOnly Cookie Sessions** instead of JWT in localStorage.

**Reasoning**:
1. ✅ **Security**: HttpOnly cookies prevent XSS attacks (tokens not accessible to JavaScript)
2. ✅ **CSRF Protection**: Can use SameSite=Lax/Strict + CSRF tokens
3. ✅ **Session Management**: Easy to revoke sessions server-side
4. ✅ **Existing Infrastructure**: Starlette SessionMiddleware already configured
5. ✅ **SaaS Best Practice**: Most modern SaaS apps use cookie sessions
6. ✅ **No localStorage Pollution**: Tokens stored securely in cookies

**Alternative Considered**: JWT in localStorage
- ❌ Vulnerable to XSS attacks
- ❌ Harder to revoke (requires token blacklist)
- ❌ Larger payload size

### Auth Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    AUTHENTICATION FLOW                        │
└─────────────────────────────────────────────────────────────┘

1. SIGNUP
   User → POST /api/auth/signup → Create User → Set Session Cookie → Redirect

2. LOGIN
   User → POST /api/auth/login → Verify Credentials → Create Session → Set Cookie → Redirect

3. PROTECTED ROUTE ACCESS
   User → GET /results → Check Session Cookie → Valid? → Allow Access
                                              → Invalid? → Redirect to /?next=/results

4. LOGOUT
   User → POST /api/auth/logout → Revoke Session → Clear Cookie → Redirect to /

5. PASSWORD RESET
   User → POST /api/auth/forgot-password → Generate Token → Email (dev: console)
   User → GET /reset-password?token=xxx → Verify Token → Show Form
   User → POST /api/auth/reset-password → Update Password → Invalidate Token
```

### Session Management

**Session Model**:
- `id` (primary key)
- `token_hash` (SHA-256 of session token)
- `user_id` (foreign key to User)
- `expires_at` (datetime)
- `revoked_at` (nullable datetime)
- `user_agent` (string)
- `ip_address` (string)
- `created_at` (datetime)

**Session Token**:
- Generated: `secrets.token_urlsafe(32)` (43 chars)
- Stored in cookie: `session_token` (HttpOnly, Secure, SameSite=Lax)
- Hashed in DB: SHA-256 hash for lookup

**Session Lifecycle**:
1. Login → Create session record → Set cookie (7 days default)
2. Each request → Verify cookie → Check session in DB → Refresh if needed
3. Logout → Mark session as revoked → Clear cookie
4. Expired → Auto-cleanup via background task

---

## 🗄️ Database Schema

### User Model
```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)  # Argon2 hash
    name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)  # Future: email verification
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### Session Model
```python
class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True)
    token_hash = Column(String(64), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    revoked_at = Column(DateTime, nullable=True)
    user_agent = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    created_at = Column(DateTime, default=datetime.utcnow)
```

### PasswordResetToken Model
```python
class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    
    id = Column(Integer, primary_key=True)
    token_hash = Column(String(64), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

## 🔐 Security Requirements

### Password Hashing
- **Algorithm**: Argon2id (via `argon2-cffi`)
- **Reason**: Winner of Password Hashing Competition, resistant to GPU attacks
- **Alternative**: bcrypt (if Argon2 unavailable)

### Rate Limiting
- **Login/Signup**: 5 attempts per 15 minutes per IP
- **Password Reset**: 3 requests per hour per email
- **Implementation**: Use existing `RateLimiterMiddleware` or create auth-specific limiter

### Input Validation
- **Email**: Pydantic EmailStr validator
- **Password**: Min 8 chars, require uppercase, lowercase, number, special char
- **Name**: Max 255 chars, trim whitespace

### Error Messages
- **Generic Errors**: "Invalid email or password" (don't leak email existence)
- **Rate Limit**: "Too many attempts. Please try again later."
- **Validation**: Specific field errors (e.g., "Password must be at least 8 characters")

### Cookie Security
```python
response.set_cookie(
    key="session_token",
    value=session_token,
    httponly=True,           # Prevent XSS
    secure=True,             # HTTPS only (prod)
    samesite="lax",          # CSRF protection
    max_age=604800,          # 7 days
    path="/"
)
```

### CSRF Protection
- **Method**: SameSite=Lax cookies (primary)
- **Future**: CSRF token for state-changing operations (optional)

---

## 📁 File Structure Plan

### Backend Files (New)
```
app/
├── models/
│   └── auth.py                    # User, Session, PasswordResetToken models
├── routers/
│   └── auth.py                    # Auth API endpoints (/api/auth/*)
├── config/
│   └── auth.py                    # Auth configuration (AUTH_ENABLED, etc.)
├── dependencies/
│   └── auth.py                    # get_current_user dependency
└── utils/
    └── password.py                # Password hashing utilities
```

### Frontend Files (New)
```
src/
├── api/
│   └── auth.ts                    # Auth API client functions
├── store/
│   └── authStore.ts               # Zustand auth state (or React Context)
├── components/
│   └── ProtectedRoute.tsx         # Route protection component
├── pages/
│   ├── LoginPage.tsx              # Login form
│   ├── SignupPage.tsx             # Signup form
│   └── Overview.tsx               # Account overview page
└── hooks/
    └── useAuth.ts                 # Auth hook (optional)
```

### Tests
```
tests/
├── test_auth.py                   # Backend auth tests
└── test_auth_frontend.ts           # Frontend auth tests (optional)
```

---

## 🚦 Feature Flag Strategy

### Environment Variables
```env
# Auth Configuration
AUTH_ENABLED=true                   # Master switch
SESSION_SECRET=your-secret-32-chars # Required for sessions
COOKIE_SECURE=false                 # true in production
SESSION_EXPIRE_HOURS=168            # 7 days default

# Route Protection (granular control)
PROTECT_INPUT=false                 # Protect /input_react
PROTECT_RESULTS=false                # Protect /results
INVITE_ONLY=false                   # Require invite code for signup

# Email (optional - dev mode prints to console)
EMAIL_ENABLED=false
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASS=your-api-key
```

### Implementation Pattern
```python
# app/config/auth.py
AUTH_CONFIG = {
    "enabled": env.bool("AUTH_ENABLED", True),
    "protect_input": env.bool("PROTECT_INPUT", False),
    "protect_results": env.bool("PROTECT_RESULTS", False),
    # ...
}

# Usage in routes
if AUTH_CONFIG["enabled"] and AUTH_CONFIG["protect_input"]:
    @router.get("/input_react")
    @require_auth
    async def input_page(...):
        ...
```

---

## ✅ Implementation Checklist

### Phase 1: Backend Auth Core
- [ ] Create `app/models/auth.py` (User, Session, PasswordResetToken)
- [ ] Create `app/utils/password.py` (Argon2 hashing)
- [ ] Create `app/routers/auth.py` (all endpoints)
- [ ] Create `app/dependencies/auth.py` (get_current_user)
- [ ] Create `app/config/auth.py` (configuration)
- [ ] Update `app/main.py` (include auth router)
- [ ] Write `tests/test_auth.py` (all test cases)
- [ ] Run tests - ALL MUST PASS

### Phase 2: Frontend Auth Integration
- [ ] Create `src/api/auth.ts` (API client)
- [ ] Create `src/store/authStore.ts` (state management)
- [ ] Create `src/components/ProtectedRoute.tsx`
- [ ] Update `src/App.tsx` (add auth routing)
- [ ] Create `src/pages/LoginPage.tsx`
- [ ] Create `src/pages/SignupPage.tsx`
- [ ] Update `app/templates/home.html` (conditional login UI)
- [ ] Test: `npm run build` + `npm run typecheck` must pass

### Phase 3: Overview Page
- [ ] Create `src/pages/Overview.tsx` (full UI)
- [ ] Add route in `app/main.py` (serve React app)
- [ ] Implement profile update
- [ ] Implement password change
- [ ] Implement session management
- [ ] Implement account deletion
- [ ] Manual testing checklist

### Phase 4: Wiring & Configuration
- [ ] Create `.env.example` with auth vars
- [ ] Update navigation (user menu)
- [ ] Add route protection logic
- [ ] Test with `AUTH_ENABLED=false` (existing behavior)
- [ ] Test with `AUTH_ENABLED=true` (new auth)

### Phase 5: Verification & Documentation
- [ ] Run all tests
- [ ] Manual test checklist
- [ ] Create `docs/AUTH_SYSTEM.md`
- [ ] Update README with auth setup
- [ ] Create PR summary

---

## 🔄 Migration Strategy

### Backward Compatibility
1. **Default**: `AUTH_ENABLED=false` → Existing behavior preserved
2. **Gradual Rollout**: Enable auth per route (`PROTECT_INPUT`, `PROTECT_RESULTS`)
3. **No Breaking Changes**: All existing routes work without auth by default

### Database Migration
- New tables: `users`, `sessions`, `password_reset_tokens`
- No changes to existing tables
- Migration script: `python init_database.py` (will create new tables)

---

## 📝 Next Steps

1. ✅ **Phase 0 Complete** - Discovery & Planning
2. ⏭️ **Phase 1** - Backend Auth Core (start now)
3. ⏭️ **Phase 2** - Frontend Integration
4. ⏭️ **Phase 3** - Overview Page
5. ⏭️ **Phase 4** - Wiring & Config
6. ⏭️ **Phase 5** - Verification & Docs

---

## 🎯 Success Criteria

- [ ] All tests pass (`pytest tests/test_auth.py`)
- [ ] Frontend builds without errors (`npm run build`)
- [ ] TypeScript checks pass (`npm run typecheck`)
- [ ] Manual test checklist completed
- [ ] Existing routes work with `AUTH_ENABLED=false`
- [ ] New auth works with `AUTH_ENABLED=true`
- [ ] Documentation complete

---

**Ready to proceed to Phase 1: Backend Auth Core** ✅
