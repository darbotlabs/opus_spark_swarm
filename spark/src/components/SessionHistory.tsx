import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { ClockCounterClockwise } from "@phosphor-icons/react";
import type { PipelineSession } from "@/types/pipeline";

interface SessionHistoryProps {
  sessions: PipelineSession[];
  onSelect: (session: PipelineSession) => void;
}

const STATUS_VARIANT: Record<string, "default" | "secondary" | "destructive"> = {
  running: "secondary",
  complete: "default",
  error: "destructive",
};

export function SessionHistory({ sessions, onSelect }: SessionHistoryProps) {
  if (sessions.length === 0) {
    return (
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <ClockCounterClockwise className="text-muted-foreground" />
            <CardTitle>Session History</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground" data-testid="empty-history">
            No previous sessions. Run an analysis to get started.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <ClockCounterClockwise className="text-muted-foreground" />
          <CardTitle>Session History</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[300px]">
          <div className="space-y-2 pr-4">
            {sessions.map((session, i) => (
              <div key={session.id}>
                <Button
                  variant="ghost"
                  className="w-full justify-start h-auto py-2 px-3 text-left"
                  onClick={() => onSelect(session)}
                  data-testid="session-entry"
                >
                  <div className="flex flex-col gap-1 min-w-0 w-full">
                    <div className="flex items-center gap-2 w-full">
                      <span className="font-medium truncate">{session.company}</span>
                      <Badge variant={STATUS_VARIANT[session.status] ?? "secondary"}>
                        {session.status}
                      </Badge>
                      <span className="text-xs text-muted-foreground ml-auto whitespace-nowrap">
                        {new Date(session.startedAt).toLocaleDateString()}
                      </span>
                    </div>
                    {session.prompt && (
                      <span className="text-xs text-muted-foreground truncate">{session.prompt}</span>
                    )}
                  </div>
                </Button>
                {i < sessions.length - 1 && <Separator />}
              </div>
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
