# RISKCAST Deprecation Guide

## Overview

This document tracks deprecated features, APIs, and components in RISKCAST.
Please migrate to the recommended alternatives before the removal date.

---

## API Deprecations

### v1 API Endpoints (Deprecated v17, Remove v18)

| Old Endpoint | New Endpoint | Migration Notes |
|--------------|--------------|-----------------|
| `POST /api/v1/risk/analyze` | `POST /api/v2/risk/analyze` | See [Request Format Changes](#request-format-changes) |
| `GET /api/v1/shipments` | `GET /api/v2/shipments` | Response includes pagination |
| `POST /api/v1/ai/chat` | `POST /api/v2/ai/advisor/chat` | Supports streaming |

#### Request Format Changes

**v1 Format (Deprecated):**
```json
{
  "cargo_type": "GENERAL",
  "mode": "sea",
  "value": 50000,
  "from_port": "CNSHA",
  "to_port": "USLAX"
}
```

**v2 Format (Current):**
```json
{
  "cargo_type": "general_merchandise",
  "transport_mode": "ocean_fcl",
  "cargo_value": 50000,
  "origin_port": "CNSHA",
  "destination_port": "USLAX"
}
```

#### Field Mapping

| v1 Field | v2 Field |
|----------|----------|
| `value` | `cargo_value` |
| `from_port` | `origin_port` |
| `to_port` | `destination_port` |
| `mode` | `transport_mode` |
| `ship_date` | `departure_date` |
| `arrive_date` | `arrival_date` |

#### Enum Value Changes

**Cargo Types:**
| v1 Value | v2 Value |
|----------|----------|
| `GENERAL` | `general_merchandise` |
| `ELECTRONICS` | `electronics_high_value` |
| `PERISHABLE` | `perishables_refrigerated` |
| `HAZMAT` | `hazardous_materials` |

**Transport Modes:**
| v1 Value | v2 Value |
|----------|----------|
| `sea` | `ocean_fcl` |
| `air` | `air_freight` |
| `truck` | `road_ftl` |
| `rail` | `rail` |

---

## Response Format Changes

**v1 Response (Deprecated):**
```json
{
  "score": 67.5,
  "level": "MEDIUM",
  "var": 15000,
  "expectedLoss": 8000,
  "factors": [...]
}
```

**v2 Response (Current):**
```json
{
  "risk_score": 67.5,
  "risk_level": "medium",
  "var_95": 15000,
  "cvar_95": 22000,
  "expected_loss": 8000,
  "confidence": 0.95,
  "risk_factors": [...],
  "recommendations": [...],
  "metadata": {
    "engine_version": "v17",
    "calculation_time_ms": 150
  }
}
```

---

## Frontend Components (Vue.js → React)

### Deprecated Components (Remove v18)

| Vue Component | React Replacement | Status |
|---------------|-------------------|--------|
| `RiskGauge.vue` | `RiskGaugePremium.tsx` | Deprecated |
| `ShipmentForm.vue` | `ShipmentWizard.tsx` | Deprecated |
| `Dashboard.vue` | `DashboardPage.tsx` | Deprecated |
| `AIChat.vue` | `AiAdvisorDock.tsx` | Deprecated |

### Migration Steps

1. Replace Vue component imports with React equivalents
2. Update state management from Vuex to React hooks
3. Replace Vue Router with React Router
4. Update event handlers from `@click` to `onClick`

---

## Backend Components

### Deprecated Modules (Remove v18)

| Module | Replacement | Notes |
|--------|-------------|-------|
| `app/risk_engine.py` | `app/core/engine/risk_engine_v16.py` | Old monolithic engine |
| `app/memory.py` | `app/database/` | Use SQLAlchemy models |
| `app/api.py` | `app/api/v2/` | Use versioned API routes |

### Deprecated Functions

```python
# DEPRECATED: Use calculate_risk_v2() instead
def calculate_risk(shipment):
    pass

# DEPRECATED: Use RiskEngine.analyze() instead
def run_analysis(data):
    pass

# DEPRECATED: Use StateStorage class instead
def save_to_memory(key, value):
    pass
```

---

## Configuration Changes

### Environment Variables

| Old Variable | New Variable | Default |
|--------------|--------------|---------|
| `DB_URL` | `DATABASE_URL` | - |
| `AI_KEY` | `ANTHROPIC_API_KEY` | - |
| `CACHE_HOST` | `REDIS_URL` | `redis://localhost:6379/0` |

---

## Using the Legacy Adapter

During migration, you can use the legacy adapter for backward compatibility:

```python
from app.core.adapters.legacy_adapter import RequestAdapter, ResponseAdapter

# Convert v1 request to v2
v2_request = RequestAdapter.v1_to_v2_risk(v1_request)

# Call v2 handler
v2_response = await analyze_risk(v2_request)

# Convert back to v1 for old clients
v1_response = ResponseAdapter.v2_to_v1_risk(v2_response)
```

### Deprecation Decorator

```python
from app.core.adapters.legacy_adapter import deprecated

@deprecated("Use /api/v2/risk/analyze instead")
async def old_endpoint():
    pass
```

---

## Deprecation Timeline

| Version | Date | Changes |
|---------|------|---------|
| v17 | 2026-01 | APIs marked deprecated, adapters added |
| v17.1 | 2026-02 | Deprecation warnings in logs |
| v18 | 2026-06 | v1 APIs removed |

---

## Getting Help

- **Migration Guide**: See `docs/MIGRATION_V16_TO_V17.md`
- **API Documentation**: See `docs/API_V2.md`
- **Support**: Contact support@riskcast.io

---

## Changelog

### v17.0.0 (2026-01)
- Marked v1 API endpoints as deprecated
- Added legacy adapters for backward compatibility
- Created migration documentation

### v16.5.0 (2025-12)
- Added v2 API endpoints (beta)
- Started deprecation process for Vue components
