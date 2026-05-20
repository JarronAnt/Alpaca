# src/alpaca/tools/filesystem.py
"""Filesystem tools with workspace integration."""

from pathlib import Path

from alpaca.core.workspace import Workspace
from alpaca.models import ToolResult
from alpaca.tools.base import BaseTool


class CreateDirectoryTool(BaseTool):
    """Create a directory."""
    
    name = "create_directory"
    description = "Create a directory in the workspace"
    
    def execute(self, **kwargs) -> ToolResult:
        """Create directory."""
        path = kwargs.get("path")
        if not path:
            return ToolResult(success=False, error="Missing 'path' argument")
        
        ws = Workspace()
        try:
            created = ws.mkdir(path)
            return ToolResult(
                success=True,
                output=f"Created directory: {created}",
                data={"path": str(created)},
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class WriteFileTool(BaseTool):
    """Write a file."""
    
    name = "write_file"
    description = "Write content to a file in the workspace"
    
    def execute(self, **kwargs) -> ToolResult:
        """Write file."""
        path = kwargs.get("path")
        content = kwargs.get("content", "")
        
        if not path:
            return ToolResult(success=False, error="Missing 'path' argument")
        
        ws = Workspace()
        try:
            # Auto-create parent directory
            ws.mkdir(Path(path).parent, exist_ok=True)
            written = ws.write(path, content)
            return ToolResult(
                success=True,
                output=f"Wrote file: {written}",
                data={"path": str(written), "size": len(content)},
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class ReadFileTool(BaseTool):
    """Read a file."""
    
    name = "read_file"
    description = "Read content of a file from the workspace"
    
    def execute(self, **kwargs) -> ToolResult:
        """Read file."""
        path = kwargs.get("path")
        if not path:
            return ToolResult(success=False, error="Missing 'path' argument")
        
        ws = Workspace()
        try:
            content = ws.read(path)
            return ToolResult(
                success=True,
                output=content,
                data={"path": path, "size": len(content)},
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class ListFilesTool(BaseTool):
    """List files."""
    
    name = "list_files"
    description = "List files in a directory"
    
    def execute(self, **kwargs) -> ToolResult:
        """List files."""
        path = kwargs.get("path", ".")
        
        ws = Workspace()
        try:
            files = ws.list_files(path)
            return ToolResult(
                success=True,
                output="\n".join(files),
                data={"files": files, "count": len(files)},
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class FileExistsTool(BaseTool):
    """Check if file exists."""
    
    name = "file_exists"
    description = "Check if a file or directory exists"
    
    def execute(self, **kwargs) -> ToolResult:
        """Check existence."""
        path = kwargs.get("path")
        if not path:
            return ToolResult(success=False, error="Missing 'path' argument")
        
        ws = Workspace()
        exists = ws.exists(path)
        return ToolResult(
            success=True,
            output=f"{'Exists' if exists else 'Does not exist'}: {path}",
            data={"exists": exists, "path": path},
        )


class WalkDirectoryTool(BaseTool):
    """Walk directory tree."""
    
    name = "walk_directory"
    description = "Recursively list all files and directories"
    
    def execute(self, **kwargs) -> ToolResult:
        """Walk directory."""
        path = kwargs.get("path", ".")
        
        ws = Workspace()
        try:
            tree = ws.walk(path)
            lines = []
            for entry in tree:
                lines.append(f"\n[{entry['path']}/]")
                for d in entry["dirs"]:
                    lines.append(f"  DIR: {d}/")
                for f in entry["files"]:
                    lines.append(f"  FILE: {f}")
            return ToolResult(
                success=True,
                output="\n".join(lines),
                data={"tree": tree},
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class DeleteFileTool(BaseTool):
    """Delete a file."""
    
    name = "delete_file"
    description = "Delete a file from the workspace"
    
    def execute(self, **kwargs) -> ToolResult:
        """Delete file."""
        path = kwargs.get("path")
        if not path:
            return ToolResult(success=False, error="Missing 'path' argument")
        
        ws = Workspace()
        try:
            ws.delete(path)
            return ToolResult(
                success=True,
                output=f"Deleted: {path}",
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
