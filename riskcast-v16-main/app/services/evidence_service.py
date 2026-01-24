"""
Evidence Service
Business logic for evidence upload, linking, and management.
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.evidence import EvidenceObject
from app.models.evidence_link import EvidenceLink
from app.core.audit_ledger.ledger import AuditLedger
from app.core.evidence.storage import EvidenceStorage, LocalEvidenceStorage
from app.shared.exceptions import NotFoundError

import logging

logger = logging.getLogger(__name__)


class EvidenceService:
    """Service for evidence management and linking."""
    
    def __init__(
        self,
        db: Session,
        storage: Optional[EvidenceStorage] = None,
        audit: Optional[AuditLedger] = None
    ):
        """
        Initialize service.
        
        Args:
            db: Database session
            storage: Storage backend (defaults to LocalEvidenceStorage)
            audit: Optional audit ledger for event logging
        """
        self.db = db
        self.storage = storage or LocalEvidenceStorage()
        self.audit = audit or AuditLedger(db)
    
    def create_evidence(
        self,
        tenant_id: str,
        content: bytes,
        content_type: str,
        filename: Optional[str] = None,
        evidence_type: str = "DOCUMENT",
        metadata: Optional[Dict[str, Any]] = None,
        created_by_user_id: Optional[str] = None,
        description: Optional[str] = None,
        is_pii: bool = False,
        retention_class: str = "STANDARD"
    ) -> EvidenceObject:
        """
        Create evidence object from content.
        
        Steps:
        1. Compute content_hash (SHA256)
        2. Check for existing evidence with same hash (deduplication)
        3. Upload to storage
        4. Create database record
        5. Emit audit event
        
        Args:
            tenant_id: Tenant ID
            content: Content bytes
            content_type: MIME type
            filename: Original filename (optional)
            evidence_type: Type of evidence (DOCUMENT, IMAGE, DATA_EXPORT, etc.)
            metadata: Additional metadata (optional)
            created_by_user_id: User ID who created this (optional)
            description: Description (optional)
            is_pii: Whether content contains PII
            retention_class: Retention classification
            
        Returns:
            EvidenceObject instance
        """
        # 1. Compute content_hash
        content_hash = hashlib.sha256(content).hexdigest()
        content_size_bytes = len(content)
        
        # 2. Check for existing (dedup by hash)
        existing = self.db.query(EvidenceObject).filter(
            and_(
                EvidenceObject.tenant_id == tenant_id,
                EvidenceObject.content_hash == content_hash,
                EvidenceObject.deleted_at.is_(None)  # Only non-deleted
            )
        ).first()
        
        if existing:
            logger.info(f"Found existing evidence with hash {content_hash[:8]}... (deduplication)")
            # Emit audit event for reuse
            self.audit.append_event(
                tenant_id=tenant_id,
                event_type="EVIDENCE",
                action="REUSED",
                entity_type="evidence_object",
                entity_id=existing.id,
                actor_type="SYSTEM",
                actor_id=created_by_user_id,
                payload={
                    "content_hash": content_hash,
                    "content_type": content_type,
                    "filename": filename,
                    "evidence_type": evidence_type
                }
            )
            return existing
        
        # 3. Upload to storage
        # Generate storage path: evidence/{tenant_id}/{year}/{month}/{hash[:2]}/{hash}.ext
        now = datetime.utcnow()
        file_ext = Path(filename).suffix if filename else ""
        storage_path = (
            f"evidence/{tenant_id}/{now.year}/{now.month:02d}/"
            f"{content_hash[:2]}/{content_hash}{file_ext}"
        )
        
        storage_uri = self.storage.upload(content, storage_path)
        
        # Determine storage provider from URI
        if storage_uri.startswith("s3://"):
            storage_provider = "s3"
        elif storage_uri.startswith("file://"):
            storage_provider = "local"
        else:
            storage_provider = "unknown"
        
        # 4. Create record
        evidence = EvidenceObject(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            content_hash=content_hash,
            content_type=content_type,
            content_size_bytes=content_size_bytes,
            storage_uri=storage_uri,
            storage_provider=storage_provider,
            filename=filename,
            description=description,
            metadata_json=metadata or {},
            evidence_type=evidence_type,
            is_pii=is_pii,
            retention_class=retention_class,
            created_by_user_id=created_by_user_id
        )
        
        self.db.add(evidence)
        self.db.flush()  # Flush to get ID
        
        # 5. Emit audit event
        self.audit.append_event(
            tenant_id=tenant_id,
            event_type="EVIDENCE",
            action="CREATED",
            entity_type="evidence_object",
            entity_id=evidence.id,
            actor_type="USER" if created_by_user_id else "SYSTEM",
            actor_id=created_by_user_id,
            payload={
                "content_hash": content_hash,
                "content_type": content_type,
                "content_size_bytes": content_size_bytes,
                "storage_uri": storage_uri,
                "storage_provider": storage_provider,
                "filename": filename,
                "evidence_type": evidence_type,
                "is_pii": is_pii
            }
        )
        
        self.db.commit()
        
        return evidence
    
    def link_evidence(
        self,
        tenant_id: str,
        evidence_id: str,
        entity_type: str,
        entity_id: str,
        link_type: str = "ATTACHMENT",
        description: Optional[str] = None,
        created_by_user_id: Optional[str] = None
    ) -> EvidenceLink:
        """
        Link evidence to an entity.
        
        Args:
            tenant_id: Tenant ID
            evidence_id: Evidence object ID
            entity_type: Type of entity (risk_assessment, risk_run, policy, claim, trigger_event)
            entity_id: ID of the entity
            link_type: Type of link (ATTACHMENT, SOURCE_DATA, DECISION_BASIS, OUTPUT)
            description: Description of the link (optional)
            created_by_user_id: User ID who created this link (optional)
            
        Returns:
            EvidenceLink instance
            
        Raises:
            NotFoundError: If evidence not found
            IntegrityError: If link already exists (unique constraint)
        """
        # Verify evidence exists
        evidence = self.db.query(EvidenceObject).filter(
            and_(
                EvidenceObject.id == evidence_id,
                EvidenceObject.tenant_id == tenant_id,
                EvidenceObject.deleted_at.is_(None)
            )
        ).first()
        
        if not evidence:
            raise NotFoundError(f"Evidence {evidence_id} not found")
        
        # Create link
        link = EvidenceLink(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            evidence_id=evidence_id,
            entity_type=entity_type,
            entity_id=entity_id,
            link_type=link_type,
            description=description
        )
        
        self.db.add(link)
        self.db.flush()  # Flush to check for unique constraint violation
        
        # Emit audit event
        self.audit.append_event(
            tenant_id=tenant_id,
            event_type="EVIDENCE_LINK",
            action="CREATED",
            entity_type=entity_type,
            entity_id=entity_id,
            actor_type="USER" if created_by_user_id else "SYSTEM",
            actor_id=created_by_user_id,
            payload={
                "evidence_id": evidence_id,
                "link_type": link_type,
                "description": description
            }
        )
        
        self.db.commit()
        
        return link
    
    def get_evidence_for_entity(
        self,
        tenant_id: str,
        entity_type: str,
        entity_id: str
    ) -> List[EvidenceObject]:
        """
        Get all evidence linked to an entity.
        
        Args:
            tenant_id: Tenant ID
            entity_type: Type of entity
            entity_id: ID of the entity
            
        Returns:
            List of EvidenceObject instances
        """
        links = self.db.query(EvidenceLink).filter(
            and_(
                EvidenceLink.tenant_id == tenant_id,
                EvidenceLink.entity_type == entity_type,
                EvidenceLink.entity_id == entity_id
            )
        ).all()
        
        evidence_ids = [link.evidence_id for link in links]
        
        if not evidence_ids:
            return []
        
        evidence = self.db.query(EvidenceObject).filter(
            and_(
                EvidenceObject.id.in_(evidence_ids),
                EvidenceObject.tenant_id == tenant_id,
                EvidenceObject.deleted_at.is_(None)
            )
        ).all()
        
        return evidence
    
    def download_evidence(
        self,
        tenant_id: str,
        evidence_id: str
    ) -> Tuple[bytes, str]:
        """
        Download evidence content.
        
        Args:
            tenant_id: Tenant ID
            evidence_id: Evidence object ID
            
        Returns:
            Tuple of (content bytes, content_type)
            
        Raises:
            NotFoundError: If evidence not found
        """
        evidence = self.db.query(EvidenceObject).filter(
            and_(
                EvidenceObject.id == evidence_id,
                EvidenceObject.tenant_id == tenant_id,
                EvidenceObject.deleted_at.is_(None)
            )
        ).first()
        
        if not evidence:
            raise NotFoundError(f"Evidence {evidence_id} not found")
        
        # Download from storage
        content = self.storage.download(evidence.storage_uri)
        
        return (content, evidence.content_type)
    
    def get_evidence_by_id(
        self,
        tenant_id: str,
        evidence_id: str
    ) -> Optional[EvidenceObject]:
        """
        Get evidence by ID.
        
        Args:
            tenant_id: Tenant ID
            evidence_id: Evidence object ID
            
        Returns:
            EvidenceObject instance or None if not found
        """
        return self.db.query(EvidenceObject).filter(
            and_(
                EvidenceObject.id == evidence_id,
                EvidenceObject.tenant_id == tenant_id,
                EvidenceObject.deleted_at.is_(None)
            )
        ).first()
    
    def delete_evidence(
        self,
        tenant_id: str,
        evidence_id: str,
        soft_delete: bool = True,
        created_by_user_id: Optional[str] = None
    ) -> bool:
        """
        Delete evidence (soft delete by default).
        
        Args:
            tenant_id: Tenant ID
            evidence_id: Evidence object ID
            soft_delete: If True, soft delete (set deleted_at). If False, hard delete.
            created_by_user_id: User ID who deleted this (optional)
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            NotFoundError: If evidence not found
        """
        evidence = self.get_evidence_by_id(tenant_id, evidence_id)
        
        if not evidence:
            raise NotFoundError(f"Evidence {evidence_id} not found")
        
        if soft_delete:
            evidence.deleted_at = datetime.utcnow()
            self.db.commit()
            
            # Emit audit event
            self.audit.append_event(
                tenant_id=tenant_id,
                event_type="EVIDENCE",
                action="DELETED",
                entity_type="evidence_object",
                entity_id=evidence_id,
                actor_type="USER" if created_by_user_id else "SYSTEM",
                actor_id=created_by_user_id,
                payload={
                    "soft_delete": True,
                    "content_hash": evidence.content_hash
                }
            )
            
            return True
        else:
            # Hard delete: remove from storage and database
            try:
                self.storage.delete(evidence.storage_uri)
            except Exception as e:
                logger.warning(f"Error deleting from storage: {e}")
            
            self.db.delete(evidence)
            self.db.commit()
            
            # Emit audit event
            self.audit.append_event(
                tenant_id=tenant_id,
                event_type="EVIDENCE",
                action="DELETED",
                entity_type="evidence_object",
                entity_id=evidence_id,
                actor_type="USER" if created_by_user_id else "SYSTEM",
                actor_id=created_by_user_id,
                payload={
                    "soft_delete": False,
                    "content_hash": evidence.content_hash
                }
            )
            
            return True
