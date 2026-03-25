import { useRef, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { AgentMessage } from "@/types/pipeline";
import { PHASE_LABELS, type PipelinePhase } from "@/types/pipeline";

interface AgentActivityFeedProps {
  messages: AgentMessage[];
}

const PHASE_COLOR: Record<PipelinePhase, string> = {
  research: "bg-blue-100 text-blue-800",
  analysis: "bg-amber-100 text-amber-800",
  architecture: "bg-purple-100 text-purple-800",
  notebook: "bg-green-100 text-green-800",
};

export function AgentActivityFeed({ messages }: AgentActivityFeedProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length]);

  return (
    <Card className="flex flex-col">
      <CardHeader>
        <CardTitle>Agent Activity</CardTitle>
      </CardHeader>
      <CardContent className="flex-1 min-h-0">
        <ScrollArea className="h-[400px]">
          {messages.length === 0 ? (
            <p className="text-sm text-muted-foreground" data-testid="empty-feed">
              Waiting for pipeline to start...
            </p>
          ) : (
            <div className="space-y-3 pr-4">
              {messages.map((msg) => (
                <div key={msg.id} className="flex flex-col gap-1" data-testid="agent-message">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">{msg.agent}</span>
                    <Badge variant="outline" className={PHASE_COLOR[msg.phase]}>
                      {PHASE_LABELS[msg.phase]}
                    </Badge>
                    <span className="text-xs text-muted-foreground ml-auto">
                      {new Date(msg.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground leading-relaxed">{msg.content}</p>
                </div>
              ))}
              <div ref={bottomRef} />
            </div>
          )}
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
