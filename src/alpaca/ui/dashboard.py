# src/alpaca/ui/dashboard.py
"""Live dashboard for agent states."""

from rich.live import Live
from rich.table import Table

from alpaca.models import AgentState, AgentStatus
from alpaca.ui.console import AGENT_STYLES, STATUS_STYLES


class Dashboard:
    """Live-updating dashboard."""
    
    def __init__(self):
        self._live: Live | None = None
        
    def _create_table(self, states: dict[str, AgentState]) -> Table:
        """Create status table."""
        table = Table(title="🦙 Alpaca Agent Status")
        table.add_column("Agent", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Task", style="dim")
        
        for name, state in states.items():
            icon, _ = AGENT_STYLES.get(name, ("❓", "white"))
            status_color = STATUS_STYLES.get(state.status.value, "white")
            
            table.add_row(
                f"{icon} {name}",
                f"[{status_color}]{state.status.value}[/{status_color}]",
                state.current_task or "-",
            )
            
        return table
    
    def render(self, states: dict[str, AgentState]) -> None:
        """Render or update dashboard."""
        table = self._create_table(states)
        
        # Simple print for now - could use Live for real-time updates
        from alpaca.logger import console
        console.print(table)
