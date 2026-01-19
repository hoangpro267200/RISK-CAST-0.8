# BÁO CÁO CHI TIẾT: CẤU TRÚC RESPONSE TỪ ENGINE V2

## Tổng quan

Khi trang **Summary** có dữ liệu và gửi đến engine qua endpoint `/api/v1/risk/v2/analyze`, engine sẽ trả về một response có cấu trúc phức tạp và đầy đủ. Tài liệu này mô tả chi tiết toàn bộ cấu trúc response.

---

## 1. ENDPOINT VÀ FLOW

### 1.1. Endpoint
```
POST /api/v1/risk/v2/analyze
```

### 1.2. Request Body
```json
{
  "transport_mode": "string",
  "cargo_type": "string",
  "route": "string",
  "pol": "string",
  "pod": "string",
  "carrier": "string",
  "etd": "ISO date string",
  "eta": "ISO date string",
  "cargo_value": number,
  "language": "vi|en|zh",
  // ... các field khác của ShipmentModel
}
```

### 1.3. Response Structure (Top Level)
```json
{
  "status": "success",
  "engine_version": "v2",
  "language": "vi|en|zh",
  "result": { /* Chi tiết bên dưới */ }
}
```

---

## 2. CẤU TRÚC `result` OBJECT (Từ RiskPipeline)

Object `result` được tạo bởi `RiskPipeline.run()` và chứa kết quả phân tích rủi ro cơ bản.

### 2.1. Các Field Chính

| Field | Type | Mô tả |
|-------|------|-------|
| `risk_score` | `float` | Điểm rủi ro tổng thể (0-100), làm tròn 2 chữ số thập phân |
| `risk_level` | `string` | Mức độ rủi ro: `"Low"`, `"Medium"`, `"High"`, `"Critical"` |
| `confidence` | `float` | Độ tin cậy của đánh giá (0-1), làm tròn 2 chữ số |

### 2.2. Profile Object

```json
{
  "profile": {
    "score": 75.5,                    // float: Risk score (0-100)
    "level": "High",                  // string: Risk level
    "confidence": 0.85,               // float: Confidence score (0-1)
    "explanation": [                  // array of strings
      "Explanation point 1",
      "Explanation point 2"
    ],
    "factors": {                      // object: Risk factor breakdown
      "delay": 0.7,
      "port": 0.6,
      "climate": 0.5,
      "carrier": 0.4,
      "esg": 0.3,
      "equipment": 0.5
    },
    "matrix": {
      "probability": 7,               // int: 1-9 (3x3 matrix)
      "severity": 8,                  // int: 1-9 (3x3 matrix)
      "quadrant": "High-High",        // string: Quadrant identifier
      "description": "High probability, high severity risk"
    }
  }
}
```

**Giải thích:**
- `explanation`: Danh sách các điểm giải thích về risk assessment
- `factors`: Điểm số chi tiết cho từng yếu tố rủi ro (0-1)
- `matrix.probability`: Xác suất xảy ra rủi ro (1-9, từ thấp đến cao)
- `matrix.severity`: Mức độ nghiêm trọng (1-9, từ thấp đến cao)
- `matrix.quadrant`: Vị trí trong ma trận rủi ro (ví dụ: "High-High", "Medium-Low")
- `matrix.description`: Mô tả văn bản về vị trí trong ma trận

### 2.3. Drivers (Các Yếu Tố Rủi Ro Chính)

```json
{
  "drivers": [
    {
      "name": "Climate Risk",
      "impact": 0.85,
      "description": "..."
    },
    // ... các driver khác
  ]
}
```

**Lưu ý:** `drivers` được tạo bởi LLM Reasoner, là danh sách các yếu tố rủi ro quan trọng nhất.

### 2.4. Recommendations

```json
{
  "recommendations": [
    "Recommendation text 1",
    "Recommendation text 2",
    // ... các recommendations khác
  ]
}
```

**Lưuý:** Recommendations là sự kết hợp giữa `reasoning_result.suggestions` và `risk_profile.recommendations`.

### 2.5. Reasoning (LLM-Generated)

```json
{
  "reasoning": {
    "explanation": "Detailed explanation of risk assessment...",
    "business_justification": "Business context and justification..."
  }
}
```

**Giải thích:**
- `explanation`: Giải thích chi tiết về đánh giá rủi ro, được tạo bởi LLM với region-aware
- `business_justification`: Lý do và bối cảnh kinh doanh cho các quyết định

