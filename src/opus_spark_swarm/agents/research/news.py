"""NewsAgent -- retrieves recent news articles and sentiment signals."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated

import httpx
from autogen import ConversableAgent

from opus_spark_swarm.agents.base import create_agent
from opus_spark_swarm.config import Settings
from opus_spark_swarm.tools.api_clients import throttle

logger = logging.getLogger(__name__)

SYSTEM_MESSAGE = (
    "You are the **News Agent**. Your job is to retrieve and summarise recent "
    "news articles about a company. You query the News API for headlines sorted "
    "by relevancy, extract title, source, date, URL, and a brief summary for "
    "each article, and provide an overall sentiment summary. When the NEWS_API_KEY "
    "is not configured, clearly state that news data is unavailable and suggest "
    "the user set the key in .env."
)

_HTTP_TIMEOUT = 15.0
_NEWS_BASE = "https://newsapi.org/v2/everything"

_settings: Settings | None = None


def get_recent_news(
    company_name: Annotated[str, "Company name to search for news"],
    days: Annotated[int, "Number of past days to search (default 30)"] = 30,
    *,
    settings: Settings | None = None,
) -> dict:
    """Fetch recent news articles about a company via the News API."""
    logger.info("Fetching news for %r (last %d days)", company_name, days)

    _effective = settings or _settings
    api_key = ""
    if _effective and _effective.news_api_key:
        api_key = _effective.news_api_key.get_secret_value()

    if not api_key:
        return {
            "company": company_name,
            "articles": [],
            "sentiment_summary": "unavailable",
            "error": "NEWS_API_KEY not configured",
            "warnings": ["News data unavailable -- set NEWS_API_KEY in .env"],
        }

    from_date = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")

    throttle.wait()
    try:
        with httpx.Client(timeout=_HTTP_TIMEOUT) as client:
            resp = client.get(
                _NEWS_BASE,
                params={
                    "q": company_name,
                    "from": from_date,
                    "sortBy": "relevancy",
                    "language": "en",
                    "pageSize": 10,
                    "apiKey": api_key,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        raw_articles = data.get("articles", [])
        articles = []
        for art in raw_articles:
            articles.append(
                {
                    "title": art.get("title"),
                    "source": (art.get("source") or {}).get("name"),
                    "published": art.get("publishedAt"),
                    "url": art.get("url"),
                    "summary": art.get("description"),
                }
            )

        # Basic keyword-based sentiment heuristic (the LLM will do deeper analysis).
        positive_kw = {"growth", "profit", "surge", "gain", "record", "expansion", "innovation"}
        negative_kw = {"loss", "decline", "layoff", "lawsuit", "scandal", "drop", "downturn", "risk"}
        pos = neg = 0
        for art in articles:
            text = f"{art.get('title', '')} {art.get('summary', '')}".lower()
            pos += sum(1 for w in positive_kw if w in text)
            neg += sum(1 for w in negative_kw if w in text)

        if pos > neg:
            sentiment = "generally positive"
        elif neg > pos:
            sentiment = "generally negative"
        else:
            sentiment = "mixed / neutral"

        return {
            "company": company_name,
            "articles": articles,
            "total_results": data.get("totalResults", len(articles)),
            "sentiment_summary": sentiment,
            "source": "News API",
        }
    except Exception as exc:
        logger.warning("News API call failed for %r: %s", company_name, exc)
        return {
            "company": company_name,
            "articles": [],
            "sentiment_summary": "unavailable",
            "error": str(exc),
            "warnings": [f"News API call failed: {exc}"],
        }


def create_news_agent(settings: Settings) -> ConversableAgent:
    """Create a configured NewsAgent with its tool registered.

    Uses AG2 self-registration: same agent registers both for_llm and
    for_execution so it can propose and execute tool calls in a GroupChat.
    """
    global _settings
    _settings = settings

    agent = create_agent(
        name="NewsAgent",
        system_message=SYSTEM_MESSAGE,
        settings=settings,
    )

    @agent.register_for_execution()
    @agent.register_for_llm(description="Get recent news articles about a company")
    def _get_recent_news(
        company_name: Annotated[str, "Company name to search for news"],
        days: Annotated[int, "Number of past days to search (default 30)"] = 30,
    ) -> dict:
        return get_recent_news(company_name, days, settings=settings)

    return agent
