# moonmap — v1 Spec

Real-time keypress visualizer for the ZSA Moonlander Mark I.

## Overview

A Windows desktop application that parses a QMK `keymap.c` source file (downloaded from ZSA Oryx),
renders the Moonlander Mark I physical layout, and provides real-time keypress highlighting with automatic
layer inference based on MO and TG key behavior.

No firmware flashing. No HID communication. Read-only visualization tool.

______________________________________________________________________

## Goals

- Parse QMK `keymap.c` source from an Oryx download into an internal layout model
- Render the full Moonlander Mark I physical layout (all layers)
- Highlight keys as they are pressed in real-time via system-wide keyboard hook
- Infer and display the active layer based on MO/TG key state
- Persist the loaded layout path and window state across sessions

## Non-Goals (v1)

- Firmware flashing
- LT (layer-tap), tap dance, or combo key handling
- macOS / Linux support
- Editing keymaps within the app
- Reading keymap directly from keyboard hardware or HID

______________________________________________________________________

## Repository

**Name:** `moonmap`
**Branch strategy:** `main` is always stable. Feature branches per logical chunk, merged to main when complete.
No release branch.

Suggested feature branch order:

1. `feat/qmk-parser` — models, parser, layer state (no UI dependency, testable in isolation)
1. `feat/physical-layout` — coordinate generation script + `moonlander_layout.json`
1. `feat/keyboard-widget` — key widget + keyboard widget rendering
1. `feat/hook-integration` — wiring pynput hook into the UI
1. `feat/layer-bar` — layer tab UI + manual override

______________________________________________________________________

## Project Structure

```text
moonmap/
├── README.md
├── requirements.txt
├── .gitignore
└── src/
    ├── main.py                        # Entry point, PyQt6 app init
    ├── config.py                      # Persistent app config (%APPDATA%)
    ├── layout/
    │   ├── __init__.py
    │   ├── models.py                  # Key, Layer, Layout dataclasses
    │   ├── qmk_parser.py              # Parses keymap.c into internal model
    │   └── layer_state.py             # MO/TG layer inference state machine
    ├── input/
    │   ├── __init__.py
    │   └── hook.py                    # System-wide keyboard hook via pynput
    ├── ui/
    │   ├── __init__.py
    │   ├── main_window.py             # Top-level PyQt6 window
    │   ├── keyboard_widget.py         # Renders both Moonlander halves
    │   ├── key_widget.py              # Individual key rendering + state
    │   └── layer_bar.py              # Layer tabs + manual override
    └── assets/
        └── moonlander_layout.json     # Static physical key position map
```

______________________________________________________________________

## Config Source: QMK keymap.c

Oryx does not export a standalone JSON for GUI tools. The correct workflow:

