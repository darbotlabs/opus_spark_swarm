"""Tests for the swarm router module."""

import pytest

from opus_spark_swarm.swarm.router import SwarmRouter, RoutingResult, INTENT_LAYER_MAP
from opus_spark_swarm.swarm.registry import SwarmRegistry


@pytest.fixture()
def registry() -> SwarmRegistry:
    return SwarmRegistry.load()


@pytest.fixture()
def settings():
    """Minimal settings for router tests (AG2 not actually invoked)."""
    import os
    os.environ.setdefault("ANTHROPIC_API_KEY", "sk-test-key-for-unit-tests")
    from opus_spark_swarm.config import get_settings
    return get_settings()


class TestClassify:
    """Test intent classification and layer routing."""

    def test_engineering_keywords(self, settings, registry):
        router = SwarmRouter(settings, registry)
        result = router.classify("Review the auth module code for security issues")
        assert "engineering" in result.target_layers

    def test_platform_keywords(self, settings, registry):
        router = SwarmRouter(settings, registry)
        result = router.classify("Configure a Copilot Studio agent with Power Platform connectors")
        assert "platform_specialists" in result.target_layers

    def test_customer_keywords(self, settings, registry):
        router = SwarmRouter(settings, registry)
        result = router.classify("Update the customer engagement status for Amica")
        assert "customer_engagements" in result.target_layers

    def test_strategy_keywords(self, settings, registry):
        router = SwarmRouter(settings, registry)
        result = router.classify("Plan the Q3 program strategy and roadmap")
        assert "strategy_org" in result.target_layers

    def test_content_keywords(self, settings, registry):
        router = SwarmRouter(settings, registry)
        result = router.classify("Write documentation and publish wiki notes")
        assert "content_docs" in result.target_layers

    def test_orchestration_keywords(self, settings, registry):
        router = SwarmRouter(settings, registry)
        result = router.classify("Select the right MCP server for agent orchestration")
        assert "orchestration" in result.target_layers

    def test_intelligence_keywords(self, settings, registry):
        router = SwarmRouter(settings, registry)
        result = router.classify("Run a deep research and analytics evaluation")
        assert "intelligence" in result.target_layers

    def test_multi_layer_classification(self, settings, registry):
        router = SwarmRouter(settings, registry)
        result = router.classify("Review the code and write documentation")
        assert "engineering" in result.target_layers
        assert "content_docs" in result.target_layers

    def test_default_to_meta(self, settings, registry):
        router = SwarmRouter(settings, registry)
        result = router.classify("What is the meaning of life?")
        assert "meta" in result.target_layers

    def test_returns_routing_result(self, settings, registry):
        router = SwarmRouter(settings, registry)
        result = router.classify("test prompt")
        assert isinstance(result, RoutingResult)

    def test_target_agents_populated(self, settings, registry):
        router = SwarmRouter(settings, registry)
        result = router.classify("Review the auth code for security")
        assert len(result.target_agents) > 0
        assert "dayour-swe" in result.target_agents

    def test_confidence_scales_with_keywords(self, settings, registry):
        router = SwarmRouter(settings, registry)
        single = router.classify("code")
        multi = router.classify("code review test security")
        assert multi.confidence >= single.confidence


class TestRouterSummary:
    """Test router metadata."""

    def test_summary_structure(self, settings, registry):
        router = SwarmRouter(settings, registry)
        s = router.summary()
        assert "registry" in s
        assert "cached_agents" in s
        assert "routing_keywords" in s
        assert s["routing_keywords"] == len(INTENT_LAYER_MAP)


class TestSwarmRouterInit:
    """Test router initialisation."""

    def test_creates_with_defaults(self, settings, registry):
        router = SwarmRouter(settings, registry)
        assert router.registry.agent_count == 67
        assert router.factory.cached_count == 0
