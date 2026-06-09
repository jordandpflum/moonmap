"""Renders both halves of the Moonlander Mark I physical layout.

Physical geometry is loaded from src/assets/moonlander_layout.json.
Each key is drawn in a single QPainter pass.

Redraws all key labels when active layer changes.
Highlights individual keys on press/release via update_key_state().
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from PyQt6.QtCore import QPoint, QPointF, QSize, pyqtSignal
from PyQt6.QtGui import QColor, QPaintEvent, QPainter
from PyQt6.QtWidgets import QWidget

from moonmap.layout.key_meanings import meaning_for_key
from moonmap.layout.models import Key, KeyDisplay, Layer, LayerAction, Layout, RgbColor
from moonmap.input.key_mapper import host_inputs_for_key
from moonmap.ui.key_widget import KeyPaintState, draw_key

ASSET_PATH = Path(__file__).resolve().parents[1] / "assets" / "moonlander_layout.json"
TRANSPARENT_CODES = {"_______", "KC_TRANSPARENT", "KC_TRNS"}


@dataclass(frozen=True)
class KeyHoverInfo:
    """Structured hover details for a rendered physical key."""

    index: int
    label: str
    active_layer_index: int
    active_layer_name: str
    active_code: str
    resolved_code: str
    main: str
    shifted: str
    hold: str
    detail: str
    meaning: str = ""
    source_layer_index: int | None = None
    source_layer_name: str | None = None
    led_color: RgbColor | None = None
    layer_action: LayerAction | None = None
    is_pressed: bool = False
    is_layer_key: bool = False
    host_inputs: tuple[str, ...] = ()
    active_layer_matches: tuple[str, ...] = ()
    all_layer_matches: tuple[str, ...] = ()

    @property
    def led_hex(self) -> str:
        """Return the LED color as a CSS-style hex string."""
        if self.led_color is None:
            return ""
        red, green, blue = self.led_color
        return f"#{red:02X}{green:02X}{blue:02X}"


@dataclass(frozen=True)
class _KeyContext:
    source_key: Key | None
    effective_key: Key | None
    inherited_layer_index: int | None


class KeyboardWidget(QWidget):
    """Render the Moonlander physical key layout."""

    hover_info_changed = pyqtSignal(object)
    key_clicked = pyqtSignal(object)

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
        self._key_contexts: dict[int, _KeyContext] = {
            index: _KeyContext(None, None, None) for index in self._key_geometry
        }
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

    def hover_info_for_key(self, index: int) -> KeyHoverInfo | None:
        """Return structured hover information for a rendered key."""
        if index not in self._key_geometry or self._layout_model is None:
            return None

        context = self._key_contexts.get(index)
        if context is None or context.effective_key is None:
            return None

        active_layer = self._layer_by_index(self._active_layer)
        source_key = context.source_key
        effective_key = context.effective_key
        display = self._displays[index]
        meaning = meaning_for_key(effective_key.code, display)
        if not meaning and source_key is not None:
            meaning = meaning_for_key(source_key.code, source_key.display)
        source_layer = (
            self._layer_by_index(context.inherited_layer_index)
            if context.inherited_layer_index is not None
            else None
        )

        return KeyHoverInfo(
            index=index,
            label=self._labels[index],
            active_layer_index=self._active_layer,
            active_layer_name=active_layer.name if active_layer is not None else f"Layer {self._active_layer}",
            active_code=source_key.code if source_key is not None else "",
            resolved_code=effective_key.code,
            main=display.main,
            shifted=display.shifted,
            hold=display.hold,
            detail=display.detail,
            meaning=meaning,
            source_layer_index=source_layer.index if source_layer is not None else None,
            source_layer_name=source_layer.name if source_layer is not None else None,
            led_color=self._led_colors[index],
            layer_action=effective_key.layer_action,
            is_pressed=index in self._pressed_indexes,
            is_layer_key=index in self._layer_key_indexes,
            host_inputs=tuple(host_inputs_for_key(effective_key)),
        )

    def key_anchor_global_pos(self, index: int) -> QPoint:
        """Return a global position near the center of a rendered key."""
        key_info = self._key_geometry[index]
        return self.mapToGlobal(QPoint(int(float(key_info["cx"])), int(float(key_info["cy"]))))

    def set_layout_model(self, layout: Layout | None) -> None:
        """Set the parsed layout model and redraw the active layer."""
        self._layout_model = layout
        self._active_layer = 0
        self._hovered_index = None
        self.hover_info_changed.emit(None)
        self._redraw_labels()

    def set_active_layer(self, layer_index: int) -> None:
        """Switch displayed key labels to a layer."""
        self._active_layer = layer_index
        self._hovered_index = None
        self.hover_info_changed.emit(None)
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
            self.hover_info_changed.emit(None)
            return
        self.hover_info_changed.emit(self.hover_info_for_key(index))

    def mousePressEvent(self, event: Any) -> None:  # noqa: N802
        """Emit structured details for click-to-test visual simulation."""
        index = self._key_index_at(event.position())
        if index is None:
            return
        info = self.hover_info_for_key(index)
        if info is not None:
            self.key_clicked.emit(info)

    def leaveEvent(self, event: Any) -> None:  # noqa: N802
        """Clear hover details when leaving the keyboard."""
        del event
        self._hovered_index = None
        self.hover_info_changed.emit(None)

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
                self._key_contexts[index] = _KeyContext(source_key, None, inherited_layer_index)
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
            self._key_contexts[index] = _KeyContext(source_key, effective_key, inherited_layer_index)
            if effective_key.layer_action is not None:
                self._layer_key_indexes.add(index)
                if effective_key.layer_action.target_layer == self._active_layer:
                    self._layer_active_indexes.add(index)

        self.update()

    def _layer_by_index(self, layer_index: int | None) -> Layer | None:
        if layer_index is None or self._layout_model is None:
            return None
        return next((layer for layer in self._layout_model.layers if layer.index == layer_index), None)

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
            tap_raw=display.tap_raw,
            hold_raw=display.hold_raw,
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
