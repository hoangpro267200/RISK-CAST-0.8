# Structured Logging Guide

## Overview

RiskCast implements a comprehensive structured logging system with JSON formatting, correlation IDs, sensitive data masking, and centralized log aggregation for production environments.

## Features

✅ **JSON Structured Logging** - Machine-readable log format  
✅ **Correlation IDs** - Track requests across services  
✅ **Context Variables** - Request ID, trace ID, user ID, tenant ID  
✅ **Sensitive Data Masking** - Automatic masking of passwords, tokens, etc.  
✅ **Request/Response Logging** - HTTP middleware with timing  
✅ **Slow Request Detection** - Performance monitoring  
✅ **Log Aggregation** - Fluentd + Elasticsearch integration  
✅ **Critical Log Separation** - Separate index for errors  
✅ **Environment-aware** - Different formats for dev vs prod  

---

## Quick Start

### 1. Initialize Logging in Your Application

In your `app/main.py`:

```python
from app.core.logging import setup_logging, get_logger

# Initialize logging on startup
logger = setup_logging(
    service_name="riskcast-api",
    environment="production",  # or "development"
    log_level="INFO",
    json_output=True
)

logger.info("Application starting", version="1.0.0", environment="production")
```

### 2. Add Middleware to FastAPI

```python
from fastapi import FastAPI
from app.middleware.request_logging import (
    RequestLoggingMiddleware,
    SlowRequestLoggingMiddleware
)

app = FastAPI()

# Add request logging middleware
app.add_middleware(
    RequestLoggingMiddleware,
    log_request_body=False,  # Set to True for debugging
    log_response_body=False
)

# Add slow request detection
app.add_middleware(
    SlowRequestLoggingMiddleware,
    threshold_ms=1000  # Log requests taking > 1 second
)
```

### 3. Use Structured Logger in Your Code

```python
from app.core.logging import get_logger

logger = get_logger(__name__)

# Basic logging with structured data
logger.info(
    "User login successful",
    user_id="user-123",
    ip_address="192.168.1.1",
    login_method="oauth"
)

# Error logging with context
try:
    result = risky_operation()
except Exception as e:
    logger.error(
        "Operation failed",
        operation="risky_operation",
        error_type=type(e).__name__,
        user_id="user-123"
    )
```

---

## Advanced Usage

### Audit Logging

Log business-critical events for compliance:

```python
from app.core.logging import get_logger

logger = get_logger(__name__)

# Audit log
logger.audit(
    action="policy_created",
    entity_type="insurance_policy",
    entity_id="POL-2026-001",
    user_id="underwriter-42",
    premium_amount=150000.00,
    currency="USD"
)
```

### Business Event Logging

Track important business events:

```python
logger.business_event(
    "quote_generated",
    quote_id="QTE-123456",
    customer_id="CUST-789",
    risk_score=75.5,
    premium=125000.00,
    coverage_type="cargo"
)
```

### Security Event Logging

Log security-related events:

```python
logger.security_event(
    "unauthorized_access_attempt",
    severity="high",
    user_id="user-suspicious",
    ip_address="203.0.113.42",
    attempted_resource="/api/v3/admin/users",
    http_method="DELETE"
)
```

### Function Call Logging Decorator

Automatically log function calls:

```python
from app.core.logging import log_function_call, get_logger
import logging

logger = get_logger(__name__)

@log_function_call(logger=logger, level=logging.DEBUG)
async def calculate_premium(policy_data: dict) -> float:
    # Function implementation
    return premium

# Logs:
# - "Calling app.pricing.calculate_premium" (with arg counts)
# - "Completed app.pricing.calculate_premium" (on success)
# - "Error in app.pricing.calculate_premium: ..." (on error)
```

### Manual Context Management

Set logging context manually:

```python
from app.core.logging import set_request_context, clear_request_context

# Set context
set_request_context(
    request_id="req-abc123",
    trace_id="trace-xyz789",
    user_id="user-456",
    tenant_id="tenant-acme"
)

# All logs will include these context variables
logger.info("Processing payment")

# Clear context when done
clear_request_context()
```

---

## Configuration

### Environment Variables

```bash
# Logging configuration
ENVIRONMENT=production          # production|staging|development
LOG_LEVEL=INFO                 # DEBUG|INFO|WARNING|ERROR|CRITICAL
```

### Development vs Production

**Development Mode:**
- Human-readable text format
- Console output with colors
- All log levels visible

