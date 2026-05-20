# src/alpaca/cli.py
"""Command-line interface."""

import sys

import click

from alpaca.config import Config, Settings
from alpaca.core.llm import get_llm_client
from alpaca.core.orchestrator import AgentOrchestrator
from alpaca.logger import configure_logging, console, get_logger

logger = get_logger(__name__)


@click.group()
@click.option("--debug", is_flag=True, help="Enable debug mode")
@click.option("--config", type=click.Path(), help="Path to config file")
@click.pass_context
def cli(ctx: click.Context, debug: bool, config: str | None) -> None:
    """Alpaca - Multi-agent AI coding assistant."""
    ctx.ensure_object(dict)
    ctx.obj["debug"] = debug
    
    log_level = "DEBUG" if debug else Config.log_level
    configure_logging(log_level, debug)


@cli.command()
@click.argument("task", required=False)
@click.option("--interactive", "-i", is_flag=True, help="Interactive mode")
@click.pass_context
def run(ctx: click.Context, task: str | None, interactive: bool) -> None:
    """Run a task or start interactive mode."""
    # Health check
    client = get_llm_client()
    if not client.health_check():
        console.print("[red]Error:[/red] Ollama is not running")
        console.print("[dim]Start Ollama with: ollama serve[/dim]")
        sys.exit(1)
    
    orchestrator = AgentOrchestrator()
    
    if interactive or not task:
        orchestrator.interactive()
    else:
        result = orchestrator.run(task)
        if not result.success:
            sys.exit(1)


@cli.command()
def status() -> None:
    """Check system status."""
    client = get_llm_client()
    
    console.print("\n[bold]Alpaca Status[/bold]")
    console.print(f"Workspace: {Config.workspace_root}")
    
    if client.health_check():
        console.print("[green]✓ Ollama is running[/green]")
    else:
        console.print("[red]✗ Ollama is not running[/red]")


@cli.command()
def init() -> None:
    """Initialize workspace."""
    from alpaca.core.workspace import Workspace
    
    ws = Workspace()
    console.print(f"[green]✓ Workspace initialized:[/green] {ws.root}")


def main() -> None:
    """Entry point."""
    cli()


if __name__ == "__main__":
    main()
