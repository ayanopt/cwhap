# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
pip install -e .    # Install
cwhap               # Run
pytest              # Test
ruff check src      # Lint
mypy src/cwhap      # Type check
```

## Architecture

```
src/cwhap/
├── app.py                    # Main Textual app, orchestrates watchers and widgets
├── models/agent.py           # LiveAgent, ConflictEvent, LiveActivityEvent
├── monitors/conflict_detector.py  # Tracks file access, detects overlaps within 5s window
├── parsers/session_parser.py # Reads ~/.claude/projects/ session index and JSONL files
├── watchers/
│   ├── tail_watcher.py       # Tails JSONL files, emits LiveActivityEvent on new lines
│   └── session_watcher.py    # IndexWatcher detects new/changed sessions
└── widgets/
    ├── agent_card.py         # Compact card with status icon, progress bar, current operation
    ├── conflict_alert.py     # Red banner when agents edit same file
    ├── heatmap.py            # File access intensity with 30s decay
    ├── live_stream.py        # Scrolling feed of tool operations
    └── sparkline.py          # 60-second activity graph (▁▂▃▄▅▆▇█)
```

## Data Flow

1. `TailWatcher` monitors `~/.claude/projects/*/*.jsonl` via watchdog
2. New JSONL lines parsed into `LiveActivityEvent` with tool name, file path, operation
3. `ConflictDetector` tracks file access per session, emits `ConflictEvent` on overlap
4. `App` routes events to widgets via `call_from_thread` for thread-safe UI updates
5. Widgets use Textual reactive system to re-render on data changes

## Key Patterns

- Agent status based on time since last activity: <5s active, <30s thinking, else idle
- Conflict window is 5 seconds - two edits to same file within window triggers alert
- Heatmap decays file counts after 30s of no access
- Sparkline tracks ops/second over rolling 60-second window
