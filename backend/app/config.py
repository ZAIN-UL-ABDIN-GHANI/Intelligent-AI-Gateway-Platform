"""Application configuration loaded from environment variables."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    gemma_base_url: str = "http://localhost:11434/v1"  # Ollama OpenAI-compatible endpoint
    gemma_model_name: str = "gemma3:4b"

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
    return Settings()
