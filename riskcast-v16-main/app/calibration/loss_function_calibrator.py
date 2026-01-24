"""
Loss Function Calibration

Calibrates the loss percentage formula:
    loss_pct = (risk_score / 10) ^ exponent

The hardcoded exponent of 1.8 has no empirical basis.
This module calibrates it from actual loss data.
"""

import numpy as np
from scipy.optimize import minimize_scalar, curve_fit
from scipy.stats import kstest, anderson, norm
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional, Callable
from enum import Enum
import hashlib
import json
import logging

from app.data.historical.loss_data_repository import CalibrationDataset
from app.core.audit_ledger.ledger import AuditLedger

logger = logging.getLogger(__name__)


class LossFunctionType(Enum):
    """Types of loss functions to calibrate."""
    POWER = "POWER"           # loss = a * risk^b
    EXPONENTIAL = "EXPONENTIAL"  # loss = a * exp(b * risk)
    LOGISTIC = "LOGISTIC"     # loss = L / (1 + exp(-k * (risk - x0)))
    PIECEWISE = "PIECEWISE"   # Different functions for different risk levels


@dataclass
class LossFunctionParams:
    """Calibrated parameters for a loss function."""
    function_type: LossFunctionType
    parameters: Dict[str, float]
    original_parameters: Dict[str, float]
    parameter_changes: Dict[str, float]
    confidence_intervals: Dict[str, Tuple[float, float]]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "function_type": self.function_type.value,
            "parameters": self.parameters,
            "original_parameters": self.original_parameters,
            "parameter_changes": self.parameter_changes,
            "confidence_intervals": {
                k: list(v) for k, v in self.confidence_intervals.items()
            }
        }


@dataclass
class LossFunctionResult:
    """Result of loss function calibration."""
    calibration_id: str
    dataset_hash: str
    function_type: LossFunctionType
    
    # Calibrated parameters
    params: LossFunctionParams
    
    # The calibrated function (for use in risk engine)
    # Stored as string representation for serialization
    function_formula: str
    
    # Performance metrics (before)
    before_mse: float
    before_mae: float
    before_r2: float
    
    # Performance metrics (after)
    after_mse: float
    after_mae: float
    after_r2: float
    
    # Improvement
    mse_improvement_pct: float
    r2_improvement_pct: float
    
    # Goodness of fit
    residual_normality_test: Dict[str, Any]  # Are residuals normal?
    heteroscedasticity_test: Dict[str, Any]  # Is variance constant?
    
    # Risk level analysis
    performance_by_risk_level: Dict[str, Dict[str, float]]
    
    # Metadata
    sample_size: int
    calibrated_at: datetime
    calibration_hash: str
    
    # Warnings
    warnings: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "calibration_id": self.calibration_id,
            "dataset_hash": self.dataset_hash,
            "function_type": self.function_type.value,
            "params": self.params.to_dict(),
            "function_formula": self.function_formula,
            "before_mse": self.before_mse,
            "before_mae": self.before_mae,
            "before_r2": self.before_r2,
            "after_mse": self.after_mse,
            "after_mae": self.after_mae,
            "after_r2": self.after_r2,
            "mse_improvement_pct": self.mse_improvement_pct,
            "r2_improvement_pct": self.r2_improvement_pct,
            "residual_normality_test": self.residual_normality_test,
            "heteroscedasticity_test": self.heteroscedasticity_test,
            "performance_by_risk_level": self.performance_by_risk_level,
            "sample_size": self.sample_size,
            "calibrated_at": self.calibrated_at.isoformat(),
            "calibration_hash": self.calibration_hash,
            "warnings": self.warnings,
        }


