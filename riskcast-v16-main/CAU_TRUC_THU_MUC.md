# 📁 BÁO CÁO CẤU TRÚC THƯ MỤC RISKCAST

**Ngày tạo:** 28/12/2025  
**Phiên bản:** v16  
**Mô tả:** Báo cáo chi tiết về cấu trúc thư mục hiện tại của hệ thống RISKCAST

---

## 📊 TỔNG QUAN

RISKCAST là một hệ thống đánh giá rủi ro logistics sử dụng AI, được xây dựng với:
- **Backend:** FastAPI (Python)
- **Frontend:** HTML/CSS/JavaScript (Jinja2 templates)
- **Database:** MySQL (với hỗ trợ memory store)
- **AI:** Anthropic Claude API

---

## 🌳 CẤU TRÚC THƯ MỤC CHÍNH

```
riskcast-v16-main/
├── 📁 app/                      # Thư mục chính chứa application code
├── 📁 assets/                   # Assets tổng quát (34 PNG files)
├── 📁 components/               # React/JSX components (5 files)
├── 📁 data/                     # Dữ liệu scenarios
├── 📁 dist/                     # Build output (CSS/JS bundles)
├── 📁 files/                    # File storage
├── 📁 logs/                     # Log files
├── 📁 pages/                    # React pages
├── 📁 riskcast_v35/             # Module v35 (cấu trúc độc lập)
├── 📁 riskcast-dashboard/       # Next.js dashboard application
├── 📁 riskcast-v16-main/        # Nested folder (có thể là duplicate/backup)
├── 📁 src/                      # Source code cho frontend (Vue/React)
├── 📁 static/                   # Static files tổng quát
├── 📄 Configuration files       # Config files (.json, .js, .ts)
└── 📄 Entry scripts             # run.py, dev_run.py, etc.
```

---

## 📂 CHI TIẾT CÁC THƯ MỤC

### 1. `app/` - Application Core

Thư mục chính chứa toàn bộ logic của ứng dụng FastAPI.

#### 1.1 `app/api/` - API Endpoints
```
api/
├── __init__.py
├── router.py                    # Main API router
├── analysis_api.py              # Analysis endpoints
├── cargo_api.py                 # Cargo endpoints
├── insights_api.py              # Insights endpoints
├── kpi_api.py                   # KPI endpoints
├── shipment_api.py              # Shipment endpoints
├── transport_api.py             # Transport endpoints
└── v1/                          # API Version 1
    ├── __init__.py
    ├── routes.py                # General routes
    ├── ai_routes.py             # AI endpoints
    ├── analyze.py               # Analysis endpoint
    └── risk_routes.py           # Risk analysis endpoints
```

**Mục đích:** Xử lý tất cả các HTTP requests, routing và API responses.

#### 1.2 `app/core/` - Core Business Logic

Thư mục quan trọng nhất chứa logic nghiệp vụ và engine tính toán.

