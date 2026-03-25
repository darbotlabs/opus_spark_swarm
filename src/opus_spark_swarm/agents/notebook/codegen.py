"""CodeGen agent -- writes Python code cells for Jupyter notebooks."""

from __future__ import annotations

from typing import Any

from autogen import ConversableAgent

from opus_spark_swarm.agents.base import create_agent
from opus_spark_swarm.config import Settings

SYSTEM_MESSAGE = (
    "Write Python code cells for Jupyter notebooks. Code should be clean, "
    "documented, and executable. Focus on data retrieval, transformation, "
    "analysis, and modeling. Every cell must be syntactically valid Python 3.11+. "
    "Include imports at the top, handle errors with try/except, and provide "
    "fallback sample data when live APIs are unavailable."
)


def create_code_cell(code: str, description: str) -> dict[str, Any]:
    """Create a notebook code cell dict.

    Parameters
    ----------
    code:
        Python source code for the cell.
    description:
        Human-readable description of what the cell does.
    """
    return {
        "cell_type": "code",
        "source": code,
        "metadata": {"description": description},
    }


def create_codegen_agent(settings: Settings) -> ConversableAgent:
    """Build and return the CodeGenAgent with its registered tools.

    Uses AG2 self-registration: same agent registers both for_llm and
    for_execution so it can propose and execute tool calls in a GroupChat.
    """
    agent = create_agent(
        name="CodeGenAgent",
        system_message=SYSTEM_MESSAGE,
        settings=settings,
    )

    @agent.register_for_execution()
    @agent.register_for_llm(description="Create a Python code cell for the notebook")
    def _create_code_cell(code: str, description: str) -> dict[str, Any]:
        return create_code_cell(code, description)

    return agent
