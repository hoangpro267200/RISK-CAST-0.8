"""
Historical Loss Data Repository

Collects and stores REAL shipment outcomes to calibrate model weights.
This is the FOUNDATION for moving from hardcoded to data-driven weights.
"""

from datetime import datetime, date
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
from uuid import uuid4
import hashlib
import json
import logging

from sqlalchemy import Column, String, Float, Integer, DateTime, Date, JSON, Boolean, ForeignKey, Enum as SQLEnum, Index
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import Session

from app.database import Base

logger = logging.getLogger(__name__)


class ShipmentOutcome(Enum):
    """Actual shipment outcomes for calibration."""
    DELIVERED_ON_TIME = "DELIVERED_ON_TIME"
    DELIVERED_LATE = "DELIVERED_LATE"
    PARTIAL_LOSS = "PARTIAL_LOSS"
    TOTAL_LOSS = "TOTAL_LOSS"
    DAMAGE_MINOR = "DAMAGE_MINOR"
    DAMAGE_MAJOR = "DAMAGE_MAJOR"
    THEFT = "THEFT"
    ABANDONED = "ABANDONED"
    RETURNED = "RETURNED"


class ClaimStatus(Enum):
    """Claim status for loss tracking."""
    NO_CLAIM = "NO_CLAIM"
    CLAIM_FILED = "CLAIM_FILED"
    CLAIM_APPROVED = "CLAIM_APPROVED"
    CLAIM_DENIED = "CLAIM_DENIED"
    CLAIM_PARTIAL = "CLAIM_PARTIAL"


