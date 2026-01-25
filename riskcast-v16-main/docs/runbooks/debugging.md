# Debugging Runbook

## 📋 Table of Contents

- [Log Analysis](#log-analysis)
- [Request Tracing](#request-tracing)
- [Database Debugging](#database-debugging)
- [API Debugging](#api-debugging)
- [Memory Debugging](#memory-debugging)
- [Performance Debugging](#performance-debugging)
- [Common Issues](#common-issues)

---

## 📊 Log Analysis

### Find Errors

#### Recent Errors

```bash
# Last hour of errors
kubectl logs -n riskcast-prod -l app=riskcast-api --since=1h | \
  jq -r 'select(.level == "ERROR") | "\(.timestamp) \(.message)"'

# Count errors
kubectl logs -n riskcast-prod -l app=riskcast-api --since=1h | \
  jq -r 'select(.level == "ERROR")' | wc -l

# Errors with full details
kubectl logs -n riskcast-prod -l app=riskcast-api --since=1h | \
  jq -r 'select(.level == "ERROR")' | jq .
```

#### Errors by Type

```bash
# Group errors by type
kubectl logs -n riskcast-prod -l app=riskcast-api --since=1h | \
  jq -r 'select(.level == "ERROR") | .extra.error_type' | \
  sort | uniq -c | sort -rn

# Errors by endpoint
kubectl logs -n riskcast-prod -l app=riskcast-api --since=1h | \
  jq -r 'select(.level == "ERROR") | .extra.endpoint' | \
  sort | uniq -c | sort -rn

# Errors by user
kubectl logs -n riskcast-prod -l app=riskcast-api --since=1h | \
  jq -r 'select(.level == "ERROR") | .extra.user_id' | \
  sort | uniq -c | sort -rn | head -10
```

#### Errors with Context

```bash
# Get errors with surrounding logs (5 lines before and after)
kubectl logs -n riskcast-prod -l app=riskcast-api --since=30m | \
  grep -B5 -A5 "ERROR"

# Get specific error message with context
kubectl logs -n riskcast-prod -l app=riskcast-api --since=1h | \
  grep -B10 -A10 "KeyError: 'premium'"

# Save errors to file for analysis
kubectl logs -n riskcast-prod -l app=riskcast-api --since=24h | \
  jq -r 'select(.level == "ERROR")' > errors-$(date +%Y%m%d).json
```

### Filter Logs by Severity

```bash
# All warnings and errors
kubectl logs -n riskcast-prod -l app=riskcast-api --since=1h | \
  jq -r 'select(.level == "WARNING" or .level == "ERROR")'

# Only critical errors
kubectl logs -n riskcast-prod -l app=riskcast-api --since=1h | \
  jq -r 'select(.level == "ERROR" and .extra.severity == "critical")'

# Info logs for specific module
kubectl logs -n riskcast-prod -l app=riskcast-api --since=1h | \
  jq -r 'select(.module == "app.pricing.engine")'
```

### Search Logs by Field

```bash
# Find by user ID
kubectl logs -n riskcast-prod -l app=riskcast-api --since=1h | \
  jq -r 'select(.extra.user_id == "user-123")'

# Find by tenant
kubectl logs -n riskcast-prod -l app=riskcast-api --since=1h | \
  jq -r 'select(.extra.tenant_id == "tenant-456")'

# Find by endpoint
kubectl logs -n riskcast-prod -l app=riskcast-api --since=1h | \
  jq -r 'select(.extra.endpoint == "/api/v3/quotes/")'

# Find slow requests (> 2 seconds)
kubectl logs -n riskcast-prod -l app=riskcast-api --since=1h | \
  jq -r 'select(.duration > 2)'
```

---

## 🔍 Request Tracing

### Trace by Request ID

```bash
# Find all logs for a specific request
kubectl logs -n riskcast-prod --all-containers --since=1h | \
  jq -r 'select(.request_id == "req_abc123")'

# Follow request through multiple services
kubectl logs -n riskcast-prod --all-containers --since=1h | \
  jq -r 'select(.request_id == "req_abc123") | "\(.timestamp) [\(.service)] \(.message)"'

# Get request timeline
kubectl logs -n riskcast-prod --all-containers --since=1h | \
  jq -r 'select(.request_id == "req_abc123") | "\(.timestamp) \(.duration // 0)s \(.message)"' | \
  sort
```

### Trace by Trace ID

```bash
# Find all logs for a distributed trace
kubectl logs -n riskcast-prod --all-containers --since=1h | \
  jq -r 'select(.trace_id == "trace_xyz789")'

# Visualize trace timeline
kubectl logs -n riskcast-prod --all-containers --since=1h | \
  jq -r 'select(.trace_id == "trace_xyz789") | 
    "\(.timestamp) [\(.service)] \(.span_id // "root") -> \(.message)"' | \
  sort
```

### Trace User Journey

```bash
# Follow a user's requests
kubectl logs -n riskcast-prod --all-containers --since=1h | \
  jq -r 'select(.extra.user_id == "user-123")' | \
  jq -s 'sort_by(.timestamp) | .[] | "\(.timestamp) \(.extra.endpoint) [\(.http_status)]"'

# Find user's errors
kubectl logs -n riskcast-prod --all-containers --since=1h | \
  jq -r 'select(.extra.user_id == "user-123" and .level == "ERROR")'
```

### Export Trace for Analysis

```bash
# Export complete trace to file
kubectl logs -n riskcast-prod --all-containers --since=1h | \
  jq -r 'select(.request_id == "req_abc123")' | \
  jq -s '.' > trace-req_abc123.json

# Create timeline visualization
kubectl logs -n riskcast-prod --all-containers --since=1h | \
  jq -r 'select(.trace_id == "trace_xyz789") | 
    "\(.timestamp)|\(.service)|\(.duration // 0)|\(.message)"' | \
  column -t -s'|' > trace-timeline.txt
```

---

## 🗄️ Database Debugging

### Slow Queries

#### Find Currently Running Slow Queries

```sql
-- Queries running longer than 5 seconds
SELECT 
  pid, 
  now() - query_start AS duration,
  state,
  wait_event_type,
  wait_event,
  query 
FROM pg_stat_activity 
WHERE state != 'idle' 
  AND query_start < NOW() - INTERVAL '5 seconds'
  AND pid != pg_backend_pid()
ORDER BY duration DESC
LIMIT 20;
```

#### Query Statistics (pg_stat_statements)

```sql
-- Top 20 slowest queries by mean time
SELECT 
  calls,
  mean_exec_time::numeric(10,2) AS mean_time_ms,
  total_exec_time::numeric(10,2) AS total_time_ms,
  stddev_exec_time::numeric(10,2) AS stddev_ms,
  min_exec_time::numeric(10,2) AS min_ms,
  max_exec_time::numeric(10,2) AS max_ms,
  rows,
  query
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 20;

-- Most frequently called queries
SELECT 
  calls,
  mean_exec_time::numeric(10,2) AS mean_time_ms,
  total_exec_time::numeric(10,2) AS total_time_ms,
  query
FROM pg_stat_statements
ORDER BY calls DESC
LIMIT 20;

-- Most time-consuming queries overall
SELECT 
  calls,
  total_exec_time::numeric(10,2) AS total_time_ms,
  mean_exec_time::numeric(10,2) AS mean_time_ms,
  query
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 20;
```

#### Explain Analyze a Query

```sql
-- Explain a slow query
EXPLAIN (ANALYZE, BUFFERS, VERBOSE) 
SELECT * FROM quotes 
WHERE created_at > NOW() - INTERVAL '7 days'
  AND status = 'active';

-- Check if query uses indexes
EXPLAIN 
SELECT * FROM quotes 
WHERE premium > 100000;
```

### Lock Analysis

#### Find Blocking Locks

```sql
-- Find queries that are blocking others
SELECT 
  blocked_locks.pid AS blocked_pid,
  blocked_activity.usename AS blocked_user,
  blocking_locks.pid AS blocking_pid,
  blocking_activity.usename AS blocking_user,
  blocked_activity.query AS blocked_statement,
  blocking_activity.query AS blocking_statement,
  blocked_activity.application_name AS blocked_app
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity 
  ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks 
  ON blocking_locks.locktype = blocked_locks.locktype
  AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
  AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
  AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
  AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
  AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
  AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
  AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
  AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
  AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
  AND blocking_locks.pid != blocked_locks.pid
JOIN pg_catalog.pg_stat_activity blocking_activity 
  ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;
```

#### View All Locks

```sql
-- All current locks
SELECT 
  locktype,
  database,
  relation::regclass,
  page,
  tuple,
  virtualxid,
  transactionid,
  mode,
  granted,
  pid
FROM pg_locks
ORDER BY pid;

-- Locks by table
SELECT 
  locktype,
  relation::regclass AS table_name,
  mode,
  granted,
  pid
FROM pg_locks
WHERE relation IS NOT NULL
ORDER BY relation;
```

#### Kill Blocking Query

```sql
-- Terminate a specific query (CAUTION)
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE pid = 12345;

-- Kill all long-running queries (CAUTION)
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'active'
  AND query_start < NOW() - INTERVAL '5 minutes'
  AND pid != pg_backend_pid();
```

### Connection Issues

#### Check Connection Count

```sql
-- Connections by state
SELECT 
  state, 
  count(*) 
FROM pg_stat_activity 
GROUP BY state
ORDER BY count DESC;

-- Connections by application
SELECT 
  application_name, 
  count(*),
  max(now() - query_start) AS max_age
FROM pg_stat_activity 
WHERE state != 'idle'
GROUP BY application_name
ORDER BY count DESC;

-- Connections by user
SELECT 
  usename, 
  count(*),
  state
FROM pg_stat_activity 
GROUP BY usename, state
ORDER BY count DESC;
```

#### Check Max Connections

```sql
-- Show max connections setting
SHOW max_connections;

-- Current vs max connections
SELECT 
  count(*) as current,
  (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') as max,
  round(100.0 * count(*) / (SELECT setting::int FROM pg_settings WHERE name = 'max_connections'), 2) as pct_used
FROM pg_stat_activity;
```

#### Connection Pool from Application

```bash
# Check connection pool stats from application
kubectl exec -it -n riskcast-prod deployment/riskcast-api -- \
  python -c "
import asyncio
import asyncpg
import os

async def check_pool():
    pool = await asyncpg.create_pool(os.getenv('DATABASE_URL'), min_size=5, max_size=20)
    print(f'Pool size: {pool.get_size()}')
    print(f'Pool free: {pool.get_free_size()}')
    await pool.close()

asyncio.run(check_pool())
"
```

### Index Analysis

```sql
-- Find missing indexes (tables with seq scans)
SELECT 
  schemaname,
  tablename,
  seq_scan,
  seq_tup_read,
  idx_scan,
  seq_tup_read / NULLIF(seq_scan, 0) AS avg_seq_tup,
  idx_scan / NULLIF(seq_scan + idx_scan, 0) * 100 AS pct_idx_scan
FROM pg_stat_user_tables
WHERE seq_scan > 0
ORDER BY seq_tup_read DESC
LIMIT 20;

-- Unused indexes
SELECT 
  schemaname,
  tablename,
  indexname,
  idx_scan,
  pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
WHERE idx_scan = 0
  AND indexrelname NOT LIKE 'pg_toast%'
ORDER BY pg_relation_size(indexrelid) DESC
LIMIT 20;

-- Index usage statistics
SELECT 
  schemaname,
  tablename,
  indexname,
  idx_scan,
  idx_tup_read,
  idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC
LIMIT 20;
```

### Table Statistics

```sql
-- Table sizes
SELECT 
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
  pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) AS index_size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 20;

-- Dead tuples (needs VACUUM)
SELECT 
  schemaname,
  tablename,
  n_live_tup,
  n_dead_tup,
  round(100.0 * n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0), 2) AS dead_pct,
  last_vacuum,
  last_autovacuum
FROM pg_stat_user_tables
WHERE n_dead_tup > 0
ORDER BY n_dead_tup DESC
LIMIT 20;
```

---

## 🌐 API Debugging

### Test Endpoint Locally

#### Port Forward to Pod

```bash
# Forward API port to localhost
kubectl port-forward -n riskcast-prod svc/riskcast-api 8000:80

# Test in another terminal
curl -v http://localhost:8000/health/ready

# Test with auth
export TOKEN="your-jwt-token"
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v3/quotes/

# Test POST
curl -X POST http://localhost:8000/api/v3/quotes/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"vessel_name":"Test Ship","coverage_amount":1000000}'
```

#### Test Specific Pod

```bash
# Get pod IP
POD_IP=$(kubectl get pod <pod-name> -n riskcast-prod -o jsonpath='{.status.podIP}')

# Test directly
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- \
  curl -v http://$POD_IP:8000/health/ready
```

### Debug Inside Pod

```bash
# Exec into pod
kubectl exec -it -n riskcast-prod deployment/riskcast-api -- /bin/bash

# Check environment variables
env | grep -E "(DATABASE|REDIS|API)" | sort

# Test database connection
python -c "
import asyncio
import asyncpg
import os

async def test():
    try:
        conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
        result = await conn.fetchval('SELECT version()')
        print(f'Connected: {result[:50]}')
        await conn.close()
    except Exception as e:
        print(f'Failed: {e}')

asyncio.run(test())
"

# Test Redis connection
python -c "
import redis
import os

try:
    r = redis.from_url(os.getenv('REDIS_URL'))
    result = r.ping()
    print(f'Redis ping: {result}')
    info = r.info('server')
    print(f'Redis version: {info[\"redis_version\"]}')
except Exception as e:
    print(f'Failed: {e}')
"

# Check Python packages
pip list | grep -E "(fastapi|sqlalchemy|redis|asyncpg)"

# Check application logs
tail -f /var/log/application.log
```

### API Request Debugging

```bash
# Verbose curl with timing
curl -w "\n\nTime Total: %{time_total}s\nTime Connect: %{time_connect}s\nTime Start Transfer: %{time_starttransfer}s\n" \
  -v https://api.riskcast.io/api/v3/quotes/ \
  -H "Authorization: Bearer $TOKEN"

# Test with different methods
curl -X GET https://api.riskcast.io/api/v3/quotes/$QUOTE_ID -H "Authorization: Bearer $TOKEN"
curl -X POST https://api.riskcast.io/api/v3/quotes/ -d '{"data":"test"}' -H "Authorization: Bearer $TOKEN"
curl -X PUT https://api.riskcast.io/api/v3/quotes/$QUOTE_ID -d '{"status":"active"}' -H "Authorization: Bearer $TOKEN"
curl -X DELETE https://api.riskcast.io/api/v3/quotes/$QUOTE_ID -H "Authorization: Bearer $TOKEN"

# Check response headers
curl -I https://api.riskcast.io/api/v3/quotes/ -H "Authorization: Bearer $TOKEN"

# Save response for analysis
curl -s https://api.riskcast.io/api/v3/quotes/ -H "Authorization: Bearer $TOKEN" | jq . > response.json
```

---

## 💾 Memory Debugging

### Check Memory Usage

```bash
# Pod memory usage
kubectl top pods -n riskcast-prod

# Detailed pod memory
kubectl describe pod <pod-name> -n riskcast-prod | grep -A 10 "memory"

# Container memory limits
kubectl get pod <pod-name> -n riskcast-prod -o jsonpath='{.spec.containers[*].resources}' | jq .

# Node memory
kubectl top nodes

# Memory by container
kubectl exec -it -n riskcast-prod <pod-name> -- \
  ps aux --sort=-%mem | head -20
```

### Memory Profiling in Python

```python
# Add to application code temporarily

# 1. Track memory usage
import tracemalloc
tracemalloc.start()

# ... run your code ...

snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')

print("[ Top 10 ]")
for stat in top_stats[:10]:
    print(stat)

# 2. Memory profiler
from memory_profiler import profile

@profile
def my_function():
    # Your code here
    pass

# 3. Detailed memory tracking
import sys
import gc

def show_memory():
    print(f"Objects: {len(gc.get_objects())}")
    print(f"Garbage: {len(gc.garbage)}")
    
    # Largest objects
    objects = gc.get_objects()
    sizes = [(sys.getsizeof(obj), type(obj).__name__) for obj in objects]
    sizes.sort(reverse=True)
    print("Largest objects:")
    for size, typename in sizes[:10]:
        print(f"  {typename}: {size / 1024 / 1024:.2f} MB")
```

### Check for Memory Leaks

```bash
# Monitor memory over time
watch -n 10 'kubectl top pod <pod-name> -n riskcast-prod'

# Get memory trend
for i in {1..20}; do 
  kubectl top pod <pod-name> -n riskcast-prod | awk '{print $3}' | tail -1
  sleep 30
done

# Check OOM kills
kubectl get events -n riskcast-prod | grep OOM

# Pod restart count (may indicate OOM)
kubectl get pods -n riskcast-prod -o json | \
  jq '.items[] | select(.status.containerStatuses[].restartCount > 0) | 
    {name: .metadata.name, restarts: .status.containerStatuses[].restartCount}'
```

---

## ⚡ Performance Debugging

### Identify Slow Endpoints

```bash
# From application logs (last hour)
kubectl logs -n riskcast-prod -l app=riskcast-api --since=1h | \
  jq -r 'select(.duration > 1) | "\(.duration)s \(.extra.endpoint) [\(.http_method)]"' | \
  sort -rn | head -20

# Average duration by endpoint
kubectl logs -n riskcast-prod -l app=riskcast-api --since=1h | \
  jq -r 'select(.duration) | "\(.extra.endpoint) \(.duration)"' | \
  awk '{sum[$1]+=$2; count[$1]++} END {for (e in sum) print e, sum[e]/count[e]}' | \
  sort -k2 -rn

# From Prometheus
curl -s 'http://prometheus:9090/api/v1/query?query=histogram_quantile(0.95,sum(rate(riskcast_http_request_duration_seconds_bucket[5m]))by(endpoint,le))' | \
  jq '.data.result[] | {endpoint: .metric.endpoint, p95: .value[1]}'
```

### Profile Specific Endpoint

```python
# Add profiling decorator to endpoint (temporarily)

import cProfile
import pstats
import io
from functools import wraps

def profile_endpoint(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()
        
        result = await func(*args, **kwargs)
        
        profiler.disable()
        s = io.StringIO()
        stats = pstats.Stats(profiler, stream=s)
        stats.sort_stats('cumulative')
        stats.print_stats(20)
        
        print(s.getvalue())
        
        return result
    return wrapper

# Usage
@app.get("/api/v3/quotes/")
@profile_endpoint
async def list_quotes():
    # ... endpoint logic ...
    pass
```

### Check External API Performance

```bash
# Test weather API
time curl -s https://api.tomorrow.io/v4/weather/forecast?location=... -H "apikey: $API_KEY" > /dev/null

# Test port API
time curl -s https://api.marinetraffic.com/ports/... -H "Authorization: $API_KEY" > /dev/null

# Check DNS resolution time
time host api.tomorrow.io
time host api.marinetraffic.com

# Full connection test
curl -w "@curl-format.txt" -o /dev/null -s https://api.tomorrow.io/v4/weather/health

# curl-format.txt:
#     time_namelookup:  %{time_namelookup}s\n
#        time_connect:  %{time_connect}s\n
#     time_appconnect:  %{time_appconnect}s\n
#    time_pretransfer:  %{time_pretransfer}s\n
#       time_redirect:  %{time_redirect}s\n
#  time_starttransfer:  %{time_starttransfer}s\n
#                     ----------\n
#          time_total:  %{time_total}s\n
```

### Application Performance Metrics

```bash
# Request rate
kubectl logs -n riskcast-prod -l app=riskcast-api --since=1m | \
  jq -r 'select(.http_status) | 1' | wc -l | awk '{print $1/60 " req/s"}'

# Error rate
total=$(kubectl logs -n riskcast-prod -l app=riskcast-api --since=5m | jq -r 'select(.http_status) | 1' | wc -l)
errors=$(kubectl logs -n riskcast-prod -l app=riskcast-api --since=5m | jq -r 'select(.http_status >= 500) | 1' | wc -l)
echo "scale=2; 100 * $errors / $total" | bc

# P50, P95, P99 response times
kubectl logs -n riskcast-prod -l app=riskcast-api --since=5m | \
  jq -r 'select(.duration) | .duration' | \
  sort -n | \
  awk '{
    values[NR] = $1
  }
  END {
    print "P50:", values[int(NR*0.5)]
    print "P95:", values[int(NR*0.95)]
    print "P99:", values[int(NR*0.99)]
  }'
```

---

## 🐛 Common Issues

### Issue: 502 Bad Gateway

**Symptoms:** Users seeing 502 errors, no response from API

**Troubleshooting:**
```bash
# 1. Check pod health
kubectl get pods -n riskcast-prod

# 2. Check pod logs
kubectl logs -n riskcast-prod -l app=riskcast-api --tail=100

# 3. Check readiness probe
kubectl describe pod <pod-name> -n riskcast-prod | grep -A 5 "Readiness"

# 4. Test health endpoint directly
kubectl exec -it -n riskcast-prod <pod-name> -- \
  curl -v http://localhost:8000/health/ready
```

**Resolution:**
```bash
# Restart pods if unhealthy
kubectl rollout restart deployment/riskcast-api -n riskcast-prod

# Or delete specific unhealthy pods
kubectl delete pod <pod-name> -n riskcast-prod

# Monitor restart
kubectl get pods -n riskcast-prod -w
```

---

### Issue: High Latency

**Symptoms:** Slow responses, timeouts, P95 > 2 seconds

**Troubleshooting:**
```bash
# 1. Check database
psql $DATABASE_URL -c "
SELECT pid, query_start, state, query 
FROM pg_stat_activity 
WHERE query_start < NOW() - INTERVAL '5 seconds'
ORDER BY query_start;
"

# 2. Check external services
curl -w "Time: %{time_total}s\n" -s https://api.tomorrow.io/v4/weather/health > /dev/null

# 3. Check Redis
redis-cli -u $REDIS_URL --latency

# 4. Check application logs for slow requests
kubectl logs -n riskcast-prod -l app=riskcast-api --since=10m | \
  jq -r 'select(.duration > 2) | "\(.duration)s \(.extra.endpoint)"'
```

**Resolution:**
- If database: optimize queries, add indexes
- If external service: enable caching, use circuit breaker
- If Redis: check memory, add replicas
- If application: profile code, optimize logic
- Scale horizontally if needed

---

### Issue: Out of Memory (OOMKilled)

**Symptoms:** Pods restarting, OOMKilled in events

**Troubleshooting:**
```bash
# Check for OOM events
kubectl get events -n riskcast-prod | grep OOM

# Check pod memory usage before restart
kubectl top pod <pod-name> -n riskcast-prod

# Check memory limits
kubectl describe pod <pod-name> -n riskcast-prod | grep -A 5 "Limits"

# Check memory usage trends (if monitoring available)
# Prometheus: container_memory_usage_bytes
```

**Resolution:**
```bash
# Temporary: Increase pod memory limits
kubectl patch deployment riskcast-api -n riskcast-prod \
  --patch '{"spec":{"template":{"spec":{"containers":[{"name":"riskcast-api","resources":{"limits":{"memory":"2Gi"}}}]}}}}'

# Long-term: Find and fix memory leak
# Add memory profiling (see Memory Debugging section)
# Review code for leaks
# Consider horizontal scaling instead of vertical
```

---

### Issue: Database Connection Pool Exhausted

**Symptoms:** "Too many connections", "Pool timeout" errors

**Troubleshooting:**
```bash
# Check connection count
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database();"

# Check max connections
psql $DATABASE_URL -c "SHOW max_connections;"

# Check application pool size
kubectl exec -it -n riskcast-prod deployment/riskcast-api -- \
  env | grep -i pool
```

**Resolution:**
```bash
# Option 1: Increase database max_connections
aws rds modify-db-parameter-group \
  --db-parameter-group-name riskcast-params \
  --parameters "ParameterName=max_connections,ParameterValue=300,ApplyMethod=immediate"

# Option 2: Optimize application connection pool
kubectl set env deployment/riskcast-api -n riskcast-prod \
  DATABASE_POOL_SIZE=20 \
  DATABASE_MAX_OVERFLOW=5 \
  DATABASE_POOL_TIMEOUT=10

# Option 3: Add read replica
# See scaling.md

# Option 4: Kill idle connections
psql $DATABASE_URL -c "
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle'
  AND state_change < NOW() - INTERVAL '10 minutes'
  AND pid != pg_backend_pid();
"
```

---

### Issue: External API Timeout

**Symptoms:** Timeouts calling weather/port APIs

**Troubleshooting:**
```bash
# Test external service
curl -v --max-time 5 https://api.tomorrow.io/v4/weather/health

# Check from within pod
kubectl exec -it -n riskcast-prod deployment/riskcast-api -- \
  curl -v --max-time 5 https://api.tomorrow.io/v4/weather/health

# Check DNS
nslookup api.tomorrow.io

# Check network policies
kubectl get networkpolicies -n riskcast-prod
```

**Resolution:**
```bash
# Enable circuit breaker
kubectl set env deployment/riskcast-api -n riskcast-prod \
  CIRCUIT_BREAKER_ENABLED=true \
  CIRCUIT_BREAKER_THRESHOLD=5 \
  CIRCUIT_BREAKER_TIMEOUT=60

# Increase timeout
kubectl set env deployment/riskcast-api -n riskcast-prod \
  EXTERNAL_API_TIMEOUT=10

# Use cached data
kubectl set env deployment/riskcast-api -n riskcast-prod \
  USE_CACHED_WEATHER=true \
  CACHE_TTL=3600
```

---

**Last Updated:** January 24, 2026  
**Version:** 1.0.0  
**Owner:** Infrastructure Team

**Keep this runbook updated with new issues and solutions!**
