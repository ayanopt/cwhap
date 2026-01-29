"""Live agent and conflict event models."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal

# Agent color palette - unique colors for up to 12 agents
AGENT_COLORS = [
    "cyan", "magenta", "yellow", "green", "blue", "red",
    "bright_cyan", "bright_magenta", "bright_yellow", "bright_green", "bright_blue", "bright_red",
]


@dataclass
class LiveAgent:
    """Represents an actively running Claude Code instance."""

    session_id: str
    project_path: str
    status: Literal["active", "thinking", "idle"] = "idle"
    last_activity: datetime = field(default_factory=lambda: datetime.now(UTC))
    current_operation: str | None = None
    current_file: str | None = None
    files_accessed: list[str] = field(default_factory=list)
    message_count: int = 0
    tool_count: int = 0
    color_index: int = 0  # Index into AGENT_COLORS

    @property
    def status_icon(self) -> str:
        """Get status indicator icon."""
        icons = {
            "active": "●",
            "thinking": "◐",
            "idle": "○",
        }
        return icons.get(self.status, "?")

    @property
    def status_color(self) -> str:
        """Get status color for display."""
        colors = {
            "active": "green",
            "thinking": "yellow",
            "idle": "dim",
        }
        return colors.get(self.status, "white")

    @property
    def agent_color(self) -> str:
        """Get unique agent color."""
        return AGENT_COLORS[self.color_index % len(AGENT_COLORS)]

    @property
    def short_id(self) -> str:
        """Get shortened session ID for display."""
        return self.session_id[:8]

    @property
    def short_project(self) -> str:
        """Get shortened project path for display."""
        parts = self.project_path.split("/")
        if len(parts) > 2:
            return f".../{'/'.join(parts[-2:])}"
        return self.project_path

    def seconds_since_activity(self) -> float:
        """Get seconds since last activity."""
        now = datetime.now(UTC)
        if self.last_activity.tzinfo is None:
            last = self.last_activity.replace(tzinfo=UTC)
        else:
            last = self.last_activity
        return (now - last).total_seconds()


@dataclass
class ConflictEvent:
    """File conflict detected between agents."""

    file_path: str
    agents: list[str]  # session_ids involved
    severity: Literal["critical", "warning"]
    conflict_type: Literal["simultaneous_edit", "read_write_race"]
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def short_agents(self) -> str:
        """Get shortened agent IDs for display."""
        return ", ".join(a[:8] for a in self.agents)

    @property
    def short_file(self) -> str:
        """Get shortened file path for display."""
        parts = self.file_path.split("/")
        if len(parts) > 2:
            return f".../{parts[-1]}"
        return self.file_path

    @property
    def severity_color(self) -> str:
        """Get color based on severity."""
        return "red" if self.severity == "critical" else "yellow"


@dataclass
class LiveActivityEvent:
    """Real-time activity from an agent."""

    session_id: str
    timestamp: datetime
    event_type: Literal["tool_start", "tool_complete", "message", "error"]
    tool_name: str | None = None
    file_path: str | None = None
    operation: str | None = None  # read, write, edit, etc.

    @property
    def display_text(self) -> str:
        """Get formatted display text."""
        time_str = self.timestamp.strftime("%H:%M:%S")
        session = self.session_id[:4]

        if self.tool_name and self.file_path:
            # Shorten file path
            parts = self.file_path.split("/")
            short_file = parts[-1] if parts else self.file_path
            return f"{time_str} [{session}] {self.tool_name} {short_file}"
        elif self.tool_name:
            return f"{time_str} [{session}] {self.tool_name}"
        else:
            return f"{time_str} [{session}] {self.event_type}"

    @property
    def color(self) -> str:
        """Get color based on operation type."""
        if self.operation == "write":
            return "yellow"
        elif self.operation == "edit":
            return "green"
        elif self.operation == "read":
            return "cyan"
        elif self.event_type == "error":
            return "red"
        return "white"
