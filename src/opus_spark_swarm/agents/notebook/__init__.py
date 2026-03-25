"""Notebook generator agent team -- executable deliverable creation.

The notebook team contributes cells to a shared notebook structure.
Conversation flow:
    markdown (intro) -> code (data) -> visualization -> markdown (analysis)
    -> code (model) -> visualization (results) -> markdown (conclusions)
    -> validation
"""

from __future__ import annotations

from typing import Any

from autogen import GroupChat, GroupChatManager

from opus_spark_swarm.agents.base import build_llm_config
from opus_spark_swarm.config import Settings

from .codegen import create_codegen_agent
from .markdown_agent import create_markdown_agent
from .validation import create_validation_agent
from .visualization import create_visualization_agent

__all__ = [
    "create_codegen_agent",
    "create_markdown_agent",
    "create_validation_agent",
    "create_visualization_agent",
    "create_notebook_team",
]


# The notebook team uses a fixed speaker order that mirrors the expected
# notebook structure: narrative → code → charts → narrative → code → charts
# → narrative → validation.
_SPEAKER_ORDER = [
    "MarkdownAgent",       # intro / executive summary
    "CodeGenAgent",        # data retrieval
    "VisualizationAgent",  # exploratory charts
    "MarkdownAgent",       # analysis narrative
    "CodeGenAgent",        # modeling / core analysis
    "VisualizationAgent",  # results charts
    "MarkdownAgent",       # conclusions
    "ValidationAgent",     # final review
]


def _speaker_selection(
    last_speaker: Any,
    group_chat: GroupChat,
) -> Any:
    """Deterministic round-robin following ``_SPEAKER_ORDER``.

    Uses only messages from named agents (not system/manager messages)
    to determine the current step in the speaker rotation.
    """
    agents_by_name = {a.name: a for a in group_chat.agents}
    agent_names = {a.name for a in group_chat.agents}
    messages = group_chat.messages

    # Count only messages from actual team agents (skip manager/system messages).
    step = sum(1 for m in messages if m.get("name") in agent_names)
    if step >= len(_SPEAKER_ORDER):
        return agents_by_name["ValidationAgent"]

    return agents_by_name[_SPEAKER_ORDER[step]]


def create_notebook_team(
    settings: Settings,
) -> tuple[GroupChat, GroupChatManager]:
    """Create the Notebook Generator agent team.

    Returns a ``(GroupChat, GroupChatManager)`` tuple ready to be initiated
    by the Orchestrator.

    Parameters
    ----------
    settings:
        Application settings instance.
    """
    markdown_agent = create_markdown_agent(settings)
    codegen_agent = create_codegen_agent(settings)
    viz_agent = create_visualization_agent(settings)
    validation_agent = create_validation_agent(settings)

    agents = [markdown_agent, codegen_agent, viz_agent, validation_agent]

    group_chat = GroupChat(
        agents=agents,
        messages=[],
        max_round=len(_SPEAKER_ORDER) + 2,  # allow a small buffer
        speaker_selection_method=_speaker_selection,
    )

    manager = GroupChatManager(
        groupchat=group_chat,
        llm_config=build_llm_config(settings),
    )

    return group_chat, manager
