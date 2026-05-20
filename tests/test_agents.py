# tests/test_agents.py
"""Test agents."""

from unittest.mock import MagicMock, patch

import pytest

from alpaca.agents.builder import BuilderAgent
from alpaca.agents.planner import PlannerAgent
from alpaca.agents.router import RouterAgent
from alpaca.models import AgentStatus


class TestRouterAgent:
    """Test router agent."""
    
    def test_is_coding_task_with_keywords(self):
        agent = RouterAgent()
        assert agent.is_coding_task("Create a python script")
        assert agent.is_coding_task("Fix the bug")
        assert not agent.is_coding_task("Hello there")
    
    @patch("alpaca.agents.router.call_llm")
    def test_run_coding_task(self, mock_call):
        mock_call.return_value = "CODE_TASK"
        agent = RouterAgent()
        
        result = agent.run("Create a python app")
        
        assert result.success
        assert result.data["is_coding_task"] is True
        assert agent.state.status == AgentStatus.SUCCESS


class TestPlannerAgent:
    """Test planner agent."""
    
    @patch("alpaca.agents.planner.call_llm")
    def test_run_creates_plan(self, mock_call):
        mock_call.return_value = '''
        <plan>
        project: test
        step: Create file
        step: Add code
        </plan>
        '''
        agent = PlannerAgent()
        
        result = agent.run("Create a test project")
        
        assert result.success
        assert "plan" in result.data
