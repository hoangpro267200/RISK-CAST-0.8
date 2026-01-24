# Correlation Matrix Calibration Complete ✅

**Date:** January 23, 2026  
**Status:** ✅ Implementation Complete  
**Feature:** Framework for Calibrating Correlation Matrix from Historical Loss Data

---

## 🎯 Summary

Successfully implemented a **Correlation Matrix Calibration Framework** that calibrates the correlation matrix between risk layers using historical data. This replaces hardcoded correlation values with empirically-derived values.

---

## ✅ What Was Implemented

### 1. Correlation Calibrator (`app/calibration/correlation_calibrator.py`)

**Features:**
- ✅ **Multiple correlation methods** (Pearson, Spearman, Kendall, Shrinkage)
- ✅ **Positive definiteness ensured** (required for Cholesky decomposition)
- ✅ **Bootstrap confidence intervals** for each correlation pair
- ✅ **Temporal stability** calculation (how stable over time)
- ✅ **Bootstrap stability** calculation (how stable across samples)
- ✅ **Comparison with original** hardcoded values
- ✅ **Pair-level statistics** with p-values
- ✅ **Warnings for anomalies** (high correlations, large changes, etc.)
- ✅ **Export to dictionary format** for risk engine use
- ✅ **Audit trail** for all calibrations

**Key Classes:**
- `CorrelationCalibrator` - Main calibration class
- `CorrelationMethod` - Enum for correlation methods
- `CorrelationPair` - Correlation between two layers with statistics
- `CorrelationMatrixResult` - Complete calibration result

### 2. Correlation Methods

**Pearson Correlation:**
- Linear correlation
- Standard method
- Fast computation

**Spearman Rank Correlation:**
- Rank-based correlation
- Robust to outliers
- Non-parametric

**Kendall's Tau:**
- Rank correlation
- Alternative to Spearman
- Good for small samples

**Ledoit-Wolf Shrinkage (RECOMMENDED):**
- Shrinks towards identity matrix
- More stable for small samples
- Guarantees positive definiteness
- Reduces estimation error

### 3. Statistical Analysis

**Bootstrap Confidence Intervals:**
- 1000 bootstrap samples
- 95% confidence intervals
- Quantifies uncertainty

**Statistical Significance:**
- p-values via Spearman correlation
- Identifies significant correlations
- Flags insignificant pairs

**Stability Metrics:**
- **Temporal stability:** Split data by time, compare matrices
- **Bootstrap stability:** Coefficient of variation across samples

### 4. Matrix Properties

**Positive Definiteness:**
- Required for Cholesky decomposition
- Used in Monte Carlo simulations
- Automatically adjusted if needed

**Condition Number:**
- Measures matrix stability
- Lower is better
- High condition number = unstable

---

## 📋 Acceptance Criteria Status

- [x] Multiple correlation methods (Pearson, Spearman, Shrinkage)
- [x] Positive definiteness ensured
- [x] Bootstrap confidence intervals
- [x] Temporal stability calculated
- [x] Comparison with original values
- [x] Pair-level statistics
- [x] Warnings for anomalies
- [x] Export to dictionary format for risk engine

---

## 🚀 Usage Examples

### Basic Calibration

```python
from app.calibration import CorrelationCalibrator, CorrelationMethod
from app.data.historical.loss_data_repository import HistoricalLossDataRepository
from app.core.audit_ledger.ledger import AuditLedger
from app.database import get_db

db = next(get_db())
audit = AuditLedger(db)
repository = HistoricalLossDataRepository(db, audit)

# Get calibration dataset
dataset = await repository.get_calibration_dataset(
    start_date=date(2024, 1, 1),
    end_date=date(2025, 12, 31)
)

# Create calibrator
calibrator = CorrelationCalibrator(audit)

# Calibrate correlation matrix
result = await calibrator.calibrate(
    dataset=dataset,
    method=CorrelationMethod.SHRINKAGE  # Recommended
)

# Check results
print(f"Positive definite: {result.is_positive_definite}")
print(f"Condition number: {result.condition_number:.2f}")
print(f"Temporal stability: {result.temporal_stability:.2f}")
print(f"Bootstrap stability: {result.bootstrap_stability:.2f}")

# View pair statistics
for pair in result.pair_statistics[:5]:  # Top 5
    print(f"{pair.layer_1} <-> {pair.layer_2}:")
    print(f"  Original: {pair.original_correlation:.3f}")
    print(f"  Calibrated: {pair.calibrated_correlation:.3f}")
    print(f"  Change: {pair.correlation_change:+.3f}")
    print(f"  CI: [{pair.confidence_interval[0]:.3f}, {pair.confidence_interval[1]:.3f}]")
    print(f"  Significant: {pair.is_significant}")
```

### Using Different Methods

```python
# Pearson (linear correlation)
result = await calibrator.calibrate(
    dataset=dataset,
    method=CorrelationMethod.PEARSON
)

# Spearman (rank correlation, robust)
result = await calibrator.calibrate(
    dataset=dataset,
    method=CorrelationMethod.SPEARMAN
)

# Shrinkage (recommended, most stable)
result = await calibrator.calibrate(
    dataset=dataset,
    method=CorrelationMethod.SHRINKAGE
)
```

