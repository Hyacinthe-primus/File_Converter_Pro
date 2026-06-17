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

import os
import json
import shutil
import sys


def _get_languages_dir() -> str:
    if getattr(sys, 'frozen', False):
        base = os.path.join(os.path.dirname(sys.executable), "_internal")
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "languages")


_LANGUAGES_DIR = _get_languages_dir()


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
            {"code": "fr", "name": "Français",  "builtin": True,
             "author": "Hyacinthe", "version": "1.0", "description": "Langue par défaut"},
            {"code": "en", "name": "English",   "builtin": True,
             "author": "Hyacinthe", "version": "1.0", "description": "Default language"},
        ]
        for code, meta in self._external_meta.items():
            result.append({
                "code":        code,
                "name":        meta.get("name", code),
                "builtin":     False,
                "author":      meta.get("author", ""),
                "version":     meta.get("version", ""),
                "description": meta.get("description", ""),
                "file":        meta.get("file", ""),
            })
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

        meta    = data.get("meta", {})
        strings = data.get("strings", {})
        code    = meta.get("code", "").strip().lower()

        if not code or not isinstance(strings, dict):
            raise ValueError("Missing code or strings.")

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
        if self.current_language in self.translations:
            lang_dict = self.translations[self.current_language]
            result = lang_dict.get(text, text)
            if isinstance(result, str) and chr(92) + 'n' in result:
                result = result.replace(chr(92) + 'n', chr(10)).replace(chr(92) + 't', chr(9))
            return result
        return text

    def translate_operation_type(self, operation_key):
        translations = {
            "fr": {
                "pdf_to_word": "PDF vers Word",
                "word_to_pdf": "Word vers PDF",
                "image_to_pdf": "Images vers PDF",
                "image_to_pdf_s": "Images vers PDF séparés",
                "merge_pdf": "Fusion PDF",
                "merge_word": "Fusion Word",
                "split_pdf": "Division PDF",
                "protect_pdf": "Protection PDF",
                "office_optimization": "Optimisation bureautique",
                "batch_conversion": "Conversion par Lot",
                "batch_rename": "Renommage par Lot",
                "file_compression": "Compression de fichiers",
                "txt_to_pdf":   "TXT → PDF",
                "rtf_to_pdf":   "RTF → PDF",
                "txt_to_docx":  "TXT → DOCX",
                "rtf_to_docx":  "RTF → DOCX",
                "csv_to_json":  "CSV → JSON",
                "json_to_csv":  "JSON → CSV",
                "xlsx_to_pdf":  "XLSX → PDF",
                "xlsx_to_json": "XLSX → JSON",
                "xlsx_to_csv":  "XLSX → CSV",
                "pptx_to_pdf":  "PPTX → PDF",
                "html_to_pdf":  "HTML → PDF",
                "pdf_to_html":  "PDF → HTML",
                "epub_to_pdf":  "EPUB → PDF",
                "jpeg_to_png":  "JPEG → PNG",
                "png_to_jpg":   "PNG → JPG",
                "jpg_to_png":   "JPG → PNG",
                "webp_to_png":  "WEBP → PNG",
                "bmp_to_png":   "BMP → PNG",
                "tiff_to_png":  "TIFF → PNG",
                "heic_to_png":  "HEIC → PNG",
                "heif_to_png":  "HEIF → PNG",
                "ico_to_png":   "ICO → PNG",
                "psd_to_png":   "PSD → PNG",
                "svg_to_png":   "SVG → PNG",
                "raw_to_png":   "RAW → PNG",
                "png_to_webp":  "PNG → WEBP",
                "png_to_avif":  "PNG → AVIF",
                "image_resize": "Redimensionnement d'image",
                "image_to_ico": "Image → ICO",
                "audio_convert": "Conversion audio",
                "video_convert": "Conversion vidéo",
                "csv_to_xlsx":  "CSV → XLSX",
                "json_to_xlsx": "JSON → XLSX",
                "csv_to_pdf":   "CSV → PDF",
                "json_to_pdf":  "JSON → PDF",
                "image_to_png":  "Image → PNG",
                "image_to_jpeg": "Image → JPEG",
                "image_to_jpg":  "Image → JPG",
                "image_to_bmp":  "Image → BMP",
                "image_to_heic": "Image → HEIC",
                "image_to_webp": "Image → WEBP",
                "image_to_tiff": "Image → TIFF",
                "image_to_psd":  "Image → PSD",
                "image_to_svg":  "Image → SVG",
                "image_to_avif": "Image → AVIF",
                "image_to_j2k":  "Image → J2K",
                "image_to_dng":  "Image → DNG",
                "video_to_mp4":  "Vidéo → MP4",
                "video_to_webm": "Vidéo → WEBM",
                "video_to_mkv":  "Vidéo → MKV",
                "video_to_mov":  "Vidéo → MOV",
                "video_to_avi":  "Vidéo → AVI",
                "video_to_mp3":  "Vidéo → MP3",
                "video_to_wav":  "Vidéo → WAV",
                "video_to_aac":  "Vidéo → AAC",
                "video_to_flac": "Vidéo → FLAC",
                "audio_to_mp3":  "Audio → MP3",
                "audio_to_wav":  "Audio → WAV",
                "audio_to_aac":  "Audio → AAC",
                "audio_to_ogg":  "Audio → OGG",
                "audio_to_flac": "Audio → FLAC",
                "audio_to_m4a":  "Audio → M4A",
            },
            "en": {
                "pdf_to_word": "PDF to Word",
                "word_to_pdf": "Word to PDF",
                "image_to_pdf": "Images to PDF",
                "image_to_pdf_s": "Separate Images to PDF",
                "merge_pdf": "Merge PDF",
                "merge_word": "Merge Word",
                "split_pdf": "Split PDF",
                "protect_pdf": "PDF Protection",
                "office_optimization": "Office Optimization",
                "batch_conversion": "Batch Conversion",
                "batch_rename": "Batch Rename",
                "file_compression": "File Compression",
                "txt_to_pdf":   "TXT → PDF",
                "rtf_to_pdf":   "RTF → PDF",
                "txt_to_docx":  "TXT → DOCX",
                "rtf_to_docx":  "RTF → DOCX",
                "csv_to_json":  "CSV → JSON",
                "json_to_csv":  "JSON → CSV",
                "xlsx_to_pdf":  "XLSX → PDF",
                "xlsx_to_json": "XLSX → JSON",
                "xlsx_to_csv":  "XLSX → CSV",
                "pptx_to_pdf":  "PPTX → PDF",
                "html_to_pdf":  "HTML → PDF",
                "pdf_to_html":  "PDF → HTML",
                "epub_to_pdf":  "EPUB → PDF",
                "jpeg_to_png":  "JPEG → PNG",
                "png_to_jpg":   "PNG → JPG",
                "jpg_to_png":   "JPG → PNG",
                "webp_to_png":  "WEBP → PNG",
                "bmp_to_png":   "BMP → PNG",
                "tiff_to_png":  "TIFF → PNG",
                "heic_to_png":  "HEIC → PNG",
                "heif_to_png":  "HEIF → PNG",
                "ico_to_png":   "ICO → PNG",
                "psd_to_png":   "PSD → PNG",
                "svg_to_png":   "SVG → PNG",
                "raw_to_png":   "RAW → PNG",
                "png_to_webp":  "PNG → WEBP",
                "png_to_avif":  "PNG → AVIF",
                "image_resize": "Image Resize",
                "image_to_ico": "Image → ICO",
                "audio_convert": "Audio Conversion",
                "video_convert": "Video Conversion",
                "csv_to_xlsx":  "CSV → XLSX",
                "json_to_xlsx": "JSON → XLSX",
                "csv_to_pdf":   "CSV → PDF",
                "json_to_pdf":  "JSON → PDF",
                "image_to_png":  "Image → PNG",
                "image_to_jpeg": "Image → JPEG",
                "image_to_jpg":  "Image → JPG",
                "image_to_bmp":  "Image → BMP",
                "image_to_heic": "Image → HEIC",
                "image_to_webp": "Image → WEBP",
                "image_to_tiff": "Image → TIFF",
                "image_to_psd":  "Image → PSD",
                "image_to_svg":  "Image → SVG",
                "image_to_avif": "Image → AVIF",
                "image_to_j2k":  "Image → J2K",
                "image_to_dng":  "Image → DNG",
                "video_to_mp4":  "Video → MP4",
                "video_to_webm": "Video → WEBM",
                "video_to_mkv":  "Video → MKV",
                "video_to_mov":  "Video → MOV",
                "video_to_avi":  "Video → AVI",
                "video_to_mp3":  "Video → MP3",
                "video_to_wav":  "Video → WAV",
                "video_to_aac":  "Video → AAC",
                "video_to_flac": "Video → FLAC",
                "audio_to_mp3":  "Audio → MP3",
                "audio_to_wav":  "Audio → WAV",
                "audio_to_aac":  "Audio → AAC",
                "audio_to_ogg":  "Audio → OGG",
                "audio_to_flac": "Audio → FLAC",
                "audio_to_m4a":  "Audio → M4A",
            }
        }
        lang = translations.get(self.current_language, translations.get("fr", {}))
        return lang.get(operation_key, operation_key)
