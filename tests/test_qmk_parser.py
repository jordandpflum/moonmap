from __future__ import annotations

from pathlib import Path

import pytest

from moonmap.layout.qmk_parser import parse_keymap_c

SAMPLE_KEYMAP = (
    Path(__file__).resolve().parents[1]
    / "sample_source_layouts"
    / "zsa_moonlander_reva_NmOnd_nlv3L0_full-featured-qwerty-writing-lay_source"
    / "zsa_moonlander_full-featured-qwerty-writing-lay_source"
    / "keymap.c"
)
EXPECTED_LAYER_COUNT = 5
EXPECTED_KEY_COUNT = 72
MO_TARGET_LAYER = 2
TG_TARGET_LAYER = 3


def test_sample_oryx_keymap_parses_all_layers_with_72_keys() -> None:
    layout = parse_keymap_c(SAMPLE_KEYMAP)

    assert layout.layer_count == EXPECTED_LAYER_COUNT
    assert [(layer.index, len(layer.keys)) for layer in layout.layers] == [
        (0, EXPECTED_KEY_COUNT),
        (1, EXPECTED_KEY_COUNT),
        (2, EXPECTED_KEY_COUNT),
        (3, EXPECTED_KEY_COUNT),
        (4, EXPECTED_KEY_COUNT),
    ]


def test_nested_qmk_calls_stay_single_physical_key_tokens() -> None:
    layout = parse_keymap_c(SAMPLE_KEYMAP)
    layer = layout.layers[0]

    assert layer.keys[28].code == "MT(MOD_LCTL, KC_ESCAPE)"
    assert layer.keys[60].code == "LT(4, KC_ENTER)"
    assert layer.keys[66].code == "MT(MOD_LALT, KC_HOME)"
    assert layer.keys[71].code == "MT(MOD_RALT, KC_BSPC)"


def test_sample_oryx_ledmap_is_imported_as_per_key_rgb() -> None:
    layout = parse_keymap_c(SAMPLE_KEYMAP)

    assert layout.layers[0].keys[0].led_color == (108, 0, 255)
    assert layout.layers[0].keys[7].led_color == (0, 114, 255)
    assert layout.layers[4].keys[71].led_color == (255, 150, 0)


def test_display_splits_shift_tap_and_hold_legends() -> None:
    layout = parse_keymap_c(SAMPLE_KEYMAP)
    layer = layout.layers[0]

    assert layer.keys[60].display.main == "⏎"
    assert layer.keys[60].display.hold == "L4"
    assert layer.keys[62].display.main == "↓"
    assert layer.keys[63].display.main == "↑"
    assert layer.keys[71].display.main == "⌫"
    assert layer.keys[71].display.hold == "RAlt"
    assert layer.keys[52].display.shifted == "?"


def test_oryx_dual_function_cases_are_displayed_as_tap_hold() -> None:
    layout = parse_keymap_c(SAMPLE_KEYMAP)

    dual_key = layout.layers[0].keys[55]

    assert dual_key.code == "DUAL_FUNC_0"
    assert dual_key.display.main == "Ctl+`"
    assert dual_key.display.hold == "Ctl+V"
    assert "tap raw: LCTL(KC_GRAVE)" in dual_key.display.detail
    assert "hold raw: LCTL(KC_V)" in dual_key.display.detail


def test_only_mo_and_tg_create_layer_actions(tmp_path: Path) -> None:
    keymap = tmp_path / "keymap.c"
    keymap.write_text(
        """
        const uint16_t PROGMEM keymaps[][MATRIX_ROWS][MATRIX_COLS] = {
          // NAV
          [1] = LAYOUT_moonlander(
            MO(2), TG(3), LT(4, KC_ENTER), TT(5), TO(0), MT(MOD_LCTL, KC_ESCAPE)
          ),
        };
        """,
        encoding="utf-8",
    )

    layer = parse_keymap_c(keymap).layers[0]

    assert layer.name == "NAV"
    assert [key.code for key in layer.keys] == [
        "MO(2)",
        "TG(3)",
        "LT(4, KC_ENTER)",
        "TT(5)",
        "TO(0)",
        "MT(MOD_LCTL, KC_ESCAPE)",
    ]
    assert layer.keys[0].layer_action is not None
    assert layer.keys[0].layer_action.type == "MO"
    assert layer.keys[0].layer_action.target_layer == MO_TARGET_LAYER
    assert layer.keys[1].layer_action is not None
    assert layer.keys[1].layer_action.type == "TG"
    assert layer.keys[1].layer_action.target_layer == TG_TARGET_LAYER
    assert [key.layer_action for key in layer.keys[2:]] == [None, None, None, None]


def test_inline_and_block_comments_are_ignored(tmp_path: Path) -> None:
    keymap = tmp_path / "keymap.c"
    keymap.write_text(
        """
        const uint16_t PROGMEM keymaps[][MATRIX_ROWS][MATRIX_COLS] = {
          [0] = LAYOUT_moonlander(
            KC_A, // home key
            /* punctuation */ KC_B,
            MT(MOD_LCTL, KC_ESCAPE)
          ),
        };
        """,
        encoding="utf-8",
    )

    layer = parse_keymap_c(keymap).layers[0]

    assert [key.code for key in layer.keys] == [
        "KC_A",
        "KC_B",
        "MT(MOD_LCTL, KC_ESCAPE)",
    ]


def test_missing_keymaps_array_raises_descriptive_error(tmp_path: Path) -> None:
    keymap = tmp_path / "keymap.c"
    keymap.write_text("const int unrelated = 1;", encoding="utf-8")

    with pytest.raises(ValueError, match="No 'keymaps' array found"):
        parse_keymap_c(keymap)


def test_missing_moonlander_layout_raises_descriptive_error(tmp_path: Path) -> None:
    keymap = tmp_path / "keymap.c"
    keymap.write_text(
        """
        const uint16_t PROGMEM keymaps[][MATRIX_ROWS][MATRIX_COLS] = {
          [0] = LAYOUT_planck_grid(KC_A)
        };
        """,
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="No LAYOUT_moonlander layers found"):
        parse_keymap_c(keymap)
