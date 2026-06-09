"""Collapsible in-memory key event log drawer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

MAX_EVENT_LOG_ENTRIES = 200


@dataclass(frozen=True)
class KeyEventLogEntry:
    """One observed or simulated key event."""

    timestamp: datetime
    event_type: str
    raw_event: str
    host_action: str
    active_layer_index: int
    active_matches: list[str]
    all_layer_matches: list[str]
    meaning: str


class KeyEventLog(QWidget):
    """Collapsed-by-default bottom drawer for recent key events."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the event log drawer."""
        super().__init__(parent)
        self._entries: list[KeyEventLogEntry] = []
        self._expanded = False
        self._summary = QLabel("No key events yet", self)
        self._toggle_button = QPushButton("Show", self)
        self._clear_button = QPushButton("Clear", self)
        self._rows_widget = QWidget(self)
        self._rows_layout = QVBoxLayout(self._rows_widget)
        self._scroll = QScrollArea(self)
        self._build_ui()
        self._sync_view()

    def add_entry(self, entry: KeyEventLogEntry) -> None:
        """Add an event to the log, keeping the newest 200 entries."""
        self._entries.append(entry)
        if len(self._entries) > MAX_EVENT_LOG_ENTRIES:
            self._entries = self._entries[-MAX_EVENT_LOG_ENTRIES:]
        self._sync_view()

    def clear(self) -> None:
        """Clear all events."""
        self._entries.clear()
        self._sync_view()

    def entries(self) -> list[KeyEventLogEntry]:
        """Return a copy of current log entries for tests."""
        return list(self._entries)

    def is_expanded(self) -> bool:
        """Return whether the drawer is expanded."""
        return self._expanded

    def summary_text(self) -> str:
        """Return the header summary text."""
        return self._summary.text()

    def set_expanded(self, expanded: bool) -> None:
        """Set expanded state."""
        self._expanded = expanded
        self._sync_view()

    def _build_ui(self) -> None:
        self.setObjectName("keyEventLog")
        self.setStyleSheet(
            """
            QFrame#logFrame {
                background: #F7F8FA;
                border: 1px solid #D5DAE0;
                border-radius: 6px;
            }
            QLabel {
                color: #20252B;
            }
            QPushButton {
                padding: 4px 10px;
            }
            """
        )

        frame = QFrame(self)
        frame.setObjectName("logFrame")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(frame)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)

        header = QHBoxLayout()
        header.addWidget(self._summary, 1)
        header.addWidget(self._toggle_button)
        header.addWidget(self._clear_button)
        layout.addLayout(header)

        self._rows_layout.setContentsMargins(0, 0, 0, 0)
        self._rows_layout.setSpacing(4)
        self._scroll.setWidgetResizable(True)
        self._scroll.setWidget(self._rows_widget)
        self._scroll.setMaximumHeight(180)
        layout.addWidget(self._scroll)

        self._toggle_button.clicked.connect(self._toggle)
        self._clear_button.clicked.connect(self.clear)

    def _toggle(self) -> None:
        self.set_expanded(not self._expanded)

    def _sync_view(self) -> None:
        self._toggle_button.setText("Hide" if self._expanded else "Show")
        self._scroll.setVisible(self._expanded)
        self._summary.setText(self._summary_for_latest_entry())
        self._clear_rows()
        if not self._expanded:
            return
        for entry in reversed(self._entries):
            self._rows_layout.addWidget(QLabel(self._row_text(entry), self._rows_widget))
        self._rows_layout.addStretch(1)

    def _clear_rows(self) -> None:
        while self._rows_layout.count():
            item = self._rows_layout.takeAt(0)
            if item is None:
                continue
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _summary_for_latest_entry(self) -> str:
        if not self._entries:
            return "No key events yet"
        latest = self._entries[-1]
        matches = ", ".join(latest.active_matches) if latest.active_matches else "no active-layer match"
        return f"{latest.event_type}: {latest.host_action}; {matches}"

    def _row_text(self, entry: KeyEventLogEntry) -> str:
        all_matches = ", ".join(entry.all_layer_matches) if entry.all_layer_matches else "none"
        active_matches = ", ".join(entry.active_matches) if entry.active_matches else "none"
        meaning = f"; {entry.meaning}" if entry.meaning else ""
        return (
            f"{entry.timestamp.isoformat(timespec='seconds')} | {entry.event_type} | "
            f"raw={entry.raw_event} | host={entry.host_action} | layer={entry.active_layer_index} | "
            f"active={active_matches} | all={all_matches}{meaning}"
        )
