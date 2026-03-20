from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = ""
    # Optional overrides read from .env (Pydantic loads these; os.environ alone is NOT set from .env).
    database_ssl: Optional[str] = Field(default=None, description="DATABASE_SSL: force on/off for asyncpg")
    database_ssl_verify: bool = Field(
        default=True,
        description="DATABASE_SSL_VERIFY: set false for local dev if SSL verify fails (e.g. macOS LibreSSL)",
    )

    @field_validator("database_ssl_verify", mode="before")
    @classmethod
    def _parse_database_ssl_verify(cls, v: object) -> bool:
        if v is None or v == "":
            return True
        if isinstance(v, bool):
            return v
        s = str(v).strip().lower()
        if s in ("0", "false", "no", "off"):
            return False
        return True

    # When True/False, force on/off. When None (unset / "auto"), resolve IPv4 DB host inside Docker only.
    database_prefer_ipv4: Optional[bool] = Field(
        default=None,
        description="DATABASE_PREFER_IPV4: prefer IPv4 for DB host (fixes Errno 99 from Docker to cloud Postgres)",
    )

    @field_validator("database_prefer_ipv4", mode="before")
    @classmethod
    def _parse_database_prefer_ipv4(cls, v: object) -> Optional[bool]:
        if v is None or v == "":
            return None
        if isinstance(v, bool):
            return v
        s = str(v).strip().lower()
        if s in ("auto",):
            return None
        if s in ("1", "true", "yes", "on"):
            return True
        if s in ("0", "false", "no", "off"):
            return False
        return None

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
