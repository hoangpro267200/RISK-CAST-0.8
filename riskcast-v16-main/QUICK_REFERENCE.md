# 🚀 RISKCAST - QUICK REFERENCE GUIDE

**Production Readiness: 9.0/10** ✅  
**Last Updated:** 2025-01-11

---

## ⚡ QUICK START

### Development
```bash
# Backend
cd riskcast-v16-main
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
uvicorn app.main:app --reload

# Frontend
cd riskcast-v16-main
npm install --legacy-peer-deps
npm run dev
```

### Production
```bash
# Set environment
export ENVIRONMENT=production
export SESSION_SECRET_KEY=$(openssl rand -hex 32)
export ANTHROPIC_API_KEY=your_key_here
export ALLOWED_ORIGINS=https://yourdomain.com

# Build frontend
npm run build

# Start server
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

---

## 🔗 KEY ENDPOINTS

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/risk/v2/analyze` | POST | Risk analysis (main endpoint) |
| `/api/v1/risk/state/{id}` | GET | Get analysis state |
| `/api/ai/stream` | POST | AI advisor streaming |
| `/metrics` | GET | Prometheus metrics |
| `/health` | GET | Health check |
| `/results/data` | GET | Get results data |

---

## 🛠️ KEY COMMANDS

### Testing
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test
pytest tests/unit/test_monte_carlo_determinism.py -v
```

### Frontend
```bash
# Development
npm run dev

# Build
npm run build

# Analyze bundle
npm run analyze

# Type check
npm run typecheck
```

### Security
```bash
# Audit dependencies
npm audit --audit-level=high
pip-audit

# Run audit script
bash scripts/audit_dependencies.sh
```

---

## 📊 MONITORING

### Metrics
- **Endpoint:** `/metrics`
- **Format:** Prometheus
- **Key Metrics:**
  - `riskcast_http_requests_total` - Request count
  - `riskcast_http_request_duration_seconds` - Request duration
  - `riskcast_http_errors_total` - Error count
  - `riskcast_http_active_requests` - Active requests

### Health Check
- **Endpoint:** `/health`
- **Response:** `{"status": "healthy", "version": "v16"}`

### Alerts
- **Config:** `prometheus_alerts.yml`
- **Key Alerts:**
  - High error rate (>5%)
  - High latency (P95 >2s)
  - AI advisor failures (>10%)

---

## 🔒 SECURITY

### Required Environment Variables (Production)
```bash
ENVIRONMENT=production
SESSION_SECRET_KEY=<strong-random-32-chars>
ANTHROPIC_API_KEY=<your-key>
ALLOWED_ORIGINS=https://yourdomain.com
```

### Rate Limits
- Risk analysis: 10 req/min
- AI advisor: 20 req/min
- Default: 100 req/min

### CSP
- Production: Nonce-based (no unsafe-inline)
- Development: Permissive (for Vite HMR)

---

## 🐛 TROUBLESHOOTING

### Static Files 404
- Check: `ASSETS_DIR` exists
- Verify: Error handler excludes `/assets/`

### Rate Limit Errors
- Check: IP whitelist
- Adjust: `app/middleware/rate_limiter.py`

### Secrets Validation Failing
- Check: `ENVIRONMENT=production` is set
- Verify: All secrets in `.env`

---

## 📚 DOCUMENTATION

- **Upgrade Progress:** `UPGRADE_PROGRESS.md`
- **Final Report:** `FINAL_UPGRADE_REPORT.md`
- **Deployment:** `DEPLOYMENT_CHECKLIST.md`
- **Audit Report:** `AUDIT_REPORT_RISKCAST.md`

---

**For detailed information, see:** `FINAL_UPGRADE_REPORT.md`
