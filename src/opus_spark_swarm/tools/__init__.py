"""Shared tools -- API clients, document parsing, notebook assembly."""

from opus_spark_swarm.tools.api_clients import (
    alpha_vantage_overview,
    fred_series,
    get_company_filings,
    github_repo_search,
    news_api_search,
    opencorporates_search,
    sec_edgar_search,
    throttle,
    wikidata_lookup,
)
from opus_spark_swarm.tools.document_parser import parse_document, parse_pdf, parse_text_file
from opus_spark_swarm.tools.notebook_builder import NotebookBuilder, create_requirements_cell

__all__ = [
    # API clients
    "sec_edgar_search",
    "get_company_filings",
    "opencorporates_search",
    "wikidata_lookup",
    "news_api_search",
    "alpha_vantage_overview",
    "fred_series",
    "github_repo_search",
    "throttle",
    # Document parsing
    "parse_pdf",
    "parse_text_file",
    "parse_document",
    # Notebook builder
    "NotebookBuilder",
    "create_requirements_cell",
]
