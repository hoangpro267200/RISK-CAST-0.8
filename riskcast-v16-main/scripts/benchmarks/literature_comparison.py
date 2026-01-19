"""
RISKCAST Benchmark Comparison Suite
====================================
Compare RISKCAST performance against published baseline methods.

Implements:
1. Chen2019: AHP + Fuzzy TOPSIS for supply chain risk
2. Wang2021: Random Forest + LSTM for shipping delays
3. Statistical significance testing

Author: RISKCAST Team
Version: 2.0
"""

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score,
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, brier_score_loss
)
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score, train_test_split
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging
import os
import sys
import json

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Result from a single benchmark method."""
    method_name: str
    metrics: Dict[str, float]
    predictions: np.ndarray
    errors: np.ndarray
    training_time: float
    description: str


@dataclass 
class ComparisonReport:
    """Complete benchmark comparison report."""
    riskcast_result: BenchmarkResult
    baseline_results: List[BenchmarkResult]
    statistical_tests: Dict[str, Dict]
    winner: str
    summary: str


# Published baseline methods configuration
BASELINE_METHODS = {
    'Chen2019_SupplyChainRisk': {
        'description': 'AHP + Fuzzy TOPSIS (Chen et al., 2019)',
        'reported_metrics': {
            'accuracy': 0.78,
            'f1_score': 0.72
        },
        'dataset_size': 150,
        'domain': 'Supply chain disruption prediction',
        'citation': 'Chen, Y. et al. (2019). Supply Chain Risk Assessment using AHP-TOPSIS'
    },
    
    'Wang2021_LogisticsDelay': {
        'description': 'Random Forest + LSTM (Wang et al., 2021)',
        'reported_metrics': {
            'accuracy': 0.82,
            'mae': 1.5
        },
        'dataset_size': 5000,
        'domain': 'Container shipping delay prediction',
        'citation': 'Wang, L. et al. (2021). Deep Learning for Logistics Delay Prediction'
    },
    
    'SimpleBaseline': {
        'description': 'Historical average (baseline)',
        'reported_metrics': {},
        'dataset_size': None,
        'domain': 'Naive baseline',
        'citation': 'N/A'
    }
}


class Chen2019Baseline:
    """
    Simplified implementation of Chen et al. 2019 AHP-TOPSIS method.
    
    This is a fair comparison baseline - implements core methodology
    without RISKCAST-specific enhancements.
    """
    
    # AHP weights from Chen2019 paper
    AHP_WEIGHTS = {
        'delay_risk': 0.25,
        'damage_risk': 0.20,
        'cost_risk': 0.15,
        'quality_risk': 0.15,
        'supplier_risk': 0.15,
        'environmental_risk': 0.10
    }
    
    def __init__(self):
        self.is_fitted = False
    
    def fit(self, X: np.ndarray, y: np.ndarray):
        """Fit is a no-op for this rule-based method."""
        self.is_fitted = True
        return self
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict risk scores using AHP-TOPSIS.
        
        Simplified: Uses weighted sum of normalized features.
        """
        if not self.is_fitted:
            raise RuntimeError("Call fit() first")
        
        # Normalize features to 0-1
        X_norm = (X - X.min(axis=0)) / (X.max(axis=0) - X.min(axis=0) + 1e-10)
        
        # Apply AHP weights (assuming features align with weights)
        n_features = X_norm.shape[1]
        weights = np.array(list(self.AHP_WEIGHTS.values())[:n_features])
        weights = weights / weights.sum()  # Normalize weights
        
        # Weighted sum
        scores = X_norm @ weights
        
        # Scale to 0-100
        return scores * 100
    
    def predict_binary(self, X: np.ndarray, threshold: float = 50) -> np.ndarray:
        """Predict binary outcome (high risk / low risk)."""
        scores = self.predict(X)
        return (scores > threshold).astype(int)


