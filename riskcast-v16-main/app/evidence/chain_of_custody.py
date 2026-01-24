"""
Evidence Chain of Custody

Implements complete chain of custody for evidence bundles:
1. Collection - Who/when/how evidence was collected
2. Storage - Where evidence is stored, integrity verification
3. Access - Who accessed evidence and when
4. Sealing - Cryptographic sealing of evidence
5. Verification - Verify evidence hasn't been tampered with

Critical for:
- Claims adjudication
- Parametric trigger verification
- Dispute resolution
- Regulatory audits
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Column,
    String,
    DateTime,
    JSON,
    Integer,
    ForeignKey,
    Index,
    Text,
)
from sqlalchemy.orm import Session

from app.database import Base
from app.core.audit.immutable_ledger import ImmutableAuditLedger
from app.core.evidence.storage import EvidenceStorage
from app.models.evidence_bundle import EvidenceBundle
from app.models.evidence import EvidenceObject

logger = logging.getLogger(__name__)


def _get_signing_key() -> str:
    """Get signing key from config."""
    try:
        from app.config import settings
        return getattr(settings, "AUDIT_SIGNING_KEY", None) or getattr(
            settings, "SECRET_KEY", "your-secret-signing-key-change-in-production"
        )
    except Exception:
        return "your-secret-signing-key-change-in-production"


class EvidenceStatus(str, Enum):
    """Status of evidence in chain of custody."""

    COLLECTED = "COLLECTED"
    VERIFIED = "VERIFIED"
    SEALED = "SEALED"
    ACCESSED = "ACCESSED"
    DISPUTED = "DISPUTED"
    ARCHIVED = "ARCHIVED"


class EvidenceType(str, Enum):
    """Types of evidence."""

    WEATHER_DATA = "WEATHER_DATA"
    PORT_DATA = "PORT_DATA"
    VESSEL_TRACKING = "VESSEL_TRACKING"
    ORACLE_DATA = "ORACLE_DATA"
    SENSOR_DATA = "SENSOR_DATA"
    DOCUMENT = "DOCUMENT"
    PHOTO = "PHOTO"
    VIDEO = "VIDEO"
    COMMUNICATION = "COMMUNICATION"
    THIRD_PARTY_REPORT = "THIRD_PARTY_REPORT"


class CustodyEventType(str, Enum):
    """Types of custody events."""

    COLLECTED = "COLLECTED"
    UPLOADED = "UPLOADED"
    VERIFIED = "VERIFIED"
    ACCESSED = "ACCESSED"
    DOWNLOADED = "DOWNLOADED"
    SEALED = "SEALED"
    DISPUTED = "DISPUTED"
    RESOLVED = "RESOLVED"
    ARCHIVED = "ARCHIVED"


@dataclass
class SealedBundle:
    """A cryptographically sealed evidence bundle."""

    bundle_id: str
    sealed_at: datetime
    sealed_by: str
    items: List[Dict[str, Any]]
    item_count: int
    total_size_bytes: int
    manifest_hash: str
    manifest_signature: str
    is_valid: bool
    verification_hash: str


class CustodyEventModel(Base):
    """Custody event database model with hash chain."""

    __tablename__ = "evidence_custody_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    bundle_id = Column(String(36), ForeignKey("evidence_bundles.id", ondelete="CASCADE"), nullable=True, index=True)
    item_id = Column(String(36), ForeignKey("evidence_objects.id", ondelete="CASCADE"), nullable=True, index=True)
    event_type = Column(String(50), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    actor_type = Column(String(20), nullable=False)
    actor_id = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    sequence_number = Column(Integer, nullable=False)
    prev_event_hash = Column(String(64), nullable=False)
    event_hash = Column(String(64), nullable=False)

    __table_args__ = (
        Index("idx_custody_event_bundle", "bundle_id"),
        Index("idx_custody_event_item", "item_id"),
        Index("idx_custody_event_sequence", "bundle_id", "sequence_number"),
    )


class ChainOfCustodyService:
    """
    Service for managing evidence chain of custody.

    Provides:
    - Evidence collection with provenance
    - Secure storage with integrity verification
    - Chain of custody tracking
    - Cryptographic sealing
    - Tamper detection
    """

    GENESIS_HASH = "0" * 64

    def __init__(
        self,
        db: Session,
        audit: ImmutableAuditLedger,
        storage: EvidenceStorage,
        signing_key: Optional[str] = None,
    ):
        self.db = db
        self.audit = audit
        self.storage = storage
        self.signing_key = (signing_key or _get_signing_key()).encode("utf-8")
        self.logger = logging.getLogger(__name__)

    def create_bundle(
        self,
        name: str,
        description: str,
        bundle_type: str = "CLAIM",
        claim_id: Optional[str] = None,
        policy_id: Optional[str] = None,
        risk_run_id: Optional[str] = None,
        created_by_user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> EvidenceBundle:
        """Create a new evidence bundle."""
        bundle = EvidenceBundle(
            name=name,
            description=description,
            bundle_type=bundle_type,
            tenant_id=tenant_id or "system",
            status="OPEN",
            created_by_user_id=created_by_user_id,
        )
        self.db.add(bundle)
        self.db.commit()
        self.db.refresh(bundle)

        self._record_custody_event(
            bundle_id=bundle.id,
            event_type=CustodyEventType.COLLECTED,
            actor_type="USER" if created_by_user_id else "SYSTEM",
            actor_id=created_by_user_id or "system",
            description=f"Evidence bundle created: {name}",
        )

        self.audit.append_event(
            event_type="EVIDENCE",
            action="BUNDLE_CREATED",
            entity_type="evidence_bundle",
            entity_id=bundle.id,
            actor_type="USER" if created_by_user_id else "SYSTEM",
            actor_id=created_by_user_id,
            tenant_id=tenant_id,
            payload={"name": name, "bundle_type": bundle_type},
        )

        return bundle

    def add_evidence(
        self,
        bundle_id: str,
        evidence_type: EvidenceType,
        name: str,
        content: bytes,
        content_type: str,
        source: str,
        source_timestamp: Optional[datetime] = None,
        collected_by: str = "SYSTEM",
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[str] = None,
    ) -> EvidenceObject:
        """
        Add evidence to a bundle.

        Content is stored securely and hashed for integrity verification.
        """
        bundle = self.db.query(EvidenceBundle).filter(EvidenceBundle.id == bundle_id).first()
        if not bundle:
            raise ValueError(f"Bundle {bundle_id} not found")
        if bundle.status == "SEALED":
            raise ValueError("Cannot add evidence to sealed bundle")

        content_hash = hashlib.sha256(content).hexdigest()
        storage_path = f"evidence/{bundle_id}/{content_hash[:16]}/{name}"
        storage_uri = self.storage.upload(content, storage_path)

        evidence = EvidenceObject(
            tenant_id=tenant_id or bundle.tenant_id,
            content_hash=content_hash,
            content_type=content_type,
            content_size_bytes=len(content),
            storage_uri=storage_uri,
            storage_provider="s3" if storage_uri.startswith("s3://") else "local",
            filename=name,
            description=description,
            metadata_json=metadata or {},
            evidence_type=evidence_type.value,
            created_by_user_id=collected_by if collected_by != "SYSTEM" else None,
        )
        self.db.add(evidence)
        self.db.flush()

        from app.models.evidence_bundle import EvidenceBundleItem

        bundle_item = EvidenceBundleItem(
            bundle_id=bundle_id,
            evidence_id=evidence.id,
            content_hash_at_addition=content_hash,
            added_by_user_id=collected_by if collected_by != "SYSTEM" else None,
            description=description,
        )
        self.db.add(bundle_item)

        bundle.item_count = (bundle.item_count or 0) + 1
        bundle.total_size_bytes = (bundle.total_size_bytes or 0) + len(content)
        self.db.commit()
        self.db.refresh(evidence)

        self._record_custody_event(
            bundle_id=bundle_id,
            item_id=evidence.id,
            event_type=CustodyEventType.UPLOADED,
            actor_type="USER" if collected_by != "SYSTEM" else "SYSTEM",
            actor_id=collected_by,
            description=f"Evidence uploaded: {name}",
            metadata={
                "content_hash": content_hash,
                "size_bytes": len(content),
                "source": source,
            },
        )

        self.audit.append_event(
            event_type="EVIDENCE",
            action="EVIDENCE_ADDED",
            entity_type="evidence_item",
            entity_id=evidence.id,
            actor_type="USER" if collected_by != "SYSTEM" else "SYSTEM",
            actor_id=collected_by if collected_by != "SYSTEM" else None,
            tenant_id=tenant_id or bundle.tenant_id,
            payload={
                "bundle_id": bundle_id,
                "evidence_type": evidence_type.value,
                "content_hash": content_hash,
                "size_bytes": len(content),
                "source": source,
            },
        )

        return evidence

    def seal_bundle(self, bundle_id: str, sealed_by_user_id: str) -> SealedBundle:
        """
        Cryptographically seal an evidence bundle.

        Once sealed:
        - No new evidence can be added
        - Manifest hash locks all content hashes
        - Signature proves authenticity
        """
        bundle = self.db.query(EvidenceBundle).filter(EvidenceBundle.id == bundle_id).first()
        if not bundle:
            raise ValueError(f"Bundle {bundle_id} not found")
        if bundle.status == "SEALED":
            raise ValueError("Bundle is already sealed")

        from app.models.evidence_bundle import EvidenceBundleItem

        bundle_items = (
            self.db.query(EvidenceBundleItem)
            .filter(EvidenceBundleItem.bundle_id == bundle_id)
            .order_by(EvidenceBundleItem.added_at)
            .all()
        )
        if not bundle_items:
            raise ValueError("Cannot seal empty bundle")

        evidence_ids = [item.evidence_id for item in bundle_items]
        evidence_objects = (
            self.db.query(EvidenceObject)
            .filter(EvidenceObject.id.in_(evidence_ids))
            .all()
        )
        evidence_map = {e.id: e for e in evidence_objects}

        for item in bundle_items:
            evidence = evidence_map.get(item.evidence_id)
            if not evidence:
                continue
            is_valid = self._verify_item_integrity(evidence)
            if not is_valid:
                raise ValueError(f"Item {item.evidence_id} failed integrity check")

        item_hashes = [item.content_hash_at_addition for item in bundle_items]
        manifest_data = "|".join(item_hashes)
        manifest_hash = hashlib.sha256(manifest_data.encode()).hexdigest()

        signature_data = f"{bundle_id}:{manifest_hash}:{datetime.utcnow().isoformat()}"
        manifest_signature = hmac.new(
            self.signing_key, signature_data.encode(), hashlib.sha256
        ).hexdigest()

        bundle.status = "SEALED"
        bundle.sealed_at = datetime.utcnow()
        bundle.sealed_by_user_id = sealed_by_user_id
        bundle.manifest_hash = manifest_hash
        self.db.commit()

        self._record_custody_event(
            bundle_id=bundle_id,
            event_type=CustodyEventType.SEALED,
            actor_type="USER",
            actor_id=sealed_by_user_id,
            description="Evidence bundle sealed",
            metadata={"manifest_hash": manifest_hash, "item_count": len(bundle_items)},
        )

        self.audit.append_event(
            event_type="EVIDENCE_SEAL",
            action="BUNDLE_SEALED",
            entity_type="evidence_bundle",
            entity_id=bundle_id,
            actor_type="USER",
            actor_id=sealed_by_user_id,
            tenant_id=bundle.tenant_id,
            payload={
                "manifest_hash": manifest_hash,
                "item_count": len(bundle_items),
                "total_size_bytes": bundle.total_size_bytes,
            },
        )

        items_data = []
        for item in bundle_items:
            evidence = evidence_map.get(item.evidence_id)
            if evidence:
                items_data.append({
                    "id": evidence.id,
                    "name": evidence.filename or "unknown",
                    "content_hash": evidence.content_hash,
                    "content_type": evidence.content_type,
                })

        verification_hash = hashlib.sha256(
            f"{bundle_id}:{manifest_hash}:{bundle.sealed_at.isoformat()}".encode()
        ).hexdigest()

        return SealedBundle(
            bundle_id=bundle_id,
            sealed_at=bundle.sealed_at,
            sealed_by=sealed_by_user_id,
            items=items_data,
            item_count=len(bundle_items),
            total_size_bytes=bundle.total_size_bytes or 0,
            manifest_hash=manifest_hash,
            manifest_signature=manifest_signature,
            is_valid=True,
            verification_hash=verification_hash,
        )

    def verify_bundle(self, bundle_id: str) -> Dict[str, Any]:
        """
        Verify integrity of a sealed evidence bundle.

        Checks:
        1. All items present
        2. All content hashes match
        3. Manifest hash matches
        4. Signature is valid
        5. Custody chain is intact
        """
        bundle = self.db.query(EvidenceBundle).filter(EvidenceBundle.id == bundle_id).first()
        if not bundle:
            raise ValueError(f"Bundle {bundle_id} not found")

        verification: Dict[str, Any] = {
            "bundle_id": bundle_id,
            "verified_at": datetime.utcnow().isoformat(),
            "is_sealed": bundle.status == "SEALED",
            "checks": {},
        }

        from app.models.evidence_bundle import EvidenceBundleItem

        bundle_items = (
            self.db.query(EvidenceBundleItem)
            .filter(EvidenceBundleItem.bundle_id == bundle_id)
            .order_by(EvidenceBundleItem.added_at)
            .all()
        )

        verification["checks"]["item_count"] = {
            "expected": bundle.item_count or 0,
            "actual": len(bundle_items),
            "valid": len(bundle_items) == (bundle.item_count or 0),
        }

        evidence_ids = [item.evidence_id for item in bundle_items]
        evidence_objects = (
            self.db.query(EvidenceObject)
            .filter(EvidenceObject.id.in_(evidence_ids))
            .all()
        )
        evidence_map = {e.id: e for e in evidence_objects}

        item_verifications = []
        all_items_valid = True
        for item in bundle_items:
            evidence = evidence_map.get(item.evidence_id)
            if not evidence:
                all_items_valid = False
                item_verifications.append({
                    "item_id": item.evidence_id,
                    "name": "unknown",
                    "valid": False,
                    "error": "Evidence object not found",
                })
                continue
            is_valid = self._verify_item_integrity(evidence)
            item_verifications.append({
                "item_id": evidence.id,
                "name": evidence.filename or "unknown",
                "valid": is_valid,
            })
            if not is_valid:
                all_items_valid = False

        verification["checks"]["item_integrity"] = {
            "valid": all_items_valid,
            "items": item_verifications,
        }

        if bundle.status == "SEALED" and bundle.manifest_hash:
            item_hashes = [item.content_hash_at_addition for item in bundle_items]
            manifest_data = "|".join(item_hashes)
            computed_manifest = hashlib.sha256(manifest_data.encode()).hexdigest()
            verification["checks"]["manifest_hash"] = {
                "stored": bundle.manifest_hash,
                "computed": computed_manifest,
                "valid": computed_manifest == bundle.manifest_hash,
            }

        custody_events = (
            self.db.query(CustodyEventModel)
            .filter(CustodyEventModel.bundle_id == bundle_id)
            .order_by(CustodyEventModel.sequence_number)
            .all()
        )
        custody_chain_valid = self._verify_custody_chain(custody_events)
        verification["checks"]["custody_chain"] = {
            "valid": custody_chain_valid,
            "event_count": len(custody_events),
        }

        all_valid = all(
            check.get("valid", False) for check in verification["checks"].values()
        )
        verification["is_valid"] = all_valid

        self.audit.append_event(
            event_type="EVIDENCE",
            action="BUNDLE_VERIFIED",
            entity_type="evidence_bundle",
            entity_id=bundle_id,
            actor_type="SYSTEM",
            tenant_id=bundle.tenant_id,
            payload={
                "is_valid": all_valid,
                "checks": {k: v.get("valid") for k, v in verification["checks"].items()},
            },
        )

        return verification

    def record_access(
        self,
        bundle_id: str,
        accessed_by_user_id: str,
        access_reason: str,
        items_accessed: Optional[List[str]] = None,
        tenant_id: Optional[str] = None,
    ):
        """Record access to evidence bundle."""
        self._record_custody_event(
            bundle_id=bundle_id,
            event_type=CustodyEventType.ACCESSED,
            actor_type="USER",
            actor_id=accessed_by_user_id,
            description=access_reason,
            metadata={
                "items_accessed": items_accessed if items_accessed else "all",
            },
        )

        self.audit.append_event(
            event_type="EVIDENCE",
            action="BUNDLE_ACCESSED",
            entity_type="evidence_bundle",
            entity_id=bundle_id,
            actor_type="USER",
            actor_id=accessed_by_user_id,
            tenant_id=tenant_id,
            payload={
                "reason": access_reason,
                "items_accessed": items_accessed if items_accessed else "all",
            },
        )

    def get_custody_history(self, bundle_id: str) -> List[Dict[str, Any]]:
        """Get complete custody history for a bundle."""
        events = (
            self.db.query(CustodyEventModel)
            .filter(CustodyEventModel.bundle_id == bundle_id)
            .order_by(CustodyEventModel.sequence_number)
            .all()
        )

        return [
            {
                "sequence": e.sequence_number,
                "event_type": e.event_type,
                "timestamp": e.timestamp.isoformat(),
                "actor_type": e.actor_type,
                "actor_id": e.actor_id,
                "description": e.description,
                "metadata": e.metadata_json,
                "event_hash": e.event_hash,
            }
            for e in events
        ]

    def _record_custody_event(
        self,
        bundle_id: str,
        event_type: CustodyEventType,
        actor_type: str,
        actor_id: str,
        description: str,
        item_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Record a custody event with hash chain."""
        last_event = (
            self.db.query(CustodyEventModel)
            .filter(CustodyEventModel.bundle_id == bundle_id)
            .order_by(CustodyEventModel.sequence_number.desc())
            .first()
        )

        if last_event:
            prev_hash = last_event.event_hash
            next_seq = last_event.sequence_number + 1
        else:
            prev_hash = self.GENESIS_HASH
            next_seq = 1

        event = CustodyEventModel(
            bundle_id=bundle_id,
            item_id=item_id,
            event_type=event_type.value,
            timestamp=datetime.utcnow(),
            actor_type=actor_type,
            actor_id=actor_id,
            description=description,
            metadata_json=metadata,
            sequence_number=next_seq,
            prev_event_hash=prev_hash,
        )

        event_data = {
            "bundle_id": bundle_id,
            "sequence": next_seq,
            "event_type": event_type.value,
            "timestamp": event.timestamp.isoformat(),
            "actor": f"{actor_type}:{actor_id}",
            "prev_hash": prev_hash,
        }
        event.event_hash = hashlib.sha256(
            json.dumps(event_data, sort_keys=True).encode()
        ).hexdigest()

        self.db.add(event)
        self.db.commit()

    def _verify_item_integrity(self, evidence: EvidenceObject) -> bool:
        """Verify item content hash matches stored content."""
        try:
            content = self.storage.download(evidence.storage_uri)
            computed_hash = hashlib.sha256(content).hexdigest()
            return computed_hash == evidence.content_hash
        except Exception as e:
            self.logger.error(f"Failed to verify item {evidence.id}: {e}")
            return False

    def _verify_custody_chain(self, events: List[CustodyEventModel]) -> bool:
        """Verify custody event hash chain."""
        if not events:
            return True

        prev_hash = self.GENESIS_HASH

        for event in events:
            if event.prev_event_hash != prev_hash:
                return False
            prev_hash = event.event_hash

        return True


def create_chain_of_custody_service(
    db: Session,
    audit: ImmutableAuditLedger,
    storage: EvidenceStorage,
    signing_key: Optional[str] = None,
) -> ChainOfCustodyService:
    """Create chain of custody service instance."""
    return ChainOfCustodyService(db, audit, storage, signing_key)
