"""
Weight Calibration Framework

Calibrates risk layer weights using historical loss data.
This is THE CRITICAL component that replaces hardcoded weights
with empirically-derived, data-driven weights.

The goal: weights should reflect ACTUAL contribution of each
risk factor to observed losses.
"""

import numpy as np
from scipy.optimize import minimize, differential_evolution
from scipy.stats import spearmanr, pearsonr
from sklearn.isotonic import IsotonicRegression
from sklearn.model_selection import KFold
from sklearn.metrics import mean_squared_error, mean_absolute_error
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Callable
from enum import Enum
import hashlib
import json
import logging

from app.data.historical.loss_data_repository import CalibrationDataset
from app.core.audit_ledger.ledger import AuditLedger

logger = logging.getLogger(__name__)


class CalibrationMethod(Enum):
    """Calibration methods available."""
    ISOTONIC_REGRESSION = "ISOTONIC_REGRESSION"  # Non-parametric, monotonic
    GRADIENT_DESCENT = "GRADIENT_DESCENT"         # Optimize weights directly
    DIFFERENTIAL_EVOLUTION = "DIFFERENTIAL_EVOLUTION"  # Global optimization
    ENSEMBLE = "ENSEMBLE"                         # Combine multiple methods


class CalibrationObjective(Enum):
    """Optimization objectives."""
    MINIMIZE_MSE = "MINIMIZE_MSE"          # Minimize mean squared error
    MINIMIZE_MAE = "MINIMIZE_MAE"          # Minimize mean absolute error
    MAXIMIZE_CORRELATION = "MAXIMIZE_CORRELATION"  # Maximize rank correlation
    BALANCED = "BALANCED"                   # Combination of objectives


@dataclass
class LayerWeight:
    """Calibrated weight for a risk layer."""
    layer_name: str
    original_weight: float      # From hardcoded defaults
    calibrated_weight: float    # From historical data
    weight_change: float        # Difference
    confidence_interval: Tuple[float, float]  # 95% CI
    importance_rank: int        # Rank among all layers
    sample_size: int            # Data points used
    statistical_significance: float  # p-value


@dataclass
class CalibrationResult:
    """Result of weight calibration."""
    # Identification
    calibration_id: str
    dataset_hash: str
    method: CalibrationMethod
    objective: CalibrationObjective
    
    # Calibrated weights
    layer_weights: Dict[str, LayerWeight]
    
    # Performance metrics (before calibration)
    before_mse: float
    before_mae: float
    before_correlation: float
    
    # Performance metrics (after calibration)
    after_mse: float
    after_mae: float
    after_correlation: float
    
    # Improvement
    mse_improvement_pct: float
    mae_improvement_pct: float
    correlation_improvement_pct: float
    
    # Validation
    cross_validation_score: float
    overfitting_risk: str  # "LOW", "MEDIUM", "HIGH"
    
    # Metadata
    sample_size: int
    calibrated_at: datetime
    calibration_hash: str
    
    # Recommendations
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "calibration_id": self.calibration_id,
            "dataset_hash": self.dataset_hash,
            "method": self.method.value,
            "objective": self.objective.value,
            "layer_weights": {
                name: {
                    "layer_name": w.layer_name,
                    "original_weight": w.original_weight,
                    "calibrated_weight": w.calibrated_weight,
                    "weight_change": w.weight_change,
                    "confidence_interval": w.confidence_interval,
                    "importance_rank": w.importance_rank,
                    "sample_size": w.sample_size,
                    "statistical_significance": w.statistical_significance,
                }
                for name, w in self.layer_weights.items()
            },
            "before_mse": self.before_mse,
            "before_mae": self.before_mae,
            "before_correlation": self.before_correlation,
            "after_mse": self.after_mse,
            "after_mae": self.after_mae,
            "after_correlation": self.after_correlation,
            "mse_improvement_pct": self.mse_improvement_pct,
            "mae_improvement_pct": self.mae_improvement_pct,
            "correlation_improvement_pct": self.correlation_improvement_pct,
            "cross_validation_score": self.cross_validation_score,
            "overfitting_risk": self.overfitting_risk,
            "sample_size": self.sample_size,
            "calibrated_at": self.calibrated_at.isoformat(),
            "calibration_hash": self.calibration_hash,
            "recommendations": self.recommendations,
        }


