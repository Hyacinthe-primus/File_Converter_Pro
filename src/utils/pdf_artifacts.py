"""PDF and DOCX artifact validation plus the PDF compatibility wrapper."""

from __future__ import annotations

import os
import threading
import zipfile
from collections.abc import Callable
from xml.etree import ElementTree

from utils.conversion_pipeline import run_conversion_pipeline

_PDF_HEADER = b"%PDF-"
_HEADER_SCAN_BYTES = 1024
_PDF_VALIDATION_LOCK = threading.Lock()

_PDF_PARSE_ERROR_MARKERS = (
    "syntax error",
    "format error",
    "cannot load",
    "object out of range",
    "non-page object",
    "page tree",
    "page may not be correct",
    "unexpected end",
)


def validate_pdf_artifact(path: str) -> tuple[bool, str]:
    """Return whether *path* is a structurally readable PDF and a failure reason."""
    try:
        size = os.path.getsize(path)
    except FileNotFoundError:
        return False, "missing output"
    except OSError as exc:
        return False, f"unreadable output: {exc}"

    if size <= 0:
        return False, "empty output"

    try:
        with open(path, "rb") as handle:
            header = handle.read(_HEADER_SCAN_BYTES)
    except OSError as exc:
        return False, f"unreadable output: {exc}"

    if _PDF_HEADER not in header:
        return False, "not a PDF"

    try:
        import fitz
    except Exception as exc:
        return False, f"invalid PDF: cannot load PDF validator: {exc}"

    failure = ""
    warnings = ""
    with _PDF_VALIDATION_LOCK:
        fitz.TOOLS.mupdf_warnings()
        try:
            with fitz.open(path) as document:
                if document.page_count <= 0:
                    failure = "PDF has no pages"
                elif getattr(document, "is_repaired", False):
                    failure = "PDF required repair"
                else:
                    xref_count = document.xref_length()
                    for page_index in range(document.page_count):
                        try:
                            page = document.load_page(page_index)
                            for xref in page.get_contents():
                                if xref <= 0 or xref >= xref_count or not document.xref_is_stream(xref):
                                    failure = (
                                        f"invalid PDF: page {page_index + 1} has an invalid content stream"
                                    )
                                    break
                                document.xref_stream(xref)
                            if failure:
                                break
                            page.get_text("text")
                            page.get_pixmap(matrix=fitz.Matrix(0.1, 0.1), alpha=False)
                        except Exception as exc:
                            failure = f"invalid PDF: page {page_index + 1}: {exc}"
                            break
        except Exception as exc:
            failure = f"invalid PDF: {exc}"
        finally:
            warnings = fitz.TOOLS.mupdf_warnings() or ""

    if failure:
        return False, failure
    for warning in warnings.splitlines():
        lowered = warning.lower()
        if any(marker in lowered for marker in _PDF_PARSE_ERROR_MARKERS):
            return False, f"invalid PDF: {warning.strip()}"

    return True, ""


def validate_docx_artifact(path: str) -> tuple[bool, str]:
    """Return whether *path* is a readable, structurally valid DOCX."""
    try:
        size = os.path.getsize(path)
    except FileNotFoundError:
        return False, "missing output"
    except OSError as exc:
        return False, f"unreadable output: {exc}"

    if size <= 0:
        return False, "empty output"

    try:
        with zipfile.ZipFile(path) as archive:
            corrupt_entry = archive.testzip()
            if corrupt_entry is not None:
                return False, f"invalid DOCX: corrupt entry {corrupt_entry}"
            names = set(archive.namelist())
            required = ("[Content_Types].xml", "word/document.xml", "_rels/.rels")
            for name in required:
                if name not in names:
                    return False, f"invalid DOCX: missing {name}"
                data = archive.read(name)
                if not data.strip():
                    return False, f"invalid DOCX: empty {name}"
                if name.endswith(".xml"):
                    ElementTree.fromstring(data)
    except zipfile.BadZipFile:
        return False, "not a DOCX"
    except (KeyError, OSError) as exc:
        return False, f"invalid DOCX: {exc}"
    except ElementTree.ParseError as exc:
        return False, f"invalid DOCX: malformed XML: {exc}"
    except Exception as exc:
        return False, f"invalid DOCX: {exc}"

    return True, ""


def validate_docx_input(path: str) -> tuple[bool, str]:
    """Validate a Word input before conversion.

    Legacy ``.doc`` files are not OOXML packages, so only existence and
    non-empty content are checked for that format. ``.docx`` inputs receive
    the same structural validation used for generated DOCX artifacts.
    """
    try:
        size = os.path.getsize(path)
    except FileNotFoundError:
        return False, "missing input"
    except OSError as exc:
        return False, f"unreadable input: {exc}"

    if not os.path.isfile(path):
        return False, "input is not a file"
    if size <= 0:
        return False, "empty input"

    if path.lower().endswith(".docx"):
        valid, reason = validate_docx_artifact(path)
        if not valid:
            return False, reason
    return True, ""


def run_pdf_engine_with_artifact_validation(
    destination: str,
    engine: Callable[[str], object],
) -> tuple[bool, str]:
    """Run one PDF engine through the shared staged pipeline."""
    result = run_conversion_pipeline(
        destination,
        [("engine", engine)],
        validate_pdf_artifact,
        stage_dir_prefix="~fcp_pdf_stage_",
        staged_prefix="~fcp_pdf_",
        staged_suffix=".pdf",
        include_engine_labels=False,
    )
    return result.success, result.error
