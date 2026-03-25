import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";

interface NotebookCell {
  cell_type: "markdown" | "code";
  source: string[] | string;
}

interface NotebookViewerProps {
  cells: NotebookCell[];
  title?: string;
}

function cellSource(cell: NotebookCell): string {
  return Array.isArray(cell.source) ? cell.source.join("") : cell.source;
}

export function NotebookViewer({ cells, title = "Generated Notebook" }: NotebookViewerProps) {
  if (cells.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground" data-testid="empty-notebook">
            No notebook cells to display.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[500px]">
          <div className="space-y-4 pr-4">
            {cells.map((cell, i) => (
              <div key={i} data-testid={`notebook-cell-${cell.cell_type}`}>
                {cell.cell_type === "markdown" ? (
                  <div className="prose prose-sm max-w-none text-foreground">
                    <pre className="whitespace-pre-wrap text-sm">{cellSource(cell)}</pre>
                  </div>
                ) : (
                  <div className="rounded-md border bg-muted/50 p-3">
                    <pre className="text-xs font-mono overflow-x-auto">{cellSource(cell)}</pre>
                  </div>
                )}
                {i < cells.length - 1 && <Separator className="mt-4" />}
              </div>
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
