"""Swarm agent registry -- loads agent metadata from swarm_registry.json.

Provides a typed, queryable interface to the 67-agent DAYOURBOT swarm
with layer-based filtering, model distribution, and definition file
lookups.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator


REGISTRY_PATH = Path(__file__).parent / "swarm_registry.json"


@dataclass(frozen=True)
class AgentEntry:
    """A single agent's metadata from the registry."""

    name: str
    description: str
    model: str
    mcps: list[str]
    layer: str
    layer_label: str
    definition_file: str
    definition_lines: int
    section_count: int


@dataclass(frozen=True)
class LayerEntry:
    """A swarm layer's metadata."""

    id: str
    label: str
    purpose: str
    agent_names: list[str]

    @property
    def agent_count(self) -> int:
        return len(self.agent_names)


@dataclass
class SwarmRegistry:
    """In-memory registry of all DAYOURBOT swarm agents.

    Loaded from ``swarm_registry.json`` at module level. Provides
    lookup by name, layer filtering, and model distribution queries.
    """

    agents: dict[str, AgentEntry] = field(default_factory=dict)
    layers: dict[str, LayerEntry] = field(default_factory=dict)
    model_distribution: dict[str, int] = field(default_factory=dict)

    # ---------------------------------------------------------------- factory

    @classmethod
    def load(cls, path: Path | str | None = None) -> "SwarmRegistry":
        """Load the registry from the JSON file."""
        path = Path(path) if path else REGISTRY_PATH
        data = json.loads(path.read_text(encoding="utf-8"))

        agents = {}
        for name, info in data.get("agents", {}).items():
            agents[name] = AgentEntry(
                name=info["name"],
                description=info.get("description", ""),
                model=info.get("model", ""),
                mcps=info.get("mcps", []),
                layer=info.get("layer", ""),
                layer_label=info.get("layer_label", ""),
                definition_file=info.get("definition_file", ""),
                definition_lines=info.get("definition_lines", 0),
                section_count=info.get("section_count", 0),
            )

        layers = {}
        for lid, linfo in data.get("layers", {}).items():
            layers[lid] = LayerEntry(
                id=lid,
                label=linfo["label"],
                purpose=linfo["purpose"],
                agent_names=linfo.get("agents", []),
            )

        return cls(
            agents=agents,
            layers=layers,
            model_distribution=data.get("model_distribution", {}),
        )

    # ---------------------------------------------------------------- queries

    @property
    def agent_count(self) -> int:
        return len(self.agents)

    @property
    def layer_count(self) -> int:
        return len(self.layers)

    def get_agent(self, name: str) -> AgentEntry | None:
        """Look up a single agent by name."""
        return self.agents.get(name)

    def agents_in_layer(self, layer_id: str) -> list[AgentEntry]:
        """Return all agents belonging to a specific layer."""
        return [a for a in self.agents.values() if a.layer == layer_id]

    def agents_by_model(self, model: str) -> list[AgentEntry]:
        """Return all agents using a specific model."""
        return [a for a in self.agents.values() if a.model == model]

    def layer_ids(self) -> list[str]:
        """Return ordered list of layer IDs."""
        return list(self.layers.keys())

    def __iter__(self) -> Iterator[AgentEntry]:
        return iter(self.agents.values())

    def __len__(self) -> int:
        return len(self.agents)

    def summary(self) -> dict:
        """Return a compact summary suitable for logging or API responses."""
        return {
            "agent_count": self.agent_count,
            "layer_count": self.layer_count,
            "model_distribution": self.model_distribution,
            "layers": {
                lid: {
                    "label": layer.label,
                    "agent_count": layer.agent_count,
                }
                for lid, layer in self.layers.items()
            },
        }


# Module-level singleton, loaded on import
_registry: SwarmRegistry | None = None


def get_registry() -> SwarmRegistry:
    """Return the module-level SwarmRegistry singleton (lazy-loaded)."""
    global _registry
    if _registry is None:
        _registry = SwarmRegistry.load()
    return _registry
