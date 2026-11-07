"""Batch PDF-to-DOCX conversions honor the configured PDF-to-Word mode."""

import io

import fitz
from docx import Document
from PIL import Image

from app.mixins.batch import BatchMixin
from app.mixins.pdf_to_word import PdfToWordMixin


class _BatchWordMixin(BatchMixin, PdfToWordMixin):
    pass


def _make_batch(mode: str | None = None) -> _BatchWordMixin:
    batch = _BatchWordMixin.__new__(_BatchWordMixin)
    batch.config = {"backup_before_conversion": False}
    if mode is not None:
        batch.config["pdf_to_word_mode"] = mode
    return batch


def _make_pdf(path, *, with_image: bool = False) -> None:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "Batch text")
    if with_image:
        image_bytes = io.BytesIO()
        Image.new("RGB", (40, 30), (200, 30, 30)).save(image_bytes, "PNG")
        page.insert_image(fitz.Rect(72, 120, 200, 220), stream=image_bytes.getvalue())
    document.save(str(path))
    document.close()


def test_batch_text_only_passes_source_and_destination(monkeypatch, tmp_path):
    source = tmp_path / "source.pdf"
    source.write_bytes(b"%PDF")
    output = tmp_path / "source.docx"
    batch = _make_batch("text_only")
    calls = []

    def fake_text_only(pdf_path, docx_path):
        calls.append((pdf_path, docx_path))
        return True

    monkeypatch.setattr(batch, "convert_pdf_to_docx_text_only", fake_text_only)
    monkeypatch.setattr(
        batch,
        "_try_word_com_pdf_to_docx",
        lambda *_args: (_ for _ in ()).throw(AssertionError("COM must not run")),
    )
    monkeypatch.setattr(
        batch,
        "_convert_pdf_to_docx_libreoffice",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("LibreOffice must not run")
        ),
    )

    assert batch._batch_pdf_to_docx(str(source), str(output)) is True
    assert calls == [(str(source), str(output))]


def test_batch_text_only_produces_text_without_images(tmp_path):
    source = tmp_path / "source.pdf"
    _make_pdf(source, with_image=True)
    output = tmp_path / "source.docx"
    batch = _make_batch("text_only")
    rich_calls = []
    batch._try_word_com_pdf_to_docx = lambda *_args: rich_calls.append("com") or False
    batch._convert_pdf_to_docx_libreoffice = (
        lambda *_args, **_kwargs: rich_calls.append("libreoffice") or False
    )
    batch._solid_fitz_fallback = lambda *_args: rich_calls.append("fitz") or False

    assert batch._batch_pdf_to_docx(str(source), str(output)) is True

    converted = Document(str(output))
    text = "\n".join(paragraph.text for paragraph in converted.paragraphs)
    assert "Batch text" in text
    assert len(converted.inline_shapes) == 0
    assert rich_calls == []


def test_batch_text_only_no_text_sets_batch_error(tmp_path):
    source = tmp_path / "image-only.pdf"
    document = fitz.open()
    image_only = document.new_page()
    image_bytes = io.BytesIO()
    Image.new("RGB", (40, 30), (200, 30, 30)).save(image_bytes, "PNG")
    image_only.insert_image(image_only.rect, stream=image_bytes.getvalue())
    document.save(str(source))
    document.close()
    output = tmp_path / "source.docx"
    batch = _make_batch("text_only")

    assert batch._batch_pdf_to_docx(str(source), str(output)) is False
    assert "No meaningful text" in batch._last_batch_error
    assert not output.exists()


def test_batch_with_images_keeps_rich_conversion_chain(tmp_path):
    source = tmp_path / "source.pdf"
    _make_pdf(source, with_image=True)
    output = tmp_path / "source.docx"
    batch = _make_batch("with_images")
    calls = []
    batch._try_word_com_pdf_to_docx = lambda *_args: calls.append("com") or False
    batch._convert_pdf_to_docx_libreoffice = (
        lambda *_args, **_kwargs: calls.append("libreoffice") or False
    )

    assert batch._batch_pdf_to_docx(str(source), str(output)) is True
    assert calls == ["com", "libreoffice"]
    assert output.is_file()
    assert output.stat().st_size > 0