class LossFunctionCalibrator:
    """
    Calibrates the loss function that converts risk scores to expected loss percentages.
    
    The original formula: loss_pct = (risk/10)^1.8
    The 1.8 exponent has no empirical basis and needs calibration.
    """
    
    # Original hardcoded parameters
    ORIGINAL_POWER_PARAMS = {
        "a": 1.0,      # Multiplier
        "b": 1.8,      # Exponent (the magic number we're replacing)
    }
    
    def __init__(self, audit: Optional[AuditLedger] = None):
        self.audit = audit
        self.logger = logging.getLogger(__name__)
    
    async def calibrate(
        self,
        dataset: CalibrationDataset,
        function_type: LossFunctionType = LossFunctionType.POWER
    ) -> LossFunctionResult:
        """
        Calibrate loss function from historical data.
        """
        self.logger.info(
            f"Starting loss function calibration with {dataset.total_shipments} shipments"
        )
        
        # 1. Extract risk scores and actual losses
        risk_scores, actual_losses = self._extract_data(dataset)
        
        if len(risk_scores) < 50:
            raise ValueError(
                f"Insufficient data for calibration. Need at least 50 loss events, "
                f"got {len(risk_scores)}."
            )
        
        # 2. Calculate baseline performance
        baseline_predictions = self._predict_original(risk_scores)
        before_mse = mean_squared_error(actual_losses, baseline_predictions)
        before_mae = mean_absolute_error(actual_losses, baseline_predictions)
        before_r2 = r2_score(actual_losses, baseline_predictions)
        
        self.logger.info(
            f"Baseline: MSE={before_mse:.6f}, MAE={before_mae:.6f}, R²={before_r2:.4f}"
        )
        
        # 3. Calibrate based on function type
        if function_type == LossFunctionType.POWER:
            params, predict_fn = self._calibrate_power(risk_scores, actual_losses)
        elif function_type == LossFunctionType.EXPONENTIAL:
            params, predict_fn = self._calibrate_exponential(risk_scores, actual_losses)
        elif function_type == LossFunctionType.LOGISTIC:
            params, predict_fn = self._calibrate_logistic(risk_scores, actual_losses)
        elif function_type == LossFunctionType.PIECEWISE:
            params, predict_fn = self._calibrate_piecewise(risk_scores, actual_losses)
        else:
            params, predict_fn = self._calibrate_power(risk_scores, actual_losses)
        
        # 4. Calculate calibrated performance
        calibrated_predictions = predict_fn(risk_scores)
        after_mse = mean_squared_error(actual_losses, calibrated_predictions)
        after_mae = mean_absolute_error(actual_losses, calibrated_predictions)
        after_r2 = r2_score(actual_losses, calibrated_predictions)
        
        self.logger.info(
            f"Calibrated: MSE={after_mse:.6f}, MAE={after_mae:.6f}, R²={after_r2:.4f}"
        )
        
        # 5. Residual analysis
        residuals = actual_losses - calibrated_predictions
        normality_test = self._test_residual_normality(residuals)
        heteroscedasticity_test = self._test_heteroscedasticity(
            risk_scores, residuals
        )
        
        # 6. Performance by risk level
        risk_level_perf = self._analyze_by_risk_level(
            risk_scores, actual_losses, calibrated_predictions
        )
        
        # 7. Generate formula string
        formula = self._generate_formula_string(function_type, params)
        
        # 8. Generate warnings
        warnings = self._generate_warnings(
            before_r2, after_r2, normality_test, 
            heteroscedasticity_test, params
        )
        
        # 9. Create result
        calibration_id = self._generate_calibration_id(dataset.dataset_hash, function_type)
        
        result = LossFunctionResult(
            calibration_id=calibration_id,
            dataset_hash=dataset.dataset_hash,
            function_type=function_type,
            params=params,
            function_formula=formula,
            before_mse=before_mse,
            before_mae=before_mae,
            before_r2=before_r2,
            after_mse=after_mse,
            after_mae=after_mae,
            after_r2=after_r2,
            mse_improvement_pct=(before_mse - after_mse) / before_mse * 100 if before_mse > 0 else 0,
            r2_improvement_pct=(after_r2 - before_r2) / abs(before_r2) * 100 if before_r2 != 0 else 0,
            residual_normality_test=normality_test,
            heteroscedasticity_test=heteroscedasticity_test,
            performance_by_risk_level=risk_level_perf,
            sample_size=len(risk_scores),
            calibrated_at=datetime.utcnow(),
            calibration_hash=self._compute_calibration_hash(params),
            warnings=warnings
        )
        
        # 10. Audit
        if self.audit:
            try:
                tenant_id = getattr(self.audit, 'tenant_id', None) or "system"
                self.audit.append_event(
                    tenant_id=tenant_id,
                    event_type="MODEL_CALIBRATION",
                    action="LOSS_FUNCTION_CALIBRATED",
                    entity_type="loss_function",
                    entity_id=calibration_id,
                    actor_type="SYSTEM",
                    payload={
                        "function_type": function_type.value,
                        "sample_size": len(risk_scores),
                        "before_r2": before_r2,
                        "after_r2": after_r2,
                        "improvement_pct": result.mse_improvement_pct,
                        "calibrated_exponent": params.parameters.get("b"),
                        "calibration_hash": result.calibration_hash
                    }
                )
            except Exception as e:
                self.logger.warning(f"Failed to audit loss function calibration: {e}")
        
        return result
    
    def _extract_data(
        self,
        dataset: CalibrationDataset
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Extract risk scores and actual loss percentages."""
        risk_scores = []
        actual_losses = []
        
        for shipment in dataset.shipments:
            # Only use shipments with actual loss data
            loss_pct = shipment.get("loss_percentage")
            risk_score = shipment.get("risk_score_predicted")
            
            if loss_pct is not None and risk_score is not None and loss_pct >= 0:
                risk_scores.append(risk_score)
                actual_losses.append(min(loss_pct, 1.0))  # Cap at 100%
        
        return np.array(risk_scores), np.array(actual_losses)
    
    def _predict_original(self, risk_scores: np.ndarray) -> np.ndarray:
        """Predict using original hardcoded formula."""
        normalized = risk_scores / 10.0
        return np.power(np.clip(normalized, 0.001, 1), self.ORIGINAL_POWER_PARAMS["b"])
    
    def _calibrate_power(
        self,
        risk_scores: np.ndarray,
        actual_losses: np.ndarray
    ) -> Tuple[LossFunctionParams, Callable]:
        """
        Calibrate power function: loss = a * (risk/10)^b
        """
        normalized_risk = risk_scores / 10.0
        
        # Define the power function
        def power_func(x, a, b):
            return a * np.power(np.clip(x, 1e-10, 1), b)
        
        # Fit using curve fitting
        try:
            popt, pcov = curve_fit(
                power_func,
                normalized_risk,
                actual_losses,
                p0=[1.0, 1.8],  # Initial guess from original
                bounds=([0.1, 0.5], [2.0, 4.0]),  # Reasonable bounds
                maxfev=5000
            )
            
            a_calibrated, b_calibrated = popt
            
            # Calculate confidence intervals from covariance
            perr = np.sqrt(np.diag(pcov))
            
            params = LossFunctionParams(
                function_type=LossFunctionType.POWER,
                parameters={"a": float(a_calibrated), "b": float(b_calibrated)},
                original_parameters=self.ORIGINAL_POWER_PARAMS.copy(),
                parameter_changes={
                    "a": float(a_calibrated - self.ORIGINAL_POWER_PARAMS["a"]),
                    "b": float(b_calibrated - self.ORIGINAL_POWER_PARAMS["b"])
                },
                confidence_intervals={
                    "a": (float(a_calibrated - 1.96*perr[0]), float(a_calibrated + 1.96*perr[0])),
                    "b": (float(b_calibrated - 1.96*perr[1]), float(b_calibrated + 1.96*perr[1]))
                }
            )
            
            def predict_fn(x):
                return power_func(x / 10.0, a_calibrated, b_calibrated)
            
            return params, predict_fn
            
        except Exception as e:
            self.logger.warning(f"Curve fit failed: {e}, using optimization")
            return self._calibrate_power_optimization(normalized_risk, actual_losses)
    
    def _calibrate_power_optimization(
        self,
        normalized_risk: np.ndarray,
        actual_losses: np.ndarray
    ) -> Tuple[LossFunctionParams, Callable]:
        """Fallback: optimize exponent using grid search."""
        best_mse = float('inf')
        best_b = 1.8
        
        for b in np.arange(0.5, 4.0, 0.1):
            predictions = np.power(normalized_risk, b)
            mse = mean_squared_error(actual_losses, predictions)
            
            if mse < best_mse:
                best_mse = mse
                best_b = b
        
        # Fine-tune
        try:
            result = minimize_scalar(
                lambda b: mean_squared_error(actual_losses, np.power(normalized_risk, b)),
                bounds=(best_b - 0.2, best_b + 0.2),
                method='bounded'
            )
            b_calibrated = result.x
        except Exception:
            b_calibrated = best_b
        
        params = LossFunctionParams(
            function_type=LossFunctionType.POWER,
            parameters={"a": 1.0, "b": float(b_calibrated)},
            original_parameters=self.ORIGINAL_POWER_PARAMS.copy(),
            parameter_changes={
                "a": 0.0,
                "b": float(b_calibrated - self.ORIGINAL_POWER_PARAMS["b"])
            },
            confidence_intervals={
                "a": (1.0, 1.0),
                "b": (float(b_calibrated - 0.2), float(b_calibrated + 0.2))
            }
        )
        
        def predict_fn(x):
            return np.power(x / 10.0, b_calibrated)
        
        return params, predict_fn
    
    def _calibrate_exponential(
        self,
        risk_scores: np.ndarray,
        actual_losses: np.ndarray
    ) -> Tuple[LossFunctionParams, Callable]:
        """
        Calibrate exponential function: loss = a * exp(b * risk/10)
        """
        normalized_risk = risk_scores / 10.0
        
        def exp_func(x, a, b):
            return a * np.exp(b * x)
        
        try:
            popt, pcov = curve_fit(
                exp_func,
                normalized_risk,
                actual_losses,
                p0=[0.01, 3.0],
                bounds=([0.001, 0.1], [0.5, 10.0]),
                maxfev=5000
            )
            
            a_cal, b_cal = popt
            perr = np.sqrt(np.diag(pcov))
            
            params = LossFunctionParams(
                function_type=LossFunctionType.EXPONENTIAL,
                parameters={"a": float(a_cal), "b": float(b_cal)},
                original_parameters={"a": 0.01, "b": 3.0},
                parameter_changes={"a": float(a_cal - 0.01), "b": float(b_cal - 3.0)},
                confidence_intervals={
                    "a": (float(a_cal - 1.96*perr[0]), float(a_cal + 1.96*perr[0])),
                    "b": (float(b_cal - 1.96*perr[1]), float(b_cal + 1.96*perr[1]))
                }
            )
            
            def predict_fn(x):
                return np.clip(exp_func(x / 10.0, a_cal, b_cal), 0, 1)
            
            return params, predict_fn
            
        except Exception as e:
            self.logger.warning(f"Exponential fit failed: {e}")
            # Fallback to power function
            return self._calibrate_power(risk_scores, actual_losses)
    
    def _calibrate_logistic(
        self,
        risk_scores: np.ndarray,
        actual_losses: np.ndarray
    ) -> Tuple[LossFunctionParams, Callable]:
        """
        Calibrate logistic function: loss = L / (1 + exp(-k * (risk/10 - x0)))
        
        Good for S-shaped relationships where loss saturates at high risk.
        """
        normalized_risk = risk_scores / 10.0
        
        def logistic_func(x, L, k, x0):
            return L / (1 + np.exp(-k * (x - x0)))
        
        try:
            popt, pcov = curve_fit(
                logistic_func,
                normalized_risk,
                actual_losses,
                p0=[1.0, 5.0, 0.5],
                bounds=([0.1, 1.0, 0.1], [1.0, 20.0, 0.9]),
                maxfev=5000
            )
            
            L_cal, k_cal, x0_cal = popt
            perr = np.sqrt(np.diag(pcov))
            
            params = LossFunctionParams(
                function_type=LossFunctionType.LOGISTIC,
                parameters={"L": float(L_cal), "k": float(k_cal), "x0": float(x0_cal)},
                original_parameters={"L": 1.0, "k": 5.0, "x0": 0.5},
                parameter_changes={
                    "L": float(L_cal - 1.0),
                    "k": float(k_cal - 5.0),
                    "x0": float(x0_cal - 0.5)
                },
                confidence_intervals={
                    "L": (float(L_cal - 1.96*perr[0]), float(L_cal + 1.96*perr[0])),
                    "k": (float(k_cal - 1.96*perr[1]), float(k_cal + 1.96*perr[1])),
                    "x0": (float(x0_cal - 1.96*perr[2]), float(x0_cal + 1.96*perr[2]))
                }
            )
            
            def predict_fn(x):
                return np.clip(logistic_func(x / 10.0, L_cal, k_cal, x0_cal), 0, 1)
            
            return params, predict_fn
            
        except Exception as e:
            self.logger.warning(f"Logistic fit failed: {e}")
            return self._calibrate_power(risk_scores, actual_losses)
    
    def _calibrate_piecewise(
        self,
        risk_scores: np.ndarray,
        actual_losses: np.ndarray
    ) -> Tuple[LossFunctionParams, Callable]:
        """
        Calibrate piecewise linear function for different risk levels.
        
        Good when relationship changes at different risk thresholds.
        """
        # Define risk buckets
        low_mask = risk_scores < 3
        med_mask = (risk_scores >= 3) & (risk_scores < 7)
        high_mask = risk_scores >= 7
        
        params_dict = {}
        
        # Fit slope for each bucket
        for name, mask in [("low", low_mask), ("med", med_mask), ("high", high_mask)]:
            if np.sum(mask) > 10:
                x = risk_scores[mask] / 10.0
                y = actual_losses[mask]
                
                # Linear fit
                A = np.vstack([x, np.ones(len(x))]).T
                try:
                    slope, intercept = np.linalg.lstsq(A, y, rcond=None)[0]
                    params_dict[f"{name}_slope"] = float(slope)
                    params_dict[f"{name}_intercept"] = float(intercept)
                except Exception:
                    params_dict[f"{name}_slope"] = 0.1
                    params_dict[f"{name}_intercept"] = 0.0
            else:
                # Not enough data, use defaults
                params_dict[f"{name}_slope"] = 0.1
                params_dict[f"{name}_intercept"] = 0.0
        
        params = LossFunctionParams(
            function_type=LossFunctionType.PIECEWISE,
            parameters=params_dict,
            original_parameters={
                "low_slope": 0.05, "low_intercept": 0.0,
                "med_slope": 0.1, "med_intercept": 0.0,
                "high_slope": 0.2, "high_intercept": 0.0
            },
            parameter_changes={k: params_dict[k] - 0.1 for k in params_dict},
            confidence_intervals={k: (v - 0.05, v + 0.05) for k, v in params_dict.items()}
        )
        
        def predict_fn(x):
            result = np.zeros_like(x, dtype=float)
            
            low_mask = x < 3
            med_mask = (x >= 3) & (x < 7)
            high_mask = x >= 7
            
            x_norm = x / 10.0
            
            result[low_mask] = params_dict["low_slope"] * x_norm[low_mask] + params_dict["low_intercept"]
            result[med_mask] = params_dict["med_slope"] * x_norm[med_mask] + params_dict["med_intercept"]
            result[high_mask] = params_dict["high_slope"] * x_norm[high_mask] + params_dict["high_intercept"]
            
            return np.clip(result, 0, 1)
        
        return params, predict_fn
    
    def _test_residual_normality(
        self,
        residuals: np.ndarray
    ) -> Dict[str, Any]:
        """Test if residuals are normally distributed."""
        try:
            # Kolmogorov-Smirnov test
            ks_stat, ks_pval = kstest(
                residuals, 
                'norm', 
                args=(np.mean(residuals), np.std(residuals))
            )
            
            # Anderson-Darling test
            ad_result = anderson(residuals, dist='norm')
            
            is_normal = ks_pval > 0.05 and len(ad_result.critical_values) > 2 and ad_result.statistic < ad_result.critical_values[2]
            
            return {
                "ks_statistic": float(ks_stat),
                "ks_pvalue": float(ks_pval),
                "ad_statistic": float(ad_result.statistic),
                "ad_critical_5pct": float(ad_result.critical_values[2]) if len(ad_result.critical_values) > 2 else None,
                "is_normal": is_normal,
                "interpretation": "Residuals appear normally distributed" if is_normal 
                               else "Residuals may not be normally distributed"
            }
        except Exception as e:
            self.logger.warning(f"Normality test failed: {e}")
            return {
                "is_normal": False,
                "interpretation": "Normality test failed",
                "error": str(e)
            }
    
    def _test_heteroscedasticity(
        self,
        risk_scores: np.ndarray,
        residuals: np.ndarray
    ) -> Dict[str, Any]:
        """Test if variance is constant across risk levels."""
        try:
            # Split into low/high risk
            median_risk = np.median(risk_scores)
            low_var = np.var(residuals[risk_scores < median_risk])
            high_var = np.var(residuals[risk_scores >= median_risk])
            
            ratio = max(low_var, high_var) / (min(low_var, high_var) + 1e-10)
            
            is_homoscedastic = ratio < 2.0  # Rule of thumb
            
            return {
                "low_risk_variance": float(low_var),
                "high_risk_variance": float(high_var),
                "variance_ratio": float(ratio),
                "is_homoscedastic": is_homoscedastic,
                "interpretation": "Variance appears constant" if is_homoscedastic
                               else "Variance differs by risk level (heteroscedastic)"
            }
        except Exception as e:
            self.logger.warning(f"Heteroscedasticity test failed: {e}")
            return {
                "is_homoscedastic": True,
                "interpretation": "Test failed",
                "error": str(e)
            }
    
    def _analyze_by_risk_level(
        self,
        risk_scores: np.ndarray,
        actual_losses: np.ndarray,
        predictions: np.ndarray
    ) -> Dict[str, Dict[str, float]]:
        """Analyze performance at different risk levels."""
        results = {}
        
        # Define risk buckets
        buckets = [
            ("low_risk", 0, 3),
            ("medium_risk", 3, 7),
            ("high_risk", 7, 10)
        ]
        
        for name, low, high in buckets:
            mask = (risk_scores >= low) & (risk_scores < high)
            
            if np.sum(mask) > 5:
                bucket_actual = actual_losses[mask]
                bucket_pred = predictions[mask]
                
                results[name] = {
                    "count": int(np.sum(mask)),
                    "avg_actual_loss": float(np.mean(bucket_actual)),
                    "avg_predicted_loss": float(np.mean(bucket_pred)),
                    "mse": float(mean_squared_error(bucket_actual, bucket_pred)),
                    "mae": float(mean_absolute_error(bucket_actual, bucket_pred)),
                    "bias": float(np.mean(bucket_pred - bucket_actual))
                }
            else:
                results[name] = {"count": int(np.sum(mask)), "note": "Insufficient data"}
        
        return results
    
    def _generate_formula_string(
        self,
        function_type: LossFunctionType,
        params: LossFunctionParams
    ) -> str:
        """Generate human-readable formula string."""
        p = params.parameters
        
        if function_type == LossFunctionType.POWER:
            return f"loss = {p['a']:.4f} * (risk/10)^{p['b']:.4f}"
        elif function_type == LossFunctionType.EXPONENTIAL:
            return f"loss = {p['a']:.6f} * exp({p['b']:.4f} * risk/10)"
        elif function_type == LossFunctionType.LOGISTIC:
            return f"loss = {p['L']:.4f} / (1 + exp(-{p['k']:.4f} * (risk/10 - {p['x0']:.4f})))"
        elif function_type == LossFunctionType.PIECEWISE:
            return (
                f"loss = {p['low_slope']:.4f}*x + {p['low_intercept']:.4f} (risk<3), "
                f"{p['med_slope']:.4f}*x + {p['med_intercept']:.4f} (3≤risk<7), "
                f"{p['high_slope']:.4f}*x + {p['high_intercept']:.4f} (risk≥7)"
            )
        else:
            return "Unknown function type"
    
    def _generate_warnings(
        self,
        before_r2: float,
        after_r2: float,
        normality_test: Dict[str, Any],
        heteroscedasticity_test: Dict[str, Any],
        params: LossFunctionParams
    ) -> List[str]:
        """Generate warnings about calibration."""
        warnings = []
        
        if after_r2 < 0.3:
            warnings.append(
                f"R² is low ({after_r2:.2f}). The model explains only "
                f"{after_r2*100:.0f}% of loss variance. Consider additional features."
            )
        
        if after_r2 < before_r2:
            warnings.append(
                "Calibration decreased R². Original function may be better "
                "or data may be insufficient."
            )
        
        if not normality_test.get("is_normal", True):
            warnings.append(
                "Residuals are not normally distributed. "
                "Predictions may be less reliable."
            )
        
        if not heteroscedasticity_test.get("is_homoscedastic", True):
            warnings.append(
                "Variance differs by risk level (heteroscedastic). "
                "Consider separate models for different risk levels."
            )
        
        # Check for extreme parameter changes
        if params.function_type == LossFunctionType.POWER:
            b_change = abs(params.parameter_changes.get("b", 0))
            if b_change > 0.5:
                warnings.append(
                    f"Exponent changed significantly (by {b_change:.2f}). "
                    f"Review if this aligns with domain knowledge."
                )
        
        return warnings
    
    def _generate_calibration_id(
        self,
        dataset_hash: str,
        function_type: LossFunctionType
    ) -> str:
        data = f"loss:{dataset_hash}:{function_type.value}:{datetime.utcnow().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def _compute_calibration_hash(self, params: LossFunctionParams) -> str:
        data = json.dumps(params.parameters, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def get_calibrated_function(
        self,
        result: LossFunctionResult
    ) -> Callable[[np.ndarray], np.ndarray]:
        """
        Get the calibrated loss function for use in risk engine.
        
        Returns a callable that takes risk scores (0-10) and returns loss percentages (0-1).
        """
        p = result.params.parameters
        
        if result.function_type == LossFunctionType.POWER:
            def fn(risk: np.ndarray) -> np.ndarray:
                normalized = np.array(risk) / 10.0
                return p["a"] * np.power(np.clip(normalized, 0.001, 1), p["b"])
            return fn
        
        elif result.function_type == LossFunctionType.EXPONENTIAL:
            def fn(risk: np.ndarray) -> np.ndarray:
                normalized = np.array(risk) / 10.0
                return np.clip(p["a"] * np.exp(p["b"] * normalized), 0, 1)
            return fn
        
        elif result.function_type == LossFunctionType.LOGISTIC:
            def fn(risk: np.ndarray) -> np.ndarray:
                normalized = np.array(risk) / 10.0
                return np.clip(p["L"] / (1 + np.exp(-p["k"] * (normalized - p["x0"]))), 0, 1)
            return fn
        
        elif result.function_type == LossFunctionType.PIECEWISE:
            def fn(risk: np.ndarray) -> np.ndarray:
                risk_arr = np.array(risk)
                result = np.zeros_like(risk_arr, dtype=float)
                
                low_mask = risk_arr < 3
                med_mask = (risk_arr >= 3) & (risk_arr < 7)
                high_mask = risk_arr >= 7
                
                x_norm = risk_arr / 10.0
                
                result[low_mask] = p["low_slope"] * x_norm[low_mask] + p["low_intercept"]
                result[med_mask] = p["med_slope"] * x_norm[med_mask] + p["med_intercept"]
                result[high_mask] = p["high_slope"] * x_norm[high_mask] + p["high_intercept"]
                
                return np.clip(result, 0, 1)
            return fn
        
        else:
            # Default to power function
            def fn(risk: np.ndarray) -> np.ndarray:
                return np.power(np.array(risk) / 10.0, 1.8)
            return fn


def create_loss_function_calibrator(audit: Optional[AuditLedger] = None) -> LossFunctionCalibrator:
    """Create loss function calibrator instance."""
    return LossFunctionCalibrator(audit)