**Production Mode:**
- JSON structured format
- Machine-parseable
- Sent to log aggregation system

---

## Log Format

### JSON Output (Production)

```json
{
  "timestamp": "2026-01-24T21:15:30.123456Z",
  "unix_timestamp": 1737751530.123456,
  "level": "INFO",
  "level_num": 20,
  "service": "riskcast-api",
  "environment": "production",
  "logger": "app.api.v3.quotes",
  "module": "quotes",
  "function": "create_quote",
  "line": 145,
  "file": "/app/app/api/v3/quotes.py",
  "message": "Quote created successfully",
  "request_id": "req-abc123-def456",
  "trace_id": "trace-xyz789",
  "user_id": "user-42",
  "tenant_id": "tenant-acme",
  "process_id": 1234,
  "thread_id": 56789,
  "thread_name": "MainThread",
  "extra": {
    "quote_id": "QTE-123456",
    "premium": 125000.00,
    "risk_score": 75.5
  }
}
```

### Text Output (Development)

```
2026-01-24 21:15:30.123 | INFO     | app.api.v3.quotes:create_quote:145 | Quote created successfully | request_id=req-abc123-def456
```

---

## Sensitive Data Masking

The logging system automatically masks sensitive data:

### Masked Fields

- `password`, `secret`, `token`, `api_key`
- `authorization`, `credential`, `private_key`
- `access_token`, `refresh_token`
- `ssn`, `credit_card`, `cvv`, `pin`

### Masked Patterns

- Bearer tokens: `Bearer eyJhbGc...` → `***MASKED***`
- Basic auth: `Basic dXNlcjpwYXNz` → `***MASKED***`
- Credit cards: `4111-1111-1111-1111` → `***MASKED***`

### Example

```python
# Input
logger.info("User authenticated", password="secret123", api_key="sk-123abc")

# Output
{
  "message": "User authenticated",
  "extra": {
    "password": "***MASKED***",
    "api_key": "***MASKED***"
  }
}
```

---

## Request/Response Logging

The `RequestLoggingMiddleware` automatically logs:

### Request Logs

```json
{
  "event": "http_request",
  "method": "POST",
  "path": "/api/v3/quotes",
  "query_params": {"tenant_id": "acme"},
  "client_ip": "203.0.113.42",
  "user_agent": "Mozilla/5.0...",
  "request_id": "req-abc123"
}
```

### Response Logs

```json
{
  "event": "http_response",
  "method": "POST",
  "path": "/api/v3/quotes",
  "status_code": 201,
  "duration_ms": 145.23,
  "request_id": "req-abc123"
}
```

### Slow Request Logs

```json
{
  "event": "slow_request",
  "method": "POST",
  "path": "/api/v3/risk-assessments",
  "duration_ms": 2543.12,
  "threshold_ms": 1000,
  "request_id": "req-abc123"
}
```

---

## Log Aggregation (Kubernetes)

### Deploy Fluentd

```bash
# Create namespace
kubectl apply -f k8s/logging/fluentd-config.yaml

# Create Elasticsearch credentials secret
kubectl create secret generic elasticsearch-credentials \
  --namespace=logging \
  --from-literal=host=elasticsearch.example.com \
  --from-literal=username=fluentd \
  --from-literal=password=your-password-here

# Verify deployment
kubectl get daemonset -n logging
kubectl logs -n logging -l app=fluentd
```

### View Logs in Elasticsearch

```bash
# Query recent logs
curl -X GET "https://elasticsearch.example.com/riskcast-logs-*/_search?pretty" \
  -u "user:pass" \
  -H 'Content-Type: application/json' \
  -d '{
    "query": {
      "range": {
        "timestamp": {
          "gte": "now-1h"
        }
      }
    },
    "sort": [{"timestamp": "desc"}],
    "size": 100
  }'

# Query by request ID
curl -X GET "https://elasticsearch.example.com/riskcast-logs-*/_search?pretty" \
  -u "user:pass" \
  -H 'Content-Type: application/json' \
  -d '{
    "query": {
      "term": {
        "request_id": "req-abc123"
      }
    }
  }'

# Query critical logs
curl -X GET "https://elasticsearch.example.com/riskcast-critical-*/_search?pretty" \
  -u "user:pass"
```

---

## Best Practices

### 1. Use Structured Data

✅ **Good:**
```python
logger.info("Payment processed", 
    payment_id="PAY-123", 
    amount=1000.00, 
    currency="USD"
)
```

❌ **Bad:**
```python
logger.info(f"Payment PAY-123 processed: $1000.00 USD")
```

