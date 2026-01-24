"""Create evidence models

Revision ID: 008_evidence
Revises: 007_model_versioning
Create Date: 2024-12-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '008_evidence'
down_revision = '007_model_versioning'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create evidence_objects table
    op.create_table(
        'evidence_objects',
        sa.Column('id', sa.String(length=26), nullable=False),
        sa.Column('tenant_id', sa.String(length=26), nullable=False),
        sa.Column(
            'type',
            sa.Enum('DOCUMENT', 'WEATHER_SNAPSHOT', 'SENSOR_SEGMENT', 'PORT_EVENT', 'IMAGE', 'VIDEO', name='evidencetype', native_enum=False),
            nullable=False
        ),
        sa.Column('source', sa.String(length=100), nullable=False),
        sa.Column('storage_uri', sa.String(length=500), nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('size_bytes', sa.BigInteger(), nullable=True),
        sa.Column('captured_at', sa.DateTime(), nullable=True),
        sa.Column('ingested_at', sa.DateTime(), nullable=False),
        sa.Column(
            'retention_class',
            sa.Enum('STANDARD', 'REGULATORY', 'LEGAL_HOLD', name='retentionclass', native_enum=False),
            nullable=False,
            server_default='STANDARD'
        ),
        sa.Column('pii_flags_json', sa.JSON(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for evidence_objects
    op.create_index('ix_evidence_tenant_type', 'evidence_objects', ['tenant_id', 'type', 'captured_at'])
    op.create_index('ix_evidence_tenant_hash', 'evidence_objects', ['tenant_id', 'content_hash'])
    op.create_index('ix_evidence_tenant_source', 'evidence_objects', ['tenant_id', 'source'])
    op.create_index(op.f('ix_evidence_objects_id'), 'evidence_objects', ['id'], unique=False)
    op.create_index(op.f('ix_evidence_objects_tenant_id'), 'evidence_objects', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_evidence_objects_type'), 'evidence_objects', ['type'], unique=False)
    op.create_index(op.f('ix_evidence_objects_source'), 'evidence_objects', ['source'], unique=False)
    op.create_index(op.f('ix_evidence_objects_content_hash'), 'evidence_objects', ['content_hash'], unique=False)
    op.create_index(op.f('ix_evidence_objects_captured_at'), 'evidence_objects', ['captured_at'], unique=False)
    op.create_index(op.f('ix_evidence_objects_ingested_at'), 'evidence_objects', ['ingested_at'], unique=False)
    op.create_index(op.f('ix_evidence_objects_retention_class'), 'evidence_objects', ['retention_class'], unique=False)
    
    # Create evidence_links table
    op.create_table(
        'evidence_links',
        sa.Column('id', sa.String(length=26), nullable=False),
        sa.Column('tenant_id', sa.String(length=26), nullable=False),
        sa.Column('evidence_id', sa.String(length=26), nullable=False),
        sa.Column('resource_type', sa.String(length=100), nullable=False),
        sa.Column('resource_id', sa.String(length=100), nullable=False),
        sa.Column('relationship_type', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['evidence_id'], ['evidence_objects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for evidence_links
    op.create_index('ix_evidence_links_resource', 'evidence_links', ['tenant_id', 'resource_type', 'resource_id'])
    op.create_index('ix_evidence_links_evidence', 'evidence_links', ['evidence_id', 'resource_type'])
    op.create_index(op.f('ix_evidence_links_id'), 'evidence_links', ['id'], unique=False)
    op.create_index(op.f('ix_evidence_links_tenant_id'), 'evidence_links', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_evidence_links_evidence_id'), 'evidence_links', ['evidence_id'], unique=False)
    op.create_index(op.f('ix_evidence_links_resource_type'), 'evidence_links', ['resource_type'], unique=False)
    op.create_index(op.f('ix_evidence_links_resource_id'), 'evidence_links', ['resource_id'], unique=False)
    op.create_index(op.f('ix_evidence_links_relationship_type'), 'evidence_links', ['relationship_type'], unique=False)
    
    # Create evidence_bundles table
    op.create_table(
        'evidence_bundles',
        sa.Column('id', sa.String(length=26), nullable=False),
        sa.Column('tenant_id', sa.String(length=26), nullable=False),
        sa.Column('schema_version', sa.String(length=50), nullable=False),
        sa.Column('manifest_json', sa.JSON(), nullable=False),
        sa.Column('bundle_hash', sa.String(length=64), nullable=False),
        sa.Column('created_by_user_id', sa.String(length=26), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for evidence_bundles
    op.create_index('ix_bundles_tenant_created', 'evidence_bundles', ['tenant_id', 'created_at'])
    op.create_index('ix_bundles_tenant_hash', 'evidence_bundles', ['tenant_id', 'bundle_hash'])
    op.create_index(op.f('ix_evidence_bundles_id'), 'evidence_bundles', ['id'], unique=False)
    op.create_index(op.f('ix_evidence_bundles_tenant_id'), 'evidence_bundles', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_evidence_bundles_bundle_hash'), 'evidence_bundles', ['bundle_hash'], unique=False)
    op.create_index(op.f('ix_evidence_bundles_created_by_user_id'), 'evidence_bundles', ['created_by_user_id'], unique=False)


def downgrade() -> None:
    # Drop indexes first
    op.drop_index(op.f('ix_evidence_bundles_created_by_user_id'), table_name='evidence_bundles')
    op.drop_index(op.f('ix_evidence_bundles_bundle_hash'), table_name='evidence_bundles')
    op.drop_index(op.f('ix_evidence_bundles_tenant_id'), table_name='evidence_bundles')
    op.drop_index(op.f('ix_evidence_bundles_id'), table_name='evidence_bundles')
    op.drop_index('ix_bundles_tenant_hash', table_name='evidence_bundles')
    op.drop_index('ix_bundles_tenant_created', table_name='evidence_bundles')
    
    op.drop_index(op.f('ix_evidence_links_relationship_type'), table_name='evidence_links')
    op.drop_index(op.f('ix_evidence_links_resource_id'), table_name='evidence_links')
    op.drop_index(op.f('ix_evidence_links_resource_type'), table_name='evidence_links')
    op.drop_index(op.f('ix_evidence_links_evidence_id'), table_name='evidence_links')
    op.drop_index(op.f('ix_evidence_links_tenant_id'), table_name='evidence_links')
    op.drop_index(op.f('ix_evidence_links_id'), table_name='evidence_links')
    op.drop_index('ix_evidence_links_evidence', table_name='evidence_links')
    op.drop_index('ix_evidence_links_resource', table_name='evidence_links')
    
    op.drop_index(op.f('ix_evidence_objects_retention_class'), table_name='evidence_objects')
    op.drop_index(op.f('ix_evidence_objects_ingested_at'), table_name='evidence_objects')
    op.drop_index(op.f('ix_evidence_objects_captured_at'), table_name='evidence_objects')
    op.drop_index(op.f('ix_evidence_objects_content_hash'), table_name='evidence_objects')
    op.drop_index(op.f('ix_evidence_objects_source'), table_name='evidence_objects')
    op.drop_index(op.f('ix_evidence_objects_type'), table_name='evidence_objects')
    op.drop_index(op.f('ix_evidence_objects_tenant_id'), table_name='evidence_objects')
    op.drop_index(op.f('ix_evidence_objects_id'), table_name='evidence_objects')
    op.drop_index('ix_evidence_tenant_source', table_name='evidence_objects')
    op.drop_index('ix_evidence_tenant_hash', table_name='evidence_objects')
    op.drop_index('ix_evidence_tenant_type', table_name='evidence_objects')
    
    # Drop tables
    op.drop_table('evidence_bundles')
    op.drop_table('evidence_links')
    op.drop_table('evidence_objects')
