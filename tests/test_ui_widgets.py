from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QColor, QImage, QPainter

from moonmap.layout.qmk_parser import parse_keymap_c
from moonmap.ui.key_tooltip import KeyTooltip
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
DUAL_9_X_INDEX = 56


def test_keyboard_widget_renders_72_keys_and_updates_labels() -> None:
    widget = KeyboardWidget()
    layout = parse_keymap_c(SAMPLE_KEYMAP)

    widget.set_layout_model(layout)

    assert widget.key_count == EXPECTED_KEY_COUNT
    assert widget.label_for_key(0) == "`"

    widget.set_active_layer(1)

    assert widget.label_for_key(0) == "`"


def test_keyboard_widget_resolves_transparent_keys_to_lower_layers() -> None:
    widget = KeyboardWidget()
    layout = parse_keymap_c(SAMPLE_KEYMAP)

    widget.set_layout_model(layout)
    widget.set_active_layer(1)

    assert layout.layers[1].keys[0].code == "KC_TRANSPARENT"
    assert widget.label_for_key(0) == "`"
    assert "Transparent on layer 1" in widget._displays[0].detail
    assert "inherits layer 0 key 0: KC_GRAVE" in widget._displays[0].detail


def test_keyboard_widget_exposes_hover_detail_for_compact_labels() -> None:
    widget = KeyboardWidget()
    layout = parse_keymap_c(SAMPLE_KEYMAP)
    widget.set_layout_model(layout)

    key_info = widget._key_geometry[ENTER_THUMB_INDEX]
    assert widget._key_index_at(QPointF(float(key_info["cx"]), float(key_info["cy"]))) == ENTER_THUMB_INDEX
    hover_info = widget.hover_info_for_key(ENTER_THUMB_INDEX)

    assert hover_info is not None
    assert widget.label_for_key(ENTER_THUMB_INDEX) == "⏎"
    assert hover_info.index == ENTER_THUMB_INDEX
    assert hover_info.active_layer_index == 0
    assert hover_info.active_code == "LT(4, KC_ENTER)"
    assert hover_info.resolved_code == "LT(4, KC_ENTER)"
    assert hover_info.main == "⏎"
    assert hover_info.hold == "L4"
    assert hover_info.meaning == "Tap sends Enter; hold activates layer 4."
    assert "hold: L4" in hover_info.detail


def test_keyboard_widget_bottom_right_row_matches_qmk_order() -> None:
    widget = KeyboardWidget()
    layout = parse_keymap_c(SAMPLE_KEYMAP)
    widget.set_layout_model(layout)

    assert [widget.label_for_key(index) for index in range(61, 66)] == ["←", "↓", "↑", "→", "TT 3"]
    assert [layout.layers[0].keys[index].code for index in range(60, 66)] == [
        "LT(4, KC_ENTER)",
        "KC_LEFT",
        "KC_DOWN",
        "KC_UP",
        "KC_RIGHT",
        "TT(3)",
    ]


def test_keyboard_widget_hover_info_includes_transparent_source_layer_and_led_color() -> None:
    widget = KeyboardWidget()
    layout = parse_keymap_c(SAMPLE_KEYMAP)
    widget.set_layout_model(layout)
    widget.set_active_layer(1)

    hover_info = widget.hover_info_for_key(0)

    assert hover_info is not None
    assert hover_info.active_layer_index == 1
    assert hover_info.active_code == "KC_TRANSPARENT"
    assert hover_info.resolved_code == "KC_GRAVE"
    assert hover_info.source_layer_index == 0
    assert hover_info.source_layer_name == "Layer 0"
    assert hover_info.led_color == layout.layers[1].keys[0].led_color
    assert hover_info.led_hex.startswith("#")
    assert hover_info.meaning == "Transparent: use the key from the next lower active layer."


def test_key_tooltip_populates_structured_rows() -> None:
    widget = KeyboardWidget()
    layout = parse_keymap_c(SAMPLE_KEYMAP)
    widget.set_layout_model(layout)
    hover_info = widget.hover_info_for_key(ENTER_THUMB_INDEX)
    assert hover_info is not None
    tooltip = KeyTooltip()

    tooltip.set_hover_info(hover_info)

    assert tooltip.row_text("tap") == "⏎"
    assert tooltip.row_text("meaning") == "Tap sends Enter; hold activates layer 4."
    assert tooltip.row_text("hold") == "L4"
    assert tooltip.row_text("active_code") == "LT(4, KC_ENTER)"
    assert tooltip.row_text("resolved_code") == "LT(4, KC_ENTER)"
    assert tooltip.row_visible("shift") is False


