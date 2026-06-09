"""Entry point for Moonlander Visualizer."""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from moonmap.ui.main_window import MainWindow


def main() -> None:
    """Run the Moonlander Visualizer Qt application."""
    app = QApplication(sys.argv)
    app.setApplicationName("Moonlander Visualizer")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
