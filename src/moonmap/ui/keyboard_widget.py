"""Renders both halves of the Moonlander Mark I physical layout.

Physical geometry is loaded from src/assets/moonlander_layout.json.
Each key is an instance of KeyWidget, positioned absolutely.

Redraws all key labels when active layer changes.
Highlights individual keys on press/release via update_key_state().
"""

from __future__ import annotations

# TODO: implement in build phase
