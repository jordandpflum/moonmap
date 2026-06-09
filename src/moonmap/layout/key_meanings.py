"""Plain-language descriptions for non-obvious QMK keycodes."""

from __future__ import annotations

import re

from moonmap.layout.models import KeyDisplay

_ALIASES = {
    "_______": "KC_TRNS",
    "XXXXXXX": "KC_NO",
    "KC_TRANSPARENT": "KC_TRNS",
    "KC_SPACE": "KC_SPC",
    "KC_ENTER": "KC_ENT",
    "KC_ESCAPE": "KC_ESC",
    "KC_BACKSPACE": "KC_BSPC",
    "KC_DELETE": "KC_DEL",
    "KC_INSERT": "KC_INS",
    "KC_LEFT_BRACKET": "KC_LBRC",
    "KC_RIGHT_BRACKET": "KC_RBRC",
    "KC_BACKSLASH": "KC_BSLS",
    "KC_SEMICOLON": "KC_SCLN",
    "KC_PAGE_UP": "KC_PGUP",
    "KC_PAGE_DOWN": "KC_PGDN",
    "KC_PRINT_SCREEN": "KC_PSCR",
}

_MODIFIERS = {
    "MOD_LCTL": "Left Ctrl",
    "MOD_RCTL": "Right Ctrl",
    "MOD_LSFT": "Left Shift",
    "MOD_RSFT": "Right Shift",
    "MOD_LALT": "Left Alt",
    "MOD_RALT": "Right Alt",
    "MOD_LGUI": "Left GUI",
    "MOD_RGUI": "Right GUI",
}

_MOD_WRAPPERS = {
    "LCTL": "Ctrl",
    "RCTL": "Ctrl",
    "LSFT": "Shift",
    "RSFT": "Shift",
    "LALT": "Alt",
    "RALT": "Alt",
    "LGUI": "GUI",
    "RGUI": "GUI",
}

_MOUSE_MEANINGS = {
    "KC_MS_UP": "Move mouse pointer up.",
    "KC_MS_DOWN": "Move mouse pointer down.",
    "KC_MS_LEFT": "Move mouse pointer left.",
    "KC_MS_RIGHT": "Move mouse pointer right.",
    "KC_MS_WH_UP": "Scroll mouse wheel up.",
    "KC_MS_WH_DOWN": "Scroll mouse wheel down.",
    "KC_MS_WH_LEFT": "Scroll mouse wheel left.",
    "KC_MS_WH_RIGHT": "Scroll mouse wheel right.",
    "KC_MS_BTN1": "Mouse button 1, usually left click.",
    "KC_MS_BTN2": "Mouse button 2, usually right click.",
    "KC_MS_BTN3": "Mouse button 3, usually middle click.",
    "KC_MS_BTN4": "Mouse button 4, usually browser back.",
    "KC_MS_BTN5": "Mouse button 5, usually browser forward.",
    "KC_MS_ACCEL0": "Use mouse key acceleration profile 0.",
    "KC_MS_ACCEL1": "Use mouse key acceleration profile 1.",
    "KC_MS_ACCEL2": "Use mouse key acceleration profile 2.",
}

_STATIC_MEANINGS = {
    "KC_AUDIO_MUTE": "Mute or unmute system audio.",
    "KC_AUDIO_VOL_UP": "Increase system volume.",
    "KC_AUDIO_VOL_DOWN": "Decrease system volume.",
    "KC_MEDIA_PREV_TRACK": "Go to previous media track.",
    "KC_MEDIA_NEXT_TRACK": "Go to next media track.",
    "KC_MEDIA_PLAY_PAUSE": "Play or pause media.",
    "KC_MEDIA_STOP": "Stop media playback.",
    "RGB_VAI": "Increase keyboard RGB brightness.",
    "RGB_VAD": "Decrease keyboard RGB brightness.",
    "RGB_SLD": "Set RGB lighting to a solid color mode.",
    "QK_BOOT": "Put the keyboard into bootloader mode for flashing firmware.",
    "CW_TOGG": "Toggle Caps Word mode.",
    "AS_TOGG": "Toggle Auto Shift mode.",
    "SC_LSPO": "Space Cadet left shift: tap for left parenthesis, hold for left shift.",
    "SC_RSPC": "Space Cadet right shift: tap for right parenthesis, hold for right shift.",
    "KC_TRNS": "Transparent: use the key from the next lower active layer.",
    "KC_NO": "No key action.",
    "TOGGLE_LAYER_COLOR": "Toggle whether the keyboard uses the per-layer LED colors.",
}

_KEY_NAMES = {
    "KC_SPC": "Space",
    "KC_ENT": "Enter",
    "KC_ESC": "Escape",
    "KC_BSPC": "Backspace",
    "KC_DEL": "Delete",
    "KC_TAB": "Tab",
    "KC_LEFT": "Left Arrow",
    "KC_RIGHT": "Right Arrow",
    "KC_UP": "Up Arrow",
    "KC_DOWN": "Down Arrow",
    "KC_PGUP": "Page Up",
    "KC_PGDN": "Page Down",
    "KC_HOME": "Home",
    "KC_END": "End",
    "KC_INS": "Insert",
    "KC_PSCR": "Print Screen",
    "KC_LCBR": "Left Brace",
    "KC_RCBR": "Right Brace",
    "KC_LBRC": "Left Bracket",
    "KC_RBRC": "Right Bracket",
}


