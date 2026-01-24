# Docker Deployment Guide

This guide covers Docker-based deployment for RISKCAST V3.

## Quick Start

### 1. Create Environment File

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Required environment variables:
```bash
# Database
DB_USER=riskcast
DB_PASSWORD=your_secure_password
DB_NAME=riskcast_v3
DB_ROOT_PASSWORD=root_secure_password

# Application
SECRET_KEY=your-secret-key-here
APP_ENV=production
LOG_LEVEL=INFO

# Optional
USE_REDIS=true
REDIS_URL=redis://redis:6379/0
CORS_ORIGINS=https://yourdomain.com
```

### 2. Build and Run

```bash
# Build images
docker-compose build

# Run migrations
docker-compose run --rm migrations

# Start services
docker-compose up -d

# View logs
docker-compose logs -f api
```

### 3. Verify Deployment

```bash
# Check health
curl http://localhost:8000/health

# Check services
docker-compose ps
```

## Development Mode

For local development with hot-reload:

```bash
# Copy override file
cp docker-compose.override.yml.example docker-compose.override.yml

# Start with development settings
docker-compose up
```

This will:
- Enable hot-reload for API changes
- Mount source code as volumes
- Start phpMyAdmin on port 8080
- Start Redis Commander on port 8081

## Production Deployment

### Using Production Override

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Environment Variables

Set production environment variables:

```bash
export SECRET_KEY=$(openssl rand -hex 32)
export DB_PASSWORD=$(openssl rand -base64 32)
export APP_ENV=production
```

### Scaling

```bash
# Scale API workers
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --scale api=3

# Scale background workers
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --scale worker=2
```

## Services

### API Server
- **Port**: 8000
- **Health**: `GET /health`
- **Workers**: 4 (configurable via gunicorn)

### Background Worker
- Processes risk runs asynchronously
- Auto-restarts on failure

### MySQL Database
- **Port**: 3306
- **Data**: Persistent volume `mysql_data`
- **Character Set**: utf8mb4

### Redis (Optional)
- **Port**: 6379
- **Data**: Persistent volume `redis_data`
- Enable with `USE_REDIS=true`

## Health Checks

All services include health checks:
- API: HTTP GET `/health`
- Database: `mysqladmin ping`
- Redis: `redis-cli ping`

## Resource Limits

Default limits (adjustable in docker-compose.yml):
- API: 2 CPU, 2GB RAM
- Worker: 2 CPU, 2GB RAM
- Database: 1 CPU, 1GB RAM
- Redis: 0.5 CPU, 512MB RAM

## Troubleshooting

### Database Connection Issues

```bash
# Check database logs
docker-compose logs db

# Test connection
docker-compose exec db mysql -u riskcast -p riskcast_v3
```

### Migration Issues

```bash
# Run migrations manually
docker-compose run --rm migrations

# Check migration status
docker-compose exec api alembic current
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f worker
```

## Backup and Restore

### Database Backup

```bash
docker-compose exec db mysqldump -u riskcast -p riskcast_v3 > backup.sql
```

### Database Restore

```bash
docker-compose exec -T db mysql -u riskcast -p riskcast_v3 < backup.sql
```

## Security Notes

1. **Never commit `.env` file** - Contains secrets
2. **Use strong passwords** - Generate with `openssl rand -base64 32`
3. **Limit network exposure** - Only expose necessary ports
4. **Regular updates** - Keep base images updated
5. **Non-root user** - Containers run as `appuser`

## Monitoring

Access monitoring tools:
- **phpMyAdmin** (dev): http://localhost:8080
- **Redis Commander** (dev): http://localhost:8081
- **API Health**: http://localhost:8000/health
- **API Docs**: http://localhost:8000/docs
