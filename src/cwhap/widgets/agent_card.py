"""Agent card widget showing live agent status."""

from collections import deque

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static

from cwhap.models.agent import LiveAgent

# Mini sparkline characters
MINI_SPARK = "▁▂▃▄▅▆▇█"


class AgentCard(Widget):
    """Compact card showing a live agent's status with activity indicator."""

    DEFAULT_CSS = """
    AgentCard {
        width: 32;
        height: 7;
        border: round $primary;
        padding: 0 1;
        margin-right: 1;
    }

    AgentCard.--active {
        border: round $success;
    }

    AgentCard.--thinking {
        border: round $warning;
    }

    AgentCard.--conflict {
        border: double $error;
        background: $error 20%;
    }

    AgentCard .agent-header {
        text-style: bold;
        height: 1;
    }

    AgentCard .agent-project {
        color: $text-muted;
        height: 1;
    }

    AgentCard .agent-operation {
        height: 1;
    }

    AgentCard .agent-activity {
        height: 1;
    }

    AgentCard .agent-stats {
        color: $text-muted;
        height: 1;
    }
    """

    agent: reactive[LiveAgent | None] = reactive(None)
    in_conflict: reactive[bool] = reactive(False)
    simple_mode: reactive[bool] = reactive(False)

    def __init__(self, agent: LiveAgent | None = None, simple_mode: bool = False, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(**kwargs)
        self._frame: int = 0  # Instance variable for animation frame
        self._activity_history: deque[int] = deque([0] * 20, maxlen=20)  # Last 20 seconds
        self._current_activity: int = 0
        self.simple_mode = simple_mode
        if agent:
            self.agent = agent

    def on_mount(self) -> None:
        """Start animation and activity timers."""
        self.set_interval(0.3, self._animate)
        self.set_interval(1.0, self._tick_activity)

    def _animate(self) -> None:  # type: ignore[override]
        """Update animation frame."""
        self._frame = (self._frame + 1) % 4
        if self.agent and self.agent.status in ("active", "thinking"):
            self.refresh()

    def _tick_activity(self) -> None:
        """Update activity history every second."""
        self._activity_history.append(self._current_activity)
        self._current_activity = 0

    def record_activity(self) -> None:
        """Record an activity event for this agent."""
        self._current_activity += 1

    def _render_mini_sparkline(self) -> str:
        """Render a mini sparkline for this agent."""
        if not self._activity_history:
            return ""
        max_val = max(self._activity_history) or 1
        chars = []
        for val in self._activity_history:
            idx = min(int(val / max_val * 7), 7) if max_val > 0 else 0
            chars.append(MINI_SPARK[idx])
        return "".join(chars)

    def compose(self) -> ComposeResult:
        yield Static("", id="header", classes="agent-header")
        yield Static("", id="project", classes="agent-project")
        yield Static("", id="operation", classes="agent-operation")
        yield Static("", id="activity", classes="agent-activity")
        yield Static("", id="stats", classes="agent-stats")

    def watch_agent(self, agent: LiveAgent | None) -> None:
        """Update display when agent changes."""
        self._update_display()

    def watch_in_conflict(self, in_conflict: bool) -> None:
        """Update conflict styling."""
        if in_conflict:
            self.add_class("--conflict")
        else:
            self.remove_class("--conflict")

    def _update_display(self) -> None:
        """Update all display elements."""
        agent = self.agent
        if not agent:
            return

        # Update styling based on status
        self.remove_class("--active", "--thinking")
        if agent.status == "active":
            self.add_class("--active")
        elif agent.status == "thinking":
            self.add_class("--thinking")

        # Header with status icon and agent color
        spinners = ["|", "/", "-", "\\"]
        agent_color = agent.agent_color

        if agent.status == "active":
            icon = f"[green]{spinners[self._frame]}[/green]"
        elif agent.status == "thinking":
            icon = f"[yellow]{spinners[self._frame]}[/yellow]"
        else:
            icon = f"[dim]{agent.status_icon}[/dim]"

        try:
            header = self.query_one("#header", Static)
            if self.simple_mode:
                header.update(f"{icon} [{agent_color}]*[/{agent_color}]{agent.short_id}")
            else:
                header.update(f"{icon} [{agent_color}]*Agent[/{agent_color}] {agent.short_id}")

            project = self.query_one("#project", Static)
            project.update(agent.short_project)

            operation = self.query_one("#operation", Static)
            if agent.current_operation:
                if self.simple_mode:
                    op_text = agent.current_operation[:20]
                    operation.update(f"{op_text}")
                else:
                    op_text = agent.current_operation[:24]
                    operation.update(f"→ {op_text}")
            elif agent.status == "idle":
                seconds = int(agent.seconds_since_activity())
                if seconds < 60:
                    operation.update(f"[dim]idle {seconds}s[/dim]")
                else:
                    mins = seconds // 60
                    operation.update(f"[dim]idle {mins}m[/dim]")
            else:
                operation.update("")

            # Activity sparkline
            activity = self.query_one("#activity", Static)
            sparkline = self._render_mini_sparkline()
            if agent.status == "active":
                activity.update(f"[green]{sparkline}[/green]")
            elif agent.status == "thinking":
                activity.update(f"[yellow]{sparkline}[/yellow]")
            else:
                activity.update(f"[dim]{sparkline}[/dim]")

            stats = self.query_one("#stats", Static)
            files_count = len(set(agent.files_accessed))
            if self.simple_mode:
                stats.update(f"M:{agent.message_count} T:{agent.tool_count}")
            else:
                stats.update(
                    f"Msgs:{agent.message_count} "
                    f"Tools:{agent.tool_count} Files:{files_count}"
                )

        except Exception:
            pass  # Widget may not be mounted yet
