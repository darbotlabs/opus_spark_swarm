"""Analyst agent team -- problem identification and statement generation."""

from __future__ import annotations

from autogen import ConversableAgent, GroupChat, GroupChatManager

from opus_spark_swarm.agents.base import build_llm_config
from opus_spark_swarm.config import Settings

from .gap_analysis import create_gap_analysis_agent
from .problem_framer import create_problem_framer
from .statement_writer import create_statement_writer
from .swot import create_swot_agent

__all__ = [
    "create_analyst_team",
    "create_gap_analysis_agent",
    "create_problem_framer",
    "create_statement_writer",
    "create_swot_agent",
]


def create_analyst_team(
    settings: Settings,
    *,
    max_round: int = 12,
) -> tuple[GroupChat, GroupChatManager]:
    """Create the full Analyst Agent Team as an AG2 GroupChat.

    The team consists of four agents that collaborate sequentially:

    1. **ProblemFramerAgent** -- scans the Company Intelligence Dossier and
       identifies candidate problem domains.
    2. **SWOTAgent** -- performs a SWOT analysis grounded in dossier data and
       the framed problems.
    3. **GapAnalysisAgent** -- compares current state against benchmarks to
       quantify gaps.
    4. **StatementWriterAgent** -- synthesises all prior outputs into 3-5
       formal business problem statements.

    Parameters
    ----------
    settings:
        Application :class:`Settings` instance (provides API keys and model
        configuration).
    max_round:
        Maximum number of group-chat rounds before the conversation is
        terminated.  Default ``12`` allows each agent ~3 turns.

    Returns
    -------
    tuple[GroupChat, GroupChatManager]
        The configured :class:`GroupChat` and its managing
        :class:`GroupChatManager`.  The caller kicks off the conversation by
        sending the Company Intelligence Dossier as the initial message.
    """
    problem_framer = create_problem_framer(settings)
    swot_agent = create_swot_agent(settings)
    gap_agent = create_gap_analysis_agent(settings)
    statement_writer = create_statement_writer(settings)

    agents: list[ConversableAgent] = [
        problem_framer,
        swot_agent,
        gap_agent,
        statement_writer,
    ]

    group_chat = GroupChat(
        agents=agents,
        messages=[],
        max_round=max_round,
        speaker_selection_method="auto",
    )

    manager = GroupChatManager(
        groupchat=group_chat,
        llm_config=build_llm_config(settings),
    )

    return group_chat, manager
