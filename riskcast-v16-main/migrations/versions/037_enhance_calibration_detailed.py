"""Enhance calibration with detailed result tables

Revision ID: 037_enhance_calibration_detailed
Revises: 036_create_premium_allocations
Create Date: 2026-01-23

Adds detailed calibration result tables:
- calibrated_weights: Individual layer weights
- calibrated_correlations: Correlation pairs
- calibrated_loss_functions: Loss function parameters
- calibration_comparisons: Run comparisons

Also enhances calibration_runs table with additional fields.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '037_enhance_calibration_detailed'
down_revision = '036_create_premium_allocations'
branch_labels = None
depends_on = None


def upgrade():
    # Enhance calibration_runs table with additional fields
    op.add_column('calibration_runs',
        sa.Column('current_stage', sa.String(length=50), nullable=True))
    op.add_column('calibration_runs',
        sa.Column('dataset_start_date', sa.Date(), nullable=True))
    op.add_column('calibration_runs',
        sa.Column('dataset_end_date', sa.Date(), nullable=True))
    op.add_column('calibration_runs',
        sa.Column('dataset_size', sa.Integer(), nullable=True))
    op.add_column('calibration_runs',
        sa.Column('dataset_hash', sa.String(length=64), nullable=True))
    op.add_column('calibration_runs',
        sa.Column('weight_calibration_json', sa.JSON(), nullable=True))
    op.add_column('calibration_runs',
        sa.Column('weight_method', sa.String(length=50), nullable=True))
    op.add_column('calibration_runs',
        sa.Column('weight_before_mse', sa.Float(), nullable=True))
    op.add_column('calibration_runs',
        sa.Column('weight_after_mse', sa.Float(), nullable=True))
    op.add_column('calibration_runs',
        sa.Column('weight_improvement_pct', sa.Float(), nullable=True))
    op.add_column('calibration_runs',
        sa.Column('correlation_calibration_json', sa.JSON(), nullable=True))
    op.add_column('calibration_runs',
        sa.Column('correlation_method', sa.String(length=50), nullable=True))
    op.add_column('calibration_runs',
        sa.Column('correlation_stability', sa.Float(), nullable=True))
    op.add_column('calibration_runs',
        sa.Column('loss_function_calibration_json', sa.JSON(), nullable=True))
    op.add_column('calibration_runs',
        sa.Column('loss_function_type', sa.String(length=50), nullable=True))
    op.add_column('calibration_runs',
        sa.Column('loss_function_before_r2', sa.Float(), nullable=True))
    op.add_column('calibration_runs',
        sa.Column('loss_function_after_r2', sa.Float(), nullable=True))
    op.add_column('calibration_runs',
        sa.Column('validation_passed', sa.Boolean(), nullable=True, server_default='0'))
    op.add_column('calibration_runs',
        sa.Column('validation_metrics_json', sa.JSON(), nullable=True))
    op.add_column('calibration_runs',
        sa.Column('duration_seconds', sa.Float(), nullable=True))
    op.add_column('calibration_runs',
        sa.Column('errors_json', sa.JSON(), nullable=True))
    op.add_column('calibration_runs',
        sa.Column('warnings', sa.JSON(), nullable=True))
    op.add_column('calibration_runs',
        sa.Column('recommendations', sa.JSON(), nullable=True))
    op.add_column('calibration_runs',
        sa.Column('calibration_hash', sa.String(length=64), nullable=True))
    
    # Update status column length
    op.alter_column('calibration_runs', 'status',
        existing_type=sa.String(length=20),
        type_=sa.String(length=50),
        existing_nullable=False)
    
    # Add index for output_model_version_id if not exists
    try:
        op.create_index('idx_cal_runs_output_model', 'calibration_runs', ['output_model_version_id'])
    except Exception:
        pass  # Index may already exist
    
    # Calibrated weights table
    op.create_table(
        'calibrated_weights',
        sa.Column('id', sa.String(length=26), primary_key=True),
        sa.Column('calibration_run_id', sa.String(length=26), nullable=False),
        sa.Column('layer_name', sa.String(length=100), nullable=False),
        sa.Column('original_weight', sa.Float(), nullable=False),
        sa.Column('calibrated_weight', sa.Float(), nullable=False),
        sa.Column('weight_change', sa.Float(), nullable=True),
        sa.Column('confidence_interval_lower', sa.Float(), nullable=True),
        sa.Column('confidence_interval_upper', sa.Float(), nullable=True),
        sa.Column('importance_rank', sa.Integer(), nullable=True),
        sa.Column('statistical_significance', sa.Float(), nullable=True),
        sa.Column('sample_size', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['calibration_run_id'], ['calibration_runs.id'], name='fk_cal_weight_run', ondelete='CASCADE'),
    )
    op.create_index('idx_calibrated_weights_run', 'calibrated_weights', ['calibration_run_id'])
    op.create_index('idx_calibrated_weights_layer', 'calibrated_weights', ['layer_name'])
    
    # Calibrated correlations table
    op.create_table(
        'calibrated_correlations',
        sa.Column('id', sa.String(length=26), primary_key=True),
        sa.Column('calibration_run_id', sa.String(length=26), nullable=False),
        sa.Column('layer_1', sa.String(length=100), nullable=False),
        sa.Column('layer_2', sa.String(length=100), nullable=False),
        sa.Column('original_correlation', sa.Float(), nullable=True),
        sa.Column('calibrated_correlation', sa.Float(), nullable=False),
        sa.Column('correlation_change', sa.Float(), nullable=True),
        sa.Column('p_value', sa.Float(), nullable=True),
        sa.Column('is_significant', sa.Boolean(), nullable=True),
        sa.Column('sample_size', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['calibration_run_id'], ['calibration_runs.id'], name='fk_cal_corr_run', ondelete='CASCADE'),
    )
    op.create_index('idx_calibrated_corr_run', 'calibrated_correlations', ['calibration_run_id'])
    op.create_index('idx_calibrated_corr_layers', 'calibrated_correlations', ['layer_1', 'layer_2'])
    op.create_index('idx_calibrated_corr_layer1', 'calibrated_correlations', ['layer_1'])
    op.create_index('idx_calibrated_corr_layer2', 'calibrated_correlations', ['layer_2'])
    
    # Calibrated loss functions table
    op.create_table(
        'calibrated_loss_functions',
        sa.Column('id', sa.String(length=26), primary_key=True),
        sa.Column('calibration_run_id', sa.String(length=26), nullable=False),
        sa.Column('function_type', sa.String(length=50), nullable=False),
        sa.Column('parameters_json', sa.JSON(), nullable=False),
        sa.Column('original_parameters_json', sa.JSON(), nullable=True),
        sa.Column('formula', sa.String(length=500), nullable=True),
        sa.Column('before_mse', sa.Float(), nullable=True),
        sa.Column('before_mae', sa.Float(), nullable=True),
        sa.Column('before_r2', sa.Float(), nullable=True),
        sa.Column('after_mse', sa.Float(), nullable=True),
        sa.Column('after_mae', sa.Float(), nullable=True),
        sa.Column('after_r2', sa.Float(), nullable=True),
        sa.Column('mse_improvement_pct', sa.Float(), nullable=True),
        sa.Column('r2_improvement_pct', sa.Float(), nullable=True),
        sa.Column('residual_analysis_json', sa.JSON(), nullable=True),
        sa.Column('risk_level_analysis_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['calibration_run_id'], ['calibration_runs.id'], name='fk_cal_loss_run', ondelete='CASCADE'),
    )
    op.create_index('idx_calibrated_loss_run', 'calibrated_loss_functions', ['calibration_run_id'])
    op.create_unique_constraint('uq_cal_loss_run', 'calibrated_loss_functions', ['calibration_run_id'])
    
    # Calibration comparisons table
    op.create_table(
        'calibration_comparisons',
        sa.Column('id', sa.String(length=26), primary_key=True),
        sa.Column('baseline_run_id', sa.String(length=26), nullable=False),
        sa.Column('comparison_run_id', sa.String(length=26), nullable=False),
        sa.Column('weight_changes_json', sa.JSON(), nullable=True),
        sa.Column('max_weight_change', sa.Float(), nullable=True),
        sa.Column('avg_weight_change', sa.Float(), nullable=True),
        sa.Column('correlation_changes_json', sa.JSON(), nullable=True),
        sa.Column('max_correlation_change', sa.Float(), nullable=True),
        sa.Column('avg_correlation_change', sa.Float(), nullable=True),
        sa.Column('loss_function_changes_json', sa.JSON(), nullable=True),
        sa.Column('overall_change_magnitude', sa.Float(), nullable=True),
        sa.Column('change_significance', sa.String(length=20), nullable=True),
        sa.Column('recommendation', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['baseline_run_id'], ['calibration_runs.id'], name='fk_cal_comp_baseline', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['comparison_run_id'], ['calibration_runs.id'], name='fk_cal_comp_comparison', ondelete='CASCADE'),
    )
    op.create_index('idx_comparison_baseline', 'calibration_comparisons', ['baseline_run_id'])
    op.create_index('idx_comparison_comparison', 'calibration_comparisons', ['comparison_run_id'])


def downgrade():
    op.drop_table('calibration_comparisons')
    op.drop_table('calibrated_loss_functions')
    op.drop_table('calibrated_correlations')
    op.drop_table('calibrated_weights')
    
    # Remove added columns from calibration_runs
    op.drop_column('calibration_runs', 'calibration_hash')
    op.drop_column('calibration_runs', 'recommendations')
    op.drop_column('calibration_runs', 'warnings')
    op.drop_column('calibration_runs', 'errors_json')
    op.drop_column('calibration_runs', 'duration_seconds')
    op.drop_column('calibration_runs', 'validation_metrics_json')
    op.drop_column('calibration_runs', 'validation_passed')
    op.drop_column('calibration_runs', 'loss_function_after_r2')
    op.drop_column('calibration_runs', 'loss_function_before_r2')
    op.drop_column('calibration_runs', 'loss_function_type')
    op.drop_column('calibration_runs', 'loss_function_calibration_json')
    op.drop_column('calibration_runs', 'correlation_stability')
    op.drop_column('calibration_runs', 'correlation_method')
    op.drop_column('calibration_runs', 'correlation_calibration_json')
    op.drop_column('calibration_runs', 'weight_improvement_pct')
    op.drop_column('calibration_runs', 'weight_after_mse')
    op.drop_column('calibration_runs', 'weight_before_mse')
    op.drop_column('calibration_runs', 'weight_method')
    op.drop_column('calibration_runs', 'weight_calibration_json')
    op.drop_column('calibration_runs', 'dataset_hash')
    op.drop_column('calibration_runs', 'dataset_size')
    op.drop_column('calibration_runs', 'dataset_end_date')
    op.drop_column('calibration_runs', 'dataset_start_date')
    op.drop_column('calibration_runs', 'current_stage')
    
    # Revert status column length
    op.alter_column('calibration_runs', 'status',
        existing_type=sa.String(length=50),
        type_=sa.String(length=20),
        existing_nullable=False)
    
    # Drop index if exists
    try:
        op.drop_index('idx_cal_runs_output_model', 'calibration_runs')
    except Exception:
        pass
