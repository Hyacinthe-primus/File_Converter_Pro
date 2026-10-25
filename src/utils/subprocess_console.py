"""Hide console windows for external tools spawned by the windowed app.

In a console=False PyInstaller app (and in the background daemon) the parent
process has no console, so spawning a console-subsystem executable can briefly
create a visible console window. This patches subprocess.Popen globally, once,
and forces CREATE_NO_WINDOW for every executable registered through
suppress_console_for().

subprocess.run() resolves Popen from the subprocess module at call time, so it
is covered by the same patch.
"""

from __future__ import annotations

import os
import subprocess
import sys

_orig_popen = None
_hidden: set[str] = set()


def _exe_name(cmd) -> str:
    if isinstance(cmd, (list, tuple)) and cmd:
        cmd = cmd[0]
    if not isinstance(cmd, str):
        return ""
    return os.path.splitext(os.path.basename(cmd))[0].lower()


def _install() -> None:
    global _orig_popen
    if _orig_popen is not None or sys.platform != "win32":
        return
    if not hasattr(subprocess, "CREATE_NO_WINDOW"):
        return

    _orig_popen = subprocess.Popen
    _no_window = subprocess.CREATE_NO_WINDOW

    def _popen_hidden(cmd, *args, **kwargs):
        if _exe_name(cmd) in _hidden:
            flags = kwargs.get("creationflags", 0) or 0
            kwargs["creationflags"] = flags | _no_window
        return _orig_popen(cmd, *args, **kwargs)

    subprocess.Popen = _popen_hidden


def suppress_console_for(*executables: str) -> None:
    """Idempotently hide console windows for the given executable names."""
    _install()
    for exe in executables:
        _hidden.add(_exe_name(exe))
