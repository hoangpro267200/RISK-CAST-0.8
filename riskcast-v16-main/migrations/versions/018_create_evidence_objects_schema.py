"""Create evidence_objects table with updated schema

Revision ID: 018_evidence_objects
Revises: 017_risk_run_jobs
Create Date: 2024-12-20

Creates evidence_objects table with content hashing and storage references.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '018_evidence_objects'
down_revision = '017_risk_run_jobs'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if evidence_objects table exists
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    table_exists = 'evidence_objects' in inspector.get_table_names()
    
    if not table_exists:
        # Create new table
        op.create_table(
            'evidence_objects',
            sa.Column('id', sa.String(length=36), nullable=False),  # UUID
            sa.Column('tenant_id', sa.String(length=36), nullable=False),  # UUID
            
            # Content identification
            sa.Column('content_hash', sa.String(length=64), nullable=False),  # SHA256
            sa.Column('content_type', sa.String(length=100), nullable=False),  # MIME type
            sa.Column('content_size_bytes', sa.BigInteger(), nullable=True),
            
            # Storage
            sa.Column('storage_uri', sa.Text(), nullable=False),  # s3://bucket/path or file://path
            sa.Column('storage_provider', sa.String(length=50), nullable=False, server_default='local'),
            
            # Metadata
            sa.Column('filename', sa.String(length=255), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('metadata_json', sa.JSON(), nullable=True, server_default='{}'),
            
            # Classification
            sa.Column('evidence_type', sa.String(length=50), nullable=True),  # DOCUMENT, IMAGE, DATA_EXPORT, etc
            sa.Column('is_pii', sa.Boolean(), nullable=False, server_default='0'),  # MySQL uses 0/1 for boolean
            sa.Column('retention_class', sa.String(length=50), nullable=False, server_default='STANDARD'),
            
            # Lifecycle
            sa.Column('created_by_user_id', sa.String(length=36), nullable=True),  # UUID
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('expires_at', sa.DateTime(), nullable=True),
            sa.Column('deleted_at', sa.DateTime(), nullable=True),  # Soft delete
            
            sa.PrimaryKeyConstraint('id')
        )
        
        # Create indexes
        op.create_index('ix_evidence_tenant', 'evidence_objects', ['tenant_id'], unique=False)
        op.create_index('ix_evidence_hash', 'evidence_objects', ['content_hash'], unique=False)
        op.create_index('ix_evidence_created_by', 'evidence_objects', ['created_by_user_id'], unique=False)
        op.create_index('ix_evidence_type', 'evidence_objects', ['evidence_type'], unique=False)
        op.create_index('ix_evidence_deleted_at', 'evidence_objects', ['deleted_at'], unique=False)
    else:
        # Table exists - add missing columns if they don't exist
        existing_columns = [col['name'] for col in inspector.get_columns('evidence_objects')]
        
        # Add new columns if they don't exist
        if 'content_hash' not in existing_columns:
            op.add_column('evidence_objects', sa.Column('content_hash', sa.String(length=64), nullable=True))
        if 'content_type' not in existing_columns:
            op.add_column('evidence_objects', sa.Column('content_type', sa.String(length=100), nullable=True))
        if 'content_size_bytes' not in existing_columns:
            op.add_column('evidence_objects', sa.Column('content_size_bytes', sa.BigInteger(), nullable=True))
        if 'storage_uri' not in existing_columns:
            op.add_column('evidence_objects', sa.Column('storage_uri', sa.Text(), nullable=True))
        if 'storage_provider' not in existing_columns:
            op.add_column('evidence_objects', sa.Column('storage_provider', sa.String(length=50), nullable=True, server_default='local'))
        if 'filename' not in existing_columns:
            op.add_column('evidence_objects', sa.Column('filename', sa.String(length=255), nullable=True))
        if 'description' not in existing_columns:
            op.add_column('evidence_objects', sa.Column('description', sa.Text(), nullable=True))
        if 'metadata_json' not in existing_columns:
            op.add_column('evidence_objects', sa.Column('metadata_json', sa.JSON(), nullable=True, server_default='{}'))
        if 'evidence_type' not in existing_columns:
            op.add_column('evidence_objects', sa.Column('evidence_type', sa.String(length=50), nullable=True))
        if 'is_pii' not in existing_columns:
            op.add_column('evidence_objects', sa.Column('is_pii', sa.Boolean(), nullable=True, server_default='0'))
        if 'retention_class' not in existing_columns:
            op.add_column('evidence_objects', sa.Column('retention_class', sa.String(length=50), nullable=True, server_default='STANDARD'))
        if 'created_by_user_id' not in existing_columns:
            op.add_column('evidence_objects', sa.Column('created_by_user_id', sa.String(length=36), nullable=True))
        if 'expires_at' not in existing_columns:
            op.add_column('evidence_objects', sa.Column('expires_at', sa.DateTime(), nullable=True))
        if 'deleted_at' not in existing_columns:
            op.add_column('evidence_objects', sa.Column('deleted_at', sa.DateTime(), nullable=True))
        
        # Create indexes if they don't exist
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('evidence_objects')]
        
        if 'ix_evidence_tenant' not in existing_indexes:
            op.create_index('ix_evidence_tenant', 'evidence_objects', ['tenant_id'], unique=False)
        if 'ix_evidence_hash' not in existing_indexes:
            op.create_index('ix_evidence_hash', 'evidence_objects', ['content_hash'], unique=False)
        if 'ix_evidence_created_by' not in existing_indexes:
            op.create_index('ix_evidence_created_by', 'evidence_objects', ['created_by_user_id'], unique=False)
        if 'ix_evidence_type' not in existing_indexes:
            op.create_index('ix_evidence_type', 'evidence_objects', ['evidence_type'], unique=False)
        if 'ix_evidence_deleted_at' not in existing_indexes:
            op.create_index('ix_evidence_deleted_at', 'evidence_objects', ['deleted_at'], unique=False)


def downgrade() -> None:
    # Drop indexes
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    
    if 'evidence_objects' in inspector.get_table_names():
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('evidence_objects')]
        
        if 'ix_evidence_deleted_at' in existing_indexes:
            op.drop_index('ix_evidence_deleted_at', table_name='evidence_objects')
        if 'ix_evidence_type' in existing_indexes:
            op.drop_index('ix_evidence_type', table_name='evidence_objects')
        if 'ix_evidence_created_by' in existing_indexes:
            op.drop_index('ix_evidence_created_by', table_name='evidence_objects')
        if 'ix_evidence_hash' in existing_indexes:
            op.drop_index('ix_evidence_hash', table_name='evidence_objects')
        if 'ix_evidence_tenant' in existing_indexes:
            op.drop_index('ix_evidence_tenant', table_name='evidence_objects')
        
        # Note: We don't drop the table or columns in downgrade to preserve data
        # If full rollback is needed, manually drop columns
