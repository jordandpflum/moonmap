"""Map host keyboard events to parsed Moonlander key indexes."""

from __future__ import annotations

import re
from typing import Any

from moonmap.layout.models import Layout

_QMK_ALIAS_TO_CANONICAL = {
    "KC_BSPC": "KC_BACKSPACE",
    "KC_DEL": "KC_DELETE",
    "KC_ENT": "KC_ENTER",
    "KC_ESC": "KC_ESCAPE",
    "KC_INS": "KC_INSERT",
    "KC_LEFT": "KC_LEFT",
    "KC_PGDN": "KC_PAGE_DOWN",
    "KC_PGUP": "KC_PAGE_UP",
    "KC_PSCR": "KC_PRINT_SCREEN",
    "KC_SPC": "KC_SPACE",
    "KC_TRNS": "KC_TRANSPARENT",
}

_PYNPUT_SPECIAL_TO_QMK = {
    "alt": "KC_LEFT_ALT",
    "alt_l": "KC_LEFT_ALT",
    "alt_r": "KC_RIGHT_ALT",
    "backspace": "KC_BACKSPACE",
    "caps_lock": "KC_CAPS_LOCK",
    "cmd": "KC_LEFT_GUI",
    "cmd_l": "KC_LEFT_GUI",
    "cmd_r": "KC_RIGHT_GUI",
    "ctrl": "KC_LEFT_CTRL",
    "ctrl_l": "KC_LEFT_CTRL",
    "ctrl_r": "KC_RIGHT_CTRL",
    "delete": "KC_DELETE",
    "down": "KC_DOWN",
    "end": "KC_END",
    "enter": "KC_ENTER",
    "esc": "KC_ESCAPE",
    "home": "KC_HOME",
    "insert": "KC_INSERT",
    "left": "KC_LEFT",
    "page_down": "KC_PAGE_DOWN",
    "page_up": "KC_PAGE_UP",
    "right": "KC_RIGHT",
    "shift": "KC_LEFT_SHIFT",
    "shift_l": "KC_LEFT_SHIFT",
    "shift_r": "KC_RIGHT_SHIFT",
    "space": "KC_SPACE",
    "tab": "KC_TAB",
    "up": "KC_UP",
}

_PUNCTUATION_TO_QMK = {
    " ": "KC_SPACE",
    "`": "KC_GRAVE",
    "~": "KC_GRAVE",
    "-": "KC_MINUS",
    "_": "KC_MINUS",
    "=": "KC_EQUAL",
    "+": "KC_EQUAL",
    "[": "KC_LEFT_BRACKET",
    "{": "KC_LEFT_BRACKET",
    "]": "KC_RIGHT_BRACKET",
    "}": "KC_RIGHT_BRACKET",
    "\\": "KC_BACKSLASH",
    "|": "KC_BACKSLASH",
    ";": "KC_SEMICOLON",
    ":": "KC_SEMICOLON",
    "'": "KC_QUOTE",
    '"': "KC_QUOTE",
    ",": "KC_COMMA",
    "<": "KC_COMMA",
    ".": "KC_DOT",
    ">": "KC_DOT",
    "/": "KC_SLASH",
    "?": "KC_SLASH",
}

_SHIFTED_DIGITS_TO_QMK = {
    "!": "KC_1",
    "@": "KC_2",
    "#": "KC_3",
    "$": "KC_4",
    "%": "KC_5",
    "^": "KC_6",
    "&": "KC_7",
    "*": "KC_8",
    "(": "KC_9",
    ")": "KC_0",
}

_LONG_QMK_NAMES = {
    "KC_BACKSLASH": "KC_BSLS",
    "KC_CAPS_LOCK": "KC_CAPS",
    "KC_DELETE": "KC_DEL",
    "KC_ESCAPE": "KC_ESC",
    "KC_INSERT": "KC_INS",
    "KC_LEFT_ALT": "KC_LALT",
    "KC_LEFT_BRACKET": "KC_LBRC",
    "KC_LEFT_CTRL": "KC_LCTL",
    "KC_LEFT_GUI": "KC_LGUI",
    "KC_LEFT_SHIFT": "KC_LSFT",
    "KC_PAGE_DOWN": "KC_PGDN",
    "KC_PAGE_UP": "KC_PGUP",
    "KC_PRINT_SCREEN": "KC_PSCR",
    "KC_RIGHT_ALT": "KC_RALT",
    "KC_RIGHT_BRACKET": "KC_RBRC",
    "KC_RIGHT_CTRL": "KC_RCTL",
    "KC_RIGHT_GUI": "KC_RGUI",
    "KC_RIGHT_SHIFT": "KC_RSFT",
    "KC_SEMICOLON": "KC_SCLN",
    "KC_SPACE": "KC_SPC",
}

_QMK_WRAPPER_RE = re.compile(r"^(?:LT|MT)\([^,]+,\s*(.+)\)$")


def normalize_pynput_key(key: Any) -> str | None:
    """Normalize a pynput key object to a canonical QMK-like keycode."""
    char = getattr(key, "char", None)
    if isinstance(char, str) and len(char) == 1:
        return _normalize_char(char)

    name = getattr(key, "name", None)
    if isinstance(name, str):
        if re.fullmatch(r"f\d{1,2}", name):
            return f"KC_{name.upper()}"
        return _canonicalize_qmk_code(_PYNPUT_SPECIAL_TO_QMK.get(name))

    return None


def normalize_qmk_code(code: str) -> str | None:
    """Normalize a parsed QMK keycode to the same canonical form as pynput keys."""
    code = code.strip()
    wrapper = _QMK_WRAPPER_RE.match(code)
    if wrapper:
        code = wrapper.group(1).strip()

    return _canonicalize_qmk_code(code)


def find_matching_key_indexes(
    layout: Layout,
    layer_index: int,
    normalized_code: str | None,
) -> list[int]:
    """Return all physical indexes matching a normalized host key on a layout layer."""
    if normalized_code is None:
        return []

    layer = next((candidate for candidate in layout.layers if candidate.index == layer_index), None)
    if layer is None:
        return []

    return [
        key.index
        for key in layer.keys
        if normalize_qmk_code(key.code) == normalized_code
    ]


def _normalize_char(char: str) -> str | None:
    if char.isalpha():
        return f"KC_{char.upper()}"
    if char.isdigit():
        return f"KC_{char}"
    if char in _SHIFTED_DIGITS_TO_QMK:
        return _SHIFTED_DIGITS_TO_QMK[char]
    return _canonicalize_qmk_code(_PUNCTUATION_TO_QMK.get(char))


def _canonicalize_qmk_code(code: str | None) -> str | None:
    if code is None:
        return None

    code = code.strip()
    if not code.startswith("KC_"):
        return None

    code = _LONG_QMK_NAMES.get(code, code)
    return _QMK_ALIAS_TO_CANONICAL.get(code, code)
