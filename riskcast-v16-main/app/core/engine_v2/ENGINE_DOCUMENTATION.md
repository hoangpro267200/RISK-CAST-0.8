# TÀI LIỆU THUẬT TOÁN VÀ CẤU TRÚC ENGINE V2

## TỔNG QUAN THUẬT TOÁN

### Mục đích
Engine v2 là **Hybrid AI Risk Assessment Engine** kết hợp nhiều phương pháp đánh giá rủi ro để tính toán điểm rủi ro tổng thể (0-100) cho một lô hàng vận chuyển logistics.

### Thuật toán chính

Engine sử dụng **kiến trúc pipeline đa tầng** với các thành phần sau:

1. **FAHP (Fuzzy Analytic Hierarchy Process)**: Tính trọng số cho các yếu tố rủi ro
2. **TOPSIS (Technique for Order Preference by Similarity to Ideal Solution)**: Đánh giá đa tiêu chí
3. **Climate Risk Model**: Mô hình rủi ro thời tiết và khí hậu
4. **Network Risk Model**: Mô hình rủi ro mạng lưới (port centrality, carrier redundancy)
5. **Unified Scoring**: Kết hợp tất cả thành phần thành điểm số cuối cùng
6. **Risk Profile Builder**: Xây dựng profile rủi ro với ma trận tác động
7. **LLM Reasoner**: Tạo giải thích và khuyến nghị bằng ngôn ngữ tự nhiên

### Flow tính toán

```
Input Shipment Data
    ↓
1. Parse & Sanitize Inputs
    ↓
2. Extract Risk Context (delay, port, climate, carrier, esg, equipment)
    ↓
3. FAHP Solver → Tính trọng số cho các yếu tố rủi ro
    ↓
4. TOPSIS Solver → Đánh giá đa tiêu chí với weights từ FAHP
    ↓
5. Climate Model → Tính rủi ro thời tiết (storm, rainfall, wind, ENSO)
    ↓
6. Network Model → Tính rủi ro mạng lưới (port centrality, carrier redundancy, propagation)
    ↓
7. Unified Scoring → Kết hợp tất cả thành phần:
   - FAHP-weighted TOPSIS: 45%
   - Climate Risk: 20%
   - Network Risk: 20%
   - Operational Risk: 15%
    ↓
8. Region-based Adjustments → Điều chỉnh theo region config
    ↓
9. Risk Profile Builder → Xây dựng profile với probability × severity matrix
    ↓
10. LLM Reasoner → Tạo explanation và recommendations
    ↓
Output: Complete Risk Assessment Result
```

---

## CHI TIẾT TỪNG FILE

### 1. `risk_pipeline.py` - Pipeline Điều Phối Chính

**Chức năng:**
- **File điều phối chính** cho toàn bộ quá trình đánh giá rủi ro
- Orchestrates tất cả các modules khác theo thứ tự đúng
- Parse và sanitize input data từ shipment
- Extract risk context từ inputs
- Gọi các models (FAHP, TOPSIS, Climate, Network) theo thứ tự
- Apply region-based adjustments
- Build final result dictionary

**Class chính:** `RiskPipeline`

**Methods quan trọng:**
- `parse_inputs()`: Parse và normalize shipment data
- `extract_risk_context()`: Extract các yếu tố rủi ro từ inputs (delay, port, climate, carrier, esg, equipment)
- `run()`: Main pipeline execution - chạy toàn bộ flow từ input → output

**Input:** `shipment_data` dictionary
**Output:** Complete risk assessment result với:
- `risk_score`: 0-100
- `risk_level`: Low/Medium/High/Critical
- `profile`: Risk profile object
- `drivers`: Key risk drivers
- `recommendations`: Mitigation suggestions
- `components`: Breakdown của từng thành phần
- `details`: Chi tiết từng model (climate, network, FAHP, TOPSIS)
- `region`: Region code và config

---

