from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QColor, QImage, QPainter

from moonmap.layout.qmk_parser import parse_keymap_c
from moonmap.ui.keyboard_widget import KeyboardWidget
from moonmap.ui.layer_bar import LayerBar
from moonmap.ui.main_window import MainWindow

SAMPLE_KEYMAP = (
    Path(__file__).resolve().parents[1]
    / "sample_source_layouts"
    / "zsa_moonlander_reva_NmOnd_nlv3L0_full-featured-qwerty-writing-lay_source"
    / "zsa_moonlander_full-featured-qwerty-writing-lay_source"
    / "keymap.c"
)
EXPECTED_KEY_COUNT = 72
HIGHLIGHT_RGB = QColor("#4FC3F7").getRgb()[:3]
ENTER_THUMB_INDEX = 60


def test_keyboard_widget_renders_72_keys_and_updates_labels() -> None:
    widget = KeyboardWidget()
    layout = parse_keymap_c(SAMPLE_KEYMAP)

    widget.set_layout_model(layout)

    assert widget.key_count == EXPECTED_KEY_COUNT
    assert widget.label_for_key(0) == "`"

    widget.set_active_layer(1)

    assert widget.label_for_key(0) == ""


def test_keyboard_widget_exposes_hover_detail_for_compact_labels() -> None:
    widget = KeyboardWidget()
    layout = parse_keymap_c(SAMPLE_KEYMAP)
    widget.set_layout_model(layout)

    details: list[str] = []
    widget.hover_detail_changed.connect(details.append)

    key_info = widget._key_geometry[ENTER_THUMB_INDEX]
    assert widget._key_index_at(QPointF(float(key_info["cx"]), float(key_info["cy"]))) == ENTER_THUMB_INDEX
    widget.hover_detail_changed.emit(f"Key {ENTER_THUMB_INDEX}: {widget._displays[ENTER_THUMB_INDEX].detail}")

    assert widget.label_for_key(ENTER_THUMB_INDEX) == "⏎"
    assert "LT(4, KC_ENTER)" in details[-1]
    assert "hold: L4" in details[-1]


def test_keyboard_widget_paints_nonblank_output_and_highlight() -> None:
    widget = KeyboardWidget()
    layout = parse_keymap_c(SAMPLE_KEYMAP)
    widget.set_layout_model(layout)
    widget.update_key_state(29, True)

    image = QImage(widget.size(), QImage.Format.Format_ARGB32)
    image.fill(QColor("#FFFFFF"))
    painter = QPainter(image)
    widget.render(painter)
    painter.end()

    assert _count_nonwhite_pixels(image) > 0
    assert _has_highlight_pixel(image)
    assert widget.pressed_indexes() == [29]


def test_layer_bar_creates_one_button_per_layer() -> None:
    layout = parse_keymap_c(SAMPLE_KEYMAP)
    layer_bar = LayerBar()

    layer_bar.set_layers(layout.layers)

    assert layer_bar.layer_count == layout.layer_count


def test_main_window_loads_layout_path() -> None:
    window = MainWindow(start_hook=False)

    window.load_layout_path(SAMPLE_KEYMAP)

    status_bar = window.statusBar()
    assert status_bar is not None
    assert status_bar.currentMessage() == "Layer 0 - Layer 0"


def _count_nonwhite_pixels(image: QImage) -> int:
    count = 0
    for y in range(image.height()):
        for x in range(image.width()):
            if QColor(image.pixel(x, y)).getRgb()[:3] != (255, 255, 255):
                count += 1
    return count


def _has_highlight_pixel(image: QImage) -> bool:
    for y in range(image.height()):
        for x in range(image.width()):
            if QColor(image.pixel(x, y)).getRgb()[:3] == HIGHLIGHT_RGB:
                return True
    return False
