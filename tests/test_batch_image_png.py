"""Transactional Batch image-to-PNG conversion tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from app.mixins.batch import BatchMixin
from utils import conversion_pipeline


def _make_batch():
    batch = BatchMixin.__new__(BatchMixin)
    batch.config = {"backup_before_conversion": False}
    return batch


def _make_jpeg(path: Path, color="blue") -> Path:
    Image.new("RGB", (16, 12), color).save(path, format="JPEG")
    return path


def _stage_files(root: Path) -> list[Path]:
    return list(root.glob("~fcp_png_*"))


def _assert_valid_png(path: Path) -> None:
    assert path.is_file()
    with Image.open(path) as image:
        assert image.format == "PNG"
        image.verify()


def test_jpg_to_png_produces_valid_png(tmp_path):
    src = _make_jpeg(tmp_path / "photo.jpg")
    out = tmp_path / "photo.png"
    batch = _make_batch()

    assert batch._batch_to_png(str(src), str(out), ".jpg") is True

    _assert_valid_png(out)
    assert not _stage_files(tmp_path)


@pytest.mark.parametrize(
    ("name", "payload"),
    [
        ("broken.jpg", b"not an image"),
        ("broken.png", b"\x89PNG\r\n\x1a\nnot a real png"),
    ],
)
def test_conversion_failure_does_not_copy_source_bytes(tmp_path, name, payload):
    src = tmp_path / name
    src.write_bytes(payload)
    out = tmp_path / "out.png"
    batch = _make_batch()

    assert batch._batch_to_png(str(src), str(out), Path(name).suffix) is False

    assert not out.exists()
    assert not _stage_files(tmp_path)
    assert batch._last_batch_error.startswith("Image to PNG conversion failed:")


def test_conversion_failure_does_not_report_success(tmp_path, monkeypatch):
    src = _make_jpeg(tmp_path / "photo.jpg")
    out = tmp_path / "photo.png"
    batch = _make_batch()

    def fail_save(_image, _target, **_kwargs):
        raise OSError("save failed")

    monkeypatch.setattr(Image.Image, "save", fail_save)

    assert batch._batch_to_png(str(src), str(out), ".jpg") is False
    assert not out.exists()
    assert "save failed" in batch._last_batch_error
    assert not _stage_files(tmp_path)


def test_conversion_failure_preserves_existing_destination(tmp_path):
    src = tmp_path / "broken.jpg"
    src.write_bytes(b"not an image")
    out = tmp_path / "photo.png"
    out.write_bytes(b"previous")
    batch = _make_batch()

    assert batch._batch_to_png(str(src), str(out), ".jpg") is False

    assert out.read_bytes() == b"previous"
    assert not _stage_files(tmp_path)


def test_conversion_failure_leaves_no_destination_when_none_existed(tmp_path):
    src = tmp_path / "broken.jpg"
    src.write_bytes(b"not an image")
    out = tmp_path / "photo.png"
    batch = _make_batch()

    assert batch._batch_to_png(str(src), str(out), ".jpg") is False

    assert not out.exists()
    assert not _stage_files(tmp_path)


@pytest.mark.parametrize("payload", [b"", b"\x89PNG\r\n\x1a\nmalformed"])
def test_empty_or_malformed_png_output_is_rejected(tmp_path, monkeypatch, payload):
    src = _make_jpeg(tmp_path / "photo.jpg")
    out = tmp_path / "photo.png"
    batch = _make_batch()

    def write_invalid(_image, target, **_kwargs):
        Path(target).write_bytes(payload)

    monkeypatch.setattr(Image.Image, "save", write_invalid)

    assert batch._batch_to_png(str(src), str(out), ".jpg") is False
    assert not out.exists()
    assert batch._last_batch_error.startswith("Image to PNG conversion failed:")
    assert not _stage_files(tmp_path)


def test_validation_failure_preserves_existing_destination(tmp_path, monkeypatch):
    src = _make_jpeg(tmp_path / "photo.jpg")
    out = tmp_path / "photo.png"
    out.write_bytes(b"previous")
    batch = _make_batch()

    def write_invalid(_image, target, **_kwargs):
        Path(target).write_bytes(b"\x89PNG\r\n\x1a\nmalformed")

    monkeypatch.setattr(Image.Image, "save", write_invalid)

    assert batch._batch_to_png(str(src), str(out), ".jpg") is False
    assert out.read_bytes() == b"previous"
    assert not _stage_files(tmp_path)


def test_temporary_files_are_cleaned_after_success_and_failure(tmp_path, monkeypatch):
    good = _make_jpeg(tmp_path / "good.jpg")
    good_out = tmp_path / "good.png"
    batch = _make_batch()

    assert batch._batch_to_png(str(good), str(good_out), ".jpg") is True
    assert not _stage_files(tmp_path)

    def fail_save(_image, _target, **_kwargs):
        raise OSError("save failed")

    monkeypatch.setattr(Image.Image, "save", fail_save)
    bad_out = tmp_path / "bad.png"
    assert batch._batch_to_png(str(good), str(bad_out), ".jpg") is False
    assert not _stage_files(tmp_path)


def test_atomic_replacement_failure_preserves_existing_destination(tmp_path, monkeypatch):
    src = _make_jpeg(tmp_path / "photo.jpg")
    out = tmp_path / "photo.png"
    out.write_bytes(b"previous")
    batch = _make_batch()

    def fail_replace(*_args):
        raise OSError("replace blocked")

    monkeypatch.setattr(conversion_pipeline.os, "replace", fail_replace)

    assert batch._batch_to_png(str(src), str(out), ".jpg") is False
    assert out.read_bytes() == b"previous"
    assert "replace blocked" in batch._last_batch_error
    assert not _stage_files(tmp_path)


def test_batch_continues_after_an_individual_image_failure(tmp_path):
    bad = tmp_path / "bad.jpg"
    bad.write_bytes(b"not an image")
    good = _make_jpeg(tmp_path / "good.jpg")
    bad_out = tmp_path / "bad.png"
    good_out = tmp_path / "good.png"
    batch = _make_batch()

    assert batch._convert_batch_file(str(bad), str(bad_out), "png") is False
    assert batch._convert_batch_file(str(good), str(good_out), "png") is True

    assert not bad_out.exists()
    _assert_valid_png(good_out)


@pytest.mark.parametrize(
    ("suffix", "method"),
    [(".pdf", "_batch_to_pdf"), (".docx", "_batch_to_docx")],
)
def test_legitimate_copy_callers_are_unchanged(tmp_path, suffix, method):
    src = tmp_path / f"source{suffix}"
    src.write_bytes(b"original bytes")
    out = tmp_path / f"out{suffix}"
    batch = _make_batch()

    assert getattr(batch, method)(str(src), str(out), suffix) is True
    assert out.read_bytes() == b"original bytes"
