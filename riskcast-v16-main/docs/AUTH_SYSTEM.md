# RISKCAST Auth System Documentation

**Version**: 1.0  
**Date**: 2025-01-27  
**Status**: Production Ready ✅

---

## 📋 Overview

Complete authentication system for RISKCAST with user management, session handling, and account security features.

---

## 🏗️ Architecture

### Authentication Method: **Cookie-Based Sessions**

**Decision**: HttpOnly Cookie Sessions (not JWT in localStorage)

**Why**:
- ✅ **Security**: HttpOnly cookies prevent XSS attacks
- ✅ **CSRF Protection**: SameSite=Lax cookies + future CSRF tokens
- ✅ **Session Management**: Easy server-side revocation
- ✅ **SaaS Best Practice**: Industry standard for web apps
- ✅ **Existing Infrastructure**: Starlette SessionMiddleware already configured

### Flow Diagram

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

---

## 🔌 API Endpoints

### Authentication Endpoints

| Method | Path | Auth Required | Description |
|--------|------|---------------|-------------|
| POST | `/api/auth/signup` | No | Register new user |
| POST | `/api/auth/login` | No | Authenticate user |
| POST | `/api/auth/logout` | No | Log out current user |
| GET | `/api/auth/me` | Yes | Get current user profile |
| PATCH | `/api/auth/me` | Yes | Update user profile (name) |
| POST | `/api/auth/change-password` | Yes | Change password |
| POST | `/api/auth/forgot-password` | No | Request password reset token |
| POST | `/api/auth/reset-password` | No | Reset password with token |
| POST | `/api/auth/logout-all` | Yes | Revoke all user sessions |
| GET | `/api/auth/sessions` | Yes | List active sessions |
| DELETE | `/api/auth/sessions/{id}` | Yes | Revoke specific session |

### Request/Response Examples

#### Signup
```bash
POST /api/auth/signup
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!@#",
  "name": "John Doe"
}

Response: 201 Created
{
  "id": 1,
  "email": "user@example.com",
  "name": "John Doe",
  "is_active": true,
  "email_verified": false,
  "created_at": "2025-01-27T10:00:00Z"
}
# Sets session_token cookie
```

#### Login
```bash
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!@#"
}

Response: 200 OK
{
  "id": 1,
  "email": "user@example.com",
  "name": "John Doe",
  "is_active": true,
  "email_verified": false,
  "created_at": "2025-01-27T10:00:00Z"
}
# Sets session_token cookie
```

#### Get Current User
```bash
GET /api/auth/me
Cookie: session_token=xxx

Response: 200 OK
{
  "id": 1,
  "email": "user@example.com",
  "name": "John Doe",
  "is_active": true,
  "email_verified": false,
  "created_at": "2025-01-27T10:00:00Z"
}
```

---

## 🔐 Security Features

### Password Security
- **Hashing**: Argon2id (preferred) or bcrypt (fallback)
- **Validation**: Minimum 8 characters, requires uppercase, lowercase, number, special character
- **Storage**: Only hashed passwords stored (never plain text)

### Session Security
- **Token Generation**: `secrets.token_urlsafe(32)` (43 chars)
- **Storage**: SHA-256 hash in database, plain token in HttpOnly cookie
- **Expiration**: Configurable (default: 7 days)
- **Revocation**: Server-side session revocation supported

### Cookie Security
```python
response.set_cookie(
    key="session_token",
    value=token,
    httponly=True,      # Prevent XSS
    secure=True,        # HTTPS only (prod)
    samesite="lax",     # CSRF protection
    max_age=604800,     # 7 days
    path="/"
)
```

### Rate Limiting
- Uses existing `RateLimiterMiddleware`
- Login/Signup: 5 attempts per 15 minutes per IP
- Password Reset: 3 requests per hour per email

### Error Messages
- **Generic Errors**: "Invalid email or password" (prevents email enumeration)
- **Rate Limit**: "Too many attempts. Please try again later."
- **Validation**: Specific field errors

---

## 📁 File Structure

### Backend Files
```
app/
├── models/
│   └── auth.py                    # User, Session, PasswordResetToken models
├── routers/
│   └── auth.py                    # Auth API endpoints
├── config/
│   └── auth.py                    # Auth configuration
├── dependencies/
│   └── auth.py                    # get_current_user, require_auth
└── utils/
    └── password.py                # Password hashing utilities
```

### Frontend Files
```
src/
├── api/
│   └── auth.ts                    # Auth API client
├── store/
│   └── authStore.tsx              # Auth state management (React Context)
├── components/
│   ├── ProtectedRoute.tsx         # Route protection component
│   └── UserMenu.tsx               # User menu dropdown
├── pages/
│   ├── LoginPage.tsx              # Login form
│   ├── SignupPage.tsx             # Signup form
│   ├── HomePage.tsx               # Home (login/welcome)
│   └── Overview.tsx               # Account management
└── config/
    └── auth.ts                    # Frontend auth config
```

---

## ⚙️ Configuration

### Environment Variables

```env
# Master switch
AUTH_ENABLED=false                 # Set to true to enable auth

# Session configuration
SESSION_SECRET=your-secret-32-chars # REQUIRED if AUTH_ENABLED=true
SESSION_EXPIRE_HOURS=168            # 7 days default
COOKIE_SECURE=false                 # true in production (requires HTTPS)
COOKIE_SAMESITE=lax                 # lax, strict, none

# Route protection (granular control)
PROTECT_INPUT=false                 # Protect /input_react
PROTECT_RESULTS=false               # Protect /results

# Email (optional)
EMAIL_ENABLED=false
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASS=your-api-key
EMAIL_FROM=noreply@riskcast.com
```