### 2. Log at Appropriate Levels

- **DEBUG:** Detailed diagnostic information
- **INFO:** General informational messages
- **WARNING:** Warning messages (degraded operation)
- **ERROR:** Error events (operation failed)
- **CRITICAL:** Critical events (system instability)

### 3. Include Relevant Context

Always include:
- Entity IDs (user_id, tenant_id, quote_id, etc.)
- Operation names
- Result indicators (success/failure)
- Error types and messages

### 4. Don't Log Sensitive Data

Never log:
- Passwords or secrets
- API keys or tokens
- Credit card numbers
- Personal identification numbers

### 5. Use Correlation IDs

Always propagate request IDs and trace IDs:

```python
# In middleware (automatic)
response.headers['X-Request-ID'] = request_id

# In external API calls
async with httpx.AsyncClient() as client:
    response = await client.get(
        "https://api.example.com/data",
        headers={"X-Request-ID": request_id}
    )
```

---

## Monitoring & Alerts

### Key Metrics to Monitor

1. **Error Rate:** Count of ERROR/CRITICAL logs
2. **Slow Requests:** Count of slow_request events
3. **Response Time:** p50, p95, p99 of duration_ms
4. **Request Volume:** Count of http_request events
5. **Security Events:** Count of security event logs

### Sample Alert Rules

```yaml
# Prometheus AlertManager rules
groups:
  - name: logging_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(log_level_error_total[5m]) > 10
        annotations:
          summary: "High error rate detected"
          
      - alert: SlowRequestsIncreasing
        expr: rate(slow_request_total[5m]) > 5
        annotations:
          summary: "Slow requests increasing"
```

---

## Troubleshooting

### No Logs Appearing

1. Check log level: `LOG_LEVEL=DEBUG`
2. Verify middleware is added to FastAPI app
3. Check logger initialization in main.py

### Logs Not in JSON Format

- Set `ENVIRONMENT=production`
- Or explicitly: `json_output=True` in `setup_logging()`

### Sensitive Data Not Masked

- Verify field names match `SENSITIVE_FIELDS` patterns
- Add custom patterns to `SENSITIVE_PATTERNS` if needed

### Fluentd Not Collecting Logs

1. Check DaemonSet status: `kubectl get ds -n logging`
2. View Fluentd logs: `kubectl logs -n logging -l app=fluentd`
3. Verify Elasticsearch credentials secret exists
4. Check network connectivity to Elasticsearch

---

## Testing

### Unit Test Example

```python
import logging
from app.core.logging import setup_logging, get_logger, mask_sensitive_data

def test_sensitive_data_masking():
    data = {
        "username": "john",
        "password": "secret123",
        "api_key": "sk-abc123"
    }
    
    masked = mask_sensitive_data(data)
    
    assert masked["username"] == "john"
    assert masked["password"] == "***MASKED***"
    assert masked["api_key"] == "***MASKED***"

def test_structured_logging():
    logger = setup_logging(environment="development")
    
    # Capture log output
    with LogCapture() as capture:
        logger.info("Test message", user_id="123", action="test")
        
    assert "Test message" in capture.output
```

---

## Migration Guide

### From Old Logging System

**Before:**
```python
import logging
logger = logging.getLogger(__name__)
logger.info("User logged in")
```

**After:**
```python
from app.core.logging import get_logger
logger = get_logger(__name__)
logger.info("User logged in", user_id="123", method="oauth")
```

### Key Changes

1. Import from `app.core.logging` instead of stdlib `logging`
2. Add structured data as kwargs
3. Use specialized methods: `audit()`, `business_event()`, `security_event()`
4. Request context is managed automatically by middleware

---

## Performance Considerations

### Overhead

- **JSON formatting:** ~0.1-0.5ms per log entry
- **Sensitive data masking:** ~0.05-0.2ms per log entry
- **Middleware:** ~0.5-1ms per request

### Optimization Tips

1. Use appropriate log levels (avoid DEBUG in production)
2. Exclude health check endpoints from logging
3. Limit log body size (default: 10KB)
4. Use async logging for high-throughput systems

---

## Support

For issues or questions:
- Documentation: `/docs/STRUCTURED_LOGGING_GUIDE.md`
- Code: `app/core/logging.py`, `app/middleware/request_logging.py`
- Kubernetes: `k8s/logging/fluentd-config.yaml`

---

**Last Updated:** January 24, 2026  
**Version:** 1.0.0
