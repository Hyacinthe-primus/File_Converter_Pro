"""Batch format recognition, mapping, and explicit rejection regressions."""

import types
from pathlib import Path

import fitz
import pytest
from docx import Document
from PIL import Image

from app.mixins.batch import BatchMixin
from converter import converters as converter_module


def _make_batch() -> BatchMixin:
    batch = BatchMixin.__new__(BatchMixin)
    batch.config = {"backup_before_conversion": False}
    return batch


def _make_image(path: Path, fmt: str) -> Path:
    if fmt == "HEIF":
        pytest.importorskip("pillow_heif")
        from pillow_heif import register_heif_opener

        register_heif_opener()
    try:
        Image.new("RGB", (18, 12), (120, 30, 30)).save(path, format=fmt)
    except Exception as exc:
        pytest.skip(f"{fmt} encoding unavailable: {exc}")
    return path


def _make_pdf(path: Path) -> Path:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "Batch")
    document.save(str(path))
    document.close()
    return path


def _assert_pdf(path: Path) -> None:
    with fitz.open(path) as document:
        assert document.page_count == 1


def _assert_png(path: Path) -> None:
    with Image.open(path) as image:
        assert image.format == "PNG"
        image.verify()


def _assert_docx(path: Path) -> None:
    document = Document(str(path))
    assert len(document.inline_shapes) == 1


def _fake_engine(monkeypatch, calls):
    class FakeEngine:
        def __init__(self):
            self.allow_local_html_resources = False

        def convert(self, conversion_type, src, dst_dir, *, skip_backup=False):
            calls.append((conversion_type, Path(src).name, Path(dst_dir)))
            return types.SimpleNamespace(success=True, error="")

    monkeypatch.setattr(converter_module, "AdvancedConverterEngine", FakeEngine)


@pytest.mark.parametrize(
    ("suffix", "fmt"),
    [
        (".heic", "HEIF"),
        (".avif", "AVIF"),
        (".j2k", "JPEG2000"),
    ],
)
def test_supported_special_images_convert_to_pdf_png_and_docx(tmp_path, suffix, fmt):
    source = _make_image(tmp_path / f"photo{suffix}", fmt)
    batch = _make_batch()

    assert batch._batch_to_pdf(str(source), str(tmp_path / "photo.pdf"), suffix) is True
    assert batch._batch_to_png(str(source), str(tmp_path / "photo.png"), suffix) is True
    assert batch._batch_image_to_docx(str(source), str(tmp_path / "photo.docx")) is True

    _assert_pdf(tmp_path / "photo.pdf")
    _assert_png(tmp_path / "photo.png")
    _assert_docx(tmp_path / "photo.docx")


def test_svg_converts_to_pdf_png_and_docx(tmp_path):
    source = tmp_path / "drawing.svg"
    source.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="12">'
        '<rect width="18" height="12" fill="red"/></svg>',
        encoding="utf-8",
    )
    batch = _make_batch()

    assert batch._batch_to_pdf(str(source), str(tmp_path / "drawing.pdf"), ".svg") is True
    assert batch._batch_to_png(str(source), str(tmp_path / "drawing.png"), ".svg") is True
    assert batch._batch_image_to_docx(str(source), str(tmp_path / "drawing.docx")) is True

    _assert_pdf(tmp_path / "drawing.pdf")
    _assert_png(tmp_path / "drawing.png")
    _assert_docx(tmp_path / "drawing.docx")


@pytest.mark.parametrize("suffix", [".dng", ".psd"])
def test_recognized_but_unsupported_images_are_rejected(suffix, tmp_path, monkeypatch):
    source = tmp_path / f"source{suffix}"
    source.write_bytes(b"unsupported image")
    batch = _make_batch()
    calls = []
    _fake_engine(monkeypatch, calls)

    assert batch._batch_to_pdf(str(source), str(tmp_path / "out.pdf"), suffix) is False
    assert suffix in batch._last_batch_error
    assert "does not support" in batch._last_batch_error

    assert batch._batch_to_png(str(source), str(tmp_path / "out.png"), suffix) is False
    assert suffix in batch._last_batch_error

    assert batch._batch_to_docx(str(source), str(tmp_path / "out.docx"), suffix) is False
    assert suffix in batch._last_batch_error
    assert calls == []


