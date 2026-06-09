from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ASSET_PATH = Path(__file__).resolve().parents[1] / "src/moonmap/assets/moonlander_layout.json"
EXPECTED_KEY_COUNT = 72
RIGHT_HAND_ROW_SLICES = [
    slice(7, 14),
    slice(21, 28),
    slice(35, 42),
    slice(48, 54),
    slice(59, 64),
]


def test_moonlander_layout_asset_has_72_unique_key_indexes() -> None:
    data: dict[str, Any] = json.loads(ASSET_PATH.read_text(encoding="utf-8"))
    keys: list[dict[str, Any]] = data["keys"]

    assert len(keys) == EXPECTED_KEY_COUNT
    assert sorted(key["index"] for key in keys) == list(range(EXPECTED_KEY_COUNT))


def test_moonlander_layout_asset_dimensions_are_in_canvas() -> None:
    data: dict[str, Any] = json.loads(ASSET_PATH.read_text(encoding="utf-8"))
    canvas_width = data["canvas_width"]
    canvas_height = data["canvas_height"]

    for key in data["keys"]:
        assert key["w"] > 0
        assert key["h"] > 0
        assert 0 <= key["x"] <= canvas_width
        assert 0 <= key["y"] <= canvas_height
        assert key["x"] + key["w"] <= canvas_width
        assert key["y"] + key["h"] <= canvas_height


def test_right_hand_main_rows_follow_visual_left_to_right_order() -> None:
    data: dict[str, Any] = json.loads(ASSET_PATH.read_text(encoding="utf-8"))
    keys: list[dict[str, Any]] = data["keys"]

    for row_slice in RIGHT_HAND_ROW_SLICES:
        row_x_positions = [key["x"] for key in keys[row_slice]]
        assert row_x_positions == sorted(row_x_positions)
