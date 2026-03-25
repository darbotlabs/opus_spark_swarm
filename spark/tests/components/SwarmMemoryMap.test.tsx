import { describe, it, expect, vi, beforeAll } from "vitest";
import { render, screen } from "@testing-library/react";
import { SwarmMemoryMap } from "../../src/components/SwarmMemoryMap";
import type { SwarmRegistry } from "../../src/types/swarm";

// Mock Three.js since jsdom has no WebGL context
vi.mock("three", () => {
  const Vector3 = vi.fn().mockImplementation((x = 0, y = 0, z = 0) => ({
    x, y, z,
    set: vi.fn().mockReturnThis(),
    copy: vi.fn().mockReturnThis(),
    clone: vi.fn().mockReturnThis(),
    lerp: vi.fn().mockReturnThis(),
    lerpVectors: vi.fn().mockReturnThis(),
    setScalar: vi.fn().mockReturnThis(),
  }));
  const Vector2 = vi.fn().mockImplementation(() => ({ x: 0, y: 0, set: vi.fn() }));
  const mockMaterial = { dispose: vi.fn(), transparent: true, opacity: 0.5, emissiveIntensity: 0.3, color: {} };
  const mockGeometry = { dispose: vi.fn(), setFromPoints: vi.fn().mockReturnThis() };
  const mockMesh = {
    position: { x: 0, y: 0, z: 0, copy: vi.fn(), set: vi.fn(), lerp: vi.fn() },
    scale: { x: 1, setScalar: vi.fn() },
    material: mockMaterial,
    geometry: mockGeometry,
    userData: {},
  };
  return {
    Scene: vi.fn().mockImplementation(() => ({
      add: vi.fn(),
      fog: null,
    })),
    PerspectiveCamera: vi.fn().mockImplementation(() => ({
      position: { set: vi.fn(), lerp: vi.fn(), x: 12, y: 8, z: 12 },
      aspect: 1,
      updateProjectionMatrix: vi.fn(),
      lookAt: vi.fn(),
    })),
    WebGLRenderer: vi.fn().mockImplementation(() => ({
      setSize: vi.fn(),
      setPixelRatio: vi.fn(),
      setClearColor: vi.fn(),
      render: vi.fn(),
      dispose: vi.fn(),
      domElement: document.createElement("canvas"),
    })),
    SphereGeometry: vi.fn().mockReturnValue(mockGeometry),
    BufferGeometry: vi.fn().mockImplementation(() => mockGeometry),
    MeshPhongMaterial: vi.fn().mockReturnValue(mockMaterial),
    MeshBasicMaterial: vi.fn().mockReturnValue(mockMaterial),
    LineBasicMaterial: vi.fn().mockReturnValue(mockMaterial),
    Mesh: vi.fn().mockReturnValue({ ...mockMesh }),
    Line: vi.fn().mockReturnValue({ ...mockMesh }),
    AmbientLight: vi.fn().mockReturnValue({ position: { set: vi.fn() } }),
    PointLight: vi.fn().mockReturnValue({ position: { set: vi.fn() } }),
    GridHelper: vi.fn().mockReturnValue({ position: { y: 0 }, material: mockMaterial }),
    Raycaster: vi.fn().mockImplementation(() => ({
      setFromCamera: vi.fn(),
      intersectObjects: vi.fn().mockReturnValue([]),
    })),
    Clock: vi.fn().mockImplementation(() => ({
      getElapsedTime: vi.fn().mockReturnValue(0),
    })),
    FogExp2: vi.fn(),
    QuadraticBezierCurve3: vi.fn().mockImplementation(() => ({
      getPoints: vi.fn().mockReturnValue([]),
    })),
    Vector3,
    Vector2,
  };
});

const MOCK_REGISTRY: SwarmRegistry = {
  version: "1.0.0",
  agent_count: 3,
  layers: {
    engineering: {
      label: "Engineering",
      purpose: "Code analysis",
      agent_count: 2,
      agents: ["dayour-swe", "dayour-architect"],
    },
    meta: {
      label: "Meta / Twin",
      purpose: "Root coordinator",
      agent_count: 1,
      agents: ["dayour"],
    },
  },
  agents: {
    "dayour-swe": {
      name: "dayour-swe",
      description: "SWE specialist",
      model: "gpt-5.4",
      mcps: ["github-mcp"],
      layer: "engineering",
      layer_label: "Engineering",
      definition_file: "dayour-swe.md",
      definition_lines: 243,
      section_count: 11,
    },
    "dayour-architect": {
      name: "dayour-architect",
      description: "System design",
      model: "gpt-5.4",
      mcps: [],
      layer: "engineering",
      layer_label: "Engineering",
      definition_file: "dayour-architect.md",
      definition_lines: 180,
      section_count: 8,
    },
    dayour: {
      name: "dayour",
      description: "Root coordinator",
      model: "claude-opus-4.6",
      mcps: ["ado-mcp"],
      layer: "meta",
      layer_label: "Meta / Twin",
      definition_file: "dayour.md",
      definition_lines: 645,
      section_count: 17,
    },
  },
  model_distribution: { "gpt-5.4": 2, "claude-opus-4.6": 1 },
  layer_distribution: { engineering: 2, meta: 1 },
};

describe("SwarmMemoryMap", () => {
  it("renders the card title", () => {
    render(<SwarmMemoryMap registry={MOCK_REGISTRY} />);
    expect(screen.getByText("Swarm Memory Map")).toBeInTheDocument();
  });

  it("renders the 3D badge", () => {
    render(<SwarmMemoryMap registry={MOCK_REGISTRY} />);
    expect(screen.getByText("3D")).toBeInTheDocument();
  });

  it("renders the canvas container", () => {
    render(<SwarmMemoryMap registry={MOCK_REGISTRY} />);
    expect(screen.getByTestId("memory-map-container")).toBeInTheDocument();
  });

  it("renders the canvas element", () => {
    render(<SwarmMemoryMap registry={MOCK_REGISTRY} />);
    expect(screen.getByTestId("memory-map-canvas")).toBeInTheDocument();
  });

  it("renders agent count in stats bar", () => {
    render(<SwarmMemoryMap registry={MOCK_REGISTRY} />);
    expect(screen.getByText(/3 agents across 2 layers/)).toBeInTheDocument();
  });

  it("renders model distribution in stats bar", () => {
    render(<SwarmMemoryMap registry={MOCK_REGISTRY} />);
    expect(screen.getByText(/GPT-5.4: 2/)).toBeInTheDocument();
    expect(screen.getByText(/Claude Opus 4.6: 1/)).toBeInTheDocument();
  });

  it("renders layer selector buttons", () => {
    render(<SwarmMemoryMap registry={MOCK_REGISTRY} />);
    expect(screen.getByTestId("layer-btn-engineering")).toBeInTheDocument();
    expect(screen.getByTestId("layer-btn-meta")).toBeInTheDocument();
  });

  it("renders layer labels with agent counts", () => {
    render(<SwarmMemoryMap registry={MOCK_REGISTRY} />);
    expect(screen.getByText("Engineering (2)")).toBeInTheDocument();
    expect(screen.getByText("Meta / Twin (1)")).toBeInTheDocument();
  });

  it("renders reset view button", () => {
    render(<SwarmMemoryMap registry={MOCK_REGISTRY} />);
    const resetBtn = screen.getByTitle("Reset view");
    expect(resetBtn).toBeInTheDocument();
  });
});
