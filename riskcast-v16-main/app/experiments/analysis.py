"""
Statistical Analysis for Experiments

Features:
1. Frequentist analysis
2. Bayesian analysis
3. Power calculations
"""

import asyncio
import math
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.experiments.framework import (
    Experiment,
    Variant,
    Metric,
    MetricType,
    ExperimentEventModel,
    ExperimentAssignmentModel,
)
from app.core.logging import get_logger

logger = get_logger(__name__)

try:
    import numpy as np
    from scipy import stats

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None
    stats = None


@dataclass
class VariantStats:
    """Statistics for a variant."""

    variant_id: str
    variant_name: str
    sample_size: int
    conversions: int = 0
    conversion_rate: float = 0.0
    mean: float = 0.0
    std: float = 0.0
    sum_value: float = 0.0
    min_value: float = 0.0
    max_value: float = 0.0


@dataclass
class ComparisonResult:
    """Result of comparing variants."""

    control_variant: str
    treatment_variant: str
    absolute_effect: float
    relative_effect: float
    p_value: float
    confidence_interval: Tuple[float, float]
    is_significant: bool
    probability_better: float
    expected_loss: float
    control_sample_size: int
    treatment_sample_size: int
    achieved_power: Optional[float] = None


@dataclass
class ExperimentResults:
    """Full experiment results."""

    experiment_id: str
    experiment_name: str
    status: str
    primary_metric: str
    variant_stats: Dict[str, VariantStats]
    comparisons: List[ComparisonResult]
    winner: Optional[str]
    recommendation: str
    analysis_date: datetime
    data_as_of: datetime


async def _run_sync(coro):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return coro()
    return await asyncio.to_thread(coro)


