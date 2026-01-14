# RISKCAST v17 - Production Deployment Checklist

## Overview

This checklist ensures a smooth, safe deployment of RISKCAST v17 to production.
Complete all items before and after deployment.

---

## 🔒 Pre-Deployment Checklist

### Environment Configuration

- [ ] Production `.env` file configured
- [ ] All secrets rotated (no development secrets in production)
- [ ] `ENVIRONMENT=production` set
- [ ] `DEBUG=false` set
- [ ] `ANTHROPIC_API_KEY` configured (for AI advisor)
- [ ] `REQUEST_SIGNING_SECRET` set (for request signing)
- [ ] `REDIS_URL` configured (for rate limiting)
- [ ] Database connection string updated

### Dependencies

- [ ] `requirements.txt` frozen with exact versions
- [ ] `package-lock.json` committed (frontend)
- [ ] No development dependencies in production
- [ ] All security updates applied
- [ ] Vulnerability scan passed (pip-audit, npm audit)

### Database

- [ ] Database backup created
- [ ] Migrations tested on staging
- [ ] Run migrations: `alembic upgrade head`
- [ ] Indexes created: `python -m app.database.indexes create`
- [ ] Connection pool sized appropriately (default: 5, max: 10)
- [ ] Query performance verified

### Security

- [ ] CSP headers enabled
- [ ] Rate limiting active (verify with test request)
- [ ] API keys generated for production services
- [ ] Request signing configured for sensitive endpoints
- [ ] HTTPS enforced (redirect HTTP → HTTPS)
- [ ] CORS configured correctly (only allowed origins)
- [ ] Secrets not exposed in logs

### Performance

- [ ] Redis connected and operational
- [ ] Caching enabled and tested
- [ ] CDN configured for static assets
- [ ] Service worker registered
- [ ] Bundle size verified (<500KB initial)
- [ ] Images optimized

### Monitoring

- [ ] Prometheus metrics endpoint `/metrics` working
- [ ] Alerts configured (high error rate, latency, etc.)
- [ ] Log aggregation setup (ELK/Datadog/CloudWatch)
- [ ] Error tracking configured (Sentry)
- [ ] Uptime monitoring active (Pingdom/StatusCake)
- [ ] Dashboard created for key metrics

### Testing

- [ ] All unit tests passing: `pytest tests/unit/`
- [ ] All integration tests passing: `pytest tests/integration/`
- [ ] E2E tests passing
- [ ] Load testing completed
- [ ] Security scan completed
- [ ] Performance benchmarks meet targets

### Documentation

- [ ] API documentation updated (`docs/API_V2.md`)
- [ ] Deployment guide updated
- [ ] Runbook created for on-call
- [ ] Changelog updated (`CHANGELOG.md`)
- [ ] Migration guide for v1→v2 users

---

## 🚀 Deployment Steps

### Step 1: Prepare Release

```bash
# 1. Ensure clean state
git status  # Should be clean

# 2. Run final tests
pytest tests/ -v

# 3. Build frontend
cd riskcast-v16-main
npm run build

# 4. Tag release
git tag -a v17.0.0 -m "RISKCAST v17 - Production Excellence"
```

### Step 2: Database Migration

```bash
# 1. Backup database (CRITICAL!)
pg_dump -h $DB_HOST -U $DB_USER -d riskcast > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Run migrations
alembic upgrade head

# 3. Create indexes
python -m app.database.indexes create

# 4. Verify migration
alembic current
```

### Step 3: Deploy Backend

```bash
# Option A: Docker deployment
docker build -t riskcast:v17 .
docker push registry.example.com/riskcast:v17

# Option B: Direct deployment
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Step 4: Deploy Frontend

```bash
# Build is already done in Step 1
# Deploy dist/ folder to CDN or static hosting

