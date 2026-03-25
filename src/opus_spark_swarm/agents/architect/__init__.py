"""Solution architect agent team -- design through structured debate.

Exposes :func:`create_architect_team` which wires up the four architect agents
inside an AG2 :class:`GroupChat` with a deterministic
**propose → critique → feasibility → refinement** speaker rotation.
"""

from __future__ import annotations

from typing import List

from autogen import ConversableAgent, GroupChat

from opus_spark_swarm.config import Settings

from .critic import create_critic_agent
from .feasibility import create_feasibility_agent
from .proposal import create_proposal_agent
from .refinement import SOLUTION_APPROVED, create_refinement_agent

__all__ = [
    "create_architect_team",
    "create_proposal_agent",
    "create_critic_agent",
    "create_feasibility_agent",
    "create_refinement_agent",
    "SOLUTION_APPROVED",
]

# Fixed agent ordering for the debate loop.
_AGENT_ORDER = ["ProposalAgent", "CriticAgent", "FeasibilityAgent", "RefinementAgent"]


def _speaker_selection(
    last_speaker: ConversableAgent,
    groupchat: GroupChat,
) -> ConversableAgent:
    """Enforce a deterministic propose → critique → feasibility → refinement rotation.

    After the RefinementAgent speaks the cycle restarts with ProposalAgent so that
    the debate can continue for another round (unless the termination condition
    fires first).
    """
    agent_map = {a.name: a for a in groupchat.agents}
    try:
        idx = _AGENT_ORDER.index(last_speaker.name)
    except ValueError:
        # If the last speaker is not in our rotation (e.g. manager), start fresh.
        return agent_map[_AGENT_ORDER[0]]
    next_idx = (idx + 1) % len(_AGENT_ORDER)
    return agent_map[_AGENT_ORDER[next_idx]]


def _is_termination_msg(message: dict) -> bool:
    """Return *True* when the RefinementAgent approves the solution."""
    content: str = message.get("content", "") or ""
    return SOLUTION_APPROVED in content


def create_architect_team(
    settings: Settings,
    max_rounds: int | None = None,
) -> GroupChat:
    """Create architect team with propose-critique-refine debate loop.

    Uses AG2 GroupChat with a custom *speaker_selection_method* to enforce::

        proposal → critic → feasibility → refinement → (repeat or terminate)

    Parameters
    ----------
    settings:
        Application :class:`Settings` instance used to configure LLM access.
    max_rounds:
        Maximum number of individual agent turns.  Defaults to
        ``settings.max_refinement_rounds * 4`` (four agents per logical round).

    Returns
    -------
    GroupChat
        A fully-configured AG2 :class:`GroupChat` ready to be wrapped in a
        :class:`GroupChatManager`.
    """
    if max_rounds is None:
        max_rounds = settings.max_refinement_rounds * 4

    agents: List[ConversableAgent] = [
        create_proposal_agent(settings),
        create_critic_agent(settings),
        create_feasibility_agent(settings),
        create_refinement_agent(settings),
    ]

    return GroupChat(
        agents=agents,
        messages=[],
        max_round=max_rounds,
        speaker_selection_method=_speaker_selection,
    )