def meaning_for_key(code: str, display: KeyDisplay) -> str:  # noqa: PLR0911
    """Return a plain-language description for a non-obvious keycode."""
    raw_code = code.strip()
    canonical = _canonical_code(raw_code)

    layer_meaning = _layer_meaning(raw_code)
    if layer_meaning:
        return layer_meaning

    if raw_code.startswith("LT(") and display.tap_raw and display.hold_raw:
        return f"Tap sends {_action_name(display.tap_raw)}; hold activates {display.hold_raw.lower()}."

    if raw_code.startswith("MT(") and display.tap_raw and display.hold_raw:
        return f"Tap sends {_action_name(display.tap_raw)}; hold acts as {_modifier_name(display.hold_raw)}."

    osm_match = re.fullmatch(r"OSM\(([^)]+)\)", raw_code)
    if osm_match:
        return f"One-shot {_modifier_name(osm_match.group(1))}: applies to the next key press."

    if display.tap_raw or display.hold_raw:
        return _tap_hold_meaning(display)

    modifier_chord = _modifier_chord_meaning(raw_code)
    if modifier_chord:
        return modifier_chord

    if canonical.startswith("KC_KP_"):
        return f"Numeric keypad {_keypad_name(canonical)}."

    if canonical in _MOUSE_MEANINGS:
        return _MOUSE_MEANINGS[canonical]

    if canonical in _STATIC_MEANINGS:
        return _STATIC_MEANINGS[canonical]

    if _is_unknown_custom_code(raw_code):
        return "Custom keycode; no built-in meaning yet."

    return ""


def _canonical_code(code: str) -> str:
    return _ALIASES.get(code.strip(), code.strip())


def _layer_meaning(code: str) -> str:
    match = re.fullmatch(r"(MO|TG|TT|TO)\((\d+)\)", code.strip())
    if match is None:
        return ""

    action, layer = match.groups()
    meanings = {
        "MO": f"Momentarily activates layer {layer} while held.",
        "TG": f"Toggles layer {layer} on or off.",
        "TT": f"Tap toggles layer {layer}; hold momentarily activates layer {layer}.",
        "TO": f"Switches directly to layer {layer}.",
    }
    return meanings[action]


def _tap_hold_meaning(display: KeyDisplay) -> str:
    parts = []
    if display.tap_raw:
        parts.append(f"Tap sends {_action_name(display.tap_raw)}")
    if display.hold_raw:
        parts.append(f"hold sends {_action_name(display.hold_raw)}")
    return "; ".join(parts) + "." if parts else ""


def _modifier_chord_meaning(code: str) -> str:
    parsed = _parse_modifier_chord(code)
    if parsed is None:
        return ""
    modifiers, key = parsed
    return f"Sends {'+'.join(modifiers)}+{_key_name(key)}."


def _parse_modifier_chord(code: str) -> tuple[list[str], str] | None:
    modifiers: list[str] = []
    current = code.strip()
    while True:
        match = re.fullmatch(r"([LR](?:CTL|SFT|ALT|GUI))\((.*)\)", current)
        if match is None:
            break
        modifiers.append(_MOD_WRAPPERS.get(match.group(1), match.group(1)))
        current = match.group(2).strip()

    if not modifiers:
        return None
    return modifiers, current


def _action_name(code: str) -> str:
    code = code.strip()
    layer_match = re.fullmatch(r"layer_(?:on|off|move)\((\d+)\)", code)
    if layer_match:
        return f"layer {layer_match.group(1)}"
    chord = _parse_modifier_chord(code)
    if chord is not None:
        modifiers, key = chord
        return f"{'+'.join(modifiers)}+{_key_name(key)}"
    return _key_name(code)


def _modifier_name(code: str) -> str:
    return _MODIFIERS.get(code.strip(), _key_name(code))


def _key_name(code: str) -> str:  # noqa: PLR0911
    code = _canonical_code(code)
    if code in _KEY_NAMES:
        return _KEY_NAMES[code]
    digit_match = re.fullmatch(r"KC_KP_(\d)", code)
    if digit_match:
        return f"keypad {digit_match.group(1)}"
    if code == "KC_KP_SLASH":
        return "keypad slash"
    if code == "KC_KP_ASTERISK":
        return "keypad asterisk"
    if code == "KC_KP_MINUS":
        return "keypad minus"
    if code == "KC_KP_PLUS":
        return "keypad plus"
    if code == "KC_KP_ENTER":
        return "keypad Enter"
    if code == "KC_KP_DOT":
        return "keypad decimal"
    letter_match = re.fullmatch(r"KC_([A-Z0-9])", code)
    if letter_match:
        return letter_match.group(1)
    function_match = re.fullmatch(r"KC_F(\d+)", code)
    if function_match:
        return f"F{function_match.group(1)}"
    if code.startswith("KC_"):
        return code[3:].replace("_", " ").title()
    return code.replace("_", " ").title()


def _keypad_name(code: str) -> str:
    digit_match = re.fullmatch(r"KC_KP_(\d)", code)
    if digit_match:
        return digit_match.group(1)
    names = {
        "KC_KP_SLASH": "slash",
        "KC_KP_ASTERISK": "asterisk",
        "KC_KP_MINUS": "minus",
        "KC_KP_PLUS": "plus",
        "KC_KP_ENTER": "Enter",
        "KC_KP_DOT": "decimal",
    }
    return names.get(code, _key_name(code))


def _is_unknown_custom_code(code: str) -> bool:
    return bool(re.fullmatch(r"[A-Z][A-Z0-9_]*", code)) and not code.startswith("KC_")
