r"""Persistent app configuration stored at %APPDATA%\moonmap\config.json."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

_CONFIG_DIR = Path(os.environ.get("APPDATA", Path.home())) / "moonmap"
_CONFIG_FILE = _CONFIG_DIR / "config.json"

_DEFAULTS: dict[str, Any] = {
    "last_layout_path": None,
    "highlight_color": "#4FC3F7",
    "window_geometry": {"x": 100, "y": 100, "w": 1100, "h": 460},
}


def load() -> dict[str, Any]:
    """Load persisted config values merged with defaults."""
    if _CONFIG_FILE.exists():
        try:
            data = json.loads(_CONFIG_FILE.read_text(encoding="utf-8"))
            return {**_DEFAULTS, **data}
        except (json.JSONDecodeError, OSError):
            pass
    return dict(_DEFAULTS)


def save(cfg: dict[str, Any]) -> None:
    """Persist config values to disk."""
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    _CONFIG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
