# Structured Logging System

## 🎯 Quick Start

### 1. Initialize in your app

```python
from app.core.logging import setup_logging

# In app/main.py startup
logger = setup_logging(service_name="riskcast-api")
logger.info("Application started", version="1.0.0")
```

### 2. Add middleware

```python
from app.middleware.request_logging import (
    RequestLoggingMiddleware,
    SlowRequestLoggingMiddleware
)

app.add_middleware(SlowRequestLoggingMiddleware, threshold_ms=1000)
app.add_middleware(RequestLoggingMiddleware)
```

### 3. Use in your code

```python
from app.core.logging import get_logger

logger = get_logger(__name__)

# Basic logging
logger.info("Quote created", quote_id="QTE-123", premium=125000.00)

# Audit logging
logger.audit("policy_updated", "policy", "POL-456", user_id="user-789")

# Business events
logger.business_event("payment_received", amount=50000.00)

# Security events
logger.security_event("unauthorized_access", severity="high", ip="203.0.113.42")
```

## ✅ Verification

Run tests to verify the system works:

```bash
python test_logging_direct.py
```

All tests should pass:
- [PASS] Password masking works
- [PASS] API key masking works
- [PASS] Nested dictionary masking works
- [PASS] Bearer token masking works
- [PASS] JSON formatting works
- [PASS] Extra data formatting works
- [PASS] Context setting works
- [PASS] Context clearing works
- [PASS] Info logging with kwargs works
- [PASS] Audit logging works
- [PASS] Business event logging works
- [PASS] Security event logging works
- [PASS] Full integration test passed

## 📚 Documentation

- **Full Guide:** `/docs/STRUCTURED_LOGGING_GUIDE.md`
- **Quick Reference:** `/docs/LOGGING_QUICK_REFERENCE.md`
- **Summary:** `/STRUCTURED_LOGGING_SUMMARY.md`
- **Integration Example:** `logging_integration_example.py`

## 🔒 Security Features

- ✅ Automatic sensitive data masking
- ✅ Password/token/API key filtering
- ✅ Bearer token masking
- ✅ Credit card number masking
- ✅ Nested dictionary support

## 📊 Output Format

### Development (Human-readable)
```
2026-01-24 21:15:30 | INFO | app.api.quotes:create:145 | Quote created | request_id=req-123
```

### Production (JSON)
```json
{
  "timestamp": "2026-01-24T21:15:30.123Z",
  "level": "INFO",
  "service": "riskcast-api",
  "message": "Quote created",
  "request_id": "req-123",
  "user_id": "user-456",
  "extra": {
    "quote_id": "QTE-123",
    "premium": 125000.00
  }
}
```

## 🚀 Deployment

### Kubernetes + Fluentd + Elasticsearch

```bash
# Deploy Fluentd
kubectl apply -f k8s/logging/fluentd-config.yaml

# Create Elasticsearch credentials
kubectl create secret generic elasticsearch-credentials \
  --namespace=logging \
  --from-literal=host=elasticsearch.example.com \
  --from-literal=username=fluentd \
  --from-literal=password=your-password
```

## 🎓 Best Practices

1. **Use structured data** (not string concatenation)
   ```python
   # Good
   logger.info("Payment processed", payment_id="PAY-123", amount=1000)
   
   # Bad
   logger.info(f"Payment {payment_id} processed: ${amount}")
   ```

2. **Include relevant context**
   ```python
   logger.info("API call", 
       endpoint="/users",
       method="GET",
       status=200,
       duration_ms=145.23
   )
   ```

3. **Use specialized methods**
   ```python
   # For audit trails
   logger.audit("data_exported", "report", "RPT-123", user_id="user-456")
   
   # For business metrics
   logger.business_event("subscription_renewed", plan="premium")
   
   # For security monitoring
   logger.security_event("rate_limit_exceeded", severity="medium")
   ```

## 🔎 Querying Logs

### Elasticsearch queries

```bash
# Find all logs for a request
curl -X GET "https://elasticsearch.example.com/riskcast-logs-*/_search" \
  -H 'Content-Type: application/json' \
  -d '{"query": {"term": {"request_id": "req-abc123"}}}'

# Find errors in last hour
curl -X GET "https://elasticsearch.example.com/riskcast-logs-*/_search" \
  -d '{
    "query": {
      "bool": {
        "must": [
          {"range": {"timestamp": {"gte": "now-1h"}}},
          {"terms": {"level": ["ERROR", "CRITICAL"]}}
        ]
      }
    }
  }'
```

## 📞 Support

For issues or questions, see:
- `/docs/STRUCTURED_LOGGING_GUIDE.md` - Complete documentation
- `/docs/LOGGING_QUICK_REFERENCE.md` - Quick reference card
- `test_logging_direct.py` - Working examples

---

**Status:** ✅ Production Ready  
**Version:** 1.0.0  
**Last Updated:** January 24, 2026
