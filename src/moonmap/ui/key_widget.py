"""Drawing helpers for Moonlander keys."""

from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen, QPolygonF


@dataclass(frozen=True)
class KeyPaintState:
    """Visual state for a painted key."""

    label: str
    is_pressed: bool = False
    is_layer_key: bool = False
    is_layer_active: bool = False
    highlight_color: str = "#4FC3F7"


def draw_key(
    painter: QPainter,
    *,
    width: float,
    height: float,
    shape: str | None,
    state: KeyPaintState,
) -> None:
    """Draw a key centered at the painter origin."""
    background, border, text = _colors_for_state(state)
    rect = QRectF(-width / 2, -height / 2, width, height)

    painter.setPen(QPen(border, 1.5))
    painter.setBrush(background)
    if shape == "thumb_wide":
        painter.drawPolygon(_thumb_wide_polygon(width, height))
    else:
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 7, 7)

    font = QFont("Arial", 9)
    font.setBold(state.is_layer_key or state.is_pressed)
    painter.setFont(font)
    painter.setPen(text)

    label_rect = rect.adjusted(4, 2, -4, -2)
    painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, _fitted_label(painter, state.label, label_rect))


def _colors_for_state(state: KeyPaintState) -> tuple[QColor, QColor, QColor]:
    background = QColor("#20242B")
    border = QColor("#4A5260")
    text = QColor("#F5F7FA")

    if state.is_layer_key:
        background = QColor("#2D3D47")
        border = QColor("#6AA8C5")
    if state.is_layer_active:
        background = QColor("#28546B")
        border = QColor("#8BDCFB")
    if state.is_pressed:
        background = QColor(state.highlight_color)
        border = QColor("#D7F4FF")
        text = QColor("#081116")

    return background, border, text


def _thumb_wide_polygon(width: float, height: float) -> QPolygonF:
    half_width = width / 2
    half_height = height / 2
    return QPolygonF(
        [
            QPointF(-half_width, half_height),
            QPointF(-half_width, 0),
            QPointF(0, -half_height),
            QPointF(half_width, 0),
            QPointF(half_width, half_height),
        ],
    )


def _fitted_label(painter: QPainter, label: str, rect: QRectF) -> str:
    metrics = QFontMetrics(painter.font())
    return metrics.elidedText(label, Qt.TextElideMode.ElideRight, int(rect.width()))
