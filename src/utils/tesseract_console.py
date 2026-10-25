"""Prevent tesseract.exe console windows from flashing on Windows.

In a console=False PyInstaller app (and in the background daemon) the parent
process has no console, so any spawn of tesseract.exe (a console-subsystem
binary) can briefly create a visible console window. pytesseract only hides
the OCR path via STARTUPINFO/SW_HIDE and leaves its one-off probes
(get_languages / get_tesseract_version) unhidden. This registers the
Tesseract executable with the shared subprocess console suppressor, so every
spawn of it is forced to run with CREATE_NO_WINDOW, regardless of the caller.
"""

from __future__ import annotations

from utils.subprocess_console import suppress_console_for


def suppress_tesseract_console() -> None:
    """Idempotently hide tesseract.exe console windows."""
    suppress_console_for("tesseract")
