"""
Trigger definition management service.

Handles creation, publishing, and versioning of parametric trigger definitions.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import hashlib
import json
import logging

from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.modules.parametric.models import TriggerDefinition, TriggerDefinitionStatus
from app.core.audit_ledger.ledger import AuditLedger
from app.shared.utils import generate_ulid

logger = logging.getLogger(__name__)


class TriggerDefinitionService:
    """Service for managing trigger definitions."""
    
    def __init__(self, db: Session, audit: Optional[AuditLedger] = None):
        """
        Initialize trigger definition service.
        
        Args:
            db: Database session
            audit: Optional audit ledger for event logging
        """
        self.db = db
        self.audit = audit or AuditLedger(db)
    
    def create_definition(
        self,
        tenant_id: Optional[str],
        name: str,
        trigger_type: str,
        params: Dict[str, Any],
        payout_structure: Dict[str, Any],
        description: Optional[str] = None,
        scope_constraints: Optional[Dict[str, Any]] = None,
        corroboration: Optional[Dict[str, Any]] = None,
        created_by: str = None
    ) -> TriggerDefinition:
        """
        Create a new trigger definition in DRAFT status.
        
        Args:
            tenant_id: Tenant ID (ULID string, None for system triggers)
            name: Definition name
            trigger_type: Trigger type (RAINFALL, WIND_SPEED, FLOOD, etc.)
            params: Trigger parameters dictionary
            payout_structure: Payout structure dictionary
            description: Optional description
            scope_constraints: Optional scope constraints
            corroboration: Optional corroboration requirements
            created_by: User ID creating (ULID string)
            
        Returns:
            Created TriggerDefinition instance
        """
        # Get version number
        existing_versions = self.db.query(TriggerDefinition).filter(
            TriggerDefinition.tenant_id == tenant_id,
            TriggerDefinition.name == name
        ).count()
        version = existing_versions + 1
        
        definition = TriggerDefinition(
            id=generate_ulid(),
            tenant_id=tenant_id,
            name=name,
            description=description,
            trigger_type=trigger_type,
            type=trigger_type,  # Legacy field
            status=TriggerDefinitionStatus.DRAFT,
            version=version,
            params_json=params,
            scope_constraints_json=scope_constraints,
            corroboration_json=corroboration,
            payout_structure_json=payout_structure,
            created_by_user_id=created_by,
            created_at=datetime.utcnow()
        )
        
        self.db.add(definition)
        self.db.commit()
        self.db.refresh(definition)
        
        # Audit
        self.audit.append_event(
            tenant_id=tenant_id,
            event_type="TRIGGER_DEFINITION",
            action="CREATED",
            entity_type="trigger_definition",
            entity_id=definition.id,
            actor_type="USER",
            actor_id=created_by,
            payload={
                "name": name,
                "trigger_type": trigger_type,
                "version": version
            }
        )
        
        logger.info(f"Created trigger definition: {definition.id} ({name} v{version})")
        
        return definition
    
    def publish_definition(
        self,
        definition_id: str,
        published_by: str
    ) -> TriggerDefinition:
        """
        Publish a trigger definition.
        
        After publishing, parameters are immutable.
        
        Args:
            definition_id: Definition ID (ULID string)
            published_by: User ID publishing (ULID string)
            
        Returns:
            Updated TriggerDefinition instance
        """
        definition = self._get_definition(definition_id)
        
        if definition.status != TriggerDefinitionStatus.DRAFT:
            raise InvalidDefinitionStateError(f"Definition is {definition.status.value}, must be DRAFT")
        
        # Validate definition completeness
        self._validate_for_publish(definition)
        
        # Compute immutable hash
        immutable_hash = self._compute_definition_hash(definition)
        
        definition.status = TriggerDefinitionStatus.PUBLISHED
        definition.immutable_hash = immutable_hash
        definition.published_at = datetime.utcnow()
        definition.published_by_user_id = published_by
        definition.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(definition)
        
        # Audit
        self.audit.append_event(
            tenant_id=definition.tenant_id,
            event_type="TRIGGER_DEFINITION",
            action="PUBLISHED",
            entity_type="trigger_definition",
            entity_id=definition.id,
            actor_type="USER",
            actor_id=published_by,
            payload={
                "immutable_hash": immutable_hash,
                "name": definition.name,
                "version": definition.version
            }
        )
        
        logger.info(f"Published trigger definition: {definition.id} (hash: {immutable_hash})")
        
        return definition
    
    def deprecate_definition(
        self,
        definition_id: str,
        deprecated_by: str,
        reason: str
    ) -> TriggerDefinition:
        """
        Deprecate a published definition.
        
        Args:
            definition_id: Definition ID (ULID string)
            deprecated_by: User ID deprecating (ULID string)
            reason: Deprecation reason
            
        Returns:
            Updated TriggerDefinition instance
        """
        definition = self._get_definition(definition_id)
        
        if definition.status != TriggerDefinitionStatus.PUBLISHED:
            raise InvalidDefinitionStateError("Can only deprecate PUBLISHED definitions")
        
        definition.status = TriggerDefinitionStatus.DEPRECATED
        definition.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(definition)
        
        # Audit
        self.audit.append_event(
            tenant_id=definition.tenant_id,
            event_type="TRIGGER_DEFINITION",
            action="DEPRECATED",
            entity_type="trigger_definition",
            entity_id=definition.id,
            actor_type="USER",
            actor_id=deprecated_by,
            payload={
                "reason": reason,
                "name": definition.name,
                "version": definition.version
            }
        )
        
        logger.info(f"Deprecated trigger definition: {definition.id}")
        
        return definition
    
    def get_published_definitions(
        self,
        tenant_id: Optional[str] = None,
        trigger_type: Optional[str] = None
    ) -> List[TriggerDefinition]:
        """
        Get published trigger definitions.
        
        Args:
            tenant_id: Optional tenant ID filter (includes global if None)
            trigger_type: Optional trigger type filter
            
        Returns:
            List of published TriggerDefinition instances
        """
        query = self.db.query(TriggerDefinition).filter(
            TriggerDefinition.status == TriggerDefinitionStatus.PUBLISHED
        )
        
        if tenant_id:
            # Include tenant-specific and global
            query = query.filter(
                or_(
                    TriggerDefinition.tenant_id == tenant_id,
                    TriggerDefinition.tenant_id.is_(None)
                )
            )
        else:
            # Only global
            query = query.filter(TriggerDefinition.tenant_id.is_(None))
        
        if trigger_type:
            query = query.filter(
                or_(
                    TriggerDefinition.trigger_type == trigger_type,
                    TriggerDefinition.type == trigger_type  # Legacy support
                )
            )
        
        return query.order_by(TriggerDefinition.created_at.desc()).all()
    
    def get_definition_versions(
        self,
        tenant_id: Optional[str],
        name: str
    ) -> List[TriggerDefinition]:
        """
        Get all versions of a trigger definition.
        
        Args:
            tenant_id: Tenant ID (ULID string, None for system)
            name: Definition name
            
        Returns:
            List of TriggerDefinition instances ordered by version
        """
        return self.db.query(TriggerDefinition).filter(
            TriggerDefinition.tenant_id == tenant_id,
            TriggerDefinition.name == name
        ).order_by(TriggerDefinition.version).all()
    
    def verify_definition_integrity(self, definition_id: str) -> Dict[str, Any]:
        """
        Verify definition hash integrity.
        
        Args:
            definition_id: Definition ID (ULID string)
            
        Returns:
            Dictionary with integrity verification results
        """
        definition = self._get_definition(definition_id)
        
        if not definition.immutable_hash:
            return {
                "valid": False,
                "reason": "Definition not published (no hash)",
                "verified_at": datetime.utcnow().isoformat()
            }
        
        computed_hash = self._compute_definition_hash(definition)
        is_valid = computed_hash == definition.immutable_hash
        
        result = {
            "valid": is_valid,
            "stored_hash": definition.immutable_hash,
            "computed_hash": computed_hash,
            "verified_at": datetime.utcnow().isoformat()
        }
        
        if not is_valid:
            logger.warning(
                f"Integrity check failed for definition {definition_id}: "
                f"stored={definition.immutable_hash}, computed={computed_hash}"
            )
        
        return result
    
    def _get_definition(self, definition_id: str) -> TriggerDefinition:
        """
        Get definition by ID.
        
        Args:
            definition_id: Definition ID (ULID string)
            
        Returns:
            TriggerDefinition instance
            
        Raises:
            TriggerDefinitionNotFoundError: If definition not found
        """
        definition = self.db.query(TriggerDefinition).filter(
            TriggerDefinition.id == definition_id
        ).first()
        if not definition:
            raise TriggerDefinitionNotFoundError(f"Definition {definition_id} not found")
        return definition
    
    def _validate_for_publish(self, definition: TriggerDefinition):
        """
        Validate definition is complete for publishing.
        
        Args:
            definition: TriggerDefinition instance
            
        Raises:
            InvalidDefinitionError: If validation fails
        """
        errors = []
        
        if not definition.name:
            errors.append("Missing name")
        
        if not definition.trigger_type and not definition.type:
            errors.append("Missing trigger_type")
        
        params = definition.params_json or {}
        if 'threshold_value' not in params:
            errors.append("Missing threshold_value in params")
        if 'comparison' not in params:
            errors.append("Missing comparison operator in params")
        
        payout = definition.payout_structure_json or {}
        if not payout or 'type' not in payout:
            errors.append("Missing payout_structure or payout type")
        
        if errors:
            raise InvalidDefinitionError("; ".join(errors))
    
    def _compute_definition_hash(self, definition: TriggerDefinition) -> str:
        """
        Compute hash of definition parameters.
        
        Args:
            definition: TriggerDefinition instance
            
        Returns:
            SHA256 hash string
        """
        hashable = {
            "trigger_type": definition.trigger_type or definition.type,
            "params": definition.params_json,
            "scope_constraints": definition.scope_constraints_json,
            "corroboration": definition.corroboration_json,
            "payout_structure": definition.payout_structure_json
        }
        canonical = json.dumps(hashable, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical.encode()).hexdigest()


# Exception classes
class TriggerDefinitionNotFoundError(Exception):
    """Trigger definition not found"""
    pass


class InvalidDefinitionStateError(Exception):
    """Invalid definition state for operation"""
    pass


class InvalidDefinitionError(Exception):
    """Invalid definition data"""
    pass
