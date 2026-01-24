"""Create model_versioning models

Revision ID: 007_model_versioning
Revises: 006_seed_roles_permissions
Create Date: 2024-12-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '007_model_versioning'
down_revision = '006_seed_roles_permissions'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create risk_model_versions table
    op.create_table(
        'risk_model_versions',
        sa.Column('id', sa.String(length=26), nullable=False),
        sa.Column('tenant_id', sa.String(length=26), nullable=True),
        sa.Column('scope', sa.Enum('GLOBAL', 'TENANT', name='modelscope', native_enum=False), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column(
            'status',
            sa.Enum('DRAFT', 'PUBLISHED', 'DEPRECATED', name='modelversionstatus', native_enum=False),
            nullable=False,
            server_default='DRAFT'
        ),
        sa.Column('model_schema_version', sa.String(length=50), nullable=False),
        sa.Column('weights_json', sa.JSON(), nullable=False),
        sa.Column('calibration_json', sa.JSON(), nullable=True),
        sa.Column('constraints_json', sa.JSON(), nullable=True),
        sa.Column('metrics_json', sa.JSON(), nullable=True),
        sa.Column('created_by_user_id', sa.String(length=26), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('immutable_hash', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for risk_model_versions
    op.create_index('ix_model_versions_status_published', 'risk_model_versions', ['status', 'published_at'])
    op.create_index('ix_model_versions_tenant_status', 'risk_model_versions', ['tenant_id', 'status'])
    op.create_index('ix_model_versions_scope_status', 'risk_model_versions', ['scope', 'status'])
    op.create_index(op.f('ix_risk_model_versions_id'), 'risk_model_versions', ['id'], unique=False)
    op.create_index(op.f('ix_risk_model_versions_name'), 'risk_model_versions', ['name'], unique=False)
    op.create_index(op.f('ix_risk_model_versions_tenant_id'), 'risk_model_versions', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_risk_model_versions_status'), 'risk_model_versions', ['status'], unique=False)
    op.create_index(op.f('ix_risk_model_versions_scope'), 'risk_model_versions', ['scope'], unique=False)
    op.create_index(op.f('ix_risk_model_versions_created_by_user_id'), 'risk_model_versions', ['created_by_user_id'], unique=False)
    op.create_index(op.f('ix_risk_model_versions_published_at'), 'risk_model_versions', ['published_at'], unique=False)
    op.create_index(op.f('ix_risk_model_versions_immutable_hash'), 'risk_model_versions', ['immutable_hash'], unique=False)
    
    # Create risk_model_activations table
    op.create_table(
        'risk_model_activations',
        sa.Column('id', sa.String(length=26), nullable=False),
        sa.Column('tenant_id', sa.String(length=26), nullable=False),
        sa.Column('corridor_id', sa.String(length=100), nullable=True),
        sa.Column('product_type', sa.String(length=100), nullable=False),
        sa.Column('model_version_id', sa.String(length=26), nullable=False),
        sa.Column('effective_from', sa.DateTime(), nullable=False),
        sa.Column('effective_to', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['model_version_id'], ['risk_model_versions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for risk_model_activations
    op.create_index('ix_activations_lookup', 'risk_model_activations', ['tenant_id', 'corridor_id', 'product_type', 'effective_from'])
    op.create_index('ix_activations_tenant_model', 'risk_model_activations', ['tenant_id', 'model_version_id'])
    op.create_index('ix_activations_effective', 'risk_model_activations', ['effective_from', 'effective_to'])
    op.create_index(op.f('ix_risk_model_activations_id'), 'risk_model_activations', ['id'], unique=False)
    op.create_index(op.f('ix_risk_model_activations_tenant_id'), 'risk_model_activations', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_risk_model_activations_corridor_id'), 'risk_model_activations', ['corridor_id'], unique=False)
    op.create_index(op.f('ix_risk_model_activations_product_type'), 'risk_model_activations', ['product_type'], unique=False)
    op.create_index(op.f('ix_risk_model_activations_model_version_id'), 'risk_model_activations', ['model_version_id'], unique=False)
    op.create_index(op.f('ix_risk_model_activations_effective_from'), 'risk_model_activations', ['effective_from'], unique=False)
    op.create_index(op.f('ix_risk_model_activations_effective_to'), 'risk_model_activations', ['effective_to'], unique=False)


def downgrade() -> None:
    # Drop indexes first
    op.drop_index(op.f('ix_risk_model_activations_effective_to'), table_name='risk_model_activations')
    op.drop_index(op.f('ix_risk_model_activations_effective_from'), table_name='risk_model_activations')
    op.drop_index(op.f('ix_risk_model_activations_model_version_id'), table_name='risk_model_activations')
    op.drop_index(op.f('ix_risk_model_activations_product_type'), table_name='risk_model_activations')
    op.drop_index(op.f('ix_risk_model_activations_corridor_id'), table_name='risk_model_activations')
    op.drop_index(op.f('ix_risk_model_activations_tenant_id'), table_name='risk_model_activations')
    op.drop_index(op.f('ix_risk_model_activations_id'), table_name='risk_model_activations')
    op.drop_index('ix_activations_effective', table_name='risk_model_activations')
    op.drop_index('ix_activations_tenant_model', table_name='risk_model_activations')
    op.drop_index('ix_activations_lookup', table_name='risk_model_activations')
    
    op.drop_index(op.f('ix_risk_model_versions_immutable_hash'), table_name='risk_model_versions')
    op.drop_index(op.f('ix_risk_model_versions_published_at'), table_name='risk_model_versions')
    op.drop_index(op.f('ix_risk_model_versions_created_by_user_id'), table_name='risk_model_versions')
    op.drop_index(op.f('ix_risk_model_versions_scope'), table_name='risk_model_versions')
    op.drop_index(op.f('ix_risk_model_versions_status'), table_name='risk_model_versions')
    op.drop_index(op.f('ix_risk_model_versions_tenant_id'), table_name='risk_model_versions')
    op.drop_index(op.f('ix_risk_model_versions_name'), table_name='risk_model_versions')
    op.drop_index(op.f('ix_risk_model_versions_id'), table_name='risk_model_versions')
    op.drop_index('ix_model_versions_scope_status', table_name='risk_model_versions')
    op.drop_index('ix_model_versions_tenant_status', table_name='risk_model_versions')
    op.drop_index('ix_model_versions_status_published', table_name='risk_model_versions')
    
    # Drop tables
    op.drop_table('risk_model_activations')
    op.drop_table('risk_model_versions')
