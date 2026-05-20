# src/alpaca/config.py
"""Configuration management with validation."""

import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with validation."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    # Application
    app_name: str = "alpaca"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    
    # LLM Configuration
    ollama_url: str = Field(
        default="http://localhost:11434/api/chat",
        alias="OLLAMA_URL",
    )
    router_model: str = Field(default="llama3", alias="ROUTER_MODEL")
    planner_model: str = Field(default="llama3", alias="PLANNER_MODEL")
    builder_model: str = Field(default="llama3", alias="BUILDER_MODEL")
    tester_model: str = Field(default="llama3", alias="TESTER_MODEL")
    reviewer_model: str = Field(default="llama3", alias="REVIEWER_MODEL")
    
    llm_timeout: int = Field(default=120, ge=1, le=600)
    llm_max_retries: int = Field(default=3, ge=0, le=10)
    llm_retry_delay: float = Field(default=1.0, ge=0.1, le=60.0)
    
    # Workspace
    workspace_root: Path = Field(
        default=Path.home() / "AgentWorkspace",
        alias="WORKSPACE_ROOT",
    )
    
    # Memory
    max_history: int = Field(default=20, ge=1, le=100)
    max_tool_steps: int = Field(default=25, ge=1, le=100)
    
    # Security
    allowed_commands: list[str] = Field(default_factory=lambda: [
        "python", "pytest", "pip", "npm", "node"
    ])
    blocked_paths: list[str] = Field(default_factory=lambda: [
        ".git", "__pycache__", "node_modules", "venv", ".venv", ".env"
    ])
    shell_timeout: int = Field(default=60, ge=1, le=300)
    
    # Coding detection
    coding_keywords: list[str] = Field(default_factory=lambda: [
        "code", "python", "javascript", "typescript", "react",
        "bug", "fix", "script", "build", "app", "game",
        "api", "cli", "tool", "project", "file", "create",
        "implement", "develop", "function", "class", "module"
    ])
    
    @field_validator("workspace_root", mode="before")
    @classmethod
    def resolve_workspace_path(cls, v: str | Path) -> Path:
        """Resolve workspace path."""
        path = Path(v).expanduser().resolve()
        # Create if doesn't exist
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        upper = v.upper()
        if upper not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return upper


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global config instance
Config = get_settings()
