"""Base watcher interface."""

from abc import ABC, abstractmethod
from typing import Callable


class BaseWatcher(ABC):
    """Abstract base class for file/process watchers."""

    def __init__(self) -> None:
        self._running = False
        self._callbacks: list[Callable] = []

    def add_callback(self, callback: Callable) -> None:
        """Add a callback to be invoked on events."""
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable) -> None:
        """Remove a callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def _notify(self, *args, **kwargs) -> None:
        """Notify all callbacks."""
        for callback in self._callbacks:
            try:
                callback(*args, **kwargs)
            except Exception:
                pass  # Don't let callback errors stop the watcher

    @abstractmethod
    def start(self) -> None:
        """Start watching."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop watching."""
        pass

    @property
    def is_running(self) -> bool:
        """Check if watcher is running."""
        return self._running