def test_opendocument_formats_use_shared_conversion_mapping(monkeypatch, tmp_path):
    calls = []
    _fake_engine(monkeypatch, calls)
    batch = _make_batch()

    for suffix, conversion_type in (
        (".odt", "odt_to_pdf"),
        (".ods", "ods_to_pdf"),
        (".odp", "odp_to_pdf"),
    ):
        source = tmp_path / f"document{suffix}"
        source.write_bytes(b"document")
        assert batch._batch_to_pdf(
            str(source), str(tmp_path / f"{source.stem}.pdf"), suffix
        ) is True
        assert calls[-1][0] == conversion_type

    odt = tmp_path / "document.odt"
    assert batch._batch_to_docx(str(odt), str(tmp_path / "document.docx"), ".odt") is True
    assert calls[-1][0] == "odt_to_docx"


def test_odt_to_png_uses_pdf_intermediate_mapping(monkeypatch, tmp_path):
    calls = []

    class FakeEngine:
        def __init__(self):
            self.allow_local_html_resources = False

        def convert(self, conversion_type, src, dst_dir, *, skip_backup=False):
            calls.append(conversion_type)
            target = Path(dst_dir) / f"{Path(src).stem}.pdf"
            _make_pdf(target)
            return types.SimpleNamespace(success=True, error="")

    monkeypatch.setattr(converter_module, "AdvancedConverterEngine", FakeEngine)
    source = tmp_path / "document.odt"
    source.write_bytes(b"document")
    output = tmp_path / "document.png"
    batch = _make_batch()

    assert batch._batch_to_png(str(source), str(output), ".odt") is True
    assert calls == ["odt_to_pdf"]
    _assert_png(output)


def test_htm_alias_uses_html_conversion_mapping(monkeypatch, tmp_path):
    calls = []
    _fake_engine(monkeypatch, calls)
    source = tmp_path / "page.htm"
    source.write_text("<html><body>page</body></html>", encoding="utf-8")
    batch = _make_batch()

    assert batch._batch_to_pdf(str(source), str(tmp_path / "page.pdf"), ".htm") is True
    assert calls[-1][0] == "html_to_pdf"


def test_ods_to_docx_is_explicitly_rejected(monkeypatch, tmp_path):
    calls = []
    _fake_engine(monkeypatch, calls)
    source = tmp_path / "sheet.ods"
    source.write_bytes(b"sheet")
    batch = _make_batch()

    assert batch._batch_to_docx(str(source), str(tmp_path / "sheet.docx"), ".ods") is False
    assert ".ods" in batch._last_batch_error
    assert calls == []


def test_doc_to_docx_is_rejected_instead_of_copied(tmp_path):
    source = tmp_path / "legacy.doc"
    source.write_bytes(b"legacy binary word document")
    output = tmp_path / "legacy.docx"
    batch = _make_batch()

    assert batch._batch_to_docx(str(source), str(output), ".doc") is False
    assert "legacy .doc" in batch._last_batch_error.lower()
    assert not output.exists()


@pytest.mark.parametrize("target", ["pdf", "docx", "png"])
@pytest.mark.parametrize("suffix", [".md", ".csv", ".mp3"])
def test_recognized_non_image_formats_without_target_path_are_rejected(
    target, suffix, tmp_path
):
    source = tmp_path / f"source{suffix}"
    source.write_bytes(b"source")
    output = tmp_path / f"out.{target}"
    batch = _make_batch()

    assert batch._convert_batch_file(str(source), str(output), target) is False
    assert batch._last_batch_error
    assert suffix in batch._last_batch_error
    assert not output.exists()