class Wang2021Baseline:
    """
    Simplified implementation of Wang et al. 2021 RF-LSTM method.
    
    Uses Random Forest (without LSTM for simplicity).
    """
    
    def __init__(self, n_estimators: int = 100):
        self.model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=10,
            random_state=42
        )
        self.is_fitted = False
    
    def fit(self, X: np.ndarray, y: np.ndarray):
        """Fit Random Forest model."""
        self.model.fit(X, y)
        self.is_fitted = True
        return self
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict probabilities."""
        if not self.is_fitted:
            raise RuntimeError("Call fit() first")
        return self.model.predict_proba(X)[:, 1] * 100
    
    def predict_binary(self, X: np.ndarray) -> np.ndarray:
        """Predict binary outcome."""
        return self.model.predict(X)


class SimpleBaseline:
    """Naive baseline: always predict historical average."""
    
    def __init__(self):
        self.mean_score = None
        self.is_fitted = False
    
    def fit(self, X: np.ndarray, y: np.ndarray):
        """Store mean outcome."""
        self.mean_score = y.mean() * 100
        self.is_fitted = True
        return self
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Always predict mean."""
        return np.full(len(X), self.mean_score)
    
    def predict_binary(self, X: np.ndarray, threshold: float = 0.5) -> np.ndarray:
        """Always predict majority class."""
        return np.full(len(X), int(self.mean_score > 50))


class RISKCASTPredictor:
    """
    RISKCAST engine wrapper for benchmark comparison.
    """
    
    def __init__(self):
        self.is_fitted = True  # Always "fitted" since it's rule-based
    
    def fit(self, X: np.ndarray, y: np.ndarray):
        """No fitting needed for RISKCAST."""
        return self
    
    def predict_from_dataframe(self, df: pd.DataFrame) -> np.ndarray:
        """Predict using RISKCAST engine."""
        from app.core.engine.risk_engine_v16 import calculate_enterprise_risk
        
        scores = []
        for _, row in df.iterrows():
            try:
                shipment_data = self._row_to_shipment(row)
                result = calculate_enterprise_risk(shipment_data)
                score = result.get('overall_risk', 5) * 10
                scores.append(score)
            except Exception as e:
                logger.warning(f"RISKCAST prediction failed: {e}")
                scores.append(50)  # Default
        
        return np.array(scores)
    
    def _row_to_shipment(self, row: pd.Series) -> Dict:
        """Convert DataFrame row to shipment data."""
        return {
            'transport_mode': row.get('transport_mode', 'sea'),
            'cargo_type': row.get('cargo_type', 'standard'),
            'route': row.get('route', 'vn_us'),
            'incoterm': row.get('incoterm', 'FOB'),
            'transit_time': float(row.get('transit_time', 30)),
            'cargo_value': float(row.get('cargo_value', 50000)),
            'carrier_rating': float(row.get('carrier_rating', 5)),
            'weather_risk': float(row.get('weather_risk', 5)),
            'port_risk': float(row.get('port_risk', 5)),
        }


