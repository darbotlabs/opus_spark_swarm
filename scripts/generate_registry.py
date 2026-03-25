"""Generate the swarm_registry.json from parsed agent metadata and layer taxonomy."""

import json
from pathlib import Path

LAYER_TAXONOMY = {
    "strategy_org": {
        "label": "Strategy & Org",
        "purpose": "Org-level planning, customer acceleration, engineering IP",
        "agents": ["dayour-cape", "dayour-cat", "dayour-bat"],
    },
    "platform_specialists": {
        "label": "Platform Specialists",
        "purpose": "Deep expertise in Copilot Studio, Power Platform, Dynamics 365, Fabric, Azure, Purview",
        "agents": [
            "dayour-studio", "dayour-pplat", "dayour-dynamics", "dayour-fabric",
            "dayour-azure", "dayour-purview", "dayour-copilot", "dayour-dataverse",
            "dayour-entra", "dayour-foundry", "dayour-graph", "dayour-intune",
            "dayour-m365", "dayour-onedrive", "dayour-sharepoint", "dayour-teams",
            "dayour-viva",
        ],
    },
    "engineering": {
        "label": "Engineering",
        "purpose": "Code analysis, system design/ADRs, UI/UX",
        "agents": [
            "dayour-swe", "dayour-architect", "dayour-design", "dayour-dev",
            "dayour-test", "dayour-qa", "dayour-sre", "dayour-security",
            "dayour-data-eng", "dayour-gitops", "dayour-github", "dayour-network",
            "dayour-integration", "dayour-finops",
        ],
    },
    "content_docs": {
        "label": "Content & Docs",
        "purpose": "Technical docs, presentations, note distillation",
        "agents": [
            "dayour-word", "dayour-ppt", "dayour-notes", "dayour-markdown",
            "dayour-flashcard", "dayour-links", "dayour-jupyter", "dayour-vlib",
        ],
    },
    "customer_engagements": {
        "label": "Customer Engagements",
        "purpose": "Per-customer engagement agents with account-specific context",
        "agents": [
            "dayour-amica", "dayour-cdw", "dayour-citi", "dayour-gap",
            "dayour-hp", "dayour-sbx", "dayour-wynn",
        ],
    },
    "intelligence": {
        "label": "Intelligence & Analysis",
        "purpose": "Research, analytics, insights, evaluation, ML/AI",
        "agents": [
            "dayour-analyst", "dayour-analytics", "dayour-researcher",
            "dayour-insights", "dayour-evaluation", "dayour-mlads",
            "dayour-pmo",
        ],
    },
    "orchestration": {
        "label": "Orchestration",
        "purpose": "MCP routing, lab environments, Teams Mainline, AG2 patterns",
        "agents": [
            "dayour-mcp", "dayour-labs", "dayour-mainline", "dayour-swarm",
            "dayour-ag2", "dayour-agentbuilder", "dayour-activity",
            "dayour-ado", "dayour-darbotlabs",
        ],
    },
    "meta": {
        "label": "Meta / Twin",
        "purpose": "Autonomous ML digital twin -- the root coordinator",
        "agents": ["dayour", "dayswarm"],
    },
}


def build_agent_lookup(layer_taxonomy: dict) -> dict:
    """Create agent_name -> layer_id lookup."""
    lookup = {}
    for layer_id, layer in layer_taxonomy.items():
        for agent_name in layer["agents"]:
            lookup[agent_name] = layer_id
    return lookup


def main():
    raw_path = Path("scripts/agents_raw.json")
    raw_agents = json.loads(raw_path.read_text(encoding="utf-8"))

    lookup = build_agent_lookup(LAYER_TAXONOMY)

    registry = {
        "version": "1.0.0",
        "agent_count": len(raw_agents),
        "layers": {},
        "agents": {},
    }

    # Build layers section
    for layer_id, layer in LAYER_TAXONOMY.items():
        registry["layers"][layer_id] = {
            "label": layer["label"],
            "purpose": layer["purpose"],
            "agent_count": len(layer["agents"]),
            "agents": layer["agents"],
        }

    # Build agents section with enriched metadata
    for agent in raw_agents:
        name = agent["name"]
        layer_id = lookup.get(name, "unclassified")
        registry["agents"][name] = {
            "name": name,
            "description": agent["description"],
            "model": agent["model"],
            "mcps": agent["mcps"],
            "layer": layer_id,
            "layer_label": LAYER_TAXONOMY.get(layer_id, {}).get("label", "Unclassified"),
            "definition_file": agent["file"],
            "definition_lines": agent["lines"],
            "section_count": agent["section_count"],
        }

    # Summary stats
    model_counts = {}
    for a in registry["agents"].values():
        m = a["model"] or "unknown"
        model_counts[m] = model_counts.get(m, 0) + 1
    registry["model_distribution"] = model_counts

    layer_counts = {}
    for a in registry["agents"].values():
        layer_counts[a["layer"]] = layer_counts.get(a["layer"], 0) + 1
    registry["layer_distribution"] = layer_counts

    out_path = Path("src/opus_spark_swarm/swarm/swarm_registry.json")
    out_path.write_text(json.dumps(registry, indent=2), encoding="utf-8")
    print(f"Registry written: {out_path} ({len(registry['agents'])} agents, {len(registry['layers'])} layers)")

    # Print summary
    for lid, layer in registry["layers"].items():
        print(f"  {layer['label']:30s} {layer['agent_count']:2d} agents")
    print(f"  Models: {registry['model_distribution']}")


if __name__ == "__main__":
    main()
