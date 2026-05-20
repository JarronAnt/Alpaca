# src/alpaca/__init__.py
"""Alpaca - Production-grade multi-agent AI coding assistant."""

__version__ = "1.0.0"
__all__ = ["AgentOrchestrator", "Config"]

from alpaca.config import Config
from alpaca.core.orchestrator import AgentOrchestrator
