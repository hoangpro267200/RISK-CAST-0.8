"""Enhance policies table with additional fields and create policy_events

Revision ID: 024_enhance_policies
Revises: 023_create_quotes
Create Date: 2025-01-23

Adds quote_id, premium_json, risk_snapshot_json, policyholder_json, 
policy_document fields, policy_hash, cancellation fields, and policy_events table.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '024_enhance_policies'
down_revision = '023_create_quotes'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if tables exist
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # Enhance policies table
    if 'policies' in inspector.get_table_names():
        existing_columns = [col['name'] for col in inspector.get_columns('policies')]
        
        # Add quote_id
        if 'quote_id' not in existing_columns:
            op.add_column('policies', sa.Column('quote_id', sa.String(length=36), nullable=True))
        
        # Add evidence_bundle_id
        if 'evidence_bundle_id' not in existing_columns:
            op.add_column('policies', sa.Column('evidence_bundle_id', sa.String(length=36), nullable=True))
        
        # Add premium_json
        if 'premium_json' not in existing_columns:
            op.add_column('policies', sa.Column('premium_json', sa.JSON(), nullable=True))
        
        # Add risk_snapshot_json
        if 'risk_snapshot_json' not in existing_columns:
            op.add_column('policies', sa.Column('risk_snapshot_json', sa.JSON(), nullable=True))
        
        # Add policyholder_json
        if 'policyholder_json' not in existing_columns:
            op.add_column('policies', sa.Column('policyholder_json', sa.JSON(), nullable=True))
        
        # Add policyholder_pii
        if 'policyholder_pii' not in existing_columns:
            op.add_column('policies', sa.Column('policyholder_pii', sa.Boolean(), nullable=True, server_default='1'))
        
        # Add shipment_id
        if 'shipment_id' not in existing_columns:
            op.add_column('policies', sa.Column('shipment_id', sa.String(length=36), nullable=True))
        
        # Add corridor_id
        if 'corridor_id' not in existing_columns:
            op.add_column('policies', sa.Column('corridor_id', sa.String(length=100), nullable=True))
        
        # Add policy document fields
        if 'policy_document_evidence_id' not in existing_columns:
            op.add_column('policies', sa.Column('policy_document_evidence_id', sa.String(length=36), nullable=True))
        if 'policy_document_hash' not in existing_columns:
            op.add_column('policies', sa.Column('policy_document_hash', sa.String(length=64), nullable=True))
        
        # Add policy_hash
        if 'policy_hash' not in existing_columns:
            op.add_column('policies', sa.Column('policy_hash', sa.String(length=64), nullable=False, server_default=''))
        
        # Add cancellation fields
        if 'cancelled_at' not in existing_columns:
            op.add_column('policies', sa.Column('cancelled_at', sa.DateTime(), nullable=True))
        if 'cancelled_by_user_id' not in existing_columns:
            op.add_column('policies', sa.Column('cancelled_by_user_id', sa.String(length=26), nullable=True))
        if 'cancellation_reason' not in existing_columns:
            op.add_column('policies', sa.Column('cancellation_reason', sa.Text(), nullable=True))
        if 'refund_amount_cents' not in existing_columns:
            op.add_column('policies', sa.Column('refund_amount_cents', sa.Integer(), nullable=True))
        
        # Add CLAIMED status (update enum if needed - MySQL doesn't support ALTER TYPE)
        # This will be handled in application code
        
        # Add foreign key constraints
        existing_fks = [fk['name'] for fk in inspector.get_foreign_keys('policies')]
        
        if 'quote_id' in existing_columns and 'fk_policies_quote' not in existing_fks:
            try:
                op.create_foreign_key(
                    'fk_policies_quote',
                    'policies', 'quotes',
                    ['quote_id'], ['id'],
                    ondelete='RESTRICT'
                )
            except Exception:
                pass
        
        if 'evidence_bundle_id' in existing_columns and 'fk_policies_evidence_bundle' not in existing_fks:
            try:
                op.create_foreign_key(
                    'fk_policies_evidence_bundle',
                    'policies', 'evidence_bundles',
                    ['evidence_bundle_id'], ['id'],
                    ondelete='SET NULL'
                )
            except Exception:
                pass
        
        if 'policy_document_evidence_id' in existing_columns and 'fk_policies_document_evidence' not in existing_fks:
            try:
                op.create_foreign_key(
                    'fk_policies_document_evidence',
                    'policies', 'evidence_objects',
                    ['policy_document_evidence_id'], ['id'],
                    ondelete='SET NULL'
                )
            except Exception:
                pass
        
        # Create indexes
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('policies')]
        
        if 'idx_policies_quote' not in existing_indexes:
            op.create_index('idx_policies_quote', 'policies', ['quote_id'], unique=False)
        if 'idx_policies_hash' not in existing_indexes:
            op.create_index('idx_policies_hash', 'policies', ['policy_hash'], unique=False)
    
    # Create policy_events table
    table_exists = 'policy_events' in inspector.get_table_names()
    
    if not table_exists:
        op.create_table(
            'policy_events',
            sa.Column('id', sa.String(length=26), nullable=False),  # ULID
            sa.Column('policy_id', sa.String(length=26), nullable=False),  # ULID
            
            sa.Column('event_type', sa.String(length=50), nullable=False),
            # BOUND, DOCUMENT_GENERATED, PREMIUM_PAID, CANCELLED, EXPIRED, CLAIM_FILED
            
            sa.Column('actor_type', sa.String(length=20), nullable=False),  # USER, SYSTEM
            sa.Column('actor_id', sa.String(length=26), nullable=True),  # ULID
            
            sa.Column('payload_json', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            
            sa.ForeignKeyConstraint(['policy_id'], ['policies.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        
        # Create indexes
        op.create_index('idx_policy_events_policy', 'policy_events', ['policy_id'], unique=False)
        op.create_index('idx_policy_events_type', 'policy_events', ['event_type'], unique=False)
        op.create_index('idx_policy_events_created', 'policy_events', ['created_at'], unique=False)


def downgrade() -> None:
    # Drop policy_events table
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    
    if 'policy_events' in inspector.get_table_names():
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('policy_events')]
        
        if 'idx_policy_events_created' in existing_indexes:
            op.drop_index('idx_policy_events_created', table_name='policy_events')
        if 'idx_policy_events_type' in existing_indexes:
            op.drop_index('idx_policy_events_type', table_name='policy_events')
        if 'idx_policy_events_policy' in existing_indexes:
            op.drop_index('idx_policy_events_policy', table_name='policy_events')
        
        op.drop_table('policy_events')
    
    # Note: We don't drop columns in downgrade to preserve data
    # If full rollback is needed, manually drop columns
