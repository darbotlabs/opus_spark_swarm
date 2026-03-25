import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { NotebookViewer } from "../../src/components/NotebookViewer";

describe("NotebookViewer", () => {
  it("renders empty state when no cells", () => {
    render(<NotebookViewer cells={[]} />);
    expect(screen.getByTestId("empty-notebook")).toBeInTheDocument();
  });

  it("renders the default title", () => {
    render(<NotebookViewer cells={[]} />);
    expect(screen.getByText("Generated Notebook")).toBeInTheDocument();
  });

  it("renders a custom title", () => {
    render(<NotebookViewer cells={[]} title="Shopify Analysis" />);
    expect(screen.getByText("Shopify Analysis")).toBeInTheDocument();
  });

  it("renders markdown cells", () => {
    const cells = [{ cell_type: "markdown" as const, source: "# Hello World" }];
    render(<NotebookViewer cells={cells} />);
    expect(screen.getByTestId("notebook-cell-markdown")).toBeInTheDocument();
    expect(screen.getByText("# Hello World")).toBeInTheDocument();
  });

  it("renders code cells", () => {
    const cells = [{ cell_type: "code" as const, source: "print('hello')" }];
    render(<NotebookViewer cells={cells} />);
    expect(screen.getByTestId("notebook-cell-code")).toBeInTheDocument();
    expect(screen.getByText("print('hello')")).toBeInTheDocument();
  });

  it("handles array source format", () => {
    const cells = [{ cell_type: "code" as const, source: ["import os\n", "print(os.getcwd())"] }];
    render(<NotebookViewer cells={cells} />);
    const codeCell = screen.getByTestId("notebook-cell-code");
    expect(codeCell.textContent).toContain("import os");
    expect(codeCell.textContent).toContain("print(os.getcwd())");
  });

  it("renders mixed cell types", () => {
    const cells = [
      { cell_type: "markdown" as const, source: "# Title" },
      { cell_type: "code" as const, source: "x = 1" },
      { cell_type: "markdown" as const, source: "## Section" },
    ];
    render(<NotebookViewer cells={cells} />);
    expect(screen.getAllByTestId("notebook-cell-markdown")).toHaveLength(2);
    expect(screen.getAllByTestId("notebook-cell-code")).toHaveLength(1);
  });
});
