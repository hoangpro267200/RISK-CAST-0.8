from functools import lru_cache
import os
from typing import Optional

# Use os.getenv instead of BaseSettings to avoid pydantic-settings dependency
# This is a simple config module, not using Pydantic models

class Settings:
    """Simple settings class using environment variables"""
    def __init__(self):
        self.api_prefix: str = os.getenv("API_PREFIX", "/api/v1")
        self.cors_origins: str = os.getenv("CORS_ORIGINS", "*")
        self.rate_limit_per_second: int = int(os.getenv("RATE_LIMIT_PER_SECOND", "20"))


@lru_cache()
def get_settings() -> Settings:
    return Settings()




