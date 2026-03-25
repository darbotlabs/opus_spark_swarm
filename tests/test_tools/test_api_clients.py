"""Tests for opus_spark_swarm.tools.api_clients -- all 7 APIs."""

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
# Helper: build a mock httpx.Client context manager
# ---------------------------------------------------------------------------

def _mock_client(json_data: dict, status_code: int = 200, raise_exc: Exception | None = None):
    """Return a mock that replaces httpx.Client as a context manager."""
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = json_data
    mock_resp.headers = {}
    mock_resp.content = b"{}"

    if raise_exc:
        mock_resp.raise_for_status.side_effect = raise_exc
    else:
        mock_resp.raise_for_status.return_value = None

    mock_client_instance = MagicMock()
    mock_client_instance.get.return_value = mock_resp

    mock_client_cls = MagicMock()
    mock_client_cls.__enter__ = MagicMock(return_value=mock_client_instance)
    mock_client_cls.__exit__ = MagicMock(return_value=False)
    return mock_client_cls


# ========================== 1. SEC EDGAR ==========================

class TestSecEdgarSearch:
    @patch("opus_spark_swarm.tools.api_clients.httpx.Client")
    def test_success(self, mock_cls):
        mock_cls.return_value = _mock_client({
            "hits": {"hits": [{"_id": "1"}], "total": 1}
        })
        from opus_spark_swarm.tools.api_clients import sec_edgar_search
        result = sec_edgar_search("Acme Corp")
        assert "filings" in result
        assert result["total"] == 1

    @patch("opus_spark_swarm.tools.api_clients.httpx.Client")
    def test_error(self, mock_cls):
        mock_cls.return_value = _mock_client({}, raise_exc=Exception("timeout"))
        from opus_spark_swarm.tools.api_clients import sec_edgar_search
        result = sec_edgar_search("Acme Corp")
        assert "error" in result


class TestGetCompanyFilings:
    @patch("opus_spark_swarm.tools.api_clients.httpx.Client")
    def test_success(self, mock_cls):
        mock_cls.return_value = _mock_client({
            "name": "Acme Corp",
            "cik": "1234567",
            "tickers": ["ACME"],
            "exchanges": ["NASDAQ"],
            "sic": "7372",
            "sicDescription": "Software",
            "filings": {
                "recent": {
                    "form": ["10-K", "10-Q"],
                    "filingDate": ["2024-01-01", "2024-04-01"],
                    "primaryDocDescription": ["Annual", "Quarterly"],
                }
            },
        })
        from opus_spark_swarm.tools.api_clients import get_company_filings
        result = get_company_filings("1234567")
        assert "filings" in result
        assert len(result["filings"]) == 2
        assert result["company_info"]["name"] == "Acme Corp"

    @patch("opus_spark_swarm.tools.api_clients.httpx.Client")
    def test_error(self, mock_cls):
        mock_cls.return_value = _mock_client({}, raise_exc=Exception("network error"))
        from opus_spark_swarm.tools.api_clients import get_company_filings
        result = get_company_filings("1234567")
        assert "error" in result


# ========================== 2. OpenCorporates ==========================

class TestOpenCorporatesSearch:
    @patch("opus_spark_swarm.tools.api_clients.httpx.Client")
    def test_success(self, mock_cls):
        mock_cls.return_value = _mock_client({
            "results": {
                "companies": [
                    {"company": {
                        "name": "Acme Corp",
                        "jurisdiction_code": "us_ca",
                        "current_status": "Active",
                        "incorporation_date": "2010-01-15",
                        "company_number": "C123",
                        "registered_address_in_full": "123 Main St",
                    }}
                ]
            }
        })
        from opus_spark_swarm.tools.api_clients import opencorporates_search
        result = opencorporates_search("Acme Corp")
        assert "companies" in result
        assert result["companies"][0]["name"] == "Acme Corp"

    @patch("opus_spark_swarm.tools.api_clients.httpx.Client")
    def test_error(self, mock_cls):
        mock_cls.return_value = _mock_client({}, raise_exc=Exception("refused"))
        from opus_spark_swarm.tools.api_clients import opencorporates_search
        result = opencorporates_search("Acme Corp")
        assert "error" in result


