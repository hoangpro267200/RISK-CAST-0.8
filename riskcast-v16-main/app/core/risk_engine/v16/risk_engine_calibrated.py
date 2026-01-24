"""
Risk Engine with Calibration Support

This is the updated risk engine that uses calibrated parameters
instead of hardcoded values.

Key changes:
- Layer weights from RiskModelVersion
- Correlation matrix from RiskModelVersion
- Loss function from RiskModelVersion
- All calculations deterministic and audited
"""

import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

import numpy as np
from scipy.stats import norm

from app.modules.model_versioning.models import RiskModelVersion
from app.core.audit_ledger.ledger import AuditLedger
from app.services.unified_data_service import UnifiedShipmentData

logger = logging.getLogger(__name__)


@dataclass
class CalibratedRiskResult:
    """Risk assessment result using calibrated model."""

    # Risk scores
    overall_risk_score: float
    layer_scores: Dict[str, float]
    weighted_layer_scores: Dict[str, float]

    # Financial metrics
    expected_loss_pct: float
    expected_loss_usd: float
    var_95: float
    var_99: float
    cvar_95: float
    cvar_99: float

    # Monte Carlo results
    loss_distribution: np.ndarray
    percentiles: Dict[str, float]

    # Factor attribution
    risk_factor_attribution: Dict[str, float]

    # Model info
    model_version_id: str
    model_version_name: str
    model_is_calibrated: bool

    # Data quality
    data_quality: str
    data_confidence: float
    data_warnings: List[str]

    # Audit
    input_hash: str
    result_hash: str
    seed: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_risk_score": self.overall_risk_score,
            "layer_scores": self.layer_scores,
            "weighted_layer_scores": self.weighted_layer_scores,
            "expected_loss_pct": self.expected_loss_pct,
            "expected_loss_usd": self.expected_loss_usd,
            "var_95": self.var_95,
            "var_99": self.var_99,
            "cvar_95": self.cvar_95,
            "cvar_99": self.cvar_99,
            "percentiles": self.percentiles,
            "risk_factor_attribution": self.risk_factor_attribution,
            "model": {
                "version_id": self.model_version_id,
                "version_name": self.model_version_name,
                "is_calibrated": self.model_is_calibrated,
            },
            "data_quality": {
                "quality": self.data_quality,
                "confidence": self.data_confidence,
                "warnings": self.data_warnings,
            },
            "audit": {
                "input_hash": self.input_hash,
                "result_hash": self.result_hash,
                "seed": self.seed,
            },
        }


