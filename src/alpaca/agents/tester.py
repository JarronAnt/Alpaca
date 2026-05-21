# src/alpaca/agents/tester.py
"""BRAK - Tester agent that runs tests."""

import os
import re
import shutil
from pathlib import Path

from alpaca.agents.base import BaseAgent
from alpaca.config import Config
from alpaca.core.workspace import Workspace
from alpaca.logger import console
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
        
        # Fallback: find any .py file (except test files)
        py_files = [f for f in project_path.glob("*.py") 
                    if not f.name.startswith("test_")]
        if len(py_files) == 1:
            return py_files[0].name
        elif len(py_files) > 1:
            # Pick the largest file (likely the main one)
            return max(py_files, key=lambda f: f.stat().st_size).name
        
        return None
    
    def _get_python_cmd(self) -> str:
        """Find the correct Python command."""
        if shutil.which("python3"):
            return "python3"
        elif shutil.which("python"):
            return "python"
        else:
            return "python3"
    
    def _detect_cli_app(self, entry_path: Path) -> tuple[bool, list[str]]:
        """Detect if app needs CLI args and return appropriate test args."""
        if not entry_path.exists():
            return False, []
        
        content = entry_path.read_text()
        
        # Check for argparse
        if "argparse" in content:
            if "add_argument" in content:
                test_args = []
                
                # Look for argument patterns
                if "nargs" in content or "num" in content.lower():
                    test_args = ["5", "3"]
                
                # Check for operation/subcommand patterns
                if any(op in content for op in ["add", "subtract", "multiply", "divide"]):
                    test_args = ["--help"]
                elif any(op in content for op in ["create", "delete", "update", "list"]):
                    test_args = ["create", "test-item"]
                elif len(test_args) == 0:
                    test_args = ["--help"]
                
                return True, test_args
        
        # Check for sys.argv usage
        if "sys.argv" in content:
            argv_count = content.count("sys.argv")
            if argv_count > 1:
                return True, ["arg1", "arg2", "arg3"]
        
        return False, []
    
    def _has_relative_imports(self, content: str) -> bool:
        """Check if code uses relative imports."""
        return bool(re.search(r'from\s+\.', content) or re.search(r'import\s+\.', content))
    
    def _fix_relative_imports(self, content: str) -> str:
        """Convert relative imports to absolute imports."""
        # Pattern: from .module import something -> from module import something
        content = re.sub(r'from\s+\.([a-zA-Z_][a-zA-Z0-9_]*)', r'from \1', content)
        # Pattern: from . import module -> import module (keep as relative, will work)
        content = re.sub(r'from\s+\.\s+import', r'import', content)
        return content
    
    def _prepare_entrypoint(self, project: Path, entry: str) -> tuple[Path, bool]:
        """
        Prepare entrypoint for execution.
        Returns (path_to_run, is_temp_file).
        """
        entry_path = project / entry
        content = entry_path.read_text()
        
        # Check for relative imports
        if self._has_relative_imports(content):
            console.print(f"[dim][BRAK] 🔄 Converting relative imports to absolute...[/dim]")
            
            # Fix the imports
            fixed_content = self._fix_relative_imports(content)
            
            # Write to temp file in project directory
            temp_path = project / f"_brak_fixed_{entry}"
            temp_path.write_text(fixed_content)
            
            return temp_path, True
        
        return entry_path, False
    
    def _build_run_command(self, entry: str, is_cli: bool, test_args: list[str]) -> str:
        """Build the Python command - runs file directly, no exec()."""
        python_cmd = self._get_python_cmd()
        
        if is_cli and test_args:
            # CLI app: run with args
            args_str = " ".join(test_args)
            return f"{python_cmd} {entry} {args_str}"
        else:
            # Simple script: just run it
            return f"{python_cmd} {entry}"
    
    def run(self) -> TaskResult:
        """Test the latest project."""
        self.update_state(AgentStatus.TESTING, task="testing project")
        
        project = self._find_project()
        if not project:
            self.update_state(AgentStatus.FAILED, error="No project found")
            return TaskResult(success=False, error="No project found")
        
        # Debug: Show what we found
        console.print(f"[dim][BRAK] 📁 Project: {project}[/dim]")
        py_files = list(project.glob("*.py"))
        console.print(f"[dim][BRAK] 🐍 Found {len(py_files)} Python files: {[f.name for f in py_files]}[/dim]")
        
        temp_file = None
        
        try:
            # Determine test mode
            if self._has_tests(project):
                console.print("[dim][BRAK] 🧪 Running pytest...[/dim]")
                result = run_tool("run_shell", {
                    "command": "python3 -m pytest -v 2>&1",
                    "cwd": str(project),
                })
            else:
                # Run the entrypoint
                entry = self._find_entrypoint(project)
                if not entry:
                    self.update_state(AgentStatus.FAILED, error="No entrypoint found")
                    return TaskResult(success=False, error="No entrypoint found")
                
                entry_path = project / entry
                
                # Prepare entrypoint (fix relative imports if needed)
                run_path, is_temp = self._prepare_entrypoint(project, entry)
                if is_temp:
                    temp_file = run_path
                    console.print(f"[dim][BRAK] 📝 Using fixed entrypoint: {run_path.name}[/dim]")
                
                # Detect if CLI app and get test args
                is_cli, test_args = self._detect_cli_app(entry_path)
                
                if is_cli:
                    console.print(f"[dim][BRAK] 🎮 CLI app detected, using test args: {test_args}[/dim]")
                else:
                    console.print(f"[dim][BRAK] ▶️  Running: {entry}[/dim]")
                
                # Build command - runs file directly, no exec()
                cmd = self._build_run_command(run_path.name, is_cli, test_args)
                
                console.print(f"[dim][BRAK] 🔧 Command: {cmd}[/dim]")
                
                # Run from project directory so imports work
                result = run_tool("run_shell", {
                    "command": cmd,
                    "cwd": str(project),
                })
                
                # Debug output
                if not result.success:
                    console.print(f"[red][BRAK] ❌ Failed[/red]")
                    if result.output:
                        console.print(f"[red]stdout: {result.output[:300]}[/red]")
                    if result.error:
                        console.print(f"[red]stderr: {result.error[:300]}[/red]")
                else:
                    console.print(f"[green][BRAK] ✅ Success![/green]")
                    if result.output:
                        console.print(f"[dim]Output: {result.output[:200]}...[/dim]")
        
        finally:
            # Cleanup temp file
            if temp_file and temp_file.exists():
                temp_file.unlink()
                console.print(f"[dim][BRAK] 🗑️  Cleaned up temp file[/dim]")
        
        # Parse results
        success = result.success
        
        self.update_state(
            AgentStatus.SUCCESS if success else AgentStatus.FAILED,
            error=result.error if not success else None,
        )
        
        test_result = TestResult(
            success=success,
            stdout=result.output or "",
            stderr=result.error or "",
        )
        
        return TaskResult(
            success=success,
            output=result.output,
            error=result.error,
            data={"test_result": test_result.model_dump()},
        )
