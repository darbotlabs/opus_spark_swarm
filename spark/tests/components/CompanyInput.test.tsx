import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CompanyInput } from "../../src/components/CompanyInput";

describe("CompanyInput", () => {
  it("renders the input field", () => {
    render(<CompanyInput onSubmit={() => {}} />);
    expect(screen.getByLabelText("Company name")).toBeInTheDocument();
  });

  it("renders the Analyse button", () => {
    render(<CompanyInput onSubmit={() => {}} />);
    expect(screen.getByText("Analyse")).toBeInTheDocument();
  });

  it("disables button when input is empty", () => {
    render(<CompanyInput onSubmit={() => {}} />);
    expect(screen.getByText("Analyse").closest("button")).toBeDisabled();
  });

  it("enables button when text is entered", async () => {
    const user = userEvent.setup();
    render(<CompanyInput onSubmit={() => {}} />);
    await user.type(screen.getByLabelText("Company name"), "Tesla");
    expect(screen.getByText("Analyse").closest("button")).not.toBeDisabled();
  });

  it("calls onSubmit with company name on button click", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(<CompanyInput onSubmit={onSubmit} />);
    await user.type(screen.getByLabelText("Company name"), "Netflix");
    await user.click(screen.getByText("Analyse"));
    expect(onSubmit).toHaveBeenCalledWith("Netflix");
  });

  it("calls onSubmit on Enter key", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(<CompanyInput onSubmit={onSubmit} />);
    await user.type(screen.getByLabelText("Company name"), "Stripe{enter}");
    expect(onSubmit).toHaveBeenCalledWith("Stripe");
  });

  it("shows suggestions on focus", async () => {
    const user = userEvent.setup();
    render(<CompanyInput onSubmit={() => {}} />);
    await user.click(screen.getByLabelText("Company name"));
    expect(screen.getByRole("listbox")).toBeInTheDocument();
  });

  it("filters suggestions as user types", async () => {
    const user = userEvent.setup();
    render(<CompanyInput onSubmit={() => {}} />);
    await user.type(screen.getByLabelText("Company name"), "Sho");
    const options = screen.getAllByRole("option");
    expect(options).toHaveLength(1);
    expect(options[0]).toHaveTextContent("Shopify");
  });

  it("respects disabled prop", () => {
    render(<CompanyInput onSubmit={() => {}} disabled />);
    expect(screen.getByLabelText("Company name")).toBeDisabled();
  });
});
