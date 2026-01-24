"""
Data Refresh Scheduler

Automatically refreshes external data sources to maintain data freshness.
Prevents system from silently using stale data.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Awaitable
from dataclasses import dataclass
from enum import Enum
import logging
from uuid import uuid4

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.interval import IntervalTrigger
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False
    # Fallback for when APScheduler not installed
    AsyncIOScheduler = None
    IntervalTrigger = None

from app.integrations.climate import get_climate_service
from app.integrations.ports import get_port_service
from app.integrations.carriers import get_carrier_service
from app.integrations.weather import get_weather_service

logger = logging.getLogger(__name__)


class RefreshStatus(Enum):
    """Status of a refresh job."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"  # Some items failed


class DataSourcePriority(Enum):
    """Priority for data refresh."""
    CRITICAL = 1    # Refresh every 5 minutes
    HIGH = 2        # Refresh every 15 minutes
    MEDIUM = 3      # Refresh every hour
    LOW = 4         # Refresh every 6 hours
    BACKGROUND = 5  # Refresh daily


@dataclass
class RefreshJob:
    """A data refresh job."""
    id: str
    source_name: str
    source_type: str
    priority: DataSourcePriority
    interval_minutes: int
    last_run: Optional[datetime]
    last_status: RefreshStatus
    last_error: Optional[str]
    consecutive_failures: int
    total_runs: int
    total_successes: int
    total_failures: int
    avg_duration_seconds: float
    is_enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "source_name": self.source_name,
            "source_type": self.source_type,
            "priority": self.priority.name,
            "interval_minutes": self.interval_minutes,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "last_status": self.last_status.value,
            "last_error": self.last_error,
            "consecutive_failures": self.consecutive_failures,
            "total_runs": self.total_runs,
            "total_successes": self.total_successes,
            "total_failures": self.total_failures,
            "success_rate": self.total_successes / self.total_runs if self.total_runs > 0 else 0,
            "avg_duration_seconds": self.avg_duration_seconds,
            "is_enabled": self.is_enabled,
        }


@dataclass
class RefreshResult:
    """Result of a refresh operation."""
    job_id: str
    source_name: str
    status: RefreshStatus
    started_at: datetime
    completed_at: datetime
    duration_seconds: float
    items_refreshed: int
    items_failed: int
    error_message: Optional[str]
    data_quality: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "job_id": self.job_id,
            "source_name": self.source_name,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat(),
            "duration_seconds": self.duration_seconds,
            "items_refreshed": self.items_refreshed,
            "items_failed": self.items_failed,
            "error_message": self.error_message,
            "data_quality": self.data_quality,
        }


