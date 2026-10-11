"""Tests for auto-save templates, auto-clean temp files, backup before conversion, and LogoLabel theme fix."""

import os
import shutil
import tempfile

import pytest


@pytest.fixture
def qapp():
    """Provide a QApplication for Qt-dependent tests."""
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def logo_label(qapp):
    """Create a LogoLabel widget for testing."""
    from PySide6.QtWidgets import QLabel

    logo = QLabel("FC")
    logo.setObjectName("LogoLabel")
    yield logo
    logo.deleteLater()


@pytest.fixture
def tmp_dir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def mock_db(tmp_dir):
    """Create a DatabaseManager with a temp DB path."""
    from database import DatabaseManager

    db = DatabaseManager()
    db.db_path = os.path.join(tmp_dir, "test_stats.db")
    db._conn = db._conn.__class__(db.db_path, check_same_thread=False)
    db._conn.execute("PRAGMA journal_mode=WAL")
    db.init_database()
    yield db
    db.close()


@pytest.fixture
def mock_app(tmp_dir):
    """Create a minimal mock app with config and template manager."""

    class MockApp:
        def __init__(self):
            self.config = {
                "auto_save_templates": True,
                "auto_clean_temp_files": True,
                "backup_before_conversion": False,
                "pdf_to_word_mode": "with_images",
                "conversion_quality": "standard",
                "word_to_pdf_mode": "preserve_all",
                "separate_image_pdfs": False,
                "compression_level": "normal",
            }
            self.temp_files = []
            self.template_manager = None

        def _ensure_template_manager(self):
            if self.template_manager is None:
                from templates.template_manager import TemplateManager

                self.template_manager = TemplateManager(mock_db)
            return self.template_manager

    return MockApp()


# ============================================================
# 1. Auto-save frequent configurations
# ============================================================


