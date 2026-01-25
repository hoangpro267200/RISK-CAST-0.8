# 📊 RiskCast Observability Guide

Complete guide to monitoring, metrics, alerting, and distributed tracing.

---

## Overview

The RiskCast observability stack provides:

- **Metrics**: Prometheus for application and business metrics
- **Tracing**: OpenTelemetry + Tempo for distributed tracing
- **Dashboards**: Grafana for visualization
- **Alerting**: Prometheus Alertmanager for notifications

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  RiskCast API                       │
│  ┌──────────────┐         ┌──────────────┐        │
│  │   Metrics    │         │   Tracing    │        │
│  │  (Prom SDK)  │         │ (OTel SDK)   │        │
│  └──────┬───────┘         └──────┬───────┘        │
│         │                         │                 │
└─────────┼─────────────────────────┼─────────────────┘
          │                         │
          ▼                         ▼
┌─────────────────┐       ┌─────────────────┐
│   Prometheus    │       │      Tempo      │
│  (Metrics DB)   │       │  (Traces DB)    │
└────────┬────────┘       └────────┬────────┘
         │                         │
         └──────────┬──────────────┘
                    │
            ┌───────▼────────┐
            │    Grafana     │
            │  (Dashboards)  │
            └────────────────┘
                    │
            ┌───────▼────────┐
            │  Alertmanager  │
            │   (Alerts)     │
            └────────────────┘
```

---

## Quick Start

### 1. Deploy Monitoring Stack

```bash
# Deploy monitoring namespace and stack
kubectl apply -k k8s/monitoring/

# Verify deployment
kubectl get pods -n monitoring

# Expected output:
# prometheus-xxx      1/1  Running
# grafana-xxx         1/1  Running
# tempo-xxx           1/1  Running
# alertmanager-xxx    1/1  Running
```

### 2. Access Dashboards

```bash
# Port-forward Grafana
kubectl port-forward -n monitoring svc/grafana 3000:3000

# Open in browser
# http://localhost:3000
# Login: admin / changeme-in-production

# Port-forward Prometheus
kubectl port-forward -n monitoring svc/prometheus 9090:9090

# http://localhost:9090
```

### 3. Install Dependencies

```bash
pip install -r app/monitoring/requirements.txt
```

---

## Prometheus Metrics

### Available Metrics

#### HTTP Request Metrics

```python
# Request count
riskcast_http_requests_total{method, endpoint, status_code}

# Request latency
riskcast_http_request_duration_seconds{method, endpoint}

# Requests in progress
riskcast_http_requests_in_progress{method, endpoint}
```

#### Business Metrics

```python
# Risk assessments
riskcast_risk_assessments_total{cargo_type, risk_grade}
riskcast_risk_assessment_duration_seconds{model_version}
riskcast_risk_score_distribution

# Quotes
riskcast_quotes_total{status, coverage_type}
riskcast_quote_premium_usd
riskcast_quote_conversion_rate{period}

# Policies
riskcast_active_policies_total{coverage_type}
riskcast_total_coverage_usd

# Claims
riskcast_claims_total{loss_type, status}
riskcast_claim_amount_usd
riskcast_claim_processing_days
```

#### Infrastructure Metrics

```python
# External services
riskcast_external_requests_total{service, status}
riskcast_external_request_duration_seconds{service}

# Database
riskcast_db_queries_total{operation, table}
riskcast_db_query_duration_seconds{operation}
riskcast_db_connections{state}

# Cache
riskcast_cache_hits_total{cache_type}
riskcast_cache_misses_total{cache_type}

# Background jobs
riskcast_jobs_total{job_type, status}
riskcast_job_duration_seconds{job_type}
riskcast_job_queue_size{queue}
```

### Example Queries

```promql
# Request rate (per second)
sum(rate(riskcast_http_requests_total[5m]))

# Error rate (percentage)
sum(rate(riskcast_http_requests_total{status_code=~"5.."}[5m])) 
/ sum(rate(riskcast_http_requests_total[5m])) * 100