### Applying to Risk Engine

```python
# Get correlation dictionary
corr_dict = calibrator.get_correlation_matrix_dict(result)

# Use in risk engine
from app.core.engine.risk_engine_v16 import RiskConfig

# Update correlation matrix
RiskConfig.CORRELATION_MATRIX = corr_dict
```

---

## 🔍 Calibration Process

### 1. Data Extraction

**Extracts from CalibrationDataset:**
- Risk factor scores for each layer
- Normalizes to 0-1 scale
- Creates feature matrix

**Requirements:**
- Minimum 50 shipments
- Risk factors available

### 2. Correlation Calculation

**Selected method:**
- Computes correlation matrix
- Handles missing values
- Ensures symmetry

### 3. Positive Definiteness

**Ensures matrix is PD:**
- Tries Cholesky decomposition
- Adjusts eigenvalues if needed
- Rescales to maintain correlations

### 4. Statistical Analysis

**Bootstrap analysis:**
- 1000 bootstrap samples
- Confidence intervals
- Stability metrics

### 5. Comparison

**Compares with original:**
- Calculates differences
- Identifies large changes
- Flags significant changes

### 6. Warnings

**Generates warnings for:**
- Non-positive-definite matrices
- Low temporal stability
- Very high correlations
- Large changes from original

---

## 📊 Correlation Matrix Properties

### Positive Definiteness

**Why it matters:**
- Required for Cholesky decomposition
- Used in Monte Carlo simulations
- Ensures valid covariance structure

**How it's ensured:**
- Eigenvalue adjustment
- Rescaling to maintain correlations
- Warning if adjustment needed

### Condition Number

**Measures:**
- Matrix stability
- Numerical precision
- Sensitivity to errors

**Interpretation:**
- < 10: Excellent
- 10-100: Good
- > 100: Poor (may cause issues)

### Stability Metrics

**Temporal Stability:**
- Split data by time
- Compare correlation matrices
- Higher = more stable over time

**Bootstrap Stability:**
- Coefficient of variation
- Across bootstrap samples
- Higher = more stable

---

## 📝 Notes

### Data Requirements

**Minimum requirements:**
- 50+ shipments for basic calibration
- 100+ shipments for reliable calibration
- 200+ shipments for stable calibration

**More data = better calibration:**
- More stable estimates
- Better confidence intervals
- More reliable temporal stability

### Method Selection

**Recommendations:**
- **Shrinkage (Ledoit-Wolf):** Best for small samples, most stable
- **Spearman:** Best for non-linear relationships, robust
- **Pearson:** Fast, good for large samples
- **Kendall:** Alternative rank correlation

**Default:** Shrinkage (most robust)

### Positive Definiteness

**When adjustment is needed:**
- Small sample size
- High correlations
- Missing data
- Numerical errors

**Adjustment method:**
- Eigenvalue correction
- Preserves correlation structure
- Warning generated

### High Correlations

**Warning triggers:**
- Correlation > 0.8
- May indicate redundant layers
- Review layer definitions

**Action:**
- Check if layers are truly independent
- Consider combining layers
- Review domain knowledge

---

## 🎯 Impact on Review Findings

This implementation directly addresses:

1. ✅ **"Hardcoded correlations not validated"** → Correlations now calibrated from data
2. ✅ **"Correlations may not reflect reality"** → Correlations reflect actual patterns
3. ✅ **"No way to improve correlations"** → Framework enables continuous improvement
4. ✅ **"Correlations are arbitrary"** → Correlations are statistically validated
5. ✅ **"Wrong correlations lead to wrong VaR"** → Accurate correlations improve VaR/CVaR

---

## 🔄 Integration with Risk Engine

### Apply Calibrated Matrix

```python
# After calibration
from app.core.engine.risk_engine_v16 import RiskConfig

# Get correlation dictionary
corr_dict = calibrator.get_correlation_matrix_dict(result)

# Update risk engine
RiskConfig.CORRELATION_MATRIX = corr_dict
```

### Periodic Re-calibration

```python
# Re-calibrate quarterly with new data
async def quarterly_correlation_calibration():
    dataset = await repository.get_calibration_dataset(
        start_date=date(2024, 1, 1),
        end_date=date.today()
    )
    
    result = await calibrator.calibrate(dataset)
    
    # Check stability
    if result.temporal_stability > 0.8:
        apply_calibrated_matrix(result)
    else:
        logger.warning("Low temporal stability, review correlations")
```

---

## 📚 Files Created/Modified

### New Files
- `app/calibration/correlation_calibrator.py`

### Modified Files
- `app/calibration/__init__.py` - Added correlation calibrator exports

### Dependencies
- Uses `CalibrationDataset` from historical loss repository
- Uses `AuditLedger` for audit trail
- Uses scipy, sklearn, numpy for correlation calculations

---

**Status:** ✅ **READY FOR TESTING**

All acceptance criteria met. System now has a framework for calibrating correlation matrices from historical loss data. This replaces hardcoded correlation values with empirically-validated, data-driven values, improving the accuracy of portfolio risk aggregation and VaR/CVaR calculations.
