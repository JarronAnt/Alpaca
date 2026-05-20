# src/alpaca/agents/tester.py
"""BRAK - Tester agent that runs tests."""

import os
from pathlib import Path

from alpaca.agents.base import BaseAgent
from alpaca.config import Config
from alpaca.core.workspace import Workspace
from alpaca.models import AgentRole, AgentStatus, TaskResult, TestResult
from alpaca.tools.registry import run_tool


class TesterAgent(BaseAgent):
    """BRAK - The testing caveman."""
    
    role = AgentRole.TESTER
    model = Config.tester_model
    
    system_prompt = """You are Brak, the Testing Caveman.

Run tests and report results clearly."""
    
    def _find_project(self) -> Path | None:
        """Find the most recent project."""
        ws = Workspace()
        return ws.find_latest_project()
    
    def _has_tests(self, project_path: Path) -> bool:
        """Check if project has test files."""
        for root, _, files in os.walk(project_path):
            for f in files:
                if f.startswith("test_") and f.endswith(".py"):
                    return True
        return False
    
    def _find_entrypoint(self, project_path: Path) -> str | None:
        """Find main entry point."""
        candidates = ["main.py", "app.py", "run.py", "server.py"]
        for c in candidates:
            if (project_path / c).exists():
                return c
        return None
    
    def run(self) -> TaskResult:
        """Test the latest project."""
        self.update_state(AgentStatus.TESTING, task="testing project")
        
        project = self._find_project()
        if not project:
            self.update_state(AgentStatus.FAILED, error="No project found")
            return TaskResult(success=False, error="No project found")
        
        # Determine test mode
        if self._has_tests(project):
            # Run pytest
            result = run_tool("run_shell", {
                "command": "pytest -v",
                "cwd": str(project),
            })
        else:
            # Run the entrypoint
            entry = self._find_entrypoint(project)
            if not entry:
                self.update_state(AgentStatus.FAILED, error="No entrypoint found")
                return TaskResult(success=False, error="No entrypoint found")
            
            result = run_tool("run_shell", {
                "command": f"python {entry}",
                "cwd": str(project),
            })
        
        # Parse results
        success = result.success
        
        self.update_state(
            AgentStatus.SUCCESS if success else AgentStatus.FAILED,
            error=result.error if not success else None,
        )
        
        test_result = TestResult(
            success=success,
            stdout=result.output,
            stderr=result.error or "",
        )
        
        return TaskResult(
            success=success,
            output=result.output,
            error=result.error,
            data={"test_result": test_result.model_dump()},
        )
