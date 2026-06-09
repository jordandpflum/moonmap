"""Renders both halves of the Moonlander Mark I physical layout.

Physical geometry is loaded from src/assets/moonlander_layout.json.
Each key is an instance of KeyWidget, positioned absolutely.

Redraws all key labels when active layer changes.
Highlights individual keys on press/release via update_key_state().
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from PyQt6.QtCore import QSize
from PyQt6.QtWidgets import QWidget

from moonmap.layout.models import Layout
from moonmap.ui.key_widget import KeyWidget

ASSET_PATH = Path(__file__).resolve().parents[1] / "assets" / "moonlander_layout.json"


class KeyboardWidget(QWidget):
    """Render the Moonlander physical key layout."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the keyboard widget."""
        super().__init__(parent)
        self._layout_model: Layout | None = None
        self._active_layer = 0
        self._geometry_data = self._load_geometry()
        self._keys: dict[int, KeyWidget] = {}

        self.setMinimumSize(self.canvas_size)
        self.setFixedSize(self.canvas_size)
        self._build_keys()

    @property
    def canvas_size(self) -> QSize:
        """Return the keyboard canvas size."""
        return QSize(
            int(self._geometry_data["canvas_width"]),
            int(self._geometry_data["canvas_height"]),
        )

    @property
    def key_count(self) -> int:
        """Return the number of physical keys rendered."""
        return len(self._keys)

    def label_for_key(self, index: int) -> str:
        """Return the current label for a rendered key."""
        return self._keys[index].label

    def pressed_indexes(self) -> list[int]:
        """Return indexes currently marked as pressed."""
        return [index for index, key in self._keys.items() if key.is_pressed]

    def set_layout_model(self, layout: Layout | None) -> None:
        """Set the parsed layout model and redraw the active layer."""
        self._layout_model = layout
        self._active_layer = 0
        self._redraw_labels()

    def set_active_layer(self, layer_index: int) -> None:
        """Switch displayed key labels to a layer."""
        self._active_layer = layer_index
        self._redraw_labels()

    def update_key_state(self, index: int, pressed: bool) -> None:
        """Update one key's pressed state."""
        key_widget = self._keys.get(index)
        if key_widget is not None:
            key_widget.set_pressed(pressed)

    def set_highlight_color(self, color: str) -> None:
        """Set the accent color for all key widgets."""
        for key_widget in self._keys.values():
            key_widget.set_highlight_color(color)

    def _load_geometry(self) -> dict[str, Any]:
        return cast(dict[str, Any], json.loads(ASSET_PATH.read_text(encoding="utf-8")))

    def _build_keys(self) -> None:
        for key_info in self._geometry_data["keys"]:
            index = int(key_info["index"])
            key_widget = KeyWidget(index=index, parent=self)
            key_widget.setGeometry(
                int(key_info["x"]),
                int(key_info["y"]),
                int(key_info["w"]),
                int(key_info["h"]),
            )
            key_widget.show()
            self._keys[index] = key_widget

    def _redraw_labels(self) -> None:
        active_layer = None
        if self._layout_model is not None:
            active_layer = next(
                (layer for layer in self._layout_model.layers if layer.index == self._active_layer),
                None,
            )

        for index, key_widget in self._keys.items():
            key = None
            if active_layer is not None and index < len(active_layer.keys):
                key = active_layer.keys[index]
            key_widget.set_key(key, active_layer=self._active_layer)
