"""Cancellation regressions for the context-menu Quick Convert window."""

import threading

import context_menu.window as cm_window


class _FakeSignal:
    def __init__(self):
        self._slots = []

    def connect(self, slot):
        self._slots.append(slot)

    def emit(self, *args):
        for slot in list(self._slots):
            slot(*args)


class _FakeThread:
    instances = []

    def __init__(self, files, conversion_type):
        self.files = files
        self.conversion_type = conversion_type
        self.done = _FakeSignal()
        self.cancelled = _FakeSignal()
        self.running = False
        self.cancel_requested = False
        _FakeThread.instances.append(self)

    def start(self):
        self.running = True

    def isRunning(self):
        return self.running

    def cancel(self):
        self.cancel_requested = True

    def wait(self, timeout=None):
        return True


def test_thread_cancelled_before_start_skips_conversion(monkeypatch, tmp_path):
    src = tmp_path / "a.png"
    src.write_bytes(b"x")
    calls = []
    monkeypatch.setattr(cm_window, "_convert_image_to_pdf", lambda *args: calls.append(args))

    thread = cm_window.ConversionThread([str(src)], "image_to_pdf")
    cancelled = []
    thread.cancelled.connect(lambda: cancelled.append(True))
    thread.cancel()
    thread.run()

    assert calls == []
    assert cancelled == [True]


def test_thread_cancel_stops_remaining_files(monkeypatch, tmp_path, qapp):
    first = tmp_path / "a.png"
    second = tmp_path / "b.png"
    first.write_bytes(b"x")
    second.write_bytes(b"x")

    started = threading.Event()
    release = threading.Event()
    calls = []

    def fake_convert(src, _dst_dir):
        calls.append(src)
        started.set()
        release.wait(2)

    monkeypatch.setattr(cm_window, "_convert_image_to_pdf", fake_convert)

    thread = cm_window.ConversionThread([str(first), str(second)], "image_to_pdf")
    cancelled = []
    thread.cancelled.connect(lambda: cancelled.append(True))
    thread.start()

    assert started.wait(2)
    thread.cancel()
    release.set()

    assert thread.wait(2000)
    qapp.processEvents()
    assert calls == [str(first)]
    assert cancelled == [True]


def test_quick_convert_cancel_button_requests_cancellation(monkeypatch, tmp_path, qapp):
    src = tmp_path / "a.png"
    src.write_bytes(b"x")
    _FakeThread.instances.clear()
    monkeypatch.setattr(cm_window, "ConversionThread", _FakeThread)

    window = cm_window.QuickConvertWindow([str(src)], conversion_type="image_to_pdf")
    window._start_conversion()

    thread = _FakeThread.instances[0]
    assert thread.running is True
    assert window.cancel_btn.isEnabled() is True

    window._cancel_conversion()

    assert thread.cancel_requested is True
    assert window.cancel_btn.text() == "Cancelling..."
    assert window.cancel_btn.isEnabled() is False

    exited = []
    monkeypatch.setattr(cm_window.os, "_exit", lambda code: exited.append(code))
    window._force_cancel_if_running()
    assert exited == [0]

    thread.running = False
    window.close()
