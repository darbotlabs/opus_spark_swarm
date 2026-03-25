"""End-to-end pipeline controller for Opus Spark Swarm."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from opus_spark_swarm.config import Settings
from opus_spark_swarm.orchestrator.quality_gates import QualityGate

logger = logging.getLogger(__name__)


def _try_import_ag2():
    """Import AG2 components, raising a clear error if unavailable."""
    try:
        from autogen import GroupChat, GroupChatManager  # noqa: F401

        return True
    except ImportError:
        return False


def _extract_json_from_messages(messages: list[dict], fallback_key: str = "content", *, prefer_agent: str | None = None) -> dict | list | None:
    """Walk messages in reverse and return the first parseable JSON block.

    AG2 agents typically emit their structured output in the last message(s).
    We look for JSON fenced blocks (```json ... ```) or raw JSON objects.

    Parameters
    ----------
    prefer_agent:
        If provided, search messages from this agent first before falling
        back to all messages.
    """
    import re

    # If a preferred agent is specified, try its messages first.
    if prefer_agent:
        agent_msgs = [m for m in messages if m.get("name") == prefer_agent]
        result = _extract_json_from_messages(agent_msgs, fallback_key)
        if result is not None:
            return result

    for msg in reversed(messages):
        text: str = msg.get("content", "") or ""
        # Try fenced JSON blocks first
        fenced = re.findall(r"```(?:json)?\s*\n?([\s\S]*?)```", text)
        for block in fenced:
            try:
                return json.loads(block.strip())
            except (json.JSONDecodeError, ValueError):
                continue
        # Try the entire text as JSON
        try:
            return json.loads(text.strip())
        except (json.JSONDecodeError, ValueError):
            continue
    return None


class Pipeline:
    """Orchestrates the 4-phase pipeline: Research → Analysis → Architecture → Notebook.

    Uses AG2 GroupChatManager as top-level coordinator.  Each phase creates its
    team's GroupChat, runs it, extracts results, scores quality, and passes
    state to the next phase.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.gate = QualityGate(threshold=settings.quality_threshold)
        self.state: dict[str, Any] = {}

        if not _try_import_ag2():
            logger.warning(
                "AG2 (autogen) is not installed.  Install it with: "
                "pip install 'ag2[anthropic]'  --  the pipeline cannot run without it."
            )

    # ---------------------------------------------------------------- public

    async def run(
        self,
        company: str | None = None,
        prompt: str | None = None,
        documents: list[str] | None = None,
        phase: str | None = None,
    ) -> dict:
        """Run the full pipeline (or a specific *phase*).

        Parameters
        ----------
        company:
            Company name to analyse.
        prompt:
            Custom business problem prompt.
        documents:
            Optional document paths for additional context.
        phase:
            Run only ``"research"``, ``"analysis"``, ``"architecture"``,
            or ``"notebook"``.

        Returns
        -------
        dict
            Accumulated state with all phase outputs and metadata.
        """
        if not _try_import_ag2():
            raise RuntimeError(
                "AG2 (autogen) is required but not installed.  "
                "Install with: pip install 'ag2[anthropic]'"
            )

        self.state["company"] = company
        self.state["prompt"] = prompt
        self.state["documents"] = documents or []

        # Phase 1: Research
        if phase is None or phase == "research":
            logger.info("--- Phase 1: Research ---")
            dossier = await self._run_research(company, documents)
            self.state["dossier"] = dossier
            score = self.gate.score_research(dossier)
            self.state["research_score"] = score
            logger.info("Research score: %.2f / %.2f", score, self.gate.threshold)

        # Phase 2: Analysis
        if phase is None or phase in ("analysis", "analyst"):
            logger.info("--- Phase 2: Analysis ---")
            analysis = await self._run_analysis(self.state.get("dossier", {}), prompt)
            self.state["analysis"] = analysis
            score = self.gate.score_analysis(analysis)
            self.state["analysis_score"] = score
            logger.info("Analysis score: %.2f / %.2f", score, self.gate.threshold)

        # Phase 3: Architecture
        if phase is None or phase in ("architecture", "architect"):
            logger.info("--- Phase 3: Architecture ---")
            blueprint = await self._run_architecture(self.state.get("analysis", {}))
            self.state["blueprint"] = blueprint
            score = self.gate.score_architecture(blueprint)
            self.state["architecture_score"] = score
            logger.info("Architecture score: %.2f / %.2f", score, self.gate.threshold)

        # Phase 4: Notebook
        if phase is None or phase == "notebook":
            logger.info("--- Phase 4: Notebook ---")
            notebook = await self._run_notebook(self.state)
            self.state["notebook"] = notebook
            score = self.gate.score_notebook(notebook)
            self.state["notebook_score"] = score
            logger.info("Notebook score: %.2f / %.2f", score, self.gate.threshold)

        self._save_outputs()
        return self.state

    async def suggest(self, company: str) -> list[dict]:
        """Run research + analysis only, return problem statements."""
        if not _try_import_ag2():
            raise RuntimeError(
                "AG2 (autogen) is required but not installed.  "
                "Install with: pip install 'ag2[anthropic]'"
            )

        self.state["company"] = company
        logger.info("--- Suggest: Research ---")
        dossier = await self._run_research(company, None)
        self.state["dossier"] = dossier
        logger.info("Research score: %.2f", self.gate.score_research(dossier))

        logger.info("--- Suggest: Analysis ---")
        analysis = await self._run_analysis(dossier, None)
        self.state["analysis"] = analysis
        logger.info("Analysis score: %.2f", self.gate.score_analysis(analysis))

        return analysis.get("problem_statements", [])

    # ------------------------------------------------------ phase internals

    async def _run_research(self, company: str | None, documents: list[str] | None) -> dict:
        """Create research team, run GroupChat, extract dossier."""
        from autogen import GroupChat, GroupChatManager

        from opus_spark_swarm.agents.base import build_llm_config
        from opus_spark_swarm.agents.research import create_research_team

        agents = create_research_team(self.settings)

        group_chat = GroupChat(
            agents=agents,
            messages=[],
            max_round=12,
            speaker_selection_method="auto",
        )
        manager = GroupChatManager(
            groupchat=group_chat,
            llm_config=build_llm_config(self.settings),
        )

        initial_message = f"Research the company '{company or 'unknown'}'."
        if documents:
            initial_message += f"\nAdditional documents provided: {documents}"
        initial_message += (
            "\n\nGather company info, market data, recent news, and public filings. "
            "When all agents have contributed, compile a final JSON dossier with keys: "
            "company, market_data, news, filings."
        )

        # Kick off the group chat from the first agent
        await agents[0].a_initiate_chat(manager, message=initial_message)

        # Extract structured output from conversation
        dossier = _extract_json_from_messages(group_chat.messages)
        if not isinstance(dossier, dict):
            # Fallback: build dossier from raw messages
            dossier = self._build_dossier_from_messages(group_chat.messages, company)

        logger.info("Research phase complete – dossier keys: %s", list(dossier.keys()))
        return dossier

    async def _run_analysis(self, dossier: dict, prompt: str | None) -> dict:
        """Create analyst team, run GroupChat, extract problem statements."""
        from opus_spark_swarm.agents.analyst import create_analyst_team

        group_chat, manager = create_analyst_team(self.settings)

        initial_message = "Here is the Company Intelligence Dossier:\n\n"
        initial_message += json.dumps(dossier, indent=2, default=str)
        if prompt:
            initial_message += f"\n\nUser-provided business problem context:\n{prompt}"
        initial_message += (
            "\n\nAnalyse this dossier. Identify problems, perform SWOT and gap analysis, "
            "then produce 3-5 formal business problem statements. Output a final JSON object "
            "with key 'problem_statements', where each statement has: title, context, "
            "evidence, impact, stakeholders, priority."
        )

        first_agent = group_chat.agents[0]
        await first_agent.a_initiate_chat(manager, message=initial_message)

        analysis = _extract_json_from_messages(group_chat.messages, prefer_agent="StatementWriterAgent")
        if not isinstance(analysis, dict) or "problem_statements" not in analysis:
            analysis = {"problem_statements": [], "raw_messages": self._summarise_messages(group_chat.messages)}

        logger.info("Analysis phase complete – %d problem statements", len(analysis.get("problem_statements", [])))
        return analysis

    async def _run_architecture(self, analysis: dict) -> dict:
        """Create architect team, run debate loop, extract blueprint."""
        from autogen import GroupChatManager

        from opus_spark_swarm.agents.architect import create_architect_team
        from opus_spark_swarm.agents.base import build_llm_config

        group_chat = create_architect_team(self.settings)
        manager = GroupChatManager(
            groupchat=group_chat,
            llm_config=build_llm_config(self.settings),
        )

        # Feed the highest-priority problem statement
        statements = analysis.get("problem_statements", [])
        if statements:
            problem = statements[0] if isinstance(statements[0], dict) else {"title": str(statements[0])}
        else:
            problem = {"title": "General business improvement", "context": json.dumps(analysis, default=str)}

        initial_message = (
            f"Design a solution for this business problem:\n\n"
            f"{json.dumps(problem, indent=2, default=str)}\n\n"
            f"Full analysis context:\n{json.dumps(analysis, indent=2, default=str)}\n\n"
            "ProposalAgent: begin with your initial solution design. "
            "The team will iterate through propose-critique-feasibility-refine cycles. "
            "Final output must be a JSON object with keys: exec_summary, architecture, "
            "phases, risks, costs, kpis."
        )

        first_agent = group_chat.agents[0]
        await first_agent.a_initiate_chat(manager, message=initial_message)

        blueprint = _extract_json_from_messages(group_chat.messages, prefer_agent="RefinementAgent")
        if not isinstance(blueprint, dict):
            blueprint = {"raw_messages": self._summarise_messages(group_chat.messages)}

        logger.info("Architecture phase complete – blueprint keys: %s", list(blueprint.keys()))
        return blueprint

    async def _run_notebook(self, state: dict) -> list:
        """Create notebook team, run GroupChat, build .ipynb, save to disk."""
        from opus_spark_swarm.agents.notebook import create_notebook_team
        from opus_spark_swarm.tools.notebook_builder import NotebookBuilder

        group_chat, manager = create_notebook_team(self.settings)

        company = state.get("company", "Unknown")
        initial_message = (
            f"Create a Jupyter notebook for the business analysis of '{company}'.\n\n"
            f"Research dossier:\n{json.dumps(state.get('dossier', {}), indent=2, default=str)}\n\n"
            f"Problem statements:\n{json.dumps(state.get('analysis', {}), indent=2, default=str)}\n\n"
            f"Solution blueprint:\n{json.dumps(state.get('blueprint', {}), indent=2, default=str)}\n\n"
            "Build the notebook with narrative markdown, executable code cells, "
            "and visualizations. The ValidationAgent should review at the end."
        )

        first_agent = group_chat.agents[0]
        await first_agent.a_initiate_chat(manager, message=initial_message)

        # Build the notebook from agent conversation
        title = f"Business Analysis: {company}"
        builder = NotebookBuilder(title=title, style=self.settings.notebook_style)
        builder.add_setup_cell()

        for msg in group_chat.messages:
            content: str = msg.get("content", "") or ""
            name = msg.get("name", "")

            if name == "MarkdownAgent" and content.strip():
                builder.add_markdown_cell(content)
            elif name == "CodeGenAgent" and content.strip():
                # Extract code blocks if fenced, otherwise use raw content
                import re
                code_blocks = re.findall(r"```(?:python)?\s*\n?([\s\S]*?)```", content)
                if code_blocks:
                    for block in code_blocks:
                        builder.add_code_cell(block.strip())
                else:
                    builder.add_code_cell(content.strip())
            elif name == "VisualizationAgent" and content.strip():
                import re
                code_blocks = re.findall(r"```(?:python)?\s*\n?([\s\S]*?)```", content)
                if code_blocks:
                    for block in code_blocks:
                        builder.add_code_cell(block.strip())
                else:
                    builder.add_markdown_cell(content)
            elif name == "ValidationAgent" and content.strip():
                builder.add_markdown_cell(f"## Validation\n\n{content}")

        # Save the notebook
        output_dir = Path(self.settings.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        safe_name = (company or "analysis").replace(" ", "_").lower()
        notebook_path = output_dir / f"{safe_name}_notebook.ipynb"
        builder.save(str(notebook_path))
        logger.info("Notebook saved to %s", notebook_path)

        # Return cell list for quality scoring
        nb_dict = builder.build()
        return nb_dict.get("cells", [])

    # ----------------------------------------------------------- persistence

    def _save_outputs(self) -> None:
        """Save all outputs to ``settings.output_dir``."""
        output_dir = Path(self.settings.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        company = (self.state.get("company") or "analysis").replace(" ", "_").lower()

        # Save dossier
        if "dossier" in self.state:
            path = output_dir / f"{company}_dossier.json"
            path.write_text(json.dumps(self.state["dossier"], indent=2, default=str), encoding="utf-8")
            logger.info("Dossier saved to %s", path)

        # Save analysis
        if "analysis" in self.state:
            path = output_dir / f"{company}_analysis.json"
            path.write_text(json.dumps(self.state["analysis"], indent=2, default=str), encoding="utf-8")
            logger.info("Analysis saved to %s", path)

        # Save blueprint
        if "blueprint" in self.state:
            path = output_dir / f"{company}_blueprint.json"
            path.write_text(json.dumps(self.state["blueprint"], indent=2, default=str), encoding="utf-8")
            logger.info("Blueprint saved to %s", path)

        # Summary
        scores = {
            k: v for k, v in self.state.items()
            if k.endswith("_score")
        }
        if scores:
            logger.info("Quality scores: %s", scores)

    # ------------------------------------------------------------- helpers

    @staticmethod
    def _build_dossier_from_messages(messages: list[dict], company: str | None) -> dict:
        """Fallback: assemble a dossier dict from raw conversation messages."""
        dossier: dict[str, Any] = {
            "company": company or "Unknown",
            "market_data": "",
            "news": "",
            "filings": "",
        }
        agent_section_map = {
            "CompanyLookupAgent": "company",
            "MarketDataAgent": "market_data",
            "NewsAgent": "news",
            "FilingsAgent": "filings",
        }
        for msg in messages:
            name = msg.get("name", "")
            content = msg.get("content", "") or ""
            if name in agent_section_map and content.strip():
                key = agent_section_map[name]
                if isinstance(dossier[key], str):
                    dossier[key] = content.strip()
                else:
                    dossier[key] = content.strip()
        return dossier

    @staticmethod
    def _summarise_messages(messages: list[dict], max_messages: int = 10) -> list[str]:
        """Return the last *max_messages* message contents as a list of strings."""
        tail = messages[-max_messages:]
        return [
            f"[{m.get('name', '?')}]: {(m.get('content', '') or '')[:500]}"
            for m in tail
        ]
