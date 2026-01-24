# Calibration Models Complete ✅

**Date:** January 23, 2026  
**Status:** ✅ Implementation Complete  
**Feature:** Database Models for Persisting Calibration Results

---

## 🎯 Summary

Successfully implemented comprehensive database models for persisting calibration results. This provides a complete audit trail, enables reproducibility, and supports model lineage tracking.

---

## ✅ What Was Implemented

### 1. Enhanced CalibrationRun Model

**Enhanced Fields:**
- ✅ `current_stage` - Current pipeline stage
- ✅ `dataset_start_date` / `dataset_end_date` - Date range
- ✅ `dataset_size` / `dataset_hash` - Dataset metadata
- ✅ `weight_calibration_json` - Full weight calibration results
- ✅ `weight_method` / `weight_before_mse` / `weight_after_mse` / `weight_improvement_pct`
- ✅ `correlation_calibration_json` - Full correlation results
- ✅ `correlation_method` / `correlation_stability`
- ✅ `loss_function_calibration_json` - Full loss function results
- ✅ `loss_function_type` / `loss_function_before_r2` / `loss_function_after_r2`
- ✅ `validation_passed` / `validation_metrics_json`
- ✅ `duration_seconds` - Execution time
- ✅ `errors_json` / `warnings` / `recommendations`
- ✅ `calibration_hash` - Hash for reproducibility

**Relationships:**
- `calibrated_weights` - One-to-many with CalibratedWeight
- `calibrated_correlations` - One-to-many with CalibratedCorrelation
- `calibrated_loss_function` - One-to-one with CalibratedLossFunction

### 2. CalibratedWeight Model

**Purpose:** Stores individual layer weights for easy querying and comparison.

**Fields:**
- `calibration_run_id` - Foreign key to calibration run
- `layer_name` - Risk layer name
- `original_weight` / `calibrated_weight` - Before/after weights
- `weight_change` - Change amount
- `confidence_interval_lower` / `confidence_interval_upper` - CI bounds
- `importance_rank` - Rank by importance
- `statistical_significance` - p-value
- `sample_size` - Sample size used

**Indexes:**
- `idx_calibrated_weights_run` - By calibration run
- `idx_calibrated_weights_layer` - By layer name

### 3. CalibratedCorrelation Model

**Purpose:** Stores correlation pairs between risk layers.

**Fields:**
- `calibration_run_id` - Foreign key to calibration run
- `layer_1` / `layer_2` - Layer pair
- `original_correlation` / `calibrated_correlation` - Before/after
- `correlation_change` - Change amount
- `p_value` - Statistical significance
- `is_significant` - Boolean flag
- `sample_size` - Sample size used

**Indexes:**
- `idx_calibrated_corr_run` - By calibration run
- `idx_calibrated_corr_layers` - Composite on layer_1, layer_2
- Individual indexes on layer_1 and layer_2

### 4. CalibratedLossFunction Model

**Purpose:** Stores calibrated loss function parameters.

**Fields:**
- `calibration_run_id` - Foreign key (unique, one per run)
- `function_type` - POWER, EXPONENTIAL, LOGISTIC, PIECEWISE
- `parameters_json` - Calibrated parameters
- `original_parameters_json` - Original parameters
- `formula` - Human-readable formula
- `before_mse` / `before_mae` / `before_r2` - Baseline metrics
- `after_mse` / `after_mae` / `after_r2` - Calibrated metrics
- `mse_improvement_pct` / `r2_improvement_pct` - Improvements
- `residual_analysis_json` - Residual analysis results
- `risk_level_analysis_json` - Performance by risk level

**Constraints:**
- Unique constraint on `calibration_run_id` (one loss function per run)

### 5. CalibrationComparison Model

**Purpose:** Compares two calibration runs to track changes over time.

