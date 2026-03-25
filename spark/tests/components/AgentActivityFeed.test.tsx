import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { AgentActivityFeed } from "../../src/components/AgentActivityFeed";
import type { AgentMessage } from "../../src/types/pipeline";

const MOCK_MESSAGES: AgentMessage[] = [
  {
    id: "m1",
    agent: "CompanyLookupAgent",
    content: "Resolved Shopify to ticker SHOP",
    timestamp: Date.now() - 5000,
    phase: "research",
  },
  {
    id: "m2",
    agent: "MarketDataAgent",
    content: "Retrieved market data for SHOP",
    timestamp: Date.now() - 3000,
    phase: "research",
  },
  {
    id: "m3",
    agent: "ProblemFramerAgent",
    content: "Identified 3 candidate problem domains",
    timestamp: Date.now() - 1000,
    phase: "analysis",
  },
];

describe("AgentActivityFeed", () => {
  it("shows empty state when no messages", () => {
    render(<AgentActivityFeed messages={[]} />);
    expect(screen.getByTestId("empty-feed")).toBeInTheDocument();
    expect(screen.getByText("Waiting for pipeline to start...")).toBeInTheDocument();
  });

  it("renders all messages", () => {
    render(<AgentActivityFeed messages={MOCK_MESSAGES} />);
    const items = screen.getAllByTestId("agent-message");
    expect(items).toHaveLength(3);
  });

  it("displays agent names", () => {
    render(<AgentActivityFeed messages={MOCK_MESSAGES} />);
    expect(screen.getByText("CompanyLookupAgent")).toBeInTheDocument();
    expect(screen.getByText("MarketDataAgent")).toBeInTheDocument();
    expect(screen.getByText("ProblemFramerAgent")).toBeInTheDocument();
  });

  it("displays message content", () => {
    render(<AgentActivityFeed messages={MOCK_MESSAGES} />);
    expect(screen.getByText("Resolved Shopify to ticker SHOP")).toBeInTheDocument();
  });

  it("displays phase badges", () => {
    render(<AgentActivityFeed messages={MOCK_MESSAGES} />);
    const researchBadges = screen.getAllByText("Research");
    expect(researchBadges.length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText("Analysis")).toBeInTheDocument();
  });

  it("renders the Activity title", () => {
    render(<AgentActivityFeed messages={[]} />);
    expect(screen.getByText("Agent Activity")).toBeInTheDocument();
  });
});