# ========================== 3. Wikidata ==========================

class TestWikidataLookup:
    @patch("opus_spark_swarm.tools.api_clients.httpx.Client")
    def test_success(self, mock_cls):
        mock_cls.return_value = _mock_client({
            "results": {
                "bindings": [{
                    "itemLabel": {"value": "Acme Corporation"},
                    "itemDescription": {"value": "Technology company"},
                    "industryLabel": {"value": "Software"},
                    "founded": {"value": "2010-01-15T00:00:00Z"},
                    "hqLabel": {"value": "San Francisco"},
                    "website": {"value": "https://acme.example.com"},
                    "item": {"value": "http://www.wikidata.org/entity/Q12345"},
                }]
            }
        })
        from opus_spark_swarm.tools.api_clients import wikidata_lookup
        result = wikidata_lookup("Acme Corporation")
        assert result["found"] is True
        assert result["name"] == "Acme Corporation"
        assert result["wikidata_id"] == "Q12345"

    @patch("opus_spark_swarm.tools.api_clients.httpx.Client")
    def test_not_found(self, mock_cls):
        mock_cls.return_value = _mock_client({"results": {"bindings": []}})
        from opus_spark_swarm.tools.api_clients import wikidata_lookup
        result = wikidata_lookup("Nonexistent Corp")
        assert result["found"] is False

    @patch("opus_spark_swarm.tools.api_clients.httpx.Client")
    def test_error(self, mock_cls):
        mock_cls.return_value = _mock_client({}, raise_exc=Exception("sparql timeout"))
        from opus_spark_swarm.tools.api_clients import wikidata_lookup
        result = wikidata_lookup("Acme Corporation")
        assert "error" in result


# ========================== 4. News API ==========================

class TestNewsApiSearch:
    @patch("opus_spark_swarm.tools.api_clients.httpx.Client")
    def test_success(self, mock_cls):
        mock_cls.return_value = _mock_client({
            "totalResults": 2,
            "articles": [
                {
                    "title": "Acme grows",
                    "source": {"name": "TechNews"},
                    "url": "https://example.com/1",
                    "publishedAt": "2024-06-01",
                    "description": "Record growth",
                },
            ],
        })
        from opus_spark_swarm.tools.api_clients import news_api_search
        result = news_api_search("Acme Corp", api_key="test-key")
        assert result["total_results"] == 2
        assert len(result["articles"]) == 1
        assert result["articles"][0]["title"] == "Acme grows"

    def test_missing_key(self):
        from opus_spark_swarm.tools.api_clients import news_api_search
        result = news_api_search("Acme Corp")
        assert "error" in result
        assert "not configured" in result["error"]

    @patch("opus_spark_swarm.tools.api_clients.httpx.Client")
    def test_error(self, mock_cls):
        mock_cls.return_value = _mock_client({}, raise_exc=Exception("403 Forbidden"))
        from opus_spark_swarm.tools.api_clients import news_api_search
        result = news_api_search("Acme Corp", api_key="test-key")
        assert "error" in result


# ========================== 5. Alpha Vantage ==========================

class TestAlphaVantageOverview:
    @patch("opus_spark_swarm.tools.api_clients.httpx.Client")
    def test_success(self, mock_cls):
        mock_cls.return_value = _mock_client({
            "Symbol": "ACME",
            "Name": "Acme Corp",
            "MarketCapitalization": "5000000000",
            "PERatio": "25.3",
            "EPS": "3.2",
            "RevenueTTM": "1200000000",
            "ProfitMargin": "0.18",
            "Sector": "Technology",
            "Industry": "Software",
            "Description": "A tech company",
            "Exchange": "NASDAQ",
            "DividendYield": "0.012",
            "52WeekHigh": "150.00",
            "52WeekLow": "90.00",
        })
        from opus_spark_swarm.tools.api_clients import alpha_vantage_overview
        result = alpha_vantage_overview("ACME", api_key="test-key")
        assert result["symbol"] == "ACME"
        assert result["name"] == "Acme Corp"
        assert result["market_cap"] == "5000000000"

    def test_missing_key(self):
        from opus_spark_swarm.tools.api_clients import alpha_vantage_overview
        result = alpha_vantage_overview("ACME")
        assert "error" in result

    @patch("opus_spark_swarm.tools.api_clients.httpx.Client")
    def test_error(self, mock_cls):
        mock_cls.return_value = _mock_client({}, raise_exc=Exception("rate limit"))
        from opus_spark_swarm.tools.api_clients import alpha_vantage_overview
        result = alpha_vantage_overview("ACME", api_key="test-key")
        assert "error" in result


