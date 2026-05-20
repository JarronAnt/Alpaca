# src/alpaca/agents/reviewer.py
"""ROG - Reviewer agent that reviews code."""

from alpaca.agents.base import BaseAgent
from alpaca.config import Config
from alpaca.models import AgentRole, AgentStatus, TaskResult


class ReviewerAgent(BaseAgent):
    """ROG - The reviewing caveman."""
    
    role = AgentRole.REVIEWER
    model = Config.reviewer_model
    
    system_prompt = """You are Rog, the Skeptical Caveman Reviewer.

Review code for:
- Bugs and logic errors
- Security issues
- Edge cases
- Code quality
- Performance problems

Provide constructive feedback.
Be thorough but concise.
"""
    
    def run(self, user_input: str, build_output: str) -> TaskResult:
        """Review the build output."""
        self.update_state(AgentStatus.REVIEWING, task="reviewing code")
        
        review_prompt = f"""Review this code:

USER REQUEST:
{user_input}

BUILD OUTPUT:
{build_output}

Provide your review focusing on bugs, security, edge cases, and quality."""
        
        self.memory.add_user(review_prompt)
        response = self.call_llm(temperature=0.3)
        self.memory.add_assistant(response)
        
        self.update_state(AgentStatus.SUCCESS)
        
        return TaskResult(
            success=True,
            output=response,
            data={"review": response},
        )
