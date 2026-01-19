"""
RISKCAST Insurance Webhook Handlers
====================================
Webhook endpoints for external data providers (port, weather, catastrophe).
"""

from fastapi import APIRouter, HTTPException, Header, Request
from typing import Dict, Optional, Any
import hmac
import hashlib
import logging
from datetime import datetime

from app.services.parametric_monitoring import get_parametric_monitor
from app.models.insurance import Policy

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks/insurance", tags=["Insurance Webhooks"])


def verify_webhook_signature(
    payload: bytes,
    signature: str,
    secret: str
) -> bool:
    """
    Verify webhook signature using HMAC.
    
    Args:
        payload: Request payload
        signature: Signature from header
        secret: Webhook secret
        
    Returns:
        True if signature is valid
    """
    expected_signature = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_signature, signature)


@router.post("/port-update/{policy_number}")
async def handle_port_update_webhook(
    policy_number: str,
    payload: Dict[str, Any],
    request: Request,
    x_signature: Optional[str] = Header(None, alias="X-Signature")
) -> Dict[str, Any]:
    """
    Handle port congestion update webhook.
    
    Webhook from port authority or MarineTraffic API.
    """
    try:
        # Verify webhook signature (in production)
        # webhook_secret = os.getenv("PORT_WEBHOOK_SECRET")
        # if not verify_webhook_signature(await request.body(), x_signature, webhook_secret):
        #     raise HTTPException(status_code=401, detail="Invalid webhook signature")
        
        logger.info(f"Received port update webhook for policy {policy_number}")
        
        # Get parametric monitor
        monitor = get_parametric_monitor()
        
        # Check policy trigger
        evaluation = await monitor.check_policy(policy_number)
        
        if evaluation and evaluation.triggered:
            return {
                "status": "triggered",
                "policy_number": policy_number,
                "payout_amount": evaluation.payout_amount,
                "message": "Parametric trigger met, claim processing initiated"
            }
        else:
            return {
                "status": "not_triggered",
                "policy_number": policy_number,
                "message": "Trigger conditions not met"
            }
        
    except Exception as e:
        logger.error(f"Error processing port update webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/weather-alert/{policy_number}")
async def handle_weather_alert_webhook(
    policy_number: str,
    payload: Dict[str, Any],
    request: Request,
    x_signature: Optional[str] = Header(None, alias="X-Signature")
) -> Dict[str, Any]:
    """
    Handle weather alert webhook.
    
    Webhook from Tomorrow.io, Floodbase, or other weather providers.
    """
    try:
        logger.info(f"Received weather alert webhook for policy {policy_number}")
        
        # Get parametric monitor
        monitor = get_parametric_monitor()
        
        # Check policy trigger
        evaluation = await monitor.check_policy(policy_number)
        
        if evaluation and evaluation.triggered:
            return {
                "status": "triggered",
                "policy_number": policy_number,
                "payout_amount": evaluation.payout_amount,
                "message": "Weather trigger met, claim processing initiated"
            }
        else:
            return {
                "status": "not_triggered",
                "policy_number": policy_number,
                "message": "Weather trigger conditions not met"
            }
        
    except Exception as e:
        logger.error(f"Error processing weather alert webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/catastrophe-alert")
async def handle_catastrophe_alert_webhook(
    payload: Dict[str, Any],
    request: Request,
    x_signature: Optional[str] = Header(None, alias="X-Signature")
) -> Dict[str, Any]:
    """
    Handle catastrophe alert webhook.
    
    Webhook from NOAA, JTWC, ICEYE, or Aon Impact Forecasting.
    Can affect multiple policies.
    """
    try:
        event_type = payload.get("event_type")
        location = payload.get("location", {})
        
        logger.info(f"Received catastrophe alert: {event_type} at {location}")
        
        # Get parametric monitor
        monitor = get_parametric_monitor()
        
        # Check all active policies that might be affected
        triggered_policies = []
        
        for policy_number, policy in monitor.active_policies.items():
            if policy.trigger and policy.trigger.trigger_type == "natcat":
                # Check if location matches
                evaluation = await monitor.check_policy(policy_number)
                if evaluation and evaluation.triggered:
                    triggered_policies.append({
                        "policy_number": policy_number,
                        "payout_amount": evaluation.payout_amount
                    })
        
        return {
            "status": "processed",
            "event_type": event_type,
            "triggered_policies": triggered_policies,
            "count": len(triggered_policies)
        }
        
    except Exception as e:
        logger.error(f"Error processing catastrophe alert webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
