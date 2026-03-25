"""AG2 agent factory -- instantiates ConversableAgents from the swarm registry.

Reads agent metadata (name, description, model, system message) from the
registry and the original Markdown definition files, producing AG2-compatible
agents that can participate in GroupChat or nested conversations.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from opus_spark_swarm.config import Settings
from opus_spark_swarm.swarm.registry import AgentEntry, SwarmRegistry, get_registry

logger = logging.getLogger(__name__)

# Where the agent definition .md files live
DEFAULT_DEFINITIONS_DIR = Path.home() / ".copilot" / "agents"

# Model name mapping to LiteLLM / AG2 compatible identifiers
MODEL_MAP: dict[str, str] = {
    "gpt-5.4": "gpt-5.4",
    "claude-sonnet-4.6": "claude-sonnet-4-6",
    "claude-opus-4.6": "claude-opus-4-6",
}


def _load_system_message(entry: AgentEntry, definitions_dir: Path) -> str:
    """Load the agent's system message from its Markdown definition file.

    Strips the YAML frontmatter and the standardised Communication Standards
    section, returning the substantive system prompt content.
    """
    md_path = definitions_dir / entry.definition_file
    if not md_path.exists():
        return f"You are {entry.name}. {entry.description}"

    text = md_path.read_text(encoding="utf-8", errors="replace")

    # Strip YAML frontmatter
    import re
    text = re.sub(r"^---\s*\n.*?\n---\s*\n", "", text, count=1, flags=re.DOTALL)

    # Strip the Communication Standards boilerplate (first ## section if it matches)
    text = re.sub(
        r"^## Communication Standards\s*\n.*?(?=^## |\Z)",
        "",
        text,
        count=1,
        flags=re.DOTALL | re.MULTILINE,
    )

    return text.strip()[:8000]  # Cap at 8K chars for token budget


def _resolve_model(entry: AgentEntry, settings: Settings) -> str:
    """Map the agent's model identifier to an AG2/LiteLLM-compatible string."""
    if entry.model:
        return MODEL_MAP.get(entry.model, entry.model)
    return settings.ag2_model


class SwarmAgentFactory:
    """Creates AG2 ConversableAgents from swarm registry entries.

    Usage::

        factory = SwarmAgentFactory(settings)
        agent = factory.create("dayour-swe")
        agents = factory.create_layer("engineering")
    """

    def __init__(
        self,
        settings: Settings,
        registry: SwarmRegistry | None = None,
        definitions_dir: Path | None = None,
    ) -> None:
        self.settings = settings
        self.registry = registry or get_registry()
        self.definitions_dir = definitions_dir or DEFAULT_DEFINITIONS_DIR
        self._cache: dict[str, Any] = {}

    def create(self, name: str) -> Any:
        """Create a single AG2 ConversableAgent by registry name.

        Returns a cached instance if the agent was already created.
        Raises KeyError if the agent name is not in the registry.
        """
        if name in self._cache:
            return self._cache[name]

        entry = self.registry.get_agent(name)
        if entry is None:
            raise KeyError(f"Agent '{name}' not found in swarm registry")

        from autogen import ConversableAgent

        model_name = _resolve_model(entry, self.settings)
        system_message = _load_system_message(entry, self.definitions_dir)

        llm_config = {
            "config_list": [
                {
                    "model": model_name,
                    "api_key": self.settings.anthropic_api_key.get_secret_value(),
                }
            ],
        }

        agent = ConversableAgent(
            name=name,
            system_message=system_message,
            llm_config=llm_config,
            human_input_mode="NEVER",
            max_consecutive_auto_reply=5,
        )

        self._cache[name] = agent
        logger.info("Created swarm agent: %s (model=%s, layer=%s)", name, model_name, entry.layer)
        return agent

    def create_layer(self, layer_id: str) -> list[Any]:
        """Create all agents in a given layer. Returns a list of AG2 agents."""
        entries = self.registry.agents_in_layer(layer_id)
        if not entries:
            raise KeyError(f"Layer '{layer_id}' not found or has no agents")
        return [self.create(e.name) for e in entries]

    def create_team(self, names: list[str]) -> list[Any]:
        """Create a specific set of agents by name."""
        return [self.create(n) for n in names]

    @property
    def cached_count(self) -> int:
        """Number of agents currently instantiated."""
        return len(self._cache)
