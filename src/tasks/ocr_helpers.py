"""
tasks/ocr_helpers.py
File Converter Pro

Headless OCR helpers for watch folders and scheduled tasks.

When a task sets ocr = true, image → PDF conversions produce searchable
PDFs through scanlayer, using the orientation configured in the app. Images
scanlayer cannot read fall back to a plain image embed, exactly like the
interactive OCR path.
"""

from __future__ import annotations

import contextlib
import logging
import os
import shutil
import tempfile

logger = logging.getLogger(__name__)

OCR_MERGE_WORKERS = 4


def resolve_orientation(raw=None):
    """Map the ocr_orientation config string to the scanlayer orientation.

    "auto" -> None (auto-detect), "none"/empty -> "none" (disabled),
    otherwise -> float angle in degrees. When *raw* is None the value is read
    from the app config.
    """
    if raw is None:
        try:
            from config import ConfigManager

            raw = ConfigManager().load_config().get("ocr_orientation", "auto")
        except Exception:
            raw = "auto"

    if isinstance(raw, bool):
        return "none" if raw is False else None
    if raw is None:
        return "none"
    value = str(raw).strip()
    if not value or value == "auto":
        return None
    if value == "none":
        return "none"
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def configure_scanlayer():
    """Resolve Tesseract, hide its console, and return the orientation value."""
    import scanlayer

    from external_binaries import resolve_binary
    from utils.tesseract_console import suppress_tesseract_console

    tesseract = resolve_binary("tesseract")
    if tesseract:
        scanlayer.configure(tesseract_cmd=tesseract)

    suppress_tesseract_console()
    return resolve_orientation()


def image_ocr_able(src: str, out_pdf: str, orientation) -> bool:
    """OCR one image into *out_pdf*; True when text was found."""
    import scanlayer

    from utils.image_formats import decodable_image_path

    try:
        with decodable_image_path(src) as readable:
            result = scanlayer.convert(
                input_path=readable,
                output_path=out_pdf,
                orientation=orientation,
                force=True,
            )
        return bool(getattr(result, "words_count", 0))
    except Exception as e:
        logger.warning("[OCR] %s failed, falling back to plain PDF: %s", src, e)
        return False


def embed_image_in_pdf(src: str, out_pdf: str) -> None:
    """Embed a single image into a plain (non-OCR) PDF using PyMuPDF."""
    import fitz

    from utils.image_formats import decodable_image_path

    pdf = fitz.open()
    with decodable_image_path(src) as readable:
        img = fitz.open(readable)
        rect = img[0].rect
        page = pdf.new_page(width=rect.width, height=rect.height)
        page.insert_image(rect, filename=readable)
        img.close()
    pdf.save(out_pdf)
    pdf.close()


def image_to_pdf(src: str, out_pdf: str, orientation) -> bool:
    """Convert one image to PDF, using OCR when possible else a plain embed.

    Returns True when OCR produced text, False when the plain embed was used.
    """
    if image_ocr_able(src, out_pdf, orientation):
        return True
    embed_image_in_pdf(src, out_pdf)
    return False


def merge_images_with_ocr(files: list[str], out_pdf: str, orientation) -> bool:
    """Merge images into one searchable PDF.

    Fast path: scanlayer's parallel merge. If it cannot handle the batch,
    fall back to one page at a time, where a page OCR cannot read is embedded
    as a plain image. Returns True when *out_pdf* was written.
    """
    if _merge_parallel(files, out_pdf, orientation):
        return True
    _merge_sequential(files, out_pdf, orientation)
    return os.path.isfile(out_pdf) and os.path.getsize(out_pdf) > 0


def _merge_parallel(files: list[str], out_pdf: str, orientation) -> bool:
    import scanlayer

    from utils.image_formats import decodable_image_path

    try:
        with contextlib.ExitStack() as stack:
            readable = [stack.enter_context(decodable_image_path(f)) for f in files]
            scanlayer.convert_merge(
                readable,
                out_pdf,
                orientation=orientation,
                force=True,
                workers=OCR_MERGE_WORKERS,
            )
    except Exception as e:
        logger.warning("[OCR] Parallel merge failed, falling back to page-by-page: %s", e)
        with contextlib.suppress(OSError):
            os.remove(out_pdf)
        return False
    return True


def _merge_sequential(files: list[str], out_pdf: str, orientation) -> None:
    import fitz

    merged = fitz.open()
    temp_dir = tempfile.mkdtemp(prefix="fcp_ocr_merge_")
    try:
        for i, path in enumerate(files):
            page_pdf = os.path.join(temp_dir, f"page_{i}.pdf")
            if not image_ocr_able(path, page_pdf, orientation):
                embed_image_in_pdf(path, page_pdf)
            with fitz.open(page_pdf) as page:
                merged.insert_pdf(page)
        merged.save(out_pdf)
    finally:
        merged.close()
        shutil.rmtree(temp_dir, ignore_errors=True)
