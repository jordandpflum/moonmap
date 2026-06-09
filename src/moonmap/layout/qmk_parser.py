"""Parses a QMK keymap.c file (as downloaded from Oryx) into the internal Layout model.

Expected format:
    const uint16_t PROGMEM keymaps[][MATRIX_ROWS][MATRIX_COLS] = {
        [0] = LAYOUT_moonlander(
            KC_ESC, KC_1, ...,
            ...
        ),
        [1] = LAYOUT_moonlander(
            ...
        ),
    };

Layer names are extracted from preceding comments if present, e.g.:
    // BASE
    [0] = LAYOUT_moonlander(
"""

from __future__ import annotations

import json
import re
from colorsys import hsv_to_rgb
from pathlib import Path
from typing import Any

from .models import Key, KeyDisplay, Layer, LayerAction, Layout, RgbColor

# Matches: MO(n) or TG(n)
_LAYER_ACTION_RE = re.compile(r"^(MO|TG)\((\d+)\)$")

# Matches: [n] = LAYOUT_moonlander( or [BASE] = LAYOUT_moonlander(
_LAYER_HEADER_RE = re.compile(r"\[([A-Za-z_][A-Za-z0-9_]*|\d+)\]\s*=\s*LAYOUT_moonlander\s*\(")

# Matches a comment line like: // BASE or /* NAV */
_COMMENT_RE = re.compile(r"//\s*(\w+)|/\*\s*(\w+)\s*\*/")

_DUAL_FUNC_DEFINE_RE = re.compile(r"^#define\s+(DUAL_FUNC_\d+)\s+(.+)$", re.MULTILINE)
_CASE_RE = re.compile(r"case\s+(DUAL_FUNC_\d+)\s*:")
_TRIPLE_RE = re.compile(r"\{\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\}")
_WRAPPER_ARG_COUNT = 2
_MOONLANDER_KEY_COUNT = 72
_MOONLANDER_KEY_TO_LED_INDEX = (
    0,
    5,
    10,
    15,
    20,
    25,
    29,
    65,
    61,
    56,
    51,
    46,
    41,
    36,
    1,
    6,
    11,
    16,
    21,
    26,
    30,
    66,
    62,
    57,
    52,
    47,
    42,
    37,
    2,
    7,
    12,
    17,
    22,
    27,
    31,
    67,
    63,
    58,
    53,
    48,
    43,
    38,
    3,
    8,
    13,
    18,
    23,
    28,
    64,
    59,
    54,
    49,
    44,
    39,
    4,
    9,
    14,
    19,
    24,
    35,
    71,
    60,
    55,
    50,
    45,
    40,
    32,
    33,
    34,
    70,
    69,
    68,
)

_SHIFTED_SYMBOLS = {
    "KC_GRAVE": "~",
    "KC_1": "!",
    "KC_2": "@",
    "KC_3": "#",
    "KC_4": "$",
    "KC_5": "%",
    "KC_6": "^",
    "KC_7": "&",
    "KC_8": "*",
    "KC_9": "(",
    "KC_0": ")",
    "KC_MINUS": "_",
    "KC_EQUAL": "+",
    "KC_LBRC": "{",
    "KC_RBRC": "}",
    "KC_BSLS": "|",
    "KC_SCLN": ":",
    "KC_QUOTE": '"',
    "KC_COMM": "<",
    "KC_COMMA": "<",
    "KC_DOT": ">",
    "KC_SLSH": "?",
    "KC_SLASH": "?",
}

_ALIASES = {
    "_______": "KC_TRNS",
    "XXXXXXX": "KC_NO",
    "KC_TRANSPARENT": "KC_TRNS",
    "KC_SPACE": "KC_SPC",
    "KC_ENTER": "KC_ENT",
    "KC_ESCAPE": "KC_ESC",
    "KC_BACKSPACE": "KC_BSPC",
    "KC_DELETE": "KC_DEL",
    "KC_LEFT_SHIFT": "KC_LSFT",
    "KC_RIGHT_SHIFT": "KC_RSFT",
    "KC_LEFT_CTRL": "KC_LCTL",
    "KC_RIGHT_CTRL": "KC_RCTL",
    "KC_LEFT_ALT": "KC_LALT",
    "KC_RIGHT_ALT": "KC_RALT",
    "KC_LEFT_GUI": "KC_LGUI",
    "KC_RIGHT_GUI": "KC_RGUI",
    "KC_LEFT_BRACKET": "KC_LBRC",
    "KC_RIGHT_BRACKET": "KC_RBRC",
    "KC_BACKSLASH": "KC_BSLS",
    "KC_SEMICOLON": "KC_SCLN",
    "KC_PAGE_UP": "KC_PGUP",
    "KC_PAGE_DOWN": "KC_PGDN",
    "KC_PRINT_SCREEN": "KC_PSCR",
}

