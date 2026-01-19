"""
RISKCAST Insurance Module V2 - API Routes
==========================================
API endpoints for insurance quote generation, transactions, and claims.
"""

from fastapi import APIRouter, HTTPException, Depends, Body
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

from app.services.insurance_quote_service import InsuranceQuoteService
from app.services.insurance_ai_advisor import InsuranceAIAdvisor
from app.services.insurance_transaction_service import InsuranceTransactionService
from app.services.insurance_claims_service import InsuranceClaimsService
from app.services.payment_processor import PaymentProcessor
from app.services.kyc_aml_service import KYCAMLService
from app.services.carriers.allianz_adapter import AllianzAdapter
from app.services.carriers.swiss_re_adapter import SwissREAdapter
from app.services.parametric_monitoring import get_parametric_monitor
from app.models.insurance import (
    InsuranceQuote, Transaction, TransactionState, 
    InsuredParty, CoverageConfig, Claim, PremiumBreakdown,
    Policy, ParametricTrigger, PayoutStructure, PaymentMethod
)
from app.utils.response import StandardResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/insurance", tags=["Insurance V2"])

# Initialize services
payment_processor = PaymentProcessor()
kyc_service = KYCAMLService()


# ============================================================================
# QUOTE GENERATION
# ============================================================================

@router.post("/quotes/generate")
async def generate_insurance_quotes(
    payload: Dict[str, Any] = Body(...)
) -> StandardResponse:
    """
    Generate insurance quotes based on risk assessment.
    
    Request body:
    {
        "risk_assessment": {...},  // RISKCAST risk assessment result
        "shipment_data": {...}     // Shipment data
    }
    
    Returns:
        List of insurance quotes (classical + parametric)
    """
    try:
        risk_assessment = payload.get("risk_assessment", {})
        shipment_data = payload.get("shipment_data", {})
        
        if not risk_assessment or not shipment_data:
            raise HTTPException(
                status_code=400,
                detail="risk_assessment and shipment_data are required"
            )
        
        # Generate quotes
        quotes = InsuranceQuoteService.generate_quotes(
            risk_assessment=risk_assessment,
            shipment_data=shipment_data
        )
        
        return StandardResponse.success(
            data={
                "quotes": [q.to_dict() for q in quotes],
                "count": len(quotes)
            },
            message=f"Generated {len(quotes)} insurance quote(s)"
        )
        
    except Exception as e:
        logger.error(f"Error generating insurance quotes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quotes/compare")
