"""Base watcher interface."""

import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


class BaseWatcher(ABC):
    """Abstract base class for file/process watchers."""

    def __init__(self) -> None:
        self._running = False
        self._callbacks: list[Callable[..., Any]] = []

    def add_callback(self, callback: Callable[..., Any]) -> None:
        """Add a callback to be invoked on events."""
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[..., Any]) -> None:
        """Remove a callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def _notify(self, *args: Any, **kwargs: Any) -> None:
        """Notify all callbacks."""
        for callback in self._callbacks:
            try:
                callback(*args, **kwargs)
            except Exception as e:
                logger.warning("Callback error in %s: %s", self.__class__.__name__, e)

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
