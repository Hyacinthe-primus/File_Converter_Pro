"""PDF→DOCX ``text_only`` empty-content regressions.

Integration tests build real PDFs and execute the real text extractor and
shared pipeline. Mocked tests isolate extractor/fallback routing where a
deterministic real failure is impractical.
"""

from __future__ import annotations

import io
from pathlib import Path

import fitz
import pytest
from docx import Document
from PIL import Image

import context_menu.conversion_helpers as conversion_helpers
from pdf_text import NoExtractableTextError, convert_pdf_text_to_docx


def _write_pages_pdf(path: Path, texts: list[str | None]) -> str:
    with fitz.open() as pdf:
        for text in texts:
            page = pdf.new_page()
            if text:
                page.insert_text((72, 72), text, fontsize=14)
        pdf.save(str(path))
    return str(path)


def _write_text_pdf(path: Path, texts: list[str], fontname: str = "helv") -> str:
    with fitz.open() as pdf:
        for text in texts:
            page = pdf.new_page()
            page.insert_text((72, 72), text, fontsize=14, fontname=fontname)
        pdf.save(str(path))
    return str(path)


def _image_stream() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (100, 100), (70, 70, 70)).save(buffer, "PNG")
    return buffer.getvalue()


def _write_scanned_pdf(path: Path) -> str:
    with fitz.open() as pdf:
        page = pdf.new_page()
        page.insert_image(fitz.Rect(72, 72, 172, 172), stream=_image_stream())
        pdf.save(str(path))
    return str(path)


def _write_mixed_pdf(path: Path) -> str:
    with fitz.open() as pdf:
        text_page = pdf.new_page()
        text_page.insert_text((72, 72), "Mixed document text", fontsize=14)
        scanned_page = pdf.new_page()
        scanned_page.insert_image(fitz.Rect(72, 72, 172, 172), stream=_image_stream())
        pdf.save(str(path))
    return str(path)


def _write_whitespace_pdf(path: Path) -> str:
    with fitz.open() as pdf:
        page = pdf.new_page()
        page.insert_text((72, 72), "   \t   ", fontsize=12)
        pdf.save(str(path))
    return str(path)


def _convert_text_only(src: str, dst_dir: Path) -> None:
    conversion_helpers._convert_pdf_to_docx(src, str(dst_dir), mode="text_only")


def _paragraph_texts(document) -> list[str]:
    return [paragraph.text for paragraph in document.paragraphs]


def _page_breaks(document) -> int:
    from docx.oxml.ns import qn

    return sum(
        1
        for br in document.element.body.iter(qn("w:br"))
        if br.get(qn("w:type")) == "page"
    )


def _staging_artifacts(directory: Path) -> list[Path]:
    return list(directory.glob("~fcp_pdf_word_*")) + list(directory.glob("~fcp_pdf_stage_*"))


def _patch_config(monkeypatch, config):
    import config as config_module

    class FakeConfigManager:
        def load_config(self):
            return config

    monkeypatch.setattr(config_module, "ConfigManager", FakeConfigManager)


@pytest.mark.integration
def test_text_only_accepts_selectable_text(tmp_path):
    src = _write_text_pdf(tmp_path / "text.pdf", ["Selectable text"])
    _convert_text_only(src, tmp_path)

    output = tmp_path / "text.docx"
    assert output.is_file()
    assert any("Selectable text" in text for text in _paragraph_texts(Document(output)))
    assert _staging_artifacts(tmp_path) == []


@pytest.mark.integration
def test_text_only_rejects_scanned_pdf_without_writing_output(monkeypatch, tmp_path):
    src = _write_scanned_pdf(tmp_path / "scan.pdf")
    fallback_calls = []
    monkeypatch.setattr(
        conversion_helpers,
        "_solid_fitz_fallback",
        lambda *args, **kwargs: fallback_calls.append((args, kwargs)),
    )

    with pytest.raises(NoExtractableTextError, match="No meaningful text"):
        _convert_text_only(src, tmp_path)

    assert not (tmp_path / "scan.docx").exists()
    assert fallback_calls == []
    assert _staging_artifacts(tmp_path) == []


@pytest.mark.integration
def test_text_only_accepts_mixed_text_and_scanned_pages(tmp_path):
    src = _write_mixed_pdf(tmp_path / "mixed.pdf")
    _convert_text_only(src, tmp_path)

    document = Document(tmp_path / "mixed.docx")
    assert any("Mixed document text" in text for text in _paragraph_texts(document))
    assert len(document.inline_shapes) == 0
    assert _page_breaks(document) == 1


@pytest.mark.integration
def test_text_only_accepts_text_on_only_one_page_of_many(tmp_path):
    src = _write_pages_pdf(tmp_path / "pages.pdf", [None, None, "Only page with text"])
    _convert_text_only(src, tmp_path)

    document = Document(tmp_path / "pages.docx")
    assert [text for text in _paragraph_texts(document) if text] == ["Only page with text"]
    assert _page_breaks(document) == 2


