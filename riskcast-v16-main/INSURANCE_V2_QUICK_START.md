# RISKCAST Insurance Module V2 - Quick Start Guide

## Overview

The Insurance Module V2 provides enterprise-grade insurtech integration, supporting both classical and parametric insurance products.

## What's Been Implemented

### ✅ Core Foundation (Complete)

1. **Type System** (`src/types/insurance.ts`)
   - Complete TypeScript definitions for all insurance entities
   - Product, Quote, Transaction, Policy, Claim models
   - AI Advisor response types

2. **Data Models** (`app/models/insurance.py`)
   - Python dataclasses matching TypeScript types
   - Full serialization support
   - Transaction state machine

3. **Parametric Engine** (`app/services/parametric_engine.py`)
   - Pricing for rainfall, port congestion, cyclone parametric products
   - Trigger evaluation logic
   - Basis risk calculation

4. **Quote Service** (`app/services/insurance_quote_service.py`)
   - Generate classical marine cargo quotes
   - Generate parametric quotes (port delay, weather delay)
   - Quote comparison and recommendations

5. **API Routes** (`app/api/v2/insurance_routes.py`)
   - Quote generation endpoint
   - Transaction management
   - Claims submission
   - Product catalog

## API Endpoints

### Generate Insurance Quotes

```bash
POST /api/v2/insurance/quotes/generate
Content-Type: application/json

{
  "risk_assessment": {
    "risk_score": {
      "overallScore": 67.5
    },
    "layers": [
      {"name": "Port Congestion", "score": 72},
      {"name": "Weather Risk", "score": 65}
    ]
  },
  "shipment_data": {
    "cargo": {
      "value_usd": 100000,
      "type": "electronics"
    },
    "transport": {
      "mode": "ocean"
    },
    "route": {
      "pol": "CNSHA",
      "pod": "USLAX"
    }
  }
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "quotes": [
      {
        "quote_id": "QUOTE_ABC123",
        "product_id": "marine_cargo_icc_a",
        "premium": {
          "total_premium": 825.00,
          "currency": "USD"
        },
        "coverage": {
          "sum_insured": 100000,
          "deductible": 5000
        }
      },
      {
        "quote_id": "QUOTE_DEF456",
        "product_id": "port_delay_parametric",
        "premium": {
          "total_premium": 893.00
        },
        "expected_payout": 744.00,
        "trigger_probability": 0.12
      }
    ],
    "count": 2
  }
}
```

### List Products

```bash
GET /api/v2/insurance/products
```

### Get Product Details

```bash
GET /api/v2/insurance/products/{product_id}
```

### Create Transaction

```bash
POST /api/v2/insurance/transactions/create
Content-Type: application/json

{
  "quote_id": "QUOTE_ABC123",
  "riskcast_assessment_id": "ASM_XYZ789",
  "shipment_reference": "SHIP_001",
  "insured_party": {
    "legal_name": "Acme Import Export Co Ltd",
    "registration_number": "12345678",
    "country": "SG",
    "address": {
      "street": "123 Main St",
      "city": "Singapore",
      "postal_code": "123456",
      "country": "SG"
    },
    "contact": {
      "name": "John Doe",
      "email": "john@acme.com",
      "phone": "+65 1234 5678"
    }
  },
  "coverage_config": {
    "sum_insured": 100000,
    "deductible": 5000,
    "effective_date": "2026-01-15T00:00:00Z",
    "expiry_date": "2026-04-15T00:00:00Z"
  }
}
```

### Submit Claim

```bash
POST /api/v2/insurance/claims/submit
Content-Type: application/json

{
  "policy_number": "RSK-PARAM-PORT_DELAY-ABC123",
  "claim_type": "classical_manual",
  "incident_date": "2026-01-18T00:00:00Z",
  "loss_type": "theft",
  "estimated_loss": 15000,
  "description": "Container fell during loading",
  "documents": [
    {"type": "photos", "url": "https://..."},
    {"type": "survey_report", "url": "https://..."}
  ]
}
```

## Integration with Risk Assessment

The insurance module integrates seamlessly with RISKCAST risk assessments:

1. **After Risk Assessment**: Call `/api/v2/insurance/quotes/generate` with the risk assessment result
2. **Quote Selection**: User selects preferred quote
3. **Transaction Creation**: Create transaction with selected quote
4. **Payment & Binding**: Process payment and bind policy
5. **Policy Active**: Monitor parametric triggers or file claims as needed

## Product Types

### Classical Insurance
- **Marine Cargo (ICC A/B/C)**: Traditional cargo insurance
- **Status**: V3 Transactional (ready for carrier integration)
- **Pricing**: Based on risk score adjustments

### Parametric Insurance
- **Port Delay**: Triggers on container dwell time > threshold
- **Weather Delay**: Triggers on rainfall > threshold
- **Status**: V2 API+Parametric (pricing and evaluation ready)
- **Pricing**: Based on historical trigger frequency and expected payout

## Next Steps for Full Implementation

1. **Carrier API Integration**
   - Implement Allianz AGCS adapter
   - Implement Swiss RE parametric adapter
   - Test quote and bind flows

2. **Payment Processing**
   - Integrate Stripe for payments
   - Support wire transfers
   - Enterprise net terms

3. **KYC/AML**
   - Integrate ComplyAdvantage or Trulioo
   - Sanctions screening
   - PEP checks

4. **Frontend Components**
   - Quote comparison UI
   - Checkout flow
   - Policy dashboard

5. **Parametric Monitoring**
   - Background jobs for trigger monitoring
   - Webhook handlers for data providers
   - Auto-claim processing

## Testing

### Test Quote Generation

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v2/insurance/quotes/generate",
    json={
        "risk_assessment": {
            "risk_score": {"overallScore": 67.5},
            "layers": [
                {"name": "Port Congestion", "score": 72},
                {"name": "Weather Risk", "score": 65}
            ]
        },
        "shipment_data": {
            "cargo": {"value_usd": 100000, "type": "electronics"},
            "transport": {"mode": "ocean"},
            "route": {"pol": "CNSHA", "pod": "USLAX"}
        }
    }
)

print(response.json())
```

## Architecture Notes

- **Modular Design**: Each component (pricing, evaluation, quotes) is independent
- **Type Safety**: Full TypeScript types for frontend, Python dataclasses for backend
- **Extensible**: Easy to add new products, carriers, or trigger types
- **Compliant**: Follows insurance industry standards and best practices

## Documentation

- Full specification: See the original Insurance Module V2 document
- Implementation status: `INSURANCE_MODULE_V2_IMPLEMENTATION.md`
- API docs: Auto-generated Swagger at `/docs` when server is running
