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
from app.core.parametric.oracle_gateway import (
    OracleGateway,
    OracleQuery,
    OracleNotConfiguredError,
)
from app.core.parametric.exceptions import OracleFetchError
from app.core.parametric.providers.tomorrow_io_provider import TomorrowIOProvider
from app.core.parametric.providers.marinetraffic_provider import MarineTrafficProvider
# Note: TriggerEvaluation is now exported from app.models.insurance

logger = logging.getLogger(__name__)


class ParametricMonitor:
    """
    Monitors parametric insurance policies for trigger events.
    """
    
    def __init__(self, oracle_gateway: Optional[OracleGateway] = None, audit_ledger: Optional[Any] = None):
        """
        Initialize monitor.
        
        Args:
            oracle_gateway: OracleGateway instance (creates new if not provided)
            audit_ledger: Optional audit ledger for data tracking
        """
        self.active_policies: Dict[str, Policy] = {}
        self.monitoring_jobs: Dict[str, Dict[str, Any]] = {}
        self.oracle_gateway = oracle_gateway or OracleGateway()
        self.audit_ledger = audit_ledger
        
        # Register providers if configured
        # Must be after oracle_gateway is set
        if self.oracle_gateway:
            self._register_weather_provider()
            self._register_port_provider()
    
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
    
    def _register_weather_provider(self) -> None:
        """Register Tomorrow.io weather provider if configured."""
        try:
            provider = TomorrowIOProvider(audit_ledger=self.audit_ledger)
            if provider.is_configured():
                self.oracle_gateway.register_provider(provider)
                logger.info("Registered Tomorrow.io weather provider")
            else:
                logger.warning(
                    "Tomorrow.io API key not configured. "
                    "Weather parametric triggers will not work. "
                    "Set TOMORROW_IO_API_KEY environment variable."
                )
        except Exception as e:
            logger.error(f"Failed to register Tomorrow.io provider: {e}", exc_info=True)
    
    def _register_port_provider(self) -> None:
        """Register MarineTraffic port provider if configured."""
        try:
            provider = MarineTrafficProvider(audit_ledger=self.audit_ledger)
            if provider.is_configured():
                self.oracle_gateway.register_provider(provider)
                logger.info("Registered MarineTraffic port provider")
            else:
                logger.warning(
                    "MarineTraffic API key not configured. "
                    "Port congestion parametric triggers will not work. "
                    "Set MARINE_TRAFFIC_API_KEY or MARINETRAFFIC_API_KEY environment variable."
                )
        except Exception as e:
            logger.error(f"Failed to register MarineTraffic provider: {e}", exc_info=True)
    
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
            
            # Add source information to data for validation
            # The oracle gateway should set this, but we ensure it's present
            if "data_source" not in current_data and "source" not in current_data:
                # Try to infer from trigger type
                trigger_type_map = {
                    "weather": "weather",
                    "port_congestion": "port",
                    "natcat": "natcat"
                }
                inferred_source = trigger_type_map.get(policy.trigger.trigger_type, "unknown")
                current_data["data_source"] = inferred_source
            
            # Evaluate trigger (includes validation for stub data)
            evaluation = self._evaluate_trigger(policy.trigger, current_data)
            
            # Update last check time
            job["last_check"] = datetime.now()
            
            if evaluation.triggered:
                job["triggered"] = True
                logger.info(
                    f"Trigger met for policy {policy_number}: "
                    f"Payout=${evaluation.payout_amount:,.2f}"
                )
                
                # Check safety guards before processing claim
                try:
                    # Process automatic claim (includes safety guard checks)
                    await self._process_automatic_claim(policy, evaluation)
                except Exception as e:
                    logger.error(
                        f"Payout blocked for policy {policy_number}: {e}",
                        exc_info=True
                    )
                    # Don't re-raise - evaluation is still valid, just payout blocked
            
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
        """
        Fetch weather data for trigger from oracle gateway.
        
        Args:
            trigger: Parametric trigger definition
            
        Returns:
            Weather data dictionary
            
        Raises:
            OracleNotConfiguredError: If weather oracle is not configured
            OracleFetchError: If fetch operation fails
        """
        location = trigger.location.get('port_code') or trigger.location.get('location')
        logger.debug(f"Fetching weather data for location: {location}")
        
        try:
            query = OracleQuery(
                location=location,
                timestamp=datetime.utcnow(),
                parameters={
                    "trigger_type": "weather",
                    "metrics": ["rainfall", "temperature", "wind"]
                }
            )
            
            payload = await self.oracle_gateway.fetch("weather", query)
            # Ensure payload includes source for validation
            result = payload.payload.copy()
            if "data_source" not in result:
                result["data_source"] = payload.source
            return result
            
        except OracleNotConfiguredError as e:
            logger.error(f"Weather oracle not configured: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching weather data: {e}", exc_info=True)
            raise OracleFetchError(f"Failed to fetch weather data: {str(e)}") from e
    
    async def _fetch_port_congestion_data(self, trigger: ParametricTrigger) -> Dict[str, Any]:
        """
        Fetch port congestion data for trigger from oracle gateway.
        
        Args:
            trigger: Parametric trigger definition
            
        Returns:
            Port congestion data dictionary
            
        Raises:
            OracleNotConfiguredError: If port oracle is not configured
            OracleFetchError: If fetch operation fails
        """
        port_code = trigger.location.get('port_code')
        logger.debug(f"Fetching port congestion data for port: {port_code}")
        
        try:
            query = OracleQuery(
                location=port_code,
                timestamp=datetime.utcnow(),
                parameters={
                    "trigger_type": "port_congestion",
                    "metrics": ["dwell_days", "vessel_count", "wait_time"]
                }
            )
            
            payload = await self.oracle_gateway.fetch("port", query)
            return payload.payload
            
        except OracleNotConfiguredError as e:
            logger.error(f"Port oracle not configured: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching port congestion data: {e}", exc_info=True)
            raise OracleFetchError(f"Failed to fetch port congestion data: {str(e)}") from e
    
    async def _fetch_catastrophe_data(self, trigger: ParametricTrigger) -> Dict[str, Any]:
        """
        Fetch catastrophe data for trigger from oracle gateway.
        
        Args:
            trigger: Parametric trigger definition
            
        Returns:
            Catastrophe data dictionary
            
        Raises:
            OracleNotConfiguredError: If natcat oracle is not configured
            OracleFetchError: If fetch operation fails
        """
        location = trigger.location.get('location') or trigger.location.get('port_code')
        logger.debug(f"Fetching catastrophe data for location: {location}")
        
        try:
            query = OracleQuery(
                location=location,
                timestamp=datetime.utcnow(),
                parameters={
                    "trigger_type": "natcat",
                    "metrics": ["storm_id", "forecast_track", "max_wind_kph"]
                }
            )
            
            payload = await self.oracle_gateway.fetch("natcat", query)
            # Ensure payload includes source for validation
            result = payload.payload.copy()
            if "data_source" not in result:
                result["data_source"] = payload.source
            return result
            
        except OracleNotConfiguredError as e:
            logger.error(f"Natcat oracle not configured: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching catastrophe data: {e}", exc_info=True)
            raise OracleFetchError(f"Failed to fetch catastrophe data: {str(e)}") from e
    
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
    
    def is_oracle_configured(self, source: str) -> bool:
        """
        Check if oracle provider is configured.
        
        Args:
            source: Oracle source name (e.g., "weather", "port", "natcat")
            
        Returns:
            True if configured, False otherwise
        """
        provider = self.oracle_gateway.get_provider(source)
        if provider is None:
            return False
        return provider.is_configured()


# Global monitor instance
_global_monitor: Optional[ParametricMonitor] = None


def get_parametric_monitor(
    oracle_gateway: Optional[OracleGateway] = None,
    audit_ledger: Optional[Any] = None
) -> ParametricMonitor:
    """
    Get global parametric monitor instance.
    
    Args:
        oracle_gateway: Optional OracleGateway instance
        
    Returns:
        ParametricMonitor instance
    """
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = ParametricMonitor(
            oracle_gateway=oracle_gateway,
            audit_ledger=audit_ledger
        )
    return _global_monitor
