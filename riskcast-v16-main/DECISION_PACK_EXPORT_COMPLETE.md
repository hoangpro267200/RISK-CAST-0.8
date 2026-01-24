# Decision Package Export Service - Complete

**Date:** January 2026  
**Status:** Implementation complete  
**Feature:** Complete decision package export for regulatory submissions, audit responses, dispute resolution, and reinsurance documentation

---

## Summary

Created a **comprehensive decision package export service** that generates ZIP files containing all information needed to understand and verify risk/underwriting/claims decisions. Packages include decision data, audit trails, evidence bundles, verification proofs, and model parameters.

---

## What Was Implemented

### 1. **`app/compliance/decision_pack_export.py`**

**Classes:**

- **`DecisionPackStorage` (Protocol)**  
  - Protocol for storage backends  
  - `upload_decision_pack(pack_id, content, content_type) -> str` (download URL)

- **`LocalDecisionPackStorage`**  
  - Implementation using `EvidenceStorage`  
  - Stores to `decision_packs/{pack_id}.zip`  
  - Returns download URL path: `/api/v3/compliance/decision-packs/{pack_id}/download`

- **`ExportedDecisionPack` (dataclass)**  
  - `pack_id`, `entity_type`, `entity_id`  
  - `files` (list with name, type, hash)  
  - `total_size_bytes`, `created_at`, `created_by`  
  - `manifest_hash`, `is_verified`  
  - `download_url`, `expires_at` (7 days)

- **`DecisionPackExportService`**  
  - Main service for exporting decision packages  
  - Methods: `export_risk_run`, `export_policy`, `export_claim`  
  - Helper: `_create_decision_summary`

**Methods:**

- **`export_risk_run(risk_run_id, include_replay=True, include_evidence=True, created_by_user_id="system")`**  
  - Exports complete decision package for a risk run  
  - Uses `DecisionReplaySystem.get_decision_package()` to get full context  
  - Creates ZIP with:
    1. `01_decision_summary.json` - Human-readable summary
    2. `02_inputs.json` - Full input data
    3. `03_data_snapshot.json` - Data state at decision time
    4. `04_model_parameters.json` - Model version and parameters
    5. `05_results.json` - Risk calculation results
    6. `06_audit_trail.json` - All audit events
    7. `07_replay_verification.json` (optional) - Replay determinism proof
    8. `08_integrity_verification.json` - Hash verification checks
    9. `00_manifest.json` - Package manifest with file hashes
  - All files are SHA-256 hashed  
  - Uploads to storage and audits the export

- **`export_policy(policy_id, include_risk_runs=True, include_claims=True, created_by_user_id="system")`**  
  - Exports complete decision package for a policy  
  - Creates ZIP with:
    1. `01_policy_summary.json` - Policy details (number, status, dates, premium, terms)
    2. `02_underwriting_decision.json` - Model version, risk run, risk snapshot, policy hash
    3. `03_audit_trail.json` - Policy audit events
    4. `04_risk_runs.json` (optional) - Related risk run (from `policy.risk_run_id`)
    5. `05_claims.json` (optional) - Related claims
    6. `00_manifest.json` - Package manifest
  - Uses `Policy` from `app.modules.underwriting.models`  
  - Uses `ModulesRiskRun` from `app.modules.risk_runs.models` for risk run data  
  - Uses `Claim` from `app.modules.claims.models` for claims

- **`export_claim(claim_id, include_evidence=True, created_by_user_id="system")`**  
  - Exports complete decision package for a claim  
  - Creates ZIP with:
    1. `01_claim_summary.json` - Claim details (number, status, FNOL, decision, amounts)
    2. `02_fnol.json` - First Notice of Loss data
    3. `03_adjudication.json` - Adjudication decision, reason, calculation details
    4. `04_audit_trail.json` - Claim audit events
    5. `05_evidence.json` (optional) - Evidence bundle verification and custody history
    6. `00_manifest.json` - Package manifest
  - Uses `ChainOfCustodyService.verify_bundle()` and `get_custody_history()` for evidence

**Factory:**

- **`create_decision_pack_export_service(db, audit, replay_system, evidence_service, storage=None)`**  
  - Creates service instance  
  - Defaults to `LocalDecisionPackStorage` using `LocalEvidenceStorage` if storage not provided

### 2. **`app/compliance/__init__.py`**

- Exports `DecisionPackExportService`, `ExportedDecisionPack`, `DecisionPackStorage`, `LocalDecisionPackStorage`, `create_decision_pack_export_service`

