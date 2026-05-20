# src/alpaca/core/parser.py
"""Tool call and plan parsing."""

import json
import re
from typing import Any

from alpaca.exceptions import ParseError
from alpaca.logger import get_logger
from alpaca.models import Plan, PlanStep, ToolCall

logger = get_logger(__name__)


class ToolParser:
    """Parse tool calls from LLM output."""
    
    TOOL_PATTERN = re.compile(
        r'<tool\s+name="([^"]+)">\s*(.*?)\s*</tool>',
        re.DOTALL | re.IGNORECASE,
    )
    
    @classmethod
    def parse(cls, text: str) -> list[ToolCall]:
        """Extract tool calls from text with robust JSON handling."""
        if not text:
            return []
            
        matches = cls.TOOL_PATTERN.finditer(text)
        tools = []
        
        for match in matches:
            name = match.group(1).strip()
            raw_args = match.group(2).strip()
            
            args = {}
            if raw_args:
                # Try multiple parsing strategies
                try:
                    # First try strict JSON
                    args = json.loads(raw_args)
                except json.JSONDecodeError:
                    try:
                        # Try with strict=False to allow control characters
                        args = json.loads(raw_args, strict=False)
                    except json.JSONDecodeError:
                        try:
                            # Try fixing common escape issues
                            # Replace literal newlines/tabs with escaped versions
                            fixed = raw_args.replace('\n', '\\n').replace('\t', '\\t').replace('\r', '\\r')
                            args = json.loads(fixed)
                        except json.JSONDecodeError as e:
                            logger.warning(
                                "Failed to parse tool args as JSON, using empty dict",
                                tool_name=name,
                                raw_preview=raw_args[:100],
                                error=str(e),
                            )
                            args = {}
                
            tools.append(ToolCall(name=name, args=args))
            
        return tools
    
    @classmethod
    def has_tool_calls(cls, text: str) -> bool:
        """Check if text contains tool calls."""
        return bool(cls.TOOL_PATTERN.search(text))


class PlanParser:
    """Parse plans from LLM output."""
    
    PLAN_PATTERN = re.compile(
        r'<plan>(.*?)</plan>',
        re.DOTALL | re.IGNORECASE,
    )
    
    @classmethod
    def parse(cls, text: str) -> Plan | None:
        """Extract plan from text."""
        if not text:
            return None
            
        match = cls.PLAN_PATTERN.search(text)
        if not match:
            logger.warning("No plan tags found in text")
            return None
            
        block = match.group(1)
        lines = [l.strip() for l in block.split('\n') if l.strip()]
        
        project_name = "project"
        steps = []
        description_lines = []
        
        for line in lines:
            if line.lower().startswith('project:'):
                project_name = line.split(':', 1)[1].strip()
            elif line.lower().startswith('step:'):
                step_desc = line.split(':', 1)[1].strip()
                steps.append(PlanStep(description=step_desc, order=len(steps)))
            else:
                description_lines.append(line)
                
        if not steps:
            logger.warning("No steps found in plan")
            return None
            
        return Plan(
            project_name=project_name,
            steps=steps,
            description='\n'.join(description_lines),
        )
