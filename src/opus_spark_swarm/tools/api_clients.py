"""Wrapper functions for all public API data sources.

Every function:
- Uses httpx (sync) with a 10-second timeout
- Returns ``{"error": str}`` on failure (never raises)
- Logs requests/responses at DEBUG level
- Respects Retry-After headers
- Enforces a 2-second minimum gap between outbound API calls
"""

from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_TIMEOUT = 10.0

# Minimum seconds between outbound API calls (across all endpoints).
_THROTTLE_SECONDS = 2.0


class _ApiThrottle:
    """Thread-safe rate limiter enforcing a minimum gap between API calls.

    Typical flow: call arrives, throttle waits until the minimum gap since
    the last call has elapsed, then releases. With a 2-second throttle and
    ~1-second response time, this produces a natural cadence of one call
    every ~2 seconds.
    """

    def __init__(self, min_gap: float = _THROTTLE_SECONDS) -> None:
        self._min_gap = min_gap
        self._last_call: float = 0.0
        self._lock = threading.Lock()

    def wait(self) -> None:
        """Block until at least ``min_gap`` seconds have passed since the last call."""
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_call
            if elapsed < self._min_gap:
                delay = self._min_gap - elapsed
                logger.debug("Throttle: waiting %.2fs before next API call", delay)
                time.sleep(delay)
            self._last_call = time.monotonic()


# Single shared throttle instance for all API calls in this process.
throttle = _ApiThrottle()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get(url: str, *, params: dict | None = None, headers: dict | None = None) -> dict:
    """Issue a GET request with throttle and retry-after awareness."""
    throttle.wait()
    logger.debug("GET %s params=%s", url, params)
    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            resp = client.get(url, params=params, headers=headers)

            # Respect Retry-After
            if resp.status_code == 429:
                retry_after = resp.headers.get("Retry-After")
                wait = int(retry_after) if retry_after and retry_after.isdigit() else 5
                logger.debug("Rate-limited; sleeping %ss", wait)
                time.sleep(wait)
                resp = client.get(url, params=params, headers=headers)

            resp.raise_for_status()
            data = resp.json()
            logger.debug("Response %s (%d bytes)", resp.status_code, len(resp.content))
            return data
    except Exception as exc:  # noqa: BLE001
        logger.error("Request failed: %s – %s", url, exc)
        return {"error": str(exc)}


# ---------------------------------------------------------------------------
# 1. SEC EDGAR
# ---------------------------------------------------------------------------

def sec_edgar_search(query: str, *, user_agent: str | None = None) -> dict:
    """Full-text search of SEC EDGAR filings."""
    headers = {"User-Agent": user_agent or "OpusSparkSwarm/1.0 research@example.com"}
    data = _get(
        "https://efts.sec.gov/LATEST/search-index",
        params={"q": query, "dateRange": "custom"},
        headers=headers,
    )
    if "error" in data:
        return data
    return {"filings": data.get("hits", {}).get("hits", []), "total": data.get("hits", {}).get("total", 0)}


def get_company_filings(cik: str, *, user_agent: str | None = None) -> dict:
    """Retrieve submission history for a company by CIK number."""
    padded = cik.zfill(10)
    headers = {"User-Agent": user_agent or "OpusSparkSwarm/1.0 research@example.com"}
    data = _get(f"https://data.sec.gov/submissions/CIK{padded}.json", headers=headers)
    if "error" in data:
        return data
    recent = data.get("filings", {}).get("recent", {})
    filings = []
    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    descs = recent.get("primaryDocDescription", [])
    for i, form in enumerate(forms):
        filings.append({
            "form": form,
            "filing_date": dates[i] if i < len(dates) else None,
            "description": descs[i] if i < len(descs) else None,
        })
    return {
        "filings": filings,
        "company_info": {
            "name": data.get("name"),
            "cik": data.get("cik"),
            "tickers": data.get("tickers", []),
            "exchanges": data.get("exchanges", []),
            "sic": data.get("sic"),
            "sic_description": data.get("sicDescription"),
        },
    }


# ---------------------------------------------------------------------------
# 2. OpenCorporates
# ---------------------------------------------------------------------------

def opencorporates_search(company_name: str) -> dict:
    """Search OpenCorporates company registry."""
    data = _get(
        "https://api.opencorporates.com/v0.4/companies/search",
        params={"q": company_name},
    )
    if "error" in data:
        return data
    raw_companies = data.get("results", {}).get("companies", [])
    companies = []
    for entry in raw_companies:
        c = entry.get("company", {})
        companies.append({
            "name": c.get("name"),
            "jurisdiction": c.get("jurisdiction_code"),
            "status": c.get("current_status"),
            "incorporation_date": c.get("incorporation_date"),
            "company_number": c.get("company_number"),
            "registered_address": c.get("registered_address_in_full"),
        })
    return {"companies": companies}


# ---------------------------------------------------------------------------
# 3. Wikidata
# ---------------------------------------------------------------------------

_WIKIDATA_SPARQL = """\
SELECT ?item ?itemLabel ?itemDescription ?industryLabel ?founded ?hqLabel ?website WHERE {{
  ?item rdfs:label "{name}"@en .
  ?item wdt:P31/wdt:P279* wd:Q4830453 .
  OPTIONAL {{ ?item wdt:P452 ?industry . }}
  OPTIONAL {{ ?item wdt:P571 ?founded . }}
  OPTIONAL {{ ?item wdt:P159 ?hq . }}
  OPTIONAL {{ ?item wdt:P856 ?website . }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" . }}
}} LIMIT 1
"""