### 2.6. Components (Các Thành Phần Tính Toán)

```json
{
  "components": {
    "fahp_weighted": 0.756,              // float: FAHP weighted score (0-1)
    "climate_risk": 0.623,               // float: Climate risk component (0-1)
    "network_risk": 0.487,               // float: Network risk component (0-1)
    "operational_risk": 0.534,           // float: Operational risk component (0-1)
    "missing_data_penalty": 0.05         // float: Penalty for missing data (0-1)
  }
}
```

**Giải thích:**
- `fahp_weighted`: Điểm số từ Fuzzy Analytic Hierarchy Process
- `climate_risk`: Rủi ro từ mô hình khí hậu
- `network_risk`: Rủi ro từ mô hình mạng lưới (port/carrier)
- `operational_risk`: Rủi ro vận hành
- `missing_data_penalty`: Hệ số phạt khi thiếu dữ liệu

### 2.7. Details (Chi Tiết Kỹ Thuật)

```json
{
  "details": {
    "climate": {
      "storm_probability": 0.234,        // float: Xác suất bão (0-1)
      "wind_index": 0.567,               // float: Chỉ số gió (0-1)
      "rainfall_intensity": 0.412        // float: Cường độ mưa (0-1)
    },
    "network": {
      "port_centrality": 0.789,          // float: Độ tập trung của cảng (0-1)
      "carrier_redundancy": 0.623,       // float: Độ dự phòng carrier (0-1)
      "propagation_factor": 0.456        // float: Hệ số lan truyền rủi ro (0-1)
    },
    "fahp_weights": {                    // object: FAHP weights cho từng yếu tố
      "delay": 0.234,
      "port": 0.189,
      "climate": 0.156,
      "carrier": 0.123,
      "esg": 0.098,
      "equipment": 0.098
    },
    "topsis_score": 0.678                // float: TOPSIS closeness coefficient (0-1)
  }
}
```

### 2.8. Region Information

```json
{
  "region": {
    "code": "APAC",                      // string: Region code
    "name": "Asia-Pacific",              // string: Region name
    "config": {
      "climate_weight": 0.6,             // float: Trọng số khí hậu cho khu vực
      "congestion_weight": 0.7,          // float: Trọng số tắc nghẽn
      "strike_weight": 0.5,              // float: Trọng số đình công
      "esg_weight": 0.45                 // float: Trọng số ESG
    }
  }
}
```

**Giải thích:** Thông tin khu vực được phát hiện tự động dựa trên POL/POD và được sử dụng để điều chỉnh tính toán rủi ro.

---

## 3. CẤU TRÚC `complete_result` (Được Tạo Trong API Endpoint)

API endpoint (`/api/v1/risk/v2/analyze`) mở rộng `result` từ RiskPipeline thành `complete_result` với nhiều field bổ sung.

### 3.1. Shipment Information

```json
{
  "shipment": {
    "id": "SH-SGN-LAX-1234567890",      // string: Shipment ID (auto-generated)
    "route": "SGN → LAX",               // string: Route display string
    "pol_code": "SGN",                  // string: Port of Loading code
    "pod_code": "LAX",                  // string: Port of Discharge code
    "origin": "SGN",                    // string: Origin port
    "destination": "LAX",               // string: Destination port
    "mode": "Ocean",                    // string: Transport mode
    "carrier": "CMA CGM",               // string: Carrier name
    "etd": "2024-01-15",                // string: Estimated Time of Departure
    "eta": "2024-02-05",                // string: Estimated Time of Arrival
    "transit_time": 21,                 // float: Transit time in days
    "container": "40HC",                // string: Container type
    "cargo": "Electronics",             // string: Cargo type
    "incoterm": "FOB",                  // string: Incoterm
    "value": 50000,                     // float: Cargo value (USD)
    "cargo_value": 50000                // float: Cargo value (USD, duplicate)
  }
}
```

### 3.2. Risk Metrics (Duplicated for Compatibility)

```json
{
  "risk_score": 75.5,                   // float: Risk score (0-100)
  "overall_risk": 75.5,                 // float: Overall risk (duplicate of risk_score)
  "risk_level": "High",                 // string: Risk level
  "confidence": 0.85                    // float: Confidence score
}
```

### 3.3. Layers (Được Tạo Từ Components)

