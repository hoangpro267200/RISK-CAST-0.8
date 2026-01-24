"""Enhance claims table with additional fields and create claim_events

Revision ID: 025_enhance_claims
Revises: 024_enhance_policies
Create Date: 2025-01-23

Adds claim_number, investigation fields, decision fields, adjudication_json,
approved_amount_cents, payout_id, and claim_events table.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '025_enhance_claims'
down_revision = '024_enhance_policies'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if tables exist
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # Enhance claims table
    if 'claims' in inspector.get_table_names():
        existing_columns = [col['name'] for col in inspector.get_columns('claims')]
        
        # Add claim_number
        if 'claim_number' not in existing_columns:
            op.add_column('claims', sa.Column('claim_number', sa.String(length=50), nullable=True))
        
        # Add investigation fields
        if 'assigned_adjuster_id' not in existing_columns:
            op.add_column('claims', sa.Column('assigned_adjuster_id', sa.String(length=26), nullable=True))
        if 'assigned_at' not in existing_columns:
            op.add_column('claims', sa.Column('assigned_at', sa.DateTime(), nullable=True))
        if 'investigation_notes' not in existing_columns:
            op.add_column('claims', sa.Column('investigation_notes', sa.Text(), nullable=True))
        
        # Add decision fields
        if 'decision' not in existing_columns:
            op.add_column('claims', sa.Column('decision', sa.String(length=20), nullable=True))
        if 'decision_reason' not in existing_columns:
            op.add_column('claims', sa.Column('decision_reason', sa.Text(), nullable=True))
        if 'decision_by_user_id' not in existing_columns:
            op.add_column('claims', sa.Column('decision_by_user_id', sa.String(length=26), nullable=True))
        if 'decision_at' not in existing_columns:
            op.add_column('claims', sa.Column('decision_at', sa.DateTime(), nullable=True))
        
        # Add approved amount
        if 'approved_amount_cents' not in existing_columns:
            op.add_column('claims', sa.Column('approved_amount_cents', sa.BigInteger(), nullable=True))
        if 'approved_currency' not in existing_columns:
            op.add_column('claims', sa.Column('approved_currency', sa.String(length=3), nullable=True))
        
        # Add adjudication_json
        if 'adjudication_json' not in existing_columns:
            op.add_column('claims', sa.Column('adjudication_json', sa.JSON(), nullable=True))
        
        # Add payout_id
        if 'payout_id' not in existing_columns:
            op.add_column('claims', sa.Column('payout_id', sa.String(length=36), nullable=True))
        
        # Add closed_at
        if 'closed_at' not in existing_columns:
            op.add_column('claims', sa.Column('closed_at', sa.DateTime(), nullable=True))
        
        # Add WITHDRAWN status (handled in application code for MySQL)
        
        # Make fnol_json required (if not already)
        # This is handled in application code
        
        # Create unique constraint for claim_number
        existing_constraints = [c['name'] for c in inspector.get_unique_constraints('claims')]
        if 'uq_claim_number' not in existing_constraints:
            try:
                op.create_unique_constraint('uq_claim_number', 'claims', ['tenant_id', 'claim_number'])
            except Exception:
                pass
        
        # Create indexes
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('claims')]
        
        if 'idx_claims_claim_number' not in existing_indexes:
            op.create_index('idx_claims_claim_number', 'claims', ['claim_number'], unique=False)
        if 'idx_claims_adjuster' not in existing_indexes:
            op.create_index('idx_claims_adjuster', 'claims', ['assigned_adjuster_id'], unique=False)
        if 'idx_claims_payout' not in existing_indexes:
            op.create_index('idx_claims_payout', 'claims', ['payout_id'], unique=False)
    
    # Create claim_events table
    table_exists = 'claim_events' in inspector.get_table_names()
    
    if not table_exists:
        op.create_table(
            'claim_events',
            sa.Column('id', sa.String(length=26), nullable=False),  # ULID
            sa.Column('tenant_id', sa.String(length=26), nullable=False),  # ULID
            sa.Column('claim_id', sa.String(length=26), nullable=False),  # ULID
            
            sa.Column('event_type', sa.String(length=50), nullable=False),
            # STATE_TRANSITION, NOTE_ADDED, EVIDENCE_ADDED, ASSIGNMENT_CHANGED,
            # INFO_REQUESTED, ADJUDICATION, PAYOUT_PROPOSED, PAYOUT_AUTHORIZED
            
            sa.Column('from_status', sa.String(length=30), nullable=True),
            sa.Column('to_status', sa.String(length=30), nullable=True),
            
            sa.Column('actor_type', sa.String(length=20), nullable=False),  # USER, SYSTEM
            sa.Column('actor_id', sa.String(length=26), nullable=True),  # ULID
            
            sa.Column('payload_json', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            
            sa.ForeignKeyConstraint(['claim_id'], ['claims.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        
        # Create indexes
        op.create_index('idx_claim_events_claim', 'claim_events', ['claim_id'], unique=False)
        op.create_index('idx_claim_events_type', 'claim_events', ['event_type'], unique=False)
        op.create_index('idx_claim_events_created', 'claim_events', ['created_at'], unique=False)
        op.create_index('idx_claim_events_tenant', 'claim_events', ['tenant_id'], unique=False)


def downgrade() -> None:
    # Drop claim_events table
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    
    if 'claim_events' in inspector.get_table_names():
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('claim_events')]
        
        if 'idx_claim_events_tenant' in existing_indexes:
            op.drop_index('idx_claim_events_tenant', table_name='claim_events')
        if 'idx_claim_events_created' in existing_indexes:
            op.drop_index('idx_claim_events_created', table_name='claim_events')
        if 'idx_claim_events_type' in existing_indexes:
            op.drop_index('idx_claim_events_type', table_name='claim_events')
        if 'idx_claim_events_claim' in existing_indexes:
            op.drop_index('idx_claim_events_claim', table_name='claim_events')
        
        op.drop_table('claim_events')
    
    # Note: We don't drop columns in downgrade to preserve data
    # If full rollback is needed, manually drop columns
