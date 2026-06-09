from __future__ import annotations

from pathlib import Path
from typing import Any

from pynput import keyboard

from moonmap.layout.models import LayerAction
from moonmap.ui.main_window import MainWindow

SAMPLE_KEYMAP = (
    Path(__file__).resolve().parents[1]
    / "sample_source_layouts"
    / "zsa_moonlander_reva_NmOnd_nlv3L0_full-featured-qwerty-writing-lay_source"
    / "zsa_moonlander_full-featured-qwerty-writing-lay_source"
    / "keymap.c"
)
DUAL_9_X_INDEX = 56


class FakeHook:
    """Test hook with the same constructor surface as KeyboardHook."""

    def __init__(self, on_press_cb: Any = None, on_release_cb: Any = None) -> None:
        self.on_press_cb = on_press_cb
        self.on_release_cb = on_release_cb
        self.started = False
        self.stopped = False

    def start(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.stopped = True


def test_main_window_auto_starts_hook() -> None:
    window = MainWindow(hook_factory=FakeHook)

    assert isinstance(window._hook, FakeHook)
    assert window._hook.started


def test_hook_press_and_release_highlight_matching_indexes() -> None:
    window = MainWindow(start_hook=False, hook_factory=FakeHook)
    window.load_layout_path(SAMPLE_KEYMAP)

    window._handle_hook_press(keyboard.KeyCode.from_char("a"))

    assert window._keyboard.pressed_indexes() == [29]
    status_bar = window.statusBar()
    assert status_bar is not None
    assert status_bar.currentMessage() == "Key down: KC_A; layer 0; matches: 29"

    window._handle_hook_release(keyboard.KeyCode.from_char("a"))

    assert window._keyboard.pressed_indexes() == []
    assert status_bar.currentMessage() == "Key up: KC_A; layer 0; matches: 29"


def test_hook_press_highlights_all_duplicate_matches() -> None:
    window = MainWindow(start_hook=False, hook_factory=FakeHook)
    window.load_layout_path(SAMPLE_KEYMAP)
    assert window._layout_model is not None
    window._layout_model.layers[0].keys[0].code = "KC_A"

    window._handle_hook_press(keyboard.KeyCode.from_char("a"))

    assert sorted(window._keyboard.pressed_indexes()) == [0, 29]


def test_hook_press_on_transparent_layer_highlights_inherited_key() -> None:
    window = MainWindow(start_hook=False, hook_factory=FakeHook)
    window.load_layout_path(SAMPLE_KEYMAP)
    window._set_active_layer(1)

    window._handle_hook_press(keyboard.KeyCode.from_char("a"))

    assert window._keyboard.pressed_indexes() == [29]
    status_bar = window.statusBar()
    assert status_bar is not None
    assert status_bar.currentMessage() == "Key down: KC_A; layer 1; matches: 29"


def test_hook_press_on_keypad_layer_matches_printable_host_output() -> None:
    window = MainWindow(start_hook=False, hook_factory=FakeHook)
    window.load_layout_path(SAMPLE_KEYMAP)
    window._set_active_layer(2)

    window._handle_hook_press(keyboard.KeyCode.from_char("7"))

    assert window._keyboard.pressed_indexes() == [17, 22]
    status_bar = window.statusBar()
    assert status_bar is not None
    assert status_bar.currentMessage() == "Key down: KC_7; layer 2; matches: 17, 22"


def test_hook_press_on_keypad_layer_matches_windows_virtual_keypad_event() -> None:
    window = MainWindow(start_hook=False, hook_factory=FakeHook)
    window.load_layout_path(SAMPLE_KEYMAP)
    window._set_active_layer(2)

    window._handle_hook_press(keyboard.KeyCode.from_vk(103))

    assert window._keyboard.pressed_indexes() == [17, 22]
    status_bar = window.statusBar()
    assert status_bar is not None
    assert status_bar.currentMessage() == "Key down: KC_7; layer 2; matches: 17, 22"


def test_modifier_down_then_key_press_matches_chord() -> None:
    window = MainWindow(start_hook=False, hook_factory=FakeHook)
    window.load_layout_path(SAMPLE_KEYMAP)

    window._handle_hook_press(keyboard.Key.ctrl)
    window._handle_hook_press(keyboard.KeyCode.from_char("x"))

    assert DUAL_9_X_INDEX in window._keyboard.pressed_indexes()
    status_bar = window.statusBar()
    assert status_bar is not None
    assert status_bar.currentMessage() == f"Key down: Ctrl+X; layer 0; matches: {DUAL_9_X_INDEX}"

    window._handle_hook_release(keyboard.KeyCode.from_char("x"))
    window._handle_hook_release(keyboard.Key.ctrl)

    assert window._keyboard.pressed_indexes() == []


def test_repeated_press_does_not_retoggle_state() -> None:
    window = MainWindow(start_hook=False, hook_factory=FakeHook)
    window.load_layout_path(SAMPLE_KEYMAP)

    window._handle_hook_press(keyboard.KeyCode.from_char("a"))
    window._handle_hook_press(keyboard.KeyCode.from_char("a"))

    assert window._keyboard.pressed_indexes() == [29]


def test_press_without_loaded_layout_is_noop() -> None:
    window = MainWindow(start_hook=False, hook_factory=FakeHook)

    window._handle_hook_press(keyboard.KeyCode.from_char("a"))

    assert window._keyboard.pressed_indexes() == []
    status_bar = window.statusBar()
    assert status_bar is not None
    assert status_bar.currentMessage() == "Key down: KC_A; no layout loaded"


def test_unsupported_event_reports_status() -> None:
    window = MainWindow(start_hook=False, hook_factory=FakeHook)

    window._handle_hook_press(object())

    status_bar = window.statusBar()
    assert status_bar is not None
    assert status_bar.currentMessage().startswith("Key down ignored: unsupported event")
    assert window._key_event_log.entries()[-1].event_type == "ignored"


def test_observable_mo_action_updates_active_layer_and_resets_on_release() -> None:
    window = MainWindow(start_hook=False, hook_factory=FakeHook)
    window.load_layout_path(SAMPLE_KEYMAP)
    assert window._layout_model is not None
    window._layout_model.layers[0].keys[29].layer_action = LayerAction("MO", 1)

    window._handle_hook_press(keyboard.KeyCode.from_char("a"))

    assert window._active_layer_index == 1

    window._handle_hook_release(keyboard.KeyCode.from_char("a"))

    assert window._active_layer_index == 0
