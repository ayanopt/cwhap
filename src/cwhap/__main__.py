"""Entry point for cwhap."""

import argparse
import json
from pathlib import Path

from cwhap.app import CwhapApp

CONFIG_FILE = Path.home() / ".cwhap" / "config.json"


def load_config() -> dict[str, bool]:
    """Load configuration from file."""
    if not CONFIG_FILE.exists():
        return {}
    try:
        with open(CONFIG_FILE) as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def save_config(config: dict[str, bool]) -> None:
    """Save configuration to file."""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
    except OSError as e:
        print(f"Warning: Could not save config: {e}")


def main() -> None:
    """Run the cwhap application."""
    parser = argparse.ArgumentParser(description="CWHAP - Live Monitor for Claude Code agents")
    parser.add_argument(
        "--simple",
        action="store_true",
        help="Use simple UI mode with minimal information",
    )
    parser.add_argument(
        "--set-default",
        action="store_true",
        help="Save the current mode (simple or full) as default",
    )
    args = parser.parse_args()

    # Load config
    config = load_config()

    # Handle --set-default
    if args.set_default:
        config["simple_mode"] = args.simple
        save_config(config)
        mode_name = "simple" if args.simple else "full"
        print(f"Default mode set to: {mode_name}")
        print(f"Config saved to: {CONFIG_FILE}")
        return

    # Use config default if no explicit flag
    simple_mode = args.simple or config.get("simple_mode", False)

    app = CwhapApp(simple_mode=simple_mode)
    app.run()


if __name__ == "__main__":
    main()
