"""Configuration management via pydantic-settings, loaded from .env."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings populated from environment variables and .env file."""

    model_config = SettingsConfigDict(env_prefix="", env_file=".env", env_file_encoding="utf-8")

    # Required
    anthropic_api_key: SecretStr

    # Model
    ag2_model: str = "claude-opus-4-6"

    # Pipeline
    max_refinement_rounds: int = 3
    quality_threshold: float = 0.8
    output_dir: Path = Path("./output")
    notebook_style: Literal["narrative", "technical", "executive"] = "narrative"
    max_research_depth: Literal["minimal", "standard", "deep"] = "standard"
    log_agent_conversations: bool = False

    # Optional API keys
    sec_edgar_user_agent: Optional[str] = None
    news_api_key: Optional[SecretStr] = None
    alpha_vantage_api_key: Optional[SecretStr] = None
    fred_api_key: Optional[SecretStr] = None
    github_token: Optional[SecretStr] = None


def get_settings() -> Settings:
    """Create and return a validated Settings instance."""
    return Settings()  # type: ignore[call-arg]