_SYMBOL_LABELS = {
    "KC_TRNS": "",
    "KC_NO": "x",
    "KC_SPC": "⎵",
    "KC_ENT": "⏎",
    "KC_BSPC": "⌫",
    "KC_TAB": "⇥",
    "KC_ESC": "Esc",
    "KC_DEL": "⌦",
    "KC_LSFT": "LSft",
    "KC_RSFT": "RSft",
    "KC_LCTL": "LCtl",
    "KC_RCTL": "RCtl",
    "KC_LALT": "LAlt",
    "KC_RALT": "RAlt",
    "KC_LGUI": "LGui",
    "KC_RGUI": "RGui",
    "KC_LEFT": "←",
    "KC_RIGHT": "→",
    "KC_UP": "↑",
    "KC_DOWN": "↓",
    "KC_PGUP": "PgUp",
    "KC_PGDN": "PgDn",
    "KC_HOME": "Home",
    "KC_END": "End",
    "KC_CAPS": "Caps",
    "KC_INS": "Ins",
    "KC_PSCR": "Prt",
    "KC_SLCK": "ScrLk",
    "KC_PAUS": "Pause",
    "KC_MUTE": "Mute",
    "KC_VOLU": "Vol+",
    "KC_VOLD": "Vol-",
    "KC_AUDIO_MUTE": "Mute",
    "KC_AUDIO_VOL_UP": "Vol+",
    "KC_AUDIO_VOL_DOWN": "Vol-",
    "KC_MEDIA_PREV_TRACK": "Prev",
    "KC_MEDIA_NEXT_TRACK": "Next",
    "KC_MEDIA_PLAY_PAUSE": "Play",
    "KC_MEDIA_STOP": "Stop",
    "KC_MS_UP": "M↑",
    "KC_MS_DOWN": "M↓",
    "KC_MS_LEFT": "M←",
    "KC_MS_RIGHT": "M→",
    "KC_MS_WH_UP": "Wh↑",
    "KC_MS_WH_DOWN": "Wh↓",
    "KC_MS_WH_LEFT": "Wh←",
    "KC_MS_WH_RIGHT": "Wh→",
    "KC_MS_BTN1": "M1",
    "KC_MS_BTN2": "M2",
    "KC_MS_BTN3": "M3",
    "KC_MS_BTN4": "M4",
    "KC_MS_BTN5": "M5",
    "KC_KP_SLASH": "KP/",
    "KC_KP_ASTERISK": "KP*",
    "KC_KP_MINUS": "KP-",
    "KC_KP_PLUS": "KP+",
    "KC_KP_ENTER": "KP⏎",
    "KC_KP_DOT": "KP.",
}

_MOD_LABELS = {
    "MOD_LCTL": "LCtl",
    "MOD_RCTL": "RCtl",
    "MOD_LSFT": "LSft",
    "MOD_RSFT": "RSft",
    "MOD_LALT": "LAlt",
    "MOD_RALT": "RAlt",
    "MOD_LGUI": "LGui",
    "MOD_RGUI": "RGui",
    "KC_LEFT_CTRL": "LCtl",
    "KC_RIGHT_CTRL": "RCtl",
    "KC_LEFT_SHIFT": "LSft",
    "KC_RIGHT_SHIFT": "RSft",
    "KC_LEFT_ALT": "LAlt",
    "KC_RIGHT_ALT": "RAlt",
    "KC_LEFT_GUI": "LGui",
    "KC_RIGHT_GUI": "RGui",
}

