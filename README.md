# cwhap

**Conductor We Have A Problem** - A terminal GUI to monitor multiple Claude Code agents in real-time.

![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)
![License MIT](https://img.shields.io/badge/license-MIT-green.svg)

## Features

- **Stats Dashboard** - Real-time aggregate metrics (agents, messages, tools, files, uptime)
- **Color-Coded Agents** - Each agent gets a unique color for easy tracking across all views
- **Mini Sparklines** - Each agent card shows its own 20-second activity history
- **Live Agent Monitoring** - See all active Claude Code sessions with real-time status updates
- **File Tree View** - Visualize agent collaboration patterns and see where agents' work overlaps
- **Conflict Detection** - Get alerts when multiple agents try to edit the same file
- **Activity Heatmap** - Visualize which files are being accessed most frequently
- **Live Stream** - Watch file operations with operation icons (R/W/E/?/$)
- **Activity Sparkline** - Track operations per second over 60-second rolling window
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
│  CWHAP - Live Monitor                                                                │
├──────────────────────────────────────────────────────────────────────────────────────┤
│  Agents: 2/3  |  Msgs: 25  |  Tools: 78  |  Files: 13  |  Uptime: 5m                │
├──────────────────────────────────────────────────────────────────────────────────────┤
│  ! CONFLICT: src/app.py - Agents abc123, def456 both editing                        │
├──────────────────────────────────────────────────────────────────────────────────────┤
│ * Active Agents                                                                      │
│ ┌────────────────────────────┬────────────────────────────┬────────────────────────┐│
│ │ | *Agent abc12345          │ / *Agent def45678          │ o *Agent ghi78901      ││
│ │ .../dev/myapp              │ .../dev/other              │ .../home/user          ││
│ │ -> Edit main.py            │ -> Read test.py            │ idle 2m                ││
│ │ ▁▂▃▄▅▆▇█▇▆▅▄▃▂▁▁▂▃▄       │ ▁▁▂▃▄▃▂▁▁▁▂▃▄▅▆▅▄▃▂▁      │ ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁  ││
│ │ Msgs:12 Tools:45 Files:7   │ Msgs:8 Tools:23 Files:4    │ Msgs:5 Tools:10 Files:2││
│ └────────────────────────────┴────────────────────────────┴────────────────────────┘│
├──────────────────────────────────────────────────────────────────────────────────────┤
│ Live Activity Stream (recent 30 events)                                             │
│ ──────────────────────────────────────────────────────────────────────────────────  │
│ 15:42:01 [*abc1] E Edit   main.py                                                   │
│ 15:42:00 [*def4] R Read   test.py                                                   │
│ 15:41:58 [*abc1] R Read   utils.py                                                  │
│ 15:41:55 [*abc1] ? Grep   [?] "function"                                            │
│ 15:41:52 [*abc1] $ Bash   $ pytest                                                  │
├──────────────────────────────────────────────────────────────────────────────────────┤
│ Agent File Tree                              │ File Activity Heatmap (30s window)   │
│                                              │ ──────────────────────────────────   │
│ ! Overlapping Access                         │ .../src/app.py          ████████ 8   │
│   +-- .../src/app.py                         │ .../test.py             █████░░░ 5   │
│       +-- *abc1 *def4                        │ .../utils.py            ███░░░░░ 3   │
│                                              │ [?] *.tsx               █░░░░░░░ 2   │
│ Independent Work                             │ $ pytest                █░░░░░░░ 1   │
│   +-- .../config.json *abc1                  │                                      │
│   +-- .../README.md *ghi7                    │                                      │
├──────────────────────────────────────────────┴──────────────────────────────────────┤
│ Activity ▁▂▃▄▅▆▇█▇▆▅▄▃▂▁▁▂▃▄▅▆▇█  Ops/sec: 2.3  Conflicts: 1                       │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

### Simple Mode (`--simple`)

```
┌──────────────────────────────────────────────────────────────┐
│  CWHAP - Live Monitor                        [3 Active] [q] │
├──────────────────────────────────────────────────────────────┤
│ * Active Agents                                              │
│ ┌─────────────┬─────────────┬─────────────┐                 │
│ │ | *abc1     │ / *def4     │ o *ghi7     │                 │
│ │ Edit main.py│ Read test.py│ idle 2m     │                 │
│ │ M:12 T:45   │ M:8 T:23    │ M:5 T:10    │                 │
│ └─────────────┴─────────────┴─────────────┘                 │
├──────────────────────────────────────────────────────────────┤
│ Live Activity Stream (recent 30 events)                     │
│ ───────────────────────────────────────────                 │
│ 15:42:01 [*abc1] E Edit   main.py                           │
│ 15:42:00 [*def4] R Read   test.py                           │
│ 15:41:58 [*abc1] R Read   utils.py                          │
└──────────────────────────────────────────────────────────────┘
```

### Status Indicators

- **|/-\\** (spinner) - Agent is actively working (animated)
- ***** Active (green) - Agent is currently performing operations
- **~** Thinking (yellow) - Agent active within last 5 seconds
- **o** Idle (dim) - No activity for 30+ seconds

### Operation Icons

| Icon | Operation | Description |
|------|-----------|-------------|
| R | Read | Reading file contents |
| W | Write | Writing new files |
| E | Edit | Modifying existing files |
| ? | Search | Pattern searches (Glob, Grep) |
| $ | Bash | Shell commands |

### Color Coding

Each agent is assigned a unique color (*) that appears:
- In the agent card header
- Next to session IDs in the live stream ([*abc1])
- In the file tree view showing which agents access which files

This makes it easy to track individual agents across all views.

### Mini Sparklines

Each agent card displays a mini sparkline showing the agent's activity over the last 20 seconds. This helps you quickly see:
- Which agents are most active
- Activity patterns over time
- When an agent becomes idle

### Conflict Detection

The **Agent File Tree** shows how agents' work overlaps:
- **! Overlapping Access** - Multiple agents accessing the same file (conflict zone!)
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
3. Tracks file access patterns across all agents with thread-safe mechanisms
4. Detects conflicts when multiple agents access the same file within 5 seconds
5. Aggregates metrics across all agents in real-time
6. Displays everything in a live updating TUI powered by Textual

## License

MIT
