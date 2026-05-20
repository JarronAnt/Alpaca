# src/alpaca/models.py
"""Pydantic models for Alpaca."""

from datetime import datetime
from enum import Enum, StrEnum
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AgentRole(StrEnum):
    """Agent roles in the system."""
    ROUTER = "router"      # THAG - decides if coding task
    PLANNER = "planner"    # OOGA - creates plan
    BUILDER = "builder"    # GROG - executes plan
    TESTER = "tester"      # BRAK - tests code
    REVIEWER = "reviewer"  # ROG - reviews code


class AgentStatus(StrEnum):
    """Agent execution statuses."""
    IDLE = "idle"
    RUNNING = "running"
    PLANNING = "planning"
    BUILDING = "building"
    TESTING = "testing"
    REVIEWING = "reviewing"
    SUCCESS = "success"
    FAILED = "failed"


class MessageRole(StrEnum):
    """Message roles for LLM conversations."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class Message(BaseModel):
    """A message in the conversation."""
    model_config = ConfigDict(frozen=True)
    
    role: MessageRole
    content: str
    name: str | None = None  # For tool messages
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for LLM API."""
        result: dict[str, Any] = {
            "role": self.role.value,
            "content": self.content,
        }
        if self.name:
            result["name"] = self.name
        return result


class ToolCall(BaseModel):
    """A tool call from an agent."""
    model_config = ConfigDict(frozen=True)
    
    name: str
    args: dict[str, Any] = Field(default_factory=dict)
    
    @field_validator("name")
    @classmethod
    def validate_tool_name(cls, v: str) -> str:
        """Validate tool name is not empty."""
        if not v.strip():
            raise ValueError("Tool name cannot be empty")
        return v.strip()


class ToolResult(BaseModel):
    """Result of a tool execution."""
    model_config = ConfigDict(frozen=True)
    
    success: bool
    output: str = ""
    error: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)


class PlanStep(BaseModel):
    """A single step in a plan."""
    model_config = ConfigDict(frozen=True)
    
    description: str
    order: int
    expected_files: list[str] = Field(default_factory=list)


class Plan(BaseModel):
    """A project plan."""
    model_config = ConfigDict(frozen=True)
    
    project_name: str
    steps: list[PlanStep]
    description: str = ""
    
    @field_validator("steps")
    @classmethod
    def validate_steps_not_empty(cls, v: list[PlanStep]) -> list[PlanStep]:
        """Ensure plan has at least one step."""
        if not v:
            raise ValueError("Plan must have at least one step")
        return v


class AgentState(BaseModel):
    """State of an agent."""
    model_config = ConfigDict(frozen=True)
    
    role: AgentRole
    status: AgentStatus
    current_task: str | None = None
    last_error: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    
    @property
    def duration_seconds(self) -> float | None:
        """Calculate execution duration."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


# src/alpaca/models.py - Fix the TaskResult class

class TaskResult(BaseModel):
    """Result of a task execution."""
    model_config = ConfigDict(frozen=True)
    
    success: bool
    output: str = ""
    error: str | None = None
    artifacts: list[str] = Field(default_factory=list)
    data: dict[str, Any] = Field(default_factory=dict)  # Changed from 'metrics' to 'data'

class TestResult(BaseModel):
    """Result of testing."""
    model_config = ConfigDict(frozen=True)
    
    success: bool
    test_count: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    stdout: str = ""
    stderr: str = ""
    coverage: float | None = None
