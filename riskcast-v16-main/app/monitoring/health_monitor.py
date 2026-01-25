"""
System Health Monitoring

Comprehensive health checks for production system:
- API health
- Database health
- External services health
- Audit chain health
- Model version health
- Data freshness health
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import asyncio
import logging
from sqlalchemy.orm import Session
from sqlalchemy import text


class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"
    UNKNOWN = "UNKNOWN"


@dataclass
class ComponentHealth:
    """Health of a single component."""
    component: str
    status: HealthStatus
    latency_ms: Optional[float]
    message: str
    last_checked: datetime
    details: Optional[Dict[str, Any]] = None


@dataclass
class SystemHealth:
    """Overall system health."""
    overall_status: HealthStatus
    components: List[ComponentHealth]
    healthy_count: int
    degraded_count: int
    unhealthy_count: int
    checked_at: datetime
    uptime_seconds: float


class HealthMonitor:
    """
    Comprehensive system health monitoring.
    Checks:
    - Database connectivity and performance
    - External API availability
    - Audit chain integrity
    - Model version status
    - Data freshness
    - Background job status
    """

    # Thresholds
    DB_LATENCY_WARNING_MS = 100
    DB_LATENCY_CRITICAL_MS = 500
    API_LATENCY_WARNING_MS = 1000
    API_LATENCY_CRITICAL_MS = 5000
    DATA_STALE_WARNING_HOURS = 1
    DATA_STALE_CRITICAL_HOURS = 6

    def __init__(
        self,
        db: Session,
        start_time: datetime = None
    ):
        self.db = db
        self.start_time = start_time or datetime.utcnow()
        self.logger = logging.getLogger(__name__)

    async def check_health(self) -> SystemHealth:
        """
        Run all health checks.
        """
        components = []
        
        # Database health
        db_health = await self._check_database()
        components.append(db_health)
        
        # Audit chain health
        audit_health = await self._check_audit_chain()
        components.append(audit_health)
        
        # Model version health
        model_health = await self._check_model_version()
        components.append(model_health)
        
        # Data freshness
        data_health = await self._check_data_freshness()
        components.append(data_health)
        
        # External services (weather, port, carrier, climate)
        for service in ["weather", "port", "carrier", "climate"]:
            service_health = await self._check_external_service(service)
            components.append(service_health)
        
        # Background jobs
        jobs_health = await self._check_background_jobs()
        components.append(jobs_health)
        
        # Calculate overall status
        healthy = sum(1 for c in components if c.status == HealthStatus.HEALTHY)
        degraded = sum(1 for c in components if c.status == HealthStatus.DEGRADED)
        unhealthy = sum(1 for c in components if c.status == HealthStatus.UNHEALTHY)
        
        if unhealthy > 0:
            overall = HealthStatus.UNHEALTHY
        elif degraded > 0:
            overall = HealthStatus.DEGRADED
        else:
            overall = HealthStatus.HEALTHY
        
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        
        return SystemHealth(
            overall_status=overall,
            components=components,
            healthy_count=healthy,
            degraded_count=degraded,
            unhealthy_count=unhealthy,
            checked_at=datetime.utcnow(),
            uptime_seconds=uptime
        )

    async def _check_database(self) -> ComponentHealth:
        """Check database health."""
        start = datetime.utcnow()
        
        try:
            # Simple query to test connectivity
            result = self.db.execute(text("SELECT 1"))
            result.fetchone()
            
            latency = (datetime.utcnow() - start).total_seconds() * 1000
            
            # Check connection pool (if available)
            pool_info = {}
            try:
                pool = self.db.get_bind().pool
                pool_info = {
                    "pool_size": pool.size(),
                    "checked_in": pool.checkedin(),
                    "checked_out": pool.checkedout(),
                    "overflow": pool.overflow()
                }
            except:
                pass
            
            if latency > self.DB_LATENCY_CRITICAL_MS:
                status = HealthStatus.UNHEALTHY
                message = f"Database latency critical: {latency:.0f}ms"
            elif latency > self.DB_LATENCY_WARNING_MS:
                status = HealthStatus.DEGRADED
                message = f"Database latency elevated: {latency:.0f}ms"
            else:
                status = HealthStatus.HEALTHY
                message = f"Database healthy: {latency:.0f}ms"
            
            return ComponentHealth(
                component="database",
                status=status,
                latency_ms=latency,
                message=message,
                last_checked=datetime.utcnow(),
                details=pool_info
            )
            
        except Exception as e:
            return ComponentHealth(
                component="database",
                status=HealthStatus.UNHEALTHY,
                latency_ms=None,
                message=f"Database error: {str(e)}",
                last_checked=datetime.utcnow()
            )

    async def _check_audit_chain(self) -> ComponentHealth:
        """Check audit chain integrity."""
        try:
            from app.core.audit.immutable_ledger import AuditEventImmutable
            
            # Get last 100 events and verify chain
            events = self.db.query(AuditEventImmutable).order_by(
                AuditEventImmutable.sequence_number.desc()
            ).limit(100).all()
            
            if not events:
                return ComponentHealth(
                    component="audit_chain",
                    status=HealthStatus.HEALTHY,
                    latency_ms=None,
                    message="No audit events to verify",
                    last_checked=datetime.utcnow()
                )
            
            # Verify chain links
            events_reversed = list(reversed(events))
            prev_hash = None
            chain_valid = True
            
            for event in events_reversed:
                if prev_hash and event.prev_event_hash != prev_hash:
                    chain_valid = False
                    break
                prev_hash = event.event_hash
            
            if chain_valid:
                return ComponentHealth(
                    component="audit_chain",
                    status=HealthStatus.HEALTHY,
                    latency_ms=None,
                    message=f"Audit chain healthy ({len(events)} events verified)",
                    last_checked=datetime.utcnow(),
                    details={
                        "events_verified": len(events),
                        "last_sequence": events[0].sequence_number
                    }
                )
            else:
                return ComponentHealth(
                    component="audit_chain",
                    status=HealthStatus.UNHEALTHY,
                    latency_ms=None,
                    message="Audit chain integrity failure detected",
                    last_checked=datetime.utcnow()
                )
                
        except Exception as e:
            return ComponentHealth(
                component="audit_chain",
                status=HealthStatus.UNKNOWN,
                latency_ms=None,
                message=f"Error checking audit chain: {str(e)}",
                last_checked=datetime.utcnow()
            )

    async def _check_model_version(self) -> ComponentHealth:
        """Check active model version health."""
        try:
            from app.modules.model_versioning.models import RiskModelVersion, ModelVersionStatus
            from app.models.system_config import SystemConfig
            
            # Get active version
            config = self.db.query(SystemConfig).filter(
                SystemConfig.key == "active_model_version_id"
            ).first()
            
            if not config:
                return ComponentHealth(
                    component="model_version",
                    status=HealthStatus.DEGRADED,
                    latency_ms=None,
                    message="No active model version configured",
                    last_checked=datetime.utcnow()
                )
            
            version = self.db.query(RiskModelVersion).filter(
                RiskModelVersion.id == config.value
            ).first()
            
            if not version:
                return ComponentHealth(
                    component="model_version",
                    status=HealthStatus.UNHEALTHY,
                    latency_ms=None,
                    message=f"Active model version not found: {config.value}",
                    last_checked=datetime.utcnow()
                )
            
            # Verify model hash if published
            if version.status == ModelVersionStatus.PUBLISHED and version.immutable_hash:
                computed_hash = version.compute_immutable_hash()
                if computed_hash != version.immutable_hash:
                    return ComponentHealth(
                        component="model_version",
                        status=HealthStatus.UNHEALTHY,
                        latency_ms=None,
                        message=f"Model integrity check failed: {version.name}",
                        last_checked=datetime.utcnow()
                    )
            
            return ComponentHealth(
                component="model_version",
                status=HealthStatus.HEALTHY,
                latency_ms=None,
                message=f"Active model: {version.name} v{version.version}",
                last_checked=datetime.utcnow(),
                details={
                    "version_id": str(version.id),
                    "name": version.name,
                    "version": version.version,
                    "is_calibrated": version.is_calibrated(),
                    "status": version.status.value if hasattr(version.status, 'value') else str(version.status)
                }
            )
            
        except Exception as e:
            return ComponentHealth(
                component="model_version",
                status=HealthStatus.UNKNOWN,
                latency_ms=None,
                message=f"Error checking model version: {str(e)}",
                last_checked=datetime.utcnow()
            )

    async def _check_data_freshness(self) -> ComponentHealth:
        """Check data freshness."""
        try:
            from app.core.audit.immutable_ledger import AuditEventImmutable
            
            # Check last data fetch events
            data_types = ["weather", "port", "carrier", "climate"]
            stale_sources = []
            fresh_sources = []
            
            for data_type in data_types:
                last_fetch = self.db.query(AuditEventImmutable).filter(
                    AuditEventImmutable.event_type == "DATA_FETCH",
                    AuditEventImmutable.action.like(f"%{data_type.upper()}%")
                ).order_by(
                    AuditEventImmutable.event_timestamp.desc()
                ).first()
                
                if last_fetch:
                    age_hours = (datetime.utcnow() - last_fetch.event_timestamp).total_seconds() / 3600
                    
                    if age_hours > self.DATA_STALE_CRITICAL_HOURS:
                        stale_sources.append(f"{data_type} ({age_hours:.1f}h)")
                    else:
                        fresh_sources.append(data_type)
                else:
                    stale_sources.append(f"{data_type} (never fetched)")
            
            if stale_sources:
                if len(stale_sources) >= 2:
                    status = HealthStatus.UNHEALTHY
                else:
                    status = HealthStatus.DEGRADED
                message = f"Stale data sources: {', '.join(stale_sources)}"
            else:
                status = HealthStatus.HEALTHY
                message = f"All data sources fresh"
            
            return ComponentHealth(
                component="data_freshness",
                status=status,
                latency_ms=None,
                message=message,
                last_checked=datetime.utcnow(),
                details={
                    "fresh_sources": fresh_sources,
                    "stale_sources": stale_sources
                }
            )
            
        except Exception as e:
            return ComponentHealth(
                component="data_freshness",
                status=HealthStatus.UNKNOWN,
                latency_ms=None,
                message=f"Error checking data freshness: {str(e)}",
                last_checked=datetime.utcnow()
            )

    async def _check_external_service(self, service: str) -> ComponentHealth:
        """Check external service health (cached status)."""
        try:
            from app.core.audit.immutable_ledger import AuditEventImmutable
            
            # Check recent fetches for this service
            recent = self.db.query(AuditEventImmutable).filter(
                AuditEventImmutable.event_type == "DATA_FETCH",
                AuditEventImmutable.action.like(f"%{service.upper()}%"),
                AuditEventImmutable.event_timestamp >= datetime.utcnow() - timedelta(hours=1)
            ).order_by(
                AuditEventImmutable.event_timestamp.desc()
            ).limit(10).all()
            
            if not recent:
                return ComponentHealth(
                    component=f"external_{service}",
                    status=HealthStatus.UNKNOWN,
                    latency_ms=None,
                    message=f"No recent {service} fetches",
                    last_checked=datetime.utcnow()
                )
            
            # Check success rate
            successes = sum(1 for e in recent if e.payload_json and e.payload_json.get("quality") != "FALLBACK")
            success_rate = successes / len(recent)
            
            avg_latency = None
            latencies = [e.payload_json.get("duration_ms") for e in recent if e.payload_json and e.payload_json.get("duration_ms")]
            if latencies:
                avg_latency = sum(latencies) / len(latencies)
            
            if success_rate >= 0.9:
                status = HealthStatus.HEALTHY
                message = f"{service} API healthy ({success_rate*100:.0f}% success)"
            elif success_rate >= 0.5:
                status = HealthStatus.DEGRADED
                message = f"{service} API degraded ({success_rate*100:.0f}% success)"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"{service} API unhealthy ({success_rate*100:.0f}% success)"
            
            return ComponentHealth(
                component=f"external_{service}",
                status=status,
                latency_ms=avg_latency,
                message=message,
                last_checked=datetime.utcnow(),
                details={
                    "success_rate": success_rate,
                    "recent_fetches": len(recent)
                }
            )
            
        except Exception as e:
            return ComponentHealth(
                component=f"external_{service}",
                status=HealthStatus.UNKNOWN,
                latency_ms=None,
                message=f"Error checking {service}: {str(e)}",
                last_checked=datetime.utcnow()
            )

    async def _check_background_jobs(self) -> ComponentHealth:
        """Check background job health."""
        try:
            from app.core.audit.immutable_ledger import AuditEventImmutable
            
            # Check for recent scheduler activity
            recent_refresh = self.db.query(AuditEventImmutable).filter(
                AuditEventImmutable.event_type == "DATA_REFRESH",
                AuditEventImmutable.event_timestamp >= datetime.utcnow() - timedelta(hours=1)
            ).count()
            
            if recent_refresh > 0:
                return ComponentHealth(
                    component="background_jobs",
                    status=HealthStatus.HEALTHY,
                    latency_ms=None,
                    message=f"Background jobs active ({recent_refresh} in last hour)",
                    last_checked=datetime.utcnow(),
                    details={"recent_jobs": recent_refresh}
                )
            else:
                return ComponentHealth(
                    component="background_jobs",
                    status=HealthStatus.DEGRADED,
                    latency_ms=None,
                    message="No background job activity in last hour",
                    last_checked=datetime.utcnow()
                )
                
        except Exception as e:
            return ComponentHealth(
                component="background_jobs",
                status=HealthStatus.UNKNOWN,
                latency_ms=None,
                message=f"Error checking background jobs: {str(e)}",
                last_checked=datetime.utcnow()
            )