### 2. `fahp.py` - Fuzzy Analytic Hierarchy Process

**Chức năng:**
- **Tính trọng số cho các yếu tố rủi ro** sử dụng FAHP
- Fuzzy AHP xử lý sự không chắc chắn trong pairwise comparisons
- Sử dụng triangular fuzzy numbers (l, m, u) để mô hình hóa uncertainty
- Convert fuzzy numbers thành crisp weights (defuzzification)

**Class chính:** `FAHPSolver`

**Thuật toán:**
1. Build pairwise comparison matrix (1-9 Saaty scale, fuzzified)
2. Convert crisp comparisons → fuzzy triangular numbers
3. Geometric mean method để tính fuzzy weights
4. Defuzzification (centroid method) để có crisp weights
5. Check consistency ratio (CR) - phải < 0.1

**Risk Factors:**
- `delay`: Rủi ro chậm trễ
- `port`: Rủi ro tắc nghẽn cảng
- `climate`: Rủi ro thời tiết
- `carrier`: Rủi ro độ tin cậy carrier
- `esg`: Rủi ro ESG
- `equipment`: Rủi ro thiết bị

**Methods quan trọng:**
- `build_default_comparison_matrix()`: Auto-build matrix từ risk context
- `compute_fuzzy_weights()`: Tính fuzzy weights bằng geometric mean
- `compute_crisp_weights()`: Defuzzify để có weights cuối cùng
- `check_consistency()`: Kiểm tra CR
- `solve()`: Complete FAHP solving process

**Output:** Dictionary mapping factor names → weights (0-1, sum to 1)

---

### 3. `topsis.py` - Technique for Order Preference by Similarity to Ideal Solution

**Chức năng:**
- **Multi-criteria decision making** để đánh giá alternatives
- Tìm ideal positive solution (best possible) và ideal negative solution (worst possible)
- Tính distance từ alternative đến 2 ideal solutions
- Closeness coefficient = distance to negative / (distance to positive + distance to negative)
- Higher closeness = better alternative

**Class chính:** `TOPSISSolver`

**Thuật toán:**
1. Build decision matrix từ alternatives
2. Normalize matrix (vector normalization hoặc min-max)
3. Apply criterion weights (từ FAHP)
4. Find ideal positive (best) và ideal negative (worst) solutions
5. Calculate Euclidean distances
6. Calculate closeness coefficient

**Methods quan trọng:**
- `build_decision_matrix()`: Tạo matrix từ alternatives
- `normalize_matrix()`: Normalize về 0-1 range
- `apply_weights()`: Apply FAHP weights
- `find_ideal_solutions()`: Tìm ideal positive/negative
- `calculate_closeness()`: Tính closeness coefficient
- `solve()`: Complete TOPSIS solving process

**Output:** `TOPSISResult` với closeness_coefficient (0-1)

**Lưu ý:** Trong RiskCast, thường chỉ có 1 alternative (shipment hiện tại), nhưng TOPSIS vẫn tính closeness để normalize score.

---

### 4. `climate_model.py` - Mô Hình Rủi Ro Thời Tiết

**Chức năng:**
- **Tính rủi ro liên quan đến thời tiết và khí hậu**
- Xem xét storm probability, rainfall intensity, wind index, temperature deviation
- Tính seasonal volatility và ENSO (El Niño/La Niña) influence
- Route-specific và month-specific adjustments

**Class chính:** `ClimateRiskModel`

**Components:**
1. **Storm Probability**: Dựa trên route region (Pacific/Atlantic/Indian) và tháng (hurricane season)
2. **Rainfall Intensity**: Monsoon seasons cho các routes cụ thể
3. **Wind Index**: Peak wind months (hurricane/typhoon season: 7-10)
4. **Temperature Deviation**: Extreme weather months
5. **Seasonal Volatility**: Routes với high seasonal variation (Arctic, Baltic)
6. **ENSO Influence**: El Niño/La Niña multipliers

