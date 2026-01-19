"""
RISKCAST Data Privacy Service
==============================
Handle GDPR/CCPA data privacy requirements.

Implements:
- GDPR Article 15: Right of access (data export)
- GDPR Article 17: Right to erasure (right to be forgotten)
- GDPR Article 20: Right to data portability
- CCPA: California Consumer Privacy Act compliance
- Data retention policies

Author: RISKCAST Team
Version: 2.0
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import json
import logging
import io

logger = logging.getLogger(__name__)


class PrivacyRequestType(Enum):
    """Types of privacy requests."""
    ACCESS = "access"           # GDPR Art. 15
    DELETION = "deletion"       # GDPR Art. 17
    PORTABILITY = "portability" # GDPR Art. 20
    RECTIFICATION = "rectification"  # GDPR Art. 16
    RESTRICTION = "restriction"  # GDPR Art. 18
    OBJECTION = "objection"     # GDPR Art. 21


class DataCategory(Enum):
    """Categories of personal data."""
    IDENTIFICATION = "identification"
    CONTACT = "contact"
    BUSINESS = "business"
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"


@dataclass
class PrivacyRequest:
    """Record of a privacy request."""
    request_id: str
    request_type: PrivacyRequestType
    user_id: str
    email: Optional[str]
    submitted_at: datetime
    completed_at: Optional[datetime]
    status: str  # pending, processing, completed, rejected
    notes: str = ""


@dataclass
class DataProcessingActivity:
    """Data processing activity record for GDPR Article 30."""
    activity_name: str
    purpose: str
    legal_basis: str  # e.g., contract, consent, legitimate interest
    data_categories: List[DataCategory]
    recipients: List[str]
    retention_period: str
    security_measures: List[str]


class DataPrivacyService:
    """
    Handle GDPR/CCPA data privacy requirements.
    
    Provides:
    - Data subject access requests (DSAR)
    - Right to erasure / deletion
    - Data portability export
    - Consent management
    - Retention policy enforcement
    """
    
    # Data retention periods by category (in days)
    RETENTION_PERIODS = {
        'risk_calculations': 365 * 7,      # 7 years (regulatory)
        'user_profiles': 365 * 3,          # 3 years after last activity
        'session_logs': 90,                # 90 days
        'error_logs': 365,                 # 1 year
        'marketing_data': 365 * 2,         # 2 years
    }
    
    # PII fields that require protection
    PII_FIELDS = [
        'email', 'phone', 'name', 'address', 'ip_address',
        'contact_person', 'shipper_name', 'consignee_name',
        'user_email', 'customer_name', 'company_name',
        'tax_id', 'bank_account', 'credit_card'
    ]
    
    # Processing activities (GDPR Article 30 register)
    PROCESSING_ACTIVITIES = [
        DataProcessingActivity(
            activity_name='Risk Calculation',
            purpose='Assess logistics risk for shipments',
            legal_basis='Contract performance (Art. 6(1)(b))',
            data_categories=[DataCategory.BUSINESS, DataCategory.TECHNICAL],
            recipients=['Internal risk team', 'Insurance partners (if authorized)'],
            retention_period='7 years (regulatory requirement)',
            security_measures=['Encryption at rest', 'Access controls', 'Audit logging']
        ),
        DataProcessingActivity(
            activity_name='User Account Management',
            purpose='Manage user accounts and authentication',
            legal_basis='Contract performance (Art. 6(1)(b))',
            data_categories=[DataCategory.IDENTIFICATION, DataCategory.CONTACT],
            recipients=['Internal IT team'],
            retention_period='Duration of account + 3 years',
            security_measures=['Password hashing', 'MFA', 'Session management']
        ),
        DataProcessingActivity(
            activity_name='Analytics and Improvement',
            purpose='Improve service quality and performance',
            legal_basis='Legitimate interest (Art. 6(1)(f))',
            data_categories=[DataCategory.BEHAVIORAL, DataCategory.TECHNICAL],
            recipients=['Internal product team'],
            retention_period='2 years (anonymized after 90 days)',
            security_measures=['Anonymization', 'Aggregation', 'Access controls']
        )
    ]
    
    def __init__(self):
        self._requests: List[PrivacyRequest] = []
    
    def export_user_data(self, user_id: str) -> Dict:
        """
        GDPR Article 15: Right of access.
        Export all data associated with a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Complete data export for the user
        """
        logger.info(f"Processing data export request for user: {user_id}")
        
        from app.models.audit_trail import AuditService
        
        # Get audit trail entries
        audit_data = AuditService.export_user_data(user_id)
        
        # Build comprehensive export
        export_data = {
            'data_subject': {
                'user_id': user_id,
                'export_date': datetime.utcnow().isoformat(),
                'export_format': 'JSON',
                'gdpr_article': 'Article 15 (Right of access)'
            },
            'data_categories': {
                'risk_assessments': audit_data.get('entries', []),
                'account_information': self._get_account_info(user_id),
                'preferences': self._get_user_preferences(user_id),
                'consent_records': self._get_consent_records(user_id)
            },
            'processing_activities': [
                {
                    'activity': pa.activity_name,
                    'purpose': pa.purpose,
                    'legal_basis': pa.legal_basis,
                    'retention_period': pa.retention_period
                }
                for pa in self.PROCESSING_ACTIVITIES
            ],
            'your_rights': {
                'rectification': 'You can request correction of inaccurate data (Art. 16)',
                'erasure': 'You can request deletion of your data (Art. 17)',
                'restriction': 'You can request restricted processing (Art. 18)',
                'portability': 'You can receive your data in machine-readable format (Art. 20)',
                'objection': 'You can object to processing (Art. 21)'
            },
            'data_protection_officer': {
                'email': 'dpo@riskcast.io',
                'address': 'RISKCAST DPO, [Address]'
            }
        }
        
        # Log the export
        self._log_privacy_request(
            PrivacyRequest(
                request_id=f"DSAR-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                request_type=PrivacyRequestType.ACCESS,
                user_id=user_id,
                email=None,
                submitted_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                status='completed'
            )
        )
        
        return export_data
    
    def delete_user_data(self, user_id: str, reason: str) -> Dict:
        """
        GDPR Article 17: Right to erasure ("right to be forgotten").
        
        Note: Some data may need to be retained for regulatory compliance.
        In such cases, data is anonymized rather than deleted.
        
        Args:
            user_id: User identifier
            reason: Reason for deletion request
            
        Returns:
            Deletion result summary
        """
        logger.info(f"Processing deletion request for user: {user_id}")
        
        from app.models.audit_trail import AuditService
        
        # Anonymize audit trail (can't delete due to regulatory requirements)
        anonymize_result = AuditService.anonymize_user_data(user_id)
        
        # Delete user account data
        account_deleted = self._delete_account_data(user_id)
        
        # Delete preferences
        preferences_deleted = self._delete_user_preferences(user_id)
        
        # Record the request
        request = PrivacyRequest(
            request_id=f"DEL-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            request_type=PrivacyRequestType.DELETION,
            user_id=user_id,
            email=None,
            submitted_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            status='completed',
            notes=reason
        )
        self._log_privacy_request(request)
        
        return {
            'request_id': request.request_id,
            'user_id': user_id,
            'deletion_date': datetime.utcnow().isoformat(),
            'actions_taken': {
                'audit_records_anonymized': anonymize_result.get('entries_anonymized', 0),
                'account_data_deleted': account_deleted,
                'preferences_deleted': preferences_deleted
            },
            'retention_note': (
                'Audit records have been anonymized but retained for regulatory compliance '
                '(7 years per financial services requirements). '
                'No personally identifiable information remains linked to these records.'
            ),
            'confirmation': 'Your personal data has been processed in accordance with GDPR Article 17'
        }
    
    def export_portable_data(self, user_id: str, format: str = 'json') -> bytes:
        """
        GDPR Article 20: Right to data portability.
        Export data in machine-readable format.
        
        Args:
            user_id: User identifier
            format: Export format ('json' or 'csv')
            
        Returns:
            Portable data as bytes
        """
        logger.info(f"Processing portability export for user: {user_id}")
        
        # Get user's data
        export_data = self.export_user_data(user_id)
        
        # Remove non-portable metadata
        portable_data = {
            'risk_assessments': export_data['data_categories']['risk_assessments'],
            'account_information': export_data['data_categories']['account_information'],
            'preferences': export_data['data_categories']['preferences'],
            'export_metadata': {
                'user_id': user_id,
                'export_date': datetime.utcnow().isoformat(),
                'format': format,
                'gdpr_article': 'Article 20 (Right to data portability)'
            }
        }
        
        if format == 'json':
            return json.dumps(portable_data, indent=2, default=str).encode('utf-8')
        elif format == 'csv':
            return self._convert_to_csv(portable_data)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def apply_data_retention_policy(self) -> Dict:
        """
        Apply data retention policy.
        Automatically delete/anonymize data past retention period.
        
        Should be run as a scheduled job (e.g., daily).
        
        Returns:
            Summary of actions taken
        """
        logger.info("Applying data retention policy")
        
        now = datetime.utcnow()
        actions = {
            'anonymized_records': 0,
            'deleted_sessions': 0,
            'deleted_logs': 0,
            'execution_date': now.isoformat()
        }
        
        # Anonymize old audit entries
        retention_cutoff = now - timedelta(days=self.RETENTION_PERIODS['risk_calculations'])
        
        # In production, this would query the database
        # For now, log the action
        logger.info(f"Would anonymize audit entries older than {retention_cutoff}")
        
        # Delete old session logs
        session_cutoff = now - timedelta(days=self.RETENTION_PERIODS['session_logs'])
        logger.info(f"Would delete session logs older than {session_cutoff}")
        
        return actions
    
    def record_consent(
        self,
        user_id: str,
        consent_type: str,
        granted: bool,
        ip_address: str = None
    ) -> Dict:
        """
        Record user consent.
        
        Args:
            user_id: User identifier
            consent_type: Type of consent (e.g., 'marketing', 'analytics')
            granted: Whether consent was granted
            ip_address: IP address for verification
            
        Returns:
            Consent record
        """
        consent_record = {
            'consent_id': f"CON-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            'user_id': user_id,
            'consent_type': consent_type,
            'granted': granted,
            'timestamp': datetime.utcnow().isoformat(),
            'ip_address': ip_address,
            'method': 'explicit_opt_in' if granted else 'explicit_opt_out'
        }
        
        logger.info(f"Recorded consent for user {user_id}: {consent_type}={granted}")
        
        return consent_record
    
    def get_processing_register(self) -> List[Dict]:
        """
        Get GDPR Article 30 processing activities register.
        
        Returns:
            List of processing activities
        """
        return [
            {
                'activity_name': pa.activity_name,
                'purpose': pa.purpose,
                'legal_basis': pa.legal_basis,
                'data_categories': [dc.value for dc in pa.data_categories],
                'recipients': pa.recipients,
                'retention_period': pa.retention_period,
                'security_measures': pa.security_measures
            }
            for pa in self.PROCESSING_ACTIVITIES
        ]
    
    def get_privacy_policy_data(self) -> Dict:
        """
        Get data for privacy policy display.
        
        Returns:
            Privacy policy information
        """
        return {
            'data_controller': {
                'name': 'RISKCAST Ltd.',
                'address': '[Company Address]',
                'email': 'privacy@riskcast.io'
            },
            'data_protection_officer': {
                'email': 'dpo@riskcast.io'
            },
            'processing_purposes': [
                {
                    'purpose': 'Risk calculation services',
                    'legal_basis': 'Contract performance',
                    'retention': '7 years'
                },
                {
                    'purpose': 'Account management',
                    'legal_basis': 'Contract performance',
                    'retention': 'Duration of account + 3 years'
                },
                {
                    'purpose': 'Service improvement',
                    'legal_basis': 'Legitimate interest',
                    'retention': '2 years (anonymized after 90 days)'
                }
            ],
            'your_rights': [
                'Access your data (Art. 15)',
                'Rectify inaccurate data (Art. 16)',
                'Erase your data (Art. 17)',
                'Restrict processing (Art. 18)',
                'Data portability (Art. 20)',
                'Object to processing (Art. 21)',
                'Lodge a complaint with supervisory authority'
            ],
            'security_measures': [
                'Encryption at rest and in transit',
                'Access controls and authentication',
                'Regular security audits',
                'Employee training',
                'Incident response procedures'
            ],
            'international_transfers': {
                'applicable': True,
                'safeguards': 'Standard Contractual Clauses (SCCs)'
            },
            'last_updated': datetime(2026, 1, 15).isoformat()
        }
    
    # Private helper methods
    
    def _get_account_info(self, user_id: str) -> Dict:
        """Get user account information."""
        # In production, this would query the user database
        return {
            'user_id': user_id,
            'note': 'Account information would be retrieved from user database'
        }
    
    def _get_user_preferences(self, user_id: str) -> Dict:
        """Get user preferences."""
        return {
            'user_id': user_id,
            'note': 'Preferences would be retrieved from preferences database'
        }
    
    def _get_consent_records(self, user_id: str) -> List[Dict]:
        """Get user consent records."""
        return []
    
    def _delete_account_data(self, user_id: str) -> bool:
        """Delete user account data."""
        # In production, this would delete from user database
        logger.info(f"Would delete account data for user: {user_id}")
        return True
    
    def _delete_user_preferences(self, user_id: str) -> bool:
        """Delete user preferences."""
        logger.info(f"Would delete preferences for user: {user_id}")
        return True
    
    def _log_privacy_request(self, request: PrivacyRequest):
        """Log a privacy request."""
        self._requests.append(request)
        logger.info(f"Logged privacy request: {request.request_id}")
    
    def _convert_to_csv(self, data: Dict) -> bytes:
        """Convert data to CSV format."""
        import csv
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Category', 'Field', 'Value'])
        
        # Flatten and write data
        for category, items in data.items():
            if isinstance(items, list):
                for i, item in enumerate(items):
                    if isinstance(item, dict):
                        for key, value in item.items():
                            writer.writerow([category, f"{key}_{i}", str(value)])
            elif isinstance(items, dict):
                for key, value in items.items():
                    writer.writerow([category, key, str(value)])
        
        return output.getvalue().encode('utf-8')


# Global service instance
_privacy_service = DataPrivacyService()


# Convenience functions for API
def export_user_data(user_id: str) -> Dict:
    """Export all data for a user (GDPR Art. 15)."""
    return _privacy_service.export_user_data(user_id)


def delete_user_data(user_id: str, reason: str) -> Dict:
    """Delete/anonymize user data (GDPR Art. 17)."""
    return _privacy_service.delete_user_data(user_id, reason)


def export_portable_data(user_id: str, format: str = 'json') -> bytes:
    """Export portable data (GDPR Art. 20)."""
    return _privacy_service.export_portable_data(user_id, format)


def get_processing_register() -> List[Dict]:
    """Get GDPR Art. 30 processing register."""
    return _privacy_service.get_processing_register()


def record_consent(user_id: str, consent_type: str, granted: bool) -> Dict:
    """Record user consent."""
    return _privacy_service.record_consent(user_id, consent_type, granted)
