/**
 * Three.js scene builder for the swarm memory map.
 *
 * Lays out 67 agents across 8 concentric orbital rings (one per layer),
 * with the meta/coordinator agents at the center. Each node pulses when
 * "remembered" (recently active) and connections trace routing paths
 * between layers.
 */

import * as THREE from "three";
import type { SwarmRegistry, SwarmAgent } from "@/types/swarm";
import { LAYER_COLORS } from "@/types/swarm";

// Layer ring radii -- meta at center, then expanding outward
const LAYER_RADII: Record<string, number> = {
  meta: 0,
  orchestration: 2.5,
  strategy_org: 4.0,
  intelligence: 5.5,
  engineering: 7.0,
  platform_specialists: 8.8,
  content_docs: 10.5,
  customer_engagements: 12.0,
};

// Layer Y offsets for vertical spread
const LAYER_Y: Record<string, number> = {
  meta: 0,
  orchestration: 0.3,
  strategy_org: -0.5,
  intelligence: 0.8,
  engineering: -0.2,
  platform_specialists: 0.5,
  content_docs: -0.8,
  customer_engagements: 0.1,
};

// Colors per layer (hex)
const LAYER_HEX: Record<string, number> = {
  strategy_org: 0xf59e0b,
  platform_specialists: 0x3b82f6,
  engineering: 0x8b5cf6,
  content_docs: 0x10b981,
  customer_engagements: 0xf43f5e,
  intelligence: 0x06b6d4,
  orchestration: 0xf97316,
  meta: 0xd946ef,
};

const MODEL_HEX: Record<string, number> = {
  "gpt-5.4": 0x22c55e,
  "claude-sonnet-4.6": 0x3b82f6,
  "claude-opus-4.6": 0xa855f7,
};

export interface NodeData {
  agent: SwarmAgent;
  mesh: THREE.Mesh;
  glowMesh: THREE.Mesh;
  basePosition: THREE.Vector3;
  activity: number; // 0..1, decays over time
  lastActiveTime: number;
}

export interface LayerRingData {
  layerId: string;
  ring: THREE.Line;
  label: string;
}

export interface SceneState {
  scene: THREE.Scene;
  camera: THREE.PerspectiveCamera;
  renderer: THREE.WebGLRenderer;
  nodes: Map<string, NodeData>;
  layerRings: LayerRingData[];
  connectionLines: THREE.Line[];
  raycaster: THREE.Raycaster;
  mouse: THREE.Vector2;
  clock: THREE.Clock;
  hoveredNode: string | null;
  focusedLayer: string | null;
  targetCameraPos: THREE.Vector3;
  targetLookAt: THREE.Vector3;
  currentLookAt: THREE.Vector3;
  autoRotateSpeed: number;
  autoRotateAngle: number;
}

function createAgentNode(agent: SwarmAgent, position: THREE.Vector3): { mesh: THREE.Mesh; glowMesh: THREE.Mesh } {
  const layerColor = LAYER_HEX[agent.layer] ?? 0x888888;
  const modelColor = MODEL_HEX[agent.model] ?? 0xaaaaaa;

  // Core sphere
  const geo = new THREE.SphereGeometry(0.18, 16, 16);
  const mat = new THREE.MeshPhongMaterial({
    color: layerColor,
    emissive: layerColor,
    emissiveIntensity: 0.3,
    shininess: 80,
    transparent: true,
    opacity: 0.9,
  });
  const mesh = new THREE.Mesh(geo, mat);
  mesh.position.copy(position);
  mesh.userData = { agentName: agent.name };

  // Outer glow sphere
  const glowGeo = new THREE.SphereGeometry(0.32, 16, 16);
  const glowMat = new THREE.MeshBasicMaterial({
    color: modelColor,
    transparent: true,
    opacity: 0.08,
  });
  const glowMesh = new THREE.Mesh(glowGeo, glowMat);
  glowMesh.position.copy(position);

  return { mesh, glowMesh };
}

function createLayerRing(layerId: string, radius: number, y: number): THREE.Line {
  if (radius === 0) {
    // Meta layer -- no ring, just a central marker
    const points = [new THREE.Vector3(0, y, 0), new THREE.Vector3(0.01, y, 0.01)];
    const geo = new THREE.BufferGeometry().setFromPoints(points);
    const mat = new THREE.LineBasicMaterial({ color: LAYER_HEX[layerId] ?? 0xffffff, transparent: true, opacity: 0.0 });
    return new THREE.Line(geo, mat);
  }

  const segments = 96;
  const points: THREE.Vector3[] = [];
  for (let i = 0; i <= segments; i++) {
    const angle = (i / segments) * Math.PI * 2;
    points.push(new THREE.Vector3(Math.cos(angle) * radius, y, Math.sin(angle) * radius));
  }
  const geo = new THREE.BufferGeometry().setFromPoints(points);
  const mat = new THREE.LineBasicMaterial({
    color: LAYER_HEX[layerId] ?? 0x666666,
    transparent: true,
    opacity: 0.15,
  });
  return new THREE.Line(geo, mat);
}

