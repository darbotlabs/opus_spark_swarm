# Opus Spark Swarm

**Opus with GitHub Spark Continuous Generative Showcase powered by AutoGen2 (AG2) Agent Teams**

[![Built with Claude Opus](https://img.shields.io/badge/Built%20with-Claude%20Opus%20-blueviolet?style=for-the-badge&logo=anthropic)](https://anthropic.com)
[![AG2 Framework](https://img.shields.io/badge/AG2-AutoGen2-orange?style=for-the-badge)](https://ag2.ai)
[![GitHub Spark](https://img.shields.io/badge/GitHub-Spark-blue?style=for-the-badge&logo=github)](https://githubnext.com/projects/github-spark)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-green?style=for-the-badge&logo=python)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

---

## Overview

Opus Spark Swarm is a **continuous, autonomous generative AI showcase** that orchestrates specialized [AG2 (AutoGen2)](https://ag2.ai/) agent teams — all powered by **Claude Opus ** — to analyze businesses, generate tailored problem statements, produce multi-document solution architectures, and deliver executable Jupyter notebooks. It runs on **GitHub Spark** as a live, interactive demonstration of what coordinated LLM agent swarms can accomplish end-to-end with zero human intervention after the initial prompt.

### What It Does

1. **You provide a company name or business prompt** (or let the system suggest one).
2. Agent teams autonomously research the company via public APIs.
3. They identify real business problems and generate formal problem statements.
4. Specialized agents design, debate, and refine multi-faceted solutions.
5. The system produces analysis documents, architecture diagrams, and a runnable Jupyter notebook — all in one continuous pipeline.

---

## Architecture

```
                         +---------------------------+
                         |     User Prompt / Input    |
                         |  (Company name, problem,   |
                         |   or "surprise me")        |
                         +------------+--------------+
                                      |
                                      v
                    +----------------------------------+
                    |       Orchestrator Agent          |
                    |    (AG2 GroupChatManager)         |
                    |    Claude Opus  backbone      |
                    +-------+----------+-------+------+
                            |          |       |
               +------------+    +-----+---+   +------------+
               v                 v         v                v
  +-------------------+ +------------+ +-------------+ +------------------+
  | Research Agent    | | Analyst    | | Solution    | | Notebook         |
  | Team              | | Agent Team | | Architect   | | Generator Agent  |
  |                   | |            | | Team        | |                  |
  | - Company Lookup  | | - Problem  | | - Design    | | - Code Cells     |
  | - Public API      | |   Framing  | | - Debate &  | | - Markdown Docs  |
  |   Queries         | | - SWOT     | |   Refine    | | - Visualization  |
  | - News & Filings  | | - Gap      | | - Trade-off | | - Executable     |
  | - Market Data     | |   Analysis | |   Analysis  | |   Deliverable    |
  +-------------------+ +------------+ +-------------+ +------------------+
               |                 |              |                |
               v                 v              v                v
        +---------------------------------------------------------+
        |              Document Assembly Agent                     |
        |  Merges all outputs into structured deliverables         |
        +---------------------------------------------------------+
                                 |
                                 v
                    +---------------------------+
                    |     Final Deliverables     |
                    |                           |
                    |  - Business Analysis PDF  |
                    |  - Solution Blueprint     |
                    |  - Jupyter Notebook       |
                    |  - Executive Summary      |
                    +---------------------------+
```

---

## Agent Teams

The swarm is composed of **five coordinated agent teams**, each with distinct roles, tools, and collaboration patterns.

### 1. Orchestrator Agent

| Property | Detail |
|----------|--------|
| **Role** | Central coordinator and workflow manager |
| **Model** | Claude Opus  |
| **AG2 Type** | `GroupChatManager` |
| **Responsibilities** | Routes tasks between teams, manages state transitions, enforces quality gates, handles retries and fallbacks |

The Orchestrator manages the full pipeline lifecycle. It determines task ordering, resolves inter-team dependencies, and ensures each phase completes before the next begins. If an agent team produces insufficient output, the Orchestrator triggers a refinement loop.

### 2. Research Agent Team

| Property | Detail |
|----------|--------|
| **Role** | Company intelligence gathering |
| **Agents** | `CompanyLookupAgent`, `MarketDataAgent`, `NewsAgent`, `FilingsAgent` |
| **Tools** | Public API integrations (see [Data Sources](#data-sources)) |
| **Output** | Structured company profile with market context |

**Workflow:**
1. `CompanyLookupAgent` resolves the company name to structured identifiers (ticker, CIK, domain) using public registries.
2. `MarketDataAgent` pulls financial summaries, sector benchmarks, and competitor landscapes.
3. `NewsAgent` retrieves recent headlines, press releases, and sentiment signals.
4. `FilingsAgent` fetches and summarizes relevant public documents (SEC filings, annual reports).
5. All agents contribute to a unified **Company Intelligence Dossier**.

### 3. Analyst Agent Team

| Property | Detail |
|----------|--------|
| **Role** | Problem identification and statement generation |
| **Agents** | `ProblemFramerAgent`, `SWOTAgent`, `GapAnalysisAgent`, `StatementWriterAgent` |
| **Output** | Ranked list of business problem statements with supporting analysis |

**Workflow:**
1. `ProblemFramerAgent` ingests the Company Intelligence Dossier and identifies candidate problem domains (operational, strategic, technical, market-facing).
2. `SWOTAgent` performs a Strengths/Weaknesses/Opportunities/Threats analysis grounded in the research data.
3. `GapAnalysisAgent` identifies discrepancies between current state and industry benchmarks.
4. `StatementWriterAgent` synthesizes findings into **3-5 formal business problem statements**, each with:
   - Problem title
   - Context and evidence
   - Impact assessment (quantified where possible)
   - Stakeholders affected
   - Suggested priority ranking

### 4. Solution Architect Agent Team

| Property | Detail |
|----------|--------|
| **Role** | Solution design through structured debate |
| **Agents** | `ProposalAgent`, `CriticAgent`, `FeasibilityAgent`, `RefinementAgent` |
| **Pattern** | Adversarial collaboration (propose-critique-refine loop) |
| **Output** | Solution blueprint with architecture, implementation roadmap, and trade-off analysis |

**Workflow:**
1. `ProposalAgent` generates an initial solution design for the highest-priority problem statement.
2. `CriticAgent` challenges assumptions, identifies risks, and flags gaps in the proposal.
3. `FeasibilityAgent` evaluates technical feasibility, cost implications, and implementation complexity.
4. `RefinementAgent` synthesizes feedback and produces a revised solution.
5. Steps 2-4 repeat for a configurable number of rounds (default: 3) or until the Orchestrator's quality gate is satisfied.

The final output is a **Solution Blueprint** containing:
- Executive summary
- Proposed architecture (with component descriptions)
- Implementation phases and milestones
- Risk register with mitigations
- Resource and cost estimates
- Success metrics and KPIs

### 5. Notebook Generator Agent

| Property | Detail |
|----------|--------|
| **Role** | Executable deliverable creation |
| **Agents** | `CodeGenAgent`, `MarkdownAgent`, `VisualizationAgent`, `ValidationAgent` |
| **Output** | Self-contained Jupyter notebook (`.ipynb`) |

**Workflow:**
1. `MarkdownAgent` creates narrative sections: problem background, methodology, analysis walkthrough, and conclusions.
2. `CodeGenAgent` writes Python code cells for data retrieval, transformation, analysis, and modeling.
3. `VisualizationAgent` adds charts, diagrams, and visual summaries using `matplotlib`, `plotly`, or `mermaid`.
4. `ValidationAgent` reviews the notebook for correctness, completeness, and executability.

---

## DAYOURBOT Swarm Integration

Beyond the 5 pipeline-specific agent teams above, Opus Spark Swarm integrates with the full **DAYOURBOT swarm** -- a fleet of 67 specialist agents organized into 8 functional layers. The swarm registry is loaded from `swarm_registry.json` and agents are instantiated on-demand via the `SwarmAgentFactory`.

### Swarm Architecture

```
                    +---------------------------+
                    |       dayswarm            |
                    |  (broadcast-gather-synth) |
                    +------------+--------------+
                                 |
                    +------------+--------------+
                    |        dayour             |
                    |   (root coordinator)      |
                    +--+-----+-----+-----+-----+
                       |     |     |     |
          +------------+  +--+--+  |  +--+----------+
          v              v      v  v  v              v
  +-----------+  +---------+  +------+  +---------+  +----------+
  | Strategy  |  |Platform |  |Engi- |  |Content  |  |Customer  |
  | & Org     |  |Special- |  |neer- |  |& Docs   |  |Engage-   |
  | (3)       |  |ists(17) |  |ing   |  |(8)      |  |ments (7) |
  +-----------+  +---------+  |(14)  |  +---------+  +----------+
                               +------+
                                  |
                          +-------+-------+
                          v               v
                   +----------+    +----------+
                   |Intelli-  |    |Orchest-  |
                   |gence (7) |    |ration (9)|
                   +----------+    +----------+
```

### Layer Taxonomy (67 agents, 8 layers)

| Layer | Agents | Models | Purpose |
|-------|--------|--------|---------|
| **Strategy & Org** | dayour-cape, dayour-cat, dayour-bat | 3 | Org-level planning, customer acceleration, engineering IP |
| **Platform Specialists** | dayour-studio, dayour-pplat, dayour-dynamics, dayour-fabric, dayour-azure, dayour-purview, dayour-copilot, dayour-dataverse, dayour-entra, dayour-foundry, dayour-graph, dayour-intune, dayour-m365, dayour-onedrive, dayour-sharepoint, dayour-teams, dayour-viva | 17 | Deep expertise in Copilot Studio, Power Platform, Dynamics 365, Fabric, Azure, Purview |
| **Engineering** | dayour-swe, dayour-architect, dayour-design, dayour-dev, dayour-test, dayour-qa, dayour-sre, dayour-security, dayour-data-eng, dayour-gitops, dayour-github, dayour-network, dayour-integration, dayour-finops | 14 | Code analysis, system design, ADRs, UI/UX, DevOps, security |
| **Content & Docs** | dayour-word, dayour-ppt, dayour-notes, dayour-markdown, dayour-flashcard, dayour-links, dayour-jupyter, dayour-vlib | 8 | Technical docs, presentations, note distillation, knowledge management |
| **Customer Engagements** | dayour-amica, dayour-cdw, dayour-citi, dayour-gap, dayour-hp, dayour-sbx, dayour-wynn | 7 | Per-customer engagement agents with account-specific context |
| **Intelligence & Analysis** | dayour-analyst, dayour-analytics, dayour-researcher, dayour-insights, dayour-evaluation, dayour-mlads, dayour-pmo | 7 | Research, analytics, insights, evaluation, ML/AI, program management |
| **Orchestration** | dayour-mcp, dayour-labs, dayour-mainline, dayour-swarm, dayour-ag2, dayour-agentbuilder, dayour-activity, dayour-ado, dayour-darbotlabs | 9 | MCP routing, lab environments, Teams Mainline, AG2 patterns |
| **Meta / Twin** | dayour, dayswarm | 2 | Autonomous ML digital twin (root coordinator) and broadcast-gather-synthesize meta-agent |

### Model Distribution

| Model | Agent Count | Usage |
|-------|-------------|-------|
| GPT-5.4 | 40 | Primary model for most specialist agents |
| Claude Sonnet 4.6 | 25 | Customer engagements, intelligence, select platform agents |
| Claude Opus 4.6 | 2 | Meta-layer coordinators (dayour, dayswarm) |

### Swarm Python API

```python
from opus_spark_swarm.swarm.registry import get_registry
from opus_spark_swarm.swarm.factory import SwarmAgentFactory
from opus_spark_swarm.swarm.router import SwarmRouter

# Query the registry
registry = get_registry()
print(registry.agent_count)            # 67
print(registry.layer_count)            # 8
agent = registry.get_agent("dayour-swe")
eng_team = registry.agents_in_layer("engineering")  # 14 agents

# Create AG2 agents from registry
factory = SwarmAgentFactory(settings)
swe = factory.create("dayour-swe")              # Single agent
eng_agents = factory.create_layer("engineering") # All 14

# Route prompts to layers
router = SwarmRouter(settings)
routing = router.classify("Review the auth module for security issues")
# => RoutingResult(target_layers=["engineering"], target_agents=[...])

# Scatter-gather across multiple layers
response = await router.scatter_gather("Analyse Shopify's supply chain")
```

---

## Data Sources

The Research Agent Team integrates with the following **public, free-tier APIs** (no paid keys required for basic operation):

| API | Purpose | Data Retrieved |
|-----|---------|----------------|
| [SEC EDGAR](https://www.sec.gov/edgar/sec-api-documentation) | Public company filings | 10-K, 10-Q, 8-K filings and financial data |
| [OpenCorporates](https://api.opencorporates.com/) | Company registry lookup | Incorporation details, officers, status |
| [Wikidata / Wikipedia](https://www.wikidata.org/) | General company information | Descriptions, founding date, industry, HQ |
| [News API](https://newsapi.org/) | Recent news articles | Headlines, sentiment, publication dates |
| [Alpha Vantage](https://www.alphavantage.co/) | Market and financial data | Stock prices, key ratios, sector performance |
| [FRED (Federal Reserve)](https://fred.stlouisfed.org/docs/api/) | Economic indicators | Industry benchmarks, economic context |
| [GitHub API](https://docs.github.com/en/rest) | Tech company OSS footprint | Repository activity, tech stack signals |

> **Note:** Some APIs require free registration for an API key. See [Configuration](#configuration) for setup.

---

## Features

### Continuous Generative Pipeline
The system runs autonomously from prompt to deliverables. Each agent team's output feeds directly into the next, with the Orchestrator managing state, retries, and quality gates. No human intervention is required after the initial input.

### Business Problem Suggestions
Don't know where to start? Provide just a company name and the Analyst Agent Team will generate **ranked business problem statements** derived from real public data — not hallucinated scenarios.

### Document Analysis
Upload existing documents (PDFs, reports, slide decks) as additional context. The Research Agent Team will parse and incorporate them into the Company Intelligence Dossier, enabling more targeted problem identification and solution design.

### Adversarial Solution Refinement
Solutions aren't generated in a single pass. The Solution Architect Team uses a **propose-critique-refine loop** where agents challenge each other's assumptions, producing more robust and realistic outputs.

### Executable Jupyter Notebooks
Every run produces a Jupyter notebook that:
- Tells the full analytical story in narrative markdown
- Contains runnable Python code for data retrieval and analysis
- Includes visualizations (charts, tables, diagrams)
- Can be re-executed with modified parameters for further exploration

### GitHub Spark Integration
Deployed as a GitHub Spark application for:
- Live interactive demonstration
- Shareable, persistent sessions
- Automatic environment provisioning
- No local setup required for viewers

---

## Project Structure

```
Opus-Spark-Swarm/
├── README.md
├── LICENSE
├── pyproject.toml
├── .env.example
├── .github/
│   └── workflows/
│       └── spark.yml               # GitHub Spark deployment
│
│   ┌─────────────────────────────────────────────────────┐
│   │  Python Backend (AG2 Pipeline)                      │
│   └─────────────────────────────────────────────────────┘
├── src/
│   └── opus_spark_swarm/
│       ├── __init__.py
│       ├── main.py                  # Entry point and CLI
│       ├── config.py                # Configuration and environment
│       ├── orchestrator/
│       │   ├── __init__.py
│       │   ├── pipeline.py          # End-to-end pipeline controller
│       │   └── quality_gates.py     # Output quality validation
│       ├── agents/
│       │   ├── __init__.py
│       │   ├── base.py              # Base agent configuration
│       │   ├── research/
│       │   │   ├── __init__.py
│       │   │   ├── company_lookup.py
│       │   │   ├── market_data.py
│       │   │   ├── news.py
│       │   │   └── filings.py
│       │   ├── analyst/
│       │   │   ├── __init__.py
│       │   │   ├── problem_framer.py
│       │   │   ├── swot.py
│       │   │   ├── gap_analysis.py
│       │   │   └── statement_writer.py
│       │   ├── architect/
│       │   │   ├── __init__.py
│       │   │   ├── proposal.py
│       │   │   ├── critic.py
│       │   │   ├── feasibility.py
│       │   │   └── refinement.py
│       │   └── notebook/
│       │       ├── __init__.py
│       │       ├── codegen.py
│       │       ├── markdown.py
│       │       ├── visualization.py
│       │       └── validation.py
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── api_clients.py       # Public API wrappers
│       │   ├── document_parser.py   # PDF/document ingestion
│       │   └── notebook_builder.py  # Jupyter notebook assembly
│       └── templates/
│           ├── notebook_base.ipynb   # Notebook skeleton
│           └── prompts/
│               ├── research.md
│               ├── analysis.md
│               ├── architecture.md
│               └── notebook.md
│
│   ┌─────────────────────────────────────────────────────┐
│   │  Spark Frontend (React 19 + Vite)                   │
│   └─────────────────────────────────────────────────────┘
├── spark/                            # Spark UI micro-app
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── components.json              # shadcn/ui configuration
│   └── src/
│       ├── App.tsx                   # Main app component (default export)
│       ├── index.css                 # Theme variables (oklch colors)
│       ├── main.tsx                  # Runtime-managed entry (DO NOT EDIT)
│       ├── main.css                  # Runtime-managed styles (DO NOT EDIT)
│       ├── components/
│       │   ├── ui/                   # Pre-installed shadcn/ui components
│       │   ├── CompanyInput.tsx      # Company search with autocomplete
│       │   ├── ProblemSelector.tsx   # Problem statement picker
│       │   ├── AgentActivityFeed.tsx # Real-time agent collaboration view
│       │   ├── NotebookViewer.tsx    # Rendered Jupyter output
│       │   └── SessionHistory.tsx    # Previous run comparison
│       ├── hooks/
│       │   └── use-mobile.ts
│       ├── lib/
│       │   └── utils.ts             # shadcn class helper (cn)
│       └── assets/
│           └── images/
│
├── notebooks/
│   ├── demo.ipynb                   # Interactive demo notebook
│   └── examples/
│       ├── retail_analysis.ipynb
│       ├── fintech_solution.ipynb
│       └── saas_optimization.ipynb
├── tests/
│   ├── __init__.py
│   ├── test_pipeline.py
│   ├── test_agents/
│   └── test_tools/
└── docs/
    ├── agent_design.md
    ├── api_reference.md
    └── examples.md
```

---

## Getting Started

### Prerequisites

- **Python 3.11+**
- **Anthropic API key** with access to Claude Opus 
- (Optional) Free API keys for enhanced data sources (see [Data Sources](#data-sources))

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/Opus-Spark-Swarm.git
cd Opus-Spark-Swarm

# Install with dependencies
pip install -e ".[dev]"

# Or using uv (recommended)
uv pip install -e ".[dev]"
```

### Configuration

```bash
# Copy the example environment file
cp .env.example .env
```

Edit `.env` with your API keys:

```env
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Optional — enhance research capabilities
SEC_EDGAR_USER_AGENT=YourName your@email.com
NEWS_API_KEY=your-newsapi-key
ALPHA_VANTAGE_API_KEY=your-alphavantage-key
FRED_API_KEY=your-fred-key

# Pipeline settings
MAX_REFINEMENT_ROUNDS=3
QUALITY_THRESHOLD=0.8
OUTPUT_DIR=./output
```

### Run the Pipeline

**CLI — Full pipeline from a company name:**

```bash
opus-spark-swarm run --company "Shopify"
```

**CLI — From a custom business problem:**

```bash
opus-spark-swarm run --prompt "How can a mid-size logistics company reduce last-mile delivery costs by 20% using AI-driven route optimization?"
```

**CLI — Generate problem suggestions only:**

```bash
opus-spark-swarm suggest --company "Tesla"
```

**CLI — With document upload:**

```bash
opus-spark-swarm run --company "Stripe" --documents ./reports/stripe_annual_2025.pdf
```

**Jupyter — Interactive mode:**

```bash
jupyter lab notebooks/demo.ipynb
```

---

## Example Output

Below is a condensed example of what the pipeline produces for the input `--company "Shopify"`:

### Generated Problem Statements (Top 3)

| # | Problem Statement | Priority | Impact |
|---|-------------------|----------|--------|
| 1 | **Merchant Churn Prediction**: Shopify's SMB merchant base experiences 18-22% annual churn. Lack of predictive churn modeling leads to reactive retention efforts and estimated $400M+ in lost annual GMV. | Critical | Revenue retention |
| 2 | **Cross-Border Payment Friction**: International merchants face 3-5 day settlement delays and 2.8% average FX conversion costs, creating competitive disadvantage vs. localized platforms. | High | Market expansion |
| 3 | **App Ecosystem Quality Control**: With 8,000+ apps in the Shopify App Store, inconsistent quality and security standards create merchant trust erosion and support burden. | Medium | Platform integrity |

### Solution Blueprint Preview

```
Problem: Merchant Churn Prediction
Solution: ML-Driven Merchant Health Scoring Platform

Phase 1 (Months 1-3): Data pipeline — aggregate merchant activity signals
Phase 2 (Months 3-6): Model development — survival analysis + gradient boosting ensemble
Phase 3 (Months 6-9): Integration — real-time scoring API + merchant success dashboard
Phase 4 (Months 9-12): Automation — trigger-based intervention workflows

Estimated Impact: 15-25% reduction in preventable churn
Confidence: High (based on comparable implementations at Block, Toast)
```

### Generated Notebook

The output notebook contains:
- 12 narrative markdown cells with business context
- 8 executable code cells (data retrieval, feature engineering, model prototype)
- 5 visualizations (churn funnel, cohort analysis, feature importance, ROC curve, impact projection)
- Fully runnable with `pip install -r requirements.txt && jupyter lab`

---

## GitHub Spark Deployment

This project is designed to run as a **GitHub Spark** application. Spark handles environment provisioning, dependency installation, and provides a shareable interactive frontend.

> **Reference:** For comprehensive Spark platform documentation derived from the system prompt, see Simon Willison's [reverse-engineering writeup](https://simonwillison.net/2025/Jul/24/github-spark/) and the interactive explorer at [github-spark-docs.simonwillison.net](https://github-spark-docs.simonwillison.net/).

### Deploy to Spark

1. Fork this repository.
2. Navigate to [GitHub Spark](https://githubnext.com/projects/github-spark).
3. Import the repository as a new Spark.
4. Set your `ANTHROPIC_API_KEY` in the Spark secrets configuration.
5. The application will be live and shareable via a unique Spark URL.

### Spark UI Features

- **Company input field** with autocomplete suggestions
- **Problem statement selector** — choose which generated problems to solve
- **Live agent activity feed** — watch the agent teams collaborate in real-time
- **Document upload** — drag-and-drop PDFs for additional context
- **Notebook viewer** — rendered Jupyter output with download option
- **Session history** — review and compare previous runs

### Spark Frontend Architecture

The Spark UI layer is a **Vite micro-app** running React 19 inside the Spark runtime container. The stack:

| Layer | Technology |
|-------|-----------|
| **Framework** | React 19 with TypeScript |
| **Bundler** | Vite 6 (`@vitejs/plugin-react-swc`) |
| **Styling** | Tailwind CSS 4 with CSS custom properties (`oklch` color values) |
| **Components** | shadcn/ui v4 (pre-installed at `@/components/ui`) |
| **Icons** | `@phosphor-icons/react` |
| **Notifications** | `sonner` for toast messages |
| **Animation** | `framer-motion` (sparingly, for purposeful UX) |
| **Charts** | D3, Recharts |
| **3D** | Three.js (optional) |

**Key constraints enforced by the Spark runtime:**

- Only isomorphic or browser-compatible npm packages are allowed. Node-only packages will break the application.
- Do not use `localStorage` or `sessionStorage`. Use the `useKV` hook (see below) for persistent state.
- `src/main.tsx` and `src/main.css` are structural files managed by the runtime and must not be modified.
- The application entry point is `src/App.tsx` (default export, no manual mounting).
- Assets must be imported explicitly (`import logo from '@/assets/images/logo.png'`), not referenced by string path.

### Spark Runtime API

The Spark runtime exposes a global `spark` object (no import required) and a React hook for persistent storage. These APIs are the primary integration surface between the Spark UI and the pipeline backend.

#### Type Definition

```typescript
declare global {
  interface Window {
    spark: {
      llmPrompt: (strings: string[], ...values: any[]) => string
      llm: (prompt: string, modelName?: string, jsonMode?: boolean) => Promise<string>
      user: () => Promise<UserInfo>
      kv: {
        keys: () => Promise<string[]>
        get: <T>(key: string) => Promise<T | undefined>
        set: <T>(key: string, value: T) => Promise<void>
        delete: (key: string) => Promise<void>
      }
    }
  }
}
```

#### Key-Value Storage (`useKV`)

The `useKV` hook provides reactive, persistent state that survives page refreshes. Use it for session history, user preferences, and pipeline results.

```typescript
import { useKV } from '@github/spark/hooks'

// Persistent state: survives page refresh
const [sessions, setSessions, deleteSessions] = useKV("pipeline-sessions", [])

// Use functional updates to avoid stale closures
setSessions((current) => [...current, newSession])
```

**Decision rule:** Ask "Should this survive a page refresh?" If yes, use `useKV`. If no, use `useState`.

#### LLM Integration (`spark.llm`)

Spark provides a built-in LLM endpoint for lightweight UI-side inference (summaries, formatting, suggestions). All prompts must be constructed with `spark.llmPrompt`.

```typescript
// Construct the prompt (REQUIRED: use spark.llmPrompt, not raw strings)
const prompt = spark.llmPrompt`Summarize these business problems for an executive audience: ${problemStatements}`
const summary = await spark.llm(prompt)

// JSON mode for structured responses
const structured = await spark.llm(prompt, "gpt-4o", true)
```

Available models: `gpt-4o` (default), `gpt-4o-mini`.

NOTE: This is for lightweight UI-side tasks (formatting, summarisation, suggestions). The heavy-lifting analysis pipeline uses Claude Opus via the AG2 backend, not `spark.llm`.

#### User Context (`spark.user`)

```typescript
const user = await spark.user()
// Returns: { avatarUrl, email, id, isOwner, login }

if (user.isOwner) {
  // Show admin features: pipeline config, API key management, debug logs
}
```

#### Direct KV API (Non-React Contexts)

For use outside React components (utility functions, async handlers):

```typescript
await spark.kv.set("last-run-config", { company: "Shopify", phase: "full" })
const config = await spark.kv.get<RunConfig>("last-run-config")
const allKeys = await spark.kv.keys()
await spark.kv.delete("last-run-config")
```

---

## AG2 Framework Integration

This project uses the [AG2 (AutoGen2)](https://ag2.ai/) framework for multi-agent orchestration. Key AG2 patterns employed:

### GroupChat with Custom Speaker Selection
```python
from autogen import GroupChat, GroupChatManager

research_chat = GroupChat(
    agents=[company_lookup, market_data, news, filings],
    messages=[],
    max_round=12,
    speaker_selection_method="auto",  # Claude Opus  selects next speaker
)
```

### Tool-Augmented Agents
```python
from autogen import ConversableAgent

company_lookup = ConversableAgent(
    name="CompanyLookupAgent",
    system_message="You research companies using public registries...",
    llm_config={"model": "claude-opus-4-6", "api_type": "anthropic"},
)

# Register API tools
@company_lookup.register_for_execution()
@market_data.register_for_llm(description="Look up a company by name")
def lookup_company(name: str) -> dict:
    ...
```

### Nested Group Chats
The Orchestrator manages team-level group chats as nested conversations, enabling clean separation of concerns while maintaining a coherent pipeline.

---

## Configuration Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | *required* | Claude Opus  API access |
| `AG2_MODEL` | `claude-opus-4-6` | Model identifier for all agents |
| `MAX_REFINEMENT_ROUNDS` | `3` | Solution propose-critique-refine iterations |
| `QUALITY_THRESHOLD` | `0.8` | Minimum quality score to pass gates (0-1) |
| `OUTPUT_DIR` | `./output` | Where deliverables are written |
| `MAX_RESEARCH_DEPTH` | `standard` | Research depth: `minimal`, `standard`, `deep` |
| `NOTEBOOK_STYLE` | `narrative` | Notebook style: `narrative`, `technical`, `executive` |
| `ENABLE_DOCUMENT_UPLOAD` | `true` | Allow document ingestion for additional context |
| `LOG_AGENT_CONVERSATIONS` | `false` | Log full inter-agent messages (verbose) |

---

## Development

### Run Tests

```bash
pytest tests/ -v
```

### Run Linting

```bash
ruff check src/
ruff format src/
```

### Run a Single Agent Team (for development)

```bash
# Run only the research phase
opus-spark-swarm run --company "Netflix" --phase research

# Run only solution architecture on an existing analysis
opus-spark-swarm run --input ./output/netflix_analysis.json --phase architect
```

---

## Roadmap

- [x] Core pipeline: Research -> Analysis -> Solution -> Notebook
- [x] AG2 multi-agent orchestration with Claude Opus
- [x] Public API integrations (SEC EDGAR, OpenCorporates, Alpha Vantage)
- [x] Jupyter notebook generation with visualizations
- [x] GitHub Spark deployment
- [ ] Spark frontend: `useKV`-backed session persistence for pipeline runs
- [ ] Spark frontend: `spark.llm` integration for UI-side summaries and formatting
- [ ] Spark frontend: `spark.user` gating for owner-only admin features
- [ ] Streaming agent activity to Spark UI in real-time
- [ ] Multi-problem parallel solution generation
- [ ] Interactive notebook editing within Spark
- [ ] Custom agent team composition via YAML config
- [ ] PDF report generation alongside notebooks
- [ ] Historical run comparison and trend analysis
- [ ] Webhook integrations (Slack, Teams) for completed runs

---

## Contributing

Contributions are welcome. Please open an issue first to discuss proposed changes.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add your feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## Acknowledgments

- [Anthropic](https://anthropic.com) -- Claude Opus model
- [AG2 (AutoGen2)](https://ag2.ai/) -- Multi-agent orchestration framework
- [GitHub Spark](https://githubnext.com/projects/github-spark) -- Application hosting and deployment
- [SEC EDGAR](https://www.sec.gov/edgar) -- Public company financial data
- [Simon Willison](https://simonwillison.net/2025/Jul/24/github-spark/) -- Spark system prompt reverse engineering and [documentation explorer](https://github-spark-docs.simonwillison.net/)
- [spark-frame](https://github.com/simonw/spark-frame) -- Interactive Spark API documentation app that informed the Spark Runtime API section of this README

---

<p align="center">
  <strong>Built with Claude Opus  | Orchestrated by AG2 | Deployed on GitHub Spark</strong>
</p>