```json
{
  "layers": [
    {
      "name": "Transport",              // string: Layer name
      "score": 75.6,                    // float: Layer score (0-100)
      "contribution": 0.756             // float: Contribution to overall score
    },
    {
      "name": "Weather",
      "score": 62.3,
      "contribution": 0.623
    },
    {
      "name": "Port",
      "score": 48.7,
      "contribution": 0.487
    },
    {
      "name": "Carrier",
      "score": 53.4,
      "contribution": 0.534
    }
  ]
}
```

**Giải thích:** Layers được build từ `components` object, mapping:
- `fahp_weighted` → "Transport"
- `climate_risk` → "Weather"
- `network_risk` → "Port"
- `operational_risk` → "Carrier"

### 3.4. Risk Factors & Drivers

```json
{
  "risk_factors": [ /* Same as drivers */ ],
  "factors": [ /* Same as drivers */ ],
  "drivers": [ /* Original drivers from result */ ]
}
```

**Lưu ý:** Các field này có thể trùng lặp nhau để tương thích với các version khác nhau của frontend.

### 3.5. Recommendations (Transformed Format)

```json
{
  "recommendations": {
    "insurance": {
      "required": true,                 // boolean: Insurance required?
      "level": "standard",              // string: "standard" | "optional"
      "threshold": 60,                  // float: Risk score threshold
      "premium": 0                      // float: Estimated premium (can be calculated)
    },
    "providers": [],                    // array: Insurance provider list
    "timing": {},                       // object: Timing recommendations
    "actions": [                        // array of strings: Action items
      "Action 1",
      "Action 2"
    ],
    "trace": {
      "version": "v2",
      "dominantSignals": [              // array: Top 3 drivers
        { "name": "...", "impact": ... }
      ],
      "triggers": []                    // array: Risk triggers
    }
  }
}
```

### 3.6. Loss Metrics

```json
{
  "loss": {
    "p95": 22500,                       // float: Value at Risk (95th percentile)
    "p99": 27000,                       // float: Conditional VaR (99th percentile)
    "expectedLoss": 15000,              // float: Expected loss (USD)
    "tailContribution": 28.5            // float: Tail risk contribution (%)
  }
}
```

**Công thức tính:**
- `expectedLoss = cargo_value * (risk_score / 100) * 0.3`
- `p95 (VaR) = expectedLoss * 1.5`
- `p99 (CVaR) = expectedLoss * 1.8`
- `tailContribution = 15.0` nếu `risk_score < 60`, ngược lại `28.5`

### 3.7. Risk Scenario Projections

```json
{
  "riskScenarioProjections": [
    {
      "date": "2024-01-15",             // string: Projection date (YYYY-MM-DD)
      "p10": 64.2,                      // float: 10th percentile (best case)
      "p50": 75.5,                      // float: 50th percentile (median)
      "p90": 86.8,                      // float: 90th percentile (worst case)
      "phase": "Booking"                // string: Journey phase
    },
    // ... 7-10 projection points
  ]
}
```

**Giải thích:**
- Tạo 7-10 điểm projection dựa trên ETD và ETA
- Mỗi điểm có 3 percentile: P10 (best case), P50 (median), P90 (worst case)
- Phases: "Booking", "Pre-Departure", "Ocean Transit", "Port Approach", "Arrival"
- Risk thường tăng cao nhất ở giai đoạn "Ocean Transit" (bathtub curve)

### 3.8. Mitigation Scenarios

