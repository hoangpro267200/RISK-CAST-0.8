# Calibration API Complete ✅

**Date:** January 23, 2026  
**Status:** ✅ Implementation Complete  
**Feature:** REST API Endpoints for Triggering and Monitoring Model Calibration

---

## 🎯 Summary

Successfully implemented REST API endpoints for triggering, monitoring, and managing model calibration runs. This provides a programmatic interface for the calibration pipeline, enabling automated calibration workflows and integration with external systems.

---

## ✅ What Was Implemented

### 1. Calibration API (`app/api/v3/calibration.py`)

**Features:**
- ✅ **POST /runs** - Start calibration run (background processing)
- ✅ **GET /runs** - List calibration runs with filtering
- ✅ **GET /runs/{id}** - Get detailed status of a calibration run
- ✅ **POST /runs/{id}/publish** - Publish calibrated model version
- ✅ **GET /methods** - List available calibration methods
- ✅ **GET /data-summary** - Get data availability summary
- ✅ **Background processing** - Long-running calibrations run asynchronously
- ✅ **RBAC protection** - All endpoints require appropriate permissions

**Key Endpoints:**
- All endpoints require authentication and RBAC permissions
- Background tasks for long-running calibrations
- Comprehensive error handling and validation
- Detailed response models with all calibration metrics

### 2. Request/Response Models

**CalibrationRequest:**
- Date range selection
- Method selection (weight, correlation, loss function)
- Validation thresholds
- Auto-publish option
- Data filters (cargo_type, ports)

**CalibrationRunResponse:**
- Run ID and status
- Current stage
- Dataset size
- Timing information
- Validation status
- Model version ID
- Error/warning counts

**CalibrationRunDetailResponse:**
- Full configuration
- Individual calibration results (weights, correlations, loss function)
- Validation metrics
- Errors, warnings, recommendations

**CalibrationMethodsResponse:**
- Available weight methods
- Available weight objectives
- Available correlation methods
- Available loss function types

---

## 📋 Acceptance Criteria Status

- [x] POST /runs starts calibration
- [x] GET /runs lists runs with status
- [x] GET /runs/{id} shows detailed status
- [x] POST /runs/{id}/publish publishes model
- [x] GET /methods lists available methods
- [x] GET /data-summary shows data availability
- [x] Background processing for long runs

---

## 🚀 Usage Examples

### 1. Get Available Methods

```bash
GET /api/v3/calibration/methods

Response:
{
  "weight_methods": ["ISOTONIC_REGRESSION", "GRADIENT_DESCENT", "DIFFERENTIAL_EVOLUTION", "ENSEMBLE"],
  "weight_objectives": ["MINIMIZE_MSE", "MINIMIZE_MAE", "MAXIMIZE_CORRELATION", "BALANCED"],
  "correlation_methods": ["PEARSON", "SPEARMAN", "KENDALL", "SHRINKAGE"],
  "loss_function_types": ["POWER", "EXPONENTIAL", "LOGISTIC", "PIECEWISE"]
}
```

### 2. Check Data Availability

```bash
GET /api/v3/calibration/data-summary?start_date=2024-01-01&end_date=2025-12-31

Response:
{
  "date_range": {
    "start": "2024-01-01",
    "end": "2025-12-31"
  },
  "total_shipments": 1250,
  "shipments_with_loss": 45,
  "loss_rate": 0.036,
  "completeness_distribution": {
    "high": 800,
    "medium": 350,
    "low": 100
  },
  "recommendations": {
    "sufficient_data": true,
    "sufficient_losses": true,
    "message": "Sufficient data for calibration"
  }
}
```

### 3. Start Calibration Run

```bash
POST /api/v3/calibration/runs
Content-Type: application/json

{
  "start_date": "2024-01-01",
  "end_date": "2025-12-31",
  "min_completeness": 0.7,
  "weight_method": "ENSEMBLE",
  "weight_objective": "BALANCED",
  "correlation_method": "SHRINKAGE",
  "loss_function_type": "POWER",
  "min_improvement_threshold": 0.05,
  "auto_publish": false,
  "model_name": "production_v1",
  "cargo_type": "ELECTRONICS"
}

Response:
{
  "run_id": "abc123def456",
  "status": "PENDING",
  "current_stage": "DATA_LOADING",
  "dataset_size": 0,
  "started_at": "2026-01-23T10:00:00Z",
  "completed_at": null,
  "duration_seconds": null,
  "validation_passed": null,
  "output_model_version_id": null,
  "error_count": 0,
  "warning_count": 0
}
```

