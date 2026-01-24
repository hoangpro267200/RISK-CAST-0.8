"""Create claims models

Revision ID: 010_claims
Revises: 009_underwriting
Create Date: 2024-12-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '010_claims'
down_revision = '009_underwriting'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create claims table
    op.create_table(
        'claims',
        sa.Column('id', sa.String(length=26), nullable=False),
        sa.Column('tenant_id', sa.String(length=26), nullable=False),
        sa.Column('policy_id', sa.String(length=26), nullable=False),
        sa.Column(
            'status',
            sa.Enum('FNOL_RECEIVED', 'UNDER_INVESTIGATION', 'AWAITING_EVIDENCE', 'APPROVED', 'DECLINED', 'AUTHORIZED', 'PAID', 'CLOSED', name='claimstatus', native_enum=False),
            nullable=False,
            server_default='FNOL_RECEIVED'
        ),
        sa.Column('fnol_json', sa.JSON(), nullable=True),
        sa.Column('risk_run_id', sa.String(length=26), nullable=True),
        sa.Column('evidence_bundle_id', sa.String(length=26), nullable=True),
        sa.Column('created_by_user_id', sa.String(length=26), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['evidence_bundle_id'], ['evidence_bundles.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['policy_id'], ['policies.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['risk_run_id'], ['risk_runs.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for claims
    op.create_index('ix_claims_tenant_status', 'claims', ['tenant_id', 'status'])
    op.create_index('ix_claims_tenant_created', 'claims', ['tenant_id', 'created_at'])
    op.create_index('ix_claims_policy_status', 'claims', ['policy_id', 'status'])
    op.create_index(op.f('ix_claims_id'), 'claims', ['id'], unique=False)
    op.create_index(op.f('ix_claims_tenant_id'), 'claims', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_claims_policy_id'), 'claims', ['policy_id'], unique=False)
    op.create_index(op.f('ix_claims_status'), 'claims', ['status'], unique=False)
    op.create_index(op.f('ix_claims_risk_run_id'), 'claims', ['risk_run_id'], unique=False)
    op.create_index(op.f('ix_claims_evidence_bundle_id'), 'claims', ['evidence_bundle_id'], unique=False)
    op.create_index(op.f('ix_claims_created_by_user_id'), 'claims', ['created_by_user_id'], unique=False)
    
    # Create claim_events table
    op.create_table(
        'claim_events',
        sa.Column('id', sa.String(length=26), nullable=False),
        sa.Column('tenant_id', sa.String(length=26), nullable=False),
        sa.Column('claim_id', sa.String(length=26), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('from_state', sa.String(length=50), nullable=True),
        sa.Column('to_state', sa.String(length=50), nullable=True),
        sa.Column('actor_type', sa.String(length=20), nullable=True),
        sa.Column('actor_id', sa.String(length=100), nullable=True),
        sa.Column('payload_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['claim_id'], ['claims.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for claim_events
    op.create_index('ix_claim_events_tenant_claim', 'claim_events', ['tenant_id', 'claim_id'])
    op.create_index('ix_claim_events_tenant_created', 'claim_events', ['tenant_id', 'created_at'])
    op.create_index('ix_claim_events_claim_type', 'claim_events', ['claim_id', 'event_type'])
    op.create_index(op.f('ix_claim_events_id'), 'claim_events', ['id'], unique=False)
    op.create_index(op.f('ix_claim_events_tenant_id'), 'claim_events', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_claim_events_claim_id'), 'claim_events', ['claim_id'], unique=False)
    op.create_index(op.f('ix_claim_events_event_type'), 'claim_events', ['event_type'], unique=False)
    op.create_index(op.f('ix_claim_events_actor_type'), 'claim_events', ['actor_type'], unique=False)
    op.create_index(op.f('ix_claim_events_actor_id'), 'claim_events', ['actor_id'], unique=False)
    
    # Create payouts table
    op.create_table(
        'payouts',
        sa.Column('id', sa.String(length=26), nullable=False),
        sa.Column('tenant_id', sa.String(length=26), nullable=False),
        sa.Column('claim_id', sa.String(length=26), nullable=True),
        sa.Column('policy_id', sa.String(length=26), nullable=False),
        sa.Column('trigger_event_id', sa.String(length=26), nullable=True),
        sa.Column(
            'status',
            sa.Enum('PROPOSED', 'APPROVED', 'AUTHORIZED', 'PAID', 'REJECTED', name='payoutstatus', native_enum=False),
            nullable=False,
            server_default='PROPOSED'
        ),
        sa.Column('amount_cents', sa.BigInteger(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('approved_by_user_id', sa.String(length=26), nullable=True),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['approved_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['claim_id'], ['claims.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['policy_id'], ['policies.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for payouts
    op.create_index('ix_payouts_tenant_status', 'payouts', ['tenant_id', 'status'])
    op.create_index('ix_payouts_tenant_created', 'payouts', ['tenant_id', 'created_at'])
    op.create_index('ix_payouts_claim_status', 'payouts', ['claim_id', 'status'])
    op.create_index('ix_payouts_policy_status', 'payouts', ['policy_id', 'status'])
    op.create_index(op.f('ix_payouts_id'), 'payouts', ['id'], unique=False)
    op.create_index(op.f('ix_payouts_tenant_id'), 'payouts', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_payouts_claim_id'), 'payouts', ['claim_id'], unique=False)
    op.create_index(op.f('ix_payouts_policy_id'), 'payouts', ['policy_id'], unique=False)
    op.create_index(op.f('ix_payouts_trigger_event_id'), 'payouts', ['trigger_event_id'], unique=False)
    op.create_index(op.f('ix_payouts_status'), 'payouts', ['status'], unique=False)
    op.create_index(op.f('ix_payouts_currency'), 'payouts', ['currency'], unique=False)
    op.create_index(op.f('ix_payouts_approved_by_user_id'), 'payouts', ['approved_by_user_id'], unique=False)
    op.create_index(op.f('ix_payouts_paid_at'), 'payouts', ['paid_at'], unique=False)


def downgrade() -> None:
    # Drop indexes first
    op.drop_index(op.f('ix_payouts_paid_at'), table_name='payouts')
    op.drop_index(op.f('ix_payouts_approved_by_user_id'), table_name='payouts')
    op.drop_index(op.f('ix_payouts_currency'), table_name='payouts')
    op.drop_index(op.f('ix_payouts_status'), table_name='payouts')
    op.drop_index(op.f('ix_payouts_trigger_event_id'), table_name='payouts')
    op.drop_index(op.f('ix_payouts_policy_id'), table_name='payouts')
    op.drop_index(op.f('ix_payouts_claim_id'), table_name='payouts')
    op.drop_index(op.f('ix_payouts_tenant_id'), table_name='payouts')
    op.drop_index(op.f('ix_payouts_id'), table_name='payouts')
    op.drop_index('ix_payouts_policy_status', table_name='payouts')
    op.drop_index('ix_payouts_claim_status', table_name='payouts')
    op.drop_index('ix_payouts_tenant_created', table_name='payouts')
    op.drop_index('ix_payouts_tenant_status', table_name='payouts')
    
    op.drop_index(op.f('ix_claim_events_actor_id'), table_name='claim_events')
    op.drop_index(op.f('ix_claim_events_actor_type'), table_name='claim_events')
    op.drop_index(op.f('ix_claim_events_event_type'), table_name='claim_events')
    op.drop_index(op.f('ix_claim_events_claim_id'), table_name='claim_events')
    op.drop_index(op.f('ix_claim_events_tenant_id'), table_name='claim_events')
    op.drop_index(op.f('ix_claim_events_id'), table_name='claim_events')
    op.drop_index('ix_claim_events_claim_type', table_name='claim_events')
    op.drop_index('ix_claim_events_tenant_created', table_name='claim_events')
    op.drop_index('ix_claim_events_tenant_claim', table_name='claim_events')
    
    op.drop_index(op.f('ix_claims_created_by_user_id'), table_name='claims')
    op.drop_index(op.f('ix_claims_evidence_bundle_id'), table_name='claims')
    op.drop_index(op.f('ix_claims_risk_run_id'), table_name='claims')
    op.drop_index(op.f('ix_claims_status'), table_name='claims')
    op.drop_index(op.f('ix_claims_policy_id'), table_name='claims')
    op.drop_index(op.f('ix_claims_tenant_id'), table_name='claims')
    op.drop_index(op.f('ix_claims_id'), table_name='claims')
    op.drop_index('ix_claims_policy_status', table_name='claims')
    op.drop_index('ix_claims_tenant_created', table_name='claims')
    op.drop_index('ix_claims_tenant_status', table_name='claims')
    
    # Drop tables
    op.drop_table('payouts')
    op.drop_table('claim_events')
    op.drop_table('claims')
