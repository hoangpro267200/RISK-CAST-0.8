"""Create risk_run_jobs table

Revision ID: 017_risk_run_jobs
Revises: 016_rbac
Create Date: 2024-12-20

Creates risk_run_jobs table for job queue with locking and retry support.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '017_risk_run_jobs'
down_revision = '016_rbac'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create risk_run_jobs table
    op.create_table(
        'risk_run_jobs',
        sa.Column('id', sa.String(length=36), nullable=False),  # UUID
        sa.Column('run_id', sa.String(length=36), nullable=False),  # UUID (FK to risk_runs.id)
        
        # Status
        sa.Column(
            'status',
            sa.Enum('PENDING', 'LOCKED', 'PROCESSING', 'COMPLETED', 'FAILED', name='riskrunjobstatus', native_enum=False),
            nullable=False,
            server_default='PENDING',
            index=True
        ),
        
        # Priority
        sa.Column('priority', sa.Integer(), nullable=False, server_default='0'),
        
        # Locking
        sa.Column('locked_by', sa.String(length=255), nullable=True),  # Worker instance ID
        sa.Column('locked_at', sa.DateTime(), nullable=True),
        sa.Column('lock_expires_at', sa.DateTime(), nullable=True),
        
        # Retry
        sa.Column('attempt_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_attempts', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('next_retry_at', sa.DateTime(), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        
        # Timing
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), index=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        
        sa.ForeignKeyConstraint(['run_id'], ['risk_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    # Index for pending jobs (filtered index - MySQL doesn't support WHERE clause in CREATE INDEX)
    # We'll create a regular index and filter in queries
    op.create_index('ix_risk_run_jobs_status_priority_created', 'risk_run_jobs', ['status', 'priority', 'created_at'], unique=False)
    
    # Index for retry jobs
    op.create_index('ix_risk_run_jobs_status_next_retry', 'risk_run_jobs', ['status', 'next_retry_at'], unique=False)
    
    # Additional indexes for common queries
    op.create_index('ix_risk_run_jobs_run_id', 'risk_run_jobs', ['run_id'], unique=False)
    op.create_index('ix_risk_run_jobs_locked_by', 'risk_run_jobs', ['locked_by'], unique=False)
    op.create_index('ix_risk_run_jobs_lock_expires_at', 'risk_run_jobs', ['lock_expires_at'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_risk_run_jobs_lock_expires_at', table_name='risk_run_jobs')
    op.drop_index('ix_risk_run_jobs_locked_by', table_name='risk_run_jobs')
    op.drop_index('ix_risk_run_jobs_run_id', table_name='risk_run_jobs')
    op.drop_index('ix_risk_run_jobs_status_next_retry', table_name='risk_run_jobs')
    op.drop_index('ix_risk_run_jobs_status_priority_created', table_name='risk_run_jobs')
    
    # Drop table
    op.drop_table('risk_run_jobs')
    
    # Drop enum type
    op.execute("DROP TYPE IF EXISTS riskrunjobstatus")
