from __future__ import annotations

from pynput import keyboard

from moonmap.input.key_mapper import (
    effective_key_for_index,
    find_matching_key_indexes,
    normalize_pynput_key,
    normalize_qmk_code,
)
from moonmap.layout.models import Key, Layer, Layout


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
