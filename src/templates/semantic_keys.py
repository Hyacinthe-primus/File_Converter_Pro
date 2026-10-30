"""Semantic identifiers for template types and configuration values.

Template rows in the database historically stored French display labels.  This
module keeps those labels as *legacy aliases* while new templates use the
language-independent keys below.  Normalization accepts semantic keys, legacy
French labels, English labels and internal values, so old databases and
exported templates keep working.
"""

from __future__ import annotations

from typing import Any

# Template types -----------------------------------------------------------
PDF_TO_WORD = "pdf_to_word"
WORD_TO_PDF = "word_to_pdf"
IMAGES_TO_PDF = "images_to_pdf"
PDF_MERGE = "pdf_merge"
WORD_MERGE = "word_merge"
PDF_SPLIT = "pdf_split"
PDF_PROTECTION = "pdf_protection"
COMPRESSION = "compression"
FILE_OPTIMIZATION = "file_optimization"

TYPE_LABEL_KEYS = {
    PDF_TO_WORD: "pdf_to_word_conversion",
    WORD_TO_PDF: "word_to_pdf_conversion",
    IMAGES_TO_PDF: "images_to_pdf_conversion",
    PDF_MERGE: "pdf_merge",
    WORD_MERGE: "word_merge",
    PDF_SPLIT: "pdf_split",
    PDF_PROTECTION: "pdf_protection",
    COMPRESSION: "Compression",
    FILE_OPTIMIZATION: "file_optimization",
}

TYPE_LEGACY_NAMES = {
    PDF_TO_WORD: "Conversion PDF\u2192Word",
    WORD_TO_PDF: "Conversion Word\u2192PDF",
    IMAGES_TO_PDF: "Conversion Images\u2192PDF",
    PDF_MERGE: "Fusion PDF",
    WORD_MERGE: "Fusion Word",
    PDF_SPLIT: "Division PDF",
    PDF_PROTECTION: "Protection PDF",
    COMPRESSION: "Compression",
    FILE_OPTIMIZATION: "Pr\u00e9r\u00e9glages de qualit\u00e9",
}

TYPE_ALIASES = {
    PDF_TO_WORD: PDF_TO_WORD,
    "PDF to Word Conversion": PDF_TO_WORD,
    "Conversion PDF\u2192Word": PDF_TO_WORD,
    "pdf_to_word_conversion": PDF_TO_WORD,
    WORD_TO_PDF: WORD_TO_PDF,
    "Word to PDF Conversion": WORD_TO_PDF,
    "Conversion Word\u2192PDF": WORD_TO_PDF,
    "word_to_pdf_conversion": WORD_TO_PDF,
    IMAGES_TO_PDF: IMAGES_TO_PDF,
    "Images to PDF Conversion": IMAGES_TO_PDF,
    "Conversion Images\u2192PDF": IMAGES_TO_PDF,
    "images_to_pdf_conversion": IMAGES_TO_PDF,
    PDF_MERGE: PDF_MERGE,
    "PDF Merge": PDF_MERGE,
    "Fusion PDF": PDF_MERGE,
    "pdf_merge": PDF_MERGE,
    WORD_MERGE: WORD_MERGE,
    "Word Merge": WORD_MERGE,
    "Fusion Word": WORD_MERGE,
    "word_merge": WORD_MERGE,
    PDF_SPLIT: PDF_SPLIT,
    "PDF Split": PDF_SPLIT,
    "Division PDF": PDF_SPLIT,
    "pdf_split": PDF_SPLIT,
    PDF_PROTECTION: PDF_PROTECTION,
    "PDF Protection": PDF_PROTECTION,
    "Protection PDF": PDF_PROTECTION,
    "pdf_protection": PDF_PROTECTION,
    COMPRESSION: COMPRESSION,
    "compression": COMPRESSION,
    FILE_OPTIMIZATION: FILE_OPTIMIZATION,
    "Quality Presets": FILE_OPTIMIZATION,
    "Office Optimization": FILE_OPTIMIZATION,
    "File optimization": FILE_OPTIMIZATION,
    "Optimisation de fichiers": FILE_OPTIMIZATION,
    "Pr\u00e9r\u00e9glages de qualit\u00e9": FILE_OPTIMIZATION,
    "file_optimization": FILE_OPTIMIZATION,
}

