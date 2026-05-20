# tests/test_parser.py
"""Test parsers."""

import pytest

from alpaca.core.parser import PlanParser, ToolParser
from alpaca.models import Plan, ToolCall


class TestToolParser:
    """Test tool parser."""
    
    def test_parse_single_tool(self):
        text = '<tool name="write_file">{"path": "test.py", "content": "print(1)"}</tool>'
        result = ToolParser.parse(text)
        
        assert len(result) == 1
        assert result[0].name == "write_file"
        assert result[0].args == {"path": "test.py", "content": "print(1)"}
    
    def test_parse_multiple_tools(self):
        text = '''
        <tool name="create_directory">{"path": "src"}</tool>
        <tool name="write_file">{"path": "src/main.py", "content": "pass"}</tool>
        '''
        result = ToolParser.parse(text)
        
        assert len(result) == 2
        assert result[0].name == "create_directory"
        assert result[1].name == "write_file"
    
    def test_parse_no_tools(self):
        result = ToolParser.parse("No tools here")
        assert result == []
    
    def test_parse_invalid_json(self):
        text = '<tool name="test">{invalid json}</tool>'
        result = ToolParser.parse(text)
        
        assert len(result) == 1
        assert result[0].args == {}  # Falls back to empty dict


class TestPlanParser:
    """Test plan parser."""
    
    def test_parse_valid_plan(self):
        text = '''
        <plan>
        project: myapp
        step: Create main.py
        step: Add functions
        </plan>
        '''
        result = PlanParser.parse(text)
        
        assert result is not None
        assert result.project_name == "myapp"
        assert len(result.steps) == 2
        assert result.steps[0].description == "Create main.py"
    
    def test_parse_no_plan(self):
        result = PlanParser.parse("No plan here")
        assert result is None
    
    def test_parse_no_steps(self):
        text = '''
        <plan>
        project: empty
        </plan>
        '''
        result = PlanParser.parse(text)
        assert result is None
