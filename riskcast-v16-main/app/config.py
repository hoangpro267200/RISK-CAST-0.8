"""
Application Configuration
Centralized settings management for RISKCAST V3
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application
    APP_NAME: str = "RISKCAST V3"
    APP_VERSION: str = "3.0.0"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # API
    API_V3_PREFIX: str = "/api/v3"
    API_TITLE: str = "RISKCAST V3 API"
    API_DESCRIPTION: str = "Enterprise Insurance-Grade Risk Intelligence Platform"
    
    # Database
    DATABASE_URL: str = Field(
        default="sqlite:///./riskcast.db",
        env="DATABASE_URL"
    )
    DATABASE_ECHO: bool = Field(default=False, env="DATABASE_ECHO")
    DATABASE_POOL_SIZE: int = Field(default=10, env="DATABASE_POOL_SIZE")
    DATABASE_MAX_OVERFLOW: int = Field(default=20, env="DATABASE_MAX_OVERFLOW")
    
    # Security
    SECRET_KEY: str = Field(
        default="change-me-in-production",
        env="SECRET_KEY"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    
    # CORS
    ALLOWED_ORIGINS: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:8000", "http://127.0.0.1:8000"],
        env="ALLOWED_ORIGINS"
    )
    
    # Observability
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    ENABLE_OPENTELEMETRY: bool = Field(default=False, env="ENABLE_OPENTELEMETRY")
    ENABLE_PROMETHEUS: bool = Field(default=False, env="ENABLE_PROMETHEUS")
    OTEL_EXPORTER_OTLP_ENDPOINT: Optional[str] = Field(
        default=None,
        env="OTEL_EXPORTER_OTLP_ENDPOINT"
    )
    
    # Risk Engine
    RISK_ENGINE_VERSION: str = Field(default="v3", env="RISK_ENGINE_VERSION")
    MC_ITERATIONS_DEFAULT: int = Field(default=50000, env="MC_ITERATIONS_DEFAULT")
    MC_ITERATIONS_MIN: int = Field(default=10000, env="MC_ITERATIONS_MIN")
    MC_ITERATIONS_MAX: int = Field(default=100000, env="MC_ITERATIONS_MAX")
    DETERMINISTIC_SEEDING: bool = Field(default=True, env="DETERMINISTIC_SEEDING")
    
    # Audit & Compliance
    AUDIT_RETENTION_DAYS: int = Field(default=2555, env="AUDIT_RETENTION_DAYS")  # 7 years
    ENABLE_AUDIT_LOGGING: bool = Field(default=True, env="ENABLE_AUDIT_LOGGING")
    AUDIT_SIGNING_KEY: str = Field(
        default="your-secret-signing-key-change-in-production",
        env="AUDIT_SIGNING_KEY",
        description="HMAC signing key for immutable audit ledger",
    )
    AUDIT_CHAIN_VERIFICATION_INTERVAL: int = Field(
        default=3600,
        env="AUDIT_CHAIN_VERIFICATION_INTERVAL",
        description="Verify hash chain every N seconds (0 = disabled)",
    )
    
    # Multi-Tenancy
    DEFAULT_TENANT_ID: Optional[str] = Field(default=None, env="DEFAULT_TENANT_ID")
    TENANT_ISOLATION_ENABLED: bool = Field(default=True, env="TENANT_ISOLATION_ENABLED")
    
    # External APIs
    TOMORROW_IO_API_KEY: Optional[str] = Field(default=None, env="TOMORROW_IO_API_KEY")
    TOMORROW_IO_RATE_LIMIT: int = Field(default=1000, env="TOMORROW_IO_RATE_LIMIT", description="Requests per day")
    MARINETRAFFIC_API_KEY: Optional[str] = Field(default=None, env="MARINETRAFFIC_API_KEY")
    MARINE_TRAFFIC_API_KEY: Optional[str] = Field(default=None, env="MARINE_TRAFFIC_API_KEY")  # Alias
    PROJECT44_API_KEY: Optional[str] = Field(default=None, env="PROJECT44_API_KEY")
    PROJECT44_CLIENT_ID: Optional[str] = Field(default=None, env="PROJECT44_CLIENT_ID")
    PROJECT44_CLIENT_SECRET: Optional[str] = Field(default=None, env="PROJECT44_CLIENT_SECRET")
    ICEYE_API_KEY: Optional[str] = Field(default=None, env="ICEYE_API_KEY")
    FLOODBASE_API_KEY: Optional[str] = Field(default=None, env="FLOODBASE_API_KEY")
    
    # Data Quality Thresholds
    MIN_DATA_QUALITY_FOR_UNDERWRITING: str = Field(
        default="CACHED",
        env="MIN_DATA_QUALITY_FOR_UNDERWRITING",
        description="Minimum data quality for underwriting: REAL_TIME, CACHED, STALE, FALLBACK"
    )
    ALLOW_FALLBACK_DATA_IN_RISK: bool = Field(
        default=False,
        env="ALLOW_FALLBACK_DATA_IN_RISK",
        description="Reject risk calculation if only fallback data available"
    )
    
    # Parametric Insurance Safety Guards
    PARAMETRIC_PAYOUTS_ENABLED: bool = Field(
        default=False,
        env="PARAMETRIC_PAYOUTS_ENABLED",
        description="Enable parametric payouts (default: False for safety)"
    )
    REQUIRED_ORACLE_SOURCES: list[str] = Field(
        default_factory=lambda: ["weather"],
        env="REQUIRED_ORACLE_SOURCES",
        description="List of oracle sources that must be configured before payouts"
    )
    
    # File Storage
    EVIDENCE_STORAGE_PATH: str = Field(
        default="./data/evidence",
        env="EVIDENCE_STORAGE_PATH"
    )
    EVIDENCE_BUCKET: str = Field(
        default="riskcast-evidence",
        env="EVIDENCE_BUCKET"
    )
    MAX_FILE_SIZE_MB: int = Field(default=50, env="MAX_FILE_SIZE_MB")
    
    # Workers
    CELERY_BROKER_URL: Optional[str] = Field(default=None, env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: Optional[str] = Field(default=None, env="CELERY_RESULT_BACKEND")
    
    # Auth-related settings (handled separately in app.auth_config.auth, but defined here to avoid validation errors)
    AUTH_ENABLED: Optional[str] = Field(default=None, env="AUTH_ENABLED")
    SESSION_SECRET: Optional[str] = Field(default=None, env="SESSION_SECRET")
    SESSION_EXPIRE_HOURS: Optional[str] = Field(default=None, env="SESSION_EXPIRE_HOURS")
    COOKIE_SECURE: Optional[str] = Field(default=None, env="COOKIE_SECURE")
    COOKIE_SAMESITE: Optional[str] = Field(default=None, env="COOKIE_SAMESITE")
    PROTECT_INPUT: Optional[str] = Field(default=None, env="PROTECT_INPUT")
    PROTECT_RESULTS: Optional[str] = Field(default=None, env="PROTECT_RESULTS")
    INVITE_ONLY: Optional[str] = Field(default=None, env="INVITE_ONLY")
    
    @validator("ALLOWED_ORIGINS", "REQUIRED_ORACLE_SOURCES", pre=True)
    def parse_list_fields(cls, v):
        if v is None or v == "":
            return []
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v
    
    @validator("SECRET_KEY")
    def validate_secret_key(cls, v, values):
        if values.get("ENVIRONMENT") == "production" and v == "change-me-in-production":
            raise ValueError("SECRET_KEY must be set in production")
        return v
    
    @validator("DATABASE_URL")
    def validate_database_url(cls, v, values):
        if values.get("ENVIRONMENT") == "production" and "localhost" in v:
            raise ValueError("DATABASE_URL must not use localhost in production")
        return v
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


# Global settings instance
settings = Settings()
