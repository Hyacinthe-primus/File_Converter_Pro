"""ThemeManager — Handle custom .fctheme files (ZIP format)."""

import zipfile
import configparser
from dataclasses import dataclass
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
THEMES_DIR = ROOT_DIR / "styles" / "themes"
CUSTOM_THEMES_DIR = ROOT_DIR / "styles" / "custom_themes"

REQUIRED_FILES = {
    "style.qss", "advanced_conversions.qss", "advanced_group.qss",
    "contact_links.css", "dashboard.qss", "lang_scroll.qss",
    "scrollbar.qss", "templates.qss", "terms_html.css", "terms.qss",
}

METADATA_FILE = "metadata.ini"


@dataclass
class ThemeMetadata:
    name: str
    author: str
    version: str
    description: str
    preview: str
    folder_name: str
    kind: str = "light"


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


def get_all_theme_names() -> list[str]:
    return get_builtin_themes() + [t.folder_name for t in get_custom_themes()]


def get_custom_theme_kind(folder_name: str) -> str:
    theme_dir = CUSTOM_THEMES_DIR / folder_name
    if not theme_dir.is_dir():
        return "light"
    meta = _read_metadata(theme_dir)
    return meta.kind if meta else "light"


def get_theme_path(theme_name: str) -> Path | None:
    builtin = THEMES_DIR / theme_name
    if builtin.is_dir() and (builtin / "style.qss").exists():
        return builtin
    custom = CUSTOM_THEMES_DIR / theme_name
    if custom.is_dir() and (custom / "style.qss").exists():
        return custom
    return None


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
                inner_names = [n[len(inner_prefix):] for n in names if n.startswith(inner_prefix) and n != inner_prefix]
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
                return False, "Fichier metadata.ini manquant dans le thème."

            meta_content = zf.read(meta_prefix + meta_name).decode("utf-8")
            meta = _parse_metadata_content(meta_content)
            if not meta:
                return False, "Impossible de lire metadata.ini."

            folder_name = _sanitize_folder_name(meta.name)
            theme_dir = CUSTOM_THEMES_DIR / folder_name

            if theme_dir.exists():
                import shutil
                counter = 2
                while (CUSTOM_THEMES_DIR / f"{folder_name}_{counter}").exists():
                    counter += 1
                folder_name = f"{folder_name}_{counter}"
                theme_dir = CUSTOM_THEMES_DIR / folder_name

            theme_dir.mkdir(parents=True)

            qss_files_found = set()

            dest = theme_dir / METADATA_FILE
            with open(dest, "w", encoding="utf-8") as dst:
                dst.write(meta_content)

            for n in inner_names:
                if n.endswith("/"):
                    continue

                basename = Path(n).name

                if basename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
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
                if basename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
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
                return False, f"Fichiers manquants : {', '.join(sorted(missing))}"

            return True, meta.name

    except zipfile.BadZipFile:
        return False, "Le fichier n'est pas un ZIP valide."
    except Exception as e:
        return False, f"Erreur lors de l'import : {e}"


def remove_theme(folder_name: str) -> tuple[bool, str]:
    theme_dir = CUSTOM_THEMES_DIR / folder_name
    if not theme_dir.exists():
        return False, "Thème introuvable."
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
    return ThemeMetadata(
        name=cp.get("theme", "name", fallback="Thème inconnu"),
        author=cp.get("theme", "author", fallback=""),
        version=cp.get("theme", "version", fallback="1.0"),
        description=cp.get("theme", "description", fallback=""),
        preview=cp.get("theme", "preview", fallback=""),
        folder_name=folder_name,
        kind=kind,
    )


def _sanitize_folder_name(name: str) -> str:
    import re
    s = re.sub(r'[^\w\s-]', '', name)
    s = re.sub(r'\s+', '_', s.strip())
    return s[:50] or "custom_theme"


def read_theme_preview(theme_path: Path) -> bytes | None:
    meta = _read_metadata(theme_path)
    if not meta or not meta.preview:
        return None
    preview_path = theme_path / meta.preview
    if not preview_path.exists():
        return None
    return preview_path.read_bytes()