# Configuration values ----------------------------------------------------
MODE_WITH_IMAGES = "with_images"
MODE_TEXT_ONLY = "text_only"
MODE_PRESERVE_ALL = "preserve_all"

QUALITY_HIGH = "high_300_dpi"
QUALITY_STANDARD = "standard_150_dpi"
QUALITY_LOW = "low_72_dpi"

ORDER_CURRENT = "current"
ORDER_ALPHA_AZ = "alpha_az"
ORDER_ALPHA_ZA = "alpha_za"
ORDER_NUM_ASC = "num_asc"
ORDER_NUM_DESC = "num_desc"
ORDER_DATE_ASC = "date_asc"
ORDER_DATE_DESC = "date_desc"
ORDER_MANUAL = "manual"

SPLIT_BY_PAGES = "by_pages"
SPLIT_ALL_PAGES = "all_pages"
SPLIT_PAGE_RANGE = "page_range"

PROTECTION_BASIC = "basic"
PROTECTION_ADVANCED = "advanced"

LEVEL_NORMAL = "normal"
LEVEL_HIGH = "high"
LEVEL_MAXIMUM = "maximum"

FORMAT_ZIP = "zip"
FORMAT_7Z = "7z"
FORMAT_TAR_GZ = "tar_gz"
FORMAT_TAR = "tar"

OPTIMIZATION_COMPRESSION = "compression"
OPTIMIZATION_CLEANING = "cleaning"
OPTIMIZATION_BOTH = "compression_cleaning"