1. Open your layout on [Oryx](https://configure.zsa.io/)
1. Click **Compile** and wait for the build
1. Click **Download Source** — this downloads a `.zip`
1. Unzip and locate `keymap.c`
1. In moonmap: **File → Load Layout** → select `keymap.c`

The parser targets the `LAYOUT_moonlander()` macro format produced by Oryx.

______________________________________________________________________

## Data Model

```text
@dataclass
class LayerAction:
    type: str  # "MO" or "TG"
    target_layer: int

@dataclass
class Key:
    index: int  # Physical key index (QMK argument order)
    label: str  # Display label e.g. "A", "MO(1)", "LCTL"
    code: str  # Raw QMK keycode string
    layer_action: Optional[LayerAction]  # None if not a layer-switching key

@dataclass
class Layer:
    index: int
    name: str  # From preceding comment in keymap.c, else "Layer N"
    keys: List[Key]  # Ordered by physical key index

@dataclass
class Layout:
    layers: List[Layer]

    @property
    def layer_count(self) -> int: ...
```

______________________________________________________________________

## Physical Layout Map

`src/assets/moonlander_layout.json` maps key index → pixel coordinates for rendering. Static — authored once,
never changes. Key index order matches QMK `LAYOUT_moonlander()` argument order (left half top-to-bottom,
then right half, thumb clusters last).

Geometry is derived from [Nuigurumi777/mllayoutvisualizer](https://github.com/Nuigurumi777/mllayoutvisualizer) —
the only useful artifact from that repo is the hardcoded pixel positions and thumb cluster rotation math.
A one-time coordinate generation script will produce this JSON before the UI is built.

```text
{
  "canvas_width": 1050,
  "canvas_height": 460,
  "keys": [
    { "index": 0, "x": 10, "y": 10, "w": 55, "h": 55 },
    ...
  ]
}
```

______________________________________________________________________

## QMK Parser (`qmk_parser.py`)

### Input

A `keymap.c` file containing one or more `LAYOUT_moonlander(...)` blocks.

### Expected format

```c
// BASE
[0] = LAYOUT_moonlander(
    KC_ESC,  KC_1,  KC_2, ...,
    ...
),
// NAV
[1] = LAYOUT_moonlander(
    ...
),
```

### Parse flow

1. Locate the `keymaps` array in the file
1. For each `[n] = LAYOUT_moonlander(` block:
   - Extract layer index `n`
   - Attempt to read layer name from the preceding `//` or `/* */` comment
   - Collect all keycode tokens inside the macro (handle nested parens for things like `LT(1, KC_SPC)`)
   - Strip inline C comments from the body
   - Split on commas → ordered list of raw keycode strings
1. For each keycode: detect MO/TG via regex, generate human-readable label, build `Key` object
1. Sort layers by index, return `Layout`

### Label mapping (selected)

| QMK Code         | Label                                 |
| ---------------- | ------------------------------------- |
| `KC_A`–`KC_Z`    | `A`–`Z`                               |
| `KC_F1`–`KC_F24` | `F1`–`F24`                            |
| `KC_SPC`         | `SPC`                                 |
| `KC_ENT`         | `ENT`                                 |
| `KC_BSPC`        | `BSPC`                                |
| `KC_TRNS`        | `▽`                                   |
| `KC_NO`          | `✕`                                   |
| `MO(n)`          | `MO(n)`                               |
| `TG(n)`          | `TG(n)`                               |
| Unknown          | raw string with `KC_` prefix stripped |

### Edge cases

- Layer name missing → default `"Layer N"`
- Unrecognized keycode → render raw string, strip `KC_` prefix
- Key count mismatch vs physical layout → warn in status bar, continue with available keys
- Malformed file (no `keymaps`, no `LAYOUT_moonlander`) → raise `ValueError` with descriptive message, show error dialog

______________________________________________________________________

## Layer State Machine (`layer_state.py`)

Handles MO and TG only. Layer 0 is always the base fallback.

### Rules

| Key type | Event   | Behavior                                                |
| -------- | ------- | ------------------------------------------------------- |
| `MO(n)`  | keydown | Append `n` to MO stack                                  |
| `MO(n)`  | keyup   | Remove `n` from MO stack                                |
| `TG(n)`  | keydown | Toggle `n` in TG set (add if absent, remove if present) |

### Active layer resolution

`active_layer = max(mo_stack ∪ tg_set)`, fallback to `0` if both empty.

If the same layer index appears in both MO stack and TG set, it's still just `max()` — no special handling needed.

```python
class LayerStateManager:
    def on_keydown(self, key: Key) -> None: ...
    def on_keyup(self, key: Key) -> None: ...
    def active_layer(self) -> int: ...
    def reset(self) -> None: ...  # call on new layout load
```

______________________________________________________________________

## Input Hook (`hook.py`)

System-wide low-level keyboard hook via `pynput`. Runs on a background thread.

```python
class KeyboardHook:
    def __init__(self, on_press_cb=None, on_release_cb=None): ...
    def start(self) -> None: ...
    def stop(self) -> None: ...
```

**Threading rule:** hook callbacks must never call Qt widget methods directly. All communication to the UI thread
goes through `pyqtSignal`.

**Windows note:** `pynput` does not require UAC elevation for `WH_KEYBOARD_LL`. Run the app as a normal user.
If keypresses are not detected, check that no other global hook is blocking (e.g. some antivirus software).

______________________________________________________________________

## UI

### Main Window (`main_window.py`)

- Menu bar: **File → Load Layout** (file dialog filtered to `*.c`), **File → Exit**
- Layout (top to bottom): `LayerBar` → `KeyboardWidget`
- Status bar: active layer display, e.g. `Layer 1 — NAV`
- Window title: `moonmap`
- On close: persist window geometry and last layout path to config
- On startup: reload last layout path if set; show empty state if not

### KeyboardWidget (`keyboard_widget.py`)

- Renders left and right halves side-by-side with a fixed gap
- Keys positioned absolutely using coordinates from `moonlander_layout.json`
- Thumb clusters rendered per geometry from the physical layout JSON
- On layer change: updates all `KeyWidget` labels to reflect the active layer's keycodes
- `update_key_state(index, pressed: bool)` — called from main window on hook events

### KeyWidget (`key_widget.py`)

Individual key. Painted via `QPainter` in `paintEvent`.

| State                              | Visual                                       |
| ---------------------------------- | -------------------------------------------- |
| Default                            | Dark background, white label                 |
| Pressed                            | Accent color (from `config.highlight_color`) |
| Layer key at rest (`MO`/`TG`)      | Subtle secondary color                       |
| Layer key — layer currently active | Brighter highlight                           |

### LayerBar (`layer_bar.py`)

- Row of tabs, one per layer: e.g. `0: BASE  1: NAV  2: SYM`
- Active layer tab highlighted
- Click → emit `manual_override(layer_index: int)` signal
- Manual override cleared by `MainWindow` on next MO/TG keydown event

______________________________________________________________________

## Configuration (`config.py`)

Stored at `%APPDATA%\MoonlanderVisualizer\config.json`.

```json
{
  "last_layout_path": "C:/Users/.../keymap.c",
  "highlight_color": "#4FC3F7",
  "window_geometry": {
    "x": 100,
    "y": 100,
    "w": 1100,
    "h": 460
  }
}
```

Loaded on startup, saved on window close and layout load. Missing keys fall back to defaults — no crash on first
run or partial config.

______________________________________________________________________

## Dependencies

```text
PyQt6>=6.6.0
pynput>=1.7.6
```

Standard library only beyond these two. No database, no network.

______________________________________________________________________

## Out of Scope — Future Considerations

- `LT(n, kc)` support (requires hold/tap timing logic, ~200ms threshold)
- Tap dance and combo key handling
- Theme editor / configurable color palette
- Layout diff view (compare two `keymap.c` exports)
- Auto-detect `keymap.c` from Downloads folder on load
- QMK Configurator JSON import (different schema from Oryx C source)
- Packaging as a standalone `.exe` (PyInstaller)
