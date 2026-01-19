# RISKCAST - PHÂN TÍCH TOÀN DIỆN THUẬT TOÁN & LUỒNG DỮ LIỆU

**Mục đích:** Trích xuất chính xác tất cả thuật toán, luồng xử lý và cấu trúc dữ liệu để phục vụ việc xây lại Results Page.

**Ngày phân tích:** 2024
**Phiên bản Engine:** v16.0 (Enterprise Risk Engine)
**Phiên bản Frontend:** v60 (Results), v20 (Input)

---

## 1) INPUT SOURCES (Backend → Frontend)

### 1.1 API Endpoint Chính

**Endpoint:** `POST /run_analysis` (trong `app/api.py`)

**Request Payload (Option A Schema):**
```json
{
  "transport_mode": "ocean_fcl|air_freight|rail_freight|road_truck|multimodal",
  "cargo_type": "electronics|textiles|food|chemicals|machinery",
  "route": "vn_us|vn_cn|vn_sg",
  "incoterm": "EXW|FCA|FAS|FOB|CFR|CIF|CPT|CIP|DAP|DPU|DDP",
  "container": "20ft|40ft|40ft_highcube|45ft|reefer",
  "packaging": "poor|fair|good|excellent",
  "priority": "low|standard|high|express",
  "packages": 0,
  "etd": "DD/MM/YYYY",
  "eta": "DD/MM/YYYY",
  "transit_time": 0.0,
  "cargo_value": 0.0,
  "distance": 0.0,
  "route_type": "direct|standard|complex|hazardous",
  "carrier_rating": 0.0,
  "weather_risk": 0.0,
  "port_risk": 0.0,
  "container_match": 0.0,
  "shipment_value": 0.0,
  "use_fuzzy": false,
  "use_forecast": false,
  "use_mc": false,
  "use_var": false,
  "ENSO_index": 0.0,
  "typhoon_frequency": 0.5,
  "sst_anomaly": 0.0,
  "port_climate_stress": 5.0,
  "climate_volatility_index": 5.0,
  "climate_tail_event_probability": 0.05,
  "ESG_score": 50.0,
  "climate_resilience": 5.0,
  "green_packaging": 5.0,
  "buyer": { ... },
  "seller": { ... },
  "priority_profile": "standard|fastest|cheapest|balanced",
  "priority_weights": { "speed": 40, "cost": 40, "risk": 20 }
}
```

### 1.2 Response Structure (Backend Output)

**File:** `app/core/services/risk_service.py` → `_transform_engine_output()`

