"""Shared conversion helpers: result object, path building, encoding utilities."""

from __future__ import annotations

import base64
import os
import time
from pathlib import Path


class ConversionResult:
    __slots__ = ("success", "source", "target", "elapsed", "error", "file_size", "engine_used", "degraded")

    def __init__(self, success, source, target, elapsed=0.0, error="", file_size=0, engine_used="", degraded=False):
        self.success = success
        self.source = source
        self.target = target
        self.elapsed = elapsed
        self.error = error
        self.file_size = file_size
        self.engine_used = engine_used
        self.degraded = degraded

    def __repr__(self):
        s = "OK" if self.success else f"ERR({self.error})"
        engine = f" [{self.engine_used}]" if self.engine_used else ""
        return f"<ConversionResult {s}{engine} {self.source!r}→{self.target!r}>"


def _timed(fn):
    t0 = time.perf_counter()
    fn()
    return time.perf_counter() - t0


def _build_dst(src, dst_dir, new_ext):
    return str(Path(dst_dir) / f"{Path(src).stem}.{new_ext.lstrip('.')}")


def _img_to_b64(data, mime="image/png"):
    return f"data:{mime};base64,{base64.b64encode(data).decode()}"


def _mime_for_ext(ext):
    return {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "gif": "image/gif",
        "webp": "image/webp",
        "svg": "image/svg+xml",
        "bmp": "image/bmp",
        "tiff": "image/tiff",
    }.get(ext.lower(), "image/png")


def _safe_html(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _read_file_b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def create_backup(src: str, suffix: str = ".bak") -> str | None:
    """
    Create a backup copy of *src* with the given suffix appended.
    Returns the backup path, or None if the source doesn't exist or copy fails.
    Cross-platform: uses shutil.copy2 which preserves metadata on all OSes.
    """
    import shutil

    if not os.path.isfile(src):
        return None
    backup_path = f"{src}{suffix}"
    try:
        shutil.copy2(src, backup_path)
        return backup_path
    except Exception as e:
        print(f"[BACKUP] Could not create backup for {src}: {e}")
        return None
