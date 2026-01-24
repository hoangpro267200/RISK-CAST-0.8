# Risk Engine Calibration Support ✅

**Date:** January 23, 2026  
**Status:** ✅ Implementation Complete  
**Feature:** Calibrated Risk Engine Using ModelVersion Parameters

---

## Summary

Added `CalibratedRiskEngine` that uses calibrated parameters from `RiskModelVersion` instead of hardcoded values. The engine loads weights, correlations, and the loss function from the model, runs deterministic Monte Carlo with calibrated correlations, and records input/result hashes plus a full audit trail.

---

## What Was Implemented

### 1. `app/core/risk_engine/v16/risk_engine_calibrated.py`

- **CalibratedRiskEngine**
  - Builds layer weights, correlation matrix, and loss function from `RiskModelVersion` via `get_layer_weight`, `get_correlation`, and `get_loss_function_params`.
  - Normalizes weights; ensures correlation matrix is positive definite.
  - Supports POWER, EXPONENTIAL, and LOGISTIC loss functions from calibrated params.

- **CalibratedRiskResult**
  - Holds risk scores, VaR/CVaR, percentiles, factor attribution, model metadata, data quality, and audit fields (input/result hashes, seed).
  - `to_dict()` for JSON-friendly output.

- **`run_assessment(shipment_data, cargo_value_usd, n_simulations)`**
  - Uses `UnifiedShipmentData` and deterministic RNG (seed).
  - Computes layer scores, applies calibrated weights, runs Monte Carlo with correlated draws, applies calibrated loss function to obtain loss distribution.
  - Derives expected loss, VaR/CVaR, percentiles, attribution.
  - Computes `input_hash` and `result_hash` for reproducibility.
  - Optionally audits via `AuditLedger` when provided.

### 2. Factory and Package Layout

- **`create_calibrated_risk_engine(model_version, audit, seed, tenant_id)`**
  - Factory for `CalibratedRiskEngine`.

- **Package structure**
  - `app/core/risk_engine/__init__.py` – exports calibrated engine.
  - `app/core/risk_engine/v16/__init__.py` – exports `CalibratedRiskEngine`, `CalibratedRiskResult`, `create_calibrated_risk_engine`.

---

## Acceptance Criteria

- [x] Engine loads weights from ModelVersion (`get_layer_weight`)
- [x] Engine loads correlations from ModelVersion (`get_correlation`)
- [x] Engine uses calibrated loss function (`get_loss_function_params`)
- [x] Monte Carlo uses calibrated correlation matrix (Cholesky)
- [x] All calculations deterministic (seeded RNG)
- [x] Input and result hashes computed
- [x] Full audit trail (when audit provided)
- [x] Data quality tracked in result (`data_quality`, `data_confidence`, `data_warnings`)
- [x] Backward compatible with non‑calibrated models (defaults from model)

---

## Usage

```python
from app.core.risk_engine.v16 import create_calibrated_risk_engine
from app.modules.model_versioning.models import RiskModelVersion
from app.core.audit_ledger.ledger import AuditLedger
from app.services.unified_data_service import UnifiedDataService, create_unified_data_service

# Load model and create engine
model = db.query(RiskModelVersion).filter(RiskModelVersion.id == model_id).first()
audit = AuditLedger(db)
engine = create_calibrated_risk_engine(
    model_version=model,
    audit=audit,
    seed=42,
    tenant_id="optional_tenant_id",
)

# Collect data and run assessment
unified_svc = create_unified_data_service(audit)
shipment_data = await unified_svc.collect_shipment_data(...)
result = await engine.run_assessment(
    shipment_data=shipment_data,
    cargo_value_usd=500_000,
    n_simulations=10_000,
)

# Use result
print(result.overall_risk_score, result.expected_loss_usd, result.var_95)
print(result.to_dict())
```

---

## Files Touched

- **Added:** `app/core/risk_engine/__init__.py`
- **Added:** `app/core/risk_engine/v16/__init__.py`
- **Added:** `app/core/risk_engine/v16/risk_engine_calibrated.py`
- **Added:** `RISK_ENGINE_CALIBRATED_COMPLETE.md`

---

## Notes

- Uses `RiskModelVersion` (not `ModelVersion`). `AuditLedger` from `app.core.audit_ledger.ledger`.
- `append_event` requires `tenant_id`; use `tenant_id="system"` when no tenant.
- `UnifiedShipmentData` supplies `overall_data_quality`, `overall_confidence`, `data_warnings`, `collection_hash` for hashing and quality metadata.
- Non‑calibrated models work via model-level defaults (`get_layer_weight`, `get_correlation`, `get_loss_function_params`).
