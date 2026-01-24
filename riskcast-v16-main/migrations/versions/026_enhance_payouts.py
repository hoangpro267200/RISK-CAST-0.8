"""Enhance payouts table with additional fields

Revision ID: 026_enhance_payouts
Revises: 025_enhance_claims
Create Date: 2025-01-23

Adds payout_number, payout_type, calculation_snapshot_json, calculation_hash,
recipient_json, approval workflow fields, payment fields, and failure tracking.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '026_enhance_payouts'
down_revision = '025_enhance_claims'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if tables exist
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # Enhance payouts table
    if 'payouts' in inspector.get_table_names():
        existing_columns = [col['name'] for col in inspector.get_columns('payouts')]
        
        # Add payout_number
        if 'payout_number' not in existing_columns:
            op.add_column('payouts', sa.Column('payout_number', sa.String(length=50), nullable=True))
        
        # Add payout_type
        if 'payout_type' not in existing_columns:
            op.add_column('payouts', sa.Column('payout_type', sa.String(length=20), nullable=True, server_default='CLAIM'))
        
        # Add calculation fields
        if 'calculation_snapshot_json' not in existing_columns:
            op.add_column('payouts', sa.Column('calculation_snapshot_json', sa.JSON(), nullable=True))
        if 'calculation_hash' not in existing_columns:
            op.add_column('payouts', sa.Column('calculation_hash', sa.String(length=64), nullable=True))
        
        # Add recipient_json
        if 'recipient_json' not in existing_columns:
            op.add_column('payouts', sa.Column('recipient_json', sa.JSON(), nullable=True))
        
        # Add approval workflow fields
        if 'proposed_by_user_id' not in existing_columns:
            op.add_column('payouts', sa.Column('proposed_by_user_id', sa.String(length=26), nullable=True))
        if 'proposed_at' not in existing_columns:
            op.add_column('payouts', sa.Column('proposed_at', sa.DateTime(), nullable=True))
        if 'approved_by_user_id' not in existing_columns:
            # This might already exist as approved_by_user_id
            pass
        if 'approved_at' not in existing_columns:
            op.add_column('payouts', sa.Column('approved_at', sa.DateTime(), nullable=True))
        if 'authorized_by_user_id' not in existing_columns:
            op.add_column('payouts', sa.Column('authorized_by_user_id', sa.String(length=26), nullable=True))
        if 'authorized_at' not in existing_columns:
            op.add_column('payouts', sa.Column('authorized_at', sa.DateTime(), nullable=True))
        
        # Add payment fields
        if 'payment_reference' not in existing_columns:
            op.add_column('payouts', sa.Column('payment_reference', sa.String(length=255), nullable=True))
        if 'payment_method' not in existing_columns:
            op.add_column('payouts', sa.Column('payment_method', sa.String(length=50), nullable=True))
        if 'payment_confirmation_json' not in existing_columns:
            op.add_column('payouts', sa.Column('payment_confirmation_json', sa.JSON(), nullable=True))
        
        # Add failure tracking
        if 'failure_reason' not in existing_columns:
            op.add_column('payouts', sa.Column('failure_reason', sa.Text(), nullable=True))
        if 'retry_count' not in existing_columns:
            op.add_column('payouts', sa.Column('retry_count', sa.Integer(), nullable=True, server_default='0'))
        
        # Update status enum to include PROCESSING, FAILED, CANCELLED
        # This is handled in application code for MySQL
        
        # Create unique constraint for payout_number
        existing_constraints = [c['name'] for c in inspector.get_unique_constraints('payouts')]
        if 'uq_payout_number' not in existing_constraints:
            try:
                op.create_unique_constraint('uq_payout_number', 'payouts', ['tenant_id', 'payout_number'])
            except Exception:
                pass
        
        # Create indexes
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('payouts')]
        
        if 'idx_payouts_payout_number' not in existing_indexes:
            op.create_index('idx_payouts_payout_number', 'payouts', ['payout_number'], unique=False)
        if 'idx_payouts_payout_type' not in existing_indexes:
            op.create_index('idx_payouts_payout_type', 'payouts', ['payout_type'], unique=False)
        if 'idx_payouts_proposed_by' not in existing_indexes:
            op.create_index('idx_payouts_proposed_by', 'payouts', ['proposed_by_user_id'], unique=False)
        if 'idx_payouts_authorized_by' not in existing_indexes:
            op.create_index('idx_payouts_authorized_by', 'payouts', ['authorized_by_user_id'], unique=False)


def downgrade() -> None:
    # Note: We don't drop columns in downgrade to preserve data
    # If full rollback is needed, manually drop columns
    pass