_PDF_TO_WORD_MODES = {
    MODE_WITH_IMAGES: MODE_WITH_IMAGES,
    MODE_TEXT_ONLY: MODE_TEXT_ONLY,
    "Conserver les images et la mise en page": MODE_WITH_IMAGES,
    "Texte brut uniquement": MODE_TEXT_ONLY,
    "Keep images and layout": MODE_WITH_IMAGES,
    "Plain text only": MODE_TEXT_ONLY,
}
_WORD_TO_PDF_MODES = {
    MODE_PRESERVE_ALL: MODE_PRESERVE_ALL,
    MODE_TEXT_ONLY: MODE_TEXT_ONLY,
    "Conserver toute la mise en page": MODE_PRESERVE_ALL,
    "Texte uniquement": MODE_TEXT_ONLY,
    "Preserve all layout": MODE_PRESERVE_ALL,
    "Text only": MODE_TEXT_ONLY,
}
_QUALITIES = {
    QUALITY_HIGH: QUALITY_HIGH,
    QUALITY_STANDARD: QUALITY_STANDARD,
    QUALITY_LOW: QUALITY_LOW,
    "high": QUALITY_HIGH,
    "standard": QUALITY_STANDARD,
    "low": QUALITY_LOW,
    "optimized": QUALITY_LOW,
    "Haute (300 DPI)": QUALITY_HIGH,
    "Haute qualit\u00e9 (300 DPI)": QUALITY_HIGH,
    "High (300 DPI)": QUALITY_HIGH,
    "High quality (300 DPI)": QUALITY_HIGH,
    "Standard (150 DPI)": QUALITY_STANDARD,
    "Qualit\u00e9 standard (150 DPI)": QUALITY_STANDARD,
    "Standard quality (150 DPI)": QUALITY_STANDARD,
    "Basse (72 DPI)": QUALITY_LOW,
    "Optimis\u00e9 (96 DPI)": QUALITY_LOW,
    "Low (72 DPI)": QUALITY_LOW,
    "Optimized (96 DPI)": QUALITY_LOW,
}
_MERGE_ORDERS = {
    ORDER_CURRENT: ORDER_CURRENT,
    ORDER_ALPHA_AZ: ORDER_ALPHA_AZ,
    ORDER_ALPHA_ZA: ORDER_ALPHA_ZA,
    ORDER_NUM_ASC: ORDER_NUM_ASC,
    ORDER_NUM_DESC: ORDER_NUM_DESC,
    ORDER_DATE_ASC: ORDER_DATE_ASC,
    ORDER_DATE_DESC: ORDER_DATE_DESC,
    ORDER_MANUAL: ORDER_MANUAL,
    "Ordre actuel (liste principale)": ORDER_CURRENT,
    "Alphab\u00e9tique": ORDER_ALPHA_AZ,
    "Alphab\u00e9tique (A\u2192Z)": ORDER_ALPHA_AZ,
    "Alphab\u00e9tique (Z\u2192A)": ORDER_ALPHA_ZA,
    "Num\u00e9rique (1\u21929)": ORDER_NUM_ASC,
    "Num\u00e9rique (9\u21921)": ORDER_NUM_DESC,
    "Date (ancien\u2192nouveau)": ORDER_DATE_ASC,
    "Date (nouveau\u2192ancien)": ORDER_DATE_DESC,
    "Manuel (glisser-d\u00e9poser)": ORDER_MANUAL,
    "Current order (main list)": ORDER_CURRENT,
    "Alphabetical (A\u2192Z)": ORDER_ALPHA_AZ,
    "Alphabetical (Z\u2192A)": ORDER_ALPHA_ZA,
    "Numeric (1\u21929)": ORDER_NUM_ASC,
    "Numeric (9\u21921)": ORDER_NUM_DESC,
    "Date (oldest\u2192newest)": ORDER_DATE_ASC,
    "Date (newest\u2192oldest)": ORDER_DATE_DESC,
    "Manual (drag and drop)": ORDER_MANUAL,
}
_SPLIT_METHODS = {
    SPLIT_BY_PAGES: SPLIT_BY_PAGES,
    SPLIT_ALL_PAGES: SPLIT_ALL_PAGES,
    SPLIT_PAGE_RANGE: SPLIT_PAGE_RANGE,
    "Par pages": SPLIT_BY_PAGES,
    "Toutes les pages": SPLIT_ALL_PAGES,
    "Plage de pages": SPLIT_PAGE_RANGE,
    "By pages": SPLIT_BY_PAGES,
    "All pages": SPLIT_ALL_PAGES,
    "Page range": SPLIT_PAGE_RANGE,
}
_PROTECTION_LEVELS = {
    PROTECTION_BASIC: PROTECTION_BASIC,
    PROTECTION_ADVANCED: PROTECTION_ADVANCED,
    "Basique (ouvrir)": PROTECTION_BASIC,
    "Basique (restrictions uniquement)": PROTECTION_BASIC,
    "Basic (open)": PROTECTION_BASIC,
    "Basic (restrictions only)": PROTECTION_BASIC,
    "Avanc\u00e9 (ouvrir + modifications)": PROTECTION_ADVANCED,
    "Avanc\u00e9 (mot de passe + restrictions)": PROTECTION_ADVANCED,
    "Advanced (open + modifications)": PROTECTION_ADVANCED,
    "Advanced (password + restrictions)": PROTECTION_ADVANCED,
}
_COMPRESSION_LEVELS = {
    LEVEL_NORMAL: LEVEL_NORMAL,
    LEVEL_HIGH: LEVEL_HIGH,
    LEVEL_MAXIMUM: LEVEL_MAXIMUM,
    "Normal": LEVEL_NORMAL,
    "normal": LEVEL_NORMAL,
    "Haute compression": LEVEL_HIGH,
    "High compression": LEVEL_HIGH,
    "high": LEVEL_HIGH,
    "Compression maximale": LEVEL_MAXIMUM,
    "Maximum compression": LEVEL_MAXIMUM,
    "maximum": LEVEL_MAXIMUM,
}
_FORMATS = {
    FORMAT_ZIP: FORMAT_ZIP,
    FORMAT_7Z: FORMAT_7Z,
    FORMAT_TAR_GZ: FORMAT_TAR_GZ,
    FORMAT_TAR: FORMAT_TAR,
    "ZIP": FORMAT_ZIP,
    "zip": FORMAT_ZIP,
    "7Z": FORMAT_7Z,
    "7z": FORMAT_7Z,
    "TAR.GZ": FORMAT_TAR_GZ,
    "tar_gz": FORMAT_TAR_GZ,
    "TAR": FORMAT_TAR,
    "tar": FORMAT_TAR,
}
_OPTIMIZATION_TYPES = {
    OPTIMIZATION_COMPRESSION: OPTIMIZATION_COMPRESSION,
    OPTIMIZATION_CLEANING: OPTIMIZATION_CLEANING,
    OPTIMIZATION_BOTH: OPTIMIZATION_BOTH,
    0: OPTIMIZATION_COMPRESSION,
    1: OPTIMIZATION_CLEANING,
    2: OPTIMIZATION_BOTH,
    "0": OPTIMIZATION_COMPRESSION,
    "1": OPTIMIZATION_CLEANING,
    "2": OPTIMIZATION_BOTH,
    "compression": OPTIMIZATION_COMPRESSION,
    "nettoyage": OPTIMIZATION_CLEANING,
    "les deux": OPTIMIZATION_BOTH,
    "Compression  -  r\u00e9duit la taille du fichier": OPTIMIZATION_COMPRESSION,
    "Compression  -  reduces file size": OPTIMIZATION_COMPRESSION,
    "Nettoyage  -  supprime uniquement les m\u00e9tadonn\u00e9es": OPTIMIZATION_CLEANING,
    "Cleaning  -  removes metadata only": OPTIMIZATION_CLEANING,
    "Compression + Nettoyage  -  recommand\u00e9": OPTIMIZATION_BOTH,
    "Compression + Cleaning  -  recommended": OPTIMIZATION_BOTH,
}

