"""Conflict detection for simultaneous file access."""

import threading
from collections import defaultdict
from collections.abc import Callable
from datetime import UTC, datetime

from cwhap.models.agent import ConflictEvent, LiveActivityEvent


class ConflictDetector:
    """Detects when multiple agents access the same file."""

    def __init__(self, conflict_window_seconds: float = 5.0) -> None:
        self.conflict_window = conflict_window_seconds
        # Track: file_path -> [(session_id, timestamp, operation)]
        self._file_access: dict[str, list[tuple[str, datetime, str]]] = defaultdict(list)
        self._callbacks: list[Callable[[ConflictEvent], None]] = []
        self._lock = threading.Lock()
        self._active_conflicts: dict[str, ConflictEvent] = {}  # file_path -> conflict

    def add_callback(self, callback: Callable[[ConflictEvent], None]) -> None:
        """Add a callback for conflict events."""
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[ConflictEvent], None]) -> None:
        """Remove a callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def record_activity(self, event: LiveActivityEvent) -> None:
        """Record file access and check for conflicts."""
        if not event.file_path or not event.operation:
            return

        # Skip non-file operations
        if event.operation not in ("read", "write", "edit"):
            return

        now = datetime.now(UTC)

        with self._lock:
            # Clean old entries
            self._cleanup_old_entries(event.file_path, now)

            # Check for conflicts
            conflicts = self._check_conflicts(
                event.file_path, event.session_id, event.operation, now
            )

            # Record this access
            self._file_access[event.file_path].append(
                (event.session_id, now, event.operation)
            )

        # Emit conflict events
        for conflict in conflicts:
            self._active_conflicts[conflict.file_path] = conflict
            self._emit_conflict(conflict)

    def get_active_conflicts(self) -> list[ConflictEvent]:
        """Get list of currently active conflicts."""
        now = datetime.now(UTC)
        active = []

        with self._lock:
            expired = []
            for file_path, conflict in self._active_conflicts.items():
                age = (now - conflict.timestamp).total_seconds()
                if age < self.conflict_window * 2:  # Keep visible a bit longer
                    active.append(conflict)
                else:
                    expired.append(file_path)

            for fp in expired:
                del self._active_conflicts[fp]

        return active

    def _cleanup_old_entries(self, file_path: str, now: datetime) -> None:
        """Remove entries older than the conflict window."""
        if file_path not in self._file_access:
            return

        entries = self._file_access[file_path]
        cutoff = self.conflict_window

        self._file_access[file_path] = [
            (sid, ts, op)
            for sid, ts, op in entries
            if (now - ts).total_seconds() < cutoff
        ]

    def _check_conflicts(
        self,
        file_path: str,
        session_id: str,
        operation: str,
        now: datetime,
    ) -> list[ConflictEvent]:
        """Check if this access conflicts with recent accesses."""
        conflicts: list[ConflictEvent] = []
        recent = self._file_access.get(file_path, [])

        # Find other sessions accessing this file
        other_sessions: dict[str, str] = {}  # session_id -> operation
        for other_id, ts, other_op in recent:
            if other_id != session_id:
                other_sessions[other_id] = other_op

        if not other_sessions:
            return conflicts

        # Check for critical conflicts: multiple edits
        if operation in ("write", "edit"):
            editing_others = [
                sid for sid, op in other_sessions.items() if op in ("write", "edit")
            ]
            if editing_others:
                conflicts.append(
                    ConflictEvent(
                        file_path=file_path,
                        agents=[session_id] + editing_others,
                        severity="critical",
                        conflict_type="simultaneous_edit",
                        timestamp=now,
                    )
                )
            else:
                # Warning: edit while others read
                reading_others = [
                    sid for sid, op in other_sessions.items() if op == "read"
                ]
                if reading_others:
                    conflicts.append(
                        ConflictEvent(
                            file_path=file_path,
                            agents=[session_id] + reading_others,
                            severity="warning",
                            conflict_type="read_write_race",
                            timestamp=now,
                        )
                    )

        return conflicts

    def _emit_conflict(self, conflict: ConflictEvent) -> None:
        """Notify all callbacks of a conflict."""
        for callback in self._callbacks:
            try:
                callback(conflict)
            except Exception:
                pass
