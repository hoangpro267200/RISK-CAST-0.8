## 📋 Overview

Complete guide to the ML-powered fraud detection and anomaly detection system.

**Features:**
- Isolation Forest for outlier detection
- Autoencoder for complex pattern learning
- Feature engineering pipeline
- Ensemble approach for robust detection
- Model training and persistence
- Explainable AI with contributing factors

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Input Data                                │
│  (Claims, Policies, Customer Behavior)                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│              Feature Engineering                             │
│  - Claim-to-coverage ratio                                   │
│  - Temporal features (time since inception, reporting delay) │
│  - Customer history (previous claims)                        │
│  - Loss type encoding                                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌──────────────────────────────────────────────────────────────┐
│             Ensemble ML Models                                │
│  ┌────────────────────┐    ┌──────────────────────┐         │
│  │ Isolation Forest   │    │   Autoencoder        │         │
│  │ (Outlier Detection)│    │ (Pattern Learning)   │         │
│  └────────┬───────────┘    └──────────┬───────────┘         │
│           │                            │                      │
│           └──────────┬─────────────────┘                     │
│                      ↓                                        │
│              Ensemble Aggregation                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│           Fraud Detection Result                             │
│  - Is Anomaly: Yes/No                                        │
│  - Fraud Score: 0-1                                          │
│  - Risk Level: LOW/MEDIUM/HIGH/CRITICAL                      │
│  - Explanation with contributing factors                     │
│  - Recommended actions                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Detection Methods

### 1. Isolation Forest

**How it works:**
- Builds ensemble of random decision trees
- Anomalies are isolated faster (fewer splits needed)
- Efficient for high-dimensional data
- No assumptions about data distribution

**Advantages:**
- Fast training and prediction
- Works well with limited labeled data
- Handles high-dimensional features
- Minimal hyperparameter tuning

**Best for:**
- Outlier detection
- Unusual value combinations
- Statistical anomalies

### 2. Autoencoder

**How it works:**
- Neural network learns to compress and reconstruct normal patterns
- High reconstruction error indicates anomaly
- Learns complex non-linear relationships

**Architecture:**
```
Input (6 features)
    ↓
Dense(32) + ReLU + Dropout(0.2)
    ↓
Dense(16) + ReLU
    ↓
Encoded(8) ← Compressed representation
    ↓
Dense(16) + ReLU
    ↓
Dense(32) + ReLU + Dropout(0.2)
    ↓
Output (6 features)

Loss: Mean Squared Error (MSE)
```

**Advantages:**
- Learns complex patterns
- Detects subtle anomalies
- No feature engineering required
- Adapts to data distribution

**Best for:**
- Complex fraud patterns
- Non-linear relationships
- Behavioral anomalies

### 3. Ensemble Approach

**Combination Strategy:**
```python
combined_score = (isolation_forest_score + autoencoder_score) / 2
is_anomaly = isolation_forest_anomaly OR autoencoder_anomaly
```

**Benefits:**
- Reduces false positives
- Increases detection coverage
- Balances different detection strategies
- More robust than single model

---

## 📊 Features Extracted

### Claim Features

| Feature | Description | Range | Fraud Indicator |
|---------|-------------|-------|-----------------|
| **claim_coverage_ratio** | Claimed amount / Coverage limit | 0.0 - 1.0+ | High ratio (>0.8) suspicious |
| **days_since_inception** | Days from policy start to loss | 0 - 365+ | Very short (<7) suspicious |
| **days_to_report** | Days from loss to claim filing | 0 - 90+ | Long delay (>14) suspicious |
| **loss_type** | Type of loss (encoded) | 0 - 6 | Certain types more common |
| **premium_paid** | Premium amount | $0 - $10k+ | Low premium, high claim suspicious |
| **previous_claims** | Customer's prior claim count | 0 - 10+ | Many claims (>3) suspicious |

### Quote Features

| Feature | Description | Fraud Relevance |
|---------|-------------|-----------------|
| Cargo value | Total shipment value | Outlier values |
| Premium | Insurance premium | Rate anomalies |
| Rate per mille | Premium / Value * 1000 | Unusual pricing |
| Risk score | Assessed risk | Score manipulation |
| Container count | Number of containers | Volume anomalies |
| Transit time | Expected transit days | Timeline issues |
| Hour/Day of week | Temporal patterns | Off-hours activity |

### Customer Behavior Features

