"""Application configuration loaded from environment variables."""
import logging
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger("ai_gateway.config")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Core
    app_name: str = "AI Gateway"
    environment: str = "development"
    database_url: str = "sqlite:///./gateway.db"
    redis_url: str = "redis://localhost:6379/0"

    # Auth
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"

    # Provider keys (empty string => provider runs in mock mode)
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    google_api_key: str = ""
    gemma_base_url: str = "http://localhost:11434/v1"
    gemma_model_name: str = "gemma2:2b"

    # Provider timeouts (seconds)
    provider_timeout_ollama: int = 15
    provider_timeout_openai: int = 45
    provider_timeout_anthropic: int = 60
    provider_timeout_google: int = 45
    provider_max_retries: int = 2

    # Routing
    default_weight_quality: float = 0.4
    default_weight_cost: float = 0.3
    default_weight_latency: float = 0.2
    default_weight_budget: float = 0.1
    semantic_cache_threshold: float = 0.92

    # Rate limiting
    default_rate_limit_per_min: int = 60


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    _log_provider_status(settings)
    return settings


def _log_provider_status(settings: Settings) -> None:
    providers = {
        "anthropic": bool(settings.anthropic_api_key and settings.anthropic_api_key.strip()),
        "openai": bool(settings.openai_api_key and settings.openai_api_key.strip()),
        "google": bool(settings.google_api_key and settings.google_api_key.strip()),
        "ollama": True,
    }
    for name, configured in providers.items():
        if configured:
            logger.info("Provider %s: LIVE mode", name)
        else:
            logger.warning("Provider %s: MOCK mode (no API key)", name)
