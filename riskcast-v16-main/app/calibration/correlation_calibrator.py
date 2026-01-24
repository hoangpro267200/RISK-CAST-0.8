"""
Correlation Matrix Calibration

Calibrates the correlation matrix between risk layers using historical data.
Replaces hardcoded correlations like 0.42, 0.52 with empirically-derived values.

Why this matters:
- Correlations affect portfolio risk aggregation
- Hardcoded correlations may not reflect reality
- Wrong correlations lead to wrong VaR/CVaR calculations
"""

import numpy as np
from scipy.stats import spearmanr, pearsonr, kendalltau
from scipy.linalg import cholesky, LinAlgError
from sklearn.covariance import LedoitWolf, EmpiricalCovariance
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
from enum import Enum
import hashlib
import json
import logging

from app.data.historical.loss_data_repository import CalibrationDataset
from app.core.audit_ledger.ledger import AuditLedger

logger = logging.getLogger(__name__)


class CorrelationMethod(Enum):
    """Methods for calculating correlations."""
    PEARSON = "PEARSON"           # Linear correlation
    SPEARMAN = "SPEARMAN"         # Rank correlation
    KENDALL = "KENDALL"           # Kendall's tau
    SHRINKAGE = "SHRINKAGE"       # Ledoit-Wolf shrinkage


@dataclass
class CorrelationPair:
    """Correlation between two risk layers."""
    layer_1: str
    layer_2: str
    original_correlation: float     # From hardcoded matrix
    calibrated_correlation: float   # From historical data
    correlation_change: float
    p_value: float                  # Statistical significance
    sample_size: int
    confidence_interval: Tuple[float, float]
    is_significant: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "layer_1": self.layer_1,
            "layer_2": self.layer_2,
            "original_correlation": self.original_correlation,
            "calibrated_correlation": self.calibrated_correlation,
            "correlation_change": self.correlation_change,
            "p_value": self.p_value,
            "sample_size": self.sample_size,
            "confidence_interval": self.confidence_interval,
            "is_significant": self.is_significant,
        }


@dataclass
class CorrelationMatrixResult:
    """Result of correlation matrix calibration."""
    calibration_id: str
    dataset_hash: str
    method: CorrelationMethod
    
    # The calibrated matrix
    correlation_matrix: np.ndarray
    layer_names: List[str]
    
    # Individual pair statistics
    pair_statistics: List[CorrelationPair]
    
    # Matrix properties
    is_positive_definite: bool
    condition_number: float
    
    # Comparison with original
    max_correlation_change: float
    avg_correlation_change: float
    significant_changes: int
    
    # Stability metrics
    temporal_stability: float       # How stable over time
    bootstrap_stability: float      # How stable across samples
    
    # Metadata
    sample_size: int
    calibrated_at: datetime
    matrix_hash: str
    
    # Warnings
    warnings: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "calibration_id": self.calibration_id,
            "dataset_hash": self.dataset_hash,
            "method": self.method.value,
            "correlation_matrix": self.correlation_matrix.tolist(),
            "layer_names": self.layer_names,
            "pair_statistics": [p.to_dict() for p in self.pair_statistics],
            "is_positive_definite": self.is_positive_definite,
            "condition_number": self.condition_number,
            "max_correlation_change": self.max_correlation_change,
            "avg_correlation_change": self.avg_correlation_change,
            "significant_changes": self.significant_changes,
            "temporal_stability": self.temporal_stability,
            "bootstrap_stability": self.bootstrap_stability,
            "sample_size": self.sample_size,
            "calibrated_at": self.calibrated_at.isoformat(),
            "matrix_hash": self.matrix_hash,
            "warnings": self.warnings,
        }


