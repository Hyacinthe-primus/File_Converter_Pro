"""Structural output validation for AdvancedConverterEngine artifacts.

The shared PDF/DOCX validators are reused directly. Formats without an
existing structural validator use a conservative signature or parser check;
those limits are documented beside the relevant helper.
"""

from __future__ import annotations

import csv
import json
import os
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree

from utils.image_formats import AVIF_BRANDS, HEIF_BRANDS
from utils.pdf_artifacts import validate_docx_artifact, validate_pdf_artifact

_IMAGE_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "gif",
    "bmp",
    "tiff",
    "tif",
    "webp",
    "heic",
    "heif",
    "avif",
    "j2k",
    "jp2",
    "dng",
    "psd",
    "svg",
    "ico",
}
_MEDIA_EXTENSIONS = {
    "mp4",
    "webm",
    "mkv",
    "mov",
    "avi",
    "mp3",
    "wav",
    "aac",
    "ogg",
    "flac",
    "m4a",
}
_PIL_VERIFY_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp", "tiff", "tif", "webp", "ico"}


def _read_head(path: str, size: int = 16) -> bytes:
    with open(path, "rb") as handle:
        return handle.read(size)


def _validate_nonempty(path: str) -> tuple[bool, str]:
    """Minimum check for formats without a reliable structural validator."""
    try:
        if not os.path.isfile(path) or os.path.getsize(path) <= 0:
            return False, "produced no output"
    except OSError as exc:
        return False, f"unreadable output: {exc}"
    return True, ""


def _validate_pdf(path: str) -> tuple[bool, str]:
    valid, reason = _validate_nonempty(path)
    if not valid:
        return False, reason
    return validate_pdf_artifact(path)


def _validate_docx(path: str) -> tuple[bool, str]:
    valid, reason = _validate_nonempty(path)
    if not valid:
        return False, reason
    return validate_docx_artifact(path)


def _validate_json(path: str) -> tuple[bool, str]:
    valid, reason = _validate_nonempty(path)
    if not valid:
        return False, reason
    try:
        with open(path, "r", encoding="utf-8") as handle:
            json.load(handle)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return False, f"invalid JSON: {exc}"
    return True, ""


def _validate_csv(path: str) -> tuple[bool, str]:
    valid, reason = _validate_nonempty(path)
    if not valid:
        return False, reason
    try:
        with open(path, "r", encoding="utf-8", newline="") as handle:
            if next(csv.reader(handle), None) is None:
                return False, "empty output"
    except (OSError, UnicodeDecodeError, csv.Error) as exc:
        return False, f"invalid CSV: {exc}"
    return True, ""


def _validate_html(path: str) -> tuple[bool, str]:
    """Minimum HTML check: UTF-8 text containing markup that the stdlib parser accepts."""
    valid, reason = _validate_nonempty(path)
    if not valid:
        return False, reason
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return False, f"invalid HTML: {exc}"
    if not text.strip():
        return False, "empty output"
    if "<" not in text or ">" not in text:
        return False, "not HTML"
    try:
        parser = HTMLParser()
        parser.feed(text)
        parser.close()
    except Exception as exc:
        return False, f"invalid HTML: {exc}"
    return True, ""


def _validate_ooxml(path: str, required: tuple[str, ...], label: str) -> tuple[bool, str]:
    valid, reason = _validate_nonempty(path)
    if not valid:
        return False, reason
    try:
        with zipfile.ZipFile(path) as archive:
            corrupt_entry = archive.testzip()
            if corrupt_entry is not None:
                return False, f"invalid {label}: corrupt entry {corrupt_entry}"
            names = set(archive.namelist())
            for name in required:
                if name not in names:
                    return False, f"invalid {label}: missing {name}"
                data = archive.read(name)
                if not data.strip():
                    return False, f"invalid {label}: empty {name}"
                if name.endswith((".xml", ".rels")):
                    ElementTree.fromstring(data)
    except zipfile.BadZipFile:
        return False, f"not a {label}"
    except (KeyError, OSError) as exc:
        return False, f"invalid {label}: {exc}"
    except ElementTree.ParseError as exc:
        return False, f"invalid {label}: malformed XML: {exc}"
    except Exception as exc:
        return False, f"invalid {label}: {exc}"
    return True, ""


def _validate_xlsx(path: str) -> tuple[bool, str]:
    return _validate_ooxml(
        path,
        ("[Content_Types].xml", "xl/workbook.xml", "_rels/.rels"),
        "XLSX",
    )


def _validate_pptx(path: str) -> tuple[bool, str]:
    return _validate_ooxml(
        path,
        ("[Content_Types].xml", "ppt/presentation.xml", "_rels/.rels"),
        "PPTX",
    )