| Feature | Description | Fraud Signal |
|---------|-------------|--------------|
| Transaction frequency | Quotes per month | Sudden spikes |
| Average value | Mean cargo value | Value changes |
| Value std dev | Value variance | Inconsistency |
| Time between transactions | Average days | Pattern shifts |
| Route diversity | Unique routes | Limited diversity |
| Cargo diversity | Cargo types | Single type focus |
| Acceptance rate | Accepted / Total quotes | Very high/low |
| Claim ratio | Claims / Policies | High frequency |

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install ML dependencies
pip install -r requirements-ml.txt

# Or install individually
pip install numpy pandas scikit-learn tensorflow joblib
```

### 2. Train Models

#### Using API

```bash
curl -X POST http://localhost:8000/api/v3/fraud/train \
  -H "Content-Type: application/json" \
  -d '{"force_retrain": false}'
```

#### Using Training Script

```bash
# Train on synthetic data
python scripts/ml/train_fraud_detection.py --sample-data --test

# Train on database data
python scripts/ml/train_fraud_detection.py
```

### 3. Detect Fraud

```python
from app.ml.anomaly_detection import fraud_service

# Detect fraud in a claim
result = await fraud_service.detect_fraud(
    claim={
        'claimed_amount': 95000,
        'loss_date': '2026-01-20',
        'filed_at': '2026-01-21T10:00:00Z',
        'loss_type': 'CARGO_LOSS',
        'customer_previous_claims': 2
    },
    policy={
        'coverage_limit': 100000,
        'cargo_value_usd': 100000,
        'effective_from': '2026-01-19',
        'total_premium_usd': 850
    }
)

print(f"Is Fraud: {result.is_anomaly}")
print(f"Fraud Score: {result.anomaly_score:.2f}")
print(f"Explanation: {result.explanation}")
```

---

## 🔍 Using the API

### Check Model Status

```bash
curl http://localhost:8000/api/v3/fraud/status
```

**Response:**
```json
{
    "is_trained": true,
    "use_autoencoder": true,
    "models_available": ["isolation_forest", "autoencoder"],
    "statistics": {
        "isolation_forest_features": 6,
        "feature_names": [
            "claim_coverage_ratio",
            "days_since_inception",
            "days_to_report",
            "loss_type",
            "premium_paid",
            "previous_claims"
        ],
        "autoencoder_encoding_dim": 8,
        "autoencoder_threshold": 0.0234
    }
}
```

### Detect Fraud

```bash
curl -X POST http://localhost:8000/api/v3/fraud/detect \
  -H "Content-Type: application/json" \
  -d '{
    "claim_id": "CLM-123",
    "claim": {
        "claimed_amount": 95000,
        "loss_date": "2026-01-20",
        "filed_at": "2026-01-21T10:00:00Z",
        "loss_type": "CARGO_LOSS",
        "customer_previous_claims": 2
    },
    "policy": {
        "coverage_limit": 100000,
        "cargo_value_usd": 100000,
        "effective_from": "2026-01-19",
        "total_premium_usd": 850
    }
}'
```

**Response:**
```json
{
    "claim_id": "CLM-123",
    "is_fraud_suspect": true,
    "fraud_score": 0.87,
    "anomaly_type": "fraud_suspect",
    "confidence": 0.92,
    "risk_level": "HIGH",
    "explanation": "Fraud risk: HIGH. Claim amount is 95% of coverage (very high); Claim filed shortly after policy inception",
    "contributing_factors": [
        "claim_coverage_ratio",
        "days_since_inception",
        "previous_claims"
    ],
    "recommended_actions": [
        "Manual review required",
        "Request additional documentation",
        "Verify loss details with third parties",
        "Check customer claim history",
        "Verify actual cargo value and loss extent"
    ],
    "metadata": {
        "isolation_forest_score": 0.89,
        "autoencoder_score": 0.85,
        "ensemble": true
    },
    "assessed_at": "2026-01-24T22:30:00Z"
}
```

---

## 📈 Risk Levels

| Level | Score Range | Description | Action Required |
|-------|-------------|-------------|-----------------|
| **LOW** | 0.0 - 0.3 | Normal claim patterns | Standard processing |
| **MEDIUM** | 0.3 - 0.5 | Some unusual indicators | Enhanced review |
| **HIGH** | 0.5 - 0.8 | Multiple fraud indicators | Manual investigation |
| **CRITICAL** | 0.8 - 1.0 | Strong fraud suspicion | Immediate investigation |

---

## 🎓 Model Training

### Training Requirements

**Minimum Data:**
- At least 100 historical claims
- Mix of normal and suspicious cases
- Recent data (within 2 years)

**Recommended:**
- 500+ claims for robust training
- Diverse claim types and amounts
- Balanced distribution

### Training Process

```python
from app.ml.anomaly_detection import fraud_service