**Response JSON Structure:**
```json
{
  "risk_score": 0.0-1.0,              // ✅ Dùng cho gauge chart
  "risk_level": "LOW|MODERATE|HIGH|CRITICAL",  // ✅ Dùng cho badge
  "expected_loss": 0,                 // ✅ Dùng cho financial summary (USD)
  "reliability": 0.0-1.0,              // ✅ Dùng cho reliability gauge
  "esg": 0.0-1.0,                      // ✅ Dùng cho ESG gauge
  "layers": [                          // ✅ Dùng cho radar chart, layer breakdown
    { "name": "Transport", "score": 0.5 },
    { "name": "Cargo", "score": 0.6 },
    { "name": "Route", "score": 0.4 },
    { "name": "Incoterm", "score": 0.5 },
    { "name": "Container", "score": 0.7 },
    { "name": "Packaging", "score": 0.5 },
    { "name": "Priority", "score": 0.6 },
    { "name": "Climate", "score": 0.5 }
  ],
  "risk_factors": [                    // ✅ Dùng cho risk drivers table
    {
      "name": "Route Complexity",
      "score": 4.5,
      "weight": 0.08,
      "contribution": 0.36
    }
  ],
  "radar": {                           // ✅ Dùng cho radar chart
    "labels": ["Transport", "Cargo", ...],
    "values": [0.5, 0.6, ...]
  },
  "mc_samples": [],                    // ✅ Dùng cho Monte Carlo histogram
  "var": 0,                            // ✅ Dùng cho VaR metric (USD)
  "cvar": 0,                           // ✅ Dùng cho CVaR metric (USD)
  "financial_distribution": {          // ✅ Dùng cho loss distribution chart
    "distribution": [1000, 2000, ...],  // Array of USD losses
    "expected_loss_usd": 5000,
    "var_95_usd": 15000,
    "cvar_95_usd": 20000
  },
  "climate_hazard_index": 5.0,         // ✅ Dùng cho climate gauge
  "climate_var_metrics": {             // ✅ Dùng cho climate risk analysis
    "climate_var_95": 0.0,
    "climate_cvar_95": 0.0
  },
  "advanced_metrics": {                // ✅ Dùng cho advanced metrics panel
    "var_95": 0.0,
    "var_99": 0.0,
    "cvar_95": 0.0,
    "cvar_99": 0.0,
    "downside_deviation": 0.0,
    "std": 0.0,
    "skewness": 0.0,
    "kurtosis": 0.0,
    "median": 0.0,
    "delay_distribution": {
      "mean_delay_days": 0.0,
      "p95_delay_days": 0.0,
      "max_delay_days": 0.0
    },
    "climate_hazard_index": 5.0,
    "climate_var_metrics": {}
  },
  "scenario_analysis": {               // ✅ Dùng cho scenario comparison
    "base": { "risk": 0.5, "loss": 5000 },
    "optimistic": { "risk": 0.3, "loss": 2000 },
    "pessimistic": { "risk": 0.8, "loss": 15000 }
  },
  "forecast": {                        // ⚠️ Có thể thiếu dữ liệu
    "trend": "increasing|decreasing|stable",
    "confidence": 0.0-1.0
  },
  "priority_profile": "standard",       // ✅ Dùng cho priority gauge
  "priority_weights": {                // ✅ Dùng cho priority breakdown
    "speed": 40,
    "cost": 40,
    "risk": 20
  },
  "advanced_parameters": {             // ✅ Dùng cho advanced params display
    "distance": 0.0,
    "route_type": "standard",
    "carrier_rating": 0.0,
    "weather_risk": 0.0,
    "port_risk": 0.0,
    "container_match": 0.0,
    "shipment_value": 0.0
  },
  "climate_v14": {                     // ✅ Dùng cho climate inputs display
    "ENSO_index": 0.0,
    "typhoon_frequency": 0.5,
    "sst_anomaly": 0.0,
    "port_climate_stress": 5.0,
    "climate_volatility_index": 5.0,
    "climate_tail_event_probability": 0.05,
    "ESG_score": 50.0,
    "climate_resilience": 5.0,
    "green_packaging": 5.0
  },
  "buyer_seller_analysis": {            // ⚠️ Có thể thiếu nếu không có buyer/seller
    "seller_risk": 0.0,
    "buyer_risk": 0.0,
    "combined_risk": 0.0
  }
}
```

### 1.3 Field Mapping & Usage

| Field | Ý nghĩa | Dùng cho Chart? | Status |
|-------|---------|----------------|--------|
| `risk_score` | Overall risk (0-1) | ✅ Gauge chart | ✅ OK |
| `risk_level` | Risk classification | ✅ Badge | ✅ OK |
| `expected_loss` | Expected financial loss (USD) | ✅ Financial summary | ✅ OK |
| `reliability` | Transport reliability (0-1) | ✅ Reliability gauge | ✅ OK |
| `esg` | ESG score (0-1) | ✅ ESG gauge | ✅ OK |
| `layers` | 8 risk layer scores | ✅ Radar chart, layer breakdown | ✅ OK |
| `risk_factors` | Detailed risk factors with weights | ✅ Risk drivers table | ✅ OK |
| `radar.labels` | Layer names | ✅ Radar chart | ✅ OK |
| `radar.values` | Layer scores (0-1) | ✅ Radar chart | ✅ OK |
| `mc_samples` | Monte Carlo distribution samples | ✅ Histogram | ✅ OK |
| `var` | Value at Risk 95% (USD) | ✅ VaR metric | ✅ OK |
| `cvar` | Conditional VaR 95% (USD) | ✅ CVaR metric | ✅ OK |
| `financial_distribution` | Full loss distribution | ✅ Loss distribution chart | ✅ OK |
| `climate_hazard_index` | Climate Hazard Index (0-10) | ✅ Climate gauge | ✅ OK |
| `climate_var_metrics` | Climate-specific VaR | ✅ Climate risk panel | ✅ OK |
| `scenario_analysis` | Base/Optimistic/Pessimistic | ✅ Scenario comparison | ✅ OK |
| `forecast` | Trend forecast | ⚠️ Forecast chart | ⚠️ Có thể thiếu |
| `priority_profile` | Priority profile name | ✅ Priority gauge | ✅ OK |
| `priority_weights` | Speed/Cost/Risk weights | ✅ Priority breakdown | ✅ OK |
| `advanced_metrics` | Statistical metrics | ✅ Advanced metrics panel | ✅ OK |
| `buyer_seller_analysis` | Partner risk analysis | ⚠️ Partner risk panel | ⚠️ Có thể thiếu |

