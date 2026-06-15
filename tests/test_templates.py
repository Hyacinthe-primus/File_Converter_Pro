"""Tests for template system — TemplateManager CRUD and template dialog imports."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestTemplateManager:
    def test_import(self):
        from templates.template_manager import TemplateManager
        assert TemplateManager is not None

    def test_normalize_type_english_to_french(self):
        from templates.template_manager import TemplateManager
        assert TemplateManager.normalize_type("PDF to Word Conversion") == "Conversion PDF→Word"
        assert TemplateManager.normalize_type("Quality Presets") == "Optimisation de fichiers"

    def test_normalize_type_passthrough(self):
        from templates.template_manager import TemplateManager
        assert TemplateManager.normalize_type("Compression") == "Compression"
        assert TemplateManager.normalize_type("Division PDF") == "Division PDF"

    def test_manager_init(self):
        from templates.template_manager import TemplateManager
        from database import DatabaseManager
        db = DatabaseManager()
        tm = TemplateManager(db)
        assert tm is not None
        assert hasattr(tm, 'current_templates')

    def test_get_templates_empty(self):
        from templates.template_manager import TemplateManager
        from database import DatabaseManager
        db = DatabaseManager()
        tm = TemplateManager(db)
        templates = tm.get_templates_by_type("pdf_to_word")
        assert isinstance(templates, dict)


class TestCreateTemplateDialog:
    def test_import(self):
        from templates.create_template_dialog import CreateTemplateDialog
        assert CreateTemplateDialog is not None


class TestTemplateEditorDialog:
    def test_import(self):
        from templates.template_editor_dialog import TemplateEditorDialog
        assert TemplateEditorDialog is not None


class TestEnhancedTemplatesDialog:
    def test_import(self):
        from templates.templates import EnhancedTemplatesDialog
        assert EnhancedTemplatesDialog is not None

    def test_inherits_translation_mixin(self):
        from templates.templates import EnhancedTemplatesDialog
        from utils.translation_mixin import TranslationMixin
        assert issubclass(EnhancedTemplatesDialog, TranslationMixin)


class TestTemplateCRUD:
    def test_save_and_get_template(self):
        from templates.template_manager import TemplateManager
        from database import DatabaseManager
        db = DatabaseManager()
        tm = TemplateManager(db)
        config = {"mode": "preserve_all", "quality": "Standard"}
        db.save_template("Test Template", "Conversion Word→PDF", config)
        tm.load_templates()
        templates = tm.get_templates_by_type("Conversion Word→PDF")
        assert len(templates) >= 1

    def test_delete_template(self):
        from templates.template_manager import TemplateManager
        from database import DatabaseManager
        db = DatabaseManager()
        tm = TemplateManager(db)
        config = {"mode": "text_only"}
        db.save_template("To Delete", "Compression", config)
        tm.load_templates()
        templates = tm.get_templates_by_type("Compression")
        tid = list(templates.keys())[0] if templates else None
        if tid:
            tm.delete_template(tid)
            tm.load_templates()
            templates_after = tm.get_templates_by_type("Compression")
            assert tid not in templates_after
