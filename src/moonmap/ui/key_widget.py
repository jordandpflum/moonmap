"""Drawing helpers for Moonlander keys."""

from __future__ import annotations

from dataclasses import dataclass, field

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen, QPolygonF

from moonmap.layout.models import KeyDisplay, RgbColor

_LIGHT_COLOR_LUMINANCE = 145


@dataclass(frozen=True)
class KeyPaintState:
    """Visual state for a painted key."""

    label: str
    display: KeyDisplay = field(default_factory=KeyDisplay)
    led_color: RgbColor | None = None
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

    _draw_legends(painter, rect, state, text)


def _colors_for_state(state: KeyPaintState) -> tuple[QColor, QColor, QColor]:
    background = QColor("#E9ECEF")
    border = QColor("#B9C0C7")
    text = QColor("#20252B")

    if state.led_color is not None and state.led_color != (0, 0, 0):
        led = QColor(*state.led_color)
        background = _mix(background, led, 0.18)
        border = _mix(border, led, 0.34)
        text = _readable_legend_color(led)

    if state.is_layer_key:
        border = QColor("#4E8CA6")
    if state.is_layer_active:
        background = _mix(background, QColor("#4FC3F7"), 0.24)
        border = QColor("#2586AC")
    if state.is_pressed:
        background = QColor(state.highlight_color)
        border = QColor("#0E789E")
        text = QColor("#081116")

    return background, border, text


def _draw_legends(painter: QPainter, rect: QRectF, state: KeyPaintState, main_color: QColor) -> None:
    display = state.display

    top_rect = QRectF(rect.left() + 4, rect.top() + 3, rect.width() - 8, rect.height() * 0.28)
    center_rect = QRectF(rect.left() + 4, rect.top() + rect.height() * 0.24, rect.width() - 8, rect.height() * 0.48)
    bottom_rect = QRectF(rect.left() + 4, rect.bottom() - rect.height() * 0.31, rect.width() - 8, rect.height() * 0.28)

    if display.shifted:
        _draw_label(
            painter,
            top_rect,
            display.shifted,
            QColor("#D07600"),
            8,
            bold=False,
            alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter,
        )

    main = display.main or state.label
    if main:
        _draw_label(
            painter,
            center_rect,
            main,
            main_color,
            11,
            bold=state.is_layer_key or state.is_pressed,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )

    if display.hold:
        _draw_label(
            painter,
            bottom_rect,
            display.hold,
            QColor("#237C87"),
            7,
            bold=False,
            alignment=Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
        )


def _draw_label(
    painter: QPainter,
    rect: QRectF,
    label: str,
    color: QColor,
    point_size: int,
    *,
    bold: bool,
    alignment: Qt.AlignmentFlag,
) -> None:
    font = QFont("Arial", point_size)
    font.setBold(bold)
    painter.setFont(font)
    painter.setPen(color)
    painter.drawText(rect, alignment, _fitted_label(painter, label, rect))


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


def _mix(base: QColor, overlay: QColor, amount: float) -> QColor:
    keep = 1 - amount
    return QColor(
        round(base.red() * keep + overlay.red() * amount),
        round(base.green() * keep + overlay.green() * amount),
        round(base.blue() * keep + overlay.blue() * amount),
    )


def _readable_legend_color(color: QColor) -> QColor:
    luminance = 0.2126 * color.red() + 0.7152 * color.green() + 0.0722 * color.blue()
    amount = 0.58 if luminance > _LIGHT_COLOR_LUMINANCE else 0.32
    return _mix(color, QColor("#111820"), amount)