class CalibratedRiskEngine:
    """
    Risk engine using calibrated parameters.

    This replaces the original RiskEngineV16 with a version that:
    1. Uses calibrated weights from RiskModelVersion
    2. Uses calibrated correlations from RiskModelVersion
    3. Uses calibrated loss function from RiskModelVersion
    4. Maintains full determinism and auditability
    """

    LAYER_NAMES = [
        "route_risk",
        "cargo_risk",
        "transport_risk",
        "commercial_risk",
        "infrastructure_risk",
        "weather_risk",
        "geopolitical_risk",
        "seasonal_risk",
        "documentation_risk",
        "handling_risk",
        "security_risk",
        "regulatory_risk",
        "financial_risk",
    ]

    def __init__(
        self,
        model_version: RiskModelVersion,
        audit: Optional[AuditLedger] = None,
        seed: Optional[int] = None,
        tenant_id: Optional[str] = None,
    ):
        self.model_version = model_version
        self.audit = audit
        self.seed = seed or 42
        self.tenant_id = tenant_id or "system"
        self._load_calibrated_parameters()

    def _load_calibrated_parameters(self) -> None:
        """Load calibrated parameters from model version."""
        self.layer_weights = {}
        for layer in self.LAYER_NAMES:
            self.layer_weights[layer] = self.model_version.get_layer_weight(layer)

        total = sum(self.layer_weights.values())
        if total <= 0:
            total = 1.0
            self.layer_weights = {k: 1.0 / len(self.LAYER_NAMES) for k in self.LAYER_NAMES}
        else:
            self.layer_weights = {k: v / total for k, v in self.layer_weights.items()}

        n = len(self.LAYER_NAMES)
        self.correlation_matrix = np.eye(n)
        for i, layer_i in enumerate(self.LAYER_NAMES):
            for j, layer_j in enumerate(self.LAYER_NAMES):
                if i < j:
                    corr = self.model_version.get_correlation(layer_i, layer_j)
                    self.correlation_matrix[i, j] = corr
                    self.correlation_matrix[j, i] = corr

        self.correlation_matrix = self._ensure_positive_definite(self.correlation_matrix)
        self.loss_function = self._create_loss_function()

    def _ensure_positive_definite(self, matrix: np.ndarray) -> np.ndarray:
        """Ensure correlation matrix is positive definite."""
        eigenvalues, eigenvectors = np.linalg.eigh(matrix)
        eigenvalues = np.maximum(eigenvalues, 1e-8)
        adjusted = eigenvectors @ np.diag(eigenvalues) @ eigenvectors.T
        d = np.sqrt(np.maximum(np.diag(adjusted), 1e-10))
        adjusted = adjusted / np.outer(d, d)
        np.fill_diagonal(adjusted, 1.0)
        return adjusted

    def _create_loss_function(self) -> Callable[[np.ndarray], np.ndarray]:
        """Create vectorized loss function from calibrated parameters."""
        lf = self.model_version.get_loss_function_params()
        lf_type = lf.get("function_type", lf.get("type", "POWER"))
        exponent = float(lf.get("risk_score_exponent", 1.8))
        multiplier = float(lf.get("multiplier", 1.0))
        base_rate = float(lf.get("base_loss_rate", 0.0))
        inflection = float(lf.get("inflection_point", 0.5))

        def power_fn(risk: np.ndarray) -> np.ndarray:
            # risk 0–10 scale; (risk/10)^b
            x = np.clip(risk / 10.0, 1e-10, 1.0)
            return multiplier * np.power(x, exponent)

        def exp_fn(risk: np.ndarray) -> np.ndarray:
            x = risk / 10.0
            return np.clip(base_rate * np.exp(exponent * x), 0.0, 1.0)

        def logistic_fn(risk: np.ndarray) -> np.ndarray:
            x = risk / 10.0
            L = base_rate if base_rate > 0 else 1.0
            k = exponent
            x0 = inflection
            return np.clip(L / (1.0 + np.exp(-k * (x - x0))), 0.0, 1.0)

        if lf_type == "EXPONENTIAL":
            return exp_fn
        if lf_type == "LOGISTIC":
            return logistic_fn
        return power_fn

    def _apply_loss_function(self, risk_scores: np.ndarray) -> np.ndarray:
        """Apply calibrated loss function to risk scores (0–1 or 0–10)."""
        # Engine uses 0–1 for weighted sums; loss expects 0–10
        risk_10 = np.clip(risk_scores * 10.0, 0.0, 10.0)
        return np.clip(self.loss_function(risk_10), 0.0, 1.0)

    async def run_assessment(
        self,
        shipment_data: UnifiedShipmentData,
        cargo_value_usd: float,
        n_simulations: int = 10000,
    ) -> CalibratedRiskResult:
        """Run risk assessment using calibrated model."""
        input_hash = self._compute_input_hash(shipment_data, cargo_value_usd)
        rng = np.random.default_rng(self.seed)

        layer_scores = self._calculate_layer_scores(shipment_data)
        weighted_scores = {
            layer: score * self.layer_weights[layer]
            for layer, score in layer_scores.items()
        }
        overall_risk = sum(weighted_scores.values())

        loss_distribution = self._run_monte_carlo(layer_scores, n_simulations, rng)

        p95 = np.percentile(loss_distribution, 95)
        p99 = np.percentile(loss_distribution, 99)
        var_95 = p95 * cargo_value_usd
        var_99 = p99 * cargo_value_usd
        tail_95 = loss_distribution >= p95
        tail_99 = loss_distribution >= p99
        cvar_95 = (
            float(np.mean(loss_distribution[tail_95]) * cargo_value_usd)
            if np.any(tail_95)
            else var_95
        )
        cvar_99 = (
            float(np.mean(loss_distribution[tail_99]) * cargo_value_usd)
            if np.any(tail_99)
            else var_99
        )

        risk_10 = min(overall_risk * 10.0, 10.0)
        expected_loss_pct = float(np.clip(self.loss_function(np.array([risk_10]))[0], 0.0, 1.0))
        expected_loss_usd = expected_loss_pct * cargo_value_usd

        attribution = self._calculate_attribution(weighted_scores, overall_risk)
        result_hash = self._compute_result_hash(
            overall_risk, expected_loss_pct, var_95, var_99
        )

        data_quality_str = (
            shipment_data.overall_data_quality.value
            if hasattr(shipment_data.overall_data_quality, "value")
            else str(shipment_data.overall_data_quality)
        )

        result = CalibratedRiskResult(
            overall_risk_score=overall_risk,
            layer_scores=layer_scores,
            weighted_layer_scores=weighted_scores,
            expected_loss_pct=expected_loss_pct,
            expected_loss_usd=expected_loss_usd,
            var_95=float(var_95),
            var_99=float(var_99),
            cvar_95=cvar_95,
            cvar_99=cvar_99,
            loss_distribution=loss_distribution,
            percentiles={
                "p50": float(np.percentile(loss_distribution, 50)),
                "p75": float(np.percentile(loss_distribution, 75)),
                "p90": float(np.percentile(loss_distribution, 90)),
                "p95": float(p95),
                "p99": float(p99),
            },
            risk_factor_attribution=attribution,
            model_version_id=str(self.model_version.id),
            model_version_name=self.model_version.name,
            model_is_calibrated=self.model_version.is_calibrated(),
            data_quality=data_quality_str,
            data_confidence=shipment_data.overall_confidence,
            data_warnings=list(shipment_data.data_warnings),
            input_hash=input_hash,
            result_hash=result_hash,
            seed=self.seed,
        )

        if self.audit:
            try:
                self.audit.append_event(
                    tenant_id=self.tenant_id,
                    event_type="RISK_ASSESSMENT",
                    action="CALIBRATED_ASSESSMENT_COMPLETE",
                    entity_type="risk_assessment",
                    entity_id=result_hash,
                    actor_type="SYSTEM",
                    payload={
                        "model_version_id": str(self.model_version.id),
                        "model_is_calibrated": self.model_version.is_calibrated(),
                        "overall_risk": overall_risk,
                        "expected_loss_pct": expected_loss_pct,
                        "var_95": float(var_95),
                        "var_99": float(var_99),
                        "data_quality": data_quality_str,
                        "input_hash": input_hash,
                        "result_hash": result_hash,
                        "seed": self.seed,
                    },
                )
            except Exception as e:
                logger.warning("Failed to audit calibrated assessment: %s", e)

        return result

    def _calculate_layer_scores(self, data: UnifiedShipmentData) -> Dict[str, float]:
        """Calculate individual layer scores from unified shipment data."""
        scores: Dict[str, float] = {}

        origin = data.origin_port_conditions or {}
        dest = data.destination_port_conditions or {}
        o_risk = (origin.get("risk") or {}).get("port_risk_score", 5.0) / 10.0
        d_risk = (dest.get("risk") or {}).get("port_risk_score", 5.0) / 10.0
        scores["route_risk"] = (o_risk + d_risk) / 2.0

        ow = (data.origin_weather or {}).get("weather_risk_score", 0.5)
        dw = (data.destination_weather or {}).get("weather_risk_score", 0.5)
        scores["weather_risk"] = (ow + dw) / 2.0

        cargo_map = {
            "ELECTRONICS": 0.7,
            "MACHINERY": 0.5,
            "TEXTILES": 0.3,
            "FOOD_PERISHABLE": 0.8,
            "FOOD_DRY": 0.4,
            "CHEMICALS": 0.6,
            "PHARMACEUTICALS": 0.7,
            "GENERAL": 0.4,
        }
        scores["cargo_risk"] = cargo_map.get(
            (data.cargo_type or "GENERAL").upper(), 0.5
        )

        if data.carrier_performance:
            cr = (data.carrier_performance.get("rating") or {}).get(
                "carrier_risk_score", 3.0
            ) / 10.0
            scores["transport_risk"] = cr
        else:
            scores["transport_risk"] = 0.5

        o_eff = (origin.get("efficiency") or {}).get("berth_utilization_pct", 70) / 100.0
        d_eff = (dest.get("efficiency") or {}).get("berth_utilization_pct", 70) / 100.0
        scores["infrastructure_risk"] = (1.0 - o_eff + 1.0 - d_eff) / 2.0

        climate = data.climate_indices or {}
        enso = climate.get("enso_phase", "NEUTRAL") or "NEUTRAL"
        if "STRONG" in str(enso).upper():
            scores["seasonal_risk"] = 0.7
        elif "MODERATE" in str(enso).upper():
            scores["seasonal_risk"] = 0.5
        else:
            scores["seasonal_risk"] = 0.3

        scores["geopolitical_risk"] = 0.3
        scores["documentation_risk"] = 0.3
        scores["handling_risk"] = scores["cargo_risk"] * 0.8
        scores["security_risk"] = 0.3
        scores["regulatory_risk"] = 0.3

        value_risk = min((data.cargo_value_usd or 0) / 1_000_000.0, 1.0)
        scores["commercial_risk"] = value_risk * 0.5
        scores["financial_risk"] = 0.3

        for layer in self.LAYER_NAMES:
            if layer not in scores:
                scores[layer] = 0.5
            scores[layer] = float(np.clip(scores[layer], 0.0, 1.0))

        return scores

    def _run_monte_carlo(
        self,
        layer_scores: Dict[str, float],
        n_simulations: int,
        rng: np.random.Generator,
    ) -> np.ndarray:
        """Run Monte Carlo using calibrated correlation matrix and loss function."""
        n_layers = len(self.LAYER_NAMES)
        L_chol = np.linalg.cholesky(self.correlation_matrix)
        Z = rng.standard_normal((n_simulations, n_layers))
        correlated_Z = Z @ L_chol.T
        U = norm.cdf(correlated_Z)

        simulated = np.zeros((n_simulations, n_layers))
        for i, layer in enumerate(self.LAYER_NAMES):
            base = layer_scores[layer]
            simulated[:, i] = np.clip(base * (0.7 + 0.6 * U[:, i]), 0.0, 1.0)

        weights_arr = np.array([self.layer_weights[layer] for layer in self.LAYER_NAMES])
        overall_scores = simulated @ weights_arr

        risk_10 = np.clip(overall_scores * 10.0, 0.0, 10.0)
        loss_pcts = self.loss_function(risk_10)
        return np.clip(loss_pcts, 0.0, 1.0)

    def _calculate_attribution(
        self,
        weighted_scores: Dict[str, float],
        overall_risk: float,
    ) -> Dict[str, float]:
        """Factor attribution: each layer's share of overall risk."""
        if overall_risk == 0:
            return {layer: 0.0 for layer in self.LAYER_NAMES}
        return {
            layer: weighted_scores[layer] / overall_risk
            for layer in self.LAYER_NAMES
        }

    def _compute_input_hash(
        self,
        data: UnifiedShipmentData,
        cargo_value: float,
    ) -> str:
        """Hash inputs for reproducibility."""
        payload = {
            "origin": data.origin_port,
            "destination": data.destination_port,
            "cargo_type": data.cargo_type,
            "cargo_value": cargo_value,
            "collection_hash": data.collection_hash,
            "model_version_id": str(self.model_version.id),
            "seed": self.seed,
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str).encode()
        ).hexdigest()

    def _compute_result_hash(
        self,
        overall_risk: float,
        expected_loss: float,
        var_95: float,
        var_99: float,
    ) -> str:
        """Hash key results for verification."""
        payload = {
            "overall_risk": round(overall_risk, 6),
            "expected_loss": round(expected_loss, 6),
            "var_95": round(float(var_95), 2),
            "var_99": round(float(var_99), 2),
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode()
        ).hexdigest()


def create_calibrated_risk_engine(
    model_version: RiskModelVersion,
    audit: Optional[AuditLedger] = None,
    seed: Optional[int] = None,
    tenant_id: Optional[str] = None,
) -> CalibratedRiskEngine:
    """Factory for calibrated risk engine."""
    return CalibratedRiskEngine(
        model_version=model_version,
        audit=audit,
        seed=seed,
        tenant_id=tenant_id,
    )
