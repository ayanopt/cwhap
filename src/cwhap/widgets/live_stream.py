"""Live activity stream widget."""

from collections import deque

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static

from cwhap.models.agent import LiveActivityEvent


class LiveStream(Widget):
    """Real-time activity stream showing agent operations."""

    DEFAULT_CSS = """
    LiveStream {
        height: 100%;
        border: solid $primary;
        padding: 1;
    }

    LiveStream > .stream-title {
        text-style: bold;
        padding-bottom: 1;
    }

    LiveStream .stream-item {
        height: auto;
    }

    LiveStream .stream-item.--read {
        color: $text;
    }

    LiveStream .stream-item.--write {
        color: $warning;
    }

    LiveStream .stream-item.--edit {
        color: $success;
    }

    LiveStream .stream-item.--error {
        color: $error;
    }
    """

    events: reactive[deque[LiveActivityEvent]] = reactive(
        lambda: deque(maxlen=50), init=False
    )

    def compose(self) -> ComposeResult:
        yield Static("[bold]Live Activity[/bold]", classes="stream-title")
        yield VerticalScroll(id="stream-scroll")

    def add_event(self, event: LiveActivityEvent) -> None:
        """Add a new event to the stream."""
        new_events = deque(self.events, maxlen=50)
        new_events.appendleft(event)  # Most recent first
        self.events = new_events
        self._refresh_display()

    def _refresh_display(self) -> None:
        """Refresh the stream display."""
        try:
            scroll = self.query_one("#stream-scroll", VerticalScroll)
        except Exception:
            return

        scroll.remove_children()

        if not self.events:
            scroll.mount(Static("[dim]Waiting for activity...[/dim]"))
            return

        for event in list(self.events)[:30]:  # Show last 30
            text = self._format_event(event)
            css_class = f"stream-item --{event.operation or 'default'}"
            scroll.mount(Static(text, classes=css_class))

    def _format_event(self, event: LiveActivityEvent) -> str:
        """Format an event for display."""
        time_str = event.timestamp.strftime("%H:%M:%S")
        session = event.session_id[:4]

        # Color based on operation
        color = event.color

        if event.tool_name and event.file_path:
            # Shorten file path
            parts = event.file_path.split("/")
            if len(parts) > 1:
                short_file = parts[-1]
            else:
                short_file = event.file_path

            if len(short_file) > 20:
                short_file = short_file[:17] + "..."

            return (
                f"[dim]{time_str}[/dim] "
                f"[[cyan]{session}[/cyan]] "
                f"[{color}]{event.tool_name}[/{color}] "
                f"{short_file}"
            )
        elif event.tool_name:
            return (
                f"[dim]{time_str}[/dim] "
                f"[[cyan]{session}[/cyan]] "
                f"[{color}]{event.tool_name}[/{color}]"
            )
        else:
            return (
                f"[dim]{time_str}[/dim] "
                f"[[cyan]{session}[/cyan]] "
                f"[dim]{event.event_type}[/dim]"
            )
