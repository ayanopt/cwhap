"""Conflict alert widget for prominent conflict warnings."""

from textual.reactive import reactive
from textual.widget import Widget

from cwhap.models.agent import ConflictEvent


class ConflictAlert(Widget):
    """Prominent alert banner for file conflicts."""

    DEFAULT_CSS = """
    ConflictAlert {
        height: auto;
        min-height: 3;
        padding: 0 1;
        background: $surface;
        display: none;
    }

    ConflictAlert.--visible {
        display: block;
    }

    ConflictAlert.--critical {
        background: $error;
        color: $text;
        border: double $warning;
    }

    ConflictAlert.--warning {
        background: $warning 30%;
        color: $text;
        border: solid $warning;
    }
    """

    conflicts: reactive[list[ConflictEvent]] = reactive(list, init=False)
    _frame: int = 0

    def on_mount(self) -> None:
        """Start blink animation for critical alerts."""
        self.set_interval(0.5, self._animate)

    def _animate(self) -> None:  # type: ignore[override]
        """Animate the alert."""
        self._frame = (self._frame + 1) % 2
        if self.conflicts:
            self.refresh()

    def watch_conflicts(self, conflicts: list[ConflictEvent]) -> None:
        """Update display when conflicts change."""
        self.remove_class("--visible", "--critical", "--warning")

        if not conflicts:
            return

        self.add_class("--visible")

        # Check for critical conflicts
        critical = [c for c in conflicts if c.severity == "critical"]
        if critical:
            self.add_class("--critical")
        else:
            self.add_class("--warning")

    def render(self) -> str:
        """Render the conflict alert."""
        if not self.conflicts:
            return ""

        critical = [c for c in self.conflicts if c.severity == "critical"]
        warnings = [c for c in self.conflicts if c.severity == "warning"]

        lines = []

        if critical:
            # Blinking alert for critical
            alert_icon = "!" if self._frame == 0 else "!!"
            c = critical[0]
            lines.append(
                f"[bold blink]{alert_icon} CONFLICT: {c.short_file}[/bold blink]"
            )
            lines.append(f"Agents {c.short_agents} editing!")

            if len(critical) > 1:
                lines.append(f"[dim]+{len(critical) - 1} more critical conflicts[/dim]")

        elif warnings:
            w = warnings[0]
            lines.append(f"[yellow]! Warning: {w.short_file}[/yellow]")
            lines.append(f"[dim]Read/write race between {w.short_agents}[/dim]")

            if len(warnings) > 1:
                lines.append(f"[dim]+{len(warnings) - 1} more warnings[/dim]")

        return "\n".join(lines)
