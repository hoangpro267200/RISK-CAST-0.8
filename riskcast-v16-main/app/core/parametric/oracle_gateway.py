"""
Oracle Gateway Interface
Production-grade interface for oracle providers with validation and normalization.
"""
from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
import json

from app.core.parametric.exceptions import OracleNotConfiguredError, OracleValidationError


@dataclass
class OracleQuery:
    """Query parameters for fetching oracle data"""
    location: Optional[str] = None  # e.g., "USNYC", "GBLON"
    timestamp: Optional[datetime] = None  # Specific time to query
    date_range: Optional[tuple[datetime, datetime]] = None  # Date range
    parameters: Dict[str, Any] = field(default_factory=dict)  # Additional query parameters


@dataclass
class OraclePayload:
    """Payload returned from oracle provider"""
    source: str
    captured_at: datetime
    payload: dict
    payload_hash: str
    raw_response: Optional[bytes] = None
    
    @classmethod
    def from_dict(cls, source: str, payload: dict, raw_response: Optional[bytes] = None) -> 'OraclePayload':
        """
        Create OraclePayload from dictionary.
        
        Computes payload_hash from canonical JSON representation.
        Ensures payload includes source information for validation.
        """
        # Ensure payload includes source for validation
        if "data_source" not in payload and "source" not in payload:
            payload["data_source"] = source
        
        # Canonical JSON serialization for hash
        canonical_json = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        payload_hash = hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()
        
        return cls(
            source=source,
            captured_at=datetime.utcnow(),
            payload=payload,
            payload_hash=payload_hash,
            raw_response=raw_response
        )


@dataclass
class ValidationResult:
    """Result of payload validation"""
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def add_error(self, message: str) -> None:
        """Add a validation error"""
        self.errors.append(message)
        self.valid = False
    
    def add_warning(self, message: str) -> None:
        """Add a validation warning"""
        self.warnings.append(message)


class OracleProvider(ABC):
    """
    Abstract base class for oracle providers.
    
    Each provider must implement:
    - fetch_event: Fetch data from the oracle source
    - validate: Validate the payload structure and content
    - normalize: Normalize payload to standard format
    - source_name: Property returning the provider name
    """
    
    @property
    @abstractmethod
    def source_name(self) -> str:
        """
        Return the source name for this provider.
        
        Examples: "tomorrow_io", "weather_api", "custom_oracle"
        """
        pass
    
    @abstractmethod
    async def fetch_event(self, query: OracleQuery) -> OraclePayload:
        """
        Fetch event data from the oracle source.
        
        Args:
            query: OracleQuery with location, timestamp, etc.
            
        Returns:
            OraclePayload with fetched data
            
        Raises:
            OracleNotConfiguredError: If provider is not configured
            OracleFetchError: If fetch operation fails
        """
        pass
    
    @abstractmethod
    def validate(self, payload: OraclePayload) -> ValidationResult:
        """
        Validate oracle payload structure and content.
        
        Args:
            payload: OraclePayload to validate
            
        Returns:
            ValidationResult with validation status and errors/warnings
        """
        pass
    
    @abstractmethod
    def normalize(self, payload: OraclePayload) -> dict:
        """
        Normalize oracle payload to standard format.
        
        Args:
            payload: OraclePayload to normalize
            
        Returns:
            Normalized dictionary in standard format
        """
        pass
    
    def is_configured(self) -> bool:
        """
        Check if provider is configured and ready to use.
        
        Default implementation returns True. Override in subclasses
        to check for required configuration (API keys, etc.).
        
        Returns:
            True if configured, False otherwise
        """
        return True


class OracleGateway:
    """
    Gateway for managing multiple oracle providers.
    
    Provides unified interface for fetching data from different
    oracle sources with validation and normalization.
    """
    
    def __init__(self):
        """Initialize gateway with empty provider registry"""
        self.providers: Dict[str, OracleProvider] = {}
    
    def register_provider(self, provider: OracleProvider) -> None:
        """
        Register an oracle provider.
        
        Args:
            provider: OracleProvider instance to register
            
        Raises:
            ValueError: If provider source_name conflicts with existing provider
        """
        source_name = provider.source_name
        if source_name in self.providers:
            raise ValueError(f"Provider '{source_name}' is already registered")
        
        self.providers[source_name] = provider
    
    def unregister_provider(self, source_name: str) -> None:
        """
        Unregister an oracle provider.
        
        Args:
            source_name: Source name of provider to unregister
        """
        if source_name in self.providers:
            del self.providers[source_name]
    
    def get_provider(self, source_name: str) -> Optional[OracleProvider]:
        """
        Get provider by source name.
        
        Args:
            source_name: Source name of provider
            
        Returns:
            OracleProvider instance or None if not found
        """
        return self.providers.get(source_name)
    
    def list_providers(self) -> List[str]:
        """
        List all registered provider source names.
        
        Returns:
            List of source names
        """
        return list(self.providers.keys())
    
    async def fetch(
        self,
        source: str,
        query: OracleQuery
    ) -> OraclePayload:
        """
        Fetch data from specified oracle provider.
        
        Args:
            source: Source name of provider
            query: OracleQuery with query parameters
            
        Returns:
            OraclePayload with fetched data
            
        Raises:
            OracleNotConfiguredError: If provider not registered or not configured
            OracleFetchError: If fetch operation fails
        """
        if source not in self.providers:
            raise OracleNotConfiguredError(
                f"Oracle provider '{source}' is not registered. "
                f"Available providers: {', '.join(self.list_providers())}"
            )
        
        provider = self.providers[source]
        
        # Check if provider is configured
        if not provider.is_configured():
            raise OracleNotConfiguredError(
                f"Oracle provider '{source}' is not configured. "
                f"Please configure the provider before use."
            )
        
        # Fetch data
        return await provider.fetch_event(query)
    
    async def fetch_and_validate(
        self,
        source: str,
        query: OracleQuery
    ) -> tuple[OraclePayload, ValidationResult]:
        """
        Fetch data and validate it.
        
        Args:
            source: Source name of provider
            query: OracleQuery with query parameters
            
        Returns:
            Tuple of (OraclePayload, ValidationResult)
            
        Raises:
            OracleNotConfiguredError: If provider not registered or not configured
            OracleFetchError: If fetch operation fails
            OracleValidationError: If validation fails
        """
        payload = await self.fetch(source, query)
        validation = self.providers[source].validate(payload)
        
        if not validation.valid:
            raise OracleValidationError(
                f"Validation failed for provider '{source}': {', '.join(validation.errors)}"
            )
        
        return payload, validation
    
    async def fetch_and_normalize(
        self,
        source: str,
        query: OracleQuery
    ) -> dict:
        """
        Fetch data, validate, and normalize it.
        
        Args:
            source: Source name of provider
            query: OracleQuery with query parameters
            
        Returns:
            Normalized dictionary in standard format
            
        Raises:
            OracleNotConfiguredError: If provider not registered or not configured
            OracleFetchError: If fetch operation fails
            OracleValidationError: If validation fails
        """
        payload, validation = await self.fetch_and_validate(source, query)
        return self.providers[source].normalize(payload)
