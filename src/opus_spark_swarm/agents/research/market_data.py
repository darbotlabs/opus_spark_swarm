"""MarketDataAgent -- retrieves financial and sector performance data."""

from __future__ import annotations

import logging
from typing import Annotated

import httpx
from autogen import ConversableAgent

from opus_spark_swarm.agents.base import create_agent
from opus_spark_swarm.config import Settings
from opus_spark_swarm.tools.api_clients import throttle

logger = logging.getLogger(__name__)

SYSTEM_MESSAGE = (
    "You are the **Market Data Agent**. Your job is to retrieve financial "
    "summaries, key ratios, and sector performance data for a given company. "
    "You use the Alpha Vantage API to pull market cap, P/E ratio, revenue, "
    "profit margins, dividend yield, 52-week range, and competitor landscape. "
    "Clearly flag when an API key is missing or calls fail, and present "
    "whatever partial data you can gather. Always cite Alpha Vantage as source."
)

_HTTP_TIMEOUT = 15.0
_AV_BASE = "https://www.alphavantage.co/query"

# Module-level reference so tool closures can read it.
_settings: Settings | None = None


def get_market_data(
    ticker: Annotated[str, "Stock ticker symbol (e.g. AAPL)"],
    *,
    settings: Settings | None = None,
) -> dict:
    """Fetch company overview and key financial metrics from Alpha Vantage."""
    logger.info("Fetching market data for ticker: %s", ticker)

    _effective = settings or _settings
    api_key = ""
    if _effective and _effective.alpha_vantage_api_key:
        api_key = _effective.alpha_vantage_api_key.get_secret_value()

    if not api_key:
        return {
            "ticker": ticker,
            "error": "ALPHA_VANTAGE_API_KEY not configured",
            "warnings": ["Market data unavailable -- set ALPHA_VANTAGE_API_KEY in .env"],
        }

    throttle.wait()
    try:
        with httpx.Client(timeout=_HTTP_TIMEOUT) as client:
            resp = client.get(
                _AV_BASE,
                params={"function": "OVERVIEW", "symbol": ticker, "apikey": api_key},
            )
            resp.raise_for_status()
            data = resp.json()

        if "Symbol" not in data:
            return {"ticker": ticker, "error": "No overview data returned", "raw": data}

        return {
            "ticker": data.get("Symbol"),
            "name": data.get("Name"),
            "market_cap": data.get("MarketCapitalization"),
            "pe_ratio": data.get("PERatio"),
            "sector": data.get("Sector"),
            "industry": data.get("Industry"),
            "52wk_high": data.get("52WeekHigh"),
            "52wk_low": data.get("52WeekLow"),
            "dividend_yield": data.get("DividendYield"),
            "revenue": data.get("RevenueTTM"),
            "profit_margin": data.get("ProfitMargin"),
            "competitors": [],  # Alpha Vantage doesn't provide this directly
            "source": "Alpha Vantage OVERVIEW",
        }
    except Exception as exc:
        logger.warning("Alpha Vantage OVERVIEW failed for %r: %s", ticker, exc)
        return {"ticker": ticker, "error": str(exc), "warnings": [f"API call failed: {exc}"]}


def get_sector_performance(
    sector: Annotated[str, "Sector name (e.g. Technology)"],
    *,
    settings: Settings | None = None,
) -> dict:
    """Fetch sector performance metrics from Alpha Vantage."""
    logger.info("Fetching sector performance for: %s", sector)

    _effective = settings or _settings
    api_key = ""
    if _effective and _effective.alpha_vantage_api_key:
        api_key = _effective.alpha_vantage_api_key.get_secret_value()

    if not api_key:
        return {
            "sector": sector,
            "error": "ALPHA_VANTAGE_API_KEY not configured",
            "warnings": ["Sector data unavailable -- set ALPHA_VANTAGE_API_KEY in .env"],
        }

    throttle.wait()
    try:
        with httpx.Client(timeout=_HTTP_TIMEOUT) as client:
            resp = client.get(
                _AV_BASE,
                params={"function": "SECTOR", "apikey": api_key},
            )
            resp.raise_for_status()
            data = resp.json()

        # Alpha Vantage returns nested dicts keyed by time period.
        periods = [
            "Rank A: Real-Time Performance",
            "Rank B: 1 Day Performance",
            "Rank C: 5 Day Performance",
            "Rank D: 1 Month Performance",
            "Rank E: 3 Month Performance",
            "Rank F: Year-to-Date (YTD) Performance",
            "Rank G: 1 Year Performance",
        ]

        performance: dict = {}
        for period in periods:
            block = data.get(period, {})
            for key, val in block.items():
                if sector.lower() in key.lower():
                    performance[period] = val
                    break

        return {
            "sector": sector,
            "performance": performance,
            "source": "Alpha Vantage SECTOR",
        }
    except Exception as exc:
        logger.warning("Alpha Vantage SECTOR failed: %s", exc)
        return {"sector": sector, "error": str(exc), "warnings": [f"API call failed: {exc}"]}


def create_market_data_agent(settings: Settings) -> ConversableAgent:
    """Create a configured MarketDataAgent with its tools registered.

    Uses AG2 self-registration: same agent registers both for_llm and
    for_execution so it can propose and execute tool calls in a GroupChat.
    """
    global _settings
    _settings = settings

    agent = create_agent(
        name="MarketDataAgent",
        system_message=SYSTEM_MESSAGE,
        settings=settings,
    )

    @agent.register_for_execution()
    @agent.register_for_llm(description="Get financial overview and key metrics for a stock ticker")
    def _get_market_data(
        ticker: Annotated[str, "Stock ticker symbol (e.g. AAPL)"],
    ) -> dict:
        return get_market_data(ticker, settings=settings)

    @agent.register_for_execution()
    @agent.register_for_llm(description="Get sector performance benchmarks")
    def _get_sector_performance(
        sector: Annotated[str, "Sector name (e.g. Technology)"],
    ) -> dict:
        return get_sector_performance(sector, settings=settings)

    return agent
