# 📚 Operational Runbooks

**Complete operational guides for day-to-day operations and incident management**

[![Status](https://img.shields.io/badge/status-production%20ready-brightgreen)]()
[![Coverage](https://img.shields.io/badge/scenarios-15%2B-blue)]()
[![Checks](https://img.shields.io/badge/automated%20checks-26-blue)]()

---

## 🎯 Quick Start

### For On-Call Engineers

```bash
# 1. Read incident response runbook
cat docs/runbooks/incident-response.md

# 2. Practice commands
kubectl get pods -n riskcast-prod
kubectl logs -n riskcast-prod -l app=riskcast-api --tail=100

# 3. Bookmark emergency contacts
# See incident-response.md
```

### For Operations Team

```bash
# 1. Run production validation
pip install httpx asyncpg redis boto3
python scripts/production/checklist.py

# 2. Review all runbooks
ls docs/runbooks/

# 3. Test procedures in staging
kubectl config use-context staging
```

### For Deployers

```bash
# Before deployment
cat docs/production-checklist.md

# Run validation
python scripts/production/checklist.py

# Deploy
# Follow production-checklist.md step-by-step
```

---

## 📁 What's Included

### Runbooks (4 comprehensive guides)

**1. [Incident Response](docs/runbooks/incident-response.md)** (2,200 lines)
- SEV-1 through SEV-4 levels with response times
- 5-step response procedures
- 5 disaster scenarios with solutions
- Communication templates
- Escalation path
- Post-mortem process

**2. [Scaling](docs/runbooks/scaling.md)** (1,800 lines)
- Auto-scaling (HPA) configuration
- Manual scaling (API, workers, DB, Redis)
- 8 automated scaling triggers
- 4 load level capacity plans
- Cost estimates

**3. [Debugging](docs/runbooks/debugging.md)** (1,700 lines)
- Log analysis with jq
- Request tracing (request_id, trace_id)
- Database debugging (slow queries, locks)
- API debugging (port forward, curl)
- Memory and performance debugging
- 6 common issues with solutions

**4. [Maintenance](docs/runbooks/maintenance.md)** (800 lines)
- Scheduled maintenance windows
- Database maintenance (VACUUM, REINDEX)
- Certificate renewal
- Dependency updates
- Cleanup tasks
- Pre/post checklists

### Tools (1 automated validator)

**[Production Checklist](scripts/production/checklist.py)** (850 lines)
- 26 automated checks
- 7 categories validated
- JSON + text output
- CI/CD integration ready

### Checklists (1 comprehensive guide)

**[Production Deployment](docs/production-checklist.md)** (700 lines)
- Pre-deployment (1 week before)
- Day-before checklist
- Deployment day procedures
- Rollback triggers and procedures
- Emergency contacts

---

## 🚀 Daily Operations

### Morning Checks

```bash
# Check system health
kubectl get pods -n riskcast-prod
kubectl top pods -n riskcast-prod
kubectl top nodes

# Check error rate (should be low)
kubectl logs -n riskcast-prod -l app=riskcast-api --since=8h | grep ERROR | wc -l

# Check latest backup
python scripts/dr/restore.py --list | head -3

# Review alerts
# Check Slack #alerts channel
# Check Grafana dashboards
```

### During Incidents

**Quick Reference:**
```bash
# 1. Assess severity (SEV-1 to SEV-4)
# 2. Create incident channel: #incident-YYYYMMDD-description
# 3. Follow docs/runbooks/incident-response.md
# 4. Common fixes:
#    - Rollback: kubectl rollout undo deployment/riskcast-api
#    - Scale: kubectl scale deployment/riskcast-api --replicas=10
#    - Restart: kubectl rollout restart deployment/riskcast-api
```

### Before Deployments

```bash
# 1. Run production checklist
python scripts/production/checklist.py

# 2. Follow production deployment guide
cat docs/production-checklist.md

# 3. Verify backup
python scripts/dr/backup.py --type full

# 4. Deploy
# Follow step-by-step procedures
```

### Weekly Maintenance

```bash
# Sunday 02:00-04:00 UTC
# Database maintenance
psql $DATABASE_URL -c "VACUUM ANALYZE quotes;"
psql $DATABASE_URL -c "VACUUM ANALYZE policies;"
psql $DATABASE_URL -c "ANALYZE;"

# Test restore
python scripts/dr/restore.py --target-db test --yes
dropdb test
```

---

## 📊 Quick Stats

| Metric | Value |
|--------|-------|
| **Runbooks** | 4 |
| **Total Lines** | ~8,000 |
| **Scenarios Documented** | 15+ |
| **Commands Reference** | 180+ |
| **Automated Checks** | 26 |
| **Checklists** | 10+ |

---

## 🎯 Runbook Summary

### Incident Response

**When to use:** Service outage, errors, performance issues, security breach

**Key sections:**
- Severity assessment (15 min to 24h response)
- 5-step response (detect, communicate, mitigate, resolve, post-mortem)
- 5 scenarios (errors, DB, memory, external, security)
- Command reference

**Quick commands:**
```bash
kubectl get pods -n riskcast-prod
kubectl logs -n riskcast-prod -l app=riskcast-api --since=10m | grep ERROR
kubectl rollout undo deployment/riskcast-api -n riskcast-prod
```

---

### Scaling

**When to use:** High load, traffic spikes, resource exhaustion

**Key sections:**
- HPA configuration
- Manual scaling (API, workers, DB, Redis)
- Capacity planning (4 load levels)
- Pre-scaling checklist

**Quick commands:**
```bash
kubectl scale deployment/riskcast-api --replicas=10 -n riskcast-prod
kubectl patch hpa riskcast-api-hpa --patch '{"spec":{"minReplicas":5}}'
aws rds create-db-instance-read-replica ...
```

---

### Debugging

**When to use:** Investigating errors, performance issues, unexpected behavior

**Key sections:**
- Log analysis and filtering
- Request tracing
- Database debugging
- API debugging
- Common issues (6 with solutions)

**Quick commands:**
```bash
kubectl logs -n riskcast-prod -l app=riskcast-api --since=1h | jq -r 'select(.level == "ERROR")'
kubectl logs -n riskcast-prod --all-containers --since=1h | jq -r 'select(.request_id == "abc123")'
psql $DATABASE_URL -c "SELECT pid, query FROM pg_stat_activity WHERE ..."
```

---

### Maintenance

**When to use:** Scheduled maintenance, database optimization, cleanup

**Key sections:**
- Maintenance windows schedule
- Database maintenance (VACUUM, REINDEX)
- Certificate renewal
- Dependency updates
- Cleanup tasks

**Quick commands:**
```bash
psql $DATABASE_URL -c "VACUUM ANALYZE quotes;"
kubectl get certificate -n riskcast-prod
pip list --outdated
```

---

## 🔧 Production Checklist Tool

**Purpose:** Validate production readiness before deployment

**Usage:**
```bash
# Run all checks
python scripts/production/checklist.py

# Output as JSON
python scripts/production/checklist.py --json

# In CI/CD pipeline
python scripts/production/checklist.py || exit 1
```

**Checks 26 items:**
- Infrastructure: DB, Redis, API, DNS, SSL
- Configuration: Env vars, secrets, feature flags
- Security: Rate limiting, CORS, headers, auth
- Monitoring: Metrics, health, logging
- Reliability: Replicas, resources, HPA
- Data: Migrations, backups, retention
- Documentation: Runbooks, architecture

**Output:**
```
✅ READY FOR PRODUCTION
   18 passed, 0 failed, 4 warnings, 4 skipped
```

---

## 🐛 Troubleshooting

### "kubectl not found"

Some checks require kubectl. Install:
```bash
# macOS
brew install kubectl

# Ubuntu
sudo apt-get install kubectl

# Or skip K8s checks
python scripts/production/checklist.py  # Will skip gracefully
```

### "Module not found"

```bash
# Install optional dependencies
pip install httpx asyncpg redis boto3

# Or install from requirements
pip install -r requirements-production.txt
```

### "Connection refused"

```bash
# Check environment variables
echo $DATABASE_URL
echo $REDIS_URL
echo $API_URL

# Test connectivity
psql $DATABASE_URL -c "SELECT 1"
redis-cli -u $REDIS_URL PING
curl $API_URL/health/ready
```

---

## 📚 Documentation Links

### Runbooks

- [Incident Response](docs/runbooks/incident-response.md)
- [Scaling](docs/runbooks/scaling.md)
- [Debugging](docs/runbooks/debugging.md)
- [Maintenance](docs/runbooks/maintenance.md)
- [Disaster Recovery](docs/runbooks/disaster-recovery.md) (from DR system)

### Checklists

- [Production Deployment](docs/production-checklist.md)
- [Production Validation Tool](scripts/production/checklist.py)

### Summaries

- [Implementation Complete](OPERATIONAL_RUNBOOKS_COMPLETE.md)
- [Quick Summary](RUNBOOKS_SUMMARY.md)
- [Acceptance Checklist](RUNBOOKS_ACCEPTANCE_CHECKLIST.md)

---

## 🎓 Training Materials

### New Team Members

**Week 1:**
- Read incident response runbook
- Practice commands in staging
- Participate in tabletop exercise

**Week 2:**
- Read debugging runbook
- Practice log analysis
- Debug sample issues

**Week 3:**
- Read scaling runbook
- Practice scaling in staging
- Review capacity plans

**Week 4:**
- Read maintenance runbook
- Shadow maintenance window
- Run production checklist

### Ongoing

- Monthly incident response drills
- Quarterly runbook reviews
- Update after each incident
- Share lessons learned

---

## 🎉 Status

```
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║      📚 OPERATIONAL RUNBOOKS COMPLETE 📚                   ║
║                                                            ║
║  ✅ Incident Response                                     ║
║  ✅ Scaling Procedures                                    ║
║  ✅ Debugging Guide                                       ║
║  ✅ Maintenance Tasks                                     ║
║  ✅ Production Validation                                 ║
║                                                            ║
║  📊 10 files, 8,000+ lines                                 ║
║  📊 14/14 criteria (100%)                                  ║
║  📊 26 automated checks                                    ║
║  📊 15+ scenarios documented                               ║
║                                                            ║
║  Ready for daily operations! 🎯                            ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```

**Status:** ✅ Production Ready  
**Version:** 1.0.0  
**Date:** January 24, 2026

**Ready to handle any operational challenge!** 💪
