"""Create risk_assessments models

Revision ID: 004_risk_assessments
Revises: 003_identity_access
Create Date: 2024-12-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '004_risk_assessments'
down_revision = '003_identity_access'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create risk_assessments table
    op.create_table(
        'risk_assessments',
        sa.Column('id', sa.String(length=26), nullable=False),
        sa.Column('tenant_id', sa.String(length=26), nullable=False),
        sa.Column('created_by_user_id', sa.String(length=26), nullable=True),
        sa.Column(
            'status',
            sa.Enum('DRAFT', 'READY', 'ARCHIVED', name='assessmentstatus', native_enum=False),
            nullable=False,
            server_default='DRAFT'
        ),
        sa.Column('input_schema_version', sa.String(length=50), nullable=False),
        sa.Column('input_snapshot_json', sa.JSON(), nullable=False),
        sa.Column('input_hash', sa.String(length=64), nullable=False),
        sa.Column('shipment_id', sa.String(length=26), nullable=True),
        sa.Column('corridor_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ondelete='SET NULL')
    )
    
    # Create indexes
    op.create_index(
        op.f('ix_risk_assessments_tenant_id'),
        'risk_assessments',
        ['tenant_id'],
        unique=False
    )
    op.create_index(
        op.f('ix_risk_assessments_created_at'),
        'risk_assessments',
        ['created_at'],
        unique=False
    )
    op.create_index(
        op.f('ix_risk_assessments_updated_at'),
        'risk_assessments',
        ['updated_at'],
        unique=False
    )
    op.create_index(
        op.f('ix_risk_assessments_created_by_user_id'),
        'risk_assessments',
        ['created_by_user_id'],
        unique=False
    )
    op.create_index(
        op.f('ix_risk_assessments_status'),
        'risk_assessments',
        ['status'],
        unique=False
    )
    op.create_index(
        op.f('ix_risk_assessments_input_hash'),
        'risk_assessments',
        ['input_hash'],
        unique=False
    )
    op.create_index(
        op.f('ix_risk_assessments_shipment_id'),
        'risk_assessments',
        ['shipment_id'],
        unique=False
    )
    op.create_index(
        op.f('ix_risk_assessments_corridor_id'),
        'risk_assessments',
        ['corridor_id'],
        unique=False
    )
    
    # Create composite indexes
    op.create_index(
        'ix_risk_assessments_tenant_created',
        'risk_assessments',
        ['tenant_id', 'created_at'],
        unique=False
    )
    op.create_index(
        'ix_risk_assessments_tenant_hash',
        'risk_assessments',
        ['tenant_id', 'input_hash'],
        unique=False
    )
    op.create_index(
        'ix_risk_assessments_tenant_status',
        'risk_assessments',
        ['tenant_id', 'status'],
        unique=False
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_risk_assessments_tenant_status', table_name='risk_assessments')
    op.drop_index('ix_risk_assessments_tenant_hash', table_name='risk_assessments')
    op.drop_index('ix_risk_assessments_tenant_created', table_name='risk_assessments')
    op.drop_index(op.f('ix_risk_assessments_corridor_id'), table_name='risk_assessments')
    op.drop_index(op.f('ix_risk_assessments_shipment_id'), table_name='risk_assessments')
    op.drop_index(op.f('ix_risk_assessments_input_hash'), table_name='risk_assessments')
    op.drop_index(op.f('ix_risk_assessments_status'), table_name='risk_assessments')
    op.drop_index(op.f('ix_risk_assessments_created_by_user_id'), table_name='risk_assessments')
    op.drop_index(op.f('ix_risk_assessments_updated_at'), table_name='risk_assessments')
    op.drop_index(op.f('ix_risk_assessments_created_at'), table_name='risk_assessments')
    op.drop_index(op.f('ix_risk_assessments_tenant_id'), table_name='risk_assessments')
    
    # Drop table
    op.drop_table('risk_assessments')