```
core/
├── engine/                      # Risk calculation engines
│   ├── risk_engine_v16.py      # Main risk engine v16
│   ├── risk_engine_base.py     # Base engine interface
│   ├── riskcast_engine_v21.py  # Engine v21
│   ├── ai_explanation_engine.py
│   ├── ai_explanation_ultra_v22.py
│   ├── esg_engine_v22.py       # ESG scoring engine
│   ├── global_freight_index_v22.py
│   ├── monte_carlo_v22.py      # Monte Carlo simulation
│   ├── risk_driver_tree_engine.py
│   ├── risk_scoring_engine.py
│   ├── shock_scenario_engine_v22.py
│   └── riskcast_validator.py
│
├── engine_v2/                   # Engine Version 2 (Hybrid AI)
│   ├── climate_model.py        # Climate risk model
│   ├── network_model.py        # Network risk model
│   ├── fahp.py                 # FAHP algorithm
│   ├── topsis.py               # TOPSIS algorithm
│   ├── normalization.py        # Data normalization
│   ├── risk_pipeline.py        # Main pipeline
│   ├── risk_profile.py         # Risk profile builder
│   ├── scoring.py              # Unified scoring
│   ├── llm_reasoner.py         # LLM explanation generator
│   └── ENGINE_DOCUMENTATION.md
│
├── services/                    # Business services
│   ├── risk_service.py         # Risk service layer
│   └── climate_service.py      # Climate data service
│
├── regions/                     # Regional models
│   ├── global_model.py         # Global risk model
│   ├── china_model.py          # China-specific model
│   ├── eu_model.py             # EU-specific model
│   ├── us_model.py             # US-specific model
│   ├── vn_model.py             # Vietnam-specific model
│   ├── sea_model.py            # Southeast Asia model
│   └── detector.py             # Region detector
│
├── scenario_engine/             # Scenario simulation
│   ├── delta_engine.py         # Delta calculations
│   ├── simulation_engine.py    # Simulation logic
│   ├── scenario_store.py       # Scenario storage
│   └── presets.py              # Predefined scenarios
│
├── report/                      # Report generation
│   ├── pdf_builder.py          # PDF report builder
│   ├── pdf_layouts.py          # PDF layouts
│   └── image_exporter.py       # Image export
│
├── utils/                       # Utility functions
│   ├── validators.py           # Data validation
│   ├── converters.py           # Data conversion
│   ├── cache.py                # Caching utilities
│   ├── sanitizer.py            # Input sanitization
│   ├── api_security.py         # API security
│   ├── auth.py                 # Authentication
│   ├── audit.py                # Audit logging
│   └── rate_limiter.py         # Rate limiting
│
├── i18n/                        # Internationalization
│   ├── translator.py           # Translation engine
│   └── languages/              # Language files
│       ├── en.json
│       ├── vi.json
│       └── ...
│
├── legacy/                      # Legacy code (v14/v15)
│   ├── riskcast_v14_5_climate_upgrade.py
│   ├── RISKCAST_v14_5_EXECUTIVE_SUMMARY.py
│   └── ...
│
├── build_helper.py             # Build utilities
├── engine_state.py             # Engine state management
├── engine_state_mysql.py       # MySQL engine state
├── risk_engine_v16.py          # Main risk engine
└── templates.py                # Template helpers
```

**Mục đích:** Chứa toàn bộ logic nghiệp vụ, thuật toán tính toán rủi ro, và các service layer.

#### 1.3 `app/models/` - Data Models
```
models/
├── base.py                     # Base model class
├── shipment.py                 # Shipment model
├── shipment_schema.py          # Shipment schema
├── cargo.py                    # Cargo model
├── transport.py                # Transport model
├── risk_analysis.py            # Risk analysis model
├── risk_module.py              # Risk module model
├── scenario.py                 # Scenario model
├── kpi.py                      # KPI model
└── kv_store.py                 # Key-value store model
```

**Mục đích:** Định nghĩa các data models và database schemas.

#### 1.4 `app/services/` - Service Layer
```
services/
├── analysis_service.py         # Analysis business logic
├── cargo_service.py            # Cargo business logic
├── insights_service.py         # Insights business logic
├── kpi_service.py              # KPI business logic
├── shipment_service.py         # Shipment business logic
└── transport_service.py        # Transport business logic
```

**Mục đích:** Service layer xử lý business logic giữa API và models.

#### 1.5 `app/templates/` - Jinja2 Templates
```
templates/
├── layouts/                    # Layout templates
│   ├── base.html              # Base layout
│   ├── base_production.html   # Production layout
│   └── input_layout.html      # Input page layout
│
├── components/                 # Reusable components
│   ├── topbar.html
│   ├── ai_panel.html
│   └── ...
│
├── input/                      # Input page templates
│   ├── input_v20.html
│   ├── input_modules_v30.html
│   └── ... (17 HTML files)
│
├── summary/                    # Summary templates
│
├── dashboard.html              # Dashboard page
├── home.html                   # Home page
└── home_v2000.html            # Home page v2000
```

**Mục đích:** HTML templates sử dụng Jinja2 để render pages.

#### 1.6 `app/static/` - Static Assets

