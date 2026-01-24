# Model Versions API & UI – Complete

**Date:** January 2026  
**Status:** Implementation complete  

## Summary

API and UI for managing risk model versions: list, detail, compare, publish, deprecate, set active, calibration info, usage stats.

---

## 1. Backend

### `app/api/v3/model_versions.py` (prefix `/models`)

- **GET /models/versions** – List versions (`status`, `include_deprecated`, `skip`, `limit`).
- **GET /models/active** – Active model version (from `SystemConfig` or latest published).
- **GET /models/versions/{id}** – Version detail.
- **GET /models/versions/{id}/parameters** – Full parameters (weights, correlations, loss).
- **GET /models/versions/{id}/calibration** – Calibration run info.
- **GET /models/versions/{id}/usage-stats** – Risk run counts by day (`?days=30`).
- **GET /models/compare/{id1}/{id2}** – Compare two versions.
- **POST /models/versions** – Create draft (existing create flow).
- **POST /models/versions/{id}/publish** – Publish (immutable hash, audit).
- **POST /models/versions/{id}/deprecate** – Deprecate with `{ reason, replacement_version_id? }`.
- **POST /models/set-active** – Set active version (`{ model_version_id }`).
- **POST /models/activations** – Create activation.
- **GET /models/activations** – List activations.
- **POST /models/activations/{id}/deactivate** – Deactivate activation.
- **GET /models/selection/preview** – Preview model selection.

### `app/models/system_config.py`

- **SystemConfig**: `id`, `key`, `value`, `description`, `created_at`, `updated_at`.
- Used for `active_model_version_id`.

### `app/modules/model_versioning/models.py`

- **RiskModelVersion**: added `deprecated_at`, `deprecated_reason`, `replacement_version_id`.

### `app/modules/model_versioning/service.py`

- **list_models** – List with filters.
- **get_model** – Get by ID.
- **create_draft_detailed** – Create DRAFT from `ModelVersionCreateRequest`.
- **deprecate** – Set DEPRECATED, store reason and replacement.
- **list_activations**, **create_activation_detailed**, **deactivate_activation** – Activation CRUD.
- **compare_versions** – Weights and loss diff.

### Migrations

- **041_create_system_configs** – `system_configs` table.
- **042_model_version_deprecation_fields** – Deprecation fields on `risk_model_versions`.

### Wiring

- **app/api/v3/__init__.py** – Imports and includes `model_versions_router` under v3.

---

## 2. Frontend

### `frontend/src/api/client.ts`

- **modelVersionsApi**: `listVersions`, `getActive`, `getVersion`, `getParameters`, `getCalibration`, `getUsageStats`, `compare`, `setActive`, `publish`, `deprecate`.

### `frontend/src/pages/models/ModelVersionsPage.tsx`

- Lists versions, shows active, “Set active” for published non-active.
- Links to `/app/models/versions/:id`.

### `frontend/src/pages/models/ModelVersionDetailPage.tsx`

- Version detail, “Set active”, links to parameters / calibration / usage-stats API.

### Routes

- **/app/models** – `ModelVersionsPage`.
- **/app/models/versions/:versionId** – `ModelVersionDetailPage`.

---

## 3. Acceptance criteria

- [x] List all model versions
- [x] Get version details and parameters
- [x] Compare two versions
- [x] Publish version (with immutable hash)
- [x] Deprecate version with reason (and optional replacement)
- [x] Set active version
- [x] Get usage statistics
- [x] Calibration info available
- [x] UI: list, detail, set-active, links to API

---

## 4. Usage

**API (base `/api/v3`):**

```bash
# List
GET /api/v3/models/versions?include_deprecated=true&limit=50

# Active
GET /api/v3/models/active

# Detail
GET /api/v3/models/versions/{id}

# Parameters / calibration / usage
GET /api/v3/models/versions/{id}/parameters
GET /api/v3/models/versions/{id}/calibration
GET /api/v3/models/versions/{id}/usage-stats?days=30

# Compare
GET /api/v3/models/compare/{id1}/{id2}

# Set active
POST /api/v3/models/set-active
Content-Type: application/json
{"model_version_id": "01H..."}

# Deprecate
POST /api/v3/models/versions/{id}/deprecate
Content-Type: application/json
{"reason": "Superseded by v2", "replacement_version_id": "01H..."}
```

**UI:**

- Open `/app/models` for the list and active version.
- Open `/app/models/versions/:id` for detail, set-active, and API links.

---

## 5. Notes

- Active version: `system_configs.key = 'active_model_version_id'`; else latest published.
- Deprecation: `deprecated_at`, `deprecated_reason`, `replacement_version_id` stored; audit events logged.
- Usage stats: use `risk_runs` (or legacy) `model_version_id` and `created_at`; `func.date` for daily grouping.
- Run migrations: `alembic upgrade head`.