### 1.4 Fields Không Dùng / Thừa

- ❌ **Không có field nào bị thừa** - Tất cả fields đều có mục đích sử dụng
- ⚠️ **Fields có thể thiếu:**
  - `forecast` - Có thể trả về `{}` nếu engine không generate
  - `buyer_seller_analysis` - Chỉ có nếu input có buyer/seller data

---

## 2) CALCULATION PIPELINE (Backend)

### 2.1 Main Risk Calculation Flow

**File:** `app/core/engine/risk_engine_v16.py` → `EnterpriseRiskEngineV16.calculate_risk()`

**Pipeline Stages:**

```
1. Parse Enhanced Data
   ↓
2. Build Climate Variables → Calculate CHI (Climate Hazard Index)
   ↓
3. Build 13 Risk Layers
   ↓
4. Calculate Priority-Aware Weights (Fuzzy AHP + Entropy)
   ↓
5. Run Monte Carlo Simulation (50,000 iterations)
   ↓
6. Calculate Financial & Operational Metrics
   ↓
7. Generate Component Insights (Carrier, Port, Packing, Partner)
   ↓
8. Generate Executive Briefing & Recommendations
```

### 2.2 Risk Score Calculation

**Formula:** Weighted sum of risk layers with interaction effects

```python
# Step 1: Calculate base layer scores
layer_scores = {
    'route_complexity': calculate_route_risk(distance, route_type),
    'cargo_sensitivity': calculate_cargo_risk(cargo_type, cargo_value),
    'packaging_quality': normalize_score(10 - packaging_quality),  # Inverted
    'transport_reliability': calculate_transport_risk(transport_mode, carrier_rating),
    'weather_exposure': weather_risk,
    'priority_level': priority,
    'container_match': normalize_score(10 - container_match),  # Inverted
    'port_risk': port_risk
}

# Step 2: Calculate weights (Fuzzy AHP + Entropy)
weights = calculate_optimal_weights(layers, shipment_data)
adjusted_weights = adjust_weights_by_priority(weights, priority_profile)

# Step 3: Base risk (weighted sum)
base_risk = sum(layer_scores[layer] * weights[layer] for layer in layers)

# Step 4: Apply interaction effects
overall_risk = apply_conditional_amplification(base_risk, layer_scores)

# Step 5: Normalize to 0-10 scale
overall_risk = clip(overall_risk, 0, 10)

# Step 6: Convert to 0-1 for frontend
risk_score = overall_risk / 10.0
```

### 2.3 Port Risk Calculation

**File:** `app/core/engine/risk_scoring_engine.py` → `_calculate_port_risk()`

```python
PORT_RISK_DB = {
    'VNSGN': 55,  # Ho Chi Minh
    'VNHPH': 50,  # Hai Phong
    'CNYTN': 60,  # Yantian
    'CNSHA': 50,  # Shanghai
    'USLAX': 70,  # Los Angeles
    'USNYC': 55,  # New York
    'SGSIN': 25,  # Singapore
    'NLRTM': 30   # Rotterdam
}

def calculate_port_risk(pol, pod):
    pol_risk = PORT_RISK_DB.get(pol.upper(), 45)
    pod_risk = PORT_RISK_DB.get(pod.upper(), 45)
    avg_risk = (pol_risk * 0.4 + pod_risk * 0.6)  # POD weighted more
    return avg_risk
```

### 2.4 Carrier Risk Calculation

**File:** `app/core/engine/risk_scoring_engine.py` → `calculate_comprehensive_risk()`

```python
# Mode base score
MODE_RISK_SCORES = {
    'air_freight': 25,
    'sea_freight': 45,
    'rail': 40,
    'road': 50,
    'multimodal': 55
}

mode_base_score = MODE_RISK_SCORES.get(mode, 50)

# Adjust by carrier reliability
if carrier_reliability:
    mode_score = mode_base_score * (1 - (carrier_reliability - 50) / 100 * 0.3)
else:
    mode_score = mode_base_score

# Carrier performance score (inverse of reliability)
carrier_score = 100 - carrier_reliability if carrier_reliability else 50

# Adjust by priority
if priority == 'fastest':
    carrier_score *= 0.85  # Lower risk for fast priority
elif priority == 'cheapest':
    carrier_score *= 1.15  # Higher risk for cheap priority

carrier_risk = clip(carrier_score, 0, 100)
```