_MOD_WRAPPER_LABELS = {
    "LCTL": "Ctl",
    "RCTL": "Ctl",
    "LSFT": "Sft",
    "RSFT": "Sft",
    "LALT": "Alt",
    "RALT": "Alt",
    "LGUI": "Gui",
    "RGUI": "Gui",
}


_DualBehavior = dict[str, str]


def _strip_c_comments(text: str) -> str:
    """Replace C comments with whitespace."""
    text = re.sub(r"//[^\n]*", " ", text)
    return re.sub(r"/\*.*?\*/", " ", text, flags=re.DOTALL)


def _split_top_level_commas(text: str) -> list[str]:
    """Split QMK macro arguments without splitting nested function arguments."""
    tokens: list[str] = []
    current: list[str] = []
    depth = 0

    for char in text:
        if char == "(":
            depth += 1
        elif char == ")" and depth > 0:
            depth -= 1

        if char == "," and depth == 0:
            token = "".join(current).strip()
            if token:
                tokens.append(token)
            current = []
            continue

        current.append(char)

    token = "".join(current).strip()
    if token:
        tokens.append(token)

    return tokens


def _parse_layer_action(code: str) -> LayerAction | None:
    m = _LAYER_ACTION_RE.match(code.strip())
    if m:
        return LayerAction(type=m.group(1), target_layer=int(m.group(2)))
    return None


def _canonical_code(code: str) -> str:
    code = code.strip()
    return _ALIASES.get(code, code)


def _make_label(code: str) -> str:  # noqa: PLR0911
    """Convert a raw QMK keycode to a short human-readable label."""
    code = code.strip()
    display = _make_display(code, {})
    if display.main:
        return display.main

    code = _canonical_code(code)
    replacements = {
        "KC_TRNS": "▽",
        "KC_NO": "✕",
        "KC_SPC": "SPC",
        "KC_ENT": "ENT",
        "KC_BSPC": "BSPC",
        "KC_TAB": "TAB",
        "KC_ESC": "ESC",
        "KC_DEL": "DEL",
        "KC_LSFT": "LSFT",
        "KC_RSFT": "RSFT",
        "KC_LCTL": "LCTL",
        "KC_RCTL": "RCTL",
        "KC_LALT": "LALT",
        "KC_RALT": "RALT",
        "KC_LGUI": "LGUI",
        "KC_RGUI": "RGUI",
        "KC_LEFT": "←",
        "KC_RIGHT": "→",
        "KC_UP": "↑",
        "KC_DOWN": "↓",
        "KC_PGUP": "PGUP",
        "KC_PGDN": "PGDN",
        "KC_HOME": "HOME",
        "KC_END": "END",
        "KC_CAPS": "CAPS",
        "KC_INS": "INS",
        "KC_PSCR": "PSCR",
        "KC_SLCK": "SLCK",
        "KC_PAUS": "PAUS",
        "KC_MUTE": "MUTE",
        "KC_VOLU": "VOL+",
        "KC_VOLD": "VOL-",
    }
    if code in replacements:
        return replacements[code]
    # Function keys: KC_F1..KC_F24
    m = re.match(r"^KC_F(\d+)$", code)
    if m:
        return f"F{m.group(1)}"
    # Layer actions
    m = _LAYER_ACTION_RE.match(code)
    if m:
        return f"{m.group(1)}({m.group(2)})"
    # Single letter: KC_A -> A
    m = re.match(r"^KC_([A-Z0-9])$", code)
    if m:
        return m.group(1)
    # Strip KC_ prefix for everything else
    if code.startswith("KC_"):
        return code[3:]
    return code


