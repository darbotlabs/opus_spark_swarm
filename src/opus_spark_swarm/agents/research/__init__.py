"""Research agent team -- company intelligence gathering."""

from __future__ import annotations

from autogen import ConversableAgent

from opus_spark_swarm.config import Settings

from .company_lookup import create_company_lookup_agent, lookup_company
from .filings import create_filings_agent, get_sec_filings
from .market_data import create_market_data_agent, get_market_data, get_sector_performance
from .news import create_news_agent, get_recent_news

# Convenience aliases matching the agent class names from the README.
CompanyLookupAgent = create_company_lookup_agent
MarketDataAgent = create_market_data_agent
NewsAgent = create_news_agent
FilingsAgent = create_filings_agent

__all__ = [
    "CompanyLookupAgent",
    "MarketDataAgent",
    "NewsAgent",
    "FilingsAgent",
    "create_company_lookup_agent",
    "create_market_data_agent",
    "create_news_agent",
    "create_filings_agent",
    "create_research_team",
    "lookup_company",
    "get_market_data",
    "get_sector_performance",
    "get_recent_news",
    "get_sec_filings",
]


def create_research_team(settings: Settings) -> list[ConversableAgent]:
    """Create all research agents with tools registered.

    Returns a list of four configured :class:`ConversableAgent` instances:
    ``[CompanyLookupAgent, MarketDataAgent, NewsAgent, FilingsAgent]``.

    Each agent has its API-calling tools pre-registered and is ready to
    participate in an AG2 GroupChat.
    """
    return [
        create_company_lookup_agent(settings),
        create_market_data_agent(settings),
        create_news_agent(settings),
        create_filings_agent(settings),
    ]
