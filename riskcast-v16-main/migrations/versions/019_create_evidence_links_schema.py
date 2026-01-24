"""Create evidence_links table with updated schema

Revision ID: 019_evidence_links
Revises: 018_evidence_objects
Create Date: 2024-12-20

Creates evidence_links table for linking evidence to entities with polymorphic relationships.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '019_evidence_links'
down_revision = '018_evidence_objects'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if evidence_links table exists
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    table_exists = 'evidence_links' in inspector.get_table_names()
    
    if not table_exists:
        # Create new table
        op.create_table(
            'evidence_links',
            sa.Column('id', sa.String(length=36), nullable=False),  # UUID
            sa.Column('tenant_id', sa.String(length=36), nullable=False),  # UUID
            
            # Evidence reference
            sa.Column('evidence_id', sa.String(length=36), nullable=False),  # UUID (FK to evidence_objects.id)
            
            # Polymorphic link
            sa.Column('entity_type', sa.String(length=100), nullable=False),  # risk_assessment, risk_run, policy, claim, trigger_event
            sa.Column('entity_id', sa.String(length=36), nullable=False),  # UUID
            
            # Link metadata
            sa.Column('link_type', sa.String(length=50), nullable=False, server_default='ATTACHMENT'),  # ATTACHMENT, SOURCE_DATA, DECISION_BASIS, OUTPUT
            sa.Column('description', sa.Text(), nullable=True),
            
            # Timing
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            
            sa.ForeignKeyConstraint(['evidence_id'], ['evidence_objects.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('evidence_id', 'entity_type', 'entity_id', name='uq_evidence_links_unique')
        )
        
        # Create indexes
        op.create_index('ix_evidence_links_entity', 'evidence_links', ['entity_type', 'entity_id'], unique=False)
        op.create_index('ix_evidence_links_evidence', 'evidence_links', ['evidence_id'], unique=False)
        op.create_index('ix_evidence_links_tenant', 'evidence_links', ['tenant_id'], unique=False)
        op.create_index('ix_evidence_links_link_type', 'evidence_links', ['link_type'], unique=False)
    else:
        # Table exists - check and add/update columns
        existing_columns = [col['name'] for col in inspector.get_columns('evidence_links')]
        
        # Rename columns if they exist with old names
        if 'resource_type' in existing_columns and 'entity_type' not in existing_columns:
            op.alter_column('evidence_links', 'resource_type', new_column_name='entity_type')
        elif 'entity_type' not in existing_columns:
            op.add_column('evidence_links', sa.Column('entity_type', sa.String(length=100), nullable=True))
            # Migrate data if resource_type exists
            if 'resource_type' in existing_columns:
                op.execute("UPDATE evidence_links SET entity_type = resource_type WHERE entity_type IS NULL")
            op.alter_column('evidence_links', 'entity_type', nullable=False)
        
        if 'resource_id' in existing_columns and 'entity_id' not in existing_columns:
            op.alter_column('evidence_links', 'resource_id', new_column_name='entity_id')
        elif 'entity_id' not in existing_columns:
            op.add_column('evidence_links', sa.Column('entity_id', sa.String(length=36), nullable=True))
            # Migrate data if resource_id exists
            if 'resource_id' in existing_columns:
                op.execute("UPDATE evidence_links SET entity_id = resource_id WHERE entity_id IS NULL")
            op.alter_column('evidence_links', 'entity_id', nullable=False)
        
        if 'relationship_type' in existing_columns and 'link_type' not in existing_columns:
            op.alter_column('evidence_links', 'relationship_type', new_column_name='link_type')
        elif 'link_type' not in existing_columns:
            op.add_column('evidence_links', sa.Column('link_type', sa.String(length=50), nullable=True, server_default='ATTACHMENT'))
            # Migrate data if relationship_type exists
            if 'relationship_type' in existing_columns:
                op.execute("UPDATE evidence_links SET link_type = relationship_type WHERE link_type IS NULL")
            op.alter_column('evidence_links', 'link_type', nullable=False)
        
        # Add description if missing
        if 'description' not in existing_columns:
            op.add_column('evidence_links', sa.Column('description', sa.Text(), nullable=True))
        
        # Update column types if needed (ULID to UUID)
        # Check if id is String(26) and update to String(36)
        id_col = next((col for col in inspector.get_columns('evidence_links') if col['name'] == 'id'), None)
        if id_col and id_col['type'].length == 26:
            # Note: This is a destructive operation - in production, you'd want to migrate data
            # For now, we'll just note that the column should be updated
            pass  # Skip auto-migration of ID type to avoid data loss
        
        # Update tenant_id if needed
        tenant_col = next((col for col in inspector.get_columns('evidence_links') if col['name'] == 'tenant_id'), None)
        if tenant_col and tenant_col['type'].length == 26:
            pass  # Skip auto-migration to avoid data loss
        
        # Update evidence_id if needed
        evidence_col = next((col for col in inspector.get_columns('evidence_links') if col['name'] == 'evidence_id'), None)
        if evidence_col and evidence_col['type'].length == 26:
            pass  # Skip auto-migration to avoid data loss
        
        # Create/update unique constraint
        existing_constraints = [c['name'] for c in inspector.get_unique_constraints('evidence_links')]
        if 'uq_evidence_links_unique' not in existing_constraints:
            # Check if old unique constraint exists
            old_constraint = next((c for c in inspector.get_unique_constraints('evidence_links') 
                                 if set(c['column_names']) == {'evidence_id', 'entity_type', 'entity_id'}), None)
            if not old_constraint:
                try:
                    op.create_unique_constraint('uq_evidence_links_unique', 'evidence_links', 
                                              ['evidence_id', 'entity_type', 'entity_id'])
                except Exception:
                    # Constraint might already exist with different name
                    pass
        
        # Create/update indexes
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('evidence_links')]
        
        if 'ix_evidence_links_entity' not in existing_indexes:
            op.create_index('ix_evidence_links_entity', 'evidence_links', ['entity_type', 'entity_id'], unique=False)
        if 'ix_evidence_links_evidence' not in existing_indexes:
            op.create_index('ix_evidence_links_evidence', 'evidence_links', ['evidence_id'], unique=False)
        if 'ix_evidence_links_tenant' not in existing_indexes:
            op.create_index('ix_evidence_links_tenant', 'evidence_links', ['tenant_id'], unique=False)
        if 'ix_evidence_links_link_type' not in existing_indexes:
            op.create_index('ix_evidence_links_link_type', 'evidence_links', ['link_type'], unique=False)


def downgrade() -> None:
    # Drop indexes
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    
    if 'evidence_links' in inspector.get_table_names():
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('evidence_links')]
        
        if 'ix_evidence_links_link_type' in existing_indexes:
            op.drop_index('ix_evidence_links_link_type', table_name='evidence_links')
        if 'ix_evidence_links_tenant' in existing_indexes:
            op.drop_index('ix_evidence_links_tenant', table_name='evidence_links')
        if 'ix_evidence_links_evidence' in existing_indexes:
            op.drop_index('ix_evidence_links_evidence', table_name='evidence_links')
        if 'ix_evidence_links_entity' in existing_indexes:
            op.drop_index('ix_evidence_links_entity', table_name='evidence_links')
        
        # Drop unique constraint
        existing_constraints = [c['name'] for c in inspector.get_unique_constraints('evidence_links')]
        if 'uq_evidence_links_unique' in existing_constraints:
            op.drop_constraint('uq_evidence_links_unique', 'evidence_links', type_='unique')
        
        # Note: We don't drop the table or columns in downgrade to preserve data
        # If full rollback is needed, manually drop columns