# Load historical data
claims_data = [
    {
        'claim': {...},
        'policy': {...}
    },
    # ... more claims
]

# Train models
await fraud_service.train_models(claims_data)

# Save models
fraud_service.save_models()
```

### Model Persistence

**Directory Structure:**
```
models/fraud/
├── isolation_forest.pkl      # Isolation Forest model
├── autoencoder/
│   ├── autoencoder.h5        # Keras model
│   └── metadata.pkl          # Scaler and threshold
└── metadata.json             # Training metadata
```

**Loading Models:**
```python
# Automatic loading on first use
fraud_service.load_models()
```

---

## 🔧 Configuration

### Isolation Forest Parameters

```python
detector = IsolationForestDetector(
    contamination=0.05,   # Expected outlier rate (5%)
    n_estimators=100      # Number of trees
)
```

**Tuning:**
- `contamination`: Increase if too many false negatives, decrease if too many false positives
- `n_estimators`: More trees = more stable but slower

### Autoencoder Parameters

```python
detector = AutoencoderAnomalyDetector(
    encoding_dim=8,           # Compressed dimension
    threshold_percentile=95   # Anomaly threshold (95th percentile)
)
```

**Tuning:**
- `encoding_dim`: Lower = more compression, higher sensitivity
- `threshold_percentile`: Higher = fewer false positives, may miss some anomalies

---

## 📊 Interpreting Results

### Contributing Factors

**claim_coverage_ratio:**
```
High ratio (>0.8): Suspicious
- Claiming almost full coverage
- May indicate inflated claim
- Example: $95k claimed on $100k policy
```

**days_since_inception:**
```
Short period (<7 days): Suspicious
- Claim filed shortly after buying policy
- Possible pre-existing damage
- Example: Loss 2 days after policy start
```

**days_to_report:**
```
Long delay (>14 days): Suspicious
- Unreasonable reporting delay
- May indicate fabricated claim
- Example: Loss on Jan 5, reported Jan 20
```

**previous_claims:**
```
Many claims (>3): Suspicious
- High claim frequency
- Pattern of claiming
- Example: 5 claims in 2 years
```

---

## 🚨 Common Fraud Patterns Detected

### Pattern 1: Quick Claim

**Indicators:**
- Policy purchased 1-5 days before loss
- High claim-to-coverage ratio
- First-time customer

**Score:** Typically 0.7-0.9

**Example:**
```json
{
    "effective_from": "2026-01-19",
    "loss_date": "2026-01-20",
    "claimed_amount": 90000,
    "coverage_limit": 100000
}
```

### Pattern 2: Serial Claimer

**Indicators:**
- 3+ previous claims
- Claims on multiple policies
- Pattern of high claim ratios

**Score:** Typically 0.6-0.8

**Example:**
```json
{
    "customer_previous_claims": 5,
    "claimed_amount": 60000,
    "average_claim": 55000
}
```

### Pattern 3: Delayed Reporting

**Indicators:**
- 14+ days to report loss
- Vague loss circumstances
- High claim amount

**Score:** Typically 0.5-0.7

**Example:**
```json
{
    "loss_date": "2026-01-05",
    "filed_at": "2026-01-25",
    "days_to_report": 20
}
```

### Pattern 4: Unusual Loss Type

**Indicators:**
- Rare loss type for route/cargo
- Loss type difficult to verify
- Suspicious timing

**Score:** Varies (0.4-0.8)

---

## 🧪 Testing & Validation

### Unit Tests

```python
import pytest
from app.ml.anomaly_detection import FeatureEngineering

def test_feature_extraction():
    claim = {
        'claimed_amount': 50000,
        'loss_date': '2026-01-15',
        'filed_at': '2026-01-16T10:00:00Z',
        'loss_type': 'CARGO_DAMAGE',
        'customer_previous_claims': 1
    }
    
    policy = {
        'coverage_limit': 100000,
        'effective_from': '2025-12-01',
        'total_premium_usd': 850
    }
    
    features = FeatureEngineering.extract_claim_features(claim, policy)
    
    assert len(features) == 6
    assert 0 <= features[0] <= 1  # claim_coverage_ratio
    assert features[1] > 0  # days_since_inception
