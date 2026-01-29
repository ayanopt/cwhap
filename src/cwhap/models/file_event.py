"""File event data model."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class FileEvent(BaseModel):
    """A file access event from a Claude Code session."""

    file_path: str
    operation: Literal["read", "write", "edit", "glob", "grep", "bash", "search"]
    timestamp: datetime
    session_id: str
    message_uuid: str
    tool_name: str

    # Optional context
    pattern: str | None = None  # For glob/grep operations
    preview: str | None = None  # Brief preview of content/result
    command: str | None = None  # For bash operations

    @property
    def is_write_operation(self) -> bool:
        """Check if this event modifies files."""
        return self.operation in {"write", "edit"}

    @property
    def is_file_operation(self) -> bool:
        """Check if this event operates on actual files (not patterns/commands)."""
        return self.operation in {"read", "write", "edit"}

    @property
    def operation_icon(self) -> str:
        """Get an icon representing the operation type."""
        icons = {
            "read": "R",
            "write": "W",
            "edit": "E",
            "glob": "G",
            "grep": "S",  # Search
            "bash": "$",
            "search": "?",
        }
        return icons.get(self.operation, "?")

    @property
    def display_name(self) -> str:
        """Get a short display name for the file."""
        parts = self.file_path.split("/")
        if len(parts) > 2:
            return f".../{parts[-2]}/{parts[-1]}"
        return self.file_path
