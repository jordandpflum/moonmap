from __future__ import annotations

from pathlib import Path

from moonmap.layout.key_meanings import meaning_for_key
from moonmap.layout.models import KeyDisplay
from moonmap.layout.qmk_parser import parse_keymap_c

SAMPLE_KEYMAP = (
    Path(__file__).resolve().parents[1]
    / "sample_source_layouts"
    / "zsa_moonlander_reva_NmOnd_nlv3L0_full-featured-qwerty-writing-lay_source"
    / "zsa_moonlander_full-featured-qwerty-writing-lay_source"
    / "keymap.c"
)


def test_mouse_key_meanings() -> None:
    assert meaning_for_key("KC_MS_UP", KeyDisplay()) == "Move mouse pointer up."
    assert meaning_for_key("KC_MS_WH_DOWN", KeyDisplay()) == "Scroll mouse wheel down."
    assert meaning_for_key("KC_MS_BTN1", KeyDisplay()) == "Mouse button 1, usually left click."


def test_layer_control_meanings() -> None:
    assert meaning_for_key("MO(4)", KeyDisplay()) == "Momentarily activates layer 4 while held."
    assert meaning_for_key("TT(3)", KeyDisplay()) == "Tap toggles layer 3; hold momentarily activates layer 3."
    assert meaning_for_key("TO(0)", KeyDisplay()) == "Switches directly to layer 0."


def test_tap_hold_wrapper_meanings() -> None:
    assert (
        meaning_for_key(
            "LT(4, KC_ENTER)",
            KeyDisplay(tap_raw="KC_ENTER", hold_raw="Layer 4"),
        )
        == "Tap sends Enter; hold activates layer 4."
    )
    assert (
        meaning_for_key(
            "MT(MOD_LCTL, KC_ESCAPE)",
            KeyDisplay(tap_raw="KC_ESCAPE", hold_raw="MOD_LCTL"),
        )
        == "Tap sends Escape; hold acts as Left Ctrl."
    )


def test_modifier_wrapper_meaning() -> None:
    assert meaning_for_key("LCTL(LSFT(KC_RIGHT))", KeyDisplay()) == "Sends Ctrl+Shift+Right Arrow."


def test_qmk_toggle_and_system_meanings() -> None:
    assert meaning_for_key("CW_TOGG", KeyDisplay()) == "Toggle Caps Word mode."
    assert meaning_for_key("AS_TOGG", KeyDisplay()) == "Toggle Auto Shift mode."
    assert meaning_for_key("QK_BOOT", KeyDisplay()) == "Put the keyboard into bootloader mode for flashing firmware."
    assert (
        meaning_for_key("SC_LSPO", KeyDisplay())
        == "Space Cadet left shift: tap for left parenthesis, hold for left shift."
    )


def test_keypad_and_unknown_custom_meanings() -> None:
    assert meaning_for_key("KC_KP_7", KeyDisplay()) == "Numeric keypad 7."
    assert meaning_for_key("CUSTOM_THING", KeyDisplay()) == "Custom keycode; no built-in meaning yet."
    assert meaning_for_key("KC_A", KeyDisplay()) == ""


def test_sample_keymap_nontrivial_keys_have_meanings_or_custom_fallback() -> None:
    layout = parse_keymap_c(SAMPLE_KEYMAP)
    prefixes = (
        "KC_MS_",
        "KC_AUDIO_",
        "KC_MEDIA_",
        "KC_KP_",
        "RGB_",
        "QK_",
        "AS_",
        "SC_",
        "CW_",
        "TOGGLE_",
        "MO(",
        "TG(",
        "TT(",
        "TO(",
        "LT(",
        "MT(",
        "OSM(",
        "LCTL(",
        "LGUI(",
        "DUAL_FUNC",
    )
    missing = [
        key.code
        for layer in layout.layers
        for key in layer.keys
        if key.code.startswith(prefixes) and not meaning_for_key(key.code, key.display)
    ]

    assert missing == []
