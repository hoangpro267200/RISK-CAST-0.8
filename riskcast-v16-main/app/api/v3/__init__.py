"""
API V3 Router
Main router for API v3 endpoints
RISKCAST V3 - Modular Monolith
"""
from fastapi import APIRouter

# Import risk API router (new unified router)
from app.api.v3.risk import router as risk_router, runs_router
from app.api.v3.risk_assessments import router as risk_assessments_router
from app.api.v3.risk_runs import router as risk_runs_router

# Import new v3 API routers
try:
    from app.api.v3.models import router as models_router
except ImportError:
    models_router = None

try:
    from app.api.v3.evidence import router as evidence_api_router
except ImportError:
    evidence_api_router = None

try:
    from app.api.v3.underwriting import router as underwriting_api_router
except ImportError:
    underwriting_api_router = None

try:
    from app.api.v3.claims import router as claims_api_router
except ImportError:
    claims_api_router = None

try:
    from app.api.v3.parametric import router as parametric_api_router
except ImportError:
    parametric_api_router = None

try:
    from app.api.v3.audit import router as audit_api_router
except ImportError:
    audit_api_router = None

try:
    from app.api.v3.compliance import router as compliance_api_router
except ImportError:
    compliance_api_router = None

try:
    from app.api.v3.analytics import router as analytics_api_router
except ImportError:
    analytics_api_router = None

try:
    from app.api.v3.calibration import router as calibration_api_router
except ImportError:
    calibration_api_router = None

try:
    from app.api.v3.corridors import router as corridors_api_router
except ImportError:
    corridors_api_router = None

try:
    from app.api.v3.sla import router as sla_api_router
except ImportError:
    sla_api_router = None

try:
    from app.api.v3.security import router as security_api_router
except ImportError:
    security_api_router = None

try:
    from app.api.v3.runbooks import router as runbooks_api_router
except ImportError:
    runbooks_api_router = None

try:
    from app.api.v3.premium_allocations import router as premium_allocations_api_router
except ImportError:
    premium_allocations_api_router = None

try:
    from app.api.v3.data_quality import router as data_quality_api_router
except ImportError:
    data_quality_api_router = None

try:
    from app.api.v3.regulatory import router as regulatory_api_router
except ImportError:
    regulatory_api_router = None

try:
    from app.api.v3.health import router as health_api_router
except ImportError:
    health_api_router = None

try:
    from app.api.v3.onboarding import router as onboarding_api_router
except ImportError:
    onboarding_api_router = None

try:
    from app.api.v3.quotes import router as quotes_api_router
except ImportError:
    quotes_api_router = None

try:
    from app.api.v3.customer_portal import router as customer_portal_router
except ImportError:
    customer_portal_router = None

try:
    from app.api.v3.webhooks import router as webhooks_router
except ImportError:
    webhooks_router = None

try:
    from app.api.v3.usage import router as usage_router
except ImportError:
    usage_router = None

# ML/AI Feature routers
try:
    from app.api.v3.fraud_detection import router as fraud_detection_router
except ImportError:
    fraud_detection_router = None

try:
    from app.api.v3.nlp import router as nlp_router
except ImportError:
    nlp_router = None

try:
    from app.api.v3.predictive_analytics import router as predictive_analytics_router
except ImportError:
    predictive_analytics_router = None

try:
    from app.api.v3.websocket import router as websocket_router
except ImportError:
    websocket_router = None

try:
    from app.api.v3.evidence_bundles import router as evidence_bundles_router
except ImportError:
    evidence_bundles_router = None

try:
    from app.api.v3.ais import router as ais_router
except ImportError:
    ais_router = None

try:
    from app.api.v3.news import router as news_router
except ImportError:
    news_router = None

try:
    from app.api.v3.currency import router as currency_router
except ImportError:
    currency_router = None

try:
    from app.api.v3.sanctions import router as sanctions_router
except ImportError:
    sanctions_router = None

try:
    from app.api.v3.model_monitoring import router as model_monitoring_router
except ImportError:
    model_monitoring_router = None

# Market Data router
try:
    from app.api.v3.market import router as market_router
except ImportError:
    market_router = None

# Billing router
try:
    from app.api.v3.billing import router as billing_router
except ImportError:
    billing_router = None

# API Marketplace router
try:
    from app.api.v3.marketplace import router as marketplace_router
except ImportError:
    marketplace_router = None

# GDPR Compliance router
try:
    from app.api.v3.gdpr import router as gdpr_router
except ImportError:
    gdpr_router = None

# Recommendations router
try:
    from app.api.v3.recommendations import router as recommendations_router
except ImportError:
    recommendations_router = None

