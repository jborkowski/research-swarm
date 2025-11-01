from pydantic import BaseSettings, Field
from typing import Optional
import os

class Settings(BaseSettings):
    # API Keys
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    serpapi_api_key: Optional[str] = Field(None, env="SERPAPI_API_KEY")
    anthropic_api_key: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    
    # Infrastructure
    redis_url: str = Field("redis://localhost:6379", env="REDIS_URL")
    tailscale_auth_key: str = Field(..., env="TAILSCALE_AUTH_KEY")
    repository_path: str = Field("/home/user/research-output", env="REPO_PATH")
    
    # Execution Limits
    max_iterations: int = Field(10, env="MAX_ITERATIONS")
    research_timeout: int = Field(900, env="RESEARCH_TIMEOUT")  # 15 minutes
    build_timeout: int = Field(1800, env="BUILD_TIMEOUT")  # 30 minutes
    
    # Notification
    email_smtp_server: str = Field("smtp.gmail.com", env="SMTP_SERVER")
    email_from: str = Field(..., env="EMAIL_FROM")
    email_to: str = Field(..., env="EMAIL_TO")
    discord_webhook: Optional[str] = Field(None, env="DISCORD_WEBHOOK")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()