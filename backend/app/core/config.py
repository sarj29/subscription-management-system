"""
Application configuration loaded from environment variables via pydantic-settings.
Never hardcode secrets here — all sensitive values must come from the .env file.
"""
from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]
class Settings(BaseSettings):
    """Central settings object.  All fields are read from environment variables."""

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------
    app_name: str = "Brightloop Subscription Management"
    environment: str = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------
    database_url: str = "postgresql+psycopg://postgres:change_me@localhost:5432/subscription_db"

    # ------------------------------------------------------------------
    # Security / JWT
    # ------------------------------------------------------------------
    secret_key: str = "INSECURE_DEFAULT_CHANGE_ME"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # ------------------------------------------------------------------
    # CORS
    # ------------------------------------------------------------------
    frontend_url: str = "http://localhost:5173"
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins(self) -> List[str]:
        """Return CORS origins as a list, splitting the comma-separated string."""
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @property
    def is_development(self) -> bool:
        return self.environment.lower() == "development"

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (singleton pattern)."""
    return Settings()


# Module-level convenience alias used throughout the app
settings = get_settings()
