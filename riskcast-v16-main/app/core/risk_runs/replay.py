"""
Risk Run Replay Tool
Verifies reproducibility of risk runs by re-executing them and comparing results.
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import asyncio
import json

from sqlalchemy.orm import Session

from app.models.risk_run import RiskRun, RiskRunStatus
from app.repositories.risk_run_repository import RiskRunRepository
from app.repositories.risk_assessment_repository import RiskAssessmentRepository
from app.modules.risk_engine_v3.service import RiskEngineV3
from app.modules.risk_engine_v3.schemas import (
    RiskEngineInputV3,
    RiskEngineRunConfig,
)
from app.shared.exceptions import NotFoundError


@dataclass
class ReplayResult:
    """Result of replaying a risk run"""
    run_id: str
    matches: bool
    original_hash: str
    replay_hash: str
    diff_summary: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    replay_duration_seconds: Optional[float] = None


class RiskRunReplayer:
    """Tool for replaying risk runs to verify reproducibility"""

    def __init__(self, db: Session):
        """
        Initialize replayer.

        Args:
            db: Database session
        """
        self.db = db
        self.repository = RiskRunRepository(db)
        self.assessment_repository = RiskAssessmentRepository(db)
        self.engine = RiskEngineV3()

    def replay(self, run_id: str) -> ReplayResult:
        """
        Replay a risk run and verify reproducibility.

        Steps:
        1. Load original run
        2. Load assessment input
        3. Re-run engine with SAME:
           - seed
           - iterations
           - engine_version
           - model_version (when implemented)
        4. Compare result_hash
        5. If mismatch, compute diff

        Args:
            run_id: Run ID (UUID string)

        Returns:
            ReplayResult with verification status
        """
        start_time = datetime.utcnow()

        try:
            # 1. Load original run
            # Note: We need tenant_id, but replay might be called without it
            # So we'll query directly
            run = self.db.query(RiskRun).filter(RiskRun.id == run_id).first()
            if not run:
                return ReplayResult(
                    run_id=run_id,
                    matches=False,
                    original_hash="",
                    replay_hash="",
                    error=f"Run {run_id} not found",
                )

            if run.status != RiskRunStatus.SUCCEEDED:
                return ReplayResult(
                    run_id=run_id,
                    matches=False,
                    original_hash=run.result_hash or "",
                    replay_hash="",
                    error=f"Run {run_id} has status {run.status.value}, expected SUCCEEDED",
                )

            if not run.result_hash:
                return ReplayResult(
                    run_id=run_id,
                    matches=False,
                    original_hash="",
                    replay_hash="",
                    error=f"Run {run_id} has no result_hash",
                )

            tenant_id = run.tenant_id
            original_hash = run.result_hash

            # 2. Load assessment input
            assessment = self.assessment_repository.get_by_id(
                tenant_id, run.assessment_id
            )
            if not assessment:
                return ReplayResult(
                    run_id=run_id,
                    matches=False,
                    original_hash=original_hash,
                    replay_hash="",
                    error=f"Assessment {run.assessment_id} not found",
                )

            # 3. Re-run engine with SAME parameters
            input_dto = RiskEngineInputV3(
                tenant_id=tenant_id,
                risk_assessment_id=assessment.id,
                input_schema_version=assessment.input_schema_version,
                input_snapshot=assessment.input_snapshot_json,
                input_hash=assessment.input_hash,
                corridor_id=assessment.corridor_id,
            )

            run_config = RiskEngineRunConfig(
                engine_version=run.engine_version,
                model_version_id=run.model_version_id,
                seed=run.seed,
                iterations=run.iterations,
            )

            # Execute engine (async)
            result_dto, replay_hash = asyncio.run(
                self.engine.run(input_dto, run_config)
            )

            # 4. Compare result_hash
            matches = original_hash == replay_hash

            # 5. If mismatch, compute diff
            diff_summary = None
            if not matches:
                # Get original result
                original_result = run.result_json or {}
                replay_result = result_dto.model_dump(
                    exclude_none=True, mode="json"
                )

                # Compute diff
                diff_summary = self._compute_diff(original_result, replay_result)

            duration = (datetime.utcnow() - start_time).total_seconds()

            return ReplayResult(
                run_id=run_id,
                matches=matches,
                original_hash=original_hash,
                replay_hash=replay_hash,
                diff_summary=diff_summary,
                replay_duration_seconds=duration,
            )

        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            return ReplayResult(
                run_id=run_id,
                matches=False,
                original_hash="",
                replay_hash="",
                error=str(e),
                replay_duration_seconds=duration,
            )

    def batch_replay(self, run_ids: List[str]) -> List[ReplayResult]:
        """
        Replay multiple runs.

        Args:
            run_ids: List of run IDs

        Returns:
            List of ReplayResult instances
        """
        results = []
        for run_id in run_ids:
            result = self.replay(run_id)
            results.append(result)
        return results

    def _compute_diff(
        self, original: Dict[str, Any], replay: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compute diff between original and replayed results.

        Args:
            original: Original result dictionary
            replay: Replayed result dictionary

        Returns:
            Diff summary dictionary with:
            - added_keys: Keys in replay but not in original
            - removed_keys: Keys in original but not in replay
            - changed_keys: Keys with different values
            - sample_diffs: Sample of value differences
        """
        diff = {
            "added_keys": [],
            "removed_keys": [],
            "changed_keys": [],
            "sample_diffs": [],
        }

        # Get all keys
        original_keys = set(original.keys())
        replay_keys = set(replay.keys())

        # Find added and removed keys
        diff["added_keys"] = sorted(list(replay_keys - original_keys))
        diff["removed_keys"] = sorted(list(original_keys - replay_keys))

        # Find changed keys
        common_keys = original_keys & replay_keys
        for key in common_keys:
            orig_val = original[key]
            replay_val = replay[key]

            if not self._values_equal(orig_val, replay_val):
                diff["changed_keys"].append(key)
                # Store sample diff (limit to first 10)
                if len(diff["sample_diffs"]) < 10:
                    diff["sample_diffs"].append({
                        "key": key,
                        "original": self._serialize_value(orig_val),
                        "replay": self._serialize_value(replay_val),
                    })

        return diff

    def _values_equal(self, val1: Any, val2: Any) -> bool:
        """
        Compare two values for equality (handles floats with tolerance).

        Args:
            val1: First value
            val2: Second value

        Returns:
            True if values are equal (within tolerance for floats)
        """
        # Handle None
        if val1 is None and val2 is None:
            return True
        if val1 is None or val2 is None:
            return False

        # Handle floats with tolerance
        if isinstance(val1, float) and isinstance(val2, float):
            return abs(val1 - val2) < 1e-6

        # Handle lists
        if isinstance(val1, list) and isinstance(val2, list):
            if len(val1) != len(val2):
                return False
            return all(
                self._values_equal(v1, v2) for v1, v2 in zip(val1, val2)
            )

        # Handle dicts
        if isinstance(val1, dict) and isinstance(val2, dict):
            if set(val1.keys()) != set(val2.keys()):
                return False
            return all(
                self._values_equal(val1[k], val2[k]) for k in val1.keys()
            )

        # Default comparison
        return val1 == val2

    def _serialize_value(self, val: Any) -> Any:
        """
        Serialize value for diff display.

        Args:
            val: Value to serialize

        Returns:
            Serialized value (truncated if too long)
        """
        if isinstance(val, (dict, list)):
            # Convert to JSON string, truncate if too long
            json_str = json.dumps(val, sort_keys=True, default=str)
            if len(json_str) > 200:
                return json_str[:200] + "..."
            return json_str
        if isinstance(val, float):
            return round(val, 8)
        return val
