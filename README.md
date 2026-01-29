# cwhap

**Conductor We Have A Problem** - A terminal GUI to monitor multiple Claude Code agents in real-time.

![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)
![License MIT](https://img.shields.io/badge/license-MIT-green.svg)

## Features

- **Color-Coded Agents** - Each agent gets a unique color for easy tracking across all views
- **Live Agent Monitoring** - See all active Claude Code sessions with real-time status updates
- **File Tree View** - Visualize agent collaboration patterns and see where agents' work overlaps
- **Conflict Detection** - Get alerts when multiple agents try to edit the same file (conflicts arise when trees touch!)
- **Activity Heatmap** - Visualize which files are being accessed most frequently with access counts
- **Live Stream** - Watch file operations as they happen across all agents with color-coded session IDs
- **Activity Sparkline** - Track operations per second over time
- **Simple Mode** - Optional minimal UI for focused monitoring

## Installation

```bash
pip install -e .
```

## Usage

```bash
# Full mode with all features (default)
cwhap

# Simple mode - minimal UI with just the live stream
cwhap --simple

# Set your preferred mode as default
cwhap --simple --set-default  # Make simple mode default
cwhap --set-default            # Make full mode default

# View help
cwhap --help
```

Then open Claude Code in other terminal windows. The dashboard will automatically detect active sessions and display their activity.

### Configuration

Your preferred mode is saved to `~/.cwhap/config.json` when you use `--set-default`.

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `q` | Quit |
| `r` | Refresh |
| `d` | Toggle dark/light mode |
| `c` | Show conflict details |

## Dashboard Layout

### Full Mode (default)

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│  CWHAP - Live Monitor                                             [3 Active] [q]     │
├──────────────────────────────────────────────────────────────────────────────────────┤
│  ⚠ CONFLICT: src/app.py - Agents abc123, def456 both editing                        │
├──────────────────────────────────────────────────────────────────────────────────────┤
│ ● Active Agents                                                                      │
│ ┌──────────────────────┬──────────────────────┬──────────────────────┐             │
│ │ ◐ ●Agent abc1       │ ◓ ●Agent def4       │ ○ ●Agent ghi7       │             │
│ │ .../dev/myapp        │ .../dev/other        │ .../home/user        │             │
│ │ → Edit main.py       │ → Read test.py       │ idle 2m              │             │
│ │ ████████░░           │ ███░░░░░░░           │                      │             │
│ │ Msgs:12 Tools:45     │ Msgs:8 Tools:23      │ Msgs:5 Tools:10      │             │
│ │      Files:7         │      Files:4         │      Files:2         │             │
│ └──────────────────────┴──────────────────────┴──────────────────────┘             │
├──────────────────────────────────────────────────────────────────────────────────────┤
│ Live Activity Stream        │ Agent File Tree          │ File Activity Heatmap     │
│ (recent 30 events)          │                          │ (30s window)              │
│ ──────────────────────      │ ⚠ Overlapping Access     │ ───────────────────────   │
│ 15:42:01 [●abc1] Edit       │   ├─ .../src/app.py      │ .../src/app.py    ████ 8  │
│          main.py            │      └─ ●abc1 ●def4      │ .../test.py       ███░ 5  │
│ 15:42:00 [●def4] Read       │                          │ .../utils.py      ██░░ 3  │
│          test.py            │ Independent Work         │ 🔍 *.tsx          █░░░ 2  │
│ 15:41:58 [●abc1] Read       │   ├─ .../config.json     │                           │
│          utils.py           │       ●abc1              │                           │
├─────────────────────────────┴──────────────────────────┴───────────────────────────┤
│ Activity ▁▂▃▄▅▆▇█▇▆▅▄▃▂▁▁▂▃▄▅▆▇█  Ops/sec: 2.3  Conflicts: 1                       │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

### Simple Mode (`--simple`)

```
┌──────────────────────────────────────────────────────────────┐
│  CWHAP - Live Monitor                        [3 Active] [q] │
├──────────────────────────────────────────────────────────────┤
│ ● Active Agents                                              │
│ ┌─────────────┬─────────────┬─────────────┐                 │
│ │ ◐ ●abc1    │ ◓ ●def4    │ ○ ●ghi7    │                 │
│ │ Edit main.py│ Read test.py│ idle 2m     │                 │
│ │ M:12 T:45   │ M:8 T:23    │ M:5 T:10    │                 │
│ └─────────────┴─────────────┴─────────────┘                 │
├──────────────────────────────────────────────────────────────┤
│ Live Activity Stream (recent 30 events)                     │
│ ───────────────────────────────────────────                 │
│ 15:42:01 [●abc1] Edit main.py                               │
│ 15:42:00 [●def4] Read test.py                               │
│ 15:41:58 [●abc1] Read utils.py                              │
└──────────────────────────────────────────────────────────────┘
```

### Status Indicators

- **●** Active (green) - Agent is currently performing operations
- **◐** Thinking (yellow) - Agent active within last 5 seconds
- **○** Idle (dim) - No activity for 30+ seconds

### Color Coding

Each agent is assigned a unique color (●) that appears:
- In the agent card header
- Next to session IDs in the live stream ([●abc1])
- In the file tree view showing which agents access which files

This makes it easy to track individual agents across all views.

### Conflict Detection

The **Agent File Tree** shows how agents' work overlaps:
- **⚠ Overlapping Access** - Multiple agents accessing the same file (conflict zone!)
- **Independent Work** - Each agent working on separate files

When two or more agents edit the same file within 5 seconds, a conflict alert banner appears:
- **Critical** (red) - Multiple agents editing same file simultaneously
- **Warning** (yellow) - One agent editing while another reads

The system triggers an audible alert (bell) for critical conflicts.

## Requirements

- Python 3.11+
- macOS, Linux, or Windows
- Claude Code installed and running

## How It Works

CWHAP monitors Claude Code session files at `~/.claude/projects/`:
1. Watches for new JSONL entries in active session files
2. Parses tool calls (Read, Write, Edit, etc.) in real-time
3. Tracks file access patterns across all agents
4. Detects conflicts when multiple agents access the same file within 5 seconds
5. Displays everything in a live updating TUI powered by Textual

## License

MIT
