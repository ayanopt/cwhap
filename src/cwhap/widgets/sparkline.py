"""Activity sparkline widget for visualizing activity over time."""

from collections import deque
from datetime import datetime, timezone

from textual.reactive import reactive
from textual.widget import Widget


class ActivitySparkline(Widget):
    """Sparkline showing activity intensity over time."""

    SPARK_CHARS = "▁▂▃▄▅▆▇█"

    DEFAULT_CSS = """
    ActivitySparkline {
        height: 3;
        padding: 0 1;
        background: $surface;
        border-top: solid $primary-darken-2;
    }
    """

    # Activity counts per second for the last 60 seconds
    history: reactive[deque[int]] = reactive(lambda: deque([0] * 60, maxlen=60), init=False)
    ops_per_second: reactive[float] = reactive(0.0)
    conflict_count: reactive[int] = reactive(0)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._last_tick = datetime.now(timezone.utc)
        self._current_count = 0

    def on_mount(self) -> None:
        """Start the tick timer."""
        self.set_interval(1.0, self._tick)

    def _tick(self) -> None:
        """Called every second to update the sparkline."""
        # Push current count and reset
        new_history = deque(self.history, maxlen=60)
        new_history.append(self._current_count)
        self.history = new_history

        # Calculate ops/sec (rolling average over last 10 seconds)
        recent = list(self.history)[-10:]
        self.ops_per_second = sum(recent) / len(recent) if recent else 0

        self._current_count = 0
        self.refresh()

    def record_activity(self) -> None:
        """Record an activity event."""
        self._current_count += 1

    def render(self) -> str:
        """Render the sparkline."""
        if not self.history:
            return "[dim]No activity[/dim]"

        max_val = max(self.history) or 1

        # Build sparkline characters
        chars = []
        for val in self.history:
            if max_val > 0:
                idx = min(int(val / max_val * 7), 7)
            else:
                idx = 0
            chars.append(self.SPARK_CHARS[idx])

        sparkline = "".join(chars)

        # Color based on activity level
        if self.ops_per_second > 5:
            color = "green"
        elif self.ops_per_second > 1:
            color = "cyan"
        else:
            color = "dim"

        conflict_text = ""
        if self.conflict_count > 0:
            conflict_text = f"  [red bold]Conflicts: {self.conflict_count}[/red bold]"

        return (
            f"Activity [{color}]{sparkline}[/{color}]  "
            f"Ops/sec: [cyan]{self.ops_per_second:.1f}[/cyan]"
            f"{conflict_text}"
        )
