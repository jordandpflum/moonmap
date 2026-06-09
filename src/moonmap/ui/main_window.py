"""Top-level application window.

Responsibilities:
- Menu bar: File → Load Layout, File → Exit
- Hosts KeyboardWidget (central widget)
- Hosts LayerBar (above keyboard)
- Status bar: active layer name
- Wires keyboard hook signals to KeyboardWidget and LayerStateManager
- Persists window geometry and last layout path via config.py
"""

from __future__ import annotations

from PyQt6.QtWidgets import QMainWindow

# TODO: implement in build phase


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self) -> None:
        """Initialize the main application window."""
        super().__init__()
        self.setWindowTitle("Moonlander Visualizer")
        # TODO: load config, build menu, init hook, init keyboard widget
