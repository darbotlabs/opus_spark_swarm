"""Tests for opus_spark_swarm.config.Settings."""

from __future__ import annotations

from pathlib import Path

import pytest


class TestSettingsDefaults:
    """Verify Settings loads with correct defaults."""

    def test_default_model(self, settings):
        assert settings.ag2_model == "claude-opus-4-6"

    def test_default_quality_threshold(self, settings):
        assert settings.quality_threshold == 0.8

    def test_default_output_dir(self, settings):
        assert settings.output_dir == Path("./output")

    def test_output_dir_is_path(self, settings):
        assert isinstance(settings.output_dir, Path)

    def test_default_notebook_style(self, settings):
        assert settings.notebook_style == "narrative"

    def test_default_max_refinement_rounds(self, settings):
        assert settings.max_refinement_rounds == 3

    def test_default_research_depth(self, settings):
        assert settings.max_research_depth == "standard"

    def test_log_conversations_default_false(self, settings):
        assert settings.log_agent_conversations is False


class TestSettingsCustomValues:
    """Verify Settings picks up custom env values."""

    def test_custom_model(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
        monkeypatch.setenv("AG2_MODEL", "claude-sonnet-4-20250514")
        from opus_spark_swarm.config import Settings
        s = Settings()
        assert s.ag2_model == "claude-sonnet-4-20250514"

    def test_custom_quality_threshold(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
        monkeypatch.setenv("QUALITY_THRESHOLD", "0.95")
        from opus_spark_swarm.config import Settings
        s = Settings()
        assert s.quality_threshold == 0.95

    def test_custom_output_dir(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
        monkeypatch.setenv("OUTPUT_DIR", "/tmp/custom_out")
        from opus_spark_swarm.config import Settings
        s = Settings()
        assert s.output_dir == Path("/tmp/custom_out")

    def test_anthropic_key_is_secret(self, settings):
        assert settings.anthropic_api_key.get_secret_value() == "sk-test-dummy-key-1234"
        assert "sk-test-dummy-key-1234" not in str(settings.anthropic_api_key)

    def test_optional_keys_present(self, settings):
        assert settings.news_api_key is not None
        assert settings.alpha_vantage_api_key is not None
        assert settings.fred_api_key is not None
        assert settings.github_token is not None

    def test_optional_keys_none_by_default(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
        # Clear optional keys
        monkeypatch.delenv("NEWS_API_KEY", raising=False)
        monkeypatch.delenv("ALPHA_VANTAGE_API_KEY", raising=False)
        monkeypatch.delenv("FRED_API_KEY", raising=False)
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("SEC_EDGAR_USER_AGENT", raising=False)
        from opus_spark_swarm.config import Settings
        s = Settings()
        assert s.news_api_key is None
        assert s.sec_edgar_user_agent is None
