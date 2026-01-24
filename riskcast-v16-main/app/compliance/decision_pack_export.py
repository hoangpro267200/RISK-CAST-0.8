"""
Decision Package Export Service

Creates comprehensive decision packages for:
1. Regulatory submissions
2. Audit responses
3. Dispute resolution
4. Reinsurance documentation

A decision package contains EVERYTHING needed to
understand and verify a risk/underwriting decision.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Protocol
from dataclasses import dataclass
import json
import hashlib
import zipfile
import io
import logging

from sqlalchemy.orm import Session

from app.core.audit import (
    ImmutableAuditLedger,
    DecisionReplaySystem,
    DecisionPackage,
)
from app.evidence import ChainOfCustodyService
from app.models.risk_run import RiskRun
from app.modules.underwriting.models import Policy
from app.modules.claims.models import Claim
from app.modules.risk_runs.models import RiskRun as ModulesRiskRun

logger = logging.getLogger(__name__)


class DecisionPackStorage(Protocol):
    """Protocol for decision pack storage."""

    def upload_decision_pack(
        self, pack_id: str, content: bytes, content_type: str
    ) -> str:
        """
        Upload decision pack to storage.

        Args:
            pack_id: Unique pack identifier
            content: ZIP file bytes
            content_type: MIME type (e.g., "application/zip")

        Returns:
            Download URL or storage URI
        """
        ...


class LocalDecisionPackStorage:
    """Local storage implementation using EvidenceStorage."""

    def __init__(self, evidence_storage):
        """
        Initialize with EvidenceStorage instance.

        Args:
            evidence_storage: EvidenceStorage instance (from app.core.evidence.storage)
        """
        self.storage = evidence_storage

    def upload_decision_pack(
        self, pack_id: str, content: bytes, content_type: str
    ) -> str:
        """Upload to evidence storage and return URI."""
        path = f"decision_packs/{pack_id}.zip"
        uri = self.storage.upload(content, path)
        # Return a download URL path (API can serve from storage)
        return f"/api/v3/compliance/decision-packs/{pack_id}/download"


@dataclass
class ExportedDecisionPack:
    """Exported decision package."""

    pack_id: str
    entity_type: str  # "risk_run", "policy", "claim"
    entity_id: str

    # Files included
    files: List[Dict[str, str]]  # [{"name": "...", "type": "...", "hash": "..."}]

    # Package info
    total_size_bytes: int
    created_at: datetime
    created_by: str

    # Verification
    manifest_hash: str
    is_verified: bool

    # Download info
    download_url: str
    expires_at: datetime


class DecisionPackExportService:
    """
    Service for exporting complete decision packages.

    Packages include:
    - Decision data (inputs, outputs, model)
    - Audit trail
    - Evidence bundles
    - Verification proofs
    - Model parameters
    """

    def __init__(
        self,
        db: Session,
        audit: ImmutableAuditLedger,
        replay_system: DecisionReplaySystem,
        evidence_service: ChainOfCustodyService,
        storage: DecisionPackStorage,
    ):
        self.db = db
        self.audit = audit
        self.replay = replay_system
        self.evidence = evidence_service
        self.storage = storage
        self.logger = logging.getLogger(__name__)

    async def export_risk_run(
        self,
        risk_run_id: str,
        include_replay: bool = True,
        include_evidence: bool = True,
        created_by_user_id: str = "system",
    ) -> ExportedDecisionPack:
        """
        Export complete decision package for a risk run.
        """
        pack_id = f"pack_{risk_run_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        # Get decision package
        decision_package = await self.replay.get_decision_package(risk_run_id)

        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        files = []

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # 1. Decision summary
            summary = self._create_decision_summary(decision_package)
            summary_json = json.dumps(summary, indent=2, default=str)
            zip_file.writestr("01_decision_summary.json", summary_json)
            files.append(
                {
                    "name": "01_decision_summary.json",
                    "type": "application/json",
                    "hash": hashlib.sha256(summary_json.encode()).hexdigest(),
                }
            )

            # 2. Full inputs
            inputs_json = json.dumps(decision_package.inputs, indent=2, default=str)
            zip_file.writestr("02_inputs.json", inputs_json)
            files.append(
                {
                    "name": "02_inputs.json",
                    "type": "application/json",
                    "hash": hashlib.sha256(inputs_json.encode()).hexdigest(),
                }
            )

            # 3. Data snapshot
            data_json = json.dumps(decision_package.data_snapshot, indent=2, default=str)
            zip_file.writestr("03_data_snapshot.json", data_json)
            files.append(
                {
                    "name": "03_data_snapshot.json",
                    "type": "application/json",
                    "hash": hashlib.sha256(data_json.encode()).hexdigest(),
                }
            )

            # 4. Model parameters
            model_json = json.dumps(
                {
                    "model_version_id": decision_package.model_version_id,
                    "model_version_name": decision_package.model_version_name,
                    "parameters": decision_package.model_parameters,
                    "model_hash": decision_package.model_hash,
                },
                indent=2,
                default=str,
            )
            zip_file.writestr("04_model_parameters.json", model_json)
            files.append(
                {
                    "name": "04_model_parameters.json",
                    "type": "application/json",
                    "hash": hashlib.sha256(model_json.encode()).hexdigest(),
                }
            )

            # 5. Results
            results_json = json.dumps(decision_package.result, indent=2, default=str)
            zip_file.writestr("05_results.json", results_json)
            files.append(
                {
                    "name": "05_results.json",
                    "type": "application/json",
                    "hash": hashlib.sha256(results_json.encode()).hexdigest(),
                }
            )

            # 6. Audit trail
            audit_json = json.dumps(decision_package.audit_events, indent=2, default=str)
            zip_file.writestr("06_audit_trail.json", audit_json)
            files.append(
                {
                    "name": "06_audit_trail.json",
                    "type": "application/json",
                    "hash": hashlib.sha256(audit_json.encode()).hexdigest(),
                }
            )

            # 7. Replay verification (if requested)
            if include_replay:
                try:
                    replay_result = await self.replay.replay_decision(risk_run_id)
                    replay_json = json.dumps(
                        {
                            "is_deterministic": replay_result.is_deterministic,
                            "original_result_hash": replay_result.original_result_hash,
                            "replayed_result_hash": replay_result.replayed_result_hash,
                            "overall_risk_diff": replay_result.overall_risk_diff,
                            "expected_loss_diff": replay_result.expected_loss_diff,
                            "model_hash_match": replay_result.model_hash_match,
                            "input_hash_match": replay_result.input_hash_match,
                            "replayed_at": replay_result.replayed_at.isoformat(),
                        },
                        indent=2,
                    )
                    zip_file.writestr("07_replay_verification.json", replay_json)
                    files.append(
                        {
                            "name": "07_replay_verification.json",
                            "type": "application/json",
                            "hash": hashlib.sha256(replay_json.encode()).hexdigest(),
                        }
                    )
                except Exception as e:
                    self.logger.warning(f"Replay failed: {e}")

            # 8. Integrity verification
            integrity = self.replay.verify_decision_integrity(risk_run_id)
            integrity_json = json.dumps(integrity, indent=2, default=str)
            zip_file.writestr("08_integrity_verification.json", integrity_json)
            files.append(
                {
                    "name": "08_integrity_verification.json",
                    "type": "application/json",
                    "hash": hashlib.sha256(integrity_json.encode()).hexdigest(),
                }
            )

            # 9. Manifest
            manifest = {
                "pack_id": pack_id,
                "entity_type": "risk_run",
                "entity_id": risk_run_id,
                "created_at": datetime.utcnow().isoformat(),
                "created_by": created_by_user_id,
                "files": files,
                "decision_hash": decision_package.package_hash,
                "export_version": "1.0",
            }
            manifest_json = json.dumps(manifest, indent=2, sort_keys=True)
            manifest_hash = hashlib.sha256(manifest_json.encode()).hexdigest()
            manifest["manifest_hash"] = manifest_hash

            zip_file.writestr("00_manifest.json", json.dumps(manifest, indent=2))

        # Get ZIP content
        zip_content = zip_buffer.getvalue()
        total_size = len(zip_content)

        # Upload to storage
        download_url = self.storage.upload_decision_pack(
            pack_id=pack_id, content=zip_content, content_type="application/zip"
        )

        # Audit the export
        self.audit.append_event(
            event_type="COMPLIANCE",
            action="DECISION_PACK_EXPORTED",
            entity_type="risk_run",
            entity_id=risk_run_id,
            actor_type="USER",
            actor_id=created_by_user_id,
            payload={
                "pack_id": pack_id,
                "file_count": len(files),
                "total_size_bytes": total_size,
                "manifest_hash": manifest_hash,
            },
        )

        return ExportedDecisionPack(
            pack_id=pack_id,
            entity_type="risk_run",
            entity_id=risk_run_id,
            files=files,
            total_size_bytes=total_size,
            created_at=datetime.utcnow(),
            created_by=created_by_user_id,
            manifest_hash=manifest_hash,
            is_verified=True,
            download_url=download_url,
            expires_at=datetime.utcnow() + timedelta(days=7),
        )

    async def export_policy(
        self,
        policy_id: str,
        include_risk_runs: bool = True,
        include_claims: bool = True,
        created_by_user_id: str = "system",
    ) -> ExportedDecisionPack:
        """
        Export complete decision package for a policy.

        Includes:
        - Policy details
        - Underwriting decision
        - Related risk runs
        - Related claims (if any)
        """
        pack_id = f"policy_pack_{policy_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        policy = self.db.query(Policy).filter(Policy.id == policy_id).first()
        if not policy:
            raise ValueError(f"Policy {policy_id} not found")

        zip_buffer = io.BytesIO()
        files = []

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # 1. Policy summary
            policy_summary = {
                "policy_id": str(policy.id),
                "policy_number": policy.policy_number,
                "status": policy.status.value if hasattr(policy.status, "value") else str(policy.status),
                "effective_from": policy.effective_from.isoformat() if policy.effective_from else None,
                "effective_to": policy.effective_to.isoformat() if policy.effective_to else None,
                "premium": policy.premium_json or {},
                "terms": policy.terms_json or {},
                "risk_snapshot": policy.risk_snapshot_json or {},
                "bound_at": policy.bound_at.isoformat() if policy.bound_at else None,
                "bound_by": str(policy.bound_by_user_id) if policy.bound_by_user_id else None,
                "created_at": policy.created_at.isoformat() if policy.created_at else None,
            }
            summary_json = json.dumps(policy_summary, indent=2, default=str)
            zip_file.writestr("01_policy_summary.json", summary_json)
            files.append(
                {
                    "name": "01_policy_summary.json",
                    "type": "application/json",
                    "hash": hashlib.sha256(summary_json.encode()).hexdigest(),
                }
            )

            # 2. Underwriting decision (from risk snapshot or policy)
            underwriting = {
                "model_version_id": str(policy.model_version_id) if policy.model_version_id else None,
                "risk_run_id": str(policy.risk_run_id) if policy.risk_run_id else None,
                "risk_snapshot": policy.risk_snapshot_json or {},
                "policy_hash": policy.policy_hash,
            }
            underwriting_json = json.dumps(underwriting, indent=2, default=str)
            zip_file.writestr("02_underwriting_decision.json", underwriting_json)
            files.append(
                {
                    "name": "02_underwriting_decision.json",
                    "type": "application/json",
                    "hash": hashlib.sha256(underwriting_json.encode()).hexdigest(),
                }
            )

            # 3. Audit trail for policy
            policy_events = self.audit.get_events_for_entity("policy", policy_id)
            audit_json = json.dumps(
                [
                    {
                        "sequence": e.sequence_number,
                        "type": e.event_type,
                        "action": e.action,
                        "timestamp": e.event_timestamp.isoformat(),
                        "payload": e.payload_json,
                    }
                    for e in policy_events
                ],
                indent=2,
            )
            zip_file.writestr("03_audit_trail.json", audit_json)
            files.append(
                {
                    "name": "03_audit_trail.json",
                    "type": "application/json",
                    "hash": hashlib.sha256(audit_json.encode()).hexdigest(),
                }
            )

            # 4. Related risk runs (if requested)
            if include_risk_runs and policy.risk_run_id:
                risk_run = (
                    self.db.query(ModulesRiskRun)
                    .filter(ModulesRiskRun.id == policy.risk_run_id)
                    .first()
                )

                if risk_run:
                    risk_run_data = {
                        "risk_run_id": str(risk_run.id),
                        "created_at": risk_run.created_at.isoformat() if risk_run.created_at else None,
                        "status": risk_run.status.value if hasattr(risk_run.status, "value") else str(risk_run.status),
                        "result": risk_run.result_json or {},
                        "result_hash": risk_run.result_hash,
                        "model_version_id": str(risk_run.model_version_id) if risk_run.model_version_id else None,
                    }
                    # Extract common fields from result_json
                    if risk_run.result_json:
                        result = risk_run.result_json
                        risk_run_data["overall_risk_score"] = result.get("overall_risk_score")
                        risk_run_data["expected_loss_percentage"] = result.get("expected_loss_pct") or result.get("expected_loss_percentage")
                        risk_run_data["var_95"] = result.get("var_95")
                        risk_run_data["var_99"] = result.get("var_99")

                    risk_runs_json = json.dumps([risk_run_data], indent=2, default=str)
                    zip_file.writestr("04_risk_runs.json", risk_runs_json)
                    files.append(
                        {
                            "name": "04_risk_runs.json",
                            "type": "application/json",
                            "hash": hashlib.sha256(risk_runs_json.encode()).hexdigest(),
                        }
                    )

            # 5. Related claims (if requested)
            if include_claims:
                claims = self.db.query(Claim).filter(Claim.policy_id == policy_id).all()

                claims_data = []
                for claim in claims:
                    # Extract loss info from fnol_json
                    fnol = claim.fnol_json or {}
                    claims_data.append(
                        {
                            "claim_id": str(claim.id),
                            "claim_number": claim.claim_number,
                            "status": claim.status.value if hasattr(claim.status, "value") else str(claim.status),
                            "filed_at": claim.created_at.isoformat() if claim.created_at else None,
                            "fnol": fnol,
                            "decision": claim.decision,
                            "decision_reason": claim.decision_reason,
                            "decision_at": claim.decision_at.isoformat() if claim.decision_at else None,
                            "decision_by": str(claim.decision_by_user_id) if claim.decision_by_user_id else None,
                            "approved_amount_cents": claim.approved_amount_cents,
                            "approved_currency": claim.approved_currency,
                            "adjudication": claim.adjudication_json or {},
                        }
                    )

                claims_json = json.dumps(claims_data, indent=2, default=str)
                zip_file.writestr("05_claims.json", claims_json)
                files.append(
                    {
                        "name": "05_claims.json",
                        "type": "application/json",
                        "hash": hashlib.sha256(claims_json.encode()).hexdigest(),
                    }
                )

            # 6. Manifest
            manifest = {
                "pack_id": pack_id,
                "entity_type": "policy",
                "entity_id": policy_id,
                "policy_number": policy.policy_number,
                "created_at": datetime.utcnow().isoformat(),
                "created_by": created_by_user_id,
                "files": files,
                "export_version": "1.0",
            }
            manifest_json = json.dumps(manifest, indent=2, sort_keys=True)
            manifest_hash = hashlib.sha256(manifest_json.encode()).hexdigest()
            manifest["manifest_hash"] = manifest_hash

            zip_file.writestr("00_manifest.json", json.dumps(manifest, indent=2))

        # Get ZIP content and upload
        zip_content = zip_buffer.getvalue()
        total_size = len(zip_content)

        download_url = self.storage.upload_decision_pack(
            pack_id=pack_id, content=zip_content, content_type="application/zip"
        )

        # Audit
        self.audit.append_event(
            event_type="COMPLIANCE",
            action="POLICY_PACK_EXPORTED",
            entity_type="policy",
            entity_id=policy_id,
            actor_type="USER",
            actor_id=created_by_user_id,
            payload={
                "pack_id": pack_id,
                "file_count": len(files),
                "total_size_bytes": total_size,
                "manifest_hash": manifest_hash,
            },
        )

        return ExportedDecisionPack(
            pack_id=pack_id,
            entity_type="policy",
            entity_id=policy_id,
            files=files,
            total_size_bytes=total_size,
            created_at=datetime.utcnow(),
            created_by=created_by_user_id,
            manifest_hash=manifest_hash,
            is_verified=True,
            download_url=download_url,
            expires_at=datetime.utcnow() + timedelta(days=7),
        )

    async def export_claim(
        self,
        claim_id: str,
        include_evidence: bool = True,
        created_by_user_id: str = "system",
    ) -> ExportedDecisionPack:
        """
        Export complete decision package for a claim.

        Includes:
        - Claim details
        - Adjudication decision
        - Evidence bundle
        - Payout records
        """
        pack_id = f"claim_pack_{claim_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        claim = self.db.query(Claim).filter(Claim.id == claim_id).first()
        if not claim:
            raise ValueError(f"Claim {claim_id} not found")

        zip_buffer = io.BytesIO()
        files = []

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # 1. Claim summary
            fnol = claim.fnol_json or {}
            claim_summary = {
                "claim_id": str(claim.id),
                "claim_number": claim.claim_number,
                "policy_id": str(claim.policy_id),
                "status": claim.status.value if hasattr(claim.status, "value") else str(claim.status),
                "filed_at": claim.created_at.isoformat() if claim.created_at else None,
                "fnol": fnol,
                "decision": claim.decision,
                "decision_reason": claim.decision_reason,
                "decision_at": claim.decision_at.isoformat() if claim.decision_at else None,
                "decision_by": str(claim.decision_by_user_id) if claim.decision_by_user_id else None,
                "approved_amount_cents": claim.approved_amount_cents,
                "approved_currency": claim.approved_currency,
            }
            summary_json = json.dumps(claim_summary, indent=2, default=str)
            zip_file.writestr("01_claim_summary.json", summary_json)
            files.append(
                {
                    "name": "01_claim_summary.json",
                    "type": "application/json",
                    "hash": hashlib.sha256(summary_json.encode()).hexdigest(),
                }
            )

            # 2. FNOL (First Notice of Loss)
            fnol_json = json.dumps(fnol, indent=2, default=str)
            zip_file.writestr("02_fnol.json", fnol_json)
            files.append(
                {
                    "name": "02_fnol.json",
                    "type": "application/json",
                    "hash": hashlib.sha256(fnol_json.encode()).hexdigest(),
                }
            )

            # 3. Adjudication details
            adjudication = {
                "decision": claim.decision,
                "reason": claim.decision_reason,
                "adjudicated_by": str(claim.decision_by_user_id) if claim.decision_by_user_id else None,
                "adjudicated_at": claim.decision_at.isoformat() if claim.decision_at else None,
                "calculation_details": claim.adjudication_json or {},
            }
            adj_json = json.dumps(adjudication, indent=2, default=str)
            zip_file.writestr("03_adjudication.json", adj_json)
            files.append(
                {
                    "name": "03_adjudication.json",
                    "type": "application/json",
                    "hash": hashlib.sha256(adj_json.encode()).hexdigest(),
                }
            )

            # 4. Audit trail
            claim_events = self.audit.get_events_for_entity("claim", claim_id)
            audit_json = json.dumps(
                [
                    {
                        "sequence": e.sequence_number,
                        "type": e.event_type,
                        "action": e.action,
                        "timestamp": e.event_timestamp.isoformat(),
                        "payload": e.payload_json,
                    }
                    for e in claim_events
                ],
                indent=2,
            )
            zip_file.writestr("04_audit_trail.json", audit_json)
            files.append(
                {
                    "name": "04_audit_trail.json",
                    "type": "application/json",
                    "hash": hashlib.sha256(audit_json.encode()).hexdigest(),
                }
            )

            # 5. Evidence (if requested)
            if include_evidence and claim.evidence_bundle_id:
                try:
                    evidence_verification = self.evidence.verify_bundle(
                        str(claim.evidence_bundle_id)
                    )
                    custody_history = self.evidence.get_custody_history(
                        str(claim.evidence_bundle_id)
                    )

                    evidence_data = {
                        "bundle_id": str(claim.evidence_bundle_id),
                        "verification": evidence_verification,
                        "custody_history": custody_history,
                    }
                    evidence_json = json.dumps(evidence_data, indent=2, default=str)
                    zip_file.writestr("05_evidence.json", evidence_json)
                    files.append(
                        {
                            "name": "05_evidence.json",
                            "type": "application/json",
                            "hash": hashlib.sha256(evidence_json.encode()).hexdigest(),
                        }
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to include evidence: {e}")

            # 6. Manifest
            manifest = {
                "pack_id": pack_id,
                "entity_type": "claim",
                "entity_id": claim_id,
                "claim_number": claim.claim_number,
                "created_at": datetime.utcnow().isoformat(),
                "created_by": created_by_user_id,
                "files": files,
                "export_version": "1.0",
            }
            manifest_json = json.dumps(manifest, indent=2, sort_keys=True)
            manifest_hash = hashlib.sha256(manifest_json.encode()).hexdigest()
            manifest["manifest_hash"] = manifest_hash

            zip_file.writestr("00_manifest.json", json.dumps(manifest, indent=2))

        # Upload
        zip_content = zip_buffer.getvalue()
        total_size = len(zip_content)

        download_url = self.storage.upload_decision_pack(
            pack_id=pack_id, content=zip_content, content_type="application/zip"
        )

        # Audit
        self.audit.append_event(
            event_type="COMPLIANCE",
            action="CLAIM_PACK_EXPORTED",
            entity_type="claim",
            entity_id=claim_id,
            actor_type="USER",
            actor_id=created_by_user_id,
            payload={
                "pack_id": pack_id,
                "file_count": len(files),
                "manifest_hash": manifest_hash,
            },
        )

        return ExportedDecisionPack(
            pack_id=pack_id,
            entity_type="claim",
            entity_id=claim_id,
            files=files,
            total_size_bytes=total_size,
            created_at=datetime.utcnow(),
            created_by=created_by_user_id,
            manifest_hash=manifest_hash,
            is_verified=True,
            download_url=download_url,
            expires_at=datetime.utcnow() + timedelta(days=7),
        )

    def _create_decision_summary(self, package: DecisionPackage) -> Dict[str, Any]:
        """Create human-readable decision summary."""
        return {
            "summary": {
                "risk_run_id": package.risk_run_id,
                "assessed_at": package.risk_run_timestamp.isoformat(),
                "overall_risk_score": package.result.get("overall_risk_score"),
                "expected_loss_percentage": package.result.get("expected_loss_percentage"),
                "var_95": package.result.get("var_95"),
                "var_99": package.result.get("var_99"),
            },
            "inputs_summary": {
                "origin": package.inputs.get("origin_port") or package.inputs.get("origin"),
                "destination": package.inputs.get("destination_port") or package.inputs.get("destination"),
                "cargo_type": package.inputs.get("cargo_type") or package.inputs.get("cargo"),
                "cargo_value": package.inputs.get("cargo_value_usd") or package.inputs.get("cargo_value"),
                "carrier": package.inputs.get("carrier_code") or package.inputs.get("carrier"),
            },
            "model": {
                "version_id": package.model_version_id,
                "version_name": package.model_version_name,
                "model_hash": package.model_hash,
            },
            "data_quality": package.data_quality,
            "verification": {
                "input_hash": package.input_hash,
                "result_hash": package.result_hash,
                "package_hash": package.package_hash,
            },
            "audit_event_count": len(package.audit_events),
        }


def create_decision_pack_export_service(
    db: Session,
    audit: ImmutableAuditLedger,
    replay_system: DecisionReplaySystem,
    evidence_service: ChainOfCustodyService,
    storage: Optional[DecisionPackStorage] = None,
) -> DecisionPackExportService:
    """
    Factory function to create DecisionPackExportService.

    Args:
        db: Database session
        audit: Immutable audit ledger
        replay_system: Decision replay system
        evidence_service: Chain of custody service
        storage: Optional storage implementation (defaults to LocalDecisionPackStorage using EvidenceStorage)

    Returns:
        DecisionPackExportService instance
    """
    if storage is None:
        from app.core.evidence.storage import LocalEvidenceStorage

        evidence_storage = LocalEvidenceStorage()
        storage = LocalDecisionPackStorage(evidence_storage)

    return DecisionPackExportService(
        db=db,
        audit=audit,
        replay_system=replay_system,
        evidence_service=evidence_service,
        storage=storage,
    )
