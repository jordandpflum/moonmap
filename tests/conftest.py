from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("APPDATA", "/tmp/moonmap-ui-tests")

import pytest
from PyQt6.QtCore import QCoreApplication
from PyQt6.QtWidgets import QApplication

_QT_APP: QApplication | None = None


@pytest.fixture(autouse=True)
def qapp() -> QApplication:
    """Keep a QApplication alive for tests that instantiate widgets."""
    config_file = Path("/tmp/moonmap-ui-tests/moonmap/config.json")
    config_file.unlink(missing_ok=True)

    global _QT_APP  # noqa: PLW0603
    app = QCoreApplication.instance()
    if isinstance(app, QApplication):
        _QT_APP = app
    if _QT_APP is None:
        _QT_APP = QApplication([])
    return _QT_APP
