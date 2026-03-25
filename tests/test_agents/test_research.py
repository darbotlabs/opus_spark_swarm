"""Tests for research agent tool functions (no real HTTP calls)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Disable the 2-second API throttle for all tests in this module.
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _disable_throttle():
    """Bypass the API throttle so tests run at full speed."""
    with patch("opus_spark_swarm.tools.api_clients.throttle") as mock_throttle:
        mock_throttle.wait.return_value = None
        yield


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _mock_client(json_data, status_code=200, raise_exc=None):
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = json_data
    mock_resp.headers = {}
    mock_resp.content = b"{}"
    if raise_exc:
        mock_resp.raise_for_status.side_effect = raise_exc
    else:
        mock_resp.raise_for_status.return_value = None
    mock_inst = MagicMock()
    mock_inst.get.return_value = mock_resp
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=mock_inst)
    cm.__exit__ = MagicMock(return_value=False)
    return cm


# ========================== lookup_company ==========================

class TestLookupCompany:
    @patch("opus_spark_swarm.agents.research.company_lookup.httpx.Client")
    def test_success(self, mock_cls):
        # OpenCorporates response
        oc_resp = MagicMock()
        oc_resp.status_code = 200
        oc_resp.json.return_value = {
            "results": {"companies": [{"company": {
                "name": "Acme Corp", "jurisdiction_code": "us_ca",
                "company_number": "C123", "current_status": "Active",
                "incorporation_date": "2010-01-15",
                "registered_address_in_full": "123 Main St",
            }}]}
        }
        oc_resp.headers = {}
        oc_resp.raise_for_status.return_value = None

        # Wikidata response
        wd_resp = MagicMock()
        wd_resp.status_code = 200
        wd_resp.json.return_value = {
            "results": {"bindings": [{
                "itemDescription": {"value": "Technology company"},
                "ticker": {"value": "ACME"},
                "founded": {"value": "2010"},
                "hqLabel": {"value": "San Francisco"},
                "industryLabel": {"value": "Software"},
                "item": {"value": "http://www.wikidata.org/entity/Q12345"},
            }]}
        }
        wd_resp.headers = {}
        wd_resp.raise_for_status.return_value = None

        mock_inst = MagicMock()
        mock_inst.get.side_effect = [oc_resp, wd_resp]
        cm = MagicMock()
        cm.__enter__ = MagicMock(return_value=mock_inst)
        cm.__exit__ = MagicMock(return_value=False)
        mock_cls.return_value = cm

        from opus_spark_swarm.agents.research.company_lookup import lookup_company
        result = lookup_company("Acme Corp")
        assert result["name"] == "Acme Corp"
        assert result["ticker"] == "ACME"
        assert result["industry"] == "Software"

    @patch("opus_spark_swarm.agents.research.company_lookup.httpx.Client")
    def test_graceful_failure(self, mock_cls):
        mock_cls.return_value = _mock_client({}, raise_exc=Exception("network down"))
        from opus_spark_swarm.agents.research.company_lookup import lookup_company
        result = lookup_company("Acme Corp")
        # Should not raise; returns a dict with warnings or partial data
        assert isinstance(result, dict)
        assert result["name"] == "Acme Corp"


# ========================== get_market_data ==========================

class TestGetMarketData:
    @patch("opus_spark_swarm.agents.research.market_data.httpx.Client")
    def test_success(self, mock_cls, settings):
        import opus_spark_swarm.agents.research.market_data as md
        md._settings = settings

        mock_cls.return_value = _mock_client({
            "Symbol": "ACME", "Name": "Acme Corp",
            "MarketCapitalization": "5000000000",
            "PERatio": "25", "Sector": "Technology",
            "Industry": "Software", "52WeekHigh": "150",
            "52WeekLow": "90", "DividendYield": "0.01",
            "RevenueTTM": "1200000000", "ProfitMargin": "0.18",
        })
        from opus_spark_swarm.agents.research.market_data import get_market_data
        result = get_market_data("ACME")
        assert result["ticker"] == "ACME"
        assert result["source"] == "Alpha Vantage OVERVIEW"

    def test_missing_key(self):
        import opus_spark_swarm.agents.research.market_data as md
        md._settings = None
        from opus_spark_swarm.agents.research.market_data import get_market_data
        result = get_market_data("ACME")
        assert "error" in result

    @patch("opus_spark_swarm.agents.research.market_data.httpx.Client")
    def test_api_failure(self, mock_cls, settings):
        import opus_spark_swarm.agents.research.market_data as md
        md._settings = settings
        mock_cls.return_value = _mock_client({}, raise_exc=Exception("500"))
        from opus_spark_swarm.agents.research.market_data import get_market_data
        result = get_market_data("ACME")
        assert "error" in result


# ========================== get_recent_news ==========================

class TestGetRecentNews:
    @patch("opus_spark_swarm.agents.research.news.httpx.Client")
    def test_success(self, mock_cls, settings):
        import opus_spark_swarm.agents.research.news as news_mod
        news_mod._settings = settings

        mock_cls.return_value = _mock_client({
            "totalResults": 1,
            "articles": [{
                "title": "Acme growth", "source": {"name": "TechNews"},
                "publishedAt": "2024-06-01", "url": "https://example.com",
                "description": "Record growth for Acme",
            }],
        })
        from opus_spark_swarm.agents.research.news import get_recent_news
        result = get_recent_news("Acme Corp")
        assert result["company"] == "Acme Corp"
        assert len(result["articles"]) == 1
        assert result["source"] == "News API"

    def test_missing_key(self):
        import opus_spark_swarm.agents.research.news as news_mod
        news_mod._settings = None
        from opus_spark_swarm.agents.research.news import get_recent_news
        result = get_recent_news("Acme Corp")
        assert "error" in result

    @patch("opus_spark_swarm.agents.research.news.httpx.Client")
    def test_api_failure(self, mock_cls, settings):
        import opus_spark_swarm.agents.research.news as news_mod
        news_mod._settings = settings
        mock_cls.return_value = _mock_client({}, raise_exc=Exception("403"))
        from opus_spark_swarm.agents.research.news import get_recent_news
        result = get_recent_news("Acme Corp")
        assert "error" in result
        assert result["sentiment_summary"] == "unavailable"


# ========================== get_sec_filings ==========================

class TestGetSecFilings:
    @patch("opus_spark_swarm.agents.research.filings.httpx.Client")
    def test_success_with_cik(self, mock_cls, settings):
        import opus_spark_swarm.agents.research.filings as fil
        fil._settings = settings

        mock_cls.return_value = _mock_client({
            "name": "Acme Corp",
            "filings": {"recent": {
                "form": ["10-K", "10-Q"],
                "filingDate": ["2024-01-01", "2024-04-01"],
                "accessionNumber": ["0001-24-000001", "0001-24-000002"],
                "primaryDocDescription": ["Annual", "Quarterly"],
            }},
        })
        from opus_spark_swarm.agents.research.filings import get_sec_filings
        result = get_sec_filings("1234567", "10-K")
        assert result["company"] == "Acme Corp"
        assert result["source"] == "SEC EDGAR"

    @patch("opus_spark_swarm.agents.research.filings.httpx.Client")
    def test_search_by_name(self, mock_cls, settings):
        import opus_spark_swarm.agents.research.filings as fil
        fil._settings = settings

        mock_cls.return_value = _mock_client({
            "hits": {"hits": [{"_source": {
                "forms": "10-K", "file_date": "2024-01-01",
                "entity_name": "Acme Corp", "entity_id": "1234567",
                "display_names": ["Annual Report"],
            }}]}
        })
        from opus_spark_swarm.agents.research.filings import get_sec_filings
        result = get_sec_filings("Acme Corp", "10-K")
        assert result["company"] == "Acme Corp"

    @patch("opus_spark_swarm.agents.research.filings.httpx.Client")
    def test_failure(self, mock_cls, settings):
        import opus_spark_swarm.agents.research.filings as fil
        fil._settings = settings
        mock_cls.return_value = _mock_client({}, raise_exc=Exception("timeout"))
        from opus_spark_swarm.agents.research.filings import get_sec_filings
        result = get_sec_filings("1234567")
        # Should not raise; returns dict with warnings
        assert isinstance(result, dict)
