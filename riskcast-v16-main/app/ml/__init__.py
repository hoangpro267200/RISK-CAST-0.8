"""
Machine Learning Module for RiskCast

Provides ML-powered anomaly detection and fraud detection capabilities.
"""

from app.ml.anomaly_detection import (
    AnomalyType,
    AnomalyResult,
    FeatureEngineering,
    IsolationForestDetector,
    AutoencoderAnomalyDetector,
    FraudDetectionService,
)


__all__ = [
    "AnomalyType",
    "AnomalyResult",
    "FeatureEngineering",
    "IsolationForestDetector",
    "AutoencoderAnomalyDetector",
    "FraudDetectionService",
]
