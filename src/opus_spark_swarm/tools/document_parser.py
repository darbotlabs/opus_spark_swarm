"""Document parsing utilities for PDF and text ingestion."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Optional PDF library -------------------------------------------------
try:
    import pdfplumber  # type: ignore[import-untyped]

    _HAS_PDFPLUMBER = True
except ImportError:
    _HAS_PDFPLUMBER = False


# ---------------------------------------------------------------------------
# PDF parsing
# ---------------------------------------------------------------------------

def parse_pdf(file_path: str) -> dict[str, Any]:
    """Extract text and metadata from a PDF file.

    Tries *pdfplumber* first for high-quality extraction, then falls back to
    a basic binary-text scan if the library is unavailable.
    """
    path = Path(file_path)
    if not path.exists():
        return {"error": f"File not found: {file_path}"}
    if not path.suffix.lower() == ".pdf":
        return {"error": f"Not a PDF file: {file_path}"}

    if _HAS_PDFPLUMBER:
        return _parse_pdf_pdfplumber(path)
    return _parse_pdf_fallback(path)


def _parse_pdf_pdfplumber(path: Path) -> dict[str, Any]:
    """Parse PDF using pdfplumber."""
    try:
        pages_text: list[str] = []
        metadata: dict[str, Any] = {}
        with pdfplumber.open(path) as pdf:
            metadata = dict(pdf.metadata) if pdf.metadata else {}
            for page in pdf.pages:
                text = page.extract_text() or ""
                pages_text.append(text)
        full_text = "\n\n".join(pages_text)
        logger.debug("Parsed PDF %s: %d pages, %d chars", path.name, len(pages_text), len(full_text))
        return {"text": full_text, "pages": len(pages_text), "metadata": metadata}
    except Exception as exc:  # noqa: BLE001
        logger.warning("pdfplumber failed for %s, trying fallback: %s", path, exc)
        return _parse_pdf_fallback(path)


def _parse_pdf_fallback(path: Path) -> dict[str, Any]:
    """Rudimentary text extraction from PDF binary (best-effort)."""
    try:
        raw = path.read_bytes()
        # Extract text between stream markers — very rough heuristic
        text_chunks: list[str] = []
        for segment in raw.split(b"stream"):
            decoded = segment.decode("latin-1", errors="ignore")
            printable = "".join(ch for ch in decoded if ch.isprintable() or ch in "\n\r\t")
            stripped = printable.strip()
            if len(stripped) > 40:
                text_chunks.append(stripped)
        full_text = "\n".join(text_chunks)
        logger.debug("Fallback PDF parse %s: %d chars extracted", path.name, len(full_text))
        return {"text": full_text, "pages": -1, "metadata": {"_parser": "fallback"}}
    except Exception as exc:  # noqa: BLE001
        return {"error": f"PDF parsing failed: {exc}"}


# ---------------------------------------------------------------------------
# Plain-text parsing
# ---------------------------------------------------------------------------

def parse_text_file(file_path: str) -> dict[str, Any]:
    """Read a plain-text / markdown / csv file."""
    path = Path(file_path)
    if not path.exists():
        return {"error": f"File not found: {file_path}"}
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        logger.debug("Parsed text file %s: %d chars", path.name, len(text))
        return {"text": text, "pages": 1, "metadata": {"filename": path.name, "size_bytes": path.stat().st_size}}
    except Exception as exc:  # noqa: BLE001
        return {"error": f"Text parsing failed: {exc}"}


# ---------------------------------------------------------------------------
# Auto-detect dispatcher
# ---------------------------------------------------------------------------

_PDF_SUFFIXES = {".pdf"}
_TEXT_SUFFIXES = {".txt", ".md", ".csv", ".tsv", ".json", ".xml", ".html", ".log", ".rst"}


def parse_document(file_path: str) -> dict[str, Any]:
    """Auto-detect file type and parse accordingly."""
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix in _PDF_SUFFIXES:
        return parse_pdf(file_path)
    if suffix in _TEXT_SUFFIXES:
        return parse_text_file(file_path)

    # Default: attempt text parse
    logger.debug("Unknown suffix '%s', attempting text parse for %s", suffix, path.name)
    return parse_text_file(file_path)
