# src/alpaca/agents/planner.py
"""OOGA - Planner agent that creates project plans."""

from alpaca.agents.base import BaseAgent
from alpaca.config import Config
from alpaca.core.parser import PlanParser
from alpaca.models import AgentRole, AgentStatus, Plan, TaskResult


class PlannerAgent(BaseAgent):
    """OOGA - The planning caveman."""
    
    role = AgentRole.PLANNER
    model = Config.planner_model
    
    system_prompt = """You are Ooga, the Planning Caveman.

Create structured plans for coding projects.

Output format:
<plan>
project: project_name
step: First step description
step: Second step description
step: Third step description
</plan>

Rules:
- Use relative paths only
- Steps should be actionable and specific
- Include setup, implementation, and verification steps
- Keep steps under 20 words each
"""
    
    def run(self, user_input: str) -> TaskResult:
        """Create a plan for the task."""
        self.update_state(AgentStatus.PLANNING, task="creating plan")
        
        self.memory.add_user(user_input)
        response = self.call_llm(temperature=0.5)
        self.memory.add_assistant(response)
        
        plan = PlanParser.parse(response)
        
        if plan:
            self.update_state(AgentStatus.SUCCESS)
            return TaskResult(
                success=True,
                output=response,
                data={"plan": plan.model_dump()},
            )
        else:
            self.update_state(AgentStatus.FAILED, error="Failed to parse plan")
            return TaskResult(
                success=False,
                output=response,
                error="Failed to create valid plan",
            )
