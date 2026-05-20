# src/alpaca/tools/registry.py
"""Tool registry for managing available tools."""

from typing import Any

from alpaca.logger import get_logger
from alpaca.models import ToolResult
from alpaca.tools.base import BaseTool
from alpaca.tools.filesystem import (
    CreateDirectoryTool,
    DeleteFileTool,
    FileExistsTool,
    ListFilesTool,
    ReadFileTool,
    WalkDirectoryTool,
    WriteFileTool,
)
from alpaca.tools.shell import ShellTool

logger = get_logger(__name__)


class ToolRegistry:
    """Registry of available tools."""
    
    def __init__(self):
        self._tools: dict[str, BaseTool] = {}
        self._register_defaults()
        
    def _register_defaults(self) -> None:
        """Register default tools."""
        tools = [
            CreateDirectoryTool(),
            WriteFileTool(),
            ReadFileTool(),
            ListFilesTool(),
            WalkDirectoryTool(),
            FileExistsTool(),
            DeleteFileTool(),
            ShellTool(),
        ]
        for tool in tools:
            self.register(tool)
    
    def register(self, tool: BaseTool) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool
        logger.debug("Registered tool", name=tool.name)
        
    def get(self, name: str) -> BaseTool | None:
        """Get a tool by name."""
        return self._tools.get(name)
        
    def list_tools(self) -> list[str]:
        """List all registered tool names."""
        return list(self._tools.keys())
        
    def execute(self, name: str, args: dict[str, Any] | None = None) -> ToolResult:
        """Execute a tool by name."""
        tool = self.get(name)
        if not tool:
            return ToolResult(
                success=False,
                error=f"Tool '{name}' not found. Available: {self.list_tools()}",
            )
        
        try:
            return tool.execute(**(args or {}))
        except Exception as e:
            logger.error("Tool execution failed", tool=name, error=str(e))
            return ToolResult(success=False, error=str(e))
    
    def get_schemas(self) -> list[dict]:
        """Get schemas for all tools."""
        return [tool.get_schema() for tool in self._tools.values()]


# Global registry
_registry: ToolRegistry | None = None


def get_registry() -> ToolRegistry:
    """Get or create tool registry singleton."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry


def run_tool(name: str, args: dict[str, Any] | None = None) -> ToolResult:
    """Convenience function to run a tool."""
    return get_registry().execute(name, args)
