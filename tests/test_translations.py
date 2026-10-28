"""Tests for the translation system."""


def test_translation_manager_loads_builtin():
    """TranslationManager should load FR and EN from JSON files."""
    from translations import TranslationManager

    tm = TranslationManager()
    assert "fr" in tm.translations
    assert "en" in tm.translations
    assert len(tm.translations["fr"]) > 100
    assert len(tm.translations["en"]) > 100


def test_translation_set_language():
    """set_language should switch the active language."""
    from translations import TranslationManager

    tm = TranslationManager()
    tm.set_language("en")
    assert tm.current_language == "en"
    tm.set_language("fr")
    assert tm.current_language == "fr"


def test_translation_text():
    """translate_text should return translated string or original key."""
    from translations import TranslationManager

    tm = TranslationManager()
    tm.set_language("fr")
    result = tm.translate_text("file_management")
    assert isinstance(result, str)
    assert result == "Gestion des Fichiers"


def test_legacy_key_alias():
    """Old French keys should still resolve through the legacy alias map."""
    from translations import TranslationManager

    tm = TranslationManager()
    tm.set_language("en")
    assert tm.translate_text("Gestion des Fichiers") == "File Management"


def test_legacy_aliases_target_existing_keys():
    """Every legacy alias should point at a key present in the English source."""
    import json
    import os

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    lang_dir = os.path.join(root, "src", "languages")
    aliases = json.load(open(os.path.join(lang_dir, "legacy_aliases.json"), encoding="utf-8"))
    en = json.load(open(os.path.join(lang_dir, "en.json"), encoding="utf-8"))
    missing = sorted({target for target in aliases.values() if target not in en})
    assert not missing, f"legacy aliases point at missing keys: {missing[:10]}"


def test_translation_fallback():
    """translate_text should return the key itself if no translation found."""
    from translations import TranslationManager

    tm = TranslationManager()
    key = "xyz_nonexistent_key_12345"
    assert tm.translate_text(key) == key


def test_get_available_languages():
    """get_available_languages should return at least FR and EN."""
    from translations import TranslationManager

    tm = TranslationManager()
    langs = tm.get_available_languages()
    codes = [lang["code"] for lang in langs]
    assert "fr" in codes
    assert "en" in codes


def test_translate_operation_type():
    """translate_operation_type should map keys to readable names."""
    from translations import TranslationManager

    tm = TranslationManager()
    result = tm.translate_operation_type("pdf_to_word")
    assert "PDF" in result or "Word" in result


def test_translate_markdown_to_html_operation():
    from translations import TranslationManager

    tm = TranslationManager()
    for language in ("fr", "en"):
        tm.set_language(language)
        assert tm.translate_operation_type("markdown_to_html") == "Markdown → HTML"
