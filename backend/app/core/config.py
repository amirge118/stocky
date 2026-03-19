from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = ""

    # JWT Authentication
    secret_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # AI Services
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # Financial Data
    fmp_api_key: str = ""

    # CORS
    cors_origins: str = "http://localhost:3000"

    # Telegram notifications
    telegram_token: str = ""
    telegram_chat_id: str = ""

    # Celery
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/1"

    # Optional
    redis_url: Optional[str] = None
    sentry_dsn: Optional[str] = None
    environment: str = "development"
    log_level: str = "INFO"
    log_request_payload: bool = True
    log_response_payload: bool = True
    log_payload_max_length: int = 2000

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins string into list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
