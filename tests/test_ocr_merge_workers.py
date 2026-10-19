"""OCR merge of several images: parallel fast path (scanlayer workers) with sequential fallback."""

import os
import sys
import types

import fitz
import pytest

from app.mixins.image_to_pdf import ImageToPdfMixin


@pytest.fixture
def qapp():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


class _ProgressBar:
    def __init__(self):
        self.ranges, self.values = [], []

    def setRange(self, lo, hi):
        self.ranges.append((lo, hi))

    def setValue(self, v):
        self.values.append(v)


class _Achievements:
    def __init__(self):
        self.ocr_pages = None

    def record_ocr_usage(self, n):
        self.ocr_pages = n


class _App(ImageToPdfMixin):
    def __init__(self):
        self.progress_bar = _ProgressBar()
        self.achievement_system = _Achievements()
        self.ui_states = []
        self.sequential_calls = []

    def translate_text(self, key):
        return key

    def show_progress(self, *_a, **_k):
        pass

    def _set_ui_enabled(self, enabled):
        self.ui_states.append(enabled)

    def _merge_images_with_ocr_sequential(self, *args):
        self.sequential_calls.append(args)


def _make_pdf(path, pages_with_text):
    doc = fitz.open()
    for has_text in pages_with_text:
        page = doc.new_page()
        if has_text:
            page.insert_text((72, 72), "recognised text")
    doc.save(path)
    doc.close()


def _install_fake_scanlayer(monkeypatch, behaviour):
    calls = []

    def convert_merge(paths, output_path, **kwargs):
        calls.append({"paths": list(paths), "output": output_path, **kwargs})
        return behaviour(paths, output_path)

    monkeypatch.setitem(sys.modules, "scanlayer", types.SimpleNamespace(convert_merge=convert_merge))
    return calls


@pytest.fixture
def images(tmp_path):
    from PIL import Image

    paths = []
    for i in range(3):
        p = tmp_path / f"p{i}.png"
        Image.new("RGB", (40, 40), "white").save(p)
        paths.append(str(p))
    return paths


class TestParallelMerge:
    def test_uses_four_workers_and_keeps_options(self, qapp, monkeypatch, images, tmp_path):
        out = str(tmp_path / "out.pdf")
        calls = _install_fake_scanlayer(monkeypatch, lambda paths, o: _make_pdf(o, [True, True, True]))
        app = _App()
        app._merge_images_with_ocr_to_pdf(images, out, 90.0)

        assert len(calls) == 1
        call = calls[0]
        assert call["workers"] == 4 == ImageToPdfMixin.OCR_MERGE_WORKERS
        assert call["force"] is True
        assert call["orientation"] == 90.0
        assert call["paths"] == images  # input order preserved
        assert app.sequential_calls == []

    def test_ocr_usage_counts_only_pages_with_text(self, qapp, monkeypatch, images, tmp_path):
        out = str(tmp_path / "out.pdf")
        _install_fake_scanlayer(monkeypatch, lambda paths, o: _make_pdf(o, [True, False, True]))
        app = _App()
        app._merge_images_with_ocr_to_pdf(images, out, None)
        assert app.achievement_system.ocr_pages == 2

    def test_ui_is_disabled_during_the_merge_and_restored(self, qapp, monkeypatch, images, tmp_path):
        out = str(tmp_path / "out.pdf")
        _install_fake_scanlayer(monkeypatch, lambda paths, o: _make_pdf(o, [True, True, True]))
        app = _App()
        app._merge_images_with_ocr_to_pdf(images, out, None)
        assert app.ui_states == [False, True]
        assert app.progress_bar.ranges == [(0, 0), (0, 100)]  # busy bar, then back to a normal one
        assert app.progress_bar.values[-1] == 100

    def test_heic_named_png_is_converted_before_scanlayer(self, qapp, monkeypatch, tmp_path):
        pytest.importorskip("pillow_heif")
        from PIL import Image
        from pillow_heif import register_heif_opener

        register_heif_opener()
        heic = tmp_path / "photo.png"
        Image.new("RGB", (32, 32), (10, 120, 200)).save(heic, format="HEIF")

        seen = {}

        def behaviour(paths, out):
            seen["paths"] = list(paths)
            seen["existed"] = [os.path.exists(p) for p in paths]
            seen["is_png"] = [open(p, "rb").read(4) == b"\x89PNG" for p in paths]
            _make_pdf(out, [True])

        _install_fake_scanlayer(monkeypatch, behaviour)
        out = str(tmp_path / "out.pdf")
        _App()._merge_images_with_ocr_to_pdf([str(heic)], out, None)

        assert seen["paths"] != [str(heic)] and all(seen["existed"]) and all(seen["is_png"])
        assert not os.path.exists(seen["paths"][0])  # temp PNG cleaned up afterwards


class TestFallback:
    def test_scanlayer_failure_falls_back_to_sequential(self, qapp, monkeypatch, images, tmp_path):
        out = str(tmp_path / "out.pdf")

        def behaviour(paths, o):
            open(o, "wb").write(b"partial")
            raise RuntimeError("Unreadable or corrupted image")

        _install_fake_scanlayer(monkeypatch, behaviour)
        app = _App()
        app._merge_images_with_ocr_to_pdf(images, out, None)

        assert app.sequential_calls == [(images, out, None)]
        assert not os.path.exists(out)  # the partial file was removed
        assert app.achievement_system.ocr_pages is None
        assert app.ui_states == [False, True]  # UI restored even though the merge failed

    def test_old_scanlayer_without_workers_falls_back(self, qapp, monkeypatch, images, tmp_path):
        def convert_merge(paths, output_path, orientation=None, force=False):  # no `workers` parameter
            raise AssertionError("not reached")

        monkeypatch.setitem(sys.modules, "scanlayer", types.SimpleNamespace(convert_merge=convert_merge))
        app = _App()
        app._merge_images_with_ocr_to_pdf(images, str(tmp_path / "o.pdf"), None)
        assert len(app.sequential_calls) == 1


class TestRunOffUiThread:
    def test_returns_result(self, qapp):
        assert ImageToPdfMixin._run_off_ui_thread(lambda: 42) == 42

    def test_reraises_errors(self, qapp):
        def boom():
            raise ValueError("nope")

        with pytest.raises(ValueError, match="nope"):
            ImageToPdfMixin._run_off_ui_thread(boom)

    def test_runs_outside_the_calling_thread(self, qapp):
        import threading

        main = threading.get_ident()
        assert ImageToPdfMixin._run_off_ui_thread(threading.get_ident) != main

    def test_ui_keeps_processing_events_while_waiting(self, qapp):
        import time

        from PySide6.QtCore import QTimer

        ticks = []
        timer = QTimer()
        timer.setInterval(20)
        timer.timeout.connect(lambda: ticks.append(1))
        timer.start()
        ImageToPdfMixin._run_off_ui_thread(lambda: time.sleep(0.3))
        timer.stop()
        assert len(ticks) >= 3