# P95 latency
histogram_quantile(0.95, 
  sum(rate(riskcast_http_request_duration_seconds_bucket[5m])) by (le)
)

# Top endpoints by traffic
topk(10, 
  sum(rate(riskcast_http_requests_total[5m])) by (endpoint)
)

# Active policies by type
sum(riskcast_active_policies_total) by (coverage_type)

# Cache hit rate
sum(rate(riskcast_cache_hits_total[5m])) 
/ (sum(rate(riskcast_cache_hits_total[5m])) + sum(rate(riskcast_cache_misses_total[5m])))
```

---

## Distributed Tracing

### OpenTelemetry Integration

RiskCast uses OpenTelemetry for distributed tracing with automatic instrumentation for:

- FastAPI endpoints
- SQLAlchemy database queries
- Redis operations
- HTTP client requests (httpx)

### Trace Example

```
Request: POST /api/v3/quotes/request
  │
  ├─ create_quote (FastAPI handler)
  │  │
  │  ├─ calculate_risk_score
  │  │  │
  │  │  ├─ fetch_historical_data (Database query)
  │  │  │  └─ SELECT * FROM loss_history (SQLAlchemy)
  │  │  │
  │  │  └─ apply_ml_model
  │  │     └─ Redis GET model:weights
  │  │
  │  └─ get_weather (External API)
  │     └─ HTTP GET https://api.tomorrow.io
  │
  └─ save_quote (Database insert)
     └─ INSERT INTO quotes (SQLAlchemy)
```

### Viewing Traces

1. **In Grafana:**
   - Navigate to Explore
   - Select "Tempo" datasource
   - Search by trace ID, service, or operation

2. **Query by Service:**
   ```
   {service.name="riskcast-api"}
   ```

3. **Query by Duration:**
   ```
   {duration > 2s}
   ```

---

## Integration Examples

### 1. Basic Endpoint with Metrics

```python
from fastapi import APIRouter
from app.monitoring import track_request_metrics, QUOTE_COUNT

router = APIRouter()

@router.post("/quotes")
@track_request_metrics("/quotes")
async def create_quote(request: dict):
    """Automatically tracked endpoint."""
    quote = await process_quote(request)
    
    # Record business metric
    QUOTE_COUNT.labels(
        status=quote.status,
        coverage_type=quote.coverage_type
    ).inc()
    
    return quote
```

### 2. Custom Tracing

```python
from app.monitoring import TracedOperation

async def complex_operation(data: dict):
    """Operation with custom tracing."""
    with TracedOperation("complex_operation", {"input_type": data["type"]}):
        # Sub-operation 1
        with TracedOperation("step_1"):
            result1 = await step_1(data)
        
        # Sub-operation 2
        with TracedOperation("step_2"):
            result2 = await step_2(result1)
        
        return result2
```

### 3. External Service Tracking

```python
from app.monitoring import track_external_request

class ExternalService:
    @track_external_request("weather-api")
    async def get_data(self):
        """Automatically tracked external call."""
        async with httpx.AsyncClient() as client:
            return await client.get("https://api.example.com")
```

### 4. Database Instrumentation

```python
from sqlalchemy import create_engine
from app.monitoring import instrument_database

engine = create_engine(DATABASE_URL)
instrument_database(engine)  # Automatic query tracing
```

---

## Alerting

### Alert Rules

#### Critical Alerts

- **APIDown**: API not responding (1 minute)
- **HighErrorRate**: >5% error rate (5 minutes)
- **DBConnectionPoolExhausted**: >90% pool usage

#### Warning Alerts

- **HighLatency**: P95 > 2s (5 minutes)
- **LowPodCount**: < 2 pods running
- **HighCacheMissRate**: > 50% miss rate
- **JobQueueBacklog**: > 1000 jobs queued

### Alert Channels

Configure in `k8s/monitoring/namespace-and-alertmanager.yaml`:

```yaml
receivers:
  - name: 'critical'
    slack_configs:
      - channel: '#critical-alerts'
    pagerduty_configs:
      - routing_key: 'YOUR_KEY'
  
  - name: 'warning'
    slack_configs:
      - channel: '#alerts'
