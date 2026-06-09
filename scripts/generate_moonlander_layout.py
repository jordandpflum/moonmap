"""Generate the static Moonlander Mark I physical layout asset.

The base geometry mirrors the wxPython drawing math from
https://github.com/Nuigurumi777/mllayoutvisualizer, which is MIT licensed.
The emitted key indexes follow the `LAYOUT_moonlander(...)` argument order
produced by Oryx: each main row lists left-half keys followed by right-half
keys, then the thumb-cluster arguments.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ASSET_PATH = Path(__file__).resolve().parents[1] / "src/moonmap/assets/moonlander_layout.json"

KEY_SIZE = 50
KEY_GAP = 5
MAIN_LEFT = 10
MAIN_TOP = 10
RIGHT_ANCHOR = 900
ROW_TOP_OFFSETS = [20, 20, 10, 0, 10, 20, 20]
CANVAS_WIDTH = 978
CANVAS_HEIGHT = 485
FULL_ROWS_BEFORE_TAPER = 3


def _main_half_positions(*, left_to_right: bool) -> list[list[dict[str, Any]]]:
    rows: list[list[dict[str, Any]]] = []
    top = MAIN_TOP
    keys_in_row = 7

    for row_index in range(5):
        if row_index >= FULL_ROWS_BEFORE_TAPER:
            keys_in_row -= 1

        row: list[dict[str, Any]] = []
        for key_index in range(keys_in_row):
            top_offset = ROW_TOP_OFFSETS[key_index]
            x = MAIN_LEFT + key_index * (KEY_SIZE + KEY_GAP)
            if not left_to_right:
                x = RIGHT_ANCHOR - x
            row.append({"x": x, "y": top + top_offset, "w": KEY_SIZE, "h": KEY_SIZE})

        rows.append(row)
        top += KEY_SIZE + KEY_GAP

    return rows


def _thumb_positions(*, left_to_right: bool) -> list[dict[str, Any]]:
    if left_to_right:
        origin_x = 420
        origin_y = 300
        return [
            {
                "x": origin_x,
                "y": origin_y,
                "w": 105,
                "h": 60,
                "shape": "thumb_wide",
                "rotation_degrees": 30,
            },
            {"x": origin_x, "y": origin_y + 65, "w": KEY_SIZE, "h": 75, "rotation_degrees": 30},
            {
                "x": origin_x + 55,
                "y": origin_y + 65,
                "w": KEY_SIZE,
                "h": 75,
                "rotation_degrees": 30,
            },
            {
                "x": origin_x + 110,
                "y": origin_y + 65,
                "w": KEY_SIZE,
                "h": 75,
                "rotation_degrees": 30,
            },
        ]

    origin_x = 398
    origin_y = 300
    return [
        {
            "x": origin_x + 55,
            "y": origin_y,
            "w": 105,
            "h": 60,
            "shape": "thumb_wide",
            "rotation_degrees": -30,
        },
        {"x": origin_x, "y": origin_y + 65, "w": KEY_SIZE, "h": 75, "rotation_degrees": -30},
        {
            "x": origin_x + 55,
            "y": origin_y + 65,
            "w": KEY_SIZE,
            "h": 75,
            "rotation_degrees": -30,
        },
        {
            "x": origin_x + 110,
            "y": origin_y + 65,
            "w": KEY_SIZE,
            "h": 75,
            "rotation_degrees": -30,
        },
    ]


def build_layout() -> dict[str, Any]:
    """Build the layout JSON payload."""
    left_rows = _main_half_positions(left_to_right=True)
    right_rows = _main_half_positions(left_to_right=False)

    keys: list[dict[str, Any]] = []
    for row_index in range(5):
        for key in left_rows[row_index]:
            keys.append(key)
        for key in right_rows[row_index]:
            keys.append(key)

    keys.extend(_thumb_positions(left_to_right=True))
    keys.extend(_thumb_positions(left_to_right=False))

    for index, key in enumerate(keys):
        key["index"] = index

    return {
        "_comment": (
            "Physical key positions for the Moonlander Mark I. Geometry derived from "
            "https://github.com/Nuigurumi777/mllayoutvisualizer (MIT). Units are pixels. "
            "Key index matches Oryx/QMK LAYOUT_moonlander() argument order."
        ),
        "canvas_width": CANVAS_WIDTH,
        "canvas_height": CANVAS_HEIGHT,
        "key_size": KEY_SIZE,
        "gap": KEY_GAP,
        "keys": keys,
    }


def main() -> None:
    """Write the Moonlander layout asset."""
    ASSET_PATH.write_text(
        json.dumps(build_layout(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
