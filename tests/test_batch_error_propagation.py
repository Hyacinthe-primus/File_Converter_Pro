"""Batch error propagation regressions."""

import types
from pathlib import Path

from PIL import Image

from app.mixins.batch import BatchMixin
from converter import converters as converter_module


def _make_batch() -> BatchMixin:
    batch = BatchMixin.__new__(BatchMixin)
    batch.config = {"backup_before_conversion": False}
    return batch


def _fake_engine(monkeypatch, *, error="", raises=None):
    class FakeEngine:
        def __init__(self):
            self.allow_local_html_resources = False

        def convert(self, *_args, **_kwargs):
            if raises is not None:
                raise raises
            return types.SimpleNamespace(success=False, error=error)

    monkeypatch.setattr(converter_module, "AdvancedConverterEngine", FakeEngine)


def test_genuine_unsupported_conversion_is_distinct(tmp_path):
    source = tmp_path / "source.xyz"
    source.write_bytes(b"source")
    batch = _make_batch()

    assert batch._convert_batch_file(str(source), str(tmp_path / "out.pdf"), "pdf") is False
    assert ".xyz" in batch._last_batch_error
    assert "does not support" in batch._last_batch_error
    assert "conversion failed" not in batch._last_batch_error.lower()


def test_engine_failure_preserves_original_error(monkeypatch, tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("source")
    batch = _make_batch()
    _fake_engine(monkeypatch, error="engine exploded")

    assert batch._convert_batch_file(str(source), str(tmp_path / "out.pdf"), "pdf") is False
    assert batch._last_batch_error == "engine exploded"


def test_engine_exception_preserves_original_error(monkeypatch, tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("source")
    batch = _make_batch()
    _fake_engine(monkeypatch, raises=RuntimeError("engine crashed"))

    assert batch._convert_batch_file(str(source), str(tmp_path / "out.pdf"), "pdf") is False
    assert "engine crashed" in batch._last_batch_error
    assert "Batch PDF conversion failed" in batch._last_batch_error


def test_copy_failure_preserves_reason(tmp_path):
    output = tmp_path / "out.pdf"
    batch = _make_batch()

    assert batch._batch_to_pdf(
        str(tmp_path / "missing.pdf"), str(output), ".pdf"
    ) is False
    assert "File copy failed" in batch._last_batch_error
    assert "missing.pdf" in batch._last_batch_error
    assert not output.exists()


def test_image_to_docx_failure_preserves_decoder_error(tmp_path):
    source = tmp_path / "source.png"
    Image.new("RGB", (8, 8), "white").save(source)
    batch = _make_batch()

    def fail_open(_path):
        raise RuntimeError("decoder exploded")

    batch._open_image_for_pdf = fail_open

    assert batch._batch_to_docx(str(source), str(tmp_path / "out.docx"), ".png") is False
    assert "Image to DOCX conversion failed" in batch._last_batch_error
    assert "decoder exploded" in batch._last_batch_error


def test_pdf_to_png_failure_preserves_render_error(tmp_path):
    source = tmp_path / "source.pdf"
    source.write_bytes(b"%PDF")
    batch = _make_batch()

    def fail_render(*_args):
        raise RuntimeError("render exploded")

    batch._pdf_to_png = fail_render

    assert batch._batch_to_png(str(source), str(tmp_path / "out.png"), ".pdf") is False
    assert "render exploded" in batch._last_batch_error


def test_error_state_is_reset_between_operations(tmp_path):
    unsupported = tmp_path / "source.xyz"
    unsupported.write_bytes(b"source")
    valid_pdf = tmp_path / "source.pdf"
    valid_pdf.write_bytes(b"pdf bytes")
    output = tmp_path / "copy.pdf"
    batch = _make_batch()

    assert batch._convert_batch_file(str(unsupported), str(tmp_path / "out.pdf"), "pdf") is False
    assert batch._last_batch_error

    assert batch._convert_batch_file(str(valid_pdf), str(output), "pdf") is True
    assert batch._last_batch_error == ""
    assert output.read_bytes() == b"pdf bytes"


def test_consecutive_failures_do_not_leak_previous_error(tmp_path):
    first = tmp_path / "first.xyz"
    second = tmp_path / "second.md"
    first.write_bytes(b"first")
    second.write_bytes(b"second")
    batch = _make_batch()

    assert batch._convert_batch_file(str(first), str(tmp_path / "out.pdf"), "pdf") is False
    assert ".xyz" in batch._last_batch_error

    assert batch._convert_batch_file(str(second), str(tmp_path / "out2.pdf"), "pdf") is False
    assert ".md" in batch._last_batch_error
    assert ".xyz" not in batch._last_batch_error


def test_direct_image_conversion_clears_previous_error(tmp_path):
    bad = tmp_path / "bad.png"
    good = tmp_path / "good.png"
    bad.write_bytes(b"bad")
    Image.new("RGB", (8, 8), "white").save(good)
    batch = _make_batch()
    real_open = BatchMixin._open_batch_image

    def fail_bad(self, path):
        if Path(path).name == "bad.png":
            raise RuntimeError("bad image")
        return real_open(self, path)

    batch._open_batch_image = types.MethodType(fail_bad, batch)

    assert batch._batch_image_to_docx(str(bad), str(tmp_path / "bad.docx")) is False
    assert "bad image" in batch._last_batch_error

    assert batch._batch_image_to_docx(str(good), str(tmp_path / "good.docx")) is True
    assert batch._last_batch_error == ""