### 2.5 Weather Risk Calculation

**File:** `app/core/engine/risk_scoring_engine.py` → `_calculate_weather_risk()`

```python
def calculate_weather_risk(transport, cargo):
    risk_score = 30  # Base
    
    # Mode adjustment
    mode = transport.get('mode', '')
    if mode == 'sea_freight':
        risk_score += 15
    elif mode == 'air_freight':
        risk_score += 10
    elif mode == 'road':
        risk_score += 5
    
    # Cargo sensitivity
    sensitivity = cargo.get('sensitivity', '')
    if sensitivity in ['temperature', 'perishable']:
        risk_score += 20
    
    # Seasonal adjustment (June-November = typhoon season)
    etd = transport.get('etd', '')
    if etd:
        month = parse_date(etd).month
        if 6 <= month <= 11:
            risk_score += 10
    
    return clip(risk_score, 0, 100)
```

### 2.6 ESG Risk Calculation

**File:** `app/core/services/risk_service.py` → `_transform_engine_output()`

```python
# ESG score from input (0-100 scale)
esg_raw = payload.get('ESG_score', 50.0)

# Convert to 0-1 for frontend
esg = round(esg_raw / 100.0, 2)

# Also includes:
# - climate_resilience (0-10)
# - green_packaging (0-10)
```

### 2.7 Financial Risk (Expected Loss, VaR, CVaR)

**File:** `app/core/engine/risk_engine_base.py` → `FinancialCalculator`

```python
# Expected Loss Calculation
expected_loss_pct = (overall_risk / 10) ** 1.5 * 0.30  # Non-linear scaling
expected_loss = shipment_value * expected_loss_pct

# Monte Carlo Simulation (50,000 iterations)
risk_distribution = mc_engine.simulate_risk_distribution(
    layers, weights, base_context, climate_vars=climate_vars
)

# Financial Distribution
financial_dist = financial_calculator.calculate_financial_distribution(
    risk_distribution, shipment_value
)

# VaR/CVaR Calculation
var_95 = percentile(risk_distribution, 95)  # 95th percentile
cvar_95 = mean(risk_distribution[risk_distribution >= var_95])  # Conditional mean
```

### 2.8 Composite Risk (Overall Risk Score)

**Formula:** Weighted aggregation with interaction effects

```python
# 1. Base weighted sum
base_risk = Σ(layer_score[i] * weight[i]) for i in layers

# 2. Interaction effects (conditional amplification)
# If multiple high-risk layers → amplify overall risk
if any(score > 7.0 for score in layer_scores.values()):
    amplification_factor = 1.0 + (count_high_risk_layers / total_layers) * 0.15
    overall_risk = base_risk * amplification_factor
else:
    overall_risk = base_risk

# 3. Climate adjustment
chi = climate_vars.calculate_CHI()  # Climate Hazard Index (0-10)
climate_impact = (chi / 10.0) * 0.3  # Max 30% impact
overall_risk = overall_risk * (1 + climate_impact)

# 4. Normalize to 0-10, then convert to 0-1
overall_risk = clip(overall_risk, 0, 10)
risk_score = overall_risk / 10.0
```

---

## 3) FRONTEND STATE (JS)

### 3.1 RISKCAST_STATE Structure

**File:** `app/api.py` → `build_riskcast_state_from_shipment()`

**Structure:**
```javascript
window.RISKCAST_STATE = {
  transport: {
    mode: "Ocean|Air|Rail|Road",
    pol: "Port of Loading Name",
    polCode: "POL",
    pod: "Port of Discharge Name",
    podCode: "POD",
    totalDistance: "5000 km",
    segmentCount: 1,
    tradeLane: "VN-US"
  },
  cargo: {
    commodity: "Electronics",
    weight: "1000 kg",
    volume: "5 CBM",
    containerType: "40ft",
    hsCode: "8517.12"
  },
  parties: {
    shipper: "Seller Name",
    consignee: "Buyer Name",
    forwarder: "Forwarder Name"
  },
  risk: {
    score: 7.2,                    // 0-10 scale
    weatherRisk: "MODERATE",
    congestion: "LOW",
    delayProb: "15%"
  },
  routeLegs: [
    {
      from: "Ho Chi Minh",
      fromCode: "SGN",
      to: "Los Angeles",
      toCode: "LAX",
      distance: "12000 km",
      step: 1,
      lat1: 10.8231,
      lon1: 106.6297,
      lat2: 34.0522,
      lon2: -118.2437
    }
  ]
}
```