# ========================== 6. FRED ==========================

class TestFredSeries:
    @patch("opus_spark_swarm.tools.api_clients.httpx.Client")
    def test_success(self, mock_cls):
        # First call returns observations, second call returns metadata
        resp1 = MagicMock()
        resp1.status_code = 200
        resp1.json.return_value = {
            "observations": [
                {"date": "2024-01-01", "value": "3.5"},
                {"date": "2024-02-01", "value": "3.6"},
            ]
        }
        resp1.headers = {}
        resp1.content = b"{}"
        resp1.raise_for_status.return_value = None

        resp2 = MagicMock()
        resp2.status_code = 200
        resp2.json.return_value = {
            "seriess": [{
                "title": "GDP Growth",
                "units": "Percent",
                "frequency": "Monthly",
                "seasonal_adjustment": "Seasonally Adjusted",
            }]
        }
        resp2.headers = {}
        resp2.content = b"{}"
        resp2.raise_for_status.return_value = None

        mock_client_instance = MagicMock()
        mock_client_instance.get.side_effect = [resp1, resp2]
        mock_client_cm = MagicMock()
        mock_client_cm.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_cm.__exit__ = MagicMock(return_value=False)
        mock_cls.return_value = mock_client_cm

        from opus_spark_swarm.tools.api_clients import fred_series
        result = fred_series("GDP", api_key="test-key")
        assert "observations" in result
        assert len(result["observations"]) == 2
        assert "series_info" in result

    def test_missing_key(self):
        from opus_spark_swarm.tools.api_clients import fred_series
        result = fred_series("GDP")
        assert "error" in result

    @patch("opus_spark_swarm.tools.api_clients.httpx.Client")
    def test_error(self, mock_cls):
        mock_cls.return_value = _mock_client({}, raise_exc=Exception("server error"))
        from opus_spark_swarm.tools.api_clients import fred_series
        result = fred_series("GDP", api_key="test-key")
        assert "error" in result


# ========================== 7. GitHub ==========================

class TestGithubRepoSearch:
    @patch("opus_spark_swarm.tools.api_clients.httpx.Client")
    def test_success(self, mock_cls):
        mock_cls.return_value = _mock_client({
            "total_count": 1,
            "items": [{
                "full_name": "acme/repo",
                "stargazers_count": 100,
                "language": "Python",
                "description": "An awesome repo",
                "updated_at": "2024-06-01",
                "html_url": "https://github.com/acme/repo",
            }],
        })
        from opus_spark_swarm.tools.api_clients import github_repo_search
        result = github_repo_search("acme", token="ghp_test")
        assert result["total_count"] == 1
        assert result["repos"][0]["name"] == "acme/repo"

    @patch("opus_spark_swarm.tools.api_clients.httpx.Client")
    def test_no_token(self, mock_cls):
        mock_cls.return_value = _mock_client({"total_count": 0, "items": []})
        from opus_spark_swarm.tools.api_clients import github_repo_search
        result = github_repo_search("acme")
        assert result["total_count"] == 0

    @patch("opus_spark_swarm.tools.api_clients.httpx.Client")
    def test_error(self, mock_cls):
        mock_cls.return_value = _mock_client({}, raise_exc=Exception("rate limited"))
        from opus_spark_swarm.tools.api_clients import github_repo_search
        result = github_repo_search("acme")
        assert "error" in result