### Feature Flags

The auth system is **opt-in** by default:
- `AUTH_ENABLED=false` → All routes work without auth (existing behavior)
- `AUTH_ENABLED=true` → Auth system active, routes protected based on flags

---

## 🚀 Getting Started

### 1. Install Dependencies

```bash
# Backend
pip install argon2-cffi email-validator

# Frontend (already in package.json)
npm install
```

### 2. Configure Environment

```bash
# Copy .env.example to .env
cp .env.example .env

# Edit .env and set:
AUTH_ENABLED=true
SESSION_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
```

### 3. Initialize Database

```bash
# Create auth tables
python init_database.py
```

### 4. Start Application

```bash
# Backend
uvicorn app.main:app --reload

# Frontend (separate terminal)
npm run dev
```

### 5. Test Auth Flow

1. Visit `http://localhost:8000/`
2. Click "Sign up" → Create account
3. Login → Access protected routes
4. Visit `/overview` → Manage account

---

## 🧪 Testing

### Run Backend Tests

```bash
# Set test environment
export AUTH_ENABLED=true
export SESSION_SECRET=test-secret-key-for-testing-only-32-chars-min

# Run tests
pytest tests/test_auth.py -v
```

### Manual Test Checklist

- [ ] Sign up new account
- [ ] Sign in with new account
- [ ] View `/overview` page
- [ ] Change password successfully
- [ ] Sign out
- [ ] Sign in with new password
- [ ] Forgot password flow (check console for token)
- [ ] Reset password with token
- [ ] Protected route redirects to login with `?next=`
- [ ] After login, redirects back to original route
- [ ] Sign out all devices
- [ ] Existing routes (`/results`, `/input_react`) still work with `AUTH_ENABLED=false`

---

## 🔄 Migration Guide

### Enabling Auth for Existing Deployment

1. **Backup Database**: Always backup before changes
2. **Set Environment Variables**: Add auth vars to `.env`
3. **Run Database Migration**: `python init_database.py`
4. **Test with Auth Disabled**: Verify `AUTH_ENABLED=false` works
5. **Enable Auth Gradually**:
   - Set `AUTH_ENABLED=true`
   - Test signup/login
   - Set `PROTECT_INPUT=true` (optional)
   - Set `PROTECT_RESULTS=true` (optional)

### Backward Compatibility

- **Default**: `AUTH_ENABLED=false` → Existing behavior preserved
- **No Breaking Changes**: All existing routes work without auth by default
- **Gradual Rollout**: Enable protection per route as needed

---

## 🛡️ Security Considerations

### Threat Model

1. **XSS Attacks**: Mitigated by HttpOnly cookies
2. **CSRF Attacks**: Mitigated by SameSite=Lax cookies
3. **Session Hijacking**: Mitigated by secure token generation and expiration
4. **Brute Force**: Mitigated by rate limiting
5. **Password Attacks**: Mitigated by Argon2id hashing
6. **Email Enumeration**: Mitigated by generic error messages

### Best Practices

- ✅ Use strong `SESSION_SECRET` (32+ characters, random)
- ✅ Set `COOKIE_SECURE=true` in production (requires HTTPS)
- ✅ Enable rate limiting in production
- ✅ Monitor failed login attempts
- ✅ Rotate session secrets periodically
- ✅ Use email verification in production (future feature)

---

## 📝 API Reference

### User Model

```typescript
interface User {
  id: number;
  email: string;
  name: string | null;
  is_active: boolean;
  email_verified: boolean;
  created_at: string;
}
```

### Session Model

```typescript
interface Session {
  id: number;
  user_id: number;
  expires_at: string;
  user_agent: string | null;
  ip_address: string | null;
  created_at: string;
  is_valid: boolean;
}
```

---

## 🐛 Troubleshooting

### Issue: "Authentication is not enabled"

**Solution**: Set `AUTH_ENABLED=true` in `.env`

### Issue: "SESSION_SECRET must be set"

**Solution**: Generate and set `SESSION_SECRET` in `.env`:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Issue: Cookies not working

**Solution**: 
- Check `COOKIE_SECURE` setting (should be `false` in dev, `true` in prod)
- Verify CORS settings allow credentials
- Check browser console for cookie errors

### Issue: Password reset token not received

**Solution**: 
- Check console output (dev mode prints tokens)
- Verify `EMAIL_ENABLED` and SMTP settings if using email
- Check spam folder

---

## 🔮 Future Enhancements

- [ ] Email verification flow
- [ ] Two-factor authentication (2FA)
- [ ] OAuth integration (Google, GitHub)
- [ ] Account roles and permissions
- [ ] API key management UI
- [ ] Session activity monitoring
- [ ] Password history (prevent reuse)
- [ ] Account lockout after failed attempts

---

## 📚 Related Documentation

- [Auth Implementation Plan](./AUTH_IMPLEMENTATION_PLAN.md)
- [Environment Setup](./AUTH_ENV_SETUP.md)
- [API Documentation](../app/routers/auth.py)

---

## ✅ Phase Completion Status

- ✅ **Phase 1**: Backend Auth Core
- ✅ **Phase 2**: Frontend Auth Integration
- ✅ **Phase 3**: Overview Page
- ✅ **Phase 4**: Wiring & Configuration
- ⏭️ **Phase 5**: Verification & Documentation

---

**Last Updated**: 2025-01-27  
**Maintainer**: RISKCAST Development Team
