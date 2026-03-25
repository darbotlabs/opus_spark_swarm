"""CLI entry point for Opus Spark Swarm."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.table import Table

console = Console()

BANNER = r"""
  ___                    ____                  _      ____
 / _ \ _ __  _   _ ___  / ___| _ __   __ _ _ __| | __ / ___|_      ____ _ _ __ _ __ ___
| | | | '_ \| | | / __| \___ \| '_ \ / _` | '__| |/ / \___ \ \ /\ / / _` | '__| '_ ` _ \
| |_| | |_) | |_| \__ \  ___) | |_) | (_| | |  |   <   ___) \ V  V / (_| | |  | | | | | |
 \___/| .__/ \__,_|___/ |____/| .__/ \__,_|_|  |_|\_\ |____/ \_/\_/ \__,_|_|  |_| |_| |_|
      |_|                     |_|
"""


def _setup_logging(verbose: bool = False) -> None:
    """Configure logging with Rich handler."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True)],
    )


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging.")
def cli(verbose: bool) -> None:
    """Opus Spark Swarm -- Claude Opus 4.6 powered AG2 agent swarm."""
    _setup_logging(verbose)


@cli.command()
@click.option("--company", "-c", default=None, help="Company name to analyse.")
@click.option("--prompt", "-p", default=None, help="Custom business problem prompt.")
@click.option("--documents", "-d", type=click.Path(exists=True, path_type=Path), default=None, help="Path to documents for additional context.")
@click.option("--phase", type=click.Choice(["research", "analyst", "architect", "notebook"]), default=None, help="Run a single pipeline phase.")
@click.option("--output-dir", "-o", type=click.Path(path_type=Path), default=None, help="Override output directory.")
def run(
    company: Optional[str],
    prompt: Optional[str],
    documents: Optional[Path],
    phase: Optional[str],
    output_dir: Optional[Path],
) -> None:
    """Run the full analysis pipeline (or a single phase)."""
    _print_banner()

    if not company and not prompt:
        raise click.UsageError("Provide --company or --prompt (or both).")

    from opus_spark_swarm.config import get_settings

    settings = get_settings()
    if output_dir:
        settings.output_dir = output_dir

    console.print(f"[bold green]Company:[/] {company or 'N/A'}")
    console.print(f"[bold green]Prompt:[/]  {prompt or 'N/A'}")
    console.print(f"[bold green]Phase:[/]   {phase or 'full pipeline'}")
    console.print(f"[bold green]Output:[/]  {settings.output_dir}")
    console.print()

    try:
        from opus_spark_swarm.orchestrator import Pipeline
    except ImportError:
        console.print(
            "[bold red]Error:[/] AG2 (autogen) is not installed.\n"
            "Install it with: [cyan]pip install 'ag2\\[anthropic]'[/]"
        )
        raise SystemExit(1)

    pipeline = Pipeline(settings)
    doc_list = [str(documents)] if documents else None

    with console.status("[bold blue]Running pipeline…[/]"):
        try:
            result = asyncio.run(
                pipeline.run(company=company, prompt=prompt, documents=doc_list, phase=phase)
            )
        except RuntimeError as exc:
            console.print(f"[bold red]Pipeline error:[/] {exc}")
            raise SystemExit(1)

    _print_results(result)


@cli.command()
@click.option("--company", "-c", required=True, help="Company name for problem suggestions.")
def suggest(company: str) -> None:
    """Generate ranked business problem suggestions for a company."""
    _print_banner()

    from opus_spark_swarm.config import get_settings

    settings = get_settings()

    console.print(f"[bold green]Generating problem suggestions for:[/] {company}")
    console.print()

    try:
        from opus_spark_swarm.orchestrator import Pipeline
    except ImportError:
        console.print(
            "[bold red]Error:[/] AG2 (autogen) is not installed.\n"
            "Install it with: [cyan]pip install 'ag2\\[anthropic]'[/]"
        )
        raise SystemExit(1)

    pipeline = Pipeline(settings)

    with console.status("[bold blue]Researching and analysing…[/]"):
        try:
            statements = asyncio.run(pipeline.suggest(company))
        except RuntimeError as exc:
            console.print(f"[bold red]Pipeline error:[/] {exc}")
            raise SystemExit(1)

    if not statements:
        console.print("[yellow]No problem statements generated.[/]")
        return

    table = Table(title=f"Problem Suggestions for {company}", show_lines=True)
    table.add_column("#", style="bold", width=3)
    table.add_column("Title", style="cyan")
    table.add_column("Impact", style="yellow")
    table.add_column("Priority", style="green")

    for i, stmt in enumerate(statements, 1):
        if isinstance(stmt, dict):
            table.add_row(
                str(i),
                stmt.get("title", "N/A"),
                stmt.get("impact", "N/A"),
                stmt.get("priority", "N/A"),
            )
        else:
            table.add_row(str(i), str(stmt), "", "")

    console.print(table)


def _print_results(result: dict) -> None:
    """Display pipeline results using Rich."""
    console.print()

    # Quality scores
    scores_table = Table(title="Quality Gate Scores")
    scores_table.add_column("Phase", style="cyan")
    scores_table.add_column("Score", style="bold")
    scores_table.add_column("Status", style="bold")

    score_keys = [
        ("research_score", "Research"),
        ("analysis_score", "Analysis"),
        ("architecture_score", "Architecture"),
        ("notebook_score", "Notebook"),
    ]
    for key, label in score_keys:
        if key in result:
            score = result[key]
            status = "[green]PASS[/]" if score >= 0.8 else "[red]BELOW THRESHOLD[/]"
            scores_table.add_row(label, f"{score:.2f}", status)

    console.print(scores_table)

    # Problem statements summary
    analysis = result.get("analysis", {})
    statements = analysis.get("problem_statements", [])
    if statements:
        console.print()
        ps_table = Table(title="Problem Statements", show_lines=True)
        ps_table.add_column("#", width=3)
        ps_table.add_column("Title", style="cyan")
        ps_table.add_column("Priority", style="green")
        for i, stmt in enumerate(statements, 1):
            if isinstance(stmt, dict):
                ps_table.add_row(str(i), stmt.get("title", ""), stmt.get("priority", ""))
            else:
                ps_table.add_row(str(i), str(stmt), "")
        console.print(ps_table)

    # Output location
    if "company" in result:
        console.print()
        console.print(f"[bold green]Outputs saved to:[/] {result.get('company', 'output')}")

    console.print(Panel("[bold green]Pipeline complete![/]", border_style="green"))


def _print_banner() -> None:
    """Display the Opus Spark Swarm banner."""
    console.print(Panel(BANNER, title="[bold magenta]Opus Spark Swarm[/]", subtitle="Claude Opus 4.6 · AG2 · GitHub Spark", border_style="bright_blue"))
