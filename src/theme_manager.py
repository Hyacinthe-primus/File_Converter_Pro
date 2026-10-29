"""ThemeManager — Handle custom .fctheme files (ZIP format)."""

import configparser
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from utils import SRC_DIR

ROOT_DIR = SRC_DIR
THEMES_DIR = ROOT_DIR / "styles" / "themes"
CUSTOM_THEMES_DIR = ROOT_DIR / "styles" / "custom_themes"

REQUIRED_FILES = {
    "style.qss",
    "advanced_conversions.qss",
    "advanced_group.qss",
    "contact_links.css",
    "dashboard.qss",
    "lang_scroll.qss",
    "scrollbar.qss",
    "settings.qss",
    "templates.qss",
    "terms_html.css",
    "terms.qss",
}

METADATA_FILE = "metadata.ini"


class ThemeMessage(str):
    """English fallback message that also carries a translation key and its format args.

    Behaves like a plain ``str`` for existing callers; the UI can call
    ``translate_text(msg.key).format(*msg.args)`` to display it in the user's language.
    """

    key: str
    args: tuple

    def __new__(cls, key: str, fallback: str, *args):
        obj = super().__new__(cls, fallback.format(*args))
        obj.key = key
        obj.args = args
        return obj


@dataclass
class ThemeMetadata:
    name: str
    author: str
    version: str
    description: str
    preview: str
    folder_name: str
    kind: str = "light"
    dashboard: dict[str, str] = field(default_factory=dict)


def _ensure_custom_dir():
    CUSTOM_THEMES_DIR.mkdir(parents=True, exist_ok=True)


def get_builtin_themes() -> list[str]:
    themes = []
    for d in THEMES_DIR.iterdir():
        if d.is_dir() and (d / "style.qss").exists():
            themes.append(d.name)
    return sorted(themes)


def get_custom_themes() -> list[ThemeMetadata]:
    _ensure_custom_dir()
    themes = []
    for d in CUSTOM_THEMES_DIR.iterdir():
        if not d.is_dir():
            continue
        meta = _read_metadata(d)
        if meta:
            themes.append(meta)
    return sorted(themes, key=lambda t: t.name.lower())


def get_custom_theme_kind(folder_name: str) -> str:
    theme_dir = CUSTOM_THEMES_DIR / folder_name
    if not theme_dir.is_dir():
        return "light"
    meta = _read_metadata(theme_dir)
    return meta.kind if meta else "light"


def get_dashboard_overrides(folder_name: str) -> dict[str, str]:
    theme_dir = CUSTOM_THEMES_DIR / folder_name
    if not theme_dir.is_dir():
        return {}
    meta = _read_metadata(theme_dir)
    return dict(meta.dashboard) if meta else {}


