# src/alpaca/tools/shell.py
"""Secure shell execution."""

import subprocess
import sys
from typing import Any

from alpaca.config import Config
from alpaca.exceptions import SecurityError
from alpaca.models import ToolResult
from alpaca.tools.base import BaseTool


class ShellTool(BaseTool):
    """Execute shell commands securely."""
    
    name = "run_shell"
    description = "Run a shell command in the workspace"
    
    def __init__(self):
        # Comprehensive list of safe commands
        self.allowed_commands = {
            # Python
            "python", "pytest", "pip", "pip3", "python3",
            # Node
            "npm", "node", "npx", "yarn",
            # Shell basics
            "cd", "ls", "cat", "echo", "pwd", "mkdir", "touch", "rm", "cp", "mv",
            "head", "tail", "grep", "find", "wc",
            # Permissions
            "chmod", "chown",
            # Version control
            "git", "gitk",
            # Network
            "curl", "wget",
            # Archives
            "tar", "unzip", "gzip",
            # Text editors (safe for non-interactive)
            "sed", "awk", "tr", "sort", "uniq",
        }
        self.blocked_commands = {
            "sudo", "su", "passwd", "mkfs", "dd", "fdisk",
            "mount", "umount", "reboot", "shutdown", "halt", "poweroff",
            "kill", "pkill", "killall",
        }
        self.timeout = Config.shell_timeout
        
    def _validate_command(self, command: str) -> None:
        """Validate command is allowed."""
        import shlex
        
        try:
            parts = shlex.split(command.strip())
        except ValueError as e:
            raise SecurityError(f"Invalid command syntax: {e}")
            
        if not parts:
            raise SecurityError("Empty command")
        
        # Check for blocked commands first
        cmd_lower = command.lower()
        for blocked in self.blocked_commands:
            if blocked in cmd_lower:
                raise SecurityError(f"Command '{blocked}' is blocked for security")
            
        base = parts[0].lower()
        
        # cd is a builtin, always allow (handled by cwd param)
        if base == "cd":
            return
            
        if base not in self.allowed_commands:
            raise SecurityError(
                f"Command '{base}' not allowed. Allowed: {sorted(self.allowed_commands)}"
            )
    
    def _normalize_command(self, command: str) -> str:
        """Normalize command for cross-platform compatibility."""
        python_path = sys.executable
        
        cmd = command.strip()
        
        # Normalize pip
        if cmd.startswith("pip"):
            args = cmd[3:].strip() if len(cmd) > 3 else ""
            return f'"{python_path}" -m pip {args}'
        
        # Normalize pytest
        if cmd.startswith("pytest"):
            args = cmd[6:].strip() if len(cmd) > 6 else ""
            return f'"{python_path}" -m pytest {args}'
            
        # Normalize python
        if cmd.startswith("python "):
            args = cmd[7:]
            return f'"{python_path}" {args}'
            
        return cmd
    
    def execute(self, **kwargs: Any) -> ToolResult:
        """Execute shell command."""
        command = kwargs.get("command", "")
        cwd = kwargs.get("cwd")
        
        if not command:
            return ToolResult(success=False, error="No command provided")
        
        try:
            self._validate_command(command)
            command = self._normalize_command(command)
            
            working_dir = cwd or str(Config.workspace_root)
            
            result = subprocess.run(
                command,
                shell=True,
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            
            return ToolResult(
                success=result.returncode == 0,
                output=result.stdout,
                error=result.stderr if result.stderr else None,
                data={
                    "return_code": result.returncode,
                    "command": command,
                    "cwd": working_dir,
                },
            )
            
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                error=f"Command timed out after {self.timeout}s",
            )
        except SecurityError as e:
            return ToolResult(success=False, error=str(e))
        except Exception as e:
            return ToolResult(success=False, error=f"Execution failed: {e}")
