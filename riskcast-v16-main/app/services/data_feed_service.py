"""
Data feed ingestion service.

Ingests data from external market data providers.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from abc import ABC, abstractmethod
import logging

from sqlalchemy.orm import Session

from app.models.corridor import PortIntelligence, CarrierProfile
from app.services.corridor_intelligence_service import CorridorIntelligenceService
from app.services.oracle_event_service import OracleEventService
from app.core.audit_ledger.ledger import AuditLedger

logger = logging.getLogger(__name__)


class DataFeedProvider(ABC):
    """Abstract base class for data feed providers."""
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return provider name identifier."""
        pass
    
    @abstractmethod
    def fetch_port_congestion(self, port_codes: List[str]) -> Dict[str, Any]:
        """
        Fetch port congestion data.
        
        Args:
            port_codes: List of port codes to fetch
            
        Returns:
            Dictionary with provider name, fetched_at timestamp, and data dict
        """
        pass
    
    @abstractmethod
    def fetch_carrier_reliability(self, carrier_codes: List[str]) -> Dict[str, Any]:
        """
        Fetch carrier reliability data.
        
        Args:
            carrier_codes: List of carrier codes to fetch
            
        Returns:
            Dictionary with provider name, fetched_at timestamp, and data dict
        """
        pass
    
    @abstractmethod
    def fetch_corridor_delays(self, corridor_codes: List[str]) -> Dict[str, Any]:
        """
        Fetch corridor delay data.
        
        Args:
            corridor_codes: List of corridor codes to fetch
            
        Returns:
            Dictionary with provider name, fetched_at timestamp, and data dict
        """
        pass


class MarineTrafficProvider(DataFeedProvider):
    """MarineTraffic AIS data provider."""
    
    @property
    def provider_name(self) -> str:
        return "MARINE_TRAFFIC"
    
    def __init__(self, api_key: str):
        """
        Initialize MarineTraffic provider.
        
        Args:
            api_key: API key for MarineTraffic API
        """
        self.api_key = api_key
        self.base_url = "https://api.marinetraffic.com/v1"
    
    def fetch_port_congestion(self, port_codes: List[str]) -> Dict[str, Any]:
        """
        Fetch port congestion data from MarineTraffic.
        
        In production, would make actual API call to MarineTraffic API.
        For now, returns stub structure.
        """
        logger.info(f"Fetching port congestion from {self.provider_name} for {len(port_codes)} ports")
        
        # TODO: Implement actual API call
        # Example:
        # response = requests.get(
        #     f"{self.base_url}/portcongestion",
        #     params={"api_key": self.api_key, "ports": ",".join(port_codes)}
        # )
        
        return {
            "provider": self.provider_name,
            "fetched_at": datetime.utcnow().isoformat(),
            "data": {
                port: {
                    "vessels_at_anchor": 25,
                    "avg_wait_hours": 48,
                    "congestion_level": "HIGH",
                    "berth_utilization": 0.92,
                    "last_updated": datetime.utcnow().isoformat()
                }
                for port in port_codes
            }
        }
    
    def fetch_carrier_reliability(self, carrier_codes: List[str]) -> Dict[str, Any]:
        """MarineTraffic doesn't provide carrier reliability data."""
        raise NotImplementedError(f"{self.provider_name} doesn't provide carrier reliability")
    
    def fetch_corridor_delays(self, corridor_codes: List[str]) -> Dict[str, Any]:
        """
        Fetch transit delay data from MarineTraffic.
        
        In production, would analyze AIS data for transit times.
        """
        logger.info(f"Fetching corridor delays from {self.provider_name} for {len(corridor_codes)} corridors")
        
        # TODO: Implement actual API call
        return {
            "provider": self.provider_name,
            "fetched_at": datetime.utcnow().isoformat(),
            "data": {
                corridor: {
                    "avg_transit_days": 28,
                    "avg_delay_days": 2.5,
                    "on_time_rate": 0.72
                }
                for corridor in corridor_codes
            }
        }


