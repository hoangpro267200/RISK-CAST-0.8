# 🐳 RiskCast Docker Configuration

## Overview

Production-ready Docker configuration for RiskCast with multi-stage builds, security best practices, and complete orchestration.

---

## Quick Start

### Development Environment

```bash
# 1. Copy environment file
cp .env.example .env

# 2. Start development services
docker-compose -f docker-compose.dev.yml up -d

# 3. Run migrations
docker-compose -f docker-compose.dev.yml exec api alembic upgrade head

# 4. Access services
# API:              http://localhost:8000
# API Docs:         http://localhost:8000/docs
# Adminer:          http://localhost:8080
# Redis Commander:  http://localhost:8081
# Mailhog:          http://localhost:8025
```

### Production Environment

```bash
# 1. Configure .env with production values
cp .env.example .env
nano .env

# 2. Build production images
docker-compose build

# 3. Start services
docker-compose up -d

# 4. Run migrations
docker-compose exec api alembic upgrade head

# 5. Check health
curl http://localhost:8000/health/live
```

---

## Architecture

### Production Stack

```
┌─────────────────────────────────────────┐
│           Nginx (Optional)              │
│      Reverse Proxy & Load Balancer     │
└──────────────┬──────────────────────────┘
               │
    ┌──────────┴──────────┐
    │                     │
┌───▼────┐          ┌─────▼────┐
│  API   │          │  Worker  │
│ (x4)   │          │  (x1)    │
└───┬────┘          └─────┬────┘
    │                     │
    └──────────┬──────────┘
               │
    ┌──────────┴──────────┐
    │                     │
┌───▼──────┐      ┌───────▼────┐
│PostgreSQL│      │   Redis    │
│   15     │      │     7      │
└──────────┘      └────────────┘
```

### Services

| Service | Container | Port | Purpose |
|---------|-----------|------|---------|
| **api** | riskcast-api | 8000 | FastAPI application |
| **worker** | riskcast-worker | - | Background job processing |
| **scheduler** | riskcast-scheduler | - | Scheduled tasks (cron) |
| **postgres** | riskcast-postgres | 5432 | Primary database |
| **redis** | riskcast-redis | 6379 | Cache & message queue |
| **nginx** | riskcast-nginx | 80/443 | Reverse proxy (optional) |

---

## Docker Files

### Dockerfile (Production)

**Multi-stage build:**
- **Stage 1 (builder):** Compile dependencies in virtual environment
- **Stage 2 (production):** Minimal runtime image with non-root user

**Features:**
- ✅ Multi-stage build (smaller final image)
- ✅ Non-root user (security)
- ✅ Virtual environment isolation
- ✅ Health checks
- ✅ dumb-init for signal handling
- ✅ Minimal runtime dependencies

**Image size:** ~200MB (vs ~1GB without multi-stage)

### Dockerfile.dev (Development)

**Single-stage build with:**
- ✅ Hot reload (uvicorn --reload)
- ✅ Development tools (pytest, ipython, debuggers)
- ✅ Volume mounting for live code updates
- ✅ PostgreSQL client for debugging

---

## Configuration Files

### docker-compose.yml (Production)

**Services:**
1. **api** - Main API server (4 workers)
2. **worker** - Background job processor
3. **scheduler** - Cron job scheduler
4. **postgres** - PostgreSQL 15
5. **redis** - Redis 7
6. **nginx** - Reverse proxy (optional, use profile)

**Features:**
- Health checks for all services
- Resource limits (CPU, memory)
- Restart policies
- Volume persistence
- Network isolation
- Dependency ordering

### docker-compose.dev.yml (Development)

**Additional services:**
- **adminer** - Database management UI (port 8080)
- **redis-commander** - Redis management UI (port 8081)
- **mailhog** - Email testing (port 8025)

**Features:**
- Volume mounting for live reload
- Debug mode enabled
- Test API keys
- Simplified configuration

---

## Resource Limits

### API Service

| Resource | Limit | Reservation |
|----------|-------|-------------|
| CPU | 2 cores | 0.5 cores |
| Memory | 2GB | 512MB |

### Worker Service

| Resource | Limit |
|----------|-------|
| CPU | 1 core |
| Memory | 1GB |

