"""
External Binaries Configuration - File Converter Pro

Centralized lookup for external tools (ffmpeg, Ghostscript, ImageMagick,
LibreOffice, wkhtmltopdf, pandoc, ...) via :func: resolve_binary.
All candidate paths live in :data:`TOOLS` - declare them nowhere else.

Lookup order: system PATH -> app-local dir -> common system dirs -> config file.

Config file: config/external_binaries.conf (INI), next to the exe when frozen,
or project root in dev. Override path with FCP_EXTERNAL_BINARIES_CONF.

    [binaries]
    ffmpeg = C:\\ffmpeg\\bin\\ffmpeg.exe
    ghostscript =

Values support %ENVVAR%/$ENVVAR expansion, "~", and relative paths (resolved
against the config/ folder's parent). Empty/missing config = auto-detect only.

TOOLS placeholders: {app_dir} (exe dir when frozen, else _MEIPASS/project root),
{app_data} (LOCALAPPDATA or ~/.file_converter_app), {meipass} (PyInstaller temp dir).
"""

from __future__ import annotations

import configparser
import glob
import os
import re
import shutil
import sys
from dataclasses import dataclass

from utils import SRC_DIR

CONFIG_FOLDER = "config"
CONFIG_FILE = "external_binaries.conf"

_cached_config = None  # None -> not parsed yet; {} -> parsed, no values
_cached_path = None


@dataclass(frozen=True)
class ToolSpec:
    """Lookup specification for one external tool.

    names      executable names tried on PATH, in order.
    app_local  path templates relative to app directories.
    system     absolute install-location patterns (glob patterns allowed).
    """

    names: tuple[str, ...]
    app_local: tuple[str, ...] = ()
    system: tuple[str, ...] = ()


