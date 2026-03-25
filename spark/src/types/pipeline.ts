/**
 * Pipeline data types shared between the Spark UI and the Python backend.
 */

export interface ProblemStatement {
  title: string;
  context: string;
  evidence: string;
  impact: string;
  stakeholders: string;
  priority: "Critical" | "High" | "Medium" | "Low";
}

export interface QualityScores {
  research_score?: number;
  analysis_score?: number;
  architecture_score?: number;
  notebook_score?: number;
}

export interface CompanyDossier {
  company: string;
  market_data: string | Record<string, unknown>;
  news: string | Record<string, unknown>;
  filings: string | Record<string, unknown>;
}

export interface SolutionBlueprint {
  exec_summary?: string;
  architecture?: string | Record<string, unknown>;
  phases?: Array<Record<string, unknown>>;
  risks?: Array<Record<string, unknown>>;
  costs?: string | Record<string, unknown>;
  kpis?: Array<Record<string, unknown>>;
}

export interface AgentMessage {
  id: string;
  agent: string;
  content: string;
  timestamp: number;
  phase: "research" | "analysis" | "architecture" | "notebook";
}

export interface PipelineSession {
  id: string;
  company: string;
  prompt?: string;
  phase: string;
  status: "running" | "complete" | "error";
  startedAt: number;
  completedAt?: number;
  scores?: QualityScores;
  dossier?: CompanyDossier;
  analysis?: { problem_statements: ProblemStatement[] };
  blueprint?: SolutionBlueprint;
  messages: AgentMessage[];
}

export type PipelinePhase = "research" | "analysis" | "architecture" | "notebook";

export const PHASE_LABELS: Record<PipelinePhase, string> = {
  research: "Research",
  analysis: "Analysis",
  architecture: "Architecture",
  notebook: "Notebook",
};
