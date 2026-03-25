"""FilingsAgent -- retrieves SEC EDGAR filings for public companies."""

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
    "You are the **Filings Agent**. Your job is to retrieve public company "
    "filings from the SEC EDGAR system. Given a CIK number (or company name "
    "for search), you query the SEC EDGAR full-text search and submissions "
    "APIs to find 10-K, 10-Q, 8-K, and other filing types. You return a list "
    "of recent filings with type, date, URL, and description. Always include "
    "the SEC_EDGAR_USER_AGENT header as required by SEC fair-access policy. "
    "If the user agent is not configured, warn but attempt a best-effort call."
)

_HTTP_TIMEOUT = 20.0
_EDGAR_SEARCH = "https://efts.sec.gov/LATEST/search-index"
_EDGAR_SUBMISSIONS = "https://data.sec.gov/submissions/CIK{cik}.json"

_settings: Settings | None = None


def _edgar_headers(settings: Settings | None = None) -> dict[str, str]:
    """Build request headers required by SEC EDGAR fair-access policy."""
    ua = "OpusSparkSwarm/1.0 research@example.com"
    _effective = settings or _settings
    if _effective and _effective.sec_edgar_user_agent:
        ua = _effective.sec_edgar_user_agent
    return {"User-Agent": ua, "Accept": "application/json"}


def _pad_cik(cik: str) -> str:
    """Zero-pad a CIK to 10 digits as required by EDGAR URLs."""
    return cik.zfill(10)


def _fetch_submissions(cik: str, settings: Settings | None = None) -> dict:
    """Fetch recent filings from the EDGAR submissions endpoint."""
    url = _EDGAR_SUBMISSIONS.format(cik=_pad_cik(cik))
    throttle.wait()
    try:
        with httpx.Client(timeout=_HTTP_TIMEOUT) as client:
            resp = client.get(url, headers=_edgar_headers(settings))
            resp.raise_for_status()
            data = resp.json()

        recent = data.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        dates = recent.get("filingDate", [])
        accessions = recent.get("accessionNumber", [])
        descriptions = recent.get("primaryDocDescription", [])

        filings = []
        for i in range(min(len(forms), 20)):
            accession_clean = accessions[i].replace("-", "") if i < len(accessions) else ""
            filings.append(
                {
                    "type": forms[i] if i < len(forms) else None,
                    "date": dates[i] if i < len(dates) else None,
                    "url": (
                        f"https://www.sec.gov/Archives/edgar/data/{_pad_cik(cik)}/{accession_clean}"
                        if accession_clean
                        else None
                    ),
                    "description": descriptions[i] if i < len(descriptions) else None,
                }
            )

        company_name = data.get("name", "")
        return {"company": company_name, "cik": cik, "filings": filings}
    except Exception as exc:
        logger.warning("EDGAR submissions fetch failed for CIK %s: %s", cik, exc)
        return {"cik": cik, "filings": [], "_warning": f"EDGAR submissions failed: {exc}"}


def _search_edgar(company: str, filing_type: str, settings: Settings | None = None) -> dict:
    """Full-text search EDGAR for filings matching a company name."""
    start_dt = (datetime.now(timezone.utc) - timedelta(days=365 * 2)).strftime("%Y-%m-%d")
    end_dt = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    throttle.wait()
    try:
        with httpx.Client(timeout=_HTTP_TIMEOUT) as client:
            resp = client.get(
                _EDGAR_SEARCH,
                params={
                    "q": company,
                    "dateRange": "custom",
                    "startdt": start_dt,
                    "enddt": end_dt,
                    "forms": filing_type,
                },
                headers=_edgar_headers(settings),
            )
            resp.raise_for_status()
            data = resp.json()

        hits = data.get("hits", {}).get("hits", [])
        results = []
        for hit in hits[:10]:
            src = hit.get("_source", {})
            results.append(
                {
                    "type": src.get("forms"),
                    "date": src.get("file_date"),
                    "entity": src.get("entity_name"),
                    "url": f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={src.get('entity_id', '')}",
                    "description": src.get("display_names"),
                }
            )
        return {"search_results": results}
    except Exception as exc:
        logger.warning("EDGAR search failed for %r: %s", company, exc)
        return {"search_results": [], "_warning": f"EDGAR search failed: {exc}"}


def get_sec_filings(
    cik: Annotated[str, "SEC CIK number (or company name for search fallback)"],
    filing_type: Annotated[str, "Filing type filter, e.g. 10-K, 10-Q, 8-K"] = "10-K",
    *,
    settings: Settings | None = None,
) -> dict:
    """Retrieve SEC EDGAR filings for a company by CIK or name search."""
    logger.info("Fetching SEC filings for CIK/company=%s, type=%s", cik, filing_type)

    warnings: list[str] = []
    filings: list[dict] = []
    company = ""

    if cik.strip().isdigit():
        sub = _fetch_submissions(cik, settings=settings)
        if sub.get("_warning"):
            warnings.append(sub["_warning"])
        filings = sub.get("filings", [])
        company = sub.get("company", "")

        # Filter to requested filing type.
        if filings and filing_type:
            filings = [f for f in filings if f.get("type", "").startswith(filing_type)]
    else:
        # Treat as company name search.
        search = _search_edgar(cik, filing_type, settings=settings)
        if search.get("_warning"):
            warnings.append(search["_warning"])
        filings = search.get("search_results", [])
        company = cik

    # Identify most recent 10-K for summary reference.
    recent_10k = next(
        (f for f in filings if f.get("type", "").startswith("10-K")),
        None,
    )
    recent_10k_summary = (
        f"Most recent 10-K filed {recent_10k['date']}: {recent_10k.get('url', 'N/A')}"
        if recent_10k
        else "No recent 10-K found in results"
    )

    result: dict = {
        "company": company,
        "cik": cik,
        "filing_type_filter": filing_type,
        "filings": filings,
        "recent_10k_summary": recent_10k_summary,
        "source": "SEC EDGAR",
    }
    if warnings:
        result["warnings"] = warnings
    return result


def create_filings_agent(settings: Settings) -> ConversableAgent:
    """Create a configured FilingsAgent with its tool registered.

    Uses AG2 self-registration: same agent registers both for_llm and
    for_execution so it can propose and execute tool calls in a GroupChat.
    """
    global _settings
    _settings = settings

    agent = create_agent(
        name="FilingsAgent",
        system_message=SYSTEM_MESSAGE,
        settings=settings,
    )

    @agent.register_for_execution()
    @agent.register_for_llm(description="Retrieve SEC EDGAR filings for a company by CIK or name")
    def _get_sec_filings(
        cik: Annotated[str, "SEC CIK number (or company name for search fallback)"],
        filing_type: Annotated[str, "Filing type filter, e.g. 10-K, 10-Q, 8-K"] = "10-K",
    ) -> dict:
        return get_sec_filings(cik, filing_type, settings=settings)

    return agent
