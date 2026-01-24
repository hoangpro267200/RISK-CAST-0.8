"""Create audit ledger models

Revision ID: 002_audit_ledger
Revises: 001_tenancy
Create Date: 2024-12-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '002_audit_ledger'
down_revision = '001_tenancy'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create audit_events table
    op.create_table(
        'audit_events',
        sa.Column('id', sa.String(length=26), nullable=False),
        sa.Column('tenant_id', sa.String(length=26), nullable=True),
        sa.Column('occurred_at', sa.DateTime(), nullable=False),
        sa.Column('actor_type', sa.Enum('USER', 'API_KEY', 'SYSTEM', name='actortype', native_enum=False), nullable=False),
        sa.Column('actor_id', sa.String(length=100), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=100), nullable=False),
        sa.Column('resource_id', sa.String(length=100), nullable=False),
        sa.Column('context_json', sa.JSON(), nullable=True),
        sa.Column('diff_json', sa.JSON(), nullable=True),
        sa.Column('prev_hash', sa.CHAR(length=64), nullable=True),
        sa.Column('event_hash', sa.CHAR(length=64), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_audit_events_tenant_id'), 'audit_events', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_audit_events_occurred_at'), 'audit_events', ['occurred_at'], unique=False)
    op.create_index(op.f('ix_audit_events_actor_type'), 'audit_events', ['actor_type'], unique=False)
    op.create_index(op.f('ix_audit_events_actor_id'), 'audit_events', ['actor_id'], unique=False)
    op.create_index(op.f('ix_audit_events_action'), 'audit_events', ['action'], unique=False)
    op.create_index(op.f('ix_audit_events_resource_type'), 'audit_events', ['resource_type'], unique=False)
    op.create_index(op.f('ix_audit_events_resource_id'), 'audit_events', ['resource_id'], unique=False)
    op.create_index(op.f('ix_audit_events_prev_hash'), 'audit_events', ['prev_hash'], unique=False)
    op.create_index(op.f('ix_audit_events_event_hash'), 'audit_events', ['event_hash'], unique=False)
    
    # Create composite indexes
    op.create_index('idx_audit_tenant_occurred', 'audit_events', ['tenant_id', 'occurred_at'], unique=False)
    op.create_index('idx_audit_tenant_resource', 'audit_events', ['tenant_id', 'resource_type', 'resource_id'], unique=False)
    op.create_index('idx_audit_tenant_action', 'audit_events', ['tenant_id', 'action', 'occurred_at'], unique=False)
    op.create_index('idx_audit_actor', 'audit_events', ['actor_type', 'actor_id', 'occurred_at'], unique=False)
    
    # Create audit_chain_heads table
    op.create_table(
        'audit_chain_heads',
        sa.Column('tenant_id', sa.String(length=26), nullable=True),
        sa.Column('last_event_hash', sa.CHAR(length=64), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('tenant_id')
    )


def downgrade() -> None:
    # Drop audit_chain_heads table
    op.drop_table('audit_chain_heads')
    
    # Drop indexes
    op.drop_index('idx_audit_actor', table_name='audit_events')
    op.drop_index('idx_audit_tenant_action', table_name='audit_events')
    op.drop_index('idx_audit_tenant_resource', table_name='audit_events')
    op.drop_index('idx_audit_tenant_occurred', table_name='audit_events')
    op.drop_index(op.f('ix_audit_events_event_hash'), table_name='audit_events')
    op.drop_index(op.f('ix_audit_events_prev_hash'), table_name='audit_events')
    op.drop_index(op.f('ix_audit_events_resource_id'), table_name='audit_events')
    op.drop_index(op.f('ix_audit_events_resource_type'), table_name='audit_events')
    op.drop_index(op.f('ix_audit_events_action'), table_name='audit_events')
    op.drop_index(op.f('ix_audit_events_actor_id'), table_name='audit_events')
    op.drop_index(op.f('ix_audit_events_actor_type'), table_name='audit_events')
    op.drop_index(op.f('ix_audit_events_occurred_at'), table_name='audit_events')
    op.drop_index(op.f('ix_audit_events_tenant_id'), table_name='audit_events')
    
    # Drop audit_events table
    op.drop_table('audit_events')
    
    # Drop enum type
    op.execute("DROP TYPE IF EXISTS actortype")