def run_benchmark_comparison(
    data_path: str,
    output_dir: str = 'reports'
) -> ComparisonReport:
    """
    Run complete benchmark comparison.
    
    Args:
        data_path: Path to historical data CSV
        output_dir: Output directory for reports
        
    Returns:
        ComparisonReport object
    """
    logger.info(f"Loading data from {data_path}")
    df = pd.read_csv(data_path)
    
    # Prepare features and target
    feature_cols = [c for c in df.columns if c not in ['delay_days', 'incident', 'loss_amount']]
    
    # Binary target: delay > 3 days
    if 'delay_days' in df.columns:
        y = (df['delay_days'] > 3).astype(int).values
    elif 'incident' in df.columns:
        y = df['incident'].astype(int).values
    else:
        raise ValueError("Data must have 'delay_days' or 'incident' column")
    
    # Extract numeric features
    X = df[feature_cols].select_dtypes(include=[np.number]).values
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    logger.info(f"Data split: {len(X_train)} train, {len(X_test)} test")
    
    results = []
    
    # Run Chen2019 baseline
    logger.info("Running Chen2019 baseline...")
    import time
    start = time.time()
    chen = Chen2019Baseline()
    chen.fit(X_train, y_train)
    chen_pred = chen.predict_binary(X_test)
    chen_scores = chen.predict(X_test)
    chen_time = time.time() - start
    
    chen_result = BenchmarkResult(
        method_name='Chen2019_AHP_TOPSIS',
        metrics=compute_metrics(y_test, chen_pred, chen_scores),
        predictions=chen_pred,
        errors=np.abs(chen_pred - y_test),
        training_time=chen_time,
        description=BASELINE_METHODS['Chen2019_SupplyChainRisk']['description']
    )
    results.append(chen_result)
    
    # Run Wang2021 baseline
    logger.info("Running Wang2021 baseline...")
    start = time.time()
    wang = Wang2021Baseline()
    wang.fit(X_train, y_train)
    wang_pred = wang.predict_binary(X_test)
    wang_scores = wang.predict(X_test)
    wang_time = time.time() - start
    
    wang_result = BenchmarkResult(
        method_name='Wang2021_RandomForest',
        metrics=compute_metrics(y_test, wang_pred, wang_scores),
        predictions=wang_pred,
        errors=np.abs(wang_pred - y_test),
        training_time=wang_time,
        description=BASELINE_METHODS['Wang2021_LogisticsDelay']['description']
    )
    results.append(wang_result)
    
    # Run simple baseline
    logger.info("Running simple baseline...")
    start = time.time()
    simple = SimpleBaseline()
    simple.fit(X_train, y_train)
    simple_pred = simple.predict_binary(X_test)
    simple_scores = simple.predict(X_test)
    simple_time = time.time() - start
    
    simple_result = BenchmarkResult(
        method_name='SimpleBaseline',
        metrics=compute_metrics(y_test, simple_pred, simple_scores),
        predictions=simple_pred,
        errors=np.abs(simple_pred - y_test),
        training_time=simple_time,
        description='Historical average baseline'
    )
    results.append(simple_result)
    
    # Run RISKCAST
    logger.info("Running RISKCAST...")
    start = time.time()
    riskcast = RISKCASTPredictor()
    # For RISKCAST, we need the original dataframe
    test_indices = np.arange(len(y))[len(X_train):]
    test_df = df.iloc[test_indices].reset_index(drop=True)
    riskcast_scores = riskcast.predict_from_dataframe(test_df)
    riskcast_pred = (riskcast_scores > 50).astype(int)
    riskcast_time = time.time() - start
    
    riskcast_result = BenchmarkResult(
        method_name='RISKCAST_v16',
        metrics=compute_metrics(y_test, riskcast_pred, riskcast_scores),
        predictions=riskcast_pred,
        errors=np.abs(riskcast_pred - y_test),
        training_time=riskcast_time,
        description='RISKCAST FAHP + TOPSIS + Monte Carlo'
    )
    
    # Statistical significance tests
    stat_tests = run_statistical_tests(riskcast_result, results)
    
    # Determine winner
    winner = determine_winner([riskcast_result] + results)
    
    # Generate summary
    summary = generate_summary(riskcast_result, results, stat_tests, winner)
    
    report = ComparisonReport(
        riskcast_result=riskcast_result,
        baseline_results=results,
        statistical_tests=stat_tests,
        winner=winner,
        summary=summary
    )
    
    # Save report
    os.makedirs(output_dir, exist_ok=True)
    save_report(report, output_dir)
    
    return report


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray, scores: np.ndarray) -> Dict[str, float]:
    """Compute all evaluation metrics."""
    metrics = {
        'accuracy': accuracy_score(y_true, y_pred),
        'precision': precision_score(y_true, y_pred, zero_division=0),
        'recall': recall_score(y_true, y_pred, zero_division=0),
        'f1_score': f1_score(y_true, y_pred, zero_division=0),
        'brier_score': brier_score_loss(y_true, scores / 100),
    }
    
    # AUC only if both classes present
    if len(np.unique(y_true)) > 1:
        metrics['auc_roc'] = roc_auc_score(y_true, scores)
    else:
        metrics['auc_roc'] = 0.5
    
    return metrics


