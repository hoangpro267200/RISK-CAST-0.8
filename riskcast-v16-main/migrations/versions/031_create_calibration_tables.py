"""Create calibration and backtesting tables.

Revision ID: 031_create_calibration
Revises: 030_create_loss_experience
Create Date: 2026-01-23

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '031_create_calibration'
down_revision = '030_create_loss_experience'
branch_labels = None
depends_on = None


def upgrade():
    # Calibration datasets
    op.create_table(
        'calibration_datasets',
        sa.Column('id', sa.String(length=26), primary_key=True),
        sa.Column('tenant_id', sa.String(length=26), nullable=True),  # NULL for global datasets
        
        # Identification
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('dataset_type', sa.String(length=50), nullable=False),
        # HISTORICAL_POLICIES, LOSS_EXPERIENCE, MARKET_DATA
        
        # Status
        sa.Column('status', sa.String(length=20), nullable=False, server_default='DRAFT'),
        # DRAFT, VALIDATED, PUBLISHED, ARCHIVED
        
        # Data specification
        sa.Column('schema_version', sa.String(length=20), nullable=False),
        sa.Column('data_source', sa.String(length=100), nullable=True),  # Where data came from
        
        # Storage
        sa.Column('storage_uri', sa.Text(), nullable=True),  # S3 URI or local path
        sa.Column('dataset_hash', sa.String(length=64), nullable=True),  # SHA256 of dataset
        sa.Column('row_count', sa.Integer(), nullable=True),
        sa.Column('size_bytes', sa.BigInteger(), nullable=True),
        
        # Time range
        sa.Column('time_range_start', sa.Date(), nullable=True),
        sa.Column('time_range_end', sa.Date(), nullable=True),
        
        # Data quality
        sa.Column('quality_metrics_json', sa.JSON(), nullable=True),
        # {
        #   "completeness": 0.98,
        #   "missing_fields": ["carrier_id"],
        #   "outliers_removed": 15,
        #   "validation_passed": true
        # }
        
        # PII handling
        sa.Column('contains_pii', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('pii_handling', sa.String(length=50), nullable=True),  # ANONYMIZED, PSEUDONYMIZED, RAW
        
        # Timestamps
        sa.Column('created_by_user_id', sa.String(length=26), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('validated_at', sa.DateTime(), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        
        # Foreign keys
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_cal_dataset_tenant', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], name='fk_cal_dataset_created_by', ondelete='SET NULL'),
    )
    
    # Calibration runs
    op.create_table(
        'calibration_runs',
        sa.Column('id', sa.String(length=26), primary_key=True),
        sa.Column('tenant_id', sa.String(length=26), nullable=True),
        
        # References
        sa.Column('dataset_id', sa.String(length=26), nullable=False),
        sa.Column('input_model_version_id', sa.String(length=26), nullable=False),
        sa.Column('output_model_version_id', sa.String(length=26), nullable=True),
        
        # Status
        sa.Column('status', sa.String(length=20), nullable=False, server_default='PENDING'),
        # PENDING, RUNNING, COMPLETED, FAILED, APPROVED
        
        # Configuration
        sa.Column('config_json', sa.JSON(), nullable=True),
        # {
        #   "method": "GRADIENT_DESCENT",
        #   "learning_rate": 0.01,
        #   "max_iterations": 1000,
        #   "convergence_threshold": 0.0001,
        #   "holdout_ratio": 0.2
        # }
        
        # Results
        sa.Column('metrics_json', sa.JSON(), nullable=True),
        # {
        #   "before": {"loss_ratio_error": 0.15, "mse": 0.02},
        #   "after": {"loss_ratio_error": 0.05, "mse": 0.008},
        #   "improvement": 0.67,
        #   "convergence_iterations": 450
        # }
        
        sa.Column('parameter_changes_json', sa.JSON(), nullable=True),
        # {
        #   "weights": {"route_risk": {"before": 0.25, "after": 0.28}},
        #   "correlations": {...},
        #   "tail_params": {...}
        # }
        
        # Timestamps
        sa.Column('created_by_user_id', sa.String(length=26), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('approved_by_user_id', sa.String(length=26), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        
        # Foreign keys
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_cal_run_tenant', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['dataset_id'], ['calibration_datasets.id'], name='fk_cal_run_dataset', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['input_model_version_id'], ['risk_model_versions.id'], name='fk_cal_run_input_model', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['output_model_version_id'], ['risk_model_versions.id'], name='fk_cal_run_output_model', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], name='fk_cal_run_created_by', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['approved_by_user_id'], ['users.id'], name='fk_cal_run_approved_by', ondelete='SET NULL'),
    )
    
    # Backtest runs
    op.create_table(
        'backtest_runs',
        sa.Column('id', sa.String(length=26), primary_key=True),
        sa.Column('tenant_id', sa.String(length=26), nullable=True),
        
        # References
        sa.Column('dataset_id', sa.String(length=26), nullable=False),
        sa.Column('model_version_id', sa.String(length=26), nullable=False),
        sa.Column('baseline_model_version_id', sa.String(length=26), nullable=True),
        
        # Status
        sa.Column('status', sa.String(length=20), nullable=False, server_default='PENDING'),
        # PENDING, RUNNING, COMPLETED, FAILED
        
        # Configuration
        sa.Column('config_json', sa.JSON(), nullable=True),
        # {
        #   "seed": 42,
        #   "iterations_per_policy": 1000,
        #   "metrics_to_compute": ["loss_ratio", "var_95", "calibration_curve"]
        # }
        
        # Results
        sa.Column('metrics_json', sa.JSON(), nullable=True),
        # {
        #   "total_policies": 1000,
        #   "deterministic_replays": 1000,
        #   "replay_mismatches": 0,
        #   "loss_ratio_predicted": 0.052,
        #   "loss_ratio_actual": 0.055,
        #   "mse": 0.0012,
        #   "auc": 0.78
        # }
        
        sa.Column('comparison_json', sa.JSON(), nullable=True),  # If baseline model provided
        # {
        #   "model_improvement": 0.15,
        #   "loss_prediction_better": true,
        #   "recommendation": "DEPLOY"
        # }
        
        # Report
        sa.Column('report_uri', sa.Text(), nullable=True),
        sa.Column('report_hash', sa.String(length=64), nullable=True),
        
        # Timestamps
        sa.Column('created_by_user_id', sa.String(length=26), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        
        # Foreign keys
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_backtest_tenant', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['dataset_id'], ['calibration_datasets.id'], name='fk_backtest_dataset', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['model_version_id'], ['risk_model_versions.id'], name='fk_backtest_model', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['baseline_model_version_id'], ['risk_model_versions.id'], name='fk_backtest_baseline', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], name='fk_backtest_created_by', ondelete='SET NULL'),
    )
    
    # Indexes
    op.create_index('idx_cal_datasets_tenant', 'calibration_datasets', ['tenant_id'])
    op.create_index('idx_cal_datasets_status', 'calibration_datasets', ['status'])
    op.create_index('idx_cal_datasets_type', 'calibration_datasets', ['dataset_type'])
    op.create_index('idx_cal_runs_tenant', 'calibration_runs', ['tenant_id'])
    op.create_index('idx_cal_runs_status', 'calibration_runs', ['status'])
    op.create_index('idx_cal_runs_dataset', 'calibration_runs', ['dataset_id'])
    op.create_index('idx_cal_runs_input_model', 'calibration_runs', ['input_model_version_id'])
    op.create_index('idx_backtest_runs_tenant', 'backtest_runs', ['tenant_id'])
    op.create_index('idx_backtest_runs_status', 'backtest_runs', ['status'])
    op.create_index('idx_backtest_runs_dataset', 'backtest_runs', ['dataset_id'])
    op.create_index('idx_backtest_runs_model', 'backtest_runs', ['model_version_id'])


def downgrade():
    op.drop_table('backtest_runs')
    op.drop_table('calibration_runs')
    op.drop_table('calibration_datasets')
