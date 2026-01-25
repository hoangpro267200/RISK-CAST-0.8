# Predictive Analytics Guide

## 📋 Overview

Complete guide to the ML-powered predictive analytics system for loss prediction, claim forecasting, and market trend analysis.

**Features:**
- Loss prediction with confidence intervals
- Claim probability forecasting
- Market trend prediction
- Premium optimization
- Feature engineering
- Model persistence

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────────┐
│                  Input Data Sources                         │
│  • Historical claims & losses                               │
│  • Policy characteristics                                   │
│  • Market rates & trends                                    │
│  • Customer behavior                                        │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ↓
┌────────────────────────────────────────────────────────────┐
│           Feature Engineering Pipeline                      │
│  • Numerical features (cargo value, transit time, etc.)     │
│  • Categorical encoding (cargo type, regions, etc.)         │
│  • Time series features (lags, moving averages, etc.)       │
│  • Derived metrics (risk scores, historical rates)          │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ↓
┌────────────────────────────────────────────────────────────┐
│              ML Models (4 types)                            │
│  ┌───────────────────────────────────────────────┐         │
│  │  1. Loss Prediction (XGBoost/GradientBoost)  │         │
│  │     • Mean prediction                          │         │
│  │     • Lower quantile (10th percentile)        │         │
│  │     • Upper quantile (90th percentile)        │         │
│  └───────────────────────────────────────────────┘         │
│                                                             │
│  ┌───────────────────────────────────────────────┐         │
│  │  2. Claim Probability (Random Forest)         │         │
│  │     • Binary classification                    │         │
│  │     • Calibrated probabilities                 │         │
│  │     • Confidence from tree agreement           │         │
│  └───────────────────────────────────────────────┘         │
│                                                             │
│  ┌───────────────────────────────────────────────┐         │
│  │  3. Market Trend (XGBoost/GradientBoost)     │         │
│  │     • Time series features                     │         │
│  │     • Multi-month forecasting                  │         │
│  │     • Confidence decay over time               │         │
│  └───────────────────────────────────────────────┘         │
│                                                             │
│  ┌───────────────────────────────────────────────┐         │
│  │  4. Premium Optimizer (Ensemble)              │         │
│  │     • Combines loss + claim models             │         │
│  │     • Market adjustment                        │         │
│  │     • Competitive pricing                      │         │
│  └───────────────────────────────────────────────┘         │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ↓
┌────────────────────────────────────────────────────────────┐
│                 Predictions & Insights                      │
│  • Expected loss with confidence intervals                  │
│  • Claim probability with risk assessment                   │
│  • Rate trend forecasts                                     │
│  • Optimized premium recommendations                        │
└────────────────────────────────────────────────────────────┘
```

---

## 🎯 Predictive Models

### 1. Loss Prediction Model

**Purpose:** Predict expected loss percentage for a shipment/policy

**Algorithm:** XGBoost Regressor with quantile regression
- Mean model: Point estimate
- Lower quantile model: 10th percentile (optimistic)
- Upper quantile model: 90th percentile (pessimistic)

**Features (12):**
```python
Numerical (8):
- cargo_value_usd
- container_count
- transit_days
- risk_score (0-1)
- weather_risk (0-1)
- port_congestion_risk (0-1)
- carrier_reliability_score (0-1)
- historical_loss_rate (0-1)

Categorical (4):
- cargo_type (GENERAL, ELECTRONICS, MACHINERY, etc.)
- origin_region (ASIA, EUROPE, AMERICAS, etc.)
- destination_region
- coverage_type (STANDARD, ENHANCED, COMPREHENSIVE)
```

**Output:**
```json
{
    "expected_loss_pct": 0.0235,
    "confidence": 0.87,
    "lower_bound_pct": 0.015,
    "upper_bound_pct": 0.034,
    "risk_level": "MEDIUM",
    "explanation": "Expected loss: 2.35% (MEDIUM risk). Key factors: weather_risk, risk_score, transit_days"
}
```

**Training:**
```bash
python scripts/ml/train_predictive_models.py --model=loss --sample-data --test
```

---

### 2. Claim Probability Model

**Purpose:** Predict likelihood of claim being filed

**Algorithm:** Random Forest Classifier
- 100 trees
- Balanced class weights
- Probability calibration via tree agreement

**Features (8):**
```python
- cargo_value_usd
- container_count
- transit_days
- risk_score
- weather_risk
- carrier_reliability_score
- customer_claim_history (count)
- route_historical_claims (rate)
```

**Output:**
```json
{
    "claim_probability": 0.15,
    "confidence": 0.82,
    "risk_assessment": "MEDIUM - 15% probability of claim",
    "recommended_actions": [
        "Monitor shipment closely",
        "Ensure carrier reliability"
    ]
}
```

**Training:**
```bash
python scripts/ml/train_predictive_models.py --model=claim --sample-data --test
```

---

### 3. Market Trend Predictor

**Purpose:** Forecast insurance rate trends

**Algorithm:** XGBoost Regressor with time series features

**Features (11):**
```python
Time-based:
- month (1-12)
- quarter (1-4)
- year
- day_of_year

