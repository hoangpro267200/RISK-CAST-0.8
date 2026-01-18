# SPRINT 2 TEST DATA MOCKS
## Sample Engine Output for Testing

**Date:** 2026-01-16  
**Purpose:** Provide mock data for testing Sprint 2 components

---

## 📦 MOCK 1: Electronics Shipment (High Risk, Full Data)

### Use Case
Test Insurance Panel + Logistics Panel with complete data

### Engine Output
```json
{
  "shipment": {
    "id": "SH-001",
    "route": "VN_US",
    "pol_code": "VNSGN",
    "pod_code": "USLAX",
    "carrier": "Ocean Carrier",
    "etd": "2026-01-20",
    "eta": "2026-02-23",
    "transit_time": 34,
    "container": "40DV",
    "cargo": "Electronics",
    "cargo_type": "Electronics",
    "container_type": "40DV",
    "cargo_value": 500000
  },
  "risk_score": 65,
  "risk_level": "HIGH",
  "confidence": 0.85,
  "layers": [
    { "id": "1", "name": "Climate Risk", "score": 72, "contribution": 28, "weight": 28 },
    { "id": "2", "name": "Port Congestion", "score": 65, "contribution": 18, "weight": 18 },
    { "id": "3", "name": "Cargo Sensitivity", "score": 58, "contribution": 15, "weight": 15 }
  ],
  "loss": {
    "expectedLoss": 12000,
    "p95": 45000,
    "p99": 78000,
    "lossCurve": [
      { "loss": 5000, "probability": 0.1 },
      { "loss": 12000, "probability": 0.3 },
      { "loss": 25000, "probability": 0.2 },
      { "loss": 45000, "probability": 0.1 },
      { "loss": 78000, "probability": 0.05 }
    ]
  },
  "insurance": {
    "lossDistribution": {
      "histogram": [
        { "bucket": "$0-$5K", "frequency": 0.35, "cumulative": 0.35 },
        { "bucket": "$5K-$10K", "frequency": 0.25, "cumulative": 0.60 },
        { "bucket": "$10K-$20K", "frequency": 0.20, "cumulative": 0.80 },
        { "bucket": "$20K-$50K", "frequency": 0.15, "cumulative": 0.95 },
        { "bucket": "$50K+", "frequency": 0.05, "cumulative": 1.00 }
      ],
      "isSynthetic": false,
      "dataPoints": 1000
    },
    "basisRisk": {
      "score": 0.12,
      "interpretation": "low",
      "explanation": "Parametric triggers are reliable for this shipment. Delay-based parametric insurance is suitable."
    },
    "triggerProbabilities": [
      {
        "trigger": "delay > 7 days",
        "probability": 0.22,
        "expectedPayout": 15000
      },
      {
        "trigger": "delay > 14 days",
        "probability": 0.08,
        "expectedPayout": 35000
      },
      {
        "trigger": "Storm encounter (Cat 2+)",
        "probability": 0.12,
        "expectedPayout": 25000
      }
    ],
    "coverageRecommendations": [
      {
        "type": "ICC(A)",
        "clause": "All Risks Marine Cargo Insurance",
        "rationale": "Electronics cargo with high value requires broadest coverage",
        "priority": "required"
      },
      {
        "type": "Delay Rider (Parametric)",
        "clause": "Trigger: Delay > 7 days from scheduled ETA",
        "rationale": "Winter Pacific crossing has elevated delay risk",
        "priority": "recommended"
      },
      {
        "type": "Moisture Damage Clause",
        "clause": "Covers condensation, humidity damage to electronics",
        "rationale": "34-day transit creates temperature cycling → condensation",
        "priority": "recommended"
      }
    ],
    "premiumLogic": {
      "expectedLoss": 12000,
      "loadFactor": 1.25,
      "calculatedPremium": 16200,
      "marketRate": 0.80,
      "riskcastRate": 0.65,
      "explanation": "Premium calculated from expected loss of $12K with 1.25x load factor. Risk adjustment (score 65): +8%"
    },
    "riders": [
      {
        "name": "Delay Rider",
        "cost": 1500,
        "benefit": "Covers delays > 7 days (22% trigger probability)"
      },
      {
        "name": "Moisture Damage Waiver",
        "cost": 500,
        "benefit": "Waives moisture exclusion for electronics"
      }
    ],
    "exclusions": [
      {
        "clause": "Pre-existing Damage",
        "reason": "Damage existing before cargo loaded onto vessel"
      },
      {
        "clause": "Improper Packaging",
        "reason": "Loss due to inadequate packing by shipper"
      }
    ],
    "deductibleRecommendation": {
      "amount": 5000,
      "rationale": "With a 22% annual claim probability and $12,000 expected loss, a $5,000 deductible balances premium savings against out-of-pocket exposure."
    }
  },
  "logistics": {
    "cargoContainerValidation": {
      "isValid": true,
      "warnings": []
    },
    "routeSeasonality": {
      "season": "Winter",
      "riskLevel": "HIGH",
      "factors": [
        {
          "factor": "Storm Frequency",
          "impact": "2.3x normal due to La Niña conditions"
        },
        {
          "factor": "Wave Height",
          "impact": "HIGH (4-6m average)"
        },
        {
          "factor": "Delay Probability",
          "impact": "+22% vs summer months"
        }
      ],
      "climaticIndices": [
        {
          "name": "ENSO (Niño)",
          "value": -0.8,
          "interpretation": "La Niña (active)"
        },
        {
          "name": "PDO",
          "value": 1.2,
          "interpretation": "Warm phase"
        },
        {
          "name": "MJO Phase",
          "value": 7,
          "interpretation": "Enhanced convection"
        }
      ]
    },
    "portCongestion": {
      "pol": {
        "name": "Ho Chi Minh",
        "dwellTime": 1.8,
        "normalDwellTime": 1.5,
        "status": "MILD"
      },
      "pod": {
        "name": "Los Angeles",
        "dwellTime": 2.4,
        "normalDwellTime": 2.0,
        "status": "MILD"
      },
      "transshipments": [
        {
          "name": "Singapore",
          "dwellTime": 3.2,
          "normalDwellTime": 1.5,
          "status": "HIGH"
        }
      ]
    },
    "delayProbabilities": {
      "p7days": 0.22,
      "p14days": 0.08,
      "p21days": 0.03
    },
    "packagingRecommendations": [
      {
        "item": "Desiccant packs",
        "cost": 200,
        "riskReduction": 40,
        "rationale": "Reduces moisture damage risk from temperature cycling"
      },
      {
        "item": "Humidity indicator cards",
        "cost": 50,
        "riskReduction": 20,
        "rationale": "Enables insurance claim documentation for moisture damage"
      },
      {
        "item": "Shock sensors",
        "cost": 150,
        "riskReduction": 30,
        "rationale": "Monitors mechanical shock during transit"
      }
    ]
  },
  "engine_version": "v2",
  "language": "en",
  "timestamp": "2026-01-16T10:00:00Z"
}
```

