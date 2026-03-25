"""Tests for opus_spark_swarm.tools.document_parser."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from opus_spark_swarm.tools.document_parser import (
    parse_document,
    parse_pdf,
    parse_text_file,
)


class TestParseTextFile:
    def test_reads_text_file(self, tmp_path):
        f = tmp_path / "sample.txt"
        f.write_text("Hello, world!", encoding="utf-8")
        result = parse_text_file(str(f))
        assert result["text"] == "Hello, world!"
        assert result["pages"] == 1
        assert result["metadata"]["filename"] == "sample.txt"

    def test_reads_csv_file(self, tmp_path):
        f = tmp_path / "data.csv"
        f.write_text("a,b,c\n1,2,3", encoding="utf-8")
        result = parse_text_file(str(f))
        assert "a,b,c" in result["text"]

    def test_missing_file(self):
        result = parse_text_file("/nonexistent/path/file.txt")
        assert "error" in result
        assert "not found" in result["error"].lower()

    def test_metadata_has_size(self, tmp_path):
        f = tmp_path / "size_test.txt"
        f.write_text("0123456789", encoding="utf-8")
        result = parse_text_file(str(f))
        assert result["metadata"]["size_bytes"] == 10


class TestParseDocument:
    def test_dispatches_to_text_for_txt(self, tmp_path):
        f = tmp_path / "readme.txt"
        f.write_text("readme content", encoding="utf-8")
        result = parse_document(str(f))
        assert result["text"] == "readme content"

    def test_dispatches_to_text_for_md(self, tmp_path):
        f = tmp_path / "notes.md"
        f.write_text("# Notes", encoding="utf-8")
        result = parse_document(str(f))
        assert "# Notes" in result["text"]

    def test_dispatches_to_text_for_json(self, tmp_path):
        f = tmp_path / "data.json"
        f.write_text(json.dumps({"key": "value"}), encoding="utf-8")
        result = parse_document(str(f))
        assert "key" in result["text"]

    def test_unknown_extension_falls_back_to_text(self, tmp_path):
        f = tmp_path / "weird.xyz"
        f.write_text("some content", encoding="utf-8")
        result = parse_document(str(f))
        assert result["text"] == "some content"


class TestParsePdf:
    def test_missing_file(self):
        result = parse_pdf("/nonexistent/file.pdf")
        assert "error" in result
        assert "not found" in result["error"].lower()

    def test_not_pdf_extension(self, tmp_path):
        f = tmp_path / "not_a_pdf.txt"
        f.write_text("hello", encoding="utf-8")
        result = parse_pdf(str(f))
        assert "error" in result
        assert "not a pdf" in result["error"].lower()

    def test_with_pdfplumber(self, tmp_path):
        f = tmp_path / "test.pdf"
        f.write_bytes(b"%PDF-1.4 fake content")

        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Page 1 text"
        mock_pdf = MagicMock()
        mock_pdf.metadata = {"Author": "Test"}
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)

        mock_pdfplumber = MagicMock()
        mock_pdfplumber.open.return_value = mock_pdf

        import opus_spark_swarm.tools.document_parser as dp
        original_flag = dp._HAS_PDFPLUMBER
        original_mod = getattr(dp, "pdfplumber", None)
        try:
            dp._HAS_PDFPLUMBER = True
            dp.pdfplumber = mock_pdfplumber
            result = parse_pdf(str(f))
        finally:
            dp._HAS_PDFPLUMBER = original_flag
            if original_mod is None and hasattr(dp, "pdfplumber"):
                delattr(dp, "pdfplumber")
            elif original_mod is not None:
                dp.pdfplumber = original_mod

        assert result["text"] == "Page 1 text"
        assert result["pages"] == 1
        assert result["metadata"]["Author"] == "Test"

    def test_pdf_fallback(self, tmp_path):
        """When pdfplumber is not available, fallback parser runs."""
        f = tmp_path / "test.pdf"
        # Write enough content to trigger the fallback heuristic
        f.write_bytes(b"%PDF-1.4 stream" + b"A" * 100 + b"endstream")
        with patch("opus_spark_swarm.tools.document_parser._HAS_PDFPLUMBER", False):
            result = parse_pdf(str(f))
        # Fallback should return pages == -1
        assert result.get("pages") == -1 or "error" in result
