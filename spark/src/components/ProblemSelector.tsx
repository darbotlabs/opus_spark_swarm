import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { ProblemStatement } from "@/types/pipeline";

interface ProblemSelectorProps {
  statements: ProblemStatement[];
  selected: number | null;
  onSelect: (index: number) => void;
}

const PRIORITY_VARIANT: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  Critical: "destructive",
  High: "default",
  Medium: "secondary",
  Low: "outline",
};

export function ProblemSelector({ statements, selected, onSelect }: ProblemSelectorProps) {
  if (statements.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Problem Statements</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            No problem statements generated yet. Run the analysis pipeline first.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Problem Statements</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3" role="radiogroup" aria-label="Problem statements">
          {statements.map((stmt, i) => (
            <Button
              key={i}
              variant={selected === i ? "default" : "outline"}
              className="w-full justify-start h-auto py-3 px-4 text-left"
              onClick={() => onSelect(i)}
              role="radio"
              aria-checked={selected === i}
            >
              <div className="flex flex-col gap-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-medium truncate">{stmt.title}</span>
                  <Badge variant={PRIORITY_VARIANT[stmt.priority] ?? "outline"}>
                    {stmt.priority}
                  </Badge>
                </div>
                <span className="text-xs text-muted-foreground truncate">{stmt.impact}</span>
              </div>
            </Button>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
