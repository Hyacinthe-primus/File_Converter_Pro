"""Pytest configuration for File Converter Pro tests."""

import json
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Run all widget tests offscreen so they never open a real window.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest


@pytest.fixture(scope="session")
def qapp():
    """Session-wide QApplication, created once on the offscreen platform."""
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app
    app.processEvents()


@pytest.fixture()
def app(qapp, tmp_path):
    """Build a real FileConverterApp offscreen with isolated config and
    non-modal message boxes, so the test never blocks on dialogs."""
    cfg = {
        "accepted_terms": True,
        "accepted_privacy": True,
        "language": "fr",
        "use_system_theme": False,
        "dark_mode": False,
        "last_project": None,
        "auto_open_last_project": False,
        "show_dashboard_on_startup": False,
    }
    cfg_file = tmp_path / "config.dat"
    cfg_file.write_text(json.dumps(cfg), encoding="utf-8")

    from PySide6.QtWidgets import QMessageBox

    from config import ConfigManager

    cm = ConfigManager(str(cfg_file), str(tmp_path / "key.key"))

    QMessageBox.critical = staticmethod(lambda *a, **k: None)
    QMessageBox.warning = staticmethod(lambda *a, **k: None)

    from app import FileConverterApp

    window = FileConverterApp(cm)
    window.hide()
    qapp.processEvents()
    return window