TOOLS: dict[str, ToolSpec] = {
    "7z": ToolSpec(
        names=("7z", "7zz", "7za"),
        app_local=(
            "{app_data}/7zip/7z.exe",
            "{app_data}/7zip/7zz",
            "{app_dir}/7zip/7z.exe",
            "{app_dir}/7zip/7zz",
        ),
        system=(
            r"%PROGRAMFILES%\7-Zip\7z.exe",
            r"%PROGRAMFILES%\7-Zip\7zz.exe",
            r"C:\Program Files\7-Zip\7z.exe",
            r"C:\Program Files\7-Zip\7zz.exe",
            r"C:\Program Files (x86)\7-Zip\7z.exe",
            r"C:\Program Files (x86)\7-Zip\7zz.exe",
            "/usr/bin/7z",
            "/usr/bin/7zz",
            "/usr/bin/7za",
            "/usr/local/bin/7z",
            "/usr/local/bin/7zz",
            "/usr/local/bin/7za",
            "/opt/homebrew/bin/7z",
            "/opt/homebrew/bin/7zz",
            "/opt/homebrew/bin/7za",
            "/opt/local/bin/7z",
            "/opt/local/bin/7zz",
            "/opt/local/bin/7za",
            "/snap/bin/7z",
            "/snap/bin/7za",
        ),
    ),
    "ffmpeg": ToolSpec(
        names=("ffmpeg",),
        app_local=("{app_dir}/ffmpeg/ffmpeg.exe", "{meipass}/ffmpeg.exe"),
        system=(
            r"%LOCALAPPDATA%\ffmpeg\bin\ffmpeg.exe",
            r"%APPDATA%\ffmpeg\bin\ffmpeg.exe",
            r"C:\ffmpeg\bin\ffmpeg.exe",
            r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
            r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",
            "/usr/bin/ffmpeg",
            "/usr/local/bin/ffmpeg",
            "/opt/homebrew/bin/ffmpeg",
            "/opt/local/bin/ffmpeg",
            "/snap/bin/ffmpeg",
        ),
    ),
    "ffprobe": ToolSpec(
        names=("ffprobe",),
        app_local=("{app_dir}/ffmpeg/ffprobe.exe", "{meipass}/ffprobe.exe"),
        system=(
            r"%LOCALAPPDATA%\ffmpeg\bin\ffprobe.exe",
            r"%APPDATA%\ffmpeg\bin\ffprobe.exe",
            r"C:\ffmpeg\bin\ffprobe.exe",
            r"C:\Program Files\ffmpeg\bin\ffprobe.exe",
            r"C:\Program Files (x86)\ffmpeg\bin\ffprobe.exe",
            "/usr/bin/ffprobe",
            "/usr/local/bin/ffprobe",
            "/opt/homebrew/bin/ffprobe",
            "/opt/local/bin/ffprobe",
            "/snap/bin/ffprobe",
        ),
    ),
    "ghostscript": ToolSpec(
        names=("gs", "gswin64c", "gswin32c"),
        app_local=(
            "{app_data}/ghostscript/bin/gswin64c.exe",
            "{app_data}/ghostscript/bin/gswin32c.exe",
            "{app_data}/ghostscript/bin/gs",
        ),
        system=(
            r"C:\Program Files\gs\gs*\bin\gswin64c.exe",
            r"C:\Program Files (x86)\gs\gs*\bin\gswin32c.exe",
            "/usr/bin/gs",
            "/usr/bin/gsc",
            "/usr/local/bin/gs",
            "/opt/homebrew/bin/gs",
            "/opt/local/bin/gs",
            "/snap/bin/gs",
        ),
    ),
    "imagemagick": ToolSpec(
        names=("magick", "convert"),
        system=(
            r"%LOCALAPPDATA%\ImageMagick-*\magick.exe",
            r"%PROGRAMFILES%\ImageMagick-*\magick.exe",
            r"C:\Program Files\ImageMagick-*\magick.exe",
            r"C:\Program Files (x86)\ImageMagick-*\magick.exe",
            "/usr/bin/magick",
            "/usr/bin/convert",
            "/usr/local/bin/magick",
            "/usr/local/bin/convert",
            "/opt/homebrew/bin/magick",
            "/opt/homebrew/bin/convert",
            "/opt/local/bin/magick",
            "/opt/local/bin/convert",
            "/snap/bin/magick",
        ),
    ),
    "libreoffice": ToolSpec(
        names=("soffice", "libreoffice"),
        app_local=("{app_dir}/libreoffice/program/soffice.exe",),
        system=(
            r"%PROGRAMFILES%\LibreOffice\program\soffice.exe",
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
            r"C:\Program Files\The Document Foundation\LibreOffice\program\soffice.exe",
            "/usr/bin/soffice",
            "/usr/bin/libreoffice",
            "/usr/local/bin/soffice",
            "/usr/local/bin/libreoffice",
            "/opt/homebrew/bin/soffice",
            "/opt/homebrew/bin/libreoffice",
            "/opt/local/bin/soffice",
            "/Applications/LibreOffice.app/Contents/MacOS/soffice",
            "/Applications/LibreOffice.app/Contents/MacOS/soffice.bin",
        ),
    ),
    "wkhtmltopdf": ToolSpec(
        names=("wkhtmltopdf",),
        system=(
            r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe",
            r"C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe",
            "/usr/bin/wkhtmltopdf",
            "/usr/local/bin/wkhtmltopdf",
            "/opt/homebrew/bin/wkhtmltopdf",
            "/opt/local/bin/wkhtmltopdf",
            "/snap/bin/wkhtmltopdf",
        ),
    ),
    "pandoc": ToolSpec(
        names=("pandoc",),
        system=(
            r"%LOCALAPPDATA%\Pandoc\pandoc.exe",
            r"%PROGRAMFILES%\Pandoc\pandoc.exe",
            r"C:\Program Files\Pandoc\pandoc.exe",
            "/usr/bin/pandoc",
            "/usr/local/bin/pandoc",
            "/opt/homebrew/bin/pandoc",
            "/opt/local/bin/pandoc",
            "/snap/bin/pandoc",
        ),
    ),
    "tesseract": ToolSpec(
        names=("tesseract",),
        app_local=(
            "{app_dir}/tesseract/tesseract.exe",
            "{app_dir}/tesseract/bin/tesseract.exe",
            "{app_data}/tesseract/tesseract.exe",
            "{meipass}/tesseract.exe",
            "{meipass}/bin/tesseract.exe",
        ),
        system=(
            r"%LOCALAPPDATA%\Tesseract-OCR\tesseract.exe",
            r"%PROGRAMFILES%\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            "/usr/bin/tesseract",
            "/usr/local/bin/tesseract",
            "/opt/homebrew/bin/tesseract",
            "/opt/local/bin/tesseract",
            "/snap/bin/tesseract",
        ),
    ),
}


# Env vars that are defined on Windows but may be absent in some shells;
# used only to make %VAR% expansion deterministic.
_FALLBACK_ENV = {
    "PROGRAMFILES": r"C:\Program Files",
    "PROGRAMDATA": r"C:\ProgramData",
}


def _config_candidates() -> list[str]:
    """Ordered list of config file paths to try."""
    candidates = []
    override = os.environ.get("FCP_EXTERNAL_BINARIES_CONF")
    if override:
        # An explicit override is exclusive: only that file is considered,
        # so a stale fallback elsewhere can never shadow the user's choice.
        return [override]
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
        candidates.append(os.path.join(exe_dir, CONFIG_FOLDER, CONFIG_FILE))
        candidates.append(os.path.join(exe_dir, "_internal", CONFIG_FOLDER, CONFIG_FILE))
    candidates.append(os.path.join(str(SRC_DIR), CONFIG_FOLDER, CONFIG_FILE))
    candidates.append(os.path.join(os.getcwd(), CONFIG_FOLDER, CONFIG_FILE))
    return candidates


def get_config_path() -> str | None:
    """Absolute path of the config file, or None if it does not exist."""
    global _cached_path
    if _cached_path is not None:
        return _cached_path
    for candidate in _config_candidates():
        if os.path.isfile(candidate):
            _cached_path = candidate
            return _cached_path
    _cached_path = None
    return None


def get_config_folder() -> str | None:
    """Absolute path of the config/ folder, or None if no config file exists."""
    path = get_config_path()
    return os.path.dirname(path) if path else None


