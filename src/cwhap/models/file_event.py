"""File event data model."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel


class FileEvent(BaseModel):
    """A file access event from a Claude Code session."""

    file_path: str
    operation: Literal["read", "write", "edit", "glob", "grep"]
    timestamp: datetime
    session_id: str
    message_uuid: str
    tool_name: str

    # Optional context
    pattern: Optional[str] = None  # For glob/grep operations
    preview: Optional[str] = None  # Brief preview of content/result

    @property
    def is_write_operation(self) -> bool:
        """Check if this event modifies files."""
        return self.operation in {"write", "edit"}

    @property
    def operation_icon(self) -> str:
        """Get an icon representing the operation type."""
        icons = {
            "read": "R",
            "write": "W",
            "edit": "E",
            "glob": "G",
            "grep": "S",  # Search
        }
        return icons.get(self.operation, "?")

    @property
    def display_name(self) -> str:
        """Get a short display name for the file."""
        parts = self.file_path.split("/")
        if len(parts) > 2:
            return f".../{parts[-2]}/{parts[-1]}"
        return self.file_path
