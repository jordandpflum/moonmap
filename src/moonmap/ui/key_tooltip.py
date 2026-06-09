"""Rich popup tooltip for Moonlander key details."""

from __future__ import annotations

from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from moonmap.ui.keyboard_widget import KeyHoverInfo


class KeyTooltip(QWidget):
    """Small structured popup shown when hovering a rendered key."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the tooltip widget."""
        super().__init__(
            parent,
            Qt.WindowType.ToolTip
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.NoDropShadowWindowHint,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAutoFillBackground(True)
        self._rows: dict[str, tuple[QLabel, QWidget]] = {}
        self._title = QLabel(self)
        self._subtitle = QLabel(self)
        self._build_ui()

    def set_hover_info(self, info: KeyHoverInfo) -> None:
        """Populate the popup from structured hover data."""
        title = info.main or info.label or info.resolved_code or f"Key {info.index}"
        self._title.setText(title)
        self._subtitle.setText(f"Key {info.index} · Layer {info.active_layer_index} - {info.active_layer_name}")

        self._set_row("meaning", "Meaning", info.meaning)
        self._set_row("tap", "Tap", info.main)
        self._set_row("shift", "Shift", info.shifted)
        self._set_row("hold", "Hold", info.hold)
        self._set_row(
            "layer_action",
            "Layer",
            (
                f"{info.layer_action.type} {info.layer_action.target_layer}"
                if info.layer_action is not None
                else ""
            ),
        )
        self._set_row("active_code", "Active code", info.active_code)
        self._set_row("resolved_code", "Resolved code", info.resolved_code)
        self._set_row(
            "source_layer",
            "Source layer",
            (
                f"{info.source_layer_index} - {info.source_layer_name}"
                if info.source_layer_index is not None and info.source_layer_name is not None
                else ""
            ),
        )
        self._set_led_row(info)
        self._set_row("state", "State", self._state_text(info))

        self.adjustSize()

    def show_near(self, point: QPoint) -> None:
        """Show the popup near a global point."""
        self.move(point + QPoint(16, 12))
        self.show()

    def row_text(self, row_id: str) -> str:
        """Return a row value for tests."""
        row = self._rows.get(row_id)
        if row is None:
            return ""
        value_widget = row[1]
        value_text = value_widget.property("value_text")
        if isinstance(value_text, str):
            return value_text
        if isinstance(value_widget, QLabel):
            return value_widget.text()
        return ""

    def row_visible(self, row_id: str) -> bool:
        """Return whether a row is currently visible."""
        row = self._rows.get(row_id)
        return bool(row and not row[0].isHidden() and not row[1].isHidden())

    def _build_ui(self) -> None:
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#FFFFFF"))
        self.setPalette(palette)

        frame = QFrame(self)
        frame.setObjectName("tooltipFrame")
        frame.setStyleSheet(
            """
            QFrame#tooltipFrame {
                background: #FFFFFF;
                border: 1px solid #B9C0C7;
                border-radius: 7px;
            }
            QLabel {
                color: #20252B;
                background: transparent;
            }
            QLabel#title {
                font-size: 18px;
                font-weight: 700;
            }
            QLabel#subtitle {
                color: #65707C;
                font-size: 11px;
            }
            QLabel[rowLabel="true"] {
                color: #65707C;
                font-size: 11px;
            }
            QLabel[rowValue="true"] {
                color: #20252B;
                font-size: 12px;
            }
            """
        )

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(frame)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(7)

        self._title.setObjectName("title")
        self._subtitle.setObjectName("subtitle")
        layout.addWidget(self._title)
        layout.addWidget(self._subtitle)

        rows = QGridLayout()
        rows.setContentsMargins(0, 4, 0, 0)
        rows.setHorizontalSpacing(14)
        rows.setVerticalSpacing(5)
        layout.addLayout(rows)

        for row_number, (row_id, label) in enumerate(
            [
                ("meaning", "Meaning"),
                ("tap", "Tap"),
                ("shift", "Shift"),
                ("hold", "Hold"),
                ("layer_action", "Layer"),
                ("active_code", "Active code"),
                ("resolved_code", "Resolved code"),
                ("source_layer", "Source layer"),
                ("led", "LED"),
                ("state", "State"),
            ],
        ):
            label_widget = QLabel(label, self)
            label_widget.setProperty("rowLabel", "true")
            value_widget = QLabel(self)
            value_widget.setProperty("rowValue", "true")
            value_widget.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            value_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            rows.addWidget(label_widget, row_number, 0, Qt.AlignmentFlag.AlignTop)
            rows.addWidget(value_widget, row_number, 1, Qt.AlignmentFlag.AlignTop)
            self._rows[row_id] = (label_widget, value_widget)

    def _set_row(self, row_id: str, label: str, value: str) -> None:
        label_widget, value_widget = self._rows[row_id]
        label_widget.setText(label)
        if isinstance(value_widget, QLabel):
            value_widget.setText(value)
        label_widget.setVisible(bool(value))
        value_widget.setVisible(bool(value))

    def _set_led_row(self, info: KeyHoverInfo) -> None:
        label_widget, value_widget = self._rows["led"]
        label_widget.setText("LED")
        if info.led_color is None:
            label_widget.setVisible(False)
            value_widget.setVisible(False)
            value_widget.setProperty("value_text", "")
            return

        red, green, blue = info.led_color
        led_hex = info.led_hex
        swatch = (
            "<span style='"
            "display:inline-block;"
            "background: "
            f"rgb({red}, {green}, {blue});"
            "border: 1px solid #87919C;"
            "width: 10px;"
            "height: 10px;"
            "'>&nbsp;&nbsp;</span>"
        )
        if isinstance(value_widget, QLabel):
            value_widget.setText(f"{swatch} {led_hex}")
        value_widget.setProperty("value_text", led_hex)
        label_widget.setVisible(True)
        value_widget.setVisible(True)

    def _state_text(self, info: KeyHoverInfo) -> str:
        states = []
        if info.is_pressed:
            states.append("Pressed")
        if info.is_layer_key:
            states.append("Layer key")
        return ", ".join(states)
