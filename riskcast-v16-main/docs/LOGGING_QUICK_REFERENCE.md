# Structured Logging - Quick Reference Card

## 🚀 Getting Started

```python
from app.core.logging import get_logger

logger = get_logger(__name__)
```

---

## 📝 Basic Logging

```python
# Debug (detailed diagnostic info)
logger.debug("Detailed info", var1=value1, var2=value2)

# Info (general informational)
logger.info("Operation completed", entity_id="123", status="success")

# Warning (degraded operation)
logger.warning("Threshold exceeded", current=95, threshold=90)

# Error (operation failed)
logger.error("Process failed", error_type="ValueError", entity="quote")

# Critical (system instability)
logger.critical("Database unreachable", service="postgresql")
```

---

## 🎯 Specialized Logging

### Audit Logging (Compliance)

```python
logger.audit(
    action="policy_created",       # What happened
    entity_type="policy",           # What was affected
    entity_id="POL-123",           # Which one
    user_id="user-456",            # Who did it
    premium=150000.00,             # Additional context
    currency="USD"
)
```

### Business Events (Metrics)

```python
logger.business_event(
    "quote_generated",             # Event name
    quote_id="QTE-789",
    customer_id="CUST-456",
    risk_score=75.5,
    premium=125000.00
)
```

### Security Events (Monitoring)

```python
logger.security_event(
    "failed_login_attempt",        # Event name
    severity="high",               # low|medium|high
    username="john.doe",
    ip_address="203.0.113.42",
    reason="invalid_password"
)
```

---

## 🔧 Function Decorator

```python
from app.core.logging import log_function_call
import logging

@log_function_call(logger=logger, level=logging.INFO)
async def calculate_premium(data: dict) -> float:
    # Entry, exit, and errors logged automatically
    return premium
```

---

## 🌐 FastAPI Integration

### Application Setup

```python
from app.core.logging import setup_logging
from app.middleware.request_logging import (
    RequestLoggingMiddleware,
    SlowRequestLoggingMiddleware
)

# Initialize logging
logger = setup_logging(
    service_name="riskcast-api",
    environment="production",  # or "development"
    log_level="INFO",
    json_output=True
)

# Add middleware
app.add_middleware(SlowRequestLoggingMiddleware, threshold_ms=1000)
app.add_middleware(RequestLoggingMiddleware)
```

### Route Handler

```python
@app.post("/api/v3/quotes")
async def create_quote(request: Request, data: dict):
    logger.info("Creating quote", customer_id=data.get("customer_id"))
    
    try:
        quote = create_quote_logic(data)
        logger.business_event("quote_created", quote_id=quote.id)
        return quote
    except ValueError as e:
        logger.warning("Invalid data", error=str(e))
        raise HTTPException(400, detail=str(e))
    except Exception as e:
        logger.error("Quote creation failed", error_type=type(e).__name__)
        raise HTTPException(500)
```

---

## 🔍 Context Management

### Automatic (via Middleware)

Request context is automatically set by `RequestLoggingMiddleware`:
- request_id
- trace_id
- user_id (if authenticated)
- tenant_id (if in request state)

### Manual

```python
from app.core.logging import set_request_context, clear_request_context

set_request_context(
    request_id="req-123",
    trace_id="trace-456",
    user_id="user-789",
    tenant_id="tenant-abc"
)

# All logs will include these values
logger.info("Processing payment")

clear_request_context()  # Clean up when done
```

---

## 🔒 Sensitive Data

### Automatically Masked Fields

- password, secret, token, api_key
- authorization, credential, private_key
- access_token, refresh_token
- ssn, credit_card, cvv, pin

### Example

```python
# Input
logger.info("Login", username="john", password="secret123")

# Output (automatically masked)
{
  "message": "Login",
  "extra": {
    "username": "john",
    "password": "***MASKED***"
  }
}
```

---

## 📊 Log Levels

| Level | When to Use | Example |
|-------|-------------|---------|
| DEBUG | Detailed diagnostic | `logger.debug("Cache hit", key="user:123")` |
| INFO | Normal operation | `logger.info("Quote created", id="QTE-123")` |
| WARNING | Degraded state | `logger.warning("High latency", ms=2500)` |
| ERROR | Operation failed | `logger.error("Payment failed", reason="timeout")` |
| CRITICAL | System failure | `logger.critical("DB down", service="postgres")` |

---

## 🔎 Elasticsearch Queries

### Find logs for a request

```json
GET /riskcast-logs-*/_search
{
  "query": {"term": {"request_id": "req-abc123"}}
}
```

### Find errors in last hour

```json
GET /riskcast-logs-*/_search
{
  "query": {
    "bool": {
      "must": [
        {"range": {"timestamp": {"gte": "now-1h"}}},
        {"terms": {"level": ["ERROR", "CRITICAL"]}}
      ]
    }
  }
}
```

