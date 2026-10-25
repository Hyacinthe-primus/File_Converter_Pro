"""Console-window suppression for external subprocesses (Windows)."""

import subprocess
import sys

import pytest

import utils.subprocess_console as subprocess_console

pytestmark = pytest.mark.skipif(
    sys.platform != "win32", reason="CREATE_NO_WINDOW is Windows-only"
)


class _FakePopen:
    def __init__(self, cmd, *args, **kwargs):
        self.cmd = cmd
        self.kwargs = kwargs


@pytest.fixture
def fake_popen(monkeypatch):
    monkeypatch.setattr(subprocess, "Popen", _FakePopen)
    monkeypatch.setattr(subprocess_console, "_orig_popen", None)
    monkeypatch.setattr(subprocess_console, "_hidden", set())
    return _FakePopen


def test_registered_executable_gets_no_window_flag(fake_popen):
    subprocess_console.suppress_console_for("ffplay")
    proc = subprocess.Popen(["ffplay", "-version"])
    assert proc.kwargs["creationflags"] & subprocess.CREATE_NO_WINDOW


def test_unregistered_executable_is_unaffected(fake_popen):
    subprocess_console.suppress_console_for("ffplay")
    proc = subprocess.Popen(["ffmpeg", "-version"])
    assert "creationflags" not in proc.kwargs


def test_existing_creation_flags_are_preserved(fake_popen):
    subprocess_console.suppress_console_for("ffplay")
    proc = subprocess.Popen(
        ["ffplay", "-version"], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
    )
    flags = proc.kwargs["creationflags"]
    assert flags & subprocess.CREATE_NO_WINDOW
    assert flags & subprocess.CREATE_NEW_PROCESS_GROUP


def test_path_and_extension_are_normalized(fake_popen):
    subprocess_console.suppress_console_for("ffplay")
    proc = subprocess.Popen([r"C:\ffmpeg\bin\FFPLAY.EXE", "-version"])
    assert proc.kwargs["creationflags"] & subprocess.CREATE_NO_WINDOW


def test_tesseract_registration_delegates(fake_popen):
    from utils.tesseract_console import suppress_tesseract_console

    suppress_tesseract_console()
    proc = subprocess.Popen(["tesseract.exe", "--version"])
    assert proc.kwargs["creationflags"] & subprocess.CREATE_NO_WINDOW


def test_patched_popen_remains_subclassable(fake_popen):
    subprocess_console.suppress_console_for("ffplay")

    class Subprocess(subprocess.Popen):
        pass

    assert issubclass(Subprocess, fake_popen)


def test_suppress_console_for_is_idempotent(fake_popen):
    subprocess_console.suppress_console_for("ffplay")
    subprocess_console.suppress_console_for("tesseract")
    ffplay = subprocess.Popen(["ffplay", "-version"])
    tesseract = subprocess.Popen(["tesseract", "--version"])
    assert ffplay.kwargs["creationflags"] & subprocess.CREATE_NO_WINDOW
    assert tesseract.kwargs["creationflags"] & subprocess.CREATE_NO_WINDOW
