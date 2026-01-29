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
│   └── agent.py              # LiveAgent, ConflictEvent, LiveActivityEvent, AGENT_COLORS
├── monitors/
│   └── conflict_detector.py  # Tracks file access, detects overlaps within 5s window
├── parsers/
│   └── session_parser.py     # Reads ~/.claude/projects/ session index and JSONL files
├── watchers/
│   ├── tail_watcher.py       # Tails JSONL files, emits LiveActivityEvent on new lines
│   └── session_watcher.py    # IndexWatcher detects new/changed sessions
└── widgets/
    ├── agent_card.py         # Color-coded card with status, progress, operation, file count
    ├── conflict_alert.py     # Red banner when agents edit same file
    ├── file_tree.py          # Tree view showing agent collaboration and overlapping access
    ├── heatmap.py            # File access intensity with counts and 30s decay
    ├── live_stream.py        # Color-coded scrolling feed of tool operations
    └── sparkline.py          # 60-second activity graph (▁▂▃▄▅▆▇█)
```

## Data Flow

1. `TailWatcher` monitors `~/.claude/projects/*/*.jsonl` via watchdog
2. New JSONL lines parsed into `LiveActivityEvent` with tool name, file path, operation
3. Each new agent gets assigned a unique color index from `AGENT_COLORS`
4. `ConflictDetector` tracks file access per session, emits `ConflictEvent` on overlap
5. `App` routes events to widgets via `call_from_thread` for thread-safe UI updates
6. Widgets use Textual reactive system to re-render on data changes
7. `FileTree` groups files by agent access patterns (overlapping vs independent)
8. All widgets receive agent color index for consistent color coding

## Key Patterns

- **Agent Status**: Based on time since last activity: <5s active, <30s thinking, else idle
- **Color Coding**: Each agent gets unique color from 12-color palette, consistent across all views
- **Conflict Detection**: 5-second window - multiple agents accessing same file triggers alert
- **File Tree**: Groups files by access pattern - "Overlapping Access" (conflicts) vs "Independent Work"
- **Heatmap**: Decays file counts after 30s, shows full paths and access counts
- **Live Stream**: Shows tool operations with color-coded agent badges [●sessionID]
- **Sparkline**: Tracks ops/second over rolling 60-second window
- **Simple Mode**: Optional flag (`--simple`) for minimal UI with just agents + stream
- **Config Persistence**: User preference saved to `~/.cwhap/config.json` via `--set-default`

## UI Modes

### Full Mode (default)
- 3-column layout: Live Stream | File Tree | Heatmap
- Agent cards show: Messages, Tools, Files accessed
- File tree visualizes collaboration patterns
- Heatmap shows file activity with counts

### Simple Mode (`--simple`)
- Single column: Live Stream only
- Compact agent cards: M:X T:Y format
- Minimal space usage for focused monitoring
