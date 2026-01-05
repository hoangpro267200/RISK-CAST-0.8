# 🔒 Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| v16.x   | :white_check_mark: |
| v15.x   | :x:                |
| v14.x   | :x:                |

## Security Best Practices

### Environment Variables

1. **Never commit `.env` file to git**
   - The `.env` file is in `.gitignore`
   - Use `.env.example` as template
   - Generate strong secrets for production

2. **Required Environment Variables:**
   ```
   ANTHROPIC_API_KEY=your_key_here
   SESSION_SECRET_KEY=strong_random_secret
   ```

3. **Production Settings:**
   - Set `ENVIRONMENT=production`
   - Set `DEBUG=False`
   - Use strong `SESSION_SECRET_KEY`
   - Restrict `ALLOWED_ORIGINS`

### API Keys

- Store API keys in environment variables only
- Never hardcode API keys in source code
- Rotate keys regularly
- Use different keys for development/production

### Input Validation

- All user inputs are sanitized using `app/core/utils/sanitizer.py`
- SQL injection prevention via parameterized queries (SQLAlchemy ORM)
- XSS prevention via HTML escaping
- Input length limits enforced

### Database Security

- Use parameterized queries (SQLAlchemy ORM handles this)
- Database credentials in environment variables
- Limit database user permissions
- Regular backups

### CORS Configuration

- Configure `ALLOWED_ORIGINS` in `.env`
- **REQUIRED in production**: Must set `ALLOWED_ORIGINS` to your actual domain(s)
- Restrict to specific domains in production
- **NEVER use wildcard `*` in production**
- Example: `ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com`
- In development, defaults to localhost origins

### Session Security

- Use strong `SESSION_SECRET_KEY`
- Sessions expire after inactivity
- HTTPS required in production

## Reporting a Vulnerability

If you discover a security vulnerability, please:

1. **DO NOT** open a public issue
2. Email security concerns to: [your-email@example.com]
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We will respond within 48 hours.

## Security Checklist

- [ ] `.env` file is in `.gitignore` ✅
- [ ] `.env.example` exists with safe placeholders
- [ ] All API keys are in environment variables (no hardcoded keys)
- [ ] `SESSION_SECRET_KEY` is strong and unique (generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
- [ ] `ENVIRONMENT=production` in production
- [ ] `DEBUG=false` in production
- [ ] `ALLOWED_ORIGINS` is restricted to specific domains (REQUIRED in production)
- [ ] HTTPS is enabled in production
- [ ] Database credentials are in environment variables (not hardcoded)
- [ ] Regular security updates applied
- [ ] Input sanitization enabled (all user inputs sanitized)
- [ ] Error messages don't leak sensitive info
- [ ] SQL injection prevention (parameterized queries via SQLAlchemy)
- [ ] XSS prevention (HTML escaping, script tag removal)
- [ ] Sanitizer tests pass (`pytest tests/unit/test_sanitizer_security.py`)

---

**Last Updated:** 2025

