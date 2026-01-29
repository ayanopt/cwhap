"""File activity heatmap widget."""

from collections import defaultdict
from datetime import UTC, datetime

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widget import Widget
from textual.widgets import Static

from cwhap.models.agent import LiveActivityEvent


class ActivityHeatmap(Widget):
    """Visual heatmap grid of file access activity."""

    HEAT_CHARS = "░▒▓█"

    DEFAULT_CSS = """
    ActivityHeatmap {
        height: 100%;
        border: solid $secondary;
        padding: 1;
    }

    ActivityHeatmap > .heatmap-title {
        text-style: bold;
        padding-bottom: 1;
    }

    ActivityHeatmap .heat-grid {
        height: auto;
    }

    ActivityHeatmap .heat-cell {
        height: 2;
        padding: 0 1;
    }
    """

    # Track file access counts
    _access_counts: dict[str, int] = {}
    _decay_time: float = 30.0  # Seconds before access fades

    def __init__(self, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__()
        self._access_counts = defaultdict(int)
        self._access_times: dict[str, datetime] = {}

    def compose(self) -> ComposeResult:
        yield Static(
            "[bold]File Activity Heatmap[/bold] [dim](30s window)[/dim]",
            classes="heatmap-title",
        )
        yield VerticalScroll(id="heatmap-scroll")

    def on_mount(self) -> None:
        """Start decay timer."""
        self.set_interval(2.0, self._decay_and_refresh)

    def record_access(self, event: LiveActivityEvent) -> None:
        """Record a file access event."""
        if not event.file_path:
            return

        # Weight by operation type
        weight = 1
        if event.operation == "write":
            weight = 3
        elif event.operation == "edit":
            weight = 2

        self._access_counts[event.file_path] += weight
        self._access_times[event.file_path] = datetime.now(UTC)

    def _decay_and_refresh(self) -> None:
        """Decay old entries and refresh display."""
        now = datetime.now(UTC)
        expired = []

        for path, last_time in self._access_times.items():
            age = (now - last_time).total_seconds()
            if age > self._decay_time:
                expired.append(path)
            elif age > self._decay_time / 2:
                # Reduce count for older entries
                self._access_counts[path] = max(1, self._access_counts[path] - 1)

        for path in expired:
            del self._access_counts[path]
            del self._access_times[path]

        self._refresh_display()

    def _refresh_display(self) -> None:
        """Refresh the heatmap display as a grid."""
        try:
            scroll = self.query_one("#heatmap-scroll", VerticalScroll)
        except Exception:
            return

        scroll.remove_children()

        if not self._access_counts:
            scroll.mount(Static("[dim]No recent activity[/dim]"))
            return

        # Sort by access count, most active first
        sorted_files = sorted(
            self._access_counts.items(), key=lambda x: x[1], reverse=True
        )[:20]  # Top 20 files

        max_count = max(c for _, c in sorted_files) if sorted_files else 1

        # Create grid rows (4 cells per row for better visibility)
        cells_per_row = 4
        for i in range(0, len(sorted_files), cells_per_row):
            row_files = sorted_files[i:i + cells_per_row]
            row_text_parts = []

            for file_path, count in row_files:
                # Shorten filename (not full path)
                if file_path.startswith("pattern:"):
                    short_name = f"?:{file_path.replace('pattern:', '')[:8]}"
                elif file_path.startswith("bash:"):
                    short_name = f"$:{file_path.replace('bash:', '')[:8]}"
                else:
                    parts = file_path.split("/")
                    filename = parts[-1] if parts else file_path
                    short_name = filename[:12] if len(filename) <= 12 else filename[:9] + "..."

                # Determine heat level and color
                heat_ratio = count / max_count
                if heat_ratio > 0.75:
                    color = "red"
                    char = self.HEAT_CHARS[3]
                elif heat_ratio > 0.5:
                    color = "yellow"
                    char = self.HEAT_CHARS[2]
                elif heat_ratio > 0.25:
                    color = "cyan"
                    char = self.HEAT_CHARS[1]
                else:
                    color = "white"
                    char = self.HEAT_CHARS[0]

                # Create heat visualization block
                block = char * 4  # 4 chars wide
                cell = f"[{color}]{block}[/{color}] {short_name:12} ({count})"
                row_text_parts.append(cell)

            # Pad row if needed
            while len(row_text_parts) < cells_per_row:
                row_text_parts.append(" " * 25)

            row_text = "".join(row_text_parts)
            scroll.mount(Static(row_text, classes="heat-cell"))