Lag features:
- rate_lag_1 (1 month ago)
- rate_lag_3 (3 months ago)
- rate_lag_6 (6 months ago)
- rate_lag_12 (12 months ago)

Rolling statistics:
- rate_ma_3 (3-month moving average)
- rate_ma_12 (12-month moving average)
- rate_std_6 (6-month standard deviation)
```

**Output:**
```json
{
    "predictions": [
        {
            "date": "2026-02-24",
            "month": "2026-02",
            "predicted_rate": 0.0082,
            "change_from_current": 0.025,
            "confidence": 0.90,
            "forecast_horizon_months": 1
        },
        ...
    ],
    "summary": {
        "trend": "INCREASING",
        "avg_future_rate": 0.0085,
        "rate_change_pct": 0.0625
    },
    "insights": [
        "Market rates expected to increase by 6.25% over 6 months",
        "Peak rates anticipated in Q2 2026"
    ]
}
```

**Training:**
```bash
python scripts/ml/train_predictive_models.py --model=market --sample-data --test
```

---

### 4. Premium Optimizer

**Purpose:** Calculate optimal premium pricing

**Algorithm:** Ensemble approach combining loss and claim models

**Pricing Formula:**
```
1. Expected Loss = Loss_Prediction × Cargo_Value × Claim_Probability

2. Actuarial Premium = Expected_Loss / Target_Loss_Ratio (0.65)

3. Gross Premium = Actuarial_Premium / (1 - Expense_Ratio - Profit_Margin)
                 = Actuarial_Premium / (1 - 0.25 - 0.10)
                 = Actuarial_Premium / 0.65

4. Actuarial Rate = (Gross_Premium / Cargo_Value) × 1000  (per mille)

5. Market Adjusted = Actuarial_Rate × 0.7 + Market_Rate × 0.3

6. Competitive Adjusted = Market_Adjusted × 0.6 + Competitive_Rate × 0.4

7. Final Rate = max(Min_Rate, min(Competitive_Adjusted, Max_Rate))
   where:
   - Min_Rate = Actuarial_Rate × 0.8
   - Max_Rate = Market_Rate × 1.5
```

**Output:**
```json
{
    "recommended_premium": 850,
    "recommended_rate": 0.85,
    "actuarial_rate": 0.88,
    "market_rate": 0.85,
    "confidence": 0.85,
    "rate_components": {
        "risk_based": 0.88,
        "market_adjusted": 0.87,
        "competitive_adjusted": 0.85,
        "final": 0.85
    },
    "pricing_factors": {
        "target_loss_ratio": 0.65,
        "expense_ratio": 0.25,
        "profit_margin": 0.10
    }
}
```

---

## 🚀 Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements-ml.txt

# Verify XGBoost
python -c "import xgboost; print('XGBoost version:', xgboost.__version__)"
```

### Training All Models

```bash
# Train all models with synthetic data
python scripts/ml/train_predictive_models.py --sample-data --test

# Output:
# ============================================================
# Training Loss Prediction Model
# ============================================================
# Generated loss data: 1000 samples
# Loss prediction model trained
#   val_mae=0.0043
#   cv_mae=0.0045
# ✓ Loss prediction model trained and saved
#
# ============================================================
# Training Claim Probability Model
# ============================================================
# Generated claim data: 1000 samples
# Claim probability model trained
#   val_auc=0.8234
#   cv_auc=0.8156
# ✓ Claim probability model trained and saved
#
# ============================================================
# Training Market Trend Predictor
# ============================================================
# Generated market data: 36 months
# Market rate trend model trained
# ✓ Market trend predictor trained and saved
#
# ============================================================
# Testing Predictive Models
# ============================================================
# 1. Testing Loss Prediction:
#   Expected Loss: 2.35%
#   Confidence: 0.87
#   Range: [1.5%, 3.4%]
#
# 2. Testing Claim Probability:
#   Claim Probability: 15.0%
#   Confidence: 0.82
#
# 3. Testing Market Trend Prediction:
#   Predictions for next 6 months:
#     2026-02: 0.0082 (+2.5%) confidence: 0.90
#     2026-03: 0.0084 (+5.0%) confidence: 0.85
#     ...
#
# ============================================================
# ✓ Training Complete!
# ============================================================
# Models saved to: models/predictive/
```

