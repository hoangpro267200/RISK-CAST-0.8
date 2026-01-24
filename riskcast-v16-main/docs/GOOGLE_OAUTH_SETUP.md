# Google OAuth Setup Guide

**RISKCAST Auth System - Google OAuth Configuration**

Hướng dẫn thiết lập Google OAuth cho local development và production.

## Prerequisites

- Google Cloud Console account
- Access to create OAuth 2.0 credentials

## Step 1: Create OAuth 2.0 Credentials

1. **Go to Google Cloud Console:**
   - Visit: https://console.cloud.google.com/
   - Select or create a project

2. **Enable Google+ API (if needed):**
   - Navigate to "APIs & Services" > "Library"
   - Search for "Google+ API" or "People API"
   - Click "Enable"

3. **Create OAuth 2.0 Client ID:**
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - If prompted, configure OAuth consent screen first:
     - User Type: External (for testing) or Internal (for G Suite)
     - App name: RISKCAST
     - Support email: your-email@example.com
     - Scopes: `openid`, `email`, `profile`
     - Test users: Add your email for testing

4. **Configure OAuth Client:**
   - Application type: **Web application**
   - Name: RISKCAST Local Dev (or RISKCAST Production)
   - **Authorized redirect URIs:**
     - For local dev: `http://127.0.0.1:8000/api/auth/google/callback`
     - For local dev (alternative): `http://localhost:8000/api/auth/google/callback`
     - For production: `https://yourdomain.com/api/auth/google/callback`

5. **Save Credentials:**
   - Copy the **Client ID** and **Client Secret**
   - Keep these secure (never commit to git)

## Step 2: Configure Environment Variables

Add to your `.env` file in the project root:

```env
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret-here
GOOGLE_REDIRECT_URI=http://127.0.0.1:8000/api/auth/google/callback

# Authentication System (Required)
AUTH_ENABLED=true
SESSION_SECRET=your-session-secret-min-32-chars
```

### Generate Session Secret

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Step 3: Verify Configuration

1. **Check environment variables are loaded:**
   ```bash
   python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('GOOGLE_CLIENT_ID:', os.getenv('GOOGLE_CLIENT_ID')[:20] + '...' if os.getenv('GOOGLE_CLIENT_ID') else 'NOT SET')"
   ```

2. **Start the server:**
   ```bash
   cd riskcast-v16-main
   python -m uvicorn app.main:app --reload
   ```

3. **Test Google OAuth endpoint:**
   ```bash
   curl http://127.0.0.1:8000/api/auth/google/start
   ```
   
   Expected response (when configured):
   ```json
   {
     "ok": true,
     "data": {
       "redirect_url": "https://accounts.google.com/o/oauth2/v2/auth?..."
     }
   }
   ```

## Step 4: Test OAuth Flow

1. **Open login page:**
   - Navigate to: `http://127.0.0.1:8000/login`

2. **Click "Continue with Google":**
   - Should redirect to Google consent screen
   - After consent, redirects back to `/api/auth/google/callback`
   - Backend creates/logs in user and redirects to `/overview` or `/dashboard`

3. **Verify user created:**
   - Check database `users` table
   - Check `oauth_identities` table for linked Google account

## Troubleshooting

### Error: "Google OAuth is not configured"

**Cause:** Missing environment variables

**Fix:**
1. Check `.env` file exists in project root
2. Verify `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI` are set
3. Restart server after adding variables

### Error: "redirect_uri_mismatch"

**Cause:** Redirect URI in request doesn't match Google Console configuration

**Fix:**
1. Go to Google Cloud Console > Credentials
2. Edit your OAuth 2.0 Client ID
3. Add exact redirect URI: `http://127.0.0.1:8000/api/auth/google/callback`
4. Save and wait 1-2 minutes for changes to propagate

### Error: "invalid_client"

**Cause:** Client ID or Client Secret is incorrect

**Fix:**
1. Double-check `.env` file has correct values
2. Ensure no extra spaces or quotes around values
3. Restart server

### Error: 503 Service Unavailable

**Cause:** `AUTH_ENABLED=false` or missing `SESSION_SECRET`

**Fix:**
1. Set `AUTH_ENABLED=true` in `.env`
2. Set `SESSION_SECRET` (generate with command above)
3. Restart server

## Production Checklist

- [ ] Use HTTPS (required for OAuth in production)
- [ ] Set `COOKIE_SECURE=true` in `.env`
- [ ] Update `GOOGLE_REDIRECT_URI` to production domain
- [ ] Add production redirect URI to Google Console
- [ ] Use strong `SESSION_SECRET` (32+ characters)
- [ ] Enable OAuth consent screen verification (if public app)
- [ ] Test OAuth flow in production environment

## Security Notes

1. **Never commit `.env` file to git** (already in `.gitignore`)
2. **Use different OAuth credentials for dev and production**
3. **Rotate `SESSION_SECRET` periodically**
4. **Monitor OAuth usage in Google Cloud Console**
5. **Whitelist redirect URIs** (already implemented in code)

## Additional Resources

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [OAuth 2.0 Security Best Practices](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-security-topics)
