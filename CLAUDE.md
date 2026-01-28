# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CWHAP (Conductor We Have A Problem) is a Python terminal GUI for **live monitoring** of Claude Code AI agents with conflict detection and data-dense visualizations.

## Commands

```bash
# Install
pip install -e .

# Run
cwhap

# Development
pip install -e ".[dev]"
pytest
mypy src/cwhap
ruff check src/cwhap
```

## Architecture

```
src/cwhap/
├── app.py                    # Main Textual app
├── models/
│   └── agent.py              # LiveAgent, ConflictEvent, LiveActivityEvent
├── monitors/
│   └── conflict_detector.py  # Time-window conflict detection
├── parsers/
│   └── session_parser.py     # Parses ~/.claude/projects/ JSONL
├── watchers/
│   ├── session_watcher.py    # IndexWatcher for session list changes
│   └── tail_watcher.py       # JSONL tailing for live activity
├── widgets/
│   ├── agent_card.py         # Live agent status card
│   ├── conflict_alert.py     # Conflict warning banner
│   ├── heatmap.py            # File access heatmap
│   ├── live_stream.py        # Real-time activity feed
│   └── sparkline.py          # Activity timeline (▁▂▃▄▅▆▇█)
└── styles/
    └── live_monitor.tcss     # Grid layout
```

## Key Features

- **Live Detection**: Sessions modified within 60s shown as active agents
- **Conflict Detection**: Alerts when 2+ agents edit same file within 5s
- **Sparkline**: Activity over last 60 seconds
- **Heatmap**: File access intensity with decay
- **Agent Cards**: Status with animated progress bars

## Keyboard Shortcuts

- `q` - Quit
- `r` - Refresh
- `d` - Toggle dark/light
- `c` - Show conflict details
