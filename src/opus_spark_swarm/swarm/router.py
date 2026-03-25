"""Swarm router -- layer-based delegation and scatter-gather orchestration.

Routes prompts to the appropriate agent layer(s) based on intent classification,
then optionally runs scatter-gather across multiple layers and synthesises
results.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from opus_spark_swarm.config import Settings
from opus_spark_swarm.swarm.factory import SwarmAgentFactory
from opus_spark_swarm.swarm.registry import SwarmRegistry, get_registry

logger = logging.getLogger(__name__)

# Intent keywords mapped to layer IDs for routing
INTENT_LAYER_MAP: dict[str, list[str]] = {
    "architecture": ["engineering"],
    "code": ["engineering"],
    "review": ["engineering"],
    "test": ["engineering"],
    "security": ["engineering"],
    "devops": ["engineering"],
    "copilot studio": ["platform_specialists"],
    "power platform": ["platform_specialists"],
    "dynamics": ["platform_specialists"],
    "fabric": ["platform_specialists"],
    "azure": ["platform_specialists"],
    "purview": ["platform_specialists"],
    "entra": ["platform_specialists"],
    "teams": ["platform_specialists"],
    "sharepoint": ["platform_specialists"],
    "strategy": ["strategy_org"],
    "program": ["strategy_org"],
    "roadmap": ["strategy_org"],
    "customer": ["customer_engagements"],
    "engagement": ["customer_engagements"],
    "account": ["customer_engagements"],
    "document": ["content_docs"],
    "notes": ["content_docs"],
    "wiki": ["content_docs"],
    "presentation": ["content_docs"],
    "research": ["intelligence"],
    "analytics": ["intelligence"],
    "evaluation": ["intelligence"],
    "insight": ["intelligence"],
    "mcp": ["orchestration"],
    "agent": ["orchestration"],
    "orchestrat": ["orchestration"],
}


@dataclass
class RoutingResult:
    """Result from the swarm router's layer classification."""

    intent: str
    target_layers: list[str]
    target_agents: list[str]
    confidence: float


@dataclass
class SwarmResponse:
    """Aggregated response from scatter-gather across layers."""

    prompt: str
    routing: RoutingResult
    layer_responses: dict[str, str] = field(default_factory=dict)
    synthesis: str = ""


class SwarmRouter:
    """Routes prompts to swarm layers and optionally runs scatter-gather.

    Usage::

        router = SwarmRouter(settings)
        routing = router.classify("Review the auth module for security issues")
        # => RoutingResult(target_layers=["engineering"], ...)

        response = await router.scatter_gather("Analyse Shopify's supply chain")
        # => SwarmResponse with per-layer responses and synthesis
    """

    def __init__(
        self,
        settings: Settings,
        registry: SwarmRegistry | None = None,
        factory: SwarmAgentFactory | None = None,
    ) -> None:
        self.settings = settings
        self.registry = registry or get_registry()
        self.factory = factory or SwarmAgentFactory(settings, self.registry)

    def classify(self, prompt: str) -> RoutingResult:
        """Classify a prompt's intent and determine target layers.

        Uses keyword matching against INTENT_LAYER_MAP. For production use,
        this should be replaced with an LLM-based classifier.
        """
        prompt_lower = prompt.lower()
        matched_layers: set[str] = set()
        matched_keywords: list[str] = []

        for keyword, layers in INTENT_LAYER_MAP.items():
            if keyword in prompt_lower:
                matched_layers.update(layers)
                matched_keywords.append(keyword)

        if not matched_layers:
            # Default: route to the meta layer (dayour orchestrator)
            matched_layers = {"meta"}

        # Collect target agents from matched layers
        target_agents = []
        for layer_id in matched_layers:
            layer = self.registry.layers.get(layer_id)
            if layer:
                target_agents.extend(layer.agent_names)

        confidence = min(1.0, len(matched_keywords) * 0.25) if matched_keywords else 0.1

        return RoutingResult(
            intent=" + ".join(matched_keywords) if matched_keywords else "general",
            target_layers=sorted(matched_layers),
            target_agents=target_agents,
            confidence=confidence,
        )

    async def scatter_gather(
        self,
        prompt: str,
        layers: list[str] | None = None,
        max_agents_per_layer: int = 3,
    ) -> SwarmResponse:
        """Scatter a prompt to multiple layers and gather responses.

        If *layers* is not specified, uses ``classify()`` to determine targets.
        Creates AG2 GroupChats per layer with up to *max_agents_per_layer* agents.
        """
        routing = self.classify(prompt) if layers is None else RoutingResult(
            intent="explicit",
            target_layers=layers,
            target_agents=[],
            confidence=1.0,
        )

        layer_responses: dict[str, str] = {}

        for layer_id in routing.target_layers:
            try:
                agents = self.factory.create_layer(layer_id)[:max_agents_per_layer]
                if not agents:
                    continue

                from autogen import GroupChat, GroupChatManager
                from opus_spark_swarm.agents.base import build_llm_config

                group_chat = GroupChat(
                    agents=agents,
                    messages=[],
                    max_round=6,
                    speaker_selection_method="auto",
                )
                manager = GroupChatManager(
                    groupchat=group_chat,
                    llm_config=build_llm_config(self.settings),
                )

                await agents[0].a_initiate_chat(manager, message=prompt)

                # Collect the last substantive message as the layer response
                for msg in reversed(group_chat.messages):
                    content = msg.get("content", "")
                    if content and content.strip():
                        layer_responses[layer_id] = content.strip()[:2000]
                        break
                else:
                    layer_responses[layer_id] = "(no response)"

                logger.info("Layer %s responded (%d chars)", layer_id, len(layer_responses.get(layer_id, "")))

            except Exception as exc:
                logger.warning("Layer %s failed: %s", layer_id, exc)
                layer_responses[layer_id] = f"ERROR: {exc}"

        return SwarmResponse(
            prompt=prompt,
            routing=routing,
            layer_responses=layer_responses,
        )

    def summary(self) -> dict:
        """Return router state summary."""
        return {
            "registry": self.registry.summary(),
            "cached_agents": self.factory.cached_count,
            "routing_keywords": len(INTENT_LAYER_MAP),
        }
