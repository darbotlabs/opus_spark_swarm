"""Tests for the swarm registry module."""

import json
from pathlib import Path

import pytest

from opus_spark_swarm.swarm.registry import AgentEntry, LayerEntry, SwarmRegistry, get_registry


REGISTRY_JSON = Path(__file__).parent.parent.parent / "src" / "opus_spark_swarm" / "swarm" / "swarm_registry.json"


class TestSwarmRegistryLoad:
    """Test loading the registry from JSON."""

    def test_load_returns_registry(self):
        reg = SwarmRegistry.load(REGISTRY_JSON)
        assert isinstance(reg, SwarmRegistry)

    def test_has_67_agents(self):
        reg = SwarmRegistry.load(REGISTRY_JSON)
        assert reg.agent_count == 67

    def test_has_8_layers(self):
        reg = SwarmRegistry.load(REGISTRY_JSON)
        assert reg.layer_count == 8

    def test_agents_are_agent_entry(self):
        reg = SwarmRegistry.load(REGISTRY_JSON)
        for agent in reg:
            assert isinstance(agent, AgentEntry)

    def test_layers_are_layer_entry(self):
        reg = SwarmRegistry.load(REGISTRY_JSON)
        for layer in reg.layers.values():
            assert isinstance(layer, LayerEntry)

    def test_model_distribution_sums_to_67(self):
        reg = SwarmRegistry.load(REGISTRY_JSON)
        total = sum(reg.model_distribution.values())
        assert total == 67


class TestSwarmRegistryQueries:
    """Test registry query methods."""

    @pytest.fixture()
    def reg(self) -> SwarmRegistry:
        return SwarmRegistry.load(REGISTRY_JSON)

    def test_get_agent_by_name(self, reg: SwarmRegistry):
        agent = reg.get_agent("dayour-swe")
        assert agent is not None
        assert agent.name == "dayour-swe"
        assert agent.layer == "engineering"

    def test_get_agent_missing(self, reg: SwarmRegistry):
        assert reg.get_agent("nonexistent") is None

    def test_agents_in_layer(self, reg: SwarmRegistry):
        eng_agents = reg.agents_in_layer("engineering")
        assert len(eng_agents) == 14
        names = [a.name for a in eng_agents]
        assert "dayour-swe" in names
        assert "dayour-architect" in names

    def test_agents_in_layer_empty(self, reg: SwarmRegistry):
        assert reg.agents_in_layer("nonexistent") == []

    def test_agents_by_model(self, reg: SwarmRegistry):
        gpt_agents = reg.agents_by_model("gpt-5.4")
        assert len(gpt_agents) == 40

    def test_layer_ids(self, reg: SwarmRegistry):
        ids = reg.layer_ids()
        assert "engineering" in ids
        assert "meta" in ids
        assert len(ids) == 8

    def test_len(self, reg: SwarmRegistry):
        assert len(reg) == 67

    def test_iter(self, reg: SwarmRegistry):
        all_agents = list(reg)
        assert len(all_agents) == 67

    def test_summary(self, reg: SwarmRegistry):
        s = reg.summary()
        assert s["agent_count"] == 67
        assert s["layer_count"] == 8
        assert "engineering" in s["layers"]


class TestLayerEntry:
    """Test LayerEntry dataclass."""

    def test_agent_count_property(self):
        layer = LayerEntry(id="test", label="Test", purpose="Testing", agent_names=["a", "b", "c"])
        assert layer.agent_count == 3


class TestAgentEntry:
    """Test AgentEntry dataclass."""

    def test_frozen(self):
        entry = AgentEntry(
            name="test",
            description="desc",
            model="gpt-5.4",
            mcps=[],
            layer="eng",
            layer_label="Engineering",
            definition_file="test.md",
            definition_lines=100,
            section_count=5,
        )
        with pytest.raises(AttributeError):
            entry.name = "changed"  # type: ignore[misc]


class TestGetRegistry:
    """Test the module-level singleton."""

    def test_returns_registry(self):
        reg = get_registry()
        assert isinstance(reg, SwarmRegistry)
        assert reg.agent_count == 67

    def test_returns_same_instance(self):
        a = get_registry()
        b = get_registry()
        assert a is b