class HistoricalShipment(Base):
    """
    Historical shipment record with actual outcomes.
    
    This table is the GOLD STANDARD for model calibration.
    """
    __tablename__ = "historical_shipments"
    
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid4()))
    
    # Source tracking
    source = Column(String(50), nullable=False)  # "INTERNAL", "PARTNER", "INDUSTRY_DB"
    source_reference = Column(String(200))
    
    # Shipment details (at time of shipment)
    shipment_date = Column(Date, nullable=False)
    origin_port = Column(String(10), nullable=False)
    destination_port = Column(String(10), nullable=False)
    carrier_code = Column(String(10))
    
    # Cargo details
    cargo_type = Column(String(50), nullable=False)
    cargo_value_usd = Column(Float, nullable=False)
    container_count = Column(Integer, default=1)
    cargo_weight_kg = Column(Float)
    packaging_quality = Column(String(20))
    
    # Route details
    distance_nm = Column(Float)
    expected_transit_days = Column(Integer)
    actual_transit_days = Column(Integer)
    transshipment_count = Column(Integer, default=0)
    
    # Conditions at time of shipment
    weather_conditions_json = Column(JSON)  # Archived weather data
    port_conditions_json = Column(JSON)     # Archived port conditions
    carrier_rating_at_time = Column(Float)
    climate_indices_json = Column(JSON)     # ENSO, etc. at time
    
    # Risk assessment (if available)
    risk_score_predicted = Column(Float)    # What our model predicted
    risk_factors_json = Column(JSON)        # Breakdown of prediction
    model_version = Column(String(50))      # Which model made prediction
    
    # ACTUAL OUTCOME - This is what we calibrate against
    outcome = Column(SQLEnum(ShipmentOutcome), nullable=False)
    outcome_date = Column(Date)
    
    # Loss details (if loss occurred)
    loss_occurred = Column(Boolean, default=False)
    loss_type = Column(String(50))
    loss_amount_usd = Column(Float)
    loss_percentage = Column(Float)  # % of cargo value
    loss_cause = Column(String(100))
    loss_description = Column(String(1000))
    
    # Delay details
    delay_occurred = Column(Boolean, default=False)
    delay_days = Column(Float)
    delay_cause = Column(String(100))
    
    # Claim details
    claim_status = Column(SQLEnum(ClaimStatus), default=ClaimStatus.NO_CLAIM)
    claim_amount_usd = Column(Float)
    claim_paid_usd = Column(Float)
    claim_date = Column(Date)
    claim_resolution_date = Column(Date)
    
    # Data quality
    data_completeness_score = Column(Float)  # 0-1, how complete is this record
    data_verified = Column(Boolean, default=False)
    verified_by = Column(String(100))
    verified_at = Column(DateTime)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    data_hash = Column(String(64))
    
    # Indexes for calibration queries
    __table_args__ = (
        Index("idx_historical_shipment_date", "shipment_date"),
        Index("idx_historical_route", "origin_port", "destination_port"),
        Index("idx_historical_cargo_type", "cargo_type"),
        Index("idx_historical_outcome", "outcome"),
        Index("idx_historical_carrier", "carrier_code"),
        Index("idx_historical_loss", "loss_occurred", "loss_percentage"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "source": self.source,
            "source_reference": self.source_reference,
            "shipment_date": self.shipment_date.isoformat() if self.shipment_date else None,
            "origin_port": self.origin_port,
            "destination_port": self.destination_port,
            "carrier_code": self.carrier_code,
            "cargo_type": self.cargo_type,
            "cargo_value_usd": self.cargo_value_usd,
            "container_count": self.container_count,
            "cargo_weight_kg": self.cargo_weight_kg,
            "packaging_quality": self.packaging_quality,
            "distance_nm": self.distance_nm,
            "expected_transit_days": self.expected_transit_days,
            "actual_transit_days": self.actual_transit_days,
            "transshipment_count": self.transshipment_count,
            "weather_conditions_json": self.weather_conditions_json,
            "port_conditions_json": self.port_conditions_json,
            "carrier_rating_at_time": self.carrier_rating_at_time,
            "climate_indices_json": self.climate_indices_json,
            "risk_score_predicted": self.risk_score_predicted,
            "risk_factors_json": self.risk_factors_json,
            "model_version": self.model_version,
            "outcome": self.outcome.value if self.outcome else None,
            "outcome_date": self.outcome_date.isoformat() if self.outcome_date else None,
            "loss_occurred": self.loss_occurred,
            "loss_type": self.loss_type,
            "loss_amount_usd": self.loss_amount_usd,
            "loss_percentage": self.loss_percentage,
            "loss_cause": self.loss_cause,
            "loss_description": self.loss_description,
            "delay_occurred": self.delay_occurred,
            "delay_days": self.delay_days,
            "delay_cause": self.delay_cause,
            "claim_status": self.claim_status.value if self.claim_status else None,
            "claim_amount_usd": self.claim_amount_usd,
            "claim_paid_usd": self.claim_paid_usd,
            "claim_date": self.claim_date.isoformat() if self.claim_date else None,
            "claim_resolution_date": self.claim_resolution_date.isoformat() if self.claim_resolution_date else None,
            "data_completeness_score": self.data_completeness_score,
            "data_verified": self.data_verified,
            "verified_by": self.verified_by,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "data_hash": self.data_hash,
        }


@dataclass
class CalibrationDataset:
    """Dataset prepared for model calibration."""
    name: str
    created_at: datetime
    
    # Dataset stats
    total_shipments: int
    date_range_start: date
    date_range_end: date
    
    # Outcome distribution
    outcome_distribution: Dict[str, int]
    loss_rate: float
    avg_loss_percentage: float
    
    # By dimension
    by_route: Dict[str, Dict[str, Any]]
    by_cargo_type: Dict[str, Dict[str, Any]]
    by_carrier: Dict[str, Dict[str, Any]]
    
    # Data for calibration
    shipments: List[Dict[str, Any]]
    
    # Quality
    avg_completeness: float
    verified_percentage: float
    
    dataset_hash: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "total_shipments": self.total_shipments,
            "date_range_start": self.date_range_start.isoformat(),
            "date_range_end": self.date_range_end.isoformat(),
            "outcome_distribution": self.outcome_distribution,
            "loss_rate": self.loss_rate,
            "avg_loss_percentage": self.avg_loss_percentage,
            "by_route": self.by_route,
            "by_cargo_type": self.by_cargo_type,
            "by_carrier": self.by_carrier,
            "shipments": self.shipments,
            "avg_completeness": self.avg_completeness,
            "verified_percentage": self.verified_percentage,
            "dataset_hash": self.dataset_hash,
        }


