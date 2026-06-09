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

from pathlib import Path

from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from moonmap import config
from moonmap.layout.layer_state import LayerStateManager
from moonmap.layout.models import Layout
from moonmap.layout.qmk_parser import parse_keymap_c
from moonmap.ui.keyboard_widget import KeyboardWidget
from moonmap.ui.layer_bar import LayerBar


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self) -> None:
        """Initialize the main application window."""
        super().__init__()
        self.setWindowTitle("Moonlander Visualizer")
        self._cfg = config.load()
        self._layout_model: Layout | None = None
        self._layer_state = LayerStateManager()

        self._layer_bar = LayerBar(self)
        self._keyboard = KeyboardWidget(self)
        self._keyboard.set_highlight_color(str(self._cfg["highlight_color"]))
        self._layer_bar.manual_layer_override.connect(self._set_active_layer)

        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 8)
        layout.setSpacing(10)
        layout.addWidget(self._layer_bar)
        layout.addWidget(self._keyboard)
        self.setCentralWidget(container)

        self._build_menu()
        self._restore_window_geometry()
        status_bar = self.statusBar()
        assert status_bar is not None
        status_bar.showMessage("Load a keymap.c to render your Moonlander layout")

        last_layout_path = self._cfg.get("last_layout_path")
        if isinstance(last_layout_path, str) and Path(last_layout_path).exists():
            self.load_layout_path(Path(last_layout_path))

    def load_layout_path(self, path: str | Path) -> None:
        """Load a QMK keymap.c from disk."""
        layout = parse_keymap_c(path)
        self._layout_model = layout
        self._layer_state.reset()
        self._keyboard.set_layout_model(layout)
        self._layer_bar.set_layers(layout.layers)
        self._set_active_layer(0)
        self._cfg["last_layout_path"] = str(path)
        config.save(self._cfg)

    def closeEvent(self, event: QCloseEvent | None) -> None:  # noqa: N802
        """Persist window geometry when the app closes."""
        geometry = self.geometry()
        self._cfg["window_geometry"] = {
            "x": geometry.x(),
            "y": geometry.y(),
            "w": geometry.width(),
            "h": geometry.height(),
        }
        config.save(self._cfg)
        super().closeEvent(event)

    def _build_menu(self) -> None:
        menu_bar = self.menuBar()
        assert menu_bar is not None
        file_menu = menu_bar.addMenu("&File")
        assert file_menu is not None

        load_action = file_menu.addAction("&Load Layout...")
        assert load_action is not None
        load_action.triggered.connect(self._choose_layout)

        file_menu.addSeparator()

        exit_action = file_menu.addAction("E&xit")
        assert exit_action is not None
        exit_action.triggered.connect(self.close)

    def _choose_layout(self) -> None:
        selected_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Moonlander keymap.c",
            str(Path.home()),
            "QMK keymap.c (keymap.c *.c);;C source files (*.c);;All files (*)",
        )
        if not selected_path:
            return

        try:
            self.load_layout_path(selected_path)
        except ValueError as exc:
            QMessageBox.critical(self, "Could not load layout", str(exc))

    def _set_active_layer(self, layer_index: int) -> None:
        self._keyboard.set_active_layer(layer_index)
        self._layer_bar.set_active_layer(layer_index)
        status_bar = self.statusBar()
        assert status_bar is not None

        if self._layout_model is None:
            status_bar.showMessage("Load a keymap.c to render your Moonlander layout")
            return

        layer = next((item for item in self._layout_model.layers if item.index == layer_index), None)
        if layer is None:
            status_bar.showMessage(f"Layer {layer_index}")
        else:
            status_bar.showMessage(f"Layer {layer.index} - {layer.name}")

    def _restore_window_geometry(self) -> None:
        geometry = self._cfg.get("window_geometry")
        if isinstance(geometry, dict):
            self.setGeometry(
                int(geometry.get("x", 100)),
                int(geometry.get("y", 100)),
                int(geometry.get("w", 1100)),
                int(geometry.get("h", 560)),
            )
