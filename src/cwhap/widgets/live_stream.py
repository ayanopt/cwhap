"""Live activity stream widget."""

from collections import deque

from rich.markup import escape
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static

from cwhap.models.agent import AGENT_COLORS, LiveActivityEvent

# Operation type icons and colors
OP_STYLES: dict[str | None, tuple[str, str]] = {
    "read": ("R", "cyan"),
    "write": ("W", "yellow"),
    "edit": ("E", "green"),
    "search": ("?", "magenta"),
    "bash": ("$", "blue"),
    None: ("-", "dim"),
}


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

    def __init__(self, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(**kwargs)
        self._agent_colors: dict[str, int] = {}

    def compose(self) -> ComposeResult:
        yield Static(
            "[bold]Live Activity Stream[/bold] [dim](recent 30 events)[/dim]",
            classes="stream-title",
        )
        yield VerticalScroll(id="stream-scroll")

    def add_event(self, event: LiveActivityEvent, agent_color_index: int = 0) -> None:
        """Add a new event to the stream."""
        self._agent_colors[event.session_id] = agent_color_index
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
        """Format an event for display with operation icons."""
        time_str = event.timestamp.strftime("%H:%M:%S")
        session = event.session_id[:4]

        # Get agent color
        color_idx = self._agent_colors.get(event.session_id, 0)
        agent_color = AGENT_COLORS[color_idx % len(AGENT_COLORS)]

        # Get operation icon and color
        op_icon, op_color = OP_STYLES.get(event.operation, ("-", "dim"))

        if event.tool_name and event.file_path:
            # Shorten file path based on type
            if event.file_path.startswith("pattern:"):
                pattern = event.file_path.replace("pattern:", "")[:20]
                short_file = f"[?] {pattern}"
            elif event.file_path.startswith("bash:"):
                cmd = event.file_path.replace("bash:", "")[:20]
                short_file = f"$ {cmd}"
            else:
                parts = event.file_path.split("/")
                if len(parts) > 2:
                    short_file = f".../{parts[-1]}"
                else:
                    short_file = parts[-1] if parts else event.file_path

                if len(short_file) > 24:
                    short_file = short_file[:21] + "..."

            return (
                f"[dim]{time_str}[/dim] "
                f"\\[[{agent_color}]*{session}[/{agent_color}]\\] "
                f"[{op_color}]{op_icon}[/{op_color}] "
                f"{escape(event.tool_name):6} "
                f"{escape(short_file)}"
            )
        elif event.tool_name:
            return (
                f"[dim]{time_str}[/dim] "
                f"\\[[{agent_color}]*{session}[/{agent_color}]\\] "
                f"[{op_color}]{op_icon}[/{op_color}] "
                f"{escape(event.tool_name)}"
            )
        else:
            return (
                f"[dim]{time_str}[/dim] "
                f"\\[[{agent_color}]*{session}[/{agent_color}]\\] "
                f"[dim]-[/dim] {event.event_type}"
            )
