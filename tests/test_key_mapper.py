from __future__ import annotations

from pathlib import Path

from pynput import keyboard

from moonmap.input.key_mapper import (
    effective_key_for_index,
    find_matching_key_matches,
    find_matching_key_indexes,
    host_inputs_for_key,
    normalize_pynput_key,
    normalize_qmk_code,
)
from moonmap.layout.models import Key, KeyDisplay, Layer, Layout
from moonmap.layout.qmk_parser import parse_keymap_c

SAMPLE_KEYMAP = (
    Path(__file__).resolve().parents[1]
    / "sample_source_layouts"
    / "zsa_moonlander_reva_NmOnd_nlv3L0_full-featured-qwerty-writing-lay_source"
    / "zsa_moonlander_full-featured-qwerty-writing-lay_source"
    / "keymap.c"
)


def test_normalize_pynput_printable_keys() -> None:
    assert normalize_pynput_key(keyboard.KeyCode.from_char("a")) == "KC_A"
    assert normalize_pynput_key(keyboard.KeyCode.from_char("A")) == "KC_A"
    assert normalize_pynput_key(keyboard.KeyCode.from_char("1")) == "KC_1"
    assert normalize_pynput_key(keyboard.KeyCode.from_char("!")) == "KC_1"
    assert normalize_pynput_key(keyboard.KeyCode.from_char("?")) == "KC_SLASH"


def test_normalize_pynput_special_keys() -> None:
    assert normalize_pynput_key(keyboard.Key.space) == "KC_SPACE"
    assert normalize_pynput_key(keyboard.Key.enter) == "KC_ENTER"
    assert normalize_pynput_key(keyboard.Key.esc) == "KC_ESCAPE"
    assert normalize_pynput_key(keyboard.Key.page_down) == "KC_PAGE_DOWN"
    assert normalize_pynput_key(keyboard.Key.f1) == "KC_F1"


def test_normalize_pynput_windows_keypad_virtual_keys() -> None:
    assert normalize_pynput_key(keyboard.KeyCode.from_vk(103)) == "KC_7"
    assert normalize_pynput_key(keyboard.KeyCode.from_vk(111)) == "KC_SLASH"
    assert normalize_pynput_key(keyboard.KeyCode.from_vk(107)) == "KC_EQUAL"


def test_normalize_qmk_aliases_and_wrappers() -> None:
    assert normalize_qmk_code("KC_SPC") == "KC_SPACE"
    assert normalize_qmk_code("KC_ESC") == "KC_ESCAPE"
    assert normalize_qmk_code("KC_ENT") == "KC_ENTER"
    assert normalize_qmk_code("KC_KP_7") == "KC_7"
    assert normalize_qmk_code("KC_KP_SLASH") == "KC_SLASH"
    assert normalize_qmk_code("KC_KP_ENTER") == "KC_ENTER"
    assert normalize_qmk_code("LT(3, KC_SPACE)") == "KC_SPACE"
    assert normalize_qmk_code("MT(MOD_LCTL, KC_ESCAPE)") == "KC_ESCAPE"
    assert normalize_qmk_code("MO(4)") is None


def test_find_matching_key_indexes_returns_all_duplicates() -> None:
    layout = Layout(
        layers=[
            Layer(
                index=0,
                name="BASE",
                keys=[
                    Key(index=0, label="A", code="KC_A"),
                    Key(index=1, label="Other A", code="KC_A"),
                    Key(index=2, label="Space", code="LT(1, KC_SPACE)"),
                ],
            ),
        ],
    )

    assert find_matching_key_indexes(layout, 0, "KC_A") == [0, 1]
    assert find_matching_key_indexes(layout, 0, "KC_SPACE") == [2]
    assert find_matching_key_indexes(layout, 99, "KC_A") == []


def test_find_matching_key_indexes_resolves_transparent_lower_layer_fallback() -> None:
    layout = Layout(
        layers=[
            Layer(
                index=0,
                name="BASE",
                keys=[
                    Key(index=0, label="A", code="KC_A"),
                    Key(index=1, label="B", code="KC_B"),
                ],
            ),
            Layer(
                index=1,
                name="NAV",
                keys=[
                    Key(index=0, label="", code="KC_TRANSPARENT"),
                    Key(index=1, label="Esc", code="KC_ESCAPE"),
                ],
            ),
        ],
    )

    assert effective_key_for_index(layout, 1, 0) == layout.layers[0].keys[0]
    assert find_matching_key_indexes(layout, 1, "KC_A") == [0]
    assert find_matching_key_indexes(layout, 1, "KC_ESCAPE") == [1]


def test_find_matching_key_indexes_matches_keypad_output_to_printable_host_keys() -> None:
    layout = Layout(
        layers=[
            Layer(
                index=2,
                name="NUMPAD",
                keys=[
                    Key(index=0, label="7", code="KC_KP_7"),
                    Key(index=1, label="/", code="KC_KP_SLASH"),
                ],
            ),
        ],
    )

    assert find_matching_key_indexes(layout, 2, normalize_pynput_key(keyboard.KeyCode.from_char("7"))) == [0]
    assert find_matching_key_indexes(layout, 2, normalize_pynput_key(keyboard.KeyCode.from_char("/"))) == [1]
    assert find_matching_key_indexes(layout, 2, normalize_pynput_key(keyboard.KeyCode.from_vk(103))) == [0]
    assert find_matching_key_indexes(layout, 2, normalize_pynput_key(keyboard.KeyCode.from_vk(111))) == [1]


def test_matching_uses_dual_function_tap_raw_actions() -> None:
    layout = parse_keymap_c(SAMPLE_KEYMAP)

    assert find_matching_key_indexes(layout, 0, "KC_9") == [56]
    assert find_matching_key_indexes(layout, 0, "KC_0") == [57]


def test_matching_uses_dual_function_hold_raw_chords() -> None:
    layout = parse_keymap_c(SAMPLE_KEYMAP)

    matches = find_matching_key_matches(
        layout,
        0,
        "KC_X",
        {"CTRL"},
        include_all_layers=False,
    )

    assert [match.key.index for match in matches] == [56]


def test_matching_supports_nested_modifier_chords() -> None:
    layout = parse_keymap_c(SAMPLE_KEYMAP)

    matches = find_matching_key_matches(
        layout,
        3,
        "KC_RIGHT",
        {"CTRL", "SHIFT"},
        include_all_layers=False,
    )

    assert [match.key.index for match in matches] == [39]


def test_all_layer_matches_keep_active_layer_first() -> None:
    layout = Layout(
        layers=[
            Layer(index=0, name="BASE", keys=[Key(index=0, label="A", code="KC_A")]),
            Layer(index=1, name="NAV", keys=[Key(index=0, label="B", code="KC_B")]),
            Layer(index=2, name="ALT", keys=[Key(index=0, label="A", code="KC_A")]),
        ],
    )

    matches = find_matching_key_matches(layout, 2, "KC_A", include_all_layers=True)

    assert [(match.layer_index, match.key.index, match.is_active_layer) for match in matches] == [
        (2, 0, True),
        (0, 0, False),
    ]


def test_host_inputs_for_key_includes_tap_and_hold_actions() -> None:
    key = Key(
        index=0,
        label="Dual",
        code="DUAL_FUNC_1",
        display=KeyDisplay(tap_raw="KC_9", hold_raw="LCTL(KC_X)"),
    )

    assert host_inputs_for_key(key) == ["9", "Ctrl+X"]
