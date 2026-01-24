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
if model_versioning_router:
    router.include_router(model_versioning_router)
if evidence_api_router:
    router.include_router(evidence_api_router)

# Include other module routers (if available)
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
if model_versioning_router:
    router.include_router(model_versioning_router)
if evidence_router:
    router.include_router(evidence_router)
if underwriting_router:
    router.include_router(underwriting_router)
if claims_router:
    router.include_router(claims_router)
if parametric_router:
    router.include_router(parametric_router)
