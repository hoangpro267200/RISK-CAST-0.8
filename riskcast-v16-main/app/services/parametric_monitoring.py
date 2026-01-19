"""
RISKCAST Parametric Insurance Monitoring System
===============================================
Monitors parametric triggers and processes automatic claims.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
import logging

from app.models.insurance import Policy, ParametricTrigger, TriggerEvaluation
from app.services.parametric_engine import ParametricTriggerEvaluator

logger = logging.getLogger(__name__)


class ParametricMonitor:
    """
    Monitors parametric insurance policies for trigger events.
    """
    
    def __init__(self):
        self.active_policies: Dict[str, Policy] = {}
        self.monitoring_jobs: Dict[str, Dict[str, Any]] = {}
    
    def register_policy(self, policy: Policy) -> None:
        """
        Register a policy for monitoring.
        
        Args:
            policy: Policy to monitor
        """
        if not policy.monitoring_enabled:
            logger.warning(f"Policy {policy.policy_number} does not have monitoring enabled")
            return
        
        if not policy.trigger:
            logger.warning(f"Policy {policy.policy_number} does not have a trigger defined")
            return
        
        self.active_policies[policy.policy_number] = policy
        
        # Create monitoring job
        self.monitoring_jobs[policy.policy_number] = {
            "policy_number": policy.policy_number,
            "trigger": policy.trigger,
            "check_frequency": "1h",  # Check every hour
            "expiry_date": policy.expiry_date,
            "last_check": None,
            "triggered": False
        }
        
        logger.info(f"Registered policy {policy.policy_number} for parametric monitoring")
    
    async def check_policy(self, policy_number: str) -> Optional[TriggerEvaluation]:
        """
        Check if a policy's trigger has been met.
        
        Args:
            policy_number: Policy number to check
            
        Returns:
            TriggerEvaluation if triggered, None otherwise
        """
        if policy_number not in self.active_policies:
            logger.warning(f"Policy {policy_number} not found in active policies")
            return None
        
        policy = self.active_policies[policy_number]
        job = self.monitoring_jobs[policy_number]
        
        # Check if policy is expired
        if datetime.now() > policy.expiry_date:
            logger.info(f"Policy {policy_number} has expired, removing from monitoring")
            self.unregister_policy(policy_number)
            return None
        
        # Check if already triggered
        if job["triggered"]:
            logger.debug(f"Policy {policy_number} already triggered, skipping check")
            return None
        
        if not policy.trigger:
            return None
        
        try:
            # Fetch current data based on trigger type
            current_data = await self._fetch_trigger_data(policy.trigger)
            
            # Evaluate trigger
            evaluation = self._evaluate_trigger(policy.trigger, current_data)
            
            # Update last check time
            job["last_check"] = datetime.now()
            
            if evaluation.triggered:
                job["triggered"] = True
                logger.info(
                    f"Trigger met for policy {policy_number}: "
                    f"Payout=${evaluation.payout_amount:,.2f}"
                )
                
                # Process automatic claim
                await self._process_automatic_claim(policy, evaluation)
            
            return evaluation
            
        except Exception as e:
            logger.error(f"Error checking policy {policy_number}: {e}", exc_info=True)
            return None
    
    async def check_all_policies(self) -> Dict[str, TriggerEvaluation]:
        """
        Check all active policies.
        
        Returns:
            Dict mapping policy_number to TriggerEvaluation
        """
        results = {}
        
        for policy_number in list(self.active_policies.keys()):
            evaluation = await self.check_policy(policy_number)
            if evaluation:
                results[policy_number] = evaluation
        
        return results
    
    async def start_monitoring_loop(self, interval_seconds: int = 3600) -> None:
        """
        Start continuous monitoring loop.
        
        Args:
            interval_seconds: Check interval in seconds (default: 1 hour)
        """
        logger.info(f"Starting parametric monitoring loop (interval: {interval_seconds}s)")
        
        while True:
            try:
                await self.check_all_policies()
                await asyncio.sleep(interval_seconds)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    def unregister_policy(self, policy_number: str) -> None:
        """Unregister a policy from monitoring."""
        if policy_number in self.active_policies:
            del self.active_policies[policy_number]
        if policy_number in self.monitoring_jobs:
            del self.monitoring_jobs[policy_number]
        logger.info(f"Unregistered policy {policy_number} from monitoring")
    
    async def _fetch_trigger_data(self, trigger: ParametricTrigger) -> Dict[str, Any]:
        """
        Fetch current data for trigger evaluation.
        
        Args:
            trigger: Parametric trigger definition
            
        Returns:
            Current data for trigger evaluation
        """
        trigger_type = trigger.trigger_type
        
        if trigger_type == "weather":
            # Fetch weather data (in production, call Tomorrow.io API)
            return await self._fetch_weather_data(trigger)
        
        elif trigger_type == "port_congestion":
            # Fetch port congestion data (in production, call port authority API)
            return await self._fetch_port_congestion_data(trigger)
        
        elif trigger_type == "natcat":
            # Fetch catastrophe data (in production, call NOAA/JTWC)
            return await self._fetch_catastrophe_data(trigger)
        
        else:
            logger.warning(f"Unknown trigger type: {trigger_type}")
            return {}
    
    async def _fetch_weather_data(self, trigger: ParametricTrigger) -> Dict[str, Any]:
        """Fetch weather data for trigger."""
        # Mock implementation (replace with actual API call)
        logger.debug(f"Fetching weather data for port: {trigger.location.get('port_code')}")
        
        # In production: Call Tomorrow.io API
        return {
            "cumulative_rainfall_mm": 120.0,  # Mock data
            "timestamp": datetime.now().isoformat()
        }
    
    async def _fetch_port_congestion_data(self, trigger: ParametricTrigger) -> Dict[str, Any]:
        """Fetch port congestion data for trigger."""
        # Mock implementation (replace with actual API call)
        logger.debug(f"Fetching port congestion data for port: {trigger.location.get('port_code')}")
        
        # In production: Call port authority API or MarineTraffic
        return {
            "dwell_days": 12.0,  # Mock data
            "timestamp": datetime.now().isoformat()
        }
    
    async def _fetch_catastrophe_data(self, trigger: ParametricTrigger) -> Dict[str, Any]:
        """Fetch catastrophe data for trigger."""
        # Mock implementation (replace with actual API call)
        logger.debug(f"Fetching catastrophe data for location: {trigger.location}")
        
        # In production: Call NOAA/JTWC/ICEYE
        return {
            "storm_id": None,
            "forecast_track": [],
            "max_wind_kph": 0
        }
    
    def _evaluate_trigger(
        self,
        trigger: ParametricTrigger,
        current_data: Dict[str, Any]
    ) -> TriggerEvaluation:
        """
        Evaluate trigger based on current data.
        
        Args:
            trigger: Trigger definition
            current_data: Current data
            
        Returns:
            TriggerEvaluation result
        """
        trigger_type = trigger.trigger_type
        
        if trigger_type == "weather":
            return ParametricTriggerEvaluator.evaluate_rainfall_trigger(trigger, current_data)
        
        elif trigger_type == "port_congestion":
            return ParametricTriggerEvaluator.evaluate_port_congestion_trigger(trigger, current_data)
        
        elif trigger_type == "natcat":
            return ParametricTriggerEvaluator.evaluate_cyclone_trigger(trigger, current_data)
        
        else:
            logger.warning(f"Unknown trigger type for evaluation: {trigger_type}")
            return TriggerEvaluation(triggered=False, reason=f"Unknown trigger type: {trigger_type}")
    
    async def _process_automatic_claim(
        self,
        policy: Policy,
        evaluation: TriggerEvaluation
    ) -> None:
        """
        Process automatic parametric claim.
        
        Args:
            policy: Policy that was triggered
            evaluation: Trigger evaluation result
        """
        from app.services.insurance_claims_service import InsuranceClaimsService
        
        try:
            logger.info(
                f"Processing automatic claim for policy {policy.policy_number}: "
                f"Payout=${evaluation.payout_amount:,.2f}"
            )
            
            # Create claim
            claim = await InsuranceClaimsService.create_parametric_claim(
                policy_number=policy.policy_number,
                trigger_evaluation=evaluation,
                trigger_evidence=evaluation.trigger_evidence
            )
            
            # Process payout
            await InsuranceClaimsService.process_parametric_payout(claim)
            
            logger.info(f"Automatic claim processed: {claim.claim_number}")
            
        except Exception as e:
            logger.error(
                f"Error processing automatic claim for policy {policy.policy_number}: {e}",
                exc_info=True
            )


# Global monitor instance
_global_monitor: Optional[ParametricMonitor] = None


def get_parametric_monitor() -> ParametricMonitor:
    """Get global parametric monitor instance."""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = ParametricMonitor()
    return _global_monitor
