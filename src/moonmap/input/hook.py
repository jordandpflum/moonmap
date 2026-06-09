"""System-wide low-level keyboard hook using pynput.
Runs on a background thread; communicates to the UI via Qt signals.

Usage:
    hook = KeyboardHook(on_press_cb=..., on_release_cb=...)
    hook.start()
    ...
    hook.stop()

Callbacks receive a pynput Key or KeyCode object.
All UI updates must go through Qt signals (not direct widget calls) since
this runs on a non-Qt thread.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pynput import keyboard


class KeyboardHook:
    """Manage a background pynput listener for keyboard events."""

    def __init__(
        self,
        on_press_cb: Callable[[Any], None] | None = None,
        on_release_cb: Callable[[Any], None] | None = None,
    ) -> None:
        """Create a hook with optional press and release callbacks."""
        self._on_press = on_press_cb
        self._on_release = on_release_cb
        self._listener: keyboard.Listener | None = None

    def start(self) -> None:
        """Start listening for keyboard events."""
        if self._listener is not None:
            return
        self._listener = keyboard.Listener(
            on_press=self._handle_press,
            on_release=self._handle_release,
        )
        self._listener.start()

    def stop(self) -> None:
        """Stop listening for keyboard events."""
        if self._listener:
            self._listener.stop()
            self._listener = None

    def _handle_press(self, key: Any) -> None:
        if self._on_press:
            self._on_press(key)

    def _handle_release(self, key: Any) -> None:
        if self._on_release:
            self._on_release(key)
