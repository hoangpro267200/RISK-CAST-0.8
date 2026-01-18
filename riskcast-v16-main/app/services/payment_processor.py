"""
RISKCAST Payment Processing Service
====================================
Handles payment processing via Stripe and other payment methods.
"""

from typing import Dict, Optional, Any
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)

# Stripe will be imported conditionally
try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False
    logger.warning("Stripe not installed. Payment processing will be mocked.")


class PaymentProcessor:
    """
    Payment processing service.
    Supports Stripe, wire transfers, and enterprise net terms.
    """
    
    def __init__(self):
        self.stripe_key = os.getenv("STRIPE_SECRET_KEY", "")
        if STRIPE_AVAILABLE and self.stripe_key:
            stripe.api_key = self.stripe_key
            self.stripe_enabled = True
        else:
            self.stripe_enabled = False
            logger.warning("Stripe not configured. Using mock payment processing.")
    
    async def process_payment(
        self,
        amount: float,
        currency: str,
        payment_method_id: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process payment via Stripe.
        
        Args:
            amount: Payment amount
            currency: Currency code (e.g., 'USD')
            payment_method_id: Stripe payment method ID
            description: Payment description
            metadata: Additional metadata
            
        Returns:
            Payment result
        """
        if not self.stripe_enabled:
            # Mock payment processing
            return await self._mock_payment(amount, currency, description)
        
        try:
            # Create payment intent
            payment_intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Convert to cents
                currency=currency.lower(),
                payment_method=payment_method_id,
                confirm=True,
                description=description,
                metadata=metadata or {}
            )
            
            if payment_intent.status == 'succeeded':
                return {
                    "status": "completed",
                    "payment_id": payment_intent.id,
                    "amount": amount,
                    "currency": currency,
                    "paid_at": datetime.fromisoformat(
                        payment_intent.created.isoformat()
                    ) if hasattr(payment_intent, 'created') else datetime.now(),
                    "payment_method_details": {
                        "type": payment_intent.payment_method_types[0] if payment_intent.payment_method_types else "card",
                        "last4": None  # Would extract from payment_method
                    }
                }
            
            elif payment_intent.status == 'requires_action':
                return {
                    "status": "requires_action",
                    "client_secret": payment_intent.client_secret,
                    "next_action": payment_intent.next_action
                }
            
            else:
                return {
                    "status": "failed",
                    "error": payment_intent.last_payment_error.message if hasattr(payment_intent, 'last_payment_error') else "Payment failed"
                }
                
        except Exception as e:
            logger.error(f"Stripe payment error: {e}", exc_info=True)
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def process_payout(
        self,
        amount: float,
        destination_account_id: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process payout (for parametric claims).
        
        Args:
            amount: Payout amount
            destination_account_id: Stripe connected account ID or bank account
            description: Payout description
            metadata: Additional metadata
            
        Returns:
            Payout result
        """
        if not self.stripe_enabled:
            # Mock payout
            return await self._mock_payout(amount, description)
        
        try:
            # Create transfer
            transfer = stripe.Transfer.create(
                amount=int(amount * 100),  # Convert to cents
                currency="usd",
                destination=destination_account_id,
                description=description,
                metadata=metadata or {}
            )
            
            return {
                "status": "completed",
                "transfer_id": transfer.id,
                "amount": amount,
                "currency": "usd",
                "transferred_at": datetime.now(),
                "destination": destination_account_id
            }
            
        except Exception as e:
            logger.error(f"Stripe payout error: {e}", exc_info=True)
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def generate_wire_instructions(
        self,
        amount: float,
        currency: str,
        reference: str
    ) -> Dict[str, Any]:
        """
        Generate wire transfer instructions.
        
        Args:
            amount: Payment amount
            currency: Currency code
            reference: Payment reference
            
        Returns:
            Wire transfer instructions
        """
        return {
            "beneficiary_name": "RISKCAST Insurance Operations Ltd",
            "beneficiary_account": "1234567890",
            "bank_name": "JPMorgan Chase Bank",
            "bank_address": "270 Park Avenue, New York, NY 10017",
            "swift_code": "CHASUS33",
            "routing_number": "021000021",
            "reference": reference,
            "amount": amount,
            "currency": currency,
            "payment_deadline": (datetime.now().replace(hour=23, minute=59, second=59) + 
                                __import__('datetime').timedelta(days=3)).isoformat(),
            "instructions": [
                "Include transaction reference in payment notes",
                "Policy will be issued within 24 hours of payment confirmation",
                "Wire transfer fees are responsibility of sender"
            ]
        }
    
    async def _mock_payment(
        self,
        amount: float,
        currency: str,
        description: str
    ) -> Dict[str, Any]:
        """Mock payment processing (for development)."""
        logger.info(f"Mock payment: ${amount} {currency} - {description}")
        
        return {
            "status": "completed",
            "payment_id": f"mock_pay_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "amount": amount,
            "currency": currency,
            "paid_at": datetime.now(),
            "payment_method_details": {
                "type": "card",
                "last4": "4242"
            }
        }
    
    async def _mock_payout(
        self,
        amount: float,
        description: str
    ) -> Dict[str, Any]:
        """Mock payout processing (for development)."""
        logger.info(f"Mock payout: ${amount} - {description}")
        
        return {
            "status": "completed",
            "transfer_id": f"mock_transfer_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "amount": amount,
            "currency": "usd",
            "transferred_at": datetime.now()
        }