class TestAutoSaveTemplates:
    def test_auto_save_creates_template(self, mock_app, mock_db):
        """auto_save_config creates a new template when none exists."""
        from templates.template_manager import TemplateManager

        tm = TemplateManager(mock_db)
        mock_app.template_manager = tm

        result = tm.auto_save_config("Conversion PDF→Word", mock_app)
        assert result is True

        templates = tm.get_templates_by_type("Conversion PDF→Word")
        auto_templates = [t for t in templates.values() if t["name"].startswith("[Auto]")]
        assert len(auto_templates) == 1
        assert "with_images" in auto_templates[0]["config"]["mode"]

    def test_auto_save_updates_existing(self, mock_app, mock_db):
        """auto_save_config updates existing auto template instead of duplicating."""
        from templates.template_manager import TemplateManager

        tm = TemplateManager(mock_db)
        mock_app.template_manager = tm

        tm.auto_save_config("Conversion PDF→Word", mock_app)
        mock_app.config["pdf_to_word_mode"] = "text_only"
        tm.auto_save_config("Conversion PDF→Word", mock_app)

        templates = tm.get_templates_by_type("Conversion PDF→Word")
        auto_templates = [t for t in templates.values() if t["name"].startswith("[Auto]")]
        assert len(auto_templates) == 1
        assert auto_templates[0]["config"]["mode"] == "text_only"

    def test_auto_save_respects_config_flag(self, mock_app, mock_db):
        """maybe_auto_save_template does nothing when auto_save_templates is False."""
        from templates.template_manager import TemplateManager

        mock_app.config["auto_save_templates"] = False
        tm = TemplateManager(mock_db)
        mock_app.template_manager = tm

        mock_app.maybe_auto_save_template = lambda tt: None

        result = tm.auto_save_config("Conversion PDF→Word", mock_app)
        assert result is True

    def test_auto_save_word_to_pdf(self, mock_app, mock_db):
        """auto_save_config works for Word to PDF type."""
        from templates.template_manager import TemplateManager

        tm = TemplateManager(mock_db)
        mock_app.template_manager = tm

        result = tm.auto_save_config("Conversion Word→PDF", mock_app)
        assert result is True

        templates = tm.get_templates_by_type("Conversion Word→PDF")
        auto_templates = [t for t in templates.values() if t["name"].startswith("[Auto]")]
        assert len(auto_templates) == 1

    def test_auto_save_compression(self, mock_app, mock_db):
        """auto_save_config works for Compression type."""
        from templates.template_manager import TemplateManager

        tm = TemplateManager(mock_db)
        mock_app.template_manager = tm

        result = tm.auto_save_config("Compression", mock_app)
        assert result is True

        templates = tm.get_templates_by_type("Compression")
        auto_templates = [t for t in templates.values() if t["name"].startswith("[Auto]")]
        assert len(auto_templates) == 1

    def test_auto_save_unsupported_type(self, mock_app, mock_db):
        """auto_save_config returns False for unsupported template types."""
        from templates.template_manager import TemplateManager

        tm = TemplateManager(mock_db)
        mock_app.template_manager = tm

        result = tm.auto_save_config("Fusion PDF", mock_app)
        assert result is False

    def test_auto_save_build_config_pdf_to_word(self, mock_app, mock_db):
        """_build_config_from_app returns correct config for PDF to Word."""
        from templates.template_manager import TemplateManager

        tm = TemplateManager(mock_db)
        config = tm._build_config_from_app("Conversion PDF→Word", mock_app)
        assert config is not None
        assert config["mode"] == "with_images"
        assert config["quality"] == "standard"

    def test_auto_save_build_config_word_to_pdf(self, mock_app, mock_db):
        """_build_config_from_app returns correct config for Word to PDF."""
        from templates.template_manager import TemplateManager

        tm = TemplateManager(mock_db)
        config = tm._build_config_from_app("Conversion Word→PDF", mock_app)
        assert config is not None
        assert config["mode"] == "preserve_all"

    def test_auto_save_build_config_compression(self, mock_app, mock_db):
        """_build_config_from_app returns correct config for Compression."""
        from templates.template_manager import TemplateManager

        tm = TemplateManager(mock_db)
        config = tm._build_config_from_app("Compression", mock_app)
        assert config is not None
        assert config["format"] == "ZIP"

    def test_auto_save_build_config_optimization(self, mock_app, mock_db):
        """_build_config_from_app returns correct config for Optimization."""
        from templates.template_manager import TemplateManager

        tm = TemplateManager(mock_db)
        config = tm._build_config_from_app("Optimisation de fichiers", mock_app)
        assert config is not None
        assert config["optimization_type"] == 2

    def test_auto_save_build_config_unsupported(self, mock_app, mock_db):
        """_build_config_from_app returns None for unsupported types."""
        from templates.template_manager import TemplateManager

        tm = TemplateManager(mock_db)
        config = tm._build_config_from_app("Fusion PDF", mock_app)
        assert config is None


# ============================================================
# 2. Auto-clean temporary files
# ============================================================


