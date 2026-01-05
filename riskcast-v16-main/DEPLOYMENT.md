# 🚀 Deployment Guide

## Prerequisites

- Python 3.9+
- Node.js 18+ (for frontend build)
- MySQL (optional, for database features)
- Environment variables configured

---

## Development Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd riskcast-v16-main
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Backend dependencies
pip install -r requirements.txt

# Development dependencies (optional)
pip install -r requirements-dev.txt
```

### 4. Configure Environment

```bash
# Copy .env.example to .env
cp .env.example .env

# Edit .env and add your API keys
# Required: ANTHROPIC_API_KEY
```

### 5. Run Development Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Access at: `http://localhost:8000`

---

## Production Deployment

### Option 1: Direct Deployment

#### 1. Environment Setup

```bash
# Copy .env.example to .env
cp .env.example .env

# Edit .env and set production values:
# ENVIRONMENT=production
# DEBUG=false
# ANTHROPIC_API_KEY=your_production_key
# SESSION_SECRET_KEY=strong_random_secret_here  # Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
# ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com  # REQUIRED in production
# MC_ITERATIONS=50000  # Production iterations
# CACHE_ENABLED=true
# CACHE_TTL=3600
```

#### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 3. Build Frontend (if using React/Vue)

```bash
npm install
npm run build
```

#### 4. Run with Gunicorn (recommended)

```bash
pip install gunicorn
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Option 2: Docker Deployment (Recommended)

#### 1. Create Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 2. Build and Run

```bash
docker build -t riskcast .
docker run -p 8000:8000 --env-file .env riskcast
```

### Option 3: Cloud Platform (AWS, GCP, Azure)

#### AWS (Elastic Beanstalk / ECS)

1. Create application
2. Configure environment variables
3. Deploy code
4. Configure load balancer

#### GCP (Cloud Run)

```bash
gcloud run deploy riskcast \
  --source . \
  --platform managed \
  --region us-central1 \
  --set-env-vars ENVIRONMENT=production
```

#### Azure (App Service)

1. Create Web App
2. Configure environment variables
3. Deploy via Git or ZIP

---

## Environment Variables

### Required

- `ANTHROPIC_API_KEY` - Anthropic API key for AI features

### Optional

**Application:**
- `ENVIRONMENT` - `development`, `staging`, or `production` (default: `development`)
- `DEBUG` - `true` or `false` (default: `false` in production)
- `HOST` - Server host (default: `0.0.0.0`)
- `PORT` - Server port (default: `8000`)

**Security:**
- `SESSION_SECRET_KEY` - Strong random secret for sessions (REQUIRED in production)
- `ALLOWED_ORIGINS` - Comma-separated list of allowed origins (REQUIRED in production)

**Database:**
- `USE_MYSQL` - Use MySQL for state storage (default: `false`)
- `DATABASE_URL` - Database connection string (if using database)

**Performance:**
- `MC_ITERATIONS` - Monte Carlo iterations for production (default: `50000`)
- `MC_ITERATIONS_DEV` - Monte Carlo iterations for development (default: `5000`)
- `CACHE_ENABLED` - Enable caching (default: `true`)
- `CACHE_TTL` - Cache TTL in seconds (default: `3600`)
- `USE_REDIS` - Use Redis for caching (default: `false`)
- `REDIS_URL` - Redis connection URL (if `USE_REDIS=true`)

**Logging:**
- `LOG_LEVEL` - Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`)

**See `.env.example` for complete list with descriptions.**

---

## Security Checklist

Before deploying to production:

- [ ] `ENVIRONMENT=production`
- [ ] `DEBUG=false`
- [ ] Strong `SESSION_SECRET_KEY` (generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
- [ ] `ALLOWED_ORIGINS` set to your actual domain(s) (REQUIRED - no defaults in production)
- [ ] HTTPS enabled
- [ ] API keys are secure (in `.env`, not hardcoded)
- [ ] `.env` file not committed to git (verify `.gitignore`)
- [ ] `.env.example` exists with safe placeholders
- [ ] Database credentials secure (if using)
- [ ] Input sanitization enabled (default)
- [ ] CORS properly configured
- [ ] Security headers enabled (default)
- [ ] Firewall rules configured
- [ ] Regular backups configured (if using database)
- [ ] Sanitizer tests pass (`pytest tests/unit/test_sanitizer_security.py`)

**See `SECURITY.md` for detailed security guidelines.**

---

## Monitoring

### Logs

Logs are written to `logs/` directory:
- `app.log` - Application logs
- `errors.log` - Error logs
- `api.log` - API logs
- `security.log` - Security events

### Health Check

Check application health:
```bash
curl http://localhost:8000/docs
```

### Metrics

Monitor:
- Response times
- Error rates
- API usage
- Resource usage (CPU, memory)

---

## Troubleshooting

### Server won't start

1. Check Python version: `python --version` (3.9+)
2. Check dependencies: `pip list`
3. Check environment variables: `env | grep RISKCAST`
4. Check logs: `logs/errors.log`

### Port already in use

```bash
# Find process using port 8000
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Kill process or use different port
export PORT=8001
```

### API errors

1. Check API key is set: `echo $ANTHROPIC_API_KEY`
2. Check API key is valid
3. Check logs: `logs/errors.log`
4. Check network connectivity

### Database errors

1. Check database is running
2. Check connection string in `.env`
3. Check database credentials
4. Check database permissions

---

## Scaling

### Horizontal Scaling

- Use load balancer (nginx, AWS ALB, etc.)
- Run multiple instances
- Use session store (Redis) for sessions
- Use shared database

### Vertical Scaling

- Increase server resources (CPU, RAM)
- Optimize code
- Use caching
- Database optimization

---

## Backup

### Application Code

- Use Git for version control
- Regular commits
- Tag releases

### Data (if using database)

- Regular database backups
- Test restore procedures
- Off-site backup storage

---

## Updates

### Updating Application

1. Pull latest code: `git pull`
2. Install dependencies: `pip install -r requirements.txt`
3. Run migrations (if any): `alembic upgrade head`
4. Restart server

### Zero-downtime Deployment

1. Deploy to new instance
2. Health check new instance
3. Switch traffic to new instance
4. Keep old instance as backup
5. Remove old instance after verification

---

## Support

For deployment issues:
- Check logs: `logs/`
- Review documentation
- Check environment variables
- Verify dependencies

---

**Last Updated:** 2025

