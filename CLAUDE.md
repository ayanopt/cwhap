# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
pip install -e .              # Install
cwhap                         # Run (full mode)
cwhap --simple                # Run in simple mode
cwhap --simple --set-default  # Set simple mode as default
pytest                        # Test
ruff check src                # Lint
mypy src/cwhap                # Type check
```

## Architecture

```
src/cwhap/
├── __main__.py               # CLI entry point with --simple and --set-default flags
├── app.py                    # Main Textual app, orchestrates watchers and widgets
├── models/
│   ├── agent.py              # LiveAgent, ConflictEvent, LiveActivityEvent, AGENT_COLORS
│   └── file_event.py         # FileEvent model with operation types
├── monitors/
│   └── conflict_detector.py  # Thread-safe conflict detection within 5s window
├── parsers/
│   └── session_parser.py     # Reads ~/.claude/projects/ session index and JSONL files
├── watchers/
│   ├── base.py               # BaseWatcher abstract class with callback system
│   ├── tail_watcher.py       # Tails JSONL files, emits LiveActivityEvent on new lines
│   └── session_watcher.py    # IndexWatcher detects new/changed sessions
└── widgets/
    ├── agent_card.py         # Card with status, mini-sparkline, operation, stats
    ├── conflict_alert.py     # Red banner when agents edit same file
    ├── file_tree.py          # Tree view showing agent collaboration patterns
    ├── heatmap.py            # File access intensity with counts and 30s decay
    ├── live_stream.py        # Color-coded scrolling feed with operation icons
    ├── sparkline.py          # 60-second activity graph (▁▂▃▄▅▆▇█)
    └── stats_bar.py          # Aggregate metrics bar (agents, messages, tools, files)
```

## Data Flow

1. `TailWatcher` monitors `~/.claude/projects/*/*.jsonl` via watchdog
2. New JSONL lines parsed into `LiveActivityEvent` with tool name, file path, operation
3. Each new agent gets assigned a unique color index (thread-safe via lock)
4. `ConflictDetector` tracks file access per session, emits `ConflictEvent` on overlap
5. `App` routes events to widgets via `call_from_thread` for thread-safe UI updates
6. Widgets use Textual reactive system to re-render on data changes
7. `FileTree` groups files by agent access patterns (overlapping vs independent)
8. `StatsBar` aggregates metrics across all agents in real-time
9. Each `AgentCard` tracks its own activity history for mini-sparklines

## Key Patterns

- **Thread Safety**: Color assignment uses threading.Lock, conflict detector is thread-safe
- **Agent Status**: Based on time since last activity: <5s active, <30s thinking, else idle
- **Color Coding**: Each agent gets unique color from 12-color palette, consistent across all views
- **Conflict Detection**: 5-second window - multiple agents accessing same file triggers alert
- **File Tree**: Groups files by access pattern - "Overlapping Access" vs "Independent Work"
- **Heatmap**: Enhanced analysis with intensity levels, operation breakdown (R/W/E), weighted scoring, percentages, and recency tracking
- **Live Stream**: Shows operation icons (R/W/E/?/$) with color-coded agent badges
- **Sparkline**: Tracks ops/second over rolling 60-second window
- **Mini-Sparklines**: Each agent card shows its own 20-second activity history
- **Stats Bar**: Real-time aggregate metrics (agents, messages, tools, files, uptime)
- **Simple Mode**: Optional flag (`--simple`) for minimal UI with just agents + stream
- **Config Persistence**: User preference saved to `~/.cwhap/config.json` via `--set-default`

## Operation Types

File operations tracked:
- `read` (R) - Reading file contents (weight: 1x)
- `write` (W) - Writing new files (weight: 3x)
- `edit` (E) - Modifying existing files (weight: 2x)
- `search` (?) - Pattern searches (Glob, Grep)
- `bash` ($) - Shell commands

Only file operations (read/write/edit) trigger conflict detection.

## Heatmap Scoring System

The Activity Heatmap uses weighted scoring to reflect the true impact of operations:
- **Write operations**: 3x weight (creating new content is high-impact)
- **Edit operations**: 2x weight (modifying existing content)
- **Read operations**: 1x weight (passive access)

This weighting ensures that a file with 10 writes (30 points) appears hotter than a file with 20 reads (20 points), which accurately reflects the activity's significance. The heatmap displays:
- 10-level heat intensity visualization
- Categorical intensity (CRIT/HIGH/MED/LOW)
- Percentage of total activity
- Per-operation breakdown
- Recency indicator

## UI Modes

### Full Mode (default)
- Stats bar at top showing aggregate metrics
- 2-row layout for main content:
  - Top row: Live Stream (full width)
  - Bottom row: File Tree | Heatmap (side by side)
- Agent cards with mini-sparklines and activity tracking
- File tree visualizes collaboration patterns
- Heatmap shows file activity with counts

### Simple Mode (`--simple`)
- Single column: Live Stream only
- Compact agent cards: M:X T:Y format
- Minimal space usage for focused monitoring

## Keyboard Shortcuts

- `q` - Quit
- `r` - Refresh (rescan active sessions)
- `c` - Show conflict details
