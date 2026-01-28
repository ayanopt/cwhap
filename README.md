# cwhap

**Conductor We Have A Problem** - A terminal GUI to monitor multiple Claude Code agents in real-time.

![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)
![License MIT](https://img.shields.io/badge/license-MIT-green.svg)

## Features

- **Live Agent Monitoring** - See all active Claude Code sessions with real-time status updates
- **Conflict Detection** - Get alerts when multiple agents try to edit the same file
- **Activity Heatmap** - Visualize which files are being accessed most frequently
- **Live Stream** - Watch file operations as they happen across all agents
- **Activity Sparkline** - Track operations per second over time

## Installation

```bash
pip install -e .
```

## Usage

```bash
cwhap
```

Then open Claude Code in other terminal windows. The dashboard will automatically detect active sessions and display their activity.

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `q` | Quit |
| `r` | Refresh |
| `d` | Toggle dark/light mode |
| `c` | Show conflict details |

## Dashboard Layout

```
┌──────────────────────────────────────────────────────────────────┐
│  CWHAP - Live Monitor                              [3 Active] [q]│
├──────────────────────────────────────────────────────────────────┤
│  ⚠ CONFLICT: src/app.py - Agents abc123, def456 both editing    │
├──────────────────────────────────────────────────────────────────┤
│ Agent abc123 ●        │ Agent def456 ◐        │ Agent ghi789 ○   │
│ /dev/myapp            │ /dev/other            │ /home/user       │
│ → Edit main.py        │ → Read test.py        │ idle 2m          │
│ ████████░░            │ ███░░░░░░░            │                  │
├───────────────────────┴───────────────────────┴──────────────────┤
│ Live Stream                        │ File Heatmap               │
│ 15:42:01 [abc1] Edit main.py      │ src/main.py    ████████    │
│ 15:42:00 [def4] Read test.py      │ tests/test.py  ███░░░░░    │
│ 15:41:58 [abc1] Read utils.py     │ src/utils.py   ██░░░░░░    │
├────────────────────────────────────┴─────────────────────────────┤
│ Activity ▁▂▃▄▅▆▇█▇▆▅▄▃▂▁▁▂▃▄▅▆▇█  Ops/sec: 2.3  Conflicts: 1   │
└──────────────────────────────────────────────────────────────────┘
```

### Status Indicators

- **●** Active - Agent is currently performing operations
- **◐** Thinking - Agent active within last 30 seconds
- **○** Idle - No recent activity

### Conflict Alerts

When two or more agents edit the same file within 5 seconds, a conflict alert appears:
- **Critical** (red) - Multiple agents editing same file
- **Warning** (yellow) - One agent editing while another reads

## Requirements

- Python 3.11+
- macOS (uses FSEvents for file watching)

## License

MIT
