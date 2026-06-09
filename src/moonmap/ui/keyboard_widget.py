"""Renders both halves of the Moonlander Mark I physical layout.

Physical geometry is loaded from src/assets/moonlander_layout.json.
Each key is drawn in a single QPainter pass.

Redraws all key labels when active layer changes.
Highlights individual keys on press/release via update_key_state().
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from PyQt6.QtCore import QSize
from PyQt6.QtGui import QPaintEvent, QPainter
from PyQt6.QtWidgets import QWidget

from moonmap.layout.models import Layout
from moonmap.ui.key_widget import KeyPaintState, draw_key

ASSET_PATH = Path(__file__).resolve().parents[1] / "assets" / "moonlander_layout.json"


class KeyboardWidget(QWidget):
    """Render the Moonlander physical key layout."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the keyboard widget."""
        super().__init__(parent)
        self._layout_model: Layout | None = None
        self._active_layer = 0
        self._geometry_data = self._load_geometry()
        self._key_geometry = {
            int(key_info["index"]): key_info for key_info in self._geometry_data["keys"]
        }
        self._labels: dict[int, str] = {index: "" for index in self._key_geometry}
        self._layer_key_indexes: set[int] = set()
        self._layer_active_indexes: set[int] = set()
        self._pressed_indexes: set[int] = set()
        self._highlight_color = "#4FC3F7"

        self.setMinimumSize(self.canvas_size)
        self.setFixedSize(self.canvas_size)

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
        return len(self._key_geometry)

    def label_for_key(self, index: int) -> str:
        """Return the current label for a rendered key."""
        return self._labels[index]

    def pressed_indexes(self) -> list[int]:
        """Return indexes currently marked as pressed."""
        return sorted(self._pressed_indexes)

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
        if index not in self._key_geometry:
            return
        if pressed:
            self._pressed_indexes.add(index)
        else:
            self._pressed_indexes.discard(index)
        self.update()

    def set_highlight_color(self, color: str) -> None:
        """Set the accent color for all key widgets."""
        self._highlight_color = color
        self.update()

    def paintEvent(self, event: QPaintEvent | None) -> None:  # noqa: N802
        """Paint the full keyboard surface."""
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        for index in sorted(self._key_geometry):
            key_info = self._key_geometry[index]
            painter.save()
            painter.translate(float(key_info["cx"]), float(key_info["cy"]))
            painter.rotate(float(key_info.get("rotation_degrees", 0)))
            draw_key(
                painter,
                width=float(key_info["w"]),
                height=float(key_info["h"]),
                shape=cast(str | None, key_info.get("shape")),
                state=KeyPaintState(
                    label=self._labels[index],
                    is_pressed=index in self._pressed_indexes,
                    is_layer_key=index in self._layer_key_indexes,
                    is_layer_active=index in self._layer_active_indexes,
                    highlight_color=self._highlight_color,
                ),
            )
            painter.restore()

    def _load_geometry(self) -> dict[str, Any]:
        return cast(dict[str, Any], json.loads(ASSET_PATH.read_text(encoding="utf-8")))

    def _redraw_labels(self) -> None:
        active_layer = None
        if self._layout_model is not None:
            active_layer = next(
                (layer for layer in self._layout_model.layers if layer.index == self._active_layer),
                None,
            )

        self._layer_key_indexes.clear()
        self._layer_active_indexes.clear()

        for index in self._key_geometry:
            key = None
            if active_layer is not None and index < len(active_layer.keys):
                key = active_layer.keys[index]
            if key is None:
                self._labels[index] = ""
                continue

            self._labels[index] = key.label
            if key.layer_action is not None:
                self._layer_key_indexes.add(index)
                if key.layer_action.target_layer == self._active_layer:
                    self._layer_active_indexes.add(index)

        self.update()
