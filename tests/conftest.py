"""Shared pytest fixtures for Opus Spark Swarm test suite."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Settings fixture with dummy keys (no real API calls)
# ---------------------------------------------------------------------------

@pytest.fixture()
def dummy_env(monkeypatch):
    """Set environment variables so Settings can be instantiated without a .env file."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-dummy-key-1234")
    monkeypatch.setenv("SEC_EDGAR_USER_AGENT", "TestSuite/1.0 test@example.com")
    monkeypatch.setenv("NEWS_API_KEY", "test-news-key")
    monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "test-av-key")
    monkeypatch.setenv("FRED_API_KEY", "test-fred-key")
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_test-token")


@pytest.fixture()
def settings(dummy_env):
    """Return a Settings instance populated with dummy values."""
    from opus_spark_swarm.config import Settings
    return Settings()


# ---------------------------------------------------------------------------
# Sample data fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_company_dossier() -> dict:
    """A minimal company intelligence dossier for testing downstream agents."""
    return {
        "company": {
            "name": "Acme Corp",
            "ticker": "ACME",
            "cik": "0001234567",
            "industry": "Technology",
            "hq": "San Francisco, CA",
            "founded": "2010-01-15",
            "description": "A leading provider of cloud solutions.",
        },
        "market_data": {
            "market_cap": "5000000000",
            "pe_ratio": "25.3",
            "revenue": "1200000000",
            "profit_margin": "0.18",
            "sector": "Technology",
        },
        "filings": [
            {"type": "10-K", "date": "2024-03-15", "description": "Annual report"},
            {"type": "10-Q", "date": "2024-06-15", "description": "Quarterly report"},
        ],
        "news": [
            {"title": "Acme Corp reports record growth", "source": "TechDaily", "sentiment": "positive"},
        ],
    }


@pytest.fixture()
def sample_analysis_output() -> dict:
    """A minimal analysis output for testing architect/notebook agents."""
    return {
        "problem_statements": [
            {
                "id": "PS-001",
                "title": "Cloud Migration Efficiency",
                "description": "Acme Corp's cloud migration costs are 30% above industry average.",
                "impact": "high",
                "evidence": ["10-K filing shows rising infrastructure costs"],
            },
            {
                "id": "PS-002",
                "title": "Market Share Erosion",
                "description": "Competitor XYZ gained 5% market share in Q3.",
                "impact": "medium",
                "evidence": ["News articles indicate competitive pressure"],
            },
        ],
        "swot": {
            "strengths": ["Strong brand recognition", "Robust R&D pipeline"],
            "weaknesses": ["High operational costs", "Legacy systems"],
            "opportunities": ["AI/ML integration", "International expansion"],
            "threats": ["Regulatory changes", "Emerging competitors"],
        },
    }


@pytest.fixture()
def sample_blueprint() -> dict:
    """A minimal solution architecture blueprint for quality-gate testing."""
    return {
        "exec_summary": "Cloud Cost Optimization Platform for reducing infrastructure spend.",
        "architecture": {
            "overview": "Microservices-based cost analyzer with recommendation engine.",
            "components": [
                {"name": "Cost Analyzer", "type": "service", "description": "Analyzes cloud spend"},
                {"name": "Recommendation Engine", "type": "service", "description": "Generates optimization suggestions"},
            ],
        },
        "phases": [
            {"name": "Phase 1", "duration": "4 weeks", "deliverables": ["Cost dashboard"]},
            {"name": "Phase 2", "duration": "6 weeks", "deliverables": ["Auto-scaling policies"]},
        ],
        "risks": [
            {"risk": "Data accuracy", "mitigation": "Validate against billing APIs", "severity": "medium"},
        ],
        "costs": {"total": "$250K", "breakdown": "Infrastructure $100K, Engineering $150K"},
        "kpis": [
            {"metric": "Cost reduction", "target": "20%", "measurement_method": "Monthly cloud spend comparison"},
        ],
    }


# ---------------------------------------------------------------------------
# Mock httpx response helper
# ---------------------------------------------------------------------------

@pytest.fixture()
def mock_httpx_response():
    """Factory fixture to create mock httpx responses."""
    def _make(status_code: int = 200, json_data: dict | None = None, headers: dict | None = None):
        resp = MagicMock()
        resp.status_code = status_code
        resp.json.return_value = json_data or {}
        resp.headers = headers or {}
        resp.content = b'{"ok": true}'
        resp.raise_for_status = MagicMock()
        if status_code >= 400:
            resp.raise_for_status.side_effect = Exception(f"HTTP {status_code}")
        return resp
    return _make
