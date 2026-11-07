"""Quick Convert publishes destinations transactionally around cancellation."""

import types
from pathlib import Path

from PIL import Image

import context_menu.window as cm_window
from converter import converters as converter_module


def _configure(monkeypatch):
    monkeypatch.setattr(
        cm_window,
        "_load_quick_config",
        lambda: {"backup_before_conversion": False},
    )


def _run_thread(files, conversion_type):
    thread = cm_window.ConversionThread([str(path) for path in files], conversion_type)
    done = []
    cancelled = []
    thread.done.connect(lambda *args: done.append(args))
    thread.cancelled.connect(lambda: cancelled.append(True))
    thread.run()
    return done, cancelled


def test_successful_conversion_publishes_final_output(monkeypatch, tmp_path):
    _configure(monkeypatch)
    source = tmp_path / "photo.png"
    Image.new("RGB", (20, 20), (20, 120, 200)).save(source)

    done, cancelled = _run_thread([source], "image_to_pdf")

    output = tmp_path / "photo.pdf"
    assert done == [(True, "1 file converted", str(tmp_path))]
    assert cancelled == []
    assert output.is_file()
    assert output.stat().st_size > 0
    assert not list(tmp_path.glob("~fcp_quick_*"))


def test_cancellation_does_not_publish_incomplete_output(monkeypatch, tmp_path):
    _configure(monkeypatch)
    source = tmp_path / "photo.png"
    source.write_bytes(b"source")
    thread_box = {}

    def fake_convert(src, staging_dir):
        Path(staging_dir, f"{Path(src).stem}.pdf").write_bytes(b"incomplete")
        thread_box["thread"].cancel()

    monkeypatch.setattr(cm_window, "_convert_image_to_pdf", fake_convert)
    thread = cm_window.ConversionThread([str(source)], "image_to_pdf")
    thread_box["thread"] = thread
    done = []
    cancelled = []
    thread.done.connect(lambda *args: done.append(args))
    thread.cancelled.connect(lambda: cancelled.append(True))

    thread.run()

    assert done == []
    assert cancelled == [True]
    assert not (tmp_path / "photo.pdf").exists()
    assert not list(tmp_path.glob("~fcp_quick_*"))


def test_generic_engine_cancellation_does_not_publish(monkeypatch, tmp_path):
    _configure(monkeypatch)
    source = tmp_path / "note.txt"
    source.write_text("source")
    output = tmp_path / "note.pdf"
    output.write_bytes(b"existing destination")
    thread_box = {}

    class FakeEngine:
        def convert(self, _conversion_type, _src, staging_dir, *, skip_backup=False):
            target = Path(staging_dir) / "note.pdf"
            target.write_bytes(b"incomplete")
            thread_box["thread"].cancel()
            return types.SimpleNamespace(success=True, target=str(target))

    monkeypatch.setattr(converter_module, "AdvancedConverterEngine", FakeEngine)
    thread = cm_window.ConversionThread([str(source)], "txt_to_pdf")
    thread_box["thread"] = thread
    thread.cancelled.connect(lambda: None)

    thread.run()

    assert output.read_bytes() == b"existing destination"
    assert not list(tmp_path.glob("~fcp_quick_*"))


def test_existing_destination_remains_unchanged_after_cancellation(monkeypatch, tmp_path):
    _configure(monkeypatch)
    source = tmp_path / "photo.png"
    source.write_bytes(b"source")
    output = tmp_path / "photo.pdf"
    output.write_bytes(b"existing destination")
    thread_box = {}

    def fake_convert(src, staging_dir):
        Path(staging_dir, f"{Path(src).stem}.pdf").write_bytes(b"incomplete")
        thread_box["thread"].cancel()

    monkeypatch.setattr(cm_window, "_convert_image_to_pdf", fake_convert)
    thread = cm_window.ConversionThread([str(source)], "image_to_pdf")
    thread_box["thread"] = thread
    thread.cancelled.connect(lambda: None)

    thread.run()

    assert output.read_bytes() == b"existing destination"
    assert not list(tmp_path.glob("~fcp_quick_*"))


def test_failure_cleans_temporary_output_and_preserves_destination(monkeypatch, tmp_path):
    _configure(monkeypatch)
    source = tmp_path / "photo.png"
    source.write_bytes(b"source")
    output = tmp_path / "photo.pdf"
    output.write_bytes(b"existing destination")

    def fail_convert(src, staging_dir):
        Path(staging_dir, f"{Path(src).stem}.pdf").write_bytes(b"incomplete")
        raise RuntimeError("conversion failed")

    monkeypatch.setattr(cm_window, "_convert_image_to_pdf", fail_convert)
    done, cancelled = _run_thread([source], "image_to_pdf")

    assert done and done[0][0] is False
    assert "conversion failed" in done[0][1]
    assert cancelled == []
    assert output.read_bytes() == b"existing destination"
    assert not list(tmp_path.glob("~fcp_quick_*"))
