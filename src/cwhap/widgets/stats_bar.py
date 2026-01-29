"""Stats summary bar widget showing aggregate metrics."""

from datetime import UTC, datetime

from textual.reactive import reactive
from textual.widget import Widget


class StatsBar(Widget):
    """Compact stats bar showing aggregate session metrics."""

    DEFAULT_CSS = """
    StatsBar {
        height: 1;
        width: 100%;
        background: $surface-darken-1;
        padding: 0 2;
    }
    """

    total_agents: reactive[int] = reactive(0)
    total_messages: reactive[int] = reactive(0)
    total_tools: reactive[int] = reactive(0)
    total_files: reactive[int] = reactive(0)
    active_count: reactive[int] = reactive(0)
    start_time: datetime | None = None

    def __init__(self, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(**kwargs)
        self.start_time = datetime.now(UTC)

    def render(self) -> str:
        """Render the stats bar."""
        uptime = ""
        if self.start_time:
            delta = datetime.now(UTC) - self.start_time
            mins = int(delta.total_seconds() // 60)
            if mins < 60:
                uptime = f"{mins}m"
            else:
                hours = mins // 60
                mins = mins % 60
                uptime = f"{hours}h{mins}m"

        # Build stats string with visual separators
        parts = [
            f"[bold cyan]Agents:[/bold cyan] {self.active_count}/{self.total_agents}",
            f"[bold green]Msgs:[/bold green] {self.total_messages}",
            f"[bold yellow]Tools:[/bold yellow] {self.total_tools}",
            f"[bold magenta]Files:[/bold magenta] {self.total_files}",
            f"[dim]Uptime: {uptime}[/dim]",
        ]

        return "  |  ".join(parts)

    def update_stats(
        self,
        agents: int = 0,
        messages: int = 0,
        tools: int = 0,
        files: int = 0,
        active: int = 0,
    ) -> None:
        """Update all stats at once."""
        self.total_agents = agents
        self.total_messages = messages
        self.total_tools = tools
        self.total_files = files
        self.active_count = active
