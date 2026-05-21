# src/alpaca/core/orchestrator.py
"""Main orchestrator that coordinates agents."""

from datetime import datetime

from alpaca.agents import BuilderAgent, PlannerAgent, ReviewerAgent, RouterAgent, TesterAgent
from alpaca.config import Config
from alpaca.exceptions import AlpacaError
from alpaca.logger import console, get_logger
from alpaca.models import AgentState, AgentStatus, TaskResult
from alpaca.ui.dashboard import Dashboard

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
            
            # Step 4: Test
           # In orchestrator.py, replace the test section with:

            max_test_retries = 3
            for attempt in range(max_test_retries):
                test_result = self.tester.run()
                if test_result.success:
                    console.print("[green]✓ Fix successful! Tests passing.[/green]")
                    
                    break
                console.print(f"[yellow]Tests failed (attempt {attempt+1}/{max_test_retries}), fixing...[/yellow]")
                fix_result = self.builder.fix(test_result.error or "Tests failed")
                if not fix_result.success:
                    return fix_result
            else:
                console.print("[red]Tests failed after max retries[/red]")
                return TaskResult(success=False, error="Tests failed after 3 attempts")            
            # Step 5: Review
            self._update_dashboard()
            review_result = self.reviewer.run(user_input, build_result.output)

            print(f"DEBUG: Reviewer returned: {review_result}") 
            self._update_dashboard()
            
            # Final summary
            console.print("\n[green]✓ Workflow complete![/green]")
            
            return TaskResult(
                success=True,
                output=build_result.output,
                data={  # Changed from metrics
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