### 4. Monitor Calibration Run

```bash
GET /api/v3/calibration/runs/abc123def456

Response (while running):
{
  "run_id": "abc123def456",
  "status": "RUNNING",
  "current_stage": "WEIGHT_CALIBRATION",
  "start_date": "2024-01-01",
  "end_date": "2025-12-31",
  "dataset_size": 1250,
  "dataset_hash": "xyz789",
  "weight_calibration": null,
  "correlation_calibration": null,
  "loss_function_calibration": null,
  "validation_passed": false,
  "validation_metrics": {},
  "output_model_version_id": null,
  "started_at": "2026-01-23T10:00:00Z",
  "completed_at": null,
  "duration_seconds": null,
  "errors": [],
  "warnings": [],
  "recommendations": []
}

Response (completed):
{
  "run_id": "abc123def456",
  "status": "SUCCESS",
  "current_stage": "COMPLETE",
  "start_date": "2024-01-01",
  "end_date": "2025-12-31",
  "dataset_size": 1250,
  "dataset_hash": "xyz789",
  "weight_calibration": {
    "method": "ENSEMBLE",
    "before_mse": 0.045,
    "after_mse": 0.032,
    "improvement_pct": 28.9,
    "overfitting_risk": "LOW",
    "top_layers": [
      {"layer": "weather", "weight": 0.25, "change": 0.05},
      {"layer": "port", "weight": 0.20, "change": -0.02}
    ]
  },
  "correlation_calibration": {
    "method": "SHRINKAGE",
    "is_positive_definite": true,
    "significant_changes": 8,
    "temporal_stability": 0.85,
    "bootstrap_stability": 0.78
  },
  "loss_function_calibration": {
    "function_type": "POWER",
    "formula": "loss = 0.95 * (risk/10)^2.1",
    "before_r2": 0.65,
    "after_r2": 0.78,
    "improvement_pct": 20.0,
    "calibrated_exponent": 2.1
  },
  "validation_passed": true,
  "validation_metrics": {
    "weight_improvement": 0.289,
    "correlation_stability": 0.78,
    "loss_function_r2": 0.78
  },
  "output_model_version_id": "model_xyz789",
  "started_at": "2026-01-23T10:00:00Z",
  "completed_at": "2026-01-23T10:15:30Z",
  "duration_seconds": 930.0,
  "errors": [],
  "warnings": [
    "Dataset has only 1250 shipments. Minimum recommended is 500 for robust calibration."
  ],
  "recommendations": [
    "Calibration successful. New model version (model_xyz789) is ready for testing."
  ]
}
```

### 5. List Calibration Runs

```bash
GET /api/v3/calibration/runs?status=SUCCESS&limit=10

Response:
[
  {
    "run_id": "abc123def456",
    "status": "SUCCESS",
    "current_stage": "COMPLETE",
    "dataset_size": 1250,
    "started_at": "2026-01-23T10:00:00Z",
    "completed_at": "2026-01-23T10:15:30Z",
    "duration_seconds": 930.0,
    "validation_passed": true,
    "output_model_version_id": "model_xyz789",
    "error_count": 0,
    "warning_count": 1
  },
  ...
]
```

### 6. Publish Calibrated Model

```bash
POST /api/v3/calibration/runs/abc123def456/publish

Response:
{
  "status": "published",
  "model_version_id": "model_xyz789",
  "model_name": "production_v1",
  "version": "1.0.0"
}
```

---

## 🔍 API Endpoints

### GET /api/v3/calibration/methods

**Description:** Get available calibration methods.

**Authentication:** Required (RISK_READ permission)

**Response:** `CalibrationMethodsResponse`

**Example:**
```bash
curl -X GET "https://api.riskcast.com/api/v3/calibration/methods" \
  -H "Authorization: Bearer <token>"
```

---

### GET /api/v3/calibration/data-summary

**Description:** Get summary of available calibration data for a date range.

**Authentication:** Required (RISK_READ permission)

**Query Parameters:**
- `start_date` (required) - Start date (YYYY-MM-DD)
- `end_date` (required) - End date (YYYY-MM-DD)

