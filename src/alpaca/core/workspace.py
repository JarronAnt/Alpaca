# src/alpaca/core/workspace.py
"""Secure workspace management."""

import os
import shutil
from pathlib import Path

from alpaca.config import Config
from alpaca.exceptions import SecurityError, WorkspaceError
from alpaca.logger import get_logger

logger = get_logger(__name__)


class Workspace:
    """Secure workspace with path boundary enforcement."""
    
    def __init__(self, root: Path | None = None):
        self.root = (root or Config.workspace_root).resolve()
        self.blocked_paths = set(Config.blocked_paths)
        
    def _resolve_path(self, path: str | Path) -> Path:
        """Resolve path within workspace boundaries."""
        # Clean the path
        path_str = str(path).replace('\\', '/').strip('/')
    
        # Remove workspace prefix if present
        workspace_str = str(self.root).replace('\\', '/')
        if path_str.startswith(workspace_str):
            path_str = path_str[len(workspace_str):].strip('/')
    
        # Strip any leading slashes - treat absolute-looking paths as relative
        path_str = path_str.lstrip('/')
        
        # Resolve relative to workspace
        full = (self.root / path_str).resolve()
    
        # Security check: must be within workspace
        try:
            full.relative_to(self.root)
        except ValueError:
            logger.error(
                "Path escape attempt detected",
                path=str(path),
                resolved=str(full),
                workspace=str(self.root),
            )
            raise SecurityError(
                f"Path '{path}' escapes workspace boundary '{self.root}'"
            )
        
        return full   
    




    def _check_blocked(self, path: Path) -> None:
        """Check if path contains blocked directories."""
        for part in path.parts:
            if part in self.blocked_paths:
                raise SecurityError(f"Access to '{part}' is blocked")
    
    def exists(self, path: str | Path) -> bool:
        """Check if path exists."""
        try:
            full = self._resolve_path(path)
            return full.exists()
        except SecurityError:
            return False
    
    def mkdir(self, path: str | Path, exist_ok: bool = True) -> Path:
        """Create directory."""
        full = self._resolve_path(path)
        self._check_blocked(full)
        
        try:
            full.mkdir(parents=True, exist_ok=exist_ok)
            logger.debug("Created directory", path=str(full))
            return full
        except Exception as e:
            raise WorkspaceError(f"Failed to create directory '{path}': {e}")
    
    def write(self, path: str | Path, content: str, mode: str = "w") -> Path:
        """Write file."""
        full = self._resolve_path(path)
        self._check_blocked(full)
       

        # If path exists as a directory, remove it first
        if full.exists() and full.is_dir():
            import shutil
            shutil.rmtree(full)
            logger.warning(f"Removed directory occupying file path: {full}")
    

        # Ensure parent exists
        full.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(full, mode, encoding="utf-8") as f:
                f.write(content)
            logger.debug("Wrote file", path=str(full), size=len(content))
            return full
        except Exception as e:
            raise WorkspaceError(f"Failed to write file '{path}': {e}")
    
    def read(self, path: str | Path) -> str:
        """Read file."""
        full = self._resolve_path(path)
        
        if not full.exists():
            raise WorkspaceError(f"File not found: '{path}'")
        if not full.is_file():
            raise WorkspaceError(f"Path is not a file: '{path}'")
            
        try:
            with open(full, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            raise WorkspaceError(f"Failed to read file '{path}': {e}")
    
    def delete(self, path: str | Path, recursive: bool = False) -> None:
        """Delete file or directory."""
        full = self._resolve_path(path)
        self._check_blocked(full)
        
        try:
            if full.is_file():
                full.unlink()
                logger.debug("Deleted file", path=str(full))
            elif full.is_dir():
                if recursive:
                    shutil.rmtree(full)
                    logger.debug("Deleted directory recursively", path=str(full))
                else:
                    full.rmdir()
                    logger.debug("Deleted empty directory", path=str(full))
        except Exception as e:
            raise WorkspaceError(f"Failed to delete '{path}': {e}")
    
    def list_files(self, path: str | Path = ".") -> list[str]:
        """List files in directory."""
        full = self._resolve_path(path)
        
        if not full.exists():
            return []
        if not full.is_dir():
            raise WorkspaceError(f"Path is not a directory: '{path}'")
            
        try:
            return [f.name for f in full.iterdir()]
        except Exception as e:
            raise WorkspaceError(f"Failed to list '{path}': {e}")
    
    def walk(self, path: str | Path = ".") -> list[dict]:
        """Walk directory tree."""
        full = self._resolve_path(path)
        results = []
        
        for root, dirs, files in os.walk(full):
            # Filter blocked directories
            dirs[:] = [d for d in dirs if d not in self.blocked_paths]
            
            rel_root = Path(root).relative_to(self.root)
            results.append({
                "path": str(rel_root),
                "dirs": dirs,
                "files": files,
            })
            
        return results
    
    def find_latest_project(self) -> Path | None:
        """Find most recently modified project directory."""
        try:
            candidates = [
                d for d in self.root.iterdir()
                if d.is_dir() and d.name not in self.blocked_paths
            ]
            
            if not candidates:
                return None
                
            candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            return candidates[0]
        except Exception as e:
            logger.error("Failed to find latest project", error=str(e))
            return None