### Find slow requests

```json
GET /riskcast-logs-*/_search
{
  "query": {"term": {"event": "slow_request"}},
  "sort": [{"duration_ms": "desc"}]
}
```

### User activity

```json
GET /riskcast-logs-*/_search
{
  "query": {"term": {"user_id": "user-123"}},
  "sort": [{"timestamp": "desc"}]
}
```

---

## 🎨 Best Practices

### ✅ DO

```python
# Use structured data (good for searching)
logger.info("Payment processed", payment_id="PAY-123", amount=1000)

# Include relevant context
logger.error("API timeout", service="stripe", duration_ms=30000)

# Use specialized methods
logger.audit("data_exported", "report", "RPT-456", user_id="usr-789")

# Log business events
logger.business_event("subscription_renewed", plan="premium")
```

### ❌ DON'T

```python
# Don't concatenate strings
logger.info(f"Payment {payment_id} processed: ${amount}")

# Don't log sensitive data
logger.info("Login", password=user_password)  # Will be masked, but avoid

# Don't use print statements
print("Debug info")  # Use logger.debug() instead

# Don't over-log
for item in items:  # Don't log every iteration
    logger.debug(f"Processing {item}")
```

---

## 🐛 Troubleshooting

### Logs not appearing?

```python
# Check log level
import logging
logger.setLevel(logging.DEBUG)

# Verify initialization
logger.info("Test log message")
```

### Logs not in JSON?

```bash
# Set environment
export ENVIRONMENT=production

# Or in code
setup_logging(json_output=True)
```

### Request ID missing?

```python
# Ensure middleware is added
app.add_middleware(RequestLoggingMiddleware)
```

---

## 📦 Log Output Format

### Development (Human-readable)

```
2026-01-24 21:15:30 | INFO     | app.api.quotes:create:145 | Quote created | request_id=req-123
```

### Production (JSON)

```json
{
  "timestamp": "2026-01-24T21:15:30.123Z",
  "level": "INFO",
  "service": "riskcast-api",
  "logger": "app.api.quotes",
  "function": "create",
  "line": 145,
  "message": "Quote created",
  "request_id": "req-123",
  "user_id": "user-456",
  "tenant_id": "tenant-789",
  "extra": {
    "quote_id": "QTE-123",
    "premium": 125000.00
  }
}
```

---

## 🔗 Response Headers

Every HTTP response includes:

```http
X-Request-ID: req-abc123-def456
X-Response-Time: 145.23ms
```

Use these for:
- Correlating client errors with server logs
- Performance tracking
- Debugging distributed systems

---

## ⚡ Performance

| Operation | Overhead |
|-----------|----------|
| JSON formatting | ~0.1-0.5ms |
| Data masking | ~0.05-0.2ms |
| Middleware | ~0.5-1ms |

**Tip:** Use appropriate log levels (avoid DEBUG in production)

---

## 📖 More Info

- **Full Guide:** `/docs/STRUCTURED_LOGGING_GUIDE.md`
- **Integration Example:** `/app/core/logging_integration_example.py`
- **Summary:** `/STRUCTURED_LOGGING_SUMMARY.md`

---

## 💡 Common Patterns

### API Endpoint

```python
@app.post("/api/v3/resource")
async def create_resource(request: Request, data: dict):
    logger.info("Creating resource", type=data.get("type"))
    
    try:
        resource = create_logic(data)
        logger.business_event("resource_created", id=resource.id)
        return resource
    except ValidationError as e:
        logger.warning("Validation failed", errors=e.errors())
        raise HTTPException(400)
    except Exception as e:
        logger.error("Creation failed", error=type(e).__name__)
        raise HTTPException(500)
```

### Background Task

```python
async def process_task(task_id: str, request_id: str):
    set_request_context(request_id=request_id)
    
    logger.info("Task started", task_id=task_id)
    
    try:
        result = await long_running_operation()
        logger.info("Task completed", task_id=task_id, result=result)
    except Exception as e:
        logger.error("Task failed", task_id=task_id)
```

### External API Call

```python
async def call_external_api(endpoint: str):
    logger.info("Calling external API", endpoint=endpoint)
    
    start = time.time()
    try:
        response = await httpx.get(endpoint)
        duration_ms = (time.time() - start) * 1000
        
        logger.info(
            "API call completed",
            endpoint=endpoint,
            status=response.status_code,
            duration_ms=round(duration_ms, 2)
        )
        return response
    except Exception as e:
        logger.error("API call failed", endpoint=endpoint, error=str(e))
        raise
```

---

**Version:** 1.0.0  
**Last Updated:** January 24, 2026

**Print this and keep it handy! 📋**