**Fields:**
- `baseline_run_id` / `comparison_run_id` - Run references
- `weight_changes_json` - Detailed weight changes
- `max_weight_change` / `avg_weight_change` - Summary stats
- `correlation_changes_json` - Detailed correlation changes
- `max_correlation_change` / `avg_correlation_change` - Summary stats
- `loss_function_changes_json` - Loss function changes
- `overall_change_magnitude` - Overall change score
- `change_significance` - LOW, MEDIUM, HIGH
- `recommendation` - Text recommendation

**Indexes:**
- `idx_comparison_baseline` - By baseline run
- `idx_comparison_comparison` - By comparison run

### 6. Migration (037_enhance_calibration_detailed.py)

**Creates:**
- Enhanced `calibration_runs` table with new fields
- `calibrated_weights` table
- `calibrated_correlations` table
- `calibrated_loss_functions` table
- `calibration_comparisons` table

**Indexes:**
- All necessary indexes for efficient querying
- Foreign key constraints with CASCADE deletes

---

## 📋 Acceptance Criteria Status

- [x] CalibrationRun model stores full run details
- [x] CalibratedWeights stores layer weights
- [x] CalibratedCorrelations stores correlation pairs
- [x] CalibratedLossFunction stores loss function params
- [x] CalibrationComparison enables run comparison
- [x] Proper indexes for queries
- [x] Migration creates tables

---

## 🚀 Usage Examples

### 1. Save Calibration Run

```python
from app.models.calibration import CalibrationRun, CalibratedWeight, CalibratedCorrelation, CalibratedLossFunction
from app.shared.utils import generate_ulid
from datetime import datetime

# Create calibration run
run = CalibrationRun(
    id=generate_ulid(),
    tenant_id=tenant_id,
    dataset_id=dataset_id,
    input_model_version_id=input_model_id,
    status="SUCCESS",
    current_stage="COMPLETE",
    dataset_start_date=date(2024, 1, 1),
    dataset_end_date=date(2025, 12, 31),
    dataset_size=1250,
    dataset_hash="abc123",
    weight_method="ENSEMBLE",
    weight_before_mse=0.045,
    weight_after_mse=0.032,
    weight_improvement_pct=28.9,
    correlation_method="SHRINKAGE",
    correlation_stability=0.78,
    loss_function_type="POWER",
    loss_function_before_r2=0.65,
    loss_function_after_r2=0.78,
    validation_passed=True,
    started_at=datetime.utcnow(),
    completed_at=datetime.utcnow(),
    duration_seconds=930.0
)

db.add(run)
db.commit()

# Save calibrated weights
for layer_name, weight_data in weight_result.layer_weights.items():
    weight = CalibratedWeight(
        id=generate_ulid(),
        calibration_run_id=run.id,
        layer_name=layer_name,
        original_weight=weight_data.original_weight,
        calibrated_weight=weight_data.calibrated_weight,
        weight_change=weight_data.weight_change,
        confidence_interval_lower=weight_data.confidence_interval[0],
        confidence_interval_upper=weight_data.confidence_interval[1],
        importance_rank=weight_data.importance_rank,
        statistical_significance=weight_data.statistical_significance,
        sample_size=weight_data.sample_size
    )
    db.add(weight)

# Save calibrated correlations
for pair, corr_data in correlation_result.pairs.items():
    corr = CalibratedCorrelation(
        id=generate_ulid(),
        calibration_run_id=run.id,
        layer_1=pair[0],
        layer_2=pair[1],
        original_correlation=corr_data.original_correlation,
        calibrated_correlation=corr_data.calibrated_correlation,
        correlation_change=corr_data.correlation_change,
        p_value=corr_data.p_value,
        is_significant=corr_data.is_significant,
        sample_size=corr_data.sample_size
    )
    db.add(corr)

# Save loss function
loss_func = CalibratedLossFunction(
    id=generate_ulid(),
    calibration_run_id=run.id,
    function_type=loss_result.function_type.value,
    parameters_json=loss_result.params.parameters,
    original_parameters_json=loss_result.params.original_parameters,
    formula=loss_result.function_formula,
    before_mse=loss_result.before_mse,
    before_mae=loss_result.before_mae,
    before_r2=loss_result.before_r2,
    after_mse=loss_result.after_mse,
    after_mae=loss_result.after_mae,
    after_r2=loss_result.after_r2,
    mse_improvement_pct=loss_result.mse_improvement_pct,
    r2_improvement_pct=loss_result.r2_improvement_pct,
    residual_analysis_json=loss_result.residual_normality_test,
    risk_level_analysis_json=loss_result.performance_by_risk_level
)
db.add(loss_func)

db.commit()
```