def load_config() -> dict:
    """Parse config/external_binaries.conf (INI) once and return [binaries].

    Only keys with a non-empty value are kept, lowercased.  Returns an empty
    dict when the file is missing, unreadable, or has no values set.
    """
    global _cached_config
    if _cached_config is not None:
        return _cached_config

    _cached_config = {}
    path = get_config_path()
    if not path:
        return _cached_config

    parser = configparser.ConfigParser(interpolation=None)
    try:
        parser.read(path, encoding="utf-8")
        if parser.has_section("binaries"):
            for key, value in parser.items("binaries"):
                value = (value or "").strip()
                if value:
                    _cached_config[key.strip().lower()] = value
    except Exception as exc:
        # A malformed config file must never crash a conversion — fall back
        # to automatic detection for every binary instead.
        print(f"[external_binaries] Could not parse config file {path}: {exc}")
        _cached_config = {}
    return _cached_config


def get_configured_binary(name: str) -> str | None:
    """Return the absolute path declared in the config file for *name*.

    Returns None when:
      - the config file is missing,
      - the key is absent or empty,
      - the declared path does not exist on disk.

    %ENVVAR% / $ENVVAR and "~" are expanded first.  Relative values are
    resolved against the application folder (the folder that contains the
    config/ directory).  Callers should only treat the result as usable when
    it is not None.
    """
    raw = load_config().get(str(name).strip().lower())
    if not raw:
        return None

    expanded = _expand_percent_vars(os.path.expandvars(os.path.expanduser(raw)))
    if not os.path.isabs(expanded):
        folder = get_config_folder()
        if folder:
            app_root = os.path.dirname(folder)
            expanded = os.path.normpath(os.path.join(app_root, expanded))

    if not os.path.isfile(expanded):
        print(
            f"[external_binaries] '{name}' is declared in {get_config_path()} but the file does not exist: {expanded}"
        )
        return None
    return expanded


def get_app_dir() -> str:
    """Application base directory (frozen: exe folder; dev: project root)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    try:
        return str(sys._MEIPASS)
    except AttributeError:
        return str(SRC_DIR)


def get_app_data_dir() -> str:
    """Default per-user app-data directory used for app-local binaries."""
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return os.path.join(base, ".file_converter_app")


def _expand_percent_vars(value: str) -> str:
    """Expand %VAR% using os.environ, with fallbacks for common Windows vars."""

    def _repl(match: "re.Match[str]") -> str:
        name = match.group(1)
        return os.environ.get(name) or _FALLBACK_ENV.get(name, match.group(0))

    return re.sub(r"%([^%]+)%", _repl, value)


def _expand_template(template: str, app_data: str | None) -> str:
    """Expand {app_dir}/{app_data}/{meipass} placeholders and env vars."""
    app_data = app_data or get_app_data_dir()
    value = template.replace("{app_dir}", get_app_dir())
    value = value.replace("{app_data}", app_data)
    value = value.replace("{meipass}", str(getattr(sys, "_MEIPASS", "")) or get_app_dir())
    value = os.path.expanduser(value)
    value = _expand_percent_vars(value)
    return os.path.normpath(value)


def locate_binary(name: str, app_data_dir: str | None = None) -> tuple[str | None, str | None]:
    """Resolve *name* and report both the path and where it was found.

    Returns ``(path, source)`` where *source* is one of:
      "system PATH", "app-local", "common dirs", "config file", or None.

    Lookup order: PATH → app-local → common system dirs → config file.
    """
    spec = TOOLS.get(str(name).strip().lower())
    if spec is None:
        configured = get_configured_binary(name)
        return configured, ("config file" if configured else None)

    for exe_name in spec.names:
        found = shutil.which(exe_name)
        if found:
            return found, "system PATH"

    for template in spec.app_local:
        candidate = _expand_template(template, app_data_dir)
        if os.path.isfile(candidate):
            return candidate, "app-local"

    for template in spec.system:
        expanded = _expand_template(template, app_data_dir)
        for match in glob.glob(expanded):
            if os.path.isfile(match):
                return match, "common dirs"

    configured = get_configured_binary(name)
    return configured, ("config file" if configured else None)


def resolve_binary(name: str, app_data_dir: str | None = None) -> str | None:
    """Single lookup entry point for an external tool.

    Enforced order: system PATH → app-local directory → common system dirs →
    config file.  Returns an absolute path, or None if the tool is not
    installed anywhere findable.  *app_data_dir* overrides the default app
    data location used for the app-local lookup (rarely needed).
    """
    path, _ = locate_binary(name, app_data_dir=app_data_dir)
    return path


def _reset_cache() -> None:
    """Forget cached config/path.  Internal helper (used by tests)."""
    global _cached_config, _cached_path
    _cached_config = None
    _cached_path = None


__all__ = [
    "CONFIG_FOLDER",
    "CONFIG_FILE",
    "TOOLS",
    "ToolSpec",
    "get_config_path",
    "get_config_folder",
    "load_config",
    "get_configured_binary",
    "get_app_dir",
    "get_app_data_dir",
    "locate_binary",
    "resolve_binary",
]
