# Auth System Fixes Summary

**Date:** 2026-01-21  
**Issues Fixed:** POST /api/auth/signup 500, GET /api/auth/google/start 503

## Root Cause Analysis

### 1. POST /api/auth/signup 500

**Root Causes:**
- ❌ Password validation missing in `SignupRequest` model
- ❌ Password "11111111" (invalid) was being hashed without validation
- ❌ Email exists check returned generic 400 instead of 409
- ❌ Exception handling caught all errors but didn't distinguish validation errors

**Impact:**
- Invalid passwords caused 500 instead of 400
- Users couldn't see specific password requirements
- Email conflicts returned confusing error messages

### 2. GET /api/auth/google/start 503

**Root Causes:**
- ❌ Missing Google OAuth environment variables (GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI)
- ❌ No redirect_uri_override whitelist (security risk: open redirect)
- ❌ Error response format inconsistent

**Impact:**
- Google OAuth button showed 503 error
- UI displayed "Google OAuth is not configured" message
- Potential security vulnerability with redirect_uri_override

## Files Changed

### 1. `app/routers/auth.py`

**Changes:**

1. **Added password validator to SignupRequest:**
   ```python
   @validator("password")
   def validate_password(cls, v):
       is_valid, error = validate_password_strength(v)
       if not is_valid:
           raise ValueError(error)
       return v
   ```

2. **Improved signup endpoint error handling:**
   - Added explicit password validation before hashing
   - Changed email exists error from 400 to 409 (Conflict)
   - Added ValueError handling for Pydantic validation errors
   - Better error messages with specific codes

3. **Added redirect_uri_override whitelist:**
   - New function `_validate_redirect_uri()` to prevent open redirect attacks
   - Only allows `127.0.0.1` and `localhost` on port 8000
   - Returns 400 with clear error if redirect_uri_override is invalid

4. **Improved Google OAuth endpoint:**
   - Better error messages
   - Security validation for redirect_uri_override
   - Consistent response format using `ok()` helper

### 2. `docs/AUTH_ENV_SETUP.md`

**Changes:**
- Added Google OAuth environment variables section
- Added reference to detailed setup guide

### 3. `docs/GOOGLE_OAUTH_SETUP.md` (NEW)

**Content:**
- Step-by-step Google Cloud Console setup
- Environment variable configuration
- Troubleshooting guide
- Production checklist
- Security notes

## Error Response Codes

### Signup Endpoint

| Scenario | Status Code | Error Code | Message |
|----------|-------------|------------|---------|
| Invalid password | 400 | `INVALID_PASSWORD` | Specific validation error |
| Email already exists | 409 | `EMAIL_EXISTS` | "An account with this email already exists" |
| Validation error (Pydantic) | 400 | `VALIDATION_ERROR` | Pydantic error message |
| Server error | 500 | `SIGNUP_FAILED` | Generic error message |

### Google OAuth Endpoint

| Scenario | Status Code | Error Code | Message |
|----------|-------------|------------|---------|
| Auth disabled | 503 | `AUTH_DISABLED` | "Authentication is not enabled" |
| OAuth not configured | 503 | `GOOGLE_OAUTH_NOT_CONFIGURED` | "Google OAuth is not configured..." |
| Invalid redirect URI | 400 | `INVALID_REDIRECT_URI` | "Redirect URI is not allowed..." |
| Success | 200 | - | Returns `{redirect_url: "..."}` |

## Security Improvements

1. **Password Validation:**
   - Enforced at Pydantic model level
   - Requirements: 8+ chars, uppercase, lowercase, number, special char
   - Clear error messages for each requirement

2. **Redirect URI Whitelist:**
   - Only allows `127.0.0.1:8000` and `localhost:8000`
   - Prevents open redirect attacks
   - Validates scheme, hostname, and port

3. **Error Messages:**
   - Generic errors for security-sensitive operations (email enumeration prevention)
   - Specific errors for user input validation

## Testing Checklist

### Manual Testing

#### 1. Signup with Invalid Password

```bash
curl -X POST http://127.0.0.1:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"11111111","name":"Test User"}'
```

**Expected:** 400 with `INVALID_PASSWORD` error

#### 2. Signup with Valid Password

```bash
curl -X POST http://127.0.0.1:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Aa1!aaaa","name":"Test User"}'
```

**Expected:** 201 with user data

#### 3. Signup with Existing Email

```bash
# Run signup twice with same email
curl -X POST http://127.0.0.1:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Aa1!aaaa","name":"Test User"}'
```

**Expected:** 409 with `EMAIL_EXISTS` error

#### 4. Google OAuth Start (Without Config)

```bash
curl http://127.0.0.1:8000/api/auth/google/start
```

**Expected:** 503 with `GOOGLE_OAUTH_NOT_CONFIGURED` error

#### 5. Google OAuth Start (With Config)

```bash
# After setting GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI
curl http://127.0.0.1:8000/api/auth/google/start
```

**Expected:** 200 with `{redirect_url: "https://accounts.google.com/..."}`

#### 6. Google OAuth Start (Invalid Redirect URI)

```bash
curl "http://127.0.0.1:8000/api/auth/google/start?redirect_uri_override=http://evil.com/callback"
```

**Expected:** 400 with `INVALID_REDIRECT_URI` error

### Frontend Testing

1. **Signup Page:**
   - [ ] Enter invalid password → See specific error message
   - [ ] Enter valid password → Signup succeeds, redirects to `/overview`
   - [ ] Enter existing email → See "Email already exists" error
   - [ ] Form validation shows password requirements

2. **Google OAuth:**
   - [ ] Click "Continue with Google" → Redirects to Google consent screen
   - [ ] After consent → Redirects back to app, user logged in
   - [ ] Without config → Shows "Google OAuth is not configured" message

## Environment Setup

### Required Variables

```env
AUTH_ENABLED=true
SESSION_SECRET=<generate-with-secrets-token-urlsafe-32>

# Optional: Google OAuth
GOOGLE_CLIENT_ID=<from-google-console>
GOOGLE_CLIENT_SECRET=<from-google-console>
GOOGLE_REDIRECT_URI=http://127.0.0.1:8000/api/auth/google/callback
```

### Generate Session Secret

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Next Steps

1. ✅ Password validation added
2. ✅ Email conflict handling improved
3. ✅ Google OAuth security hardened
4. ✅ Error messages standardized
5. ⏳ Add integration tests (optional)
6. ⏳ Add E2E tests with Playwright (optional)

## References

- [Google OAuth Setup Guide](./GOOGLE_OAUTH_SETUP.md)
- [Auth Environment Setup](./AUTH_ENV_SETUP.md)
- [Password Validation Rules](../app/utils/password.py)
