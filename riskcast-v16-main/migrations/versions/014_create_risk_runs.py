"""Create risk_runs table

Revision ID: 014_risk_runs
Revises: 013_hash_chained_audit
Create Date: 2024-12-20

Creates risk_runs table with UUID primary key and provenance fields.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '014_risk_runs'
down_revision = '013_hash_chained_audit'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create risk_runs table
    op.create_table(
        'risk_runs',
        sa.Column('id', sa.String(length=36), nullable=False),  # UUID
        sa.Column('tenant_id', sa.String(length=26), nullable=False),  # ULID (matches tenants.id)
        sa.Column('assessment_id', sa.String(length=26), nullable=False),  # FK to risk_assessments
        
        # Status
        sa.Column(
            'status',
            sa.Enum('PENDING', 'QUEUED', 'RUNNING', 'SUCCEEDED', 'FAILED', 'CANCELLED', name='riskrunstatus', native_enum=False),
            nullable=False,
            server_default='PENDING'
        ),
        
        # Configuration
        sa.Column('seed', sa.BigInteger(), nullable=False),
        sa.Column('seed_strategy', sa.String(length=20), nullable=False),
        sa.Column('iterations', sa.Integer(), nullable=False, server_default='10000'),
        
        # Versioning
        sa.Column('engine_version', sa.String(length=50), nullable=False),
        sa.Column('model_version_id', sa.String(length=36), nullable=True),  # UUID (FK added later)
        
        # Results (populated on completion)
        sa.Column('result_json', sa.JSON(), nullable=True),
        sa.Column('result_hash', sa.String(length=64), nullable=True),
        
        # Error info (if failed)
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_details', sa.JSON(), nullable=True),
        
        # Timing
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        
        # Retry tracking
        sa.Column('attempt_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_attempts', sa.Integer(), nullable=False, server_default='3'),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assessment_id'], ['risk_assessments.id'], ondelete='CASCADE'),
    )
    
    # Create indexes
    op.create_index(
        'idx_risk_runs_tenant',
        'risk_runs',
        ['tenant_id'],
        unique=False
    )
    op.create_index(
        'idx_risk_runs_assessment',
        'risk_runs',
        ['assessment_id'],
        unique=False
    )
    op.create_index(
        'idx_risk_runs_status',
        'risk_runs',
        ['status'],
        unique=False
    )
    op.create_index(
        'ix_risk_runs_created_at',
        'risk_runs',
        ['created_at'],
        unique=False
    )
    op.create_index(
        'ix_risk_runs_started_at',
        'risk_runs',
        ['started_at'],
        unique=False
    )
    op.create_index(
        'ix_risk_runs_completed_at',
        'risk_runs',
        ['completed_at'],
        unique=False
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_risk_runs_completed_at', table_name='risk_runs')
    op.drop_index('ix_risk_runs_started_at', table_name='risk_runs')
    op.drop_index('ix_risk_runs_created_at', table_name='risk_runs')
    op.drop_index('idx_risk_runs_status', table_name='risk_runs')
    op.drop_index('idx_risk_runs_assessment', table_name='risk_runs')
    op.drop_index('idx_risk_runs_tenant', table_name='risk_runs')
    
    # Drop table
    op.drop_table('risk_runs')
    
    # Drop enum type
    op.execute("DROP TYPE IF EXISTS riskrunstatus")
