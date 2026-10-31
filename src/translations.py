"""
Translation Manager

Provides internationalization (i18n) support for French, English,
and any external language loaded from a .lang file (JSON format).

Key Features:
    - Centralized dictionary for all UI strings (fr / en built-in)
    - Dynamic text translation based on selected language
    - Technical operation type translation (e.g., 'pdf_to_word' -> 'PDF to Word')
    - External .lang file support: users can create community translations
      and import them through Settings -> Language tab.
    - .lang files are stored in the  languages/  sub-folder next to the app.
    - On startup all .lang files in that folder are loaded automatically.

Classes:
    TranslationManager: Manages current language state and translates text on demand.

Usage:
    translator = TranslationManager()
    translator.set_language("en")
    text = translator.translate_text("Settings")

    # Load an external .lang file
    ok, msg = translator.load_lang_file("/path/to/german.lang")

"""

import json
import os
import shutil
import sys

from utils import SRC_DIR


def _get_languages_dir():
    if getattr(sys, "frozen", False):
        base = os.path.join(os.path.dirname(sys.executable), "_internal")
    else:
        base = str(SRC_DIR)
    return os.path.join(base, "languages")


_LANGUAGES_DIR = _get_languages_dir()


def _load_legacy_aliases() -> dict:
    """Load the old-key to semantic-key aliases used by pre-rename .lang files."""
    path = os.path.join(_LANGUAGES_DIR, "legacy_aliases.json")
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return {str(key): str(value) for key, value in data.items() if isinstance(value, str)}
    except Exception as e:
        print(f"[TranslationManager] Failed to load legacy_aliases.json: {e}")
    return {}


_LEGACY_ALIASES = _load_legacy_aliases()


def _starts_with_flag(name: str) -> bool:
    """True if the name already begins with a flag emoji (two regional indicators)."""
    count = 0
    for char in name:
        code = ord(char)
        if 0x1F1E6 <= code <= 0x1F1FF:
            count += 1
        else:
            break
    return count >= 2


def decorate_language_name(name: str) -> str:
    """Return the name, prefixed with a globe if it does not already carry a flag."""
    name = name or ""
    if _starts_with_flag(name):
        return name
    return "🌐 " + name


def _load_builtin_translations() -> dict:
    """Load built-in FR and EN translations from JSON files."""
    translations = {}
    for code in ("fr", "en"):
        path = os.path.join(_LANGUAGES_DIR, f"{code}.json")
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    translations[code] = json.load(f)
            except Exception as e:
                print(f"[TranslationManager] Failed to load {code}.json: {e}")
                translations[code] = {}
        else:
            translations[code] = {}
    return translations


