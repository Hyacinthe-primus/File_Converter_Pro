"""Helpers for images whose real format differs from (or isn't handled by) their file extension.

Phones often save HEIC photos with a .png/.jpg name, and PyMuPDF / the OCR
engine cannot decode HEIC/AVIF at all. These helpers detect the real format
from the file content and, when needed, hand decoders a temporary PNG.
"""

from __future__ import annotations

import contextlib
import os
import tempfile
from collections.abc import Iterator
from pathlib import Path

HEIF_BRANDS = (b"heic", b"heix", b"hevc", b"hevx", b"heim", b"heis", b"hevm", b"hevs", b"mif1", b"msf1")
AVIF_BRANDS = (b"avif", b"avis")
_CONVERT_EXTS = (".heic", ".heif", ".avif")


def sniff_image_ext(path: str, fallback_ext: str = "") -> str:
    """Return ".heic" / ".avif" when the file content says so, else ``fallback_ext``."""
    try:
        with open(path, "rb") as f:
            head = f.read(16)
    except OSError:
        return fallback_ext
    if head[4:8] == b"ftyp":
        brand = head[8:12]
        if brand in HEIF_BRANDS:
            return ".heic"
        if brand in AVIF_BRANDS:
            return ".avif"
    return fallback_ext


def register_heif() -> None:
    """Teach Pillow to open HEIC/HEIF (no-op if pillow-heif is unavailable)."""
    try:
        from pillow_heif import register_heif_opener

        register_heif_opener()
    except Exception:
        pass


@contextlib.contextmanager
def decodable_image_path(path: str) -> Iterator[str]:
    """Yield a path that PyMuPDF, Pillow and the OCR engine can all read.

    Regular images are passed through untouched. HEIC/HEIF/AVIF files (by
    content or by extension, so misnamed ones too) are converted to a temporary
    PNG that is deleted when the block exits. If the conversion fails the
    original path is yielded, so the caller reports its usual error.
    """
    ext = sniff_image_ext(path, Path(path).suffix.lower())
    if ext not in _CONVERT_EXTS:
        yield path
        return

    tmp_path = None
    try:
        from PIL import Image, ImageOps

        register_heif()
        with Image.open(path) as img:
            img = ImageOps.exif_transpose(img)
            has_alpha = "A" in img.getbands() or "transparency" in img.info
            img = img.convert("RGBA" if has_alpha else "RGB")
            fd, tmp_path = tempfile.mkstemp(prefix="fcp_img_", suffix=".png")
            os.close(fd)
            img.save(tmp_path, format="PNG")
    except Exception as e:
        print(f"[IMAGE] Could not convert {path} to a readable format: {e}")
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
        tmp_path = None

    try:
        yield tmp_path or path
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
