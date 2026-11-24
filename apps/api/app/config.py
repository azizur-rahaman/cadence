"""Application configuration loaded from environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+psycopg://cadence:cadence@db:5432/cadence"
    app_now: str = "2026-11-11T15:00:00Z"
    clock_mode: Literal["live", "frozen"] = "live"
    company_timezone: str = "America/Chicago"
    auth_secret: str = "cadence-local-dev-secret-change-me"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    seed_file: str = "seed/seed.json"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
