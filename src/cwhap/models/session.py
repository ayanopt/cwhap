"""Session data model."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SessionIndexEntry(BaseModel):
    """Entry in sessions-index.json."""

    session_id: str = Field(alias="sessionId")
    full_path: str = Field(alias="fullPath")
    file_mtime: int = Field(alias="fileMtime")
    first_prompt: str = Field(alias="firstPrompt")
    summary: str
    message_count: int = Field(alias="messageCount")
    created: datetime
    modified: datetime
    git_branch: str = Field(alias="gitBranch")
    project_path: str = Field(alias="projectPath")
    is_sidechain: bool = Field(alias="isSidechain")

    model_config = {"populate_by_name": True}


class SessionIndex(BaseModel):
    """Sessions index file structure."""

    version: int
    entries: list[SessionIndexEntry]
    original_path: str = Field(alias="originalPath")

    model_config = {"populate_by_name": True}


class Session(BaseModel):
    """A Claude Code session with computed statistics."""

    session_id: str
    project_path: str
    first_prompt: str
    summary: str
    message_count: int
    created: datetime
    modified: datetime
    git_branch: str = ""
    is_sidechain: bool = False

    # Computed fields (populated after parsing session file)
    tool_call_count: int = 0
    files_read: list[str] = Field(default_factory=list)
    files_written: list[str] = Field(default_factory=list)
    files_edited: list[str] = Field(default_factory=list)
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    model: Optional[str] = None

    @property
    def is_active(self) -> bool:
        """Check if session was modified recently (within last 5 minutes)."""
        delta = datetime.now(self.modified.tzinfo) - self.modified
        return delta.total_seconds() < 300

    @property
    def all_files_accessed(self) -> set[str]:
        """Get all unique files accessed by this session."""
        return set(self.files_read + self.files_written + self.files_edited)

    @classmethod
    def from_index_entry(cls, entry: SessionIndexEntry) -> "Session":
        """Create a Session from a SessionIndexEntry."""
        return cls(
            session_id=entry.session_id,
            project_path=entry.project_path,
            first_prompt=entry.first_prompt,
            summary=entry.summary,
            message_count=entry.message_count,
            created=entry.created,
            modified=entry.modified,
            git_branch=entry.git_branch,
            is_sidechain=entry.is_sidechain,
        )
