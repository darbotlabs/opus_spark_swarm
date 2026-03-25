"""Tests for opus_spark_swarm.agents.base."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestBuildLlmConfig:
    def test_returns_dict(self, settings):
        from opus_spark_swarm.agents.base import build_llm_config
        config = build_llm_config(settings)
        assert isinstance(config, dict)
        assert "config_list" in config

    def test_config_list_has_model(self, settings):
        from opus_spark_swarm.agents.base import build_llm_config
        config = build_llm_config(settings)
        entry = config["config_list"][0]
        assert entry["model"] == "claude-opus-4-6"
        assert entry["api_type"] == "anthropic"

    def test_api_key_resolved(self, settings):
        from opus_spark_swarm.agents.base import build_llm_config
        config = build_llm_config(settings)
        assert config["config_list"][0]["api_key"] == "sk-test-dummy-key-1234"

    def test_custom_model(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
        monkeypatch.setenv("AG2_MODEL", "claude-sonnet-4-20250514")
        from opus_spark_swarm.config import Settings
        from opus_spark_swarm.agents.base import build_llm_config
        s = Settings()
        config = build_llm_config(s)
        assert config["config_list"][0]["model"] == "claude-sonnet-4-20250514"


class TestCreateAgent:
    @patch("opus_spark_swarm.agents.base.ConversableAgent")
    def test_returns_agent(self, mock_agent_cls, settings):
        mock_agent_cls.return_value = MagicMock()
        from opus_spark_swarm.agents.base import create_agent
        agent = create_agent("TestAgent", "You are a test agent.", settings)
        mock_agent_cls.assert_called_once()
        assert agent is not None

    @patch("opus_spark_swarm.agents.base.ConversableAgent")
    def test_system_message_prepends_base(self, mock_agent_cls, settings):
        mock_agent_cls.return_value = MagicMock()
        from opus_spark_swarm.agents.base import create_agent, BASE_SYSTEM_PROMPT
        create_agent("TestAgent", "Custom prompt.", settings)
        call_kwargs = mock_agent_cls.call_args[1]
        assert BASE_SYSTEM_PROMPT in call_kwargs["system_message"]
        assert "Custom prompt." in call_kwargs["system_message"]

    @patch("opus_spark_swarm.agents.base.ConversableAgent")
    def test_human_input_mode_default(self, mock_agent_cls, settings):
        mock_agent_cls.return_value = MagicMock()
        from opus_spark_swarm.agents.base import create_agent
        create_agent("TestAgent", "test", settings)
        call_kwargs = mock_agent_cls.call_args[1]
        assert call_kwargs["human_input_mode"] == "NEVER"

    @patch("opus_spark_swarm.agents.base.ConversableAgent")
    def test_extra_llm_config(self, mock_agent_cls, settings):
        mock_agent_cls.return_value = MagicMock()
        from opus_spark_swarm.agents.base import create_agent
        create_agent("TestAgent", "test", settings, extra_llm_config={"temperature": 0.5})
        call_kwargs = mock_agent_cls.call_args[1]
        assert call_kwargs["llm_config"]["temperature"] == 0.5

    @patch("opus_spark_swarm.agents.base.ConversableAgent")
    def test_agent_name(self, mock_agent_cls, settings):
        mock_agent_cls.return_value = MagicMock()
        from opus_spark_swarm.agents.base import create_agent
        create_agent("MySpecialAgent", "test", settings)
        call_kwargs = mock_agent_cls.call_args[1]
        assert call_kwargs["name"] == "MySpecialAgent"
