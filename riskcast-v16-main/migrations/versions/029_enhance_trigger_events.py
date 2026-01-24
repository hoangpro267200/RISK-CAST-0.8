"""Enhance trigger events table with additional fields

Revision ID: 029_enhance_trigger_events
Revises: 028_enhance_trigger_definitions
Create Date: 2025-01-23

Adds detected_at, detection_json, validation_json, payout_calculation_json,
proposed_payout_cents, evaluation_hash, validated_at, approved_at, approved_by_user_id.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '029_enhance_trigger_events'
down_revision = '028_enhance_trigger_definitions'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if tables exist
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # Enhance trigger_events table
    if 'trigger_events' in inspector.get_table_names():
        existing_columns = [col['name'] for col in inspector.get_columns('trigger_events')]
        
        # Add detected_at
        if 'detected_at' not in existing_columns:
            op.add_column('trigger_events', sa.Column('detected_at', sa.DateTime(), nullable=True))
        
        # Add detection_json
        if 'detection_json' not in existing_columns:
            op.add_column('trigger_events', sa.Column('detection_json', sa.JSON(), nullable=True))
        
        # Add validation_json (might already exist as validation_json)
        if 'validation_json' not in existing_columns:
            op.add_column('trigger_events', sa.Column('validation_json', sa.JSON(), nullable=True))
        
        # Add payout_calculation_json
        if 'payout_calculation_json' not in existing_columns:
            op.add_column('trigger_events', sa.Column('payout_calculation_json', sa.JSON(), nullable=True))
        
        # Add proposed_payout_cents
        if 'proposed_payout_cents' not in existing_columns:
            op.add_column('trigger_events', sa.Column('proposed_payout_cents', sa.BigInteger(), nullable=True))
        
        # Add evaluation_hash
        if 'evaluation_hash' not in existing_columns:
            op.add_column('trigger_events', sa.Column('evaluation_hash', sa.String(length=64), nullable=True))
        
        # Add validated_at
        if 'validated_at' not in existing_columns:
            op.add_column('trigger_events', sa.Column('validated_at', sa.DateTime(), nullable=True))
        
        # Add approved_at
        if 'approved_at' not in existing_columns:
            op.add_column('trigger_events', sa.Column('approved_at', sa.DateTime(), nullable=True))
        
        # Add approved_by_user_id
        if 'approved_by_user_id' not in existing_columns:
            op.add_column('trigger_events', sa.Column('approved_by_user_id', sa.String(length=26), nullable=True))
        
        # Update status enum to include VALIDATING, CORROBORATION_FAILED
        # This is handled in application code for MySQL
        
        # Create foreign key for approved_by_user_id
        existing_constraints = [c['name'] for c in inspector.get_foreign_keys('trigger_events')]
        if 'fk_trigger_events_approved_by' not in existing_constraints:
            try:
                op.create_foreign_key(
                    'fk_trigger_events_approved_by',
                    'trigger_events',
                    'users',
                    ['approved_by_user_id'],
                    ['id'],
                    ondelete='SET NULL'
                )
            except Exception:
                pass
        
        # Create indexes
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('trigger_events')]
        
        if 'idx_trigger_events_detected' not in existing_indexes:
            op.create_index('idx_trigger_events_detected', 'trigger_events', ['detected_at'], unique=False)
        if 'idx_trigger_events_evaluation_hash' not in existing_indexes:
            op.create_index('idx_trigger_events_evaluation_hash', 'trigger_events', ['evaluation_hash'], unique=False)
        if 'idx_trigger_events_approved_by' not in existing_indexes:
            op.create_index('idx_trigger_events_approved_by', 'trigger_events', ['approved_by_user_id'], unique=False)


def downgrade() -> None:
    # Note: We don't drop columns in downgrade to preserve data
    # If full rollback is needed, manually drop columns
    pass