**Methods quan trọng:**
- `compute_storm_probability()`: Tính xác suất bão
- `compute_rainfall_intensity()`: Tính cường độ mưa
- `compute_wind_index()`: Tính chỉ số gió
- `compute_temperature_deviation()`: Tính độ lệch nhiệt độ
- `compute_seasonal_volatility()`: Tính biến động theo mùa
- `compute_enso_influence()`: Tính ảnh hưởng ENSO
- `compute_climate_risk()`: Kết hợp tất cả → overall climate risk (0-1)

**Output:** `ClimateRiskScore` object với:
- `overall_risk`: 0-1
- Individual components (storm_probability, rainfall_intensity, wind_index, etc.)
- `explanation`: Dict giải thích các components

**Weighted combination:**
- Storm: 30%
- Wind: 25%
- Rainfall: 20%
- Temperature: 10%
- Volatility: 15%
- Applied với ENSO multiplier

---

### 5. `network_model.py` - Mô Hình Rủi Ro Mạng Lưới

**Chức năng:**
- **Tính rủi ro liên quan đến network dependencies và propagation**
- Port centrality (betweenness centrality concept) - ports quan trọng có risk cao hơn nếu disrupted
- Carrier redundancy - carriers với network tốt có risk thấp hơn
- Upstream/downstream dependencies
- Disruption propagation factor

**Class chính:** `NetworkRiskModel`

**Components:**
1. **Port Centrality**: Centrality scores cho major ports (Singapore, Rotterdam, Shanghai, etc.)
   - High centrality = high disruption impact
   - Take maximum của POL và POD
2. **Carrier Redundancy**: Network redundancy của carriers
   - Major carriers (Maersk, MSC, COSCO) có redundancy tốt = risk thấp
   - Unknown carriers = risk cao hơn
3. **Upstream Dependency**: Supply chain dependencies trước shipment
4. **Downstream Dependency**: Distribution network sau arrival
5. **Propagation Factor**: Khả năng disruption lan truyền

**Methods quan trọng:**
- `compute_port_centrality()`: Tính centrality risk của ports
- `compute_carrier_redundancy()`: Tính redundancy risk của carrier
- `compute_upstream_dependency()`: Tính upstream dependency risk
- `compute_downstream_dependency()`: Tính downstream dependency risk
- `compute_propagation_factor()`: Tính propagation factor
- `compute_network_risk()`: Kết hợp tất cả → overall network risk (0-1)

**Port Centrality Database:**
- Top tier (0.9+): Singapore, Rotterdam, Shanghai, Hong Kong, Los Angeles
- Second tier (0.65-0.75): Busan, Dubai, Hamburg, Antwerp, Long Beach
- Default: 0.5

**Carrier Redundancy Scores:**
- Major carriers: 0.25-0.35 (low risk = high redundancy)
- Default: 0.60 (higher risk = lower redundancy)

**Output:** `NetworkRiskScore` object với:
- `overall_risk`: 0-1
- Individual components (port_centrality, carrier_redundancy, propagation_factor, etc.)
- `explanation`: Dict giải thích

**Weighted combination:**
- Port Centrality: 25%
- Carrier Redundancy: 20%
- Upstream Dependency: 15%
- Downstream Dependency: 15%
- Propagation: 25%

---

### 6. `scoring.py` - Unified Risk Scoring

**Chức năng:**
- **Kết hợp tất cả các components thành điểm số cuối cùng (0-100)**
- Weighted fusion của FAHP-weighted TOPSIS, Climate, Network, và Operational risk
- Apply non-linear scaling để emphasize high-risk scenarios
- Missing data penalty cho các fields quan trọng thiếu

**Class chính:** `UnifiedRiskScoring`

**Weight Fusion Coefficients:**
- FAHP-weighted TOPSIS: 45%
- Climate Risk: 20%
- Network Risk: 20%
- Operational Risk: 15%

