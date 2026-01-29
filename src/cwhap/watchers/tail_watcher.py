"""Efficient JSONL tailing watcher for live monitoring."""

import json
import threading
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from cwhap.models.agent import LiveActivityEvent
from cwhap.watchers.base import BaseWatcher

CLAUDE_PROJECTS_DIR = Path.home() / ".claude" / "projects"


class TailFileHandler(FileSystemEventHandler):
    """Handler that tails JSONL files for new content."""

    def __init__(self, callback: Callable[[LiveActivityEvent], None]) -> None:
        super().__init__()
        self.callback = callback
        self._positions: dict[str, int] = {}
        self._lock = threading.Lock()

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification - read new lines."""
        if event.is_directory:
            return

        path = Path(event.src_path)

        # Only process session JSONL files
        if path.suffix != ".jsonl" or path.name == "sessions-index.json":
            return

        self._process_new_lines(path)

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle new file creation."""
        if event.is_directory:
            return

        path = Path(event.src_path)
        if path.suffix == ".jsonl" and path.name != "sessions-index.json":
            # Start tracking from beginning
            with self._lock:
                self._positions[str(path)] = 0
            self._process_new_lines(path)

    def _process_new_lines(self, path: Path) -> None:
        """Read and process new lines from a file."""
        path_str = str(path)

        with self._lock:
            last_pos = self._positions.get(path_str, 0)

        try:
            with open(path) as f:
                f.seek(last_pos)
                new_lines = f.readlines()
                new_pos = f.tell()

            with self._lock:
                self._positions[path_str] = new_pos

            # Parse new lines and emit events
            session_id = path.stem
            for line in new_lines:
                line = line.strip()
                if not line:
                    continue

                event = self._parse_line(line, session_id)
                if event:
                    self.callback(event)

        except (OSError, json.JSONDecodeError):
            pass  # File may have been deleted or corrupted

    def _parse_line(self, line: str, session_id: str) -> LiveActivityEvent | None:
        """Parse a JSONL line into a LiveActivityEvent."""
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            return None

        msg_type = data.get("type")
        timestamp_str = data.get("timestamp")

        if not timestamp_str:
            timestamp = datetime.now(UTC)
        else:
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            except ValueError:
                timestamp = datetime.now(UTC)

        # Extract tool use from assistant messages
        if msg_type == "assistant":
            message = data.get("message", {})
            content = message.get("content", [])

            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        tool_name = block.get("name", "")
                        input_params = block.get("input", {})

                        # Extract file path
                        file_path = None
                        operation = None

                        for key in ["file_path", "path", "notebook_path"]:
                            if key in input_params:
                                file_path = input_params[key]
                                break

                        # Determine operation type
                        if tool_name == "Read":
                            operation = "read"
                        elif tool_name == "Write":
                            operation = "write"
                        elif tool_name in ("Edit", "NotebookEdit"):
                            operation = "edit"
                        elif tool_name in ("Glob", "Grep"):
                            operation = "search"
                            pattern = input_params.get("pattern", "")
                            file_path = f"pattern:{pattern}" if pattern else None
                        elif tool_name == "Bash":
                            operation = "bash"
                            cmd = input_params.get("command", "")[:50]
                            file_path = f"bash:{cmd}" if cmd else None

                        return LiveActivityEvent(
                            session_id=session_id,
                            timestamp=timestamp,
                            event_type="tool_start",
                            tool_name=tool_name,
                            file_path=file_path,
                            operation=operation,
                        )

        elif msg_type == "user":
            return LiveActivityEvent(
                session_id=session_id,
                timestamp=timestamp,
                event_type="message",
            )

        return None


class TailWatcher(BaseWatcher):
    """Watches session files and tails them for new activity."""

    def __init__(self, watch_path: Path | None = None) -> None:
        super().__init__()
        self.watch_path = watch_path or CLAUDE_PROJECTS_DIR
        self._observer: Observer | None = None  # type: ignore[valid-type]
        self._handler: TailFileHandler | None = None

    def start(self) -> None:
        """Start watching and tailing session files."""
        if self._running:
            return

        if not self.watch_path.exists():
            return

        self._handler = TailFileHandler(self._on_activity)
        self._observer = Observer()

        # Initialize positions for existing files
        self._init_file_positions()

        self._observer.schedule(self._handler, str(self.watch_path), recursive=True)  # type: ignore[no-untyped-call]
        self._observer.start()  # type: ignore[no-untyped-call]
        self._running = True

    def stop(self) -> None:
        """Stop watching."""
        if not self._running or not self._observer:
            return

        self._observer.stop()  # type: ignore[attr-defined]
        self._observer.join(timeout=5)  # type: ignore[attr-defined]
        self._observer = None
        self._handler = None
        self._running = False

    def _init_file_positions(self) -> None:
        """Initialize file positions to end of existing files."""
        if not self._handler:
            return

        for project_dir in self.watch_path.iterdir():
            if not project_dir.is_dir():
                continue

            for jsonl_file in project_dir.glob("*.jsonl"):
                if jsonl_file.name == "sessions-index.json":
                    continue

                try:
                    size = jsonl_file.stat().st_size
                    self._handler._positions[str(jsonl_file)] = size
                except OSError:
                    pass

    def _on_activity(self, event: LiveActivityEvent) -> None:
        """Handle activity event from handler."""
        self._notify(event)
