"""
Oracle event ingestion and storage service.

Handles immutable storage of data from external oracle sources.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import hashlib
import json
import logging

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.modules.parametric.models import OracleEvent, OracleEventCorrelation
from app.core.audit_ledger.ledger import AuditLedger
from app.shared.utils import generate_ulid

logger = logging.getLogger(__name__)


class OracleEventService:
    """Service for managing oracle events."""
    
    # Minimum confidence for corroboration
    CORROBORATION_THRESHOLD = 0.7
    
    def __init__(self, db: Session, audit: Optional[AuditLedger] = None):
        """
        Initialize oracle event service.
        
        Args:
            db: Database session
            audit: Optional audit ledger for event logging
        """
        self.db = db
        self.audit = audit or AuditLedger(db)
    
    def ingest_event(
        self,
        source: str,
        event_type: str,
        payload: Dict[str, Any],
        captured_at: datetime,
        scope_type: Optional[str] = None,
        scope_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        source_event_id: Optional[str] = None,
        confidence_score: Optional[float] = None,
        data_quality: Optional[Dict[str, Any]] = None,
        raw_response: Optional[bytes] = None,
        batch_id: Optional[str] = None
    ) -> OracleEvent:
        """
        Ingest an oracle event.
        
        Events are immutable once stored - payload cannot be modified.
        
        Args:
            source: Source identifier (e.g., "TOMORROW_IO", "MARINE_TRAFFIC")
            event_type: Event type (e.g., "WEATHER", "FLOOD")
            payload: Event payload dictionary (immutable)
            captured_at: When data was captured
            scope_type: Optional scope type (LOCATION, ROUTE, PORT, GLOBAL)
            scope_id: Optional scope identifier
            tenant_id: Optional tenant ID (NULL for global feeds)
            source_event_id: Optional external event ID
            confidence_score: Optional confidence score (0-1)
            data_quality: Optional data quality metadata
            raw_response: Optional raw API response bytes
            batch_id: Optional ingestion batch ID
            
        Returns:
            Created or existing OracleEvent instance
        """
        # Compute payload hash
        payload_hash = self._compute_payload_hash(payload)
        
        # Check for duplicate (same source + hash + time window)
        existing = self._find_duplicate(source, payload_hash, captured_at)
        if existing:
            logger.info(f"Duplicate event detected, returning existing: {existing.id}")
            return existing  # Return existing, don't create duplicate
        
        # Compute raw response hash if provided
        raw_hash = None
        if raw_response:
            raw_hash = hashlib.sha256(raw_response).hexdigest()
        
        # Create event
        event = OracleEvent(
            id=generate_ulid(),
            tenant_id=tenant_id,
            source=source,
            source_event_id=source_event_id,
            scope_type=scope_type,
            scope_id=scope_id,
            event_type=event_type,
            captured_at=captured_at,
            payload_json=payload,
            payload_hash=payload_hash,
            raw_response_hash=raw_hash,
            confidence_score=confidence_score,
            data_quality_json=data_quality,
            ingested_at=datetime.utcnow(),
            ingestion_batch_id=batch_id,
            processed=False
        )
        
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        
        # Audit
        self.audit.append_event(
            tenant_id=tenant_id,
            event_type="ORACLE_EVENT",
            action="INGESTED",
            entity_type="oracle_event",
            entity_id=event.id,
            actor_type="SYSTEM",
            actor_id=None,
            payload={
                "source": source,
                "event_type": event_type,
                "payload_hash": payload_hash,
                "scope": f"{scope_type}:{scope_id}" if scope_type else None
            }
        )
        
        logger.info(f"Ingested oracle event: {event.id} ({source}/{event_type})")
        
        return event
    
    def find_corroborating_events(
        self,
        event_id: str,
        time_window_minutes: int = 60,
        min_sources: int = 2
    ) -> List[OracleEvent]:
        """
        Find events from other sources that corroborate this event.
        
        For parametric triggers, we require multi-source corroboration.
        
        Args:
            event_id: Event ID (ULID string)
            time_window_minutes: Time window for corroboration search
            min_sources: Minimum number of sources required
            
        Returns:
            List of corroborating OracleEvent instances
        """
        event = self._get_event(event_id)
        
        # Time window
        start_time = event.captured_at - timedelta(minutes=time_window_minutes)
        end_time = event.captured_at + timedelta(minutes=time_window_minutes)
        
        # Find events with same scope and type from different sources
        corroborating = self.db.query(OracleEvent).filter(
            OracleEvent.id != event.id,
            OracleEvent.source != event.source,  # Different source
            OracleEvent.event_type == event.event_type,
            OracleEvent.scope_type == event.scope_type,
            OracleEvent.scope_id == event.scope_id,
            OracleEvent.captured_at.between(start_time, end_time)
        ).all()
        
        logger.debug(
            f"Found {len(corroborating)} corroborating events for {event_id} "
            f"in {time_window_minutes} minute window"
        )
        
        return corroborating
    
    def create_correlation(
        self,
        primary_event_id: str,
        corroborating_event_id: str,
        correlation_type: str,
        correlation_score: float
    ) -> OracleEventCorrelation:
        """
        Create a correlation record between two events.
        
        Args:
            primary_event_id: Primary event ID (ULID string)
            corroborating_event_id: Corroborating event ID (ULID string)
            correlation_type: Correlation type (CONFIRMS, CONTRADICTS, SUPPLEMENTS)
            correlation_score: Correlation score (0-1)
            
        Returns:
            Created OracleEventCorrelation instance
        """
        correlation = OracleEventCorrelation(
            id=generate_ulid(),
            primary_event_id=primary_event_id,
            corroborating_event_id=corroborating_event_id,
            correlation_type=correlation_type,
            correlation_score=correlation_score,
            created_at=datetime.utcnow()
        )
        
        self.db.add(correlation)
        self.db.commit()
        self.db.refresh(correlation)
        
        logger.info(
            f"Created correlation: {primary_event_id} <-> {corroborating_event_id} "
            f"({correlation_type}, score={correlation_score})"
        )
        
        return correlation
    
    def get_events_for_trigger_evaluation(
        self,
        event_type: str,
        scope_type: str,
        scope_id: str,
        time_window_start: datetime,
        time_window_end: datetime,
        min_confidence: float = 0.8
    ) -> List[OracleEvent]:
        """
        Get oracle events for trigger evaluation.
        
        Returns events that meet quality thresholds.
        
        Args:
            event_type: Event type to filter
            scope_type: Scope type to filter
            scope_id: Scope ID to filter
            time_window_start: Start of time window
            time_window_end: End of time window
            min_confidence: Minimum confidence score (default 0.8)
            
        Returns:
            List of OracleEvent instances
        """
        events = self.db.query(OracleEvent).filter(
            OracleEvent.event_type == event_type,
            OracleEvent.scope_type == scope_type,
            OracleEvent.scope_id == scope_id,
            OracleEvent.captured_at.between(time_window_start, time_window_end),
            or_(
                OracleEvent.confidence_score >= min_confidence,
                OracleEvent.confidence_score.is_(None)  # Allow unscored
            )
        ).order_by(OracleEvent.captured_at).all()
        
        logger.debug(
            f"Found {len(events)} events for trigger evaluation: "
            f"{event_type} @ {scope_type}:{scope_id} "
            f"between {time_window_start} and {time_window_end}"
        )
        
        return events
    
    def verify_event_integrity(self, event_id: str) -> Dict[str, Any]:
        """
        Verify payload hash integrity.
        
        Args:
            event_id: Event ID (ULID string)
            
        Returns:
            Dictionary with integrity verification results
        """
        event = self._get_event(event_id)
        
        computed_hash = self._compute_payload_hash(event.payload_json)
        
        is_valid = computed_hash == event.payload_hash
        
        result = {
            "valid": is_valid,
            "stored_hash": event.payload_hash,
            "computed_hash": computed_hash,
            "verified_at": datetime.utcnow().isoformat()
        }
        
        if not is_valid:
            logger.warning(
                f"Integrity check failed for event {event_id}: "
                f"stored={event.payload_hash}, computed={computed_hash}"
            )
        
        return result
    
    def mark_processed(
        self,
        event_id: str
    ) -> OracleEvent:
        """
        Mark an event as processed.
        
        Args:
            event_id: Event ID (ULID string)
            
        Returns:
            Updated OracleEvent instance
        """
        event = self._get_event(event_id)
        
        event.processed = True
        event.processed_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(event)
        
        logger.debug(f"Marked event {event_id} as processed")
        
        return event
    
    def _get_event(self, event_id: str) -> OracleEvent:
        """
        Get event by ID.
        
        Args:
            event_id: Event ID (ULID string)
            
        Returns:
            OracleEvent instance
            
        Raises:
            OracleEventNotFoundError: If event not found
        """
        event = self.db.query(OracleEvent).filter(
            OracleEvent.id == event_id
        ).first()
        if not event:
            raise OracleEventNotFoundError(f"Event {event_id} not found")
        return event
    
    def _find_duplicate(
        self,
        source: str,
        payload_hash: str,
        captured_at: datetime,
        window_minutes: int = 5
    ) -> Optional[OracleEvent]:
        """
        Find duplicate event within time window.
        
        Args:
            source: Source identifier
            payload_hash: Payload hash
            captured_at: Capture timestamp
            window_minutes: Time window in minutes
            
        Returns:
            Existing OracleEvent if duplicate found, None otherwise
        """
        start = captured_at - timedelta(minutes=window_minutes)
        end = captured_at + timedelta(minutes=window_minutes)
        
        return self.db.query(OracleEvent).filter(
            OracleEvent.source == source,
            OracleEvent.payload_hash == payload_hash,
            OracleEvent.captured_at.between(start, end)
        ).first()
    
    def _compute_payload_hash(self, payload: Dict[str, Any]) -> str:
        """
        Compute deterministic hash of payload.
        
        Args:
            payload: Payload dictionary
            
        Returns:
            SHA256 hash string
        """
        canonical = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical.encode()).hexdigest()


# Exception classes
class OracleEventNotFoundError(Exception):
    """Oracle event not found"""
    pass
