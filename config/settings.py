from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Keys
    openai_api_key: str
    serpapi_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None

    # Infrastructure
    redis_url: str = "redis://localhost:6379"
    tailscale_auth_key: Optional[str] = None
    repository_path: str = "./outputs/research-repository"

    # Execution Limits
    max_iterations: int = 10
    research_timeout: int = 900
    build_timeout: int = 1800

    # Notification
    email_smtp_server: str = "smtp.gmail.com"
    email_smtp_port: int = 587
    email_from: Optional[str] = None
    email_to: Optional[str] = None
    email_password: Optional[str] = None
    discord_webhook: Optional[str] = None

    # LLM Configuration
    default_model: str = "gpt-4"
    temperature: float = 0.1

    # Application
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file="config/.env",
        env_file_encoding="utf-8",
        extra="allow"
    )


settings = Settings()
