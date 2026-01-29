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
- **Activity Heatmap** - Comprehensive file activity analysis with intensity levels, operation breakdown, and recency tracking
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
| `r` | Refresh (rescan active sessions) |
| `c` | Show conflict details |

## Dashboard Layout

### Full Mode (default)

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ CWHAP - Live Monitor                                                         [q/r/c]  │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ Agents: 3 detected (2 active)  |  Msgs: 125  |  Tools: 387  |  Files: 24  |  5m      │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ ! CONFLICT: src/app.py                                                                 │
│ Agents abc1, def4 both editing!                                                        │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ * Active Agents                                                                        │
│ ┌──────────────────────────┬──────────────────────────┬──────────────────────────┐   │
│ │ | *Agent abc1            │ / *Agent def4            │ o *Agent ghi7            │   │
│ │ .../dev/myapp            │ .../dev/other            │ .../home/user            │   │
│ │ -> Edit main.py          │ -> Read test.py          │ idle 2m                  │   │
│ │ ▁▂▃▄▅▆▇█▇▆▅▄▃▂▁▁▂▃▄     │ ▁▁▂▃▄▃▂▁▁▁▂▃▄▅▆▅▄▃▂     │ ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁     │   │
│ │ Msgs:45 Tools:132 Files:9│ Msgs:56 Tools:187 Files:8│ Msgs:24 Tools:68 Files:7│   │
│ └──────────────────────────┴──────────────────────────┴──────────────────────────┘   │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ Live Activity Stream (recent 30 events)                                               │
│ ────────────────────────────────────────────────────────────────────────────────────  │
│ 15:42:01 [*abc1] E Edit   main.py                                                     │
│ 15:42:00 [*def4] R Read   test.py                                                     │
│ 15:41:58 [*abc1] R Read   utils.py                                                    │
│ 15:41:55 [*abc1] ? Grep   [?] "function"                                              │
│ 15:41:52 [*abc1] $ Bash   $ pytest                                                    │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ Agent File Tree                   │ File Activity Analysis                            │
│                                   │ Legend: Heat[HOT/HIGH/MED/LOW] | Count (%) | ... │
│ ! Overlapping Access              │ ────────────────────────────────────────────────  │
│   +-- src/app.py                  │ src/main.py     HOT  ██████████  250 (52%) | ... │
│       +-- *abc1 *def4             │ src/utils.py    MED  ▄▄▄▄         98 (20%) | ... │
│                                   │ tests/test.py   LOW  ▁▁           45  (9%) | ... │
│ Independent Work                  │ config.yaml     LOW                12  (3%) | ... │
│   +-- config.json *abc1           │                                                   │
│   +-- README.md *ghi7             │                                                   │
├───────────────────────────────────┴───────────────────────────────────────────────────┤
│ Activity ▁▂▃▄▅▆▇█▇▆▅▄▃▂▁▁▂▃▄▅▆▇█  Ops/sec: 3.2  Conflicts: 1                         │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

**Key differences from diagram:**
- Stats bar shows "X detected (Y active)" format
- Agent cards include 20-second activity sparklines
- Live stream shows operation icons (R/W/E/?/$) with tool names
- Heatmap displays intensity levels (HOT/HIGH/MED/LOW), block bars, percentages, and operation breakdowns
- All widgets update in real-time as agents work

### Simple Mode (`--simple`)

```
┌────────────────────────────────────────────────────────────────┐
│ CWHAP - Live Monitor                                   [q/r/c] │
├────────────────────────────────────────────────────────────────┤
│ * Active Agents                                                │
│ ┌─────────────────┬─────────────────┬─────────────────┐       │
│ │ | *abc1         │ / *def4         │ o *ghi7         │       │
│ │ Edit main.py    │ Read test.py    │ idle 2m         │       │
│ │ M:45 T:132      │ M:56 T:187      │ M:24 T:68       │       │
│ └─────────────────┴─────────────────┴─────────────────┘       │
├────────────────────────────────────────────────────────────────┤
│ Live Activity Stream (recent 30 events)                       │
│ ────────────────────────────────────────────────────────────  │
│ 15:42:01 [*abc1] E Edit   main.py                             │
│ 15:42:00 [*def4] R Read   test.py                             │
│ 15:41:58 [*abc1] R Read   utils.py                            │
│ 15:41:55 [*abc1] ? Grep   [?] "function"                      │
└────────────────────────────────────────────────────────────────┘
```

**Simple mode features:**
- Compact agent cards showing just messages and tools
- Full-width live activity stream
- No file tree or heatmap (focused view)
- Same operation icons and color coding

### Status Indicators

The status icon in agent cards shows real-time agent state:

- **|/-\\** (animated spinner) - Active: agent is currently performing operations
- **~** (tilde) - Thinking: agent was active within last 5 seconds
- **o** (circle) - Idle: no activity for 30+ seconds

Card borders change color to match status (green=active, yellow=thinking, default=idle)

### Operation Icons

The live stream displays single-character operation icons with color coding:

| Icon | Operation | Color | Description |
|------|-----------|-------|-------------|
| R | Read | Cyan | Reading file contents |
| W | Write | Yellow | Writing new files |
| E | Edit | Green | Modifying existing files |
| ? | Search | Magenta | Pattern searches (Glob, Grep) |
| $ | Bash | Blue | Shell commands |

Example: `15:42:01 [*abc1] E Edit   main.py` shows an edit operation

### Agent Color Coding

Each agent is automatically assigned a unique color from a 12-color palette. This color appears consistently throughout the UI:

- **Agent Card Header**: `*Agent` marker shows agent's unique color
- **Live Stream**: Session ID badges like `[*abc1]` use the agent's color
- **File Tree**: Agent badges next to filenames (`*abc1 *def4`) show which agents accessed each file
- **Conflict Alerts**: Multi-colored badges highlight which agents are involved

The consistent color coding makes it easy to visually track individual agents across all views and quickly identify collaboration patterns.

### Mini Sparklines

Each agent card displays a mini sparkline showing the agent's activity over the last 20 seconds. This helps you quickly see:
- Which agents are most active
- Activity patterns over time
- When an agent becomes idle

### File Activity Heatmap

The **File Activity Analysis** widget provides comprehensive metrics for each file:

**Display Format:**
```
filename | intensity | heat_bar | count (%) | ops | age
```

**Metrics Explained:**
- **Intensity Level**: HOT (>75%), HIGH (>50%), MED (>25%), LOW (<25%) - color-coded
- **Heat Bar**: 10-level visual representation using smooth block characters (▁▂▃▄▅▆▇█)
- **Weighted Count**: write=3x, edit=2x, read=1x (shows true impact, not just frequency)
- **Percentage**: Portion of total activity for context
- **Operation Breakdown**: R:read W:write E:edit - exact operation counts
- **Age**: Time since last access (<5s green, <15s yellow, >15s dim)

**Example:**
```
src/main.py     HOT ██████████  150 (51.9%) | R: 0 W:50 E: 0 | <5s
src/utils.py    MED  ▄▄▄▄         60 (20.8%) | R: 0 W: 0 E:30 | <15s
```

This design handles disparate activity levels gracefully (e.g., 1000 edits vs 1 read) and clearly shows not just which files are hot, but how they're being used.

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