function createConnectionLine(from: THREE.Vector3, to: THREE.Vector3, color: number): THREE.Line {
  // Curved connection using a quadratic bezier midpoint
  const mid = new THREE.Vector3().lerpVectors(from, to, 0.5);
  mid.y += 1.5;

  const curve = new THREE.QuadraticBezierCurve3(from.clone(), mid, to.clone());
  const points = curve.getPoints(20);
  const geo = new THREE.BufferGeometry().setFromPoints(points);
  const mat = new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.06 });
  return new THREE.Line(geo, mat);
}

export function buildScene(
  canvas: HTMLCanvasElement,
  registry: SwarmRegistry,
  width: number,
  height: number,
): SceneState {
  // Renderer
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.setSize(width, height);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setClearColor(0x0a0a14, 1);

  // Scene
  const scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2(0x0a0a14, 0.025);

  // Camera
  const camera = new THREE.PerspectiveCamera(55, width / height, 0.1, 100);
  camera.position.set(12, 8, 12);

  // Lights
  const ambient = new THREE.AmbientLight(0x334466, 0.6);
  scene.add(ambient);

  const point1 = new THREE.PointLight(0x8b5cf6, 1.2, 40);
  point1.position.set(5, 8, 5);
  scene.add(point1);

  const point2 = new THREE.PointLight(0x3b82f6, 0.8, 40);
  point2.position.set(-5, 6, -5);
  scene.add(point2);

  const point3 = new THREE.PointLight(0x10b981, 0.5, 30);
  point3.position.set(0, -4, 8);
  scene.add(point3);

  // Grid helper (faint)
  const grid = new THREE.GridHelper(30, 30, 0x1a1a2e, 0x1a1a2e);
  grid.position.y = -2;
  (grid.material as THREE.Material).transparent = true;
  (grid.material as THREE.Material).opacity = 0.15;
  scene.add(grid);

  // Layer rings and nodes
  const nodes = new Map<string, NodeData>();
  const layerRings: LayerRingData[] = [];

  const layerIds = Object.keys(registry.layers);
  for (const layerId of layerIds) {
    const layer = registry.layers[layerId];
    const radius = LAYER_RADII[layerId] ?? 6;
    const yOffset = LAYER_Y[layerId] ?? 0;

    // Ring
    const ring = createLayerRing(layerId, radius, yOffset);
    scene.add(ring);
    layerRings.push({ layerId, ring, label: layer.label });

    // Agents distributed around the ring
    const agentNames = layer.agents;
    agentNames.forEach((name, i) => {
      const agent = registry.agents[name];
      if (!agent) return;

      let position: THREE.Vector3;
      if (radius === 0) {
        // Meta agents at center, slightly offset
        const offset = i === 0 ? -0.4 : 0.4;
        position = new THREE.Vector3(offset, yOffset, offset);
      } else {
        const angle = (i / agentNames.length) * Math.PI * 2;
        // Add slight randomness for organic feel
        const jitterR = (Math.random() - 0.5) * 0.3;
        const jitterY = (Math.random() - 0.5) * 0.4;
        position = new THREE.Vector3(
          Math.cos(angle) * (radius + jitterR),
          yOffset + jitterY,
          Math.sin(angle) * (radius + jitterR),
        );
      }

      const { mesh, glowMesh } = createAgentNode(agent, position);
      scene.add(mesh);
      scene.add(glowMesh);

      nodes.set(name, {
        agent,
        mesh,
        glowMesh,
        basePosition: position.clone(),
        activity: 0,
        lastActiveTime: 0,
      });
    });
  }

  // Connection lines: meta -> each layer (root coordinator fan-out)
  const connectionLines: THREE.Line[] = [];
  const metaNode = nodes.get("dayour");
  if (metaNode) {
    for (const layerId of layerIds) {
      if (layerId === "meta") continue;
      const layerAgents = registry.layers[layerId]?.agents ?? [];
      if (layerAgents.length > 0) {
        const firstAgent = nodes.get(layerAgents[0]);
        if (firstAgent) {
          const line = createConnectionLine(
            metaNode.basePosition,
            firstAgent.basePosition,
            LAYER_HEX[layerId] ?? 0x666666,
          );
          scene.add(line);
          connectionLines.push(line);
        }
      }
    }
  }

  return {
    scene,
    camera,
    renderer,
    nodes,
    layerRings,
    connectionLines,
    raycaster: new THREE.Raycaster(),
    mouse: new THREE.Vector2(-999, -999),
    clock: new THREE.Clock(),
    hoveredNode: null,
    focusedLayer: null,
    targetCameraPos: new THREE.Vector3(12, 8, 12),
    targetLookAt: new THREE.Vector3(0, 0, 0),
    currentLookAt: new THREE.Vector3(0, 0, 0),
    autoRotateSpeed: 0.08,
    autoRotateAngle: 0,
  };
}