def _make_display(code: str, dual_behaviors: dict[str, _DualBehavior]) -> KeyDisplay:  # noqa: PLR0911
    raw_code = code.strip()
    behavior = dual_behaviors.get(raw_code)
    if behavior is not None:
        main = _compact_action_label(behavior.get("tap", ""))
        hold = _compact_hold_label(behavior.get("hold", ""))
        detail = _detail(raw_code, main=main, hold=hold, tap_raw=behavior.get("tap", ""), hold_raw=behavior.get("hold", ""))
        return KeyDisplay(main=main, hold=hold, detail=detail)

    if raw_code.startswith("LT(") and raw_code.endswith(")"):
        args = _split_top_level_commas(raw_code[3:-1])
        if len(args) == _WRAPPER_ARG_COUNT:
            main = _compact_code_label(args[1])
            hold = f"L{args[0].strip()}"
            return KeyDisplay(
                main=main,
                shifted=_shifted_for_code(args[1]),
                hold=hold,
                detail=_detail(raw_code, main=main, hold=hold, tap_raw=args[1], hold_raw=f"Layer {args[0].strip()}"),
            )

    if raw_code.startswith("MT(") and raw_code.endswith(")"):
        args = _split_top_level_commas(raw_code[3:-1])
        if len(args) == _WRAPPER_ARG_COUNT:
            main = _compact_code_label(args[1])
            hold = _modifier_label(args[0])
            return KeyDisplay(
                main=main,
                shifted=_shifted_for_code(args[1]),
                hold=hold,
                detail=_detail(raw_code, main=main, hold=hold, tap_raw=args[1], hold_raw=args[0]),
            )

    layer_match = re.match(r"^(MO|TG|TT|TO)\((\d+)\)$", raw_code)
    if layer_match:
        main = f"{layer_match.group(1)} {layer_match.group(2)}"
        return KeyDisplay(main=main, hold="" if layer_match.group(1) == "TO" else f"L{layer_match.group(2)}", detail=_detail(raw_code, main=main))

    osm_match = re.match(r"^OSM\(([^)]+)\)$", raw_code)
    if osm_match:
        main = _modifier_label(osm_match.group(1))
        return KeyDisplay(main=main, hold="1-shot", detail=_detail(raw_code, main=main, hold="1-shot"))

    chord = _parse_modifier_chord(raw_code)
    if chord is not None:
        main, hold = chord
        return KeyDisplay(
            main=main,
            shifted=_shifted_for_code(raw_code),
            hold=hold,
            detail=_detail(raw_code, main=main, hold=hold),
        )

    keypad_display = _make_keypad_display(raw_code)
    if keypad_display is not None:
        return keypad_display

    main = _compact_code_label(raw_code)
    return KeyDisplay(
        main=main,
        shifted=_shifted_for_code(raw_code),
        detail=_detail(raw_code, main=main, shifted=_shifted_for_code(raw_code)),
    )


def _compact_code_label(code: str) -> str:  # noqa: PLR0911
    code = _canonical_code(code.strip())
    if not code:
        return ""

    if code in _SYMBOL_LABELS:
        return _SYMBOL_LABELS[code]

    function_match = re.match(r"^KC_F(\d+)$", code)
    if function_match:
        return f"F{function_match.group(1)}"

    digit_match = re.match(r"^KC_KP_(\d)$", code)
    if digit_match:
        return f"KP{digit_match.group(1)}"

    single_match = re.match(r"^KC_([A-Z0-9])$", code)
    if single_match:
        return single_match.group(1)

    punctuation = {
        "KC_GRAVE": "`",
        "KC_MINUS": "-",
        "KC_EQUAL": "=",
        "KC_LBRC": "[",
        "KC_RBRC": "]",
        "KC_BSLS": "\\",
        "KC_SCLN": ";",
        "KC_QUOTE": "'",
        "KC_COMMA": ",",
        "KC_COMM": ",",
        "KC_DOT": ".",
        "KC_SLASH": "/",
        "KC_SLSH": "/",
        "KC_LCBR": "{",
        "KC_RCBR": "}",
    }
    if code in punctuation:
        return punctuation[code]

    if code.startswith("KC_"):
        return _title_abbreviation(code[3:])
    return _title_abbreviation(code)


def _compact_action_label(code: str) -> str:
    chord = _parse_modifier_chord(code)
    if chord is not None:
        main, modifiers = chord
        return f"{modifiers}+{main}"
    return _compact_code_label(code)