# If using nginx
cp -r dist/* /var/www/riskcast/
nginx -s reload
```

### Step 5: Blue-Green Deployment (Recommended)

```bash
# 1. Deploy to "green" environment
kubectl apply -f k8s/deployment-green.yaml

# 2. Verify green is healthy
curl https://green.riskcast.io/health

# 3. Switch traffic
kubectl patch service riskcast -p '{"spec":{"selector":{"version":"green"}}}'

# 4. Monitor for issues (keep blue running)
# ...

# 5. If all good, scale down blue
kubectl scale deployment riskcast-blue --replicas=0
```

---

## ✅ Post-Deployment Verification

### Smoke Tests (Immediate)

Run these tests immediately after deployment:

- [ ] Health check: `curl https://api.riskcast.io/health`
- [ ] Risk analysis works:
  ```bash
  curl -X POST https://api.riskcast.io/api/v1/risk/v2/analyze \
    -H "Content-Type: application/json" \
    -d '{"origin_port":"CNSHA","destination_port":"USLAX","cargo_value":50000}'
  ```
- [ ] AI advisor responds (if applicable)
- [ ] Frontend loads correctly
- [ ] Authentication works
- [ ] Rate limiting active (check headers)

### Metrics Verification (First Hour)

- [ ] Error rate < 0.1%
- [ ] p95 latency < 1s
- [ ] No memory leaks (stable memory usage)
- [ ] Database connections stable
- [ ] Redis connections stable
- [ ] No unusual CPU spikes

### Performance Verification

- [ ] Lighthouse score > 90
- [ ] Web Vitals green (LCP < 2.5s, FID < 100ms, CLS < 0.1)
- [ ] Bundle size < 500KB
- [ ] API response time < 500ms (p95)
- [ ] Cache hit rate > 70%

### 24-Hour Monitoring

- [ ] Continuous error rate monitoring
- [ ] Latency tracking
- [ ] Resource usage trends
- [ ] User feedback (if any issues reported)

---

## 🔙 Rollback Plan

### Quick Rollback (< 5 minutes)

If critical issues are detected:

```bash
# Kubernetes
kubectl rollout undo deployment/riskcast

# Docker
docker stop riskcast-v17
docker start riskcast-v16

# Direct
git checkout v16.x
pip install -r requirements.txt
supervisorctl restart riskcast
```

### Database Rollback

If database migration caused issues:

```bash
# 1. Rollback migration
alembic downgrade -1

# 2. If needed, restore from backup
psql -h $DB_HOST -U $DB_USER -d riskcast < backup_YYYYMMDD_HHMMSS.sql
```

### Rollback Decision Criteria

Rollback immediately if:
- Error rate > 5%
- p95 latency > 5s
- Complete service outage
- Data corruption detected
- Security vulnerability discovered

---

## 📋 Sign-Off

### Approvals Required

| Role | Name | Approved | Date |
|------|------|----------|------|
| Engineering Lead | | ☐ | |
| QA Lead | | ☐ | |
| Product Manager | | ☐ | |
| Security Team | | ☐ | |

### Deployment Record

| Field | Value |
|-------|-------|
| Version | v17.0.0 |
| Deployed By | |
| Deployment Started | |
| Deployment Completed | |
| Rollback Performed | ☐ Yes / ☐ No |
| Notes | |

---

## 📞 Emergency Contacts

| Role | Name | Contact |
|------|------|---------|
| On-Call Engineer | | |
| Engineering Lead | | |
| DevOps | | |
| Database Admin | | |

---

## 📊 Key Metrics Dashboard

After deployment, monitor these dashboards:

1. **System Health**: Error rates, latency, throughput
2. **Infrastructure**: CPU, Memory, Disk, Network
3. **Application**: Risk analyses/hour, AI requests/hour
4. **Business**: Active users, API key usage

---

## 🎉 Success Criteria

The deployment is considered successful when:

✅ All smoke tests pass
✅ Error rate < 0.1% for 24 hours
✅ No critical bugs reported
✅ Performance targets met
✅ All monitoring alerts configured
✅ Documentation updated

---

## Changelog

### v17.0.0 (2026-01)

**New Features:**
- Advanced rate limiting with Redis
- API key authentication system
- Request signing for sensitive operations
- AI advisor streaming responses
- Excel export for recommendations
- Multi-language support (EN, VI, ZH, JA, KO)
- Database indexes for performance

**Improvements:**
- Legacy v1 → v2 adapters for backward compatibility
- Enhanced error handling
- Comprehensive integration tests
- Performance benchmarking suite

**Security:**
- Distributed rate limiting
- API key scoping
- Request signature verification