### Database (PostgreSQL)

| Resource | Limit |
|----------|-------|
| CPU | 2 cores |
| Memory | 4GB |

### Redis

| Resource | Limit |
|----------|-------|
| CPU | 1 core |
| Memory | 1GB |
| Max Memory Policy | allkeys-lru |
| Max Memory | 512MB |

---

## Environment Variables

### Required Variables

```bash
# Database
POSTGRES_USER=riskcast
POSTGRES_PASSWORD=strong-password
POSTGRES_DB=riskcast
DATABASE_URL=postgresql://user:pass@postgres:5432/dbname

# Redis
REDIS_URL=redis://redis:6379

# Security
SECRET_KEY=your-secret-key

# External APIs
TOMORROW_IO_API_KEY=your-key
MARINE_TRAFFIC_API_KEY=your-key
PROJECT44_API_KEY=your-key
```

### Optional Variables

```bash
# Application
ENVIRONMENT=production
LOG_LEVEL=INFO
API_PORT=8000

# AWS
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
S3_BUCKET=riskcast-bucket

# Worker
WORKER_CONCURRENCY=4
```

---

## Helper Scripts

### scripts/docker.sh

**Production Commands:**
```bash
./scripts/docker.sh build          # Build images
./scripts/docker.sh up             # Start services
./scripts/docker.sh down           # Stop services
./scripts/docker.sh restart        # Restart services
./scripts/docker.sh logs [service] # View logs
./scripts/docker.sh migrate        # Run migrations
./scripts/docker.sh shell          # Open API shell
./scripts/docker.sh db-shell       # Open DB shell
```

**Development Commands:**
```bash
./scripts/docker.sh dev-up         # Start dev environment
./scripts/docker.sh dev-test       # Run tests
./scripts/docker.sh dev-migrate    # Run migrations
./scripts/docker.sh dev-db-reset   # Reset database
```

**Maintenance Commands:**
```bash
./scripts/docker.sh backup-db      # Create DB backup
./scripts/docker.sh restore-db     # Restore from backup
./scripts/docker.sh cleanup        # Clean Docker resources
./scripts/docker.sh health         # Check health
```

---

## Health Checks

### API Health Check

```bash
# Endpoint
GET /health/live

# Docker health check
CMD: curl -f http://localhost:8000/health/live || exit 1

# Intervals
- interval: 30s
- timeout: 10s
- start_period: 60s
- retries: 3
```

### PostgreSQL Health Check

```bash
CMD: pg_isready -U riskcast -d riskcast
- interval: 10s
- timeout: 5s
- retries: 5
```

### Redis Health Check

```bash
CMD: redis-cli ping
- interval: 10s
- timeout: 5s
- retries: 5
```

---

## Security Features

### 1. Non-Root User

```dockerfile
# Create user with UID 1000
RUN groupadd --gid 1000 riskcast && \
    useradd --uid 1000 --gid riskcast --shell /bin/bash riskcast

# Switch to non-root user
USER riskcast
```

### 2. Minimal Image

- Based on `python:3.11-slim`
- Only runtime dependencies in final stage
- No build tools in production image

### 3. Read-Only Filesystems

```yaml
# Example for extra security
security_opt:
  - no-new-privileges:true
read_only: true
tmpfs:
  - /tmp
  - /app/tmp
```

### 4. Network Isolation

```yaml
networks:
  riskcast-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16
```

### 5. Secret Management

- Use Docker secrets (production)
- Environment variables (development)
- Never commit .env files

---

## Volumes

### Persistent Volumes

| Volume | Purpose | Size Estimate |
|--------|---------|---------------|
| postgres-data | Database storage | 10-100GB |
| redis-data | Cache persistence | 1-5GB |
| api-logs | Application logs | 1-10GB |
| worker-logs | Worker logs | 1-5GB |

### Backup Strategy

```bash
# Create backup
./scripts/docker.sh backup-db

# Backup location
./backup_YYYYMMDD_HHMMSS.sql

# Restore backup
./scripts/docker.sh restore-db backup_file.sql
```

---

## Monitoring

### Container Stats

```bash
# Real-time stats
docker stats

# Specific service
docker stats riskcast-api
```

### Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api