---

## 📦 MOCK 2: Perishable + Wrong Container (MISMATCH)

### Use Case
Test cargo-container mismatch detection

### Engine Output
```json
{
  "shipment": {
    "id": "SH-002",
    "route": "VN_JP",
    "pol_code": "VNSGN",
    "pod_code": "JPYOK",
    "carrier": "Cool Logistics",
    "etd": "2026-02-15",
    "eta": "2026-02-22",
    "transit_time": 7,
    "container": "40DV",
    "cargo": "Frozen Seafood",
    "cargo_type": "Frozen Seafood",
    "container_type": "40DV",
    "cargo_value": 150000
  },
  "risk_score": 75,
  "risk_level": "HIGH",
  "confidence": 0.90,
  "layers": [
    { "id": "1", "name": "Cargo-Container Mismatch", "score": 95, "contribution": 45, "weight": 45 }
  ],
  "loss": {
    "expectedLoss": 25000,
    "p95": 75000,
    "p99": 120000
  },
  "logistics": {
    "cargoContainerValidation": {
      "isValid": false,
      "warnings": [
        {
          "code": "PERISHABLE_NON_REEFER",
          "message": "Perishable cargo requires refrigerated container",
          "severity": "error"
        }
      ]
    },
    "routeSeasonality": {
      "season": "Spring",
      "riskLevel": "MEDIUM",
      "factors": [],
      "climaticIndices": []
    },
    "portCongestion": {
      "pol": { "name": "Ho Chi Minh", "dwellTime": 1.5, "normalDwellTime": 1.5, "status": "NORMAL" },
      "pod": { "name": "Yokohama", "dwellTime": 2.0, "normalDwellTime": 2.0, "status": "NORMAL" },
      "transshipments": []
    },
    "delayProbabilities": {
      "p7days": 0.05,
      "p14days": 0.01,
      "p21days": 0.00
    },
    "packagingRecommendations": []
  }
}
```

---

## 📦 MOCK 3: High Value + Multiple Transshipments

### Use Case
Test insurance flags and port congestion

### Engine Output
```json
{
  "shipment": {
    "id": "SH-003",
    "route": "DE_AU",
    "pol_code": "DEHAM",
    "pod_code": "AUMEL",
    "carrier": "Hapag-Lloyd",
    "etd": "2026-03-01",
    "eta": "2026-04-15",
    "transit_time": 45,
    "container": "20RF",
    "cargo": "Pharmaceuticals",
    "cargo_type": "Pharmaceuticals",
    "container_type": "20RF",
    "cargo_value": 2000000
  },
  "risk_score": 60,
  "risk_level": "HIGH",
  "confidence": 0.88,
  "loss": {
    "expectedLoss": 50000,
    "p95": 150000,
    "p99": 300000
  },
  "logistics": {
    "cargoContainerValidation": {
      "isValid": true,
      "warnings": []
    },
    "portCongestion": {
      "pol": { "name": "Hamburg", "dwellTime": 2.0, "normalDwellTime": 2.0, "status": "NORMAL" },
      "pod": { "name": "Melbourne", "dwellTime": 3.0, "normalDwellTime": 2.5, "status": "MILD" },
      "transshipments": [
        { "name": "Singapore", "dwellTime": 3.5, "normalDwellTime": 1.5, "status": "HIGH" },
        { "name": "Port Klang", "dwellTime": 2.8, "normalDwellTime": 1.5, "status": "HIGH" }
      ]
    },
    "delayProbabilities": {
      "p7days": 0.35,
      "p14days": 0.15,
      "p21days": 0.08
    }
  }
}
```

