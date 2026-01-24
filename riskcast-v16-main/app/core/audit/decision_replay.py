"""
Decision Replay System

Enables reproduction of any risk decision from the audit trail.
This is CRITICAL for:
1. Regulatory audits ("Why did you give this risk score?")
2. Dispute resolution ("Prove your assessment was correct")
3. Model validation ("Verify model consistency")
4. Debugging ("What went wrong?")

The system can replay a decision using:
- Original inputs (from assessment/audit)
- Original model version (pinned)
- Original data state (archived when available)
- Original random seed (deterministic)
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.audit.immutable_ledger import ImmutableAuditLedger
from app.core.data_quality.gateway import DataQualityLevel, DataQualityReport, DecisionType
from app.core.risk_input.canonicalization import compute_input_hash
from app.core.risk_engine.v16.risk_engine_calibrated import (
    CalibratedRiskEngine,
    CalibratedRiskResult,
)
from app.models.risk_assessment import RiskAssessment
from app.models.risk_run import RiskRun, RiskRunStatus
from app.modules.model_versioning.models import RiskModelVersion
from app.services.unified_data_service import UnifiedShipmentData

logger = logging.getLogger(__name__)


@dataclass
class ReplayResult:
    """Result of decision replay."""

    original_risk_run_id: str
    original_timestamp: datetime
    original_result_hash: str
    original_overall_risk: float
    original_expected_loss_pct: float

    replayed_result_hash: str
    replayed_overall_risk: float
    replayed_expected_loss_pct: float

    is_deterministic: bool
    overall_risk_diff: float
    expected_loss_diff: float

    model_version_id: str
    model_version_name: str
    model_is_calibrated: bool

    replayed_at: datetime
    replay_seed: int
    replay_duration_ms: int

    input_hash_match: bool
    model_hash_match: bool

    differences: Optional[Dict[str, Any]] = None


@dataclass
class DecisionPackage:
    """Complete package of information for a decision."""

    risk_run_id: str
    risk_run_timestamp: datetime

    inputs: Dict[str, Any]
    input_hash: str

    data_snapshot: Dict[str, Any]
    data_sources: List[Dict[str, Any]]
    data_quality: Dict[str, Any]

    model_version_id: str
    model_version_name: str
    model_parameters: Dict[str, Any]
    model_hash: str

    result: Dict[str, Any]
    result_hash: str

    seed: int

    audit_events: List[Dict[str, Any]]

    package_hash: str
    generated_at: datetime


def _parse_date(v: Any) -> Optional[date]:
    """Parse date from input snapshot."""
    if v is None:
        return None
    if isinstance(v, date) and not isinstance(v, datetime):
        return v
    if isinstance(v, datetime):
        return v.date()
    s = str(v).strip()
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
        try:
            dt = datetime.strptime(s[:26], fmt)
            return dt.date()
        except ValueError:
            continue
    return None


def _mock_data_quality_report() -> DataQualityReport:
    """Minimal report for replay (archived data)."""
    return DataQualityReport(
        decision_type=DecisionType.RISK_ASSESSMENT,
        overall_quality=DataQualityLevel.GOOD,
        overall_confidence=0.8,
        sources=[],
        missing_sources=[],
        fallback_sources=[],
        warnings=[],
        can_proceed=True,
        requires_acknowledgment=False,
        block_reason=None,
        generated_at=datetime.utcnow(),
    )


def _inputs_to_shipment_data(
    inputs: Dict[str, Any],
    data_snapshot: Dict[str, Any],
    collection_hash: str = "replay",
) -> UnifiedShipmentData:
    """Build UnifiedShipmentData from inputs and optional data snapshot."""
    # Handle nested shipment key (common in canonical input)
    raw = inputs.get("shipment", inputs)
    origin = str((raw.get("origin_port") or raw.get("origin")) or "")
    dest = str((raw.get("destination_port") or raw.get("destination")) or "")
    cargo = str((raw.get("cargo_type") or raw.get("cargo")) or "GENERAL")
    value = float(raw.get("cargo_value_usd") or raw.get("cargo_value") or 0)
    containers = int(raw.get("container_count") or raw.get("containers") or 1)
    dep = _parse_date(raw.get("departure_date") or raw.get("etd"))
    eta = _parse_date(raw.get("expected_arrival_date") or raw.get("eta"))
    carrier = raw.get("carrier_code") or raw.get("carrier")

    if not dep:
        dep = date.today()
    if not eta:
        eta = dep

    weather = data_snapshot.get("weather") or {}
    ports = data_snapshot.get("ports") or {}
    origin_weather = weather.get("origin", data_snapshot.get("origin_weather", {}))
    dest_weather = weather.get("destination", data_snapshot.get("destination_weather", {}))
    route_weather = weather.get("route", data_snapshot.get("route_weather"))
    origin_port = ports.get("origin", data_snapshot.get("origin_port_conditions", {}))
    dest_port = ports.get("destination", data_snapshot.get("destination_port_conditions", {}))
    carrier_data = (data_snapshot.get("carrier") or {}).get("performance")
    carrier_route = (data_snapshot.get("carrier") or {}).get("route_performance")
    climate = data_snapshot.get("climate", data_snapshot.get("climate_indices", {}))

    return UnifiedShipmentData(
        origin_port=origin,
        destination_port=dest,
        cargo_type=cargo,
        cargo_value_usd=value,
        container_count=containers,
        departure_date=dep,
        expected_arrival_date=eta,
        carrier_code=carrier,
        origin_weather=origin_weather,
        destination_weather=dest_weather,
        route_weather=route_weather,
        origin_port_conditions=origin_port,
        destination_port_conditions=dest_port,
        carrier_performance=carrier_data,
        carrier_route_performance=carrier_route,
        climate_indices=climate,
        data_sources=[],
        data_quality_report=_mock_data_quality_report(),
        overall_data_quality=DataQualityLevel.GOOD,
        overall_confidence=0.8,
        data_warnings=[],
        collected_at=datetime.utcnow(),
        collection_hash=collection_hash,
    )


class DecisionReplaySystem:
    """
    System for replaying and verifying risk decisions.

    Key capabilities:
    1. Retrieve complete decision context from audit trail
    2. Replay decision with original parameters
    3. Verify determinism (same inputs → same outputs)
    4. Export decision package for regulatory review
    """

    def __init__(self, db: Session, audit_ledger: ImmutableAuditLedger):
        self.db = db
        self.audit = audit_ledger

    async def replay_decision(self, risk_run_id: str) -> ReplayResult:
        """
        Replay a risk decision to verify determinism.

        Proves that the same inputs with the same model produce the same results.
        """
        start_time = datetime.utcnow()

        risk_run = self.db.query(RiskRun).filter(RiskRun.id == risk_run_id).first()
        if not risk_run:
            raise ValueError(f"Risk run {risk_run_id} not found")

        if risk_run.status != RiskRunStatus.SUCCEEDED:
            raise ValueError(
                f"Risk run {risk_run_id} has status {risk_run.status.value}, "
                "expected SUCCEEDED. Cannot replay failed or pending runs."
            )

        assessment = (
            self.db.query(RiskAssessment)
            .filter(RiskAssessment.id == risk_run.assessment_id)
            .first()
        )
        if not assessment:
            raise ValueError(
                f"Assessment {risk_run.assessment_id} for run {risk_run_id} not found"
            )

        model_version = None
        if risk_run.model_version_id:
            model_version = (
                self.db.query(RiskModelVersion)
                .filter(RiskModelVersion.id == risk_run.model_version_id)
                .first()
            )
        if not model_version:
            raise ValueError(
                f"Model version {risk_run.model_version_id or 'N/A'} not found. "
                "Cannot replay without original model."
            )

        model_hash_match = True
        if model_version.immutable_hash:
            try:
                computed = model_version.compute_immutable_hash()
                model_hash_match = computed == model_version.immutable_hash
            except Exception:
                model_hash_match = False

        inputs = assessment.input_snapshot_json or {}
        original_input_hash = assessment.input_hash
        original_seed = int(risk_run.seed)
        data_snapshot = getattr(risk_run, "data_snapshot_json", None) or {}
        result_json = risk_run.result_json or {}
        original_overall = float(result_json.get("overall_risk_score", 0))
        original_expected = float(
            result_json.get("expected_loss_pct") or result_json.get("expected_loss", 0)
        )
        original_result_hash = risk_run.result_hash or ""

        engine = CalibratedRiskEngine(
            model_version=model_version,
            audit=None,
            seed=original_seed,
            tenant_id=risk_run.tenant_id,
        )

        raw = inputs.get("shipment", inputs)
        cargo_override = raw.get("cargo_value_usd") or raw.get("cargo_value")
        replayed = await self._replay_with_archived_data(
            engine, inputs, data_snapshot,
            float(cargo_override) if cargo_override is not None else None,
        )

        end_time = datetime.utcnow()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        is_det = (
            abs(replayed.overall_risk_score - original_overall) < 1e-6
            and abs(replayed.expected_loss_pct - original_expected) < 1e-6
        )
        replayed_input_hash = compute_input_hash(inputs)
        input_hash_match = replayed_input_hash == original_input_hash

        differences = None
        if not is_det:
            differences = self._compute_differences(risk_run, replayed, result_json)

        result = ReplayResult(
            original_risk_run_id=risk_run_id,
            original_timestamp=risk_run.created_at,
            original_result_hash=original_result_hash,
            original_overall_risk=original_overall,
            original_expected_loss_pct=original_expected,
            replayed_result_hash=replayed.result_hash,
            replayed_overall_risk=replayed.overall_risk_score,
            replayed_expected_loss_pct=replayed.expected_loss_pct,
            is_deterministic=is_det,
            overall_risk_diff=replayed.overall_risk_score - original_overall,
            expected_loss_diff=replayed.expected_loss_pct - original_expected,
            model_version_id=str(model_version.id),
            model_version_name=model_version.name,
            model_is_calibrated=model_version.is_calibrated(),
            replayed_at=end_time,
            replay_seed=original_seed,
            replay_duration_ms=duration_ms,
            input_hash_match=input_hash_match,
            model_hash_match=model_hash_match,
            differences=differences,
        )

        self.audit.append_event(
            event_type="COMPLIANCE",
            action="DECISION_REPLAYED",
            entity_type="risk_run",
            entity_id=risk_run_id,
            actor_type="SYSTEM",
            tenant_id=risk_run.tenant_id,
            payload={
                "is_deterministic": is_det,
                "input_hash_match": input_hash_match,
                "model_hash_match": model_hash_match,
                "overall_risk_diff": result.overall_risk_diff,
                "replay_duration_ms": duration_ms,
            },
        )

        return result

    async def get_decision_package(self, risk_run_id: str) -> DecisionPackage:
        """
        Get complete decision package for regulatory review.

        Contains everything needed to understand and verify a decision.
        """
        risk_run = self.db.query(RiskRun).filter(RiskRun.id == risk_run_id).first()
        if not risk_run:
            raise ValueError(f"Risk run {risk_run_id} not found")

        assessment = (
            self.db.query(RiskAssessment)
            .filter(RiskAssessment.id == risk_run.assessment_id)
            .first()
        )
        model_version = None
        if risk_run.model_version_id:
            model_version = (
                self.db.query(RiskModelVersion)
                .filter(RiskModelVersion.id == risk_run.model_version_id)
                .first()
            )

        events = self.audit.get_events_for_entity(
            entity_type="risk_run",
            entity_id=risk_run_id,
            tenant_id=risk_run.tenant_id,
        )
        serialized = [
            {
                "sequence": e.sequence_number,
                "type": e.event_type,
                "action": e.action,
                "timestamp": e.event_timestamp.isoformat(),
                "payload": e.payload_json,
                "hash": e.event_hash,
            }
            for e in events
        ]

        inputs = (assessment.input_snapshot_json or {}) if assessment else {}
        result_json = risk_run.result_json or {}
        result = {
            "overall_risk_score": result_json.get("overall_risk_score"),
            "expected_loss_percentage": result_json.get("expected_loss_pct")
            or result_json.get("expected_loss"),
            "var_95": result_json.get("var_95"),
            "var_99": result_json.get("var_99"),
            "layer_scores": result_json.get("layer_scores") or result_json.get("risk_factors"),
            "factor_attribution": result_json.get("risk_factor_attribution")
            or result_json.get("risk_factors"),
        }

        model_params = {}
        if model_version:
            model_params = {
                "base_weights": model_version.base_weights_json,
                "correlation_matrix": model_version.correlation_matrix_json,
                "loss_transform_params": model_version.loss_transform_params_json,
            }

        pkg = DecisionPackage(
            risk_run_id=risk_run_id,
            risk_run_timestamp=risk_run.created_at,
            inputs=inputs,
            input_hash=assessment.input_hash if assessment else "",
            data_snapshot=getattr(risk_run, "data_snapshot_json", None) or {},
            data_sources=[],
            data_quality={},
            model_version_id=str(model_version.id) if model_version else "unknown",
            model_version_name=model_version.name if model_version else "unknown",
            model_parameters=model_params,
            model_hash=model_version.immutable_hash or "" if model_version else "",
            result=result,
            result_hash=risk_run.result_hash or "",
            seed=int(risk_run.seed),
            audit_events=serialized,
            package_hash="",
            generated_at=datetime.utcnow(),
        )
        pkg.package_hash = self._compute_package_hash(pkg)

        self.audit.append_event(
            event_type="COMPLIANCE",
            action="DECISION_PACKAGE_EXPORTED",
            entity_type="risk_run",
            entity_id=risk_run_id,
            actor_type="SYSTEM",
            tenant_id=risk_run.tenant_id,
            payload={
                "package_hash": pkg.package_hash,
                "event_count": len(serialized),
            },
        )

        return pkg

    def verify_decision_integrity(self, risk_run_id: str) -> Dict[str, Any]:
        """
        Verify integrity of a stored decision.

        Checks:
        1. Input hash matches stored inputs
        2. Result hash matches stored results
        3. Model hash matches stored model
        4. Audit chain is intact
        """
        risk_run = self.db.query(RiskRun).filter(RiskRun.id == risk_run_id).first()
        if not risk_run:
            raise ValueError(f"Risk run {risk_run_id} not found")

        assessment = (
            self.db.query(RiskAssessment)
            .filter(RiskAssessment.id == risk_run.assessment_id)
            .first()
        )
        model_version = None
        if risk_run.model_version_id:
            model_version = (
                self.db.query(RiskModelVersion)
                .filter(RiskModelVersion.id == risk_run.model_version_id)
                .first()
            )

        inputs = (assessment.input_snapshot_json or {}) if assessment else {}
        result_json = risk_run.result_json or {}

        checks: Dict[str, Any] = {}

        computed_input = compute_input_hash(inputs)
        checks["input_hash"] = {
            "stored": assessment.input_hash if assessment else None,
            "computed": computed_input,
            "valid": computed_input == (assessment.input_hash if assessment else None),
        }

        o_risk = float(result_json.get("overall_risk_score", 0))
        exp = float(result_json.get("expected_loss_pct") or result_json.get("expected_loss", 0))
        v95 = float(result_json.get("var_95", 0))
        v99 = float(result_json.get("var_99", 0))
        computed_result = self._compute_result_hash(o_risk, exp, v95, v99)
        checks["result_hash"] = {
            "stored": risk_run.result_hash,
            "computed": computed_result,
            "valid": computed_result == risk_run.result_hash,
        }

        if model_version and model_version.immutable_hash:
            try:
                computed_model = model_version.compute_immutable_hash()
                checks["model_hash"] = {
                    "stored": model_version.immutable_hash,
                    "computed": computed_model,
                    "valid": computed_model == model_version.immutable_hash,
                }
            except Exception as e:
                checks["model_hash"] = {
                    "stored": model_version.immutable_hash,
                    "computed": None,
                    "valid": False,
                    "note": str(e),
                }
        else:
            checks["model_hash"] = {
                "stored": None,
                "computed": None,
                "valid": True,
                "note": "Model was not published with immutable hash",
            }

        events = self.audit.get_events_for_entity(
            entity_type="risk_run",
            entity_id=risk_run_id,
            tenant_id=risk_run.tenant_id,
        )
        if events:
            first_seq = events[0].sequence_number
            last_seq = events[-1].sequence_number
            verification = self.audit.verify_chain(
                start_sequence=first_seq,
                end_sequence=last_seq,
            )
            checks["audit_chain"] = {
                "valid": verification.is_valid,
                "events_checked": verification.events_checked,
                "verification_hash": verification.verification_hash,
            }
        else:
            checks["audit_chain"] = {
                "valid": False,
                "note": "No audit events found for this risk run",
            }

        all_valid = all(c.get("valid", False) for c in checks.values())

        return {
            "risk_run_id": risk_run_id,
            "verified_at": datetime.utcnow().isoformat(),
            "is_valid": all_valid,
            "checks": checks,
        }

    async def _replay_with_archived_data(
        self,
        engine: CalibratedRiskEngine,
        inputs: Dict[str, Any],
        data_snapshot: Dict[str, Any],
        cargo_value_override: Optional[float] = None,
    ) -> CalibratedRiskResult:
        """Replay assessment using archived data state."""
        raw = inputs.get("shipment", inputs)
        cargo_value = cargo_value_override
        if cargo_value is None:
            cargo_value = float(raw.get("cargo_value_usd") or raw.get("cargo_value") or 0)
        shipment = _inputs_to_shipment_data(inputs, data_snapshot)
        return await engine.run_assessment(
            shipment_data=shipment,
            cargo_value_usd=cargo_value,
        )

    def _compute_differences(
        self,
        risk_run: RiskRun,
        replayed: CalibratedRiskResult,
        result_json: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Compute detailed differences between original and replay."""
        orig_overall = float(result_json.get("overall_risk_score", 0))
        orig_exp = float(
            result_json.get("expected_loss_pct") or result_json.get("expected_loss", 0)
        )
        diffs: Dict[str, Any] = {
            "overall_risk": {
                "original": orig_overall,
                "replayed": replayed.overall_risk_score,
                "diff": replayed.overall_risk_score - orig_overall,
            },
            "expected_loss": {
                "original": orig_exp,
                "replayed": replayed.expected_loss_pct,
                "diff": replayed.expected_loss_pct - orig_exp,
            },
        }
        layer_orig = result_json.get("layer_scores") or result_json.get("risk_factors") or {}
        if layer_orig and replayed.layer_scores:
            layer_diffs = {}
            for layer, orig_score in layer_orig.items():
                if isinstance(orig_score, (int, float)):
                    replay_score = replayed.layer_scores.get(layer, 0.0)
                    layer_diffs[layer] = {
                        "original": orig_score,
                        "replayed": replay_score,
                        "diff": replay_score - orig_score,
                    }
            diffs["layer_scores"] = layer_diffs
        return diffs

    def _compute_result_hash(
        self,
        overall_risk: float,
        expected_loss: float,
        var_95: float,
        var_99: float,
    ) -> str:
        """Compute hash of results (match engine's _compute_result_hash)."""
        data = {
            "overall_risk": round(overall_risk, 6),
            "expected_loss": round(expected_loss, 6),
            "var_95": round(var_95, 2),
            "var_99": round(var_99, 2),
        }
        canonical = json.dumps(data, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()

    def _compute_package_hash(self, package: DecisionPackage) -> str:
        """Compute hash of complete decision package."""
        data = {
            "risk_run_id": package.risk_run_id,
            "input_hash": package.input_hash,
            "result_hash": package.result_hash,
            "model_hash": package.model_hash,
            "event_count": len(package.audit_events),
        }
        canonical = json.dumps(data, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()
