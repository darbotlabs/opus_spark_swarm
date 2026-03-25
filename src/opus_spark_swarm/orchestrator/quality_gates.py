"""Quality gate scoring for pipeline phase outputs."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class QualityGate:
    """Scores pipeline outputs on completeness, coherence, and evidence grounding."""

    def __init__(self, threshold: float = 0.8) -> None:
        self.threshold = threshold

    # ---------------------------------------------------------------- scorers

    def score_research(self, dossier: dict) -> float:
        """Score company intelligence dossier (0-1).

        Checks: has company info, has market data, has news, has filings
        (partial results OK -- each section is worth 0.25).
        """
        if not dossier:
            return 0.0

        score = 0.0
        sections = ["company", "market_data", "news", "filings"]
        weight = 1.0 / len(sections)

        for section in sections:
            data = dossier.get(section)
            if data:
                # Non-empty string or non-empty collection counts.
                if isinstance(data, str) and data.strip():
                    score += weight
                elif isinstance(data, (dict, list)) and len(data) > 0:
                    score += weight
                elif data:
                    score += weight

        logger.debug("Research quality score: %.2f (threshold %.2f)", score, self.threshold)
        return round(score, 2)

    def score_analysis(self, analysis: dict) -> float:
        """Score analyst output (0-1).

        Checks:
        - Has ``problem_statements`` key (0.2)
        - At least 3 statements (0.3)
        - Each statement has title, context, evidence, impact (0.5 spread evenly)
        """
        if not analysis:
            return 0.0

        score = 0.0
        statements = analysis.get("problem_statements", [])

        if not statements:
            return 0.0

        # Has the key at all
        score += 0.2

        # Quantity check
        if len(statements) >= 3:
            score += 0.3
        elif len(statements) >= 1:
            score += 0.15

        # Quality check -- each statement should have required fields
        required_fields = ["title", "context", "evidence", "impact"]
        if statements:
            field_weight = 0.5 / len(statements)
            for stmt in statements:
                if isinstance(stmt, dict):
                    present = sum(1 for f in required_fields if stmt.get(f))
                    score += field_weight * (present / len(required_fields))

        result = round(min(score, 1.0), 2)
        logger.debug("Analysis quality score: %.2f (threshold %.2f)", result, self.threshold)
        return result

    def score_architecture(self, blueprint: dict) -> float:
        """Score solution blueprint (0-1).

        Checks for presence of: exec_summary, architecture, phases, risks,
        costs, kpis -- each worth ~0.167.
        """
        if not blueprint:
            return 0.0

        sections = ["exec_summary", "architecture", "phases", "risks", "costs", "kpis"]
        weight = 1.0 / len(sections)
        score = 0.0

        for section in sections:
            data = blueprint.get(section)
            if data:
                if isinstance(data, str) and data.strip():
                    score += weight
                elif isinstance(data, (dict, list)) and len(data) > 0:
                    score += weight
                elif data:
                    score += weight

        result = round(min(score, 1.0), 2)
        logger.debug("Architecture quality score: %.2f (threshold %.2f)", result, self.threshold)
        return result

    def score_notebook(self, cells: list) -> float:
        """Score notebook (0-1).

        Checks:
        - Has markdown cells (0.25)
        - Has code cells (0.25)
        - Has visualization-related content (0.25)
        - Validation passed / has validation marker (0.25)
        """
        if not cells:
            return 0.0

        has_markdown = False
        has_code = False
        has_viz = False
        has_validation = False

        viz_keywords = ["plt.", "plotly", "fig.", "chart", "plot(", "mermaid", "matplotlib"]
        validation_keywords = ["validation", "validated", "VALIDATED", "PASS"]

        for cell in cells:
            cell_type = cell.get("cell_type", "")
            source = cell.get("source", "")
            if isinstance(source, list):
                source = "".join(source)

            if cell_type == "markdown":
                has_markdown = True
                if any(kw in source.lower() for kw in validation_keywords):
                    has_validation = True
            elif cell_type == "code":
                has_code = True
                if any(kw in source for kw in viz_keywords):
                    has_viz = True

        score = 0.0
        if has_markdown:
            score += 0.25
        if has_code:
            score += 0.25
        if has_viz:
            score += 0.25
        if has_validation:
            score += 0.25

        logger.debug("Notebook quality score: %.2f (threshold %.2f)", score, self.threshold)
        return round(score, 2)

    # ------------------------------------------------------------------ gate

    def passes(self, score: float) -> bool:
        """Return ``True`` if *score* meets or exceeds the threshold."""
        return score >= self.threshold


# ---------------------------------------------------------------------------
# Module-level convenience wrappers (used by the test suite)
# ---------------------------------------------------------------------------

_default_gate = QualityGate()


def score_research(dossier: dict) -> float:
    """Score a research dossier using the default quality gate."""
    return _default_gate.score_research(dossier)


def score_analysis(analysis: dict) -> float:
    """Score an analysis output using the default quality gate."""
    return _default_gate.score_analysis(analysis)


def score_architecture(blueprint: dict) -> float:
    """Score a solution blueprint using the default quality gate."""
    return _default_gate.score_architecture(blueprint)


def score_notebook(cells: list) -> float:
    """Score notebook cells using the default quality gate."""
    return _default_gate.score_notebook(cells)


def passes(score: float, threshold: float = 0.8) -> bool:
    """Return ``True`` if *score* meets or exceeds *threshold*."""
    return score >= threshold