class Project44Provider(DataFeedProvider):
    """Project44 visibility data provider."""
    
    @property
    def provider_name(self) -> str:
        return "PROJECT44"
    
    def __init__(self, api_key: str):
        """
        Initialize Project44 provider.
        
        Args:
            api_key: API key for Project44 API
        """
        self.api_key = api_key
        self.base_url = "https://api.project44.com"
    
    def fetch_port_congestion(self, port_codes: List[str]) -> Dict[str, Any]:
        """
        Fetch port congestion data from Project44.
        
        In production, would make actual API call.
        """
        logger.info(f"Fetching port congestion from {self.provider_name} for {len(port_codes)} ports")
        
        # TODO: Implement actual API call
        return {
            "provider": self.provider_name,
            "fetched_at": datetime.utcnow().isoformat(),
            "data": {
                port: {
                    "dwell_time_days": 5.2,
                    "normal_dwell_time_days": 3.0,
                    "congestion_level": "MEDIUM",
                    "last_updated": datetime.utcnow().isoformat()
                }
                for port in port_codes
            }
        }
    
    def fetch_carrier_reliability(self, carrier_codes: List[str]) -> Dict[str, Any]:
        """
        Fetch carrier reliability metrics from Project44.
        
        In production, would make actual API call.
        """
        logger.info(f"Fetching carrier reliability from {self.provider_name} for {len(carrier_codes)} carriers")
        
        # TODO: Implement actual API call
        return {
            "provider": self.provider_name,
            "fetched_at": datetime.utcnow().isoformat(),
            "data": {
                carrier: {
                    "schedule_reliability": 0.72,
                    "avg_delay_days": 2.5,
                    "on_time_rate": 0.68,
                    "reliability_score": 0.75
                }
                for carrier in carrier_codes
            }
        }
    
    def fetch_corridor_delays(self, corridor_codes: List[str]) -> Dict[str, Any]:
        """
        Fetch corridor delay data from Project44.
        
        In production, would make actual API call.
        """
        logger.info(f"Fetching corridor delays from {self.provider_name} for {len(corridor_codes)} corridors")
        
        # TODO: Implement actual API call
        return {
            "provider": self.provider_name,
            "fetched_at": datetime.utcnow().isoformat(),
            "data": {
                corridor: {
                    "avg_transit_days": 30,
                    "avg_delay_days": 3.1,
                    "on_time_rate": 0.70
                }
                for corridor in corridor_codes
            }
        }


