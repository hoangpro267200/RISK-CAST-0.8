from functools import lru_cache
from pydantic import BaseSettings


class Settings(BaseSettings):
    api_prefix: str = "/api/v1"
    cors_origins: str = "*"
    rate_limit_per_second: int = 20


@lru_cache()
def get_settings() -> Settings:
    return Settings()




