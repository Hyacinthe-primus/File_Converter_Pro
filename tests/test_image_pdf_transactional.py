"""Transactional guarantees for non-OCR image-to-PDF workflows."""

from __future__ import annotations

import threading
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image

import context_menu.conversion_helpers as helpers
import context_menu.window as cm_window
from app.mixins.batch import BatchMixin
from app.mixins.image_to_pdf import ImageToPdfMixin
from tasks import scheduler, watcher


def _make_image(path: Path, size=(32, 24)) -> Path:
    Image.new("RGB", size, "white").save(path)
    return path


def _invalid_engine(_files, target, _cancel_event=None):
    Path(target).write_bytes(b"not a pdf")


class _BadImage:
    def save(self, target, **_kwargs):
        Path(target).write_bytes(b"not a pdf")


class _MainHarness(ImageToPdfMixin):
    def __init__(self, output_dir: Path, fixed_output: Path | None = None):
        self.output_dir = output_dir
        self.fixed_output = fixed_output
        self.config = {"enable_system_notifications": False, "backup_before_conversion": False}
        self.db_manager = SimpleNamespace(add_conversion_record=lambda **_kwargs: None)
        self.achievement_system = SimpleNamespace(record_conversion=lambda *_args, **_kwargs: None)
        self.progress_bar = SimpleNamespace(setValue=lambda _value: None)
        self.system_notifier = SimpleNamespace(send=lambda *_args, **_kwargs: None)

    def get_output_directory(self, filename=None):
        if self.fixed_output is not None:
            return str(self.fixed_output)
        if filename:
            return str(self.output_dir / filename)
        return str(self.output_dir)

    def translate_text(self, text):
        return str(text)

    def show_progress(self, *_args, **_kwargs):
        return None

    def record_config_usage(self, *_args, **_kwargs):
        return None


def _message_boxes(monkeypatch):
    from app.mixins import image_to_pdf

    information = []
    critical = []
    monkeypatch.setattr(
        image_to_pdf.QMessageBox, "information", staticmethod(lambda *args: information.append(args))
    )
    monkeypatch.setattr(
        image_to_pdf.QMessageBox, "critical", staticmethod(lambda *args: critical.append(args))
    )
    return information, critical


def test_quick_single_image_failure_preserves_destination_and_staging_is_cleaned(tmp_path, monkeypatch):
    src = _make_image(tmp_path / "source.png")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    destination = out_dir / "source.pdf"
    destination.write_bytes(b"previous")

    monkeypatch.setattr(helpers, "_embed_images_in_pdf", _invalid_engine)

    with pytest.raises(RuntimeError, match="Image to PDF conversion failed"):
        helpers._convert_image_to_pdf(str(src), str(out_dir))

    assert destination.read_bytes() == b"previous"
    assert not list(out_dir.glob("~fcp_*"))


def test_quick_single_image_success_remains_valid(tmp_path):
    src = _make_image(tmp_path / "source.png")
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    helpers._convert_image_to_pdf(str(src), str(out_dir))

    output = out_dir / "source.pdf"
    assert output.is_file()
    import fitz

    with fitz.open(output) as document:
        assert document.page_count == 1


def test_quick_merged_image_failure_preserves_destination_and_staging_is_cleaned(tmp_path, monkeypatch):
    src = _make_image(tmp_path / "source.png")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    destination = out_dir / "merged_images_20260101_010101.pdf"
    destination.write_bytes(b"previous")

    monkeypatch.setattr(helpers.time, "strftime", lambda _format: "20260101_010101")
    monkeypatch.setattr(helpers, "_embed_images_in_pdf", _invalid_engine)

    with pytest.raises(RuntimeError, match="Image merge failed"):
        helpers._merge_images_to_pdf([str(src)], str(out_dir))

    assert destination.read_bytes() == b"previous"
    assert not list(out_dir.glob("~fcp_*"))


def test_quick_merged_image_cancellation_preserves_destination(tmp_path, monkeypatch):
    src = _make_image(tmp_path / "source.png")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    destination = out_dir / "merged_images_20260101_010101.pdf"
    destination.write_bytes(b"previous")
    cancel_event = threading.Event()
    cancel_event.set()

    monkeypatch.setattr(helpers.time, "strftime", lambda _format: "20260101_010101")

    with pytest.raises(cm_window._ConversionCancelled):
        helpers._merge_images_to_pdf([str(src)], str(out_dir), cancel_event=cancel_event)

    assert destination.read_bytes() == b"previous"
    assert not list(out_dir.glob("~fcp_*"))


def test_main_separate_image_success_remains_valid(tmp_path, monkeypatch):
    src = _make_image(tmp_path / "source.png")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    app = _MainHarness(out_dir)
    _message_boxes(monkeypatch)

    app.convert_images_to_separate_pdfs([str(src)], [])

    output = out_dir / "source.pdf"
    import fitz

    with fitz.open(output) as document:
        assert document.page_count == 1


