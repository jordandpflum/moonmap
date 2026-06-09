"""MO/TG layer state machine.

Active layer = highest index layer currently active via MO stack or TG set.
Fallback = Layer 0 (base).
"""

from __future__ import annotations

from .models import Key


class LayerStateManager:
    """Track active layers from MO and TG key actions."""

    def __init__(self) -> None:
        """Initialize empty momentary and toggle layer state."""
        self._mo_stack: list[int] = []  # layers active while MO key is held
        self._tg_set: set[int] = set()  # layers toggled on/off

    def on_keydown(self, key: Key) -> None:
        """Update layer state for a key press."""
        action = key.layer_action
        if action is None:
            return
        if action.type == "MO":
            if action.target_layer not in self._mo_stack:
                self._mo_stack.append(action.target_layer)
        elif action.type == "TG":
            t = action.target_layer
            if t in self._tg_set:
                self._tg_set.discard(t)
            else:
                self._tg_set.add(t)

    def on_keyup(self, key: Key) -> None:
        """Update layer state for a key release."""
        action = key.layer_action
        if action is None:
            return
        if action.type == "MO":
            try:
                self._mo_stack.remove(action.target_layer)
            except ValueError:
                pass  # key release without matching press — safe to ignore

    def active_layer(self) -> int:
        """Return the highest active layer index, or base layer zero."""
        candidates: set[int] = self._tg_set | set(self._mo_stack)
        if not candidates:
            return 0
        return max(candidates)

    def reset(self) -> None:
        """Clear all layer state — call when a new layout is loaded."""
        self._mo_stack.clear()
        self._tg_set.clear()
