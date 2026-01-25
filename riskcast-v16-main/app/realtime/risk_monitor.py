"""
Real-time Risk Monitoring Service

Features:
1. Live risk score updates
2. Threshold alerts
3. Portfolio risk aggregation
4. Market condition monitoring
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass
from decimal import Decimal
import json

from app.realtime.websocket_manager import ws_manager, MessageType
from app.core.logging import get_logger


logger = get_logger(__name__)


@dataclass
class RiskAlert:
    """Risk alert definition."""
    alert_id: str
    alert_type: str  # threshold_breach, trend_change, anomaly
    severity: str    # low, medium, high, critical
    entity_type: str # policy, portfolio, route
    entity_id: str
    message: str
    current_value: float
    threshold_value: Optional[float]
    created_at: datetime
    metadata: Dict[str, Any]


class RiskThreshold:
    """Risk threshold configuration."""
    
    # Policy risk thresholds
    POLICY_RISK_HIGH = 0.7
    POLICY_RISK_CRITICAL = 0.85
    
    # Portfolio risk thresholds
    PORTFOLIO_VAR_WARNING = 0.05  # 5% VaR
    PORTFOLIO_VAR_CRITICAL = 0.10  # 10% VaR
    
    # Concentration risk thresholds
    CONCENTRATION_WARNING = 0.3   # 30% in single route/cargo
    CONCENTRATION_CRITICAL = 0.5  # 50% in single route/cargo
    
    # Trend change threshold
    TREND_INCREASE_THRESHOLD = 0.1  # 10% increase
    
    # Expected loss thresholds
    EXPECTED_LOSS_WARNING = 0.02   # 2%
    EXPECTED_LOSS_CRITICAL = 0.05  # 5%


class RealTimeRiskMonitor:
    """
    Monitors risk in real-time and sends alerts via WebSocket.
    
    Features:
    - Continuous risk assessment
    - Threshold monitoring
    - Trend detection
    - Market condition updates
    - Portfolio aggregation
    """
    
    def __init__(
        self,
        update_interval: int = 60  # seconds
    ):
        self.update_interval = update_interval
        
        # Tracked entities
        self._monitored_policies: Dict[str, str] = {}  # policy_id -> tenant_id
        self._monitored_routes: Set[str] = set()
        
        # Cache of latest risk scores
        self._risk_cache: Dict[str, dict] = {}
        
        # Alert history (to prevent duplicates)
        self._recent_alerts: Dict[str, datetime] = {}
        
        # Alert cooldown period (seconds)
        self._alert_cooldown = 300  # 5 minutes
        
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        
        # Services (will be injected or imported dynamically)
        self._risk_engine = None
        self._data_service = None
    
    def set_services(self, risk_engine, data_service):
        """
        Set service dependencies.
        
        Args:
            risk_engine: CalibratedRiskEngine instance
            data_service: UnifiedDataService instance
        """
        self._risk_engine = risk_engine
        self._data_service = data_service
        logger.info("Risk monitor services configured")
    
    async def start(self):
        """Start the risk monitor."""
        if not self._risk_engine or not self._data_service:
            logger.warning("Risk monitor started without services configured")
        
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info(
            "Real-time risk monitor started",
            update_interval=self.update_interval
        )
    
    async def stop(self):
        """Stop the risk monitor."""
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Real-time risk monitor stopped")
    
    async def add_policy_monitoring(self, policy_id: str, tenant_id: str):
        """
        Add a policy to real-time monitoring.
        
        Args:
            policy_id: Policy identifier
            tenant_id: Tenant identifier
        """
        self._monitored_policies[policy_id] = tenant_id
        
        logger.info(
            "Policy added to monitoring",
            policy_id=policy_id,
            tenant_id=tenant_id,
            total_monitored=len(self._monitored_policies)
        )
        
        # Trigger immediate assessment
        if self._risk_engine and self._data_service:
            try:
                await self._assess_policy_risk(policy_id, tenant_id)
            except Exception as e:
                logger.error(
                    "Initial policy assessment failed",
                    policy_id=policy_id,
                    error=str(e)
                )
    
    async def remove_policy_monitoring(self, policy_id: str):
        """
        Remove a policy from monitoring.
        
        Args:
            policy_id: Policy identifier
        """
        tenant_id = self._monitored_policies.pop(policy_id, None)
        self._risk_cache.pop(f"policy:{policy_id}", None)
        
        if tenant_id:
            logger.info(
                "Policy removed from monitoring",
                policy_id=policy_id,
                total_monitored=len(self._monitored_policies)
            )
    
    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while self._running:
            try:
                await self._run_monitoring_cycle()
                await asyncio.sleep(self.update_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Monitoring cycle error", error=str(e))
                await asyncio.sleep(5)  # Brief pause before retry
    
    async def _run_monitoring_cycle(self):
        """Run a single monitoring cycle."""
        cycle_start = datetime.utcnow()
        
        logger.debug(
            "Monitoring cycle started",
            monitored_policies=len(self._monitored_policies)
        )
        
        # Update market conditions
        if self._data_service:
            try:
                await self._update_market_conditions()
            except Exception as e:
                logger.error("Market update failed", error=str(e))
        
        # Re-assess monitored policies
        assessed_count = 0
        error_count = 0
        
        for policy_id, tenant_id in list(self._monitored_policies.items()):
            try:
                await self._assess_policy_risk(policy_id, tenant_id)
                assessed_count += 1
            except Exception as e:
                error_count += 1
                logger.error(
                    "Policy assessment failed",
                    policy_id=policy_id,
                    error=str(e)
                )
        
        # Check portfolio-level risks
        if self._monitored_policies:
            try:
                await self._assess_portfolio_risks()
            except Exception as e:
                logger.error("Portfolio assessment failed", error=str(e))
        
        # Clean old alerts
        self._cleanup_old_alerts()
        
        cycle_duration = (datetime.utcnow() - cycle_start).total_seconds()
        
        logger.info(
            "Monitoring cycle completed",
            assessed=assessed_count,
            errors=error_count,
            duration_seconds=cycle_duration
        )
    
    async def _update_market_conditions(self):
        """Fetch and broadcast market condition updates."""
        try:
            # Simulate market data (in production, fetch from data service)
            market_data = {
                "weather_alerts": [],
                "port_congestion": {},
                "exchange_rates": {},
                "commodity_prices": {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Broadcast to subscribers
            await ws_manager.send_to_room("public:market", {
                "type": MessageType.MARKET_DATA,
                "data": market_data
            })
            
            logger.debug("Market conditions updated")
            
        except Exception as e:
            logger.error("Market update error", error=str(e))
    
    async def _assess_policy_risk(self, policy_id: str, tenant_id: str):
        """
        Assess risk for a single policy.
        
        Args:
            policy_id: Policy identifier
            tenant_id: Tenant identifier
        """
        # In production, would fetch policy and run risk assessment
        # For now, simulate with cached data or basic logic
        
        try:
            # Simulate risk assessment
            # In production: Use risk_engine.assess_risk()
            current_risk = {
                "policy_id": policy_id,
                "tenant_id": tenant_id,
                "risk_score": 0.65,  # Simulated
                "risk_grade": "B",
                "expected_loss_pct": 0.015,
                "var_95": 0.045,
                "var_99": 0.078,
                "layer_scores": {
                    "route": 0.55,
                    "cargo": 0.45,
                    "carrier": 0.35,
                    "weather": 0.70,
                    "geopolitical": 0.40
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Check for changes
            cache_key = f"policy:{policy_id}"
            previous = self._risk_cache.get(cache_key)
            
            # Update cache
            self._risk_cache[cache_key] = current_risk
            
            # Check thresholds
            await self._check_policy_thresholds(
                policy_id,
                tenant_id,
                current_risk,
                previous
            )
            
            # Broadcast update to policy room
            await ws_manager.send_to_room(f"policy:{policy_id}", {
                "type": MessageType.RISK_UPDATE,
                "data": current_risk
            })
            
            # Also send to tenant risk room
            await ws_manager.send_to_room(f"tenant:{tenant_id}:risks", {
                "type": MessageType.RISK_UPDATE,
                "data": current_risk
            })
            
            logger.debug(
                "Policy risk assessed",
                policy_id=policy_id,
                risk_score=current_risk["risk_score"]
            )
            
        except Exception as e:
            logger.error(
                "Policy risk assessment failed",
                policy_id=policy_id,
                error=str(e)
            )
            raise
    
    async def _check_policy_thresholds(
        self,
        policy_id: str,
        tenant_id: str,
        current: dict,
        previous: Optional[dict]
    ):
        """
        Check if risk thresholds are breached.
        
        Args:
            policy_id: Policy identifier
            tenant_id: Tenant identifier
            current: Current risk assessment
            previous: Previous risk assessment (if available)
        """
        alerts = []
        risk_score = current["risk_score"]
        
        # Critical risk threshold
        if risk_score >= RiskThreshold.POLICY_RISK_CRITICAL:
            alerts.append(RiskAlert(
                alert_id=f"policy:{policy_id}:critical",
                alert_type="threshold_breach",
                severity="critical",
                entity_type="policy",
                entity_id=policy_id,
                message=f"Policy risk is CRITICAL: {risk_score:.2%}",
                current_value=risk_score,
                threshold_value=RiskThreshold.POLICY_RISK_CRITICAL,
                created_at=datetime.utcnow(),
                metadata={
                    "layer_scores": current.get("layer_scores", {}),
                    "var_95": current.get("var_95"),
                    "var_99": current.get("var_99")
                }
            ))
        
        # High risk threshold
        elif risk_score >= RiskThreshold.POLICY_RISK_HIGH:
            alerts.append(RiskAlert(
                alert_id=f"policy:{policy_id}:high",
                alert_type="threshold_breach",
                severity="high",
                entity_type="policy",
                entity_id=policy_id,
                message=f"Policy risk is HIGH: {risk_score:.2%}",
                current_value=risk_score,
                threshold_value=RiskThreshold.POLICY_RISK_HIGH,
                created_at=datetime.utcnow(),
                metadata={"layer_scores": current.get("layer_scores", {})}
            ))
        
        # Expected loss threshold
        expected_loss = current.get("expected_loss_pct", 0)
        if expected_loss >= RiskThreshold.EXPECTED_LOSS_CRITICAL:
            alerts.append(RiskAlert(
                alert_id=f"policy:{policy_id}:expected_loss",
                alert_type="threshold_breach",
                severity="high",
                entity_type="policy",
                entity_id=policy_id,
                message=f"Expected loss is high: {expected_loss:.2%}",
                current_value=expected_loss,
                threshold_value=RiskThreshold.EXPECTED_LOSS_CRITICAL,
                created_at=datetime.utcnow(),
                metadata={"risk_score": risk_score}
            ))
        
        # Trend detection (significant increase)
        if previous:
            prev_score = previous.get("risk_score", 0)
            change = risk_score - prev_score
            
            if change >= RiskThreshold.TREND_INCREASE_THRESHOLD:
                alerts.append(RiskAlert(
                    alert_id=f"policy:{policy_id}:trend",
                    alert_type="trend_change",
                    severity="medium",
                    entity_type="policy",
                    entity_id=policy_id,
                    message=f"Risk increased by {change:.1%} since last assessment",
                    current_value=risk_score,
                    threshold_value=prev_score,
                    created_at=datetime.utcnow(),
                    metadata={
                        "previous_score": prev_score,
                        "change": change,
                        "change_pct": (change / prev_score) if prev_score > 0 else 0
                    }
                ))
        
        # Send all alerts
        for alert in alerts:
            await self._send_alert(alert, tenant_id)
    
    async def _assess_portfolio_risks(self):
        """Assess portfolio-level risks across tenants."""
        # Group policies by tenant
        tenant_policies: Dict[str, List[str]] = {}
        
        for policy_id, tenant_id in self._monitored_policies.items():
            if tenant_id not in tenant_policies:
                tenant_policies[tenant_id] = []
            tenant_policies[tenant_id].append(policy_id)
        
        # Assess each tenant's portfolio
        for tenant_id, policy_ids in tenant_policies.items():
            try:
                # Calculate portfolio metrics
                risk_scores = []
                total_value = 0
                
                for policy_id in policy_ids:
                    cache_key = f"policy:{policy_id}"
                    risk_data = self._risk_cache.get(cache_key)
                    if risk_data:
                        risk_scores.append(risk_data["risk_score"])
                        # Would include policy value in production
                        total_value += 1000000  # Placeholder
                
                if not risk_scores:
                    continue
                
                # Calculate portfolio-level metrics
                portfolio_metrics = {
                    "tenant_id": tenant_id,
                    "policy_count": len(risk_scores),
                    "avg_risk_score": sum(risk_scores) / len(risk_scores),
                    "max_risk_score": max(risk_scores),
                    "min_risk_score": min(risk_scores),
                    "total_exposure": total_value,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # Send portfolio update
                await ws_manager.send_to_room(
                    f"tenant:{tenant_id}:portfolio",
                    {
                        "type": "portfolio_update",
                        "data": portfolio_metrics
                    }
                )
                
                logger.debug(
                    "Portfolio risk assessed",
                    tenant_id=tenant_id,
                    policy_count=len(risk_scores),
                    avg_risk=portfolio_metrics["avg_risk_score"]
                )
                
            except Exception as e:
                logger.error(
                    "Portfolio assessment failed",
                    tenant_id=tenant_id,
                    error=str(e)
                )
    
    async def _send_alert(self, alert: RiskAlert, tenant_id: str):
        """
        Send an alert if not recently sent.
        
        Args:
            alert: RiskAlert instance
            tenant_id: Tenant identifier
        """
        # Check if we've sent this alert recently (cooldown)
        if alert.alert_id in self._recent_alerts:
            last_sent = self._recent_alerts[alert.alert_id]
            time_since = (datetime.utcnow() - last_sent).total_seconds()
            
            if time_since < self._alert_cooldown:
                logger.debug(
                    "Alert suppressed (cooldown)",
                    alert_id=alert.alert_id,
                    time_since=time_since
                )
                return
        
        # Record alert timestamp
        self._recent_alerts[alert.alert_id] = datetime.utcnow()
        
        # Prepare alert message
        alert_data = {
            "type": MessageType.ALERT,
            "data": {
                "alert_id": alert.alert_id,
                "alert_type": alert.alert_type,
                "severity": alert.severity,
                "entity_type": alert.entity_type,
                "entity_id": alert.entity_id,
                "message": alert.message,
                "current_value": alert.current_value,
                "threshold_value": alert.threshold_value,
                "timestamp": alert.created_at.isoformat(),
                "metadata": alert.metadata
            }
        }
        
        # Send to tenant alerts room
        await ws_manager.send_to_room(f"tenant:{tenant_id}:alerts", alert_data)
        
        # Send to entity-specific room
        await ws_manager.send_to_room(
            f"{alert.entity_type}:{alert.entity_id}",
            alert_data
        )
        
        logger.info(
            "Risk alert sent",
            alert_id=alert.alert_id,
            alert_type=alert.alert_type,
            severity=alert.severity,
            entity_id=alert.entity_id,
            message=alert.message
        )
    
    def _cleanup_old_alerts(self):
        """Remove old alerts from tracking."""
        cutoff = datetime.utcnow() - timedelta(hours=1)
        
        old_alerts = [
            alert_id for alert_id, timestamp in self._recent_alerts.items()
            if timestamp < cutoff
        ]
        
        for alert_id in old_alerts:
            del self._recent_alerts[alert_id]
        
        if old_alerts:
            logger.debug("Old alerts cleaned up", count=len(old_alerts))
    
    def get_monitored_count(self) -> int:
        """Get count of monitored policies."""
        return len(self._monitored_policies)
    
    def get_stats(self) -> dict:
        """Get monitoring statistics."""
        return {
            "monitored_policies": len(self._monitored_policies),
            "cached_assessments": len(self._risk_cache),
            "recent_alerts": len(self._recent_alerts),
            "is_running": self._running,
            "update_interval": self.update_interval
        }


# Global instance
risk_monitor = RealTimeRiskMonitor()