def test_main_separate_image_failure_preserves_destination(tmp_path, monkeypatch):
    src = _make_image(tmp_path / "source.png")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    destination = out_dir / "source.pdf"
    destination.write_bytes(b"previous")
    app = _MainHarness(out_dir)
    _message_boxes(monkeypatch)

    monkeypatch.setattr(helpers, "_embed_images_in_pdf", _invalid_engine)

    app.convert_images_to_separate_pdfs([str(src)], [])

    assert destination.read_bytes() == b"previous"
    assert not list(out_dir.glob("~fcp_*"))


@pytest.mark.parametrize("image_count", [2, 1])
def test_main_merged_image_failure_preserves_destination(tmp_path, monkeypatch, image_count):
    images = [_make_image(tmp_path / f"source_{index}.png") for index in range(image_count)]
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    destination = out_dir / "result.pdf"
    destination.write_bytes(b"previous")
    app = _MainHarness(out_dir, fixed_output=destination)

    monkeypatch.setattr(ImageToPdfMixin, "_open_image_for_pdf", lambda _self, _path: _BadImage())
    _information, critical = _message_boxes(monkeypatch)

    app.convert_images_to_merged_pdf([str(path) for path in images], [])

    assert destination.read_bytes() == b"previous"
    assert len(critical) == 1
    assert not list(out_dir.glob("~fcp_*"))


def test_main_merged_image_success_remains_valid(tmp_path, monkeypatch):
    images = [_make_image(tmp_path / "one.png"), _make_image(tmp_path / "two.png")]
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    destination = out_dir / "result.pdf"
    app = _MainHarness(out_dir, fixed_output=destination)
    _message_boxes(monkeypatch)

    app.convert_images_to_merged_pdf([str(path) for path in images], [])

    import fitz

    with fitz.open(destination) as document:
        assert document.page_count == 2


def test_main_single_image_success_remains_valid(tmp_path, monkeypatch):
    src = _make_image(tmp_path / "source.png")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    destination = out_dir / "source.pdf"
    app = _MainHarness(out_dir, fixed_output=destination)
    _message_boxes(monkeypatch)

    app.convert_images_to_merged_pdf([str(src)], [])

    import fitz

    with fitz.open(destination) as document:
        assert document.page_count == 1


@pytest.mark.parametrize("runner", [watcher._run_conversion, scheduler._run_conversion])
def test_automation_single_image_failure_preserves_destination(tmp_path, monkeypatch, runner):
    src = _make_image(tmp_path / "source.png")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    destination = out_dir / "source.pdf"
    destination.write_bytes(b"previous")

    monkeypatch.setattr(helpers, "_embed_images_in_pdf", _invalid_engine)

    with pytest.raises(RuntimeError, match="Image to PDF conversion failed"):
        runner("image_to_pdf", str(src), str(out_dir), ocr=False)

    assert destination.read_bytes() == b"previous"
    assert not list(out_dir.glob("~fcp_*"))


@pytest.mark.parametrize("runner", [watcher._run_merge, scheduler._run_merge])
def test_automation_merged_image_failure_preserves_destination(tmp_path, monkeypatch, runner):
    src = _make_image(tmp_path / "source.png")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    destination = out_dir / "merged_images_20260101_010101.pdf"
    destination.write_bytes(b"previous")

    monkeypatch.setattr(helpers.time, "strftime", lambda _format: "20260101_010101")
    monkeypatch.setattr(helpers, "_embed_images_in_pdf", _invalid_engine)

    with pytest.raises(RuntimeError, match="Image merge failed"):
        runner("images_to_pdf_merged", [str(src)], str(out_dir), ocr=False)

    assert destination.read_bytes() == b"previous"
    assert not list(out_dir.glob("~fcp_*"))


def test_batch_image_failure_preserves_destination_and_staging_is_cleaned(tmp_path, monkeypatch):
    src = _make_image(tmp_path / "source.png")
    destination = tmp_path / "source.pdf"
    destination.write_bytes(b"previous")
    batch = BatchMixin.__new__(BatchMixin)
    batch.config = {"backup_before_conversion": False}
    batch._open_image_for_pdf = lambda _path: _BadImage()

    assert batch._batch_to_pdf(str(src), str(destination), ".png") is False

    assert destination.read_bytes() == b"previous"
    assert batch._last_batch_error.startswith("Image to PDF conversion failed:")
    assert not list(tmp_path.glob("~fcp_*"))


def test_automation_ocr_image_path_is_unchanged(tmp_path, monkeypatch):
    from tasks import ocr_helpers

    src = _make_image(tmp_path / "source.png")
    out_dir = tmp_path / "out"
    calls = []

    monkeypatch.setattr(ocr_helpers, "configure_scanlayer", lambda: None)
    monkeypatch.setattr(
        ocr_helpers,
        "image_to_pdf",
        lambda path, output, orientation: calls.append((path, output, orientation)) or True,
    )
    monkeypatch.setattr(
        helpers,
        "_convert_image_to_pdf",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("non-OCR helper used")),
    )

    watcher._run_conversion("image_to_pdf", str(src), str(out_dir), ocr=True)

    assert calls == [(str(src), str(out_dir / "source.pdf"), None)]
