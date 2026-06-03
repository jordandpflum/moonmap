"""Data model for a parsed QMK keymap."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LayerAction:
    """Describes a layer-switching action on a key."""

    type: str  # "MO" or "TG"
    target_layer: int


@dataclass
class Key:
    """A single key on a single layer."""

    index: int  # Physical key index (0-based, Moonlander ordering)
    label: str  # Human-readable label, e.g. "A", "MO(1)", "LCTL"
    code: str  # Raw QMK keycode string from keymap.c
    layer_action: LayerAction | None = None  # None if not a layer-switching key


@dataclass
class Layer:
    """One layer of the keymap."""

    index: int
    name: str  # e.g. "BASE", "NAV" — from comment in keymap.c if present
    keys: list[Key] = field(default_factory=list)


@dataclass
class Layout:
    """Full parsed keymap."""

    layers: list[Layer] = field(default_factory=list)

    @property
    def layer_count(self) -> int:
        """Return the number of parsed layers."""
        return len(self.layers)
