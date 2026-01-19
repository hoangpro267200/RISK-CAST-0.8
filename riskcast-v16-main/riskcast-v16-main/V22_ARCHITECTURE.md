# RiskCast V22 Architecture Diagram

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT APPLICATION                          │
│                                                                     │
│  from api_response_v22 import generate_risk_assessment_v22         │
│  result = generate_risk_assessment_v22(shipment_data)              │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      api_response_v22.py                            │
│                  Main Orchestration Layer                           │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ STEP 1: VALIDATION                                          │  │
│  │  validator = RiskCastV21Validator()                         │  │
│  │  is_valid, results = validator.validate_full_input(data)    │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                             │                                       │
│                             ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ STEP 2: CORE RISK SCORING                                   │  │
│  │  scorer = RiskScoringEngineV21()                            │  │
│  │  risk = scorer.calculate_comprehensive_risk(data, modules)  │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                             │                                       │
│                             ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ STEP 3: ENHANCED FEATURES                                   │  │
│  │  enhancer = EnhancedAlgorithmicFeaturesV21()                │  │
│  │  delay = enhancer.predictive_delay_model(...)               │  │
│  │  routes = enhancer.route_optimization_suggestions(...)      │  │
│  │  insurance = enhancer.insurance_optimization(...)           │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                             │                                       │
│                             ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ STEP 4: V22 FUTURE MODULES (Hooks)                         │  │
│  │  ┌────────────────────────────────────────────────────┐    │  │
│  │  │ TODO: AIExplanationEngine                          │    │  │
│  │  │ TODO: RiskDriverTree                               │    │  │
│  │  │ TODO: ESGScoringEngine (placeholder)              │    │  │
│  │  │ TODO: MonteCarloSimulationEngine (placeholder)    │    │  │
│  │  │ TODO: StressTestEngine (placeholder)              │    │  │
│  │  └────────────────────────────────────────────────────┘    │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                             │                                       │
│                             ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ STEP 5: BUILD COMPREHENSIVE RESPONSE                       │  │
│  │  return {                                                   │  │
│  │    'success': True,                                         │  │
│  │    'risk_assessment': {...},                                │  │
│  │    'operational_intelligence': {...},                       │  │
│  │    'recommendations': {...},                                │  │
│  │    'esg_assessment': {...},      # V22 NEW                 │  │
│  │    'monte_carlo_simulation': {...}, # V22 NEW              │  │
│  │  }                                                          │  │
│  └─────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │ JSON Response  │
                    └────────────────┘
```

## Module Dependencies

```
api_response_v22.py
    │
    ├─── imports ──→ riskcast_validator.py
    │                     │
    │                     └─── provides: RiskCastV21Validator
    │                                     ValidationSeverity
    │                                     ValidationResult
    │
    ├─── imports ──→ risk_scoring_engine.py
    │                     │
    │                     └─── provides: RiskScoringEngineV21
    │                                     RiskLevel
    │                                     RiskCategory
    │
    └─── imports ──→ enhanced_features.py
                          │
                          └─── provides: EnhancedAlgorithmicFeaturesV21
                                (imports risk_scoring_engine dynamically)
```

## Data Flow Diagram

```
INPUT DATA
    │
    ├── transport { mode, carrier, incoterm, pol, pod, ... }
    ├── cargo { type, weight, value, sensitivity, ... }
    ├── seller { company, country, tax_id, ... }
    ├── buyer { company, country, tax_id, ... }
    └── modules { esg, monte_carlo, stress_test, ... }
    │
    ▼
┌─────────────────────────┐
│  VALIDATION LAYER       │  ← riskcast_validator.py
│  • 60+ business rules   │
│  • Cross-field checks   │
│  • Returns: is_valid +  │
│    validation_results   │
└────────┬────────────────┘
         │ (if valid)
         ▼