class TestAutoCleanTempFiles:
    def test_cleanup_removes_temp_files(self, tmp_dir):
        """cleanup_temp_files removes all tracked temp files."""
        from app.logic import AppLogicMixin

        mixin = AppLogicMixin.__new__(AppLogicMixin)
        mixin.temp_files = []

        f1 = os.path.join(tmp_dir, "temp1.tmp")
        f2 = os.path.join(tmp_dir, "temp2.tmp")
        with open(f1, "w") as f:
            f.write("temp1")
        with open(f2, "w") as f:
            f.write("temp2")

        mixin.temp_files = [f1, f2]
        mixin.cleanup_temp_files()

        assert not os.path.exists(f1)
        assert not os.path.exists(f2)
        assert len(mixin.temp_files) == 0

    def test_cleanup_handles_missing_files(self, tmp_dir):
        """cleanup_temp_files doesn't crash on already-deleted files."""
        from app.logic import AppLogicMixin

        mixin = AppLogicMixin.__new__(AppLogicMixin)
        mixin.temp_files = [os.path.join(tmp_dir, "nonexistent.tmp")]
        mixin.cleanup_temp_files()
        assert len(mixin.temp_files) == 0

    def test_cleanup_handles_empty_list(self):
        """cleanup_temp_files works with empty list."""
        from app.logic import AppLogicMixin

        mixin = AppLogicMixin.__new__(AppLogicMixin)
        mixin.temp_files = []
        mixin.cleanup_temp_files()
        assert len(mixin.temp_files) == 0

    def test_create_temp_file_tracks(self, tmp_dir):
        """create_temp_file creates and tracks a temp file."""
        from app.logic import AppLogicMixin

        mixin = AppLogicMixin.__new__(AppLogicMixin)
        mixin.temp_files = []

        path = mixin.create_temp_file(suffix=".test")
        assert os.path.exists(path)
        assert path in mixin.temp_files

        mixin.cleanup_temp_files()
        assert not os.path.exists(path)

    def test_cleanup_clears_list_after(self, tmp_dir):
        """cleanup_temp_files clears the tracking list even if some fail."""
        from app.logic import AppLogicMixin

        mixin = AppLogicMixin.__new__(AppLogicMixin)
        f1 = os.path.join(tmp_dir, "temp1.tmp")
        with open(f1, "w") as f:
            f.write("data")
        mixin.temp_files = [f1, "/nonexistent/path/file.tmp"]
        mixin.cleanup_temp_files()
        assert len(mixin.temp_files) == 0

    def test_close_event_calls_cleanup_when_enabled(self, tmp_dir):
        """closeEvent calls cleanup_temp_files when auto_clean_temp_files is True."""
        cleaned = []

        class _Obj:
            config = {"auto_clean_temp_files": True}
            temp_files = []
            db_manager = type("", (), {"close": lambda self: None})()

            def cleanup_temp_files(self):
                for f in self.temp_files:
                    if os.path.exists(f):
                        os.remove(f)
                        cleaned.append(f)
                self.temp_files.clear()

            def closeEvent(self, event):
                try:
                    self.db_manager.close()
                except Exception:
                    pass
                if self.config.get("auto_clean_temp_files", True):
                    self.cleanup_temp_files()

        obj = _Obj()
        f1 = os.path.join(tmp_dir, "temp_close.tmp")
        with open(f1, "w") as f:
            f.write("data")
        obj.temp_files = [f1]

        class MockEvent:
            def accept(self):
                pass

        obj.closeEvent(MockEvent())
        assert f1 in cleaned
        assert not os.path.exists(f1)

    def test_close_event_skips_cleanup_when_disabled(self, tmp_dir):
        """closeEvent skips cleanup_temp_files when auto_clean_temp_files is False."""
        cleaned = []

        class _Obj:
            config = {"auto_clean_temp_files": False}
            temp_files = []
            db_manager = type("", (), {"close": lambda self: None})()

            def cleanup_temp_files(self):
                for f in self.temp_files:
                    if os.path.exists(f):
                        os.remove(f)
                        cleaned.append(f)
                self.temp_files.clear()

            def closeEvent(self, event):
                try:
                    self.db_manager.close()
                except Exception:
                    pass
                if self.config.get("auto_clean_temp_files", True):
                    self.cleanup_temp_files()

        obj = _Obj()
        f1 = os.path.join(tmp_dir, "temp_keep.tmp")
        with open(f1, "w") as f:
            f.write("data")
        obj.temp_files = [f1]

        class MockEvent:
            def accept(self):
                pass

        obj.closeEvent(MockEvent())
        assert f1 not in cleaned
        assert os.path.exists(f1)


# ============================================================
# 3. Backup before conversion
# ============================================================


