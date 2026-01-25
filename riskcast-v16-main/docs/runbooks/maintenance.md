# Maintenance Runbook

## 📋 Table of Contents

- [Scheduled Maintenance Windows](#scheduled-maintenance-windows)
- [Pre-Maintenance Checklist](#pre-maintenance-checklist)
- [Database Maintenance](#database-maintenance)
- [Certificate Renewal](#certificate-renewal)
- [Dependency Updates](#dependency-updates)
- [Log Rotation](#log-rotation)
- [Cleanup Tasks](#cleanup-tasks)
- [Health Verification](#health-verification)
- [Post-Maintenance](#post-maintenance)

---

## 📅 Scheduled Maintenance Windows

### Regular Maintenance Schedule

| Activity | Window | Frequency | Duration | Downtime? |
|----------|--------|-----------|----------|-----------|
| **Database Maintenance** | Sunday 02:00-04:00 UTC | Weekly | ~2 hours | No (read-only) |
| **Infrastructure Updates** | Saturday 02:00-06:00 UTC | Monthly | ~4 hours | No |
| **Application Deployments** | Weekdays 10:00-16:00 UTC | As needed | ~20 min | No (rolling) |
| **Certificate Renewal** | Automatic (Let's Encrypt) | Every 60 days | ~5 min | No |
| **Dependency Updates** | Monthly | Quarterly | ~1 hour | No (staging first) |

### Maintenance Notification

**Timeline:**
- **T-72h:** Internal notification to engineering team
- **T-48h:** Customer notification via email + status page
- **T-24h:** Reminder to team, verify backup
- **T-1h:** Final checks, silence non-critical alerts
- **T-0:** Begin maintenance
- **T+end:** Notify completion, restore monitoring

---

## ✅ Pre-Maintenance Checklist

### 1 Week Before

- [ ] Review maintenance plan
- [ ] Schedule team coverage
- [ ] Prepare rollback procedures
- [ ] Test procedures in staging
- [ ] Update documentation if needed
- [ ] Coordinate with stakeholders

### 48 Hours Before

- [ ] **Notify customers** (for planned maintenance)
  ```bash
  # Update status page
  curl -X POST https://api.statuspage.io/v1/pages/PAGE_ID/incidents \
    -H "Authorization: OAuth TOKEN" \
    -d '{
      "incident": {
        "name": "Scheduled Maintenance",
        "status": "scheduled",
        "scheduled_for": "2026-01-27T02:00:00Z",
        "scheduled_until": "2026-01-27T04:00:00Z",
        "body": "We will be performing routine database maintenance",
        "impact_override": "minor"
      }
    }'
  ```

- [ ] Send customer email notification
- [ ] Post in #customers Slack channel
- [ ] Update internal wiki

### 24 Hours Before

- [ ] **Verify recent backup**
  ```bash
  python scripts/dr/restore.py --list | head -5
  
  # Verify backup age < 24 hours
  aws s3 ls s3://riskcast-backups/database/full/ --recursive | tail -5
  ```

- [ ] **Create fresh backup**
  ```bash
  python scripts/dr/backup.py --type full
  ```

- [ ] **Prepare rollback plan**
  - Document current versions
  - Have rollback commands ready
  - Test rollback in staging

- [ ] **Schedule team coverage**
  - Primary: [Name]
  - Backup: [Name]
  - On-call: [Name]

### 1 Hour Before

- [ ] **Silence non-critical alerts**
  ```bash
  # Silence in AlertManager
  curl -X POST http://alertmanager:9093/api/v2/silences \
    -H "Content-Type: application/json" \
    -d '{
      "matchers": [
        {"name": "severity", "value": "warning", "isRegex": false}
      ],
      "startsAt": "'$(date -u +%Y-%m-%dT%H:%M:%S.000Z)'",
      "endsAt": "'$(date -u -d '+4 hours' +%Y-%m-%dT%H:%M:%S.000Z)'",
      "comment": "Scheduled maintenance window",
      "createdBy": "oncall@riskcast.io"
    }'
  ```

- [ ] **Verify system health**
  ```bash
  ./scripts/health-check.sh --full
  kubectl get pods -n riskcast-prod
  kubectl top nodes
  ```

- [ ] **Check metrics dashboards**
  - Error rate normal
  - Response times normal
  - Resource utilization acceptable

- [ ] **Final notification**
  ```
  #infrastructure:
  "Starting maintenance in 1 hour. Window: 02:00-04:00 UTC. 
  Status page updated. Team: @[primary] @[backup] @oncall"
  ```

---

## 🗄️ Database Maintenance

### Run VACUUM ANALYZE

**Purpose:** Reclaim space, update statistics, improve query performance

**Frequency:** Weekly (automated in Sunday maintenance window)

```bash
# Connect to database
kubectl exec -it -n riskcast-prod deployment/postgres -- \
  psql -U riskcast -d riskcast

# Or use psql directly
psql $DATABASE_URL
```

#### VACUUM ANALYZE (Online, No Lock)

```sql
-- Analyze all tables (fast, no locks)
ANALYZE;

-- Vacuum analyze specific table (recommended)
VACUUM ANALYZE quotes;
VACUUM ANALYZE policies;
VACUUM ANALYZE risk_runs;
VACUUM ANALYZE claims;
VACUUM ANALYZE tenants;

-- Check dead tuples before vacuuming
SELECT 
  schemaname,
  tablename,
  n_live_tup,
  n_dead_tup,
  round(100.0 * n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0), 2) AS dead_pct,
  last_vacuum,
  last_autovacuum
FROM pg_stat_user_tables
WHERE n_dead_tup > 1000
ORDER BY n_dead_tup DESC;

-- Vacuum tables with high dead tuple count
VACUUM ANALYZE quotes;  -- This may take several minutes for large tables
```

#### VACUUM FULL (Offline, Requires Downtime)

**⚠️ WARNING:** Requires exclusive lock, blocks all operations

**Only use when:**
- Table bloat is significant (> 50%)
- Maintenance window allows downtime
- Standard VACUUM is insufficient

```sql
-- Check table bloat first
SELECT 
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
  round(100 * pg_total_relation_size(schemaname||'.'||tablename) / NULLIF(pg_relation_size(schemaname||'.'||tablename), 0)) AS bloat_ratio
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;

-- If needed, VACUUM FULL (DOWNTIME REQUIRED)
-- 1. Set application to read-only mode
-- 2. Notify users
-- 3. Run VACUUM FULL
VACUUM FULL ANALYZE quotes;

-- 4. Restore normal operation
```

### Reindex

**Purpose:** Rebuild indexes, fix index bloat, improve query performance

**Frequency:** Monthly or when index performance degrades

```bash
# Connect to database
psql $DATABASE_URL
```

```sql
-- Check index sizes
SELECT 
  schemaname,
  tablename,
  indexname,
  pg_size_pretty(pg_relation_size(indexrelid)) AS index_size,
  idx_scan,
  idx_tup_read,
  idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY pg_relation_size(indexrelid) DESC
LIMIT 20;

-- Reindex specific table (no downtime)
REINDEX TABLE CONCURRENTLY quotes;
REINDEX TABLE CONCURRENTLY policies;

-- Reindex specific index
REINDEX INDEX CONCURRENTLY quotes_pkey;
REINDEX INDEX CONCURRENTLY idx_quotes_created_at;

-- Reindex all indexes in schema (DOWNTIME - use with caution)
-- REINDEX SCHEMA public;

-- Reindex entire database (DOWNTIME - rarely needed)
-- REINDEX DATABASE riskcast;
```

### Update Statistics

```sql
-- Update query planner statistics (fast, no lock)
ANALYZE;

-- Update specific table statistics
ANALYZE quotes;
ANALYZE VERBOSE quotes;  -- With progress output

-- Check if statistics are recent
SELECT 
  schemaname,
  tablename,
  last_analyze,
  last_autoanalyze,
  n_mod_since_analyze
FROM pg_stat_user_tables
ORDER BY n_mod_since_analyze DESC
LIMIT 20;
```

### Check Database Health

```sql
-- Check for bloat
SELECT 
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
  n_dead_tup,
  round(100.0 * n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0), 1) AS dead_pct
FROM pg_stat_user_tables
WHERE n_dead_tup > 0
ORDER BY n_dead_tup DESC
LIMIT 20;

-- Check for missing indexes (high seq_scan)
SELECT 
  schemaname,
  tablename,
  seq_scan,
  seq_tup_read,
  idx_scan,
  n_live_tup,
  round(100.0 * idx_scan / NULLIF(seq_scan + idx_scan, 0), 1) AS idx_scan_pct
FROM pg_stat_user_tables
WHERE seq_scan > 0
  AND n_live_tup > 10000
ORDER BY seq_scan DESC
LIMIT 20;

-- Check for unused indexes
SELECT 
  schemaname,
  tablename,
  indexname,
  pg_size_pretty(pg_relation_size(indexrelid)) AS index_size,
  idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0
  AND indexrelname NOT LIKE 'pg_toast%'
ORDER BY pg_relation_size(indexrelid) DESC
LIMIT 20;
```

---

## 🔐 Certificate Renewal

### Check Certificate Expiration

```bash
# Check Kubernetes TLS secret
kubectl get secret -n riskcast-prod riskcast-api-tls \
  -o jsonpath='{.data.tls\.crt}' | \
  base64 -d | \
  openssl x509 -noout -dates

# Check with cert-manager
kubectl describe certificate -n riskcast-prod riskcast-api-tls

# Check all certificates
kubectl get certificates -n riskcast-prod -o json | \
  jq '.items[] | {name: .metadata.name, notAfter: .status.notAfter}'

# Alert if expiring soon (< 30 days)
kubectl get certificates -n riskcast-prod -o json | \
  jq '.items[] | select(.status.renewalTime != null) | 
    {name: .metadata.name, 
     expires: .status.notAfter,
     renewsAt: .status.renewalTime}'
```

### Force Certificate Renewal

```bash
# Option 1: Delete and recreate certificate (triggers renewal)
kubectl delete certificate -n riskcast-prod riskcast-api-tls
kubectl apply -f k8s/base/certificate.yaml

# Option 2: Annotate certificate for renewal
kubectl annotate certificate -n riskcast-prod riskcast-api-tls \
  cert-manager.io/issue-temporary-certificate="true" \
  --overwrite

# Monitor renewal
kubectl describe certificate -n riskcast-prod riskcast-api-tls
kubectl get certificaterequest -n riskcast-prod
kubectl logs -n cert-manager -l app=cert-manager

# Verify new certificate
kubectl get secret -n riskcast-prod riskcast-api-tls \
  -o jsonpath='{.data.tls\.crt}' | \
  base64 -d | \
  openssl x509 -noout -text | grep -A 2 "Validity"
```

### Certificate Troubleshooting

```bash
# Check cert-manager status
kubectl get challenges -n riskcast-prod
kubectl get orders -n riskcast-prod

# Check cert-manager logs
kubectl logs -n cert-manager deployment/cert-manager --tail=100

# Check Let's Encrypt rate limits
# - 50 certificates per registered domain per week
# - 5 duplicate certificates per week

# Manual certificate verification
openssl s_client -connect api.riskcast.io:443 -servername api.riskcast.io
```

---

## 📦 Dependency Updates

### Python Dependencies

#### Check for Updates

```bash
# Check outdated packages
pip list --outdated

# Or with pip-review
pip install pip-review
pip-review
```

#### Update Dependencies

```bash
# Update requirements.in (if using pip-tools)
# Edit requirements.in manually to update versions

# Compile new requirements.txt
pip-compile --upgrade requirements.in

# Or update all to latest
pip-compile --upgrade --resolver=backtracking requirements.in

# Review changes
git diff requirements.txt

# Test in development
pip install -r requirements.txt
pytest

# Test in staging
# Deploy to staging and run tests

# If all good, deploy to production
```

#### Critical Security Updates

```bash
# Check for security vulnerabilities
pip-audit

# Or use safety
safety check

# Update specific package with security issue
pip install --upgrade <package>==<version>
pip freeze > requirements.txt

# Deploy immediately if critical
```

### Container Base Image

```bash
# Check for updates to base image
docker pull python:3.11-slim

# Check digest
docker inspect python:3.11-slim | jq '.[0].RepoDigests'

# Update Dockerfile
# FROM python:3.11-slim

# Rebuild image
docker build -t riskcast-api:test .

# Test locally
docker run -it riskcast-api:test pytest

# Test in staging
# Push image and deploy to staging

# Deploy to production
```

### System Package Updates (if needed)

```bash
# In Dockerfile, update system packages
RUN apt-get update && apt-get upgrade -y && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Rebuild and test
```

### Kubernetes Component Updates

```bash
# Check current versions
kubectl version

# Check for updates
aws eks describe-cluster --name riskcast-prod --query 'cluster.version'

# Update EKS cluster (requires maintenance window)
aws eks update-cluster-version \
  --name riskcast-prod \
  --kubernetes-version 1.28

# Wait for update
aws eks wait cluster-active --name riskcast-prod

# Update node groups
aws eks update-nodegroup-version \
  --cluster-name riskcast-prod \
  --nodegroup-name workers \
  --kubernetes-version 1.28
```

---

## 📝 Log Rotation

### Kubernetes Log Management

**Note:** Logs are automatically rotated by Kubernetes

#### Verify Log Rotation

```bash
# Check log file sizes on nodes
kubectl debug node/<node-name> -it --image=busybox -- \
  du -sh /var/log/containers/riskcast* | sort -h

# Check log retention policy
kubectl get pods -n kube-system -l k8s-app=fluentd -o yaml | \
  grep -A 5 "FLUENT_ELASTICSEARCH_LOGSTASH_PREFIX"
```

#### Manual Log Cleanup (if needed)

```bash
# Clean logs older than 7 days (run on nodes)
kubectl debug node/<node-name> -it --image=busybox -- \
  find /var/log/containers -name "*.log" -mtime +7 -delete

# Check disk space after cleanup
kubectl debug node/<node-name> -it --image=busybox -- \
  df -h /var/log
```

### Application Log Management

```bash
# Check application log files (if logging to file)
kubectl exec -it -n riskcast-prod deployment/riskcast-api -- \
  ls -lh /var/log/

# Rotate application logs (if needed)
kubectl exec -it -n riskcast-prod deployment/riskcast-api -- \
  logrotate -f /etc/logrotate.conf
```

### Elasticsearch Log Cleanup

```bash
# Check Elasticsearch indexes
curl -X GET "localhost:9200/_cat/indices?v" | grep riskcast

# Delete old indexes (> 90 days)
curl -X DELETE "localhost:9200/riskcast-logs-2025-10-*"

# Or use Curator for automated cleanup
# curator_cli delete_indices \
#   --filter_list '[{"filtertype":"age","source":"name","direction":"older","timestring":"%Y.%m.%d","unit":"days","unit_count":90}]'
```

---

## 🧹 Cleanup Tasks

### Remove Old Data

#### Archive Old Audit Events

```sql
-- Check audit events count
SELECT 
  date_trunc('month', created_at) AS month,
  count(*) 
FROM audit_events 
GROUP BY month 
ORDER BY month DESC;

-- Create archive table (if not exists)
CREATE TABLE IF NOT EXISTS audit_events_archive (
  LIKE audit_events INCLUDING ALL
);

-- Archive events older than 2 years
INSERT INTO audit_events_archive 
SELECT * FROM audit_events 
WHERE created_at < NOW() - INTERVAL '2 years';

-- Verify archived data
SELECT count(*) FROM audit_events_archive;

-- Delete archived data from main table
DELETE FROM audit_events 
WHERE created_at < NOW() - INTERVAL '2 years';

-- Vacuum to reclaim space
VACUUM ANALYZE audit_events;
```

#### Clean Temporary Data

```sql
-- Remove expired quotes (older than 30 days, status = 'draft')
DELETE FROM quotes 
WHERE status = 'draft' 
  AND created_at < NOW() - INTERVAL '30 days';

-- Remove expired sessions (older than 7 days)
DELETE FROM user_sessions 
WHERE created_at < NOW() - INTERVAL '7 days';

-- Clean up soft-deleted records (if using soft delete)
-- DELETE FROM quotes WHERE deleted_at < NOW() - INTERVAL '90 days';
```

### Clean Temporary Files

```bash
# Clean /tmp in all pods
kubectl get pods -n riskcast-prod -o name | \
  xargs -I {} kubectl exec -n riskcast-prod {} -- \
  find /tmp -type f -mtime +1 -delete

# Check space reclaimed
kubectl exec -it -n riskcast-prod deployment/riskcast-api -- \
  df -h /tmp
```

### Prune Docker Images

```bash
# On nodes (via DaemonSet or SSH)
# Remove images older than 1 week
docker system prune -af --filter "until=168h"

# Remove unused volumes
docker volume prune -f

# Remove build cache
docker builder prune -af

# Check space reclaimed
docker system df
```

### Clean Redis Keys

```bash
# Check Redis memory usage
redis-cli -u $REDIS_URL INFO memory

# Find keys by pattern
redis-cli -u $REDIS_URL --scan --pattern "cache:*" | head -100

# Delete old cache keys (CAUTION: can affect performance)
redis-cli -u $REDIS_URL --scan --pattern "cache:old:*" | \
  xargs redis-cli -u $REDIS_URL DEL

# Or set TTL on keys without expiration
redis-cli -u $REDIS_URL --scan --pattern "cache:*" | \
  while read key; do 
    redis-cli -u $REDIS_URL EXPIRE "$key" 3600
  done
```

### Database Backup Cleanup

```bash
# List old backups
python scripts/dr/restore.py --list | tail -20

# Cleanup happens automatically via retention policy
# But you can manually delete if needed
aws s3 ls s3://riskcast-backups/database/full/ --recursive | \
  awk '$1 < "'$(date -d '60 days ago' +%Y-%m-%d)'" {print $4}' | \
  xargs -I {} aws s3 rm s3://riskcast-backups/{}
```

---

## ✅ Health Verification After Maintenance

### Run Comprehensive Health Check

```bash
# Full health check
./scripts/health-check.sh --full

# Check all pods are running
kubectl get pods -n riskcast-prod

# Check pod health
kubectl wait --for=condition=ready pod \
  -l app=riskcast-api \
  -n riskcast-prod \
  --timeout=300s
```

### Verify Metrics

```bash
# Check metrics endpoint
curl -s http://prometheus:9090/-/healthy

# Verify application metrics
curl -s https://api.riskcast.io/metrics | grep riskcast_ | head -20

# Check specific metrics
curl -s 'http://prometheus:9090/api/v1/query?query=up{job="riskcast-api"}' | jq .
```

### Run Smoke Tests

```bash
# Run smoke tests
./scripts/smoke-test.sh https://api.riskcast.io

# Test critical endpoints
curl -s https://api.riskcast.io/health/ready
curl -s https://api.riskcast.io/health/live
curl -s https://api.riskcast.io/api/v3/quotes/ -H "Authorization: Bearer $TOKEN"
```

### Check Error Rates

```bash
# Check recent errors (should be zero or minimal)
kubectl logs -n riskcast-prod -l app=riskcast-api --since=10m | \
  grep ERROR | wc -l

# Check error types
kubectl logs -n riskcast-prod -l app=riskcast-api --since=10m | \
  jq -r 'select(.level == "ERROR") | .extra.error_type' | \
  sort | uniq -c

# Check 5xx error rate
kubectl logs -n riskcast-prod -l app=riskcast-api --since=10m | \
  jq -r 'select(.http_status >= 500) | 1' | wc -l
```

### Verify Database Health

```sql
-- Check connection count
SELECT count(*) FROM pg_stat_activity;

-- Check for long-running queries
SELECT pid, now() - query_start AS duration, state, query 
FROM pg_stat_activity 
WHERE state != 'idle' 
  AND query_start < NOW() - INTERVAL '1 minute'
ORDER BY duration DESC;

-- Check recent vacuum
SELECT 
  schemaname,
  tablename,
  last_vacuum,
  last_autovacuum,
  last_analyze
FROM pg_stat_user_tables
ORDER BY last_vacuum DESC NULLS LAST
LIMIT 10;
```

### Check Performance

```bash
# Response time check
kubectl logs -n riskcast-prod -l app=riskcast-api --since=5m | \
  jq -r 'select(.duration) | .duration' | \
  awk '{sum+=$1; n++; if($1>max) max=$1} 
       END {print "Avg:", sum/n, "Max:", max}'

# Request rate
kubectl logs -n riskcast-prod -l app=riskcast-api --since=1m | \
  jq -r 'select(.http_status) | 1' | wc -l | \
  awk '{print $1/60 " req/s"}'
```

---

## 📝 Post-Maintenance

### Completion Checklist

- [ ] **All health checks passed**
- [ ] **Smoke tests successful**
- [ ] **No error spikes in logs**
- [ ] **Performance metrics normal**
- [ ] **Database queries performing well**
- [ ] **Monitoring dashboards look good**

### Update Communications

- [ ] **Update status page to operational**
  ```bash
  curl -X PATCH https://api.statuspage.io/v1/pages/PAGE_ID/incidents/INCIDENT_ID \
    -H "Authorization: OAuth TOKEN" \
    -d '{"incident":{"status":"resolved"}}'
  ```

- [ ] **Send completion notification**
  ```
  #infrastructure:
  "✅ Maintenance completed successfully
  Duration: [actual time]
  All systems operational
  No issues detected"
  ```

- [ ] **Notify customers** (if they were notified of maintenance)

### Documentation

- [ ] **Document any issues encountered**
  - What went wrong
  - How it was resolved
  - Lessons learned

- [ ] **Update runbooks if procedures changed**
  - New steps discovered
  - Better approaches found
  - Troubleshooting tips

- [ ] **Update capacity planning** (if relevant)
  - Database size changes
  - Resource usage changes
  - Performance improvements

### Restore Normal Operations

- [ ] **Re-enable all alerts**
  ```bash
  # Delete silence in AlertManager
  curl -X DELETE "http://alertmanager:9093/api/v2/silence/SILENCE_ID"
  ```

- [ ] **Verify monitoring is active**
  ```bash
  kubectl logs -n monitoring -l app=prometheus --tail=20
  kubectl logs -n monitoring -l app=alertmanager --tail=20
  ```

- [ ] **Check alert rules are firing correctly**
  ```bash
  curl -s http://prometheus:9090/api/v1/rules | \
    jq '.data.groups[].rules[] | select(.alerts != null)'
  ```

### Post-Mortem (if issues occurred)

If maintenance didn't go as planned:

- [ ] Schedule post-mortem meeting (within 48 hours)
- [ ] Document timeline of events
- [ ] Identify root cause
- [ ] Create action items for improvements
- [ ] Update procedures to prevent recurrence

---

## 📊 Maintenance Metrics

Track these metrics over time:

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Maintenance duration | < 2 hours | Actual time in maintenance window |
| Downtime | 0 minutes | Time with service unavailable |
| Issues encountered | 0 | Count of problems during maintenance |
| Rollbacks required | 0 | Times had to rollback changes |
| Customer complaints | 0 | Support tickets related to maintenance |

---

## 🔄 Maintenance Automation

### Automated Database Maintenance

```bash
# Create CronJob for weekly VACUUM
kubectl apply -f - <<EOF
apiVersion: batch/v1
kind: CronJob
metadata:
  name: database-maintenance
  namespace: riskcast-prod
spec:
  schedule: "0 2 * * 0"  # Sunday 2 AM UTC
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: maintenance
            image: postgres:15-alpine
            command:
            - /bin/sh
            - -c
            - |
              psql \$DATABASE_URL <<SQL
              VACUUM ANALYZE quotes;
              VACUUM ANALYZE policies;
              VACUUM ANALYZE risk_runs;
              VACUUM ANALYZE claims;
              ANALYZE;
              SQL
            env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: riskcast-database-credentials
                  key: DATABASE_URL
          restartPolicy: OnFailure
EOF
```

### Automated Cleanup Script

```bash
# scripts/maintenance/cleanup.sh
#!/bin/bash

echo "Running automated cleanup tasks..."

# Clean old audit events
psql $DATABASE_URL -c "DELETE FROM audit_events WHERE created_at < NOW() - INTERVAL '2 years';"

# Clean old sessions
psql $DATABASE_URL -c "DELETE FROM user_sessions WHERE created_at < NOW() - INTERVAL '7 days';"

# Clean temp files
kubectl get pods -n riskcast-prod -o name | \
  xargs -I {} kubectl exec -n riskcast-prod {} -- \
  find /tmp -type f -mtime +1 -delete

echo "Cleanup completed"
```

---

**Last Updated:** January 24, 2026  
**Version:** 1.0.0  
**Owner:** Infrastructure Team

**Review maintenance procedures after each maintenance window and update this runbook!**