### 2. Query Calibration Runs

```python
# Get all successful runs
runs = db.query(CalibrationRun).filter(
    CalibrationRun.status == "SUCCESS",
    CalibrationRun.tenant_id == tenant_id
).order_by(CalibrationRun.completed_at.desc()).all()

# Get run with details
run = db.query(CalibrationRun).filter(
    CalibrationRun.id == run_id
).first()

# Access related data
weights = run.calibrated_weights.all()
correlations = run.calibrated_correlations.all()
loss_function = run.calibrated_loss_function
```

### 3. Compare Calibration Runs

```python
from app.models.calibration import CalibrationComparison

baseline_run = db.query(CalibrationRun).filter(
    CalibrationRun.id == baseline_id
).first()

comparison_run = db.query(CalibrationRun).filter(
    CalibrationRun.id == comparison_id
).first()

# Calculate differences
weight_changes = {}
for weight in comparison_run.calibrated_weights:
    baseline_weight = baseline_run.calibrated_weights.filter(
        CalibratedWeight.layer_name == weight.layer_name
    ).first()
    if baseline_weight:
        weight_changes[weight.layer_name] = {
            "before": baseline_weight.calibrated_weight,
            "after": weight.calibrated_weight,
            "change": weight.calibrated_weight - baseline_weight.calibrated_weight
        }

# Create comparison
comparison = CalibrationComparison(
    id=generate_ulid(),
    baseline_run_id=baseline_run.id,
    comparison_run_id=comparison_run.id,
    weight_changes_json=weight_changes,
    max_weight_change=max(abs(c["change"]) for c in weight_changes.values()),
    avg_weight_change=sum(abs(c["change"]) for c in weight_changes.values()) / len(weight_changes),
    change_significance="HIGH" if max_weight_change > 0.1 else "MEDIUM",
    recommendation="Significant changes detected. Review before deploying."
)

db.add(comparison)
db.commit()
```

### 4. Query by Layer

```python
# Get all weights for a specific layer across runs
weights = db.query(CalibratedWeight).filter(
    CalibratedWeight.layer_name == "weather",
    CalibratedWeight.calibration_run_id.in_(
        db.query(CalibrationRun.id).filter(
            CalibrationRun.status == "SUCCESS"
        )
    )
).order_by(CalibratedWeight.created_at.desc()).all()

# Track weight evolution
for weight in weights:
    print(f"{weight.created_at}: {weight.calibrated_weight}")
```

---

## 🔍 Model Relationships

```
CalibrationRun (1) ──< (N) CalibratedWeight
CalibrationRun (1) ──< (N) CalibratedCorrelation
CalibrationRun (1) ──< (1) CalibratedLossFunction
CalibrationRun (1) ──< (N) CalibrationComparison (baseline)
CalibrationRun (1) ──< (N) CalibrationComparison (comparison)
```

---

## 📊 Indexes

**CalibrationRun:**
- `idx_cal_runs_tenant` - Tenant filtering
- `idx_cal_runs_status` - Status filtering
- `idx_cal_runs_dataset` - Dataset lookup
- `idx_cal_runs_input_model` - Input model lookup
- `idx_cal_runs_output_model` - Output model lookup
- `idx_calibration_run_started` - Time-based queries

