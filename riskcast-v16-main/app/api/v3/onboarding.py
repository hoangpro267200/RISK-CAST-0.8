"""
Customer Onboarding API

Endpoints for customer onboarding:
1. Company registration
2. KYC/KYB verification
3. Credit assessment
4. Pricing tier assignment
5. Account activation
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_audit
from app.core.audit.immutable_ledger import ImmutableAuditLedger


router = APIRouter(prefix="/onboarding", tags=["Onboarding"])


# ============================================================================
# Schemas
# ============================================================================

class CompanyRegistration(BaseModel):
    """Company registration request."""
    # Company details
    company_name: str = Field(..., min_length=2, max_length=200)
    legal_name: str = Field(..., min_length=2, max_length=200)
    registration_number: str = Field(..., min_length=5, max_length=50)
    tax_id: Optional[str] = None
    
    # Address
    address_line_1: str
    address_line_2: Optional[str] = None
    city: str
    state_province: Optional[str] = None
    postal_code: str
    country: str = Field(..., min_length=2, max_length=2)  # ISO country code
    
    # Contact
    primary_contact_name: str
    primary_contact_email: EmailStr
    primary_contact_phone: str
    
    # Business info
    industry: str
    annual_shipment_volume: int  # Number of shipments per year
    average_cargo_value_usd: float
    primary_cargo_types: List[str]
    primary_routes: List[str]  # e.g., ["CNSHA-USLAX", "SGSIN-NLRTM"]
    
    # Insurance history
    current_insurer: Optional[str] = None
    years_insured: int = 0
    claims_history_3yr: Optional[dict] = None  # {year: {count, amount}}


class KYCDocument(BaseModel):
    """KYC document submission."""
    document_type: str  # CERTIFICATE_OF_INCORPORATION, TAX_CERTIFICATE, etc.
    document_number: str
    issue_date: str
    expiry_date: Optional[str] = None
    issuing_authority: str
    document_url: str  # S3 URL of uploaded document


class OnboardingStatus(BaseModel):
    """Current onboarding status."""
    customer_id: str
    company_name: str
    status: str  # PENDING, KYC_REQUIRED, CREDIT_CHECK, APPROVED, REJECTED
    
    # Checklist
    registration_complete: bool
    kyc_documents_submitted: bool
    kyc_verified: bool
    credit_assessed: bool
    tier_assigned: bool
    account_activated: bool
    
    # Details
    assigned_tier: Optional[str]
    credit_limit_usd: Optional[float]
    
    # Next steps
    pending_items: List[str]
    estimated_completion: Optional[str]


class CreditAssessment(BaseModel):
    """Credit assessment result."""
    customer_id: str
    credit_score: int  # 0-100
    credit_grade: str  # A, B, C, D, F
    recommended_credit_limit_usd: float
    recommended_tier: str
    risk_factors: List[str]
    assessment_date: str


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/register")
async def register_company(
    registration: CompanyRegistration,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    audit: ImmutableAuditLedger = Depends(get_audit)
):
    """
    Register a new company for onboarding.
    
    This creates the customer record and initiates the onboarding process.
    """
    from app.models.customer import Customer
    
    # Check if company already registered
    existing = db.query(Customer).filter(
        Customer.registration_number == registration.registration_number
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Company already registered")
    
    # Create customer
    customer = Customer(
        company_name=registration.company_name,
        legal_name=registration.legal_name,
        registration_number=registration.registration_number,
        tax_id=registration.tax_id,
        
        address_line_1=registration.address_line_1,
        address_line_2=registration.address_line_2,
        city=registration.city,
        state_province=registration.state_province,
        postal_code=registration.postal_code,
        country=registration.country,
        
        primary_contact_name=registration.primary_contact_name,
        primary_contact_email=registration.primary_contact_email,
        primary_contact_phone=registration.primary_contact_phone,
        
        industry=registration.industry,
        annual_shipment_volume=registration.annual_shipment_volume,
        average_cargo_value_usd=registration.average_cargo_value_usd,
        primary_cargo_types=registration.primary_cargo_types,
        primary_routes=registration.primary_routes,
        
        current_insurer=registration.current_insurer,
        years_insured=registration.years_insured,
        claims_history_json=registration.claims_history_3yr,
        
        status="PENDING",
        onboarding_stage="REGISTRATION_COMPLETE"
    )
    
    db.add(customer)
    db.commit()
    db.refresh(customer)
    
    # Audit
    audit.append_event(
        event_type="CUSTOMER",
        action="COMPANY_REGISTERED",
        entity_type="customer",
        entity_id=str(customer.id),
        actor_type="SYSTEM",
        payload={
            "company_name": registration.company_name,
            "country": registration.country,
            "industry": registration.industry
        }
    )
    
    # Trigger background KYC check
    background_tasks.add_task(
        _initiate_kyc_check,
        str(customer.id),
        registration.country
    )
    
    return {
        "customer_id": str(customer.id),
        "status": "PENDING",
        "message": "Registration complete. Please submit KYC documents.",
        "next_step": f"Submit KYC documents via /api/v3/onboarding/kyc/{customer.id}",
        "required_documents": _get_required_documents(registration.country)
    }


@router.post("/kyc/{customer_id}")
async def submit_kyc_documents(
    customer_id: str,
    documents: List[KYCDocument],
    db: Session = Depends(get_db),
    audit: ImmutableAuditLedger = Depends(get_audit)
):
    """
    Submit KYC documents for verification.
    """
    from app.models.customer import Customer, KYCDocumentModel
    
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Store documents
    for doc in documents:
        kyc_doc = KYCDocumentModel(
            customer_id=customer_id,
            document_type=doc.document_type,
            document_number=doc.document_number,
            issue_date=doc.issue_date,
            expiry_date=doc.expiry_date,
            issuing_authority=doc.issuing_authority,
            document_url=doc.document_url,
            status="PENDING_VERIFICATION"
        )
        db.add(kyc_doc)
    
    customer.onboarding_stage = "KYC_SUBMITTED"
    db.commit()
    
    # Audit
    audit.append_event(
        event_type="CUSTOMER",
        action="KYC_DOCUMENTS_SUBMITTED",
        entity_type="customer",
        entity_id=customer_id,
        actor_type="SYSTEM",
        payload={
            "document_count": len(documents),
            "document_types": [d.document_type for d in documents]
        }
    )
    
    return {
        "status": "SUBMITTED",
        "message": "KYC documents submitted for verification",
        "documents_received": len(documents),
        "estimated_verification_time": "1-2 business days"
    }


@router.get("/status/{customer_id}", response_model=OnboardingStatus)
async def get_onboarding_status(
    customer_id: str,
    db: Session = Depends(get_db)
):
    """
    Get current onboarding status.
    """
    from app.models.customer import Customer, KYCDocumentModel
    
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Check document status
    docs = db.query(KYCDocumentModel).filter(
        KYCDocumentModel.customer_id == customer_id
    ).all()
    
    kyc_submitted = len(docs) > 0
    kyc_verified = all(d.status == "VERIFIED" for d in docs) if docs else False
    
    # Determine pending items
    pending = []
    if not kyc_submitted:
        pending.append("Submit KYC documents")
    elif not kyc_verified:
        pending.append("KYC verification in progress")
    if customer.onboarding_stage == "CREDIT_CHECK":
        pending.append("Credit assessment in progress")
    if not customer.pricing_tier:
        pending.append("Tier assignment pending")
    if customer.status != "ACTIVE":
        pending.append("Account activation pending")
    
    return OnboardingStatus(
        customer_id=customer_id,
        company_name=customer.company_name,
        status=customer.status,
        registration_complete=True,
        kyc_documents_submitted=kyc_submitted,
        kyc_verified=kyc_verified,
        credit_assessed=customer.credit_score is not None,
        tier_assigned=customer.pricing_tier is not None,
        account_activated=customer.status == "ACTIVE",
        assigned_tier=customer.pricing_tier,
        credit_limit_usd=customer.credit_limit_usd,
        pending_items=pending,
        estimated_completion="1-3 business days" if pending else None
    )


@router.post("/verify-kyc/{customer_id}")
async def verify_kyc(
    customer_id: str,
    verification_result: dict,
    db: Session = Depends(get_db),
    audit: ImmutableAuditLedger = Depends(get_audit)
):
    """
    Internal endpoint: Record KYC verification result.
    
    Called by KYC verification service/manual review.
    """
    from app.models.customer import Customer, KYCDocumentModel
    
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Update document statuses
    for doc_id, status_info in verification_result.get("documents", {}).items():
        doc = db.query(KYCDocumentModel).filter(
            KYCDocumentModel.id == doc_id
        ).first()
        if doc:
            doc.status = status_info.get("status", "PENDING_VERIFICATION")
            doc.verification_notes = status_info.get("notes")
            doc.verified_at = datetime.utcnow()
    
    # Update customer status
    all_verified = verification_result.get("all_verified", False)
    
    if all_verified:
        customer.onboarding_stage = "KYC_VERIFIED"
        customer.kyc_verified_at = datetime.utcnow()
    else:
        customer.onboarding_stage = "KYC_FAILED"
        customer.status = "KYC_REJECTED"
    
    db.commit()
    
    # Audit
    audit.append_event(
        event_type="CUSTOMER",
        action="KYC_VERIFIED" if all_verified else "KYC_REJECTED",
        entity_type="customer",
        entity_id=customer_id,
        actor_type="SYSTEM",
        payload=verification_result
    )
    
    return {"status": "KYC_VERIFIED" if all_verified else "KYC_REJECTED"}


@router.post("/credit-assessment/{customer_id}", response_model=CreditAssessment)
async def assess_credit(
    customer_id: str,
    db: Session = Depends(get_db),
    audit: ImmutableAuditLedger = Depends(get_audit)
):
    """
    Perform credit assessment for customer.
    """
    from app.models.customer import Customer
    
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    if customer.onboarding_stage not in ["KYC_VERIFIED", "CREDIT_CHECK"]:
        raise HTTPException(
            status_code=400, 
            detail=f"KYC must be verified before credit assessment. Current stage: {customer.onboarding_stage}"
        )
    
    # Calculate credit score (simplified)
    score, grade, factors = _calculate_credit_score(customer)
    
    # Determine credit limit and tier
    credit_limit = _calculate_credit_limit(score, customer.annual_shipment_volume, customer.average_cargo_value_usd)
    tier = _determine_tier(score, customer.years_insured, customer.claims_history_json)
    
    # Update customer
    customer.credit_score = score
    customer.credit_grade = grade
    customer.credit_limit_usd = credit_limit
    customer.pricing_tier = tier
    customer.onboarding_stage = "CREDIT_ASSESSED"
    customer.credit_assessed_at = datetime.utcnow()
    
    db.commit()
    
    # Audit
    audit.append_event(
        event_type="CUSTOMER",
        action="CREDIT_ASSESSED",
        entity_type="customer",
        entity_id=customer_id,
        actor_type="SYSTEM",
        payload={
            "credit_score": score,
            "credit_grade": grade,
            "credit_limit": credit_limit,
            "tier": tier
        }
    )
    
    return CreditAssessment(
        customer_id=customer_id,
        credit_score=score,
        credit_grade=grade,
        recommended_credit_limit_usd=credit_limit,
        recommended_tier=tier,
        risk_factors=factors,
        assessment_date=datetime.utcnow().isoformat()
    )


@router.post("/activate/{customer_id}")
async def activate_account(
    customer_id: str,
    db: Session = Depends(get_db),
    audit: ImmutableAuditLedger = Depends(get_audit)
):
    """
    Activate customer account.
    
    Final step in onboarding.
    """
    from app.models.customer import Customer
    
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Check all prerequisites
    if customer.onboarding_stage != "CREDIT_ASSESSED":
        raise HTTPException(
            status_code=400, 
            detail=f"Credit assessment required. Current stage: {customer.onboarding_stage}"
        )
    
    if not customer.pricing_tier:
        raise HTTPException(status_code=400, detail="Pricing tier must be assigned")
    
    # Activate
    customer.status = "ACTIVE"
    customer.onboarding_stage = "COMPLETE"
    customer.activated_at = datetime.utcnow()
    
    db.commit()
    
    # Audit
    audit.append_event(
        event_type="CUSTOMER",
        action="ACCOUNT_ACTIVATED",
        entity_type="customer",
        entity_id=customer_id,
        actor_type="SYSTEM",
        payload={
            "company_name": customer.company_name,
            "tier": customer.pricing_tier,
            "credit_limit": customer.credit_limit_usd
        }
    )
    
    # Send welcome email (would be async task)
    # await send_welcome_email(customer)
    
    return {
        "status": "ACTIVATED",
        "customer_id": customer_id,
        "company_name": customer.company_name,
        "tier": customer.pricing_tier,
        "credit_limit_usd": customer.credit_limit_usd,
        "message": "Account activated successfully. Welcome to RISKCAST!"
    }


# ============================================================================
# Helper Functions
# ============================================================================

async def _initiate_kyc_check(customer_id: str, country: str):
    """Background task to initiate KYC check."""
    # Would call external KYC service
    pass


def _get_required_documents(country: str) -> List[dict]:
    """Get required KYC documents by country."""
    base_docs = [
        {"type": "CERTIFICATE_OF_INCORPORATION", "description": "Certificate of Incorporation"},
        {"type": "TAX_CERTIFICATE", "description": "Tax Registration Certificate"},
        {"type": "PROOF_OF_ADDRESS", "description": "Proof of Business Address (utility bill, bank statement)"},
        {"type": "DIRECTOR_ID", "description": "Government ID of at least one director"}
    ]
    
    # Add country-specific requirements
    if country == "US":
        base_docs.append({"type": "W9", "description": "W-9 Tax Form"})
    elif country in ["GB", "EU"]:
        base_docs.append({"type": "VAT_CERTIFICATE", "description": "VAT Registration Certificate"})
    
    return base_docs


def _calculate_credit_score(customer) -> tuple:
    """Calculate credit score based on customer data."""
    score = 50  # Base score
    factors = []
    
    # Years in business
    if customer.years_insured >= 5:
        score += 15
    elif customer.years_insured >= 2:
        score += 10
    else:
        factors.append("Limited insurance history")
    
    # Shipment volume
    if customer.annual_shipment_volume >= 500:
        score += 10
    elif customer.annual_shipment_volume >= 100:
        score += 5
    else:
        factors.append("Low shipment volume")
    
    # Claims history
    if customer.claims_history_json:
        total_claims = sum(y.get("count", 0) for y in customer.claims_history_json.values())
        if total_claims == 0:
            score += 20
        elif total_claims <= 2:
            score += 10
        else:
            score -= 10
            factors.append("Multiple claims in history")
    else:
        score += 10  # No history = no claims
    
    # Industry risk
    high_risk_industries = ["CHEMICALS", "PHARMACEUTICALS", "ELECTRONICS"]
    if customer.industry in high_risk_industries:
        score -= 5
        factors.append(f"Higher risk industry: {customer.industry}")
    
    # Determine grade
    if score >= 80:
        grade = "A"
    elif score >= 65:
        grade = "B"
    elif score >= 50:
        grade = "C"
    elif score >= 35:
        grade = "D"
    else:
        grade = "F"
    
    return min(100, max(0, score)), grade, factors


def _calculate_credit_limit(score: int, volume: int, avg_value: float) -> float:
    """Calculate credit limit based on score and business size."""
    # Base limit on average shipment value × expected volume
    base_limit = avg_value * min(volume / 12, 50)  # Monthly volume, capped
    
    # Adjust by credit score
    multipliers = {
        "A": 2.0,
        "B": 1.5,
        "C": 1.0,
        "D": 0.5,
        "F": 0.25
    }
    
    grade = "A" if score >= 80 else "B" if score >= 65 else "C" if score >= 50 else "D" if score >= 35 else "F"
    
    return round(base_limit * multipliers[grade], -3)  # Round to nearest thousand


def _determine_tier(score: int, years: int, claims: dict) -> str:
    """Determine pricing tier."""
    if score >= 80 and years >= 3:
        return "PREMIER"
    elif score >= 65 and years >= 1:
        return "PREFERRED"
    elif score < 35:
        return "HIGH_RISK"
    else:
        return "STANDARD"
