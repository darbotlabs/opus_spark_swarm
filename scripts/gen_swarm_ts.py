"""Generate a TypeScript module exporting the swarm registry data."""

import json
from pathlib import Path

data = json.loads(Path("src/opus_spark_swarm/swarm/swarm_registry.json").read_text(encoding="utf-8"))

ts_content = 'import type { SwarmRegistry } from "@/types/swarm";\n\n'
ts_content += "export const SWARM_REGISTRY: SwarmRegistry = "
ts_content += json.dumps(data, indent=2)
ts_content += " as SwarmRegistry;\n"

Path("spark/src/lib/swarm-data.ts").write_text(ts_content, encoding="utf-8")
print("Written spark/src/lib/swarm-data.ts")