```json
{
  "scenarios": [
    {
      "id": "baseline",                 // string: Scenario ID
      "title": "Current Plan (Baseline)",
      "category": "BASELINE",           // string: Category
      "riskReduction": 0,               // float: Risk reduction points
      "costImpact": 0,                  // float: Cost impact (USD, negative = savings)
      "isRecommended": false,           // boolean: Is this recommended?
      "rank": 99,                       // int: Rank (lower = better)
      "description": "Proceed with current plan without changes"
    },
    {
      "id": "insurance",
      "title": "Add Cargo Insurance",
      "category": "INSURANCE",
      "riskReduction": 26.4,            // float: Risk reduction (points)
      "costImpact": 750,                // float: Insurance premium (USD)
      "isRecommended": true,            // boolean: Recommended if risk_score > 70
      "rank": 1,                        // int: Rank
      "description": "Comprehensive cargo insurance covering 26% of identified risks"
    },
    {
      "id": "timing",
      "title": "Adjust Departure Timing",
      "category": "TIMING",
      "riskReduction": 15.1,
      "costImpact": -800,               // float: Negative = cost savings
      "isRecommended": false,
      "rank": 3,
      "description": "Shift ETD to avoid peak congestion/weather window"
    },
    {
      "id": "carrier",
      "title": "Upgrade to Premium Carrier",
      "category": "ROUTING",
      "riskReduction": 13.6,
      "costImpact": 400,
      "isRecommended": false,
      "rank": 4,
      "description": "Switch to carrier with higher reliability rating"
    },
    {
      "id": "route",
      "title": "Alternative Routing",
      "category": "ROUTING",
      "riskReduction": 18.9,
      "costImpact": 1200,
      "isRecommended": false,
      "rank": 5,
      "description": "Use alternative route avoiding high-risk zones"
    },
    {
      "id": "combined",
      "title": "Insurance + Timing Optimization",
      "category": "COMBINED",
      "riskReduction": 37.8,
      "costImpact": 1250,
      "isRecommended": true,
      "rank": 1,
      "description": "Combined strategy for maximum risk reduction"
    }
  ]
}
```

**Categories:**
- `BASELINE`: Kịch bản hiện tại (không thay đổi)
- `INSURANCE`: Mua bảo hiểm hàng hóa
- `TIMING`: Điều chỉnh thời gian khởi hành
- `ROUTING`: Thay đổi carrier hoặc route
- `COMBINED`: Kết hợp nhiều biện pháp

**Logic:**
- Scenarios được sắp xếp theo `rank` (thấp hơn = tốt hơn)
- `isRecommended = true` nếu risk_score vượt ngưỡng nhất định
- `riskReduction`: Số điểm giảm rủi ro (tính bằng điểm, không phải %)

### 3.9. Decision Summary

```json
{
  "decision_summary": {
    "confidence": 0.85,                 // float: Overall confidence
    "overall_risk": {
      "score": 75.5,                    // float: Risk score
      "level": "High"                   // string: Risk level
    },
    "insurance": {
      "status": "RECOMMENDED",          // string: "RECOMMENDED" | "OPTIONAL" | "NOT_NEEDED"
      "recommendation": "BUY",          // string: "BUY" | "CONSIDER" | "SKIP"
      "rationale": "High risk level (High) with score 76/100 warrants cargo insurance coverage",
      "risk_delta_points": 26.4,        // float: Risk reduction points
      "cost_impact_usd": 750,           // float: Cost impact
      "providers": []                   // array: Insurance providers list
    },
    "timing": {
      "status": "OPTIONAL",             // string: "RECOMMENDED" | "OPTIONAL" | "NOT_NEEDED"
      "recommendation": "KEEP_ETD",     // string: "ADJUST_ETD" | "KEEP_ETD"
      "rationale": "Current timing acceptable - minor optimization possible",
      "optimal_window": null,           // object | null: { "start": "YYYY-MM-DD", "end": "YYYY-MM-DD" }
      "risk_reduction_points": null,    // float | null: Risk reduction
      "cost_impact_usd": null           // float | null: Cost impact
    },
    "routing": {
      "status": "OPTIONAL",
      "recommendation": "KEEP_ROUTE",   // string: "CHANGE_ROUTE" | "KEEP_ROUTE"
      "rationale": "Current route acceptable - premium options available",
      "best_alternative": null,         // string | null: Best alternative route/carrier
      "tradeoff": null,                 // string | null: Cost-risk tradeoff description
      "risk_reduction_points": null,
      "cost_impact_usd": null
    }
  }
}
```

**Decision Logic:**
- **Insurance:**
  - `RECOMMENDED` nếu `risk_score >= 70` và `confidence >= 0.6`
  - `OPTIONAL` nếu `risk_score >= 49` (70% của 70)
  - Ngưỡng: 70
  
- **Timing:**
  - `RECOMMENDED` nếu `risk_score >= 75` và có weather/congestion driver
  - Ngưỡng: 75
  
- **Routing:**
  - `RECOMMENDED` nếu `risk_score >= 80`
  - Ngưỡng: 80

### 3.10. Decision Signal (Frontend Compatibility)

```json
{
  "decisionSignal": {
    "recommendation": "BUY",            // string: "BUY" | "OPTIONAL" | "SKIP"
    "rationale": "High risk level (High) with score 76/100 warrants cargo insurance coverage",
    "providers": []                     // array: Insurance providers
  }
}
```