### 3.2 RISKCAST_RESULTS_V2 (Results Data)

**File:** `app/static/js/pages/results/results_state_v60.js`

**Storage:** `localStorage.getItem('RISKCAST_RESULTS_V2')`

**Structure:**
```javascript
{
  shipment_id: "",
  route: "SGN → LAX",
  pol: "SGN",
  pod: "LAX",
  carrier: "",
  etd: "",
  eta: "",
  profile: {
    score: 0.5,              // 0-1 scale
    level: "MODERATE",
    confidence: 0.85,
    matrix: {
      probability: 0.3,
      severity: 0.6,
      quadrant: "HIGH_SEVERITY",
      description: "..."
    }
  },
  key_drivers: [
    { name: "Route Complexity", score: 0.6, weight: 0.08 }
  ],
  recommendations: [],
  details: {
    components: {
      fahp_weighted: 0.4,
      climate_risk: 0.3,
      network_risk: 0.2,
      operational_risk: 0.1,
      missing_data_penalty: 0.0
    },
    climate: {
      storm_probability: 0.15,
      wind_index: 5.2,
      rainfall_intensity: 3.8
    },
    network: {
      port_centrality: 0.7,
      carrier_redundancy: 0.5,
      propagation_factor: 0.3
    },
    fahp_weights: {
      route_complexity: 0.12,
      cargo_sensitivity: 0.15,
      ...
    },
    topsis_score: 0.65
  },
  region: {
    code: "VN-US",
    name: "Vietnam - United States",
    config: {
      climate_weight: 0.25,
      congestion_weight: 0.20,
      strike_weight: 0.15,
      esg_weight: 0.10
    }
  }
}
```

### 3.3 State Update Flow

**1. Input Page → RISKCAST_STATE:**
- User fills form → `StateManager.setState()`
- Auto-sync to `RISKCAST_STATE` via `syncToRISKCAST_STATE()`
- Stored in `localStorage.setItem('RISKCAST_STATE', ...)`

**2. API Call → Results:**
- Submit form → `POST /run_analysis`
- Backend calculates → Returns JSON
- Frontend stores: `localStorage.setItem('RISKCAST_RESULTS_V2', JSON.stringify(result))`

**3. Results Page Load:**
- `results_state_v60.js` reads `RISKCAST_RESULTS_V2`
- Parses to view-model structure
- Exposes as `window.RISKCAST_RESULTS_VIEWMODEL`

### 3.4 Keys Dùng cho Charts

| Key | Chart Usage | Status |
|-----|-------------|--------|
| `profile.score` | Global risk gauge | ✅ OK |
| `profile.level` | Risk level badge | ✅ OK |
| `details.components.*` | Components breakdown bar chart | ✅ OK |
| `details.fahp_weights` | FAHP weights radar chart | ✅ OK |
| `key_drivers` | Risk drivers table | ✅ OK |
| `details.climate.*` | Climate metrics panel | ✅ OK |
| `details.network.*` | Network metrics panel | ✅ OK |

### 3.5 Keys Không Dùng / Sai Format

- ⚠️ **`RISKCAST_EVALUATE_V1`** - Legacy format, chỉ dùng làm fallback
- ⚠️ **`forecast`** - Có thể thiếu trong v2 results
- ⚠️ **`buyer_seller_analysis`** - Chỉ có nếu input có buyer/seller

---

## 4) CHART DATA MODEL

### 4.1 Global Risk Gauge (Doughnut Chart)

**File:** `app/static/js/pages/results/results_charts_v60.js` → `createGlobalGauge()`

**Data Source:**
```javascript
const score = viewModel.score.risk_score;  // 0-1 scale
const remaining = 100 - (score * 100);    // Convert to 0-100

// Chart Data
{
  datasets: [{
    data: [score * 100, remaining],
    backgroundColor: [color, 'rgba(15, 23, 42, 0.3)']
  }]
}
```

**Format Expect:** `risk_score` (0-1) từ `viewModel.score.risk_score`
**Status:** ✅ Đúng format

### 4.2 Components Breakdown Bar Chart

**Data Source:**
```javascript
const comp = viewModel.components;

// Chart Data
{
  labels: ['FAHP', 'Climate', 'Network', 'Operational', 'Data Penalty'],
  datasets: [{
    data: [
      comp.fahp_weighted * 100,      // Convert to percentage
      comp.climate_risk * 100,
      comp.network_risk * 100,
      comp.operational_risk * 100,
      comp.missing_data_penalty * 100
    ]
  }]
}
```

