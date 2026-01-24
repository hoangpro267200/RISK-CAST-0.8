"""
Corridor and market intelligence models.

Models for corridors, versioned benchmarks, ports, and carriers.
"""

from datetime import date, datetime
from typing import Optional
import sqlalchemy as sa
from sqlalchemy import Column, String, Integer, BigInteger, Boolean, DateTime, Date, Text, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.database import Base


class Corridor(Base):
    """
    Corridor model.
    
    Represents a shipping route (e.g., Shanghai → Rotterdam).
    Static information about the route.
    """
    __tablename__ = 'corridors'
    
    # Primary key
    id = Column(String(length=26), primary_key=True)
    
    # Identification
    corridor_code = Column(String(length=50), nullable=False, unique=True, index=True)
    name = Column(String(length=255), nullable=False)
    description = Column(Text(), nullable=True)
    
    # Route definition
    origin_port_code = Column(String(length=10), nullable=False, index=True)
    origin_port_name = Column(String(length=255), nullable=True)
    origin_country = Column(String(length=3), nullable=True)
    origin_coordinates = Column(sa.JSON(), nullable=True)  # {"lat": ..., "lng": ...}
    
    destination_port_code = Column(String(length=10), nullable=False, index=True)
    destination_port_name = Column(String(length=255), nullable=True)
    destination_country = Column(String(length=3), nullable=True)
    destination_coordinates = Column(sa.JSON(), nullable=True)
    
    # Route characteristics
    distance_nm = Column(Integer(), nullable=True)  # Nautical miles
    typical_transit_days = Column(Integer(), nullable=True)
    route_type = Column(String(length=50), nullable=True)  # DIRECT, TRANSSHIPMENT, MULTIMODAL
    transshipment_ports = Column(sa.JSON(), nullable=True)  # List of intermediate ports
    
    # Classification
    trade_lane = Column(String(length=100), nullable=True, index=True)  # e.g., "Asia-Europe", "Transpacific"
    region = Column(String(length=100), nullable=True)
    cargo_types = Column(sa.JSON(), nullable=True)  # Typical cargo types on this route
    
    # Status
    status = Column(String(length=20), nullable=False, server_default='ACTIVE', index=True)
    # ACTIVE, INACTIVE, SEASONAL
    
    # Timestamps
    created_at = Column(DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    updated_at = Column(DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    
    # Relationships
    benchmarks = relationship(
        'CorridorBenchmark',
        back_populates='corridor',
        order_by='desc(CorridorBenchmark.version)',
        lazy='select'
    )
    
    def __repr__(self):
        return f"<Corridor(id={self.id}, code={self.corridor_code}, {self.origin_port_code}→{self.destination_port_code})>"


class CorridorBenchmark(Base):
    """
    Corridor benchmark model.
    
    Versioned snapshots of corridor performance metrics.
    Each version has effective dates and can be marked as current.
    """
    __tablename__ = 'corridor_benchmarks'
    
    # Primary key
    id = Column(String(length=26), primary_key=True)
    
    # Foreign key
    corridor_id = Column(String(length=26), ForeignKey('corridors.id'), nullable=False, index=True)
    
    # Versioning
    version = Column(Integer(), nullable=False)
    effective_from = Column(Date(), nullable=False, index=True)
    effective_to = Column(Date(), nullable=True)
    is_current = Column(Boolean(), nullable=False, server_default='0', index=True)
    
    # Data source
    data_source = Column(String(length=100), nullable=True)  # INTERNAL, MARKET_DATA, CARRIER_FEED
    data_period_start = Column(Date(), nullable=True)
    data_period_end = Column(Date(), nullable=True)
    sample_size = Column(Integer(), nullable=True)  # Number of shipments in sample
    
    # Delay metrics
    delay_metrics_json = Column(sa.JSON(), nullable=True)
    # {
    #   "on_time_rate": 0.72,
    #   "avg_delay_days": 2.5,
    #   "delay_std_days": 3.1,
    #   "p50_delay_days": 1,
    #   "p90_delay_days": 5,
    #   "p99_delay_days": 12
    # }
    
    # Risk metrics
    risk_metrics_json = Column(sa.JSON(), nullable=True)
    # {
    #   "corridor_risk_score": 0.45,
    #   "loss_rate_historical": 0.012,
    #   "claim_frequency": 0.03,
    #   "avg_claim_severity_pct": 0.15,
    #   "piracy_risk": "LOW",
    #   "weather_risk": "MEDIUM",
    #   "port_congestion_risk": "HIGH"
    # }
    
    # Carrier performance on this corridor
    carrier_performance_json = Column(sa.JSON(), nullable=True)
    # {
    #   "MAERSK": {"on_time_rate": 0.78, "reliability_score": 0.82},
    #   "MSC": {"on_time_rate": 0.71, "reliability_score": 0.75},
    #   ...
    # }
    
    # Seasonal factors
    seasonal_factors_json = Column(sa.JSON(), nullable=True)
    # {
    #   "Q1": {"delay_multiplier": 1.2, "risk_multiplier": 1.1},
    #   "Q2": {"delay_multiplier": 1.0, "risk_multiplier": 1.0},
    #   ...
    # }
    
    # Cost benchmarks
    cost_benchmarks_json = Column(sa.JSON(), nullable=True)
    # {
    #   "avg_freight_rate_per_teu": 2500,
    #   "currency": "USD",
    #   "insurance_rate_per_mille": 4.5
    # }
    
    # Integrity
    benchmark_hash = Column(String(length=64), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    created_by_user_id = Column(String(length=26), ForeignKey('users.id'), nullable=True)
    
    # Relationships
    corridor = relationship('Corridor', foreign_keys=[corridor_id], back_populates='benchmarks', lazy='select')
    created_by_user = relationship('User', foreign_keys=[created_by_user_id], lazy='select')
    
    __table_args__ = (
        Index('idx_benchmark_version', 'corridor_id', 'version'),
        sa.UniqueConstraint('corridor_id', 'version', name='uq_corridor_benchmark_version')
    )
    
    def __repr__(self):
        return f"<CorridorBenchmark(id={self.id}, corridor_id={self.corridor_id}, version={self.version}, is_current={self.is_current})>"


class PortIntelligence(Base):
    """
    Port intelligence model.
    
    Stores information about ports including current conditions
    and risk factors.
    """
    __tablename__ = 'port_intelligence'
    
    # Primary key
    id = Column(String(length=26), primary_key=True)
    
    # Port identification
    port_code = Column(String(length=10), nullable=False, unique=True, index=True)
    port_name = Column(String(length=255), nullable=False)
    country = Column(String(length=3), nullable=False, index=True)
    region = Column(String(length=100), nullable=True)
    coordinates = Column(sa.JSON(), nullable=True)
    
    # Port characteristics
    port_type = Column(String(length=50), nullable=True)  # CONTAINER, BULK, MIXED
    size_class = Column(String(length=20), nullable=True)  # MEGA, LARGE, MEDIUM, SMALL
    annual_teu_capacity = Column(BigInteger(), nullable=True)
    
    # Current conditions (updated frequently)
    current_conditions_json = Column(sa.JSON(), nullable=True)
    # {
    #   "congestion_level": "HIGH",
    #   "avg_wait_days": 5,
    #   "berth_utilization": 0.92,
    #   "last_updated": "2024-01-15T10:00:00Z"
    # }
    
    # Risk factors
    risk_factors_json = Column(sa.JSON(), nullable=True)
    # {
    #   "weather_exposure": "TYPHOON",
    #   "labor_risk": "MEDIUM",
    #   "infrastructure_quality": "HIGH",
    #   "security_rating": "A"
    # }
    
    # Timestamps
    created_at = Column(DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    updated_at = Column(DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    
    def __repr__(self):
        return f"<PortIntelligence(id={self.id}, port_code={self.port_code}, name={self.port_name})>"


class CarrierProfile(Base):
    """
    Carrier profile model.
    
    Stores information about carriers including global metrics
    and service quality.
    """
    __tablename__ = 'carrier_profiles'
    
    # Primary key
    id = Column(String(length=26), primary_key=True)
    
    # Carrier identification
    carrier_code = Column(String(length=20), nullable=False, unique=True, index=True)
    carrier_name = Column(String(length=255), nullable=False)
    carrier_type = Column(String(length=50), nullable=True)  # OCEAN, AIR, TRUCKING, RAIL
    
    # Global metrics
    global_metrics_json = Column(sa.JSON(), nullable=True)
    # {
    #   "fleet_size": 450,
    #   "market_share_pct": 17.5,
    #   "financial_rating": "A+",
    #   "reliability_score": 0.78,
    #   "claims_frequency": 0.025
    # }
    
    # Service quality
    service_quality_json = Column(sa.JSON(), nullable=True)
    # {
    #   "schedule_reliability": 0.72,
    #   "documentation_quality": 0.85,
    #   "customer_service_score": 3.8,
    #   "digital_capabilities": "HIGH"
    # }
    
    # Timestamps
    created_at = Column(DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    updated_at = Column(DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    
    def __repr__(self):
        return f"<CarrierProfile(id={self.id}, carrier_code={self.carrier_code}, name={self.carrier_name})>"
