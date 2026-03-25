import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { SessionHistory } from "../../src/components/SessionHistory";
import type { PipelineSession } from "../../src/types/pipeline";

const MOCK_SESSIONS: PipelineSession[] = [
  {
    id: "s1",
    company: "Shopify",
    phase: "notebook",
    status: "complete",
    startedAt: Date.now() - 60000,
    completedAt: Date.now(),
    messages: [],
    scores: { research_score: 0.9, analysis_score: 0.85 },
  },
  {
    id: "s2",
    company: "Tesla",
    prompt: "EV supply chain optimization",
    phase: "analysis",
    status: "running",
    startedAt: Date.now() - 30000,
    messages: [],
  },
  {
    id: "s3",
    company: "Netflix",
    phase: "research",
    status: "error",
    startedAt: Date.now() - 120000,
    messages: [],
  },
];

describe("SessionHistory", () => {
  it("renders empty state when no sessions", () => {
    render(<SessionHistory sessions={[]} onSelect={() => {}} />);
    expect(screen.getByTestId("empty-history")).toBeInTheDocument();
    expect(screen.getByText(/No previous sessions/)).toBeInTheDocument();
  });

  it("renders all sessions", () => {
    render(<SessionHistory sessions={MOCK_SESSIONS} onSelect={() => {}} />);
    const entries = screen.getAllByTestId("session-entry");
    expect(entries).toHaveLength(3);
  });

  it("displays company names", () => {
    render(<SessionHistory sessions={MOCK_SESSIONS} onSelect={() => {}} />);
    expect(screen.getByText("Shopify")).toBeInTheDocument();
    expect(screen.getByText("Tesla")).toBeInTheDocument();
    expect(screen.getByText("Netflix")).toBeInTheDocument();
  });

  it("displays status badges", () => {
    render(<SessionHistory sessions={MOCK_SESSIONS} onSelect={() => {}} />);
    expect(screen.getByText("complete")).toBeInTheDocument();
    expect(screen.getByText("running")).toBeInTheDocument();
    expect(screen.getByText("error")).toBeInTheDocument();
  });

  it("displays prompt when present", () => {
    render(<SessionHistory sessions={MOCK_SESSIONS} onSelect={() => {}} />);
    expect(screen.getByText("EV supply chain optimization")).toBeInTheDocument();
  });

  it("calls onSelect when session is clicked", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    render(<SessionHistory sessions={MOCK_SESSIONS} onSelect={onSelect} />);
    await user.click(screen.getByText("Tesla"));
    expect(onSelect).toHaveBeenCalledWith(MOCK_SESSIONS[1]);
  });

  it("renders Session History title", () => {
    render(<SessionHistory sessions={[]} onSelect={() => {}} />);
    expect(screen.getByText("Session History")).toBeInTheDocument();
  });
});