model_versions_router = None
try:
    from app.api.v3.model_versions import router as model_versions_router
except Exception:
    pass

# Import other module routers (if they exist)
try:
    from app.modules.tenancy.router import router as tenancy_router
except ImportError:
    tenancy_router = None

try:
    from app.modules.identity_access.router import router as auth_router
except ImportError:
    auth_router = None

try:
    from app.modules.rbac_policy.router import router as rbac_router
except ImportError:
    rbac_router = None

try:
    from app.modules.audit_ledger.router import router as audit_router
except ImportError:
    audit_router = None

try:
    from app.modules.observability.router import router as observability_router
except ImportError:
    observability_router = None

try:
    from app.modules.model_versioning.router import router as model_versioning_router
except ImportError:
    model_versioning_router = None

try:
    from app.modules.evidence.router import router as evidence_router
except ImportError:
    evidence_router = None

try:
    from app.modules.underwriting.router import router as underwriting_router
except ImportError:
    underwriting_router = None

try:
    from app.modules.claims.router import router as claims_router
except ImportError:
    claims_router = None

try:
    from app.modules.parametric.router import router as parametric_router
except ImportError:
    parametric_router = None

# Create main v3 router
router = APIRouter()

# Include risk routers (new unified API)
router.include_router(risk_router)
router.include_router(runs_router)
router.include_router(risk_assessments_router)
router.include_router(risk_runs_router)

# Include new v3 API routers
if models_router:
    router.include_router(models_router)
if model_versions_router:
    router.include_router(model_versions_router)
if evidence_api_router:
    router.include_router(evidence_api_router)
if underwriting_api_router:
    router.include_router(underwriting_api_router)
if claims_api_router:
    router.include_router(claims_api_router)
if parametric_api_router:
    router.include_router(parametric_api_router)
if audit_api_router:
    router.include_router(audit_api_router)
if compliance_api_router:
    router.include_router(compliance_api_router)
if analytics_api_router:
    router.include_router(analytics_api_router)
if calibration_api_router:
    router.include_router(calibration_api_router)
if corridors_api_router:
    router.include_router(corridors_api_router)
if sla_api_router:
    router.include_router(sla_api_router)
if security_api_router:
    router.include_router(security_api_router)
if runbooks_api_router:
    router.include_router(runbooks_api_router)
if premium_allocations_api_router:
    router.include_router(premium_allocations_api_router)
if data_quality_api_router:
    router.include_router(data_quality_api_router)
if regulatory_api_router:
    router.include_router(regulatory_api_router)
if health_api_router:
    router.include_router(health_api_router)
if onboarding_api_router:
    router.include_router(onboarding_api_router)
if quotes_api_router:
    router.include_router(quotes_api_router)
if customer_portal_router:
    router.include_router(customer_portal_router)
if webhooks_router:
    router.include_router(webhooks_router)
if usage_router:
    router.include_router(usage_router)

# Include ML/AI feature routers
if fraud_detection_router:
    router.include_router(fraud_detection_router)
if nlp_router:
    router.include_router(nlp_router)
if predictive_analytics_router:
    router.include_router(predictive_analytics_router)
if websocket_router:
    router.include_router(websocket_router)
if evidence_bundles_router:
    router.include_router(evidence_bundles_router)
if ais_router:
    router.include_router(ais_router)
if news_router:
    router.include_router(news_router)
if currency_router:
    router.include_router(currency_router)
if sanctions_router:
    router.include_router(sanctions_router)
if model_monitoring_router:
    router.include_router(model_monitoring_router)

# Market Data router
if market_router:
    router.include_router(market_router)

# Billing router
if billing_router:
    router.include_router(billing_router)

# API Marketplace router
if marketplace_router:
    router.include_router(marketplace_router)

# GDPR Compliance router
if gdpr_router:
    router.include_router(gdpr_router)

# Recommendations router
if recommendations_router:
    router.include_router(recommendations_router)

# Include other module routers (if available)
# Note: Only include module routers that are NOT covered by v3 API routers
if tenancy_router:
    router.include_router(tenancy_router)
if auth_router:
    router.include_router(auth_router)
if rbac_router:
    router.include_router(rbac_router)
if audit_router:
    router.include_router(audit_router)
if observability_router:
    router.include_router(observability_router)

# NOTE: The following module routers are excluded to avoid duplicate operation IDs
# because they're already covered by the v3 API routers above:
# - model_versioning_router (covered by model_versions_router)
# - evidence_router (covered by evidence_api_router)
# - underwriting_router (covered by underwriting_api_router)
# - claims_router (covered by claims_api_router)
# - parametric_router (covered by parametric_api_router)
