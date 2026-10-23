"""Prevent tesseract.exe console windows from flashing on Windows.

In a console=False PyInstaller app (and in the background daemon) the parent
process has no console, so any spawn of tesseract.exe (a console-subsystem
binary) can briefly create a visible console window. pytesseract only hides
the OCR path via STARTUPINFO/SW_HIDE and leaves its one-off probes
(get_languages / get_tesseract_version) unhidden. This patches
subprocess.Popen globally, once, so every spawn of the Tesseract executable
is forced to run with CREATE_NO_WINDOW, regardless of the caller.
"""

from __future__ import annotations

import os
import subprocess
import sys

_patched = False


def suppress_tesseract_console() -> None:
    """Idempotently patch subprocess.Popen to hide tesseract.exe windows."""
    global _patched
    if _patched or sys.platform != "win32":
        return
    if not hasattr(subprocess, "CREATE_NO_WINDOW"):
        return

    try:
        _orig_popen = subprocess.Popen
        _no_window = subprocess.CREATE_NO_WINDOW

        def _popen_hidden(cmd, *args, **kwargs):
            exe = cmd[0] if isinstance(cmd, (list, tuple)) and cmd else None
            if isinstance(exe, str):
                base = os.path.basename(exe).lower()
                if base in ("tesseract", "tesseract.exe", "tesseract.exe.exe"):
                    flags = kwargs.get("creationflags", 0) or 0
                    kwargs["creationflags"] = flags | _no_window
            return _orig_popen(cmd, *args, **kwargs)

        subprocess.Popen = _popen_hidden
        _patched = True
    except Exception:
        pass