```

### Testing Alerts

```bash
# Trigger high error rate
curl -X POST prometheus:9090/api/v1/alerts

# Check active alerts
curl prometheus:9090/api/v1/alerts
```

---

## Grafana Dashboards

### Pre-configured Dashboards

1. **RISKCAST Overview**
   - Request rate, error rate, latency
   - Active policies, quote conversion
   - Risk assessment metrics

2. **Infrastructure**
   - Database performance
   - Cache hit rates
   - External service latency

3. **Business Metrics**
   - Quote funnel
   - Policy growth
   - Claims processing

### Creating Custom Dashboards

```json
{
  "title": "My Dashboard",
  "panels": [
    {
      "title": "Request Rate",
      "targets": [
        {
          "expr": "sum(rate(riskcast_http_requests_total[5m]))"
        }
      ]
    }
  ]
}
```

---

## Performance Considerations

### Metric Cardinality

⚠️ **Avoid high-cardinality labels:**

```python
# ❌ BAD: User ID as label (millions of values)
REQUEST_COUNT.labels(user_id="user-123", endpoint="/api")

# ✅ GOOD: Fixed set of values
REQUEST_COUNT.labels(endpoint="/api", status_code="200")
```

### Sampling

For high-traffic endpoints, use sampling:

```python
# Sample 10% of traces
if random.random() < 0.1:
    with TracedOperation("expensive_operation"):
        result = await expensive_operation()
```

### Prometheus Storage

- Default retention: 15 days
- Storage: 50GB PVC
- Adjust in `prometheus-deployment.yaml`:

```yaml
args:
  - '--storage.tsdb.retention.time=30d'
  - '--storage.tsdb.retention.size=100GB'
```

---

## Troubleshooting

### Metrics Not Appearing

```bash
# Check if /metrics endpoint works
kubectl exec -it <pod-name> -n riskcast-prod -- curl localhost:8000/metrics

# Check Prometheus targets
kubectl port-forward -n monitoring svc/prometheus 9090:9090
# Visit http://localhost:9090/targets
```

### Traces Not Showing Up

```bash
# Verify Tempo is running
kubectl get pods -n monitoring | grep tempo

# Check OTLP endpoint is accessible
kubectl exec -it <pod-name> -n riskcast-prod -- \
  curl -v http://tempo.monitoring:4317

# Verify environment variable
kubectl exec -it <pod-name> -n riskcast-prod -- env | grep OTEL
```

### High Memory Usage

```bash
# Check Prometheus memory
kubectl top pod -n monitoring

# Reduce scrape interval (prometheus-config.yaml)
scrape_interval: 30s  # Instead of 15s

# Reduce retention
--storage.tsdb.retention.time=7d
```

---

## Best Practices

### 1. Metric Naming

```python
# ✅ GOOD
riskcast_http_requests_total
riskcast_db_query_duration_seconds

# ❌ BAD
HttpRequests
db_query_time_ms
```

### 2. Label Usage

```python
# ✅ GOOD: Low cardinality
REQUEST_COUNT.labels(
    method="GET",
    endpoint="/api/quotes",
    status_code="200"
)

# ❌ BAD: High cardinality
REQUEST_COUNT.labels(
    user_id="user-12345",  # Millions of possible values
    timestamp="2024-01-01"
)
```

### 3. Span Naming

```python
# ✅ GOOD: Descriptive, consistent
with TracedOperation("calculate_risk_score"):
    ...

# ❌ BAD: Too generic
with TracedOperation("process"):
    ...
```

### 4. Alert Tuning

- Set appropriate thresholds based on SLOs
- Use `for:` clause to avoid flapping
- Group related alerts
- Include runbook links

---

## SLO Targets

| Metric | Target | Critical |
|--------|--------|----------|
| Availability | 99.9% | 99.5% |
| Error Rate | < 1% | < 5% |
| P95 Latency | < 1s | < 2s |
| P99 Latency | < 2s | < 5s |

---

**Version:** 1.0.0  
**Date:** 2026-01-24  
**Status:** ✅ Production Ready
