"""Parser for Claude Code session files."""

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Literal

from cwhap.models.file_event import FileEvent
from cwhap.models.message import AssistantMessage, Message, UserMessage
from cwhap.models.session import Session, SessionIndex

# Valid operation types
OperationType = Literal["read", "write", "edit", "glob", "grep", "bash", "search"]

# Default Claude Code data directory
CLAUDE_DATA_DIR = Path.home() / ".claude"
PROJECTS_DIR = CLAUDE_DATA_DIR / "projects"


def get_project_dirs() -> list[Path]:
    """Get all project directories in Claude data folder."""
    if not PROJECTS_DIR.exists():
        return []
    return [p for p in PROJECTS_DIR.iterdir() if p.is_dir() and not p.name.startswith(".")]


def load_sessions_index(project_dir: Path) -> SessionIndex | None:
    """Load sessions-index.json from a project directory."""
    index_file = project_dir / "sessions-index.json"
    if not index_file.exists():
        return None

    try:
        with open(index_file) as f:
            data = json.load(f)
        return SessionIndex.model_validate(data)
    except (json.JSONDecodeError, ValueError):
        return None


def get_all_sessions() -> list[Session]:
    """Get all sessions from all projects."""
    sessions: list[Session] = []

    for project_dir in get_project_dirs():
        index = load_sessions_index(project_dir)
        if not index:
            continue

        for entry in index.entries:
            sessions.append(Session.from_index_entry(entry))

    # Sort by modified time, most recent first
    sessions.sort(key=lambda s: s.modified, reverse=True)
    return sessions


def parse_session_line(line: str) -> Message | None:
    """Parse a single JSONL line into a Message."""
    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        return None

    msg_type = data.get("type")
    if msg_type not in ("user", "assistant", "file-history-snapshot", "summary"):
        return None

    # Handle message payload based on type
    message_data = data.get("message")
    if message_data:
        if msg_type == "user":
            data["message"] = UserMessage.model_validate(message_data)
        elif msg_type == "assistant":
            data["message"] = AssistantMessage.model_validate(message_data)

    try:
        return Message.model_validate(data)
    except ValueError:
        return None


def iter_session_messages(session_file: Path) -> Iterator[Message]:
    """Iterate over messages in a session file."""
    if not session_file.exists():
        return

    with open(session_file) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            msg = parse_session_line(line)
            if msg:
                yield msg


def extract_file_events(message: Message) -> list[FileEvent]:
    """Extract file events from a message's tool uses."""
    events: list[FileEvent] = []

    for tool in message.tool_uses:
        if not tool.is_file_operation:
            continue

        file_path = tool.file_path
        if not file_path:
            # For glob/grep, use pattern as identifier
            pattern = tool.input_params.get("pattern", "")
            file_path = f"pattern:{pattern}"

        operation_map: dict[str, OperationType] = {
            "Read": "read",
            "Write": "write",
            "Edit": "edit",
            "Glob": "glob",
            "Grep": "grep",
            "NotebookEdit": "edit",
        }

        operation = operation_map.get(tool.name, "read")

        events.append(
            FileEvent(
                file_path=file_path,
                operation=operation,
                timestamp=message.timestamp,
                session_id=message.session_id,
                message_uuid=message.uuid,
                tool_name=tool.name,
                pattern=tool.input_params.get("pattern"),
            )
        )

    return events


def load_session_details(session: Session) -> Session:
    """Load full session details by parsing the session JSONL file."""
    # Find the session file
    session_file = None
    for project_dir in get_project_dirs():
        candidate = project_dir / f"{session.session_id}.jsonl"
        if candidate.exists():
            session_file = candidate
            break

    if not session_file:
        return session

    files_read: list[str] = []
    files_written: list[str] = []
    files_edited: list[str] = []
    tool_count = 0
    total_input = 0
    total_output = 0
    model = None

    for message in iter_session_messages(session_file):
        # Extract tool usage
        tools = message.tool_uses
        tool_count += len(tools)

        for tool in tools:
            path = tool.file_path
            if path:
                if tool.name == "Read":
                    files_read.append(path)
                elif tool.name == "Write":
                    files_written.append(path)
                elif tool.name in ("Edit", "NotebookEdit"):
                    files_edited.append(path)

        # Extract token usage
        if message.type == "assistant" and message.message:
            msg = message.message
            if isinstance(msg, AssistantMessage):
                if msg.model and not model:
                    model = msg.model
                if msg.usage:
                    total_input += msg.usage.input_tokens
                    total_output += msg.usage.output_tokens

    # Update session with computed fields
    session.tool_call_count = tool_count
    session.files_read = list(set(files_read))
    session.files_written = list(set(files_written))
    session.files_edited = list(set(files_edited))
    session.total_input_tokens = total_input
    session.total_output_tokens = total_output
    session.model = model

    return session


def get_recent_file_events(limit: int = 50) -> list[FileEvent]:
    """Get recent file events across all sessions."""
    events: list[FileEvent] = []

    for project_dir in get_project_dirs():
        index = load_sessions_index(project_dir)
        if not index:
            continue

        # Only look at recent sessions
        recent_entries = sorted(index.entries, key=lambda e: e.modified, reverse=True)[:5]

        for entry in recent_entries:
            session_file = project_dir / f"{entry.session_id}.jsonl"
            for message in iter_session_messages(session_file):
                events.extend(extract_file_events(message))

    # Sort by timestamp, most recent first
    events.sort(key=lambda e: e.timestamp, reverse=True)
    return events[:limit]
