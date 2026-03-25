import { useState, useCallback } from "react";
import { useKV } from "@/hooks/use-kv";
import { Separator } from "@/components/ui/separator";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { CompanyInput } from "@/components/CompanyInput";
import { ProblemSelector } from "@/components/ProblemSelector";
import { AgentActivityFeed } from "@/components/AgentActivityFeed";
import { NotebookViewer } from "@/components/NotebookViewer";
import { SessionHistory } from "@/components/SessionHistory";
import { SwarmMemoryMap } from "@/components/SwarmMemoryMap";
import { SWARM_REGISTRY } from "@/lib/swarm-data";
import { Toaster } from "sonner";
import type {
  PipelineSession,
  ProblemStatement,
  AgentMessage,
  PipelinePhase,
} from "@/types/pipeline";

const PHASE_ORDER: PipelinePhase[] = ["research", "analysis", "architecture", "notebook"];

function phaseProgress(phase: string): number {
  const idx = PHASE_ORDER.indexOf(phase as PipelinePhase);
  if (idx === -1) return 0;
  return Math.round(((idx + 1) / PHASE_ORDER.length) * 100);
}

export default function App() {
  const [sessions, setSessions] = useKV<PipelineSession[]>("pipeline-sessions", []);
  const [activeSession, setActiveSession] = useState<PipelineSession | null>(null);
  const [selectedProblem, setSelectedProblem] = useState<number | null>(null);

  const handleCompanySubmit = useCallback(
    (company: string) => {
      const session: PipelineSession = {
        id: crypto.randomUUID(),
        company,
        phase: "research",
        status: "running",
        startedAt: Date.now(),
        messages: [],
        scores: {},
      };
      setActiveSession(session);
      setSelectedProblem(null);
      setSessions((prev) => [session, ...prev]);
    },
    [setSessions],
  );

  const handleSessionSelect = useCallback((session: PipelineSession) => {
    setActiveSession(session);
    setSelectedProblem(null);
  }, []);

  const problems: ProblemStatement[] =
    activeSession?.analysis?.problem_statements ?? [];
  const messages: AgentMessage[] = activeSession?.messages ?? [];
  const notebookCells = activeSession?.blueprint
    ? [
        { cell_type: "markdown" as const, source: `# ${activeSession.company} Analysis` },
        {
          cell_type: "markdown" as const,
          source: activeSession.blueprint.exec_summary ?? "Blueprint generated.",
        },
      ]
    : [];

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-card">
        <div className="container mx-auto flex items-center gap-3 py-4 px-6">
          <h1 className="text-xl font-bold tracking-tight">Opus Spark Swarm</h1>
          <Badge variant="secondary">AG2 Pipeline</Badge>
          {activeSession?.status === "running" && (
            <div className="flex items-center gap-2 ml-auto">
              <span className="text-xs text-muted-foreground">
                {activeSession.phase}
              </span>
              <Progress value={phaseProgress(activeSession.phase)} className="w-32" />
            </div>
          )}
        </div>
      </header>

      <main className="container mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6 p-6">
        <div className="lg:col-span-3">
          <SwarmMemoryMap
            registry={SWARM_REGISTRY}
            activeAgents={messages.map((m) => m.agent)}
          />
        </div>

        <div className="lg:col-span-2 space-y-6">
          <CompanyInput
            onSubmit={handleCompanySubmit}
            disabled={activeSession?.status === "running"}
          />

          {problems.length > 0 && (
            <ProblemSelector
              statements={problems}
              selected={selectedProblem}
              onSelect={setSelectedProblem}
            />
          )}

          <Separator />

          <AgentActivityFeed messages={messages} />

          {notebookCells.length > 0 && (
            <NotebookViewer cells={notebookCells} title={`${activeSession?.company} Notebook`} />
          )}
        </div>

        <aside className="space-y-6">
          <SessionHistory sessions={sessions} onSelect={handleSessionSelect} />
        </aside>
      </main>

      <Toaster />
    </div>
  );
}
