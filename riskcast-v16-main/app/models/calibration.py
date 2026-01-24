"""
Calibration models.

Models for calibration datasets, runs, and backtesting.
"""

from datetime import date, datetime
from typing import Optional
import sqlalchemy as sa
from sqlalchemy import Column, String, BigInteger, Float, Date, DateTime, ForeignKey, Boolean, Text, Index
from sqlalchemy.orm import relationship

from app.database import Base


class CalibrationDataset(Base):
    """
    Calibration dataset model.
    
    Represents a dataset used for model calibration.
    """
    __tablename__ = 'calibration_datasets'
    
    # Primary key
    id = Column(String(length=26), primary_key=True)
    
    # Tenant
    tenant_id = Column(String(length=26), ForeignKey('tenants.id'), nullable=True, index=True)
    
    # Identification
    name = Column(String(length=255), nullable=False)
    description = Column(Text(), nullable=True)
    dataset_type = Column(String(length=50), nullable=False)
    # HISTORICAL_POLICIES, LOSS_EXPERIENCE, MARKET_DATA
    
    # Status
    status = Column(String(length=20), nullable=False, server_default='DRAFT', index=True)
    # DRAFT, VALIDATED, PUBLISHED, ARCHIVED
    
    # Data specification
    schema_version = Column(String(length=20), nullable=False)
    data_source = Column(String(length=100), nullable=True)
    
    # Storage
    storage_uri = Column(Text(), nullable=True)
    dataset_hash = Column(String(length=64), nullable=True)
    row_count = Column(sa.Integer(), nullable=True)
    size_bytes = Column(BigInteger(), nullable=True)
    
    # Time range
    time_range_start = Column(Date(), nullable=True)
    time_range_end = Column(Date(), nullable=True)
    
    # Data quality
    quality_metrics_json = Column(sa.JSON(), nullable=True)
    
    # PII handling
    contains_pii = Column(Boolean(), nullable=False, server_default='0')
    pii_handling = Column(String(length=50), nullable=True)
    # ANONYMIZED, PSEUDONYMIZED, RAW
    
    # Timestamps
    created_by_user_id = Column(String(length=26), ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    validated_at = Column(DateTime(), nullable=True)
    published_at = Column(DateTime(), nullable=True)
    
    # Relationships
    created_by_user = relationship('User', foreign_keys=[created_by_user_id], lazy='select')
    calibration_runs = relationship('CalibrationRun', back_populates='dataset', lazy='select')
    backtest_runs = relationship('BacktestRun', back_populates='dataset', lazy='select')
    
    def __repr__(self):
        return f"<CalibrationDataset(id={self.id}, name={self.name}, status={self.status})>"


class CalibrationRun(Base):
    """
    Calibration run model.
    
    Represents a single calibration execution with complete details.
    Stores full information about each calibration run for audit trail and reproducibility.
    """
    __tablename__ = 'calibration_runs'
    
    # Primary key
    id = Column(String(length=26), primary_key=True)
    
    # Tenant
    tenant_id = Column(String(length=26), ForeignKey('tenants.id'), nullable=True, index=True)
    
    # References
    dataset_id = Column(String(length=26), ForeignKey('calibration_datasets.id'), nullable=False, index=True)
    input_model_version_id = Column(String(length=26), ForeignKey('risk_model_versions.id'), nullable=False, index=True)
    output_model_version_id = Column(String(length=26), ForeignKey('risk_model_versions.id'), nullable=True, index=True)
    
    # Status
    status = Column(String(length=50), nullable=False, server_default='PENDING', index=True)
    # PENDING, RUNNING, SUCCESS, PARTIAL_SUCCESS, FAILED, APPROVED
    
    current_stage = Column(String(length=50))  # DATA_LOADING, WEIGHT_CALIBRATION, etc.
    
    # Configuration
    config_json = Column(sa.JSON(), nullable=True)
    
    # Dataset info
    dataset_start_date = Column(Date, nullable=True)
    dataset_end_date = Column(Date, nullable=True)
    dataset_size = Column(sa.Integer)
    dataset_hash = Column(String(length=64))
    
    # Weight calibration results
    weight_calibration_json = Column(sa.JSON)
    weight_method = Column(String(length=50))
    weight_before_mse = Column(Float)
    weight_after_mse = Column(Float)
    weight_improvement_pct = Column(Float)
    
    # Correlation calibration results
    correlation_calibration_json = Column(sa.JSON)
    correlation_method = Column(String(length=50))
    correlation_stability = Column(Float)
    
    # Loss function calibration results
    loss_function_calibration_json = Column(sa.JSON)
    loss_function_type = Column(String(length=50))
    loss_function_before_r2 = Column(Float)
    loss_function_after_r2 = Column(Float)
    
    # Validation
    validation_passed = Column(Boolean, default=False)
    validation_metrics_json = Column(sa.JSON)
    
    # Results (legacy, kept for backward compatibility)
    metrics_json = Column(sa.JSON(), nullable=True)
    parameter_changes_json = Column(sa.JSON(), nullable=True)
    
    # Timing
    created_by_user_id = Column(String(length=26), ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    started_at = Column(DateTime(), nullable=True, index=True)
    completed_at = Column(DateTime(), nullable=True)
    duration_seconds = Column(Float)
    approved_by_user_id = Column(String(length=26), ForeignKey('users.id'), nullable=True)
    approved_at = Column(DateTime(), nullable=True)
    
    # Errors and warnings
    errors_json = Column(sa.JSON, default=list)
    warnings = Column(sa.JSON, default=list)
    recommendations = Column(sa.JSON, default=list)
    
    # Audit
    calibration_hash = Column(String(length=64))
    
    # Relationships
    dataset = relationship('CalibrationDataset', foreign_keys=[dataset_id], back_populates='calibration_runs', lazy='select')
    input_model = relationship('RiskModelVersion', foreign_keys=[input_model_version_id], lazy='select')
    output_model = relationship('RiskModelVersion', foreign_keys=[output_model_version_id], lazy='select')
    created_by_user = relationship('User', foreign_keys=[created_by_user_id], lazy='select')
    approved_by_user = relationship('User', foreign_keys=[approved_by_user_id], lazy='select')
    
    # Detailed relationships
    calibrated_weights = relationship('CalibratedWeight', back_populates='calibration_run', lazy='dynamic', cascade='all, delete-orphan')
    calibrated_correlations = relationship('CalibratedCorrelation', back_populates='calibration_run', lazy='dynamic', cascade='all, delete-orphan')
    calibrated_loss_function = relationship('CalibratedLossFunction', back_populates='calibration_run', uselist=False, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<CalibrationRun(id={self.id}, status={self.status}, dataset_id={self.dataset_id})>"


class BacktestRun(Base):
    """
    Backtest run model.
    
    Represents a backtesting execution for model validation.
    """
    __tablename__ = 'backtest_runs'
    
    # Primary key
    id = Column(String(length=26), primary_key=True)
    
    # Tenant
    tenant_id = Column(String(length=26), ForeignKey('tenants.id'), nullable=True, index=True)
    
    # References
    dataset_id = Column(String(length=26), ForeignKey('calibration_datasets.id'), nullable=False, index=True)
    model_version_id = Column(String(length=26), ForeignKey('risk_model_versions.id'), nullable=False, index=True)
    baseline_model_version_id = Column(String(length=26), ForeignKey('risk_model_versions.id'), nullable=True)
    
    # Status
    status = Column(String(length=20), nullable=False, server_default='PENDING', index=True)
    # PENDING, RUNNING, COMPLETED, FAILED
    
    # Configuration
    config_json = Column(sa.JSON(), nullable=True)
    
    # Results
    metrics_json = Column(sa.JSON(), nullable=True)
    comparison_json = Column(sa.JSON(), nullable=True)
    
    # Report
    report_uri = Column(Text(), nullable=True)
    report_hash = Column(String(length=64), nullable=True)
    
    # Timestamps
    created_by_user_id = Column(String(length=26), ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    started_at = Column(DateTime(), nullable=True)
    completed_at = Column(DateTime(), nullable=True)
    
    # Relationships
    dataset = relationship('CalibrationDataset', foreign_keys=[dataset_id], back_populates='backtest_runs', lazy='select')
    model_version = relationship('RiskModelVersion', foreign_keys=[model_version_id], lazy='select')
    baseline_model_version = relationship('RiskModelVersion', foreign_keys=[baseline_model_version_id], lazy='select')
    created_by_user = relationship('User', foreign_keys=[created_by_user_id], lazy='select')
    
    def __repr__(self):
        return f"<BacktestRun(id={self.id}, status={self.status}, model_version_id={self.model_version_id})>"


class CalibratedWeight(Base):
    """
    Calibrated layer weights from a calibration run.
    
    Stored separately for easy querying and comparison.
    """
    __tablename__ = 'calibrated_weights'
    
    id = Column(String(length=26), primary_key=True)
    calibration_run_id = Column(
        String(length=26),
        ForeignKey('calibration_runs.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    layer_name = Column(String(length=100), nullable=False, index=True)
    original_weight = Column(Float, nullable=False)
    calibrated_weight = Column(Float, nullable=False)
    weight_change = Column(Float)
    confidence_interval_lower = Column(Float)
    confidence_interval_upper = Column(Float)
    importance_rank = Column(sa.Integer)
    statistical_significance = Column(Float)  # p-value
    sample_size = Column(sa.Integer)
    
    created_at = Column(DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    
    # Relationships
    calibration_run = relationship('CalibrationRun', foreign_keys=[calibration_run_id], back_populates='calibrated_weights', lazy='select')
    
    __table_args__ = (
        Index('idx_calibrated_weights_run', 'calibration_run_id'),
        Index('idx_calibrated_weights_layer', 'layer_name'),
    )
    
    def __repr__(self):
        return f"<CalibratedWeight(id={self.id}, layer={self.layer_name}, weight={self.calibrated_weight})>"


class CalibratedCorrelation(Base):
    """
    Calibrated correlation pairs from a calibration run.
    """
    __tablename__ = 'calibrated_correlations'
    
    id = Column(String(length=26), primary_key=True)
    calibration_run_id = Column(
        String(length=26),
        ForeignKey('calibration_runs.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    layer_1 = Column(String(length=100), nullable=False, index=True)
    layer_2 = Column(String(length=100), nullable=False, index=True)
    original_correlation = Column(Float)
    calibrated_correlation = Column(Float, nullable=False)
    correlation_change = Column(Float)
    p_value = Column(Float)
    is_significant = Column(Boolean)
    sample_size = Column(sa.Integer)
    
    created_at = Column(DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    
    # Relationships
    calibration_run = relationship('CalibrationRun', foreign_keys=[calibration_run_id], back_populates='calibrated_correlations', lazy='select')
    
    __table_args__ = (
        Index('idx_calibrated_corr_run', 'calibration_run_id'),
        Index('idx_calibrated_corr_layers', 'layer_1', 'layer_2'),
    )
    
    def __repr__(self):
        return f"<CalibratedCorrelation(id={self.id}, {self.layer_1}-{self.layer_2}, corr={self.calibrated_correlation})>"


class CalibratedLossFunction(Base):
    """
    Calibrated loss function parameters.
    """
    __tablename__ = 'calibrated_loss_functions'
    
    id = Column(String(length=26), primary_key=True)
    calibration_run_id = Column(
        String(length=26),
        ForeignKey('calibration_runs.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        unique=True  # One loss function per calibration run
    )
    
    function_type = Column(String(length=50), nullable=False)
    parameters_json = Column(sa.JSON, nullable=False)
    original_parameters_json = Column(sa.JSON)
    formula = Column(String(length=500))
    
    before_mse = Column(Float)
    before_mae = Column(Float)
    before_r2 = Column(Float)
    
    after_mse = Column(Float)
    after_mae = Column(Float)
    after_r2 = Column(Float)
    
    mse_improvement_pct = Column(Float)
    r2_improvement_pct = Column(Float)
    
    residual_analysis_json = Column(sa.JSON)
    risk_level_analysis_json = Column(sa.JSON)
    
    created_at = Column(DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    
    # Relationships
    calibration_run = relationship('CalibrationRun', foreign_keys=[calibration_run_id], back_populates='calibrated_loss_function', lazy='select')
    
    __table_args__ = (
        Index('idx_calibrated_loss_run', 'calibration_run_id'),
    )
    
    def __repr__(self):
        return f"<CalibratedLossFunction(id={self.id}, type={self.function_type}, r2={self.after_r2})>"


class CalibrationComparison(Base):
    """
    Comparison between calibration runs.
    
    Helps track how calibration changes over time.
    """
    __tablename__ = 'calibration_comparisons'
    
    id = Column(String(length=26), primary_key=True)
    
    baseline_run_id = Column(
        String(length=26),
        ForeignKey('calibration_runs.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    comparison_run_id = Column(
        String(length=26),
        ForeignKey('calibration_runs.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Weight changes
    weight_changes_json = Column(sa.JSON)
    max_weight_change = Column(Float)
    avg_weight_change = Column(Float)
    
    # Correlation changes
    correlation_changes_json = Column(sa.JSON)
    max_correlation_change = Column(Float)
    avg_correlation_change = Column(Float)
    
    # Loss function changes
    loss_function_changes_json = Column(sa.JSON)
    
    # Overall assessment
    overall_change_magnitude = Column(Float)
    change_significance = Column(String(length=20))  # LOW, MEDIUM, HIGH
    recommendation = Column(Text)
    
    created_at = Column(DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    
    # Relationships
    baseline_run = relationship('CalibrationRun', foreign_keys=[baseline_run_id], lazy='select')
    comparison_run = relationship('CalibrationRun', foreign_keys=[comparison_run_id], lazy='select')
    
    __table_args__ = (
        Index('idx_comparison_baseline', 'baseline_run_id'),
        Index('idx_comparison_comparison', 'comparison_run_id'),
    )
    
    def __repr__(self):
        return f"<CalibrationComparison(id={self.id}, baseline={self.baseline_run_id}, comparison={self.comparison_run_id})>"