##### CSS Structure (82 files)
```
static/css/
├── base/                       # Base styles
│   ├── variables.css          # CSS variables
│   ├── reset.css              # CSS reset
│   ├── typography.css         # Typography
│   └── mixins.css             # CSS mixins
│
├── layout/                     # Layout styles
│   ├── grid.css               # Grid system
│   ├── navbar.css             # Navigation bar
│   ├── sidebar.css            # Sidebar
│   └── layout_frame.css       # Layout frame
│
├── components/                 # Component styles
│   ├── buttons.css
│   ├── cards.css
│   ├── forms.css
│   ├── modals.css
│   ├── stats_card.css
│   ├── ai_panel.css
│   ├── progress_tracker.css
│   └── recommendations.css
│
├── pages/                      # Page-specific styles
│   ├── home.css
│   ├── input.css
│   ├── results.css
│   └── dashboard.css
│
└── theme/                      # Theme styles
    └── ...
```

##### JavaScript Structure (153 files)
```
static/js/
├── core/                       # Core modules
│   ├── riskcast_data_store.js  # Data store
│   ├── streaming.js            # Streaming handler
│   ├── translations.js         # Translation system
│   └── utils.js                # Core utilities
│
├── modules/                    # Feature modules
│   ├── smart_input.js          # Smart input system
│   ├── ai_chat.js              # AI chat
│   ├── progress_tracker.js     # Progress tracker
│   └── ...
│
├── pages/                      # Page-specific scripts
│   ├── home/
│   ├── input/
│   ├── results/
│   └── dashboard/
│
├── components/                 # UI components
│   ├── DecisionSummary.js
│   ├── RiskFanChart.js
│   ├── RiskCostFrontierChart.js
│   └── ...
│
└── visualization/              # Visualization modules
    └── ...
```

##### Other Static Assets
```
static/
├── cesium/                     # Cesium 3D Globe library (374 files)
│   ├── Assets/                # Cesium assets
│   ├── Widgets/               # Cesium widgets
│   ├── Workers/               # Web workers
│   └── Cesium.js              # Main Cesium library
│
├── icons/                      # SVG icons (52 files)
│   ├── v16/                   # Version 16 icons
│   └── v3000/                 # Version 3000 icons
│
├── images/                     # Images
│   └── hero-ship.jpg
│
└── data/                       # JSON data files
    └── expert/                # Expert data
```

#### 1.7 `app/routes/` - Additional Routes
```
routes/
├── overview.py                 # Overview page route
├── ai_endpoints_v33.py         # AI endpoints v33
├── backend_overview_route_v32.py
├── backend_overview_route_v33.py
└── update_shipment_route_v33.py
```

#### 1.8 `app/config/` - Configuration
```
config/
└── database.py                 # Database configuration
```

#### 1.9 `app/middleware/` - Middleware
```
middleware/
├── cache_headers.py            # Cache headers
├── error_handler.py            # Error handling
└── security_headers.py         # Security headers
```

#### 1.10 `app/validators/` - Validators
```
validators/
├── cargo_validator.py
├── kpi_validator.py
├── risk_validator.py
├── shipment_validator.py
└── transport_validator.py
```

#### 1.11 Root Files trong `app/`
```
app/
├── main.py                     # FastAPI application entry point
├── api.py                      # Legacy API routes
├── api_ai.py                   # AI API endpoints
├── config.py                   # App configuration
├── risk_engine.py              # Risk engine wrapper
├── memory.py                   # Memory system
└── __init__.py
```

---

### 2. `riskcast_v35/` - Module v35

Cấu trúc độc lập cho version 35 của RISKCAST.

```
riskcast_v35/
├── app/                        # Application code (104 files)
│   ├── ui/                     # UI components
│   └── ...
├── alembic/                    # Database migrations
├── static/                     # Static files
├── tests/                      # Test files
├── docker-compose.yml
└── requirements.txt
```

---

### 3. `riskcast-dashboard/` - Next.js Dashboard

Dashboard application được xây dựng với Next.js và TypeScript.

```
riskcast-dashboard/
├── app/                        # Next.js app directory
├── components/                 # React components
├── lib/                        # Utility libraries
├── public/                     # Public assets
├── next.config.ts              # Next.js config
├── tsconfig.json               # TypeScript config
├── tailwind.config.ts          # Tailwind CSS config
└── package.json
```

---

### 4. `src/` - Frontend Source Code

Source code cho frontend applications (Vue/React).

