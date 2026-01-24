"""
Evidence bundle management service.

Handles bundle lifecycle:
1. Create bundle (OPEN)
2. Add items
3. Link to entities
4. Seal bundle (OPEN -> SEALED)

Sealed bundles are immutable with verified manifest hash.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import hashlib
import json

from sqlalchemy.orm import Session
from sqlalchemy import func as sa_func

from app.models.evidence import EvidenceObject
from app.models.evidence_bundle import (
    EvidenceBundle,
    EvidenceBundleItem,
    EvidenceBundleLink
)
from app.schemas.evidence_bundle import (
    BundleCreateRequest,
    BundleItemAddRequest,
    BundleLinkRequest,
    BundleManifest
)
from app.core.audit_ledger.ledger import AuditLedger

import logging

logger = logging.getLogger(__name__)


class EvidenceBundleService:
    """Service for managing evidence bundles."""
    
    def __init__(self, db: Session, audit: Optional[AuditLedger] = None):
        """
        Initialize evidence bundle service.
        
        Args:
            db: Database session
            audit: Optional audit ledger for event logging
        """
        self.db = db
        self.audit = audit or AuditLedger(db)
    
    def create_bundle(
        self,
        tenant_id: str,
        request: BundleCreateRequest,
        created_by: str
    ) -> EvidenceBundle:
        """
        Create a new evidence bundle in OPEN status.
        
        OPEN bundles can have items added/removed.
        Must be sealed before linking to insurance decisions.
        
        Args:
            tenant_id: Tenant ID (UUID string)
            request: Bundle creation request
            created_by: User ID creating the bundle (UUID string)
            
        Returns:
            Created EvidenceBundle
        """
        bundle = EvidenceBundle(
            tenant_id=tenant_id,
            name=request.name,
            description=request.description,
            bundle_type=request.bundle_type.value,
            status='OPEN',
            retention_class=request.retention_class.value,
            created_by_user_id=created_by,
            created_at=datetime.utcnow()
        )
        
        self.db.add(bundle)
        self.db.commit()
        self.db.refresh(bundle)
        
        # Audit
        self.audit.append_event(
            tenant_id=tenant_id,
            event_type="EVIDENCE_BUNDLE",
            action="CREATED",
            entity_type="evidence_bundle",
            entity_id=bundle.id,
            actor_type="USER",
            actor_id=created_by,
            payload={
                "bundle_type": request.bundle_type.value,
                "retention_class": request.retention_class.value
            }
        )
        
        logger.info(f"Created evidence bundle: {bundle.id} (type={request.bundle_type.value})")
        
        return bundle
    
    def add_item(
        self,
        bundle_id: str,
        request: BundleItemAddRequest,
        added_by: str
    ) -> EvidenceBundleItem:
        """
        Add an evidence object to a bundle.
        
        Args:
            bundle_id: Bundle ID (UUID string)
            request: Item add request
            added_by: User ID adding the item (UUID string)
            
        Returns:
            Created EvidenceBundleItem
            
        Raises:
            BundleSealedError: If bundle is already sealed
            EvidenceNotFoundError: If evidence doesn't exist
            DuplicateItemError: If evidence already in bundle
        """
        bundle = self._get_bundle(bundle_id)
        
        if bundle.status != 'OPEN':
            raise BundleSealedError(f"Cannot add items to {bundle.status} bundle")
        
        # Get evidence and verify it exists
        evidence = self.db.query(EvidenceObject).filter(
            EvidenceObject.id == request.evidence_id,
            EvidenceObject.tenant_id == bundle.tenant_id,
            EvidenceObject.deleted_at.is_(None)  # Only non-deleted
        ).first()
        
        if not evidence:
            raise EvidenceNotFoundError(f"Evidence {request.evidence_id} not found")
        
        # Check not already in bundle
        existing = self.db.query(EvidenceBundleItem).filter(
            EvidenceBundleItem.bundle_id == bundle_id,
            EvidenceBundleItem.evidence_id == request.evidence_id
        ).first()
        
        if existing:
            raise DuplicateItemError(f"Evidence {request.evidence_id} already in bundle")
        
        # Get next sequence number
        max_seq = self.db.query(
            sa_func.max(EvidenceBundleItem.sequence)
        ).filter(
            EvidenceBundleItem.bundle_id == bundle_id
        ).scalar() or 0
        
        # Create item
        item = EvidenceBundleItem(
            bundle_id=bundle_id,
            evidence_id=request.evidence_id,
            sequence=max_seq + 1,
            role=request.role.value if hasattr(request.role, 'value') else request.role,
            description=request.description,
            content_hash_at_addition=evidence.content_hash,
            added_at=datetime.utcnow(),
            added_by_user_id=added_by
        )
        
        self.db.add(item)
        
        # Update PII tracking
        if evidence.is_pii:
            bundle.contains_pii = True
            if bundle.pii_categories is None:
                bundle.pii_categories = []
            # Merge PII categories if evidence has metadata
            if evidence.metadata_json and 'pii_categories' in evidence.metadata_json:
                existing_categories = set(bundle.pii_categories or [])
                new_categories = set(evidence.metadata_json.get('pii_categories', []))
                bundle.pii_categories = list(existing_categories | new_categories)
        
        self.db.commit()
        self.db.refresh(item)
        
        # Audit
        self.audit.append_event(
            tenant_id=bundle.tenant_id,
            event_type="EVIDENCE_BUNDLE",
            action="ITEM_ADDED",
            entity_type="evidence_bundle",
            entity_id=bundle_id,
            actor_type="USER",
            actor_id=added_by,
            payload={
                "evidence_id": request.evidence_id,
                "content_hash": evidence.content_hash,
                "role": request.role.value if hasattr(request.role, 'value') else request.role
            }
        )
        
        logger.info(f"Added item {request.evidence_id} to bundle {bundle_id}")
        
        return item
    
    def remove_item(
        self,
        bundle_id: str,
        evidence_id: str,
        removed_by: str
    ) -> None:
        """
        Remove an item from an OPEN bundle.
        
        Args:
            bundle_id: Bundle ID (UUID string)
            evidence_id: Evidence ID to remove (UUID string)
            removed_by: User ID removing the item (UUID string)
            
        Raises:
            BundleSealedError: If bundle is sealed
            ItemNotFoundError: If item not in bundle
        """
        bundle = self._get_bundle(bundle_id)
        
        if bundle.status != 'OPEN':
            raise BundleSealedError(f"Cannot remove items from {bundle.status} bundle")
        
        item = self.db.query(EvidenceBundleItem).filter(
            EvidenceBundleItem.bundle_id == bundle_id,
            EvidenceBundleItem.evidence_id == evidence_id
        ).first()
        
        if not item:
            raise ItemNotFoundError(f"Evidence {evidence_id} not in bundle")
        
        self.db.delete(item)
        self.db.commit()
        
        # Audit
        self.audit.append_event(
            tenant_id=bundle.tenant_id,
            event_type="EVIDENCE_BUNDLE",
            action="ITEM_REMOVED",
            entity_type="evidence_bundle",
            entity_id=bundle_id,
            actor_type="USER",
            actor_id=removed_by,
            payload={"evidence_id": evidence_id}
        )
        
        logger.info(f"Removed item {evidence_id} from bundle {bundle_id}")
    
    def seal_bundle(
        self,
        bundle_id: str,
        sealed_by: str
    ) -> EvidenceBundle:
        """
        Seal a bundle, making it immutable.
        
        Computes and stores the manifest hash.
        After sealing, no items can be added or removed.
        
        Args:
            bundle_id: Bundle ID (UUID string)
            sealed_by: User ID sealing the bundle (UUID string)
            
        Returns:
            Sealed EvidenceBundle
            
        Raises:
            BundleSealedError: If bundle already sealed
            EmptyBundleError: If bundle has no items
        """
        bundle = self._get_bundle(bundle_id)
        
        if bundle.status != 'OPEN':
            raise BundleSealedError(f"Bundle already {bundle.status}")
        
        # Get all items
        items = self.db.query(EvidenceBundleItem).filter(
            EvidenceBundleItem.bundle_id == bundle_id
        ).order_by(EvidenceBundleItem.sequence).all()
        
        if not items:
            raise EmptyBundleError("Cannot seal empty bundle")
        
        # Build manifest
        manifest = self._build_manifest(items)
        manifest_hash = self._compute_manifest_hash(manifest)
        
        # Update bundle
        bundle.status = 'SEALED'
        bundle.manifest_json = manifest
        bundle.manifest_hash = manifest_hash
        bundle.sealed_at = datetime.utcnow()
        bundle.sealed_by_user_id = sealed_by
        
        self.db.commit()
        self.db.refresh(bundle)
        
        # Audit
        self.audit.append_event(
            tenant_id=bundle.tenant_id,
            event_type="EVIDENCE_BUNDLE",
            action="SEALED",
            entity_type="evidence_bundle",
            entity_id=bundle_id,
            actor_type="USER",
            actor_id=sealed_by,
            payload={
                "manifest_hash": manifest_hash,
                "item_count": len(items)
            }
        )
        
        logger.info(f"Sealed bundle {bundle_id} with {len(items)} items, hash={manifest_hash[:16]}...")
        
        return bundle
    
    def link_to_entity(
        self,
        bundle_id: str,
        request: BundleLinkRequest,
        linked_by: str
    ) -> EvidenceBundleLink:
        """
        Link a sealed bundle to a domain entity.
        
        For insurance decisions, bundles must be sealed before linking.
        
        Args:
            bundle_id: Bundle ID (UUID string)
            request: Link request
            linked_by: User ID creating the link (UUID string)
            
        Returns:
            Created EvidenceBundleLink
            
        Raises:
            BundleNotSealedError: If bundle must be sealed but isn't
            DuplicateLinkError: If bundle already linked to entity
        """
        bundle = self._get_bundle(bundle_id)
        
        # For certain link types, require sealed bundle
        insurance_entity_types = ['policy', 'claim', 'trigger_event', 'quote', 'underwriting_decision']
        if request.entity_type in insurance_entity_types and bundle.status != 'SEALED':
            raise BundleNotSealedError(
                f"Bundle must be sealed before linking to {request.entity_type}"
            )
        
        # Check not already linked
        existing = self.db.query(EvidenceBundleLink).filter(
            EvidenceBundleLink.bundle_id == bundle_id,
            EvidenceBundleLink.entity_type == request.entity_type,
            EvidenceBundleLink.entity_id == request.entity_id
        ).first()
        
        if existing:
            raise DuplicateLinkError("Bundle already linked to this entity")
        
        link = EvidenceBundleLink(
            bundle_id=bundle_id,
            entity_type=request.entity_type,
            entity_id=request.entity_id,
            link_type=request.link_type.value if hasattr(request.link_type, 'value') else request.link_type,
            created_at=datetime.utcnow()
        )
        
        self.db.add(link)
        self.db.commit()
        self.db.refresh(link)
        
        # Audit
        self.audit.append_event(
            tenant_id=bundle.tenant_id,
            event_type="EVIDENCE_BUNDLE",
            action="LINKED",
            entity_type="evidence_bundle",
            entity_id=bundle_id,
            actor_type="USER",
            actor_id=linked_by,
            payload={
                "target_entity_type": request.entity_type,
                "target_entity_id": request.entity_id,
                "link_type": request.link_type.value if hasattr(request.link_type, 'value') else request.link_type
            }
        )
        
        logger.info(f"Linked bundle {bundle_id} to {request.entity_type}:{request.entity_id}")
        
        return link
    
    def verify_bundle_integrity(self, bundle_id: str) -> Dict[str, Any]:
        """
        Verify integrity of a sealed bundle.
        
        Checks:
        1. Manifest hash matches stored hash
        2. Each item's current hash matches hash at addition
        
        Args:
            bundle_id: Bundle ID (UUID string)
            
        Returns:
            Verification result dictionary with details
        """
        bundle = self._get_bundle(bundle_id)
        
        if bundle.status != 'SEALED':
            return {
                "valid": False,
                "error": "Bundle not sealed",
                "details": None
            }
        
        # Get items
        items = self.db.query(EvidenceBundleItem).filter(
            EvidenceBundleItem.bundle_id == bundle_id
        ).order_by(EvidenceBundleItem.sequence).all()
        
        # Rebuild manifest and check hash
        manifest = self._build_manifest(items)
        computed_hash = self._compute_manifest_hash(manifest)
        
        if computed_hash != bundle.manifest_hash:
            return {
                "valid": False,
                "error": "Manifest hash mismatch",
                "expected": bundle.manifest_hash,
                "computed": computed_hash
            }
        
        # Check each item's content hash
        mismatches = []
        for item in items:
            evidence = self.db.query(EvidenceObject).filter(
                EvidenceObject.id == item.evidence_id,
                EvidenceObject.deleted_at.is_(None)
            ).first()
            
            if evidence and evidence.content_hash != item.content_hash_at_addition:
                mismatches.append({
                    "evidence_id": item.evidence_id,
                    "expected_hash": item.content_hash_at_addition,
                    "current_hash": evidence.content_hash
                })
        
        if mismatches:
            return {
                "valid": False,
                "error": "Content hash mismatches",
                "mismatches": mismatches
            }
        
        return {
            "valid": True,
            "manifest_hash": bundle.manifest_hash,
            "item_count": len(items),
            "verified_at": datetime.utcnow().isoformat()
        }
    
    def get_bundles_for_entity(
        self,
        entity_type: str,
        entity_id: str
    ) -> List[EvidenceBundle]:
        """
        Get all bundles linked to an entity.
        
        Args:
            entity_type: Entity type
            entity_id: Entity ID (UUID string)
            
        Returns:
            List of EvidenceBundle instances
        """
        links = self.db.query(EvidenceBundleLink).filter(
            EvidenceBundleLink.entity_type == entity_type,
            EvidenceBundleLink.entity_id == entity_id
        ).all()
        
        bundle_ids = [link.bundle_id for link in links]
        
        if not bundle_ids:
            return []
        
        return self.db.query(EvidenceBundle).filter(
            EvidenceBundle.id.in_(bundle_ids)
        ).all()
    
    def set_legal_hold(
        self,
        bundle_id: str,
        reason: str,
        set_by: str
    ) -> EvidenceBundle:
        """
        Place a legal hold on a bundle, preventing expiration.
        
        Args:
            bundle_id: Bundle ID (UUID string)
            reason: Reason for legal hold
            set_by: User ID setting the hold (UUID string)
            
        Returns:
            Updated EvidenceBundle
        """
        bundle = self._get_bundle(bundle_id)
        
        bundle.legal_hold = True
        bundle.legal_hold_reason = reason
        bundle.retention_class = 'LEGAL_HOLD'
        bundle.expires_at = None
        
        self.db.commit()
        self.db.refresh(bundle)
        
        # Audit
        self.audit.append_event(
            tenant_id=bundle.tenant_id,
            event_type="EVIDENCE_BUNDLE",
            action="LEGAL_HOLD_SET",
            entity_type="evidence_bundle",
            entity_id=bundle_id,
            actor_type="USER",
            actor_id=set_by,
            payload={"reason": reason}
        )
        
        logger.info(f"Set legal hold on bundle {bundle_id}: {reason}")
        
        return bundle
    
    def _get_bundle(self, bundle_id: str) -> EvidenceBundle:
        """
        Get bundle by ID or raise error.
        
        Args:
            bundle_id: Bundle ID (UUID string)
            
        Returns:
            EvidenceBundle instance
            
        Raises:
            BundleNotFoundError: If bundle not found
        """
        bundle = self.db.query(EvidenceBundle).filter(
            EvidenceBundle.id == bundle_id
        ).first()
        
        if not bundle:
            raise BundleNotFoundError(f"Bundle {bundle_id} not found")
        
        return bundle
    
    def _build_manifest(self, items: List[EvidenceBundleItem]) -> Dict[str, Any]:
        """
        Build manifest dictionary from items.
        
        Args:
            items: List of EvidenceBundleItem instances
            
        Returns:
            Manifest dictionary
        """
        total_size = 0
        item_list = []
        
        for item in items:
            evidence = self.db.query(EvidenceObject).filter(
                EvidenceObject.id == item.evidence_id,
                EvidenceObject.deleted_at.is_(None)
            ).first()
            
            item_data = {
                "evidence_id": item.evidence_id,
                "content_hash": item.content_hash_at_addition,
                "sequence": item.sequence,
                "role": item.role,
                "added_at": item.added_at.isoformat()
            }
            
            if evidence:
                item_data.update({
                    "content_type": evidence.content_type,
                    "filename": evidence.filename,
                    "size_bytes": evidence.content_size_bytes or 0
                })
                if evidence.content_size_bytes:
                    total_size += evidence.content_size_bytes
            else:
                item_data.update({
                    "content_type": None,
                    "filename": None,
                    "size_bytes": 0
                })
            
            item_list.append(item_data)
        
        return {
            "items": item_list,
            "item_count": len(items),
            "total_size_bytes": total_size,
            "sealed_at": datetime.utcnow().isoformat()
        }
    
    def _compute_manifest_hash(self, manifest: Dict[str, Any]) -> str:
        """
        Compute SHA256 hash of manifest.
        
        Uses canonical JSON serialization for deterministic hashing.
        
        Args:
            manifest: Manifest dictionary
            
        Returns:
            SHA256 hash as hex string (64 characters)
        """
        canonical = json.dumps(manifest, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical.encode()).hexdigest()


# Exception classes
class BundleNotFoundError(Exception):
    """Bundle not found"""
    pass


class BundleSealedError(Exception):
    """Bundle is sealed and cannot be modified"""
    pass


class BundleNotSealedError(Exception):
    """Bundle must be sealed for this operation"""
    pass


class EmptyBundleError(Exception):
    """Bundle has no items"""
    pass


class EvidenceNotFoundError(Exception):
    """Evidence object not found"""
    pass


class DuplicateItemError(Exception):
    """Evidence already in bundle"""
    pass


class DuplicateLinkError(Exception):
    """Bundle already linked to entity"""
    pass


class ItemNotFoundError(Exception):
    """Item not found in bundle"""
    pass
