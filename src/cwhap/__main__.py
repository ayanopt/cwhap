"""Entry point for cwhap."""

from cwhap.app import CwhapApp


def main() -> None:
    """Run the cwhap application."""
    app = CwhapApp()
    app.run()


if __name__ == "__main__":
    main()