export function updateScene(state: SceneState, _dt: number) {
  const t = state.clock.getElapsedTime();

  // Auto-rotate camera
  state.autoRotateAngle += state.autoRotateSpeed * _dt;
  const camRadius = state.focusedLayer ? 8 : 16;
  const camY = state.focusedLayer ? 5 : 8;
  state.targetCameraPos.set(
    Math.cos(state.autoRotateAngle) * camRadius,
    camY + Math.sin(t * 0.3) * 0.5,
    Math.sin(state.autoRotateAngle) * camRadius,
  );

  // Smooth camera interpolation
  state.camera.position.lerp(state.targetCameraPos, 0.02);
  state.currentLookAt.lerp(state.targetLookAt, 0.03);
  state.camera.lookAt(state.currentLookAt);

  // Animate nodes
  for (const [name, node] of state.nodes) {
    const mat = node.mesh.material as THREE.MeshPhongMaterial;
    const glowMat = node.glowMesh.material as THREE.MeshBasicMaterial;

    // Floating bob
    const bobPhase = name.length * 0.7 + t * 0.6;
    const bob = Math.sin(bobPhase) * 0.08;
    node.mesh.position.y = node.basePosition.y + bob;
    node.glowMesh.position.y = node.basePosition.y + bob;

    // Activity decay
    if (node.activity > 0) {
      node.activity = Math.max(0, node.activity - _dt * 0.15);
    }

    // Pulse based on activity
    const pulse = 0.3 + node.activity * 0.7;
    mat.emissiveIntensity = pulse + Math.sin(t * 2 + name.length) * 0.05;
    glowMat.opacity = 0.05 + node.activity * 0.25;

    // Scale on hover
    const isHovered = state.hoveredNode === name;
    const targetScale = isHovered ? 1.8 : 1.0 + node.activity * 0.5;
    const currentScale = node.mesh.scale.x;
    const newScale = currentScale + (targetScale - currentScale) * 0.1;
    node.mesh.scale.setScalar(newScale);
    node.glowMesh.scale.setScalar(newScale * 1.6);
  }

  // Animate connection line opacity
  for (const line of state.connectionLines) {
    const mat = line.material as THREE.LineBasicMaterial;
    mat.opacity = 0.04 + Math.sin(t * 0.5) * 0.02;
  }

  // Animate layer ring opacity
  for (const lr of state.layerRings) {
    const mat = lr.ring.material as THREE.LineBasicMaterial;
    const isFocused = state.focusedLayer === lr.layerId;
    const targetOpacity = isFocused ? 0.5 : 0.12;
    mat.opacity += (targetOpacity - mat.opacity) * 0.05;
  }

  state.renderer.render(state.scene, state.camera);
}

export function activateAgent(state: SceneState, agentName: string) {
  const node = state.nodes.get(agentName);
  if (node) {
    node.activity = 1.0;
    node.lastActiveTime = state.clock.getElapsedTime();
  }
}

export function focusLayer(state: SceneState, layerId: string | null) {
  state.focusedLayer = layerId;
  if (layerId && layerId !== "meta") {
    const radius = LAYER_RADII[layerId] ?? 6;
    const y = LAYER_Y[layerId] ?? 0;
    state.targetLookAt.set(0, y, 0);
    state.autoRotateSpeed = 0.12;
  } else {
    state.targetLookAt.set(0, 0, 0);
    state.autoRotateSpeed = 0.08;
  }
}

export function handleResize(state: SceneState, width: number, height: number) {
  state.camera.aspect = width / height;
  state.camera.updateProjectionMatrix();
  state.renderer.setSize(width, height);
}

export function hitTest(state: SceneState, x: number, y: number, rect: DOMRect): string | null {
  state.mouse.x = ((x - rect.left) / rect.width) * 2 - 1;
  state.mouse.y = -((y - rect.top) / rect.height) * 2 + 1;
  state.raycaster.setFromCamera(state.mouse, state.camera);

  const meshes = Array.from(state.nodes.values()).map((n) => n.mesh);
  const intersects = state.raycaster.intersectObjects(meshes);
  if (intersects.length > 0) {
    return intersects[0].object.userData.agentName ?? null;
  }
  return null;
}

export function dispose(state: SceneState) {
  state.renderer.dispose();
  for (const node of state.nodes.values()) {
    node.mesh.geometry.dispose();
    (node.mesh.material as THREE.Material).dispose();
    node.glowMesh.geometry.dispose();
    (node.glowMesh.material as THREE.Material).dispose();
  }
  for (const lr of state.layerRings) {
    lr.ring.geometry.dispose();
    (lr.ring.material as THREE.Material).dispose();
  }
  for (const cl of state.connectionLines) {
    cl.geometry.dispose();
    (cl.material as THREE.Material).dispose();
  }
}
