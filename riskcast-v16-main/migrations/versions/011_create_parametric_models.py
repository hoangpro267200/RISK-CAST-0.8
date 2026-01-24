"""Create parametric models

Revision ID: 011_parametric
Revises: 010_claims
Create Date: 2024-12-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '011_parametric'
down_revision = '010_claims'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create trigger_definitions table
    op.create_table(
        'trigger_definitions',
        sa.Column('id', sa.String(length=26), nullable=False),
        sa.Column('tenant_id', sa.String(length=26), nullable=False),
        sa.Column(
            'status',
            sa.Enum('DRAFT', 'PUBLISHED', 'DEPRECATED', name='triggerdefinitionstatus', native_enum=False),
            nullable=False,
            server_default='DRAFT'
        ),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('params_json', sa.JSON(), nullable=False),
        sa.Column('created_by_user_id', sa.String(length=26), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('immutable_hash', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for trigger_definitions
    op.create_index('ix_trigger_def_tenant_type', 'trigger_definitions', ['tenant_id', 'type', 'status'])
    op.create_index(op.f('ix_trigger_definitions_id'), 'trigger_definitions', ['id'], unique=False)
    op.create_index(op.f('ix_trigger_definitions_tenant_id'), 'trigger_definitions', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_trigger_definitions_status'), 'trigger_definitions', ['status'], unique=False)
    op.create_index(op.f('ix_trigger_definitions_type'), 'trigger_definitions', ['type'], unique=False)
    op.create_index(op.f('ix_trigger_definitions_created_by_user_id'), 'trigger_definitions', ['created_by_user_id'], unique=False)
    op.create_index(op.f('ix_trigger_definitions_published_at'), 'trigger_definitions', ['published_at'], unique=False)
    op.create_index(op.f('ix_trigger_definitions_immutable_hash'), 'trigger_definitions', ['immutable_hash'], unique=False)
    
    # Create unique constraint for tenant_id, type, version
    op.create_unique_constraint('uq_trigger_def_tenant_type_version', 'trigger_definitions', ['tenant_id', 'type', 'version'])
    
    # Create oracle_events table
    op.create_table(
        'oracle_events',
        sa.Column('id', sa.String(length=26), nullable=False),
        sa.Column('tenant_id', sa.String(length=26), nullable=True),
        sa.Column('source', sa.String(length=100), nullable=False),
        sa.Column('captured_at', sa.DateTime(), nullable=False),
        sa.Column('payload_json', sa.JSON(), nullable=False),
        sa.Column('payload_hash', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for oracle_events
    op.create_index('ix_oracle_events_source', 'oracle_events', ['tenant_id', 'source', 'captured_at'])
    op.create_index('ix_oracle_events_hash', 'oracle_events', ['payload_hash'])
    op.create_index('ix_oracle_events_tenant_captured', 'oracle_events', ['tenant_id', 'captured_at'])
    op.create_index(op.f('ix_oracle_events_id'), 'oracle_events', ['id'], unique=False)
    op.create_index(op.f('ix_oracle_events_tenant_id'), 'oracle_events', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_oracle_events_source'), 'oracle_events', ['source'], unique=False)
    op.create_index(op.f('ix_oracle_events_captured_at'), 'oracle_events', ['captured_at'], unique=False)
    op.create_index(op.f('ix_oracle_events_payload_hash'), 'oracle_events', ['payload_hash'], unique=False)
    
    # Create trigger_events table
    op.create_table(
        'trigger_events',
        sa.Column('id', sa.String(length=26), nullable=False),
        sa.Column('tenant_id', sa.String(length=26), nullable=False),
        sa.Column('trigger_definition_id', sa.String(length=26), nullable=False),
        sa.Column('policy_id', sa.String(length=26), nullable=False),
        sa.Column(
            'status',
            sa.Enum('DETECTED', 'VALIDATED', 'PROPOSED_PAYOUT', 'APPROVED', 'PAID', 'REJECTED', name='triggereventstatus', native_enum=False),
            nullable=False,
            server_default='DETECTED'
        ),
        sa.Column('matched_at', sa.DateTime(), nullable=True),
        sa.Column('validation_json', sa.JSON(), nullable=True),
        sa.Column('evidence_bundle_id', sa.String(length=26), nullable=True),
        sa.Column('payout_id', sa.String(length=26), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['evidence_bundle_id'], ['evidence_bundles.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['policy_id'], ['policies.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['payout_id'], ['payouts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['trigger_definition_id'], ['trigger_definitions.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for trigger_events
    op.create_index('ix_trigger_events_tenant_status', 'trigger_events', ['tenant_id', 'status'])
    op.create_index('ix_trigger_events_tenant_created', 'trigger_events', ['tenant_id', 'created_at'])
    op.create_index('ix_trigger_events_policy_status', 'trigger_events', ['policy_id', 'status'])
    op.create_index(op.f('ix_trigger_events_id'), 'trigger_events', ['id'], unique=False)
    op.create_index(op.f('ix_trigger_events_tenant_id'), 'trigger_events', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_trigger_events_trigger_definition_id'), 'trigger_events', ['trigger_definition_id'], unique=False)
    op.create_index(op.f('ix_trigger_events_policy_id'), 'trigger_events', ['policy_id'], unique=False)
    op.create_index(op.f('ix_trigger_events_status'), 'trigger_events', ['status'], unique=False)
    op.create_index(op.f('ix_trigger_events_matched_at'), 'trigger_events', ['matched_at'], unique=False)
    op.create_index(op.f('ix_trigger_events_evidence_bundle_id'), 'trigger_events', ['evidence_bundle_id'], unique=False)
    op.create_index(op.f('ix_trigger_events_payout_id'), 'trigger_events', ['payout_id'], unique=False)


def downgrade() -> None:
    # Drop indexes first
    op.drop_index(op.f('ix_trigger_events_payout_id'), table_name='trigger_events')
    op.drop_index(op.f('ix_trigger_events_evidence_bundle_id'), table_name='trigger_events')
    op.drop_index(op.f('ix_trigger_events_matched_at'), table_name='trigger_events')
    op.drop_index(op.f('ix_trigger_events_status'), table_name='trigger_events')
    op.drop_index(op.f('ix_trigger_events_policy_id'), table_name='trigger_events')
    op.drop_index(op.f('ix_trigger_events_trigger_definition_id'), table_name='trigger_events')
    op.drop_index(op.f('ix_trigger_events_tenant_id'), table_name='trigger_events')
    op.drop_index(op.f('ix_trigger_events_id'), table_name='trigger_events')
    op.drop_index('ix_trigger_events_policy_status', table_name='trigger_events')
    op.drop_index('ix_trigger_events_tenant_created', table_name='trigger_events')
    op.drop_index('ix_trigger_events_tenant_status', table_name='trigger_events')
    
    op.drop_index(op.f('ix_oracle_events_payload_hash'), table_name='oracle_events')
    op.drop_index(op.f('ix_oracle_events_captured_at'), table_name='oracle_events')
    op.drop_index(op.f('ix_oracle_events_source'), table_name='oracle_events')
    op.drop_index(op.f('ix_oracle_events_tenant_id'), table_name='oracle_events')
    op.drop_index(op.f('ix_oracle_events_id'), table_name='oracle_events')
    op.drop_index('ix_oracle_events_tenant_captured', table_name='oracle_events')
    op.drop_index('ix_oracle_events_hash', table_name='oracle_events')
    op.drop_index('ix_oracle_events_source', table_name='oracle_events')
    
    op.drop_constraint('uq_trigger_def_tenant_type_version', 'trigger_definitions', type_='unique')
    
    op.drop_index(op.f('ix_trigger_definitions_immutable_hash'), table_name='trigger_definitions')
    op.drop_index(op.f('ix_trigger_definitions_published_at'), table_name='trigger_definitions')
    op.drop_index(op.f('ix_trigger_definitions_created_by_user_id'), table_name='trigger_definitions')
    op.drop_index(op.f('ix_trigger_definitions_type'), table_name='trigger_definitions')
    op.drop_index(op.f('ix_trigger_definitions_status'), table_name='trigger_definitions')
    op.drop_index(op.f('ix_trigger_definitions_tenant_id'), table_name='trigger_definitions')
    op.drop_index(op.f('ix_trigger_definitions_id'), table_name='trigger_definitions')
    op.drop_index('ix_trigger_def_tenant_type', table_name='trigger_definitions')
    
    # Drop tables
    op.drop_table('trigger_events')
    op.drop_table('oracle_events')
    op.drop_table('trigger_definitions')
