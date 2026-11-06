"""Shared OCR orchestration: real Tesseract coverage and failure safety."""

import sys
import types
from pathlib import Path

import fitz
import pytest
from PIL import Image, ImageDraw, ImageFont

import tasks.ocr_helpers as ocr_helpers
from external_binaries import resolve_binary
from utils.pdf_artifacts import validate_pdf_artifact

TESSERACT = resolve_binary("tesseract")


def _make_text_image(path: Path, text: str) -> Path:
    canvas = Image.new("RGB", (1400, 300), "white")
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 72)
    except OSError:
        font = ImageFont.load_default(size=72)
    draw.text((40, 80), text, fill="black", font=font)
    canvas.save(path)
    return path


def _make_pdf(path: Path, text: str = "page") -> Path:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    document.save(str(path))
    document.close()
    return path


def _pdf_text(path: Path) -> str:
    with fitz.open(str(path)) as document:
        return "\n".join(page.get_text() for page in document)


def test_main_and_automation_use_same_bounded_worker_count():
    from app.mixins.image_to_pdf import ImageToPdfMixin

    assert ImageToPdfMixin.OCR_MERGE_WORKERS == ocr_helpers.OCR_MERGE_WORKERS == 4


@pytest.mark.integration
@pytest.mark.skipif(not TESSERACT, reason="Tesseract is not installed; real OCR test skipped")
def test_real_tesseract_image_ocr_preserves_searchable_text(tmp_path):
    ocr_helpers.configure_scanlayer("auto")
    source = _make_text_image(tmp_path / "scan.png", "HELLO OCR 12345")
    output = tmp_path / "scan.pdf"

    assert ocr_helpers.image_to_pdf(str(source), str(output), None) is True
    assert validate_pdf_artifact(str(output)) == (True, "")
    text = _pdf_text(output)
    assert "HELLO" in text
    assert "12345" in text
    assert not list(tmp_path.glob("~fcp_ocr_*"))


@pytest.mark.integration
@pytest.mark.skipif(not TESSERACT, reason="Tesseract is not installed; real OCR test skipped")
def test_real_tesseract_merge_ocr_preserves_page_order_and_text(tmp_path):
    ocr_helpers.configure_scanlayer("auto")
    first = _make_text_image(tmp_path / "first.png", "FIRST PAGE")
    second = _make_text_image(tmp_path / "second.png", "SECOND PAGE")
    output = tmp_path / "merged.pdf"

    assert ocr_helpers.merge_images_with_ocr([str(first), str(second)], str(output), None) is True
    assert validate_pdf_artifact(str(output)) == (True, "")
    with fitz.open(str(output)) as document:
        assert document.page_count == 2
        pages = [page.get_text() for page in document]
    assert "FIRST" in pages[0]
    assert "SECOND" in pages[1]
    assert not list(tmp_path.glob("~fcp_ocr_*"))


def test_image_ocr_failure_preserves_existing_destination(monkeypatch, tmp_path):
    source = _make_text_image(tmp_path / "scan.png", "UNREADABLE")
    output = _make_pdf(tmp_path / "output.pdf", "stale")
    original = output.read_bytes()
    monkeypatch.setattr(ocr_helpers, "image_ocr_able", lambda *_args: False)

    def fail_embed(*_args):
        raise RuntimeError("plain embed failed")

    monkeypatch.setattr(ocr_helpers, "embed_image_in_pdf", fail_embed)

    with pytest.raises(RuntimeError, match="OCR image conversion failed"):
        ocr_helpers.image_to_pdf(str(source), str(output), None)

    assert output.read_bytes() == original
    assert not list(tmp_path.glob("~fcp_ocr_*"))