class WeightCalibrator:
    """
    Calibrates risk layer weights using historical loss data.
    
    This is what transforms RISKCAST from a research prototype
    with hardcoded weights into a production system with
    empirically-validated weights.
    """
    
    # Default weights (the ones we're replacing)
    DEFAULT_WEIGHTS = {
        "route_risk": 0.15,
        "cargo_risk": 0.12,
        "transport_risk": 0.10,
        "commercial_risk": 0.08,
        "infrastructure_risk": 0.08,
        "weather_risk": 0.10,
        "geopolitical_risk": 0.07,
        "seasonal_risk": 0.06,
        "documentation_risk": 0.05,
        "handling_risk": 0.07,
        "security_risk": 0.05,
        "regulatory_risk": 0.04,
        "financial_risk": 0.03,
    }
    
    def __init__(self, audit: Optional[AuditLedger] = None):
        self.audit = audit
        self.logger = logging.getLogger(__name__)
        
        # Constraints for weights
        self.MIN_WEIGHT = 0.01  # No weight can be < 1%
        self.MAX_WEIGHT = 0.30  # No weight can be > 30%
        self.WEIGHT_SUM = 1.0   # Weights must sum to 1
    
    async def calibrate(
        self,
        dataset: CalibrationDataset,
        method: CalibrationMethod = CalibrationMethod.ENSEMBLE,
        objective: CalibrationObjective = CalibrationObjective.BALANCED
    ) -> CalibrationResult:
        """
        Calibrate weights using historical data.
        
        This is the main entry point for calibration.
        """
        self.logger.info(
            f"Starting calibration with {dataset.total_shipments} shipments, "
            f"method={method.value}, objective={objective.value}"
        )
        
        # 1. Extract features and targets from dataset
        X, y, feature_names = self._prepare_data(dataset)
        
        if len(X) < 100:
            raise ValueError(
                f"Insufficient data for calibration. Need at least 100 shipments, "
                f"got {len(X)}. Collect more historical data."
            )
        
        # 2. Calculate baseline performance (with default weights)
        baseline_predictions = self._predict_with_weights(X, self.DEFAULT_WEIGHTS, feature_names)
        before_mse = mean_squared_error(y, baseline_predictions)
        before_mae = mean_absolute_error(y, baseline_predictions)
        before_corr, _ = spearmanr(y, baseline_predictions)
        
        self.logger.info(
            f"Baseline performance: MSE={before_mse:.4f}, MAE={before_mae:.4f}, "
            f"Correlation={before_corr:.4f}"
        )
        
        # 3. Run calibration based on method
        if method == CalibrationMethod.ISOTONIC_REGRESSION:
            calibrated_weights = self._calibrate_isotonic(X, y, feature_names)
        elif method == CalibrationMethod.GRADIENT_DESCENT:
            calibrated_weights = self._calibrate_gradient(X, y, feature_names, objective)
        elif method == CalibrationMethod.DIFFERENTIAL_EVOLUTION:
            calibrated_weights = self._calibrate_evolution(X, y, feature_names, objective)
        elif method == CalibrationMethod.ENSEMBLE:
            calibrated_weights = self._calibrate_ensemble(X, y, feature_names, objective)
        else:
            raise ValueError(f"Unknown calibration method: {method}")
        
        # 4. Calculate calibrated performance
        calibrated_predictions = self._predict_with_weights(X, calibrated_weights, feature_names)
        after_mse = mean_squared_error(y, calibrated_predictions)
        after_mae = mean_absolute_error(y, calibrated_predictions)
        after_corr, _ = spearmanr(y, calibrated_predictions)
        
        self.logger.info(
            f"Calibrated performance: MSE={after_mse:.4f}, MAE={after_mae:.4f}, "
            f"Correlation={after_corr:.4f}"
        )
        
        # 5. Cross-validation to check overfitting
        cv_score = self._cross_validate(X, y, calibrated_weights, feature_names)
        overfitting_risk = self._assess_overfitting_risk(
            after_mse, cv_score, len(X), len(feature_names)
        )
        
        # 6. Calculate confidence intervals and significance
        layer_weights = self._compute_weight_statistics(
            X, y, feature_names, calibrated_weights, dataset.total_shipments
        )
        
        # 7. Generate recommendations
        recommendations = self._generate_recommendations(
            layer_weights, before_corr, after_corr, overfitting_risk
        )
        
        # 8. Create result
        calibration_id = self._generate_calibration_id(
            dataset.dataset_hash, method, objective
        )
        
        result = CalibrationResult(
            calibration_id=calibration_id,
            dataset_hash=dataset.dataset_hash,
            method=method,
            objective=objective,
            layer_weights=layer_weights,
            before_mse=before_mse,
            before_mae=before_mae,
            before_correlation=before_corr,
            after_mse=after_mse,
            after_mae=after_mae,
            after_correlation=after_corr,
            mse_improvement_pct=(before_mse - after_mse) / before_mse * 100 if before_mse > 0 else 0,
            mae_improvement_pct=(before_mae - after_mae) / before_mae * 100 if before_mae > 0 else 0,
            correlation_improvement_pct=(after_corr - before_corr) / abs(before_corr) * 100 if before_corr != 0 else 0,
            cross_validation_score=cv_score,
            overfitting_risk=overfitting_risk,
            sample_size=len(X),
            calibrated_at=datetime.utcnow(),
            calibration_hash=self._compute_calibration_hash(calibrated_weights),
            recommendations=recommendations
        )
        
        # 9. Audit the calibration
        if self.audit:
            try:
                tenant_id = getattr(self.audit, 'tenant_id', None) or "system"
                self.audit.append_event(
                    tenant_id=tenant_id,
                    event_type="MODEL_CALIBRATION",
                    action="WEIGHTS_CALIBRATED",
                    entity_type="calibration",
                    entity_id=calibration_id,
                    actor_type="SYSTEM",
                    payload={
                        "method": method.value,
                        "objective": objective.value,
                        "sample_size": len(X),
                        "before_mse": before_mse,
                        "after_mse": after_mse,
                        "improvement_pct": result.mse_improvement_pct,
                        "overfitting_risk": overfitting_risk,
                        "calibration_hash": result.calibration_hash
                    }
                )
            except Exception as e:
                self.logger.warning(f"Failed to audit calibration: {e}")
        
        return result
    
    def _prepare_data(
        self,
        dataset: CalibrationDataset
    ) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        Prepare data for calibration.
        
        Extracts risk factor scores and actual loss percentages.
        """
        feature_names = list(self.DEFAULT_WEIGHTS.keys())
        X = []
        y = []
        
        for shipment in dataset.shipments:
            # Extract risk factors from shipment
            risk_factors = shipment.get("risk_factors", {})
            
            # Build feature vector
            features = []
            for layer_name in feature_names:
                # Get the layer's risk score (0-10 scale)
                layer_score = risk_factors.get(layer_name, 5.0)  # Default to middle
                features.append(layer_score / 10.0)  # Normalize to 0-1
            
            X.append(features)
            
            # Target is actual loss percentage (0-1)
            loss_pct = shipment.get("loss_percentage", 0.0)
            y.append(loss_pct)
        
        return np.array(X), np.array(y), feature_names
    
    def _predict_with_weights(
        self,
        X: np.ndarray,
        weights: Dict[str, float],
        feature_names: List[str]
    ) -> np.ndarray:
        """Predict risk scores using given weights."""
        weight_vector = np.array([weights.get(name, 0.0) for name in feature_names])
        return X @ weight_vector
    
    def _calibrate_isotonic(
        self,
        X: np.ndarray,
        y: np.ndarray,
        feature_names: List[str]
    ) -> Dict[str, float]:
        """
        Calibrate using isotonic regression for each layer.
        
        This is a non-parametric method that ensures monotonicity
        (higher risk scores → higher losses).
        """
        calibrated_weights = {}
        
        for i, layer_name in enumerate(feature_names):
            # Fit isotonic regression for this layer
            ir = IsotonicRegression(out_of_bounds='clip')
            ir.fit(X[:, i], y)
            
            # The "weight" is the average slope of the isotonic function
            # Higher slope = more important layer
            x_sorted = np.sort(X[:, i])
            y_pred = ir.predict(x_sorted)
            
            if len(x_sorted) > 1 and (x_sorted[-1] - x_sorted[0]) > 0:
                slope = (y_pred[-1] - y_pred[0]) / (x_sorted[-1] - x_sorted[0])
            else:
                slope = self.DEFAULT_WEIGHTS[layer_name]
            
            calibrated_weights[layer_name] = max(self.MIN_WEIGHT, abs(slope))
        
        # Normalize weights to sum to 1
        return self._normalize_weights(calibrated_weights)
    
    def _calibrate_gradient(
        self,
        X: np.ndarray,
        y: np.ndarray,
        feature_names: List[str],
        objective: CalibrationObjective
    ) -> Dict[str, float]:
        """
        Calibrate using gradient-based optimization.
        
        Directly optimizes weights to minimize prediction error.
        """
        n_features = len(feature_names)
        
        # Initial weights from defaults
        w0 = np.array([self.DEFAULT_WEIGHTS[name] for name in feature_names])
        
        # Define objective function
        def objective_fn(w):
            # Ensure weights are normalized
            w_normalized = w / w.sum()
            predictions = X @ w_normalized
            
            if objective == CalibrationObjective.MINIMIZE_MSE:
                return mean_squared_error(y, predictions)
            elif objective == CalibrationObjective.MINIMIZE_MAE:
                return mean_absolute_error(y, predictions)
            elif objective == CalibrationObjective.MAXIMIZE_CORRELATION:
                corr, _ = spearmanr(y, predictions)
                return -corr  # Negative because we minimize
            elif objective == CalibrationObjective.BALANCED:
                mse = mean_squared_error(y, predictions)
                corr, _ = spearmanr(y, predictions)
                return mse - 0.1 * corr  # Balance MSE and correlation
            else:
                return mean_squared_error(y, predictions)
        
        # Constraints: weights must be positive and sum to ~1
        bounds = [(self.MIN_WEIGHT, self.MAX_WEIGHT) for _ in range(n_features)]
        
        # Optimize
        result = minimize(
            objective_fn,
            w0,
            method='L-BFGS-B',
            bounds=bounds,
            options={'maxiter': 1000}
        )
        
        # Extract and normalize weights
        calibrated = result.x / result.x.sum()
        
        return {name: float(calibrated[i]) for i, name in enumerate(feature_names)}
    
    def _calibrate_evolution(
        self,
        X: np.ndarray,
        y: np.ndarray,
        feature_names: List[str],
        objective: CalibrationObjective
    ) -> Dict[str, float]:
        """
        Calibrate using differential evolution (global optimization).
        
        Better at finding global optimum, avoids local minima.
        """
        n_features = len(feature_names)
        
        def objective_fn(w):
            w_normalized = w / w.sum()
            predictions = X @ w_normalized
            
            if objective == CalibrationObjective.BALANCED:
                mse = mean_squared_error(y, predictions)
                corr, _ = spearmanr(y, predictions)
                return mse - 0.1 * corr
            elif objective == CalibrationObjective.MINIMIZE_MSE:
                return mean_squared_error(y, predictions)
            elif objective == CalibrationObjective.MINIMIZE_MAE:
                return mean_absolute_error(y, predictions)
            elif objective == CalibrationObjective.MAXIMIZE_CORRELATION:
                corr, _ = spearmanr(y, predictions)
                return -corr
            else:
                return mean_squared_error(y, predictions)
        
        bounds = [(self.MIN_WEIGHT, self.MAX_WEIGHT) for _ in range(n_features)]
        
        result = differential_evolution(
            objective_fn,
            bounds,
            maxiter=500,
            seed=42,  # Reproducibility
            polish=True  # Refine with local search
        )
        
        calibrated = result.x / result.x.sum()
        
        return {name: float(calibrated[i]) for i, name in enumerate(feature_names)}
    
    def _calibrate_ensemble(
        self,
        X: np.ndarray,
        y: np.ndarray,
        feature_names: List[str],
        objective: CalibrationObjective
    ) -> Dict[str, float]:
        """
        Ensemble calibration combining multiple methods.
        
        More robust than any single method.
        """
        # Run multiple methods
        weights_isotonic = self._calibrate_isotonic(X, y, feature_names)
        weights_gradient = self._calibrate_gradient(X, y, feature_names, objective)
        weights_evolution = self._calibrate_evolution(X, y, feature_names, objective)
        
        # Evaluate each
        methods = [
            ("isotonic", weights_isotonic),
            ("gradient", weights_gradient),
            ("evolution", weights_evolution)
        ]
        
        best_score = float('inf')
        best_weights = None
        
        scores = []
        for name, weights in methods:
            predictions = self._predict_with_weights(X, weights, feature_names)
            mse = mean_squared_error(y, predictions)
            scores.append((name, mse, weights))
            
            if mse < best_score:
                best_score = mse
                best_weights = weights
        
        self.logger.info(f"Ensemble scores: {[(n, s) for n, s, _ in scores]}")
        
        # Average weights from top 2 methods
        scores.sort(key=lambda x: x[1])
        top_2 = scores[:2]
        
        averaged = {}
        for layer_name in feature_names:
            avg_weight = sum(w[layer_name] for _, _, w in top_2) / 2
            averaged[layer_name] = avg_weight
        
        return self._normalize_weights(averaged)
    
    def _cross_validate(
        self,
        X: np.ndarray,
        y: np.ndarray,
        weights: Dict[str, float],
        feature_names: List[str],
        n_folds: int = 5
    ) -> float:
        """Cross-validate calibration to check for overfitting."""
        kf = KFold(n_splits=n_folds, shuffle=True, random_state=42)
        
        scores = []
        for train_idx, val_idx in kf.split(X):
            X_train, X_val = X[train_idx], X[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]
            
            # Re-calibrate on training fold
            calibrated = self._calibrate_gradient(
                X_train, y_train, feature_names, CalibrationObjective.MINIMIZE_MSE
            )
            
            # Evaluate on validation fold
            predictions = self._predict_with_weights(X_val, calibrated, feature_names)
            mse = mean_squared_error(y_val, predictions)
            scores.append(mse)
        
        return float(np.mean(scores))
    
    def _assess_overfitting_risk(
        self,
        train_mse: float,
        cv_mse: float,
        n_samples: int,
        n_features: int
    ) -> str:
        """Assess risk of overfitting."""
        # Ratio of CV error to training error
        ratio = cv_mse / train_mse if train_mse > 0 else 1.0
        
        # Also consider sample size vs features
        samples_per_feature = n_samples / n_features if n_features > 0 else 0
        
        if ratio > 1.5 or samples_per_feature < 50:
            return "HIGH"
        elif ratio > 1.2 or samples_per_feature < 100:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _compute_weight_statistics(
        self,
        X: np.ndarray,
        y: np.ndarray,
        feature_names: List[str],
        calibrated_weights: Dict[str, float],
        total_samples: int
    ) -> Dict[str, LayerWeight]:
        """Compute statistics for each calibrated weight."""
        layer_weights = {}
        
        # Bootstrap for confidence intervals
        n_bootstrap = 100
        bootstrap_weights = {name: [] for name in feature_names}
        
        np.random.seed(42)  # Reproducibility
        for _ in range(n_bootstrap):
            # Sample with replacement
            indices = np.random.choice(len(X), size=len(X), replace=True)
            X_boot = X[indices]
            y_boot = y[indices]
            
            # Calibrate on bootstrap sample
            weights_boot = self._calibrate_gradient(
                X_boot, y_boot, feature_names, CalibrationObjective.MINIMIZE_MSE
            )
            
            for name in feature_names:
                bootstrap_weights[name].append(weights_boot[name])
        
        # Calculate statistics
        for i, name in enumerate(feature_names):
            boot_values = np.array(bootstrap_weights[name])
            ci_lower = float(np.percentile(boot_values, 2.5))
            ci_upper = float(np.percentile(boot_values, 97.5))
            
            # Correlation with target for significance
            corr, p_value = spearmanr(X[:, i], y)
            
            layer_weights[name] = LayerWeight(
                layer_name=name,
                original_weight=self.DEFAULT_WEIGHTS[name],
                calibrated_weight=calibrated_weights[name],
                weight_change=calibrated_weights[name] - self.DEFAULT_WEIGHTS[name],
                confidence_interval=(ci_lower, ci_upper),
                importance_rank=0,  # Set below
                sample_size=total_samples,
                statistical_significance=float(p_value) if not np.isnan(p_value) else 1.0
            )
        
        # Set importance ranks
        sorted_layers = sorted(
            layer_weights.values(),
            key=lambda x: x.calibrated_weight,
            reverse=True
        )
        for rank, layer in enumerate(sorted_layers, 1):
            layer_weights[layer.layer_name].importance_rank = rank
        
        return layer_weights
    
    def _generate_recommendations(
        self,
        layer_weights: Dict[str, LayerWeight],
        before_corr: float,
        after_corr: float,
        overfitting_risk: str
    ) -> List[str]:
        """Generate recommendations based on calibration results."""
        recommendations = []
        
        # Check for significant weight changes
        for name, layer in layer_weights.items():
            change_pct = abs(layer.weight_change) / layer.original_weight * 100 if layer.original_weight > 0 else 0
            if change_pct > 50:
                direction = "increased" if layer.weight_change > 0 else "decreased"
                recommendations.append(
                    f"Layer '{name}' weight {direction} significantly ({change_pct:.0f}%). "
                    f"Review if this aligns with domain knowledge."
                )
        
        # Check correlation improvement
        if after_corr > before_corr + 0.1:
            recommendations.append(
                f"Calibration improved correlation by {(after_corr - before_corr):.2f}. "
                f"Model is now better aligned with actual losses."
            )
        elif after_corr < before_corr:
            recommendations.append(
                f"WARNING: Calibration decreased correlation. "
                f"Consider using more data or different method."
            )
        
        # Check overfitting
        if overfitting_risk == "HIGH":
            recommendations.append(
                "HIGH overfitting risk detected. Collect more historical data "
                "or use regularization."
            )
        elif overfitting_risk == "MEDIUM":
            recommendations.append(
                "MEDIUM overfitting risk. Monitor performance on new data."
            )
        
        # Check for insignificant layers
        insignificant = [
            name for name, layer in layer_weights.items()
            if layer.statistical_significance > 0.1
        ]
        if insignificant:
            recommendations.append(
                f"Layers with weak statistical significance: {insignificant}. "
                f"Consider if these should be included."
            )
        
        return recommendations
    
    def _normalize_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        """Normalize weights to sum to 1."""
        total = sum(weights.values())
        if total == 0:
            return self.DEFAULT_WEIGHTS.copy()
        return {k: v / total for k, v in weights.items()}
    
    def _generate_calibration_id(
        self,
        dataset_hash: str,
        method: CalibrationMethod,
        objective: CalibrationObjective
    ) -> str:
        """Generate unique calibration ID."""
        data = f"{dataset_hash}:{method.value}:{objective.value}:{datetime.utcnow().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def _compute_calibration_hash(self, weights: Dict[str, float]) -> str:
        """Compute hash of calibrated weights."""
        canonical = json.dumps(weights, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()


def create_weight_calibrator(audit: Optional[AuditLedger] = None) -> WeightCalibrator:
    """Create weight calibrator instance."""
    return WeightCalibrator(audit)