def test_key_tooltip_shows_regular_keyboard_inputs_for_dual_function_key() -> None:
    widget = KeyboardWidget()
    layout = parse_keymap_c(SAMPLE_KEYMAP)
    widget.set_layout_model(layout)
    hover_info = widget.hover_info_for_key(DUAL_9_X_INDEX)
    assert hover_info is not None
    tooltip = KeyTooltip()

    tooltip.set_hover_info(hover_info)

    assert hover_info.host_inputs == ("9", "Ctrl+X")
    assert tooltip.row_text("host_inputs") == "9, Ctrl+X"
    assert tooltip.row_visible("host_inputs") is True


def test_key_tooltip_shows_inherited_source_and_led_hex() -> None:
    widget = KeyboardWidget()
    layout = parse_keymap_c(SAMPLE_KEYMAP)
    widget.set_layout_model(layout)
    widget.set_active_layer(1)
    hover_info = widget.hover_info_for_key(0)
    assert hover_info is not None
    tooltip = KeyTooltip()

    tooltip.set_hover_info(hover_info)

    assert tooltip.row_text("source_layer") == "0 - Layer 0"
    assert tooltip.row_text("active_code") == "KC_TRANSPARENT"
    assert tooltip.row_text("resolved_code") == "KC_GRAVE"
    assert tooltip.row_text("led") == hover_info.led_hex


def test_key_tooltip_hides_meaning_for_obvious_keys() -> None:
    widget = KeyboardWidget()
    layout = parse_keymap_c(SAMPLE_KEYMAP)
    widget.set_layout_model(layout)
    hover_info = widget.hover_info_for_key(15)
    assert hover_info is not None
    assert hover_info.resolved_code == "KC_Q"
    tooltip = KeyTooltip()

    tooltip.set_hover_info(hover_info)

    assert tooltip.row_text("meaning") == ""
    assert tooltip.row_visible("meaning") is False
    assert tooltip.row_visible("host_inputs") is True


def test_key_tooltip_hides_regular_keyboard_row_when_no_host_input() -> None:
    widget = KeyboardWidget()
    layout = parse_keymap_c(SAMPLE_KEYMAP)
    layout.layers[0].keys[15].code = "CUSTOM_THING"
    layout.layers[0].keys[15].display = layout.layers[0].keys[15].display.__class__()
    widget.set_layout_model(layout)
    hover_info = widget.hover_info_for_key(15)
    assert hover_info is not None
    tooltip = KeyTooltip()

    tooltip.set_hover_info(hover_info)

    assert tooltip.row_text("host_inputs") == ""
    assert tooltip.row_visible("host_inputs") is False


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


def test_main_window_hover_does_not_replace_live_status_bar() -> None:
    window = MainWindow(start_hook=False)
    window.load_layout_path(SAMPLE_KEYMAP)
    status_bar = window.statusBar()
    assert status_bar is not None
    status_bar.showMessage("Key down: KC_A; layer 0; matches: 29")
    hover_info = window._keyboard.hover_info_for_key(ENTER_THUMB_INDEX)
    assert hover_info is not None

    window._handle_hover_info_changed(hover_info)

    assert status_bar.currentMessage() == "Key down: KC_A; layer 0; matches: 29"


def test_main_window_simulated_click_highlights_and_logs_event() -> None:
    window = MainWindow(start_hook=False)
    window.load_layout_path(SAMPLE_KEYMAP)
    hover_info = window._keyboard.hover_info_for_key(DUAL_9_X_INDEX)
    assert hover_info is not None

    window._handle_key_clicked(hover_info)

    assert window._keyboard.pressed_indexes() == [DUAL_9_X_INDEX]
    assert window._key_event_log.entries()[-1].event_type == "simulated"
    assert window._key_event_log.entries()[-1].host_action == "9, Ctrl+X"


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
