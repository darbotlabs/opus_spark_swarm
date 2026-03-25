import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

// Mock the SwarmMemoryMap since it requires WebGL (Three.js)
vi.mock("../src/components/SwarmMemoryMap", () => ({
  SwarmMemoryMap: () => <div data-testid="swarm-memory-map-mock">SwarmMemoryMap</div>,
}));

// Mock the swarm data module
vi.mock("../src/lib/swarm-data", () => ({
  SWARM_REGISTRY: {
    version: "1.0.0",
    agent_count: 0,
    layers: {},
    agents: {},
    model_distribution: {},
    layer_distribution: {},
  },
}));

import App from "../src/App";

describe("App", () => {
  it("renders the header with title", () => {
    render(<App />);
    expect(screen.getByText("Opus Spark Swarm")).toBeInTheDocument();
  });

  it("renders the AG2 Pipeline badge", () => {
    render(<App />);
    expect(screen.getByText("AG2 Pipeline")).toBeInTheDocument();
  });

  it("renders the company input", () => {
    render(<App />);
    expect(screen.getByLabelText("Company name")).toBeInTheDocument();
  });

  it("renders session history section", () => {
    render(<App />);
    expect(screen.getByText("Session History")).toBeInTheDocument();
  });

  it("renders empty agent activity feed", () => {
    render(<App />);
    expect(screen.getByText("Waiting for pipeline to start...")).toBeInTheDocument();
  });

  it("creates a session when company is submitted", async () => {
    const user = userEvent.setup();
    vi.stubGlobal("crypto", { randomUUID: () => "test-uuid-1234" });

    render(<App />);
    const input = screen.getByLabelText("Company name");
    await user.type(input, "Shopify");
    await user.click(screen.getByText("Analyse"));

    // The session should appear in history (the entry shows the company name)
    const entries = screen.getAllByText("Shopify");
    expect(entries.length).toBeGreaterThanOrEqual(1);

    vi.unstubAllGlobals();
  });
});
