"""
Centralized settings loader for ai-service.
Mirrors the role of backend/src/shared/logger/env.js — one place that
reads and validates environment variables, nothing else touches os.environ directly.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongodb_uri: str
    mongodb_db_name: str = "quantai"
    env: str = "development"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    """Cached so we only parse .env once per process."""
    return Settings()