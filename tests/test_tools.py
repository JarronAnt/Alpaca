# tests/test_tools.py
"""Test tools."""

import pytest

from alpaca.exceptions import SecurityError
from alpaca.tools.filesystem import WriteFileTool
from alpaca.tools.registry import ToolRegistry, run_tool
from alpaca.tools.shell import ShellTool


class TestFilesystemTools:
    """Test filesystem tools."""
    
    def test_write_file_tool(self, tmp_path):
        tool = WriteFileTool()
        result = tool.execute(path=str(tmp_path / "test.txt"), content="hello")
        
        assert result.success
        assert "test.txt" in result.output


class TestShellTool:
    """Test shell tool."""
    
    def test_allowed_command(self):
        tool = ShellTool()
        result = tool.execute(command="python --version")
        
        # May fail if python not in path, but should not be security error
        assert not isinstance(result.error, str) or "not in allowed" not in result.error
    
    def test_blocked_command(self):
        tool = ShellTool()
        result = tool.execute(command="rm -rf /")
        
        assert not result.success
        assert "not in allowed" in result.error or "rm" in result.error


class TestRegistry:
    """Test tool registry."""
    
    def test_get_existing_tool(self):
        registry = ToolRegistry()
        tool = registry.get("write_file")
        
        assert tool is not None
        assert tool.name == "write_file"
    
    def test_get_missing_tool(self):
        registry = ToolRegistry()
        tool = registry.get("nonexistent")
        
        assert tool is None
    
    def test_execute_missing_tool(self):
        registry = ToolRegistry()
        result = registry.execute("nonexistent")
        
        assert not result.success
        assert "not found" in result.error
