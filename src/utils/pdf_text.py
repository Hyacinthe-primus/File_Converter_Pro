"""Shared text-only PDF → DOCX extraction.

Used by the main app's text-only mode and Quick Convert so both follow the
same extraction behavior without invoking Word COM, pdf2docx, or layout
preservation.
"""

from __future__ import annotations

from collections.abc import Callable

_NO_TEXT_MESSAGE = (
    "No meaningful text could be extracted from the PDF. "
    "It may be a scanned or image-only document; use the 'with images' mode or OCR the PDF first."
)


class NoExtractableTextError(RuntimeError):
    """Raised when a PDF has no meaningful selectable text."""


def _has_meaningful_text(text: str) -> bool:
    return bool(text.strip())


def convert_pdf_text_to_docx(
    pdf_path: str,
    docx_path: str,
    cancel_check: Callable[[], None] | None = None,
) -> None:
    """Extract PDF text into a DOCX, without images or page layout."""
    import fitz
    from docx import Document

    if cancel_check is not None:
        cancel_check()

    word_doc = Document()
    pdf_doc = fitz.open(pdf_path)
    has_meaningful_text = False
    try:
        page_count = len(pdf_doc)
        for page_num in range(page_count):
            if cancel_check is not None:
                cancel_check()
            text = pdf_doc.load_page(page_num).get_text("text")
            if _has_meaningful_text(text):
                has_meaningful_text = True
                for line in text.split("\n"):
                    line = line.strip()
                    if line:
                        word_doc.add_paragraph(line)
            if page_num < page_count - 1:
                word_doc.add_page_break()
        if cancel_check is not None:
            cancel_check()
        if not has_meaningful_text:
            raise NoExtractableTextError(_NO_TEXT_MESSAGE)
    finally:
        pdf_doc.close()

    word_doc.save(docx_path)


def build_text_only_engines(
    pdf_path: str,
    fallback: Callable[[str, str], object],
    *,
    text_converter: Callable[..., None] | None = None,
    cancel_check: Callable[[], None] | None = None,
) -> tuple[list[tuple[str, Callable[[str], object]]], list[NoExtractableTextError]]:
    """Build text-only engines and collect any no-text failure.

    The rich fallback is skipped when the text extractor reports that the
    PDF has no meaningful text, so an image-only document cannot be
    reported as a successful text-only conversion.
    """
    converter = text_converter or convert_pdf_text_to_docx
    no_text_errors: list[NoExtractableTextError] = []

    def _run_text(target: str) -> None:
        try:
            if cancel_check is None:
                converter(pdf_path, target)
            else:
                converter(pdf_path, target, cancel_check=cancel_check)
        except NoExtractableTextError as exc:
            no_text_errors.append(exc)
            raise

    def _run_fallback(target: str) -> object:
        if no_text_errors:
            raise no_text_errors[0]
        return fallback(pdf_path, target)

    return [
        ("text extraction", _run_text),
        ("fitz fallback", _run_fallback),
    ], no_text_errors