def _validate_image(path: str, extension: str) -> tuple[bool, str]:
    valid, reason = _validate_nonempty(path)
    if not valid:
        return False, reason

    label = extension.upper()
    try:
        head = _read_head(path)
    except OSError as exc:
        return False, f"unreadable {label}: {exc}"

    ext = extension.lower()
    header_ok = False
    if ext == "png":
        header_ok = head.startswith(b"\x89PNG\r\n\x1a\n")
    elif ext in {"jpg", "jpeg"}:
        header_ok = head.startswith(b"\xff\xd8\xff")
    elif ext == "gif":
        header_ok = head.startswith((b"GIF87a", b"GIF89a"))
    elif ext == "bmp":
        header_ok = head.startswith(b"BM")
    elif ext in {"tiff", "tif", "dng"}:
        header_ok = head[:4] in (b"II*\x00", b"MM\x00*")
    elif ext == "webp":
        header_ok = head[:4] == b"RIFF" and head[8:12] == b"WEBP"
    elif ext == "ico":
        header_ok = head.startswith(b"\x00\x00\x01\x00")
    elif ext == "psd":
        header_ok = head.startswith(b"8BPS")
    elif ext == "heic" or ext == "heif":
        header_ok = head[4:8] == b"ftyp" and head[8:12] in HEIF_BRANDS
    elif ext == "avif":
        header_ok = head[4:8] == b"ftyp" and head[8:12] in AVIF_BRANDS
    elif ext in {"j2k", "jp2"}:
        header_ok = head.startswith(b"\xff\x4f\xff\x51") or head.startswith(
            b"\x00\x00\x00\x0cjP  \r\n\x87\n"
        )
    elif ext == "svg":
        try:
            root = ElementTree.parse(path).getroot()
        except (OSError, ElementTree.ParseError) as exc:
            return False, f"invalid SVG: {exc}"
        if root.tag.rsplit("}", 1)[-1].lower() != "svg":
            return False, "not an SVG"
        header_ok = True

    if not header_ok:
        return False, f"not a {label}"

    # Pillow provides structural verification for the mainstream raster formats.
    # HEIC/AVIF/J2K/DNG/PSD/SVG deliberately use the checks above because the
    # decoder plugins are optional or do not validate the container reliably.
    if ext not in _PIL_VERIFY_EXTENSIONS:
        return True, ""
    try:
        from PIL import Image
    except Exception:
        return True, ""
    try:
        with Image.open(path) as image:
            image.verify()
    except Exception as exc:
        return False, f"invalid {label}: {exc}"
    return True, ""


def _validate_media(path: str, extension: str) -> tuple[bool, str]:
    """Minimum container check for audio/video outputs.

    Full decoding is intentionally left to ffmpeg itself; these checks catch
    empty, truncated-to-header, or clearly wrong-container outputs without
    requiring ffprobe as an additional dependency.
    """
    valid, reason = _validate_nonempty(path)
    if not valid:
        return False, reason

    label = extension.upper()
    try:
        head = _read_head(path)
    except OSError as exc:
        return False, f"unreadable {label}: {exc}"

    ext = extension.lower()
    ok = False
    if ext in {"mp4", "m4a"}:
        ok = head[4:8] == b"ftyp"
    elif ext == "mov":
        ok = head[4:8] in {b"ftyp", b"moov", b"mdat", b"free", b"wide", b"skip"}
    elif ext in {"webm", "mkv"}:
        ok = head.startswith(b"\x1aE\xdf\xa3")
    elif ext == "avi":
        ok = head[:4] == b"RIFF" and head[8:12] == b"AVI "
    elif ext == "wav":
        ok = head[:4] == b"RIFF" and head[8:12] == b"WAVE"
    elif ext == "mp3":
        ok = head.startswith(b"ID3") or (len(head) >= 2 and head[0] == 0xFF and head[1] & 0xE0 == 0xE0)
    elif ext == "aac":
        ok = len(head) >= 2 and head[0] == 0xFF and head[1] & 0xF0 == 0xF0
    elif ext == "flac":
        ok = head.startswith(b"fLaC")
    elif ext == "ogg":
        ok = head.startswith(b"OggS")

    if not ok:
        return False, f"not a {label}"
    return True, ""


def validator_for_extension(extension: str):
    """Return a validator accepting one output path for *extension*."""
    ext = extension.lower().lstrip(".")
    if ext == "pdf":
        return _validate_pdf
    if ext == "docx":
        return _validate_docx
    if ext == "json":
        return _validate_json
    if ext == "csv":
        return _validate_csv
    if ext == "html":
        return _validate_html
    if ext == "xlsx":
        return _validate_xlsx
    if ext == "pptx":
        return _validate_pptx
    if ext in _IMAGE_EXTENSIONS:
        return lambda path: _validate_image(path, ext)
    if ext in _MEDIA_EXTENSIONS:
        return lambda path: _validate_media(path, ext)
    return _validate_nonempty
