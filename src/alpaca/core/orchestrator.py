# src/alpaca/core/orchestrator.py
"""Main orchestrator that coordinates agents."""

import difflib
from datetime import datetime
from pathlib import Path

from alpaca.agents import BuilderAgent, PlannerAgent, ReviewerAgent, RouterAgent, TesterAgent
from alpaca.config import Config
from alpaca.exceptions import AlpacaError
from alpaca.logger import console, get_logger
from alpaca.models import AgentState, AgentStatus, TaskResult
from alpaca.ui.dashboard import Dashboard
from rich.syntax import Syntax

logger = get_logger(__name__)


class AgentOrchestrator:
    """Orchestrates the multi-agent workflow."""
    
    def __init__(self):
        self.router = RouterAgent()
        self.planner = PlannerAgent()
        self.builder = BuilderAgent()
        self.tester = TesterAgent()
        self.reviewer = ReviewerAgent()
        
        self.dashboard = Dashboard()
        self.agents = {
            "THAG": self.router,
            "OOGA": self.planner,
            "GROG": self.builder,
            "BRAK": self.tester,
            "ROG": self.reviewer,
        }
        
    def get_states(self) -> dict[str, AgentState]:
        """Get current states of all agents."""
        return {
            name: agent.state
            for name, agent in self.agents.items()
        }
    
    def _update_dashboard(self) -> None:
        """Render current dashboard."""
        states = self.get_states()
        self.dashboard.render(states)
    
    def _snapshot_files(self, project_path: Path) -> dict[str, str]:
        """Snapshot all Python files for diff comparison."""
        snapshot = {}
        if not project_path.exists():
            return snapshot
            
        for py_file in project_path.glob("*.py"):
            # Skip temp files and hidden files
            if not py_file.name.startswith("_") and not py_file.name.startswith("."):
                try:
                    snapshot[py_file.name] = py_file.read_text()
                except Exception as e:
                    logger.warning(f"Could not read {py_file.name}: {e}")
        return snapshot
    
    def _show_diff(self, old_snapshot: dict, project_path: Path):
        """Show what changed between snapshots."""
        if not old_snapshot:
            return
            
        console.print("\n[bold cyan]📊 Changes Made by GROG:[/bold cyan]")
        has_changes = False
        
        # Check for modified files
        for filename, old_content in old_snapshot.items():
            file_path = project_path / filename
            if not file_path.exists():
                console.print(f"[red]🗑️  Deleted: {filename}[/red]")
                has_changes = True
                continue
            
            new_content = file_path.read_text()
            if old_content != new_content:
                has_changes = True
                console.print(f"\n[green]📝 Modified: {filename}[/green]")
                
                # Generate unified diff
                diff = difflib.unified_diff(
                    old_content.splitlines(keepends=True),
                    new_content.splitlines(keepends=True),
                    fromfile=f"{filename} (before)",
                    tofile=f"{filename} (after)",
                    lineterm=""
                )
                diff_lines = list(diff)
                
                if diff_lines:
                    diff_text = "".join(diff_lines)
                    # Show diff with syntax highlighting
                    syntax = Syntax(diff_text, "diff", theme="monokai", line_numbers=False)
                    console.print(syntax)
                else:
                    console.print("[dim]  (whitespace changes only)[/dim]")
            else:
                console.print(f"[dim]✓ Unchanged: {filename}[/dim]")
        
        # Check for new files
        if project_path.exists():
            for py_file in project_path.glob("*.py"):
                if not py_file.name.startswith("_") and py_file.name not in old_snapshot:
                    has_changes = True
                    console.print(f"\n[green]➕ Created: {py_file.name}[/green]")
                    try:
                        content = py_file.read_text()
                        # Show first 20 lines of new file
                        lines = content.splitlines()[:20]
                        preview = "\n".join(lines)
                        if len(content.splitlines()) > 20:
                            preview += "\n# ... (truncated)"
                        syntax = Syntax(preview, "python", theme="monokai")
                        console.print(syntax)
                    except Exception as e:
                        console.print(f"[red]Could not read new file: {e}[/red]")
        
        if not has_changes:
            console.print("[yellow]⚠️  No file changes detected[/yellow]")
        
        console.print("")  # Empty line after diff
    
    def run(self, user_input: str) -> TaskResult:
        """Run the full workflow."""
        logger.info("Starting workflow", input_preview=user_input[:50])
        
        try:
            # Step 1: Route
            self._update_dashboard()
            route_result = self.router.run(user_input)
            
            if not route_result.data.get("is_coding_task"):
                console.print(f"\n[dim]{route_result.output}[/dim]")
                return TaskResult(success=True, output=route_result.output)
            
            # Step 2: Plan
            self._update_dashboard()
            plan_result = self.planner.run(user_input)
            
            if not plan_result.success:
                console.print("[red]Planning failed[/red]")
                return plan_result
            
            plan = plan_result.data.get("plan")
            
            # Step 3: Build
            self._update_dashboard()
            build_result = self.builder.run(user_input, plan)
            
            if not build_result.success:
                console.print("[red]Build failed[/red]")
                if build_result.error:
                    console.print(f"[red]Error: {build_result.error}[/red]")
                return build_result
            
            # Step 4: Test with retry loop and diff tracking
            from alpaca.core.workspace import Workspace
            ws = Workspace()
            project_path = ws.find_latest_project()

            if not project_path:
                console.print("[red]No project found for testing[/red]")
                return TaskResult(success=False, error="No project found")
            
            
            max_test_retries = 3
            for attempt in range(max_test_retries):
                self._update_dashboard()
                test_result = self.tester.run()
                
                if test_result.success:
                    if attempt > 0:
                        console.print("[green]✓ Fix successful! Tests passing.[/green]")
                    break
                
                # Test failed - attempt fix with diff tracking
                console.print(f"[yellow]Tests failed (attempt {attempt+1}/{max_test_retries}), fixing...[/yellow]")
                
                # Snapshot before fix
                before_snapshot = self._snapshot_files(project_path)
                
                fix_result = self.builder.fix(test_result.error or "Tests failed")
                
                if not fix_result.success:
                    console.print("[red]Fix failed[/red]")
                    return fix_result
                
                # Show what changed
                self._show_diff(before_snapshot, project_path)
                
            else:
                # All retries exhausted
                console.print("[red]Tests failed after max retries[/red]")
                return TaskResult(success=False, error="Tests failed after 3 attempts")
            
            # Step 5: Review
            self._update_dashboard()
            review_result = self.reviewer.run(user_input, build_result.output)
            
            console.print(f"[dim]DEBUG: Reviewer returned: {review_result.success}[/dim]")
            self._update_dashboard()
            
            # Final summary
            console.print("\n[green]✓ Workflow complete![/green]")
            
            return TaskResult(
                success=True,
                output=build_result.output,
                data={
                    "plan": plan,
                    "test_result": test_result.data.get("test_result") if test_result.data else None,
                    "review": review_result.output,
                },
            )
            
        except AlpacaError as e:
            logger.error("Workflow failed", error=str(e))
            return TaskResult(success=False, error=str(e))
        except Exception as e:
            logger.exception("Unexpected error in workflow")
            return TaskResult(success=False, error=f"Unexpected error: {e}")
    
    def interactive(self) -> None:
        """Run interactive mode."""
        console.print("\n[bold green]🦙 Alpaca Multi-Agent System[/bold green]")
        console.print(f"[dim]Workspace: {Config.workspace_root}[/dim]")
        console.print("[dim]Type 'exit' or 'quit' to stop[/dim]\n")
        
        while True:
            try:
                user_input = console.input("[bold blue]You:[/bold blue] ").strip()
                
                if user_input.lower() in {"exit", "quit", "q"}:
                    console.print("[dim]Goodbye![/dim]")
                    break
                
                if not user_input:
                    continue
                
                self.run(user_input)
                console.print()  # Empty line between runs
                
            except KeyboardInterrupt:
                console.print("\n[dim]Interrupted. Type 'exit' to quit.[/dim]")
            except EOFError:
                break