class DataRefreshScheduler:
    """
    Schedules and executes data refresh jobs.
    
    Ensures data freshness across all external sources.
    """
    
    # Default refresh intervals by source type
    DEFAULT_INTERVALS = {
        "weather": 15,       # 15 minutes
        "port": 60,          # 1 hour
        "carrier": 360,      # 6 hours
        "climate": 1440,     # 24 hours
        "historical": 10080, # 7 days
    }
    
    # Priority thresholds for alerts
    STALE_THRESHOLDS = {
        DataSourcePriority.CRITICAL: timedelta(minutes=30),
        DataSourcePriority.HIGH: timedelta(hours=1),
        DataSourcePriority.MEDIUM: timedelta(hours=6),
        DataSourcePriority.LOW: timedelta(hours=24),
        DataSourcePriority.BACKGROUND: timedelta(days=7),
    }
    
    def __init__(
        self,
        audit: Optional[Any] = None,
        weather_service: Optional[Any] = None,
        port_service: Optional[Any] = None,
        carrier_service: Optional[Any] = None,
        climate_service: Optional[Any] = None,
    ):
        self.audit = audit
        self.weather_service = weather_service
        self.port_service = port_service
        self.carrier_service = carrier_service
        self.climate_service = climate_service
        
        if not APSCHEDULER_AVAILABLE:
            logger.warning("APScheduler not available. Install with: pip install apscheduler")
            self.scheduler = None
        else:
            self.scheduler = AsyncIOScheduler()
        
        self.jobs: Dict[str, RefreshJob] = {}
        self.logger = logging.getLogger(__name__)
        
        # Ports and carriers to refresh
        self.active_ports: List[str] = []
        self.active_carriers: List[str] = []
    
    def configure_active_entities(
        self,
        ports: List[str],
        carriers: List[str]
    ):
        """Configure which ports and carriers to actively refresh."""
        self.active_ports = ports
        self.active_carriers = carriers
        self.logger.info(
            f"Configured refresh for {len(ports)} ports and {len(carriers)} carriers"
        )
    
    def start(self):
        """Start the scheduler."""
        if not self.scheduler:
            self.logger.error("Cannot start scheduler: APScheduler not available")
            return
        
        # Initialize services if not provided
        if not self.weather_service:
            try:
                self.weather_service = get_weather_service(self.audit)
            except Exception as e:
                self.logger.warning(f"Could not initialize weather service: {e}")
        
        if not self.port_service:
            try:
                self.port_service = get_port_service(self.audit)
            except Exception as e:
                self.logger.warning(f"Could not initialize port service: {e}")
        
        if not self.carrier_service:
            try:
                self.carrier_service = get_carrier_service(self.audit)
            except Exception as e:
                self.logger.warning(f"Could not initialize carrier service: {e}")
        
        if not self.climate_service:
            try:
                self.climate_service = get_climate_service(self.audit)
            except Exception as e:
                self.logger.warning(f"Could not initialize climate service: {e}")
        
        self._setup_default_jobs()
        self.scheduler.start()
        self.logger.info("Data refresh scheduler started")
    
    def stop(self):
        """Stop the scheduler."""
        if self.scheduler:
            self.scheduler.shutdown(wait=True)
            self.logger.info("Data refresh scheduler stopped")
    
    def _setup_default_jobs(self):
        """Setup default refresh jobs."""
        if not self.scheduler:
            return
        
        # Weather refresh - every 15 minutes
        self._add_job(
            job_id="refresh_weather",
            source_name="weather",
            source_type="weather",
            priority=DataSourcePriority.HIGH,
            interval_minutes=15,
            func=self._refresh_weather
        )
        
        # Port conditions - every hour
        self._add_job(
            job_id="refresh_ports",
            source_name="port_conditions",
            source_type="port",
            priority=DataSourcePriority.MEDIUM,
            interval_minutes=60,
            func=self._refresh_ports
        )
        
        # Carrier performance - every 6 hours
        self._add_job(
            job_id="refresh_carriers",
            source_name="carrier_performance",
            source_type="carrier",
            priority=DataSourcePriority.LOW,
            interval_minutes=360,
            func=self._refresh_carriers
        )
        
        # Climate indices - daily
        self._add_job(
            job_id="refresh_climate",
            source_name="climate_indices",
            source_type="climate",
            priority=DataSourcePriority.BACKGROUND,
            interval_minutes=1440,
            func=self._refresh_climate
        )
        
        # Data staleness check - every 5 minutes
        self._add_job(
            job_id="check_staleness",
            source_name="staleness_monitor",
            source_type="monitor",
            priority=DataSourcePriority.CRITICAL,
            interval_minutes=5,
            func=self._check_data_staleness
        )
    
    def _add_job(
        self,
        job_id: str,
        source_name: str,
        source_type: str,
        priority: DataSourcePriority,
        interval_minutes: int,
        func: Callable[[], Awaitable[RefreshResult]]
    ):
        """Add a refresh job."""
        if not self.scheduler:
            return
        
        # Create job record
        job = RefreshJob(
            id=job_id,
            source_name=source_name,
            source_type=source_type,
            priority=priority,
            interval_minutes=interval_minutes,
            last_run=None,
            last_status=RefreshStatus.PENDING,
            last_error=None,
            consecutive_failures=0,
            total_runs=0,
            total_successes=0,
            total_failures=0,
            avg_duration_seconds=0.0
        )
        self.jobs[job_id] = job
        
        # Schedule with APScheduler
        self.scheduler.add_job(
            self._execute_job,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id=job_id,
            args=[job_id, func],
            replace_existing=True
        )
        
        self.logger.info(f"Added refresh job: {job_id} (every {interval_minutes} min)")
    
    async def _execute_job(
        self,
        job_id: str,
        func: Callable[[], Awaitable[RefreshResult]]
    ):
        """Execute a refresh job."""
        job = self.jobs.get(job_id)
        if not job or not job.is_enabled:
            return
        
        started_at = datetime.utcnow()
        job.last_run = started_at
        job.last_status = RefreshStatus.RUNNING
        
        try:
            result = await func()
            
            # Update job stats
            job.total_runs += 1
            if result.status == RefreshStatus.SUCCESS:
                job.total_successes += 1
                job.consecutive_failures = 0
            elif result.status == RefreshStatus.FAILED:
                job.total_failures += 1
                job.consecutive_failures += 1
            elif result.status == RefreshStatus.PARTIAL:
                job.total_successes += 1  # Partial is still a success
                job.consecutive_failures = 0
            
            job.last_status = result.status
            job.last_error = result.error_message
            
            # Update average duration
            job.avg_duration_seconds = (
                (job.avg_duration_seconds * (job.total_runs - 1) + result.duration_seconds)
                / job.total_runs
            )
            
            # Audit
            if self.audit:
                try:
                    tenant_id = getattr(self.audit, 'tenant_id', None) or "system"
                    self.audit.append_event(
                        tenant_id=tenant_id,
                        event_type="DATA_REFRESH",
                        action=f"REFRESH_{job.source_type.upper()}",
                        entity_type="refresh_job",
                        entity_id=job_id,
                        actor_type="SCHEDULER",
                        payload={
                            "status": result.status.value,
                            "items_refreshed": result.items_refreshed,
                            "items_failed": result.items_failed,
                            "duration_seconds": result.duration_seconds,
                            "data_quality": result.data_quality
                        }
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to audit refresh: {e}")
            
            # Alert if consecutive failures
            if job.consecutive_failures >= 3:
                await self._send_alert(
                    f"Data refresh failing: {job.source_name}",
                    f"{job.consecutive_failures} consecutive failures. Last error: {job.last_error}"
                )
            
        except Exception as e:
            job.total_runs += 1
            job.total_failures += 1
            job.consecutive_failures += 1
            job.last_status = RefreshStatus.FAILED
            job.last_error = str(e)
            
            self.logger.error(f"Job {job_id} failed: {e}", exc_info=True)
    
    async def _refresh_weather(self) -> RefreshResult:
        """Refresh weather data for active ports."""
        started_at = datetime.utcnow()
        refreshed = 0
        failed = 0
        
        if not self.weather_service:
            return RefreshResult(
                job_id="refresh_weather",
                source_name="weather",
                status=RefreshStatus.FAILED,
                started_at=started_at,
                completed_at=datetime.utcnow(),
                duration_seconds=0,
                items_refreshed=0,
                items_failed=0,
                error_message="Weather service not available",
                data_quality="UNAVAILABLE"
            )
        
        for port_code in self.active_ports[:50]:  # Limit to 50 ports per refresh
            try:
                # Get port coordinates
                port_info = await self._get_port_info(port_code)
                if port_info:
                    await self.weather_service.get_weather_for_port(
                        port_code=port_code,
                        port_lat=port_info.get("lat"),
                        port_lng=port_info.get("lng")
                    )
                    refreshed += 1
            except Exception as e:
                self.logger.error(f"Failed to refresh weather for {port_code}: {e}")
                failed += 1
        
        completed_at = datetime.utcnow()
        
        return RefreshResult(
            job_id="refresh_weather",
            source_name="weather",
            status=RefreshStatus.SUCCESS if failed == 0 else RefreshStatus.PARTIAL,
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=(completed_at - started_at).total_seconds(),
            items_refreshed=refreshed,
            items_failed=failed,
            error_message=f"{failed} ports failed" if failed > 0 else None,
            data_quality="REAL_TIME" if failed == 0 else "PARTIAL"
        )
    
    async def _refresh_ports(self) -> RefreshResult:
        """Refresh port conditions."""
        started_at = datetime.utcnow()
        refreshed = 0
        failed = 0
        
        if not self.port_service:
            return RefreshResult(
                job_id="refresh_ports",
                source_name="port_conditions",
                status=RefreshStatus.FAILED,
                started_at=started_at,
                completed_at=datetime.utcnow(),
                duration_seconds=0,
                items_refreshed=0,
                items_failed=0,
                error_message="Port service not available",
                data_quality="UNAVAILABLE"
            )
        
        for port_code in self.active_ports[:50]:  # Limit to 50 ports per refresh
            try:
                await self.port_service.get_port_risk_assessment(port_code)
                refreshed += 1
            except Exception as e:
                self.logger.error(f"Failed to refresh port {port_code}: {e}")
                failed += 1
        
        completed_at = datetime.utcnow()
        
        return RefreshResult(
            job_id="refresh_ports",
            source_name="port_conditions",
            status=RefreshStatus.SUCCESS if failed == 0 else RefreshStatus.PARTIAL,
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=(completed_at - started_at).total_seconds(),
            items_refreshed=refreshed,
            items_failed=failed,
            error_message=f"{failed} ports failed" if failed > 0 else None,
            data_quality="REAL_TIME" if failed == 0 else "PARTIAL"
        )
    
    async def _refresh_carriers(self) -> RefreshResult:
        """Refresh carrier performance."""
        started_at = datetime.utcnow()
        refreshed = 0
        failed = 0
        
        if not self.carrier_service:
            return RefreshResult(
                job_id="refresh_carriers",
                source_name="carrier_performance",
                status=RefreshStatus.FAILED,
                started_at=started_at,
                completed_at=datetime.utcnow(),
                duration_seconds=0,
                items_refreshed=0,
                items_failed=0,
                error_message="Carrier service not available",
                data_quality="UNAVAILABLE"
            )
        
        for carrier_code in self.active_carriers[:50]:  # Limit to 50 carriers per refresh
            try:
                await self.carrier_service.get_carrier_risk_assessment(carrier_code)
                refreshed += 1
            except Exception as e:
                self.logger.error(f"Failed to refresh carrier {carrier_code}: {e}")
                failed += 1
        
        completed_at = datetime.utcnow()
        
        return RefreshResult(
            job_id="refresh_carriers",
            source_name="carrier_performance",
            status=RefreshStatus.SUCCESS if failed == 0 else RefreshStatus.PARTIAL,
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=(completed_at - started_at).total_seconds(),
            items_refreshed=refreshed,
            items_failed=failed,
            error_message=f"{failed} carriers failed" if failed > 0 else None,
            data_quality="REAL_TIME" if failed == 0 else "PARTIAL"
        )
    
    async def _refresh_climate(self) -> RefreshResult:
        """Refresh climate indices."""
        started_at = datetime.utcnow()
        
        if not self.climate_service:
            return RefreshResult(
                job_id="refresh_climate",
                source_name="climate_indices",
                status=RefreshStatus.FAILED,
                started_at=started_at,
                completed_at=datetime.utcnow(),
                duration_seconds=0,
                items_refreshed=0,
                items_failed=1,
                error_message="Climate service not available",
                data_quality="UNAVAILABLE"
            )
        
        try:
            await self.climate_service.get_climate_risk_assessment()
            
            completed_at = datetime.utcnow()
            return RefreshResult(
                job_id="refresh_climate",
                source_name="climate_indices",
                status=RefreshStatus.SUCCESS,
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=(completed_at - started_at).total_seconds(),
                items_refreshed=1,
                items_failed=0,
                error_message=None,
                data_quality="REAL_TIME"
            )
            
        except Exception as e:
            completed_at = datetime.utcnow()
            return RefreshResult(
                job_id="refresh_climate",
                source_name="climate_indices",
                status=RefreshStatus.FAILED,
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=(completed_at - started_at).total_seconds(),
                items_refreshed=0,
                items_failed=1,
                error_message=str(e),
                data_quality="FALLBACK"
            )
    
    async def _check_data_staleness(self) -> RefreshResult:
        """Check for stale data and alert."""
        started_at = datetime.utcnow()
        stale_sources = []
        
        for job_id, job in self.jobs.items():
            if job_id == "check_staleness":
                continue
            
            if not job.last_run:
                stale_sources.append(f"{job.source_name} (never refreshed)")
                continue
            
            threshold = self.STALE_THRESHOLDS.get(
                job.priority,
                timedelta(hours=24)
            )
            
            if datetime.utcnow() - job.last_run > threshold:
                stale_sources.append(
                    f"{job.source_name} (last: {job.last_run.isoformat()})"
                )
        
        completed_at = datetime.utcnow()
        
        if stale_sources:
            await self._send_alert(
                "Stale data detected",
                f"The following data sources are stale: {', '.join(stale_sources)}"
            )
        
        return RefreshResult(
            job_id="check_staleness",
            source_name="staleness_monitor",
            status=RefreshStatus.SUCCESS,
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=(completed_at - started_at).total_seconds(),
            items_refreshed=len(self.jobs) - 1,
            items_failed=len(stale_sources),
            error_message=f"{len(stale_sources)} stale sources" if stale_sources else None,
            data_quality=None
        )
    
    async def _send_alert(self, title: str, message: str):
        """Send alert for data issues."""
        # This would integrate with your alerting system (Slack, PagerDuty, etc.)
        self.logger.warning(f"ALERT: {title} - {message}")
        
        if self.audit:
            try:
                tenant_id = getattr(self.audit, 'tenant_id', None) or "system"
                self.audit.append_event(
                    tenant_id=tenant_id,
                    event_type="ALERT",
                    action="DATA_STALENESS_ALERT",
                    entity_type="data_quality",
                    entity_id=str(uuid4()),
                    actor_type="SCHEDULER",
                    payload={
                        "title": title,
                        "message": message,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
            except Exception as e:
                self.logger.warning(f"Failed to audit alert: {e}")
    
    async def _get_port_info(self, port_code: str) -> Optional[Dict[str, Any]]:
        """Get port coordinates from database or cache."""
        try:
            from app.integrations.ports.marine_traffic import PORT_INFO_DATABASE
            return PORT_INFO_DATABASE.get(port_code)
        except ImportError:
            # Fallback: return None, service will handle it
            return None
    
    def get_job_status(self) -> List[Dict[str, Any]]:
        """Get status of all jobs."""
        return [job.to_dict() for job in self.jobs.values()]
    
    def trigger_refresh(self, job_id: str):
        """Manually trigger a refresh job."""
        if not self.scheduler:
            self.logger.error("Cannot trigger refresh: scheduler not available")
            return
        
        if job_id in self.jobs:
            try:
                self.scheduler.modify_job(job_id, next_run_time=datetime.utcnow())
                self.logger.info(f"Manually triggered refresh job: {job_id}")
            except Exception as e:
                self.logger.error(f"Failed to trigger job {job_id}: {e}")
        else:
            self.logger.warning(f"Job {job_id} not found")
    
    async def run_refresh_now(self, job_id: str) -> RefreshResult:
        """Run a refresh job immediately and return result."""
        job = self.jobs.get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        # Get the function for this job
        func_map = {
            "refresh_weather": self._refresh_weather,
            "refresh_ports": self._refresh_ports,
            "refresh_carriers": self._refresh_carriers,
            "refresh_climate": self._refresh_climate,
            "check_staleness": self._check_data_staleness,
        }
        
        func = func_map.get(job_id)
        if not func:
            raise ValueError(f"No function for job {job_id}")
        
        # Execute
        result = await func()
        
        # Update job stats
        await self._execute_job(job_id, func)
        
        return result


# Singleton instance
data_refresh_scheduler: Optional[DataRefreshScheduler] = None


def get_data_refresh_scheduler(
    audit: Optional[Any] = None,
    **kwargs
) -> DataRefreshScheduler:
    """Get or create data refresh scheduler singleton."""
    global data_refresh_scheduler
    if data_refresh_scheduler is None:
        data_refresh_scheduler = DataRefreshScheduler(audit=audit, **kwargs)
    return data_refresh_scheduler
