# src/alpaca/ui/console.py
"""Console utilities."""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()

# Agent styling
AGENT_STYLES = {
    "THAG": ("🪨", "cyan"),
    "OOGA": ("🧾", "yellow"),
    "GROG": ("🪓", "green"),
    "BRAK": ("💥", "red"),
    "ROG": ("🧙", "magenta"),
}

STATUS_STYLES = {
    "idle": "white",
    "running": "yellow",
    "planning": "yellow",
    "building": "yellow",
    "testing": "yellow",
    "reviewing": "yellow",
    "success": "green",
    "failed": "red",
}


def log_agent(agent: str, message: str) -> None:
    """Log an agent message."""
    icon, color = AGENT_STYLES.get(agent, ("❓", "white"))
    console.print(f"[{color}]{icon} [{agent}][/{color}] {message}")