class CorrelationCalibrator:
    """
    Calibrates correlation matrix from historical data.
    
    The correlation matrix is critical for:
    - Aggregating risk across layers
    - Portfolio VaR calculations
    - Understanding risk interactions
    """
    
    # Original hardcoded correlations (from risk_engine_v16.py)
    # These are the values we're replacing
    ORIGINAL_CORRELATIONS = {
        ("route_risk", "weather_risk"): 0.52,
        ("route_risk", "geopolitical_risk"): 0.38,
        ("cargo_risk", "handling_risk"): 0.45,
        ("cargo_risk", "transport_risk"): 0.42,
        ("weather_risk", "seasonal_risk"): 0.65,
        ("transport_risk", "infrastructure_risk"): 0.35,
        ("commercial_risk", "financial_risk"): 0.55,
        ("documentation_risk", "regulatory_risk"): 0.48,
        ("security_risk", "geopolitical_risk"): 0.42,
        ("route_risk", "infrastructure_risk"): 0.30,
        ("cargo_risk", "security_risk"): 0.25,
        ("weather_risk", "infrastructure_risk"): 0.28,
        ("transport_risk", "handling_risk"): 0.40,
        ("commercial_risk", "documentation_risk"): 0.32,
        ("geopolitical_risk", "regulatory_risk"): 0.35,
    }
    
    LAYER_NAMES = [
        "route_risk", "cargo_risk", "transport_risk", "commercial_risk",
        "infrastructure_risk", "weather_risk", "geopolitical_risk",
        "seasonal_risk", "documentation_risk", "handling_risk",
        "security_risk", "regulatory_risk", "financial_risk"
    ]
    
    def __init__(self, audit: Optional[AuditLedger] = None):
        self.audit = audit
        self.logger = logging.getLogger(__name__)
    
    async def calibrate(
        self,
        dataset: CalibrationDataset,
        method: CorrelationMethod = CorrelationMethod.SHRINKAGE
    ) -> CorrelationMatrixResult:
        """
        Calibrate correlation matrix from historical data.
        """
        self.logger.info(
            f"Starting correlation calibration with {dataset.total_shipments} shipments"
        )
        
        # 1. Extract risk factor scores
        X, layer_names = self._extract_risk_scores(dataset)
        
        if len(X) < 50:
            raise ValueError(
                f"Insufficient data for correlation calibration. "
                f"Need at least 50 shipments, got {len(X)}."
            )
        
        # 2. Calculate correlation matrix
        if method == CorrelationMethod.PEARSON:
            corr_matrix = self._calculate_pearson(X)
        elif method == CorrelationMethod.SPEARMAN:
            corr_matrix = self._calculate_spearman(X)
        elif method == CorrelationMethod.KENDALL:
            corr_matrix = self._calculate_kendall(X)
        elif method == CorrelationMethod.SHRINKAGE:
            corr_matrix = self._calculate_shrinkage(X)
        else:
            corr_matrix = self._calculate_shrinkage(X)
        
        # 3. Ensure positive definiteness
        corr_matrix, was_adjusted = self._ensure_positive_definite(corr_matrix)
        
        # 4. Calculate pair statistics
        pair_stats = self._calculate_pair_statistics(X, layer_names, corr_matrix)
        
        # 5. Calculate stability metrics
        temporal_stability = self._calculate_temporal_stability(dataset, method)
        bootstrap_stability = self._calculate_bootstrap_stability(X, method)
        
        # 6. Compare with original
        original_matrix = self._build_original_matrix(layer_names)
        changes = self._compare_matrices(original_matrix, corr_matrix, layer_names)
        
        # 7. Generate warnings
        warnings = self._generate_warnings(
            corr_matrix, layer_names, pair_stats, 
            was_adjusted, temporal_stability
        )
        
        # 8. Create result
        calibration_id = self._generate_calibration_id(dataset.dataset_hash, method)
        matrix_hash = self._compute_matrix_hash(corr_matrix)
        
        result = CorrelationMatrixResult(
            calibration_id=calibration_id,
            dataset_hash=dataset.dataset_hash,
            method=method,
            correlation_matrix=corr_matrix,
            layer_names=layer_names,
            pair_statistics=pair_stats,
            is_positive_definite=not was_adjusted,
            condition_number=float(np.linalg.cond(corr_matrix)),
            max_correlation_change=changes["max_change"],
            avg_correlation_change=changes["avg_change"],
            significant_changes=changes["significant_count"],
            temporal_stability=temporal_stability,
            bootstrap_stability=bootstrap_stability,
            sample_size=len(X),
            calibrated_at=datetime.utcnow(),
            matrix_hash=matrix_hash,
            warnings=warnings
        )
        
        # 9. Audit
        if self.audit:
            try:
                tenant_id = getattr(self.audit, 'tenant_id', None) or "system"
                self.audit.append_event(
                    tenant_id=tenant_id,
                    event_type="MODEL_CALIBRATION",
                    action="CORRELATION_MATRIX_CALIBRATED",
                    entity_type="correlation_matrix",
                    entity_id=calibration_id,
                    actor_type="SYSTEM",
                    payload={
                        "method": method.value,
                        "sample_size": len(X),
                        "is_positive_definite": result.is_positive_definite,
                        "condition_number": result.condition_number,
                        "avg_change": result.avg_correlation_change,
                        "matrix_hash": matrix_hash
                    }
                )
            except Exception as e:
                self.logger.warning(f"Failed to audit correlation calibration: {e}")
        
        return result
    
    def _extract_risk_scores(
        self,
        dataset: CalibrationDataset
    ) -> Tuple[np.ndarray, List[str]]:
        """Extract risk layer scores from dataset."""
        layer_names = self.LAYER_NAMES
        X = []
        
        for shipment in dataset.shipments:
            risk_factors = shipment.get("risk_factors", {})
            
            row = []
            for layer in layer_names:
                # Get score (0-10 scale, normalize to 0-1)
                score = risk_factors.get(layer, 5.0) / 10.0
                row.append(score)
            
            X.append(row)
        
        return np.array(X), layer_names
    
    def _calculate_pearson(self, X: np.ndarray) -> np.ndarray:
        """Calculate Pearson correlation matrix."""
        return np.corrcoef(X.T)
    
    def _calculate_spearman(self, X: np.ndarray) -> np.ndarray:
        """Calculate Spearman rank correlation matrix."""
        n_features = X.shape[1]
        corr_matrix = np.eye(n_features)
        
        for i in range(n_features):
            for j in range(i + 1, n_features):
                corr, _ = spearmanr(X[:, i], X[:, j])
                if not np.isnan(corr):
                    corr_matrix[i, j] = corr
                    corr_matrix[j, i] = corr
        
        return corr_matrix
    
    def _calculate_kendall(self, X: np.ndarray) -> np.ndarray:
        """Calculate Kendall's tau correlation matrix."""
        n_features = X.shape[1]
        corr_matrix = np.eye(n_features)
        
        for i in range(n_features):
            for j in range(i + 1, n_features):
                corr, _ = kendalltau(X[:, i], X[:, j])
                if not np.isnan(corr):
                    corr_matrix[i, j] = corr
                    corr_matrix[j, i] = corr
        
        return corr_matrix
    
    def _calculate_shrinkage(self, X: np.ndarray) -> np.ndarray:
        """
        Calculate correlation matrix using Ledoit-Wolf shrinkage.
        
        This is the RECOMMENDED method because:
        - More stable for small samples
        - Reduces estimation error
        - Guarantees positive definiteness
        """
        try:
            # Ledoit-Wolf shrinkage estimator
            lw = LedoitWolf().fit(X)
            cov_matrix = lw.covariance_
            
            # Convert covariance to correlation
            std = np.sqrt(np.diag(cov_matrix))
            # Avoid division by zero
            std = np.where(std == 0, 1.0, std)
            corr_matrix = cov_matrix / np.outer(std, std)
            
            # Ensure diagonal is exactly 1
            np.fill_diagonal(corr_matrix, 1.0)
            
            return corr_matrix
        except Exception as e:
            self.logger.warning(f"Shrinkage method failed, falling back to Pearson: {e}")
            return self._calculate_pearson(X)
    
    def _ensure_positive_definite(
        self,
        corr_matrix: np.ndarray
    ) -> Tuple[np.ndarray, bool]:
        """
        Ensure correlation matrix is positive definite.
        
        A non-positive-definite matrix cannot be used for
        Cholesky decomposition in Monte Carlo simulations.
        """
        try:
            # Try Cholesky decomposition
            cholesky(corr_matrix)
            return corr_matrix, False
        except LinAlgError:
            # Matrix is not positive definite, fix it
            self.logger.warning("Correlation matrix not positive definite, adjusting...")
            
            # Eigenvalue adjustment method
            eigenvalues, eigenvectors = np.linalg.eigh(corr_matrix)
            
            # Set negative eigenvalues to small positive
            eigenvalues = np.maximum(eigenvalues, 1e-8)
            
            # Reconstruct matrix
            adjusted = eigenvectors @ np.diag(eigenvalues) @ eigenvectors.T
            
            # Rescale to ensure diagonal is 1
            d = np.sqrt(np.diag(adjusted))
            d = np.where(d == 0, 1.0, d)
            adjusted = adjusted / np.outer(d, d)
            np.fill_diagonal(adjusted, 1.0)
            
            return adjusted, True
    
    def _calculate_pair_statistics(
        self,
        X: np.ndarray,
        layer_names: List[str],
        corr_matrix: np.ndarray
    ) -> List[CorrelationPair]:
        """Calculate statistics for each correlation pair."""
        pairs = []
        n = len(layer_names)
        
        for i in range(n):
            for j in range(i + 1, n):
                layer_1 = layer_names[i]
                layer_2 = layer_names[j]
                
                # Get calibrated correlation
                calibrated = float(corr_matrix[i, j])
                
                # Get original correlation
                key = (layer_1, layer_2)
                rev_key = (layer_2, layer_1)
                original = self.ORIGINAL_CORRELATIONS.get(
                    key, 
                    self.ORIGINAL_CORRELATIONS.get(rev_key, 0.0)
                )
                
                # Calculate p-value
                corr, p_value = spearmanr(X[:, i], X[:, j])
                p_value = float(p_value) if not np.isnan(p_value) else 1.0
                
                # Bootstrap confidence interval
                ci = self._bootstrap_correlation_ci(X[:, i], X[:, j])
                
                pairs.append(CorrelationPair(
                    layer_1=layer_1,
                    layer_2=layer_2,
                    original_correlation=original,
                    calibrated_correlation=calibrated,
                    correlation_change=calibrated - original,
                    p_value=p_value,
                    sample_size=len(X),
                    confidence_interval=ci,
                    is_significant=p_value < 0.05
                ))
        
        return pairs
    
    def _bootstrap_correlation_ci(
        self,
        x: np.ndarray,
        y: np.ndarray,
        n_bootstrap: int = 1000,
        alpha: float = 0.05
    ) -> Tuple[float, float]:
        """Calculate bootstrap confidence interval for correlation."""
        correlations = []
        
        np.random.seed(42)  # Reproducibility
        for _ in range(n_bootstrap):
            indices = np.random.choice(len(x), size=len(x), replace=True)
            corr, _ = spearmanr(x[indices], y[indices])
            if not np.isnan(corr):
                correlations.append(corr)
        
        if not correlations:
            return (0.0, 0.0)
        
        lower = float(np.percentile(correlations, 100 * alpha / 2))
        upper = float(np.percentile(correlations, 100 * (1 - alpha / 2)))
        
        return (lower, upper)
    
    def _calculate_temporal_stability(
        self,
        dataset: CalibrationDataset,
        method: CorrelationMethod
    ) -> float:
        """
        Calculate how stable correlations are over time.
        
        Split data by time and compare correlation matrices.
        """
        shipments = dataset.shipments
        
        if len(shipments) < 60:
            return 0.5  # Not enough data to assess
        
        # Sort by date
        try:
            sorted_shipments = sorted(
                shipments,
                key=lambda x: x.get("shipment_date", "2000-01-01")
            )
        except Exception:
            return 0.5
        
        # Split into halves
        mid = len(sorted_shipments) // 2
        first_half = sorted_shipments[:mid]
        second_half = sorted_shipments[mid:]
        
        if len(first_half) < 30 or len(second_half) < 30:
            return 0.5  # Not enough data to assess
        
        try:
            # Calculate correlations for each half
            X1, _ = self._extract_risk_scores_from_list(first_half)
            X2, _ = self._extract_risk_scores_from_list(second_half)
            
            if method == CorrelationMethod.SHRINKAGE:
                corr1 = self._calculate_shrinkage(X1)
                corr2 = self._calculate_shrinkage(X2)
            elif method == CorrelationMethod.SPEARMAN:
                corr1 = self._calculate_spearman(X1)
                corr2 = self._calculate_spearman(X2)
            else:
                corr1 = self._calculate_pearson(X1)
                corr2 = self._calculate_pearson(X2)
            
            # Compare matrices (correlation of correlations)
            upper1 = corr1[np.triu_indices_from(corr1, k=1)]
            upper2 = corr2[np.triu_indices_from(corr2, k=1)]
            
            stability, _ = pearsonr(upper1, upper2)
            stability = float(stability) if not np.isnan(stability) else 0.5
            
            return max(0, stability)  # Ensure non-negative
        except Exception as e:
            self.logger.warning(f"Failed to calculate temporal stability: {e}")
            return 0.5
    
    def _calculate_bootstrap_stability(
        self,
        X: np.ndarray,
        method: CorrelationMethod,
        n_bootstrap: int = 100
    ) -> float:
        """
        Calculate how stable correlations are across bootstrap samples.
        """
        correlation_matrices = []
        
        np.random.seed(42)  # Reproducibility
        for _ in range(n_bootstrap):
            indices = np.random.choice(len(X), size=len(X), replace=True)
            X_boot = X[indices]
            
            try:
                if method == CorrelationMethod.SHRINKAGE:
                    corr = self._calculate_shrinkage(X_boot)
                elif method == CorrelationMethod.SPEARMAN:
                    corr = self._calculate_spearman(X_boot)
                else:
                    corr = self._calculate_pearson(X_boot)
                
                correlation_matrices.append(corr[np.triu_indices_from(corr, k=1)])
            except Exception:
                continue
        
        if not correlation_matrices:
            return 0.5
        
        # Calculate coefficient of variation for each correlation
        stacked = np.vstack(correlation_matrices)
        mean_vals = np.abs(np.mean(stacked, axis=0))
        mean_vals = np.where(mean_vals == 0, 1e-6, mean_vals)
        cv = np.std(stacked, axis=0) / mean_vals
        
        # Stability is 1 - average CV (higher is more stable)
        stability = 1 - np.mean(cv)
        
        return float(max(0, min(1, stability)))
    
    def _extract_risk_scores_from_list(
        self,
        shipments: List[Dict[str, Any]]
    ) -> Tuple[np.ndarray, List[str]]:
        """Extract risk scores from a list of shipments."""
        layer_names = self.LAYER_NAMES
        X = []
        
        for shipment in shipments:
            risk_factors = shipment.get("risk_factors", {})
            row = [risk_factors.get(layer, 5.0) / 10.0 for layer in layer_names]
            X.append(row)
        
        return np.array(X), layer_names
    
    def _build_original_matrix(self, layer_names: List[str]) -> np.ndarray:
        """Build correlation matrix from original hardcoded values."""
        n = len(layer_names)
        matrix = np.eye(n)
        
        for i, layer_i in enumerate(layer_names):
            for j, layer_j in enumerate(layer_names):
                if i < j:
                    key = (layer_i, layer_j)
                    rev_key = (layer_j, layer_i)
                    corr = self.ORIGINAL_CORRELATIONS.get(
                        key,
                        self.ORIGINAL_CORRELATIONS.get(rev_key, 0.0)
                    )
                    matrix[i, j] = corr
                    matrix[j, i] = corr
        
        return matrix
    
    def _compare_matrices(
        self,
        original: np.ndarray,
        calibrated: np.ndarray,
        layer_names: List[str]
    ) -> Dict[str, Any]:
        """Compare original and calibrated matrices."""
        diff = np.abs(calibrated - original)
        upper_diff = diff[np.triu_indices_from(diff, k=1)]
        
        return {
            "max_change": float(np.max(upper_diff)),
            "avg_change": float(np.mean(upper_diff)),
            "significant_count": int(np.sum(upper_diff > 0.1))  # > 0.1 change
        }
    
    def _generate_warnings(
        self,
        corr_matrix: np.ndarray,
        layer_names: List[str],
        pair_stats: List[CorrelationPair],
        was_adjusted: bool,
        temporal_stability: float
    ) -> List[str]:
        """Generate warnings about the calibration."""
        warnings = []
        
        if was_adjusted:
            warnings.append(
                "Correlation matrix was adjusted to ensure positive definiteness. "
                "This may indicate data quality issues or too few samples."
            )
        
        if temporal_stability < 0.7:
            warnings.append(
                f"Temporal stability is low ({temporal_stability:.2f}). "
                f"Correlations may be changing over time."
            )
        
        # Check for very high correlations
        high_corr = np.where(np.abs(corr_matrix) > 0.8)
        high_pairs = [
            (layer_names[i], layer_names[j])
            for i, j in zip(high_corr[0], high_corr[1])
            if i < j
        ]
        if high_pairs:
            warnings.append(
                f"Very high correlations detected: {high_pairs}. "
                f"Consider if these layers are redundant."
            )
        
        # Check for significant changes from original
        large_changes = [
            p for p in pair_stats
            if abs(p.correlation_change) > 0.2
        ]
        if large_changes:
            pairs = [(p.layer_1, p.layer_2, p.correlation_change) for p in large_changes[:5]]
            warnings.append(
                f"Large correlation changes from original: {pairs}. "
                f"Review if these align with domain knowledge."
            )
        
        return warnings
    
    def _generate_calibration_id(
        self,
        dataset_hash: str,
        method: CorrelationMethod
    ) -> str:
        data = f"corr:{dataset_hash}:{method.value}:{datetime.utcnow().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def _compute_matrix_hash(self, matrix: np.ndarray) -> str:
        return hashlib.sha256(matrix.tobytes()).hexdigest()[:16]
    
    def get_correlation_matrix_dict(
        self,
        result: CorrelationMatrixResult
    ) -> Dict[Tuple[str, str], float]:
        """Convert matrix result to dictionary format for use in risk engine."""
        corr_dict = {}
        
        for i, layer_i in enumerate(result.layer_names):
            for j, layer_j in enumerate(result.layer_names):
                if i < j:
                    corr_dict[(layer_i, layer_j)] = float(result.correlation_matrix[i, j])
        
        return corr_dict


def create_correlation_calibrator(audit: Optional[AuditLedger] = None) -> CorrelationCalibrator:
    """Create correlation calibrator instance."""
    return CorrelationCalibrator(audit)
