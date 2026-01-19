# 📡 API Documentation

## 🌐 Base URL

Development: `http://localhost:8000`  
Production: `https://yourdomain.com`

## 📚 API Versions

- **v1 (Current):** `/api/v1/` - Active version
- **Legacy:** `/api/` - Backward compatibility (deprecated)

---

## 🔐 Authentication

Currently, API uses session-based authentication. API keys may be required for some endpoints.

---

## 📋 Endpoints

### Risk Analysis

#### POST `/api/v1/risk/v2/analyze`

Analyze shipment risk using Engine v2.

**Request Body:**
```json
{
  "shipment": {
    "trade_route": {
      "pol": "VNSGN",
      "pod": "USNYC",
      "mode": "SEA",
      "container_type": "40GP",
      "etd": "2025-02-01",
      "transit_time_days": 30
    },
    "cargo_packing": {
      "cargo_type": "Electronics",
      "hs_code": "8471.30",
      "gross_weight_kg": 15000,
      "volume_cbm": 65.5
    },
    "seller": {
      "company": "Seller Co.",
      "country": "Vietnam"
    },
    "buyer": {
      "company": "Buyer Co.",
      "country": "USA"
    }
  },
  "riskModules": {
    "esg": true,
    "weather": true,
    "congestion": true,
    "carrier_perf": true,
    "market": true,
    "insurance": true
  }
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Analysis completed",
  "data": {
    "risk_score": 6.5,
    "risk_level": "MEDIUM",
    "layer_scores": {...},
    "monte_carlo": {...},
    "financial_metrics": {...}
  },
  "status_code": 200
}
```

**Response (Error):**
```json
{
  "success": false,
  "error": true,
  "message": "Validation error",
  "error_code": "VALIDATION_ERROR",
  "error_type": "validation",
  "status_code": 422,
  "errors": {
    "shipment.trade_route.pol": ["POL is required"]
  }
}
```

**Status Codes:**
- `200` - Success
- `400` - Bad Request
- `422` - Validation Error
- `500` - Internal Server Error

---

### Legacy Endpoints

#### POST `/api/analyze`

Legacy risk analysis endpoint (deprecated, use `/api/v1/risk/v2/analyze` instead).

---

## 📖 Interactive API Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **OpenAPI Schema:** `http://localhost:8000/openapi.json`

---

## 🔄 Standard Response Format

### Success Response

```json
{
  "success": true,
  "message": "Success message",
  "data": {...},
  "status_code": 200,
  "meta": {...}  // Optional
}
```

### Error Response

```json
{
  "success": false,
  "error": true,
  "message": "Error message",
  "error_code": "ERROR_CODE",
  "error_type": "validation|client|server|authentication",
  "status_code": 400,
  "details": {...},  // Optional
  "errors": {...}    // For validation errors
}
```

---

## 🚨 Error Codes

### Client Errors (4xx)

- `VALIDATION_ERROR` - Input validation failed
- `NOT_FOUND` - Resource not found
- `UNAUTHORIZED` - Authentication required
- `FORBIDDEN` - Access denied

### Server Errors (5xx)

- `INTERNAL_SERVER_ERROR` - Generic server error
- `RISK_CALCULATION_ERROR` - Risk calculation failed
- `EXTERNAL_API_ERROR` - External API call failed
- `CONFIGURATION_ERROR` - Configuration error

---

## 📝 Examples

### cURL Example

```bash
curl -X POST "http://localhost:8000/api/v1/risk/v2/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "shipment": {
      "trade_route": {
        "pol": "VNSGN",
        "pod": "USNYC",
        "mode": "SEA"
      }
    }
  }'
```

### Python Example

```python
import requests

url = "http://localhost:8000/api/v1/risk/v2/analyze"
payload = {
    "shipment": {
        "trade_route": {
            "pol": "VNSGN",
            "pod": "USNYC",
            "mode": "SEA"
        }
    }
}

response = requests.post(url, json=payload)
data = response.json()

if data["success"]:
    print(f"Risk Score: {data['data']['risk_score']}")
else:
    print(f"Error: {data['message']}")
```

### JavaScript Example

```javascript
fetch('http://localhost:8000/api/v1/risk/v2/analyze', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    shipment: {
      trade_route: {
        pol: 'VNSGN',
        pod: 'USNYC',
        mode: 'SEA'
      }
    }
  })
})
.then(response => response.json())
.then(data => {
  if (data.success) {
    console.log('Risk Score:', data.data.risk_score);
  } else {
    console.error('Error:', data.message);
  }
});
```

---

## 🔒 Rate Limiting

Currently no rate limiting. May be added in the future.

---

## 📞 Support

For API issues or questions:
- Check interactive docs: `/docs`
- Review error messages
- Check logs: `logs/api.log`

---

**Last Updated:** 2025  
**API Version:** v1