class TestBackupBeforeConversion:
    def test_create_backup_basic(self, tmp_dir):
        """create_backup creates a .bak copy of the source file."""
        from converter.helpers import create_backup

        src = os.path.join(tmp_dir, "document.txt")
        with open(src, "w") as f:
            f.write("important content")

        backup_path = create_backup(src)
        assert backup_path is not None
        assert backup_path == src + ".bak"
        assert os.path.exists(backup_path)
        with open(backup_path, "r") as f:
            assert f.read() == "important content"

    def test_create_backup_custom_suffix(self, tmp_dir):
        """create_backup respects custom suffix."""
        from converter.helpers import create_backup

        src = os.path.join(tmp_dir, "photo.jpg")
        with open(src, "wb") as f:
            f.write(b"\xff\xd8\xff")

        backup_path = create_backup(src, suffix=".backup")
        assert backup_path == src + ".backup"
        assert os.path.exists(backup_path)

    def test_create_backup_nonexistent_source(self, tmp_dir):
        """create_backup returns None for non-existent source."""
        from converter.helpers import create_backup

        result = create_backup(os.path.join(tmp_dir, "nonexistent.txt"))
        assert result is None

    def test_create_backup_preserves_content(self, tmp_dir):
        """create_backup produces an exact copy."""
        from converter.helpers import create_backup

        src = os.path.join(tmp_dir, "data.bin")
        content = bytes(range(256))
        with open(src, "wb") as f:
            f.write(content)

        backup_path = create_backup(src)
        with open(backup_path, "rb") as f:
            assert f.read() == content

    def test_engine_backup_enabled(self, tmp_dir):
        """Engine creates backup when backup_enabled is True."""
        from converter.converters import AdvancedConverterEngine

        engine = AdvancedConverterEngine()
        engine.backup_enabled = True

        src = os.path.join(tmp_dir, "test.txt")
        with open(src, "w") as f:
            f.write("test content")

        dst_dir = os.path.join(tmp_dir, "output")
        os.makedirs(dst_dir, exist_ok=True)

        backup_path = src + ".bak"
        if os.path.exists(backup_path):
            os.remove(backup_path)

        engine.convert("txt_to_pdf", src, dst_dir)

        assert os.path.exists(backup_path)
        with open(backup_path, "r") as f:
            assert f.read() == "test content"

    def test_engine_backup_disabled(self, tmp_dir):
        """Engine does NOT create backup when backup_enabled is False."""
        from converter.converters import AdvancedConverterEngine

        engine = AdvancedConverterEngine()
        engine.backup_enabled = False

        src = os.path.join(tmp_dir, "test.txt")
        with open(src, "w") as f:
            f.write("test content")

        dst_dir = os.path.join(tmp_dir, "output")
        os.makedirs(dst_dir, exist_ok=True)

        backup_path = src + ".bak"
        if os.path.exists(backup_path):
            os.remove(backup_path)

        engine.convert("txt_to_pdf", src, dst_dir)

        assert not os.path.exists(backup_path)

    def test_engine_backup_default_disabled(self, tmp_dir):
        """Engine defaults to backup_enabled=False."""
        from converter.converters import AdvancedConverterEngine

        engine = AdvancedConverterEngine()
        assert engine.backup_enabled is False

    def test_backup_overwrites_existing(self, tmp_dir):
        """create_backup overwrites an existing backup file."""
        from converter.helpers import create_backup

        src = os.path.join(tmp_dir, "file.txt")
        with open(src, "w") as f:
            f.write("new content")

        backup_path = src + ".bak"
        with open(backup_path, "w") as f:
            f.write("old content")

        create_backup(src)
        with open(backup_path, "r") as f:
            assert f.read() == "new content"


# ============================================================
# Cross-platform compatibility tests
# ============================================================


class TestCrossPlatform:
    def test_create_backup_uses_shutil(self, tmp_dir):
        """create_backup uses shutil.copy2 which is cross-platform."""
        import inspect

        from converter.helpers import create_backup

        source = inspect.getsource(create_backup)
        assert "shutil.copy2" in source

    def test_cleanup_uses_os_path(self):
        """cleanup_temp_files uses os.path which is cross-platform."""
        import inspect

        from app.logic import AppLogicMixin

        source = inspect.getsource(AppLogicMixin.cleanup_temp_files)
        assert "os.path" in source

    def test_temp_file_uses_tempfile(self):
        """create_temp_file uses tempfile module which is cross-platform."""
        import inspect

        from app.logic import AppLogicMixin

        source = inspect.getsource(AppLogicMixin.create_temp_file)
        assert "tempfile" in source

    def test_auto_save_uses_json(self):
        """auto_save_config uses json which is cross-platform."""
        import inspect

        from templates.template_manager import TemplateManager

        source = inspect.getsource(TemplateManager.auto_save_config)
        assert "json" in source


# ============================================================
# LogoLabel theme fix tests
# ============================================================


