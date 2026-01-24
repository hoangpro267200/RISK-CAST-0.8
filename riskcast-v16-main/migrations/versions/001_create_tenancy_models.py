"""Create tenancy models

Revision ID: 001_tenancy
Revises: 
Create Date: 2024-12-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '001_tenancy'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create tenants table
    op.create_table(
        'tenants',
        sa.Column('id', sa.String(length=26), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'SUSPENDED', name='tenantstatus', native_enum=False), nullable=False),
        sa.Column('subscription_tier', sa.String(length=100), nullable=True),
        sa.Column('features_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tenants_created_at'), 'tenants', ['created_at'], unique=False)
    op.create_index(op.f('ix_tenants_name'), 'tenants', ['name'], unique=True)
    op.create_index(op.f('ix_tenants_status'), 'tenants', ['status'], unique=False)
    op.create_index(op.f('ix_tenants_updated_at'), 'tenants', ['updated_at'], unique=False)
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=26), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'DISABLED', name='userstatus', native_enum=False), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_created_at'), 'users', ['created_at'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_status'), 'users', ['status'], unique=False)
    op.create_index(op.f('ix_users_updated_at'), 'users', ['updated_at'], unique=False)
    
    # Create roles table
    op.create_table(
        'roles',
        sa.Column('id', sa.String(length=26), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('scope', sa.Enum('TENANT', 'PLATFORM', name='rolescope', native_enum=False), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', 'scope', name='uq_role_name_scope')
    )
    op.create_index(op.f('ix_roles_created_at'), 'roles', ['created_at'], unique=False)
    op.create_index(op.f('ix_roles_name'), 'roles', ['name'], unique=False)
    op.create_index(op.f('ix_roles_scope'), 'roles', ['scope'], unique=False)
    op.create_index(op.f('ix_roles_updated_at'), 'roles', ['updated_at'], unique=False)
    
    # Create permissions table
    op.create_table(
        'permissions',
        sa.Column('id', sa.String(length=26), nullable=False),
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_permissions_created_at'), 'permissions', ['created_at'], unique=False)
    op.create_index(op.f('ix_permissions_key'), 'permissions', ['key'], unique=True)
    op.create_index(op.f('ix_permissions_updated_at'), 'permissions', ['updated_at'], unique=False)
    
    # Create role_permissions table (association)
    op.create_table(
        'role_permissions',
        sa.Column('role_id', sa.String(length=26), nullable=False),
        sa.Column('permission_id', sa.String(length=26), nullable=False),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('role_id', 'permission_id')
    )
    
    # Create memberships table
    op.create_table(
        'memberships',
        sa.Column('id', sa.String(length=26), nullable=False),
        sa.Column('tenant_id', sa.String(length=26), nullable=False),
        sa.Column('user_id', sa.String(length=26), nullable=False),
        sa.Column('role_id', sa.String(length=26), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'INVITED', 'SUSPENDED', name='membershipstatus', native_enum=False), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'user_id', name='uq_membership_tenant_user')
    )
    op.create_index(op.f('ix_memberships_created_at'), 'memberships', ['created_at'], unique=False)
    op.create_index(op.f('ix_memberships_role_id'), 'memberships', ['role_id'], unique=False)
    op.create_index(op.f('ix_memberships_status'), 'memberships', ['status'], unique=False)
    op.create_index(op.f('ix_memberships_tenant_id'), 'memberships', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_memberships_updated_at'), 'memberships', ['updated_at'], unique=False)
    op.create_index(op.f('ix_memberships_user_id'), 'memberships', ['user_id'], unique=False)
    op.create_index('idx_membership_tenant_role', 'memberships', ['tenant_id', 'role_id'], unique=False)


def downgrade() -> None:
    # Drop memberships table
    op.drop_index('idx_membership_tenant_role', table_name='memberships')
    op.drop_index(op.f('ix_memberships_user_id'), table_name='memberships')
    op.drop_index(op.f('ix_memberships_updated_at'), table_name='memberships')
    op.drop_index(op.f('ix_memberships_tenant_id'), table_name='memberships')
    op.drop_index(op.f('ix_memberships_status'), table_name='memberships')
    op.drop_index(op.f('ix_memberships_role_id'), table_name='memberships')
    op.drop_index(op.f('ix_memberships_created_at'), table_name='memberships')
    op.drop_table('memberships')
    
    # Drop role_permissions table
    op.drop_table('role_permissions')
    
    # Drop permissions table
    op.drop_index(op.f('ix_permissions_updated_at'), table_name='permissions')
    op.drop_index(op.f('ix_permissions_key'), table_name='permissions')
    op.drop_index(op.f('ix_permissions_created_at'), table_name='permissions')
    op.drop_table('permissions')
    
    # Drop roles table
    op.drop_index(op.f('ix_roles_updated_at'), table_name='roles')
    op.drop_index(op.f('ix_roles_scope'), table_name='roles')
    op.drop_index(op.f('ix_roles_name'), table_name='roles')
    op.drop_index(op.f('ix_roles_created_at'), table_name='roles')
    op.drop_table('roles')
    
    # Drop users table
    op.drop_index(op.f('ix_users_updated_at'), table_name='users')
    op.drop_index(op.f('ix_users_status'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_created_at'), table_name='users')
    op.drop_table('users')
    
    # Drop tenants table
    op.drop_index(op.f('ix_tenants_updated_at'), table_name='tenants')
    op.drop_index(op.f('ix_tenants_status'), table_name='tenants')
    op.drop_index(op.f('ix_tenants_name'), table_name='tenants')
    op.drop_index(op.f('ix_tenants_created_at'), table_name='tenants')
    op.drop_table('tenants')
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS membershipstatus")
    op.execute("DROP TYPE IF EXISTS rolescope")
    op.execute("DROP TYPE IF EXISTS userstatus")
    op.execute("DROP TYPE IF EXISTS tenantstatus")
