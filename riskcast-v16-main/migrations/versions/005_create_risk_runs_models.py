"""Create risk_runs models

Revision ID: 005_risk_runs
Revises: 004_risk_assessments
Create Date: 2024-12-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '005_risk_runs'
down_revision = '004_risk_assessments'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create risk_runs table
    op.create_table(
        'risk_runs',
        sa.Column('id', sa.String(length=26), nullable=False),
        sa.Column('tenant_id', sa.String(length=26), nullable=False),
        sa.Column('risk_assessment_id', sa.String(length=26), nullable=False),
        sa.Column(
            'status',
            sa.Enum('QUEUED', 'RUNNING', 'SUCCEEDED', 'FAILED', 'CANCELED', name='riskrunstatus', native_enum=False),
            nullable=False,
            server_default='QUEUED'
        ),
        sa.Column('engine_version', sa.String(length=100), nullable=False),
        sa.Column('model_version_id', sa.String(length=26), nullable=True),
        sa.Column('result_schema_version', sa.String(length=50), nullable=False),
        sa.Column(
            'seed_strategy',
            sa.Enum('DETERMINISTIC_INPUT_HASH', 'USER_PROVIDED', name='seedstrategy', native_enum=False),
            nullable=False
        ),
        sa.Column('seed', sa.BigInteger(), nullable=False),
        sa.Column('iterations', sa.Integer(), nullable=False),
        sa.Column('options_json', sa.JSON(), nullable=True),
        sa.Column('result_json', sa.JSON(), nullable=True),
        sa.Column('result_hash', sa.String(length=64), nullable=True),
        sa.Column('error_json', sa.JSON(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['risk_assessment_id'], ['risk_assessments.id'], ondelete='CASCADE')
    )
    
    # Create indexes for risk_runs
    op.create_index(
        op.f('ix_risk_runs_tenant_id'),
        'risk_runs',
        ['tenant_id'],
        unique=False
    )
    op.create_index(
        op.f('ix_risk_runs_created_at'),
        'risk_runs',
        ['created_at'],
        unique=False
    )
    op.create_index(
        op.f('ix_risk_runs_updated_at'),
        'risk_runs',
        ['updated_at'],
        unique=False
    )
    op.create_index(
        op.f('ix_risk_runs_risk_assessment_id'),
        'risk_runs',
        ['risk_assessment_id'],
        unique=False
    )
    op.create_index(
        op.f('ix_risk_runs_status'),
        'risk_runs',
        ['status'],
        unique=False
    )
    op.create_index(
        op.f('ix_risk_runs_engine_version'),
        'risk_runs',
        ['engine_version'],
        unique=False
    )
    op.create_index(
        op.f('ix_risk_runs_model_version_id'),
        'risk_runs',
        ['model_version_id'],
        unique=False
    )
    op.create_index(
        op.f('ix_risk_runs_result_hash'),
        'risk_runs',
        ['result_hash'],
        unique=False
    )
    op.create_index(
        op.f('ix_risk_runs_started_at'),
        'risk_runs',
        ['started_at'],
        unique=False
    )
    op.create_index(
        op.f('ix_risk_runs_completed_at'),
        'risk_runs',
        ['completed_at'],
        unique=False
    )
    
    # Create composite indexes for risk_runs
    op.create_index(
        'ix_risk_runs_tenant_assessment',
        'risk_runs',
        ['tenant_id', 'risk_assessment_id', 'created_at'],
        unique=False
    )
    op.create_index(
        'ix_risk_runs_tenant_status',
        'risk_runs',
        ['tenant_id', 'status'],
        unique=False
    )
    op.create_index(
        'ix_risk_runs_assessment_status',
        'risk_runs',
        ['risk_assessment_id', 'status'],
        unique=False
    )
    
    # Create risk_run_jobs table
    op.create_table(
        'risk_run_jobs',
        sa.Column('id', sa.String(length=26), nullable=False),
        sa.Column('tenant_id', sa.String(length=26), nullable=False),
        sa.Column('risk_run_id', sa.String(length=26), nullable=False),
        sa.Column(
            'status',
            sa.Enum('QUEUED', 'LOCKED', 'DONE', 'FAILED', name='riskrunjobstatus', native_enum=False),
            nullable=False,
            server_default='QUEUED'
        ),
        sa.Column('locked_by', sa.String(length=100), nullable=True),
        sa.Column('locked_at', sa.DateTime(), nullable=True),
        sa.Column('attempt_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('available_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['risk_run_id'], ['risk_runs.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('risk_run_id', name='uq_risk_run_jobs_risk_run_id')
    )
    
    # Create indexes for risk_run_jobs
    op.create_index(
        op.f('ix_risk_run_jobs_tenant_id'),
        'risk_run_jobs',
        ['tenant_id'],
        unique=False
    )
    op.create_index(
        op.f('ix_risk_run_jobs_created_at'),
        'risk_run_jobs',
        ['created_at'],
        unique=False
    )
    op.create_index(
        op.f('ix_risk_run_jobs_updated_at'),
        'risk_run_jobs',
        ['updated_at'],
        unique=False
    )
    op.create_index(
        op.f('ix_risk_run_jobs_risk_run_id'),
        'risk_run_jobs',
        ['risk_run_id'],
        unique=True
    )
    op.create_index(
        op.f('ix_risk_run_jobs_status'),
        'risk_run_jobs',
        ['status'],
        unique=False
    )
    op.create_index(
        op.f('ix_risk_run_jobs_available_at'),
        'risk_run_jobs',
        ['available_at'],
        unique=False
    )
    
    # Create composite indexes for risk_run_jobs
    op.create_index(
        'ix_risk_run_jobs_status_available',
        'risk_run_jobs',
        ['status', 'available_at'],
        unique=False
    )
    op.create_index(
        'ix_risk_run_jobs_tenant_status',
        'risk_run_jobs',
        ['tenant_id', 'status'],
        unique=False
    )


def downgrade() -> None:
    # Drop indexes for risk_run_jobs
    op.drop_index('ix_risk_run_jobs_tenant_status', table_name='risk_run_jobs')
    op.drop_index('ix_risk_run_jobs_status_available', table_name='risk_run_jobs')
    op.drop_index(op.f('ix_risk_run_jobs_available_at'), table_name='risk_run_jobs')
    op.drop_index(op.f('ix_risk_run_jobs_status'), table_name='risk_run_jobs')
    op.drop_index(op.f('ix_risk_run_jobs_risk_run_id'), table_name='risk_run_jobs')
    op.drop_index(op.f('ix_risk_run_jobs_updated_at'), table_name='risk_run_jobs')
    op.drop_index(op.f('ix_risk_run_jobs_created_at'), table_name='risk_run_jobs')
    op.drop_index(op.f('ix_risk_run_jobs_tenant_id'), table_name='risk_run_jobs')
    
    # Drop risk_run_jobs table
    op.drop_table('risk_run_jobs')
    
    # Drop indexes for risk_runs
    op.drop_index('ix_risk_runs_assessment_status', table_name='risk_runs')
    op.drop_index('ix_risk_runs_tenant_status', table_name='risk_runs')
    op.drop_index('ix_risk_runs_tenant_assessment', table_name='risk_runs')
    op.drop_index(op.f('ix_risk_runs_completed_at'), table_name='risk_runs')
    op.drop_index(op.f('ix_risk_runs_started_at'), table_name='risk_runs')
    op.drop_index(op.f('ix_risk_runs_result_hash'), table_name='risk_runs')
    op.drop_index(op.f('ix_risk_runs_model_version_id'), table_name='risk_runs')
    op.drop_index(op.f('ix_risk_runs_engine_version'), table_name='risk_runs')
    op.drop_index(op.f('ix_risk_runs_status'), table_name='risk_runs')
    op.drop_index(op.f('ix_risk_runs_risk_assessment_id'), table_name='risk_runs')
    op.drop_index(op.f('ix_risk_runs_updated_at'), table_name='risk_runs')
    op.drop_index(op.f('ix_risk_runs_created_at'), table_name='risk_runs')
    op.drop_index(op.f('ix_risk_runs_tenant_id'), table_name='risk_runs')
    
    # Drop risk_runs table
    op.drop_table('risk_runs')
