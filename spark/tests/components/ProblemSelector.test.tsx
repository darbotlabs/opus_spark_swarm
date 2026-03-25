import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ProblemSelector } from "../../src/components/ProblemSelector";
import type { ProblemStatement } from "../../src/types/pipeline";

const MOCK_STATEMENTS: ProblemStatement[] = [
  {
    title: "Merchant Churn",
    context: "High churn rate among SMB merchants",
    evidence: "18-22% annual churn",
    impact: "Revenue retention",
    stakeholders: "Product team",
    priority: "Critical",
  },
  {
    title: "Cross-Border Friction",
    context: "International payment delays",
    evidence: "3-5 day settlement",
    impact: "Market expansion",
    stakeholders: "Payments team",
    priority: "High",
  },
  {
    title: "App Quality",
    context: "Inconsistent app ecosystem",
    evidence: "8000+ apps with variable quality",
    impact: "Platform integrity",
    stakeholders: "Developer relations",
    priority: "Medium",
  },
];

describe("ProblemSelector", () => {
  it("renders empty state when no statements", () => {
    render(<ProblemSelector statements={[]} selected={null} onSelect={() => {}} />);
    expect(screen.getByText(/No problem statements generated/)).toBeInTheDocument();
  });

  it("renders all problem statements", () => {
    render(<ProblemSelector statements={MOCK_STATEMENTS} selected={null} onSelect={() => {}} />);
    expect(screen.getByText("Merchant Churn")).toBeInTheDocument();
    expect(screen.getByText("Cross-Border Friction")).toBeInTheDocument();
    expect(screen.getByText("App Quality")).toBeInTheDocument();
  });

  it("renders priority badges", () => {
    render(<ProblemSelector statements={MOCK_STATEMENTS} selected={null} onSelect={() => {}} />);
    expect(screen.getByText("Critical")).toBeInTheDocument();
    expect(screen.getByText("High")).toBeInTheDocument();
    expect(screen.getByText("Medium")).toBeInTheDocument();
  });

  it("calls onSelect when a statement is clicked", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    render(<ProblemSelector statements={MOCK_STATEMENTS} selected={null} onSelect={onSelect} />);
    await user.click(screen.getByText("Cross-Border Friction"));
    expect(onSelect).toHaveBeenCalledWith(1);
  });

  it("marks selected statement with aria-checked", () => {
    render(<ProblemSelector statements={MOCK_STATEMENTS} selected={0} onSelect={() => {}} />);
    const radios = screen.getAllByRole("radio");
    expect(radios[0]).toHaveAttribute("aria-checked", "true");
    expect(radios[1]).toHaveAttribute("aria-checked", "false");
  });
});
