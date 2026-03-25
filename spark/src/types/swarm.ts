/**
 * Swarm registry types matching the Python swarm_registry.json structure.
 */

export interface SwarmAgent {
  name: string;
  description: string;
  model: string;
  mcps: string[];
  layer: string;
  layer_label: string;
  definition_file: string;
  definition_lines: number;
  section_count: number;
}

export interface SwarmLayer {
  label: string;
  purpose: string;
  agent_count: number;
  agents: string[];
}

export interface SwarmRegistry {
  version: string;
  agent_count: number;
  layers: Record<string, SwarmLayer>;
  agents: Record<string, SwarmAgent>;
  model_distribution: Record<string, number>;
  layer_distribution: Record<string, number>;
}

export const LAYER_COLORS: Record<string, string> = {
  strategy_org: "bg-amber-100 text-amber-800 border-amber-200",
  platform_specialists: "bg-blue-100 text-blue-800 border-blue-200",
  engineering: "bg-violet-100 text-violet-800 border-violet-200",
  content_docs: "bg-emerald-100 text-emerald-800 border-emerald-200",
  customer_engagements: "bg-rose-100 text-rose-800 border-rose-200",
  intelligence: "bg-cyan-100 text-cyan-800 border-cyan-200",
  orchestration: "bg-orange-100 text-orange-800 border-orange-200",
  meta: "bg-fuchsia-100 text-fuchsia-800 border-fuchsia-200",
};

export const MODEL_LABELS: Record<string, string> = {
  "gpt-5.4": "GPT-5.4",
  "claude-sonnet-4.6": "Claude Sonnet 4.6",
  "claude-opus-4.6": "Claude Opus 4.6",
};
