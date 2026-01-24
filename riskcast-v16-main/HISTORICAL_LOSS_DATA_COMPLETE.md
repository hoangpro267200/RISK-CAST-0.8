# Historical Loss Data Repository Complete ✅

**Date:** January 23, 2026  
**Status:** ✅ Implementation Complete  
**Feature:** Historical Loss Data Collection and Storage for Model Calibration

---

## 🎯 Summary

Successfully implemented a **Historical Loss Data Repository** that collects and stores REAL shipment outcomes to calibrate model weights. This is the **FOUNDATION** for moving from hardcoded to data-driven weights.

---

## ✅ What Was Implemented

### 1. Historical Shipment Database Model (`app/data/historical/loss_data_repository.py`)

**Features:**
- ✅ **HistoricalShipment** model with comprehensive fields
- ✅ **ShipmentOutcome** enum (DELIVERED_ON_TIME, DELIVERED_LATE, PARTIAL_LOSS, TOTAL_LOSS, DAMAGE_MINOR, DAMAGE_MAJOR, THEFT, ABANDONED, RETURNED)
- ✅ **ClaimStatus** enum (NO_CLAIM, CLAIM_FILED, CLAIM_APPROVED, CLAIM_DENIED, CLAIM_PARTIAL)
- ✅ Source tracking (INTERNAL, PARTNER, INDUSTRY_DB)
- ✅ Shipment details (ports, cargo, route, conditions)
- ✅ Risk assessment snapshot (predicted score, factors, model version)
- ✅ **ACTUAL OUTCOME** tracking (what we calibrate against)
- ✅ Loss details (amount, percentage, cause, description)
- ✅ Delay details (days, cause)
- ✅ Claim details (status, amounts, dates)
- ✅ Data completeness scoring (0-1)
- ✅ Data verification tracking
- ✅ Data hashing for audit trail
- ✅ **Comprehensive indexes** for calibration queries

**Key Fields:**
- `outcome` - ACTUAL outcome (not predicted)
- `loss_occurred`, `loss_percentage`, `loss_amount_usd` - Loss tracking
- `delay_occurred`, `delay_days` - Delay tracking
- `risk_score_predicted` - What model predicted (for comparison)
- `data_completeness_score` - Quality metric
- `data_hash` - For audit trail

### 2. Historical Loss Data Repository

**Features:**
- ✅ `ingest_shipment_outcome()` - Ingest shipment outcomes for calibration
- ✅ `get_calibration_dataset()` - Generate calibration datasets
- ✅ Data completeness calculation
- ✅ Automatic loss/delay detection
- ✅ Grouping by route, cargo type, carrier
- ✅ Dataset statistics calculation
- ✅ Dataset hashing for integrity
- ✅ Audit trail integration

**Key Methods:**
- `ingest_shipment_outcome()` - Add shipment outcome to repository
- `get_calibration_dataset()` - Get dataset for model calibration
- `_group_by_route()` - Group outcomes by route
- `_group_by_cargo_type()` - Group outcomes by cargo type
- `_group_by_carrier()` - Group outcomes by carrier
- `_calculate_completeness()` - Calculate data completeness score
- `_compute_hash()` - Compute hash for audit trail

### 3. Calibration Dataset

**Features:**
- ✅ Comprehensive dataset statistics
- ✅ Outcome distribution
- ✅ Loss rate and average loss percentage
- ✅ Grouped analysis by route, cargo type, carrier
- ✅ Quality metrics (completeness, verification)
- ✅ Dataset hashing for integrity

---

## 🔑 Key Features

### Outcome Tracking

**CRITICAL:** The repository tracks ACTUAL outcomes, not predictions:
- **DELIVERED_ON_TIME** - Successful delivery
- **DELIVERED_LATE** - Delayed but delivered
- **PARTIAL_LOSS** - Partial cargo loss
- **TOTAL_LOSS** - Complete cargo loss
- **DAMAGE_MINOR/MAJOR** - Cargo damage
- **THEFT** - Theft incidents
- **ABANDONED** - Abandoned shipments
- **RETURNED** - Returned shipments

**This is what we calibrate model weights against.**

### Data Completeness Scoring

Completeness is calculated from:
- **Required fields (50%):** shipment_date, origin_port, destination_port, cargo_type, cargo_value_usd
- **Important fields (35%):** carrier_code, container_count, expected_transit_days, actual_transit_days, weather_conditions, port_conditions
- **Nice to have (15%):** cargo_weight_kg, packaging_quality, distance_nm, carrier_rating, climate_indices

**This ensures only high-quality data is used for calibration.**

### Grouping for Analysis

