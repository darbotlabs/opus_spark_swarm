"""Tests for the analyst agent team."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


# We mock AG2 imports since they require network/model access.
@pytest.fixture(autouse=True)
def _mock_ag2():
    """Patch AG2 classes so analyst team can be created without a real LLM."""
    with patch("opus_spark_swarm.agents.base.ConversableAgent") as mock_ca, \
         patch("opus_spark_swarm.agents.analyst.GroupChat") as mock_gc, \
         patch("opus_spark_swarm.agents.analyst.GroupChatManager") as mock_gcm, \
         patch("opus_spark_swarm.agents.analyst.create_problem_framer") as mock_pf, \
         patch("opus_spark_swarm.agents.analyst.create_swot_agent") as mock_swot, \
         patch("opus_spark_swarm.agents.analyst.create_gap_analysis_agent") as mock_gap, \
         patch("opus_spark_swarm.agents.analyst.create_statement_writer") as mock_sw:

        # Each factory returns a mock with a .name attribute
        mock_pf.return_value = MagicMock(name="ProblemFramerAgent")
        mock_pf.return_value.name = "ProblemFramerAgent"
        mock_swot.return_value = MagicMock(name="SWOTAgent")
        mock_swot.return_value.name = "SWOTAgent"
        mock_gap.return_value = MagicMock(name="GapAnalysisAgent")
        mock_gap.return_value.name = "GapAnalysisAgent"
        mock_sw.return_value = MagicMock(name="StatementWriterAgent")
        mock_sw.return_value.name = "StatementWriterAgent"

        mock_gc_instance = MagicMock()
        mock_gc_instance.agents = [
            mock_pf.return_value, mock_swot.return_value,
            mock_gap.return_value, mock_sw.return_value,
        ]
        mock_gc.return_value = mock_gc_instance
        mock_gcm.return_value = MagicMock()

        yield {
            "ConversableAgent": mock_ca,
            "GroupChat": mock_gc,
            "GroupChatManager": mock_gcm,
            "problem_framer": mock_pf,
            "swot": mock_swot,
            "gap": mock_gap,
            "statement_writer": mock_sw,
        }


class TestCreateAnalystTeam:
    def test_returns_tuple(self, settings):
        from opus_spark_swarm.agents.analyst import create_analyst_team
        result = create_analyst_team(settings)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_group_chat_created(self, settings):
        from opus_spark_swarm.agents.analyst import create_analyst_team
        gc, manager = create_analyst_team(settings)
        assert gc is not None
        assert manager is not None

    def test_four_agents_created(self, settings):
        from opus_spark_swarm.agents.analyst import create_analyst_team
        gc, _ = create_analyst_team(settings)
        assert len(gc.agents) == 4

    def test_agent_names(self, settings):
        from opus_spark_swarm.agents.analyst import create_analyst_team
        gc, _ = create_analyst_team(settings)
        names = [a.name for a in gc.agents]
        assert "ProblemFramerAgent" in names
        assert "SWOTAgent" in names
        assert "GapAnalysisAgent" in names
        assert "StatementWriterAgent" in names

    def test_custom_max_round(self, settings):
        from opus_spark_swarm.agents.analyst import create_analyst_team
        from opus_spark_swarm.agents.analyst import GroupChat
        create_analyst_team(settings, max_round=20)
        call_kwargs = GroupChat.call_args[1]
        assert call_kwargs["max_round"] == 20
