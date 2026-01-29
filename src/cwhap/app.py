"""Main CWHAP Textual application - Live Monitor."""

import logging
import threading
import time
from pathlib import Path
from typing import ClassVar

from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Container, HorizontalScroll
from textual.reactive import reactive
from textual.widgets import Footer, Header, Static

from cwhap.models.agent import ConflictEvent, LiveActivityEvent, LiveAgent
from cwhap.monitors.conflict_detector import ConflictDetector
from cwhap.parsers.session_parser import PROJECTS_DIR, load_sessions_index
from cwhap.watchers.session_watcher import IndexWatcher
from cwhap.watchers.tail_watcher import TailWatcher
from cwhap.widgets.agent_card import AgentCard
from cwhap.widgets.conflict_alert import ConflictAlert
from cwhap.widgets.file_tree import FileTree
from cwhap.widgets.heatmap import ActivityHeatmap
from cwhap.widgets.live_stream import LiveStream
from cwhap.widgets.sparkline import ActivitySparkline
from cwhap.widgets.stats_bar import StatsBar

# Set up logging
logger = logging.getLogger(__name__)


class CwhapApp(App[None]):
    """CWHAP - Live Monitor for Claude Code agents."""

    TITLE = "CWHAP - Live Monitor"
    CSS_PATH = Path(__file__).parent / "styles" / "live_monitor.tcss"

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("d", "toggle_dark", "Dark/Light"),
        Binding("c", "focus_conflicts", "Conflicts"),
    ]

    dark: reactive[bool] = reactive(True)

    def __init__(self, simple_mode: bool = False) -> None:
        super().__init__()
        self.simple_mode = simple_mode
        self._agents: dict[str, LiveAgent] = {}
        self._agent_cards: dict[str, AgentCard] = {}
        self._tail_watcher: TailWatcher | None = None
        self._index_watcher: IndexWatcher | None = None
        self._conflict_detector = ConflictDetector(conflict_window_seconds=5.0)
        self._next_color_index = 0  # For assigning unique colors to agents
        self._color_lock = threading.Lock()  # Thread-safe color assignment

    def compose(self) -> ComposeResult:
        """Create the live monitor layout."""
        yield Header()

        # Stats summary bar
        yield StatsBar(id="stats-bar")

        # Conflict alert banner (hidden by default)
        yield ConflictAlert(id="conflict-alert")

        # Active agents section
        yield Static("[bold]Active Agents[/bold]", id="agents-title")
        yield HorizontalScroll(
            Static("[dim]Scanning for active agents...[/dim]", id="no-agents"),
            id="agents-container",
        )

        # Main content layout depends on mode
        if self.simple_mode:
            # Simple mode: just stream
            yield Container(
                LiveStream(id="live-stream"),
                id="main-content",
            )
        else:
            # Full mode: stream + heatmap + file tree
            yield Container(
                LiveStream(id="live-stream"),
                FileTree(id="file-tree"),
                ActivityHeatmap(id="heatmap"),
                id="main-content",
            )

        # Activity sparkline footer
        yield ActivitySparkline(id="sparkline")

        yield Footer()

    async def on_mount(self) -> None:
        """Initialize watchers and scan for active sessions."""
        # Set up conflict detector callback
        self._conflict_detector.add_callback(self._on_conflict)

        # Start watchers
        self._start_watchers()

        # Initial scan for active sessions
        self._scan_active_sessions()

        # Start periodic refresh for agent status
        self.set_interval(2.0, self._refresh_agent_status)

    def _start_watchers(self) -> None:
        """Start file system watchers."""
        # Tail watcher for live activity
        self._tail_watcher = TailWatcher()
        self._tail_watcher.add_callback(self._on_activity)
        self._tail_watcher.start()

        # Index watcher for new sessions
        self._index_watcher = IndexWatcher()
        self._index_watcher.add_callback(self._on_index_changed)
        self._index_watcher.start()

    def _stop_watchers(self) -> None:
        """Stop file system watchers."""
        if self._tail_watcher:
            self._tail_watcher.stop()
            self._tail_watcher = None

        if self._index_watcher:
            self._index_watcher.stop()
            self._index_watcher = None

    def _scan_active_sessions(self) -> None:
        """Scan for currently active sessions."""
        now = time.time()
        active_threshold = 60  # Consider sessions active if modified within 60s

        for project_dir in PROJECTS_DIR.iterdir():
            if not project_dir.is_dir() or project_dir.name.startswith("."):
                continue

            index = load_sessions_index(project_dir)
            if not index:
                continue

            for entry in index.entries:
                # Check if session file was recently modified
                session_file = project_dir / f"{entry.session_id}.jsonl"
                if not session_file.exists():
                    continue

                try:
                    mtime = session_file.stat().st_mtime
                    age = now - mtime
                except OSError:
                    continue

                if age < active_threshold:
                    # This session is active
                    if entry.session_id not in self._agents:
                        with self._color_lock:
                            color_idx = self._next_color_index
                            self._next_color_index += 1
                        agent = LiveAgent(
                            session_id=entry.session_id,
                            project_path=entry.project_path,
                            status="active" if age < 10 else "idle",
                            message_count=entry.message_count,
                            color_index=color_idx,
                        )
                        self._add_agent(agent)
                    else:
                        # Update existing agent
                        agent = self._agents[entry.session_id]
                        agent.message_count = entry.message_count
                        if age < 10:
                            agent.status = "active"

        self._update_agents_display()

    def _add_agent(self, agent: LiveAgent) -> None:
        """Add a new agent to tracking."""
        self._agents[agent.session_id] = agent

        # Create card widget
        card = AgentCard(agent, simple_mode=self.simple_mode)
        self._agent_cards[agent.session_id] = card

    def _update_agents_display(self) -> None:
        """Update the agents container display."""
        try:
            container = self.query_one("#agents-container", HorizontalScroll)
        except Exception:
            return

        # Remove placeholder if it exists
        try:
            placeholder = self.query_one("#no-agents", Static)
            placeholder.remove()
        except Exception:
            pass

        # Remove old cards not in agents
        for session_id in list(self._agent_cards.keys()):
            if session_id not in self._agents:
                card = self._agent_cards.pop(session_id)
                try:
                    card.remove()
                except Exception:
                    pass

        # Add/update cards
        for session_id, agent in self._agents.items():
            if session_id not in self._agent_cards:
                card = AgentCard(agent, simple_mode=self.simple_mode)
                self._agent_cards[session_id] = card
                container.mount(card)
            else:
                # Update existing card
                card = self._agent_cards[session_id]
                card.agent = agent

        # Show placeholder if no agents (only if not already present)
        if not self._agents:
            try:
                self.query_one("#no-agents", Static)
            except Exception:
                container.mount(
                    Static("[dim]No active agents detected[/dim]", id="no-agents")
                )

    def _refresh_agent_status(self) -> None:
        """Periodically refresh agent status."""
        inactive_threshold = 30  # Mark idle after 30s of no activity

        for agent in self._agents.values():
            seconds_idle = agent.seconds_since_activity()

            if seconds_idle > inactive_threshold:
                agent.status = "idle"
                agent.current_operation = None
            elif seconds_idle > 5:
                agent.status = "thinking"

        # Update conflict status on cards
        conflicts = self._conflict_detector.get_active_conflicts()
        conflict_sessions = set()
        for c in conflicts:
            conflict_sessions.update(c.agents)

        for session_id, card in self._agent_cards.items():
            card.in_conflict = session_id in conflict_sessions
            card._update_display()

        # Update conflict alert
        try:
            alert = self.query_one("#conflict-alert", ConflictAlert)
            alert.conflicts = conflicts
        except Exception:
            pass

        # Update sparkline conflict count
        try:
            sparkline = self.query_one("#sparkline", ActivitySparkline)
            sparkline.conflict_count = len([c for c in conflicts if c.severity == "critical"])
        except Exception:
            pass

        # Update stats bar
        self._update_stats_bar()

    def _on_activity(self, event: LiveActivityEvent) -> None:
        """Handle live activity event from tail watcher."""
        self.call_from_thread(self._handle_activity, event)

    def _handle_activity(self, event: LiveActivityEvent) -> None:
        """Process activity event in main thread."""
        session_id = event.session_id

        # Update or create agent
        if session_id not in self._agents:
            # New session detected - thread-safe color assignment
            with self._color_lock:
                color_idx = self._next_color_index
                self._next_color_index += 1
            new_agent = LiveAgent(
                session_id=session_id,
                project_path="",  # Will be updated from index
                status="active",
                color_index=color_idx,
            )
            self._add_agent(new_agent)
            self._update_agents_display()

        agent = self._agents[session_id]
        agent.status = "active"
        agent.last_activity = event.timestamp

        if event.tool_name:
            agent.tool_count += 1
            if event.file_path:
                # Track file access
                if event.file_path not in agent.files_accessed:
                    agent.files_accessed.append(event.file_path)

                # Shorten file path for display
                parts = event.file_path.split('/')
                short_file = parts[-1] if parts else event.file_path
                agent.current_operation = f"{event.tool_name} {short_file}"
                agent.current_file = event.file_path
            else:
                agent.current_operation = event.tool_name

        if event.event_type == "message":
            agent.message_count += 1

        # Record for conflict detection
        self._conflict_detector.record_activity(event)

        # Update live stream
        try:
            stream = self.query_one("#live-stream", LiveStream)
            stream.add_event(event, agent.color_index)
        except Exception:
            pass

        # Update heatmap
        try:
            heatmap = self.query_one("#heatmap", ActivityHeatmap)
            heatmap.record_access(event)
        except Exception:
            pass

        # Update file tree
        try:
            tree = self.query_one("#file-tree", FileTree)
            tree.record_access(event, agent.color_index)
        except Exception:
            pass

        # Update sparkline
        try:
            sparkline = self.query_one("#sparkline", ActivitySparkline)
            sparkline.record_activity()
        except Exception:
            pass

        # Update agent card with activity
        if session_id in self._agent_cards:
            card = self._agent_cards[session_id]
            card.agent = agent
            card.record_activity()  # Track per-agent activity

    def _on_conflict(self, conflict: ConflictEvent) -> None:
        """Handle conflict event."""
        self.call_from_thread(self._handle_conflict, conflict)

    def _handle_conflict(self, conflict: ConflictEvent) -> None:
        """Process conflict event in main thread."""
        # Update conflict alert
        try:
            alert = self.query_one("#conflict-alert", ConflictAlert)
            current = list(alert.conflicts)
            current.append(conflict)
            alert.conflicts = current[-10:]  # Keep last 10
        except Exception:
            pass

        # Play bell for critical conflicts
        if conflict.severity == "critical":
            self.bell()

    def _on_index_changed(self, project_path: str) -> None:
        """Handle index file change."""
        self.call_from_thread(self._scan_active_sessions)

    def action_refresh(self) -> None:
        """Manual refresh."""
        self._scan_active_sessions()

    def action_toggle_dark(self) -> None:
        """Toggle dark mode."""
        self.dark = not self.dark

    def action_focus_conflicts(self) -> None:
        """Focus on conflict alert."""
        conflicts = self._conflict_detector.get_active_conflicts()
        if conflicts:
            c = conflicts[0]
            self.notify(
                f"File: {c.file_path}\n"
                f"Agents: {c.short_agents}\n"
                f"Type: {c.conflict_type}",
                title=f"{'CRITICAL' if c.severity == 'critical' else 'Warning'}: Conflict",
                severity="error" if c.severity == "critical" else "warning",
            )
        else:
            self.notify("No active conflicts", title="Conflicts")

    def _update_stats_bar(self) -> None:
        """Update the stats bar with current metrics."""
        try:
            stats_bar = self.query_one("#stats-bar", StatsBar)
            total_messages = sum(a.message_count for a in self._agents.values())
            total_tools = sum(a.tool_count for a in self._agents.values())
            all_files: set[str] = set()
            for a in self._agents.values():
                all_files.update(a.files_accessed)
            active_count = sum(1 for a in self._agents.values() if a.status == "active")

            stats_bar.update_stats(
                agents=len(self._agents),
                messages=total_messages,
                tools=total_tools,
                files=len(all_files),
                active=active_count,
            )
        except Exception:
            pass

    async def action_quit(self) -> None:
        """Quit the application."""
        self._stop_watchers()
        self.exit()
