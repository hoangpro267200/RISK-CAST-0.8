"""Create hash-chained audit ledger

Revision ID: 013_hash_chained_audit
Revises: 012_risk_assessments
Create Date: 2024-12-20

Creates hash-chained audit ledger with sequence numbers for append-only event logging.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '013_hash_chained_audit'
down_revision = '012_risk_assessments'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create audit_events table (append-only)
    op.create_table(
        'audit_events',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=26), nullable=False),  # Match tenants.id (ULID)
        
        # Chain fields
        sa.Column('sequence_num', sa.BigInteger(), nullable=False),
        sa.Column('prev_hash', sa.String(length=64), nullable=True),
        sa.Column('event_hash', sa.String(length=64), nullable=False),
        
        # Event data
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=100), nullable=True),
        sa.Column('entity_id', sa.String(length=100), nullable=True),  # Can be ULID or other IDs
        sa.Column('action', sa.String(length=50), nullable=False),
        
        # Actor
        sa.Column('actor_type', sa.String(length=50), nullable=False),  # USER, SYSTEM, API_KEY
        sa.Column('actor_id', sa.String(length=255), nullable=True),
        
        # Payload
        sa.Column('payload_json', sa.JSON(), nullable=True),
        
        # Metadata
        sa.Column('created_at', sa.DateTime(), nullable=False),
        
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'sequence_num', name='uq_audit_events_tenant_sequence'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
    )
    
    # Create audit_chain_heads table (for maintaining chain integrity)
    op.create_table(
        'audit_chain_heads',
        sa.Column('tenant_id', sa.String(length=26), nullable=False, primary_key=True),  # Match tenants.id (ULID)
        sa.Column('latest_sequence_num', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('latest_hash', sa.String(length=64), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
    )
    
    # Indexes for audit_events
    op.create_index(
        'idx_audit_events_tenant_seq',
        'audit_events',
        ['tenant_id', 'sequence_num'],
        unique=False
    )
    op.create_index(
        'idx_audit_events_entity',
        'audit_events',
        ['entity_type', 'entity_id'],
        unique=False
    )
    op.create_index(
        'idx_audit_events_created',
        'audit_events',
        ['created_at'],
        unique=False
    )
    op.create_index(
        'ix_audit_events_tenant_id',
        'audit_events',
        ['tenant_id'],
        unique=False
    )
    op.create_index(
        'ix_audit_events_sequence_num',
        'audit_events',
        ['sequence_num'],
        unique=False
    )
    op.create_index(
        'ix_audit_events_event_hash',
        'audit_events',
        ['event_hash'],
        unique=False
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_audit_events_event_hash', table_name='audit_events')
    op.drop_index('ix_audit_events_sequence_num', table_name='audit_events')
    op.drop_index('ix_audit_events_tenant_id', table_name='audit_events')
    op.drop_index('idx_audit_events_created', table_name='audit_events')
    op.drop_index('idx_audit_events_entity', table_name='audit_events')
    op.drop_index('idx_audit_events_tenant_seq', table_name='audit_events')
    
    # Drop tables
    op.drop_table('audit_chain_heads')
    op.drop_table('audit_events')
