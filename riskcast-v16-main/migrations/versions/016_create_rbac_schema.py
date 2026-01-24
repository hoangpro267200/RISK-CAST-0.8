"""Create RBAC schema with roles, permissions, and role_permissions

Revision ID: 016_rbac
Revises: 015_update_tenancy
Create Date: 2024-12-20

Creates RBAC tables with UUID primary keys and seeds system roles and permissions.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '016_rbac'
down_revision = '015_update_tenancy'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create roles table
    op.create_table(
        'rbac_roles',
        sa.Column('id', sa.String(length=36), nullable=False),  # UUID
        sa.Column('tenant_id', sa.String(length=36), nullable=True),  # UUID (NULL for system roles)
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_system_role', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'name', name='uq_rbac_roles_tenant_name')
    )
    op.create_index('ix_rbac_roles_tenant_id', 'rbac_roles', ['tenant_id'], unique=False)
    op.create_index('ix_rbac_roles_name', 'rbac_roles', ['name'], unique=False)
    op.create_index('ix_rbac_roles_is_system_role', 'rbac_roles', ['is_system_role'], unique=False)
    
    # Create permissions table
    op.create_table(
        'rbac_permissions',
        sa.Column('id', sa.String(length=36), nullable=False),  # UUID
        sa.Column('name', sa.String(length=100), nullable=False, unique=True),
        sa.Column('resource', sa.String(length=100), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_rbac_permissions_name', 'rbac_permissions', ['name'], unique=True)
    op.create_index('ix_rbac_permissions_resource', 'rbac_permissions', ['resource'], unique=False)
    op.create_index('ix_rbac_permissions_action', 'rbac_permissions', ['action'], unique=False)
    
    # Create role_permissions association table
    op.create_table(
        'rbac_role_permissions',
        sa.Column('role_id', sa.String(length=36), nullable=False),
        sa.Column('permission_id', sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(['permission_id'], ['rbac_permissions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['rbac_roles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('role_id', 'permission_id')
    )
    op.create_index('ix_rbac_role_permissions_role_id', 'rbac_role_permissions', ['role_id'], unique=False)
    op.create_index('ix_rbac_role_permissions_permission_id', 'rbac_role_permissions', ['permission_id'], unique=False)
    
    # Seed system roles (using Python UUID generation)
    import uuid
    admin_id = str(uuid.uuid4())
    underwriter_id = str(uuid.uuid4())
    claims_adjuster_id = str(uuid.uuid4())
    viewer_id = str(uuid.uuid4())
    
    op.execute(f"""
        INSERT INTO rbac_roles (id, name, is_system_role, description) VALUES
        ('{admin_id}', 'admin', TRUE, 'Full access'),
        ('{underwriter_id}', 'underwriter', TRUE, 'Underwriting operations'),
        ('{claims_adjuster_id}', 'claims_adjuster', TRUE, 'Claims operations'),
        ('{viewer_id}', 'viewer', TRUE, 'Read-only access')
    """)
    
    # Seed permissions
    risk_read_id = str(uuid.uuid4())
    risk_write_id = str(uuid.uuid4())
    policy_read_id = str(uuid.uuid4())
    policy_bind_id = str(uuid.uuid4())
    claim_read_id = str(uuid.uuid4())
    claim_adjudicate_id = str(uuid.uuid4())
    audit_read_id = str(uuid.uuid4())
    audit_export_id = str(uuid.uuid4())
    
    op.execute(f"""
        INSERT INTO rbac_permissions (id, name, resource, action) VALUES
        ('{risk_read_id}', 'risk:read', 'risk', 'read'),
        ('{risk_write_id}', 'risk:write', 'risk', 'write'),
        ('{policy_read_id}', 'policy:read', 'policy', 'read'),
        ('{policy_bind_id}', 'policy:bind', 'policy', 'bind'),
        ('{claim_read_id}', 'claim:read', 'claim', 'read'),
        ('{claim_adjudicate_id}', 'claim:adjudicate', 'claim', 'adjudicate'),
        ('{audit_read_id}', 'audit:read', 'audit', 'read'),
        ('{audit_export_id}', 'audit:export', 'audit', 'export')
    """)
    
    # Assign permissions to roles
    # Admin gets all permissions
    op.execute(f"""
        INSERT INTO rbac_role_permissions (role_id, permission_id) VALUES
        ('{admin_id}', '{risk_read_id}'),
        ('{admin_id}', '{risk_write_id}'),
        ('{admin_id}', '{policy_read_id}'),
        ('{admin_id}', '{policy_bind_id}'),
        ('{admin_id}', '{claim_read_id}'),
        ('{admin_id}', '{claim_adjudicate_id}'),
        ('{admin_id}', '{audit_read_id}'),
        ('{admin_id}', '{audit_export_id}')
    """)
    
    # Underwriter permissions
    op.execute(f"""
        INSERT INTO rbac_role_permissions (role_id, permission_id) VALUES
        ('{underwriter_id}', '{risk_read_id}'),
        ('{underwriter_id}', '{policy_read_id}'),
        ('{underwriter_id}', '{policy_bind_id}'),
        ('{underwriter_id}', '{audit_read_id}')
    """)
    
    # Claims adjuster permissions
    op.execute(f"""
        INSERT INTO rbac_role_permissions (role_id, permission_id) VALUES
        ('{claims_adjuster_id}', '{claim_read_id}'),
        ('{claims_adjuster_id}', '{claim_adjudicate_id}'),
        ('{claims_adjuster_id}', '{audit_read_id}')
    """)
    
    # Viewer permissions
    op.execute(f"""
        INSERT INTO rbac_role_permissions (role_id, permission_id) VALUES
        ('{viewer_id}', '{risk_read_id}'),
        ('{viewer_id}', '{policy_read_id}'),
        ('{viewer_id}', '{claim_read_id}'),
        ('{viewer_id}', '{audit_read_id}')
    """)


def downgrade() -> None:
    # Drop role_permissions table
    op.drop_index('ix_rbac_role_permissions_permission_id', table_name='rbac_role_permissions')
    op.drop_index('ix_rbac_role_permissions_role_id', table_name='rbac_role_permissions')
    op.drop_table('rbac_role_permissions')
    
    # Drop permissions table
    op.drop_index('ix_rbac_permissions_action', table_name='rbac_permissions')
    op.drop_index('ix_rbac_permissions_resource', table_name='rbac_permissions')
    op.drop_index('ix_rbac_permissions_name', table_name='rbac_permissions')
    op.drop_table('rbac_permissions')
    
    # Drop roles table
    op.drop_index('ix_rbac_roles_is_system_role', table_name='rbac_roles')
    op.drop_index('ix_rbac_roles_name', table_name='rbac_roles')
    op.drop_index('ix_rbac_roles_tenant_id', table_name='rbac_roles')
    op.drop_table('rbac_roles')
