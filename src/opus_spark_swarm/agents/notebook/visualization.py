"""Visualization agent -- creates chart code cells for Jupyter notebooks."""

from __future__ import annotations

from typing import Any

from autogen import ConversableAgent

from opus_spark_swarm.agents.base import create_agent
from opus_spark_swarm.config import Settings

SYSTEM_MESSAGE = (
    "Create visualization code cells using matplotlib and plotly. Charts should "
    "be clear, well-labeled, and tell a story. Generate bar charts, line charts, "
    "pie charts, heatmaps, and sankey diagrams as appropriate for the data. "
    "Always include axis labels, titles, legends, and color schemes that are "
    "accessible and print-friendly."
)


def create_chart_cell(
    chart_type: str, data_description: str, code: str
) -> dict[str, Any]:
    """Create a notebook visualization code cell dict.

    Parameters
    ----------
    chart_type:
        Type of chart (e.g. ``"bar"``, ``"line"``, ``"pie"``, ``"heatmap"``,
        ``"sankey"``).
    data_description:
        Human-readable description of the data being visualized.
    code:
        Python source code that produces the chart.
    """
    return {
        "cell_type": "code",
        "source": code,
        "metadata": {
            "chart_type": chart_type,
            "description": data_description,
        },
    }


def create_visualization_agent(settings: Settings) -> ConversableAgent:
    """Build and return the VisualizationAgent with its registered tools.

    Uses AG2 self-registration: same agent registers both for_llm and
    for_execution so it can propose and execute tool calls in a GroupChat.
    """
    agent = create_agent(
        name="VisualizationAgent",
        system_message=SYSTEM_MESSAGE,
        settings=settings,
    )

    @agent.register_for_execution()
    @agent.register_for_llm(description="Create a visualization code cell for the notebook")
    def _create_chart_cell(
        chart_type: str, data_description: str, code: str
    ) -> dict[str, Any]:
        return create_chart_cell(chart_type, data_description, code)

    return agent