class StatisticalAnalyzer:
    """Performs statistical analysis on experiment data."""

    def __init__(
        self,
        session: Session,
        significance_level: float = 0.05,
        power_threshold: float = 0.80,
    ):
        self.session = session
        self.significance_level = significance_level
        self.power_threshold = power_threshold

    def _get_variant_stats_sync(
        self,
        experiment_id: str,
        variant_id: str,
        variant_name: str,
        metric: Metric,
    ) -> VariantStats:
        """Get statistics for a variant."""
        q = select(func.count(ExperimentAssignmentModel.id)).where(
            ExperimentAssignmentModel.experiment_id == experiment_id
        ).where(ExperimentAssignmentModel.variant_id == variant_id)
        sample_size = self.session.execute(q).scalar() or 0

        base = (
            select(
                func.count(ExperimentEventModel.id).label("cnt"),
                func.sum(ExperimentEventModel.value).label("sum_val"),
                func.avg(ExperimentEventModel.value).label("avg_val"),
                func.min(ExperimentEventModel.value).label("min_val"),
                func.max(ExperimentEventModel.value).label("max_val"),
            )
            .where(ExperimentEventModel.experiment_id == experiment_id)
            .where(ExperimentEventModel.variant_id == variant_id)
            .where(ExperimentEventModel.metric_name == metric.name)
        )
        row = self.session.execute(base).one_or_none()

        if not row:
            return VariantStats(
                variant_id=variant_id,
                variant_name=variant_name,
                sample_size=sample_size,
            )

        count = row.cnt or 0
        sum_val = float(row.sum_val or 0)
        mean = float(row.avg_val or 0)
        min_val = float(row.min_val or 0)
        max_val = float(row.max_val or 0)

        std_val = 0.0
        try:
            std_q = (
                select(func.stddev(ExperimentEventModel.value))
                .where(ExperimentEventModel.experiment_id == experiment_id)
                .where(ExperimentEventModel.variant_id == variant_id)
                .where(ExperimentEventModel.metric_name == metric.name)
            )
            std_row = self.session.execute(std_q).scalar_one_or_none()
            if std_row is not None and std_row[0] is not None:
                std_val = float(std_row[0])
        except Exception:
            if NUMPY_AVAILABLE and count > 0:
                vals_q = (
                    select(ExperimentEventModel.value)
                    .where(ExperimentEventModel.experiment_id == experiment_id)
                    .where(ExperimentEventModel.variant_id == variant_id)
                    .where(ExperimentEventModel.metric_name == metric.name)
                )
                vals = [r[0] for r in self.session.execute(vals_q).all()]
                std_val = float(np.std(vals)) if vals else 0.0

        conversions = 0
        conversion_rate = 0.0
        if metric.metric_type == MetricType.CONVERSION and sample_size > 0:
            conversions = int(sum_val)
            conversion_rate = conversions / sample_size

        return VariantStats(
            variant_id=variant_id,
            variant_name=variant_name,
            sample_size=sample_size,
            conversions=conversions,
            conversion_rate=conversion_rate,
            mean=mean,
            std=std_val,
            sum_value=sum_val,
            min_value=min_val,
            max_value=max_val,
        )

    def _compare_conversion_sync(
        self,
        control: VariantStats,
        treatment: VariantStats,
    ) -> ComparisonResult:
        """Compare conversion rates using chi-squared test."""
        if not NUMPY_AVAILABLE or stats is None:
            return _dummy_comparison(control, treatment, "scipy required for analysis")

        absolute_effect = treatment.conversion_rate - control.conversion_rate
        relative_effect = (
            absolute_effect / control.conversion_rate
            if control.conversion_rate > 0
            else 0
        )

        contingency = [
            [control.conversions, control.sample_size - control.conversions],
            [treatment.conversions, treatment.sample_size - treatment.conversions],
        ]
        chi2, p_value, dof, expected = stats.chi2_contingency(contingency)

        se = 0.0
        if control.sample_size > 0 and treatment.sample_size > 0:
            se = math.sqrt(
                control.conversion_rate * (1 - control.conversion_rate) / control.sample_size
                + treatment.conversion_rate
                * (1 - treatment.conversion_rate)
                / treatment.sample_size
            )
        z = stats.norm.ppf(1 - self.significance_level / 2)
        ci_low = absolute_effect - z * se
        ci_high = absolute_effect + z * se

        alpha_c = control.conversions + 1
        beta_c = control.sample_size - control.conversions + 1
        alpha_t = treatment.conversions + 1
        beta_t = treatment.sample_size - treatment.conversions + 1
        samples_c = np.random.beta(alpha_c, beta_c, 10000)
        samples_t = np.random.beta(alpha_t, beta_t, 10000)
        prob_better = float(np.mean(samples_t > samples_c))
        expected_loss = float(np.mean(np.maximum(samples_c - samples_t, 0)))

        return ComparisonResult(
            control_variant=control.variant_name,
            treatment_variant=treatment.variant_name,
            absolute_effect=absolute_effect,
            relative_effect=relative_effect,
            p_value=float(p_value),
            confidence_interval=(ci_low, ci_high),
            is_significant=p_value < self.significance_level,
            probability_better=prob_better,
            expected_loss=expected_loss,
            control_sample_size=control.sample_size,
            treatment_sample_size=treatment.sample_size,
        )

    def _compare_continuous_sync(
        self,
        control: VariantStats,
        treatment: VariantStats,
    ) -> ComparisonResult:
        """Compare continuous metrics using t-test."""
        if not NUMPY_AVAILABLE or stats is None:
            return _dummy_comparison(control, treatment, "scipy required for analysis")

        absolute_effect = treatment.mean - control.mean
        relative_effect = (
            absolute_effect / control.mean if control.mean != 0 else 0
        )

        n1, n2 = control.sample_size, treatment.sample_size
        mean1, mean2 = control.mean, treatment.mean
        std1, std2 = control.std, treatment.std

        se = math.sqrt(std1**2 / n1 + std2**2 / n2) if n1 > 0 and n2 > 0 else 1.0
        t_stat = (mean2 - mean1) / se if se > 0 else 0

        df = 1
        denom = (std1**2 / n1) ** 2 / max(1, n1 - 1) + (std2**2 / n2) ** 2 / max(1, n2 - 1)
        if n1 > 1 and n2 > 1 and denom > 0:
            num = (std1**2 / n1 + std2**2 / n2) ** 2
            df = max(1, num / denom)
        p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df))

        t_crit = stats.t.ppf(1 - self.significance_level / 2, df)
        ci_low = absolute_effect - t_crit * se
        ci_high = absolute_effect + t_crit * se

        pooled_se = math.sqrt(std1**2 + std2**2) if (std1 > 0 or std2 > 0) else 1.0
        z_score = absolute_effect / pooled_se if pooled_se > 0 else 0
        prob_better = float(stats.norm.cdf(z_score))
        expected_loss = abs(absolute_effect) * (1 - prob_better)

        return ComparisonResult(
            control_variant=control.variant_name,
            treatment_variant=treatment.variant_name,
            absolute_effect=absolute_effect,
            relative_effect=relative_effect,
            p_value=float(p_value),
            confidence_interval=(ci_low, ci_high),
            is_significant=p_value < self.significance_level,
            probability_better=prob_better,
            expected_loss=expected_loss,
            control_sample_size=control.sample_size,
            treatment_sample_size=treatment.sample_size,
        )

    def _analyze_experiment_sync(self, experiment: Experiment) -> ExperimentResults:
        """Perform full analysis (sync)."""
        primary_metric = experiment.get_primary_metric()
        variant_stats = {}
        for v in experiment.variants:
            variant_stats[v.id] = self._get_variant_stats_sync(
                experiment.id, v.id, v.name, primary_metric
            )

        control = experiment.variants[0]
        comparisons = []
        for v in experiment.variants[1:]:
            if primary_metric.metric_type == MetricType.CONVERSION:
                comp = self._compare_conversion_sync(
                    variant_stats[control.id], variant_stats[v.id]
                )
            else:
                comp = self._compare_continuous_sync(
                    variant_stats[control.id], variant_stats[v.id]
                )
            comparisons.append(comp)

        winner = None
        recommendation = "Continue collecting data"
        significant = [c for c in comparisons if c.is_significant and c.relative_effect > 0]
        if significant:
            best = max(significant, key=lambda c: c.relative_effect)
            winner = best.treatment_variant
            recommendation = (
                f"Implement {winner}. {best.relative_effect:.1%} improvement "
                f"with p-value {best.p_value:.4f}"
            )
        else:
            all_sufficient = all(
                variant_stats[v.id].sample_size >= experiment.min_sample_size
                for v in experiment.variants
            )
            if all_sufficient:
                recommendation = "No significant winner. Consider stopping."

        return ExperimentResults(
            experiment_id=experiment.id,
            experiment_name=experiment.name,
            status=experiment.status.value,
            primary_metric=primary_metric.name,
            variant_stats=variant_stats,
            comparisons=comparisons,
            winner=winner,
            recommendation=recommendation,
            analysis_date=datetime.utcnow(),
            data_as_of=datetime.utcnow(),
        )

    async def analyze_experiment(self, experiment: Experiment) -> ExperimentResults:
        """Perform full analysis of an experiment."""
        return await _run_sync(lambda: self._analyze_experiment_sync(experiment))