**Format Expect:** `components.*` (0-1) từ `viewModel.details.components`
**Status:** ✅ Đúng format

### 4.3 FAHP Weights Radar Chart

**Data Source:**
```javascript
const weights = viewModel.details.fahp_weights;

// Chart Data
{
  labels: Object.keys(weights).map(k => formatLabel(k)),
  datasets: [{
    data: Object.values(weights).map(v => v * 100)  // Convert to percentage
  }]
}
```

**Format Expect:** `fahp_weights` object từ `viewModel.details.fahp_weights`
**Status:** ⚠️ Có thể thiếu nếu engine không trả về

### 4.4 Risk Layers Radar Chart

**Data Source:**
```javascript
// From backend response
const radar = response.radar;

// Chart Data
{
  labels: radar.labels,  // ["Transport", "Cargo", ...]
  datasets: [{
    data: radar.values.map(v => v * 100)  // Convert 0-1 to 0-100
  }]
}
```

**Format Expect:** `radar.labels` và `radar.values` (0-1) từ backend response
**Status:** ✅ Đúng format

### 4.5 Monte Carlo Distribution Histogram

**Data Source:**
```javascript
// From backend response
const mc_samples = response.mc_samples;  // Array of USD losses

// Chart Data
{
  labels: generateBins(mc_samples),  // Bin ranges
  datasets: [{
    data: countByBin(mc_samples)     // Frequency per bin
  }]
}
```

**Format Expect:** `mc_samples` array từ `response.mc_samples`
**Status:** ✅ Đúng format

### 4.6 Financial Loss Distribution Chart

**Data Source:**
```javascript
// From backend response
const fin_dist = response.financial_distribution;

// Chart Data
{
  labels: generateBins(fin_dist.distribution),
  datasets: [{
    data: countByBin(fin_dist.distribution),
    // Also show VaR/CVaR lines
    annotations: {
      var_95: fin_dist.var_95_usd,
      cvar_95: fin_dist.cvar_95_usd
    }
  }]
}
```

**Format Expect:** `financial_distribution.distribution` array từ backend
**Status:** ✅ Đúng format

### 4.7 Scenario Comparison Chart

**Data Source:**
```javascript
// From backend response
const scenarios = response.scenario_analysis;

// Chart Data
{
  labels: ['Base', 'Optimistic', 'Pessimistic'],
  datasets: [{
    label: 'Risk Score',
    data: [
      scenarios.base.risk * 100,
      scenarios.optimistic.risk * 100,
      scenarios.pessimistic.risk * 100
    ]
  }, {
    label: 'Expected Loss (USD)',
    data: [
      scenarios.base.loss,
      scenarios.optimistic.loss,
      scenarios.pessimistic.loss
    ]
  }]
}
```

**Format Expect:** `scenario_analysis` object từ backend
**Status:** ✅ Đúng format

---

## 5) DATA FLOW GRAPH

