from __future__ import annotations

from pathlib import Path

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


def test_keyboard_widget_renders_72_keys_and_updates_labels() -> None:
    widget = KeyboardWidget()
    layout = parse_keymap_c(SAMPLE_KEYMAP)

    widget.set_layout_model(layout)

    assert widget.key_count == EXPECTED_KEY_COUNT
    assert widget.label_for_key(0) == "GRAVE"

    widget.set_active_layer(1)

    assert widget.label_for_key(0) == "TRANSPARENT"


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
