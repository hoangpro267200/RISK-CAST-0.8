"""Create oracle events and parametric tables

Revision ID: 027_create_oracle_events
Revises: 026_enhance_payouts
Create Date: 2025-01-23

Creates oracle_events table for immutable storage of external oracle data
and oracle_event_correlations table for multi-source corroboration.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '027_create_oracle_events'
down_revision = '026_enhance_payouts'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if oracle_events table exists
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    
    table_exists = 'oracle_events' in inspector.get_table_names()
    
    if not table_exists:
        # Create oracle_events table if it doesn't exist
        op.create_table(
            'oracle_events',
            sa.Column('id', sa.String(length=26), nullable=False),  # ULID
            sa.Column('tenant_id', sa.String(length=26), nullable=True),  # NULL for global feeds
            sa.Column('source', sa.String(length=100), nullable=False),
            sa.Column('captured_at', sa.DateTime(), nullable=False),
            sa.Column('payload_json', sa.JSON(), nullable=False),
            sa.Column('payload_hash', sa.String(length=64), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
    
    # Enhance oracle_events table with additional fields
    if table_exists:
        existing_columns = [col['name'] for col in inspector.get_columns('oracle_events')]
    else:
        existing_columns = []
    
    # Add new columns if they don't exist
    if 'source_event_id' not in existing_columns:
        op.add_column('oracle_events', sa.Column('source_event_id', sa.String(length=255), nullable=True))
    
    if 'scope_type' not in existing_columns:
        op.add_column('oracle_events', sa.Column('scope_type', sa.String(length=50), nullable=True))
    
    if 'scope_id' not in existing_columns:
        op.add_column('oracle_events', sa.Column('scope_id', sa.String(length=255), nullable=True))
    
    if 'event_type' not in existing_columns:
        op.add_column('oracle_events', sa.Column('event_type', sa.String(length=100), nullable=True))
    
    if 'event_time' not in existing_columns:
        op.add_column('oracle_events', sa.Column('event_time', sa.DateTime(), nullable=True))
    
    if 'raw_response_hash' not in existing_columns:
        op.add_column('oracle_events', sa.Column('raw_response_hash', sa.String(length=64), nullable=True))
    
    if 'confidence_score' not in existing_columns:
        op.add_column('oracle_events', sa.Column('confidence_score', sa.Float(), nullable=True))
    
    if 'data_quality_json' not in existing_columns:
        op.add_column('oracle_events', sa.Column('data_quality_json', sa.JSON(), nullable=True))
    
    if 'ingested_at' not in existing_columns:
        op.add_column('oracle_events', sa.Column('ingested_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')))
    
    if 'ingestion_batch_id' not in existing_columns:
        op.add_column('oracle_events', sa.Column('ingestion_batch_id', sa.String(length=100), nullable=True))
    
    if 'processed' not in existing_columns:
        op.add_column('oracle_events', sa.Column('processed', sa.Boolean(), nullable=True, server_default='0'))
    
    if 'processed_at' not in existing_columns:
        op.add_column('oracle_events', sa.Column('processed_at', sa.DateTime(), nullable=True))
    
    # Create indexes
    existing_indexes = [idx['name'] for idx in inspector.get_indexes('oracle_events')] if table_exists else []
    
    if 'idx_oracle_events_type' not in existing_indexes:
        op.create_index('idx_oracle_events_type', 'oracle_events', ['event_type'], unique=False)
    
    if 'idx_oracle_events_scope' not in existing_indexes:
        op.create_index('idx_oracle_events_scope', 'oracle_events', ['scope_type', 'scope_id'], unique=False)
    
    if 'idx_oracle_events_batch' not in existing_indexes:
        op.create_index('idx_oracle_events_batch', 'oracle_events', ['ingestion_batch_id'], unique=False)
    
    if 'idx_oracle_events_processed' not in existing_indexes:
        op.create_index('idx_oracle_events_processed', 'oracle_events', ['processed'], unique=False)
    
    # Oracle event correlations (for multi-source corroboration)
    if 'oracle_event_correlations' not in inspector.get_table_names():
        op.create_table(
            'oracle_event_correlations',
        sa.Column('id', sa.String(length=26), nullable=False),  # ULID
        sa.Column('tenant_id', sa.String(length=26), nullable=True),  # NULL for global feeds
        
        # Source identification
        sa.Column('source', sa.String(length=100), nullable=False),
        # TOMORROW_IO, MARINE_TRAFFIC, ICEYE, FLOODBASE, MANUAL
        sa.Column('source_event_id', sa.String(length=255), nullable=True),  # External ID if any
        
        # Scope
        sa.Column('scope_type', sa.String(length=50), nullable=True),  # LOCATION, ROUTE, PORT, GLOBAL
        sa.Column('scope_id', sa.String(length=255), nullable=True),  # lat,lng or port_code or route_id
        
        # Event data (immutable)
        sa.Column('event_type', sa.String(length=100), nullable=False),
        # WEATHER, FLOOD, PORT_CONGESTION, VESSEL_DELAY, CYCLONE, etc.
        
        sa.Column('captured_at', sa.DateTime(), nullable=False),  # When data was captured
        sa.Column('event_time', sa.DateTime(), nullable=True),  # When event occurred (if different)
        
        sa.Column('payload_json', sa.JSON(), nullable=False),
        # {
        #   "temperature_c": 35,
        #   "rainfall_mm": 150,
        #   "wind_speed_kmh": 80,
        #   "humidity_pct": 95,
        #   ...
        # }
        
        # Integrity
        sa.Column('payload_hash', sa.String(length=64), nullable=False),
        sa.Column('raw_response_hash', sa.String(length=64), nullable=True),  # Hash of raw API response
        
        # Quality metadata
        sa.Column('confidence_score', sa.Float(), nullable=True),  # 0-1
        sa.Column('data_quality_json', sa.JSON(), nullable=True),
        # {
        #   "resolution": "hourly",
        #   "coverage": "full",
        #   "source_reliability": 0.95
        # }
        
        # Ingestion metadata
        sa.Column('ingested_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('ingestion_batch_id', sa.String(length=100), nullable=True),
        
        # Processing
        sa.Column('processed', sa.Boolean(), nullable=True, server_default='0'),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Oracle event correlations (for multi-source corroboration)
    op.create_table(
        'oracle_event_correlations',
        sa.Column('id', sa.String(length=26), nullable=False),  # ULID
        
        sa.Column('primary_event_id', sa.String(length=26), nullable=False),
        sa.Column('corroborating_event_id', sa.String(length=26), nullable=False),
        
        sa.Column('correlation_type', sa.String(length=50), nullable=True),  # CONFIRMS, CONTRADICTS, SUPPLEMENTS
        sa.Column('correlation_score', sa.Float(), nullable=True),  # 0-1
        
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        
        sa.ForeignKeyConstraint(['primary_event_id'], ['oracle_events.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['corroborating_event_id'], ['oracle_events.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Indexes
    op.create_index('idx_oracle_events_source', 'oracle_events', ['source'], unique=False)
    op.create_index('idx_oracle_events_type', 'oracle_events', ['event_type'], unique=False)
    op.create_index('idx_oracle_events_captured', 'oracle_events', ['captured_at'], unique=False)
    op.create_index('idx_oracle_events_scope', 'oracle_events', ['scope_type', 'scope_id'], unique=False)
    op.create_index('idx_oracle_events_hash', 'oracle_events', ['payload_hash'], unique=False)
    op.create_index('idx_oracle_events_tenant', 'oracle_events', ['tenant_id'], unique=False)
    op.create_index('idx_oracle_events_processed', 'oracle_events', ['processed'], unique=False)
    op.create_index('idx_oracle_events_batch', 'oracle_events', ['ingestion_batch_id'], unique=False)
    
    op.create_index('idx_correlations_primary', 'oracle_event_correlations', ['primary_event_id'], unique=False)
    op.create_index('idx_correlations_corroborating', 'oracle_event_correlations', ['corroborating_event_id'], unique=False)
    op.create_index('idx_correlations_type', 'oracle_event_correlations', ['correlation_type'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_correlations_type', table_name='oracle_event_correlations')
    op.drop_index('idx_correlations_corroborating', table_name='oracle_event_correlations')
    op.drop_index('idx_correlations_primary', table_name='oracle_event_correlations')
    
    op.drop_index('idx_oracle_events_batch', table_name='oracle_events')
    op.drop_index('idx_oracle_events_processed', table_name='oracle_events')
    op.drop_index('idx_oracle_events_tenant', table_name='oracle_events')
    op.drop_index('idx_oracle_events_hash', table_name='oracle_events')
    op.drop_index('idx_oracle_events_scope', table_name='oracle_events')
    op.drop_index('idx_oracle_events_captured', table_name='oracle_events')
    op.drop_index('idx_oracle_events_type', table_name='oracle_events')
    op.drop_index('idx_oracle_events_source', table_name='oracle_events')
    
    op.drop_table('oracle_event_correlations')
    op.drop_table('oracle_events')
