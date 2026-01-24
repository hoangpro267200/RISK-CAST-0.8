"""
Stub Oracle Provider
Returns explicit 'not configured' errors for unconfigured providers.
"""
from __future__ import annotations

from typing import Dict, List

from app.core.parametric.oracle_gateway import (
    OracleProvider,
    OracleQuery,
    OraclePayload,
    ValidationResult,
)
from app.core.parametric.exceptions import OracleNotConfiguredError


class StubOracleProvider(OracleProvider):
    """
    Stub provider that returns explicit 'not configured' errors.
    
    Use this as a placeholder for providers that are not yet configured.
    Provides clear error messages to guide configuration.
    """
    
    def __init__(self, source_name: str, configuration_instructions: str = ""):
        """
        Initialize stub provider.
        
        Args:
            source_name: Name of the oracle source (e.g., "tomorrow_io")
            configuration_instructions: Instructions for configuring the provider
        """
        self._source_name = source_name
        self._configuration_instructions = configuration_instructions or (
            f"Configure {source_name} credentials in settings."
        )
    
    @property
    def source_name(self) -> str:
        """Return the source name"""
        return self._source_name
    
    def is_configured(self) -> bool:
        """Stub provider is never configured"""
        return False
    
    async def fetch_event(self, query: OracleQuery) -> OraclePayload:
        """
        Raise OracleNotConfiguredError with clear message.
        
        Note: This method should never be called in production when properly configured.
        It exists to provide clear error messages when providers are not set up.
        
        Raises:
            OracleNotConfiguredError: Always, with configuration instructions
        """
        raise OracleNotConfiguredError(
            f"Oracle provider '{self._source_name}' is not configured. "
            f"{self._configuration_instructions}"
        )
    
    def validate(self, payload: OraclePayload) -> ValidationResult:
        """
        Validation always fails for stub provider.
        
        Args:
            payload: OraclePayload (unused)
            
        Returns:
            ValidationResult with error
        """
        result = ValidationResult(valid=False)
        result.add_error(
            f"Provider '{self._source_name}' is not configured. "
            f"{self._configuration_instructions}"
        )
        return result
    
    def normalize(self, payload: OraclePayload) -> dict:
        """
        Normalization always fails for stub provider.
        
        Args:
            payload: OraclePayload (unused)
            
        Raises:
            OracleNotConfiguredError: Always
        """
        raise OracleNotConfiguredError(
            f"Oracle provider '{self._source_name}' is not configured. "
            f"{self._configuration_instructions}"
        )


class TomorrowIOStubProvider(StubOracleProvider):
    """Stub provider specifically for Tomorrow.io"""
    
    def __init__(self):
        super().__init__(
            source_name="tomorrow_io",
            configuration_instructions=(
                "Configure Tomorrow.io API key in environment variables or settings. "
                "Set TOMORROW_IO_API_KEY to enable this provider."
            )
        )


class WeatherAPIStubProvider(StubOracleProvider):
    """Stub provider specifically for WeatherAPI"""
    
    def __init__(self):
        super().__init__(
            source_name="weather_api",
            configuration_instructions=(
                "Configure WeatherAPI key in environment variables or settings. "
                "Set WEATHER_API_KEY to enable this provider."
            )
        )
