"""
Corridor intelligence service.

Manages corridors, versioned benchmarks, ports, and carriers.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
import hashlib
import json
import logging

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.corridor import Corridor, CorridorBenchmark, PortIntelligence, CarrierProfile
from app.core.audit_ledger.ledger import AuditLedger
from app.shared.utils import generate_ulid

logger = logging.getLogger(__name__)


class CorridorService:
    """Service for corridor intelligence management."""
    
    def __init__(self, db: Session, audit: Optional[AuditLedger] = None):
        """
        Initialize corridor service.
        
        Args:
            db: Database session
            audit: Optional audit ledger
        """
        self.db = db
        self.audit = audit or AuditLedger(db)
    
    def create_corridor(
        self,
        corridor_code: str,
        name: str,
        origin_port_code: str,
        destination_port_code: str,
        created_by: Optional[str] = None,
        description: Optional[str] = None,
        origin_port_name: Optional[str] = None,
        origin_country: Optional[str] = None,
        origin_coordinates: Optional[Dict[str, float]] = None,
        destination_port_name: Optional[str] = None,
        destination_country: Optional[str] = None,
        destination_coordinates: Optional[Dict[str, float]] = None,
        distance_nm: Optional[int] = None,
        typical_transit_days: Optional[int] = None,
        route_type: Optional[str] = None,
        transshipment_ports: Optional[List[str]] = None,
        trade_lane: Optional[str] = None,
        region: Optional[str] = None,
        cargo_types: Optional[List[str]] = None
    ) -> Corridor:
        """
        Create a new corridor.
        
        Args:
            corridor_code: Unique corridor code (e.g., "SHA-ROT")
            name: Corridor name
            origin_port_code: Origin port code
            destination_port_code: Destination port code
            created_by: User ID creating (ULID string)
            ... other optional fields
            
        Returns:
            Created Corridor instance
        """
        # Check if corridor code already exists
        existing = self.db.query(Corridor).filter(
            Corridor.corridor_code == corridor_code
        ).first()
        if existing:
            raise CorridorExistsError(f"Corridor with code {corridor_code} already exists")
        
        corridor = Corridor(
            id=generate_ulid(),
            corridor_code=corridor_code,
            name=name,
            description=description,
            origin_port_code=origin_port_code,
            origin_port_name=origin_port_name,
            origin_country=origin_country,
            origin_coordinates=origin_coordinates,
            destination_port_code=destination_port_code,
            destination_port_name=destination_port_name,
            destination_country=destination_country,
            destination_coordinates=destination_coordinates,
            distance_nm=distance_nm,
            typical_transit_days=typical_transit_days,
            route_type=route_type,
            transshipment_ports=transshipment_ports,
            trade_lane=trade_lane,
            region=region,
            cargo_types=cargo_types,
            status='ACTIVE',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(corridor)
        self.db.commit()
        self.db.refresh(corridor)
        
        # Audit
        if created_by:
            self.audit.append_event(
                tenant_id=None,
                event_type="CORRIDOR",
                action="CREATED",
                entity_type="corridor",
                entity_id=corridor.id,
                actor_type="USER",
                actor_id=created_by,
                payload={"corridor_code": corridor_code, "name": name}
            )
        
        logger.info(f"Created corridor: {corridor.id} ({corridor_code})")
        
        return corridor
    
    def create_benchmark(
        self,
        corridor_id: str,
        effective_from: date,
        delay_metrics: Dict[str, Any],
        risk_metrics: Dict[str, Any],
        created_by: str,
        effective_to: Optional[date] = None,
        data_source: Optional[str] = None,
        data_period_start: Optional[date] = None,
        data_period_end: Optional[date] = None,
        sample_size: Optional[int] = None,
        carrier_performance: Optional[Dict[str, Any]] = None,
        seasonal_factors: Optional[Dict[str, Any]] = None,
        cost_benchmarks: Optional[Dict[str, Any]] = None
    ) -> CorridorBenchmark:
        """
        Create a new benchmark version for a corridor.
        
        Args:
            corridor_id: Corridor ID (ULID string)
            effective_from: Effective start date
            delay_metrics: Delay metrics dictionary
            risk_metrics: Risk metrics dictionary
            created_by: User ID creating (ULID string)
            effective_to: Optional effective end date
            data_source: Data source identifier
            data_period_start: Data period start
            data_period_end: Data period end
            sample_size: Sample size
            carrier_performance: Carrier performance dictionary
            seasonal_factors: Seasonal factors dictionary
            cost_benchmarks: Cost benchmarks dictionary
            
        Returns:
            Created CorridorBenchmark instance
        """
        # Verify corridor exists
        corridor = self.db.query(Corridor).filter(Corridor.id == corridor_id).first()
        if not corridor:
            raise CorridorNotFoundError(f"Corridor {corridor_id} not found")
        
        # Get next version number
        existing_versions = self.db.query(CorridorBenchmark).filter(
            CorridorBenchmark.corridor_id == corridor_id
        ).count()
        next_version = existing_versions + 1
        
        # Mark previous current benchmark as not current
        if effective_to is None:  # This will be the new current
            self.db.query(CorridorBenchmark).filter(
                CorridorBenchmark.corridor_id == corridor_id,
                CorridorBenchmark.is_current == True
            ).update({'is_current': False}, synchronize_session=False)
        
        # Build benchmark data
        benchmark_data = {
            "delay_metrics": delay_metrics,
            "risk_metrics": risk_metrics,
            "carrier_performance": carrier_performance or {},
            "seasonal_factors": seasonal_factors or {},
            "cost_benchmarks": cost_benchmarks or {}
        }
        
        # Compute hash
        benchmark_hash = self._compute_benchmark_hash(benchmark_data)
        
        benchmark = CorridorBenchmark(
            id=generate_ulid(),
            corridor_id=corridor_id,
            version=next_version,
            effective_from=effective_from,
            effective_to=effective_to,
            is_current=(effective_to is None),
            data_source=data_source,
            data_period_start=data_period_start,
            data_period_end=data_period_end,
            sample_size=sample_size,
            delay_metrics_json=delay_metrics,
            risk_metrics_json=risk_metrics,
            carrier_performance_json=carrier_performance,
            seasonal_factors_json=seasonal_factors,
            cost_benchmarks_json=cost_benchmarks,
            benchmark_hash=benchmark_hash,
            created_by_user_id=created_by,
            created_at=datetime.utcnow()
        )
        
        self.db.add(benchmark)
        self.db.commit()
        self.db.refresh(benchmark)
        
        # Audit
        self.audit.append_event(
            tenant_id=None,
            event_type="CORRIDOR_BENCHMARK",
            action="CREATED",
            entity_type="corridor_benchmark",
            entity_id=benchmark.id,
            actor_type="USER",
            actor_id=created_by,
            payload={
                "corridor_id": corridor_id,
                "version": next_version,
                "effective_from": effective_from.isoformat(),
                "is_current": benchmark.is_current
            }
        )
        
        logger.info(f"Created benchmark v{next_version} for corridor {corridor_id}")
        
        return benchmark
    
    def get_current_benchmark(
        self,
        corridor_id: str
    ) -> Optional[CorridorBenchmark]:
        """
        Get current benchmark for a corridor.
        
        Args:
            corridor_id: Corridor ID (ULID string)
            
        Returns:
            Current CorridorBenchmark or None
        """
        return self.db.query(CorridorBenchmark).filter(
            CorridorBenchmark.corridor_id == corridor_id,
            CorridorBenchmark.is_current == True
        ).first()
    
    def get_benchmark_for_date(
        self,
        corridor_id: str,
        target_date: date
    ) -> Optional[CorridorBenchmark]:
        """
        Get benchmark effective for a specific date.
        
        Args:
            corridor_id: Corridor ID (ULID string)
            target_date: Target date
            
        Returns:
            CorridorBenchmark effective for date or None
        """
        return self.db.query(CorridorBenchmark).filter(
            CorridorBenchmark.corridor_id == corridor_id,
            CorridorBenchmark.effective_from <= target_date,
            or_(
                CorridorBenchmark.effective_to >= target_date,
                CorridorBenchmark.effective_to.is_(None)
            )
        ).order_by(CorridorBenchmark.effective_from.desc()).first()
    
    def list_corridors(
        self,
        trade_lane: Optional[str] = None,
        region: Optional[str] = None,
        status: Optional[str] = None,
        origin_country: Optional[str] = None,
        destination_country: Optional[str] = None
    ) -> List[Corridor]:
        """
        List corridors with filters.
        
        Args:
            trade_lane: Filter by trade lane
            region: Filter by region
            status: Filter by status
            origin_country: Filter by origin country
            destination_country: Filter by destination country
            
        Returns:
            List of Corridor instances
        """
        query = self.db.query(Corridor)
        
        if trade_lane:
            query = query.filter(Corridor.trade_lane == trade_lane)
        if region:
            query = query.filter(Corridor.region == region)
        if status:
            query = query.filter(Corridor.status == status)
        if origin_country:
            query = query.filter(Corridor.origin_country == origin_country)
        if destination_country:
            query = query.filter(Corridor.destination_country == destination_country)
        
        return query.order_by(Corridor.name).all()
    
    def create_or_update_port(
        self,
        port_code: str,
        port_name: str,
        country: str,
        region: Optional[str] = None,
        coordinates: Optional[Dict[str, float]] = None,
        port_type: Optional[str] = None,
        size_class: Optional[str] = None,
        annual_teu_capacity: Optional[int] = None,
        current_conditions: Optional[Dict[str, Any]] = None,
        risk_factors: Optional[Dict[str, Any]] = None
    ) -> PortIntelligence:
        """
        Create or update port intelligence.
        
        Args:
            port_code: Port code (e.g., "SGSIN")
            port_name: Port name
            country: Country code
            ... other optional fields
            
        Returns:
            PortIntelligence instance
        """
        port = self.db.query(PortIntelligence).filter(
            PortIntelligence.port_code == port_code
        ).first()
        
        if port:
            # Update existing
            port.port_name = port_name
            port.country = country
            if region is not None:
                port.region = region
            if coordinates is not None:
                port.coordinates = coordinates
            if port_type is not None:
                port.port_type = port_type
            if size_class is not None:
                port.size_class = size_class
            if annual_teu_capacity is not None:
                port.annual_teu_capacity = annual_teu_capacity
            if current_conditions is not None:
                port.current_conditions_json = current_conditions
            if risk_factors is not None:
                port.risk_factors_json = risk_factors
            port.updated_at = datetime.utcnow()
        else:
            # Create new
            port = PortIntelligence(
                id=generate_ulid(),
                port_code=port_code,
                port_name=port_name,
                country=country,
                region=region,
                coordinates=coordinates,
                port_type=port_type,
                size_class=size_class,
                annual_teu_capacity=annual_teu_capacity,
                current_conditions_json=current_conditions,
                risk_factors_json=risk_factors,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self.db.add(port)
        
        self.db.commit()
        self.db.refresh(port)
        
        logger.info(f"Created/updated port: {port.id} ({port_code})")
        
        return port
    
    def create_or_update_carrier(
        self,
        carrier_code: str,
        carrier_name: str,
        carrier_type: Optional[str] = None,
        global_metrics: Optional[Dict[str, Any]] = None,
        service_quality: Optional[Dict[str, Any]] = None
    ) -> CarrierProfile:
        """
        Create or update carrier profile.
        
        Args:
            carrier_code: Carrier code (e.g., "MAERSK")
            carrier_name: Carrier name
            carrier_type: Carrier type
            global_metrics: Global metrics dictionary
            service_quality: Service quality dictionary
            
        Returns:
            CarrierProfile instance
        """
        carrier = self.db.query(CarrierProfile).filter(
            CarrierProfile.carrier_code == carrier_code
        ).first()
        
        if carrier:
            # Update existing
            carrier.carrier_name = carrier_name
            if carrier_type is not None:
                carrier.carrier_type = carrier_type
            if global_metrics is not None:
                carrier.global_metrics_json = global_metrics
            if service_quality is not None:
                carrier.service_quality_json = service_quality
            carrier.updated_at = datetime.utcnow()
        else:
            # Create new
            carrier = CarrierProfile(
                id=generate_ulid(),
                carrier_code=carrier_code,
                carrier_name=carrier_name,
                carrier_type=carrier_type,
                global_metrics_json=global_metrics,
                service_quality_json=service_quality,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self.db.add(carrier)
        
        self.db.commit()
        self.db.refresh(carrier)
        
        logger.info(f"Created/updated carrier: {carrier.id} ({carrier_code})")
        
        return carrier
    
    def _compute_benchmark_hash(self, benchmark_data: Dict[str, Any]) -> str:
        """
        Compute hash of benchmark data.
        
        Args:
            benchmark_data: Benchmark data dictionary
            
        Returns:
            SHA256 hash string
        """
        canonical = json.dumps(benchmark_data, sort_keys=True, separators=(',', ':'), default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()


# Exception classes
class CorridorNotFoundError(Exception):
    """Corridor not found"""
    pass


class CorridorExistsError(Exception):
    """Corridor already exists"""
    pass


class BenchmarkNotFoundError(Exception):
    """Benchmark not found"""
    pass
