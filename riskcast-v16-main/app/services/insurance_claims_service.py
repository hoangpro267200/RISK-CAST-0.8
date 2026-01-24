"""
RISKCAST Insurance Claims Processing Service
============================================
Handles both parametric (automatic) and classical (manual) claims.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from uuid import uuid4
import logging

from app.models.insurance import (
    Claim, ClaimType, Policy, TriggerEvaluation
)
from app.core.parametric.exceptions import PayoutBlockedError, InvalidTriggerEvaluationError
from app.config import settings
from app.services.parametric_monitoring import get_parametric_monitor

logger = logging.getLogger(__name__)


class InsuranceClaimsService:
    """
    Service for processing insurance claims.
    """
    
    @staticmethod
    def _has_real_oracle_evidence(trigger_evidence: Optional[Dict[str, Any]]) -> bool:
        """
        Check if trigger evidence is from real oracle (not stub).
        
        Args:
            trigger_evidence: Trigger evidence dictionary
            
        Returns:
            True if evidence is from real oracle, False otherwise
        """
        if not trigger_evidence:
            return False
        
        data_source = trigger_evidence.get("data_source", "").upper()
        source = trigger_evidence.get("source", "").upper()
        
        # Check for stub/mock indicators
        if "STUB" in data_source or "STUB" in source:
            return False
        
        if "MOCK" in data_source or "MOCK" in source:
            return False
        
        # If data_source is missing, assume it might be stub
        if not data_source and not source:
            return False
        
        return True
    
    @staticmethod
    def _check_payout_safety_guards(
        trigger_evaluation: TriggerEvaluation,
        trigger_evidence: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Check safety guards before allowing payout.
        
        Args:
            trigger_evaluation: Trigger evaluation result
            trigger_evidence: Trigger evidence data
            
        Raises:
            PayoutBlockedError: If payout is blocked by safety guards
        """
        # Check if payouts are enabled
        if not settings.PARAMETRIC_PAYOUTS_ENABLED:
            raise PayoutBlockedError(
                "Parametric payouts are disabled. "
                "Set PARAMETRIC_PAYOUTS_ENABLED=true to enable payouts."
            )
        
        # Check if evidence is from real oracle
        evidence = trigger_evidence or trigger_evaluation.trigger_evidence
        if not InsuranceClaimsService._has_real_oracle_evidence(evidence):
            raise PayoutBlockedError(
                "Payout requires real oracle data. "
                "Configure oracle providers before enabling payouts. "
                f"Evidence data_source: {evidence.get('data_source') if evidence else 'missing'}"
            )
        
        # Check required oracle sources are configured
        monitor = get_parametric_monitor()
        for source in settings.REQUIRED_ORACLE_SOURCES:
            if not monitor.is_oracle_configured(source):
                raise PayoutBlockedError(
                    f"Payout requires configured oracle: '{source}'. "
                    f"Configure {source} oracle provider before enabling payouts."
                )
    
    @staticmethod
    async def create_parametric_claim(
        policy_number: str,
        trigger_evaluation: TriggerEvaluation,
        trigger_evidence: Optional[Dict[str, Any]] = None
    ) -> Claim:
        """
        Create automatic parametric claim.
        
        Includes safety guards to prevent payouts without real oracle data.
        
        Args:
            policy_number: Policy number
            trigger_evaluation: Trigger evaluation result
            trigger_evidence: Trigger evidence data
            
        Returns:
            Created claim
            
        Raises:
            PayoutBlockedError: If payout is blocked by safety guards
        """
        # Check safety guards before creating claim
        InsuranceClaimsService._check_payout_safety_guards(trigger_evaluation, trigger_evidence)
        
        claim_number = f"CLM-{datetime.now().strftime('%Y%m%d')}-{uuid4().hex[:6].upper()}"
        
        claim = Claim(
            claim_number=claim_number,
            policy_number=policy_number,
            claim_type=ClaimType.PARAMETRIC_AUTOMATIC,
            trigger_date=datetime.now(),
            trigger_event=trigger_evidence or trigger_evaluation.trigger_evidence,
            payout_amount=trigger_evaluation.payout_amount,
            status="verified",
            evidence={
                "trigger_data": trigger_evidence,
                "verification": {
                    "verified": True,
                    "verified_at": datetime.now().isoformat(),
                    "data_source": trigger_evidence.get("data_source") if trigger_evidence else "unknown"
                }
            },
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        logger.info(
            f"Created parametric claim {claim_number} for policy {policy_number}: "
            f"Payout=${trigger_evaluation.payout_amount:,.2f}"
        )
        
        # In production, save to database
        # await db.claims.create(claim.to_dict())
        
        return claim
    
    @staticmethod
    async def create_classical_claim(
        policy_number: str,
        incident_date: datetime,
        loss_type: str,
        estimated_loss: float,
        description: str,
        documents: List[Dict[str, str]]
    ) -> Claim:
        """
        Create manual classical claim.
        
        Args:
            policy_number: Policy number
            incident_date: Date of incident
            loss_type: Type of loss
            estimated_loss: Estimated loss amount
            description: Claim description
            documents: Supporting documents
            
        Returns:
            Created claim
        """
        claim_number = f"CLM-{datetime.now().strftime('%Y%m%d')}-{uuid4().hex[:6].upper()}"
        
        claim = Claim(
            claim_number=claim_number,
            policy_number=policy_number,
            claim_type=ClaimType.CLASSICAL_MANUAL,
            incident_date=incident_date,
            loss_type=loss_type,
            estimated_loss=estimated_loss,
            description=description,
            status="submitted",
            evidence={
                "documents": documents
            },
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        logger.info(
            f"Created classical claim {claim_number} for policy {policy_number}: "
            f"Estimated loss=${estimated_loss:,.2f}"
        )
        
        # In production, save to database and forward to carrier
        # await db.claims.create(claim.to_dict())
        # await forward_to_carrier(claim)
        
        return claim
    
    @staticmethod
    async def process_parametric_payout(claim: Claim) -> Dict[str, Any]:
        """
        Process parametric claim payout.
        
        Includes safety guards to prevent payouts without real oracle data.
        
        Args:
            claim: Parametric claim
            
        Returns:
            Payout processing result
            
        Raises:
            PayoutBlockedError: If payout is blocked by safety guards
        """
        if claim.claim_type != ClaimType.PARAMETRIC_AUTOMATIC:
            raise ValueError("This method only processes parametric claims")
        
        if not claim.payout_amount:
            raise ValueError("Claim does not have payout amount")
        
        # Check safety guards before processing payout
        trigger_evidence = claim.trigger_event if hasattr(claim, 'trigger_event') else claim.evidence.get("trigger_data") if claim.evidence else None
        
        # Re-check evidence is real (defense in depth)
        if not InsuranceClaimsService._has_real_oracle_evidence(trigger_evidence):
            raise PayoutBlockedError(
                "Payout blocked: Claim evidence is not from real oracle. "
                "Cannot process payout with stub/mock data."
            )
        
        # Re-check payouts are enabled (defense in depth)
        if not settings.PARAMETRIC_PAYOUTS_ENABLED:
            raise PayoutBlockedError(
                "Payout blocked: Parametric payouts are disabled in settings."
            )
        
        try:
            # Update claim status
            claim.status = "payout_initiated"
            claim.updated_at = datetime.now()
            
            logger.info(
                f"Processing parametric payout for claim {claim.claim_number}: "
                f"${claim.payout_amount:,.2f}"
            )
            
            # In production:
            # 1. Verify trigger with secondary data source
            # 2. Initiate bank transfer via Stripe/payment provider
            # 3. Update claim status
            # 4. Send confirmation email
            
            # Mock payout processing
            payment_reference = f"PAY-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            claim.status = "paid"
            claim.paid_at = datetime.now()
            claim.payment_reference = payment_reference
            claim.payment_amount = claim.payout_amount
            claim.updated_at = datetime.now()
            
            logger.info(
                f"Parametric payout completed for claim {claim.claim_number}: "
                f"Payment reference: {payment_reference}"
            )
            
            return {
                "claim_number": claim.claim_number,
                "payout_amount": claim.payout_amount,
                "payment_reference": payment_reference,
                "paid_at": claim.paid_at.isoformat(),
                "status": "paid"
            }
            
        except Exception as e:
            logger.error(f"Error processing parametric payout: {e}", exc_info=True)
            claim.status = "rejected"
            claim.updated_at = datetime.now()
            raise
    
    @staticmethod
    async def verify_trigger_with_secondary_source(
        trigger_evidence: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Verify trigger with secondary data source to reduce basis risk.
        
        Args:
            trigger_evidence: Primary trigger evidence
            
        Returns:
            Verification result
        """
        # In production, fetch from secondary data source
        # For example, if primary is Tomorrow.io, verify with local meteorological service
        
        logger.info("Verifying trigger with secondary data source")
        
        # Mock verification (always confirm for now)
        return {
            "confirmed": True,
            "secondary_source": "local_meteorological_service",
            "verified_at": datetime.now().isoformat(),
            "confidence": 0.95
        }
    
    @staticmethod
    async def forward_to_carrier(claim: Claim) -> Dict[str, Any]:
        """
        Forward classical claim to carrier for processing.
        
        Args:
            claim: Classical claim
            
        Returns:
            Carrier response
        """
        if claim.claim_type != ClaimType.CLASSICAL_MANUAL:
            raise ValueError("This method only processes classical claims")
        
        # In production:
        # 1. Get policy to find carrier
        # 2. Use appropriate carrier adapter
        # 3. Submit claim via carrier API
        # 4. Store carrier claim reference
        
        logger.info(f"Forwarding claim {claim.claim_number} to carrier")
        
        # Mock carrier response
        return {
            "carrier_claim_number": f"CARRIER-CLM-{datetime.now().strftime('%Y%m%d')}",
            "carrier_claim_id": f"carrier-{uuid4().hex[:8]}",
            "adjuster_name": "John Smith",
            "adjuster_contact": "john.smith@carrier.com",
            "estimated_processing_days": 30
        }
    
    @staticmethod
    async def get_claim_status(claim_number: str) -> Optional[Claim]:
        """
        Get claim status by claim number.
        
        Args:
            claim_number: Claim number
            
        Returns:
            Claim object or None
        """
        # In production, fetch from database
        # return await db.claims.find_one({"claim_number": claim_number})
        
        logger.info(f"Fetching claim status for {claim_number}")
        return None  # Mock - would fetch from DB
