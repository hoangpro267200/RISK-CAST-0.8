# RISKCAST Architecture Documentation

## 🏗️ Project Structure

RISKCAST has been refactored into a clean, scalable SaaS structure following best practices for maintainability and modularity.

### Directory Structure

```
RISKCAST/
├── app/
│   ├── api/                    # API endpoints
│   │   ├── v1/                # API v1 routes
│   │   │   ├── __init__.py
│   │   │   ├── routes.py      # General routes
│   │   │   ├── ai_routes.py   # AI endpoints
│   │   │   ├── risk_routes.py # Risk analysis endpoints
│   │   │   └── analyze.py     # Analysis endpoint
│   │   └── __init__.py        # Main API router
│   │
│   ├── core/                   # Core business logic
│   │   ├── engine/            # Risk calculation engines
│   │   │   ├── __init__.py
│   │   │   ├── risk_engine_base.py
│   │   │   └── risk_engine_v16.py
│   │   ├── services/          # Business services
│   │   │   ├── __init__.py
│   │   │   ├── risk_service.py
│   │   │   └── climate_service.py
│   │   ├── utils/             # Utility functions
│   │   │   ├── __init__.py
│   │   │   ├── validators.py
│   │   │   ├── converters.py
│   │   │   └── cache.py
│   │   └── legacy/            # Legacy code (v14/v15)
│   │       └── ...            # Old versions for reference
│   │
│   ├── templates/             # Jinja2 templates
│   │   ├── layouts/          # Layout templates
│   │   ├── components/       # Reusable components
│   │   └── pages/            # Page templates
│   │
│   ├── static/               # Static assets
│   │   ├── css/
│   │   │   ├── base/        # Base styles (variables, reset, typography)
│   │   │   ├── layout/      # Layout styles (navbar, sidebar, grid)
│   │   │   ├── components/  # Component styles
│   │   │   └── pages/       # Page-specific styles
│   │   ├── js/
│   │   │   ├── core/        # Core modules (data store, streaming)
│   │   │   ├── modules/     # Feature modules
│   │   │   └── pages/       # Page-specific scripts
│   │   ├── images/
│   │   └── icons/
│   │
│   ├── main.py               # FastAPI application entry point
│   ├── api.py               # Legacy API routes (backward compatibility)
│   ├── api_ai.py            # AI API endpoints
│   ├── risk_engine.py       # Risk engine wrapper
│   └── memory.py            # Memory system for shipment history
│
├── data/                    # Data storage
├── files/                   # File storage
├── venv/                    # Virtual environment
├── .gitignore              # Git ignore rules
├── requirements.txt        # Python dependencies
└── README.md               # Project README
```

## 🎯 Architecture Principles

### 1. Separation of Concerns
- **API Layer** (`app/api/`): Handles HTTP requests/responses
- **Service Layer** (`app/core/services/`): Business logic
- **Engine Layer** (`app/core/engine/`): Core calculations
- **Utils Layer** (`app/core/utils/`): Helper functions

### 2. Modularity
- Each module has a single responsibility
- Clear interfaces between modules
- Easy to test and maintain

### 3. Scalability
- Versioned API (`/api/v1/`)
- Modular CSS/JS structure
- Component-based templates

### 4. Maintainability
- Clear folder structure
- Consistent naming conventions
- Legacy code isolated in `core/legacy/`

## 📦 Core Modules

### Engine Module (`app/core/engine/`)
Contains the core risk calculation logic.

**Files:**
- `risk_engine_v16.py`: Main risk calculation engine
- `risk_engine_base.py`: Base engine interface

**Exports:**
```python
from app.core.engine import (
    EnterpriseRiskEngine,
    calculate_enterprise_risk,
    compute_partner_risk
)
```

### Services Module (`app/core/services/`)
Business logic services that orchestrate engine calls.

**Files:**
- `risk_service.py`: Risk analysis service
- `climate_service.py`: Climate data service

**Example Usage:**
```python
from app.core.services import run_risk_engine_v14
from app.core.services.climate_service import get_climate_data

# Calculate risk
result = run_risk_engine_v14(shipment_data)

# Get climate data
climate = get_climate_data(route="vn_us", ...)
```

### Utils Module (`app/core/utils/`)
Utility functions for validation, conversion, and caching.

**Files:**
- `validators.py`: Input validation and sanitization
- `converters.py`: Data format conversion
- `cache.py`: Caching utilities

**Example Usage:**
```python
from app.core.utils import (
    sanitize_input,
    validate_shipment_data,
    format_risk_level
)

# Validate and sanitize
is_valid, error = validate_shipment_data(data)
clean_data = sanitize_input(data)
```

## 🔌 API Structure

### API v1 (`/api/v1/`)

**Routes:**
- `POST /api/v1/analyze` - Risk analysis
- `POST /api/v1/risk/analyze` - Risk analysis (via risk_routes)
- `POST /api/v1/ai/*` - AI endpoints (to be migrated)