class HistoricalLossDataRepository:
    """
    Repository for historical loss data.
    
    This is the SOURCE OF TRUTH for model calibration.
    """
    
    def __init__(self, db: Session, audit: Optional[Any] = None):
        self.db = db
        self.audit = audit
    
    async def ingest_shipment_outcome(
        self,
        shipment_data: Dict[str, Any],
        outcome: ShipmentOutcome,
        source: str,
        source_reference: Optional[str] = None
    ) -> HistoricalShipment:
        """
        Ingest a shipment outcome for calibration.
        
        This is how we build the dataset that replaces hardcoded weights.
        """
        # Calculate data completeness
        completeness = self._calculate_completeness(shipment_data)
        
        # Determine if loss occurred
        loss_occurred = outcome in [
            ShipmentOutcome.PARTIAL_LOSS,
            ShipmentOutcome.TOTAL_LOSS,
            ShipmentOutcome.DAMAGE_MINOR,
            ShipmentOutcome.DAMAGE_MAJOR,
            ShipmentOutcome.THEFT
        ]
        
        # Calculate loss percentage
        loss_percentage = 0.0
        if loss_occurred and shipment_data.get("loss_amount_usd"):
            cargo_value = shipment_data.get("cargo_value_usd", 0)
            if cargo_value > 0:
                loss_percentage = shipment_data["loss_amount_usd"] / cargo_value
        elif outcome == ShipmentOutcome.TOTAL_LOSS:
            loss_percentage = 1.0
        
        # Determine if delay occurred
        delay_occurred = False
        delay_days = 0.0
        expected = shipment_data.get("expected_transit_days")
        actual = shipment_data.get("actual_transit_days")
        if expected and actual and actual > expected:
            delay_occurred = True
            delay_days = actual - expected
        
        # Parse dates
        shipment_date = shipment_data.get("shipment_date")
        if isinstance(shipment_date, str):
            shipment_date = date.fromisoformat(shipment_date)
        
        outcome_date = shipment_data.get("outcome_date")
        if isinstance(outcome_date, str):
            outcome_date = date.fromisoformat(outcome_date)
        
        claim_date = shipment_data.get("claim_date")
        if isinstance(claim_date, str):
            claim_date = date.fromisoformat(claim_date)
        
        claim_resolution_date = shipment_data.get("claim_resolution_date")
        if isinstance(claim_resolution_date, str):
            claim_resolution_date = date.fromisoformat(claim_resolution_date)
        
        # Create record
        shipment = HistoricalShipment(
            source=source,
            source_reference=source_reference,
            shipment_date=shipment_date,
            origin_port=shipment_data.get("origin_port"),
            destination_port=shipment_data.get("destination_port"),
            carrier_code=shipment_data.get("carrier_code"),
            cargo_type=shipment_data.get("cargo_type"),
            cargo_value_usd=shipment_data.get("cargo_value_usd"),
            container_count=shipment_data.get("container_count", 1),
            cargo_weight_kg=shipment_data.get("cargo_weight_kg"),
            packaging_quality=shipment_data.get("packaging_quality"),
            distance_nm=shipment_data.get("distance_nm"),
            expected_transit_days=expected,
            actual_transit_days=actual,
            transshipment_count=shipment_data.get("transshipment_count", 0),
            weather_conditions_json=shipment_data.get("weather_conditions"),
            port_conditions_json=shipment_data.get("port_conditions"),
            carrier_rating_at_time=shipment_data.get("carrier_rating"),
            climate_indices_json=shipment_data.get("climate_indices"),
            risk_score_predicted=shipment_data.get("risk_score_predicted"),
            risk_factors_json=shipment_data.get("risk_factors"),
            model_version=shipment_data.get("model_version"),
            outcome=outcome,
            outcome_date=outcome_date,
            loss_occurred=loss_occurred,
            loss_type=shipment_data.get("loss_type"),
            loss_amount_usd=shipment_data.get("loss_amount_usd"),
            loss_percentage=loss_percentage,
            loss_cause=shipment_data.get("loss_cause"),
            loss_description=shipment_data.get("loss_description"),
            delay_occurred=delay_occurred,
            delay_days=delay_days,
            delay_cause=shipment_data.get("delay_cause") if delay_occurred else None,
            claim_status=ClaimStatus(shipment_data.get("claim_status", "NO_CLAIM")),
            claim_amount_usd=shipment_data.get("claim_amount_usd"),
            claim_paid_usd=shipment_data.get("claim_paid_usd"),
            claim_date=claim_date,
            claim_resolution_date=claim_resolution_date,
            data_completeness_score=completeness,
        )
        
        # Compute hash
        shipment.data_hash = self._compute_hash(shipment)
        
        self.db.add(shipment)
        self.db.commit()
        self.db.refresh(shipment)
        
        # Audit
        if self.audit:
            try:
                tenant_id = getattr(self.audit, 'tenant_id', None) or "system"
                self.audit.append_event(
                    tenant_id=tenant_id,
                    event_type="CALIBRATION_DATA",
                    action="SHIPMENT_OUTCOME_INGESTED",
                    entity_type="historical_shipment",
                    entity_id=shipment.id,
                    actor_type="SYSTEM",
                    payload={
                        "source": source,
                        "outcome": outcome.value,
                        "loss_occurred": loss_occurred,
                        "loss_percentage": loss_percentage,
                        "completeness": completeness,
                        "data_hash": shipment.data_hash
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to audit shipment ingestion: {e}")
        
        return shipment
    
    async def get_calibration_dataset(
        self,
        start_date: date,
        end_date: date,
        min_completeness: float = 0.7,
        filters: Optional[Dict[str, Any]] = None
    ) -> CalibrationDataset:
        """
        Get dataset for model calibration.
        
        This dataset is used to calculate REAL weights based on REAL outcomes.
        """
        query = self.db.query(HistoricalShipment).filter(
            HistoricalShipment.shipment_date >= start_date,
            HistoricalShipment.shipment_date <= end_date,
            HistoricalShipment.data_completeness_score >= min_completeness
        )
        
        # Apply filters
        if filters:
            if filters.get("cargo_type"):
                query = query.filter(HistoricalShipment.cargo_type == filters["cargo_type"])
            if filters.get("origin_port"):
                query = query.filter(HistoricalShipment.origin_port == filters["origin_port"])
            if filters.get("destination_port"):
                query = query.filter(HistoricalShipment.destination_port == filters["destination_port"])
            if filters.get("carrier_code"):
                query = query.filter(HistoricalShipment.carrier_code == filters["carrier_code"])
        
        shipments = query.all()
        
        if not shipments:
            raise ValueError("No shipments found matching criteria")
        
        # Calculate statistics
        outcome_distribution = {}
        for s in shipments:
            outcome = s.outcome.value
            outcome_distribution[outcome] = outcome_distribution.get(outcome, 0) + 1
        
        loss_shipments = [s for s in shipments if s.loss_occurred]
        loss_rate = len(loss_shipments) / len(shipments) if shipments else 0
        avg_loss_pct = (
            sum(s.loss_percentage for s in loss_shipments) / len(loss_shipments)
            if loss_shipments else 0
        )
        
        # Group by dimensions
        by_route = self._group_by_route(shipments)
        by_cargo_type = self._group_by_cargo_type(shipments)
        by_carrier = self._group_by_carrier(shipments)
        
        # Prepare shipment data for calibration
        shipment_data = [self._shipment_to_calibration_record(s) for s in shipments]
        
        # Calculate dataset hash
        dataset_hash = self._compute_dataset_hash(shipment_data)
        
        # Quality metrics
        avg_completeness = sum(s.data_completeness_score for s in shipments) / len(shipments)
        verified_count = sum(1 for s in shipments if s.data_verified)
        verified_pct = verified_count / len(shipments) if shipments else 0
        
        dataset = CalibrationDataset(
            name=f"calibration_{start_date}_{end_date}",
            created_at=datetime.utcnow(),
            total_shipments=len(shipments),
            date_range_start=start_date,
            date_range_end=end_date,
            outcome_distribution=outcome_distribution,
            loss_rate=loss_rate,
            avg_loss_percentage=avg_loss_pct,
            by_route=by_route,
            by_cargo_type=by_cargo_type,
            by_carrier=by_carrier,
            shipments=shipment_data,
            avg_completeness=avg_completeness,
            verified_percentage=verified_pct,
            dataset_hash=dataset_hash
        )
        
        # Audit dataset creation
        if self.audit:
            try:
                tenant_id = getattr(self.audit, 'tenant_id', None) or "system"
                self.audit.append_event(
                    tenant_id=tenant_id,
                    event_type="CALIBRATION_DATA",
                    action="CALIBRATION_DATASET_CREATED",
                    entity_type="calibration_dataset",
                    entity_id=dataset_hash,
                    actor_type="SYSTEM",
                    payload={
                        "name": dataset.name,
                        "total_shipments": dataset.total_shipments,
                        "loss_rate": dataset.loss_rate,
                        "avg_completeness": dataset.avg_completeness,
                        "dataset_hash": dataset_hash
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to audit dataset creation: {e}")
        
        return dataset
    
    def _group_by_route(self, shipments: List[HistoricalShipment]) -> Dict[str, Dict[str, Any]]:
        """Group shipment outcomes by route."""
        routes = {}
        
        for s in shipments:
            route_key = f"{s.origin_port}-{s.destination_port}"
            if route_key not in routes:
                routes[route_key] = {
                    "total": 0,
                    "losses": 0,
                    "total_loss_pct": 0,
                    "delays": 0,
                    "total_delay_days": 0
                }
            
            routes[route_key]["total"] += 1
            if s.loss_occurred:
                routes[route_key]["losses"] += 1
                routes[route_key]["total_loss_pct"] += s.loss_percentage or 0
            if s.delay_occurred:
                routes[route_key]["delays"] += 1
                routes[route_key]["total_delay_days"] += s.delay_days or 0
        
        # Calculate rates
        for route_key, data in routes.items():
            total = data["total"]
            data["loss_rate"] = data["losses"] / total if total > 0 else 0
            data["avg_loss_pct"] = data["total_loss_pct"] / data["losses"] if data["losses"] > 0 else 0
            data["delay_rate"] = data["delays"] / total if total > 0 else 0
            data["avg_delay_days"] = data["total_delay_days"] / data["delays"] if data["delays"] > 0 else 0
        
        return routes
    
    def _group_by_cargo_type(self, shipments: List[HistoricalShipment]) -> Dict[str, Dict[str, Any]]:
        """Group shipment outcomes by cargo type."""
        cargo_types = {}
        
        for s in shipments:
            cargo = s.cargo_type
            if cargo not in cargo_types:
                cargo_types[cargo] = {
                    "total": 0,
                    "losses": 0,
                    "total_loss_pct": 0,
                    "loss_causes": {}
                }
            
            cargo_types[cargo]["total"] += 1
            if s.loss_occurred:
                cargo_types[cargo]["losses"] += 1
                cargo_types[cargo]["total_loss_pct"] += s.loss_percentage or 0
                
                cause = s.loss_cause or "unknown"
                cargo_types[cargo]["loss_causes"][cause] = \
                    cargo_types[cargo]["loss_causes"].get(cause, 0) + 1
        
        # Calculate rates
        for cargo, data in cargo_types.items():
            total = data["total"]
            data["loss_rate"] = data["losses"] / total if total > 0 else 0
            data["avg_loss_pct"] = data["total_loss_pct"] / data["losses"] if data["losses"] > 0 else 0
        
        return cargo_types
    
    def _group_by_carrier(self, shipments: List[HistoricalShipment]) -> Dict[str, Dict[str, Any]]:
        """Group shipment outcomes by carrier."""
        carriers = {}
        
        for s in shipments:
            if not s.carrier_code:
                continue
            
            carrier = s.carrier_code
            if carrier not in carriers:
                carriers[carrier] = {
                    "total": 0,
                    "losses": 0,
                    "total_loss_pct": 0,
                    "delays": 0,
                    "on_time": 0
                }
            
            carriers[carrier]["total"] += 1
            if s.loss_occurred:
                carriers[carrier]["losses"] += 1
                carriers[carrier]["total_loss_pct"] += s.loss_percentage or 0
            if s.delay_occurred:
                carriers[carrier]["delays"] += 1
            else:
                carriers[carrier]["on_time"] += 1
        
        # Calculate rates
        for carrier, data in carriers.items():
            total = data["total"]
            data["loss_rate"] = data["losses"] / total if total > 0 else 0
            data["avg_loss_pct"] = data["total_loss_pct"] / data["losses"] if data["losses"] > 0 else 0
            data["on_time_rate"] = data["on_time"] / total if total > 0 else 0
        
        return carriers
    
    def _shipment_to_calibration_record(self, s: HistoricalShipment) -> Dict[str, Any]:
        """Convert shipment to calibration record."""
        return {
            "id": s.id,
            "shipment_date": s.shipment_date.isoformat() if s.shipment_date else None,
            "origin_port": s.origin_port,
            "destination_port": s.destination_port,
            "carrier_code": s.carrier_code,
            "cargo_type": s.cargo_type,
            "cargo_value_usd": s.cargo_value_usd,
            "container_count": s.container_count,
            "distance_nm": s.distance_nm,
            "expected_transit_days": s.expected_transit_days,
            "actual_transit_days": s.actual_transit_days,
            "weather_conditions": s.weather_conditions_json,
            "port_conditions": s.port_conditions_json,
            "carrier_rating": s.carrier_rating_at_time,
            "climate_indices": s.climate_indices_json,
            "risk_score_predicted": s.risk_score_predicted,
            "risk_factors": s.risk_factors_json,
            "model_version": s.model_version,
            "outcome": s.outcome.value if s.outcome else None,
            "loss_occurred": s.loss_occurred,
            "loss_percentage": s.loss_percentage,
            "loss_cause": s.loss_cause,
            "delay_occurred": s.delay_occurred,
            "delay_days": s.delay_days,
            "claim_status": s.claim_status.value if s.claim_status else None,
            "claim_paid_usd": s.claim_paid_usd,
            "data_completeness": s.data_completeness_score,
            "data_hash": s.data_hash
        }
    
    def _calculate_completeness(self, data: Dict[str, Any]) -> float:
        """Calculate data completeness score."""
        required_fields = [
            "shipment_date", "origin_port", "destination_port",
            "cargo_type", "cargo_value_usd"
        ]
        
        important_fields = [
            "carrier_code", "container_count", "expected_transit_days",
            "actual_transit_days", "weather_conditions", "port_conditions"
        ]
        
        nice_to_have = [
            "cargo_weight_kg", "packaging_quality", "distance_nm",
            "carrier_rating", "climate_indices"
        ]
        
        score = 0.0
        
        # Required: 50% weight
        required_present = sum(1 for f in required_fields if data.get(f) is not None)
        score += (required_present / len(required_fields)) * 0.5
        
        # Important: 35% weight
        important_present = sum(1 for f in important_fields if data.get(f) is not None)
        score += (important_present / len(important_fields)) * 0.35
        
        # Nice to have: 15% weight
        nice_present = sum(1 for f in nice_to_have if data.get(f) is not None)
        score += (nice_present / len(nice_to_have)) * 0.15
        
        return score
    
    def _compute_hash(self, shipment: HistoricalShipment) -> str:
        """Compute hash of shipment record."""
        data = {
            "shipment_date": shipment.shipment_date.isoformat() if shipment.shipment_date else None,
            "origin_port": shipment.origin_port,
            "destination_port": shipment.destination_port,
            "cargo_type": shipment.cargo_type,
            "cargo_value_usd": shipment.cargo_value_usd,
            "outcome": shipment.outcome.value if shipment.outcome else None,
            "loss_percentage": shipment.loss_percentage,
        }
        canonical = json.dumps(data, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()
    
    def _compute_dataset_hash(self, shipment_data: List[Dict[str, Any]]) -> str:
        """Compute hash of calibration dataset."""
        hashes = [s.get("data_hash", "") for s in shipment_data]
        combined = "".join(sorted(hashes))
        return hashlib.sha256(combined.encode()).hexdigest()