**Lưu ý:** Field này tạo ra để tương thích với React frontend, mapping từ `decision_summary.insurance`.

### 3.11. Timing (Nếu Recommended)

```json
{
  "timing": {
    "optimalWindow": {                  // object: Only present if timing.status == "RECOMMENDED"
      "start": "2024-01-18",
      "end": "2024-01-22"
    },
    "riskReduction": 15.1               // float: Risk reduction points
  }
}
```

### 3.12. Traces (Sensitivity Analysis Data)

```json
{
  "traces": {
    "Transport": {
      "layerName": "Transport",
      "steps": [
        {
          "stepId": "step-transport",
          "method": "risk_layer_analysis",
          "summary": "Analyzed Transport risk factors"
        }
      ],
      "sensitivity": [
        {
          "name": "Transport Score",
          "impact": 15.12               // float: Impact on overall score
        },
        {
          "name": "Transport Contribution",
          "impact": 11.34
        }
      ]
    },
    // ... các layers khác
  }
}
```

**Giải thích:** Traces được tạo cho mỗi layer có `score > 50` hoặc `contribution > 15`, dùng cho sensitivity analysis chart.

### 3.13. Data Reliability

```json
{
  "dataReliability": [
    {
      "domain": "Risk Engine",
      "confidence": 0.85,               // float: Confidence score
      "completeness": 0.85,             // float: Data completeness (0-1)
      "freshness": 0.90,                // float: Data freshness (0-1)
      "notes": "Engine v2 risk analysis results"
    },
    {
      "domain": "Shipment Data",
      "confidence": 0.80,
      "completeness": 0.75,
      "freshness": 0.85,
      "notes": "Shipment information provided"
    }
  ]
}
```

### 3.14. Methodology

```json
{
  "methodology": {
    "riskAggregation": {
      "model": "FAHP",
      "method": "Fuzzy Analytic Hierarchy Process with Monte Carlo simulation"
    }
  }
}
```

### 3.15. Metadata

```json
{
  "engine_version": "v2",               // string: Engine version
  "language": "vi",                     // string: Language code
  "timestamp": "2024-01-15T10:30:00"   // string: ISO timestamp
}
```

---

## 4. LUU TRỮ BACKEND STATE

### 4.1. Storage Location

`complete_result` được lưu vào shared backend state thông qua `set_last_result_v2(complete_result)`.

### 4.2. Purpose

- Results page có thể đọc dữ liệu từ backend state qua `GET /results/data`
- Đảm bảo Results page luôn hiển thị dữ liệu từ engine (ENGINE-FIRST architecture)
- Tránh duplicate execution

### 4.3. Key Name

```
LAST_RESULT_V2
```

---

## 5. VÍ DỤ RESPONSE ĐẦY ĐỦ

### 5.1. Response từ API

```json
{
  "status": "success",
  "engine_version": "v2",
  "language": "vi",
  "result": {
    "risk_score": 75.5,
    "risk_level": "High",
    "confidence": 0.85,
    "profile": {
      "score": 75.5,
      "level": "High",
      "confidence": 0.85,
      "explanation": [
        "Risk score of 75.5 indicates high risk level",
        "Primary drivers: Climate risk and port congestion"
      ],
      "factors": {
        "delay": 0.7,
        "port": 0.6,
        "climate": 0.5,
        "carrier": 0.4
      },
      "matrix": {
        "probability": 7,
        "severity": 8,
        "quadrant": "High-High",
        "description": "High probability, high severity risk"
      }
    },
    "drivers": [
      {
        "name": "Climate Risk",
        "impact": 0.85,
        "description": "Storm probability is elevated for this route"
      }
    ],
    "recommendations": [
      "Consider purchasing cargo insurance",
      "Monitor weather conditions closely"
    ],
    "reasoning": {
      "explanation": "The shipment faces elevated risk due to...",
      "business_justification": "Given the cargo value and risk level..."
    },
    "components": {
      "fahp_weighted": 0.756,
      "climate_risk": 0.623,
      "network_risk": 0.487,
      "operational_risk": 0.534,
      "missing_data_penalty": 0.05
    },
    "details": {
      "climate": {
        "storm_probability": 0.234,
        "wind_index": 0.567,
        "rainfall_intensity": 0.412
      },
      "network": {
        "port_centrality": 0.789,
        "carrier_redundancy": 0.623,
        "propagation_factor": 0.456
      },
      "fahp_weights": {
        "delay": 0.234,
        "port": 0.189,
        "climate": 0.156
      },
      "topsis_score": 0.678
    },
    "region": {
      "code": "APAC",
      "name": "Asia-Pacific",
      "config": {
        "climate_weight": 0.6,
        "congestion_weight": 0.7,
        "strike_weight": 0.5,
        "esg_weight": 0.45
      }
    }
  }
}
```

