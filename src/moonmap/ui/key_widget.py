"""Renders a single key on the keyboard.

Visual states:
  - default:      dark background, white label
  - pressed:      accent color (from config highlight_color)
  - layer_key:    secondary color (MO/TG key at rest)
  - layer_active: brighter highlight when that layer is currently active
"""

from __future__ import annotations

# TODO: implement in build phase
