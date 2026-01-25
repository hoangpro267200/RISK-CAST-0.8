# Incident Response Runbook

## 📋 Table of Contents

- [Severity Levels](#severity-levels)
- [Incident Commander Responsibilities](#incident-commander-responsibilities)
- [Response Procedures](#response-procedures)
- [Escalation Path](#escalation-path)
- [Useful Commands Reference](#useful-commands-reference)

---

## 🚨 Severity Levels

| Level | Description | Response Time | Examples | Impact |
|-------|-------------|---------------|----------|--------|
| **SEV-1 Critical** | Complete service outage | **15 minutes** | - Complete API outage<br>- Data breach/security incident<br>- Database corruption<br>- Mass data loss | All customers affected, complete service unavailability |
| **SEV-2 Major** | Partial service degradation | **30 minutes** | - Partial API outage<br>- Degraded performance (>5s p95)<br>- Important feature down<br>- High error rate (>5%) | Multiple customers affected, major functionality impaired |
| **SEV-3 Minor** | Non-critical feature issue | **2 hours** | - Single endpoint down<br>- Minor performance degradation<br>- Non-critical feature bug | Some customers affected, workarounds available |
| **SEV-4 Low** | Minor issues | **24 hours** | - Cosmetic bugs<br>- Documentation issues<br>- Minor UI glitches | Few customers affected, minimal impact |

---

## 👔 Incident Commander Responsibilities

The Incident Commander (IC) is responsible for:

### Primary Duties

1. **Declare incident and severity**
   - Assess impact and assign SEV level
   - Create incident tracking ticket
   - Start incident timeline

2. **Coordinate response team**
   - Identify required specialists
   - Assign investigation tasks
   - Manage parallel work streams

3. **Manage communication**
   - Create incident channel
   - Send regular status updates
   - Coordinate with support/sales
   - Update status page

4. **Track timeline**
   - Document all actions taken
   - Record decision points
   - Note time of key events

5. **Initiate post-mortem**
   - Schedule within 24-48 hours
   - Ensure action items are tracked
   - Review blameless culture

### IC Rotation

- Primary: On-call engineer
- Backup: Team lead
- Escalation: Engineering manager

---

## 🔥 Response Procedures

### Step 1: Detection & Triage (First 5 minutes)

#### Quick Health Assessment

```bash
# Check all pods status
kubectl get pods -n riskcast-prod

# Check resource usage
kubectl top pods -n riskcast-prod

# Check recent deployments
kubectl rollout history deployment/riskcast-api -n riskcast-prod
```

#### Find Recent Errors

```bash
# Last 10 minutes of errors
kubectl logs -n riskcast-prod -l app=riskcast-api --since=10m | grep ERROR

# Error count
kubectl logs -n riskcast-prod -l app=riskcast-api --since=10m | grep ERROR | wc -l

# Unique error types
kubectl logs -n riskcast-prod -l app=riskcast-api --since=10m | \
  jq -r 'select(.level == "ERROR") | .extra.error_type' | \
  sort | uniq -c | sort -rn
```

#### Check Metrics

```bash
# Error rate
curl -s 'http://prometheus:9090/api/v1/query?query=rate(riskcast_http_requests_total{status=~"5.."}[5m])' | jq .

# Request rate
curl -s 'http://prometheus:9090/api/v1/query?query=rate(riskcast_http_requests_total[5m])' | jq .

# Response time p95
curl -s 'http://prometheus:9090/api/v1/query?query=histogram_quantile(0.95,rate(riskcast_http_request_duration_seconds_bucket[5m]))' | jq .
```

#### Check External Services

```bash
# Database connection pool
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';"

# Redis status
redis-cli -u $REDIS_URL ping

# External API status
curl -s https://api.tomorrow.io/v4/weather/health
curl -s https://api.marinetraffic.com/health
```

---

### Step 2: Communication (First 10 minutes)

#### Create Incident Channel

Create Slack channel: `#incident-YYYYMMDD-brief-description`

Example: `#incident-20260124-api-outage`

#### Post Initial Update

```
🚨 INCIDENT DECLARED

Severity: SEV-X
Issue: [Brief one-line description]
Impact: [What users are experiencing]
Incident Commander: @[name]
Status: Investigating

Timeline:
- HH:MM: Incident detected
- HH:MM: IC declared, team assembling
- HH:MM: [Next update in 15 minutes]
```

#### Update Frequency

| Severity | Update Frequency | Channels |
|----------|------------------|----------|
| SEV-1 | Every 15 minutes | Slack, Status Page, Email |
| SEV-2 | Every 30 minutes | Slack, Status Page |
| SEV-3 | Every 1-2 hours | Slack |
| SEV-4 | As needed | Ticket only |

#### Update Status Page

```bash
# Update status page (example using StatusPage.io API)
curl -X POST https://api.statuspage.io/v1/pages/PAGE_ID/incidents \
  -H "Authorization: OAuth TOKEN" \
  -d '{
    "incident": {
      "name": "API Performance Degradation",
      "status": "investigating",
      "body": "We are investigating elevated error rates",
      "impact_override": "major"
    }
  }'
```

---

### Step 3: Mitigation (Ongoing)

#### Scenario 1: High Error Rate

**Symptoms:** Error rate > 5%, 500 errors in logs

**Investigation:**
```bash
# Check recent deployments
kubectl rollout history deployment/riskcast-api -n riskcast-prod

# Check pod events
kubectl describe pods -n riskcast-prod | grep -A 10 Events

# Check application logs
kubectl logs -n riskcast-prod -l app=riskcast-api --tail=100 | grep ERROR
```

**Mitigation:**
```bash
# Option 1: Rollback to previous version
kubectl rollout undo deployment/riskcast-api -n riskcast-prod

# Option 2: Roll back to specific revision
kubectl rollout undo deployment/riskcast-api -n riskcast-prod --to-revision=5

# Monitor rollback
kubectl rollout status deployment/riskcast-api -n riskcast-prod

# Verify error rate decreased
kubectl logs -n riskcast-prod -l app=riskcast-api --since=5m | grep ERROR | wc -l
```

---

#### Scenario 2: Database Issues

**Symptoms:** Slow queries, connection errors, timeouts

**Investigation:**
```bash
# Check active connections
psql $DATABASE_URL -c "SELECT count(*), state FROM pg_stat_activity GROUP BY state;"

# Find long-running queries
psql $DATABASE_URL -c "
SELECT pid, now() - query_start AS duration, state, query 
FROM pg_stat_activity 
WHERE state != 'idle' 
  AND query_start < NOW() - INTERVAL '10 seconds'
ORDER BY duration DESC
LIMIT 10;
"

# Check for locks
psql $DATABASE_URL -c "
SELECT blocked_locks.pid AS blocked_pid,
       blocking_locks.pid AS blocking_pid,
       blocked_activity.query AS blocked_statement
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
WHERE NOT blocked_locks.granted;
"
```

**Mitigation:**
```bash
# Kill long-running queries (CAUTION: can affect users)
psql $DATABASE_URL -c "
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE state = 'active' 
  AND query_start < NOW() - INTERVAL '5 minutes'
  AND query NOT LIKE '%pg_%'
  AND pid != pg_backend_pid();
"

# If database is completely locked, restart (LAST RESORT)
kubectl rollout restart statefulset/postgres -n riskcast-prod

# Add read replica if needed
aws rds create-db-instance-read-replica \
  --db-instance-identifier riskcast-replica-emergency \
  --source-db-instance-identifier riskcast-primary
```

---

#### Scenario 3: Memory/CPU Issues

**Symptoms:** OOMKilled pods, high CPU usage, slow responses

**Investigation:**
```bash
# Check resource usage
kubectl top pods -n riskcast-prod

# Check pod events for OOM
kubectl get events -n riskcast-prod | grep OOM

# Check node resources
kubectl top nodes

# Describe pod for resource limits
kubectl describe pod -n riskcast-prod <pod-name> | grep -A 5 "Limits\|Requests"
```

**Mitigation:**
```bash
# Option 1: Scale horizontally
kubectl scale deployment/riskcast-api --replicas=8 -n riskcast-prod

# Option 2: Restart pods gracefully (rolling restart)
kubectl rollout restart deployment/riskcast-api -n riskcast-prod

# Option 3: Increase pod resources temporarily
kubectl patch deployment riskcast-api -n riskcast-prod \
  --patch '{"spec":{"template":{"spec":{"containers":[{"name":"riskcast-api","resources":{"limits":{"memory":"2Gi","cpu":"2000m"}}}]}}}}'

# Monitor restart
kubectl get pods -n riskcast-prod -w
```

---

#### Scenario 4: External Service Outage

**Symptoms:** Timeouts to external APIs, external API errors

**Investigation:**
```bash
# Check external service status
curl -v https://api.tomorrow.io/v4/weather/health
curl -v https://api.marinetraffic.com/health

# Check DNS resolution
nslookup api.tomorrow.io
nslookup api.marinetraffic.com

# Check our outbound connections
kubectl exec -it -n riskcast-prod deployment/riskcast-api -- \
  curl -v https://api.tomorrow.io/v4/weather/health
```

**Mitigation:**
```bash
# Option 1: Enable circuit breaker (if configured)
kubectl set env deployment/riskcast-api -n riskcast-prod \
  ENABLE_CIRCUIT_BREAKER=true

# Option 2: Use cached data
kubectl set env deployment/riskcast-api -n riskcast-prod \
  USE_CACHED_WEATHER=true

# Option 3: Fail gracefully
kubectl set env deployment/riskcast-api -n riskcast-prod \
  WEATHER_REQUIRED=false

# Notify users via status page
curl -X POST https://api.statuspage.io/v1/pages/PAGE_ID/incidents \
  -H "Authorization: OAuth TOKEN" \
  -d '{"incident":{"name":"Weather Data Delayed","status":"identified","impact_override":"minor"}}'
```

---

#### Scenario 5: Security Incident

**Symptoms:** Unauthorized access, suspicious activity, security alerts

**Immediate Actions:**
```bash
# 1. STOP - Don't panic, assess the situation
# 2. ISOLATE - Prevent further damage
# 3. DOCUMENT - Record everything

# Block suspicious IPs (example)
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: emergency-block-suspicious
  namespace: riskcast-prod
spec:
  podSelector:
    matchLabels:
      app: riskcast-api
  policyTypes:
  - Ingress
  ingress:
  - from:
    - ipBlock:
        cidr: 0.0.0.0/0
        except:
        - <suspicious_ip>/32
EOF

# Rotate all credentials IMMEDIATELY
python scripts/secrets/rotate.py --all --yes

# Check audit logs for unauthorized access
psql $DATABASE_URL -c "
SELECT * FROM audit_events 
WHERE action IN ('LOGIN', 'ACCESS', 'DELETE', 'UPDATE')
  AND created_at > NOW() - INTERVAL '2 hours'
ORDER BY created_at DESC
LIMIT 100;
"

# Export logs for forensics
kubectl logs -n riskcast-prod --all-containers --since=24h > incident-logs-$(date +%Y%m%d).log

# Notify security team IMMEDIATELY
# Follow security incident response plan
```

---

### Step 4: Resolution (Verification)

#### Verify Fix is Working

```bash
# 1. Check error rate returned to normal
kubectl logs -n riskcast-prod -l app=riskcast-api --since=10m | grep ERROR | wc -l

# 2. Run smoke tests
./scripts/smoke-test.sh https://api.riskcast.io

# 3. Check metrics
curl -s 'http://prometheus:9090/api/v1/query?query=rate(riskcast_http_requests_total{status=~"5.."}[5m])' | jq .

# 4. Test critical endpoints
curl -s https://api.riskcast.io/api/v3/quotes/ -H "Authorization: Bearer $TOKEN"
curl -s https://api.riskcast.io/api/v3/risk/analyze -H "Authorization: Bearer $TOKEN"

# 5. Check with real user (if possible)
```

#### Update Communications

```
✅ INCIDENT RESOLVED

Resolution: [What was done to fix the issue]
Root Cause: [Brief explanation]
Impact Duration: [Start time - End time]
Affected Users: [Estimate]
Next Steps: [Post-mortem scheduled, follow-up actions]

Thank you for your patience during this incident.
```

#### Update Status Page

```bash
curl -X PATCH https://api.statuspage.io/v1/pages/PAGE_ID/incidents/INCIDENT_ID \
  -H "Authorization: OAuth TOKEN" \
  -d '{
    "incident": {
      "status": "resolved",
      "body": "The issue has been resolved. All systems are operational."
    }
  }'
```

#### Close Incident Channel

Post final summary in channel, then archive:
```
📋 INCIDENT SUMMARY

Duration: [X hours Y minutes]
Root Cause: [Brief explanation]
Resolution: [What fixed it]
Action Items: [Link to post-mortem doc]

Post-Mortem: Scheduled for [date/time]

This channel will be archived in 24 hours.
```

---

### Step 5: Post-Mortem (Within 24-48 hours)

#### Post-Mortem Template

Use template at `docs/templates/postmortem.md`

#### Required Sections

1. **Executive Summary**
   - What happened (1-2 sentences)
   - Impact (users/revenue affected)
   - Duration

2. **Timeline**
   - All events with timestamps
   - Actions taken
   - Communication sent

3. **Root Cause Analysis**
   - Technical root cause
   - Why it wasn't caught earlier
   - Why monitoring didn't alert sooner

4. **Impact Assessment**
   - Users affected
   - Requests failed
   - Revenue impact (if applicable)
   - Reputation impact

5. **What Went Well**
   - Fast detection
   - Good communication
   - Effective mitigation

6. **What Went Wrong**
   - Missed alerts
   - Slow response
   - Communication gaps

7. **Action Items**
   - [ ] Preventive measures (P0)
   - [ ] Detection improvements (P1)
   - [ ] Process improvements (P2)
   - [ ] Documentation updates (P3)

8. **Lessons Learned**
   - Technical lessons
   - Process lessons
   - Team lessons

#### Post-Mortem Meeting

- Schedule within 24-48 hours
- Required attendees: IC, key responders, engineering manager
- Optional: Support, sales, product
- Duration: 60 minutes
- **BLAMELESS** - Focus on systems, not people

---

## 📊 Escalation Path

```
┌─────────────────────────────────────────────────────────┐
│            Escalation Hierarchy                          │
└─────────────────────────────────────────────────────────┘

Level 1: On-Call Engineer
  ↓ (if unresolved after 30 min for SEV-1, 1 hour for SEV-2)

Level 2: Team Lead / Senior Engineer
  ↓ (if unresolved after 1 hour for SEV-1, 2 hours for SEV-2)

Level 3: Engineering Manager
  ↓ (if major incident or multi-system failure)

Level 4: VP Engineering
  ↓ (if company-wide impact or external communication needed)

Level 5: CTO
```

### When to Escalate

| Situation | Action |
|-----------|--------|
| SEV-1 > 30 min unresolved | Escalate to Team Lead |
| SEV-1 > 1 hour unresolved | Escalate to Eng Manager |
| Data breach/security | Escalate immediately to VP Eng + Security |
| Customer threatening to leave | Escalate to Eng Manager + Sales |
| Media attention | Escalate to VP Eng + Communications |
| Need executive decision | Escalate to appropriate level |

### Contact Information

| Role | Name | Phone | Email | Slack |
|------|------|-------|-------|-------|
| On-Call Rotation | Current | +1-555-0100 | oncall@riskcast.io | @oncall |
| Team Lead | [Name] | +1-555-0101 | lead@riskcast.io | @lead |
| Eng Manager | [Name] | +1-555-0102 | manager@riskcast.io | @manager |
| VP Engineering | [Name] | +1-555-0103 | vp@riskcast.io | @vpeng |
| CTO | [Name] | +1-555-0104 | cto@riskcast.io | @cto |
| Security Lead | [Name] | +1-555-0105 | security@riskcast.io | @security |
| Database Admin | [Name] | +1-555-0106 | dba@riskcast.io | @dba |

---

## 🔧 Useful Commands Reference

### Quick Health Check

```bash
# All-in-one health check
./scripts/health-check.sh --full

# Pod status
kubectl get pods -n riskcast-prod -o wide

# Recent events
kubectl get events -n riskcast-prod --sort-by='.lastTimestamp' | tail -20

# Application logs (last 100 lines)
kubectl logs -n riskcast-prod -l app=riskcast-api --tail=100
```

### Error Analysis

```bash
# Count errors in last hour
kubectl logs -n riskcast-prod -l app=riskcast-api --since=1h | grep ERROR | wc -l

# Get errors with context (5 lines before and after)
kubectl logs -n riskcast-prod -l app=riskcast-api --since=30m | grep -B5 -A5 ERROR

# Group errors by type
kubectl logs -n riskcast-prod -l app=riskcast-api --since=1h | \
  jq -r 'select(.level == "ERROR") | .extra.error_type' | \
  sort | uniq -c | sort -rn | head -10
```

### Request Tracing

```bash
# Find all logs for a specific request
kubectl logs -n riskcast-prod --all-containers --since=1h | \
  jq -r 'select(.request_id == "abc123")' | jq .

# Find all logs for a trace
kubectl logs -n riskcast-prod --all-containers --since=1h | \
  jq -r 'select(.trace_id == "xyz789")' | jq .
```

### Database Quick Stats

```bash
# Connection count by state
psql $DATABASE_URL -c "SELECT state, count(*) FROM pg_stat_activity GROUP BY state;"

# Top 10 largest tables
psql $DATABASE_URL -c "
SELECT relname, n_live_tup, n_dead_tup, 
       pg_size_pretty(pg_total_relation_size(relid)) as size
FROM pg_stat_user_tables 
ORDER BY n_live_tup DESC 
LIMIT 10;
"

# Slow queries (> 5 seconds)
psql $DATABASE_URL -c "
SELECT pid, now() - query_start as duration, query 
FROM pg_stat_activity 
WHERE state = 'active' 
  AND query_start < NOW() - INTERVAL '5 seconds'
ORDER BY duration DESC;
"
```

### External Service Checks

```bash
# Check weather API
curl -w "\nTime: %{time_total}s\nStatus: %{http_code}\n" \
  -s https://api.tomorrow.io/v4/weather/health

# Check port API
curl -w "\nTime: %{time_total}s\nStatus: %{http_code}\n" \
  -s https://api.marinetraffic.com/health

# Check DNS
dig api.tomorrow.io +short
dig api.marinetraffic.com +short
```

### Performance Metrics

```bash
# Request rate (requests per second)
kubectl logs -n riskcast-prod -l app=riskcast-api --since=1m | \
  jq -r 'select(.http_status) | 1' | wc -l | awk '{print $1/60}'

# Average response time
kubectl logs -n riskcast-prod -l app=riskcast-api --since=5m | \
  jq -r 'select(.duration) | .duration' | \
  awk '{sum+=$1; n++} END {print sum/n}'

# Error rate
kubectl logs -n riskcast-prod -l app=riskcast-api --since=5m | \
  jq -r 'select(.http_status >= 500) | 1' | wc -l
```

---

## 📝 Incident Communication Templates

### Initial Notification (SEV-1/SEV-2)

```
🚨 INCIDENT: [Brief Title]

Severity: SEV-X
Status: Investigating
Impact: [What users are experiencing]
Started: [Time]
IC: @[name]

We are investigating and will update every [15/30] minutes.

Status Page: https://status.riskcast.io
```

### Progress Update

```
📊 UPDATE [HH:MM]

Current Status: [Investigating/Identified/Monitoring]
Actions Taken: [What we've done]
Next Steps: [What we're doing next]
ETA: [If known]

Next update: [Time]
```

### Resolution Notification

```
✅ RESOLVED [HH:MM]

The incident has been resolved.

Summary: [What happened]
Resolution: [What fixed it]
Duration: [Total time]
Impact: [Users/requests affected]

Post-Mortem: Will be shared within 48 hours

Thank you for your patience.
```

---

**Last Updated:** January 24, 2026  
**Version:** 1.0.0  
**Owner:** Infrastructure Team

**Review this runbook quarterly and after each major incident!**
