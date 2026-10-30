"""Tests for the language-independent template configuration keys."""

from templates import semantic_keys as sk


def test_type_aliases_normalize_to_semantic_keys():
    assert sk.normalize_type("Conversion PDF\u2192Word") == sk.PDF_TO_WORD
    assert sk.normalize_type("PDF to Word Conversion") == sk.PDF_TO_WORD
    assert sk.normalize_type("pdf_to_word_conversion") == sk.PDF_TO_WORD
    assert sk.normalize_type("Quality Presets") == sk.FILE_OPTIMIZATION
    assert sk.legacy_type(sk.PDF_TO_WORD) == "Conversion PDF\u2192Word"
    assert sk.type_label_key(sk.PDF_TO_WORD) == "pdf_to_word_conversion"


def test_normalize_config_accepts_legacy_labels():
    pdf_mode = sk.normalize_config(sk.PDF_TO_WORD, {"mode": "Texte brut uniquement"})
    assert pdf_mode["mode"] == sk.MODE_TEXT_ONLY

    word_mode = sk.normalize_config(sk.WORD_TO_PDF, {"mode": "Conserver toute la mise en page"})
    assert word_mode["mode"] == sk.MODE_PRESERVE_ALL

    merge = sk.normalize_config(sk.PDF_MERGE, {"merge_order": "Alphab\u00e9tique (A\u2192Z)"})
    assert merge["merge_order"] == sk.ORDER_ALPHA_AZ

    split = sk.normalize_config(sk.PDF_SPLIT, {"split_method": "Par pages"})
    assert split["split_method"] == sk.SPLIT_BY_PAGES
    assert (
        sk.normalize_config(sk.PDF_PROTECTION, {"protection_level": "Avanc\u00e9 (ouvrir + modifications)"})[
            "protection_level"
        ]
        == sk.PROTECTION_ADVANCED
    )


def test_normalize_config_accepts_internal_values():
    compression = sk.normalize_config(
        sk.COMPRESSION,
        {
            "format": "7Z",
            "compression_level": "Haute compression",
            "split_archive": True,
            "split_size": 50,
        },
    )
    assert compression["format"] == sk.FORMAT_7Z
    assert compression["compression_level"] == sk.LEVEL_HIGH
    assert compression["split_archive"] is True
    assert compression["split_size"] == 50

    optimization = sk.normalize_config(
        sk.FILE_OPTIMIZATION,
        {"optimization_type": "Compression + Nettoyage  -  recommand\u00e9"},
    )
    assert optimization["optimization_type"] == sk.OPTIMIZATION_BOTH


def test_display_value_uses_translation_keys():
    labels = {
        "text_only_2": "Texte brut uniquement",
        "preserve_all_layout": "Conserver toute la mise en page",
        "alphabetical_a_to_z": "Alphab\u00e9tique (A\u2192Z)",
    }
    assert sk.display_value("mode", sk.MODE_TEXT_ONLY, labels.get, sk.PDF_TO_WORD) == "Texte brut uniquement"
    assert (
        sk.display_value("mode", sk.MODE_PRESERVE_ALL, labels.get, sk.WORD_TO_PDF)
        == "Conserver toute la mise en page"
    )
    assert sk.display_value("merge_order", sk.ORDER_ALPHA_AZ, labels.get) == "Alphab\u00e9tique (A\u2192Z)"