def wikidata_lookup(company_name: str) -> dict:
    """Look up a company on Wikidata via SPARQL."""
    sparql = _WIKIDATA_SPARQL.format(name=company_name.replace('"', '\\"'))
    logger.debug("SPARQL query for '%s'", company_name)
    throttle.wait()
    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            resp = client.get(
                "https://query.wikidata.org/sparql",
                params={"query": sparql, "format": "json"},
                headers={"User-Agent": "OpusSparkSwarm/1.0"},
            )
            if resp.status_code == 429:
                retry_after = resp.headers.get("Retry-After")
                wait = int(retry_after) if retry_after and retry_after.isdigit() else 5
                time.sleep(wait)
                resp = client.get(
                    "https://query.wikidata.org/sparql",
                    params={"query": sparql, "format": "json"},
                    headers={"User-Agent": "OpusSparkSwarm/1.0"},
                )
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:  # noqa: BLE001
        logger.error("Wikidata request failed: %s", exc)
        return {"error": str(exc)}

    bindings = data.get("results", {}).get("bindings", [])
    if not bindings:
        return {"name": company_name, "found": False}
    b = bindings[0]

    def _val(key: str) -> str | None:
        return b[key]["value"] if key in b else None

    return {
        "name": _val("itemLabel"),
        "description": _val("itemDescription"),
        "industry": _val("industryLabel"),
        "founded": _val("founded"),
        "headquarters": _val("hqLabel"),
        "website": _val("website"),
        "wikidata_id": (_val("item") or "").rsplit("/", 1)[-1],
        "found": True,
    }


# ---------------------------------------------------------------------------
# 4. News API
# ---------------------------------------------------------------------------

def news_api_search(
    query: str,
    *,
    api_key: str | None = None,
    days: int = 30,
) -> dict:
    """Search recent news articles via NewsAPI."""
    if not api_key:
        return {"error": "news_api_key not configured"}
    from_date = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    data = _get(
        "https://newsapi.org/v2/everything",
        params={"q": query, "sortBy": "relevancy", "from": from_date, "apiKey": api_key},
    )
    if "error" in data:
        return data
    articles = [
        {
            "title": a.get("title"),
            "source": (a.get("source") or {}).get("name"),
            "url": a.get("url"),
            "published_at": a.get("publishedAt"),
            "description": a.get("description"),
        }
        for a in data.get("articles", [])
    ]
    return {"total_results": data.get("totalResults", 0), "articles": articles}


# ---------------------------------------------------------------------------
# 5. Alpha Vantage
# ---------------------------------------------------------------------------

def alpha_vantage_overview(ticker: str, *, api_key: str | None = None) -> dict:
    """Fetch company overview from Alpha Vantage."""
    if not api_key:
        return {"error": "alpha_vantage_api_key not configured"}
    data = _get(
        "https://www.alphavantage.co/query",
        params={"function": "OVERVIEW", "symbol": ticker, "apikey": api_key},
    )
    if "error" in data:
        return data
    if not data or "Symbol" not in data:
        return {"error": f"No overview data for ticker '{ticker}'"}
    return {
        "symbol": data.get("Symbol"),
        "name": data.get("Name"),
        "market_cap": data.get("MarketCapitalization"),
        "pe_ratio": data.get("PERatio"),
        "eps": data.get("EPS"),
        "revenue": data.get("RevenueTTM"),
        "profit_margin": data.get("ProfitMargin"),
        "sector": data.get("Sector"),
        "industry": data.get("Industry"),
        "description": data.get("Description"),
        "exchange": data.get("Exchange"),
        "dividend_yield": data.get("DividendYield"),
        "52_week_high": data.get("52WeekHigh"),
        "52_week_low": data.get("52WeekLow"),
    }


# ---------------------------------------------------------------------------
# 6. FRED (Federal Reserve Economic Data)
# ---------------------------------------------------------------------------

def fred_series(series_id: str, *, api_key: str | None = None) -> dict:
    """Retrieve an economic data series from FRED."""
    if not api_key:
        return {"error": "fred_api_key not configured"}
    data = _get(
        "https://api.stlouisfed.org/fred/series/observations",
        params={"series_id": series_id, "api_key": api_key, "file_type": "json"},
    )
    if "error" in data:
        return data
    observations = [
        {"date": o.get("date"), "value": o.get("value")}
        for o in data.get("observations", [])
    ]
    # Fetch series metadata
    meta = _get(
        "https://api.stlouisfed.org/fred/series",
        params={"series_id": series_id, "api_key": api_key, "file_type": "json"},
    )
    series_info: dict[str, Any] = {}
    if "error" not in meta:
        serieses = meta.get("seriess", [])
        if serieses:
            s = serieses[0]
            series_info = {
                "title": s.get("title"),
                "units": s.get("units"),
                "frequency": s.get("frequency"),
                "seasonal_adjustment": s.get("seasonal_adjustment"),
            }
    return {"observations": observations, "series_info": series_info}


# ---------------------------------------------------------------------------
# 7. GitHub Repositories
# ---------------------------------------------------------------------------

def github_repo_search(query: str, *, token: str | None = None) -> dict:
    """Search GitHub repositories."""
    headers: dict[str, str] = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = _get(
        "https://api.github.com/search/repositories",
        params={"q": query},
        headers=headers,
    )
    if "error" in data:
        return data
    repos = [
        {
            "name": r.get("full_name"),
            "stars": r.get("stargazers_count"),
            "language": r.get("language"),
            "description": r.get("description"),
            "updated_at": r.get("updated_at"),
            "url": r.get("html_url"),
        }
        for r in data.get("items", [])
    ]
    return {"total_count": data.get("total_count", 0), "repos": repos}
