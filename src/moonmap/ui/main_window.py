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

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from moonmap import config
from moonmap.input.hook import KeyboardHook
from moonmap.input.key_mapper import find_matching_key_indexes, normalize_pynput_key
from moonmap.layout.layer_state import LayerStateManager
from moonmap.layout.models import Key, Layout
from moonmap.layout.qmk_parser import parse_keymap_c
from moonmap.ui.keyboard_widget import KeyboardWidget
from moonmap.ui.layer_bar import LayerBar


class HookLike(Protocol):
    """Interface used by MainWindow for keyboard hooks."""

    def start(self) -> None:
        """Start listening."""

    def stop(self) -> None:
        """Stop listening."""


class KeyboardSignals(QObject):
    """Qt signal bridge for keyboard hook callbacks."""

    pressed = pyqtSignal(object)
    released = pyqtSignal(object)
    hook_error = pyqtSignal(str)


@dataclass
class PressedKeyState:
    """Tracks highlighted indexes and source keys for one host key press."""

    indexes: list[int]
    keys: list[Key]


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(
        self,
        *,
        start_hook: bool = True,
        hook_factory: Callable[..., HookLike] = KeyboardHook,
    ) -> None:
        """Initialize the main application window."""
        super().__init__()
        self.setWindowTitle("Moonlander Visualizer")
        self._cfg = config.load()
        self._layout_model: Layout | None = None
        self._layer_state = LayerStateManager()
        self._active_layer_index = 0
        self._pressed_keys: dict[str, PressedKeyState] = {}
        self._keyboard_signals = KeyboardSignals(self)
        self._keyboard_signals.pressed.connect(self._handle_hook_press)
        self._keyboard_signals.released.connect(self._handle_hook_release)
        self._keyboard_signals.hook_error.connect(self._show_hook_error)
        self._hook: HookLike | None = hook_factory(
            on_press_cb=self._keyboard_signals.pressed.emit,
            on_release_cb=self._keyboard_signals.released.emit,
        )

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

        if start_hook:
            self._start_hook()

    def load_layout_path(self, path: str | Path) -> None:
        """Load a QMK keymap.c from disk."""
        layout = parse_keymap_c(path)
        self._layout_model = layout
        self._layer_state.reset()
        self._pressed_keys.clear()
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
        if self._hook is not None:
            self._hook.stop()
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
        self._active_layer_index = layer_index
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

    def _start_hook(self) -> None:
        if self._hook is None:
            return

        try:
            self._hook.start()
        except Exception as exc:  # noqa: BLE001
            self._keyboard_signals.hook_error.emit(str(exc))

    def _handle_hook_press(self, raw_key: Any) -> None:
        normalized_code = normalize_pynput_key(raw_key)
        if normalized_code is None or normalized_code in self._pressed_keys:
            return

        matched_keys = self._matching_keys(normalized_code)
        indexes = [key.index for key in matched_keys]
        self._pressed_keys[normalized_code] = PressedKeyState(indexes=indexes, keys=matched_keys)

        for index in indexes:
            self._keyboard.update_key_state(index, True)

        layer_changed = False
        for key in matched_keys:
            previous_layer = self._layer_state.active_layer()
            self._layer_state.on_keydown(key)
            layer_changed = layer_changed or previous_layer != self._layer_state.active_layer()

        if layer_changed:
            self._set_active_layer(self._layer_state.active_layer())

    def _handle_hook_release(self, raw_key: Any) -> None:
        normalized_code = normalize_pynput_key(raw_key)
        if normalized_code is None:
            return

        pressed_state = self._pressed_keys.pop(normalized_code, None)
        if pressed_state is None:
            return

        for index in pressed_state.indexes:
            self._keyboard.update_key_state(index, False)

        layer_changed = False
        for key in pressed_state.keys:
            previous_layer = self._layer_state.active_layer()
            self._layer_state.on_keyup(key)
            layer_changed = layer_changed or previous_layer != self._layer_state.active_layer()

        if layer_changed:
            self._set_active_layer(self._layer_state.active_layer())

    def _matching_keys(self, normalized_code: str) -> list[Key]:
        if self._layout_model is None:
            return []

        layer = next(
            (
                candidate
                for candidate in self._layout_model.layers
                if candidate.index == self._active_layer_index
            ),
            None,
        )
        if layer is None:
            return []

        indexes = find_matching_key_indexes(
            self._layout_model,
            self._active_layer_index,
            normalized_code,
        )
        index_set = set(indexes)
        return [key for key in layer.keys if key.index in index_set]

    def _show_hook_error(self, message: str) -> None:
        status_bar = self.statusBar()
        assert status_bar is not None
        status_bar.showMessage(f"Keyboard hook unavailable: {message}")