---

## 📦 MOCK 4: Low Risk Baseline

### Use Case
Test with minimal risk - verify panels still work

### Engine Output
```json
{
  "shipment": {
    "id": "SH-004",
    "route": "CN_US",
    "pol_code": "CNSHA",
    "pod_code": "USLAX",
    "carrier": "Maersk",
    "etd": "2026-05-01",
    "eta": "2026-05-15",
    "transit_time": 14,
    "container": "40DV",
    "cargo": "Textiles",
    "cargo_type": "Textiles",
    "container_type": "40DV",
    "cargo_value": 50000
  },
  "risk_score": 35,
  "risk_level": "LOW",
  "confidence": 0.75,
  "loss": {
    "expectedLoss": 2000,
    "p95": 8000,
    "p99": 15000
  },
  "insurance": {
    "basisRisk": {
      "score": 0.08,
      "interpretation": "low",
      "explanation": "Low risk shipment - standard coverage sufficient"
    },
    "coverageRecommendations": [
      {
        "type": "ICC(B)",
        "clause": "Named Perils Coverage",
        "rationale": "Low risk cargo - standard coverage sufficient",
        "priority": "optional"
      }
    ],
    "premiumLogic": {
      "expectedLoss": 2000,
      "loadFactor": 1.20,
      "calculatedPremium": 2400,
      "marketRate": 0.50,
      "riskcastRate": 0.48,
      "explanation": "Low risk - minimal premium"
    },
    "deductibleRecommendation": {
      "amount": 1000,
      "rationale": "Low risk - minimal deductible recommended"
    }
  },
  "logistics": {
    "cargoContainerValidation": {
      "isValid": true,
      "warnings": []
    },
    "routeSeasonality": {
      "season": "Spring",
      "riskLevel": "LOW",
      "factors": [],
      "climaticIndices": []
    },
    "portCongestion": {
      "pol": { "name": "Shanghai", "dwellTime": 1.5, "normalDwellTime": 1.5, "status": "NORMAL" },
      "pod": { "name": "Los Angeles", "dwellTime": 2.0, "normalDwellTime": 2.0, "status": "NORMAL" },
      "transshipments": []
    },
    "delayProbabilities": {
      "p7days": 0.05,
      "p14days": 0.01,
      "p21days": 0.00
    }
  }
}
```

---

## 📦 MOCK 5: Missing Insurance/Logistics Data

### Use Case
Test graceful degradation when data missing

### Engine Output
```json
{
  "shipment": {
    "id": "SH-005",
    "route": "US_GB",
    "pol_code": "USNYC",
    "pod_code": "GBLIV",
    "carrier": "Unknown",
    "cargo": "General Cargo",
    "cargo_type": "General Cargo",
    "container_type": "40DV",
    "cargo_value": 100000
  },
  "risk_score": 50,
  "risk_level": "MEDIUM",
  "confidence": 0.60,
  "loss": {
    "expectedLoss": 5000,
    "p95": 20000,
    "p99": 40000
  }
  // No insurance or logistics fields
}
```

**Expected Behavior:**
- Insurance panel does NOT appear (conditional rendering)
- Logistics panel appears but with minimal/default data
- No console errors
- Other panels still work

---

## 🧪 HOW TO USE MOCKS

### Option 1: Backend Mock
Add to backend test endpoint:
```python
# In app/api/v1/risk_routes.py
if request.json().get('test_mode') == 'sprint2_mock1':
    return mock_engine_output_1
```

### Option 2: Frontend Mock
In browser console:
```javascript
// Save mock data to localStorage
localStorage.setItem('RISKCAST_RESULTS_V2', JSON.stringify(mock1));
// Refresh /results page
```

### Option 3: Adapter Test
```typescript
import { adaptResultV2 } from '@/adapters/adaptResultV2';
const viewModel = adaptResultV2(mock1);
// Verify viewModel.insurance and viewModel.logistics
```

---

## ✅ VALIDATION CHECKLIST

For each mock, verify:

### Insurance Data
- [ ] `insurance.lossDistribution.histogram` has buckets
- [ ] `insurance.basisRisk.score` is 0-1
- [ ] `insurance.triggerProbabilities` has valid probabilities
- [ ] `insurance.coverageRecommendations` has priority
- [ ] `insurance.premiumLogic` has all fields
- [ ] `insurance.deductibleRecommendation` has amount

### Logistics Data
- [ ] `logistics.cargoContainerValidation.isValid` is boolean
- [ ] `logistics.routeSeasonality.riskLevel` is LOW/MEDIUM/HIGH
- [ ] `logistics.portCongestion.pol/pod` have dwell times
- [ ] `logistics.delayProbabilities` decrease: P7 > P14 > P21

---

**END OF TEST DATA MOCKS**
