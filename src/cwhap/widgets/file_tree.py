"""File tree widget showing agent collaboration."""

from collections import defaultdict
from datetime import UTC, datetime

from rich.markup import escape
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widget import Widget
from textual.widgets import Static

from cwhap.models.agent import AGENT_COLORS, LiveActivityEvent


class FileTree(Widget):
    """Shows files and which agents are accessing them."""

    DEFAULT_CSS = """
    FileTree {
        height: 100%;
        border: solid $accent;
        padding: 1;
    }

    FileTree > .tree-title {
        text-style: bold;
        padding-bottom: 1;
    }

    FileTree .tree-item {
        height: auto;
    }

    FileTree .tree-conflict {
        background: $error 20%;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._file_agents: dict[str, set[str]] = defaultdict(set)
        self._agent_colors: dict[str, int] = {}
        self._last_access: dict[str, datetime] = {}
        self._decay_time: float = 30.0

    def compose(self) -> ComposeResult:
        yield Static("[bold]Agent File Tree[/bold]", classes="tree-title")
        yield VerticalScroll(id="tree-scroll")

    def on_mount(self) -> None:
        """Start refresh timer."""
        self.set_interval(2.0, self._decay_and_refresh)  # type: ignore

    def record_access(
        self, event: LiveActivityEvent, agent_color_index: int
    ) -> None:
        """Record file access by an agent."""
        if not event.file_path:
            return

        # Skip patterns and bash commands for tree view
        if event.file_path.startswith(("pattern:", "bash:")):
            return

        self._file_agents[event.file_path].add(event.session_id)
        self._agent_colors[event.session_id] = agent_color_index
        self._last_access[event.file_path] = datetime.now(UTC)

    def _decay_and_refresh(self) -> None:
        """Remove old entries and refresh display."""
        now = datetime.now(UTC)
        expired = []

        for file_path, last_time in self._last_access.items():
            age = (now - last_time).total_seconds()
            if age > self._decay_time:
                expired.append(file_path)

        for file_path in expired:
            del self._file_agents[file_path]
            del self._last_access[file_path]

        self._refresh_display()

    def _refresh_display(self) -> None:
        """Refresh the tree display."""
        try:
            scroll = self.query_one("#tree-scroll", VerticalScroll)
        except Exception:
            return

        scroll.remove_children()

        if not self._file_agents:
            scroll.mount(Static("[dim]No file activity[/dim]"))
            return

        # Group files by number of agents accessing them
        conflicts = []
        solo = []

        for file_path, agents in self._file_agents.items():
            if len(agents) > 1:
                conflicts.append((file_path, agents))
            elif len(agents) == 1:
                solo.append((file_path, agents))

        # Show conflicts first (most important)
        if conflicts:
            scroll.mount(Static("[bold red]! Overlapping Access[/bold red]"))
            for file_path, agents in sorted(conflicts, key=lambda x: len(x[1]), reverse=True):
                self._add_file_item(scroll, file_path, agents, is_conflict=True)
            scroll.mount(Static(""))

        # Show solo files
        if solo:
            scroll.mount(Static("[bold]Independent Work[/bold]"))
            for file_path, agents in sorted(solo):
                self._add_file_item(scroll, file_path, agents, is_conflict=False)

    def _add_file_item(
        self, container: VerticalScroll, file_path: str, agents: set[str], is_conflict: bool
    ) -> None:
        """Add a file item to the display."""
        # Shorten file path
        parts = file_path.split("/")
        if len(parts) > 3:
            short_path = f".../{'/'.join(parts[-2:])}"
        else:
            short_path = file_path

        # Build agent badges
        agent_badges = []
        for session_id in sorted(agents):
            short_id = session_id[:4]
            color_idx = self._agent_colors.get(session_id, 0)
            color = AGENT_COLORS[color_idx % len(AGENT_COLORS)]
            agent_badges.append(f"[{color}]*{short_id}[/{color}]")

        badges_str = " ".join(agent_badges)

        if is_conflict:
            text = f"  ├─ {escape(short_path)}\n     └─ {badges_str}"
            css_class = "tree-item tree-conflict"
        else:
            text = f"  ├─ {escape(short_path)} {badges_str}"
            css_class = "tree-item"

        container.mount(Static(text, classes=css_class))