**Methods quan trọng:**
- `compute_fahp_weighted_component()`: Tính FAHP-weighted component từ TOPSIS score
- `compute_operational_risk()`: Tính operational risk từ inputs (transit time, cargo value, container match, priority, packaging)
- `compute_missing_data_penalty()`: Penalty 10% per missing critical field
- `apply_nonlinear_scaling()`: Exponential scaling để emphasize high-risk
- `compute_unified_score()`: Main method - kết hợp tất cả → final score 0-100

**Non-linear Scaling:**
- Lower risk (<0.5): gradual scaling (x^0.9)
- Higher risk (≥0.5): exponential emphasis (x^0.7)

**Critical Fields:** route, pol, pod, cargo_value

**Output:** `RiskScoreComponents` object với:
- `fahp_weighted`: 0-1
- `climate_risk`: 0-1
- `network_risk`: 0-1
- `operational_risk`: 0-1
- `missing_data_penalty`: 0-1
- `final_score`: 0-100

---

### 7. `risk_profile.py` - Risk Profile Builder

**Chức năng:**
- **Xây dựng comprehensive risk profile** với probability × severity matrix
- Determine risk level (Low/Medium/High/Critical) từ score
- Compute probability và severity levels
- Build 3×3 impact matrix (9 quadrants)
- Identify key risk drivers
- Generate explanations và recommendations

**Class chính:** `RiskProfileBuilder`

**Risk Level Thresholds:**
- Low: 0-30
- Medium: 30-60
- High: 60-80
- Critical: 80-100

**Probability Thresholds:**
- Low: 0-0.4
- Medium: 0.4-0.7
- High: 0.7-1.0

**Severity Thresholds:**
- Low: 0-40
- Medium: 40-70
- High: 70-100

**Impact Matrix (3×3):**
```
         Severity
      Low  Med  High
P Low  1    2    3
r Medium 4    5    6
o High  7    8    9
b
```

**Methods quan trọng:**
- `determine_risk_level()`: Map score → RiskLevel enum
- `determine_probability()`: Tính probability level (có adjust cho variance)
- `determine_severity()`: Tính severity level (có adjust cho cargo value)
- `compute_quadrant()`: Map probability × severity → quadrant (1-9)
- `get_quadrant_description()`: Description cho từng quadrant
- `identify_key_drivers()`: Top N risk drivers
- `generate_explanation()`: Generate explanation points
- `generate_recommendations()`: Generate mitigation recommendations
- `build_profile()`: Main method - build complete RiskProfile

**Output:** `RiskProfile` object với:
- `score`: 0-100
- `level`: "Low"/"Medium"/"High"/"Critical"
- `confidence`: 0-1
- `explanation`: List of explanation strings
- `factors`: Dict of risk factors
- `matrix`: ImpactMatrix (probability, severity, quadrant, description)
- `drivers`: List of key drivers
- `recommendations`: List of recommendations

---

### 8. `normalization.py` - Normalization Utilities

**Chức năng:**
- **Các hàm utility để normalize data** về range 0-1
- Hỗ trợ các methods: min-max, z-score, vector normalization
- Clamp values, smooth step functions

**Functions:**
- `min_max_normalize()`: Min-max normalization (0-1 range), có reverse option
- `z_score_normalize()`: Z-score normalization với sigmoid mapping
- `normalize_matrix()`: Normalize matrix (cho TOPSIS) - min_max hoặc vector method
- `normalize_dict()`: Normalize dictionary của values
- `clamp()`: Clamp value giữa min và max
- `smooth_step()`: Smooth interpolation function

**Sử dụng:** Được dùng bởi TOPSIS, scoring, và các modules khác để normalize inputs.

---

### 9. `llm_reasoner.py` - LLM Reasoner

**Chức năng:**
- **Tạo natural language explanations** và reasoning cho risk assessments
- Có thể dùng LLM (Anthropic Claude) hoặc deterministic fallback
- Generate explanations, key drivers, suggestions, business justification
- Region-aware và language support (vi, en, zh)