---

## 💻 API Usage

### 1. Predict Loss

```bash
curl -X POST http://localhost:8000/api/v3/predict/loss \
  -H "Content-Type: application/json" \
  -d '{
    "cargo_value_usd": 100000,
    "container_count": 2,
    "transit_days": 21,
    "risk_score": 0.65,
    "weather_risk": 0.6,
    "port_congestion_risk": 0.3,
    "carrier_reliability_score": 0.85,
    "historical_loss_rate": 0.02,
    "cargo_type": "ELECTRONICS",
    "origin_region": "ASIA",
    "destination_region": "EUROPE"
}'
```

**Response:**
```json
{
    "expected_loss_pct": 0.0235,
    "expected_loss_amount": 2350,
    "confidence": 0.87,
    "lower_bound_pct": 0.015,
    "upper_bound_pct": 0.034,
    "risk_level": "MEDIUM",
    "explanation": "Expected loss: 2.35% (MEDIUM risk). Key factors: weather_risk, risk_score, transit_days",
    "feature_importance": {
        "weather_risk": 0.25,
        "risk_score": 0.20,
        "transit_days": 0.15,
        ...
    }
}
```

### 2. Predict Claim Probability

```bash
curl -X POST http://localhost:8000/api/v3/predict/claim-probability \
  -H "Content-Type: application/json" \
  -d '{
    "cargo_value_usd": 100000,
    "container_count": 2,
    "transit_days": 21,
    "risk_score": 0.65,
    "weather_risk": 0.6,
    "carrier_reliability_score": 0.85,
    "customer_claim_history": 1,
    "route_historical_claims": 0.08
}'
```

### 3. Predict Market Trend

```bash
curl -X POST http://localhost:8000/api/v3/predict/market-trend \
  -H "Content-Type: application/json" \
  -d '{
    "months_ahead": 6
}'
```

### 4. Optimize Premium

```bash
curl -X POST http://localhost:8000/api/v3/optimize/premium \
  -H "Content-Type: application/json" \
  -d '{
    "policy_data": {
        "cargo_value_usd": 100000,
        "container_count": 2,
        "transit_days": 21,
        "risk_score": 0.65,
        ...
    },
    "market_rate": 0.85,
    "competitive_rate": 0.82
}'
```

---

## 🧪 Testing & Validation

### Cross-Validation

All models use 5-fold cross-validation during training:

**Loss Prediction:**
- Metric: Mean Absolute Error (MAE)
- Target: < 0.005 (0.5% error)
- Typical: 0.0043 - 0.0048

**Claim Probability:**
- Metric: ROC-AUC
- Target: > 0.75
- Typical: 0.80 - 0.85

**Market Trend:**
- Metric: MAE on holdout set
- Target: < 0.0005 (0.05% error)
- Typical: 0.0003 - 0.0006

### Confidence Intervals

**Loss Prediction:**
- 80% confidence interval (10th-90th percentile)
- Narrower interval = higher confidence
- Confidence score: 1 - (interval_width × 10)

**Claim Probability:**
- Confidence from tree agreement
- High agreement = high confidence
- Confidence score: 1 - std_dev(tree_predictions)

**Market Trend:**
- Confidence decays with forecast horizon
- Month 1: 0.90 confidence
- Month 6: 0.65 confidence
- Formula: 0.9 - (month × 0.05)

---

## 📊 Performance Benchmarks

### Training Speed

| Model | Samples | Features | Time |
|-------|---------|----------|------|
| Loss Prediction | 1000 | 12 | ~5s |
| Claim Probability | 1000 | 8 | ~3s |
| Market Trend | 36 months | 11 | ~2s |

### Prediction Speed

| Model | Latency (single) | Throughput (batch 100) |
|-------|------------------|------------------------|
| Loss Prediction | <10ms | <100ms |
| Claim Probability | <5ms | <50ms |
| Market Trend | <5ms | <20ms |
| Premium Optimization | <15ms | <150ms |

### Model Size

| Model | Disk Size |
|-------|-----------|
| Loss Prediction (XGBoost) | ~2MB |
| Claim Probability (RF) | ~5MB |
| Market Trend (XGBoost) | ~1MB |
| **Total** | **~8MB** |