```

### Integration Tests

```bash
# Run training script with test mode
python scripts/ml/train_fraud_detection.py --sample-data --test
```

### Performance Metrics

**Evaluation Metrics:**
- Precision: True frauds / Total flagged
- Recall: Detected frauds / Total frauds
- F1-Score: Harmonic mean of precision and recall
- False Positive Rate: Normal claims flagged as fraud

**Target Metrics:**
```
Precision: >0.70 (minimize false positives)
Recall: >0.80 (catch most frauds)
F1-Score: >0.75
False Positive Rate: <0.10
```

---

## 🔐 Production Deployment

### 1. Pre-Deployment Checklist

- [ ] Models trained on production data
- [ ] Performance metrics validated
- [ ] False positive rate acceptable
- [ ] Model artifacts backed up
- [ ] Monitoring configured
- [ ] Alerting rules set up

### 2. Model Versioning

```bash
models/fraud/
├── v1.0/
│   ├── isolation_forest.pkl
│   └── autoencoder/
├── v1.1/
│   ├── isolation_forest.pkl
│   └── autoencoder/
└── current -> v1.1/
```

### 3. Monitoring

**Key Metrics to Track:**
- Prediction latency
- Fraud detection rate
- False positive rate (user feedback)
- Model drift indicators
- Feature distribution changes

**Prometheus Metrics:**
```python
fraud_detections_total = Counter('fraud_detections_total', 'Total fraud detections')
fraud_score_histogram = Histogram('fraud_score', 'Fraud score distribution')
prediction_latency = Histogram('fraud_prediction_latency_seconds', 'Prediction latency')
```

### 4. Retraining Schedule

**Recommended:**
- Weekly: If high volume (>100 claims/week)
- Monthly: Medium volume (20-100 claims/week)
- Quarterly: Low volume (<20 claims/week)

**Trigger Retraining:**
- Model performance degradation
- Significant data distribution changes
- New fraud patterns identified
- After major system changes

---

## 🐛 Troubleshooting

### Model Not Trained

**Problem:** `Model not trained` error

**Solution:**
```bash
# Train models
python scripts/ml/train_fraud_detection.py --sample-data

# Or via API
curl -X POST http://localhost:8000/api/v3/fraud/train
```

### TensorFlow Not Available

**Problem:** Autoencoder not working

**Solution:**
```bash
# Install TensorFlow
pip install tensorflow

# Or use CPU-only version
pip install tensorflow-cpu

# System will fall back to Isolation Forest only if TensorFlow unavailable
```

### High False Positive Rate

**Problem:** Too many normal claims flagged

**Solutions:**
1. Increase contamination parameter (0.05 → 0.10)
2. Increase threshold percentile (95 → 97)
3. Retrain with more diverse data
4. Adjust risk level thresholds

### Low Detection Rate

**Problem:** Missing fraudulent claims

**Solutions:**
1. Decrease contamination parameter (0.05 → 0.03)
2. Decrease threshold percentile (95 → 90)
3. Add more training examples of fraud
4. Review feature engineering

---

## 📚 References

### Academic Papers

1. **Isolation Forest:**
   - Liu, F. T., Ting, K. M., & Zhou, Z. H. (2008). "Isolation Forest"
   - IEEE International Conference on Data Mining

2. **Autoencoder Anomaly Detection:**
   - Sakurada, M., & Yairi, T. (2014). "Anomaly Detection Using Autoencoders"
   - International Journal of Prognostics and Health Management

### Code Examples

- [Scikit-learn Isolation Forest](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html)
- [Keras Autoencoders](https://blog.keras.io/building-autoencoders-in-keras.html)
- [Fraud Detection Patterns](https://github.com/Fraud-Detection-Handbook)

---

## 🎯 Best Practices

### Feature Engineering

✅ **DO:**
- Normalize features before training
- Handle missing values appropriately
- Create domain-specific features
- Test feature importance
- Document feature definitions

❌ **DON'T:**
- Use raw categorical values without encoding
- Include redundant features
- Ignore data quality issues
- Forget to scale features

### Model Training

✅ **DO:**
- Use representative training data
- Validate on holdout set
- Monitor training metrics
- Save model artifacts
- Version control models

❌ **DON'T:**
- Overtrain on small datasets
- Ignore class imbalance
- Skip validation
- Lose model versions

### Production Usage

✅ **DO:**
- Log all predictions
- Track false positives
- Monitor model drift
- Provide explanations
- Enable human review

❌ **DON'T:**
- Auto-reject without review
- Ignore user feedback
- Skip model updates
- Forget to monitor

---

**Last Updated:** January 24, 2026  
**Version:** 1.0.0  
**Owner:** ML Engineering Team
