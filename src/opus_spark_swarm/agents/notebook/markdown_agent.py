"""Markdown agent -- writes narrative markdown cells for Jupyter notebooks."""

from __future__ import annotations

from typing import Any

from autogen import ConversableAgent

from opus_spark_swarm.agents.base import create_agent
from opus_spark_swarm.config import Settings

SYSTEM_MESSAGE = (
    "Write narrative markdown cells that tell the analytical story. Include "
    "problem background, methodology, findings, and conclusions. Structure "
    "content with clear headings, bullet points, and emphasis. Adapt tone to "
    "the configured notebook style (narrative, technical, or executive)."
)


def create_markdown_cell(content: str) -> dict[str, Any]:
    """Create a notebook markdown cell dict.

    Parameters
    ----------
    content:
        Markdown-formatted text for the cell.
    """
    return {
        "cell_type": "markdown",
        "source": content,
    }


def create_markdown_agent(settings: Settings) -> ConversableAgent:
    """Build and return the MarkdownAgent with its registered tools.

    Uses AG2 self-registration: same agent registers both for_llm and
    for_execution so it can propose and execute tool calls in a GroupChat.
    """
    agent = create_agent(
        name="MarkdownAgent",
        system_message=SYSTEM_MESSAGE,
        settings=settings,
    )

    @agent.register_for_execution()
    @agent.register_for_llm(description="Create a markdown narrative cell for the notebook")
    def _create_markdown_cell(content: str) -> dict[str, Any]:
        return create_markdown_cell(content)

    return agent