**Class chính:** `LLMReasoner`

**Modes:**
1. **LLM Mode**: Sử dụng Anthropic Claude API (nếu có API key)
2. **Deterministic Mode**: Fallback logic khi LLM không available

**Methods quan trọng:**
- `generate_reasoning_deterministic()`: Deterministic explanation generation
- `generate_reasoning_llm()`: LLM-based generation (Anthropic Claude)
- `generate_reasoning()`: Main method - tự chọn LLM hoặc deterministic
- `generate_scenario_explanation()`: Explain scenario comparisons
- `generate_region_reasoning()`: Region-aware reasoning với translation

**Output:** `LLMReasoningResult` object với:
- `explanation`: Main explanation text
- `key_drivers`: List of top risk drivers
- `confidence_score`: 0-1
- `suggestions`: List of mitigation suggestions
- `business_justification`: Executive-friendly justification

**Region-specific insights:**
- SEA: Southwest monsoon patterns
- CN: Golden Week congestion spikes
- US: ILWU labor negotiations
- EU: Port strikes patterns

---

### 10. `__init__.py` - Package Exports

**Chức năng:**
- **Package initialization file**
- Export tất cả public classes và functions
- Define `__all__` list

**Exports:**
- `RiskPipeline`
- `RiskProfile`, `RiskProfileBuilder`
- `UnifiedRiskScoring`
- `FAHPSolver`
- `TOPSISSolver`
- `ClimateRiskModel`
- `NetworkRiskModel`
- `LLMReasoner`

---

## CẤU TRÚC DỮ LIỆU

### Input: Shipment Data
```python
{
    "route": str,              # Route identifier
    "pol": str,                # Port of Loading
    "pod": str,                # Port of Discharge
    "carrier": str,            # Carrier name
    "etd": str,                # Estimated Time of Departure
    "eta": str,                # Estimated Time of Arrival
    "cargo_value": float,      # Cargo value in USD
    "cargo_type": str,         # Type of cargo
    "transit_time": float,     # Transit time in days
    "container_type": str,     # Container type
    "priority": str,           # "critical", "high", "standard", "low"
    "packaging_quality": float,  # 0-1
    "container_match": float,    # 0-1
    "carrier_rating": float,     # 0-1
}
```

### Output: Risk Assessment Result
```python
{
    "risk_score": float,           # 0-100
    "risk_level": str,             # "Low", "Medium", "High", "Critical"
    "confidence": float,           # 0-1
    "profile": {
        "score": float,
        "level": str,
        "confidence": float,
        "explanation": List[str],
        "factors": Dict[str, float],
        "matrix": {
            "probability": str,
            "severity": str,
            "quadrant": int,
            "description": str,
        },
    },
    "drivers": List[str],          # Key risk drivers
    "recommendations": List[str],   # Mitigation suggestions
    "reasoning": {
        "explanation": str,
        "business_justification": str,
    },
    "components": {
        "fahp_weighted": float,
        "climate_risk": float,
        "network_risk": float,
        "operational_risk": float,
        "missing_data_penalty": float,
    },
    "details": {
        "climate": {...},
        "network": {...},
        "fahp_weights": Dict[str, float],
        "topsis_score": float,
    },
    "region": {
        "code": str,
        "name": str,
        "config": {...},
    },
}
```

---

## THUẬT TOÁN CHI TIẾT

### 1. FAHP Weight Calculation

**Bước 1:** Build pairwise comparison matrix
- Scale 1-9 (Saaty scale)
- Convert thành fuzzy triangular numbers (l, m, u)

**Bước 2:** Geometric mean method
```
GM_i = (∏(a_ij))^(1/n)  for each row i
```

**Bước 3:** Normalize fuzzy weights
```
W_i = GM_i / (∑GM_j)
```

**Bước 4:** Defuzzification (centroid method)
```
crisp_weight = (l + 2m + u) / 4
```

