"""Tests for opus_spark_swarm.tools.notebook_builder."""

from __future__ import annotations

import json
import os

import pytest

from opus_spark_swarm.tools.notebook_builder import NotebookBuilder, create_requirements_cell


class TestNotebookBuilderInit:
    def test_creates_valid_notebook(self):
        nb = NotebookBuilder("Test Notebook")
        result = nb.build()
        assert result["nbformat"] == 4
        assert "cells" in result

    def test_title_cell_added(self):
        nb = NotebookBuilder("My Title")
        result = nb.build()
        assert any("# My Title" in (c.get("source", "") or "") for c in result["cells"])

    def test_metadata_contains_opus_spark(self):
        nb = NotebookBuilder("Test", style="technical")
        result = nb.build()
        meta = result.get("metadata", {}).get("opus_spark_swarm", {})
        assert meta["title"] == "Test"
        assert meta["style"] == "technical"

    def test_empty_notebook_has_title_cell_only(self):
        nb = NotebookBuilder("Empty")
        result = nb.build()
        # Title cell is the only cell added at init
        assert len(result["cells"]) == 1


class TestNotebookBuilderCells:
    def test_add_markdown_cell(self):
        nb = NotebookBuilder("Test")
        nb.add_markdown_cell("## Section")
        result = nb.build()
        md_cells = [c for c in result["cells"] if c["cell_type"] == "markdown"]
        assert any("## Section" in c["source"] for c in md_cells)

    def test_add_code_cell(self):
        nb = NotebookBuilder("Test")
        nb.add_code_cell("print('hello')")
        result = nb.build()
        code_cells = [c for c in result["cells"] if c["cell_type"] == "code"]
        assert any("print('hello')" in c["source"] for c in code_cells)

    def test_add_code_cell_with_metadata(self):
        nb = NotebookBuilder("Test")
        nb.add_code_cell("x = 1", metadata={"tags": ["data"]})
        result = nb.build()
        code_cells = [c for c in result["cells"] if c["cell_type"] == "code"]
        tagged = [c for c in code_cells if "data" in c.get("metadata", {}).get("tags", [])]
        assert len(tagged) == 1

    def test_add_setup_cell(self):
        nb = NotebookBuilder("Test")
        nb.add_setup_cell()
        result = nb.build()
        code_cells = [c for c in result["cells"] if c["cell_type"] == "code"]
        setup_cells = [c for c in code_cells if "setup" in c.get("metadata", {}).get("tags", [])]
        assert len(setup_cells) == 1
        assert "import pandas" in setup_cells[0]["source"]


class TestNotebookBuilderOutput:
    def test_build_returns_dict(self):
        nb = NotebookBuilder("Test")
        result = nb.build()
        assert isinstance(result, dict)
        assert result["nbformat"] == 4

    def test_to_json_returns_valid_json(self):
        nb = NotebookBuilder("Test")
        nb.add_code_cell("x = 42")
        json_str = nb.to_json()
        parsed = json.loads(json_str)
        assert parsed["nbformat"] == 4

    def test_save_writes_file(self, tmp_path):
        nb = NotebookBuilder("Saved Notebook")
        nb.add_markdown_cell("## Intro")
        nb.add_code_cell("print('saved')")
        path = str(tmp_path / "test_notebook.ipynb")
        nb.save(path)
        assert os.path.exists(path)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["nbformat"] == 4
        assert len(data["cells"]) >= 2


class TestCreateRequirementsCell:
    def test_creates_requirements_cell(self):
        cell = create_requirements_cell(["pandas", "numpy", "matplotlib"])
        assert cell["cell_type"] == "code"
        assert "pip install" in cell["source"]
        assert "pandas" in cell["source"]
        assert "requirements" in cell.get("metadata", {}).get("tags", [])

    def test_single_package(self):
        cell = create_requirements_cell(["httpx"])
        assert "httpx" in cell["source"]

    def test_empty_packages(self):
        cell = create_requirements_cell([])
        assert "pip install" in cell["source"]
