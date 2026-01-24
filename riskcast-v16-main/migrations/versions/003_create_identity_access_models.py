"""Create identity access models

Revision ID: 003_identity_access
Revises: 002_audit_ledger
Create Date: 2024-12-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '003_identity_access'
down_revision = '002_audit_ledger'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create sessions table
    op.create_table(
        'sessions',
        sa.Column('id', sa.String(length=26), nullable=False),
        sa.Column('user_id', sa.String(length=26), nullable=False),
        sa.Column('token_hash', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for sessions
    op.create_index(op.f('ix_sessions_created_at'), 'sessions', ['created_at'], unique=False)
    op.create_index(op.f('ix_sessions_user_id'), 'sessions', ['user_id'], unique=False)
    op.create_index(op.f('ix_sessions_expires_at'), 'sessions', ['expires_at'], unique=False)
    op.create_index(op.f('ix_sessions_token_hash'), 'sessions', ['token_hash'], unique=True)
    op.create_index(op.f('ix_sessions_updated_at'), 'sessions', ['updated_at'], unique=False)
    op.create_index('idx_sessions_user_expires', 'sessions', ['user_id', 'expires_at'], unique=False)
    
    # Create api_keys table
    op.create_table(
        'api_keys',
        sa.Column('id', sa.String(length=26), nullable=False),
        sa.Column('tenant_id', sa.String(length=26), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('key_hash', sa.String(length=255), nullable=False),
        sa.Column('key_prefix', sa.String(length=10), nullable=False),
        sa.Column('scopes_json', sa.JSON(), nullable=True),
        sa.Column('status', sa.Enum('ACTIVE', 'REVOKED', name='apikeystatus', native_enum=False), nullable=False),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_by_user_id', sa.String(length=26), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for api_keys
    op.create_index(op.f('ix_api_keys_created_at'), 'api_keys', ['created_at'], unique=False)
    op.create_index(op.f('ix_api_keys_key_hash'), 'api_keys', ['key_hash'], unique=True)
    op.create_index(op.f('ix_api_keys_key_prefix'), 'api_keys', ['key_prefix'], unique=False)
    op.create_index(op.f('ix_api_keys_name'), 'api_keys', ['name'], unique=False)
    op.create_index(op.f('ix_api_keys_status'), 'api_keys', ['status'], unique=False)
    op.create_index(op.f('ix_api_keys_tenant_id'), 'api_keys', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_api_keys_updated_at'), 'api_keys', ['updated_at'], unique=False)
    op.create_index(op.f('ix_api_keys_expires_at'), 'api_keys', ['expires_at'], unique=False)
    op.create_index('idx_api_keys_tenant_status', 'api_keys', ['tenant_id', 'status'], unique=False)


def downgrade() -> None:
    # Drop api_keys table
    op.drop_index('idx_api_keys_tenant_status', table_name='api_keys')
    op.drop_index(op.f('ix_api_keys_expires_at'), table_name='api_keys')
    op.drop_index(op.f('ix_api_keys_updated_at'), table_name='api_keys')
    op.drop_index(op.f('ix_api_keys_tenant_id'), table_name='api_keys')
    op.drop_index(op.f('ix_api_keys_status'), table_name='api_keys')
    op.drop_index(op.f('ix_api_keys_name'), table_name='api_keys')
    op.drop_index(op.f('ix_api_keys_key_prefix'), table_name='api_keys')
    op.drop_index(op.f('ix_api_keys_key_hash'), table_name='api_keys')
    op.drop_index(op.f('ix_api_keys_created_at'), table_name='api_keys')
    op.drop_table('api_keys')
    
    # Drop sessions table
    op.drop_index('idx_sessions_user_expires', table_name='sessions')
    op.drop_index(op.f('ix_sessions_updated_at'), table_name='sessions')
    op.drop_index(op.f('ix_sessions_token_hash'), table_name='sessions')
    op.drop_index(op.f('ix_sessions_expires_at'), table_name='sessions')
    op.drop_index(op.f('ix_sessions_user_id'), table_name='sessions')
    op.drop_index(op.f('ix_sessions_created_at'), table_name='sessions')
    op.drop_table('sessions')
    
    # Drop enum type
    op.execute("DROP TYPE IF EXISTS apikeystatus")
