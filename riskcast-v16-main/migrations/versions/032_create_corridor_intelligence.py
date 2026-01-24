"""Create corridor intelligence tables.

Revision ID: 032_create_corridor_intelligence
Revises: 031_create_calibration
Create Date: 2026-01-23

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '032_create_corridor_intelligence'
down_revision = '031_create_calibration'
branch_labels = None
depends_on = None


def upgrade():
    # Corridors - static definition
    op.create_table(
        'corridors',
        sa.Column('id', sa.String(length=26), primary_key=True),
        
        # Identification
        sa.Column('corridor_code', sa.String(length=50), nullable=False, unique=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        
        # Route definition
        sa.Column('origin_port_code', sa.String(length=10), nullable=False),
        sa.Column('origin_port_name', sa.String(length=255), nullable=True),
        sa.Column('origin_country', sa.String(length=3), nullable=True),
        sa.Column('origin_coordinates', sa.JSON(), nullable=True),  # {"lat": ..., "lng": ...}
        
        sa.Column('destination_port_code', sa.String(length=10), nullable=False),
        sa.Column('destination_port_name', sa.String(length=255), nullable=True),
        sa.Column('destination_country', sa.String(length=3), nullable=True),
        sa.Column('destination_coordinates', sa.JSON(), nullable=True),
        
        # Route characteristics
        sa.Column('distance_nm', sa.Integer(), nullable=True),  # Nautical miles
        sa.Column('typical_transit_days', sa.Integer(), nullable=True),
        sa.Column('route_type', sa.String(length=50), nullable=True),  # DIRECT, TRANSSHIPMENT, MULTIMODAL
        sa.Column('transshipment_ports', sa.JSON(), nullable=True),  # List of intermediate ports
        
        # Classification
        sa.Column('trade_lane', sa.String(length=100), nullable=True),  # e.g., "Asia-Europe", "Transpacific"
        sa.Column('region', sa.String(length=100), nullable=True),
        sa.Column('cargo_types', sa.JSON(), nullable=True),  # Typical cargo types on this route
        
        # Status
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        # ACTIVE, INACTIVE, SEASONAL
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
    )
    
    # Corridor benchmarks - versioned snapshots
    op.create_table(
        'corridor_benchmarks',
        sa.Column('id', sa.String(length=26), primary_key=True),
        sa.Column('corridor_id', sa.String(length=26), nullable=False),
        
        # Versioning
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('effective_from', sa.Date(), nullable=False),
        sa.Column('effective_to', sa.Date(), nullable=True),  # NULL = current
        sa.Column('is_current', sa.Boolean(), nullable=False, server_default='0'),
        
        # Data source
        sa.Column('data_source', sa.String(length=100), nullable=True),  # INTERNAL, MARKET_DATA, CARRIER_FEED
        sa.Column('data_period_start', sa.Date(), nullable=True),
        sa.Column('data_period_end', sa.Date(), nullable=True),
        sa.Column('sample_size', sa.Integer(), nullable=True),  # Number of shipments in sample
        
        # Delay metrics
        sa.Column('delay_metrics_json', sa.JSON(), nullable=True),
        # {
        #   "on_time_rate": 0.72,
        #   "avg_delay_days": 2.5,
        #   "delay_std_days": 3.1,
        #   "p50_delay_days": 1,
        #   "p90_delay_days": 5,
        #   "p99_delay_days": 12
        # }
        
        # Risk metrics
        sa.Column('risk_metrics_json', sa.JSON(), nullable=True),
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
        sa.Column('carrier_performance_json', sa.JSON(), nullable=True),
        # {
        #   "MAERSK": {"on_time_rate": 0.78, "reliability_score": 0.82},
        #   "MSC": {"on_time_rate": 0.71, "reliability_score": 0.75},
        #   ...
        # }
        
        # Seasonal factors
        sa.Column('seasonal_factors_json', sa.JSON(), nullable=True),
        # {
        #   "Q1": {"delay_multiplier": 1.2, "risk_multiplier": 1.1},
        #   "Q2": {"delay_multiplier": 1.0, "risk_multiplier": 1.0},
        #   ...
        # }
        
        # Cost benchmarks
        sa.Column('cost_benchmarks_json', sa.JSON(), nullable=True),
        # {
        #   "avg_freight_rate_per_teu": 2500,
        #   "currency": "USD",
        #   "insurance_rate_per_mille": 4.5
        # }
        
        # Integrity
        sa.Column('benchmark_hash', sa.String(length=64), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by_user_id', sa.String(length=26), nullable=True),
        
        # Foreign keys
        sa.ForeignKeyConstraint(['corridor_id'], ['corridors.id'], name='fk_benchmark_corridor', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], name='fk_benchmark_created_by', ondelete='SET NULL'),
        
        # Unique version per corridor
        sa.UniqueConstraint('corridor_id', 'version', name='uq_corridor_benchmark_version')
    )
    
    # Port intelligence
    op.create_table(
        'port_intelligence',
        sa.Column('id', sa.String(length=26), primary_key=True),
        
        # Port identification
        sa.Column('port_code', sa.String(length=10), nullable=False, unique=True),
        sa.Column('port_name', sa.String(length=255), nullable=False),
        sa.Column('country', sa.String(length=3), nullable=False),
        sa.Column('region', sa.String(length=100), nullable=True),
        sa.Column('coordinates', sa.JSON(), nullable=True),
        
        # Port characteristics
        sa.Column('port_type', sa.String(length=50), nullable=True),  # CONTAINER, BULK, MIXED
        sa.Column('size_class', sa.String(length=20), nullable=True),  # MEGA, LARGE, MEDIUM, SMALL
        sa.Column('annual_teu_capacity', sa.BigInteger(), nullable=True),
        
        # Current conditions (updated frequently)
        sa.Column('current_conditions_json', sa.JSON(), nullable=True),
        # {
        #   "congestion_level": "HIGH",
        #   "avg_wait_days": 5,
        #   "berth_utilization": 0.92,
        #   "last_updated": "2024-01-15T10:00:00Z"
        # }
        
        # Risk factors
        sa.Column('risk_factors_json', sa.JSON(), nullable=True),
        # {
        #   "weather_exposure": "TYPHOON",
        #   "labor_risk": "MEDIUM",
        #   "infrastructure_quality": "HIGH",
        #   "security_rating": "A"
        # }
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    )
    
    # Carrier profiles
    op.create_table(
        'carrier_profiles',
        sa.Column('id', sa.String(length=26), primary_key=True),
        
        # Carrier identification
        sa.Column('carrier_code', sa.String(length=20), nullable=False, unique=True),
        sa.Column('carrier_name', sa.String(length=255), nullable=False),
        sa.Column('carrier_type', sa.String(length=50), nullable=True),  # OCEAN, AIR, TRUCKING, RAIL
        
        # Global metrics
        sa.Column('global_metrics_json', sa.JSON(), nullable=True),
        # {
        #   "fleet_size": 450,
        #   "market_share_pct": 17.5,
        #   "financial_rating": "A+",
        #   "reliability_score": 0.78,
        #   "claims_frequency": 0.025
        # }
        
        # Service quality
        sa.Column('service_quality_json', sa.JSON(), nullable=True),
        # {
        #   "schedule_reliability": 0.72,
        #   "documentation_quality": 0.85,
        #   "customer_service_score": 3.8,
        #   "digital_capabilities": "HIGH"
        # }
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    )
    
    # Indexes
    op.create_index('idx_corridors_ports', 'corridors', ['origin_port_code', 'destination_port_code'])
    op.create_index('idx_corridors_trade_lane', 'corridors', ['trade_lane'])
    op.create_index('idx_corridors_status', 'corridors', ['status'])
    op.create_index('idx_benchmarks_corridor', 'corridor_benchmarks', ['corridor_id'])
    op.create_index('idx_benchmarks_current', 'corridor_benchmarks', ['corridor_id', 'is_current'])
    op.create_index('idx_benchmarks_effective', 'corridor_benchmarks', ['effective_from', 'effective_to'])
    op.create_index('idx_port_code', 'port_intelligence', ['port_code'])
    op.create_index('idx_port_country', 'port_intelligence', ['country'])
    op.create_index('idx_carrier_code', 'carrier_profiles', ['carrier_code'])


def downgrade():
    op.drop_table('carrier_profiles')
    op.drop_table('port_intelligence')
    op.drop_table('corridor_benchmarks')
    op.drop_table('corridors')
