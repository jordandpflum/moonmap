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

import re
from pathlib import Path

from .models import Key, Layer, LayerAction, Layout

# Matches: MO(n) or TG(n)
_LAYER_ACTION_RE = re.compile(r"^(MO|TG)\((\d+)\)$")

# Matches: [n] = LAYOUT_moonlander(  with optional comment on prior line
_LAYER_HEADER_RE = re.compile(r"\[(\d+)\]\s*=\s*LAYOUT_moonlander\s*\(")

# Matches a comment line like: // BASE or /* NAV */
_COMMENT_RE = re.compile(r"//\s*(\w+)|/\*\s*(\w+)\s*\*/")


def _parse_layer_action(code: str) -> LayerAction | None:
    m = _LAYER_ACTION_RE.match(code.strip())
    if m:
        return LayerAction(type=m.group(1), target_layer=int(m.group(2)))
    return None


def _make_label(code: str) -> str:
    """Convert a raw QMK keycode to a short human-readable label."""
    code = code.strip()
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


def parse_keymap_c(path: str | Path) -> Layout:
    """Parse a keymap.c file and return a Layout.
    Raises ValueError with a descriptive message on parse failure.
    """
    text = Path(path).read_text(encoding="utf-8", errors="replace")

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
            layer_idx = int(m.group(1))

            # Try to grab a name from the comment on the preceding line
            name = f"Layer {layer_idx}"
            if i > 0:
                cm = _COMMENT_RE.search(lines[i - 1])
                if cm:
                    name = cm.group(1) or cm.group(2) or name

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

            # Flatten to a single string and split on commas
            body = " ".join(body_lines)
            # Strip the final closing paren
            body = body.rsplit(")", 1)[0]
            # Remove C comments within the body
            body = re.sub(r"//[^\n]*", " ", body)
            body = re.sub(r"/\*.*?\*/", " ", body, flags=re.DOTALL)

            raw_codes = [c.strip() for c in body.split(",") if c.strip()]

            keys: list[Key] = []
            for idx, code in enumerate(raw_codes):
                action = _parse_layer_action(code)
                keys.append(
                    Key(
                        index=idx,
                        label=_make_label(code),
                        code=code,
                        layer_action=action,
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
    return Layout(layers=layers)