def test_merge_ocr_failure_preserves_existing_destination(monkeypatch, tmp_path):
    images = [
        _make_text_image(tmp_path / "one.png", "ONE"),
        _make_text_image(tmp_path / "two.png", "TWO"),
    ]
    output = _make_pdf(tmp_path / "output.pdf", "stale")
    original = output.read_bytes()
    monkeypatch.setattr(ocr_helpers, "_merge_parallel", lambda *_args: False)

    def fail_sequential(*_args):
        raise RuntimeError("sequential merge failed")

    monkeypatch.setattr(ocr_helpers, "_merge_sequential", fail_sequential)

    assert ocr_helpers.merge_images_with_ocr([str(path) for path in images], str(output), None) is False

    assert output.read_bytes() == original
    assert not list(tmp_path.glob("~fcp_ocr_*"))


def test_invalid_ocr_output_falls_back_to_plain_embed(monkeypatch, tmp_path):
    source = _make_text_image(tmp_path / "scan.png", "INVALID OCR")
    output = tmp_path / "output.pdf"
    module = types.ModuleType("scanlayer")

    class Result:
        words_count = 1

    def convert(input_path=None, output_path=None, orientation=None, force=False):
        Path(output_path).write_bytes(b"%PDF")
        return Result()

    module.convert = convert
    monkeypatch.setitem(sys.modules, "scanlayer", module)

    assert ocr_helpers.image_to_pdf(str(source), str(output), None) is False
    assert validate_pdf_artifact(str(output)) == (True, "")
    assert _pdf_text(output).strip() == ""
    assert not list(tmp_path.glob("~fcp_ocr_*"))


def test_invalid_parallel_merge_falls_back_to_sequential(monkeypatch, tmp_path):
    images = [
        _make_text_image(tmp_path / "one.png", "ONE"),
        _make_text_image(tmp_path / "two.png", "TWO"),
    ]
    output = tmp_path / "merged.pdf"
    module = types.ModuleType("scanlayer")
    calls = {"merge": 0, "convert": 0}

    class Result:
        words_count = 1

    def convert_merge(paths, output_path, **kwargs):
        calls["merge"] += 1
        Path(output_path).write_bytes(b"%PDF")

    def convert(input_path=None, output_path=None, orientation=None, force=False):
        calls["convert"] += 1
        _make_pdf(Path(output_path), "PAGE TEXT")
        return Result()

    module.convert_merge = convert_merge
    module.convert = convert
    monkeypatch.setitem(sys.modules, "scanlayer", module)

    assert ocr_helpers.merge_images_with_ocr([str(path) for path in images], str(output), None) is True
    assert calls == {"merge": 1, "convert": 2}
    assert validate_pdf_artifact(str(output)) == (True, "")
    with fitz.open(str(output)) as document:
        assert document.page_count == 2
        assert all("PAGE TEXT" in page.get_text() for page in document)
    assert not list(tmp_path.glob("~fcp_ocr_*"))


def test_sequential_merge_cleans_temporary_directory(monkeypatch, tmp_path):
    images = [
        _make_text_image(tmp_path / "one.png", "ONE"),
        _make_text_image(tmp_path / "two.png", "TWO"),
    ]
    output = tmp_path / "merged.pdf"
    module = types.ModuleType("scanlayer")
    created_dirs = []
    real_mkdtemp = ocr_helpers.tempfile.mkdtemp

    class Result:
        words_count = 1

    def convert(input_path=None, output_path=None, orientation=None, force=False):
        _make_pdf(Path(output_path), "PAGE TEXT")
        return Result()

    def mkdtemp(*args, **kwargs):
        path = real_mkdtemp(dir=tmp_path, prefix="fcp_ocr_merge_")
        created_dirs.append(path)
        return path

    module.convert = convert
    monkeypatch.setitem(sys.modules, "scanlayer", module)
    monkeypatch.setattr(ocr_helpers, "_merge_parallel", lambda *_args: False)
    monkeypatch.setattr(ocr_helpers.tempfile, "mkdtemp", mkdtemp)

    assert ocr_helpers.merge_images_with_ocr([str(path) for path in images], str(output), None) is True
    assert created_dirs
    assert all(not Path(path).exists() for path in created_dirs)
    assert not list(tmp_path.glob("~fcp_ocr_*"))
