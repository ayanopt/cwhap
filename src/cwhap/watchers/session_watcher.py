"""Session file watcher using watchdog."""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from cwhap.watchers.base import BaseWatcher

# Default Claude Code data directory
CLAUDE_PROJECTS_DIR = Path.home() / ".claude" / "projects"


@dataclass
class SessionEvent:
    """Event representing a change to a session file."""

    event_type: Literal["created", "modified", "deleted"]
    session_id: str
    project_path: str
    file_path: Path


class SessionFileHandler(FileSystemEventHandler):
    """Handler for session file changes."""

    def __init__(self, callback: Callable[[SessionEvent], None]) -> None:
        super().__init__()
        self.callback = callback

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation."""
        self._process_event(event, "created")

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification."""
        self._process_event(event, "modified")

    def on_deleted(self, event: FileSystemEvent) -> None:
        """Handle file deletion."""
        self._process_event(event, "deleted")

    def _process_event(
        self, event: FileSystemEvent, event_type: Literal["created", "modified", "deleted"]
    ) -> None:
        """Process a file system event."""
        if event.is_directory:
            return

        path = Path(event.src_path)

        # Only care about JSONL session files
        if path.suffix != ".jsonl":
            return

        # Skip sessions-index.json (it's JSON, not JSONL)
        if path.name == "sessions-index.json":
            return

        # Extract session ID from filename
        session_id = path.stem

        # Extract project path from parent directory name
        project_dir = path.parent
        project_path = project_dir.name.replace("-", "/")

        session_event = SessionEvent(
            event_type=event_type,
            session_id=session_id,
            project_path=project_path,
            file_path=path,
        )

        self.callback(session_event)


class SessionWatcher(BaseWatcher):
    """Watches Claude Code session files for changes."""

    def __init__(self, watch_path: Path | None = None) -> None:
        super().__init__()
        self.watch_path = watch_path or CLAUDE_PROJECTS_DIR
        self._observer: Observer | None = None  # type: ignore[valid-type]

    def start(self) -> None:
        """Start watching session files."""
        if self._running:
            return

        if not self.watch_path.exists():
            return

        self._observer = Observer()
        handler = SessionFileHandler(self._on_session_event)

        # Watch the projects directory recursively
        self._observer.schedule(handler, str(self.watch_path), recursive=True)  # type: ignore[no-untyped-call]
        self._observer.start()  # type: ignore[no-untyped-call]
        self._running = True

    def stop(self) -> None:
        """Stop watching."""
        if not self._running or not self._observer:
            return

        self._observer.stop()  # type: ignore[attr-defined]
        self._observer.join(timeout=5)  # type: ignore[attr-defined]
        self._observer = None
        self._running = False

    def _on_session_event(self, event: SessionEvent) -> None:
        """Handle a session event."""
        self._notify(event)


class IndexWatcher(BaseWatcher):
    """Watches sessions-index.json files for changes."""

    def __init__(self, watch_path: Path | None = None) -> None:
        super().__init__()
        self.watch_path = watch_path or CLAUDE_PROJECTS_DIR
        self._observer: Observer | None = None  # type: ignore[valid-type]

    def start(self) -> None:
        """Start watching index files."""
        if self._running:
            return

        if not self.watch_path.exists():
            return

        self._observer = Observer()
        handler = IndexFileHandler(self._on_index_changed)

        self._observer.schedule(handler, str(self.watch_path), recursive=True)  # type: ignore[no-untyped-call]
        self._observer.start()  # type: ignore[no-untyped-call]
        self._running = True

    def stop(self) -> None:
        """Stop watching."""
        if not self._running or not self._observer:
            return

        self._observer.stop()  # type: ignore[attr-defined]
        self._observer.join(timeout=5)  # type: ignore[attr-defined]
        self._observer = None
        self._running = False

    def _on_index_changed(self, project_path: str) -> None:
        """Handle an index change."""
        self._notify(project_path)


class IndexFileHandler(FileSystemEventHandler):
    """Handler for sessions-index.json changes."""

    def __init__(self, callback: Callable[[str], None]) -> None:
        super().__init__()
        self.callback = callback

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification."""
        if event.is_directory:
            return

        path = Path(event.src_path)
        if path.name == "sessions-index.json":
            project_path = path.parent.name.replace("-", "/")
            self.callback(project_path)
