"""CompanyLookupAgent -- resolves a company name to structured identifiers."""

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
    "You are the **Company Lookup Agent**. Your job is to resolve a given "
    "company name into structured identifiers (ticker symbol, SEC CIK number, "
    "industry classification, headquarters, founding date, and a short "
    "description). You query OpenCorporates and Wikidata to gather this "
    "information. When results are ambiguous, prefer the most prominent or "
    "publicly-traded entity. Always cite the data source for each field."
)

_HTTP_TIMEOUT = 15.0


def _query_opencorporates(name: str) -> dict:
    """Search OpenCorporates for company registration data."""
    throttle.wait()
    url = "https://api.opencorporates.com/v0.4/companies/search"
    try:
        with httpx.Client(timeout=_HTTP_TIMEOUT) as client:
            resp = client.get(url, params={"q": name, "per_page": 3})
            resp.raise_for_status()
            data = resp.json()
        companies = data.get("results", {}).get("companies", [])
        if not companies:
            return {}
        top = companies[0].get("company", {})
        return {
            "name": top.get("name"),
            "jurisdiction": top.get("jurisdiction_code"),
            "company_number": top.get("company_number"),
            "status": top.get("current_status"),
            "incorporation_date": top.get("incorporation_date"),
            "registered_address": top.get("registered_address_in_full"),
            "source": "OpenCorporates",
        }
    except Exception as exc:
        logger.warning("OpenCorporates lookup failed for %r: %s", name, exc)
        return {"_warning": f"OpenCorporates unavailable: {exc}"}


def _query_wikidata(name: str) -> dict:
    """Run a Wikidata SPARQL query for company metadata."""
    throttle.wait()
    sparql = f"""
    SELECT ?item ?itemLabel ?itemDescription ?ticker ?founded ?hq ?hqLabel ?industryLabel WHERE {{
      ?item rdfs:label "{name}"@en .
      ?item wdt:P31/wdt:P279* wd:Q4830453 .
      OPTIONAL {{ ?item wdt:P249 ?ticker . }}
      OPTIONAL {{ ?item wdt:P571 ?founded . }}
      OPTIONAL {{ ?item wdt:P159 ?hq . }}
      OPTIONAL {{ ?item wdt:P452 ?industry . }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" . }}
    }}
    LIMIT 1
    """
    url = "https://query.wikidata.org/sparql"
    try:
        with httpx.Client(timeout=_HTTP_TIMEOUT) as client:
            resp = client.get(
                url,
                params={"query": sparql},
                headers={"Accept": "application/sparql-results+json"},
            )
            resp.raise_for_status()
            data = resp.json()
        bindings = data.get("results", {}).get("bindings", [])
        if not bindings:
            return {}
        b = bindings[0]
        return {
            "wikidata_id": b.get("item", {}).get("value", "").rsplit("/", 1)[-1],
            "description": b.get("itemDescription", {}).get("value"),
            "ticker": b.get("ticker", {}).get("value"),
            "founded": b.get("founded", {}).get("value"),
            "hq": b.get("hqLabel", {}).get("value"),
            "industry": b.get("industryLabel", {}).get("value"),
            "source": "Wikidata",
        }
    except Exception as exc:
        logger.warning("Wikidata lookup failed for %r: %s", name, exc)
        return {"_warning": f"Wikidata unavailable: {exc}"}


def lookup_company(
    name: Annotated[str, "Company name to look up"],
) -> dict:
    """Resolve a company name to structured identifiers via OpenCorporates and Wikidata."""
    logger.info("Looking up company: %s", name)
    oc_data = _query_opencorporates(name)
    wd_data = _query_wikidata(name)

    warnings = [
        v for v in (oc_data.get("_warning"), wd_data.get("_warning")) if v
    ]

    result: dict = {
        "name": oc_data.get("name") or wd_data.get("description") and name or name,
        "ticker": wd_data.get("ticker"),
        "cik": None,  # CIK resolved downstream by FilingsAgent
        "industry": wd_data.get("industry"),
        "hq": wd_data.get("hq") or oc_data.get("registered_address"),
        "founded": wd_data.get("founded") or oc_data.get("incorporation_date"),
        "description": wd_data.get("description"),
        "identifiers": {
            "opencorporates": {
                "jurisdiction": oc_data.get("jurisdiction"),
                "company_number": oc_data.get("company_number"),
            },
            "wikidata_id": wd_data.get("wikidata_id"),
        },
    }
    if warnings:
        result["warnings"] = warnings
    return result


def create_company_lookup_agent(settings: Settings) -> ConversableAgent:
    """Create a configured CompanyLookupAgent with its tool registered.

    Uses the standard AG2 self-registration pattern: the same agent
    registers both ``for_llm`` (so it can propose tool calls) and
    ``for_execution`` (so it can execute them within a GroupChat).
    """
    agent = create_agent(
        name="CompanyLookupAgent",
        system_message=SYSTEM_MESSAGE,
        settings=settings,
    )

    @agent.register_for_execution()
    @agent.register_for_llm(description="Look up a company by name and resolve to structured identifiers")
    def _lookup_company(
        name: Annotated[str, "Company name to look up"],
    ) -> dict:
        return lookup_company(name)

    return agent
