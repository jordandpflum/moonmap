"""Row of layer tabs displayed above the keyboard widget.

- One tab per layer, labeled with layer name and index
- Active layer tab is highlighted
- Clicking a tab fires a manual_layer_override signal
- Manual override is cleared by the MainWindow on the next MO/TG event
"""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QAbstractButton, QButtonGroup, QHBoxLayout, QPushButton, QWidget

from moonmap.layout.models import Layer


class LayerBar(QWidget):
    """Layer selector displayed above the keyboard."""

    manual_layer_override = pyqtSignal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the layer bar."""
        super().__init__(parent)
        self._button_group = QButtonGroup(self)
        self._button_group.setExclusive(True)
        self._button_group.idClicked.connect(self.manual_layer_override.emit)

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(6)
        self._layout.addStretch(1)

    @property
    def layer_count(self) -> int:
        """Return the number of visible layer buttons."""
        return len(self._button_group.buttons())

    def set_layers(self, layers: list[Layer]) -> None:
        """Replace the visible layer tabs."""
        while self._layout.count() > 0:
            item = self._layout.takeAt(0)
            if item is None:
                continue
            widget = item.widget()
            if isinstance(widget, QAbstractButton):
                self._button_group.removeButton(widget)
                widget.deleteLater()

        for layer in layers:
            button = QPushButton(f"{layer.index}: {layer.name}", self)
            button.setCheckable(True)
            button.setMinimumHeight(30)
            self._button_group.addButton(button, layer.index)
            self._layout.addWidget(button)

        self._layout.addStretch(1)
        self.set_active_layer(layers[0].index if layers else 0)

    def set_active_layer(self, layer_index: int) -> None:
        """Mark one layer tab as active."""
        button = self._button_group.button(layer_index)
        if button is not None:
            button.setChecked(True)
