"""Shared conversion helpers: result object, path building, encoding utilities."""

from __future__ import annotations

import base64
import os
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


def _create_backup_exclusive(src: str, suffix: str) -> str | None:
    import shutil

    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    counter = 0
    while True:
        backup_path = f"{src}{suffix}" if counter == 0 else f"{src}{suffix}.{counter}"
        try:
            fd = os.open(backup_path, flags, 0o600)
        except FileExistsError:
            counter += 1
            continue
        except OSError as e:
            print(f"[BACKUP] Could not create backup for {src}: {e}")
            return None
        break

    try:
        with open(src, "rb") as src_file:
            with os.fdopen(fd, "wb") as dst_file:
                fd = -1
                shutil.copyfileobj(src_file, dst_file)
        shutil.copystat(src, backup_path)
        return backup_path
    except Exception as e:
        if fd >= 0:
            try:
                os.close(fd)
            except OSError:
                pass
        try:
            os.unlink(backup_path)
        except OSError:
            pass
        print(f"[BACKUP] Could not create backup for {src}: {e}")
        return None


def create_backup(src: str, suffix: str = ".bak", overwrite: bool = True) -> str | None:
    """
    Create a backup copy of *src* with the given suffix appended.
    Returns the backup path, or None if the source doesn't exist or copy fails.
    Cross-platform: uses shutil.copy2 for overwrite=True and an exclusive
    create/copy/copystat path for overwrite=False.
    """
    import shutil

    if not os.path.isfile(src):
        return None
    if not overwrite:
        return _create_backup_exclusive(src, suffix)
    backup_path = f"{src}{suffix}"
    try:
        shutil.copy2(src, backup_path)
        return backup_path
    except Exception as e:
        print(f"[BACKUP] Could not create backup for {src}: {e}")
        return None
