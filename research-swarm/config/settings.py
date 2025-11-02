from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional
import os

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # API Keys
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    serpapi_api_key: Optional[str] = Field(default=None, alias="SERPAPI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")

    # Infrastructure
    redis_url: str = Field(default="redis://localhost:6379", alias="REDIS_URL")
    tailscale_auth_key: Optional[str] = Field(default=None, alias="TAILSCALE_AUTH_KEY")
    repository_path: str = Field(default="/home/user/research-output", alias="REPO_PATH")

    # Execution Limits
    max_iterations: int = Field(default=10, alias="MAX_ITERATIONS")
    research_timeout: int = Field(default=900, alias="RESEARCH_TIMEOUT")  # 15 minutes
    build_timeout: int = Field(default=1800, alias="BUILD_TIMEOUT")  # 30 minutes

    # Notification
    email_smtp_server: str = Field(default="smtp.gmail.com", alias="SMTP_SERVER")
    email_from: Optional[str] = Field(default=None, alias="EMAIL_FROM")
    email_to: Optional[str] = Field(default=None, alias="EMAIL_TO")
    discord_webhook: Optional[str] = Field(default=None, alias="DISCORD_WEBHOOK")

settings = Settings()