class DataFeedService:
    """Service for managing data feed ingestion."""
    
    def __init__(
        self,
        db: Session,
        corridor_service: CorridorIntelligenceService,
        oracle_service: OracleEventService,
        audit: Optional[AuditLedger] = None
    ):
        """
        Initialize data feed service.
        
        Args:
            db: Database session
            corridor_service: Corridor intelligence service
            oracle_service: Oracle event service
            audit: Optional audit ledger
        """
        self.db = db
        self.corridor_service = corridor_service
        self.oracle_service = oracle_service
        self.audit = audit or AuditLedger(db)
        self.providers: Dict[str, DataFeedProvider] = {}
    
    def register_provider(self, provider: DataFeedProvider):
        """
        Register a data feed provider.
        
        Args:
            provider: DataFeedProvider instance
        """
        self.providers[provider.provider_name] = provider
        logger.info(f"Registered data feed provider: {provider.provider_name}")
    
    def ingest_port_congestion(
        self,
        port_codes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Ingest port congestion data from all providers.
        
        Updates port_intelligence table and creates oracle events.
        
        Args:
            port_codes: Optional list of port codes (if None, fetches all ports)
            
        Returns:
            Dictionary with ingestion results
        """
        if not port_codes:
            # Get all active ports
            ports = self.db.query(PortIntelligence).all()
            port_codes = [p.port_code for p in ports]
        
        if not port_codes:
            logger.warning("No ports found for congestion ingestion")
            return {
                "ports_updated": 0,
                "oracle_events_created": 0,
                "errors": []
            }
        
        results = {
            "ports_updated": 0,
            "oracle_events_created": 0,
            "errors": []
        }
        
        for provider_name, provider in self.providers.items():
            try:
                data = provider.fetch_port_congestion(port_codes)
                
                for port_code, conditions in data.get('data', {}).items():
                    try:
                        # Update port intelligence
                        self.corridor_service.update_port_conditions(
                            port_code=port_code,
                            conditions={
                                **conditions,
                                "source": provider_name,
                                "fetched_at": data.get('fetched_at')
                            }
                        )
                        results["ports_updated"] += 1
                    except Exception as e:
                        error_msg = f"Port {port_code}: {str(e)}"
                        results["errors"].append(error_msg)
                        logger.error(error_msg, exc_info=True)
                    
                    # Create oracle event for audit trail
                    try:
                        self.oracle_service.ingest_event(
                            source=provider_name,
                            event_type="PORT_CONGESTION",
                            payload=conditions,
                            captured_at=datetime.utcnow(),
                            scope_type="PORT",
                            scope_id=port_code
                        )
                        results["oracle_events_created"] += 1
                    except Exception as e:
                        error_msg = f"Oracle event for port {port_code}: {str(e)}"
                        results["errors"].append(error_msg)
                        logger.error(error_msg, exc_info=True)
                
            except Exception as e:
                error_msg = f"Provider {provider_name}: {str(e)}"
                results["errors"].append(error_msg)
                logger.error(error_msg, exc_info=True)
        
        # Audit
        try:
            self.audit.append_event(
                tenant_id=None,
                event_type="DATA_FEED",
                action="PORT_CONGESTION_INGESTED",
                entity_type="data_feed",
                entity_id=None,
                actor_type="SYSTEM",
                actor_id="DATA_FEED_SERVICE",
                payload=results
            )
        except Exception as e:
            logger.error(f"Failed to audit port congestion ingestion: {e}", exc_info=True)
        
        logger.info(f"Port congestion ingestion completed: {results['ports_updated']} ports updated, {results['oracle_events_created']} events created")
        
        return results
    
    def ingest_carrier_reliability(
        self,
        carrier_codes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Ingest carrier reliability data from all providers.
        
        Args:
            carrier_codes: Optional list of carrier codes (if None, fetches all carriers)
            
        Returns:
            Dictionary with ingestion results
        """
        if not carrier_codes:
            carriers = self.db.query(CarrierProfile).all()
            carrier_codes = [c.carrier_code for c in carriers]
        
        if not carrier_codes:
            logger.warning("No carriers found for reliability ingestion")
            return {
                "carriers_updated": 0,
                "oracle_events_created": 0,
                "errors": []
            }
        
        results = {
            "carriers_updated": 0,
            "oracle_events_created": 0,
            "errors": []
        }
        
        for provider_name, provider in self.providers.items():
            try:
                data = provider.fetch_carrier_reliability(carrier_codes)
                
                for carrier_code, metrics in data.get('data', {}).items():
                    try:
                        # Update carrier profile
                        carrier = self.db.query(CarrierProfile).filter(
                            CarrierProfile.carrier_code == carrier_code
                        ).first()
                        
                        if carrier:
                            # Merge with existing metrics
                            existing = carrier.service_quality_json or {}
                            existing.update({
                                **metrics,
                                "source": provider_name,
                                "updated_at": datetime.utcnow().isoformat(),
                                "fetched_at": data.get('fetched_at')
                            })
                            carrier.service_quality_json = existing
                            carrier.updated_at = datetime.utcnow()
                            results["carriers_updated"] += 1
                        else:
                            logger.warning(f"Carrier {carrier_code} not found in database")
                    
                    except Exception as e:
                        error_msg = f"Carrier {carrier_code}: {str(e)}"
                        results["errors"].append(error_msg)
                        logger.error(error_msg, exc_info=True)
                    
                    # Create oracle event
                    try:
                        self.oracle_service.ingest_event(
                            source=provider_name,
                            event_type="CARRIER_RELIABILITY",
                            payload=metrics,
                            captured_at=datetime.utcnow(),
                            scope_type="CARRIER",
                            scope_id=carrier_code
                        )
                        results["oracle_events_created"] += 1
                    except Exception as e:
                        error_msg = f"Oracle event for carrier {carrier_code}: {str(e)}"
                        results["errors"].append(error_msg)
                        logger.error(error_msg, exc_info=True)
                
            except NotImplementedError:
                # Provider doesn't support this data type
                logger.debug(f"Provider {provider_name} doesn't support carrier reliability")
                pass
            except Exception as e:
                error_msg = f"Provider {provider_name}: {str(e)}"
                results["errors"].append(error_msg)
                logger.error(error_msg, exc_info=True)
        
        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to commit carrier updates: {e}", exc_info=True)
            results["errors"].append(f"Commit failed: {str(e)}")
        
        # Audit
        try:
            self.audit.append_event(
                tenant_id=None,
                event_type="DATA_FEED",
                action="CARRIER_RELIABILITY_INGESTED",
                entity_type="data_feed",
                entity_id=None,
                actor_type="SYSTEM",
                actor_id="DATA_FEED_SERVICE",
                payload=results
            )
        except Exception as e:
            logger.error(f"Failed to audit carrier reliability ingestion: {e}", exc_info=True)
        
        logger.info(f"Carrier reliability ingestion completed: {results['carriers_updated']} carriers updated, {results['oracle_events_created']} events created")
        
        return results
    
    def ingest_corridor_delays(
        self,
        corridor_codes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Ingest corridor delay data from all providers.
        
        Args:
            corridor_codes: Optional list of corridor codes (if None, fetches all corridors)
            
        Returns:
            Dictionary with ingestion results
        """
        from app.models.corridor import Corridor
        
        if not corridor_codes:
            corridors = self.db.query(Corridor).filter(
                Corridor.status == 'ACTIVE'
            ).all()
            corridor_codes = [c.corridor_code for c in corridors]
        
        if not corridor_codes:
            logger.warning("No corridors found for delay ingestion")
            return {
                "corridors_processed": 0,
                "oracle_events_created": 0,
                "errors": []
            }
        
        results = {
            "corridors_processed": 0,
            "oracle_events_created": 0,
            "errors": []
        }
        
        for provider_name, provider in self.providers.items():
            try:
                data = provider.fetch_corridor_delays(corridor_codes)
                
                for corridor_code, delay_data in data.get('data', {}).items():
                    try:
                        # Create oracle event for corridor delays
                        self.oracle_service.ingest_event(
                            source=provider_name,
                            event_type="CORRIDOR_DELAY",
                            payload=delay_data,
                            captured_at=datetime.utcnow(),
                            scope_type="ROUTE",
                            scope_id=corridor_code
                        )
                        results["oracle_events_created"] += 1
                        results["corridors_processed"] += 1
                    except Exception as e:
                        error_msg = f"Corridor {corridor_code}: {str(e)}"
                        results["errors"].append(error_msg)
                        logger.error(error_msg, exc_info=True)
                
            except Exception as e:
                error_msg = f"Provider {provider_name}: {str(e)}"
                results["errors"].append(error_msg)
                logger.error(error_msg, exc_info=True)
        
        # Audit
        try:
            self.audit.append_event(
                tenant_id=None,
                event_type="DATA_FEED",
                action="CORRIDOR_DELAYS_INGESTED",
                entity_type="data_feed",
                entity_id=None,
                actor_type="SYSTEM",
                actor_id="DATA_FEED_SERVICE",
                payload=results
            )
        except Exception as e:
            logger.error(f"Failed to audit corridor delays ingestion: {e}", exc_info=True)
        
        logger.info(f"Corridor delays ingestion completed: {results['corridors_processed']} corridors processed, {results['oracle_events_created']} events created")
        
        return results
    
    def run_scheduled_ingestion(self) -> Dict[str, Any]:
        """
        Run all scheduled data ingestion.
        
        Called by cron job or scheduler.
        
        Returns:
            Dictionary with results from all ingestion tasks
        """
        logger.info("Starting scheduled data feed ingestion")
        
        results = {
            "started_at": datetime.utcnow().isoformat(),
            "port_congestion": {},
            "carrier_reliability": {},
            "corridor_delays": {}
        }
        
        try:
            results["port_congestion"] = self.ingest_port_congestion()
        except Exception as e:
            logger.error(f"Port congestion ingestion failed: {e}", exc_info=True)
            results["port_congestion"] = {"error": str(e)}
        
        try:
            results["carrier_reliability"] = self.ingest_carrier_reliability()
        except Exception as e:
            logger.error(f"Carrier reliability ingestion failed: {e}", exc_info=True)
            results["carrier_reliability"] = {"error": str(e)}
        
        try:
            results["corridor_delays"] = self.ingest_corridor_delays()
        except Exception as e:
            logger.error(f"Corridor delays ingestion failed: {e}", exc_info=True)
            results["corridor_delays"] = {"error": str(e)}
        
        results["completed_at"] = datetime.utcnow().isoformat()
        
        logger.info(f"Scheduled data feed ingestion completed: {results}")
        
        return results
