"""Jupyter notebook assembly utilities using nbformat."""

from __future__ import annotations

import json
import logging
from typing import Any

import nbformat

logger = logging.getLogger(__name__)

_NB_VERSION = 4


class NotebookBuilder:
    """Programmatically build a Jupyter notebook (nbformat v4)."""

    def __init__(self, title: str, style: str = "narrative") -> None:
        self._nb = nbformat.v4.new_notebook()
        self._nb.metadata.update({
            "opus_spark_swarm": {"title": title, "style": style},
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3.11.0"},
        })
        self.title = title
        self.style = style
        # Add title cell
        self.add_markdown_cell(f"# {title}")

    # ------------------------------------------------------------------ cells

    def add_markdown_cell(self, content: str) -> None:
        """Append a markdown cell."""
        cell = nbformat.v4.new_markdown_cell(content)
        self._nb.cells.append(cell)

    def add_code_cell(self, code: str, metadata: dict[str, Any] | None = None) -> None:
        """Append a code cell with optional metadata."""
        cell = nbformat.v4.new_code_cell(code)
        if metadata:
            cell.metadata.update(metadata)
        self._nb.cells.append(cell)

    def add_setup_cell(self) -> None:
        """Add a standard imports / setup code cell."""
        setup_code = (
            "import pandas as pd\n"
            "import numpy as np\n"
            "import matplotlib.pyplot as plt\n"
            "import json\n"
            "from datetime import datetime, timedelta\n"
            "\n"
            "pd.set_option('display.max_columns', None)\n"
            "plt.style.use('seaborn-v0_8-whitegrid')\n"
            "%matplotlib inline"
        )
        self.add_code_cell(setup_code, metadata={"tags": ["setup"]})

    # ---------------------------------------------------------------- output

    def build(self) -> dict:
        """Return the notebook as a plain dict (nbformat v4 schema)."""
        return json.loads(json.dumps(self._nb, default=str))

    def save(self, path: str) -> None:
        """Write the notebook to *path* as an ``.ipynb`` file."""
        with open(path, "w", encoding="utf-8") as fh:
            nbformat.write(self._nb, fh, version=_NB_VERSION)
        logger.info("Notebook saved to %s", path)

    def to_json(self) -> str:
        """Serialise the notebook to a JSON string."""
        return json.dumps(self.build(), indent=1)


# -------------------------------------------------------------------- helper

def create_requirements_cell(packages: list[str]) -> dict:
    """Return a code-cell dict that pip-installs *packages*."""
    install_line = " ".join(packages)
    code = f"!pip install -q {install_line}"
    cell = nbformat.v4.new_code_cell(code)
    cell.metadata["tags"] = ["requirements"]
    return json.loads(json.dumps(cell, default=str))
