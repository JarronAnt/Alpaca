# src/alpaca/logger.py
"""Structured logging configuration."""

import sys

import structlog
from rich.console import Console
from rich.traceback import install as install_rich_traceback


def configure_logging(log_level: str = "INFO", debug: bool = False) -> None:
    """Configure structured logging."""
    
    # Install rich traceback handler
    install_rich_traceback(show_locals=debug)
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if not debug else structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Set up standard library logging
    import logging
    
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level),
    )


def get_logger(name: str | None = None):
    """Get a structured logger."""
    return structlog.get_logger(name)


# Console for rich output
console = Console()