**Response:** Data summary with recommendations

**Example:**
```bash
curl -X GET "https://api.riskcast.com/api/v3/calibration/data-summary?start_date=2024-01-01&end_date=2025-12-31" \
  -H "Authorization: Bearer <token>"
```

---

### POST /api/v3/calibration/runs

**Description:** Start a new calibration run.

**Authentication:** Required (RISK_WRITE permission)

**Request Body:** `CalibrationRequest`

**Response:** `CalibrationRunResponse` (initial state)

**Example:**
```bash
curl -X POST "https://api.riskcast.com/api/v3/calibration/runs" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-01-01",
    "end_date": "2025-12-31",
    "weight_method": "ENSEMBLE",
    "auto_publish": false
  }'
```

**Notes:**
- Calibration runs in background
- Use GET /runs/{id} to monitor progress
- Run ID is returned immediately

---

### GET /api/v3/calibration/runs

**Description:** List calibration runs.

**Authentication:** Required (RISK_READ permission)

**Query Parameters:**
- `status` (optional) - Filter by status (PENDING, RUNNING, SUCCESS, PARTIAL_SUCCESS, FAILED)
- `limit` (optional) - Maximum results (default: 20, max: 100)

**Response:** List of `CalibrationRunResponse`

**Example:**
```bash
curl -X GET "https://api.riskcast.com/api/v3/calibration/runs?status=SUCCESS&limit=10" \
  -H "Authorization: Bearer <token>"
```

---

### GET /api/v3/calibration/runs/{run_id}

**Description:** Get detailed status of a calibration run.

**Authentication:** Required (RISK_READ permission)

**Path Parameters:**
- `run_id` - Calibration run ID

**Response:** `CalibrationRunDetailResponse`

**Example:**
```bash
curl -X GET "https://api.riskcast.com/api/v3/calibration/runs/abc123def456" \
  -H "Authorization: Bearer <token>"
```

**Notes:**
- Returns detailed results when complete
- Shows current stage while running
- Includes all calibration metrics

---

### POST /api/v3/calibration/runs/{run_id}/publish

**Description:** Publish the model version from a calibration run.

**Authentication:** Required (RISK_WRITE permission)

**Path Parameters:**
- `run_id` - Calibration run ID

**Response:** Publication status

**Example:**
```bash
curl -X POST "https://api.riskcast.com/api/v3/calibration/runs/abc123def456/publish" \
  -H "Authorization: Bearer <token>"
```

**Notes:**
- Only works if calibration was successful
- Sets model status to PUBLISHED
- Computes immutable hash
- Creates audit event

---

## 🔐 Security

**Authentication:**
- All endpoints require authentication
- Supports Bearer token (session auth)
- Supports X-API-Key header (API key auth)

**Authorization:**
- GET endpoints require `RISK_READ` permission
- POST endpoints require `RISK_WRITE` permission
- Uses RBAC system for permission checking

**Tenant Isolation:**
- Calibration runs are tenant-scoped
- Users can only access runs for their tenant
- Model versions respect tenant scope

---

## 📊 Background Processing

**Implementation:**
- Uses FastAPI `BackgroundTasks` for async execution
- Calibration runs in background thread
- Status stored in-memory (for now)
- Production should use Redis or database

**Status Tracking:**
- Initial state: `PENDING`
- While running: `RUNNING`
- On completion: `SUCCESS`, `PARTIAL_SUCCESS`, or `FAILED`
- Current stage tracked throughout

**Monitoring:**
- Poll GET /runs/{id} to check progress
- Status updates in real-time
- Errors captured and returned

---

## 🎯 Integration Examples

### Python Client