_LABEL_KEYS = {
    "mode": {
        MODE_WITH_IMAGES: "keep_images_and_layout",
        MODE_TEXT_ONLY: "text_only",
        MODE_PRESERVE_ALL: "preserve_all_layout",
    },
    "quality": {
        QUALITY_HIGH: "high_300_dpi",
        QUALITY_STANDARD: "standard_150_dpi",
        QUALITY_LOW: "low_72_dpi",
    },
    "merge_order": {
        ORDER_CURRENT: "current_order_main_list",
        ORDER_ALPHA_AZ: "alphabetical_a_to_z",
        ORDER_ALPHA_ZA: "alphabetical_z_to_a",
        ORDER_NUM_ASC: "numeric_1_to_9",
        ORDER_NUM_DESC: "numeric_9_to_1",
        ORDER_DATE_ASC: "date_oldest_to_newest",
        ORDER_DATE_DESC: "date_newest_to_oldest",
        ORDER_MANUAL: "manual_drag_and_drop",
    },
    "split_method": {
        SPLIT_BY_PAGES: "by_pages",
        SPLIT_ALL_PAGES: "all_pages",
        SPLIT_PAGE_RANGE: "page_range",
    },
    "protection_level": {
        PROTECTION_BASIC: "basic_open",
        PROTECTION_ADVANCED: "advanced",
    },
    "compression_level": {
        LEVEL_NORMAL: "Normal",
        LEVEL_HIGH: "high_compression",
        LEVEL_MAXIMUM: "maximum_compression",
    },
    "format": {
        FORMAT_ZIP: "ZIP",
        FORMAT_7Z: "7Z",
        FORMAT_TAR_GZ: "tar_gz",
        FORMAT_TAR: "TAR",
    },
    "optimization_type": {
        OPTIMIZATION_COMPRESSION: "compression_reduces_file_size",
        OPTIMIZATION_CLEANING: "cleaning_removes_metadata_only",
        OPTIMIZATION_BOTH: "compression_cleaning_recommended",
    },
}

_LEGACY_QUALITY_LABELS = {
    QUALITY_HIGH: "Haute (300 DPI)",
    QUALITY_STANDARD: "Standard (150 DPI)",
    QUALITY_LOW: "Basse (72 DPI)",
}
_LEGACY_COMPRESSION_LABELS = {
    LEVEL_NORMAL: "Normal",
    LEVEL_HIGH: "Haute compression",
    LEVEL_MAXIMUM: "Compression maximale",
}
_LEGACY_SPLIT_LABELS = {
    SPLIT_BY_PAGES: "Par pages",
    SPLIT_ALL_PAGES: "Toutes les pages",
    SPLIT_PAGE_RANGE: "Plage de pages",
}
_LEGACY_MERGE_LABELS = {
    ORDER_CURRENT: "Ordre actuel (liste principale)",
    ORDER_ALPHA_AZ: "Alphab\u00e9tique (A\u2192Z)",
    ORDER_ALPHA_ZA: "Alphab\u00e9tique (Z\u2192A)",
    ORDER_NUM_ASC: "Num\u00e9rique (1\u21929)",
    ORDER_NUM_DESC: "Num\u00e9rique (9\u21921)",
    ORDER_DATE_ASC: "Date (ancien\u2192nouveau)",
    ORDER_DATE_DESC: "Date (nouveau\u2192ancien)",
    ORDER_MANUAL: "Manuel (glisser-d\u00e9poser)",
}


