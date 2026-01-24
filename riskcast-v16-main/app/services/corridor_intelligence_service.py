"""
Corridor intelligence service.

Manages corridor data, benchmarks, and real-time updates.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
import hashlib
import json
import logging

import sqlalchemy as sa
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models.corridor import Corridor, CorridorBenchmark, PortIntelligence, CarrierProfile
from app.core.audit_ledger.ledger import AuditLedger
from app.shared.utils import generate_ulid

logger = logging.getLogger(__name__)


class CorridorIntelligenceService:
    """Service for corridor intelligence management."""
    
    def __init__(self, db: Session, audit: Optional[AuditLedger] = None):
        """
        Initialize corridor intelligence service.
        
        Args:
            db: Database session
            audit: Optional audit ledger
        """
        self.db = db
        self.audit = audit or AuditLedger(db)
    
    # ==================== Corridor Management ====================
    
    def create_corridor(
        self,
        corridor_code: str,
        name: str,
        origin_port_code: str,
        destination_port_code: str,
        created_by: str,
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
        # Check for existing
        existing = self.db.query(Corridor).filter(
            Corridor.corridor_code == corridor_code
        ).first()
        if existing:
            raise CorridorExistsError(f"Corridor {corridor_code} already exists")
        
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
        self.audit.append_event(
            tenant_id=None,
            event_type="CORRIDOR",
            action="CREATED",
            entity_type="corridor",
            entity_id=corridor.id,
            actor_type="USER",
            actor_id=created_by,
            payload={
                "corridor_code": corridor_code,
                "origin": origin_port_code,
                "destination": destination_port_code
            }
        )
        
        logger.info(f"Created corridor: {corridor.id} ({corridor_code})")
        
        return corridor
    
    def get_corridor(self, corridor_id: str) -> Corridor:
        """
        Get corridor by ID.
        
        Args:
            corridor_id: Corridor ID (ULID string)
            
        Returns:
            Corridor instance
            
        Raises:
            CorridorNotFoundError: If corridor not found
        """
        corridor = self.db.query(Corridor).filter(
            Corridor.id == corridor_id
        ).first()
        if not corridor:
            raise CorridorNotFoundError(f"Corridor {corridor_id} not found")
        return corridor
    
    def get_corridor_by_code(self, corridor_code: str) -> Corridor:
        """
        Get corridor by code.
        
        Args:
            corridor_code: Corridor code
            
        Returns:
            Corridor instance
            
        Raises:
            CorridorNotFoundError: If corridor not found
        """
        corridor = self.db.query(Corridor).filter(
            Corridor.corridor_code == corridor_code
        ).first()
        if not corridor:
            raise CorridorNotFoundError(f"Corridor {corridor_code} not found")
        return corridor
    
    def find_corridor(
        self,
        origin_port_code: str,
        destination_port_code: str
    ) -> Optional[Corridor]:
        """
        Find corridor by origin/destination.
        
        Args:
            origin_port_code: Origin port code
            destination_port_code: Destination port code
            
        Returns:
            Corridor instance or None
        """
        return self.db.query(Corridor).filter(
            Corridor.origin_port_code == origin_port_code,
            Corridor.destination_port_code == destination_port_code,
            Corridor.status == 'ACTIVE'
        ).first()
    
    def list_corridors(
        self,
        trade_lane: Optional[str] = None,
        origin_country: Optional[str] = None,
        destination_country: Optional[str] = None,
        status: str = 'ACTIVE'
    ) -> List[Corridor]:
        """
        List corridors with filters.
        
        Args:
            trade_lane: Filter by trade lane
            origin_country: Filter by origin country
            destination_country: Filter by destination country
            status: Filter by status (default: 'ACTIVE')
            
        Returns:
            List of Corridor instances
        """
        query = self.db.query(Corridor).filter(Corridor.status == status)
        
        if trade_lane:
            query = query.filter(Corridor.trade_lane == trade_lane)
        if origin_country:
            query = query.filter(Corridor.origin_country == origin_country)
        if destination_country:
            query = query.filter(Corridor.destination_country == destination_country)
        
        return query.order_by(Corridor.corridor_code).all()
    
    # ==================== Benchmark Management ====================
    
    def publish_benchmark(
        self,
        corridor_id: str,
        delay_metrics: Dict[str, Any],
        risk_metrics: Dict[str, Any],
        effective_from: date,
        published_by: str,
        carrier_performance: Optional[Dict[str, Any]] = None,
        seasonal_factors: Optional[Dict[str, Any]] = None,
        cost_benchmarks: Optional[Dict[str, Any]] = None,
        data_source: Optional[str] = None,
        data_period_start: Optional[date] = None,
        data_period_end: Optional[date] = None,
        sample_size: Optional[int] = None
    ) -> CorridorBenchmark:
        """
        Publish a new benchmark version for a corridor.
        
        Marks previous current benchmark as historical.
        
        Args:
            corridor_id: Corridor ID (ULID string)
            delay_metrics: Delay metrics dictionary
            risk_metrics: Risk metrics dictionary
            effective_from: Effective start date
            published_by: User ID publishing (ULID string)
            carrier_performance: Carrier performance dictionary
            seasonal_factors: Seasonal factors dictionary
            cost_benchmarks: Cost benchmarks dictionary
            data_source: Data source identifier
            data_period_start: Data period start
            data_period_end: Data period end
            sample_size: Sample size
            
        Returns:
            Created CorridorBenchmark instance
        """
        corridor = self.get_corridor(corridor_id)
        
        # Get next version number
        max_version = self.db.query(
            func.max(CorridorBenchmark.version)
        ).filter(
            CorridorBenchmark.corridor_id == corridor_id
        ).scalar() or 0
        
        new_version = max_version + 1
        
        # Mark current benchmark as historical
        current = self.db.query(CorridorBenchmark).filter(
            CorridorBenchmark.corridor_id == corridor_id,
            CorridorBenchmark.is_current == True
        ).first()
        
        if current:
            current.is_current = False
            current.effective_to = effective_from
        
        # Create new benchmark
        benchmark = CorridorBenchmark(
            id=generate_ulid(),
            corridor_id=corridor_id,
            version=new_version,
            effective_from=effective_from,
            is_current=True,
            data_source=data_source,
            data_period_start=data_period_start,
            data_period_end=data_period_end,
            sample_size=sample_size,
            delay_metrics_json=delay_metrics,
            risk_metrics_json=risk_metrics,
            carrier_performance_json=carrier_performance,
            seasonal_factors_json=seasonal_factors,
            cost_benchmarks_json=cost_benchmarks,
            created_by_user_id=published_by,
            created_at=datetime.utcnow()
        )
        
        # Compute benchmark hash
        benchmark.benchmark_hash = self._compute_benchmark_hash(benchmark)
        
        self.db.add(benchmark)
        self.db.commit()
        self.db.refresh(benchmark)
        
        # Audit
        self.audit.append_event(
            tenant_id=None,
            event_type="CORRIDOR_BENCHMARK",
            action="PUBLISHED",
            entity_type="corridor_benchmark",
            entity_id=benchmark.id,
            actor_type="USER",
            actor_id=published_by,
            payload={
                "corridor_id": corridor_id,
                "corridor_code": corridor.corridor_code,
                "version": new_version,
                "benchmark_hash": benchmark.benchmark_hash
            }
        )
        
        logger.info(f"Published benchmark v{new_version} for corridor {corridor_id}")
        
        return benchmark
    
    def get_current_benchmark(self, corridor_id: str) -> Optional[CorridorBenchmark]:
        """
        Get the current active benchmark for a corridor.
        
        Args:
            corridor_id: Corridor ID (ULID string)
            
        Returns:
            Current CorridorBenchmark or None
        """
        return self.db.query(CorridorBenchmark).filter(
            CorridorBenchmark.corridor_id == corridor_id,
            CorridorBenchmark.is_current == True
        ).first()
    
    def get_benchmark_as_of(
        self,
        corridor_id: str,
        as_of_date: date
    ) -> Optional[CorridorBenchmark]:
        """
        Get benchmark that was effective on a given date.
        
        Args:
            corridor_id: Corridor ID (ULID string)
            as_of_date: Target date
            
        Returns:
            CorridorBenchmark effective for date or None
        """
        return self.db.query(CorridorBenchmark).filter(
            CorridorBenchmark.corridor_id == corridor_id,
            CorridorBenchmark.effective_from <= as_of_date,
            or_(
                CorridorBenchmark.effective_to.is_(None),
                CorridorBenchmark.effective_to > as_of_date
            )
        ).order_by(CorridorBenchmark.effective_from.desc()).first()
    
    def get_benchmark_history(
        self,
        corridor_id: str,
        limit: int = 10
    ) -> List[CorridorBenchmark]:
        """
        Get benchmark version history for a corridor.
        
        Args:
            corridor_id: Corridor ID (ULID string)
            limit: Maximum number of versions to return
            
        Returns:
            List of CorridorBenchmark instances (ordered by version desc)
        """
        return self.db.query(CorridorBenchmark).filter(
            CorridorBenchmark.corridor_id == corridor_id
        ).order_by(
            CorridorBenchmark.version.desc()
        ).limit(limit).all()
    
    def compare_benchmarks(
        self,
        benchmark_id_1: str,
        benchmark_id_2: str
    ) -> Dict[str, Any]:
        """
        Compare two benchmark versions.
        
        Args:
            benchmark_id_1: First benchmark ID (ULID string)
            benchmark_id_2: Second benchmark ID (ULID string)
            
        Returns:
            Dictionary with comparison results
            
        Raises:
            BenchmarkNotFoundError: If one or both benchmarks not found
        """
        b1 = self.db.query(CorridorBenchmark).filter(
            CorridorBenchmark.id == benchmark_id_1
        ).first()
        b2 = self.db.query(CorridorBenchmark).filter(
            CorridorBenchmark.id == benchmark_id_2
        ).first()
        
        if not b1 or not b2:
            raise BenchmarkNotFoundError("One or both benchmarks not found")
        
        def compare_metrics(m1: Optional[Dict], m2: Optional[Dict]) -> Dict:
            """Compare two metric dictionaries."""
            if not m1 or not m2:
                return {"error": "Missing data"}
            
            changes = {}
            all_keys = set(m1.keys()) | set(m2.keys())
            for key in all_keys:
                v1 = m1.get(key)
                v2 = m2.get(key)
                if v1 != v2:
                    if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
                        change_pct = ((v2 - v1) / v1 * 100) if v1 != 0 else None
                        changes[key] = {
                            "old": v1,
                            "new": v2,
                            "change_pct": round(change_pct, 2) if change_pct else None,
                            "change_abs": round(v2 - v1, 4)
                        }
                    else:
                        changes[key] = {"old": v1, "new": v2}
            return changes
        
        return {
            "benchmark_1": {
                "id": b1.id,
                "version": b1.version,
                "effective_from": b1.effective_from.isoformat(),
                "is_current": b1.is_current
            },
            "benchmark_2": {
                "id": b2.id,
                "version": b2.version,
                "effective_from": b2.effective_from.isoformat(),
                "is_current": b2.is_current
            },
            "delay_metrics_changes": compare_metrics(
                b1.delay_metrics_json, b2.delay_metrics_json
            ),
            "risk_metrics_changes": compare_metrics(
                b1.risk_metrics_json, b2.risk_metrics_json
            ),
            "cost_changes": compare_metrics(
                b1.cost_benchmarks_json, b2.cost_benchmarks_json
            )
        }
    
    # ==================== Port Intelligence ====================
    
    def update_port_conditions(
        self,
        port_code: str,
        conditions: Dict[str, Any],
        updated_by: Optional[str] = None
    ) -> PortIntelligence:
        """
        Update current conditions for a port.
        
        Args:
            port_code: Port code
            conditions: Conditions dictionary
            updated_by: Optional user ID (ULID string)
            
        Returns:
            Updated PortIntelligence instance
            
        Raises:
            PortNotFoundError: If port not found
        """
        port = self.db.query(PortIntelligence).filter(
            PortIntelligence.port_code == port_code
        ).first()
        
        if not port:
            raise PortNotFoundError(f"Port {port_code} not found")
        
        # Add timestamp
        conditions['last_updated'] = datetime.utcnow().isoformat()
        
        port.current_conditions_json = conditions
        port.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(port)
        
        # Audit
        if updated_by:
            self.audit.append_event(
                tenant_id=None,
                event_type="PORT_INTELLIGENCE",
                action="UPDATED",
                entity_type="port_intelligence",
                entity_id=port.id,
                actor_type="USER",
                actor_id=updated_by,
                payload={
                    "port_code": port_code,
                    "conditions_keys": list(conditions.keys())
                }
            )
        
        logger.info(f"Updated port conditions: {port_code}")
        
        return port
    
    def get_port_intelligence(self, port_code: str) -> PortIntelligence:
        """
        Get port intelligence by code.
        
        Args:
            port_code: Port code
            
        Returns:
            PortIntelligence instance
            
        Raises:
            PortNotFoundError: If port not found
        """
        port = self.db.query(PortIntelligence).filter(
            PortIntelligence.port_code == port_code
        ).first()
        if not port:
            raise PortNotFoundError(f"Port {port_code} not found")
        return port
    
    # ==================== Carrier Profiles ====================
    
    def get_carrier_profile(self, carrier_code: str) -> CarrierProfile:
        """
        Get carrier profile by code.
        
        Args:
            carrier_code: Carrier code
            
        Returns:
            CarrierProfile instance
            
        Raises:
            CarrierNotFoundError: If carrier not found
        """
        carrier = self.db.query(CarrierProfile).filter(
            CarrierProfile.carrier_code == carrier_code
        ).first()
        if not carrier:
            raise CarrierNotFoundError(f"Carrier {carrier_code} not found")
        return carrier
    
    def get_carrier_corridor_performance(
        self,
        carrier_code: str,
        corridor_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get carrier performance on specific corridor.
        
        Args:
            carrier_code: Carrier code
            corridor_id: Corridor ID (ULID string)
            
        Returns:
            Carrier performance dictionary or None
        """
        benchmark = self.get_current_benchmark(corridor_id)
        if not benchmark or not benchmark.carrier_performance_json:
            return None
        
        return benchmark.carrier_performance_json.get(carrier_code)
    
    # ==================== Risk Engine Integration ====================
    
    def get_corridor_risk_inputs(
        self,
        corridor_id: str,
        carrier_code: Optional[str] = None,
        as_of_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Get corridor data formatted for risk engine input.
        
        This is the integration point with the risk assessment engine.
        
        Args:
            corridor_id: Corridor ID (ULID string)
            carrier_code: Optional carrier code for carrier-specific performance
            as_of_date: Optional date to get historical benchmark (default: current)
            
        Returns:
            Dictionary with formatted risk inputs
            
        Raises:
            CorridorNotFoundError: If corridor not found
            NoBenchmarkError: If no benchmark available
        """
        corridor = self.get_corridor(corridor_id)
        
        if as_of_date:
            benchmark = self.get_benchmark_as_of(corridor_id, as_of_date)
        else:
            benchmark = self.get_current_benchmark(corridor_id)
        
        if not benchmark:
            raise NoBenchmarkError(f"No benchmark available for corridor {corridor_id}")
        
        # Get port conditions
        origin_port = self.db.query(PortIntelligence).filter(
            PortIntelligence.port_code == corridor.origin_port_code
        ).first()
        
        dest_port = self.db.query(PortIntelligence).filter(
            PortIntelligence.port_code == corridor.destination_port_code
        ).first()
        
        # Build risk input
        risk_inputs = {
            "corridor": {
                "corridor_id": corridor.id,
                "corridor_code": corridor.corridor_code,
                "origin_port": corridor.origin_port_code,
                "destination_port": corridor.destination_port_code,
                "distance_nm": corridor.distance_nm,
                "typical_transit_days": corridor.typical_transit_days,
                "trade_lane": corridor.trade_lane,
                "route_type": corridor.route_type
            },
            "benchmark": {
                "version": benchmark.version,
                "effective_from": benchmark.effective_from.isoformat(),
                "benchmark_hash": benchmark.benchmark_hash,
                "delay_metrics": benchmark.delay_metrics_json or {},
                "risk_metrics": benchmark.risk_metrics_json or {}
            },
            "origin_port_conditions": origin_port.current_conditions_json if origin_port else None,
            "destination_port_conditions": dest_port.current_conditions_json if dest_port else None,
            "seasonal_factors": benchmark.seasonal_factors_json or {}
        }
        
        # Add carrier-specific performance if provided
        if carrier_code and benchmark.carrier_performance_json:
            carrier_perf = benchmark.carrier_performance_json.get(carrier_code)
            if carrier_perf:
                risk_inputs["carrier_performance"] = carrier_perf
        
        return risk_inputs
    
    # ==================== Private Methods ====================
    
    def _compute_benchmark_hash(self, benchmark: CorridorBenchmark) -> str:
        """
        Compute hash of benchmark data.
        
        Args:
            benchmark: CorridorBenchmark instance
            
        Returns:
            SHA256 hash string
        """
        hashable = {
            "corridor_id": benchmark.corridor_id,
            "delay_metrics": benchmark.delay_metrics_json,
            "risk_metrics": benchmark.risk_metrics_json,
            "carrier_performance": benchmark.carrier_performance_json,
            "seasonal_factors": benchmark.seasonal_factors_json,
            "cost_benchmarks": benchmark.cost_benchmarks_json
        }
        canonical = json.dumps(hashable, sort_keys=True, separators=(',', ':'), default=str)
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


class NoBenchmarkError(Exception):
    """No benchmark available"""
    pass


class PortNotFoundError(Exception):
    """Port not found"""
    pass


class CarrierNotFoundError(Exception):
    """Carrier not found"""
    pass