```
src/
├── components/                 # React/Vue components (37 files)
├── features/                   # Feature modules (68 files)
├── pages/                      # Page components
├── hooks/                      # React hooks (4 files)
├── utils/                      # Utilities (5 files)
├── types/                      # TypeScript types
├── validation/                 # Validation logic
├── data/                       # Data files
├── styles/                     # Styles
├── App.tsx                     # React App
├── App.vue                     # Vue App
├── main.js                     # Vue entry point
├── main.tsx                    # React entry point
└── style.css
```

---

### 5. `components/` - JSX Components

React/JSX components ở root level.

```
components/
├── header.jsx
├── kpiPanel.jsx
├── riskModule.jsx
├── sidebar.jsx
└── tabs.jsx
```

---

### 6. `pages/` - React Pages

React page components.

```
pages/
├── analytics/
│   └── index.jsx
├── cargo/
├── overview/
└── transport/
```

---

### 7. Root Level Files

#### Configuration Files
- `package.json` - Node.js dependencies
- `package-lock.json` - Lock file
- `requirements.txt` - Python dependencies
- `vite.config.js` - Vite configuration
- `tailwind.config.js` - Tailwind CSS config
- `postcss.config.js` - PostCSS config
- `jsconfig.json` - JavaScript config
- `tsconfig.json` - TypeScript config
- `pyrightconfig.json` - Pyright config

#### Entry Scripts
- `dev_run.py` - Development server runner
- `run_server.py` - Production server runner
- `run.py` - Alternative runner
- `run.ps1` - PowerShell startup script
- `start-server.ps1` - Server startup script
- `start-server-simple.ps1` - Simple startup script
- `start_server.bat` - Batch startup script
- `install-deps.ps1` - Dependency installer

#### Build & Utilities
- `build.py` - Build script
- `init_database.py` - Database initialization

#### HTML Entry Points
- `index.html` - Main HTML entry
- `index-react.html` - React app entry

#### Documentation
- `ARCHITECTURE.md` - Architecture documentation

---

## 🔄 DATA FLOW

### Request Flow
```
HTTP Request
    ↓
app/main.py (FastAPI app)
    ↓
app/api/ (API router)
    ↓
app/services/ (Service layer)
    ↓
app/core/engine/ (Engine layer)
    ↓
app/models/ (Data models)
    ↓
Database/Response
```

### Frontend Flow
```
Browser
    ↓
Jinja2 Templates (app/templates/)
    ↓
Static Assets (app/static/)
    ├── CSS (styling)
    ├── JavaScript (functionality)
    └── Images/Icons (assets)
    ↓
API Calls → Backend
```

---

## 📦 DEPENDENCIES

### Python Dependencies
- FastAPI - Web framework
- SQLAlchemy - ORM
- MySQL - Database
- Anthropic - AI API
- Pydantic - Data validation
- Jinja2 - Template engine

### JavaScript Dependencies
- Vite - Build tool
- Tailwind CSS - CSS framework
- Cesium - 3D Globe
- Chart.js - Charts
- React/Vue - Frontend frameworks

---

## 🎯 KEY FEATURES

1. **Risk Assessment Engine**
   - Multiple engine versions (v16, v21, v22, v2)
   - Hybrid AI approach (FAHP + TOPSIS)
   - Climate risk modeling
   - Network risk analysis

2. **API Architecture**
   - RESTful API
   - Versioned endpoints (/api/v1/)
   - AI-powered endpoints
   - Streaming responses

3. **Frontend**
   - Component-based architecture
   - Modular CSS/JS
   - Responsive design
   - Interactive visualizations

4. **Internationalization**
   - Multi-language support
   - Translation system

5. **Reporting**
   - PDF generation
   - Image export
   - Custom layouts

---

## 📝 NOTES

- **Legacy Code:** Các code cũ được giữ trong `app/core/legacy/` để tham khảo
- **Engine Versions:** Hệ thống hỗ trợ nhiều phiên bản engine để tương thích ngược
- **Module Structure:** Mỗi module có trách nhiệm riêng biệt, dễ maintain
- **Static Assets:** CSS và JS được tổ chức theo module để tối ưu performance

---

**Tài liệu được tạo tự động dựa trên cấu trúc thư mục hiện tại.**

