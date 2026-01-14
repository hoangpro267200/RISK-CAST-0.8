"""
API Key authentication model.

RISKCAST v17 - API Key Management
"""

from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text
from datetime import datetime, timedelta
from typing import Optional, Tuple, List
import secrets
import hashlib
import json

# Try to import Base from database, fallback to declarative_base
try:
    from app.database import Base
except ImportError:
    from sqlalchemy.ext.declarative import declarative_base
    Base = declarative_base()


class APIKey(Base):
    """
    API Key for programmatic access to RISKCAST.
    
    Features:
    - Secure key generation with prefix for identification
    - Scope-based permissions
    - Usage tracking
    - Expiration support
    - Revocation support
    """
    
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Key identification
    key_hash = Column(String(64), unique=True, nullable=False, index=True)
    key_prefix = Column(String(12), nullable=False)  # First 12 chars for display (rsk_xxxxxxxx)
    
    # Metadata
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Ownership
    user_id = Column(String(255), index=True, nullable=True)
    organization_id = Column(String(255), index=True, nullable=True)
    
    # Permissions (JSON array of scopes)
    scopes = Column(Text, default='["*"]')  # Default: all permissions
    
    # Usage tracking
    last_used_at = Column(DateTime, nullable=True)
    request_count = Column(Integer, default=0)
    
    # Lifecycle
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    
    # Revocation
    revoked = Column(Boolean, default=False)
    revoked_at = Column(DateTime, nullable=True)
    revoked_reason = Column(String(255), nullable=True)
    
    # Rate limiting (per-key override)
    rate_limit_requests = Column(Integer, nullable=True)  # Override default rate limit
    rate_limit_window = Column(Integer, nullable=True)  # Window in seconds
    
    @staticmethod
    def generate_key() -> Tuple[str, str]:
        """
        Generate new API key.
        
        Returns:
            (key, hash) - The actual key (show once) and hash (store in DB)
        
        Key format: rsk_<32 random chars>
        Example: rsk_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
        """
        # Generate cryptographically secure random key
        random_part = secrets.token_urlsafe(24)  # 32 chars base64
        key = f"rsk_{random_part}"
        
        # Hash for storage (SHA-256)
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        return key, key_hash
    
    @staticmethod
    def hash_key(key: str) -> str:
        """Hash an API key for lookup."""
        return hashlib.sha256(key.encode()).hexdigest()
    
    def is_valid(self) -> bool:
        """Check if API key is still valid."""
        # Check revocation
        if self.revoked:
            return False
        
        # Check expiration
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        
        return True
    
    def get_scopes(self) -> List[str]:
        """Get list of permission scopes."""
        try:
            return json.loads(self.scopes) if self.scopes else []
        except json.JSONDecodeError:
            return []
    
    def set_scopes(self, scopes: List[str]):
        """Set permission scopes."""
        self.scopes = json.dumps(scopes)
    
    def has_scope(self, required_scope: str) -> bool:
        """
        Check if key has required scope.
        
        Supports wildcard (*) for all permissions.
        Supports prefix matching (e.g., 'risk:*' matches 'risk:analyze')
        """
        scopes = self.get_scopes()
        
        # Wildcard - all permissions
        if '*' in scopes:
            return True
        
        # Exact match
        if required_scope in scopes:
            return True
        
        # Prefix matching (e.g., 'risk:*' matches 'risk:analyze')
        for scope in scopes:
            if scope.endswith(':*'):
                prefix = scope[:-2]
                if required_scope.startswith(prefix):
                    return True
        
        return False
    
    def record_usage(self):
        """Record API key usage."""
        self.last_used_at = datetime.utcnow()
        self.request_count += 1
    
    def revoke(self, reason: Optional[str] = None):
        """Revoke the API key."""
        self.revoked = True
        self.revoked_at = datetime.utcnow()
        self.revoked_reason = reason
    
    def to_dict(self, include_key: bool = False, actual_key: Optional[str] = None) -> dict:
        """Convert to dictionary for API response."""
        result = {
            'id': self.id,
            'key_prefix': self.key_prefix,
            'name': self.name,
            'description': self.description,
            'scopes': self.get_scopes(),
            'user_id': self.user_id,
            'organization_id': self.organization_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'request_count': self.request_count,
            'revoked': self.revoked,
            'is_valid': self.is_valid()
        }
        
        # Only include actual key on creation
        if include_key and actual_key:
            result['key'] = actual_key
        
        return result
    
    @classmethod
    def create(
        cls,
        name: str,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        scopes: Optional[List[str]] = None,
        description: Optional[str] = None,
        expires_in_days: Optional[int] = None
    ) -> Tuple['APIKey', str]:
        """
        Create a new API key.
        
        Returns:
            (APIKey instance, actual key string)
        
        Note: The actual key is only returned once on creation!
        """
        # Generate key
        key, key_hash = cls.generate_key()
        
        # Calculate expiry
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        # Create instance
        api_key = cls(
            key_hash=key_hash,
            key_prefix=key[:12],  # "rsk_xxxxxxxx"
            name=name,
            description=description,
            user_id=user_id,
            organization_id=organization_id,
            scopes=json.dumps(scopes or ['*']),
            expires_at=expires_at
        )
        
        return api_key, key


# Available scopes for documentation
AVAILABLE_SCOPES = {
    '*': 'Full access to all endpoints',
    'risk:analyze': 'Run risk analysis',
    'risk:read': 'Read risk assessment results',
    'risk:scenarios': 'Run scenario simulations',
    'ai:chat': 'Use AI advisor chat',
    'ai:export': 'Export AI recommendations',
    'state:read': 'Read saved states',
    'state:write': 'Write/update states',
    'state:delete': 'Delete states',
    'admin:keys': 'Manage API keys',
    'admin:users': 'Manage users',
}
