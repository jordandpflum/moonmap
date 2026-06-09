"""Renders both halves of the Moonlander Mark I physical layout.

Physical geometry is loaded from src/assets/moonlander_layout.json.
Each key is drawn in a single QPainter pass.

Redraws all key labels when active layer changes.
Highlights individual keys on press/release via update_key_state().
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, cast

from PyQt6.QtCore import QPointF, QSize, pyqtSignal
from PyQt6.QtGui import QColor, QPaintEvent, QPainter
from PyQt6.QtWidgets import QWidget

from moonmap.layout.models import Key, KeyDisplay, Layer, Layout, RgbColor
from moonmap.ui.key_widget import KeyPaintState, draw_key

ASSET_PATH = Path(__file__).resolve().parents[1] / "assets" / "moonlander_layout.json"
TRANSPARENT_CODES = {"_______", "KC_TRANSPARENT", "KC_TRNS"}


class KeyboardWidget(QWidget):
    """Render the Moonlander physical key layout."""

    hover_detail_changed = pyqtSignal(str)

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
        self._displays: dict[int, KeyDisplay] = {index: KeyDisplay() for index in self._key_geometry}
        self._led_colors: dict[int, RgbColor | None] = {index: None for index in self._key_geometry}
        self._layer_key_indexes: set[int] = set()
        self._layer_active_indexes: set[int] = set()
        self._pressed_indexes: set[int] = set()
        self._highlight_color = "#4FC3F7"
        self._hovered_index: int | None = None

        self.setMouseTracking(True)
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
        painter.fillRect(self.rect(), QColor("#FFFFFF"))

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
                    display=self._displays[index],
                    led_color=self._led_colors[index],
                    is_pressed=index in self._pressed_indexes,
                    is_layer_key=index in self._layer_key_indexes,
                    is_layer_active=index in self._layer_active_indexes,
                    highlight_color=self._highlight_color,
                ),
            )
            painter.restore()

    def mouseMoveEvent(self, event: Any) -> None:  # noqa: N802
        """Emit hover details for the key under the cursor."""
        index = self._key_index_at(event.position())
        if index == self._hovered_index:
            return
        self._hovered_index = index
        if index is None:
            self.hover_detail_changed.emit("")
            return
        detail = self._displays[index].detail or self._labels[index]
        self.hover_detail_changed.emit(f"Key {index}: {detail}" if detail else f"Key {index}")

    def leaveEvent(self, event: Any) -> None:  # noqa: N802
        """Clear hover details when leaving the keyboard."""
        del event
        self._hovered_index = None
        self.hover_detail_changed.emit("")

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
            source_key = None
            effective_key = None
            inherited_layer_index = None
            if active_layer is not None:
                source_key, effective_key, inherited_layer_index = self._effective_key_for_index(active_layer, index)
            if effective_key is None:
                self._labels[index] = ""
                self._displays[index] = KeyDisplay()
                self._led_colors[index] = None
                continue

            display = self._display_for_effective_key(
                source_key=source_key,
                effective_key=effective_key,
                active_layer_index=active_layer.index if active_layer is not None else self._active_layer,
                inherited_layer_index=inherited_layer_index,
            )

            self._labels[index] = display.main
            self._displays[index] = display
            self._led_colors[index] = source_key.led_color if source_key is not None else effective_key.led_color
            if effective_key.layer_action is not None:
                self._layer_key_indexes.add(index)
                if effective_key.layer_action.target_layer == self._active_layer:
                    self._layer_active_indexes.add(index)

        self.update()

    def _effective_key_for_index(self, active_layer: Layer, index: int) -> tuple[Key | None, Key | None, int | None]:
        source_key = active_layer.keys[index] if index < len(active_layer.keys) else None
        if source_key is not None and not _is_transparent(source_key):
            return source_key, source_key, None

        if self._layout_model is None:
            return source_key, source_key, None

        lower_layers = sorted(
            (layer for layer in self._layout_model.layers if layer.index < active_layer.index),
            key=lambda layer: layer.index,
            reverse=True,
        )
        for layer in lower_layers:
            if index >= len(layer.keys):
                continue
            candidate = layer.keys[index]
            if not _is_transparent(candidate):
                return source_key, candidate, layer.index

        return source_key, source_key, None

    def _display_for_effective_key(
        self,
        *,
        source_key: Key | None,
        effective_key: Key,
        active_layer_index: int,
        inherited_layer_index: int | None,
    ) -> KeyDisplay:
        display = effective_key.display
        if source_key is None or not _is_transparent(source_key) or inherited_layer_index is None:
            return display

        inherited_detail = (
            f"Transparent on layer {active_layer_index}; "
            f"inherits layer {inherited_layer_index} key {effective_key.index}: {effective_key.code}"
        )
        detail = f"{inherited_detail}; {display.detail}" if display.detail else inherited_detail
        return KeyDisplay(
            main=display.main,
            shifted=display.shifted,
            hold=display.hold,
            detail=detail,
        )

    def _key_index_at(self, point: QPointF) -> int | None:
        for index in reversed(sorted(self._key_geometry)):
            key_info = self._key_geometry[index]
            center_x = float(key_info["cx"])
            center_y = float(key_info["cy"])
            width = float(key_info["w"])
            height = float(key_info["h"])
            angle = -math.radians(float(key_info.get("rotation_degrees", 0)))
            dx = point.x() - center_x
            dy = point.y() - center_y
            local_x = dx * math.cos(angle) - dy * math.sin(angle)
            local_y = dx * math.sin(angle) + dy * math.cos(angle)
            if -width / 2 <= local_x <= width / 2 and -height / 2 <= local_y <= height / 2:
                return index
        return None


def _is_transparent(key: Key) -> bool:
    return key.code.strip() in TRANSPARENT_CODES