```
┌─────────────────────────────────────────────────────────────────┐
│ INPUT PAGE (Frontend)                                           │
│ - User fills form (transport, cargo, seller, buyer)            │
│ - StateManager.setState() → syncToRISKCAST_STATE()              │
│ - localStorage.setItem('RISKCAST_STATE', ...)                    │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ API CALL                                                         │
│ POST /run_analysis                                               │
│ Payload: { transport_mode, cargo_type, route, ... }             │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ BACKEND MAPPING (risk_service.py)                                │
│ _map_shipment_to_engine()                                        │
│ - Option A schema → Engine input format                          │
│ - Map transport_mode → 'sea'|'air'|'rail'|'road'                │
│ - Map cargo_type → 'fragile'|'standard'|'perishable'             │
│ - Extract climate variables                                      │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ RISK ENGINE v16 (risk_engine_v16.py)                             │
│ EnterpriseRiskEngineV16.calculate_risk()                        │
│                                                                   │
│ 1. Parse Enhanced Data                                            │
│ 2. Build Climate Variables → CHI                                 │
│ 3. Build 13 Risk Layers                                          │
│    - route_complexity                                             │
│    - cargo_sensitivity                                            │
│    - packaging_quality                                           │
│    - transport_reliability                                       │
│    - weather_exposure                                             │
│    - priority_level                                              │
│    - container_match                                             │
│    - port_risk                                                   │
│ 4. Calculate Weights (Fuzzy AHP + Entropy)                       │
│ 5. Run Monte Carlo (50,000 iterations)                          │
│ 6. Calculate Metrics (VaR, CVaR, Expected Loss)                 │
│ 7. Generate Insights (Carrier, Port, Packing, Partner)          │
│ 8. Generate AI Summary                                           │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ OUTPUT TRANSFORMATION (risk_service.py)                          │
│ _transform_engine_output()                                       │
│ - Engine output (0-10 scale) → Frontend format (0-1 scale)       │
│ - Build layers array                                             │
│ - Build radar data                                               │
│ - Extract financial distribution                                 │
│ - Format scenario analysis                                       │
│ - Add climate inputs snapshot                                    │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ API RESPONSE JSON                                                │
│ {                                                                │
│   risk_score: 0.5,                                               │
│   risk_level: "MODERATE",                                        │
│   expected_loss: 5000,                                           │
│   layers: [...],                                                 │
│   radar: { labels: [...], values: [...] },                      │
│   mc_samples: [...],                                             │
│   var: 15000,                                                    │
│   cvar: 20000,                                                   │
│   financial_distribution: {...},                                │
│   scenario_analysis: {...},                                     │
│   ...                                                            │
│ }                                                                │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND STORAGE                                                 │
│ localStorage.setItem('RISKCAST_RESULTS_V2', JSON.stringify(...)) │
│                                                                   │
│ Also update:                                                     │
│ - localStorage.setItem('RISKCAST_STATE', ...)                    │
│ - window.LAST_RESULT = response                                  │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ RESULTS PAGE (Frontend)                                          │
│ results_state_v60.js                                             │
│ - Load from localStorage.getItem('RISKCAST_RESULTS_V2')          │
│ - Parse to view-model structure                                  │
│ - Expose as window.RISKCAST_RESULTS_VIEWMODEL                    │
│                                                                   │
│ results_charts_v60.js                                            │
│ - Read viewModel                                                 │
│ - Create Chart.js instances                                      │
│ - Bind data to charts                                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6) PROBLEMS LIST

### 6.1 Thiếu Dữ Liệu

1. **`forecast` object có thể rỗng**
   - **Vị trí:** `response.forecast`
   - **Vấn đề:** Engine có thể không generate forecast nếu `use_forecast=false`
   - **Giải pháp:** Frontend cần check `if (forecast && Object.keys(forecast).length > 0)`

2. **`buyer_seller_analysis` thiếu nếu không có buyer/seller input**
   - **Vị trí:** `response.buyer_seller_analysis`
   - **Vấn đề:** Chỉ có khi input có `buyer` và `seller` objects
   - **Giải pháp:** Frontend cần check existence trước khi render

3. **`fahp_weights` có thể thiếu trong một số trường hợp**
   - **Vị trí:** `viewModel.details.fahp_weights`
   - **Vấn đề:** Engine v2 có thể không trả về nếu không dùng FAHP
   - **Giải pháp:** Chart code đã có check `if (!weights || Object.keys(weights).length === 0)`

### 6.2 Format Sai

1. **`risk_score` scale inconsistency**
   - **Vấn đề:** Backend trả về 0-1, nhưng một số code expect 0-100
   - **Vị trí:** `results_charts_v60.js` → `createGlobalGauge()` đã convert đúng
   - **Status:** ✅ Đã fix

2. **`layers` score scale**
   - **Vấn đề:** Backend trả về 0-1, nhưng radar chart cần 0-100
   - **Vị trí:** `results_charts_v60.js` → Radar chart code
   - **Status:** ✅ Đã convert đúng

### 6.3 Thuật Toán Chưa Đồng Bộ

1. **Risk level classification có thể khác nhau giữa engines**
   - **Vấn đề:** Engine v16 vs v21 có thể classify risk level khác nhau
   - **Giải pháp:** Standardize risk level thresholds

2. **Weight calculation methods**
   - **Vấn đề:** Engine v16 dùng Fuzzy AHP + Entropy, nhưng v21 dùng fixed weights
   - **Giải pháp:** Đảm bảo frontend handle cả hai cases

### 6.4 Fields Rác

- ❌ **Không có fields rác** - Tất cả fields đều có mục đích

### 6.5 Logic Chồng Chéo

1. **Multiple state storage locations**
   - **Vấn đề:** Data được lưu ở nhiều nơi:
     - `localStorage.RISKCAST_STATE`
     - `localStorage.RISKCAST_RESULTS_V2`
     - `localStorage.RISKCAST_EVALUATE_V1` (legacy)
     - `window.LAST_RESULT`
   - **Giải pháp:** Consolidate vào một source of truth

2. **View-model parsing có nhiều fallback paths**
   - **Vấn đề:** `results_state_v60.js` có nhiều parse functions (v2, v1, fallback)
   - **Giải pháp:** Standardize response format từ backend

---

## 7) WHAT DATA IS MISSING FOR A GOOD RESULTS PAGE?

### 7.1 Đề Xuất Thêm Bảng Dữ Liệu

1. **Risk Timeline / Journey Map**
   - **Dữ liệu cần:** 
     - Các milestones trong shipment journey
     - Risk score tại mỗi milestone
     - Delay probability tại mỗi stage
   - **Nguồn:** Cần engine tính toán theo route segments

2. **Comparative Analysis Table**
   - **Dữ liệu cần:**
     - So sánh với shipments tương tự (historical)
     - Benchmark scores (industry average)
   - **Nguồn:** Cần database historical shipments

3. **Mitigation Actions Table**
   - **Dữ liệu cần:**
     - List of recommended actions
     - Expected risk reduction per action
     - Cost per action
     - Priority ranking
   - **Nguồn:** Engine đã có `recommendations`, nhưng cần expand

### 7.2 Mỗi Biểu Đồ Nên Dùng Data Nào

1. **Risk Trend Chart (Time Series)**
   - **Dữ liệu cần:** Risk score over time (nếu có historical data)
   - **Hiện tại:** ❌ Không có
   - **Đề xuất:** Thêm endpoint `/risk/history?shipment_id=...`

2. **Geographic Risk Heatmap**
   - **Dữ liệu cần:** Risk scores by geographic region
   - **Hiện tại:** ❌ Không có
   - **Đề xuất:** Engine tính risk cho từng route segment

3. **Cost-Benefit Analysis Chart**
   - **Dữ liệu cần:** 
     - Cost of mitigation actions
     - Expected risk reduction
     - ROI calculation
   - **Hiện tại:** ⚠️ Có một phần trong `recommendations`
   - **Đề xuất:** Expand `recommendations` với cost/benefit data

### 7.3 Thuật Toán Cần Bổ Sung

1. **Delay Prediction Model**
   - **Hiện tại:** Có `delay_probability` và `delay_days_estimate`
   - **Thiếu:** Confidence interval, distribution curve
   - **Đề xuất:** Expand `delay_distribution` với full PDF

2. **Sensitivity Analysis**
   - **Hiện tại:** ❌ Không có
   - **Đề xuất:** Tính toán impact của thay đổi từng input parameter

3. **Correlation Analysis**
   - **Hiện tại:** Có `layer_interactions`
   - **Thiếu:** Correlation matrix giữa các risk factors
   - **Đề xuất:** Thêm correlation matrix vào `advanced_metrics`

4. **Confidence Scoring**
   - **Hiện tại:** Có `confidence` trong profile
   - **Thiếu:** Confidence breakdown theo từng metric
   - **Đề xuất:** Thêm `confidence_metrics` object

---

## 8) SUMMARY & RECOMMENDATIONS

### 8.1 Data Completeness Score

- ✅ **Core Metrics:** 100% (risk_score, risk_level, expected_loss)
- ✅ **Layer Scores:** 100% (8 layers với scores)
- ✅ **Financial Metrics:** 100% (VaR, CVaR, expected_loss)
- ⚠️ **Scenario Analysis:** 90% (có thể thiếu forecast)
- ⚠️ **Partner Analysis:** 70% (chỉ có nếu có buyer/seller input)
- ✅ **Climate Metrics:** 100% (CHI, climate_var_metrics)

### 8.2 Critical Issues to Fix

1. **Standardize risk_score scale** - ✅ Đã fix (backend trả về 0-1, frontend convert)
2. **Handle missing forecast data** - ⚠️ Cần thêm null checks
3. **Consolidate state storage** - ⚠️ Cần refactor để có single source of truth

### 8.3 Recommended Enhancements

1. **Add delay distribution chart** - Hiển thị full PDF của delay days
2. **Add sensitivity analysis panel** - Show impact của thay đổi parameters
3. **Add comparative benchmarks** - So sánh với industry average
4. **Expand recommendations** - Thêm cost/benefit analysis

---

**Kết thúc phân tích**
e