def run_statistical_tests(
    riskcast: BenchmarkResult,
    baselines: List[BenchmarkResult]
) -> Dict[str, Dict]:
    """Run statistical significance tests."""
    tests = {}
    
    for baseline in baselines:
        # Paired t-test on errors
        t_stat, p_value = stats.ttest_rel(
            riskcast.errors,
            baseline.errors
        )
        
        # McNemar's test for classification
        # (Simplified: using proportion test)
        riskcast_correct = (riskcast.errors == 0).sum()
        baseline_correct = (baseline.errors == 0).sum()
        n = len(riskcast.errors)
        
        z_stat = (riskcast_correct - baseline_correct) / np.sqrt(n)
        z_p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
        
        tests[baseline.method_name] = {
            'paired_ttest': {
                't_statistic': float(t_stat),
                'p_value': float(p_value),
                'significant': p_value < 0.05
            },
            'proportion_test': {
                'z_statistic': float(z_stat),
                'p_value': float(z_p_value),
                'significant': z_p_value < 0.05
            },
            'riskcast_better': riskcast.metrics['accuracy'] > baseline.metrics['accuracy']
        }
    
    return tests


def determine_winner(results: List[BenchmarkResult]) -> str:
    """Determine best method based on F1 score."""
    best = max(results, key=lambda r: r.metrics['f1_score'])
    return best.method_name


def generate_summary(
    riskcast: BenchmarkResult,
    baselines: List[BenchmarkResult],
    tests: Dict,
    winner: str
) -> str:
    """Generate human-readable summary."""
    
    summary = f"""
RISKCAST Benchmark Comparison Report
=====================================

RISKCAST Performance:
  - Accuracy: {riskcast.metrics['accuracy']:.3f}
  - F1 Score: {riskcast.metrics['f1_score']:.3f}
  - AUC-ROC:  {riskcast.metrics['auc_roc']:.3f}
  - Brier:    {riskcast.metrics['brier_score']:.4f}

Baseline Comparisons:
"""
    
    for baseline in baselines:
        test = tests.get(baseline.method_name, {})
        sig = "✓" if test.get('paired_ttest', {}).get('significant', False) else "✗"
        better = "BETTER" if test.get('riskcast_better', False) else "WORSE"
        
        summary += f"""
  {baseline.method_name}:
    - Accuracy: {baseline.metrics['accuracy']:.3f}
    - F1 Score: {baseline.metrics['f1_score']:.3f}
    - RISKCAST is {better} (p={test.get('paired_ttest', {}).get('p_value', 1.0):.4f}) {sig}
"""
    
    summary += f"""
WINNER: {winner}
"""
    
    if winner == 'RISKCAST_v16':
        summary += """
CONCLUSION: RISKCAST outperforms published baselines on this dataset.
The results support the scientific validity of the FAHP+TOPSIS+MC approach.
"""
    else:
        summary += f"""
CONCLUSION: {winner} outperforms RISKCAST on this dataset.
Consider investigating why and potential improvements.
"""
    
    return summary


def save_report(report: ComparisonReport, output_dir: str):
    """Save report to files."""
    
    # Save JSON report
    report_dict = {
        'riskcast': {
            'method': report.riskcast_result.method_name,
            'metrics': report.riskcast_result.metrics,
            'training_time': report.riskcast_result.training_time
        },
        'baselines': [
            {
                'method': b.method_name,
                'metrics': b.metrics,
                'training_time': b.training_time
            }
            for b in report.baseline_results
        ],
        'statistical_tests': report.statistical_tests,
        'winner': report.winner
    }
    
    with open(os.path.join(output_dir, 'benchmark_report.json'), 'w') as f:
        json.dump(report_dict, f, indent=2)
    
    # Save text summary
    with open(os.path.join(output_dir, 'benchmark_summary.txt'), 'w') as f:
        f.write(report.summary)
    
    logger.info(f"Reports saved to {output_dir}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='RISKCAST Benchmark Comparison')
    parser.add_argument('--data', required=True, help='Path to historical data CSV')
    parser.add_argument('--output', default='reports', help='Output directory')
    
    args = parser.parse_args()
    
    report = run_benchmark_comparison(
        data_path=args.data,
        output_dir=args.output
    )
    
    print(report.summary)
