"""Enhance model versioning with detailed parameters

Revision ID: 020_enhance_model_versioning
Revises: 019_evidence_links
Create Date: 2025-01-23

Adds detailed model parameter fields: base_weights, correlation_matrix, 
tail_parameters, interaction_multipliers, loss_transform_params, monte_carlo_defaults.
Adds version field (semantic versioning) and parent_version_id for lineage.
Enhances activations table with scope_type and scope_id.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '020_enhance_model_versioning'
down_revision = '019_evidence_links'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new detailed parameter fields to risk_model_versions
    op.add_column('risk_model_versions', 
        sa.Column('version', sa.String(length=50), nullable=True))
    op.add_column('risk_model_versions',
        sa.Column('base_weights_json', sa.JSON(), nullable=True))
    op.add_column('risk_model_versions',
        sa.Column('correlation_matrix_json', sa.JSON(), nullable=True))
    op.add_column('risk_model_versions',
        sa.Column('tail_parameters_json', sa.JSON(), nullable=True))
    op.add_column('risk_model_versions',
        sa.Column('interaction_multipliers_json', sa.JSON(), nullable=True))
    op.add_column('risk_model_versions',
        sa.Column('loss_transform_params_json', sa.JSON(), nullable=True))
    op.add_column('risk_model_versions',
        sa.Column('monte_carlo_defaults_json', sa.JSON(), nullable=True))
    
    # Add lineage fields
    op.add_column('risk_model_versions',
        sa.Column('parent_version_id', sa.String(length=26), nullable=True))
    op.add_column('risk_model_versions',
        sa.Column('calibration_run_id', sa.String(length=26), nullable=True))
    op.add_column('risk_model_versions',
        sa.Column('calibration_dataset_id', sa.String(length=26), nullable=True))
    
    # Add approval tracking fields
    op.add_column('risk_model_versions',
        sa.Column('published_by_user_id', sa.String(length=26), nullable=True))
    op.add_column('risk_model_versions',
        sa.Column('approved_by_user_id', sa.String(length=26), nullable=True))
    op.add_column('risk_model_versions',
        sa.Column('approved_at', sa.DateTime(), nullable=True))
    op.add_column('risk_model_versions',
        sa.Column('approval_notes', sa.Text(), nullable=True))
    
    # Add foreign key for parent_version_id
    op.create_foreign_key(
        'fk_model_version_parent',
        'risk_model_versions', 'risk_model_versions',
        ['parent_version_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Add foreign keys for approval tracking
    op.create_foreign_key(
        'fk_model_version_published_by',
        'risk_model_versions', 'users',
        ['published_by_user_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_model_version_approved_by',
        'risk_model_versions', 'users',
        ['approved_by_user_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Add indexes
    op.create_index('ix_model_versions_version', 'risk_model_versions', ['version'])
    op.create_index('ix_model_versions_parent', 'risk_model_versions', ['parent_version_id'])
    
    # Create unique constraint for tenant_id, name, version
    # Note: MySQL doesn't support NULL in unique constraints the same way as PostgreSQL
    # So we create a unique index that allows multiple NULLs
    try:
        op.create_unique_constraint(
            'uq_model_tenant_name_version',
            'risk_model_versions',
            ['tenant_id', 'name', 'version']
        )
    except Exception:
        # Constraint might already exist or MySQL might handle it differently
        # Create a unique index instead
        op.create_index(
            'ix_model_versions_tenant_name_version',
            'risk_model_versions',
            ['tenant_id', 'name', 'version'],
            unique=True
        )
    
    # Migrate existing data: set version from model_schema_version if available
    op.execute("""
        UPDATE risk_model_versions 
        SET version = '1.0.0' 
        WHERE version IS NULL AND model_schema_version IS NOT NULL
    """)
    op.execute("""
        UPDATE risk_model_versions 
        SET version = '1.0.0' 
        WHERE version IS NULL
    """)
    
    # Migrate existing weights_json to base_weights_json if it exists
    op.execute("""
        UPDATE risk_model_versions 
        SET base_weights_json = weights_json 
        WHERE base_weights_json IS NULL AND weights_json IS NOT NULL
    """)
    
    # Make version NOT NULL after migration
    op.alter_column('risk_model_versions', 'version', nullable=False)
    
    # Enhance risk_model_activations table
    # Add scope_type and scope_id fields
    op.add_column('risk_model_activations',
        sa.Column('scope_type', sa.String(length=50), nullable=True, server_default='DEFAULT'))
    op.add_column('risk_model_activations',
        sa.Column('scope_id', sa.String(length=26), nullable=True))
    
    # Add status field for activations
    op.add_column('risk_model_activations',
        sa.Column('status', sa.String(length=20), nullable=True, server_default='ACTIVE'))
    
    # Add audit fields for activations
    op.add_column('risk_model_activations',
        sa.Column('activated_by_user_id', sa.String(length=26), nullable=True))
    op.add_column('risk_model_activations',
        sa.Column('activated_at', sa.DateTime(), nullable=True))
    op.add_column('risk_model_activations',
        sa.Column('deactivated_at', sa.DateTime(), nullable=True))
    op.add_column('risk_model_activations',
        sa.Column('deactivation_reason', sa.Text(), nullable=True))
    
    # Migrate existing data: convert corridor_id/product_type to scope_type/scope_id
    # Keep corridor_id and product_type for backward compatibility
    op.execute("""
        UPDATE risk_model_activations 
        SET scope_type = 'PRODUCT',
            scope_id = NULL,
            activated_at = created_at
        WHERE scope_type IS NULL
    """)
    
    # Make scope_type NOT NULL after migration
    op.alter_column('risk_model_activations', 'scope_type', nullable=False)
    op.alter_column('risk_model_activations', 'status', nullable=False)
    
    # Add foreign key for activated_by_user_id
    op.create_foreign_key(
        'fk_activation_activated_by',
        'risk_model_activations', 'users',
        ['activated_by_user_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Add indexes for activations
    op.create_index('ix_activations_scope', 
                   'risk_model_activations', ['scope_type', 'scope_id'])
    op.create_index('ix_activations_status', 
                   'risk_model_activations', ['status'])
    op.create_index('ix_activations_effective', 
                   'risk_model_activations', ['effective_from', 'effective_to'])
    
    # Seed baseline model version with current hardcoded values
    # Get baseline values from RiskConfig in risk_engine_base.py
    baseline_weights = {
        "route_risk": 0.25,
        "cargo_risk": 0.20,
        "carrier_risk": 0.20,
        "timing_risk": 0.15,
        "weather_risk": 0.10,
        "geopolitical_risk": 0.10
    }
    
    baseline_correlation = {
        "route_cargo": 0.3,
        "weather_timing": 0.5,
        "carrier_route": 0.2
    }
    
    baseline_tail_params = {
        "degrees_of_freedom": 4,
        "tail_shock_probability": 0.05,
        "extreme_loss_multiplier": 2.5
    }
    
    baseline_interaction = {
        "high_value_perishable": 1.3,
        "hazmat_congested_port": 1.5
    }
    
    baseline_loss_transform = {
        "base_loss_rate": 0.02,
        "risk_score_exponent": 1.5,
        "min_loss_pct": 0.001,
        "max_loss_pct": 0.15
    }
    
    baseline_mc_defaults = {
        "default_iterations": 10000,
        "confidence_levels": [0.95, 0.99]
    }
    
    # Check if baseline model already exists and seed if not
    import json
    import hashlib
    from datetime import datetime
    from sqlalchemy import text
    
    conn = op.get_bind()
    result = conn.execute(text("SELECT id FROM risk_model_versions WHERE name = 'baseline' AND version = '1.0.0' LIMIT 1"))
    existing = result.fetchone()
    
    if not existing:
        # Generate immutable hash
        params_str = json.dumps({
            "base_weights": baseline_weights,
            "correlation_matrix": baseline_correlation,
            "tail_parameters": baseline_tail_params,
            "interaction_multipliers": baseline_interaction,
            "loss_transform_params": baseline_loss_transform,
            "monte_carlo_defaults": baseline_mc_defaults
        }, sort_keys=True)
        immutable_hash = hashlib.sha256(params_str.encode()).hexdigest()
        
        # Generate ULID for baseline model (using a fixed pattern for reproducibility)
        baseline_id = '01HZ0000000000000000000001'  # Fixed ULID for baseline
        now = datetime.utcnow()
        
        # Insert baseline model
        conn.execute(text("""
            INSERT INTO risk_model_versions (
                id, name, version, description, status, scope, model_schema_version,
                base_weights_json,
                correlation_matrix_json,
                tail_parameters_json,
                interaction_multipliers_json,
                loss_transform_params_json,
                monte_carlo_defaults_json,
                immutable_hash,
                published_at,
                created_at,
                updated_at
            ) VALUES (
                :id, 'baseline', '1.0.0', 
                'Initial baseline model migrated from hardcoded values',
                'PUBLISHED', 'GLOBAL', 'risk_model_v1.0',
                :base_weights,
                :correlation_matrix,
                :tail_params,
                :interaction_mult,
                :loss_transform,
                :mc_defaults,
                :hash,
                :now,
                :now,
                :now
            )
        """), {
            'id': baseline_id,
            'base_weights': json.dumps(baseline_weights),
            'correlation_matrix': json.dumps(baseline_correlation),
            'tail_params': json.dumps(baseline_tail_params),
            'interaction_mult': json.dumps(baseline_interaction),
            'loss_transform': json.dumps(baseline_loss_transform),
            'mc_defaults': json.dumps(baseline_mc_defaults),
            'hash': immutable_hash,
            'now': now
        })
        
        # Create default activation for baseline model
        activation_id = '01HZ0000000000000000000002'  # Fixed ULID for activation
        conn.execute(text("""
            INSERT INTO risk_model_activations (
                id, tenant_id, model_version_id, scope_type, 
                effective_from, status, activated_at, created_at, updated_at
            ) VALUES (
                :id, NULL, :model_version_id, 'DEFAULT',
                :now, 'ACTIVE', :now, :now, :now
            )
        """), {
            'id': activation_id,
            'model_version_id': baseline_id,
            'now': now
        })


def downgrade() -> None:
    # Drop indexes and constraints
    try:
        op.drop_constraint('uq_model_tenant_name_version', 'risk_model_versions', type_='unique')
    except Exception:
        pass  # Constraint might not exist or be named differently
    
    try:
        op.drop_index('ix_model_versions_tenant_name_version', table_name='risk_model_versions')
    except Exception:
        pass  # Index might not exist
    
    op.drop_index('ix_activations_effective', table_name='risk_model_activations')
    op.drop_index('ix_activations_status', table_name='risk_model_activations')
    op.drop_index('ix_activations_scope', table_name='risk_model_activations')
    op.drop_index('ix_model_versions_parent', table_name='risk_model_versions')
    op.drop_index('ix_model_versions_version', table_name='risk_model_versions')
    
    # Drop foreign keys
    op.drop_constraint('fk_activation_activated_by', 'risk_model_activations', type_='foreignkey')
    op.drop_constraint('fk_model_version_approved_by', 'risk_model_versions', type_='foreignkey')
    op.drop_constraint('fk_model_version_published_by', 'risk_model_versions', type_='foreignkey')
    op.drop_constraint('fk_model_version_parent', 'risk_model_versions', type_='foreignkey')
    
    # Drop columns from risk_model_activations
    op.drop_column('risk_model_activations', 'deactivation_reason')
    op.drop_column('risk_model_activations', 'deactivated_at')
    op.drop_column('risk_model_activations', 'activated_at')
    op.drop_column('risk_model_activations', 'activated_by_user_id')
    op.drop_column('risk_model_activations', 'status')
    op.drop_column('risk_model_activations', 'scope_id')
    op.drop_column('risk_model_activations', 'scope_type')
    
    # Drop columns from risk_model_versions
    op.drop_column('risk_model_versions', 'approval_notes')
    op.drop_column('risk_model_versions', 'approved_at')
    op.drop_column('risk_model_versions', 'approved_by_user_id')
    op.drop_column('risk_model_versions', 'published_by_user_id')
    op.drop_column('risk_model_versions', 'calibration_dataset_id')
    op.drop_column('risk_model_versions', 'calibration_run_id')
    op.drop_column('risk_model_versions', 'parent_version_id')
    op.drop_column('risk_model_versions', 'monte_carlo_defaults_json')
    op.drop_column('risk_model_versions', 'loss_transform_params_json')
    op.drop_column('risk_model_versions', 'interaction_multipliers_json')
    op.drop_column('risk_model_versions', 'tail_parameters_json')
    op.drop_column('risk_model_versions', 'correlation_matrix_json')
    op.drop_column('risk_model_versions', 'base_weights_json')
    op.drop_column('risk_model_versions', 'version')
