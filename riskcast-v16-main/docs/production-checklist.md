# Production Deployment Checklist

## 📋 Table of Contents

- [Pre-Deployment (1 Week Before)](#pre-deployment-1-week-before)
- [Day Before Deployment](#day-before-deployment)
- [Deployment Day](#deployment-day)
- [Post-Deployment](#post-deployment)
- [Rollback Triggers](#rollback-triggers)
- [Emergency Contacts](#emergency-contacts)

---

## 🗓️ Pre-Deployment (1 Week Before)

### Code & Testing

- [ ] **All tests passing**
  ```bash
  pytest tests/ -v --cov=app --cov-fail-under=70
  ```
  - Unit tests: ✅
  - Integration tests: ✅
  - E2E tests: ✅

- [ ] **Code coverage > 70%**
  ```bash
  pytest --cov=app --cov-report=html
  open htmlcov/index.html
  ```

- [ ] **No critical security vulnerabilities**
  ```bash
  bandit -r app/
  safety check
  pip-audit
  ```

- [ ] **Performance tests completed**
  ```bash
  locust -f tests/load/locustfile.py --headless --users 100 --spawn-rate 10
  ```

- [ ] **Load testing passed**
  - Target: Handle 500 req/s with p95 < 2s
  - Database: No slow queries (< 1s)
  - Memory: No leaks over 4 hour test

### Documentation

- [ ] **API documentation updated**
  - OpenAPI spec current
  - Postman collection updated
  - Example requests documented

- [ ] **Runbooks created/updated**
  - [ ] Incident response
  - [ ] Scaling procedures
  - [ ] Debugging guide
  - [ ] Disaster recovery

- [ ] **Architecture docs current**
  - System diagram updated
  - Component descriptions current
  - Integration points documented

- [ ] **Change log updated**
  - New features documented
  - Breaking changes noted
  - Migration steps included

### Infrastructure

- [ ] **Production environment provisioned**
  - [ ] Kubernetes cluster running
  - [ ] Namespaces created
  - [ ] Network policies configured
  - [ ] Ingress controller setup

- [ ] **Database sized appropriately**
  - Instance class: db.r6g.xlarge (or as needed)
  - Storage: 250 GB (with auto-scaling)
  - Max connections: 200+
  - Backup retention: 30 days

- [ ] **Redis cluster configured**
  - Node type: cache.r6g.large (or as needed)
  - Replicas: 2+
  - Memory: 8 GB+
  - Encryption enabled

- [ ] **CDN configured** (if applicable)
  - CloudFront distribution created
  - SSL certificate provisioned
  - Cache policies configured

- [ ] **Monitoring setup**
  - [ ] Prometheus deployed
  - [ ] Grafana dashboards configured
  - [ ] AlertManager rules set
  - [ ] Slack notifications configured

---

## 📅 Day Before Deployment

### Final Checks

- [ ] **Staging deployment successful**
  ```bash
  kubectl get pods -n riskcast-staging
  kubectl rollout status deployment/riskcast-api -n riskcast-staging
  ```

- [ ] **Smoke tests passing in staging**
  ```bash
  ./scripts/smoke-test.sh https://staging.api.riskcast.io
  ```

- [ ] **Database backup verified**
  ```bash
  python scripts/dr/restore.py --list
  # Verify latest backup < 24 hours old
  ```

- [ ] **Rollback plan documented**
  ```
  # Create rollback-plan.md:
  - Current production version: [git SHA]
  - Previous stable version: [git SHA]
  - Rollback command: kubectl rollout undo deployment/riskcast-api
  - Database rollback: alembic downgrade -1
  - Expected rollback time: 5 minutes
  ```

### Communication

- [ ] **Team notified of deployment window**
  ```
  #engineering:
  "🚀 Production deployment scheduled for [DATE] at [TIME]
  
  What: v[VERSION] - [Brief description]
  When: [DATE] [TIME] UTC
  Duration: ~30 minutes
  Deployer: @[name]
  Backup: @[name]
  
  Deployment doc: [link]
  Rollback plan: [link]"
  ```

- [ ] **Support team briefed**
  - New features explained
  - Known issues shared
  - Escalation path confirmed

- [ ] **Status page prepared**
  ```bash
  curl -X POST https://api.statuspage.io/v1/pages/PAGE_ID/incidents \
    -H "Authorization: OAuth TOKEN" \
    -d '{
      "incident": {
        "name": "Planned Deployment",
        "status": "scheduled",
        "scheduled_for": "2026-01-27T14:00:00Z",
        "scheduled_until": "2026-01-27T14:30:00Z",
        "body": "We will be deploying v1.5.0 with new features",
        "impact_override": "none"
      }
    }'
  ```

- [ ] **Customer communication ready** (if major changes)
  - Email draft prepared
  - In-app notification ready
  - Documentation updated

---

## 🚀 Deployment Day

### Pre-Deployment (T-1 hour)

- [ ] **Verify production backup < 1 hour old**
  ```bash
  python scripts/dr/backup.py --type full
  python scripts/dr/restore.py --list | head -3
  ```

- [ ] **Check monitoring dashboards**
  - Error rate: Normal (< 1%)
  - Response time p95: Normal (< 1s)
  - CPU usage: Normal (< 70%)
  - Memory usage: Normal (< 80%)
  - Database connections: Normal (< 80%)

- [ ] **Confirm team availability**
  - Primary deployer: ✅
  - Backup engineer: ✅
  - On-call engineer: ✅
  - Database admin: ✅ (on standby)

- [ ] **Silence non-critical alerts**
  ```bash
  # In AlertManager, create silence for 1 hour
  # Severity: warning
  # Comment: "Planned deployment"
  ```

- [ ] **Create deployment tracking issue**
  ```
  Title: Production Deployment v[VERSION] - [DATE]
  
  ## Checklist
  - [ ] Pre-deployment checks
  - [ ] Database migrations
  - [ ] Application deployment
  - [ ] Smoke tests
  - [ ] Monitoring verification
  - [ ] Communication
  
  ## Timeline
  - T-1h: Pre-checks
  - T-0: Begin deployment
  - T+10m: Migrations complete
  - T+20m: Deployment complete
  - T+30m: Verification complete
  ```

### Deployment (T-0)

#### Step 1: Database Migrations (T+0 to T+10m)

- [ ] **Run migration pre-checks**
  ```bash
  python scripts/db/check_migrations.py
  ```

- [ ] **Create pre-migration backup**
  ```bash
  python scripts/db/backup.py
  ```

- [ ] **Apply migrations**
  ```bash
  # Using migration script (with locking)
  python scripts/db/migrate.py
  
  # Or directly with alembic
  alembic upgrade head
  ```

- [ ] **Verify migrations applied**
  ```bash
  alembic current
  python scripts/db/check_migrations.py
  ```

- [ ] **Test critical queries**
  ```sql
  -- Test that new columns/tables exist
  SELECT * FROM quotes LIMIT 1;
  SELECT * FROM new_table LIMIT 1;
  ```

#### Step 2: Deploy Application (T+10m to T+20m)

- [ ] **Deploy new version**
  ```bash
  # Via GitHub Actions (preferred)
  git tag v1.5.0
  git push origin v1.5.0
  
  # Or via kubectl
  kubectl set image deployment/riskcast-api \
    riskcast-api=ghcr.io/riskcast/riskcast-api:v1.5.0 \
    -n riskcast-prod
  ```

- [ ] **Monitor rollout**
  ```bash
  kubectl rollout status deployment/riskcast-api -n riskcast-prod --watch
  ```

- [ ] **Verify pods are healthy**
  ```bash
  kubectl get pods -n riskcast-prod -l app=riskcast-api
  kubectl wait --for=condition=ready pod -l app=riskcast-api -n riskcast-prod --timeout=300s
  ```

- [ ] **Check pod logs for errors**
  ```bash
  kubectl logs -n riskcast-prod -l app=riskcast-api --tail=50 | grep -i error
  ```

#### Step 3: Smoke Tests (T+20m to T+25m)

- [ ] **Run automated smoke tests**
  ```bash
  ./scripts/smoke-test.sh https://api.riskcast.io
  ```

- [ ] **Test critical endpoints manually**
  ```bash
  # Health checks
  curl https://api.riskcast.io/health/ready
  curl https://api.riskcast.io/health/live
  
  # API endpoints
  curl -H "Authorization: Bearer $TOKEN" https://api.riskcast.io/api/v3/quotes/
  curl -H "Authorization: Bearer $TOKEN" https://api.riskcast.io/api/v3/risk/analyze
  
  # Metrics
  curl https://api.riskcast.io/metrics | grep riskcast_
  ```

- [ ] **Test new features**
  - [Feature 1]: ✅
  - [Feature 2]: ✅
  - [Feature 3]: ✅

### Post-Deployment (T+30min)

#### Monitor (T+30m to T+120m)

- [ ] **Monitor error rates** (first 30 minutes)
  ```bash
  # Check error rate every 5 minutes
  watch -n 300 'kubectl logs -n riskcast-prod -l app=riskcast-api --since=5m | grep ERROR | wc -l'
  ```
  - T+5m: Error count: _____
  - T+10m: Error count: _____
  - T+15m: Error count: _____
  - T+30m: Error count: _____

- [ ] **Check response times** (first 30 minutes)
  ```bash
  kubectl logs -n riskcast-prod -l app=riskcast-api --since=5m | \
    jq -r 'select(.duration) | .duration' | \
    awk '{sum+=$1; n++; if($1>max) max=$1} END {print "Avg:", sum/n, "Max:", max}'
  ```
  - T+5m: Avg: ___s, Max: ___s
  - T+15m: Avg: ___s, Max: ___s
  - T+30m: Avg: ___s, Max: ___s

- [ ] **Verify all endpoints working**
  ```bash
  # Run comprehensive endpoint test
  python scripts/test-endpoints.py --all
  ```

- [ ] **Review application logs**
  ```bash
  kubectl logs -n riskcast-prod -l app=riskcast-api --tail=100
  ```
  - No critical errors: ✅
  - No unexpected warnings: ✅
  - Request processing normal: ✅

- [ ] **Check database performance**
  ```sql
  -- Check for slow queries
  SELECT pid, now() - query_start AS duration, query 
  FROM pg_stat_activity 
  WHERE state = 'active' 
    AND query_start < NOW() - INTERVAL '5 seconds'
  ORDER BY duration DESC;
  
  -- Check connection count
  SELECT count(*) FROM pg_stat_activity;
  ```

- [ ] **Verify monitoring metrics**
  - CPU usage normal
  - Memory usage stable
  - No disk space issues
  - Network traffic normal

#### Completion (T+2 hours)

- [ ] **Update status page**
  ```bash
  curl -X PATCH https://api.statuspage.io/v1/pages/PAGE_ID/incidents/INCIDENT_ID \
    -H "Authorization: OAuth TOKEN" \
    -d '{"incident":{"status":"completed"}}'
  ```

- [ ] **Notify team of completion**
  ```
  #engineering:
  "✅ Production deployment v[VERSION] completed successfully
  
  - Duration: [actual time]
  - Issues: None
  - Status: All systems operational
  
  Monitoring for next 24 hours. Please report any issues to @oncall"
  ```

- [ ] **Document any issues**
  - Issue 1: [description] - Resolved: [how]
  - Issue 2: [description] - Resolved: [how]

- [ ] **Re-enable alerts**
  ```bash
  # Remove silence in AlertManager
  ```

- [ ] **Close deployment tracking issue**
  - Mark all checklist items complete
  - Add final notes
  - Close issue

---

## 🔴 Rollback Triggers

**Initiate rollback immediately if:**

| Trigger | Threshold | Action |
|---------|-----------|--------|
| **Error rate spike** | > 5% for 5 minutes | Rollback deployment |
| **P95 latency spike** | > 5 seconds for 5 minutes | Rollback deployment |
| **Critical functionality broken** | Any critical endpoint down | Rollback deployment |
| **Database issues** | Connection pool exhausted | Rollback migrations + deployment |
| **Pod crashloop** | > 50% pods failing | Rollback deployment |
| **Memory leak** | OOMKilled pods | Rollback deployment |
| **Data corruption** | Detected data issues | STOP, investigate, possibly rollback migrations |

### Rollback Procedure

```bash
# 1. Announce rollback
"🔴 INITIATING ROLLBACK - [reason]"

# 2. Rollback application deployment
kubectl rollout undo deployment/riskcast-api -n riskcast-prod

# 3. Monitor rollback
kubectl rollout status deployment/riskcast-api -n riskcast-prod

# 4. If database migrations were applied, rollback migrations
alembic downgrade -1

# 5. Verify system is stable
./scripts/smoke-test.sh https://api.riskcast.io

# 6. Notify completion
"✅ Rollback complete. System stable on previous version."

# 7. Post-mortem required within 24 hours
```

---

## 📞 Emergency Contacts

| Role | Name | Phone | Slack | Availability |
|------|------|-------|-------|--------------|
| **Primary Deployer** | [Name] | +1-555-0100 | @deployer | During deployment |
| **Backup Engineer** | [Name] | +1-555-0101 | @backup | During deployment |
| **On-Call Engineer** | Rotation | +1-555-0102 | @oncall | 24/7 |
| **Database Admin** | [Name] | +1-555-0103 | @dba | On standby |
| **Engineering Manager** | [Name] | +1-555-0104 | @manager | On standby |
| **VP Engineering** | [Name] | +1-555-0105 | @vpeng | Escalation only |

### Escalation Path

1. **Issues during deployment** → Backup Engineer
2. **Rollback needed** → On-Call Engineer + DBA
3. **Major incident** → Engineering Manager
4. **Company-wide impact** → VP Engineering

---

## 📊 Post-Deployment Report Template

```markdown
# Production Deployment Report - v[VERSION]

## Summary
- **Date:** [YYYY-MM-DD]
- **Time:** [HH:MM] - [HH:MM] UTC
- **Version:** v[VERSION]
- **Deployer:** [Name]
- **Status:** ✅ Successful / ⚠️ Issues / ❌ Rolled Back

## Changes Deployed
- [Feature/Fix 1]
- [Feature/Fix 2]
- [Feature/Fix 3]

## Timeline
- T-1h: Pre-checks completed
- T-0: Deployment started
- T+10m: Migrations completed
- T+20m: Application deployed
- T+25m: Smoke tests passed
- T+30m: Monitoring verified
- T+2h: Deployment complete

## Metrics
- **Downtime:** 0 minutes (rolling deployment)
- **Error Rate:** [X%] (baseline: [Y%])
- **Response Time p95:** [Xs] (baseline: [Ys])
- **Deployment Duration:** [X] minutes

## Issues Encountered
- None / [Description of any issues and resolutions]

## Lessons Learned
- [What went well]
- [What could be improved]
- [Action items for next deployment]

## Follow-up Actions
- [ ] Monitor for 24 hours
- [ ] Update documentation if needed
- [ ] Schedule retrospective if issues occurred
```

---

## 🎓 Deployment Best Practices

### DO

✅ **Deploy during business hours** (unless critical fix)
- Better team availability
- Easier to get help if needed
- Can monitor impact in real-time

✅ **Use rolling deployments**
- Zero downtime
- Gradual rollout
- Easy to rollback

✅ **Test in staging first**
- Catch issues early
- Verify migrations work
- Test rollback procedures

✅ **Have a rollback plan**
- Know how to rollback quickly
- Test rollback in staging
- Document the procedure

✅ **Communicate clearly**
- Notify before deployment
- Update during deployment
- Confirm after completion

### DON'T

❌ **Don't deploy on Fridays** (unless necessary)
- Limited time to fix issues
- Team may be unavailable over weekend

❌ **Don't deploy without backups**
- Always have recent backup
- Verify backup integrity
- Test restore procedure

❌ **Don't skip smoke tests**
- Always verify deployment worked
- Test critical functionality
- Check for regressions

❌ **Don't ignore warnings**
- Address warnings before deploying
- Fix security vulnerabilities
- Resolve linter errors

❌ **Don't deploy multiple changes together**
- One change at a time
- Easier to identify issues
- Simpler to rollback

---

## 📝 Deployment Log Template

Keep a log during deployment:

```
=== Production Deployment Log ===
Date: [YYYY-MM-DD]
Version: v[VERSION]
Deployer: [Name]

[HH:MM] Pre-deployment backup created
[HH:MM] Database migrations started
[HH:MM] Migrations completed successfully
[HH:MM] Application deployment started
[HH:MM] Deployment rolling out... (3/10 pods updated)
[HH:MM] Deployment complete (10/10 pods healthy)
[HH:MM] Smoke tests started
[HH:MM] Smoke tests passed ✅
[HH:MM] Monitoring checks passed ✅
[HH:MM] Deployment complete ✅

Notes:
- [Any observations]
- [Issues encountered and resolutions]
```

---

**Last Updated:** January 24, 2026  
**Version:** 1.0.0  
**Owner:** Infrastructure Team

**Use this checklist for every production deployment! Print it if needed!** 📋
