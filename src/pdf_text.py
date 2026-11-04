"""Shared text-only PDF → DOCX extraction.

Used by the main app's text-only mode and Quick Convert so both follow the
same extraction behavior without invoking Word COM, pdf2docx, or layout
preservation.
"""

from __future__ import annotations

from collections.abc import Callable


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
    try:
        page_count = len(pdf_doc)
        for page_num in range(page_count):
            if cancel_check is not None:
                cancel_check()
            text = pdf_doc.load_page(page_num).get_text("text")
            if text.strip():
                for line in text.split("\n"):
                    line = line.strip()
                    if line:
                        word_doc.add_paragraph(line)
            if page_num < page_count - 1:
                word_doc.add_page_break()
        if cancel_check is not None:
            cancel_check()
    finally:
        pdf_doc.close()

    word_doc.save(docx_path)
