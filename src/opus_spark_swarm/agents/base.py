"""Base agent helpers and shared LLM configuration for AG2 agents."""

from __future__ import annotations

from typing import Any

from autogen import ConversableAgent

from opus_spark_swarm.config import Settings

# Default system prompt preamble injected into every agent.
BASE_SYSTEM_PROMPT = (
    "You are a specialist agent in the Opus Spark Swarm, an autonomous "
    "business analysis pipeline powered by Claude Opus 4.6 via the AG2 "
    "(AutoGen2) framework. Always ground your responses in evidence, cite "
    "sources where possible, and collaborate constructively with other agents."
)


def build_llm_config(settings: Settings) -> dict[str, Any]:
    """Build the AG2-compatible ``llm_config`` dict from application settings.

    Returns a configuration dict suitable for passing to any
    :class:`autogen.ConversableAgent` ``llm_config`` parameter.
    """
    return {
        "config_list": [
            {
                "model": settings.ag2_model,
                "api_type": "anthropic",
                "api_key": settings.anthropic_api_key.get_secret_value(),
            }
        ],
    }


def create_agent(
    name: str,
    system_message: str,
    settings: Settings,
    *,
    human_input_mode: str = "NEVER",
    extra_llm_config: dict[str, Any] | None = None,
) -> ConversableAgent:
    """Create a :class:`ConversableAgent` with standard Opus Spark Swarm config.

    Parameters
    ----------
    name:
        Agent name (used in AG2 group chats).
    system_message:
        Role-specific system prompt. The shared *BASE_SYSTEM_PROMPT* is
        prepended automatically.
    settings:
        Application :class:`Settings` instance.
    human_input_mode:
        AG2 human-input mode (default ``"NEVER"`` for autonomous operation).
    extra_llm_config:
        Optional overrides merged into the LLM config dict.
    """
    llm_config = build_llm_config(settings)
    if extra_llm_config:
        llm_config.update(extra_llm_config)

    full_prompt = f"{BASE_SYSTEM_PROMPT}\n\n{system_message}"

    return ConversableAgent(
        name=name,
        system_message=full_prompt,
        llm_config=llm_config,
        human_input_mode=human_input_mode,
    )