def import_theme(zip_path: str) -> tuple[bool, str]:
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()

            qss_in_zip = [n for n in names if Path(n).name in REQUIRED_FILES]

            qss_dirs = {}
            for n in qss_in_zip:
                parts = n.split("/")
                if len(parts) >= 2:
                    d = parts[0]
                    qss_dirs.setdefault(d, []).append(n)

            if qss_dirs:
                theme_dir_name = next(iter(qss_dirs))
                inner_prefix = theme_dir_name + "/"
                inner_names = [
                    n[len(inner_prefix) :] for n in names if n.startswith(inner_prefix) and n != inner_prefix
                ]
            else:
                theme_dir_name = ""
                inner_prefix = ""
                inner_names = [n for n in names if not n.endswith("/")]

            meta_name = None
            meta_prefix = inner_prefix
            for n in inner_names:
                if n == METADATA_FILE:
                    meta_name = n
                    break

            if not meta_name:
                for n in names:
                    if n == METADATA_FILE:
                        meta_name = n
                        meta_prefix = ""
                        break

            if not meta_name:
                return False, ThemeMessage("theme_err_metadata_missing", "Metadata file missing in the theme.")

            meta_content = zf.read(meta_prefix + meta_name).decode("utf-8")
            meta = _parse_metadata_content(meta_content)
            if not meta:
                return False, ThemeMessage("theme_err_metadata_unreadable", "Unable to read metadata.ini.")

            folder_name = _sanitize_folder_name(meta.name)
            theme_dir = CUSTOM_THEMES_DIR / folder_name

            existing = get_custom_themes()
            for t in existing:
                if t.name.lower() == meta.name.lower():
                    return False, ThemeMessage("theme_already_installed", "Theme '{}' is already installed.", meta.name)
                if t.folder_name == folder_name:
                    return False, ThemeMessage("theme_folder_exists", "Theme folder '{}' already exists.", folder_name)

            theme_dir.mkdir(parents=True)

            qss_files_found = set()

            dest = theme_dir / METADATA_FILE
            with open(dest, "w", encoding="utf-8") as dst:
                dst.write(meta_content)

            for n in inner_names:
                if n.endswith("/"):
                    continue

                basename = Path(n).name

                if basename.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                    full_path = inner_prefix + n
                    dest = theme_dir / basename
                    with zf.open(full_path) as src, open(dest, "wb") as dst:
                        dst.write(src.read())
                    continue

                if basename in REQUIRED_FILES:
                    qss_files_found.add(basename)

                full_path = inner_prefix + n
                dest = theme_dir / basename
                with zf.open(full_path) as src, open(dest, "wb") as dst:
                    dst.write(src.read())

            for n in names:
                basename = Path(n).name
                if basename.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                    if n.startswith(inner_prefix) and inner_prefix:
                        continue
                    full_path = n
                    dest = theme_dir / basename
                    with zf.open(full_path) as src, open(dest, "wb") as dst:
                        dst.write(src.read())

            missing = REQUIRED_FILES - qss_files_found
            if missing:
                import shutil

                shutil.rmtree(theme_dir)
                return False, ThemeMessage("theme_err_missing_files", "Missing files: {}", ", ".join(sorted(missing)))

            return True, meta.name

    except zipfile.BadZipFile:
        return False, ThemeMessage("theme_err_invalid_zip", "The file is not a valid ZIP archive.")
    except Exception as e:
        return False, ThemeMessage("theme_err_import_failed", "Error during import: {}", str(e))


def remove_theme(folder_name: str) -> tuple[bool, str]:
    theme_dir = CUSTOM_THEMES_DIR / folder_name
    if not theme_dir.exists():
        return False, ThemeMessage("theme_err_not_found", "Theme not found.")
    import shutil

    shutil.rmtree(theme_dir)
    return True, folder_name


def _read_metadata(theme_dir: Path) -> ThemeMetadata | None:
    for f in theme_dir.iterdir():
        if f.suffix == ".ini" and f.name.startswith("metadata"):
            try:
                content = f.read_text(encoding="utf-8")
                return _parse_metadata_content(content, theme_dir.name)
            except Exception:
                return None
    return None


def _parse_metadata_content(content: str, folder_name: str = "") -> ThemeMetadata | None:
    cp = configparser.ConfigParser()
    cp.read_string(content)
    if not cp.has_section("theme"):
        return None
    kind = cp.get("theme", "kind", fallback="light").lower()
    if kind not in ("light", "dark"):
        kind = "light"
    dashboard = {}
    if cp.has_section("dashboard"):
        dashboard = {key.strip().lower(): value.strip() for key, value in cp.items("dashboard")}
    return ThemeMetadata(
        name=cp.get("theme", "name", fallback="Unknown Theme"),
        author=cp.get("theme", "author", fallback=""),
        version=cp.get("theme", "version", fallback="1.0"),
        description=cp.get("theme", "description", fallback=""),
        preview=cp.get("theme", "preview", fallback=""),
        folder_name=folder_name,
        kind=kind,
        dashboard=dashboard,
    )


def _sanitize_folder_name(name: str) -> str:
    import re

    s = re.sub(r"[^\w\s-]", "", name)
    s = re.sub(r"\s+", "_", s.strip())
    return s[:50] or "custom_theme"


