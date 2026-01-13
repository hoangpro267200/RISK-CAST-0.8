# RISKCAST Security Guide

## 🔒 Security Features

RISKCAST includes enterprise-grade security features:

### 1. Authentication & Authorization
- **JWT-based authentication** (`app/core/utils/auth.py`)
- Token creation, verification, and refresh
- Route protection decorators

**Usage:**
```python
from app.core.utils.auth import require_auth, create_jwt, verify_jwt

# Protect a route
@router.post("/secure")
@require_auth
async def secure_endpoint(request: Request):
    user_id = request.state.user_id
    return {"user_id": user_id}

# Create a token
token = create_jwt({"user_id": "123", "email": "user@example.com"})

# Verify a token
payload = verify_jwt(token)
```

### 2. Rate Limiting
- **60 requests/minute** for normal endpoints
- **10 requests/minute** for AI endpoints
- Per-IP tracking
- Automatic cleanup

**Usage:**
```python
from app.core.utils.rate_limiter import rate_limit, ai_rate_limit

@router.post("/normal")
@rate_limit(max_requests=60, per_minutes=1)
async def normal_endpoint(request: Request):
    return {"message": "OK"}

@router.post("/ai")
@ai_rate_limit
async def ai_endpoint(request: Request):
    return {"message": "AI response"}
```

### 3. Input Sanitization
- XSS prevention
- SQL injection prevention
- JavaScript injection prevention
- HTML sanitization

**Usage:**
```python
from app.core.utils.sanitizer import sanitize_input

# Sanitize any input
safe_input = sanitize_input(user_input)
sanitized_dict = sanitize_input({"name": "<script>alert('xss')</script>"})
```

### 4. Security Headers
All responses include:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Content-Security-Policy`
- `Strict-Transport-Security` (HTTPS only)

### 5. Error Handling
- Sanitized error messages
- Internal error logging
- No stack traces in production
- Error IDs for tracking

### 6. Audit Logging
- API call logging
- Authentication events
- Security incidents
- Admin actions

**Logs Location:**
- `/logs/audit.log` - All audit events
- `/logs/security.log` - Security events
- `/logs/errors.log` - Application errors

## 🔐 Environment Variables

Create `.env` file (use `.env.example` as template):

```bash
# Required
ANTHROPIC_API_KEY=your_api_key_here
SECRET_KEY=your_secret_key_here

# Security
JWT_EXPIRE_MINUTES=60
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_AI_PER_MINUTE=10

# CORS (comma-separated)
ALLOWED_ORIGINS=http://localhost:8000,https://yoursite.com

# Environment
ENVIRONMENT=production
```

## 🚀 Production Deployment

1. **Set Environment Variables:**
   ```bash
   export ENVIRONMENT=production
   export SECRET_KEY=$(openssl rand -hex 32)
   export ALLOWED_ORIGINS=https://yoursite.com
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r files/requirements.txt
   ```

3. **Verify Security:**
   - No API keys in logs
   - CORS restricted
   - Rate limiting active
   - Security headers present

4. **Monitor Logs:**
   ```bash
   tail -f logs/audit.log
   tail -f logs/security.log
   ```

## 📋 Security Checklist

- [ ] `SECRET_KEY` set and strong (32+ characters)
- [ ] `ANTHROPIC_API_KEY` set in environment
- [ ] `ALLOWED_ORIGINS` restricted to production domains
- [ ] `ENVIRONMENT=production` set
- [ ] HTTPS enabled (for HSTS)
- [ ] Logs directory writable
- [ ] `.env` file not in version control
- [ ] Rate limiting tested
- [ ] Authentication tested
- [ ] Error messages sanitized

## 🔍 Security Testing

Test rate limiting:
```bash
# Should fail after 60 requests
for i in {1..65}; do curl http://localhost:8000/api/test; done
```

Test authentication:
```bash
# Should fail without token
curl http://localhost:8000/api/secure

# Should succeed with token
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/secure
```

Test input sanitization:
```bash
# Should sanitize XSS
curl -X POST http://localhost:8000/api/test \
  -d '{"input": "<script>alert(\"xss\")</script>"}'
```

## 📚 Documentation

- `PHASE_7_SECURITY_HARDENING_REPORT.md` - Full security report
- `.env.example` - Environment variables template

## 🆘 Support

For security issues, check:
1. `/logs/security.log` - Security events
2. `/logs/errors.log` - Application errors
3. `/logs/audit.log` - All audit events





