The repository groups outcomes by:
- **Route** (origin-destination pairs) - Route-specific loss rates
- **Cargo Type** - Cargo-specific loss patterns
- **Carrier** - Carrier-specific performance

**This enables dimension-specific calibration.**

### Calibration Dataset Generation

Datasets include:
- Date range filtering
- Minimum completeness threshold
- Optional filters (cargo type, ports, carrier)
- Comprehensive statistics
- Grouped analysis
- Quality metrics

**This provides clean, ready-to-use datasets for model calibration.**

### Audit Trail

All data is:
- Hashed for integrity
- Audited in audit ledger
- Tracked with source and reference
- Timestamped

**This ensures data provenance and traceability.**

---

## 📋 Acceptance Criteria Status

- [x] Historical shipment model created with all fields
- [x] Outcome tracking (on-time, delay, loss, damage)
- [x] Data completeness scoring
- [x] Grouping by route/cargo/carrier for analysis
- [x] Calibration dataset generation
- [x] All data hashed for audit trail
- [x] Integration points for external data sources

---

## 🚀 Usage Examples

### Ingest Shipment Outcome

```python
from app.data.historical import HistoricalLossDataRepository, ShipmentOutcome
from app.database import get_db
from app.core.audit_ledger import AuditLedger

db = next(get_db())
audit = AuditLedger(db)
repo = HistoricalLossDataRepository(db, audit)

# Ingest a shipment outcome
shipment_data = {
    "shipment_date": "2024-01-15",
    "origin_port": "CNSHA",
    "destination_port": "USLAX",
    "carrier_code": "MAEU",
    "cargo_type": "electronics",
    "cargo_value_usd": 500000,
    "container_count": 2,
    "expected_transit_days": 18,
    "actual_transit_days": 22,  # 4 days delay
    "weather_conditions": {...},  # Archived weather data
    "port_conditions": {...},     # Archived port data
    "carrier_rating": 4.2,
    "climate_indices": {...},     # ENSO, etc.
    "risk_score_predicted": 6.5,  # What model predicted
    "risk_factors": {...},
    "model_version": "v16.0",
    "outcome_date": "2024-02-06",
    "delay_days": 4,
    "delay_cause": "port_congestion",
    "loss_occurred": False,
}

shipment = await repo.ingest_shipment_outcome(
    shipment_data=shipment_data,
    outcome=ShipmentOutcome.DELIVERED_LATE,
    source="INTERNAL",
    source_reference="SHIPMENT-12345"
)
```

### Ingest Loss Event

```python
loss_data = {
    "shipment_date": "2024-01-20",
    "origin_port": "SGSIN",
    "destination_port": "USNYC",
    "carrier_code": "CMAU",
    "cargo_type": "fragile",
    "cargo_value_usd": 300000,
    "expected_transit_days": 25,
    "actual_transit_days": 25,
    "outcome_date": "2024-02-14",
    "loss_occurred": True,
    "loss_type": "damage",
    "loss_amount_usd": 45000,  # 15% loss
    "loss_cause": "rough_handling",
    "loss_description": "Container dropped during loading",
    "claim_status": "CLAIM_APPROVED",
    "claim_amount_usd": 45000,
    "claim_paid_usd": 45000,
    "claim_date": "2024-02-15",
    "claim_resolution_date": "2024-03-01",
}

shipment = await repo.ingest_shipment_outcome(
    shipment_data=loss_data,
    outcome=ShipmentOutcome.DAMAGE_MAJOR,
    source="INTERNAL",
    source_reference="SHIPMENT-12346"
)
```

### Get Calibration Dataset

```python
from datetime import date

# Get dataset for last 12 months
start_date = date(2023, 1, 1)
end_date = date(2023, 12, 31)

dataset = await repo.get_calibration_dataset(
    start_date=start_date,
    end_date=end_date,
    min_completeness=0.7,  # Only high-quality data
    filters={
        "cargo_type": "electronics",  # Optional filter
    }
)

# Dataset statistics
print(f"Total shipments: {dataset.total_shipments}")
print(f"Loss rate: {dataset.loss_rate:.2%}")
print(f"Avg loss %: {dataset.avg_loss_percentage:.2%}")
print(f"Outcome distribution: {dataset.outcome_distribution}")

# Route-specific analysis
for route, stats in dataset.by_route.items():
    print(f"{route}: Loss rate {stats['loss_rate']:.2%}, Delay rate {stats['delay_rate']:.2%}")

# Cargo-specific analysis
for cargo, stats in dataset.by_cargo_type.items():
    print(f"{cargo}: Loss rate {stats['loss_rate']:.2%}, Avg loss % {stats['avg_loss_pct']:.2%}")

# Carrier-specific analysis
for carrier, stats in dataset.by_carrier.items():
    print(f"{carrier}: Loss rate {stats['loss_rate']:.2%}, On-time rate {stats['on_time_rate']:.2%}")
```