def _make_keypad_display(code: str) -> KeyDisplay | None:
    raw_code = code.strip()
    code = _canonical_code(raw_code)

    digit_match = re.match(r"^KC_KP_(\d)$", code)
    if digit_match:
        main = digit_match.group(1)
        return KeyDisplay(main=main, hold="KP", detail=_detail(raw_code, main=main, hold="keypad"))

    keypad_symbols = {
        "KC_KP_SLASH": "/",
        "KC_KP_ASTERISK": "*",
        "KC_KP_MINUS": "-",
        "KC_KP_PLUS": "+",
        "KC_KP_ENTER": "⏎",
        "KC_KP_DOT": ".",
    }
    main = keypad_symbols.get(code)
    if main is None:
        return None
    return KeyDisplay(main=main, hold="KP", detail=_detail(raw_code, main=main, hold="keypad"))


def _compact_hold_label(code: str) -> str:
    if not code:
        return ""
    if code.startswith("layer_on(") or code.startswith("layer_off(") or code.startswith("layer_move("):
        match = re.search(r"\((\d+)\)", code)
        return f"L{match.group(1)}" if match else "Layer"
    return _compact_action_label(code)


def _modifier_label(code: str) -> str:
    code = code.strip()
    return _MOD_LABELS.get(code, _compact_code_label(code))


def _shifted_for_code(code: str) -> str:
    return _SHIFTED_SYMBOLS.get(_canonical_code(code.strip()), "")


def _parse_modifier_chord(code: str) -> tuple[str, str] | None:
    wrappers: list[str] = []
    current = code.strip()
    while True:
        match = re.match(r"^([LR](?:CTL|SFT|ALT|GUI))\((.*)\)$", current)
        if match is None:
            break
        wrappers.append(_MOD_WRAPPER_LABELS.get(match.group(1), match.group(1)))
        current = match.group(2).strip()

    if not wrappers:
        return None

    return _compact_code_label(current), "+".join(wrappers)


def _title_abbreviation(value: str) -> str:
    parts = [part for part in value.split("_") if part]
    if not parts:
        return value
    if len(parts) == 1:
        return parts[0][:8].title()
    return "".join(part[:3].title() for part in parts)[:8]


def _detail(
    raw_code: str,
    *,
    main: str,
    shifted: str = "",
    hold: str = "",
    tap_raw: str = "",
    hold_raw: str = "",
) -> str:
    parts = [f"Raw: {raw_code}"]
    if main:
        parts.append(f"tap/main: {main}")
    if shifted:
        parts.append(f"shift: {shifted}")
    if hold:
        parts.append(f"hold: {hold}")
    if tap_raw and tap_raw != main:
        parts.append(f"tap raw: {tap_raw}")
    if hold_raw and hold_raw != hold:
        parts.append(f"hold raw: {hold_raw}")
    return "; ".join(parts)


def _parse_dual_behaviors(text: str) -> dict[str, _DualBehavior]:
    behaviors: dict[str, _DualBehavior] = {}
    macro_defaults = {match.group(1): match.group(2).strip() for match in _DUAL_FUNC_DEFINE_RE.finditer(text)}

    case_matches = list(_CASE_RE.finditer(text))
    for idx, match in enumerate(case_matches):
        name = match.group(1)
        section_start = match.end()
        section_end = case_matches[idx + 1].start() if idx + 1 < len(case_matches) else text.find("default:", section_start)
        if section_end == -1:
            section_end = text.find("case RGB_SLD", section_start)
        if section_end == -1:
            section_end = len(text)
        section = text[section_start:section_end]
        tap_section, hold_section = _split_tap_hold_sections(section)
        tap = _extract_behavior_action(tap_section) if tap_section else ""
        hold = _extract_behavior_action(hold_section) if hold_section else ""
        if tap or hold:
            behaviors[name] = {"tap": tap, "hold": hold}

    for name, macro_code in macro_defaults.items():
        if name not in behaviors and macro_code.startswith("LT("):
            args = _split_top_level_commas(macro_code[3:-1])
            if len(args) == _WRAPPER_ARG_COUNT:
                behaviors[name] = {"tap": args[1].strip(), "hold": f"layer_on({args[0].strip()})"}

    return behaviors


def _parse_layer_enums(text: str) -> dict[str, int]:
    """Parse simple QMK layer enum constants."""
    enum_values: dict[str, int] = {}
    for enum_body in re.findall(r"enum(?:\s+\w+)?\s*\{(.*?)\};", text, flags=re.DOTALL):
        next_value = 0
        for token in _split_top_level_commas(_strip_c_comments(enum_body)):
            item = token.strip()
            if not item:
                continue
            match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)(?:\s*=\s*(\d+))?$", item)
            if match is None:
                continue
            name = match.group(1)
            explicit_value = match.group(2)
            value = int(explicit_value) if explicit_value is not None else next_value
            enum_values[name] = value
            next_value = value + 1
    return enum_values


