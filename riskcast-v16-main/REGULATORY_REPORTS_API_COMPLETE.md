# Regulatory Reporting API - Complete

**Date:** January 2026  
**Status:** Implementation complete  
**Feature:** API for generating regulatory reports (solvency, loss ratio, model performance, claims statistics)

---

## Summary

Created **`app/api/v3/regulatory.py`** with endpoints to generate regulatory reports for solvency, loss ratios, model performance, and claims statistics. All report generation is audited via the immutable audit ledger.

---

## What Was Implemented

### 1. **`app/api/v3/regulatory.py`** (prefix `/regulatory`)

**Schemas:**
- **`ReportPeriod`** – `start_date`, `end_date`, `period_type` (CUSTOM, MONTHLY, QUARTERLY, ANNUAL)
- **`ReportRequest`** – `report_type`, `start_date`, `end_date`, `include_details`, `format` (JSON/PDF/EXCEL)
- **`SolvencyReport`** – Premium (gross/net/earned), losses (incurred/paid/outstanding), ratios (loss/expense/combined), capital (required/available/solvency ratio), exposure, VaR 95/99
- **`LossRatioReport`** – `overall_loss_ratio`, `by_cargo_type`, `by_route`, `by_carrier`, `monthly_trend`, `loss_causes`
- **`ModelPerformanceReport`** – `model_versions`, `predicted_vs_actual`, `calibration_error`, `discrimination_auc`, `backtesting_results`, `psi_score`, `csi_scores`
- **`ClaimsStatisticsReport`** – Volume (filed/closed/pending), amounts (claimed/paid/denied/pending), processing (avg days, within SLA, compliance %), `by_loss_type`, `by_status`

**Endpoints:**

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/regulatory/reports/solvency` | Generate solvency/capital adequacy report |
| `POST` | `/regulatory/reports/loss-ratio` | Generate loss ratio analysis by segment |
| `POST` | `/regulatory/reports/model-performance` | Generate model performance validation report |
| `POST` | `/regulatory/reports/claims-statistics` | Generate claims statistics report |
| `GET` | `/regulatory/report-types` | List available regulatory report types |

**Request body (report endpoints):** `ReportRequest` with `start_date`, `end_date`, optional `report_type`, `include_details`, `format`.

**Authentication & authorization:** All endpoints use `PermissionChecker("compliance:export")` and `resolve_tenant_context`. Queries are tenant-scoped when `context.tenant_id` is set.

**Audit:** Each report generation triggers `audit.append_event` with `COMPLIANCE` event type and actions:
- `SOLVENCY_REPORT_GENERATED`
- `LOSS_RATIO_REPORT_GENERATED`
- `MODEL_PERFORMANCE_REPORT_GENERATED`
- `CLAIMS_STATS_REPORT_GENERATED`

---

## Data Sources

- **Solvency:** `Policy` (underwriting), `Claim` (claims). Premium from `premium_json`; coverage from `terms_json`.
- **Loss ratio:** `HistoricalShipment` from `app.data.historical.loss_data_repository`. Returns 501 if not available.
- **Model performance:** `RiskRun` (risk_runs), `RiskModelVersion` (model_versioning), `HistoricalShipment` (optional) for predicted vs actual.
- **Claims statistics:** `Claim` (claims). Claimed amount from `fnol_json` or `approved_amount_cents`; loss type from `fnol_json`.

---

## Acceptance Criteria

- [x] Solvency report with capital metrics – `POST /regulatory/reports/solvency`
- [x] Loss ratio by segment – `POST /regulatory/reports/loss-ratio` (cargo, route, carrier, monthly trend, loss causes)
- [x] Model performance validation – `POST /regulatory/reports/model-performance` (calibration, AUC, backtesting, PSI)
- [x] Claims statistics – `POST /regulatory/reports/claims-statistics`
- [x] All reports audited – Immutable audit ledger, sync `append_event`
- [x] Report types documented – `GET /regulatory/report-types`

---

## Usage

**Solvency report:**
```bash
POST /api/v3/regulatory/reports/solvency
Content-Type: application/json
{
  "report_type": "CUSTOM",
  "start_date": "2026-01-01",
  "end_date": "2026-01-31",
  "include_details": false,
  "format": "JSON"
}
```

**Loss ratio report:**
```bash
POST /api/v3/regulatory/reports/loss-ratio
Content-Type: application/json
{ "start_date": "2026-01-01", "end_date": "2026-01-31" }
```

**Model performance report:**
```bash
POST /api/v3/regulatory/reports/model-performance
Content-Type: application/json
{ "start_date": "2026-01-01", "end_date": "2026-01-31" }
```

**Claims statistics report:**
```bash
POST /api/v3/regulatory/reports/claims-statistics
Content-Type: application/json
{ "start_date": "2026-01-01", "end_date": "2026-01-31" }
```

**Report types:**
```bash
GET /api/v3/regulatory/report-types
```

---

## Notes

- **Tenant scoping:** Policy, Claim, RiskRun queries filter by `tenant_id` when `TenantContext` has a tenant.
- **Helpers:** `_policy_total_premium`, `_policy_coverage_limit`, `_claim_claimed_amount`, `_claim_loss_type` derive values from JSON fields.
- **sklearn:** Model performance uses `roc_auc_score` when available; otherwise AUC defaults to 0.5.
- **numpy:** Used for means and arrays in model performance and claims stats.
- **Report IDs:** Format `{type}_{YYYYMMDDHHMMSS}` (e.g. `solvency_20260123143000`).

The regulatory API is mounted at `/api/v3/regulatory` and requires `compliance:export` permission.