### Legacy API (`/api/`)
- Maintained for backward compatibility
- Uses `app/api.py` and `app/api_ai.py`

### AI API (`/api/ai/`)
- Streaming AI responses
- AI analysis endpoints
- Currently in `app/api_ai.py`

## 🎨 Frontend Architecture

### CSS Organization
CSS files are organized by responsibility:

- **Base** (`css/base/`): Foundation styles
  - Variables (colors, spacing, typography)
  - Reset/normalize
  - Typography
  - Mixins/utilities

- **Layout** (`css/layout/`): Page structure
  - Navbar
  - Sidebar
  - Grid system

- **Components** (`css/components/`): Reusable UI components
  - Cards, buttons, chips
  - Forms, stats cards
  - AI panel

- **Pages** (`css/pages/`): Page-specific styles
  - Home, input, results
  - Dashboard, overview

### JavaScript Organization
JavaScript files are organized by purpose:

- **Core** (`js/core/`): Core functionality
  - Data store
  - Streaming handler
  - Translations

- **Modules** (`js/modules/`): Feature modules
  - Smart input system
  - AI chat
  - Progress tracker
  - Enterprise input

- **Pages** (`js/pages/`): Page-specific scripts
  - Home, input, results
  - Dashboard, overview

### Template Organization
Templates use Jinja2 with component-based structure:

- **Layouts** (`templates/layouts/`): Page layouts
  - `base.html`: Base layout
  - `input_layout.html`: Input page layout
  - `dashboard_layout.html`: Dashboard layout

- **Components** (`templates/components/`): Reusable components
  - Navbar, sidebar
  - Stats cards, AI panel
  - Progress tracker

- **Pages** (`templates/pages/`): Page templates
  - Home, input, results
  - Dashboard, overview

**Example Template Structure:**
```jinja2
{% extends "layouts/base.html" %}

{% block content %}
  {% include "components/navbar.html" %}
  {% include "components/sidebar.html" %}
  <!-- Page content -->
{% endblock %}
```

## 🔄 Import Conventions

### Python Imports
```python
# Core modules
from app.core.engine import calculate_enterprise_risk
from app.core.services import run_risk_engine_v14
from app.core.utils import sanitize_input

# API modules
from app.api.v1 import router as v1_router

# Legacy (avoid in new code)
from app.core.legacy import ...
```

### JavaScript Imports (ES6 Modules)
```javascript
// Core modules
import { RiskCastStore } from '../core/riskcast_data_store.js';
import { StreamingHandler } from '../core/streaming.js';

// Feature modules
import { SmartInput } from '../modules/smart_input.js';
import { AIChat } from '../modules/ai_chat.js';
```

### CSS Imports
```css
/* Base */
@import 'base/variables.css';
@import 'base/reset.css';
@import 'base/typography.css';

/* Layout */
@import 'layout/navbar.css';
@import 'layout/sidebar.css';

/* Components */
@import 'components/cards.css';
@import 'components/buttons.css';
```

## 🚀 Getting Started

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your API keys
```

### Running the Application
```bash
# Development server
uvicorn app.main:app --reload

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Development Guidelines

1. **Follow the Structure**: Place files in appropriate directories
2. **Use Services**: Don't call engines directly from API routes
3. **Validate Input**: Always validate user input using utils
4. **Handle Errors**: Use proper error handling and logging
5. **Write Tests**: Add tests for new features
6. **Document Code**: Add docstrings and comments

## 📝 Migration Notes

### From Old Structure
If you have code referencing the old structure:

**Old:**
```python
from app.core.risk_engine_v16 import calculate_enterprise_risk
from app.utils import sanitize_input
```

**New:**
```python
from app.core.engine.risk_engine_v16 import calculate_enterprise_risk
from app.core.utils.validators import sanitize_input
```

### Legacy Code
Legacy v14/v15 code is preserved in `app/core/legacy/` for reference. Avoid importing directly from legacy modules in new code.

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the project root:

```env
ANTHROPIC_API_KEY=your_api_key_here
APP_NAME=RISKCAST
DEBUG=True
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=info
```

### Static Files
Static files are served from `app/static/`. The FastAPI app automatically mounts this directory at `/static`.

### Templates
Templates are loaded from `app/templates/`. Use Jinja2 syntax for templating.

## 🧪 Testing

### Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_risk_engine.py

# Run with coverage
pytest --cov=app
```

### Test Structure
```
tests/
├── test_engine/
├── test_services/
├── test_api/
└── test_utils/
```

## 📚 Additional Resources

- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **Jinja2 Templates**: https://jinja.palletsprojects.com/
- **Pydantic Models**: https://pydantic-docs.helpmanual.io/

## 🤝 Contributing

1. Follow the architecture principles
2. Maintain code quality standards
3. Update documentation for new features
4. Add tests for new code
5. Use type hints for Python code

---

**Last Updated**: After refactoring (2025)
**Version**: 1.0.0 (Refactored Structure)





















