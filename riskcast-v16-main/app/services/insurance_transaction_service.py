"""
RISKCAST Insurance Transaction Service
======================================
Manages insurance transaction state machine and workflow.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from uuid import uuid4
import logging

from app.models.insurance import (
    Transaction, TransactionState, StateTransition,
    InsuredParty, CoverageConfig, InsuranceQuote, InsuranceProduct
)

logger = logging.getLogger(__name__)


class TransactionStateMachine:
    """
    State machine for insurance transactions.
    """
    
    # Valid state transitions
    VALID_TRANSITIONS = {
        TransactionState.QUOTE_REQUESTED: [TransactionState.QUOTE_GENERATED],
        TransactionState.QUOTE_GENERATED: [
            TransactionState.CONFIGURING,
            TransactionState.KYC_REQUIRED,
            TransactionState.CANCELLED
        ],
        TransactionState.CONFIGURING: [TransactionState.CONFIGURED],
        TransactionState.CONFIGURED: [TransactionState.KYC_REQUIRED],
        TransactionState.KYC_REQUIRED: [TransactionState.KYC_IN_PROGRESS],
        TransactionState.KYC_IN_PROGRESS: [
            TransactionState.KYC_APPROVED,
            TransactionState.KYC_FAILED
        ],
        TransactionState.KYC_APPROVED: [TransactionState.PAYMENT_PENDING],
        TransactionState.PAYMENT_PENDING: [TransactionState.PAYMENT_PROCESSING],
        TransactionState.PAYMENT_PROCESSING: [
            TransactionState.PAYMENT_COMPLETED,
            TransactionState.PAYMENT_FAILED
        ],
        TransactionState.PAYMENT_COMPLETED: [TransactionState.BINDING],
        TransactionState.BINDING: [
            TransactionState.BOUND,
            TransactionState.PAYMENT_FAILED  # If binding fails, refund
        ],
        TransactionState.BOUND: [TransactionState.POLICY_DELIVERED],
        TransactionState.POLICY_DELIVERED: [TransactionState.ACTIVE],
        TransactionState.ACTIVE: [
            TransactionState.CLAIM_FILED,
            TransactionState.EXPIRED,
            TransactionState.CANCELLED
        ],
        TransactionState.CLAIM_FILED: [TransactionState.CLAIM_SETTLED],
    }
    
    @staticmethod
    def can_transition(from_state: TransactionState, to_state: TransactionState) -> bool:
        """Check if state transition is valid."""
        allowed = TransactionStateMachine.VALID_TRANSITIONS.get(from_state, [])
        return to_state in allowed
    
    @staticmethod
    def transition(
        transaction: Transaction,
        new_state: TransactionState,
        reason: Optional[str] = None,
        actor: str = "system"
    ) -> Transaction:
        """
        Transition transaction to new state.
        
        Args:
            transaction: Transaction object
            new_state: Target state
            reason: Reason for transition
            actor: Who initiated transition ('system', 'user', 'carrier')
            
        Returns:
            Updated transaction
        """
        # Validate transition
        if not TransactionStateMachine.can_transition(transaction.state, new_state):
            raise ValueError(
                f"Invalid state transition from {transaction.state.value} to {new_state.value}"
            )
        
        # Record transition
        transition = StateTransition(
            from_state=transaction.state,
            to_state=new_state,
            timestamp=datetime.now(),
            reason=reason,
            actor=actor
        )
        
        # Update transaction
        transaction.state = new_state
        transaction.updated_at = datetime.now()
        transaction.state_history.append(transition)
        
        logger.info(
            f"Transaction {transaction.transaction_id} transitioned: "
            f"{transition.from_state.value} -> {transition.to_state.value}"
        )
        
        return transaction


class InsuranceTransactionService:
    """
    Service for managing insurance transactions.
    """
    
    @staticmethod
    def create_transaction(
        quote: InsuranceQuote,
        riskcast_assessment_id: str,
        shipment_reference: str,
        insured_party: InsuredParty,
        coverage_config: CoverageConfig
    ) -> Transaction:
        """
        Create a new insurance transaction.
        
        Args:
            quote: Insurance quote
            riskcast_assessment_id: RISKCAST assessment ID
            shipment_reference: Shipment reference
            insured_party: Insured party information
            coverage_config: Coverage configuration
            
        Returns:
            Created transaction
        """
        transaction_id = f"TXN_{datetime.now().strftime('%Y%m%d')}_{uuid4().hex[:8].upper()}"
        
        # Get product (simplified - in production, fetch from DB)
        from app.services.insurance_quote_service import InsuranceQuoteService
        product_data = InsuranceQuoteService.PRODUCT_CATALOG.get(quote.product_id)
        
        if not product_data:
            raise ValueError(f"Product {quote.product_id} not found")
        
        # Build product object
        from app.models.insurance import (
            InsuranceProduct, InsuranceProductCategory, 
            InsuranceProductTier, ProductStatus
        )
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
        
        # Create transaction
        transaction = Transaction(
            transaction_id=transaction_id,
            state=TransactionState.QUOTE_GENERATED,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            riskcast_assessment_id=riskcast_assessment_id,
            shipment_reference=shipment_reference,
            product=product,
            coverage_config=coverage_config,
            quote=quote,
            insured=insured_party,
            state_history=[]
        )
        
        # Record initial state
        initial_transition = StateTransition(
            from_state=TransactionState.QUOTE_REQUESTED,
            to_state=TransactionState.QUOTE_GENERATED,
            timestamp=datetime.now(),
            reason="Quote generated",
            actor="system"
        )
        transaction.state_history.append(initial_transition)
        
        return transaction
    
    @staticmethod
    def update_state(
        transaction: Transaction,
        new_state: TransactionState,
        reason: Optional[str] = None,
        actor: str = "system"
    ) -> Transaction:
        """
        Update transaction state.
        
        Args:
            transaction: Transaction to update
            new_state: New state
            reason: Reason for state change
            actor: Who initiated change
            
        Returns:
            Updated transaction
        """
        return TransactionStateMachine.transition(
            transaction=transaction,
            new_state=new_state,
            reason=reason,
            actor=actor
        )
    
    @staticmethod
    def get_next_steps(transaction: Transaction) -> List[Dict[str, Any]]:
        """
        Get next possible steps for a transaction.
        
        Args:
            transaction: Current transaction
            
        Returns:
            List of possible next steps
        """
        current_state = transaction.state
        allowed_states = TransactionStateMachine.VALID_TRANSITIONS.get(current_state, [])
        
        steps = []
        for state in allowed_states:
            step_info = {
                "state": state.value,
                "description": InsuranceTransactionService._get_state_description(state),
                "action_required": InsuranceTransactionService._get_action_required(state)
            }
            steps.append(step_info)
        
        return steps
    
    @staticmethod
    def _get_state_description(state: TransactionState) -> str:
        """Get human-readable description of state."""
        descriptions = {
            TransactionState.CONFIGURING: "Configure coverage parameters",
            TransactionState.KYC_REQUIRED: "Complete identity verification",
            TransactionState.PAYMENT_PENDING: "Complete payment",
            TransactionState.BINDING: "Policy is being bound with carrier",
            TransactionState.BOUND: "Policy has been issued",
            TransactionState.ACTIVE: "Policy is active and coverage is in effect",
        }
        return descriptions.get(state, state.value.replace("_", " ").title())
    
    @staticmethod
    def _get_action_required(state: TransactionState) -> str:
        """Get action required for state."""
        actions = {
            TransactionState.CONFIGURING: "user",
            TransactionState.KYC_REQUIRED: "user",
            TransactionState.PAYMENT_PENDING: "user",
            TransactionState.BINDING: "system",
            TransactionState.BOUND: "system",
        }
        return actions.get(state, "none")