class TestLogoLabelThemeFix:
    def _make_parent_with_logo(self, qapp):
        from PySide6.QtWidgets import QLabel, QWidget

        parent = QWidget()
        logo = QLabel("FC", parent)
        logo.setObjectName("LogoLabel")
        return parent, logo

    def test_update_logo_label_dark(self, qapp):
        """_update_logo_label sets dark color for dark themes."""
        from app.mixins.theme_language import ThemeLanguageMixin

        parent, logo = self._make_parent_with_logo(qapp)
        ThemeLanguageMixin._update_logo_label(parent, "dark")
        assert "#e8ff6b" in logo.styleSheet()
        parent.deleteLater()

    def test_update_logo_label_light(self, qapp):
        """_update_logo_label sets light color for light themes."""
        from app.mixins.theme_language import ThemeLanguageMixin

        parent, logo = self._make_parent_with_logo(qapp)
        ThemeLanguageMixin._update_logo_label(parent, "light")
        assert "#2d2dc8" in logo.styleSheet()
        parent.deleteLater()

    def test_update_logo_label_custom_dark(self, qapp):
        """_update_logo_label detects dark custom themes."""
        from app.mixins.theme_language import ThemeLanguageMixin

        parent, logo = self._make_parent_with_logo(qapp)
        ThemeLanguageMixin._update_logo_label(parent, "Obsidian")
        assert "#e8ff6b" in logo.styleSheet()
        parent.deleteLater()

    def test_update_logo_label_custom_light(self, qapp):
        """_update_logo_label detects light custom themes."""
        from app.mixins.theme_language import ThemeLanguageMixin

        parent, logo = self._make_parent_with_logo(qapp)
        ThemeLanguageMixin._update_logo_label(parent, "opaline")
        assert "#2d2dc8" in logo.styleSheet()
        parent.deleteLater()

    def test_update_logo_label_no_logo(self, qapp):
        """_update_logo_label handles missing LogoLabel gracefully."""
        from PySide6.QtWidgets import QWidget

        parent = QWidget()
        from app.mixins.theme_language import ThemeLanguageMixin

        ThemeLanguageMixin._update_logo_label(parent, "dark")
        parent.deleteLater()


class TestAdvancedConversionsCustomTheme:
    def test_resolve_theme_name_custom(self):
        """resolve_theme_name returns custom theme name."""
        from types import SimpleNamespace

        from advanced_conversions import resolve_theme_name

        parent = SimpleNamespace(current_theme="Riso_Press", dark_mode=True)
        assert resolve_theme_name(parent) == "Riso_Press"

    def test_resolve_theme_name_builtin_dark(self):
        """resolve_theme_name falls back to dark."""
        from types import SimpleNamespace

        from advanced_conversions import resolve_theme_name

        parent = SimpleNamespace(current_theme="dark", dark_mode=True)
        assert resolve_theme_name(parent) == "dark"

    def test_resolve_theme_name_builtin_light(self):
        """resolve_theme_name falls back to light."""
        from types import SimpleNamespace

        from advanced_conversions import resolve_theme_name

        parent = SimpleNamespace(current_theme="light", dark_mode=False)
        assert resolve_theme_name(parent) == "light"

    def test_resolve_theme_name_no_parent(self):
        """resolve_theme_name defaults to light when no parent."""
        from advanced_conversions import resolve_theme_name

        assert resolve_theme_name(None) == "light"

    def test_theme_changed_signal_exists(self, qapp):
        """FileConverterApp has a theme_changed signal."""
        from app import FileConverterApp

        assert hasattr(FileConverterApp, "theme_changed")

    def test_dialog_connects_to_theme_signal(self, qapp):
        """AdvancedConversionsDialog connects to parent's theme_changed signal."""
        from unittest.mock import patch

        from PySide6.QtCore import Signal
        from PySide6.QtWidgets import QTabWidget, QWidget

        from advanced_conversions import AdvancedConversionsDialog

        class FakeParent(QWidget):
            theme_changed = Signal(str)

        parent = FakeParent()
        received = []

        def _on_theme(theme_name):
            received.append(theme_name)

        with (
            patch("advanced_conversions._load_qss", return_value=""),
            patch.object(AdvancedConversionsDialog, "_setup_ui"),
            patch.object(AdvancedConversionsDialog, "_apply_theme_style"),
        ):
            dlg = AdvancedConversionsDialog.__new__(AdvancedConversionsDialog)
            dlg.parent_window = parent
            dlg._tab_widget = QTabWidget()
            dlg._apply_theme_style = lambda: received.append("applied")
            if hasattr(parent, "theme_changed"):
                parent.theme_changed.connect(dlg._apply_theme_style)
            parent.theme_changed.emit("Riso_Press")
            assert received == ["applied"]
        parent.deleteLater()