def _dummy_comparison(
    control: VariantStats,
    treatment: VariantStats,
    msg: str,
) -> ComparisonResult:
    """Placeholder when scipy is missing."""
    return ComparisonResult(
        control_variant=control.variant_name,
        treatment_variant=treatment.variant_name,
        absolute_effect=0.0,
        relative_effect=0.0,
        p_value=1.0,
        confidence_interval=(0.0, 0.0),
        is_significant=False,
        probability_better=0.5,
        expected_loss=0.0,
        control_sample_size=control.sample_size,
        treatment_sample_size=treatment.sample_size,
    )


class PowerCalculator:
    """Calculate required sample size and achieved power."""

    @staticmethod
    def required_sample_size(
        baseline_rate: float,
        minimum_detectable_effect: float,
        significance_level: float = 0.05,
        power: float = 0.80,
    ) -> int:
        """Required sample size per variant for conversion metrics."""
        if not stats:
            return 1000
        p1 = baseline_rate
        p2 = baseline_rate * (1 + minimum_detectable_effect)
        if abs(p2 - p1) < 1e-9:
            return 1000
        p_pool = (p1 + p2) / 2
        z_alpha = stats.norm.ppf(1 - significance_level / 2)
        z_beta = stats.norm.ppf(power)
        n = (
            z_alpha * math.sqrt(2 * p_pool * (1 - p_pool))
            + z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))
        ) ** 2 / (p2 - p1) ** 2
        return max(1, int(math.ceil(n)))

    @staticmethod
    def achieved_power(
        control_rate: float,
        treatment_rate: float,
        control_sample: int,
        treatment_sample: int,
        significance_level: float = 0.05,
    ) -> float:
        """Achieved power given observed data."""
        if not stats:
            return 0.0
        effect = abs(treatment_rate - control_rate)
        se = math.sqrt(
            control_rate * (1 - control_rate) / control_sample
            + treatment_rate * (1 - treatment_rate) / treatment_sample
        )
        if se == 0:
            return 1.0
        z_alpha = stats.norm.ppf(1 - significance_level / 2)
        ncp = effect / se
        power = 1 - stats.norm.cdf(z_alpha - ncp) + stats.norm.cdf(-z_alpha - ncp)
        return float(power)