---

## 🔧 Configuration & Tuning

### Loss Prediction Hyperparameters

```python
# XGBoost configuration
{
    "objective": "reg:squarederror",  # or "reg:quantileerror"
    "n_estimators": 100,              # Number of trees
    "max_depth": 6,                   # Tree depth
    "learning_rate": 0.1,             # Step size
    "quantile_alpha": 0.1 / 0.9       # For quantile models
}
```

**Tuning Guidelines:**
- Increase `n_estimators` (100→200) for better accuracy
- Decrease `max_depth` (6→4) to prevent overfitting
- Adjust `learning_rate` (0.1→0.05) for smoother convergence

### Claim Probability Hyperparameters

```python
# Random Forest configuration
{
    "n_estimators": 100,              # Number of trees
    "max_depth": 10,                  # Tree depth
    "class_weight": "balanced",       # Handle imbalanced data
    "random_state": 42
}
```

**Tuning Guidelines:**
- Increase `n_estimators` for stability
- Adjust `max_depth` based on feature complexity
- Use `class_weight='balanced'` for imbalanced datasets

### Premium Optimizer Parameters

```python
{
    "target_loss_ratio": 0.65,  # 65% of premium for losses
    "expense_ratio": 0.25,       # 25% for expenses
    "profit_margin": 0.10        # 10% profit
}
```

**Adjustment:**
- Increase `target_loss_ratio` (0.65→0.70) for conservative pricing
- Decrease `profit_margin` (0.10→0.05) for competitive pricing

---

## 🐛 Troubleshooting

### XGBoost Not Available

**Problem:** `XGBOOST_AVAILABLE = False`

**Solution:**
```bash
# Install XGBoost
pip install xgboost

# Or system will fallback to GradientBoostingRegressor (slower but functional)
```

### Poor Prediction Accuracy

**Problem:** High MAE or low AUC

**Solutions:**
1. Increase training data (1000→5000+ samples)
2. Add more relevant features
3. Tune hyperparameters
4. Check for data quality issues

### Model Not Trained Error

**Problem:** `Model not trained. Call train() first.`

**Solution:**
```bash
# Train models
python scripts/ml/train_predictive_models.py --sample-data

# Or via API
curl -X POST http://localhost:8000/api/v3/predictive/train
```

---

## 📚 Best Practices

### Data Quality

✅ **DO:**
- Use recent historical data (<2 years old)
- Ensure sufficient samples (1000+ for training)
- Handle missing values appropriately
- Normalize/scale features
- Encode categorical variables

❌ **DON'T:**
- Mix different time periods without context
- Include outliers without investigation
- Use sparse features (mostly zeros)

### Model Deployment

✅ **DO:**
- Version control models
- Log all predictions
- Monitor model drift
- Retrain periodically (quarterly)
- A/B test new models

❌ **DON'T:**
- Deploy without validation
- Ignore prediction confidence
- Skip model monitoring
- Use stale models (>1 year old)

### Premium Optimization

✅ **DO:**
- Consider market conditions
- Factor in competition
- Apply reasonable bounds
- Provide explanations
- Review regularly

❌ **DON'T:**
- Price below cost
- Ignore market trends
- Over-optimize for profit
- Apply one-size-fits-all pricing

---

## 🔄 Model Retraining

### When to Retrain

- **Quarterly:** Routine retraining
- **Data drift:** When accuracy drops
- **Market changes:** Major rate shifts
- **New patterns:** Emerging risk factors

### Retraining Process

```bash
# 1. Collect new data
# 2. Validate data quality
# 3. Retrain models
python scripts/ml/train_predictive_models.py --all

# 4. Validate on holdout set
python scripts/ml/train_predictive_models.py --test

# 5. Compare with current models
# 6. Deploy if improved
# 7. Monitor performance
```

---

## 📈 Production Deployment

### Checklist

- [ ] Models trained on production data
- [ ] Cross-validation scores acceptable
- [ ] Prediction latency < 100ms
- [ ] Model artifacts backed up
- [ ] Monitoring configured
- [ ] Alerting rules set up
- [ ] Documentation updated
- [ ] Stakeholders informed

### Monitoring Metrics

```python
# Track in production
- Prediction volume
- Prediction latency
- Feature distribution changes
- Prediction accuracy (when actuals available)
- Model version in use
- Error rates
```

---

**Last Updated:** January 24, 2026  
**Version:** 1.0.0  
**Owner:** ML Engineering Team
