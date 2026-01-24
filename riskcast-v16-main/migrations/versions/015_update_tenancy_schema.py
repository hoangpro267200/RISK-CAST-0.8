"""Create/update tenancy schema with UUID and required fields

Revision ID: 015_update_tenancy
Revises: 014_create_risk_runs
Create Date: 2024-12-20

Creates tenants and memberships tables with UUID primary keys,
or updates existing tables to add missing fields (slug, settings_json, role).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '015_update_tenancy'
down_revision = '014_create_risk_runs'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if tenants table exists
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    tables = inspector.get_table_names()
    
    if 'tenants' not in tables:
        # Create tenants table from scratch with UUID
        op.create_table(
            'tenants',
            sa.Column('id', sa.String(length=36), nullable=False),  # UUID
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('slug', sa.String(length=100), nullable=True, unique=True),
            sa.Column('status', sa.Enum('ACTIVE', 'SUSPENDED', name='tenantstatus', native_enum=False), nullable=False, server_default='ACTIVE'),
            sa.Column('settings_json', sa.JSON(), nullable=True, server_default='{}'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_tenants_name', 'tenants', ['name'], unique=False)
        op.create_index('ix_tenants_slug', 'tenants', ['slug'], unique=True)
        op.create_index('ix_tenants_status', 'tenants', ['status'], unique=False)
        op.create_index('ix_tenants_created_at', 'tenants', ['created_at'], unique=False)
    else:
        # Add missing columns to existing tenants table
        columns = [col['name'] for col in inspector.get_columns('tenants')]
        
        if 'slug' not in columns:
            op.add_column('tenants', sa.Column('slug', sa.String(length=100), nullable=True))
            op.create_index('ix_tenants_slug', 'tenants', ['slug'], unique=True)
        
        if 'settings_json' not in columns:
            op.add_column('tenants', sa.Column('settings_json', sa.JSON(), nullable=True, server_default='{}'))
    
    # Check if memberships table exists
    if 'memberships' not in tables:
        # Create memberships table from scratch with UUID
        op.create_table(
            'memberships',
            sa.Column('id', sa.String(length=36), nullable=False),  # UUID
            sa.Column('tenant_id', sa.String(length=36), nullable=False),  # UUID (FK to tenants.id)
            sa.Column('user_id', sa.String(length=36), nullable=False),  # UUID (FK to users.id)
            sa.Column('role', sa.String(length=50), nullable=False, server_default='member'),
            sa.Column('status', sa.Enum('ACTIVE', 'INVITED', 'SUSPENDED', name='membershipstatus', native_enum=False), nullable=False, server_default='ACTIVE'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('tenant_id', 'user_id', name='uq_membership_tenant_user')
        )
        op.create_index('ix_memberships_user', 'memberships', ['user_id'], unique=False)
        op.create_index('ix_memberships_tenant', 'memberships', ['tenant_id'], unique=False)
        op.create_index('ix_memberships_role', 'memberships', ['role'], unique=False)
        op.create_index('ix_memberships_status', 'memberships', ['status'], unique=False)
        op.create_index('ix_memberships_created_at', 'memberships', ['created_at'], unique=False)
    else:
        # Add missing columns to existing memberships table
        columns = [col['name'] for col in inspector.get_columns('memberships')]
        
        if 'role' not in columns:
            op.add_column('memberships', sa.Column('role', sa.String(length=50), nullable=True, server_default='member'))
            op.create_index('ix_memberships_role', 'memberships', ['role'], unique=False)


def downgrade() -> None:
    # Remove role column from memberships if it exists
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    if 'memberships' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('memberships')]
        if 'role' in columns:
            try:
                op.drop_index('ix_memberships_role', table_name='memberships')
                op.drop_column('memberships', 'role')
            except Exception:
                pass
    
    # Remove settings_json and slug from tenants if they exist
    if 'tenants' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('tenants')]
        if 'settings_json' in columns:
            try:
                op.drop_column('tenants', 'settings_json')
            except Exception:
                pass
        if 'slug' in columns:
            try:
                op.drop_index('ix_tenants_slug', table_name='tenants')
                op.drop_column('tenants', 'slug')
            except Exception:
                pass