**Bước 5:** Check consistency ratio
```
CR = CI / RI
CR < 0.1 → acceptable
```

### 2. TOPSIS Score Calculation

**Bước 1:** Normalize decision matrix
```
r_ij = x_ij / √(∑x_kj²)  (vector normalization)
```

**Bước 2:** Apply weights
```
v_ij = w_j * r_ij
```

**Bước 3:** Find ideal solutions
```
A+ = (max v_i1, max v_i2, ..., max v_im) for maximize criteria
     (min v_i1, min v_i2, ..., min v_im) for minimize criteria
A- = opposite of A+
```

**Bước 4:** Calculate distances
```
d+ = √(∑(v_ij - A+j)²)
d- = √(∑(v_ij - A-j)²)
```

**Bước 5:** Closeness coefficient
```
CC = d- / (d+ + d-)
```

### 3. Unified Score Calculation

**Bước 1:** Weighted fusion
```
base_score = 
    fahp_weighted * 0.45 +
    climate_risk * 0.20 +
    network_risk * 0.20 +
    operational_risk * 0.15
```

**Bước 2:** Non-linear scaling
```
if base_score < 0.5:
    scaled = base_score^0.9
else:
    scaled = base_score^0.7
```

**Bước 3:** Apply missing data penalty
```
final_score = scaled * missing_penalty * 100
```

**Bước 4:** Clamp to 0-100
```
final_score = max(0, min(100, final_score))
```

---

## REGION-BASED ADJUSTMENTS

Engine hỗ trợ region-specific adjustments thông qua `RegionDetector`:

**Regions:**
- VN (Vietnam)
- SEA (Southeast Asia)
- CN (China)
- EU (Europe)
- US (United States)
- GLOBAL

**Region Config:**
```python
{
    "climate_weight": float,          # Multiplier for climate risk
    "congestion_weight": float,       # Multiplier for port congestion
    "strike_weight": float,           # Multiplier for strike risk
    "esg_weight": float,              # Multiplier for ESG risk
    "network_propagation_factor": float,
    "region_name": str,
    "characteristics": List[str],
}
```

**Adjustments:**
1. Climate và Network risks được nhân với region weights
2. FAHP weights được điều chỉnh theo region config
3. Final score được điều chỉnh với region-specific formula

---

## ERROR HANDLING & DEFENSIVE PROGRAMMING

Tất cả modules có defensive checks:

1. **None value handling**: Kiểm tra None trước khi gọi `.upper()` hoặc string operations
2. **Type validation**: Convert và validate types (float, string, etc.)
3. **Range clamping**: Clamp values về valid ranges (0-1, 0-100)
4. **Default values**: Fallback values khi data thiếu
5. **Exception handling**: Try-except blocks cho external APIs (LLM)

---

## PERFORMANCE CONSIDERATIONS

1. **FAHP**: O(n²) complexity cho n risk factors (thường n=6)
2. **TOPSIS**: O(n×m) cho n alternatives, m criteria (thường n=1)
3. **Climate Model**: O(1) - simple calculations
4. **Network Model**: O(1) - lookup-based với dictionary
5. **LLM Calls**: Async để không block pipeline (nếu dùng LLM)

**Overall Complexity:** O(1) với constants hợp lý, không có loops phức tạp.

---

## EXTENSIBILITY

Engine được thiết kế modular:

1. **Thêm risk factors mới**: Cập nhật `FAHPSolver.RISK_FACTORS`
2. **Thêm regions mới**: Extend `RegionDetector`
3. **Thay đổi weights**: Modify `UnifiedRiskScoring` weight coefficients
4. **Custom normalization**: Thêm methods vào `normalization.py`
5. **Custom models**: Implement interface tương tự Climate/Network models

---

*Tài liệu này mô tả chi tiết thuật toán và cấu trúc của RiskCast Engine v2. Để hiểu sâu hơn về implementation, vui lòng tham khảo code comments trong từng file.*



