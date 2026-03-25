"""Parse all DAYOURBOT agent definition files and extract metadata."""

import json
import re
from pathlib import Path

agents_dir = Path(r"C:\Users\dayour\.copilot\agents")
agents = []

for md_file in sorted(agents_dir.glob("*.md")):
    text = md_file.read_text(encoding="utf-8", errors="replace")

    fm_match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    meta = {}
    if fm_match:
        mcps_list = []
        for line in fm_match.group(1).strip().split("\n"):
            stripped = line.strip()
            if stripped.startswith("- "):
                mcps_list.append(stripped[2:].strip())
            elif ":" in stripped and not stripped.startswith("#"):
                key, val = stripped.split(":", 1)
                val = val.strip().strip('"').strip("'")
                meta[key.strip()] = val
        if mcps_list:
            meta["mcps"] = mcps_list

    sections = re.findall(r"^##\s+(.+)$", text, re.MULTILINE)
    lines = len(text.split("\n"))

    agents.append({
        "file": md_file.name,
        "name": meta.get("name", md_file.stem),
        "description": meta.get("description", ""),
        "model": meta.get("model", ""),
        "mcps": meta.get("mcps", []),
        "lines": lines,
        "section_count": len(sections),
    })

print(json.dumps(agents, indent=2))
