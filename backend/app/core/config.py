"""Application-wide settings for the FastAPI backend.

Centralizes all environment-driven configuration (database URL, JWT
secrets, token lifetimes, CORS origins, allowed hosts) behind a single
cached `Settings` object so no other module reads `os.environ` directly.
"""

from __future__ import annotations

import json
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_host_list(value: object) -> list[str]:
    """Accept JSON arrays or comma-separated host/origin strings."""

    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    if not text:
        return []
    if text.startswith("["):
        parsed = json.loads(text)
        return [str(item).strip() for item in parsed if str(item).strip()]
    return [part.strip() for part in text.split(",") if part.strip()]


class Settings(BaseSettings):
    """Typed configuration sourced from environment variables / `.env`."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = Field(default="Hiring AI Backend")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    api_v1_prefix: str = Field(default="/api/v1")

    database_url: str = Field(
        default="sqlite+aiosqlite:///./hiring_ai.sqlite",
        alias="DATABASE_URL",
    )

    jwt_secret_key: str = Field(..., alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")
    password_reset_token_expire_minutes: int = Field(
        default=30, alias="PASSWORD_RESET_TOKEN_EXPIRE_MINUTES"
    )

    frontend_url: str = Field(default="http://localhost:3000", alias="FRONTEND_URL")
    # Stored as strings so Render CSV/URL values are not JSON-decoded on boot.
    cors_allow_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        alias="CORS_ALLOW_ORIGINS",
    )
    allowed_hosts: str = Field(
        default="localhost,127.0.0.1,test,testserver",
        alias="ALLOWED_HOSTS",
    )

    upload_dir: str = Field(default="./uploads", alias="UPLOAD_DIR")
    max_upload_size_mb: int = Field(default=10, alias="MAX_UPLOAD_SIZE_MB")

    sendliberty_api_key: str | None = Field(default=None, alias="SENDLIBERTY_API_KEY")
    sl_api_key: str | None = Field(default=None, alias="SL_API_KEY")
    resend_api_key: str | None = Field(default=None, alias="RESEND_API_KEY")
    email_from: str = Field(default="Talent Lens <noreply@localhost>", alias="EMAIL_FROM")
    smtp_host: str | None = Field(default=None, alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_username: str | None = Field(default=None, alias="SMTP_USERNAME")
    smtp_password: str | None = Field(default=None, alias="SMTP_PASSWORD")
    email_otp_expire_minutes: int = Field(default=10, alias="EMAIL_OTP_EXPIRE_MINUTES")
    email_link_expire_minutes: int = Field(default=30, alias="EMAIL_LINK_EXPIRE_MINUTES")
    email_otp_max_attempts: int = Field(default=5, alias="EMAIL_OTP_MAX_ATTEMPTS")
    email_send_limit: int = Field(default=3, alias="EMAIL_SEND_LIMIT")
    email_send_window_minutes: int = Field(default=15, alias="EMAIL_SEND_WINDOW_MINUTES")

    @field_validator("database_url", mode="before")
    @classmethod
    def async_postgres_url(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        url = value
        if url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://") :]
        if url.startswith("postgresql://") and "+asyncpg" not in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def sendliberty_key(self) -> str | None:
        return self.sendliberty_api_key or self.sl_api_key

    @property
    def cors_origins(self) -> list[str]:
        origins = _parse_host_list(self.cors_allow_origins)
        frontend = self.frontend_url.rstrip("/")
        if frontend and frontend not in origins:
            origins.append(frontend)
        return origins

    @property
    def trusted_hosts(self) -> list[str]:
        hosts = _parse_host_list(self.allowed_hosts)
        if "*" in hosts:
            return ["*"]
        extras = [
            "localhost",
            "127.0.0.1",
            ".onrender.com",
            ".up.railway.app",
        ]
        for extra in extras:
            if extra not in hosts:
                hosts.append(extra)
        return hosts


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached, process-wide `Settings` instance."""

    return Settings()