def normalize_type(value: Any) -> str:
    """Return the semantic template type for any legacy/translated value."""
    if not isinstance(value, str):
        return value
    if value in TYPE_ALIASES:
        return TYPE_ALIASES[value]
    normalized = " ".join(value.split())
    for alias, key in TYPE_ALIASES.items():
        if isinstance(alias, str) and " ".join(alias.split()).casefold() == normalized.casefold():
            return key
    return value


def legacy_type(value: Any) -> str:
    """Return the historical French storage name for a template type."""
    key = normalize_type(value)
    return TYPE_LEGACY_NAMES.get(key, value)


def type_label_key(value: Any) -> str:
    """Return the translation key used to display a template type."""
    key = normalize_type(value)
    return TYPE_LABEL_KEYS.get(key, value)


def _choice(value: Any, mapping: dict, default: Any) -> Any:
    if value in mapping:
        return mapping[value]
    if isinstance(value, str):
        normalized = " ".join(value.split())
        for alias, result in mapping.items():
            if isinstance(alias, str) and " ".join(alias.split()).casefold() == normalized.casefold():
                return result
    return default


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def normalize_config(template_type: Any, config: dict | None) -> dict:
    """Return a semantic configuration for any template type.

    Unknown fields are preserved so user metadata (for example ``name_template``
    or ``is_default``) is not lost.
    """
    key = normalize_type(template_type)
    cfg = dict(config or {})

    if key == PDF_TO_WORD:
        result = {
            "mode": _choice(cfg.get("mode"), _PDF_TO_WORD_MODES, MODE_WITH_IMAGES),
            "quality": _choice(cfg.get("quality"), _QUALITIES, QUALITY_STANDARD),
            "keep_bookmarks": bool(cfg.get("keep_bookmarks", True)),
            "extract_images": bool(cfg.get("extract_images", False)),
        }
    elif key == WORD_TO_PDF:
        result = {
            "mode": _choice(cfg.get("mode"), _WORD_TO_PDF_MODES, MODE_PRESERVE_ALL),
            "quality": _choice(cfg.get("quality"), _QUALITIES, QUALITY_STANDARD),
            "include_metadata": bool(cfg.get("include_metadata", True)),
            "compress_images": bool(cfg.get("compress_images", cfg.get("compress", True))),
            "page_format": cfg.get("page_format", "A4"),
            "orientation": cfg.get("orientation", "Portrait"),
        }
    elif key == IMAGES_TO_PDF:
        result = {
            "separate": bool(cfg.get("separate", False)),
            "orientation": cfg.get("orientation", "Portrait"),
            "quality": _choice(cfg.get("quality"), _QUALITIES, QUALITY_STANDARD),
            "margin": _as_int(cfg.get("margin"), 20),
            "compress_images": bool(cfg.get("compress_images", True)),
            "keep_original_order": bool(cfg.get("keep_original_order", True)),
        }
    elif key in (PDF_MERGE, WORD_MERGE):
        result = {
            "merge_order": _choice(cfg.get("merge_order"), _MERGE_ORDERS, ORDER_CURRENT),
            "name_template": cfg.get("name_template", ""),
        }
        if key == PDF_MERGE:
            result.update(
                {
                    "merge_bookmarks": bool(cfg.get("merge_bookmarks", True)),
                    "remove_duplicates": bool(cfg.get("remove_duplicates", False)),
                    "add_page_numbers": bool(cfg.get("add_page_numbers", False)),
                }
            )
        else:
            result.update(
                {
                    "keep_formatting": bool(cfg.get("keep_formatting", True)),
                    "add_page_breaks": bool(cfg.get("add_page_breaks", True)),
                }
            )
    elif key == PDF_SPLIT:
        result = {
            "split_method": _choice(cfg.get("split_method"), _SPLIT_METHODS, SPLIT_BY_PAGES),
            "pages_per_file": max(1, _as_int(cfg.get("pages_per_file"), 1)),
            "keep_bookmarks": bool(cfg.get("keep_bookmarks", True)),
            "name_template": cfg.get("name_template", ""),
        }
    elif key == PDF_PROTECTION:
        result = {
            "protection_level": _choice(
                cfg.get("protection_level", cfg.get("mode")),
                _PROTECTION_LEVELS,
                PROTECTION_BASIC,
            ),
            "allow_printing": bool(cfg.get("allow_printing", True)),
            "allow_copying": bool(cfg.get("allow_copying", True)),
            "allow_modifications": bool(cfg.get("allow_modifications", False)),
        }
    elif key == COMPRESSION:
        split_size = max(0, _as_int(cfg.get("split_size"), 0))
        split = bool(cfg.get("split_archive", split_size > 0)) and split_size > 0
        result = {
            "format": _choice(cfg.get("format"), _FORMATS, FORMAT_ZIP),
            "compression_level": _choice(cfg.get("compression_level"), _COMPRESSION_LEVELS, LEVEL_NORMAL),
            "encrypt": bool(cfg.get("encrypt", False)),
            "delete_originals": bool(cfg.get("delete_originals", False)),
            "split_archive": split,
            "split_size": split_size if split else 0,
        }
    elif key == FILE_OPTIMIZATION:
        result = {
            "optimization_type": _choice(cfg.get("optimization_type"), _OPTIMIZATION_TYPES, OPTIMIZATION_BOTH),
            "quality_level": _as_int(cfg.get("quality_level"), 1),
            "remove_metadata": bool(cfg.get("remove_metadata", True)),
            "compress_images": bool(cfg.get("compress_images", True)),
            "keep_backup": bool(cfg.get("keep_backup", True)),
        }
    else:
        result = cfg

    if "is_default" in cfg:
        result["is_default"] = bool(cfg["is_default"])
    return result


