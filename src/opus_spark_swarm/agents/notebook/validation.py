"""Validation agent -- reviews assembled notebooks for quality."""

from __future__ import annotations

import ast
from typing import Any

from autogen import ConversableAgent

from opus_spark_swarm.agents.base import create_agent
from opus_spark_swarm.config import Settings

SYSTEM_MESSAGE = (
    "Review the assembled notebook for correctness, completeness, and "
    "executability. Check that: all imports are present, variables are defined "
    "before use, markdown flow is logical, visualizations match the data, "
    "and the notebook tells a coherent analytical story from start to finish."
)


def validate_notebook(cells: list[dict[str, Any]]) -> dict[str, Any]:
    """Validate a list of notebook cells for common issues.

    Parameters
    ----------
    cells:
        Ordered list of cell dicts (``cell_type``, ``source``, optional ``metadata``).

    Returns
    -------
    dict with ``valid``, ``issues``, ``suggestions``, and ``completeness_score``.
    """
    issues: list[str] = []
    suggestions: list[str] = []

    code_cells = [c for c in cells if c.get("cell_type") == "code"]
    markdown_cells = [c for c in cells if c.get("cell_type") == "markdown"]

    # --- structural checks ---
    if not cells:
        issues.append("Notebook has no cells.")
    if not code_cells:
        issues.append("Notebook has no code cells.")
    if not markdown_cells:
        issues.append("Notebook has no markdown cells.")

    # Check that first cell is markdown (title/intro)
    if cells and cells[0].get("cell_type") != "markdown":
        suggestions.append("Consider starting the notebook with a markdown title cell.")

    # Check that last cell is markdown (conclusions)
    if cells and cells[-1].get("cell_type") != "markdown":
        suggestions.append("Consider ending the notebook with a conclusions markdown cell.")

    # --- code syntax checks ---
    defined_names: set[str] = set()
    for i, cell in enumerate(code_cells):
        source = cell.get("source", "")
        try:
            tree = ast.parse(source)
            # Track top-level assignments
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            defined_names.add(target.id)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        defined_names.add(alias.asname or alias.name.split(".")[0])
                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        defined_names.add(alias.asname or alias.name)
        except SyntaxError as exc:
            issues.append(f"Code cell {i} has a syntax error: {exc.msg}")

    # --- completeness scoring ---
    has_imports = any("import " in c.get("source", "") for c in code_cells)
    has_viz = any(
        c.get("metadata", {}).get("chart_type")
        or "plt." in c.get("source", "")
        or "plotly" in c.get("source", "")
        for c in code_cells
    )
    has_intro = len(markdown_cells) >= 1
    has_conclusion = len(markdown_cells) >= 2

    score_parts = [
        0.2 * bool(has_imports),
        0.2 * bool(has_viz),
        0.2 * bool(has_intro),
        0.2 * bool(has_conclusion),
        0.2 * (len(issues) == 0),
    ]
    completeness_score = round(sum(score_parts), 2)

    if not has_imports:
        suggestions.append("Add import statements at the top of the notebook.")
    if not has_viz:
        suggestions.append("Add at least one visualization cell.")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "suggestions": suggestions,
        "completeness_score": completeness_score,
    }


def create_validation_agent(settings: Settings) -> ConversableAgent:
    """Build and return the ValidationAgent with its registered tools.

    Uses AG2 self-registration: same agent registers both for_llm and
    for_execution so it can propose and execute tool calls in a GroupChat.
    """
    agent = create_agent(
        name="ValidationAgent",
        system_message=SYSTEM_MESSAGE,
        settings=settings,
    )

    @agent.register_for_execution()
    @agent.register_for_llm(description="Validate the assembled notebook cells for correctness and completeness")
    def _validate_notebook(cells: list[dict[str, Any]]) -> dict[str, Any]:
        return validate_notebook(cells)

    return agent
