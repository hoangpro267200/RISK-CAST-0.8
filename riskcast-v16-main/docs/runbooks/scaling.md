# Scaling Runbook

## 📋 Table of Contents

- [Auto-Scaling Configuration](#auto-scaling-configuration)
- [Manual Scaling](#manual-scaling)
- [Scaling Triggers](#scaling-triggers)
- [Capacity Planning](#capacity-planning)
- [Pre-Scaling Checklist](#pre-scaling-checklist)

---

## ⚙️ Auto-Scaling Configuration

### Current HPA Settings

**API Pods (riskcast-api):**
- Min replicas: **3**
- Max replicas: **20**
- Target CPU: **70%**
- Target Memory: **80%**
- Scale up policy: 100% of current pods (max 4 pods) every 15 seconds
- Scale down policy: 50% of current pods every 5 minutes

**Worker Pods (riskcast-worker):**
- Min replicas: **2**
- Max replicas: **10**
- Target CPU: **75%**
- Target Memory: **85%**
- Queue depth: **1000** messages

### View Current Configuration

```bash
# List all HPAs
kubectl get hpa -n riskcast-prod

# Detailed HPA status
kubectl describe hpa riskcast-api-hpa -n riskcast-prod

# Watch HPA in real-time
kubectl get hpa -n riskcast-prod -w
```

### Modify HPA Settings

```bash
# Update min/max replicas
kubectl patch hpa riskcast-api-hpa -n riskcast-prod \
  --patch '{"spec":{"minReplicas":5,"maxReplicas":30}}'

# Update target CPU
kubectl patch hpa riskcast-api-hpa -n riskcast-prod \
  --patch '{"spec":{"metrics":[{"type":"Resource","resource":{"name":"cpu","target":{"type":"Utilization","averageUtilization":60}}}]}}'

# Update target memory
kubectl patch hpa riskcast-api-hpa -n riskcast-prod \
  --patch '{"spec":{"metrics":[{"type":"Resource","resource":{"name":"memory","target":{"type":"Utilization","averageUtilization":75}}}]}}'
```

---

## 🎛️ Manual Scaling

### Scale API Pods

#### View Current State

```bash
# Current replica count
kubectl get deployment riskcast-api -n riskcast-prod

# Detailed status
kubectl describe deployment riskcast-api -n riskcast-prod | grep -A 5 "Replicas"

# Current HPA recommendation
kubectl get hpa riskcast-api-hpa -n riskcast-prod
```

#### Scale Up

```bash
# Manual scale (temporarily overrides HPA)
kubectl scale deployment/riskcast-api --replicas=10 -n riskcast-prod

# Verify scaling
kubectl get pods -n riskcast-prod -l app=riskcast-api

# Watch rollout
kubectl rollout status deployment/riskcast-api -n riskcast-prod

# Check if pods are ready
kubectl wait --for=condition=ready pod -l app=riskcast-api -n riskcast-prod --timeout=300s
```

**Note:** Manual scaling will be overridden by HPA after the next evaluation cycle (typically 15-30 seconds).

#### Temporarily Disable HPA

```bash
# Scale down HPA min to match desired count
kubectl patch hpa riskcast-api-hpa -n riskcast-prod \
  --patch '{"spec":{"minReplicas":10,"maxReplicas":10}}'

# Or delete HPA temporarily
kubectl delete hpa riskcast-api-hpa -n riskcast-prod

# Scale manually
kubectl scale deployment/riskcast-api --replicas=10 -n riskcast-prod

# Re-enable HPA later
kubectl apply -f k8s/base/hpa.yaml
```

#### Scale Down

```bash
# Manual scale down
kubectl scale deployment/riskcast-api --replicas=5 -n riskcast-prod

# Verify graceful shutdown
kubectl logs -n riskcast-prod -l app=riskcast-api --tail=50 | grep -i "shutdown"

# Check for connection draining
kubectl get pods -n riskcast-prod -l app=riskcast-api -w
```

---

### Scale Worker Pods

```bash
# View current workers
kubectl get deployment riskcast-worker -n riskcast-prod

# Scale up for batch processing
kubectl scale deployment/riskcast-worker --replicas=8 -n riskcast-prod

# Monitor worker queue
kubectl logs -n riskcast-prod -l app=riskcast-worker --since=5m | grep "Queue depth"

# Check job completion rate
kubectl logs -n riskcast-prod -l app=riskcast-worker --since=5m | grep "Processed" | wc -l
```

---

### Scale Database

#### Read Replicas (RDS)

**Create Read Replica:**

```bash
# Create read replica
aws rds create-db-instance-read-replica \
  --db-instance-identifier riskcast-replica-2 \
  --source-db-instance-identifier riskcast-primary \
  --db-instance-class db.r6g.xlarge \
  --availability-zone us-east-1b \
  --publicly-accessible false \
  --tags Key=Environment,Value=production Key=Purpose,Value=read-replica

# Monitor creation status
aws rds describe-db-instances \
  --db-instance-identifier riskcast-replica-2 \
  --query 'DBInstances[0].DBInstanceStatus'

# Wait for available status
aws rds wait db-instance-available \
  --db-instance-identifier riskcast-replica-2

# Get endpoint
aws rds describe-db-instances \
  --db-instance-identifier riskcast-replica-2 \
  --query 'DBInstances[0].Endpoint.Address'
```

**Update Application to Use Replica:**

```bash
# Add read replica endpoint to config
kubectl set env deployment/riskcast-api -n riskcast-prod \
  DATABASE_READ_URL="postgresql://user:pass@replica-endpoint:5432/riskcast"

# Verify application is using it
kubectl logs -n riskcast-prod -l app=riskcast-api --tail=20 | grep "read replica"
```

**Remove Read Replica:**

```bash
# Delete replica
aws rds delete-db-instance \
  --db-instance-identifier riskcast-replica-2 \
  --skip-final-snapshot

# Update application
kubectl set env deployment/riskcast-api -n riskcast-prod \
  DATABASE_READ_URL-
```

#### Vertical Scaling (Instance Class)

**⚠️ Requires maintenance window (5-30 minutes downtime)**

```bash
# View current instance class
aws rds describe-db-instances \
  --db-instance-identifier riskcast-primary \
  --query 'DBInstances[0].DBInstanceClass'

# Modify instance class (apply immediately for emergencies)
aws rds modify-db-instance \
  --db-instance-identifier riskcast-primary \
  --db-instance-class db.r6g.2xlarge \
  --apply-immediately

# Monitor modification
aws rds describe-db-instances \
  --db-instance-identifier riskcast-primary \
  --query 'DBInstances[0].[DBInstanceStatus,PendingModifiedValues]'

# For scheduled maintenance (preferred)
aws rds modify-db-instance \
  --db-instance-identifier riskcast-primary \
  --db-instance-class db.r6g.2xlarge \
  --no-apply-immediately \
  --preferred-maintenance-window sun:02:00-sun:04:00
```

#### Connection Pool Scaling

```bash
# Update max connections on database
aws rds modify-db-instance \
  --db-instance-identifier riskcast-primary \
  --max-connections 500 \
  --apply-immediately

# Update application connection pool
kubectl set env deployment/riskcast-api -n riskcast-prod \
  DATABASE_POOL_SIZE=50 \
  DATABASE_MAX_OVERFLOW=10

# Verify new settings
psql $DATABASE_URL -c "SHOW max_connections;"
```

---

### Scale Redis

#### Add Redis Replicas (ElastiCache)

```bash
# Increase replica count
aws elasticache increase-replica-count \
  --replication-group-id riskcast-redis \
  --new-replica-count 2 \
  --apply-immediately

# Monitor status
aws elasticache describe-replication-groups \
  --replication-group-id riskcast-redis \
  --query 'ReplicationGroups[0].Status'

# Wait for available
aws elasticache wait replication-group-available \
  --replication-group-id riskcast-redis
```

#### Vertical Scaling (Node Type)

```bash
# Modify node type (requires maintenance window)
aws elasticache modify-replication-group \
  --replication-group-id riskcast-redis \
  --cache-node-type cache.r6g.xlarge \
  --apply-immediately

# Monitor modification
aws elasticache describe-replication-groups \
  --replication-group-id riskcast-redis
```

#### Redis Memory Management

```bash
# Check memory usage
redis-cli -u $REDIS_URL INFO memory

# Set eviction policy
redis-cli -u $REDIS_URL CONFIG SET maxmemory-policy allkeys-lru

# Clear old keys (CAUTION)
redis-cli -u $REDIS_URL --scan --pattern "cache:*" | \
  head -1000 | \
  xargs redis-cli -u $REDIS_URL DEL
```

---

## 🎯 Scaling Triggers

### Automatic Scaling Triggers

| Metric | Threshold | Duration | Action | Priority |
|--------|-----------|----------|--------|----------|
| **CPU > 80%** | > 80% | 5 minutes | Scale up API pods | High |
| **Memory > 85%** | > 85% | 5 minutes | Scale up API pods | High |
| **Response Time p95 > 2s** | > 2 seconds | 5 minutes | Scale up API + investigate | High |
| **Error Rate > 5%** | > 5% | 5 minutes | Investigate + scale up | Critical |
| **Queue Depth > 1000** | > 1000 msgs | 10 minutes | Scale up workers | Medium |
| **DB Connections > 80%** | > 80% of max | 15 minutes | Add read replica | High |
| **Redis Memory > 90%** | > 90% | 10 minutes | Scale Redis or evict keys | High |
| **Request Rate > 500 rps** | > 500 req/s | 5 minutes | Scale up API | Medium |

### Manual Scaling Triggers

| Event | Recommended Action | Timing |
|-------|-------------------|--------|
| **Planned Marketing Campaign** | 2x API pods, verify cache | 1 day before |
| **Product Launch** | 3x API pods, add read replica | 1 day before |
| **Black Friday / Cyber Monday** | Max scale all services | 1 week before |
| **Known Traffic Spike** | Pre-scale based on estimate | 4 hours before |
| **Load Test** | Isolate environment or scale | Before test |
| **Database Maintenance** | Add read replica | Before maintenance |

### Monitoring Commands

```bash
# Check current load
kubectl top pods -n riskcast-prod

# Watch metrics in real-time
watch -n 5 'kubectl top pods -n riskcast-prod'

# Check request rate
kubectl logs -n riskcast-prod -l app=riskcast-api --since=1m | \
  jq -r 'select(.http_status) | 1' | wc -l | awk '{print $1/60 " req/s"}'

# Check error rate
kubectl logs -n riskcast-prod -l app=riskcast-api --since=5m | \
  jq -r 'select(.http_status >= 500) | 1' | wc -l

# Check queue depth
kubectl exec -it -n riskcast-prod deployment/riskcast-worker -- \
  redis-cli -u $REDIS_URL LLEN task_queue
```

---

## 📊 Capacity Planning

### Load Levels

| Load Level | Description | API Pods | Workers | DB Class | Redis | Estimated RPS |
|------------|-------------|----------|---------|----------|-------|---------------|
| **Normal** | Regular business hours | 3 | 2 | db.r6g.large | cache.r6g.large | 50-100 |
| **High** | Peak hours / marketing | 5-10 | 4 | db.r6g.xlarge | cache.r6g.xlarge | 200-300 |
| **Peak** | Product launch / event | 10-20 | 8 | db.r6g.2xlarge | cache.r6g.2xlarge | 500-800 |
| **Emergency** | Unexpected viral traffic | 20+ | 10+ | db.r6g.4xlarge | cache.r6g.4xlarge | 1000+ |

### Resource Requirements per Load Level

#### API Pods

| Level | CPU Request | Memory Request | CPU Limit | Memory Limit |
|-------|-------------|----------------|-----------|--------------|
| Normal | 500m | 512Mi | 1000m | 1Gi |
| High | 750m | 768Mi | 1500m | 1.5Gi |
| Peak | 1000m | 1Gi | 2000m | 2Gi |
| Emergency | 1500m | 1.5Gi | 3000m | 3Gi |

#### Database Sizing

| Level | Instance Class | vCPUs | Memory | Storage | Connections |
|-------|---------------|-------|---------|---------|-------------|
| Normal | db.r6g.large | 2 | 16 GB | 100 GB | 100 |
| High | db.r6g.xlarge | 4 | 32 GB | 250 GB | 200 |
| Peak | db.r6g.2xlarge | 8 | 64 GB | 500 GB | 400 |
| Emergency | db.r6g.4xlarge | 16 | 128 GB | 1 TB | 800 |

### Cost Estimates (Monthly)

| Component | Normal | High | Peak | Emergency |
|-----------|--------|------|------|-----------|
| API Pods (EKS) | $200 | $400 | $800 | $1,500 |
| Workers | $100 | $200 | $400 | $600 |
| Database | $300 | $600 | $1,200 | $2,400 |
| Redis | $150 | $300 | $600 | $1,200 |
| **Total Est.** | **$750** | **$1,500** | **$3,000** | **$5,700** |

*Note: Estimates only, actual costs vary by region and usage*

---

## ✅ Pre-Scaling Checklist

### Before Scaling Up

- [ ] **Check current resource utilization**
  ```bash
  kubectl top pods -n riskcast-prod
  kubectl top nodes
  ```

- [ ] **Verify node capacity**
  ```bash
  kubectl describe nodes | grep -A 5 "Allocated resources"
  ```

- [ ] **Check database connection pool limits**
  ```bash
  psql $DATABASE_URL -c "SHOW max_connections;"
  psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity;"
  ```

- [ ] **Verify Redis has capacity**
  ```bash
  redis-cli -u $REDIS_URL INFO memory
  redis-cli -u $REDIS_URL INFO stats
  ```

- [ ] **Update rate limits if needed**
  ```bash
  kubectl set env deployment/riskcast-api -n riskcast-prod \
    RATE_LIMIT_PER_MINUTE=1000
  ```

- [ ] **Check external service quotas**
  - Tomorrow.io API quota
  - Marine Traffic API quota
  - AWS service limits

- [ ] **Verify monitoring is working**
  ```bash
  curl -s http://prometheus:9090/-/healthy
  kubectl logs -n monitoring -l app=prometheus --tail=20
  ```

- [ ] **Notify team of scaling event**
  ```
  #infrastructure channel:
  "Scaling up API pods from 3 to 10 for [reason]. ETA: 5 minutes. @oncall"
  ```

- [ ] **Prepare rollback plan**
  - Document current state
  - Have rollback commands ready
  - Know how to scale back down

### During Scaling

- [ ] **Monitor pod startup**
  ```bash
  kubectl get pods -n riskcast-prod -w
  kubectl logs -f -n riskcast-prod -l app=riskcast-api
  ```

- [ ] **Check readiness probes**
  ```bash
  kubectl describe pods -n riskcast-prod | grep -A 3 "Readiness"
  ```

- [ ] **Verify load distribution**
  ```bash
  kubectl top pods -n riskcast-prod
  ```

- [ ] **Monitor error rates**
  ```bash
  kubectl logs -n riskcast-prod -l app=riskcast-api --since=5m | grep ERROR | wc -l
  ```

- [ ] **Check response times**
  ```bash
  kubectl logs -n riskcast-prod -l app=riskcast-api --since=5m | \
    jq -r 'select(.duration) | .duration' | \
    awk '{sum+=$1; n++} END {print "Avg:", sum/n, "seconds"}'
  ```

### After Scaling

- [ ] **Verify all pods are ready**
  ```bash
  kubectl get pods -n riskcast-prod -l app=riskcast-api
  ```

- [ ] **Run smoke tests**
  ```bash
  ./scripts/smoke-test.sh https://api.riskcast.io
  ```

- [ ] **Check metrics dashboard**
  - CPU utilization decreased
  - Memory utilization stable
  - Response times improved
  - Error rate normal

- [ ] **Verify database connections distributed**
  ```bash
  psql $DATABASE_URL -c "SELECT client_addr, count(*) FROM pg_stat_activity GROUP BY client_addr;"
  ```

- [ ] **Document scaling action**
  - What was scaled
  - Why it was scaled
  - Results (before/after metrics)
  - Issues encountered

- [ ] **Update capacity plan if needed**

---

## 📈 Scaling Best Practices

### DO

✅ **Scale gradually**
- Add 50-100% of current capacity at a time
- Wait 5-10 minutes between scaling actions
- Monitor effects before continuing

✅ **Scale horizontally first**
- Add more pods before increasing pod size
- Better availability and fault tolerance
- More granular control

✅ **Pre-scale for known events**
- Marketing campaigns
- Product launches
- Expected traffic spikes

✅ **Monitor continuously**
- Set up alerts for scaling events
- Track scaling history
- Review capacity monthly

✅ **Test scaling procedures**
- Practice in staging
- Document scaling times
- Verify rollback procedures

### DON'T

❌ **Don't scale reactively without investigation**
- Understand why you need to scale
- Fix underlying issues if possible
- Scaling might mask problems

❌ **Don't exceed node capacity**
- Check node resources first
- Add nodes if needed
- Use cluster autoscaler

❌ **Don't forget about dependencies**
- Database connection limits
- External API quotas
- Network bandwidth

❌ **Don't scale down too aggressively**
- Leave headroom for bursts
- Consider time zones and patterns
- Use gradual scale-down

❌ **Don't ignore costs**
- Monitor spending
- Right-size resources
- Use spot instances for workers

---

## 🔄 Auto-Scaling Edge Cases

### HPA Not Scaling

**Symptoms:** Metrics show high load but HPA not scaling up

**Troubleshooting:**
```bash
# Check HPA status
kubectl describe hpa riskcast-api-hpa -n riskcast-prod

# Check metrics server
kubectl top nodes
kubectl top pods -n riskcast-prod

# Check metrics server logs
kubectl logs -n kube-system -l k8s-app=metrics-server

# Force HPA recalculation
kubectl patch hpa riskcast-api-hpa -n riskcast-prod \
  --patch '{"metadata":{"annotations":{"autoscaling.alpha.kubernetes.io/current-metrics":"[]"}}}'
```

### Pod Stuck in Pending

**Symptoms:** New pods created but stuck in Pending state

**Troubleshooting:**
```bash
# Check pod events
kubectl describe pod <pod-name> -n riskcast-prod

# Check node resources
kubectl describe nodes | grep -A 5 "Allocated resources"

# Add more nodes if needed
aws eks update-nodegroup-config \
  --cluster-name riskcast-prod \
  --nodegroup-name workers \
  --scaling-config minSize=5,maxSize=20,desiredSize=10
```

### Rapid Scaling (Flapping)

**Symptoms:** HPA scaling up and down rapidly

**Fix:**
```bash
# Increase stabilization window
kubectl patch hpa riskcast-api-hpa -n riskcast-prod \
  --patch '{"spec":{"behavior":{"scaleDown":{"stabilizationWindowSeconds":300}}}}'

# Adjust target utilization
kubectl patch hpa riskcast-api-hpa -n riskcast-prod \
  --patch '{"spec":{"metrics":[{"type":"Resource","resource":{"name":"cpu","target":{"type":"Utilization","averageUtilization":60}}}]}}'
```

---

**Last Updated:** January 24, 2026  
**Version:** 1.0.0  
**Owner:** Infrastructure Team

**Review scaling procedures quarterly and after major traffic events!**
