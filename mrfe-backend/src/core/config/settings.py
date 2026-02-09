"""Configuration management for dev/staging/prod."""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    """Application environment."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class Settings(BaseSettings):
    """Strongly typed runtime configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        protected_namespaces=(),
    )

    app_name: str = "MRFE Backend"
    app_version: str = "2.0.0"
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False
    api_prefix: str = "/api/v1"

    database_url: str = "sqlite+aiosqlite:///./mrfe.db"
    database_echo: bool = False
    database_pool_size: int = 20
    database_max_overflow: int = 40

    mongo_url: str = "mongodb://localhost:27017"
    mongo_database: str = "mrfe"
    mongo_news_collection: str = "news_events"
    newsapi_api_key: str | None = None
    newsapi_base_url: str = "https://newsapi.org/v2"
    newsapi_query: str = "markets OR stocks OR economy OR earnings"
    newsapi_sources: str = ""
    newsapi_language: str = "en"
    newsapi_page_size: int = 50

    fred_api_key: str | None = None

    redis_url: str = "redis://localhost:6379/0"
    redis_ttl: int = 3600

    jwt_algorithm: str = "RS256"
    jwt_private_key: str = Field(default="dev-private-key")
    jwt_public_key: str = Field(default="dev-public-key")
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30
    service_api_keys_csv: str = ""

    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    rate_limit_per_minute: int = 120
    sentry_dsn: str | None = None
    otel_enabled: bool = True
    log_level: str = "INFO"
    llm_provider: str = "openrouter"
    anthropic_api_key: str | None = None
    anthropic_base_url: str = "https://api.anthropic.com"
    anthropic_model: str = "claude-3-opus-latest"
    anthropic_timeout_seconds: float = 30.0
    anthropic_version: str = "2023-06-01"
    openrouter_api_key: str | None = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_http_referer: str = "https://mrfe.local"
    openrouter_x_title: str = "MRFE Backend"
    openrouter_primary_model: str = "openai/gpt-4o-mini"
    openrouter_fallback_model: str = "openai/gpt-4o-mini"
    openrouter_timeout_seconds: float = 30.0
    openrouter_max_retries: int = 2
    openrouter_monthly_budget_usd: float = 0.0
    openrouter_max_cost_usd_per_request: float = 0.0
    model_registry_path: str = "storage/model_registry.json"
    drift_alert_threshold: float = 0.18
    ensemble_regime_weight: float = 0.35
    event_classifier_enabled: bool = True
    event_classifier_model: str = "ProsusAI/finbert"
    event_classifier_device: int = -1
    event_classifier_local_files_only: bool = True
    fingerprint_regressor_path: str = "src/infrastructure/ml/models/fingerprint_regressor.pkl"
    fingerprint_vector_store_path: str = "storage/fingerprint_vectors.json"
    fingerprint_vector_dimension: int = 8
    similarity_min_score: float = 0.6
    data_collection_cron_hour: int = 2
    data_retention_days: int = 365
    data_retention_glob: str = "data/**/*"
    data_dir: str = "data"
    alphavantage_api_key: str | None = None
    alphavantage_base_url: str = "https://www.alphavantage.co/query"
    alphavantage_page_size: int = 50

    @property
    def is_production(self) -> bool:
        """Return true for production environment."""
        return self.environment == Environment.PRODUCTION

    @property
    def service_api_keys(self) -> list[str]:
        """Return configured service API keys from comma-separated env value."""
        return [item.strip() for item in self.service_api_keys_csv.split(",") if item.strip()]

    @field_validator("jwt_algorithm")
    @classmethod
    def enforce_rs256(cls, value: str) -> str:
        """Force RS256 algorithm for security policy compliance."""
        return "RS256" if value.upper() != "RS256" else value.upper()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cache settings instance."""
    return Settings()


settings = get_settings()
