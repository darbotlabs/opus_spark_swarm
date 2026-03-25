import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Robot, CaretDown, CaretRight } from "@phosphor-icons/react";
import type { SwarmRegistry, SwarmLayer, SwarmAgent } from "@/types/swarm";
import { LAYER_COLORS, MODEL_LABELS } from "@/types/swarm";

interface SwarmVisualizationProps {
  registry: SwarmRegistry;
}

function LayerSection({
  layerId,
  layer,
  agents,
  expanded,
  onToggle,
}: {
  layerId: string;
  layer: SwarmLayer;
  agents: SwarmAgent[];
  expanded: boolean;
  onToggle: () => void;
}) {
  const colorClass = LAYER_COLORS[layerId] ?? "bg-gray-100 text-gray-800 border-gray-200";

  return (
    <div className="border rounded-lg overflow-hidden" data-testid={`layer-${layerId}`}>
      <Button
        variant="ghost"
        className="w-full justify-between h-auto py-3 px-4 rounded-none"
        onClick={onToggle}
        aria-expanded={expanded}
      >
        <div className="flex items-center gap-3">
          {expanded ? <CaretDown weight="bold" /> : <CaretRight weight="bold" />}
          <span className="font-semibold">{layer.label}</span>
          <Badge variant="outline" className={colorClass}>
            {layer.agent_count} agents
          </Badge>
        </div>
        <span className="text-xs text-muted-foreground max-w-[300px] truncate text-right">
          {layer.purpose}
        </span>
      </Button>

      {expanded && (
        <div className="border-t bg-muted/30 p-3">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
            {agents.map((agent) => (
              <div
                key={agent.name}
                className="flex flex-col gap-1 rounded-md border bg-card p-2 text-xs"
                data-testid="swarm-agent-card"
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium">{agent.name}</span>
                  <Badge variant="outline" className="text-[10px] px-1.5 py-0">
                    {MODEL_LABELS[agent.model] ?? agent.model}
                  </Badge>
                </div>
                <p className="text-muted-foreground line-clamp-2 leading-tight">
                  {agent.description || "No description"}
                </p>
                {agent.mcps.length > 0 && (
                  <div className="flex gap-1 flex-wrap mt-0.5">
                    {agent.mcps.slice(0, 3).map((mcp) => (
                      <span key={mcp} className="text-[10px] bg-muted rounded px-1">
                        {mcp}
                      </span>
                    ))}
                    {agent.mcps.length > 3 && (
                      <span className="text-[10px] text-muted-foreground">
                        +{agent.mcps.length - 3} more
                      </span>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export function SwarmVisualization({ registry }: SwarmVisualizationProps) {
  const [expandedLayers, setExpandedLayers] = useState<Set<string>>(new Set());

  const toggleLayer = (layerId: string) => {
    setExpandedLayers((prev) => {
      const next = new Set(prev);
      if (next.has(layerId)) {
        next.delete(layerId);
      } else {
        next.add(layerId);
      }
      return next;
    });
  };

  const totalAgents = registry.agent_count;
  const layerIds = Object.keys(registry.layers);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Robot weight="duotone" className="text-primary" />
            <CardTitle>DAYOURBOT Swarm</CardTitle>
          </div>
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <span>{totalAgents} agents</span>
            <span>{layerIds.length} layers</span>
            <span>
              {Object.entries(registry.model_distribution).map(([model, count]) => (
                <Badge key={model} variant="secondary" className="ml-1 text-[10px]">
                  {MODEL_LABELS[model] ?? model}: {count}
                </Badge>
              ))}
            </span>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {/* Model distribution bar */}
        <div className="flex gap-0.5 h-2 rounded-full overflow-hidden mb-4" data-testid="model-bar">
          {Object.entries(registry.model_distribution).map(([model, count]) => {
            const pct = (count / totalAgents) * 100;
            const color =
              model === "gpt-5.4"
                ? "bg-green-500"
                : model.includes("sonnet")
                  ? "bg-blue-500"
                  : "bg-purple-500";
            return (
              <div
                key={model}
                className={`${color} transition-all`}
                style={{ width: `${pct}%` }}
                title={`${MODEL_LABELS[model] ?? model}: ${count} agents (${Math.round(pct)}%)`}
              />
            );
          })}
        </div>

        <Separator className="mb-4" />

        <ScrollArea className="h-[500px]">
          <div className="space-y-2 pr-4">
            {layerIds.map((layerId) => {
              const layer = registry.layers[layerId];
              const agents = layer.agents
                .map((name) => registry.agents[name])
                .filter(Boolean);

              return (
                <LayerSection
                  key={layerId}
                  layerId={layerId}
                  layer={layer}
                  agents={agents}
                  expanded={expandedLayers.has(layerId)}
                  onToggle={() => toggleLayer(layerId)}
                />
              );
            })}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
