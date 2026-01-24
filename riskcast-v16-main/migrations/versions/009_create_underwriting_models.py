"""Create underwriting models

Revision ID: 009_underwriting
Revises: 008_evidence
Create Date: 2024-12-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '009_underwriting'
down_revision = '008_evidence'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create underwriting_submissions table
    op.create_table(
        'underwriting_submissions',
        sa.Column('id', sa.String(length=26), nullable=False),
        sa.Column('tenant_id', sa.String(length=26), nullable=False),
        sa.Column(
            'status',
            sa.Enum('DRAFT', 'SUBMITTED', 'UNDER_REVIEW', 'REQUESTED_INFO', 'QUOTED', 'BOUND', 'DECLINED', 'CANCELED', name='submissionstatus', native_enum=False),
            nullable=False,
            server_default='DRAFT'
        ),
        sa.Column('created_by_user_id', sa.String(length=26), nullable=True),
        sa.Column('risk_assessment_id', sa.String(length=26), nullable=False),
        sa.Column('risk_run_id', sa.String(length=26), nullable=True),
        sa.Column('evidence_bundle_id', sa.String(length=26), nullable=True),
        sa.Column('requested_coverage_json', sa.JSON(), nullable=True),
        sa.Column('corridor_id', sa.String(length=100), nullable=True),
        sa.Column('product_type', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['evidence_bundle_id'], ['evidence_bundles.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['risk_assessment_id'], ['risk_assessments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['risk_run_id'], ['risk_runs.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for underwriting_submissions
    op.create_index('ix_submissions_tenant_status', 'underwriting_submissions', ['tenant_id', 'status'])
    op.create_index('ix_submissions_tenant_created', 'underwriting_submissions', ['tenant_id', 'created_at'])
    op.create_index(op.f('ix_underwriting_submissions_id'), 'underwriting_submissions', ['id'], unique=False)
    op.create_index(op.f('ix_underwriting_submissions_tenant_id'), 'underwriting_submissions', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_underwriting_submissions_status'), 'underwriting_submissions', ['status'], unique=False)
    op.create_index(op.f('ix_underwriting_submissions_created_by_user_id'), 'underwriting_submissions', ['created_by_user_id'], unique=False)
    op.create_index(op.f('ix_underwriting_submissions_risk_assessment_id'), 'underwriting_submissions', ['risk_assessment_id'], unique=False)
    op.create_index(op.f('ix_underwriting_submissions_risk_run_id'), 'underwriting_submissions', ['risk_run_id'], unique=False)
    op.create_index(op.f('ix_underwriting_submissions_evidence_bundle_id'), 'underwriting_submissions', ['evidence_bundle_id'], unique=False)
    op.create_index(op.f('ix_underwriting_submissions_corridor_id'), 'underwriting_submissions', ['corridor_id'], unique=False)
    op.create_index(op.f('ix_underwriting_submissions_product_type'), 'underwriting_submissions', ['product_type'], unique=False)
    
    # Create underwriting_decisions table
    op.create_table(
        'underwriting_decisions',
        sa.Column('id', sa.String(length=26), nullable=False),
        sa.Column('tenant_id', sa.String(length=26), nullable=False),
        sa.Column('submission_id', sa.String(length=26), nullable=False),
        sa.Column('decided_by_user_id', sa.String(length=26), nullable=True),
        sa.Column(
            'decision',
            sa.Enum('QUOTE', 'DECLINE', 'REQUEST_INFO', name='decisiontype', native_enum=False),
            nullable=False
        ),
        sa.Column('terms_json', sa.JSON(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('model_version_id', sa.String(length=26), nullable=True),
        sa.Column('risk_run_id', sa.String(length=26), nullable=True),
        sa.Column('evidence_bundle_id', sa.String(length=26), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['decided_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['evidence_bundle_id'], ['evidence_bundles.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['model_version_id'], ['risk_model_versions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['risk_run_id'], ['risk_runs.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['submission_id'], ['underwriting_submissions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for underwriting_decisions
    op.create_index('ix_decisions_tenant_submission', 'underwriting_decisions', ['tenant_id', 'submission_id'])
    op.create_index('ix_decisions_tenant_created', 'underwriting_decisions', ['tenant_id', 'created_at'])
    op.create_index(op.f('ix_underwriting_decisions_id'), 'underwriting_decisions', ['id'], unique=False)
    op.create_index(op.f('ix_underwriting_decisions_tenant_id'), 'underwriting_decisions', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_underwriting_decisions_submission_id'), 'underwriting_decisions', ['submission_id'], unique=False)
    op.create_index(op.f('ix_underwriting_decisions_decided_by_user_id'), 'underwriting_decisions', ['decided_by_user_id'], unique=False)
    op.create_index(op.f('ix_underwriting_decisions_decision'), 'underwriting_decisions', ['decision'], unique=False)
    op.create_index(op.f('ix_underwriting_decisions_model_version_id'), 'underwriting_decisions', ['model_version_id'], unique=False)
    op.create_index(op.f('ix_underwriting_decisions_risk_run_id'), 'underwriting_decisions', ['risk_run_id'], unique=False)
    op.create_index(op.f('ix_underwriting_decisions_evidence_bundle_id'), 'underwriting_decisions', ['evidence_bundle_id'], unique=False)
    
    # Create policies table
    op.create_table(
        'policies',
        sa.Column('id', sa.String(length=26), nullable=False),
        sa.Column('tenant_id', sa.String(length=26), nullable=False),
        sa.Column('policy_number', sa.String(length=100), nullable=False),
        sa.Column(
            'status',
            sa.Enum('ACTIVE', 'CANCELED', 'EXPIRED', name='policystatus', native_enum=False),
            nullable=False,
            server_default='ACTIVE'
        ),
        sa.Column('submission_id', sa.String(length=26), nullable=True),
        sa.Column('bound_by_user_id', sa.String(length=26), nullable=True),
        sa.Column('bound_at', sa.DateTime(), nullable=True),
        sa.Column('effective_from', sa.DateTime(), nullable=False),
        sa.Column('effective_to', sa.DateTime(), nullable=False),
        sa.Column('model_version_id', sa.String(length=26), nullable=False),
        sa.Column('risk_run_id', sa.String(length=26), nullable=False),
        sa.Column('terms_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['bound_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['model_version_id'], ['risk_model_versions.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['risk_run_id'], ['risk_runs.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['submission_id'], ['underwriting_submissions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for policies
    op.create_index('ix_policies_tenant_status', 'policies', ['tenant_id', 'status'])
    op.create_index('ix_policies_tenant_policy_number', 'policies', ['tenant_id', 'policy_number'])
    op.create_index('ix_policies_effective_period', 'policies', ['effective_from', 'effective_to'])
    op.create_index(op.f('ix_policies_id'), 'policies', ['id'], unique=False)
    op.create_index(op.f('ix_policies_tenant_id'), 'policies', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_policies_policy_number'), 'policies', ['policy_number'], unique=False)
    op.create_index(op.f('ix_policies_status'), 'policies', ['status'], unique=False)
    op.create_index(op.f('ix_policies_submission_id'), 'policies', ['submission_id'], unique=False)
    op.create_index(op.f('ix_policies_bound_by_user_id'), 'policies', ['bound_by_user_id'], unique=False)
    op.create_index(op.f('ix_policies_bound_at'), 'policies', ['bound_at'], unique=False)
    op.create_index(op.f('ix_policies_effective_from'), 'policies', ['effective_from'], unique=False)
    op.create_index(op.f('ix_policies_effective_to'), 'policies', ['effective_to'], unique=False)
    op.create_index(op.f('ix_policies_model_version_id'), 'policies', ['model_version_id'], unique=False)
    op.create_index(op.f('ix_policies_risk_run_id'), 'policies', ['risk_run_id'], unique=False)
    
    # Create unique constraint for policy_number per tenant
    op.create_unique_constraint('uq_policies_tenant_policy_number', 'policies', ['tenant_id', 'policy_number'])


def downgrade() -> None:
    # Drop indexes first
    op.drop_constraint('uq_policies_tenant_policy_number', 'policies', type_='unique')
    
    op.drop_index(op.f('ix_policies_risk_run_id'), table_name='policies')
    op.drop_index(op.f('ix_policies_model_version_id'), table_name='policies')
    op.drop_index(op.f('ix_policies_effective_to'), table_name='policies')
    op.drop_index(op.f('ix_policies_effective_from'), table_name='policies')
    op.drop_index(op.f('ix_policies_bound_at'), table_name='policies')
    op.drop_index(op.f('ix_policies_bound_by_user_id'), table_name='policies')
    op.drop_index(op.f('ix_policies_submission_id'), table_name='policies')
    op.drop_index(op.f('ix_policies_status'), table_name='policies')
    op.drop_index(op.f('ix_policies_policy_number'), table_name='policies')
    op.drop_index(op.f('ix_policies_tenant_id'), table_name='policies')
    op.drop_index(op.f('ix_policies_id'), table_name='policies')
    op.drop_index('ix_policies_effective_period', table_name='policies')
    op.drop_index('ix_policies_tenant_policy_number', table_name='policies')
    op.drop_index('ix_policies_tenant_status', table_name='policies')
    
    op.drop_index(op.f('ix_underwriting_decisions_evidence_bundle_id'), table_name='underwriting_decisions')
    op.drop_index(op.f('ix_underwriting_decisions_risk_run_id'), table_name='underwriting_decisions')
    op.drop_index(op.f('ix_underwriting_decisions_model_version_id'), table_name='underwriting_decisions')
    op.drop_index(op.f('ix_underwriting_decisions_decision'), table_name='underwriting_decisions')
    op.drop_index(op.f('ix_underwriting_decisions_decided_by_user_id'), table_name='underwriting_decisions')
    op.drop_index(op.f('ix_underwriting_decisions_submission_id'), table_name='underwriting_decisions')
    op.drop_index(op.f('ix_underwriting_decisions_tenant_id'), table_name='underwriting_decisions')
    op.drop_index(op.f('ix_underwriting_decisions_id'), table_name='underwriting_decisions')
    op.drop_index('ix_decisions_tenant_created', table_name='underwriting_decisions')
    op.drop_index('ix_decisions_tenant_submission', table_name='underwriting_decisions')
    
    op.drop_index(op.f('ix_underwriting_submissions_product_type'), table_name='underwriting_submissions')
    op.drop_index(op.f('ix_underwriting_submissions_corridor_id'), table_name='underwriting_submissions')
    op.drop_index(op.f('ix_underwriting_submissions_evidence_bundle_id'), table_name='underwriting_submissions')
    op.drop_index(op.f('ix_underwriting_submissions_risk_run_id'), table_name='underwriting_submissions')
    op.drop_index(op.f('ix_underwriting_submissions_risk_assessment_id'), table_name='underwriting_submissions')
    op.drop_index(op.f('ix_underwriting_submissions_created_by_user_id'), table_name='underwriting_submissions')
    op.drop_index(op.f('ix_underwriting_submissions_status'), table_name='underwriting_submissions')
    op.drop_index(op.f('ix_underwriting_submissions_tenant_id'), table_name='underwriting_submissions')
    op.drop_index(op.f('ix_underwriting_submissions_id'), table_name='underwriting_submissions')
    op.drop_index('ix_submissions_tenant_created', table_name='underwriting_submissions')
    op.drop_index('ix_submissions_tenant_status', table_name='underwriting_submissions')
    
    # Drop tables
    op.drop_table('policies')
    op.drop_table('underwriting_decisions')
    op.drop_table('underwriting_submissions')
