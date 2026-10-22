"""Application-wide settings loaded from environment variables.

This module centralizes configuration so that no other module needs to
call `os.getenv` directly. All configuration values are validated eagerly
at import time via Pydantic so misconfiguration fails fast at startup.
"""

from __future__ import annotations

from functools import lru_cache

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    """Typed application settings sourced from environment variables / .env.

    Attributes:
        google_api_key: API key used to authenticate with the Gemini API.
        gemini_model: The Gemini model identifier to use for all agents.
        llm_temperature: Sampling temperature applied to the shared LLM client.
        shortlist_score_threshold: Minimum total score (inclusive) required
            for a candidate to be automatically shortlisted.
        manual_review_score_threshold: Minimum total score (inclusive)
            required for a candidate to be routed to manual review instead
            of being rejected outright.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    google_api_key: str = Field(..., alias="GOOGLE_API_KEY")
    gemini_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_MODEL")
    llm_temperature: float = Field(default=0.2, alias="LLM_TEMPERATURE")

    shortlist_score_threshold: float = Field(default=80.0)
    manual_review_score_threshold: float = Field(default=60.0)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached, process-wide `Settings` instance.

    Using an `lru_cache` avoids re-reading and re-validating environment
    variables on every call while still allowing tests to construct their
    own `Settings` instances directly when needed.

    Returns:
        The singleton `Settings` instance for this process.
    """

    return Settings()