```python
import requests

BASE_URL = "https://api.riskcast.com/api/v3/calibration"
TOKEN = "your_token_here"

headers = {"Authorization": f"Bearer {TOKEN}"}

# Check data availability
response = requests.get(
    f"{BASE_URL}/data-summary",
    params={"start_date": "2024-01-01", "end_date": "2025-12-31"},
    headers=headers
)
data_summary = response.json()

# Start calibration
response = requests.post(
    f"{BASE_URL}/runs",
    json={
        "start_date": "2024-01-01",
        "end_date": "2025-12-31",
        "weight_method": "ENSEMBLE",
        "auto_publish": False
    },
    headers=headers
)
run = response.json()
run_id = run["run_id"]

# Monitor progress
import time
while True:
    response = requests.get(f"{BASE_URL}/runs/{run_id}", headers=headers)
    status = response.json()
    
    if status["status"] in ["SUCCESS", "PARTIAL_SUCCESS", "FAILED"]:
        break
    
    time.sleep(5)  # Poll every 5 seconds

# Publish if successful
if status["status"] == "SUCCESS":
    response = requests.post(
        f"{BASE_URL}/runs/{run_id}/publish",
        headers=headers
    )
    print(f"Published: {response.json()}")
```

### JavaScript/TypeScript Client

```typescript
const BASE_URL = "https://api.riskcast.com/api/v3/calibration";
const TOKEN = "your_token_here";

const headers = {
  Authorization: `Bearer ${TOKEN}`,
  "Content-Type": "application/json"
};

// Start calibration
const startResponse = await fetch(`${BASE_URL}/runs`, {
  method: "POST",
  headers,
  body: JSON.stringify({
    start_date: "2024-01-01",
    end_date: "2025-12-31",
    weight_method: "ENSEMBLE",
    auto_publish: false
  })
});

const run = await startResponse.json();
const runId = run.run_id;

// Monitor progress
const pollStatus = async () => {
  const response = await fetch(`${BASE_URL}/runs/${runId}`, { headers });
  return await response.json();
};

let status = await pollStatus();
while (!["SUCCESS", "PARTIAL_SUCCESS", "FAILED"].includes(status.status)) {
  await new Promise(resolve => setTimeout(resolve, 5000));
  status = await pollStatus();
}

// Publish if successful
if (status.status === "SUCCESS") {
  const publishResponse = await fetch(
    `${BASE_URL}/runs/${runId}/publish`,
    { method: "POST", headers }
  );
  console.log("Published:", await publishResponse.json());
}
```

---

## 📝 Notes

### In-Memory Storage

**Current Implementation:**
- Calibration runs stored in-memory dictionary
- Lost on server restart
- Not suitable for production

**Production Recommendations:**
- Store runs in database (`CalibrationRun` model exists)
- Use Redis for status tracking
- Persist results for audit trail

### Error Handling

**Validation:**
- Date range validation
- Method enum validation
- Threshold range validation

**Error Responses:**
- 400 Bad Request - Invalid input
- 404 Not Found - Run not found
- 500 Internal Server Error - Calibration failure

### Performance

**Background Processing:**
- Calibrations can take 10-30 minutes
- Background tasks prevent timeout
- Status polling recommended

**Optimization:**
- Consider job queue (Celery, RQ)
- Add progress percentage
- Stream logs if needed

---

## 🎯 Impact on Review Findings

This implementation directly addresses:

1. ✅ **"No programmatic way to trigger calibration"** → REST API endpoints
2. ✅ **"Calibration is manual"** → Automated via API
3. ✅ **"No way to monitor calibration progress"** → Status endpoints
4. ✅ **"No integration with CI/CD"** → API enables automation
5. ✅ **"Calibration results not accessible"** → Detailed response models

---

## 🔄 Next Steps

### Recommended Enhancements

1. **Database Persistence:** Store runs in `CalibrationRun` model
2. **Job Queue:** Use Celery/RQ for better background processing
3. **Progress Updates:** Add progress percentage to status
4. **Webhooks:** Notify on calibration completion
5. **Scheduled Calibrations:** Add cron-like scheduling
6. **Calibration History:** Add filtering and search
7. **Export Results:** Add CSV/JSON export endpoints
8. **Comparison:** Compare multiple calibration runs

---

## 📚 Files Created/Modified

### New Files
- `app/api/v3/calibration.py`

### Modified Files
- `app/api/v3/__init__.py` - Already includes calibration router (line 55-57)

### Dependencies
- Uses `CalibrationPipeline` for orchestration
- Uses `AuditLedger` for audit trail
- Uses RBAC for permissions
- Uses `RiskModelVersion` for model versioning

---

**Status:** ✅ **READY FOR TESTING**

All acceptance criteria met. System now has REST API endpoints for triggering, monitoring, and managing model calibration runs. This provides a programmatic interface for the calibration pipeline, enabling automated workflows and integration with external systems.