def display_value(field: str, value: Any, translate, template_type: Any = None) -> str:
    """Translate a semantic config value for display."""
    if value is None:
        return ""
    if field == "mode":
        key = _choice(value, _PDF_TO_WORD_MODES, value)
        if key == MODE_TEXT_ONLY:
            if normalize_type(template_type) == PDF_TO_WORD:
                return translate("text_only_2")
            return translate("text_only")
        if key == MODE_PRESERVE_ALL:
            return translate("preserve_all_layout")
        if key == MODE_WITH_IMAGES:
            return translate("keep_images_and_layout")
    label_key = _LABEL_KEYS.get(field, {}).get(value)
    if label_key:
        return translate(label_key)
    if isinstance(value, bool):
        return translate("yes") if value else translate("no")
    return str(value)


def quality_legacy_label(value: Any) -> str:
    return _LEGACY_QUALITY_LABELS.get(_choice(value, _QUALITIES, QUALITY_STANDARD), "Standard (150 DPI)")


def compression_level_legacy_label(value: Any) -> str:
    return _LEGACY_COMPRESSION_LABELS.get(_choice(value, _COMPRESSION_LEVELS, LEVEL_NORMAL), "Normal")


def split_method_legacy_label(value: Any) -> str:
    return _LEGACY_SPLIT_LABELS.get(_choice(value, _SPLIT_METHODS, SPLIT_BY_PAGES), "Par pages")


def merge_order_legacy_label(value: Any) -> str:
    return _LEGACY_MERGE_LABELS.get(_choice(value, _MERGE_ORDERS, ORDER_CURRENT), "Ordre actuel (liste principale)")


def archive_format_legacy(value: Any) -> str:
    return {
        FORMAT_ZIP: "ZIP",
        FORMAT_7Z: "7Z",
        FORMAT_TAR_GZ: "TAR.GZ",
        FORMAT_TAR: "TAR",
    }.get(_choice(value, _FORMATS, FORMAT_ZIP), "ZIP")


def optimization_type_value(value: Any) -> int:
    return {
        OPTIMIZATION_COMPRESSION: 0,
        OPTIMIZATION_CLEANING: 1,
        OPTIMIZATION_BOTH: 2,
    }.get(_choice(value, _OPTIMIZATION_TYPES, OPTIMIZATION_BOTH), 2)