**CalibratedWeight:**
- `idx_calibrated_weights_run` - By calibration run
- `idx_calibrated_weights_layer` - By layer name

**CalibratedCorrelation:**
- `idx_calibrated_corr_run` - By calibration run
- `idx_calibrated_corr_layers` - Composite on layer_1, layer_2
- `idx_calibrated_corr_layer1` - By layer_1
- `idx_calibrated_corr_layer2` - By layer_2

**CalibratedLossFunction:**
- `idx_calibrated_loss_run` - By calibration run
- Unique constraint on `calibration_run_id`

**CalibrationComparison:**
- `idx_comparison_baseline` - By baseline run
- `idx_comparison_comparison` - By comparison run

---

## 🎯 Impact on Review Findings

This implementation directly addresses:

1. ✅ **"No audit trail for calibrations"** → Complete run history stored
2. ✅ **"Cannot reproduce calibrations"** → Full configuration and results stored
3. ✅ **"No way to track model lineage"** → Links to input/output model versions
4. ✅ **"Cannot compare calibrations"** → CalibrationComparison model
5. ✅ **"No historical analysis"** → Detailed models enable time-series analysis

---

## 📝 Notes

### Data Consistency

**Cascade Deletes:**
- Deleting a `CalibrationRun` cascades to:
  - All `CalibratedWeight` records
  - All `CalibratedCorrelation` records
  - The `CalibratedLossFunction` record
  - All `CalibrationComparison` records referencing it

**Foreign Keys:**
- All foreign keys have proper constraints
- `ondelete='CASCADE'` for child records
- `ondelete='RESTRICT'` for model versions (prevent accidental deletion)

### Performance

**Indexes:**
- All foreign keys indexed
- Common query patterns indexed
- Composite indexes for multi-column queries

**Query Optimization:**
- Use `lazy='dynamic'` for large collections
- Use `lazy='select'` for single relationships
- Consider eager loading for specific queries

### Migration

**Upgrade:**
- Adds new columns to existing `calibration_runs` table
- Creates new tables for detailed results
- Adds indexes and constraints

**Downgrade:**
- Removes new tables
- Removes new columns
- Reverts status column length

---

## 🔄 Integration with Pipeline

The calibration pipeline should save results to these models:

```python
# In calibration_pipeline.py _package_model method
# After creating model version, save detailed results

# Save weights
for layer_name, layer_weight in result.weight_result.layer_weights.items():
    calibrated_weight = CalibratedWeight(
        id=generate_ulid(),
        calibration_run_id=result.run_id,
        layer_name=layer_name,
        # ... other fields
    )
    db.add(calibrated_weight)

# Save correlations
for pair, corr_pair in result.correlation_result.pairs.items():
    calibrated_corr = CalibratedCorrelation(
        id=generate_ulid(),
        calibration_run_id=result.run_id,
        layer_1=pair[0],
        layer_2=pair[1],
        # ... other fields
    )
    db.add(calibrated_corr)

# Save loss function
calibrated_loss = CalibratedLossFunction(
    id=generate_ulid(),
    calibration_run_id=result.run_id,
    # ... fields from result.loss_function_result
)
db.add(calibrated_loss)

db.commit()
```

---

## 📚 Files Created/Modified

### Modified Files
- `app/models/calibration.py` - Enhanced CalibrationRun, added new models

### New Files
- `migrations/versions/037_enhance_calibration_detailed.py` - Migration for new tables

### Dependencies
- Uses `app.database.Base` for base class
- Uses `String(26)` for ULID IDs
- Uses MySQL JSON columns
- Uses `generate_ulid()` for ID generation

---

**Status:** ✅ **READY FOR TESTING**

All acceptance criteria met. System now has comprehensive database models for persisting calibration results, providing complete audit trail, reproducibility, and model lineage tracking.
