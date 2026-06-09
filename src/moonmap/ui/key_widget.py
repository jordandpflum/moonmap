"""Renders a single key on the keyboard.

Visual states:
  - default:      dark background, white label
  - pressed:      accent color (from config highlight_color)
  - layer_key:    secondary color (MO/TG key at rest)
  - layer_active: brighter highlight when that layer is currently active
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QPaintEvent, QPainter, QPen
from PyQt6.QtWidgets import QWidget

from moonmap.layout.models import Key


class KeyWidget(QWidget):
    """Painted widget for one physical key."""

    def __init__(self, index: int, parent: QWidget | None = None) -> None:
        """Initialize the key widget."""
        super().__init__(parent)
        self.index = index
        self._label = ""
        self._pressed = False
        self._is_layer_key = False
        self._layer_active = False
        self._highlight_color = QColor("#4FC3F7")
        self.setMinimumSize(24, 24)

    @property
    def label(self) -> str:
        """Return the current displayed label."""
        return self._label

    @property
    def is_pressed(self) -> bool:
        """Return whether this key is currently pressed."""
        return self._pressed

    def set_key(self, key: Key | None, *, active_layer: int) -> None:
        """Set the key model displayed by this widget."""
        if key is None:
            self._label = ""
            self._is_layer_key = False
            self._layer_active = False
        else:
            self._label = key.label
            self._is_layer_key = key.layer_action is not None
            self._layer_active = (
                key.layer_action is not None and key.layer_action.target_layer == active_layer
            )
        self.update()

    def set_pressed(self, pressed: bool) -> None:
        """Set whether this key is currently pressed."""
        self._pressed = pressed
        self.update()

    def set_highlight_color(self, color: str) -> None:
        """Set the accent color used for pressed keys."""
        self._highlight_color = QColor(color)
        self.update()

    def paintEvent(self, event: QPaintEvent | None) -> None:  # noqa: N802
        """Paint the key cap."""
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(1, 1, -1, -1)
        background = QColor("#20242B")
        border = QColor("#4A5260")
        text = QColor("#F5F7FA")

        if self._is_layer_key:
            background = QColor("#2D3D47")
            border = QColor("#6AA8C5")
        if self._layer_active:
            background = QColor("#28546B")
            border = QColor("#8BDCFB")
        if self._pressed:
            background = self._highlight_color
            border = QColor("#D7F4FF")
            text = QColor("#081116")

        painter.setPen(QPen(border, 1.5))
        painter.setBrush(background)
        painter.drawRoundedRect(rect, 7, 7)

        font = QFont("Arial", 9)
        font.setBold(self._is_layer_key or self._pressed)
        painter.setFont(font)
        painter.setPen(text)
        painter.drawText(rect.adjusted(4, 2, -4, -2), Qt.AlignmentFlag.AlignCenter, self._label)