┌─────────────────────────┐
│  RISK SCORING LAYER     │  ← risk_scoring_engine.py
│  • 16 risk dimensions   │
│  • 5 risk categories    │
│  • Sub-factor tracking  │
│  • Returns: risk_       │
│    assessment dict      │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  ENHANCED FEATURES      │  ← enhanced_features.py
│  • Delay prediction     │
│  • Route optimization   │
│  • Insurance advice     │
│  • Weight adjustment    │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  V22 MODULES (Future)   │  ← Integration hooks in api_response_v22.py
│  • AI Explanations      │
│  • Risk Driver Tree     │
│  • ESG Scoring          │
│  • Monte Carlo Sim      │
│  • Stress Testing       │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  COMPREHENSIVE RESPONSE │
│  {                      │
│    success: true        │
│    risk_assessment: {}  │
│    recommendations: {}  │
│    esg_assessment: {}   │
│    ...                  │
│  }                      │
└─────────────────────────┘
```

## Risk Scoring Architecture

```
RiskScoringEngineV21
    │
    ├─── RISK_LAYERS (16 dimensions)
    │       │
    │       ├─── TRANSPORT (4 layers)
    │       │     ├── mode_reliability
    │       │     ├── carrier_performance
    │       │     ├── route_complexity
    │       │     └── transit_time_variance
    │       │
    │       ├─── CARGO (3 layers)
    │       │     ├── cargo_sensitivity
    │       │     ├── packing_quality
    │       │     └── dg_compliance
    │       │
    │       ├─── COMMERCIAL (4 layers)
    │       │     ├── incoterm_risk
    │       │     ├── seller_credibility
    │       │     ├── buyer_credibility
    │       │     └── insurance_adequacy
    │       │
    │       ├─── COMPLIANCE (2 layers)
    │       │     ├── documentation_complexity
    │       │     └── trade_compliance
    │       │
    │       └─── EXTERNAL (3 layers)
    │             ├── port_congestion
    │             ├── weather_climate
    │             └── market_volatility
    │
    ├─── calculate_comprehensive_risk()
    │       │
    │       ├─→ calculate_sub_factors()  [V22 NEW]
    │       ├─→ calculate each layer score
    │       ├─→ aggregate by category
    │       ├─→ generate recommendations
    │       ├─→ generate mitigation plan
    │       └─→ estimate financial impact
    │
    └─── Returns:
            {
              overall_score: 38.26,
              risk_level: "medium",
              layer_scores: {...},
              sub_factor_scores: {...},  [V22 NEW]
              category_scores: {...},
              recommendations: [...],
              mitigation_plan: {...},
              financial_impact: {...}
            }
```

## Validation Flow

```
RiskCastV21Validator.validate_full_input(data)
    │
    ├─→ _validate_transport()
    │     ├─ Check required fields
    │     ├─ Validate mode & shipment_type
    │     ├─ Validate incoterm & compatibility
    │     ├─ Validate container_type
    │     ├─ Validate dates (ETD)
    │     ├─ Check transit_time reasonableness
    │     └─ Validate reliability_score range
    │
    ├─→ _validate_cargo()
    │     ├─ Check required fields
    │     ├─ Validate HS Code format
    │     ├─ Check weight consistency (gross > net)
    │     ├─ Calculate density & flag anomalies
    │     ├─ Validate sensitivity type
    │     ├─ Check dangerous goods requirements
    │     └─ Validate insurance coverage
    │
    ├─→ _validate_party(seller)
    │     ├─ Check required fields
    │     ├─ Validate email format
    │     ├─ Check phone format
    │     └─ Validate tax_id length
    │
    ├─→ _validate_party(buyer)
    │     └─ (same as seller)
    │
    ├─→ _validate_cross_field_rules()
    │     ├─ DG mode restrictions
    │     ├─ Temperature cargo → reefer check
    │     ├─ High-value → coverage check
    │     └─ Priority vs mode compatibility
    │
    └─→ _validate_modules()
          └─ Check module names valid
                [esg, weather_climate, port_congestion,
                 carrier_performance, market_condition,
                 insurance_optimization, monte_carlo, stress_test]
