# Decision Replay System Complete

**Date:** January 2026  
**Status:** Implementation complete  
**Feature:** Reproduce any risk decision from the audit trail for compliance and verification

---

## Summary

Implemented a **Decision Replay System** that reproduces risk decisions from the audit trail using original inputs, model version, seed, and (when available) archived data state. Supports determinism verification, decision package export for regulatory review, and integrity checks (input/result/model hashes, audit chain).

---

## What Was Implemented

### 1. `app/core/audit/decision_replay.py`

- **`ReplayResult`**  
  - Original vs replayed risk/expected-loss, result hashes; `is_deterministic`; model info; replay metadata; `input_hash_match` / `model_hash_match`; `differences` when non-deterministic.

- **`DecisionPackage`**  
  - Full decision context: risk_run, inputs, input_hash, data_snapshot, data_sources, data_quality, model version/parameters/hash, result, result_hash, seed, audit_events, package_hash, generated_at.

- **`DecisionReplaySystem`**
  - **`replay_decision(risk_run_id)`** (async)  
    - Loads `RiskRun`, `RiskAssessment`, `RiskModelVersion`.  
    - Rebuilds `UnifiedShipmentData` from `input_snapshot` + optional `data_snapshot`.  
    - Runs `CalibratedRiskEngine` with original model and seed.  
    - Compares replayed vs stored results; sets `is_deterministic`, `input_hash_match`, `model_hash_match`; fills `differences` if not deterministic.  
    - Appends `COMPLIANCE` / `DECISION_REPLAYED` to immutable audit ledger.
  - **`get_decision_package(risk_run_id)`** (async)  
    - Builds `DecisionPackage` from risk run, assessment, model, and audit events for the run.  
    - Computes `package_hash`.  
    - Appends `COMPLIANCE` / `DECISION_PACKAGE_EXPORTED`.
  - **`verify_decision_integrity(risk_run_id)`** (sync)  
    - Checks input hash (via `compute_input_hash`), result hash, model hash, and audit chain (using `ImmutableAuditLedger.verify_chain`).  
    - Returns `{ risk_run_id, verified_at, is_valid, checks }`.

- **Helpers**  
  - `_inputs_to_shipment_data`: maps `inputs` + `data_snapshot` → `UnifiedShipmentData`.  
  - `_replay_with_archived_data`: runs engine with archived data.  
  - `_compute_differences`, `_compute_result_hash`, `_compute_package_hash`.

### 2. Integration

- **Audit**  
  - Uses `ImmutableAuditLedger` for replay and package-export events.  
  - `verify_decision_integrity` uses `get_events_for_entity` and `verify_chain`.

- **Models**  
  - `RiskRun`, `RiskAssessment` (from `app.models`), `RiskModelVersion` (from `app.modules.model_versioning.models`).  
  - Inputs from `assessment.input_snapshot_json`; optional `data_snapshot` from `risk_run.data_snapshot_json` (when present).

- **Engine**  
  - `CalibratedRiskEngine` from `app.core.risk_engine.v16.risk_engine_calibrated`; replay runs with `audit=None` to avoid double audit, and all replay-related audit goes through the immutable ledger.

### 3. Exports

- `app.core.audit` now exports `DecisionReplaySystem`, `DecisionPackage`, `ReplayResult`.

---

## Acceptance Criteria

- [x] Replay any risk decision from audit trail (via risk run + assessment + model).
- [x] Verify determinism (same inputs + model + seed → same outputs; `is_deterministic` + `differences`).
- [x] Export decision package for compliance (`get_decision_package`).
- [x] Verify stored hashes match computed (input, result, model) in `verify_decision_integrity`.
- [x] Track replay and package export in audit trail (`DECISION_REPLAYED`, `DECISION_PACKAGE_EXPORTED`).
- [x] Handle missing model version gracefully (clear `ValueError` when model not found).
- [x] Detailed difference reporting when non-deterministic (`_compute_differences`).

---

## Usage

```python
from app.core.audit import (
    create_immutable_audit_ledger,
    DecisionReplaySystem,
)
from app.database import SessionLocal

db = SessionLocal()
audit = create_immutable_audit_ledger(db)
replay = DecisionReplaySystem(db, audit)

# Replay and verify determinism
result = await replay.replay_decision("risk-run-uuid")
assert result.is_deterministic
assert result.input_hash_match and result.model_hash_match

# Export for regulators
pkg = await replay.get_decision_package("risk-run-uuid")
# pkg.inputs, pkg.result, pkg.audit_events, pkg.package_hash, ...

# Integrity check only (no replay)
integrity = replay.verify_decision_integrity("risk-run-uuid")
assert integrity["is_valid"]
```

---

## Notes

- **Input hashes**  
  - `verify_decision_integrity` and replay use `compute_input_hash` from `app.core.risk_input.canonicalization` over `assessment.input_snapshot_json` for consistency with assessments.

- **Data snapshot**  
  - Replay uses `data_snapshot` when `risk_run.data_snapshot_json` exists; otherwise minimal defaults. Full data archival (e.g. weather, ports) can be added later.

- **Model version**  
  - Replay requires a resolved `RiskModelVersion`. If `risk_run.model_version_id` is missing or the model was removed, replay raises a clear error.

- **Audit**  
  - Replay and package export events are written only to the **immutable** audit ledger, not the legacy one.
