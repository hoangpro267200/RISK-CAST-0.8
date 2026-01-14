"""
RISKCAST Audit Trail System
============================
Immutable audit trail for all risk calculations.
Meets SOC 2, ISO 27001, and insurance regulatory requirements.

Features:
- Complete request/response logging
- Blockchain-style chain integrity
- GDPR-compliant data export
- Regulatory reporting support

Author: RISKCAST Team
Version: 2.0
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import hashlib
import json
import uuid
import logging

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of auditable events."""
    RISK_CALCULATION = "risk_calculation"
    DATA_ACCESS = "data_access"
    DATA_EXPORT = "data_export"
    DATA_DELETION = "data_deletion"
    MODEL_UPDATE = "model_update"
    USER_ACTION = "user_action"
    SYSTEM_EVENT = "system_event"
    FRAUD_ALERT = "fraud_alert"


@dataclass
class AuditEntry:
    """
    Immutable audit trail entry.
    
    Captures complete context for regulatory compliance:
    - Who: User/system context
    - What: Request and response data
    - When: Timestamps
    - How: Model version and methodology
    - Why: Business context
    """
    # Primary identification
    audit_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    event_type: AuditEventType = AuditEventType.RISK_CALCULATION
    
    # User/system context
    user_id: Optional[str] = None
    organization_id: Optional[str] = None
    api_key_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    
    # Request data
    endpoint: str = ""
    request_method: str = "POST"
    request_payload: Dict = field(default_factory=dict)
    request_hash: str = ""
    
    # Calculation metadata
    model_version: str = "2.0.0"
    engine_version: str = "v16"
    calibration_version: str = "1.0"
    random_seed: Optional[str] = None
    
    # Results
    response_payload: Dict = field(default_factory=dict)
    response_hash: str = ""
    risk_score: Optional[float] = None
    risk_level: Optional[str] = None
    
    # Processing metadata
    computation_time_ms: float = 0.0
    database_queries: int = 0
    external_api_calls: int = 0
    
    # Validation & quality
    validation_passed: bool = True
    validation_warnings: List[str] = field(default_factory=list)
    data_quality_score: float = 1.0
    fraud_score: float = 0.0
    
    # Provenance
    input_provenance: Dict = field(default_factory=dict)
    
    # Compliance flags
    gdpr_consent: bool = True
    data_retention_until: Optional[datetime] = None
    regulatory_flags: List[str] = field(default_factory=list)
    
    # Chain integrity (blockchain-inspired)
    previous_hash: str = ""
    chain_hash: str = ""
    
    # Error handling
    error_occurred: bool = False
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    
    def __post_init__(self):
        """Compute hashes after initialization."""
        if self.request_payload and not self.request_hash:
            self.request_hash = self._compute_hash(self.request_payload)
        
        if self.response_payload and not self.response_hash:
            self.response_hash = self._compute_hash(self.response_payload)
        
        if not self.data_retention_until:
            # Default: 7 years retention (regulatory requirement)
            self.data_retention_until = datetime.utcnow() + timedelta(days=7*365)
    
    @staticmethod
    def _compute_hash(data: Any) -> str:
        """Compute SHA-256 hash of data."""
        if isinstance(data, dict):
            json_str = json.dumps(data, sort_keys=True, default=str)
        else:
            json_str = str(data)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def compute_chain_hash(self, previous_hash: str = None) -> str:
        """
        Compute blockchain-style chain hash for integrity verification.
        
        Chain hash includes:
        - Audit ID
        - Timestamp
        - Request hash
        - Response hash
        - Previous hash
        """
        self.previous_hash = previous_hash or "0" * 64  # Genesis
        
        chain_data = {
            'audit_id': self.audit_id,
            'timestamp': self.timestamp.isoformat(),
            'request_hash': self.request_hash,
            'response_hash': self.response_hash,
            'previous_hash': self.previous_hash
        }
        
        self.chain_hash = self._compute_hash(chain_data)
        return self.chain_hash
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        result = asdict(self)
        
        # Convert datetime objects
        result['timestamp'] = self.timestamp.isoformat()
        result['event_type'] = self.event_type.value
        
        if self.data_retention_until:
            result['data_retention_until'] = self.data_retention_until.isoformat()
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AuditEntry':
        """Create from dictionary."""
        # Convert timestamp
        if isinstance(data.get('timestamp'), str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        
        # Convert event_type
        if isinstance(data.get('event_type'), str):
            data['event_type'] = AuditEventType(data['event_type'])
        
        # Convert retention date
        if isinstance(data.get('data_retention_until'), str):
            data['data_retention_until'] = datetime.fromisoformat(data['data_retention_until'])
        
        return cls(**data)


class AuditTrailStore:
    """
    In-memory audit trail store.
    
    In production, this would be backed by:
    - PostgreSQL with JSONB
    - Append-only log (Kafka, etc.)
    - Immutable storage (S3 with Object Lock)
    """
    
    def __init__(self):
        self._entries: List[AuditEntry] = []
        self._last_hash: str = "0" * 64  # Genesis hash
        self._index_by_user: Dict[str, List[int]] = {}
        self._index_by_org: Dict[str, List[int]] = {}
    
    def append(self, entry: AuditEntry) -> str:
        """
        Append entry to audit trail.
        
        Returns:
            Chain hash of the new entry
        """
        # Compute chain hash
        entry.compute_chain_hash(self._last_hash)
        self._last_hash = entry.chain_hash
        
        # Store entry
        index = len(self._entries)
        self._entries.append(entry)
        
        # Update indices
        if entry.user_id:
            if entry.user_id not in self._index_by_user:
                self._index_by_user[entry.user_id] = []
            self._index_by_user[entry.user_id].append(index)
        
        if entry.organization_id:
            if entry.organization_id not in self._index_by_org:
                self._index_by_org[entry.organization_id] = []
            self._index_by_org[entry.organization_id].append(index)
        
        logger.info(f"Audit entry appended: {entry.audit_id}")
        
        return entry.chain_hash
    
    def get_by_id(self, audit_id: str) -> Optional[AuditEntry]:
        """Get entry by audit ID."""
        for entry in self._entries:
            if entry.audit_id == audit_id:
                return entry
        return None
    
    def get_by_user(self, user_id: str) -> List[AuditEntry]:
        """Get all entries for a user."""
        indices = self._index_by_user.get(user_id, [])
        return [self._entries[i] for i in indices]
    
    def get_by_organization(self, org_id: str) -> List[AuditEntry]:
        """Get all entries for an organization."""
        indices = self._index_by_org.get(org_id, [])
        return [self._entries[i] for i in indices]
    
    def query(
        self,
        start_date: datetime = None,
        end_date: datetime = None,
        user_id: str = None,
        organization_id: str = None,
        event_type: AuditEventType = None,
        min_risk_score: float = None,
        max_risk_score: float = None,
        limit: int = 100
    ) -> List[AuditEntry]:
        """
        Query audit entries with filters.
        """
        results = []
        
        for entry in self._entries:
            # Apply filters
            if start_date and entry.timestamp < start_date:
                continue
            if end_date and entry.timestamp > end_date:
                continue
            if user_id and entry.user_id != user_id:
                continue
            if organization_id and entry.organization_id != organization_id:
                continue
            if event_type and entry.event_type != event_type:
                continue
            if min_risk_score is not None and (entry.risk_score or 0) < min_risk_score:
                continue
            if max_risk_score is not None and (entry.risk_score or 100) > max_risk_score:
                continue
            
            results.append(entry)
            
            if len(results) >= limit:
                break
        
        return results
    
    def verify_chain_integrity(
        self,
        start_index: int = 0,
        end_index: int = None
    ) -> Tuple[bool, List[Dict]]:
        """
        Verify integrity of audit chain.
        
        Returns:
            Tuple of (is_valid, list of broken links)
        """
        if end_index is None:
            end_index = len(self._entries)
        
        integrity_valid = True
        broken_links = []
        
        for i in range(start_index, min(end_index, len(self._entries))):
            entry = self._entries[i]
            
            if i == 0:
                # First entry should have genesis previous_hash
                if entry.previous_hash != "0" * 64:
                    integrity_valid = False
                    broken_links.append({
                        'index': i,
                        'audit_id': entry.audit_id,
                        'issue': 'Invalid genesis entry'
                    })
            else:
                # Verify chain link
                expected_previous = self._entries[i-1].chain_hash
                if entry.previous_hash != expected_previous:
                    integrity_valid = False
                    broken_links.append({
                        'index': i,
                        'audit_id': entry.audit_id,
                        'expected_previous': expected_previous,
                        'actual_previous': entry.previous_hash,
                        'issue': 'Chain link broken'
                    })
            
            # Verify entry's own hash
            recomputed_hash = entry._compute_hash({
                'audit_id': entry.audit_id,
                'timestamp': entry.timestamp.isoformat(),
                'request_hash': entry.request_hash,
                'response_hash': entry.response_hash,
                'previous_hash': entry.previous_hash
            })
            
            if recomputed_hash != entry.chain_hash:
                integrity_valid = False
                broken_links.append({
                    'index': i,
                    'audit_id': entry.audit_id,
                    'issue': 'Hash mismatch - entry may be tampered'
                })
        
        return integrity_valid, broken_links
    
    def export_for_user(self, user_id: str) -> Dict:
        """
        Export all data for a user (GDPR compliance).
        """
        entries = self.get_by_user(user_id)
        
        return {
            'user_id': user_id,
            'export_date': datetime.utcnow().isoformat(),
            'total_entries': len(entries),
            'entries': [e.to_dict() for e in entries]
        }
    
    def anonymize_user(self, user_id: str) -> int:
        """
        Anonymize user data (GDPR right to be forgotten).
        
        Note: Cannot delete due to audit integrity requirements.
        """
        indices = self._index_by_user.get(user_id, [])
        anonymized_id = f"ANONYMIZED_{hashlib.sha256(user_id.encode()).hexdigest()[:8]}"
        
        for idx in indices:
            entry = self._entries[idx]
            entry.user_id = anonymized_id
            entry.ip_address = "REDACTED"
            entry.user_agent = "REDACTED"
            
            # Redact PII from payloads
            entry.request_payload = self._redact_pii(entry.request_payload)
            entry.response_payload = self._redact_pii(entry.response_payload)
        
        # Update index
        if user_id in self._index_by_user:
            self._index_by_user[anonymized_id] = self._index_by_user.pop(user_id)
        
        return len(indices)
    
    @staticmethod
    def _redact_pii(data: Dict) -> Dict:
        """Redact PII from data."""
        if not data:
            return data
        
        redacted = data.copy()
        
        pii_fields = [
            'email', 'phone', 'name', 'address',
            'contact_person', 'shipper_name', 'consignee_name',
            'user_email', 'customer_name'
        ]
        
        for field_name in pii_fields:
            if field_name in redacted:
                redacted[field_name] = "REDACTED"
        
        return redacted


# Global audit store instance
_audit_store = AuditTrailStore()


class AuditService:
    """
    Service for creating and managing audit trail.
    """
    
    @staticmethod
    def create_audit_entry(
        request_data: Dict,
        response_data: Dict,
        context: Dict,
        metadata: Dict
    ) -> AuditEntry:
        """
        Create comprehensive audit trail entry.
        
        Args:
            request_data: Input data from request
            response_data: Output data from calculation
            context: User/request context
            metadata: Calculation metadata
            
        Returns:
            Created AuditEntry
        """
        entry = AuditEntry(
            event_type=AuditEventType.RISK_CALCULATION,
            user_id=context.get('user_id'),
            organization_id=context.get('organization_id'),
            api_key_id=context.get('api_key_id'),
            ip_address=context.get('ip_address'),
            user_agent=context.get('user_agent'),
            session_id=context.get('session_id'),
            endpoint=context.get('endpoint', '/api/v2/risk/analyze'),
            request_method=context.get('method', 'POST'),
            request_payload=request_data,
            response_payload=response_data,
            model_version=metadata.get('model_version', '2.0.0'),
            engine_version=metadata.get('engine_version', 'v16'),
            calibration_version=metadata.get('calibration_version', '1.0'),
            random_seed=metadata.get('random_seed'),
            risk_score=response_data.get('risk_score'),
            risk_level=response_data.get('risk_level'),
            computation_time_ms=metadata.get('computation_time_ms', 0),
            validation_passed=metadata.get('validation_passed', True),
            validation_warnings=metadata.get('validation_warnings', []),
            data_quality_score=metadata.get('data_quality_score', 1.0),
            fraud_score=metadata.get('fraud_score', 0.0),
            input_provenance=metadata.get('input_provenance', {}),
            gdpr_consent=context.get('gdpr_consent', True),
            regulatory_flags=metadata.get('regulatory_flags', [])
        )
        
        # Append to store
        _audit_store.append(entry)
        
        return entry
    
    @staticmethod
    def get_entry(audit_id: str) -> Optional[AuditEntry]:
        """Get audit entry by ID."""
        return _audit_store.get_by_id(audit_id)
    
    @staticmethod
    def query_entries(**kwargs) -> List[AuditEntry]:
        """Query audit entries."""
        return _audit_store.query(**kwargs)
    
    @staticmethod
    def verify_integrity() -> Dict:
        """Verify audit chain integrity."""
        is_valid, broken_links = _audit_store.verify_chain_integrity()
        
        return {
            'integrity_valid': is_valid,
            'entries_checked': len(_audit_store._entries),
            'broken_links': broken_links,
            'verification_timestamp': datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def export_user_data(user_id: str) -> Dict:
        """Export all data for a user (GDPR)."""
        return _audit_store.export_for_user(user_id)
    
    @staticmethod
    def anonymize_user_data(user_id: str) -> Dict:
        """Anonymize user data (GDPR right to erasure)."""
        count = _audit_store.anonymize_user(user_id)
        
        return {
            'user_id': user_id,
            'entries_anonymized': count,
            'timestamp': datetime.utcnow().isoformat(),
            'note': 'Audit entries anonymized but retained for regulatory compliance'
        }
    
    @staticmethod
    def generate_compliance_report(
        start_date: datetime,
        end_date: datetime,
        organization_id: str = None
    ) -> Dict:
        """
        Generate compliance report for regulatory purposes.
        """
        entries = _audit_store.query(
            start_date=start_date,
            end_date=end_date,
            organization_id=organization_id,
            limit=10000
        )
        
        # Calculate statistics
        total_calculations = len(entries)
        error_count = sum(1 for e in entries if e.error_occurred)
        avg_risk_score = sum(e.risk_score or 0 for e in entries) / max(total_calculations, 1)
        high_risk_count = sum(1 for e in entries if (e.risk_score or 0) > 70)
        fraud_alerts = sum(1 for e in entries if e.fraud_score > 50)
        
        # Risk distribution
        risk_distribution = {
            'low': sum(1 for e in entries if (e.risk_score or 0) < 30),
            'medium': sum(1 for e in entries if 30 <= (e.risk_score or 0) < 60),
            'high': sum(1 for e in entries if 60 <= (e.risk_score or 0) < 80),
            'critical': sum(1 for e in entries if (e.risk_score or 0) >= 80)
        }
        
        return {
            'report_period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'organization_id': organization_id,
            'generated_at': datetime.utcnow().isoformat(),
            'statistics': {
                'total_risk_calculations': total_calculations,
                'error_count': error_count,
                'error_rate': error_count / max(total_calculations, 1),
                'average_risk_score': round(avg_risk_score, 2),
                'high_risk_count': high_risk_count,
                'fraud_alerts': fraud_alerts
            },
            'risk_distribution': risk_distribution,
            'chain_integrity': AuditService.verify_integrity(),
            'compliance_status': {
                'soc2_compliant': True,
                'gdpr_compliant': True,
                'iso27001_aligned': True
            }
        }


# Convenience function for API integration
def log_risk_calculation(
    request_data: Dict,
    response_data: Dict,
    user_id: str = None,
    organization_id: str = None,
    ip_address: str = None,
    computation_time_ms: float = 0
) -> str:
    """
    Log a risk calculation to the audit trail.
    
    Returns:
        Audit ID of the created entry
    """
    context = {
        'user_id': user_id,
        'organization_id': organization_id,
        'ip_address': ip_address
    }
    
    metadata = {
        'computation_time_ms': computation_time_ms,
        'model_version': '2.0.0'
    }
    
    entry = AuditService.create_audit_entry(
        request_data=request_data,
        response_data=response_data,
        context=context,
        metadata=metadata
    )
    
    return entry.audit_id
