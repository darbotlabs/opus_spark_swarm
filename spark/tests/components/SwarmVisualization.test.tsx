import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { SwarmVisualization } from "../../src/components/SwarmVisualization";
import type { SwarmRegistry } from "../../src/types/swarm";

const MOCK_REGISTRY: SwarmRegistry = {
  version: "1.0.0",
  agent_count: 5,
  layers: {
    engineering: {
      label: "Engineering",
      purpose: "Code analysis, system design/ADRs, UI/UX",
      agent_count: 2,
      agents: ["dayour-swe", "dayour-architect"],
    },
    meta: {
      label: "Meta / Twin",
      purpose: "Autonomous ML digital twin",
      agent_count: 1,
      agents: ["dayour"],
    },
    platform_specialists: {
      label: "Platform Specialists",
      purpose: "Deep expertise in Copilot Studio",
      agent_count: 2,
      agents: ["dayour-studio", "dayour-azure"],
    },
  },
  agents: {
    "dayour-swe": {
      name: "dayour-swe",
      description: "Software engineering specialist",
      model: "gpt-5.4",
      mcps: ["github-mcp-server", "ado-mcp"],
      layer: "engineering",
      layer_label: "Engineering",
      definition_file: "dayour-swe.md",
      definition_lines: 243,
      section_count: 11,
    },
    "dayour-architect": {
      name: "dayour-architect",
      description: "System design and ADRs",
      model: "gpt-5.4",
      mcps: ["github-mcp-server"],
      layer: "engineering",
      layer_label: "Engineering",
      definition_file: "dayour-architect.md",
      definition_lines: 180,
      section_count: 8,
    },
    dayour: {
      name: "dayour",
      description: "Root coordinator digital twin",
      model: "claude-opus-4.6",
      mcps: ["ado-mcp", "flashcard-mcp"],
      layer: "meta",
      layer_label: "Meta / Twin",
      definition_file: "dayour.md",
      definition_lines: 645,
      section_count: 17,
    },
    "dayour-studio": {
      name: "dayour-studio",
      description: "Copilot Studio specialist",
      model: "claude-sonnet-4.6",
      mcps: ["studio-mcp"],
      layer: "platform_specialists",
      layer_label: "Platform Specialists",
      definition_file: "dayour-studio.md",
      definition_lines: 1031,
      section_count: 20,
    },
    "dayour-azure": {
      name: "dayour-azure",
      description: "Azure platform specialist",
      model: "gpt-5.4",
      mcps: ["azure-mcp"],
      layer: "platform_specialists",
      layer_label: "Platform Specialists",
      definition_file: "dayour-azure.md",
      definition_lines: 400,
      section_count: 12,
    },
  },
  model_distribution: { "gpt-5.4": 3, "claude-sonnet-4.6": 1, "claude-opus-4.6": 1 },
  layer_distribution: { engineering: 2, meta: 1, platform_specialists: 2 },
};

describe("SwarmVisualization", () => {
  it("renders the title", () => {
    render(<SwarmVisualization registry={MOCK_REGISTRY} />);
    expect(screen.getByText("DAYOURBOT Swarm")).toBeInTheDocument();
  });

  it("shows total agent count", () => {
    render(<SwarmVisualization registry={MOCK_REGISTRY} />);
    expect(screen.getByText("5 agents")).toBeInTheDocument();
  });

  it("shows layer count", () => {
    render(<SwarmVisualization registry={MOCK_REGISTRY} />);
    expect(screen.getByText("3 layers")).toBeInTheDocument();
  });

  it("renders all layer sections", () => {
    render(<SwarmVisualization registry={MOCK_REGISTRY} />);
    expect(screen.getByTestId("layer-engineering")).toBeInTheDocument();
    expect(screen.getByTestId("layer-meta")).toBeInTheDocument();
    expect(screen.getByTestId("layer-platform_specialists")).toBeInTheDocument();
  });

  it("renders layer labels", () => {
    render(<SwarmVisualization registry={MOCK_REGISTRY} />);
    expect(screen.getByText("Engineering")).toBeInTheDocument();
    expect(screen.getByText("Meta / Twin")).toBeInTheDocument();
    expect(screen.getByText("Platform Specialists")).toBeInTheDocument();
  });

  it("renders agent count badges per layer", () => {
    render(<SwarmVisualization registry={MOCK_REGISTRY} />);
    const badges = screen.getAllByText("2 agents");
    expect(badges.length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("1 agents")).toBeInTheDocument();
  });

  it("renders model distribution bar", () => {
    render(<SwarmVisualization registry={MOCK_REGISTRY} />);
    expect(screen.getByTestId("model-bar")).toBeInTheDocument();
  });

  it("expands a layer on click to show agent cards", async () => {
    const user = userEvent.setup();
    render(<SwarmVisualization registry={MOCK_REGISTRY} />);

    // Initially no agent cards visible
    expect(screen.queryAllByTestId("swarm-agent-card")).toHaveLength(0);

    // Click Engineering layer
    await user.click(screen.getByText("Engineering"));

    // Now should show 2 agent cards
    const cards = screen.getAllByTestId("swarm-agent-card");
    expect(cards).toHaveLength(2);
    expect(screen.getByText("dayour-swe")).toBeInTheDocument();
    expect(screen.getByText("dayour-architect")).toBeInTheDocument();
  });

  it("shows agent descriptions in expanded view", async () => {
    const user = userEvent.setup();
    render(<SwarmVisualization registry={MOCK_REGISTRY} />);

    await user.click(screen.getByText("Engineering"));
    expect(screen.getByText("Software engineering specialist")).toBeInTheDocument();
  });

  it("shows model badges on agent cards", async () => {
    const user = userEvent.setup();
    render(<SwarmVisualization registry={MOCK_REGISTRY} />);

    await user.click(screen.getByText("Meta / Twin"));
    expect(screen.getByText("Claude Opus 4.6")).toBeInTheDocument();
  });

  it("shows MCP tags on agent cards", async () => {
    const user = userEvent.setup();
    render(<SwarmVisualization registry={MOCK_REGISTRY} />);

    await user.click(screen.getByText("Engineering"));
    const mcpTags = screen.getAllByText("github-mcp-server");
    expect(mcpTags.length).toBeGreaterThanOrEqual(1);
  });

  it("collapses layer on second click", async () => {
    const user = userEvent.setup();
    render(<SwarmVisualization registry={MOCK_REGISTRY} />);

    await user.click(screen.getByText("Engineering"));
    expect(screen.getAllByTestId("swarm-agent-card")).toHaveLength(2);

    await user.click(screen.getByText("Engineering"));
    expect(screen.queryAllByTestId("swarm-agent-card")).toHaveLength(0);
  });
});
