"""
RISKCAST Scientific Calibration Framework
==========================================
Calibrate raw FAHP+TOPSIS+MC risk scores to actual probabilities.

Methods:
1. Platt Scaling (logistic regression on scores)
2. Isotonic Regression (monotonic calibration)
3. Bayesian Update (with prior)

Usage:
    python scripts/calibration/calibrator_v2.py --data historical.csv --method isotonic

Author: RISKCAST Team
Version: 2.0
License: Proprietary
"""

import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from scipy import stats
from typing import Dict, Tuple, Optional, List
from dataclasses import dataclass, asdict
import json
import logging
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CalibrationMetrics:
    """Calibration quality metrics."""
    brier_score: float
    expected_calibration_error: float
    log_loss: float
    max_calibration_error: float
    area_under_roc: float
    sample_size: int
    method: str


@dataclass
class CalibrationResult:
    """Complete calibration result."""
    metrics: CalibrationMetrics
    reliability_diagram_data: Dict
    calibration_parameters: Dict
    validation_split_performance: Dict


class RiskScoreCalibrator:
    """
    Calibrate raw FAHP+TOPSIS+MC risk scores to actual probabilities.
    
    This is CRITICAL for insurance underwriting - risk scores must
    correspond to actual incident frequencies.
    
    Attributes:
        method: Calibration method ('platt', 'isotonic', 'bayesian')
        calibrator: Fitted calibration model
        validation_metrics: CalibrationMetrics after fitting
        is_fitted: Whether calibrator has been fit
    """
    
    # Acceptable calibration thresholds (industry standards)
    BRIER_THRESHOLD = 0.15  # Lower is better, 0 = perfect
    ECE_THRESHOLD = 0.05    # Expected Calibration Error
    
    def __init__(self, method: str = 'isotonic'):
        """
        Initialize calibrator.
        
        Args:
            method: 'platt', 'isotonic', or 'bayesian'
        """
        if method not in ('platt', 'isotonic', 'bayesian'):
            raise ValueError(f"Unknown method: {method}. Use 'platt', 'isotonic', or 'bayesian'")
        
        self.method = method
        self.calibrator = None
        self.validation_metrics: Optional[CalibrationMetrics] = None
        self.reliability_data: Optional[Dict] = None
        self.is_fitted = False
        
        # Bayesian prior parameters
        self._prior_alpha = 1.0  # Beta prior
        self._prior_beta = 1.0
        self._bin_alphas = None
        self._bin_betas = None
        self._bin_edges = None
    
    def fit(self, 
            raw_scores: np.ndarray, 
            actual_outcomes: np.ndarray,
            validation_split: float = 0.2) -> 'RiskScoreCalibrator':
        """
        Fit calibration model.
        
        Args:
            raw_scores: Uncalibrated risk scores (0-100)
            actual_outcomes: Binary outcomes (0=no incident, 1=incident)
            validation_split: Fraction of data for validation
            
        Returns:
            self for chaining
        """
        logger.info(f"Fitting {self.method} calibrator on {len(raw_scores)} samples...")
        
        # Input validation
        raw_scores = np.asarray(raw_scores).flatten()
        actual_outcomes = np.asarray(actual_outcomes).flatten()
        
        if len(raw_scores) != len(actual_outcomes):
            raise ValueError("raw_scores and actual_outcomes must have same length")
        
        if not np.all((actual_outcomes == 0) | (actual_outcomes == 1)):
            raise ValueError("actual_outcomes must be binary (0 or 1)")
        
        # Normalize scores to 0-1 for calibration
        scores_normalized = raw_scores / 100.0
        scores_normalized = np.clip(scores_normalized, 0, 1)
        
        # Split data for validation
        n_samples = len(raw_scores)
        n_val = int(n_samples * validation_split)
        indices = np.random.permutation(n_samples)
        
        train_idx = indices[n_val:]
        val_idx = indices[:n_val]
        
        train_scores = scores_normalized[train_idx]
        train_outcomes = actual_outcomes[train_idx]
        val_scores = scores_normalized[val_idx]
        val_outcomes = actual_outcomes[val_idx]
        
        # Fit calibrator
        if self.method == 'platt':
            self._fit_platt(train_scores, train_outcomes)
        elif self.method == 'isotonic':
            self._fit_isotonic(train_scores, train_outcomes)
        elif self.method == 'bayesian':
            self._fit_bayesian(train_scores, train_outcomes)
        
        self.is_fitted = True
        
        # Compute validation metrics
        self._compute_validation_metrics(val_scores, val_outcomes)
        
        logger.info(f"Calibration complete. Brier={self.validation_metrics.brier_score:.4f}, "
                   f"ECE={self.validation_metrics.expected_calibration_error:.4f}")
        
        return self
    
    def _fit_platt(self, scores: np.ndarray, outcomes: np.ndarray):
        """Fit Platt scaling (logistic regression)."""
        self.calibrator = LogisticRegression(solver='lbfgs', max_iter=1000)
        self.calibrator.fit(scores.reshape(-1, 1), outcomes)
    
    def _fit_isotonic(self, scores: np.ndarray, outcomes: np.ndarray):
        """Fit isotonic regression (monotonic calibration)."""
        self.calibrator = IsotonicRegression(
            out_of_bounds='clip',
            increasing=True  # Higher score should mean higher probability
        )
        self.calibrator.fit(scores, outcomes)
    
    def _fit_bayesian(self, scores: np.ndarray, outcomes: np.ndarray, n_bins: int = 20):
        """Fit Bayesian calibration with Beta priors."""
        self._bin_edges = np.linspace(0, 1, n_bins + 1)
        self._bin_alphas = np.ones(n_bins) * self._prior_alpha
        self._bin_betas = np.ones(n_bins) * self._prior_beta
        
        # Update priors with observed data
        bin_indices = np.digitize(scores, self._bin_edges) - 1
        bin_indices = np.clip(bin_indices, 0, n_bins - 1)
        
        for i in range(n_bins):
            mask = bin_indices == i
            if mask.sum() > 0:
                n_positive = outcomes[mask].sum()
                n_total = mask.sum()
                self._bin_alphas[i] += n_positive
                self._bin_betas[i] += (n_total - n_positive)
    
    def transform(self, raw_scores: np.ndarray) -> np.ndarray:
        """
        Apply calibration to new scores.
        
        Args:
            raw_scores: Uncalibrated risk scores (0-100)
            
        Returns:
            Calibrated probabilities (0-1)
        """
        if not self.is_fitted:
            raise RuntimeError("Calibrator not fitted. Call fit() first.")
        
        raw_scores = np.asarray(raw_scores).flatten()
        scores_normalized = raw_scores / 100.0
        scores_normalized = np.clip(scores_normalized, 0, 1)
        
        if self.method == 'platt':
            return self.calibrator.predict_proba(scores_normalized.reshape(-1, 1))[:, 1]
        elif self.method == 'isotonic':
            return self.calibrator.transform(scores_normalized)
        elif self.method == 'bayesian':
            return self._transform_bayesian(scores_normalized)
    
    def _transform_bayesian(self, scores: np.ndarray) -> np.ndarray:
        """Apply Bayesian calibration."""
        n_bins = len(self._bin_alphas)
        bin_indices = np.digitize(scores, self._bin_edges) - 1
        bin_indices = np.clip(bin_indices, 0, n_bins - 1)
        
        # Posterior mean of Beta distribution
        calibrated = np.zeros_like(scores)
        for i in range(n_bins):
            mask = bin_indices == i
            if mask.sum() > 0:
                # E[Beta(alpha, beta)] = alpha / (alpha + beta)
                calibrated[mask] = self._bin_alphas[i] / (self._bin_alphas[i] + self._bin_betas[i])
        
        return calibrated
    
    def _compute_validation_metrics(self, scores: np.ndarray, actuals: np.ndarray):
        """Compute calibration quality metrics on validation set."""
        calibrated = self.transform(scores * 100)  # transform expects 0-100
        
        # Brier Score (lower is better, 0 = perfect)
        brier = np.mean((calibrated - actuals) ** 2)
        
        # Expected Calibration Error (ECE)
        n_bins = 10
        bin_edges = np.linspace(0, 1, n_bins + 1)
        bin_indices = np.digitize(calibrated, bin_edges) - 1
        bin_indices = np.clip(bin_indices, 0, n_bins - 1)
        
        ece = 0.0
        mce = 0.0  # Maximum calibration error
        for i in range(n_bins):
            mask = bin_indices == i
            if mask.sum() > 0:
                bin_accuracy = actuals[mask].mean()
                bin_confidence = calibrated[mask].mean()
                bin_error = abs(bin_accuracy - bin_confidence)
                ece += mask.sum() / len(actuals) * bin_error
                mce = max(mce, bin_error)
        
        # Log Loss (cross-entropy)
        epsilon = 1e-15
        calibrated_clipped = np.clip(calibrated, epsilon, 1 - epsilon)
        log_loss = -np.mean(
            actuals * np.log(calibrated_clipped) + 
            (1 - actuals) * np.log(1 - calibrated_clipped)
        )
        
        # AUC-ROC
        from sklearn.metrics import roc_auc_score
        try:
            auc = roc_auc_score(actuals, calibrated)
        except ValueError:
            auc = 0.5  # Default if only one class present
        
        self.validation_metrics = CalibrationMetrics(
            brier_score=float(brier),
            expected_calibration_error=float(ece),
            log_loss=float(log_loss),
            max_calibration_error=float(mce),
            area_under_roc=float(auc),
            sample_size=len(actuals),
            method=self.method
        )
        
        # Generate reliability diagram data
        prob_true, prob_pred = calibration_curve(
            actuals, calibrated, n_bins=n_bins, strategy='uniform'
        )
        
        self.reliability_data = {
            'predicted_probabilities': prob_pred.tolist(),
            'true_frequencies': prob_true.tolist(),
            'n_bins': n_bins
        }
    
    def is_acceptable(self) -> Tuple[bool, List[str]]:
        """
        Check if calibration meets industry standards.
        
        Returns:
            Tuple of (is_acceptable, list of issues)
        """
        if not self.is_fitted:
            return False, ["Calibrator not fitted"]
        
        issues = []
        
        if self.validation_metrics.brier_score > self.BRIER_THRESHOLD:
            issues.append(f"Brier score {self.validation_metrics.brier_score:.4f} > {self.BRIER_THRESHOLD}")
        
        if self.validation_metrics.expected_calibration_error > self.ECE_THRESHOLD:
            issues.append(f"ECE {self.validation_metrics.expected_calibration_error:.4f} > {self.ECE_THRESHOLD}")
        
        return len(issues) == 0, issues
    
    def plot_calibration_curve(self, save_path: str = 'calibration_curve.png'):
        """Generate and save calibration curve."""
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            logger.warning("matplotlib not available for plotting")
            return
        
        if not self.is_fitted or self.reliability_data is None:
            raise RuntimeError("Calibrator not fitted. Call fit() first.")
        
        data = self.reliability_data
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Perfect calibration line
        ax.plot([0, 1], [0, 1], 'k--', label='Perfect Calibration', linewidth=2)
        
        # Actual calibration
        ax.plot(
            data['predicted_probabilities'],
            data['true_frequencies'],
            'o-',
            label=f'RISKCAST ({self.method})',
            linewidth=2,
            markersize=8,
            color='#1f77b4'
        )
        
        ax.set_xlabel('Predicted Probability', fontsize=12)
        ax.set_ylabel('True Frequency', fontsize=12)
        ax.set_title('RISKCAST Calibration Curve', fontsize=14, fontweight='bold')
        ax.legend(fontsize=11)
        ax.grid(alpha=0.3)
        ax.set_xlim([0, 1])
        ax.set_ylim([0, 1])
        
        # Add metrics as text box
        metrics_text = (
            f"Brier Score: {self.validation_metrics.brier_score:.4f}\n"
            f"ECE: {self.validation_metrics.expected_calibration_error:.4f}\n"
            f"Log Loss: {self.validation_metrics.log_loss:.4f}\n"
            f"AUC-ROC: {self.validation_metrics.area_under_roc:.4f}\n"
            f"n = {self.validation_metrics.sample_size}"
        )
        ax.text(0.05, 0.95, metrics_text, transform=ax.transAxes,
                fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        # Add pass/fail indicator
        is_acceptable, issues = self.is_acceptable()
        status_color = '#2ca02c' if is_acceptable else '#d62728'
        status_text = '✓ PASSES THRESHOLDS' if is_acceptable else '✗ NEEDS IMPROVEMENT'
        ax.text(0.95, 0.05, status_text, transform=ax.transAxes,
                fontsize=12, fontweight='bold', color=status_color,
                horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300)
        logger.info(f"Calibration curve saved to {save_path}")
        plt.close()
    
    def save(self, filepath: str):
        """Save calibrator to file."""
        import joblib
        
        save_data = {
            'method': self.method,
            'calibrator': self.calibrator,
            'validation_metrics': asdict(self.validation_metrics) if self.validation_metrics else None,
            'reliability_data': self.reliability_data,
            'is_fitted': self.is_fitted,
            # Bayesian specific
            '_bin_edges': self._bin_edges,
            '_bin_alphas': self._bin_alphas,
            '_bin_betas': self._bin_betas,
        }
        
        joblib.dump(save_data, filepath)
        logger.info(f"Calibrator saved to {filepath}")
    
    @classmethod
    def load(cls, filepath: str) -> 'RiskScoreCalibrator':
        """Load calibrator from file."""
        import joblib
        
        save_data = joblib.load(filepath)
        
        calibrator = cls(method=save_data['method'])
        calibrator.calibrator = save_data['calibrator']
        calibrator.is_fitted = save_data['is_fitted']
        calibrator.reliability_data = save_data['reliability_data']
        
        if save_data['validation_metrics']:
            calibrator.validation_metrics = CalibrationMetrics(**save_data['validation_metrics'])
        
        # Bayesian specific
        calibrator._bin_edges = save_data.get('_bin_edges')
        calibrator._bin_alphas = save_data.get('_bin_alphas')
        calibrator._bin_betas = save_data.get('_bin_betas')
        
        logger.info(f"Calibrator loaded from {filepath}")
        return calibrator
    
    def get_report(self) -> Dict:
        """Generate calibration report as dictionary."""
        if not self.is_fitted:
            return {'error': 'Calibrator not fitted'}
        
        is_acceptable, issues = self.is_acceptable()
        
        return {
            'method': self.method,
            'metrics': asdict(self.validation_metrics),
            'reliability_diagram': self.reliability_data,
            'thresholds': {
                'brier_threshold': self.BRIER_THRESHOLD,
                'ece_threshold': self.ECE_THRESHOLD
            },
            'is_acceptable': is_acceptable,
            'issues': issues
        }


def run_calibration_pipeline(
    data_path: str,
    output_dir: str = 'reports',
    method: str = 'isotonic'
) -> Dict:
    """
    Run full calibration pipeline.
    
    Args:
        data_path: Path to historical data CSV
        output_dir: Output directory for reports
        method: Calibration method
        
    Returns:
        Calibration report dictionary
    """
    logger.info(f"Starting calibration pipeline with data: {data_path}")
    
    # Load historical data
    df = pd.read_csv(data_path)
    
    # Required columns
    required_cols = ['risk_score', 'delay_days']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    # Extract scores and outcomes
    raw_scores = df['risk_score'].values
    
    # Binary outcome: delay > 3 days (configurable threshold)
    delay_threshold = 3
    actual_outcomes = (df['delay_days'] > delay_threshold).astype(int).values
    
    logger.info(f"Loaded {len(df)} records. Incident rate: {actual_outcomes.mean():.2%}")
    
    # Fit calibrator
    calibrator = RiskScoreCalibrator(method=method)
    calibrator.fit(raw_scores, actual_outcomes)
    
    # Generate outputs
    os.makedirs(output_dir, exist_ok=True)
    
    # Save calibration curve
    calibrator.plot_calibration_curve(
        save_path=os.path.join(output_dir, 'calibration_curve.png')
    )
    
    # Save calibrator model
    calibrator.save(os.path.join(output_dir, 'risk_score_calibrator.pkl'))
    
    # Save report as JSON
    report = calibrator.get_report()
    with open(os.path.join(output_dir, 'calibration_report.json'), 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Calibration pipeline complete. Reports saved to {output_dir}")
    
    return report


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='RISKCAST Calibration Pipeline')
    parser.add_argument('--data', required=True, help='Path to historical data CSV')
    parser.add_argument('--method', default='isotonic', choices=['platt', 'isotonic', 'bayesian'])
    parser.add_argument('--output', default='reports', help='Output directory')
    
    args = parser.parse_args()
    
    report = run_calibration_pipeline(
        data_path=args.data,
        output_dir=args.output,
        method=args.method
    )
    
    # Print summary
    print("\n" + "="*60)
    print("CALIBRATION SUMMARY")
    print("="*60)
    print(f"Method: {report['method']}")
    print(f"Brier Score: {report['metrics']['brier_score']:.4f}")
    print(f"ECE: {report['metrics']['expected_calibration_error']:.4f}")
    print(f"AUC-ROC: {report['metrics']['area_under_roc']:.4f}")
    print(f"Acceptable: {'YES ✓' if report['is_acceptable'] else 'NO ✗'}")
    if report['issues']:
        print(f"Issues: {', '.join(report['issues'])}")
    print("="*60)