### 5.2. Complete Result (Stored in Backend)

Phần này chứa toàn bộ `complete_result` được lưu trong backend state, bao gồm tất cả các field được mở rộng từ `result` như đã mô tả ở phần 3.

---

## 6. TÓM TẮT CẤU TRÚC

### 6.1. Response Structure Summary

```
POST /api/v1/risk/v2/analyze Response
│
├── status: "success"
├── engine_version: "v2"
├── language: "vi|en|zh"
└── result (from RiskPipeline)
    ├── risk_score, risk_level, confidence
    ├── profile (score, level, confidence, explanation, factors, matrix)
    ├── drivers (key risk drivers)
    ├── recommendations (array of strings)
    ├── reasoning (explanation, business_justification)
    ├── components (fahp_weighted, climate_risk, network_risk, operational_risk, missing_data_penalty)
    ├── details (climate, network, fahp_weights, topsis_score)
    └── region (code, name, config)

complete_result (stored in backend, not in API response)
│
├── shipment (id, route, pol_code, pod_code, ...)
├── risk_score, overall_risk, risk_level, confidence
├── layers (Transport, Weather, Port, Carrier)
├── risk_factors, factors, drivers
├── recommendations (transformed object format)
├── profile, matrix
├── loss (p95, p99, expectedLoss, tailContribution)
├── riskScenarioProjections (time series with P10/P50/P90)
├── scenarios (mitigation scenarios with risk-cost tradeoffs)
├── decision_summary (insurance, timing, routing decisions)
├── decisionSignal (frontend compatibility)
├── timing (optimalWindow if recommended)
├── traces (sensitivity analysis data)
├── dataReliability (confidence, completeness, freshness)
├── methodology
└── engine_version, language, timestamp
```

### 6.2. Key Differences

| Aspect | API Response (`result`) | Backend State (`complete_result`) |
|--------|------------------------|----------------------------------|
| **Purpose** | Return to frontend immediately | Store for Results page |
| **Size** | Smaller (core analysis only) | Larger (with all UI mappings) |
| **Includes** | Raw engine output | Engine output + UI transformations |
| **Shipment Info** | No | Yes (detailed shipment object) |
| **Layers** | No | Yes (built from components) |
| **Scenarios** | No | Yes (mitigation scenarios) |
| **Decision Summary** | No | Yes (insurance/timing/routing) |

---

## 7. NOTES VÀ BEST PRACTICES

### 7.1. ENGINE-FIRST Architecture

- Engine chỉ chạy một lần trong Summary page
- Kết quả được lưu vào backend state
- Results page đọc từ backend state (không chạy lại engine)
- UI chỉ render dữ liệu, không tính toán

### 7.2. Data Flow

```
Summary Page (Submit)
  ↓
POST /api/v1/risk/v2/analyze
  ↓
RiskPipeline.run() → result
  ↓
API endpoint → complete_result
  ↓
set_last_result_v2(complete_result) → Backend State
  ↓
Results Page (Load)
  ↓
GET /results/data → complete_result
```

### 7.3. Language Support

- Engine hỗ trợ multi-language: `vi`, `en`, `zh`
- LLM reasoning được generate theo language
- Frontend có thể truyền `language` trong request

### 7.4. Error Handling

- Nếu engine fail: HTTP 500 với error detail
- Nếu store state fail: Log warning nhưng vẫn return response
- Frontend nên handle error response appropriately

---

## 8. CHANGELOG VÀ VERSIONS

### Engine Version: v2

- Sử dụng FAHP + TOPSIS + Climate Model + Network Model
- LLM reasoning với region-aware
- Multi-language support
- Scenario simulation capabilities
- Decision summary với insurance/timing/routing recommendations

---

**Tài liệu này được tạo ngày:** 2024-01-15  
**Version:** 1.0  
**Author:** Auto-generated from codebase analysis

