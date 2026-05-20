# src/alpaca/exceptions.py
"""Custom exceptions for Alpaca."""


class AlpacaError(Exception):
    """Base exception for all Alpaca errors."""
    pass


class ConfigurationError(AlpacaError):
    """Raised when configuration is invalid."""
    pass


class LLMError(AlpacaError):
    """Raised when LLM API call fails."""
    pass


class ToolError(AlpacaError):
    """Raised when a tool execution fails."""
    pass


class ParseError(AlpacaError):
    """Raised when parsing fails."""
    pass


class WorkspaceError(AlpacaError):
    """Raised when workspace operation fails."""
    pass


class AgentError(AlpacaError):
    """Raised when an agent fails."""
    pass


class SecurityError(AlpacaError):
    """Raised when a security violation is detected."""
    pass