@pytest.mark.integration
def test_text_only_preserves_unicode_text(tmp_path):
    src = _write_text_pdf(tmp_path / "unicode.pdf", ["中文测试"], fontname="china-s")
    _convert_text_only(src, tmp_path)

    document = Document(tmp_path / "unicode.docx")
    assert any("中文测试" in text for text in _paragraph_texts(document))


@pytest.mark.integration
def test_text_only_rejects_whitespace_only_pdf(tmp_path):
    src = _write_whitespace_pdf(tmp_path / "whitespace.pdf")

    with pytest.raises(NoExtractableTextError, match="No meaningful text"):
        _convert_text_only(src, tmp_path)

    assert not (tmp_path / "whitespace.docx").exists()
    assert _staging_artifacts(tmp_path) == []


@pytest.mark.integration
def test_text_only_invalid_pdf_fails_without_touching_destination(tmp_path):
    src = tmp_path / "broken.pdf"
    src.write_bytes(b"this is not a pdf")
    output = tmp_path / "broken.docx"
    output.write_bytes(b"existing destination")

    with pytest.raises(RuntimeError, match="All PDF→DOCX methods failed"):
        _convert_text_only(str(src), tmp_path)

    assert output.read_bytes() == b"existing destination"
    assert _staging_artifacts(tmp_path) == []


@pytest.mark.integration
def test_text_only_rejection_preserves_existing_destination(tmp_path):
    src = _write_scanned_pdf(tmp_path / "scan.pdf")
    output = tmp_path / "scan.docx"
    output.write_bytes(b"existing destination")

    with pytest.raises(NoExtractableTextError, match="No meaningful text"):
        _convert_text_only(src, tmp_path)

    assert output.read_bytes() == b"existing destination"
    assert _staging_artifacts(tmp_path) == []


@pytest.mark.integration
def test_text_only_extractor_reports_no_text_for_scanned_pdf(tmp_path):
    src = _write_scanned_pdf(tmp_path / "scan.pdf")
    output = tmp_path / "scan.docx"

    with pytest.raises(NoExtractableTextError, match="No meaningful text"):
        convert_pdf_text_to_docx(src, str(output))

    assert not output.exists()


@pytest.mark.integration
def test_quick_convert_window_text_only_rejects_scanned_pdf(tmp_path):
    import context_menu.window as cm_window

    src = _write_scanned_pdf(tmp_path / "scan.pdf")
    output = tmp_path / "scan.docx"

    with pytest.raises(NoExtractableTextError, match="No meaningful text"):
        cm_window._convert_pdf_to_docx(src, str(tmp_path), mode="text_only")

    assert not output.exists()
    assert _staging_artifacts(tmp_path) == []


@pytest.mark.integration
def test_main_text_only_rejects_scanned_pdf(tmp_path):
    from app.mixins.pdf_to_word import PdfToWordMixin

    src = _write_scanned_pdf(tmp_path / "scan.pdf")
    output = tmp_path / "scan.docx"
    mixin = PdfToWordMixin.__new__(PdfToWordMixin)

    assert mixin.convert_pdf_to_docx_text_only(src, str(output)) is False
    assert "No meaningful text" in mixin._last_pdf_to_word_error
    assert not output.exists()
    assert _staging_artifacts(tmp_path) == []


@pytest.mark.integration
@pytest.mark.parametrize("module_name", ["watcher", "scheduler"])
def test_automation_text_only_propagates_no_text_failure(monkeypatch, tmp_path, module_name):
    from tasks import scheduler, watcher

    src = _write_scanned_pdf(tmp_path / "scan.pdf")
    out_dir = tmp_path / "out"
    _patch_config(monkeypatch, {"pdf_to_word_mode": "text_only"})
    runner = watcher._run_conversion if module_name == "watcher" else scheduler._run_conversion

    with pytest.raises(NoExtractableTextError, match="No meaningful text"):
        runner("pdf_to_docx", src, str(out_dir))

    assert not (out_dir / "scan.docx").exists()
    assert _staging_artifacts(out_dir) == []


def test_mocked_no_text_failure_skips_rich_fallback(monkeypatch, tmp_path):
    src = _write_text_pdf(tmp_path / "input.pdf", ["ignored"])
    fallback_calls = []

    def fail_text_to_docx(*_args, **_kwargs):
        raise NoExtractableTextError("no meaningful text")

    monkeypatch.setattr(conversion_helpers, "convert_pdf_text_to_docx", fail_text_to_docx)
    monkeypatch.setattr(
        conversion_helpers,
        "_solid_fitz_fallback",
        lambda *args, **kwargs: fallback_calls.append((args, kwargs)),
    )

    with pytest.raises(NoExtractableTextError, match="no meaningful text"):
        _convert_text_only(src, tmp_path)

    assert fallback_calls == []
    assert not (tmp_path / "input.docx").exists()
    assert _staging_artifacts(tmp_path) == []