def _resolve_layer_header(identifier: str, layer_enums: dict[str, int]) -> tuple[int, str | None] | None:
    if identifier.isdigit():
        return int(identifier), None
    layer_index = layer_enums.get(identifier)
    if layer_index is None:
        return None
    return layer_index, identifier


def _layer_name_from_comments(lines: list[str], line_index: int) -> str | None:
    for candidate in (lines[line_index], lines[line_index - 1] if line_index > 0 else ""):
        comment_match = _COMMENT_RE.search(candidate)
        if comment_match:
            return comment_match.group(1) or comment_match.group(2)
    return None


def _split_tap_hold_sections(section: str) -> tuple[str, str] | tuple[None, None]:
    tap_marker = "record->tap.count > 0"
    tap_pos = section.find(tap_marker)
    if tap_pos == -1:
        return None, None

    first_open = section.find("{", tap_pos)
    if first_open == -1:
        return None, None
    tap_body, tap_end = _extract_braced_block(section, first_open)
    else_pos = section.find("else", tap_end)
    if else_pos == -1:
        return tap_body, ""
    else_open = section.find("{", else_pos)
    if else_open == -1:
        return tap_body, ""
    hold_body, _ = _extract_braced_block(section, else_open)
    return tap_body, hold_body


def _extract_behavior_action(section: str) -> str:
    for name in ("register_code16", "register_code", "layer_on", "layer_off", "layer_move"):
        call = _extract_first_call(section, name)
        if call is not None:
            if name.startswith("register"):
                return call
            return f"{name}({call})"
    return ""


def _extract_first_call(text: str, name: str) -> str | None:
    marker = f"{name}("
    start = text.find(marker)
    if start == -1:
        return None
    open_index = start + len(name)
    body, _ = _extract_parenthesized(text, open_index)
    return body.strip()


def _parse_ledmap(text: str) -> dict[int, list[RgbColor]]:
    ledmap_pos = text.find("ledmap")
    if ledmap_pos == -1:
        return {}

    open_index = text.find("{", ledmap_pos)
    if open_index == -1:
        return {}

    try:
        block, _ = _extract_braced_block(text, open_index)
    except ValueError:
        return {}

    result: dict[int, list[RgbColor]] = {}
    position = 0
    while True:
        match = re.search(r"\[(\d+)\]\s*=\s*\{", block[position:])
        if match is None:
            break
        layer_index = int(match.group(1))
        layer_open = position + match.end() - 1
        try:
            layer_body, layer_end = _extract_braced_block(block, layer_open)
        except ValueError:
            break
        triples = [
            _hsv_triplet_to_rgb(int(hue), int(saturation), int(value))
            for hue, saturation, value in _TRIPLE_RE.findall(layer_body)
        ]
        result[layer_index] = triples
        position = layer_end

    return result


def _hsv_triplet_to_rgb(hue: int, saturation: int, value: int) -> RgbColor:
    if hue == 0 and saturation == 0 and value == 0:
        return (0, 0, 0)
    red, green, blue = hsv_to_rgb(hue / 255, saturation / 255, value / 255)
    return (round(red * 255), round(green * 255), round(blue * 255))


def _extract_parenthesized(text: str, open_index: int) -> tuple[str, int]:
    if open_index >= len(text) or text[open_index] != "(":
        raise ValueError("expected opening parenthesis")
    depth = 0
    for index in range(open_index, len(text)):
        char = text[index]
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return text[open_index + 1 : index], index + 1
    raise ValueError("unterminated parenthesized block")


def _extract_braced_block(text: str, open_index: int) -> tuple[str, int]:
    if open_index >= len(text) or text[open_index] != "{":
        raise ValueError("expected opening brace")
    depth = 0
    for index in range(open_index, len(text)):
        char = text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[open_index + 1 : index], index + 1
    raise ValueError("unterminated braced block")


