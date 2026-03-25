"""Tests for quality gates (score_research, score_analysis, score_architecture).

The quality_gates module may not exist yet; these tests define the expected
contract so they serve as both specification and regression tests.
"""

from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Try importing quality_gates; skip all tests if module doesn't exist yet.
# ---------------------------------------------------------------------------
try:
    from opus_spark_swarm.orchestrator.quality_gates import (
        score_research,
        score_analysis,
        score_architecture,
        passes,
    )
    _HAS_QUALITY_GATES = True
except ImportError:
    _HAS_QUALITY_GATES = False

pytestmark = pytest.mark.skipif(
    not _HAS_QUALITY_GATES,
    reason="quality_gates module not yet implemented",
)


# ========================== score_research ==========================

class TestScoreResearch:
    def test_complete_dossier(self, sample_company_dossier):
        score = score_research(sample_company_dossier)
        assert 0.0 <= score <= 1.0
        assert score >= 0.7  # a complete dossier should score well

    def test_partial_dossier(self):
        partial = {"company": {"name": "Acme"}}
        score = score_research(partial)
        assert 0.0 <= score <= 1.0
        assert score < 0.8  # partial data should score lower

    def test_empty_dossier(self):
        score = score_research({})
        assert score == 0.0 or score < 0.3


# ========================== score_analysis ==========================

class TestScoreAnalysis:
    def test_valid_analysis(self, sample_analysis_output):
        score = score_analysis(sample_analysis_output)
        assert 0.0 <= score <= 1.0
        assert score >= 0.5

    def test_insufficient_statements(self):
        weak = {"problem_statements": []}
        score = score_analysis(weak)
        assert score < 0.5

    def test_no_swot(self):
        no_swot = {"problem_statements": [{"id": "PS-001", "title": "X", "description": "Y"}]}
        score = score_analysis(no_swot)
        assert 0.0 <= score <= 1.0


# ========================== score_architecture ==========================

class TestScoreArchitecture:
    def test_complete_blueprint(self, sample_blueprint):
        score = score_architecture(sample_blueprint)
        assert 0.0 <= score <= 1.0
        assert score >= 0.6

    def test_incomplete_blueprint(self):
        partial = {"title": "Incomplete", "components": []}
        score = score_architecture(partial)
        assert score < 0.7

    def test_empty_blueprint(self):
        score = score_architecture({})
        assert score < 0.3


# ========================== passes ==========================

class TestPasses:
    def test_above_threshold(self):
        assert passes(0.85, threshold=0.8) is True

    def test_below_threshold(self):
        assert passes(0.5, threshold=0.8) is False

    def test_exact_threshold(self):
        assert passes(0.8, threshold=0.8) is True

    def test_zero_threshold(self):
        assert passes(0.1, threshold=0.0) is True
