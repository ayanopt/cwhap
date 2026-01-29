"""File activity heatmap widget."""

from collections import defaultdict
from datetime import UTC, datetime

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widget import Widget
from textual.widgets import Static

from cwhap.models.agent import LiveActivityEvent


class ActivityHeatmap(Widget):
    """Enhanced file activity heatmap with detailed metrics."""

    # 10-level heat intensity
    HEAT_CHARS = " .:-=+*#%@"

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

    ActivityHeatmap .heat-row {
        height: auto;
    }

    ActivityHeatmap .heat-legend {
        color: $text-muted;
        height: 1;
    }
    """

    # Track file access counts
    _access_counts: dict[str, int] = {}
    _access_by_op: dict[str, dict[str, int]] = {}  # file -> {op -> count}
    _decay_time: float = 30.0  # Seconds before access fades

    def __init__(self, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(**kwargs)
        self._access_counts = defaultdict(int)
        self._access_by_op = defaultdict(lambda: defaultdict(int))
        self._access_times: dict[str, datetime] = {}

    def compose(self) -> ComposeResult:
        yield Static(
            "[bold]File Activity Analysis[/bold] [dim](weighted: write=3x, edit=2x, read=1x)[/dim]",
            classes="heatmap-title",
        )
        yield VerticalScroll(id="heatmap-scroll")

    def on_mount(self) -> None:
        """Start decay timer."""
        self.set_interval(2.0, self._decay_and_refresh)

    def record_access(self, event: LiveActivityEvent) -> None:
        """Record a file access event with operation tracking."""
        if not event.file_path:
            return

        # Track by operation type
        op = event.operation or "unknown"
        self._access_by_op[event.file_path][op] += 1

        # Weight by operation type for overall score
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
            if path in self._access_by_op:
                del self._access_by_op[path]

        self._refresh_display()

    def _refresh_display(self) -> None:
        """Refresh the heatmap display with detailed metrics."""
        try:
            scroll = self.query_one("#heatmap-scroll", VerticalScroll)
        except Exception:
            return

        scroll.remove_children()

        if not self._access_counts:
            scroll.mount(Static("[dim]No recent activity[/dim]"))
            return

        # Add legend
        legend = (
            "[dim]Legend: Heat[HOT/HIGH/MED/LOW] | "
            "Count (%) | R:read W:write E:edit | Age[/dim]"
        )
        scroll.mount(Static(legend, classes="heat-legend"))
        scroll.mount(Static(""))

        # Sort by access count, most active first
        sorted_files = sorted(
            self._access_counts.items(), key=lambda x: x[1], reverse=True
        )[:15]  # Top 15 files

        total_activity = sum(c for _, c in sorted_files)
        max_count = max(c for _, c in sorted_files) if sorted_files else 1
        now = datetime.now(UTC)

        # Create detailed rows
        for file_path, count in sorted_files:
            # Shorten filename intelligently
            if file_path.startswith("pattern:"):
                short_name = f"[?] {file_path.replace('pattern:', '')[:20]}"
            elif file_path.startswith("bash:"):
                short_name = f"[$] {file_path.replace('bash:', '')[:20]}"
            else:
                parts = file_path.split("/")
                filename = parts[-1] if parts else file_path
                if len(parts) > 1:
                    parent = parts[-2]
                    short_name = f"{parent}/{filename}"[:24]
                else:
                    short_name = filename[:24]

            short_name = f"{short_name:24}"

            # Calculate heat level (0-9)
            heat_ratio = count / max_count
            heat_level = int(heat_ratio * 9)
            heat_char = self.HEAT_CHARS[heat_level]

            # Intensity category
            if heat_ratio > 0.75:
                intensity = "[red]HOT [/red]"
                bar_color = "red"
            elif heat_ratio > 0.5:
                intensity = "[yellow]HIGH[/yellow]"
                bar_color = "yellow"
            elif heat_ratio > 0.25:
                intensity = "[cyan]MED [/cyan]"
                bar_color = "cyan"
            else:
                intensity = "[dim]LOW [/dim]"
                bar_color = "white"

            # Heat bar (10 chars)
            bar_length = max(1, int(heat_ratio * 10))
            heat_bar = heat_char * bar_length
            heat_bar = f"[{bar_color}]{heat_bar:10}[/{bar_color}]"

            # Percentage
            percentage = (count / total_activity * 100) if total_activity > 0 else 0

            # Operation breakdown
            ops = self._access_by_op.get(file_path, {})
            reads = ops.get("read", 0)
            writes = ops.get("write", 0)
            edits = ops.get("edit", 0)
            op_str = f"R:{reads:2} W:{writes:2} E:{edits:2}"

            # Time since last access
            last_time = self._access_times.get(file_path)
            if last_time:
                age_seconds = (now - last_time).total_seconds()
                if age_seconds < 5:
                    age = "[green]<5s[/green]"
                elif age_seconds < 15:
                    age = "[yellow]<15s[/yellow]"
                else:
                    age = f"[dim]{int(age_seconds)}s[/dim]"
            else:
                age = "[dim]?[/dim]"

            # Format: filename | intensity | heat bar | count (%) | ops | age
            line = (
                f"{short_name} {intensity} {heat_bar} "
                f"{count:4} ({percentage:4.1f}%) | {op_str} | {age}"
            )
            scroll.mount(Static(line, classes="heat-row"))
