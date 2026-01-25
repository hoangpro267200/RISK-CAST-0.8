# Disaster Recovery Runbook

## 📚 Table of Contents

- [Overview](#overview)
- [Recovery Objectives](#recovery-objectives)
- [Backup Strategy](#backup-strategy)
- [Disaster Scenarios](#disaster-scenarios)
- [Recovery Procedures](#recovery-procedures)
- [Testing](#testing)
- [Contact Information](#contact-information)

---

## 🎯 Overview

This document outlines disaster recovery procedures for the RISKCAST platform.

**Last Updated:** January 24, 2026  
**Version:** 1.0.0

### Recovery Objectives

| Metric | Target | Notes |
|--------|--------|-------|
| **RTO** (Recovery Time Objective) | 4 hours | Maximum acceptable downtime |
| **RPO** (Recovery Point Objective) | 1 hour | Maximum acceptable data loss |
| **MTTR** (Mean Time To Recover) | 2 hours | Average recovery time |

---

## 💾 Backup Strategy

### Backup Schedule

| Component | Backup Type | Frequency | Retention | Location |
|-----------|-------------|-----------|-----------|----------|
| **PostgreSQL** | Full | Weekly (Sunday 3 AM) | 30 days | S3 (us-east-1) |
| **PostgreSQL** | Incremental | Daily (Mon-Sat 3 AM) | 7 days | S3 (us-east-1) |
| **Redis** | RDB Snapshot | Hourly | 24 hours | S3 (us-east-1) |
| **Configuration** | Git Archive | Every change | Indefinite | GitHub + S3 |
| **Secrets** | AWS Secrets Manager | Versioned | 30 versions | AWS Secrets Manager |
| **Logs** | Elasticsearch | Continuous | 90 days | Elasticsearch |

### Backup Verification

All backups are automatically verified:
- ✅ File integrity check (SHA-256 checksum)
- ✅ pg_restore validation
- ✅ Table count verification
- ✅ Metadata validation

### Backup Commands

```bash
# Run full backup
python scripts/dr/backup.py --type full

# Run incremental backup
python scripts/dr/backup.py --type incremental

# Automatic backup (full on Monday, incremental other days)
python scripts/dr/backup.py

# List existing backups
python scripts/dr/restore.py --list
```

---

## 🚨 Disaster Scenarios

### Priority Levels

| Level | Response Time | Description |
|-------|---------------|-------------|
| **P0 - Critical** | Immediate | Complete service outage |
| **P1 - High** | < 1 hour | Major functionality impaired |
| **P2 - Medium** | < 4 hours | Partial service degradation |
| **P3 - Low** | < 24 hours | Minor issues |

---

## 🔥 Scenario 1: Database Corruption

**Priority:** P0 - Critical  
**Symptoms:**
- Application errors about data integrity
- PostgreSQL errors in logs
- Inconsistent query results
- Transactions failing unexpectedly

### Recovery Steps

#### Step 1: Assess the Damage

```bash
# Check database status
psql $DATABASE_URL -c "\l+"

# Check for corruption
psql $DATABASE_URL -c "SELECT * FROM pg_stat_database WHERE datname = 'riskcast';"

# Check table integrity
psql $DATABASE_URL -c "SELECT tablename FROM pg_tables WHERE schemaname = 'public';"
```

#### Step 2: Stop Application

```bash
# Stop all application pods to prevent further writes
kubectl scale deployment riskcast-api --replicas=0 -n riskcast-prod

# Verify pods are stopped
kubectl get pods -n riskcast-prod
```

#### Step 3: Create Emergency Backup

```bash
# Attempt to backup current state (even if corrupted)
python scripts/dr/backup.py --type full --no-verify

# This may fail, but try anyway
```

#### Step 4: List Available Backups

```bash
# List recent backups
python scripts/dr/restore.py --list

# Note the most recent uncorrupted backup
```

#### Step 5: Restore Database

```bash
# Restore from backup
python scripts/dr/restore.py \
  --backup-key database/full/20240115_030000/backup.dump \
  --drop-existing \
  --yes

# This will:
# 1. Download backup from S3
# 2. Drop existing database
# 3. Create new database
# 4. Restore from backup
# 5. Verify restoration
```

#### Step 6: Run Migrations

```bash
# Ensure schema is up to date
alembic upgrade head

# Verify migrations
python scripts/db/check_migrations.py
```

#### Step 7: Verify Data Integrity

```bash
# Run verification script
python scripts/dr/verify.py --full

# Check critical tables
psql $DATABASE_URL -c "SELECT COUNT(*) FROM quotes;"
psql $DATABASE_URL -c "SELECT COUNT(*) FROM policies;"
psql $DATABASE_URL -c "SELECT COUNT(*) FROM tenants;"
```

#### Step 8: Restart Application

```bash
# Restart application pods
kubectl scale deployment riskcast-api --replicas=3 -n riskcast-prod

# Monitor rollout
kubectl rollout status deployment/riskcast-api -n riskcast-prod

# Check logs
kubectl logs -f deployment/riskcast-api -n riskcast-prod
```

#### Step 9: Run Smoke Tests

```bash
# Run comprehensive smoke tests
./scripts/smoke-test.sh https://api.riskcast.io

# Test critical endpoints
curl https://api.riskcast.io/health/ready
curl https://api.riskcast.io/api/v3/health
```

#### Step 10: Notify Stakeholders

```bash
# Send notification
# - Update status page
# - Notify customers
# - Document incident
```

**Expected Duration:** 2-3 hours  
**Data Loss:** Up to 1 hour (last backup)

---

## 🌍 Scenario 2: Complete Region Failure

**Priority:** P0 - Critical  
**Symptoms:**
- AWS region completely unavailable
- All services down
- Cannot access primary infrastructure

### Recovery Steps

#### Step 1: Activate DR Region

```bash
# Switch to DR region
export AWS_REGION=us-west-2
export AWS_DEFAULT_REGION=us-west-2

# Verify DR region is healthy
aws ec2 describe-availability-zones --region us-west-2
```

#### Step 2: Update DNS

```bash
# Prepare DNS change batch
cat > dr-dns-change.json <<EOF
{
  "Changes": [{
    "Action": "UPSERT",
    "ResourceRecordSet": {
      "Name": "api.riskcast.io",
      "Type": "A",
      "AliasTarget": {
        "HostedZoneId": "Z1BKCTXD74EZPE",
        "DNSName": "dr-lb.us-west-2.elb.amazonaws.com",
        "EvaluateTargetHealth": true
      }
    }
  }]
}
EOF

# Apply DNS change
aws route53 change-resource-record-sets \
  --hosted-zone-id Z3M3LMPEXAMPLE \
  --change-batch file://dr-dns-change.json

# Monitor DNS propagation
dig api.riskcast.io
```

#### Step 3: Restore Database in DR Region

```bash
# Download latest backup
python scripts/dr/restore.py --list

# Restore to DR database
export DATABASE_URL="postgresql://user:pass@dr-db.us-west-2.rds.amazonaws.com:5432/riskcast"

python scripts/dr/restore.py \
  --backup-key database/full/latest/backup.dump \
  --target-db riskcast_prod \
  --drop-existing \
  --yes
```

#### Step 4: Deploy Application to DR Cluster

```bash
# Switch kubectl context
kubectl config use-context dr-cluster-us-west-2

# Verify cluster access
kubectl get nodes

# Deploy application
kustomize build k8s/overlays/dr | kubectl apply -f -

# Deploy secrets
kubectl apply -f k8s/secrets/external-secrets.yaml

# Monitor deployment
kubectl get pods -n riskcast-prod -w
```

#### Step 5: Verify Services

```bash
# Wait for pods to be ready
kubectl wait --for=condition=ready pod -l app=riskcast-api -n riskcast-prod --timeout=300s

# Run smoke tests
./scripts/smoke-test.sh https://dr.api.riskcast.io

# Check all endpoints
curl https://dr.api.riskcast.io/health/live
curl https://dr.api.riskcast.io/health/ready
curl https://dr.api.riskcast.io/metrics
```

#### Step 6: Enable Monitoring

```bash
# Update monitoring targets
kubectl apply -f k8s/monitoring/servicemonitor.yaml

# Verify Prometheus scraping
kubectl logs -f -n monitoring -l app=prometheus

# Check Grafana dashboards
open https://grafana.riskcast.io
```

#### Step 7: Notify Users

```bash
# Update status page
curl -X POST https://api.statuspage.io/v1/pages/PAGE_ID/incidents \
  -H "Authorization: OAuth TOKEN" \
  -d '{"incident":{"name":"Region Failover","status":"investigating"}}'

# Send email to customers
python scripts/notifications/send_email.py \
  --template region-failover \
  --subject "Service Update: Regional Failover"
```

**Expected Duration:** 3-4 hours  
**Data Loss:** Up to 1 hour (last backup replicated to DR)

---

## 🗑️ Scenario 3: Data Loss (Accidental Deletion)

**Priority:** P1 - High  
**Symptoms:**
- Missing records reported by users
- Audit logs show unexpected deletions
- Data inconsistencies

### Recovery Steps

#### Step 1: Identify What Was Deleted

```bash
# Query audit logs
psql $DATABASE_URL <<EOF
SELECT 
  id, 
  action, 
  table_name, 
  record_id, 
  user_id, 
  created_at 
FROM audit_events 
WHERE action = 'DELETE' 
  AND created_at > NOW() - INTERVAL '2 hours'
ORDER BY created_at DESC;
EOF

# Export for analysis
psql $DATABASE_URL -c "COPY (SELECT * FROM audit_events WHERE action = 'DELETE' AND created_at > NOW() - INTERVAL '2 hours') TO STDOUT WITH CSV HEADER" > deleted_records.csv
```

#### Step 2: Determine Recovery Window

```bash
# Find time range
DELETION_TIME="2024-01-15 14:30:00"

# List backups before deletion
python scripts/dr/restore.py --list | grep "2024-01-15"
```

#### Step 3: Restore to Temporary Database

```bash
# Create temporary database for recovery
createdb riskcast_recovery

# Restore from pre-deletion backup
python scripts/dr/restore.py \
  --backup-key database/full/20240115_030000/backup.dump \
  --target-db riskcast_recovery \
  --yes
```

#### Step 4: Extract Deleted Data

```bash
# Connect to recovery database
psql postgresql://user:pass@host:5432/riskcast_recovery

# Export deleted records
\copy (SELECT * FROM quotes WHERE id IN (123, 456, 789)) TO '/tmp/recovered_quotes.csv' WITH CSV HEADER
\copy (SELECT * FROM policies WHERE id IN (111, 222, 333)) TO '/tmp/recovered_policies.csv' WITH CSV HEADER
```

#### Step 5: Restore Data to Production

```bash
# Connect to production database
psql $DATABASE_URL

# Import recovered data
\copy quotes FROM '/tmp/recovered_quotes.csv' WITH CSV HEADER
\copy policies FROM '/tmp/recovered_policies.csv' WITH CSV HEADER

# Verify counts
SELECT COUNT(*) FROM quotes WHERE id IN (123, 456, 789);
SELECT COUNT(*) FROM policies WHERE id IN (111, 222, 333);
```

#### Step 6: Verify Data Integrity

```bash
# Run integrity checks
python scripts/dr/verify.py --tables quotes,policies

# Check relationships
psql $DATABASE_URL -c "SELECT COUNT(*) FROM quotes q JOIN policies p ON q.policy_id = p.id;"
```

#### Step 7: Clean Up

```bash
# Drop recovery database
dropdb riskcast_recovery

# Archive deleted_records.csv for incident report
aws s3 cp deleted_records.csv s3://riskcast-incidents/20240115/
```

**Expected Duration:** 1-2 hours  
**Data Loss:** None (if backup exists before deletion)

---

## 🔒 Scenario 4: Security Breach

**Priority:** P0 - Critical  
**Symptoms:**
- Unauthorized access detected
- Suspicious activity in audit logs
- Security monitoring alerts
- Unusual database queries

### Recovery Steps

#### Step 1: IMMEDIATE - Isolate Systems

```bash
# Block all external traffic
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: emergency-lockdown
  namespace: riskcast-prod
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress: []
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
    ports:
    - protocol: TCP
      port: 53
EOF

# Verify lockdown
kubectl describe networkpolicy emergency-lockdown -n riskcast-prod
```

#### Step 2: Rotate ALL Credentials

```bash
# Rotate database passwords
python scripts/secrets/rotate.py --secret riskcast/production/database --yes

# Rotate API keys
python scripts/secrets/rotate.py --secret riskcast/production/app --key secret_key --yes

# Rotate external API keys
python scripts/secrets/rotate.py --all --yes

# Force logout all users (if applicable)
psql $DATABASE_URL -c "DELETE FROM user_sessions WHERE created_at < NOW();"
```

#### Step 3: Review Audit Logs

```bash
# Export recent audit logs
python scripts/security/audit-review.py \
  --since "2 hours ago" \
  --output /tmp/audit_review.json

# Check for suspicious patterns
python scripts/security/detect-anomalies.py \
  --input /tmp/audit_review.json

# Export for forensics
aws s3 cp /tmp/audit_review.json s3://riskcast-security/incidents/$(date +%Y%m%d)/
```

#### Step 4: Identify Compromised Data

```bash
# Check accessed records
psql $DATABASE_URL <<EOF
SELECT DISTINCT
  table_name,
  COUNT(*) as access_count,
  array_agg(DISTINCT user_id) as user_ids
FROM audit_events
WHERE created_at > NOW() - INTERVAL '24 hours'
  AND user_id IN (SELECT id FROM users WHERE is_suspicious = true)
GROUP BY table_name;
EOF
```

#### Step 5: Restore from Clean Backup (if needed)

```bash
# If data is compromised, restore from pre-breach backup
python scripts/dr/restore.py \
  --backup-key database/full/YYYYMMDD_HHMMSS/backup.dump \
  --target-db riskcast_clean \
  --yes

# Verify no breach indicators in restored data
python scripts/security/scan-database.py --database riskcast_clean
```

#### Step 6: Patch Vulnerabilities

```bash
# Update all dependencies
pip install --upgrade -r requirements.txt

# Rebuild Docker images
docker build -t riskcast-api:patched .

# Deploy patched version
kubectl set image deployment/riskcast-api riskcast-api=riskcast-api:patched -n riskcast-prod
```

#### Step 7: Restore Service

```bash
# Remove network lockdown
kubectl delete networkpolicy emergency-lockdown -n riskcast-prod

# Verify services
./scripts/smoke-test.sh https://api.riskcast.io

# Monitor for suspicious activity
kubectl logs -f -n riskcast-prod -l app=riskcast-api | grep -i "error\|warn\|unauthorized"
```

#### Step 8: Notify Affected Users

```bash
# Identify affected users
psql $DATABASE_URL -c "SELECT DISTINCT user_id FROM audit_events WHERE created_at > 'BREACH_TIME';" > affected_users.txt

# Send notifications (following data breach protocols)
python scripts/notifications/breach-notification.py \
  --users affected_users.txt \
  --template security-breach

# Update status page
curl -X POST https://api.statuspage.io/v1/pages/PAGE_ID/incidents \
  -H "Authorization: OAuth TOKEN" \
  -d '{"incident":{"name":"Security Incident","status":"resolved"}}'
```

#### Step 9: Follow Incident Response Plan

- Document timeline
- Preserve evidence
- Notify authorities (if required)
- Update security procedures
- Conduct post-mortem

**Expected Duration:** 4-8 hours  
**Data Loss:** Varies based on breach extent

---

## 🧪 Recovery Testing

### Test Schedule

| Test Type | Frequency | Duration | Last Tested |
|-----------|-----------|----------|-------------|
| Backup Verification | Daily | 5 min | Automatic |
| Restore Test (Dev) | Weekly | 30 min | Manual |
| Full DR Drill | Quarterly | 4 hours | Scheduled |
| Tabletop Exercise | Monthly | 1 hour | Team |

### Test Procedures

#### Weekly Restore Test

```bash
# 1. Create test database
createdb riskcast_test_restore

# 2. Restore latest backup
python scripts/dr/restore.py \
  --backup-key database/full/latest/backup.dump \
  --target-db riskcast_test_restore \
  --yes

# 3. Verify data
python scripts/dr/verify.py --database riskcast_test_restore --full

# 4. Cleanup
dropdb riskcast_test_restore

# 5. Document results
echo "$(date): Weekly restore test passed" >> /var/log/dr-tests.log
```

#### Quarterly DR Drill

Full disaster recovery simulation:

1. **Preparation** (30 min)
   - Notify team of drill
   - Prepare DR environment
   - Document current state

2. **Execution** (2 hours)
   - Simulate failure scenario
   - Execute recovery procedures
   - Time each step

3. **Verification** (1 hour)
   - Verify all services
   - Run full test suite
   - Check data integrity

4. **Debrief** (30 min)
   - Review timeline
   - Identify improvements
   - Update runbook

---

## 📞 Contact Information

### Emergency Contacts

| Role | Name | Phone | Email | Pager |
|------|------|-------|-------|-------|
| **On-Call Engineer** | Rotation | +1-555-0100 | oncall@riskcast.io | PagerDuty |
| **Database Admin** | DBA Team | +1-555-0101 | dba@riskcast.io | - |
| **Security Lead** | Security Team | +1-555-0102 | security@riskcast.io | - |
| **VP Engineering** | John Doe | +1-555-0103 | john@riskcast.io | - |
| **CTO** | Jane Smith | +1-555-0104 | jane@riskcast.io | - |

### Escalation Path

1. **Level 1:** On-Call Engineer (responds within 15 min)
2. **Level 2:** Team Lead (responds within 30 min)
3. **Level 3:** VP Engineering (responds within 1 hour)
4. **Level 4:** CTO (responds within 2 hours)

### External Contacts

| Service | Contact | Phone | Email |
|---------|---------|-------|-------|
| **AWS Support** | Enterprise | +1-206-266-4064 | - |
| **Database Vendor** | Postgres Pro | +1-555-0201 | support@postgres.pro |
| **Security Vendor** | SecOps Inc | +1-555-0202 | emergency@secops.com |

---

## 📋 Pre-Incident Checklist

Ensure these are always current:

- [ ] Backups running successfully
- [ ] Latest backup verified (< 24 hours old)
- [ ] DR environment accessible
- [ ] Credentials rotated regularly
- [ ] Runbook reviewed and updated
- [ ] Team trained on procedures
- [ ] Contact list current
- [ ] Monitoring and alerting working
- [ ] Disaster recovery drills scheduled

---

## 📊 Recovery Verification Checklist

After any recovery, verify:

- [ ] All health checks passing
- [ ] Database integrity verified
- [ ] Critical functionality working
- [ ] Monitoring active and alerting
- [ ] No error spikes in logs
- [ ] Performance metrics normal
- [ ] Security scans clean
- [ ] Smoke tests passing
- [ ] Stakeholders notified
- [ ] Incident documented

---

## 📚 Additional Resources

- **[Backup Script](../../scripts/dr/backup.py)** - Automated backup tool
- **[Restore Script](../../scripts/dr/restore.py)** - Database restore tool
- **[Migration Guide](../migrations/MIGRATION_GUIDE.md)** - Zero-downtime migrations
- **[Security Runbook](security-incident.md)** - Security incident procedures
- **[Monitoring Guide](../monitoring/MONITORING_GUIDE.md)** - System monitoring

---

**Document Owner:** Infrastructure Team  
**Review Frequency:** Quarterly  
**Last Reviewed:** January 24, 2026  
**Next Review:** April 24, 2026

---

**Remember:** In a disaster, stay calm, follow the runbook, and communicate with the team. 🚨