# Last 100 lines
docker-compose logs --tail=100 api
```

### Health Status

```bash
# Check all services
docker-compose ps

# Health endpoint
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
```

---

## Troubleshooting

### Issue: Container won't start

```bash
# Check logs
docker-compose logs api

# Check if port is already in use
lsof -i :8000

# Force recreate
docker-compose up -d --force-recreate api
```

### Issue: Database connection failed

```bash
# Check if PostgreSQL is healthy
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Test connection
docker-compose exec api psql $DATABASE_URL
```

### Issue: Out of disk space

```bash
# Check disk usage
docker system df

# Clean up
docker system prune -f

# Clean everything (careful!)
docker system prune -af --volumes
```

### Issue: Slow performance

```bash
# Check resource usage
docker stats

# Increase limits in docker-compose.yml
deploy:
  resources:
    limits:
      cpus: '4'
      memory: 4G
```

---

## Development Workflow

### 1. Start Development Environment

```bash
# Start all services
docker-compose -f docker-compose.dev.yml up -d

# Check status
docker-compose -f docker-compose.dev.yml ps
```

### 2. Code Changes

- Edit code on host machine
- Changes automatically detected (hot reload)
- No need to rebuild container

### 3. Run Tests

```bash
# All tests
docker-compose -f docker-compose.dev.yml exec api pytest

# Specific test
docker-compose -f docker-compose.dev.yml exec api pytest tests/unit/test_risk_engine.py -v

# With coverage
docker-compose -f docker-compose.dev.yml exec api pytest --cov=app
```

### 4. Database Migrations

```bash
# Create migration
docker-compose -f docker-compose.dev.yml exec api alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose -f docker-compose.dev.yml exec api alembic upgrade head

# Rollback
docker-compose -f docker-compose.dev.yml exec api alembic downgrade -1
```

### 5. Shell Access

```bash
# Python shell
docker-compose -f docker-compose.dev.yml exec api python

# IPython shell
docker-compose -f docker-compose.dev.yml exec api ipython

# Bash shell
docker-compose -f docker-compose.dev.yml exec api bash
```

---

## Production Deployment

### 1. Build Images

```bash
# Build with specific version
VERSION=1.0.0 docker-compose build

# Tag for registry
docker tag riskcast-api:1.0.0 registry.example.com/riskcast-api:1.0.0
```

### 2. Push to Registry

```bash
# Push to Docker Hub
docker push registry.example.com/riskcast-api:1.0.0

# Or use docker-compose
docker-compose push
```

### 3. Deploy

```bash
# Pull latest images
docker-compose pull

# Start services
docker-compose up -d

# Run migrations
docker-compose exec api alembic upgrade head

# Verify
curl http://localhost:8000/health/live
```

### 4. Zero-Downtime Deployment

```bash
# Scale up new version
docker-compose up -d --scale api=8

# Health check new instances
# ...

# Scale down old version
docker-compose up -d --scale api=4

# Or use rolling update
docker-compose up -d --no-deps --build api
```

---

## Performance Optimization

### 1. Use Build Cache

```bash
# Build with cache
docker-compose build

# Build without cache (when needed)
docker-compose build --no-cache
```

### 2. Multi-Stage Build Benefits

- **Build stage:** ~800MB
- **Final stage:** ~200MB
- **Savings:** 75% smaller image

### 3. Resource Allocation

```yaml
# Optimize based on workload
api:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 2G
      reservations:
        cpus: '1'
        memory: 1G
```

---

## Best Practices

### 1. Always Use .dockerignore

Reduces build context size and speeds up builds.

### 2. Use Specific Image Tags

```yaml
# Good
image: postgres:15-alpine

# Bad
image: postgres:latest
```

### 3. Implement Health Checks

Ensures services are actually ready before routing traffic.

### 4. Set Resource Limits

Prevents one service from consuming all resources.

### 5. Use Non-Root Users

Improves security by running containers with minimal privileges.

### 6. Keep Images Small

- Multi-stage builds
- Minimal base images
- Clean up in same layer

### 7. Version Everything

- Image tags
- docker-compose version
- Dependencies

---

**Version:** 1.0.0  
**Date:** 2026-01-24  
**Status:** ✅ Production Ready
