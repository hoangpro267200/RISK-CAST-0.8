# Auth System Environment Setup

**RISKCAST Auth System - Phase 4**

## Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# ============================
# Authentication System
# ============================

# Master switch - disable auth entirely (default: false)
AUTH_ENABLED=false

# Session secret (REQUIRED if AUTH_ENABLED=true)
# Generate a strong random secret: python -c "import secrets; print(secrets.token_urlsafe(32))"
SESSION_SECRET=your-secret-key-min-32-chars-change-in-production

# Session expiration (hours, default: 168 = 7 days)
SESSION_EXPIRE_HOURS=168

# Cookie security (set true in production with HTTPS)
COOKIE_SECURE=false
COOKIE_SAMESITE=lax

# Route protection flags (granular control)
PROTECT_INPUT=false
PROTECT_RESULTS=false

# Invite-only mode (future feature)
INVITE_ONLY=false

# Email configuration (optional - dev mode prints to console)
EMAIL_ENABLED=false
# SMTP_HOST=smtp.sendgrid.net
# SMTP_PORT=587
# SMTP_USER=apikey
# SMTP_PASS=your-sendgrid-api-key
# EMAIL_FROM=noreply@riskcast.com

# Google OAuth (optional - for "Continue with Google" login)
# See docs/GOOGLE_OAUTH_SETUP.md for detailed setup instructions
# GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
# GOOGLE_CLIENT_SECRET=your-client-secret
# GOOGLE_REDIRECT_URI=http://127.0.0.1:8000/api/auth/google/callback
```

## Quick Start

### 1. Enable Auth System

```bash
# In .env file
AUTH_ENABLED=true
SESSION_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
```

### 2. Protect Routes (Optional)

```bash
# Protect input page
PROTECT_INPUT=true

# Protect results page
PROTECT_RESULTS=true
```

### 3. Initialize Database

```bash
# Create auth tables
python init_database.py
```

### 4. Start Server

```bash
# Backend
uvicorn app.main:app --reload

# Frontend (in another terminal)
npm run dev
```

## Testing

### Test with Auth Disabled (Default)
```bash
AUTH_ENABLED=false
# All routes work without authentication
```

### Test with Auth Enabled
```bash
AUTH_ENABLED=true
SESSION_SECRET=your-secret-key
# Routes work, but signup/login required if PROTECT_* flags are set
```

## Production Checklist

- [ ] Set `AUTH_ENABLED=true`
- [ ] Generate strong `SESSION_SECRET` (32+ characters)
- [ ] Set `COOKIE_SECURE=true` (requires HTTPS)
- [ ] Set `PROTECT_INPUT=true` and `PROTECT_RESULTS=true` if needed
- [ ] Configure email settings if using password reset
- [ ] Test all auth flows (signup, login, logout, password reset)
