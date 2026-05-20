# src/alpaca/agents/base.py
"""Base agent class."""

from abc import ABC, abstractmethod
from typing import Any

from alpaca.config import Config
from alpaca.core.llm import call_llm
from alpaca.core.memory import ConversationMemory
from alpaca.logger import get_logger
from alpaca.models import AgentRole, AgentState, AgentStatus, Message, TaskResult

logger = get_logger(__name__)


class BaseAgent(ABC):
    """Base class for all agents."""
    
    role: AgentRole
    model: str
    system_prompt: str
    
    def __init__(self):
        self.memory = ConversationMemory()
        self.memory.set_system(self.system_prompt)
        self.state = AgentState(
            role=self.role,
            status=AgentStatus.IDLE,
        )
        self.logger = get_logger(f"alpaca.agents.{self.role.value}")
        
    def update_state(
        self,
        status: AgentStatus,
        task: str | None = None,
        error: str | None = None,
    ) -> None:
        """Update agent state."""
        from datetime import datetime
        
        now = datetime.utcnow()
        
        if status == AgentStatus.RUNNING and self.state.status != AgentStatus.RUNNING:
            self.state = AgentState(
                role=self.role,
                status=status,
                current_task=task,
                start_time=now,
            )
        else:
            self.state = AgentState(
                role=self.role,
                status=status,
                current_task=task or self.state.current_task,
                last_error=error,
                start_time=self.state.start_time,
                end_time=now if status in (AgentStatus.SUCCESS, AgentStatus.FAILED) else None,
            )
            
        self.logger.info(
            "State updated",
            status=status.value,
            task=task,
        )
    
    def call_llm(self, temperature: float = 0.7) -> str:
        """Call LLM with current memory."""
        messages = self.memory.get_messages()
        return call_llm(self.model, messages, temperature)
    
    @abstractmethod
    def run(self, *args: Any, **kwargs: Any) -> TaskResult:
        """Execute the agent's task."""
        pass
    
    def reset(self) -> None:
        """Reset agent state and memory."""
        self.memory.clear()
        self.memory.set_system(self.system_prompt)
        self.state = AgentState(role=self.role, status=AgentStatus.IDLE)
