# src/alpaca/tools/base.py
"""Base tool interface."""

from abc import ABC, abstractmethod
from typing import Any

from alpaca.models import ToolResult


class BaseTool(ABC):
    """Base class for all tools."""
    
    name: str
    description: str
    
    @abstractmethod
    def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the tool."""
        pass
    
    def get_schema(self) -> dict[str, Any]:
        """Get JSON schema for the tool."""
        return {
            "name": self.name,
            "description": self.description,
        }
