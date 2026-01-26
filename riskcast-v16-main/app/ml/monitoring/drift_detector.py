"""
Model Drift Detection System

Detects:
1. Data Drift - Input distribution changes
2. Concept Drift - Relationship between input/output changes
3. Prediction Drift - Output distribution changes
4. Performance Drift - Model accuracy degradation
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import json
import hashlib

from scipy import stats
from scipy.spatial.distance import jensenshannon

from app.core.logging import get_logger


logger = get_logger(__name__)

# Optional Redis import
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False


class DriftType(str, Enum):
    """Types of drift."""
    DATA_DRIFT = "DATA_DRIFT"
    CONCEPT_DRIFT = "CONCEPT_DRIFT"
    PREDICTION_DRIFT = "PREDICTION_DRIFT"
    PERFORMANCE_DRIFT = "PERFORMANCE_DRIFT"


class DriftSeverity(str, Enum):
    """Drift severity levels."""
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class FeatureDrift:
    """Drift detection for a single feature."""
    feature_name: str
    drift_detected: bool
    drift_score: float  # 0-1, higher = more drift
    p_value: float
    test_statistic: float
    test_method: str  # "ks", "chi2", "psi"
    baseline_stats: Dict
    current_stats: Dict
    severity: DriftSeverity


@dataclass
class DriftReport:
    """Complete drift detection report."""
    report_id: str
    model_name: str
    model_version: str
    
    # Timestamps
    baseline_start: datetime
    baseline_end: datetime
    detection_start: datetime
    detection_end: datetime
    generated_at: datetime
    
    # Overall results
    drift_detected: bool
    overall_severity: DriftSeverity
    drift_types_detected: List[DriftType]
    
    # Feature-level results
    feature_drifts: List[FeatureDrift]
    drifted_features: List[str]
    
    # Prediction drift
    prediction_drift_score: float
    prediction_drift_detected: bool
    
    # Performance drift
    baseline_performance: Dict[str, float]
    current_performance: Dict[str, float]
    performance_degradation: Dict[str, float]
    
    # Recommendations
    recommendations: List[str]
    
    # Metadata
    samples_baseline: int
    samples_current: int
    
    def to_dict(self) -> Dict:
        return {
            "report_id": self.report_id,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "drift_detected": self.drift_detected,
            "overall_severity": self.overall_severity.value,
            "drift_types_detected": [d.value for d in self.drift_types_detected],
            "drifted_features": self.drifted_features,
            "prediction_drift_score": self.prediction_drift_score,
            "performance_degradation": self.performance_degradation,
            "recommendations": self.recommendations,
            "generated_at": self.generated_at.isoformat()
        }


@dataclass
class DataWindow:
    """Sliding window for data collection."""
    features: Dict[str, List[float]] = field(default_factory=dict)
    predictions: List[float] = field(default_factory=list)
    actuals: List[float] = field(default_factory=list)
    timestamps: List[datetime] = field(default_factory=list)
    max_size: int = 10000
    
    def add_sample(
        self,
        features: Dict[str, float],
        prediction: float,
        actual: Optional[float] = None
    ):
        """Add a sample to the window."""
        for name, value in features.items():
            if name not in self.features:
                self.features[name] = []
            self.features[name].append(float(value))
            
            # Trim if exceeds max size
            if len(self.features[name]) > self.max_size:
                self.features[name] = self.features[name][-self.max_size:]
        
        self.predictions.append(float(prediction))
        if len(self.predictions) > self.max_size:
            self.predictions = self.predictions[-self.max_size:]
        
        if actual is not None:
            self.actuals.append(float(actual))
            if len(self.actuals) > self.max_size:
                self.actuals = self.actuals[-self.max_size:]
        
        self.timestamps.append(datetime.utcnow())
        if len(self.timestamps) > self.max_size:
            self.timestamps = self.timestamps[-self.max_size:]
    
    def get_feature_array(self, feature_name: str) -> np.ndarray:
        return np.array(self.features.get(feature_name, []))
    
    def size(self) -> int:
        return len(self.predictions)


class StatisticalTests:
    """Statistical tests for drift detection."""
    
    @staticmethod
    def kolmogorov_smirnov(
        baseline: np.ndarray,
        current: np.ndarray,
        alpha: float = 0.05
    ) -> Tuple[float, float, bool]:
        """
        Kolmogorov-Smirnov test for continuous features.
        
        Returns: (statistic, p_value, drift_detected)
        """
        statistic, p_value = stats.ks_2samp(baseline, current)
        drift_detected = p_value < alpha
        return statistic, p_value, drift_detected
    
    @staticmethod
    def chi_squared(
        baseline: np.ndarray,
        current: np.ndarray,
        n_bins: int = 10,
        alpha: float = 0.05
    ) -> Tuple[float, float, bool]:
        """
        Chi-squared test for categorical/binned features.
        
        Returns: (statistic, p_value, drift_detected)
        """
        # Bin the data
        all_data = np.concatenate([baseline, current])
        bins = np.histogram_bin_edges(all_data, bins=n_bins)
        
        baseline_hist, _ = np.histogram(baseline, bins=bins)
        current_hist, _ = np.histogram(current, bins=bins)
        
        # Add small constant to avoid division by zero
        baseline_hist = baseline_hist + 1
        current_hist = current_hist + 1
        
        statistic, p_value = stats.chisquare(current_hist, f_exp=baseline_hist)
        drift_detected = p_value < alpha
        
        return statistic, p_value, drift_detected
    
    @staticmethod
    def population_stability_index(
        baseline: np.ndarray,
        current: np.ndarray,
        n_bins: int = 10
    ) -> float:
        """
        Population Stability Index (PSI).
        
        PSI < 0.1: No significant change
        0.1 <= PSI < 0.2: Moderate change
        PSI >= 0.2: Significant change
        
        Returns: PSI score
        """
        # Bin the data
        all_data = np.concatenate([baseline, current])
        bins = np.histogram_bin_edges(all_data, bins=n_bins)
        
        baseline_hist, _ = np.histogram(baseline, bins=bins, density=True)
        current_hist, _ = np.histogram(current, bins=bins, density=True)
        
        # Normalize to proportions
        baseline_prop = baseline_hist / (baseline_hist.sum() + 1e-10)
        current_prop = current_hist / (current_hist.sum() + 1e-10)
        
        # Add small constant
        baseline_prop = np.clip(baseline_prop, 1e-10, 1)
        current_prop = np.clip(current_prop, 1e-10, 1)
        
        # Calculate PSI
        psi = np.sum(
            (current_prop - baseline_prop) * np.log(current_prop / baseline_prop)
        )
        
        return float(psi)
    
    @staticmethod
    def jensen_shannon_divergence(
        baseline: np.ndarray,
        current: np.ndarray,
        n_bins: int = 10
    ) -> float:
        """
        Jensen-Shannon divergence.
        
        Returns: JS divergence (0-1)
        """
        all_data = np.concatenate([baseline, current])
        bins = np.histogram_bin_edges(all_data, bins=n_bins)
        
        baseline_hist, _ = np.histogram(baseline, bins=bins, density=True)
        current_hist, _ = np.histogram(current, bins=bins, density=True)
        
        # Normalize
        baseline_prop = baseline_hist / (baseline_hist.sum() + 1e-10)
        current_prop = current_hist / (current_hist.sum() + 1e-10)
        
        return float(jensenshannon(baseline_prop, current_prop))
    
    @staticmethod
    def wasserstein_distance(
        baseline: np.ndarray,
        current: np.ndarray
    ) -> float:
        """
        Wasserstein (Earth Mover's) distance.
        
        Returns: Wasserstein distance
        """
        return float(stats.wasserstein_distance(baseline, current))


class DriftDetector:
    """
    Main drift detection service.
    """
    
    # Thresholds
    PSI_THRESHOLD_LOW = 0.1
    PSI_THRESHOLD_HIGH = 0.2
    JS_THRESHOLD_LOW = 0.05
    JS_THRESHOLD_HIGH = 0.1
    PERFORMANCE_THRESHOLD = 0.05  # 5% degradation
    
    def __init__(
        self,
        model_name: str,
        model_version: str,
        redis_client: Optional[Any] = None,  # redis.Redis type
        baseline_window_days: int = 30,
        detection_window_days: int = 7
    ):
        self.model_name = model_name
        self.model_version = model_version
        self.redis = redis_client
        self.baseline_window_days = baseline_window_days
        self.detection_window_days = detection_window_days
        
        # Data windows
        self.baseline_window = DataWindow()
        self.current_window = DataWindow()
        
        # Feature importance for weighted drift
        self.feature_importance: Dict[str, float] = {}
        
        # Statistical tests
        self.tests = StatisticalTests()
    
    def set_baseline(self, window: DataWindow):
        """Set baseline data window."""
        self.baseline_window = window
        logger.info(
            f"Baseline set for {self.model_name}",
            extra={"samples": window.size()}
        )
    
    def record_prediction(
        self,
        features: Dict[str, float],
        prediction: float,
        actual: Optional[float] = None
    ):
        """Record a prediction for monitoring."""
        self.current_window.add_sample(features, prediction, actual)
    
    async def detect_drift(
        self,
        alpha: float = 0.05
    ) -> DriftReport:
        """
        Run comprehensive drift detection.
        """
        report_id = hashlib.md5(
            f"{self.model_name}:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:12]
        
        drift_types = []
        drifted_features = []
        feature_drifts = []
        recommendations = []
        
        # 1. Data Drift Detection (per feature)
        for feature_name in self.baseline_window.features.keys():
            baseline_data = self.baseline_window.get_feature_array(feature_name)
            current_data = self.current_window.get_feature_array(feature_name)
            
            if len(baseline_data) < 100 or len(current_data) < 100:
                continue
            
            feature_drift = self._detect_feature_drift(
                feature_name, baseline_data, current_data, alpha
            )
            feature_drifts.append(feature_drift)
            
            if feature_drift.drift_detected:
                drifted_features.append(feature_name)
        
        if drifted_features:
            drift_types.append(DriftType.DATA_DRIFT)
            recommendations.append(
                f"Data drift detected in {len(drifted_features)} features: "
                f"{', '.join(drifted_features[:5])}"
            )
        
        # 2. Prediction Drift Detection
        baseline_preds = np.array(self.baseline_window.predictions)
        current_preds = np.array(self.current_window.predictions)
        
        pred_drift_score = 0.0
        pred_drift_detected = False
        
        if len(baseline_preds) >= 100 and len(current_preds) >= 100:
            pred_drift_score = self.tests.population_stability_index(
                baseline_preds, current_preds
            )
            pred_drift_detected = pred_drift_score > self.PSI_THRESHOLD_LOW
            
            if pred_drift_detected:
                drift_types.append(DriftType.PREDICTION_DRIFT)
                recommendations.append(
                    f"Prediction distribution has shifted (PSI: {pred_drift_score:.3f})"
                )
        
        # 3. Performance Drift Detection
        baseline_perf, current_perf, perf_degradation = self._detect_performance_drift()
        
        if any(deg > self.PERFORMANCE_THRESHOLD for deg in perf_degradation.values()):
            drift_types.append(DriftType.PERFORMANCE_DRIFT)
            recommendations.append(
                "Model performance has degraded. Consider retraining."
            )
        
        # 4. Concept Drift Detection (if actuals available)
        if len(self.current_window.actuals) >= 100:
            concept_drift = self._detect_concept_drift()
            if concept_drift:
                drift_types.append(DriftType.CONCEPT_DRIFT)
                recommendations.append(
                    "Concept drift detected. Input-output relationship has changed."
                )
        
        # Determine overall severity
        severity = self._calculate_severity(
            feature_drifts, pred_drift_score, perf_degradation
        )
        
        # Add recommendations based on severity
        if severity == DriftSeverity.CRITICAL:
            recommendations.insert(0, "CRITICAL: Immediate model retraining recommended")
        elif severity == DriftSeverity.HIGH:
            recommendations.insert(0, "HIGH: Schedule model retraining soon")
        elif severity == DriftSeverity.MEDIUM:
            recommendations.insert(0, "MEDIUM: Monitor closely and plan retraining")
        
        report = DriftReport(
            report_id=report_id,
            model_name=self.model_name,
            model_version=self.model_version,
            baseline_start=self.baseline_window.timestamps[0] if self.baseline_window.timestamps else datetime.utcnow(),
            baseline_end=self.baseline_window.timestamps[-1] if self.baseline_window.timestamps else datetime.utcnow(),
            detection_start=self.current_window.timestamps[0] if self.current_window.timestamps else datetime.utcnow(),
            detection_end=self.current_window.timestamps[-1] if self.current_window.timestamps else datetime.utcnow(),
            generated_at=datetime.utcnow(),
            drift_detected=len(drift_types) > 0,
            overall_severity=severity,
            drift_types_detected=drift_types,
            feature_drifts=feature_drifts,
            drifted_features=drifted_features,
            prediction_drift_score=pred_drift_score,
            prediction_drift_detected=pred_drift_detected,
            baseline_performance=baseline_perf,
            current_performance=current_perf,
            performance_degradation=perf_degradation,
            recommendations=recommendations,
            samples_baseline=self.baseline_window.size(),
            samples_current=self.current_window.size()
        )
        
        # Store report
        await self._store_report(report)
        
        logger.info(
            f"Drift detection complete for {self.model_name}",
            extra={
                "drift_detected": report.drift_detected,
                "severity": severity.value,
                "drifted_features": len(drifted_features)
            }
        )
        
        return report
    
    def _detect_feature_drift(
        self,
        feature_name: str,
        baseline: np.ndarray,
        current: np.ndarray,
        alpha: float
    ) -> FeatureDrift:
        """Detect drift for a single feature."""
        # Run multiple tests
        ks_stat, ks_p, ks_drift = self.tests.kolmogorov_smirnov(baseline, current, alpha)
        psi = self.tests.population_stability_index(baseline, current)
        js = self.tests.jensen_shannon_divergence(baseline, current)
        
        # Use PSI as primary drift score
        drift_score = min(psi / self.PSI_THRESHOLD_HIGH, 1.0)
        drift_detected = psi > self.PSI_THRESHOLD_LOW or ks_drift
        
        # Determine severity
        if psi > self.PSI_THRESHOLD_HIGH:
            severity = DriftSeverity.HIGH
        elif psi > self.PSI_THRESHOLD_LOW:
            severity = DriftSeverity.MEDIUM
        elif ks_drift:
            severity = DriftSeverity.LOW
        else:
            severity = DriftSeverity.NONE
        
        return FeatureDrift(
            feature_name=feature_name,
            drift_detected=drift_detected,
            drift_score=drift_score,
            p_value=float(ks_p),
            test_statistic=float(ks_stat),
            test_method="ks+psi",
            baseline_stats={
                "mean": float(np.mean(baseline)),
                "std": float(np.std(baseline)),
                "min": float(np.min(baseline)),
                "max": float(np.max(baseline)),
                "median": float(np.median(baseline))
            },
            current_stats={
                "mean": float(np.mean(current)),
                "std": float(np.std(current)),
                "min": float(np.min(current)),
                "max": float(np.max(current)),
                "median": float(np.median(current))
            },
            severity=severity
        )
    
    def _detect_performance_drift(self) -> Tuple[Dict, Dict, Dict]:
        """Detect performance degradation."""
        baseline_perf = {}
        current_perf = {}
        degradation = {}
        
        # Calculate metrics if actuals available
        baseline_actuals = np.array(self.baseline_window.actuals)
        baseline_preds = np.array(self.baseline_window.predictions[:len(baseline_actuals)])
        
        current_actuals = np.array(self.current_window.actuals)
        current_preds = np.array(self.current_window.predictions[:len(current_actuals)])
        
        if len(baseline_actuals) >= 50:
            baseline_perf["mae"] = float(np.mean(np.abs(baseline_actuals - baseline_preds)))
            baseline_perf["rmse"] = float(np.sqrt(np.mean((baseline_actuals - baseline_preds) ** 2)))
            with np.errstate(divide='ignore', invalid='ignore'):
                mape = np.mean(np.abs((baseline_actuals - baseline_preds) / baseline_actuals)) * 100
                baseline_perf["mape"] = float(mape) if not (np.isnan(mape) or np.isinf(mape)) else None
        
        if len(current_actuals) >= 50:
            current_perf["mae"] = float(np.mean(np.abs(current_actuals - current_preds)))
            current_perf["rmse"] = float(np.sqrt(np.mean((current_actuals - current_preds) ** 2)))
            with np.errstate(divide='ignore', invalid='ignore'):
                mape = np.mean(np.abs((current_actuals - current_preds) / current_actuals)) * 100
                current_perf["mape"] = float(mape) if not (np.isnan(mape) or np.isinf(mape)) else None
        
        # Calculate degradation
        for metric in ["mae", "rmse", "mape"]:
            if metric in baseline_perf and metric in current_perf:
                baseline_val = baseline_perf[metric]
                current_val = current_perf[metric]
                if baseline_val and baseline_val > 0:
                    degradation[metric] = (current_val - baseline_val) / baseline_val
                else:
                    degradation[metric] = 0.0
        
        return baseline_perf, current_perf, degradation
    
    def _detect_concept_drift(self) -> bool:
        """
        Detect concept drift using prediction error analysis.
        """
        current_actuals = np.array(self.current_window.actuals)
        current_preds = np.array(self.current_window.predictions[:len(current_actuals)])
        
        if len(current_actuals) < 100:
            return False
        
        # Calculate rolling error
        errors = current_actuals - current_preds
        
        # Split into windows and check for trend
        window_size = len(errors) // 5
        if window_size < 20:
            return False
        
        window_means = []
        for i in range(5):
            start = i * window_size
            end = (i + 1) * window_size
            window_means.append(np.mean(np.abs(errors[start:end])))
        
        # Check for increasing trend in errors
        correlation = np.corrcoef(range(5), window_means)[0, 1]
        
        return bool(correlation > 0.7)  # Strong positive correlation = concept drift
    
    def _calculate_severity(
        self,
        feature_drifts: List[FeatureDrift],
        pred_drift_score: float,
        perf_degradation: Dict
    ) -> DriftSeverity:
        """Calculate overall drift severity."""
        # Count high severity features
        high_drift_features = len([
            f for f in feature_drifts
            if f.severity in [DriftSeverity.HIGH, DriftSeverity.CRITICAL]
        ])
        
        medium_drift_features = len([
            f for f in feature_drifts
            if f.severity == DriftSeverity.MEDIUM
        ])
        
        # Check prediction drift
        pred_severity = DriftSeverity.NONE
        if pred_drift_score > self.PSI_THRESHOLD_HIGH:
            pred_severity = DriftSeverity.HIGH
        elif pred_drift_score > self.PSI_THRESHOLD_LOW:
            pred_severity = DriftSeverity.MEDIUM
        
        # Check performance degradation
        perf_severity = DriftSeverity.NONE
        max_degradation = max(perf_degradation.values()) if perf_degradation else 0
        if max_degradation > 0.2:
            perf_severity = DriftSeverity.CRITICAL
        elif max_degradation > 0.1:
            perf_severity = DriftSeverity.HIGH
        elif max_degradation > 0.05:
            perf_severity = DriftSeverity.MEDIUM
        
        # Overall severity
        if perf_severity == DriftSeverity.CRITICAL or high_drift_features > 3:
            return DriftSeverity.CRITICAL
        elif perf_severity == DriftSeverity.HIGH or high_drift_features > 1:
            return DriftSeverity.HIGH
        elif pred_severity == DriftSeverity.HIGH or medium_drift_features > 3:
            return DriftSeverity.MEDIUM
        elif medium_drift_features > 0 or pred_severity == DriftSeverity.MEDIUM:
            return DriftSeverity.LOW
        
        return DriftSeverity.NONE
    
    async def _store_report(self, report: DriftReport):
        """Store drift report."""
        if self.redis:
            try:
                key = f"drift:report:{self.model_name}:{report.report_id}"
                await self.redis.setex(
                    key,
                    86400 * 30,  # 30 days
                    json.dumps(report.to_dict())
                )
                
                # Store in time series
                ts_key = f"drift:history:{self.model_name}"
                await self.redis.zadd(
                    ts_key,
                    {report.report_id: report.generated_at.timestamp()}
                )
            except Exception as e:
                logger.warning(f"Failed to store drift report: {e}")