---

## Acceptance Criteria

- [x] Export risk run with all data – `export_risk_run()` includes inputs, data snapshot, model params, results, audit trail, replay verification, integrity checks
- [x] Export policy with related entities – `export_policy()` includes policy, underwriting decision, risk run, claims
- [x] Export claim with evidence – `export_claim()` includes claim, FNOL, adjudication, evidence bundle
- [x] ZIP file with manifest – All exports create ZIP with `00_manifest.json` listing all files
- [x] All files hashed – Each file has SHA-256 hash in manifest
- [x] Replay verification included – Optional replay verification for risk runs
- [x] Upload to storage – All packages uploaded via `DecisionPackStorage`
- [x] All exports audited – Every export creates audit event in `ImmutableAuditLedger`

---

## Usage

**Export risk run:**
```python
from app.compliance import create_decision_pack_export_service
from app.core.audit import create_immutable_audit_ledger, DecisionReplaySystem
from app.evidence import create_chain_of_custody_service

service = create_decision_pack_export_service(
    db=db,
    audit=create_immutable_audit_ledger(db),
    replay_system=DecisionReplaySystem(db, create_immutable_audit_ledger(db)),
    evidence_service=create_chain_of_custody_service(db, audit, storage),
)

pack = await service.export_risk_run(
    risk_run_id="01H...",
    include_replay=True,
    created_by_user_id="01H..."
)
# pack.download_url -> "/api/v3/compliance/decision-packs/pack_01H..._20260123120000/download"
```

**Export policy:**
```python
pack = await service.export_policy(
    policy_id="01H...",
    include_risk_runs=True,
    include_claims=True,
    created_by_user_id="01H..."
)
```

**Export claim:**
```python
pack = await service.export_claim(
    claim_id="01H...",
    include_evidence=True,
    created_by_user_id="01H..."
)
```

---

## Package Structure

**Risk Run Package:**
- `00_manifest.json` - Package manifest with file hashes
- `01_decision_summary.json` - Human-readable summary
- `02_inputs.json` - Full input data
- `03_data_snapshot.json` - Data state snapshot
- `04_model_parameters.json` - Model version and parameters
- `05_results.json` - Risk calculation results
- `06_audit_trail.json` - Audit events
- `07_replay_verification.json` (optional) - Replay determinism proof
- `08_integrity_verification.json` - Hash verification

**Policy Package:**
- `00_manifest.json`
- `01_policy_summary.json`
- `02_underwriting_decision.json`
- `03_audit_trail.json`
- `04_risk_runs.json` (optional)
- `05_claims.json` (optional)

**Claim Package:**
- `00_manifest.json`
- `01_claim_summary.json`
- `02_fnol.json`
- `03_adjudication.json`
- `04_audit_trail.json`
- `05_evidence.json` (optional)

---

## Notes

- **Storage:** Uses `DecisionPackStorage` protocol. Default implementation (`LocalDecisionPackStorage`) uses `EvidenceStorage` and stores to `decision_packs/{pack_id}.zip`. Returns download URL path that API can serve.
- **Hashing:** All files are SHA-256 hashed. Manifest includes all file hashes and a manifest hash for package integrity verification.
- **Audit:** All exports are audited via `ImmutableAuditLedger.append_event()` with `COMPLIANCE` event type and action `DECISION_PACK_EXPORTED`, `POLICY_PACK_EXPORTED`, or `CLAIM_PACK_EXPORTED`.
- **Replay:** Risk run exports can include replay verification (optional) to prove determinism. Uses `DecisionReplaySystem.replay_decision()`.
- **Evidence:** Claim exports can include evidence bundle verification and custody history (optional). Uses `ChainOfCustodyService.verify_bundle()` and `get_custody_history()`.
- **Models:** Uses `Policy` from `app.modules.underwriting.models`, `Claim` from `app.modules.claims.models`, `ModulesRiskRun` from `app.modules.risk_runs.models` for policy exports. Risk run exports use `DecisionReplaySystem` which uses `app.models.risk_run.RiskRun` (legacy).
- **Expiration:** All packages have 7-day expiration (`expires_at = created_at + 7 days`).
- **Async:** `export_risk_run`, `export_policy`, `export_claim` are async. `verify_decision_integrity`, `get_events_for_entity`, `verify_bundle`, `get_custody_history`, `append_event` are sync (no await).

The decision pack export service is ready for regulatory submissions, audit responses, dispute resolution, and reinsurance documentation.