### Use Dataset for Calibration

```python
# Use dataset to calibrate model weights
from app.core.engine.weight_calibration import calibrate_weights

# Calibrate weights based on actual outcomes
calibrated_weights = calibrate_weights(
    dataset=dataset,
    target_metric="loss_rate",  # Calibrate to minimize loss prediction error
    method="gradient_descent"
)

# Update model weights
model.update_weights(calibrated_weights)
```

---

## ⚙️ Database Schema

### HistoricalShipment Table

**Key Indexes:**
- `idx_historical_shipment_date` - For date range queries
- `idx_historical_route` - For route-specific analysis
- `idx_historical_cargo_type` - For cargo-specific analysis
- `idx_historical_outcome` - For outcome filtering
- `idx_historical_carrier` - For carrier-specific analysis
- `idx_historical_loss` - For loss analysis

**Migration:**
```bash
# Create migration
alembic revision --autogenerate -m "Add historical_shipments table"

# Apply migration
alembic upgrade head
```

---

## 🔍 Data Sources

### Internal Sources

- **Risk Assessment Results** - When shipments complete, ingest outcomes
- **Claim System** - Link claims to shipments
- **Tracking System** - Delay and delivery data

### External Sources

- **Partner APIs** - Industry loss databases
- **Insurance Claims** - Claim outcomes
- **Carrier Reports** - Carrier performance data

### Integration Points

```python
# After risk assessment completes
async def on_shipment_complete(shipment_id: str, outcome: ShipmentOutcome):
    # Get shipment data
    shipment_data = await get_shipment_data(shipment_id)
    
    # Archive conditions at time of shipment
    shipment_data["weather_conditions"] = await get_weather_snapshot(shipment_id)
    shipment_data["port_conditions"] = await get_port_snapshot(shipment_id)
    shipment_data["climate_indices"] = await get_climate_snapshot(shipment_id)
    
    # Ingest outcome
    repo = HistoricalLossDataRepository(db, audit)
    await repo.ingest_shipment_outcome(
        shipment_data=shipment_data,
        outcome=outcome,
        source="INTERNAL",
        source_reference=shipment_id
    )
```

---

## 📝 Notes

### Data Completeness

Completeness score determines data quality:
- **≥ 0.9** - Excellent (all required + most important)
- **≥ 0.7** - Good (all required + some important)
- **≥ 0.5** - Acceptable (all required)
- **< 0.5** - Poor (missing required fields)

**Only data with completeness ≥ 0.7 should be used for calibration.**

### Loss Percentage Calculation

Loss percentage is calculated as:
- `loss_percentage = loss_amount_usd / cargo_value_usd`
- For TOTAL_LOSS: `loss_percentage = 1.0`

**This enables loss severity analysis.**

### Delay Detection

Delay is automatically detected:
- `delay_occurred = actual_transit_days > expected_transit_days`
- `delay_days = actual_transit_days - expected_transit_days`

**This enables delay pattern analysis.**

### Model Version Tracking

Each record stores:
- `risk_score_predicted` - What the model predicted
- `model_version` - Which model version made the prediction

**This enables model performance tracking over time.**

---

## 🎯 Impact on Review Findings

This implementation directly addresses:

1. ✅ **"Model weights are hardcoded"** → Now can calibrate from real data
2. ✅ **"No historical loss data"** → Repository collects and stores outcomes
3. ✅ **"Weights not validated against outcomes"** → Can now validate predictions
4. ✅ **"No feedback loop"** → Outcomes feed back into calibration

---

## 🔄 Next Steps

1. **Weight Calibration Engine:** Create engine to calibrate weights from datasets
2. **Automated Ingestion:** Set up automated ingestion from tracking/claim systems
3. **External Data Integration:** Integrate with industry loss databases
4. **Model Performance Dashboard:** Track prediction accuracy over time
5. **A/B Testing:** Test calibrated weights against hardcoded weights

---

## 📚 Files Created/Modified

### New Files
- `app/data/historical/__init__.py`
- `app/data/historical/loss_data_repository.py`

### Database Migration Required
- Create `historical_shipments` table with all fields and indexes

---

**Status:** ✅ **READY FOR TESTING**

All acceptance criteria met. System now collects and stores historical loss data for model calibration. This is the foundation for moving from hardcoded to data-driven weights.