class TranslationManager:
    def __init__(self):
        self.current_language = "fr"
        self._external_meta = {}
        self.translations = _load_builtin_translations()
        self._autoload_lang_files()

    # Language management
    def set_language(self, language: str) -> None:
        self.current_language = language

    def get_available_languages(self) -> list:
        result = [
            {
                "code": "fr",
                "name": "🇫🇷 Français",
                "builtin": True,
                "author": "Hyacinthe",
                "version": "1.0",
                "description": "Langue par défaut",
            },
            {
                "code": "en",
                "name": "🇬🇧 English",
                "builtin": True,
                "author": "Hyacinthe",
                "version": "1.0",
                "description": "Default language",
            },
        ]
        for code, meta in self._external_meta.items():
            result.append(
                {
                    "code": code,
                    "name": meta.get("name", code),
                    "builtin": False,
                    "author": meta.get("author", ""),
                    "version": meta.get("version", ""),
                    "description": meta.get("description", ""),
                    "file": meta.get("file", ""),
                }
            )
        return result

    def _autoload_lang_files(self) -> None:
        if not os.path.isdir(_LANGUAGES_DIR):
            return
        for fname in os.listdir(_LANGUAGES_DIR):
            if fname.endswith(".lang"):
                path = os.path.join(_LANGUAGES_DIR, fname)
                try:
                    self._load_lang_file_internal(path)
                except Exception as e:
                    print(f"[TranslationManager] Could not load {fname}: {e}")

    def load_lang_file(self, filepath: str) -> tuple:
        if not os.path.isfile(filepath):
            return False, "File not found."
        dest = os.path.join(_LANGUAGES_DIR, os.path.basename(filepath))
        try:
            shutil.copy2(filepath, dest)
        except Exception as e:
            return False, f"Cannot save to languages folder: {e}"

        self._load_lang_file_internal(dest)
        with open(dest, "r", encoding="utf-8") as f:
            data = json.load(f)
        return True, data.get("meta", {}).get("name", os.path.basename(filepath))

    def _load_lang_file_internal(self, filepath: str) -> None:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        meta = data.get("meta", {})
        raw_strings = data.get("strings", {})
        code = meta.get("code", "").strip().lower()

        if not code or not isinstance(raw_strings, dict):
            raise ValueError("Missing code or strings.")

        strings = {}
        for key, value in raw_strings.items():
            new_key = _LEGACY_ALIASES.get(key, key)
            if key in _LEGACY_ALIASES and str(strings.get(new_key, "")).strip():
                continue
            strings[new_key] = value

        if code not in self.translations:
            self.translations[code] = {}
        self.translations[code].update(strings)

        meta["file"] = filepath
        self._external_meta[code] = meta

    def remove_lang_file(self, code: str) -> tuple:
        if code in ("fr", "en"):
            return False, "Cannot remove a built-in language."
        if code not in self._external_meta:
            return False, f"Language '{code}' is not loaded."

        filepath = self._external_meta[code].get("file", "")
        if filepath and os.path.isfile(filepath):
            try:
                os.remove(filepath)
            except Exception as e:
                return False, f"Cannot delete file: {e}"

        self._external_meta.pop(code, None)
        self.translations.pop(code, None)

        if self.current_language == code:
            self.current_language = "fr"

        return True, ""

    def translate_text(self, text):
        if not isinstance(text, str):
            return text

        key = _LEGACY_ALIASES.get(text, text)
        if self.current_language in self.translations:
            lang_dict = self.translations[self.current_language]
            result = lang_dict.get(key)
            if result is None and key != text:
                result = lang_dict.get(text)
            if result is None:
                result = text
            if isinstance(result, str) and chr(92) + "n" in result:
                result = result.replace(chr(92) + "n", chr(10)).replace(chr(92) + "t", chr(9))
            return result
        return text

    def translate_operation_type(self, operation_key):
        """Return a human-readable, localized operation label.

        Language files are the source of truth. Keys without a translation
        fall back to a generated SOURCE → TARGET label so format-only
        operations still render clearly in every language.
        """
        if not isinstance(operation_key, str):
            return operation_key

        aliases = {
            "image_to_pdf": "images_to_pdf",
            "image_to_pdf_s": "images_to_pdf",
        }
        key = aliases.get(operation_key, operation_key)
        translated = self.translate_text(key)
        if translated != key:
            if operation_key == "image_to_pdf_s":
                return f"{translated} ({self.translate_text('one_pdf_per_image')})"
            return translated

        if operation_key == "Compression (selection)":
            return f"{self.translate_text('file_compression')} ({self.translate_text('selected_files')})"
        if operation_key == "Compression (all)":
            return f"{self.translate_text('file_compression')} ({self.translate_text('all_files')})"

        if "_to_" in key:
            source, target = key.split("_to_", 1)
            labels = {
                "txt": "TXT", "rtf": "RTF", "csv": "CSV", "json": "JSON",
                "xlsx": "XLSX", "pptx": "PPTX", "markdown": "Markdown",
                "html": "HTML", "pdf": "PDF", "epub": "EPUB",
            }
            return f"{labels.get(source.lower(), source.upper())} → {labels.get(target.lower(), target.upper())}"

        special = {
            "image_resize": "Image Resize",
            "audio_convert": "Audio Conversion",
            "video_convert": "Video Conversion",
        }
        return special.get(key, key)
