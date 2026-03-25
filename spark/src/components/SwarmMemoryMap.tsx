import { useRef, useEffect, useCallback, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Cube, ArrowsClockwise, Eye } from "@phosphor-icons/react";
import type { SwarmRegistry } from "@/types/swarm";
import { LAYER_COLORS, MODEL_LABELS } from "@/types/swarm";
import {
  buildScene,
  updateScene,
  activateAgent,
  focusLayer,
  handleResize,
  hitTest,
  dispose,
  type SceneState,
} from "@/lib/swarm-scene";

interface SwarmMemoryMapProps {
  registry: SwarmRegistry;
  activeAgents?: string[];
}

export function SwarmMemoryMap({ registry, activeAgents = [] }: SwarmMemoryMapProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const stateRef = useRef<SceneState | null>(null);
  const animFrameRef = useRef<number>(0);
  const [hoveredAgent, setHoveredAgent] = useState<string | null>(null);
  const [focusedLayerId, setFocusedLayerId] = useState<string | null>(null);

  // Initialize scene
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const parent = canvas.parentElement;
    if (!parent) return;

    const w = parent.clientWidth;
    const h = parent.clientHeight;

    const sceneState = buildScene(canvas, registry, w, h);
    stateRef.current = sceneState;

    // Animation loop
    let lastTime = performance.now();
    function animate() {
      const now = performance.now();
      const dt = Math.min((now - lastTime) / 1000, 0.1);
      lastTime = now;

      if (stateRef.current) {
        updateScene(stateRef.current, dt);
      }
      animFrameRef.current = requestAnimationFrame(animate);
    }
    animFrameRef.current = requestAnimationFrame(animate);

    return () => {
      cancelAnimationFrame(animFrameRef.current);
      if (stateRef.current) {
        dispose(stateRef.current);
        stateRef.current = null;
      }
    };
  }, [registry]);

  // Activate agents when activeAgents prop changes
  useEffect(() => {
    if (!stateRef.current) return;
    for (const name of activeAgents) {
      activateAgent(stateRef.current, name);
    }
  }, [activeAgents]);

  // Resize handler
  useEffect(() => {
    function onResize() {
      const canvas = canvasRef.current;
      const parent = canvas?.parentElement;
      if (!canvas || !parent || !stateRef.current) return;
      handleResize(stateRef.current, parent.clientWidth, parent.clientHeight);
    }
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  // Mouse interaction
  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!stateRef.current || !canvasRef.current) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const agentName = hitTest(stateRef.current, e.clientX, e.clientY, rect);
    stateRef.current.hoveredNode = agentName;
    setHoveredAgent(agentName);
  }, []);

  const handleClick = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!stateRef.current || !canvasRef.current) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const agentName = hitTest(stateRef.current, e.clientX, e.clientY, rect);
    if (agentName && stateRef.current) {
      activateAgent(stateRef.current, agentName);
      const agent = registry.agents[agentName];
      if (agent) {
        setFocusedLayerId(agent.layer);
        focusLayer(stateRef.current, agent.layer);
      }
    }
  }, [registry]);

  const handleLayerFocus = useCallback((layerId: string | null) => {
    setFocusedLayerId(layerId);
    if (stateRef.current) {
      focusLayer(stateRef.current, layerId);
    }
  }, []);

  const handleResetView = useCallback(() => {
    setFocusedLayerId(null);
    setHoveredAgent(null);
    if (stateRef.current) {
      focusLayer(stateRef.current, null);
    }
  }, []);

  // Activate a random set of agents periodically for ambient effect
  useEffect(() => {
    const interval = setInterval(() => {
      if (!stateRef.current) return;
      const allNames = Object.keys(registry.agents);
      const randomAgent = allNames[Math.floor(Math.random() * allNames.length)];
      activateAgent(stateRef.current, randomAgent);
    }, 2000);
    return () => clearInterval(interval);
  }, [registry]);

  const hoveredData = hoveredAgent ? registry.agents[hoveredAgent] : null;
  const layerIds = Object.keys(registry.layers);

  return (
    <Card className="overflow-hidden">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Cube weight="duotone" className="text-primary" />
            <CardTitle>Swarm Memory Map</CardTitle>
            <Badge variant="secondary" className="text-[10px]">3D</Badge>
          </div>
          <div className="flex items-center gap-1">
            <Button variant="ghost" size="icon" onClick={handleResetView} title="Reset view">
              <ArrowsClockwise />
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-0 relative">
        {/* 3D Canvas */}
        <div className="relative w-full h-[500px] bg-[#0a0a14]" data-testid="memory-map-container">
          <canvas
            ref={canvasRef}
            className="w-full h-full cursor-crosshair"
            onMouseMove={handleMouseMove}
            onClick={handleClick}
            data-testid="memory-map-canvas"
          />

          {/* Hover tooltip */}
          {hoveredData && (
            <div
              className="absolute top-3 left-3 bg-card/90 backdrop-blur-sm border rounded-lg p-3 max-w-[240px] pointer-events-none"
              data-testid="agent-tooltip"
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="font-semibold text-sm">{hoveredData.name}</span>
                <Badge variant="outline" className="text-[10px] px-1">
                  {MODEL_LABELS[hoveredData.model] ?? hoveredData.model}
                </Badge>
              </div>
              <p className="text-xs text-muted-foreground leading-snug line-clamp-2">
                {hoveredData.description || "No description"}
              </p>
              <div className="flex items-center gap-1 mt-1.5">
                <Badge
                  variant="outline"
                  className={`text-[10px] px-1 ${LAYER_COLORS[hoveredData.layer] ?? ""}`}
                >
                  {hoveredData.layer_label}
                </Badge>
                {hoveredData.mcps.length > 0 && (
                  <span className="text-[10px] text-muted-foreground">
                    {hoveredData.mcps.length} MCPs
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Legend / layer selector (bottom) */}
          <div className="absolute bottom-3 left-3 right-3 flex items-center gap-1 flex-wrap">
            {layerIds.map((lid) => {
              const layer = registry.layers[lid];
              const isFocused = focusedLayerId === lid;
              return (
                <Button
                  key={lid}
                  variant={isFocused ? "default" : "ghost"}
                  size="sm"
                  className={`h-6 text-[10px] px-2 ${!isFocused ? "bg-black/40 text-white/70 hover:text-white hover:bg-black/60" : ""}`}
                  onClick={() => handleLayerFocus(isFocused ? null : lid)}
                  data-testid={`layer-btn-${lid}`}
                >
                  <Eye weight={isFocused ? "fill" : "regular"} className="mr-0.5" />
                  {layer.label} ({layer.agent_count})
                </Button>
              );
            })}
          </div>
        </div>

        <Separator />

        {/* Stats bar */}
        <div className="flex items-center justify-between px-4 py-2 text-xs text-muted-foreground">
          <span>{registry.agent_count} agents across {layerIds.length} layers</span>
          <div className="flex items-center gap-3">
            {Object.entries(registry.model_distribution).map(([model, count]) => (
              <span key={model} className="flex items-center gap-1">
                <span
                  className="w-2 h-2 rounded-full inline-block"
                  style={{
                    backgroundColor:
                      model === "gpt-5.4" ? "#22c55e" :
                      model.includes("sonnet") ? "#3b82f6" : "#a855f7",
                  }}
                />
                {MODEL_LABELS[model] ?? model}: {count}
              </span>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