async def compare_insurance_quotes(
    payload: Dict[str, Any] = Body(...)
) -> StandardResponse:
    """
    Compare multiple insurance quotes.
    
    Request body:
    {
        "quotes": [...]  // List of quote IDs or quote objects
    }
    """
    try:
        quotes_data = payload.get("quotes", [])
        
        if not quotes_data:
            raise HTTPException(status_code=400, detail="quotes array is required")
        
        # Convert to InsuranceQuote objects (simplified - in production, fetch from DB)
        quotes = []
        for q_data in quotes_data:
            # This is simplified - in production, reconstruct from database
            # For now, assume quotes_data contains full quote objects
            if isinstance(q_data, dict) and "quote_id" in q_data:
                # Reconstruct quote from dict
                premium_data = q_data.get("premium", {})
                premium = PremiumBreakdown(
                    base_premium=premium_data.get("base_premium", 0),
                    risk_adjustment=premium_data.get("risk_adjustment", 0),
                    surcharges=premium_data.get("surcharges", []),
                    total_premium=premium_data.get("total_premium", 0),
                    currency=premium_data.get("currency", "USD")
                )
                
                quote = InsuranceQuote(
                    quote_id=q_data["quote_id"],
                    product_id=q_data.get("product_id", ""),
                    premium=premium,
                    transaction_id=q_data.get("transaction_id"),
                    carrier_quote_id=q_data.get("carrier_quote_id"),
                )
                quotes.append(quote)
        
        comparison = InsuranceQuoteService.compare_quotes(quotes)
        
        return StandardResponse.success(
            data=comparison,
            message="Quote comparison completed"
        )
        
    except Exception as e:
        logger.error(f"Error comparing quotes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# TRANSACTION MANAGEMENT
# ============================================================================

@router.post("/transactions/create")
async def create_transaction(
    payload: Dict[str, Any] = Body(...)
) -> StandardResponse:
    """
    Create a new insurance transaction.
    
    Request body:
    {
        "quote_id": "...",
        "riskcast_assessment_id": "...",
        "shipment_reference": "...",
        "insured_party": {...},
        "coverage_config": {...}
    }
    """
    try:
        quote_id = payload.get("quote_id")
        riskcast_assessment_id = payload.get("riskcast_assessment_id")
        shipment_reference = payload.get("shipment_reference")
        insured_party_data = payload.get("insured_party", {})
        coverage_config_data = payload.get("coverage_config", {})
        
        if not all([quote_id, riskcast_assessment_id, shipment_reference]):
            raise HTTPException(
                status_code=400,
                detail="quote_id, riskcast_assessment_id, and shipment_reference are required"
            )
        
        # Build insured party
        insured = InsuredParty(
            legal_name=insured_party_data.get("legal_name", ""),
            registration_number=insured_party_data.get("registration_number", ""),
            country=insured_party_data.get("country", ""),
            address=insured_party_data.get("address", {}),
            contact=insured_party_data.get("contact", {}),
            industry=insured_party_data.get("industry"),
            beneficial_owner=insured_party_data.get("beneficial_owner")
        )
        
        # Build coverage config
        effective_date_str = coverage_config_data.get("effective_date")
        if effective_date_str:
            effective_date = datetime.fromisoformat(effective_date_str.replace('Z', '+00:00'))
        else:
            effective_date = datetime.now()
        
        expiry_date_str = coverage_config_data.get("expiry_date")
        if expiry_date_str:
            expiry_date = datetime.fromisoformat(expiry_date_str.replace('Z', '+00:00'))
        else:
            expiry_date = effective_date + timedelta(days=90)
        
        coverage_config = CoverageConfig(
            sum_insured=coverage_config_data.get("sum_insured", 0),
            deductible=coverage_config_data.get("deductible", 0),
            effective_date=effective_date,
            expiry_date=expiry_date,
            trigger_threshold=coverage_config_data.get("trigger_threshold"),
            payout_per_day=coverage_config_data.get("payout_per_day"),
            max_payout_days=coverage_config_data.get("max_payout_days"),
            max_payout_amount=coverage_config_data.get("max_payout_amount"),
            extensions=coverage_config_data.get("extensions", [])
        )
        
        # Fetch quote (in production, from database)
        # For now, create a mock quote
        from app.models.insurance import PremiumBreakdown
        mock_quote = InsuranceQuote(
            quote_id=quote_id,
            product_id="marine_cargo_icc_a",  # Default
            premium=PremiumBreakdown(
                base_premium=1000,
                risk_adjustment=0,
                total_premium=1000,
                currency="USD"
            )
        )
        
        # Create transaction using service
        transaction = InsuranceTransactionService.create_transaction(
            quote=mock_quote,
            riskcast_assessment_id=riskcast_assessment_id,
            shipment_reference=shipment_reference,
            insured_party=insured,
            coverage_config=coverage_config
        )
        
        return StandardResponse.success(
            data=transaction.to_dict(),
            message="Transaction created successfully"
        )
        
    except Exception as e:
        logger.error(f"Error creating transaction: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transactions/{transaction_id}")
async def get_transaction(transaction_id: str) -> StandardResponse:
    """
    Get transaction details by ID.
    """
    try:
        # In production: Fetch from database
        # For now, return mock data
        return StandardResponse.success(
            data={
                "transaction_id": transaction_id,
                "state": TransactionState.QUOTE_GENERATED.value,
                "message": "Transaction retrieved (mock data)"
            },
            message="Transaction retrieved"
        )
        
    except Exception as e:
        logger.error(f"Error retrieving transaction: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transactions/{transaction_id}/state")
async def update_transaction_state(
    transaction_id: str,
    payload: Dict[str, Any] = Body(...)
) -> StandardResponse:
    """
    Update transaction state (e.g., move to payment, binding, etc.).
    
    Request body:
    {
        "new_state": "payment_pending",
        "reason": "..."
    }
    """
    try:
        new_state = payload.get("new_state")
        reason = payload.get("reason")
        
        if not new_state:
            raise HTTPException(status_code=400, detail="new_state is required")
        
        # Validate state transition
        valid_states = [s.value for s in TransactionState]
        if new_state not in valid_states:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid state. Valid states: {valid_states}"
            )
        
        # In production: Fetch from database
        # For now, create mock transaction
        from app.models.insurance import (
            InsuranceProduct, InsuranceProductCategory, 
            InsuranceProductTier, ProductStatus, PremiumBreakdown
        )
        from app.services.insurance_quote_service import InsuranceQuoteService
        
        # Mock transaction (in production, fetch from DB)
        mock_product = InsuranceProduct(
            product_id="marine_cargo_icc_a",
            name="Marine Cargo Insurance",
            category=InsuranceProductCategory.CLASSICAL,
            tier=InsuranceProductTier.A,
            status=ProductStatus.TRANSACTIONAL,
            description="Test",
            coverage_type="ICC_A",
            pricing_model="classical"
        )
        
        mock_quote = InsuranceQuote(
            quote_id="QUOTE_TEST",
            product_id="marine_cargo_icc_a",
            premium=PremiumBreakdown(
                base_premium=1000,
                risk_adjustment=0,
                total_premium=1000
            )
        )
        
        mock_insured = InsuredParty(
            legal_name="Test Company",
            registration_number="123456",
            country="US",
            address={},
            contact={}
        )
        
        mock_coverage = CoverageConfig(
            sum_insured=100000,
            deductible=5000,
            effective_date=datetime.now(),
            expiry_date=datetime.now()
        )
        
        transaction = Transaction(
            transaction_id=transaction_id,
            state=TransactionState.QUOTE_GENERATED,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            riskcast_assessment_id="TEST",
            shipment_reference="TEST",
            product=mock_product,
            coverage_config=mock_coverage,
            quote=mock_quote,
            insured=mock_insured,
            state_history=[]
        )
        
        # Update state
        new_state_enum = TransactionState(new_state)
        updated_transaction = InsuranceTransactionService.update_state(
            transaction=transaction,
            new_state=new_state_enum,
            reason=reason,
            actor="user"
        )
        
        # Get next steps
        next_steps = InsuranceTransactionService.get_next_steps(updated_transaction)
        
        return StandardResponse.success(
            data={
                "transaction_id": transaction_id,
                "previous_state": TransactionState.QUOTE_GENERATED.value,
                "new_state": new_state,
                "updated_at": updated_transaction.updated_at.isoformat(),
                "next_steps": next_steps
            },
            message=f"Transaction state updated to {new_state}"
        )
        
    except Exception as e:
        logger.error(f"Error updating transaction state: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PAYMENT PROCESSING
# ============================================================================

@router.post("/transactions/{transaction_id}/payment")
async def process_payment(
    transaction_id: str,
    payload: Dict[str, Any] = Body(...)
) -> StandardResponse:
    """
    Process payment for a transaction.
    
    Request body:
    {
        "payment_method": "credit_card" | "wire_transfer" | "net_30",
        "payment_method_id": "...",  // Stripe payment method ID for cards
        "amount": 0.0,
        "currency": "USD"
    }
    """
    try:
        payment_method = payload.get("payment_method")
        payment_method_id = payload.get("payment_method_id")
        amount = payload.get("amount", 0)
        currency = payload.get("currency", "USD")
        
        if not payment_method:
            raise HTTPException(status_code=400, detail="payment_method is required")
        
        # In production: Fetch transaction from database to get amount
        # For now, use amount from payload
        
        if payment_method == PaymentMethod.CREDIT_CARD.value:
            if not payment_method_id:
                raise HTTPException(status_code=400, detail="payment_method_id required for credit card")
            
            # Process via Stripe
            payment_result = await payment_processor.process_payment(
                amount=amount,
                currency=currency,
                payment_method_id=payment_method_id,
                description=f"RISKCAST Insurance - Transaction {transaction_id}",
                metadata={
                    "transaction_id": transaction_id,
                    "payment_method": payment_method
                }
            )
            
            return StandardResponse.success(
                data={
                    "transaction_id": transaction_id,
                    "payment_result": payment_result
                },
                message="Payment processed"
            )
        
        elif payment_method == PaymentMethod.WIRE_TRANSFER.value:
            # Generate wire instructions
            wire_instructions = payment_processor.generate_wire_instructions(
                amount=amount,
                currency=currency,
                reference=f"RISKCAST-{transaction_id}"
            )
            
            return StandardResponse.success(
                data={
                    "transaction_id": transaction_id,
                    "wire_instructions": wire_instructions,
                    "payment_method": "wire_transfer"
                },
                message="Wire transfer instructions generated"
            )
        
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported payment method: {payment_method}"
            )
        
    except Exception as e:
        logger.error(f"Error processing payment: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# KYC/AML
# ============================================================================

@router.post("/kyc/verify")
async def verify_kyc(
    payload: Dict[str, Any] = Body(...)
) -> StandardResponse:
    """
    Perform KYC/AML verification.
    
    Request body:
    {
        "entity_data": {
            "legal_name": "...",
            "registration_number": "...",
            "country": "...",
            "industry": "..."
        },
        "beneficial_owners": [...]  // Optional
    }
    """
    try:
        entity_data = payload.get("entity_data", {})
        beneficial_owners = payload.get("beneficial_owners")
        
        if not entity_data:
            raise HTTPException(status_code=400, detail="entity_data is required")
        
        # Perform full KYC check
        kyc_result = await kyc_service.perform_full_kyc(
            entity_data=entity_data,
            beneficial_owners=beneficial_owners
        )
        
        return StandardResponse.success(
            data=kyc_result,
            message=f"KYC verification completed: {kyc_result['status']}"
        )
        
    except Exception as e:
        logger.error(f"Error performing KYC verification: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CLAIMS
# ============================================================================

@router.post("/claims/submit")
async def submit_claim(
    payload: Dict[str, Any] = Body(...)
) -> StandardResponse:
    """
    Submit an insurance claim.
    
    Request body:
    {
        "policy_number": "...",
        "claim_type": "classical_manual" | "parametric_automatic",
        "incident_date": "...",
        "loss_type": "...",
        "estimated_loss": 0,
        "description": "...",
        "documents": [...]
    }
    """
    try:
        policy_number = payload.get("policy_number")
        claim_type = payload.get("claim_type")
        
        if not policy_number or not claim_type:
            raise HTTPException(
                status_code=400,
                detail="policy_number and claim_type are required"
            )
        
        from app.models.insurance import ClaimType
        from datetime import datetime as dt
        
        if claim_type == ClaimType.CLASSICAL_MANUAL.value:
            # Classical manual claim
            incident_date_str = payload.get("incident_date")
            incident_date = dt.fromisoformat(incident_date_str.replace('Z', '+00:00')) if incident_date_str else dt.now()
            
            claim = await InsuranceClaimsService.create_classical_claim(
                policy_number=policy_number,
                incident_date=incident_date,
                loss_type=payload.get("loss_type", ""),
                estimated_loss=payload.get("estimated_loss", 0),
                description=payload.get("description", ""),
                documents=payload.get("documents", [])
            )
            
            # Forward to carrier
            carrier_response = await InsuranceClaimsService.forward_to_carrier(claim)
            
            return StandardResponse.success(
                data={
                    **claim.to_dict(),
                    "carrier_response": carrier_response
                },
                message="Classical claim submitted successfully"
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid claim_type: {claim_type}. Use 'classical_manual' for manual claims."
            )
        
    except Exception as e:
        logger.error(f"Error submitting claim: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/claims/{claim_number}")
async def get_claim(claim_number: str) -> StandardResponse:
    """
    Get claim details by claim number.
    """
    try:
        claim = await InsuranceClaimsService.get_claim_status(claim_number)
        
        if claim:
            return StandardResponse.success(
                data=claim.to_dict(),
                message="Claim retrieved"
            )
        else:
            return StandardResponse.success(
                data={
                    "claim_number": claim_number,
                    "status": "not_found",
                    "message": "Claim not found (mock - implement database lookup)"
                },
                message="Claim not found"
            )
        
    except Exception as e:
        logger.error(f"Error retrieving claim: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PRODUCT CATALOG
# ============================================================================

@router.get("/products")
async def list_products() -> StandardResponse:
    """
    List available insurance products.
    """
    try:
        products = list(InsuranceQuoteService.PRODUCT_CATALOG.values())
        
        return StandardResponse.success(
            data={"products": products},
            message=f"Retrieved {len(products)} products"
        )
        
    except Exception as e:
        logger.error(f"Error listing products: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products/{product_id}")
async def get_product(product_id: str) -> StandardResponse:
    """
    Get product details by ID.
    """
    try:
        product = InsuranceQuoteService.PRODUCT_CATALOG.get(product_id)
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return StandardResponse.success(
            data={"product": product},
            message="Product retrieved"
        )
        
    except Exception as e:
        logger.error(f"Error retrieving product: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CARRIER INTEGRATION
# ============================================================================

@router.post("/carriers/allianz/quote")
async def get_allianz_quote(
    payload: Dict[str, Any] = Body(...)
) -> StandardResponse:
    """
    Get quote directly from Allianz AGCS.
    
    Request body:
    {
        "shipment": {...},
        "coverage": {...},
        "risk_data": {...}
    }
    """
    try:
        import os
        api_key = os.getenv("ALLIANZ_API_KEY", "mock_key")
        
        adapter = AllianzAdapter(api_key=api_key)
        
        # Build quote request
        from app.models.insurance import CarrierQuoteRequest
        quote_request = CarrierQuoteRequest(**payload)
        
        # Get quote
        quote_response = await adapter.get_quote(quote_request)
        
        return StandardResponse.success(
            data=quote_response.__dict__ if hasattr(quote_response, '__dict__') else quote_response,
            message="Allianz quote retrieved"
        )
        
    except Exception as e:
        logger.error(f"Error getting Allianz quote: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/carriers/swiss-re/quote")
async def get_swiss_re_quote(
    payload: Dict[str, Any] = Body(...)
) -> StandardResponse:
    """
    Get parametric quote from Swiss RE.
    """
    try:
        import os
        api_key = os.getenv("SWISS_RE_API_KEY", "mock_key")
        
        adapter = SwissREAdapter(api_key=api_key)
        
        from app.models.insurance import CarrierQuoteRequest
        quote_request = CarrierQuoteRequest(**payload)
        
        quote_response = await adapter.get_quote(quote_request)
        
        return StandardResponse.success(
            data=quote_response.__dict__ if hasattr(quote_response, '__dict__') else quote_response,
            message="Swiss RE quote retrieved"
        )
        
    except Exception as e:
        logger.error(f"Error getting Swiss RE quote: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# AI ADVISOR
# ============================================================================

@router.post("/advisor/why-buy")
async def advisor_why_buy_insurance(
    payload: Dict[str, Any] = Body(...)
) -> StandardResponse:
    """
    AI Advisor: Answer "Why should I buy insurance?"
    
    Request body:
    {
        "risk_assessment": {...},
        "user_profile": {...}  // Optional
    }
    """
    try:
        risk_assessment = payload.get("risk_assessment", {})
        user_profile = payload.get("user_profile")
        
        if not risk_assessment:
            raise HTTPException(status_code=400, detail="risk_assessment is required")
        
        response = InsuranceAIAdvisor.answer_why_buy_insurance(
            risk_assessment=risk_assessment,
            user_profile=user_profile
        )
        
        return StandardResponse.success(
            data=InsuranceAIAdvisor.to_dict(response),
            message="AI Advisor response generated"
        )
        
    except Exception as e:
        logger.error(f"Error generating AI advisor response: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/advisor/explain-product")
async def advisor_explain_product(
    payload: Dict[str, Any] = Body(...)
) -> StandardResponse:
    """
    AI Advisor: Explain why a product is recommended.
    
    Request body:
    {
        "product_id": "...",
        "risk_assessment": {...}
    }
    """
    try:
        product_id = payload.get("product_id")
        risk_assessment = payload.get("risk_assessment", {})
        
        if not product_id:
            raise HTTPException(status_code=400, detail="product_id is required")
        
        # Get product
        product_data = InsuranceQuoteService.PRODUCT_CATALOG.get(product_id)
        if not product_data:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Build product object (simplified)
        from app.models.insurance import InsuranceProduct, InsuranceProductCategory, InsuranceProductTier, ProductStatus
        product = InsuranceProduct(
            product_id=product_data["product_id"],
            name=product_data["name"],
            category=InsuranceProductCategory(product_data["category"]),
            tier=InsuranceProductTier(product_data["tier"]),
            status=ProductStatus(product_data["status"]),
            description=product_data["description"],
            coverage_type=product_data.get("coverage_type", ""),
            pricing_model=product_data.get("pricing_model", "classical")
        )
        
        # Get alternatives (simplified - just other products)
        alternatives = []
        for alt_id, alt_data in InsuranceQuoteService.PRODUCT_CATALOG.items():
            if alt_id != product_id:
                alt = InsuranceProduct(
                    product_id=alt_data["product_id"],
                    name=alt_data["name"],
                    category=InsuranceProductCategory(alt_data["category"]),
                    tier=InsuranceProductTier(alt_data["tier"]),
                    status=ProductStatus(alt_data["status"]),
                    description=alt_data["description"],
                    coverage_type=alt_data.get("coverage_type", ""),
                    pricing_model=alt_data.get("pricing_model", "classical")
                )
                alternatives.append(alt)
        
        response = InsuranceAIAdvisor.explain_product_recommendation(
            selected_product=product,
            alternatives=alternatives,
            risk_assessment=risk_assessment
        )
        
        return StandardResponse.success(
            data=InsuranceAIAdvisor.to_dict(response),
            message="Product explanation generated"
        )
        
    except Exception as e:
        logger.error(f"Error generating product explanation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/advisor/explain-pricing")
async def advisor_explain_pricing(
    payload: Dict[str, Any] = Body(...)
) -> StandardResponse:
    """
    AI Advisor: Explain how premium was calculated.
    
    Request body:
    {
        "quote": {...},  // Insurance quote object
        "risk_assessment": {...}
    }
    """
    try:
        quote_data = payload.get("quote", {})
        risk_assessment = payload.get("risk_assessment", {})
        
        if not quote_data:
            raise HTTPException(status_code=400, detail="quote is required")
        
        # Reconstruct quote (simplified)
        from app.models.insurance import PricingBreakdown
        
        premium_data = quote_data.get("premium", {})
        premium = PremiumBreakdown(
            base_premium=premium_data.get("base_premium", 0),
            risk_adjustment=premium_data.get("risk_adjustment", 0),
            surcharges=premium_data.get("surcharges", []),
            total_premium=premium_data.get("total_premium", 0),
            currency=premium_data.get("currency", "USD")
        )
        
        pricing_data = quote_data.get("pricing_breakdown")
        pricing_breakdown = None
        if pricing_data:
            pricing_breakdown = PricingBreakdown(
                expected_loss=pricing_data.get("expected_loss", 0),
                load_factor=pricing_data.get("load_factor", 1.0),
                administrative_costs=pricing_data.get("administrative_costs", 0),
                risk_adjustments=pricing_data.get("risk_adjustments", [])
            )
        
        quote = InsuranceQuote(
            quote_id=quote_data.get("quote_id", ""),
            product_id=quote_data.get("product_id", ""),
            premium=premium,
            pricing_breakdown=pricing_breakdown
        )
        
        response = InsuranceAIAdvisor.explain_pricing_calculation(
            quote=quote,
            risk_assessment=risk_assessment
        )
        
        return StandardResponse.success(
            data=InsuranceAIAdvisor.to_dict(response),
            message="Pricing explanation generated"
        )
        
    except Exception as e:
        logger.error(f"Error generating pricing explanation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/advisor/educate-parametric")
async def advisor_educate_parametric() -> StandardResponse:
    """
    AI Advisor: Educate about parametric insurance.
    """
    try:
        response = InsuranceAIAdvisor.educate_parametric()
        
        return StandardResponse.success(
            data=InsuranceAIAdvisor.to_dict(response),
            message="Parametric insurance education"
        )
        
    except Exception as e:
        logger.error(f"Error generating education: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PARAMETRIC MONITORING
# ============================================================================

@router.post("/policies/{policy_number}/register-monitoring")
async def register_policy_monitoring(
    policy_number: str,
    payload: Dict[str, Any] = Body(...)
) -> StandardResponse:
    """
    Register a policy for parametric monitoring.
    
    Request body:
    {
        "trigger": {...},  // ParametricTrigger
        "payout_structure": {...}  // PayoutStructure
    }
    """
    try:
        # Build policy object (in production, fetch from database)
        from app.models.insurance import (
            InsuranceProduct, InsuranceProductCategory,
            InsuranceProductTier, ProductStatus
        )
        
        trigger_data = payload.get("trigger", {})
        trigger = ParametricTrigger(**trigger_data)
        
        payout_data = payload.get("payout_structure", {})
        payout_structure = PayoutStructure(**payout_data) if payout_data else None
        
        # Mock policy (in production, fetch from DB)
        policy = Policy(
            policy_number=policy_number,
            transaction_id="TXN_MOCK",
            product=InsuranceProduct(
                product_id="port_delay_parametric",
                name="Port Delay Parametric",
                category=InsuranceProductCategory.PARAMETRIC,
                tier=InsuranceProductTier.B,
                status=ProductStatus.API_PARAMETRIC,
                description="Test",
                coverage_type="parametric",
                pricing_model="parametric"
            ),
            coverage_config=CoverageConfig(
                sum_insured=100000,
                deductible=0,
                effective_date=datetime.now(),
                expiry_date=datetime.now()
            ),
            insured=InsuredParty(
                legal_name="Test",
                registration_number="123",
                country="US",
                address={},
                contact={}
            ),
            premium=1000,
            effective_date=datetime.now(),
            expiry_date=datetime.now() + timedelta(days=90),
            status="active",
            trigger=trigger,
            payout_structure=payout_structure,
            monitoring_enabled=True
        )
        
        # Register with monitor
        monitor = get_parametric_monitor()
        monitor.register_policy(policy)
        
        return StandardResponse.success(
            data={
                "policy_number": policy_number,
                "monitoring_enabled": True,
                "trigger_type": trigger.trigger_type
            },
            message="Policy registered for parametric monitoring"
        )
        
    except Exception as e:
        logger.error(f"Error registering policy monitoring: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/policies/{policy_number}/check-trigger")
async def check_policy_trigger(
    policy_number: str
) -> StandardResponse:
    """
    Manually check if a policy's trigger has been met.
    """
    try:
        monitor = get_parametric_monitor()
        evaluation = await monitor.check_policy(policy_number)
        
        if evaluation:
            return StandardResponse.success(
                data={
                    "policy_number": policy_number,
                    "triggered": evaluation.triggered,
                    "payout_amount": evaluation.payout_amount if evaluation.triggered else 0,
                    "reason": evaluation.reason,
                    "trigger_evidence": evaluation.trigger_evidence
                },
                message="Trigger check completed"
            )
        else:
            return StandardResponse.success(
                data={
                    "policy_number": policy_number,
                    "triggered": False,
                    "message": "Policy not found or not monitored"
                },
                message="Trigger check completed"
            )
        
    except Exception as e:
        logger.error(f"Error checking policy trigger: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
