"""Enhance underwriting submissions with events and additional fields

Revision ID: 022_enhance_underwriting
Revises: 021_evidence_bundles
Create Date: 2025-01-23

Adds submission_number, applicant_json, assignment fields, decision fields,
and submission events table for history tracking.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '022_enhance_underwriting'
down_revision = '021_evidence_bundles'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if tables exist
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # Add new columns to underwriting_submissions
    if 'underwriting_submissions' in inspector.get_table_names():
        existing_columns = [col['name'] for col in inspector.get_columns('underwriting_submissions')]
        
        # Add submission_number
        if 'submission_number' not in existing_columns:
            op.add_column('underwriting_submissions', sa.Column('submission_number', sa.String(length=50), nullable=True))
        
        # Add applicant_json
        if 'applicant_json' not in existing_columns:
            op.add_column('underwriting_submissions', sa.Column('applicant_json', sa.JSON(), nullable=True))
        
        # Add applicant_pii flag
        if 'applicant_pii' not in existing_columns:
            op.add_column('underwriting_submissions', sa.Column('applicant_pii', sa.Boolean(), nullable=True, server_default='1'))
        
        # Add shipment_id
        if 'shipment_id' not in existing_columns:
            op.add_column('underwriting_submissions', sa.Column('shipment_id', sa.String(length=36), nullable=True))
        
        # Add assignment fields
        if 'assigned_to_user_id' not in existing_columns:
            op.add_column('underwriting_submissions', sa.Column('assigned_to_user_id', sa.String(length=26), nullable=True))
        if 'assigned_at' not in existing_columns:
            op.add_column('underwriting_submissions', sa.Column('assigned_at', sa.DateTime(), nullable=True))
        
        # Add decision fields
        if 'decision' not in existing_columns:
            op.add_column('underwriting_submissions', sa.Column('decision', sa.String(length=20), nullable=True))
        if 'decision_reason' not in existing_columns:
            op.add_column('underwriting_submissions', sa.Column('decision_reason', sa.Text(), nullable=True))
        if 'decision_by_user_id' not in existing_columns:
            op.add_column('underwriting_submissions', sa.Column('decision_by_user_id', sa.String(length=26), nullable=True))
        if 'decision_at' not in existing_columns:
            op.add_column('underwriting_submissions', sa.Column('decision_at', sa.DateTime(), nullable=True))
        
        # Add submitted_at
        if 'submitted_at' not in existing_columns:
            op.add_column('underwriting_submissions', sa.Column('submitted_at', sa.DateTime(), nullable=True))
        
        # Add expires_at
        if 'expires_at' not in existing_columns:
            op.add_column('underwriting_submissions', sa.Column('expires_at', sa.DateTime(), nullable=True))
        
        # Add EXPIRED status to enum (if needed)
        # Note: MySQL doesn't support ALTER TYPE, so we'll handle this in application code
        
        # Create unique constraint for submission_number per tenant
        existing_constraints = [c['name'] for c in inspector.get_unique_constraints('underwriting_submissions')]
        if 'uq_submission_number' not in existing_constraints:
            try:
                op.create_unique_constraint('uq_submission_number', 'underwriting_submissions', ['tenant_id', 'submission_number'])
            except Exception:
                pass  # Constraint might already exist
        
        # Create indexes
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('underwriting_submissions')]
        
        if 'idx_submissions_assignee' not in existing_indexes:
            op.create_index('idx_submissions_assignee', 'underwriting_submissions', ['assigned_to_user_id'], unique=False)
        if 'idx_submissions_submitted_at' not in existing_indexes:
            op.create_index('idx_submissions_submitted_at', 'underwriting_submissions', ['submitted_at'], unique=False)
        if 'idx_submissions_expires_at' not in existing_indexes:
            op.create_index('idx_submissions_expires_at', 'underwriting_submissions', ['expires_at'], unique=False)
    
    # Create underwriting_submission_events table
    table_exists = 'underwriting_submission_events' in inspector.get_table_names()
    
    if not table_exists:
        op.create_table(
            'underwriting_submission_events',
            sa.Column('id', sa.String(length=26), nullable=False),  # ULID
            sa.Column('submission_id', sa.String(length=26), nullable=False),  # ULID (FK)
            
            sa.Column('event_type', sa.String(length=50), nullable=False),
            # STATE_TRANSITION, NOTE_ADDED, EVIDENCE_ADDED, ASSIGNMENT_CHANGED, INFO_REQUESTED
            
            sa.Column('from_status', sa.String(length=30), nullable=True),
            sa.Column('to_status', sa.String(length=30), nullable=True),
            
            sa.Column('actor_type', sa.String(length=20), nullable=False),  # USER, SYSTEM
            sa.Column('actor_id', sa.String(length=26), nullable=True),  # ULID
            
            sa.Column('payload_json', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            
            sa.ForeignKeyConstraint(['submission_id'], ['underwriting_submissions.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        
        # Create indexes
        op.create_index('idx_submission_events_submission', 'underwriting_submission_events', ['submission_id'], unique=False)
        op.create_index('idx_submission_events_created', 'underwriting_submission_events', ['created_at'], unique=False)
        op.create_index('idx_submission_events_type', 'underwriting_submission_events', ['event_type'], unique=False)


def downgrade() -> None:
    # Drop indexes
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # Drop submission events table
    if 'underwriting_submission_events' in inspector.get_table_names():
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('underwriting_submission_events')]
        
        if 'idx_submission_events_type' in existing_indexes:
            op.drop_index('idx_submission_events_type', table_name='underwriting_submission_events')
        if 'idx_submission_events_created' in existing_indexes:
            op.drop_index('idx_submission_events_created', table_name='underwriting_submission_events')
        if 'idx_submission_events_submission' in existing_indexes:
            op.drop_index('idx_submission_events_submission', table_name='underwriting_submission_events')
        
        op.drop_table('underwriting_submission_events')
    
    # Drop columns from underwriting_submissions (optional - preserve data)
    if 'underwriting_submissions' in inspector.get_table_names():
        existing_columns = [col['name'] for col in inspector.get_columns('underwriting_submissions')]
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('underwriting_submissions')]
        existing_constraints = [c['name'] for c in inspector.get_unique_constraints('underwriting_submissions')]
        
        # Drop indexes
        if 'idx_submissions_expires_at' in existing_indexes:
            op.drop_index('idx_submissions_expires_at', table_name='underwriting_submissions')
        if 'idx_submissions_submitted_at' in existing_indexes:
            op.drop_index('idx_submissions_submitted_at', table_name='underwriting_submissions')
        if 'idx_submissions_assignee' in existing_indexes:
            op.drop_index('idx_submissions_assignee', table_name='underwriting_submissions')
        
        # Drop unique constraint
        if 'uq_submission_number' in existing_constraints:
            op.drop_constraint('uq_submission_number', 'underwriting_submissions', type_='unique')
        
        # Note: We don't drop columns in downgrade to preserve data
        # If full rollback is needed, manually drop columns
