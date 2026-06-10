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
from datetime import datetime
from pathlib import Path
from time import monotonic
from typing import Any, Protocol

from PyQt6.QtCore import QObject, QTimer, pyqtSignal
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
from moonmap.input.key_mapper import (
    KeyMatch,
    find_matching_key_matches,
    format_host_action,
    modifier_for_normalized_code,
    normalize_pynput_key,
)
from moonmap.layout.layer_state import LayerStateManager
from moonmap.layout.key_meanings import meaning_for_key
from moonmap.layout.models import Key, Layout
from moonmap.ui.key_event_log import KeyEventLog, KeyEventLogEntry
from moonmap.layout.qmk_parser import parse_keymap_c
from moonmap.ui.key_tooltip import KeyTooltip
from moonmap.ui.keyboard_widget import KeyHoverInfo, KeyboardWidget
from moonmap.ui.layer_bar import LayerBar

HOVER_TOOLTIP_DELAY_MS = 250
MIN_VISIBLE_HIGHLIGHT_MS = 110


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

    host_action: str
    indexes: list[int]
    keys: list[Key]
    matches: list[KeyMatch]
    pressed_at: float
    highlight_tokens: dict[int, int]
    inferred_layer_index: int | None = None


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
        self._committed_layer_index = 0
        self._pressed_keys: dict[str, PressedKeyState] = {}
        self._inferred_layer_keys: dict[str, int] = {}
        self._key_highlight_tokens: dict[int, int] = {}
        self._next_highlight_token = 0
        self._active_modifiers: set[str] = set()
        self._pending_hover_info: KeyHoverInfo | None = None
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
        self._key_event_log = KeyEventLog(self)
        self._key_tooltip = KeyTooltip(self)
        self._hover_timer = QTimer(self)
        self._hover_timer.setSingleShot(True)
        self._hover_timer.setInterval(HOVER_TOOLTIP_DELAY_MS)
        self._hover_timer.timeout.connect(self._show_pending_hover_tooltip)
        self._keyboard.set_highlight_color(str(self._cfg["highlight_color"]))
        self._keyboard.hover_info_changed.connect(self._handle_hover_info_changed)
        self._keyboard.key_clicked.connect(self._handle_key_clicked)
        self._layer_bar.manual_layer_override.connect(self._set_active_layer)

        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 8)
        layout.setSpacing(10)
        layout.addWidget(self._layer_bar)
        layout.addWidget(self._keyboard)
        layout.addWidget(self._key_event_log)
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
        self._inferred_layer_keys.clear()
        self._key_highlight_tokens.clear()
        self._active_modifiers.clear()
        self._key_event_log.clear()
        self._hide_hover_tooltip()
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
        self._hide_hover_tooltip()
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
        self._committed_layer_index = layer_index
        self._inferred_layer_keys.clear()
        self._show_visual_layer(layer_index)

    def _show_visual_layer(self, layer_index: int) -> None:
        self._hide_hover_tooltip()
        self._active_layer_index = layer_index
        self._keyboard.set_active_layer(layer_index)
        self._layer_bar.set_active_layer(layer_index)
        self._show_active_layer_status()

    def _show_active_layer_status(self) -> None:
        if self._layout_model is None:
            self._show_status("Load a keymap.c to render your Moonlander layout")
            return

        layer = next((item for item in self._layout_model.layers if item.index == self._active_layer_index), None)
        if layer is None:
            self._show_status(f"Layer {self._active_layer_index}")
        else:
            self._show_status(f"Layer {layer.index} - {layer.name}")

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
            self._show_status("Keyboard hook active")
        except Exception as exc:  # noqa: BLE001
            self._keyboard_signals.hook_error.emit(str(exc))

    def _handle_hook_press(self, raw_key: Any) -> None:
        normalized_code = normalize_pynput_key(raw_key)
        if normalized_code is None:
            self._show_status(f"Key down ignored: unsupported event {raw_key!r}")
            self._log_key_event(
                event_type="ignored",
                raw_event=repr(raw_key),
                host_action="Unsupported",
                matches=[],
                all_matches=[],
            )
            return

        if normalized_code in self._pressed_keys:
            return

        modifier = modifier_for_normalized_code(normalized_code)
        active_modifiers = frozenset(self._active_modifiers)
        matches = self._matching_matches(normalized_code, active_modifiers)
        active_matches = [match for match in matches if match.is_active_layer]
        inferred_layer_index = self._inferred_layer_for_press(matches, active_matches)
        if active_matches and inferred_layer_index is not None:
            self._inferred_layer_keys[normalized_code] = inferred_layer_index
        elif inferred_layer_index is not None:
            self._inferred_layer_keys[normalized_code] = inferred_layer_index
            self._show_visual_layer(inferred_layer_index)
            matches = self._matching_matches(normalized_code, active_modifiers)
            active_matches = [match for match in matches if match.is_active_layer]
        highlighted_matches = active_matches or matches
        matched_keys = [match.key for match in highlighted_matches]
        indexes = [key.index for key in matched_keys]
        host_action = format_host_action(normalized_code, active_modifiers)
        highlight_tokens = self._set_key_highlights(indexes, True)
        self._pressed_keys[normalized_code] = PressedKeyState(
            host_action=host_action,
            indexes=indexes,
            keys=matched_keys,
            matches=highlighted_matches,
            pressed_at=monotonic(),
            highlight_tokens=highlight_tokens,
            inferred_layer_index=inferred_layer_index,
        )

        self._show_key_diagnostic("down", normalized_code, indexes, host_action=host_action)
        self._log_key_event(
            event_type="press",
            raw_event=repr(raw_key),
            host_action=host_action,
            matches=active_matches,
            all_matches=matches,
        )

        layer_changed = False
        for key in matched_keys:
            previous_layer = self._layer_state.active_layer()
            self._layer_state.on_keydown(key)
            layer_changed = layer_changed or previous_layer != self._layer_state.active_layer()

        if layer_changed:
            self._set_active_layer(self._layer_state.active_layer())

        if modifier is not None:
            self._active_modifiers.add(modifier)

    def _handle_hook_release(self, raw_key: Any) -> None:
        normalized_code = normalize_pynput_key(raw_key)
        if normalized_code is None:
            self._show_status(f"Key up ignored: unsupported event {raw_key!r}")
            self._log_key_event(
                event_type="ignored",
                raw_event=repr(raw_key),
                host_action="Unsupported",
                matches=[],
                all_matches=[],
            )
            return

        pressed_state = self._pressed_keys.pop(normalized_code, None)
        if pressed_state is None:
            host_action = format_host_action(normalized_code, frozenset(self._active_modifiers))
            self._show_key_diagnostic("up", normalized_code, [], host_action=host_action)
            self._remove_modifier(normalized_code)
            return

        self._clear_released_key_highlights(pressed_state)
        if pressed_state.inferred_layer_index is not None:
            self._release_inferred_layer(normalized_code)

        layer_changed = False
        for key in pressed_state.keys:
            previous_layer = self._layer_state.active_layer()
            self._layer_state.on_keyup(key)
            layer_changed = layer_changed or previous_layer != self._layer_state.active_layer()

        if layer_changed:
            self._set_active_layer(self._layer_state.active_layer())
        else:
            self._show_key_diagnostic(
                "up",
                normalized_code,
                pressed_state.indexes,
                host_action=pressed_state.host_action,
            )
        self._log_key_event(
            event_type="release",
            raw_event=repr(raw_key),
            host_action=pressed_state.host_action,
            matches=[match for match in pressed_state.matches if match.is_active_layer],
            all_matches=pressed_state.matches,
        )
        self._remove_modifier(normalized_code)

    def _inferred_layer_for_press(self, matches: list[KeyMatch], active_matches: list[KeyMatch]) -> int | None:
        if active_matches:
            if self._inferred_layer_keys:
                return self._active_layer_index
            return None
        layer_indexes = {match.layer_index for match in matches}
        if len(layer_indexes) != 1:
            return None
        return next(iter(layer_indexes))

    def _release_inferred_layer(self, normalized_code: str) -> None:
        self._inferred_layer_keys.pop(normalized_code, None)
        if self._inferred_layer_keys:
            next_layer = next(reversed(self._inferred_layer_keys.values()))
            self._show_visual_layer(next_layer)
            return
        self._show_visual_layer(self._committed_layer_index)

    def _set_key_highlights(self, indexes: list[int], pressed: bool) -> dict[int, int]:
        highlight_tokens: dict[int, int] = {}
        for index in indexes:
            if pressed:
                self._next_highlight_token += 1
                token = self._next_highlight_token
                self._key_highlight_tokens[index] = token
                highlight_tokens[index] = token
            else:
                self._key_highlight_tokens.pop(index, None)
            self._keyboard.update_key_state(index, pressed)
        return highlight_tokens

    def _clear_released_key_highlights(self, pressed_state: PressedKeyState) -> None:
        elapsed_ms = int((monotonic() - pressed_state.pressed_at) * 1000)
        remaining_ms = max(0, MIN_VISIBLE_HIGHLIGHT_MS - elapsed_ms)
        if remaining_ms == 0:
            self._clear_key_highlights_if_current(pressed_state.highlight_tokens)
            return

        QTimer.singleShot(
            remaining_ms,
            lambda: self._clear_key_highlights_if_current(pressed_state.highlight_tokens),
        )

    def _clear_key_highlights_if_current(self, highlight_tokens: dict[int, int]) -> None:
        for index, token in highlight_tokens.items():
            if self._key_highlight_tokens.get(index) != token:
                continue
            self._key_highlight_tokens.pop(index, None)
            self._keyboard.update_key_state(index, False)

    def _matching_matches(
        self,
        normalized_code: str,
        active_modifiers: frozenset[str],
    ) -> list[KeyMatch]:
        if self._layout_model is None:
            return []

        return find_matching_key_matches(
            self._layout_model,
            self._active_layer_index,
            normalized_code,
            active_modifiers,
            include_all_layers=True,
        )

    def _show_hook_error(self, message: str) -> None:
        self._show_status(f"Keyboard hook unavailable: {message}")

    def _show_key_diagnostic(
        self,
        event_name: str,
        normalized_code: str,
        indexes: list[int],
        *,
        host_action: str | None = None,
    ) -> None:
        if self._layout_model is None:
            self._show_status(f"Key {event_name}: {normalized_code}; no layout loaded")
            return

        match_text = ", ".join(str(index) for index in indexes) if indexes else "none"
        code_text = host_action if host_action and host_action != _format_code_fallback(normalized_code) else normalized_code
        self._show_status(
            f"Key {event_name}: {code_text}; layer {self._active_layer_index}; "
            f"matches: {match_text}",
        )

    def _show_status(self, message: str) -> None:
        status_bar = self.statusBar()
        assert status_bar is not None
        status_bar.showMessage(message)

    def _handle_hover_info_changed(self, info: object) -> None:
        if not isinstance(info, KeyHoverInfo):
            self._hide_hover_tooltip()
            return

        self._pending_hover_info = info
        self._hover_timer.start()

    def _show_pending_hover_tooltip(self) -> None:
        if self._pending_hover_info is None:
            return

        self._key_tooltip.set_hover_info(self._pending_hover_info)
        self._key_tooltip.show_near(self._keyboard.key_anchor_global_pos(self._pending_hover_info.index))

    def _hide_hover_tooltip(self) -> None:
        self._hover_timer.stop()
        self._pending_hover_info = None
        self._key_tooltip.hide()

    def _remove_modifier(self, normalized_code: str) -> None:
        modifier = modifier_for_normalized_code(normalized_code)
        if modifier is not None:
            self._active_modifiers.discard(modifier)

    def _handle_key_clicked(self, info: object) -> None:
        if not isinstance(info, KeyHoverInfo):
            return
        self._keyboard.update_key_state(info.index, True)
        QTimer.singleShot(200, lambda: self._keyboard.update_key_state(info.index, False))
        host_action = ", ".join(info.host_inputs) if info.host_inputs else info.resolved_code
        self._show_status(f"Simulated: key {info.index}; {host_action}; visual only")
        self._key_event_log.add_entry(
            KeyEventLogEntry(
                timestamp=datetime.now(),
                event_type="simulated",
                raw_event=f"click key {info.index}",
                host_action=host_action,
                active_layer_index=self._active_layer_index,
                active_matches=[f"L{info.active_layer_index}:{info.index} {info.resolved_code}"],
                all_layer_matches=[f"L{info.active_layer_index}:{info.index} {info.resolved_code}"],
                meaning=info.meaning,
            ),
        )

    def _log_key_event(
        self,
        *,
        event_type: str,
        raw_event: str,
        host_action: str,
        matches: list[KeyMatch],
        all_matches: list[KeyMatch],
    ) -> None:
        self._key_event_log.add_entry(
            KeyEventLogEntry(
                timestamp=datetime.now(),
                event_type=event_type,
                raw_event=raw_event,
                host_action=host_action,
                active_layer_index=self._active_layer_index,
                active_matches=[self._match_label(match) for match in matches],
                all_layer_matches=[self._match_label(match) for match in all_matches],
                meaning=self._meaning_for_matches(matches or all_matches),
            ),
        )

    def _match_label(self, match: KeyMatch) -> str:
        return f"L{match.layer_index}:{match.key.index} {match.key.code}"

    def _meaning_for_matches(self, matches: list[KeyMatch]) -> str:
        if not matches:
            return ""
        key = matches[0].key
        return meaning_for_key(key.code, key.display)


def _format_code_fallback(normalized_code: str) -> str:
    return format_host_action(normalized_code, frozenset())
