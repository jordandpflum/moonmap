"""Generate the static Moonlander Mark I physical layout asset.

The base geometry mirrors the wxPython drawing math from
https://github.com/Nuigurumi777/mllayoutvisualizer, which is MIT licensed.
The emitted key indexes follow the `LAYOUT_moonlander(...)` argument order
produced by Oryx: each main row lists left-half keys followed by right-half
keys. The two wide inner keys on the bottom row are still part of the main
row argument order; only the three tall keys on each thumb cluster are thumb
arguments.
"""

from __future__ import annotations

import json
import math
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
ROW_KEY_COUNTS = [7, 7, 7, 6, 5]
LEFT_THUMB_TRANSFORM = (420, 0, math.pi / 6.0)
RIGHT_THUMB_TRANSFORM = (240, 475, -math.pi / 6.0)


def _main_half_positions(*, left_to_right: bool) -> list[list[dict[str, Any]]]:
    rows: list[list[dict[str, Any]]] = []
    top = MAIN_TOP

    for keys_in_row in ROW_KEY_COUNTS:
        row: list[dict[str, Any]] = []
        for key_index in range(keys_in_row):
            top_offset = ROW_TOP_OFFSETS[key_index]
            x = MAIN_LEFT + key_index * (KEY_SIZE + KEY_GAP)
            if not left_to_right:
                x = RIGHT_ANCHOR - x
            y = top + top_offset
            row.append(
                {
                    "x": x,
                    "y": y,
                    "cx": x + KEY_SIZE / 2,
                    "cy": y + KEY_SIZE / 2,
                    "w": KEY_SIZE,
                    "h": KEY_SIZE,
                },
            )

        rows.append(row)
        top += KEY_SIZE + KEY_GAP

    return rows


def _thumb_positions(*, left_to_right: bool) -> list[dict[str, Any]]:
    local_rects: list[dict[str, Any]]
    if left_to_right:
        transform = LEFT_THUMB_TRANSFORM
        local_rects = [
            {"x": 0, "y": 0, "w": 105, "h": 60, "shape": "thumb_wide"},
            {"x": 0, "y": 65, "w": KEY_SIZE, "h": 75},
            {"x": 55, "y": 65, "w": KEY_SIZE, "h": 75},
            {"x": 110, "y": 65, "w": KEY_SIZE, "h": 75},
        ]
    else:
        transform = RIGHT_THUMB_TRANSFORM
        local_rects = [
            {"x": 55, "y": 0, "w": 105, "h": 60, "shape": "thumb_wide"},
            {"x": 0, "y": 65, "w": KEY_SIZE, "h": 75},
            {"x": 55, "y": 65, "w": KEY_SIZE, "h": 75},
            {"x": 110, "y": 65, "w": KEY_SIZE, "h": 75},
        ]

    return [_transform_thumb_rect(rect, transform) for rect in local_rects]


def _thumb_wide_position(*, left_to_right: bool) -> dict[str, Any]:
    """Return the wide inner thumb key used by the main-row argument order."""
    return _thumb_positions(left_to_right=left_to_right)[0]


def _thumb_tall_positions(*, left_to_right: bool) -> list[dict[str, Any]]:
    """Return the three tall thumb keys that follow the main-row arguments."""
    return _thumb_positions(left_to_right=left_to_right)[1:]


def _transform_thumb_rect(rect: dict[str, Any], transform: tuple[float, float, float]) -> dict[str, Any]:
    dx, dy, angle = transform
    x = float(rect["x"])
    y = float(rect["y"])
    w = float(rect["w"])
    h = float(rect["h"])
    cx, cy = _transform_point(x + w / 2, y + h / 2, dx, dy, angle)

    key = {
        "x": round(cx - w / 2, 3),
        "y": round(cy - h / 2, 3),
        "cx": round(cx, 3),
        "cy": round(cy, 3),
        "w": int(w),
        "h": int(h),
        "rotation_degrees": round(math.degrees(angle), 3),
    }
    if "shape" in rect:
        key["shape"] = rect["shape"]
    return key


def _transform_point(
    x: float,
    y: float,
    dx: float,
    dy: float,
    angle: float,
) -> tuple[float, float]:
    translated_x = x + dx
    translated_y = y + dy
    return (
        translated_x * math.cos(angle) - translated_y * math.sin(angle),
        translated_x * math.sin(angle) + translated_y * math.cos(angle),
    )


def build_layout() -> dict[str, Any]:
    """Build the layout JSON payload."""
    left_rows = _main_half_positions(left_to_right=True)
    right_rows = _main_half_positions(left_to_right=False)

    keys: list[dict[str, Any]] = []
    for row_index in range(4):
        for key in left_rows[row_index]:
            keys.append(key)
        for key in reversed(right_rows[row_index]):
            keys.append(key)

    keys.extend(left_rows[4])
    keys.append(_thumb_wide_position(left_to_right=True))
    keys.append(_thumb_wide_position(left_to_right=False))
    keys.extend(reversed(right_rows[4]))
    keys.extend(_thumb_tall_positions(left_to_right=True))
    keys.extend(_thumb_tall_positions(left_to_right=False))

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