```

## Enhanced Features Architecture

```
EnhancedAlgorithmicFeaturesV21 (all static methods)
    │
    ├─── dynamic_weight_adjustment(layer_scores, priority, cargo_value)
    │      │
    │      ├─→ If cargo_value > 500k: boost insurance & cargo weights
    │      ├─→ If priority = 'fastest': boost time-related weights
    │      ├─→ If priority = 'cheapest': boost market weight
    │      └─→ Normalize total weight to 1.0
    │
    ├─── predictive_delay_model(transport, layer_scores)
    │      │
    │      ├─→ Calculate delay factors from risk scores
    │      ├─→ Estimate expected delay days
    │      ├─→ Calculate delay probability
    │      └─→ Return {expected_transit, delay_prob, p50, p95, breakdown}
    │
    ├─── route_optimization_suggestions(transport, layer_scores)
    │      │
    │      ├─→ Check if sea freight with high variance → suggest air
    │      ├─→ Check if poor carrier → suggest premium
    │      ├─→ Check if high congestion → suggest alt port
    │      └─→ Return [{alternative, benefit, trade_off, risk_reduction}]
    │
    └─── insurance_optimization(cargo, layer_scores, overall_risk)
           │
           ├─→ If high risk → suggest ICC A upgrade
           ├─→ If sensitive cargo → suggest damage survey clause
           ├─→ If compliance risk → suggest war/strikes clause
           └─→ Return {current_coverage, recommendations[]}
```

## Module Configuration

```
modules = {
    # V21 Modules (Working)
    'esg': True/False,
    'weather_climate': True/False,
    'port_congestion': True/False,
    'carrier_performance': True/False,
    'market_condition': True/False,
    'insurance_optimization': True/False,
    
    # V22 Modules (Placeholder)
    'monte_carlo': True/False,     # → MonteCarloSimulationEngine
    'stress_test': True/False,     # → StressTestEngine
}

# Future V22 modules (not in config yet)
'ai_explanation': True/False,      # → AIExplanationEngine
'risk_driver_tree': True/False,    # → RiskDriverTreeEngine
```

## Error Handling Flow

```
generate_risk_assessment_v22(input_data)
    │
    ├─→ validate_full_input()
    │     │
    │     ├─ If ERRORS found
    │     │   └─→ Return {
    │     │         success: False,
    │     │         validation_errors: [...],
    │     │         validation_warnings: [...]
    │     │       }
    │     │
    │     └─ If only WARNINGS
    │           └─→ Continue, include warnings in response
    │
    └─→ calculate_comprehensive_risk()
          └─→ Always returns valid risk_assessment
              (uses safe defaults for missing data)
```

## File Structure Summary

```
app/core/engine/
│
├── riskcast_engine_v21.py      [LEGACY - Keep for backward compat]
│   └── 1626 lines monolithic
│
├── riskcast_validator.py       [V22 NEW]
│   └── 573 lines
│       ├── ValidationSeverity
│       ├── ValidationResult
│       └── RiskCastV21Validator
│
├── risk_scoring_engine.py      [V22 NEW]
│   └── 652 lines
│       ├── RiskLevel
│       ├── RiskCategory
│       └── RiskScoringEngineV21
│           └── calculate_sub_factors() [V22 enhancement]
│
├── enhanced_features.py        [V22 NEW]
│   └── 157 lines
│       └── EnhancedAlgorithmicFeaturesV21
│           ├── dynamic_weight_adjustment()
│           ├── predictive_delay_model()
│           ├── route_optimization_suggestions()
│           └── insurance_optimization()
│
└── api_response_v22.py         [V22 NEW - Main Entry]
    └── 402 lines
        ├── generate_risk_assessment_v22()
        └── V22 integration hooks (5 TODO sections)
```

## Version Comparison Matrix

| Feature | V21 | V22 | V23 (Planned) |
|---------|-----|-----|---------------|
| Modular Architecture | ❌ | ✅ | ✅ |
| Input Validation (60+ rules) | ✅ | ✅ | ✅ |
| 16-Layer Risk Scoring | ✅ | ✅ | ✅ |
| Sub-Factor Tracking | ❌ | ✅ | ✅ |
| Enhanced Features | ✅ | ✅ | ✅ |
| AI Explanations | ❌ | 🔄 Hook | ✅ |
| Risk Driver Tree | ❌ | 🔄 Hook | ✅ |
| ESG Scoring | 🔄 Partial | 🔄 Hook | ✅ |
| Monte Carlo Simulation | ❌ | 🔄 Hook | ✅ |
| Stress Testing | ❌ | 🔄 Hook | ✅ |
| Real-time Data Feeds | ❌ | ❌ | ✅ |
| Machine Learning Models | ❌ | ❌ | ✅ |

Legend: ✅ Implemented | 🔄 Placeholder/Hook | ❌ Not Available

---

**Architecture Status:** ✅ V22 Phase 1 Complete - Ready for Feature Integration

*This architecture provides a clean, scalable foundation for RiskCast V22 and beyond.*