def parse_keymap_c(path: str | Path) -> Layout:
    """Parse a keymap.c file and return a Layout.
    Raises ValueError with a descriptive message on parse failure.
    """
    path = Path(path)
    text = path.read_text(encoding="utf-8", errors="replace")
    dual_behaviors = _parse_dual_behaviors(text)
    layer_enums = _parse_layer_enums(text)
    ledmap = _parse_ledmap(text)
    display_overrides = _load_display_overrides(path)

    # Isolate the keymaps block
    start = text.find("keymaps")
    if start == -1:
        raise ValueError("No 'keymaps' array found — is this a QMK keymap.c?")

    lines = text.splitlines()
    layers: list[Layer] = []

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        m = _LAYER_HEADER_RE.search(line)
        if m:
            resolved_layer = _resolve_layer_header(m.group(1), layer_enums)
            if resolved_layer is None:
                i += 1
                continue
            layer_idx, enum_name = resolved_layer

            name = _layer_name_from_comments(lines, i) or enum_name or f"Layer {layer_idx}"

            # Collect everything until the closing paren of this LAYOUT call
            # (handle nested parens for things like LT(1, KC_SPC))
            body_lines = [line[m.end() :]]  # text after LAYOUT_moonlander(
            depth = line.count("(") - line.count(")")
            j = i + 1
            while j < len(lines) and depth > 0:
                body_line = lines[j]
                body_lines.append(body_line)
                depth += body_line.count("(") - body_line.count(")")
                j += 1

            # Strip comments before flattening so `//` comments stay line-scoped.
            body = _strip_c_comments("\n".join(body_lines))
            # Flatten to a single string and split on top-level commas.
            body = " ".join(body.splitlines())
            # Strip the final closing paren
            body = body.rsplit(")", 1)[0]

            raw_codes = _split_top_level_commas(body)

            keys: list[Key] = []
            for idx, code in enumerate(raw_codes):
                action = _parse_layer_action(code)
                display = _make_display(code, dual_behaviors)
                display = _apply_display_override(display, display_overrides, layer_idx, idx)
                keys.append(
                    Key(
                        index=idx,
                        label=display.main,
                        code=code,
                        layer_action=action,
                        display=display,
                    ),
                )

            layers.append(Layer(index=layer_idx, name=name, keys=keys))
            i = j
            continue
        i += 1

    if not layers:
        raise ValueError(
            "No LAYOUT_moonlander layers found — check that this is a Moonlander keymap.c",
        )

    layers.sort(key=lambda layer: layer.index)
    _apply_ledmap(layers, ledmap)
    return Layout(layers=layers)


def _apply_ledmap(layers: list[Layer], ledmap: dict[int, list[RgbColor]]) -> None:
    if len(_MOONLANDER_KEY_TO_LED_INDEX) != _MOONLANDER_KEY_COUNT:
        return

    for layer in layers:
        colors = ledmap.get(layer.index)
        if colors is None or len(colors) != _MOONLANDER_KEY_COUNT or len(layer.keys) != _MOONLANDER_KEY_COUNT:
            continue
        for key in layer.keys:
            key.led_color = colors[_MOONLANDER_KEY_TO_LED_INDEX[key.index]]


def _load_display_overrides(keymap_path: Path) -> dict[str, Any]:
    override_path = keymap_path.with_name("moonmap_display.json")
    if not override_path.exists():
        return {}
    try:
        data = json.loads(override_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def _apply_display_override(
    display: KeyDisplay,
    overrides: dict[str, Any],
    layer_index: int,
    key_index: int,
) -> KeyDisplay:
    layer_overrides = overrides.get(str(layer_index))
    if not isinstance(layer_overrides, dict):
        return display
    key_overrides = layer_overrides.get(str(key_index))
    if not isinstance(key_overrides, dict):
        return display

    main = key_overrides.get("main", display.main)
    shifted = key_overrides.get("shifted", display.shifted)
    hold = key_overrides.get("hold", display.hold)
    detail = key_overrides.get("detail", display.detail)
    if not all(isinstance(value, str) for value in (main, shifted, hold, detail)):
        return display
    return KeyDisplay(main=main, shifted=shifted, hold=hold, detail=detail)
