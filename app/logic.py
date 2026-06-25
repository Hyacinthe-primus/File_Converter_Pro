"""
app/logic.py

Contains all conversion, processing, and data-management methods of
FileConverterApp, extracted as a mixin for clarity.  Import order:

    logic.py  (AppLogicMixin)
        ↑
    ui.py     (AppUIMixin)
        ↑
    __init__.py (FileConverterApp)

"""

import sys
import os
from PySide6.QtWidgets import QDialog, QMessageBox
from PySide6.QtCore import QTimer, QRect
from PySide6.QtGui import QGuiApplication
import time

try:
    from pdf2docx import Converter as _Converter
    Converter = _Converter
except ImportError as _e:
    Converter = None
    print(f"[IMPORT] pdf2docx not available: {_e}")

from config import is_dark_mode_qt
from database import DatabaseManager
from translations import TranslationManager
from dialogs import TermsAndPrivacyDialog
from achievements import AchievementSystem
from special_events_manager import SpecialEventsManager
from system_notifier import SystemNotifier
import re as _re

def _sanitize_xml(t: str) -> str:
    """Remove control characters that break ReportLab's XML parser."""
    return _re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', t or '')

from app.mixins.optimization import OptimizationMixin
from app.mixins.image_to_pdf import ImageToPdfMixin
from app.mixins.batch import BatchMixin
from app.mixins.pdf_operations import PdfOperationsMixin
from app.mixins.pdf_to_word import PdfToWordMixin
from app.mixins.word_to_pdf import WordToPdfMixin
from app.mixins.compression import CompressionMixin

class AppLogicMixin(OptimizationMixin, ImageToPdfMixin, BatchMixin, PdfOperationsMixin, PdfToWordMixin, WordToPdfMixin, CompressionMixin):
    """Mixin: conversion engine and data logic for FileConverterApp."""

    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.config = config_manager.load_config()
        self.current_language = self.config.get("language", "fr")
        self.current_theme = self.config.get("custom_theme", None)
        if self.current_theme and self.current_theme not in ("dark", "light"):
            from theme_manager import get_custom_theme_kind
            self.dark_mode = get_custom_theme_kind(self.current_theme) == "dark"
        elif self.config.get("use_system_theme", True):
            self.dark_mode = is_dark_mode_qt()
        else:
            self.dark_mode = self.config.get("dark_mode", False)

        if not self.current_theme or self.current_theme in ("dark", "light"):
            self.current_theme = "dark" if self.dark_mode else "light"

        self.translation_manager = TranslationManager()
        self.translation_manager.set_language(self.current_language)

        self.files_list = []
        self.current_project = None
        self._project_data = {}
        self.preview_dialog = None
        self.temp_files = []

        self.terms_accepted = self.config.get("accepted_terms", False) and self.config.get("accepted_privacy", False)
        if not self.terms_accepted:
            self.show_terms_dialog()
            if not (self.config.get("accepted_terms") and self.config.get("accepted_privacy")):
                sys.exit(0)

        self.db_manager = DatabaseManager()
        self.template_settings = {}
        self.template_manager = None

        self.adv_db_manager = None
        try:
            from converter import AdvancedDatabaseManager
            self.adv_db_manager = AdvancedDatabaseManager()
        except Exception:
            pass

        self.achievement_system = AchievementSystem(self.config_manager)
        self.achievement_system.achievement_unlocked.connect(self.queue_achievement)
        self.achievement_system.rank_unlocked.connect(self.show_rank_popup)
        self.achievement_queue = []
        self.is_showing_achievement = False
        self.rank_queue = []

        self.achievement_system.record_app_launch()
        self.dashboard_dialog = None
        self.history_dialog = None
        self.templates_dialog = None
        self.achievements_dialog = None
        self.dark_mode_timer_start = None

        if self.dark_mode:
            self.dark_mode_timer_start = time.time()
        self.dark_mode_timer = QTimer()
        self.dark_mode_timer.timeout.connect(self.update_dark_mode_time)
        self.dark_mode_timer.start(60000)

        self.system_notifier = SystemNotifier(self, self.current_language)
        self.system_notifier.set_translator(self.translation_manager)

        self.setup_ui()

        _geom = self.config.get("window_geometry")
        _maximized = self.config.get("window_maximized", False)
        if _maximized:
            self.showMaximized()
        elif _geom:
            restored = QRect(
                _geom.get("x", 100),
                _geom.get("y", 100),
                _geom.get("width", 1400),
                _geom.get("height", 900),
            )
            self.setGeometry(restored)
            if not QGuiApplication.screenAt(self.geometry().center()):
                self.setGeometry(100, 100, 1400, 900)

        self.apply_theme(self.dark_mode)

        self.update_texts()
        self.special_events = SpecialEventsManager(self)
        _argv_project = None
        for _arg in sys.argv[1:]:
            if _arg.lower().endswith('.fcproj') and os.path.exists(_arg):
                _argv_project = _arg
                break

        if _argv_project:
            QTimer.singleShot(500, lambda p=_argv_project: self.open_project_file(p))
        elif self.config.get("auto_open_last_project") and self.current_project and os.path.exists(self.current_project):
            QTimer.singleShot(1000, self.open_last_project)
        if self.config.get("show_dashboard_on_startup", False):
            QTimer.singleShot(1500, self.show_dashboard)

        QTimer.singleShot(2000, self._check_donor_return)

    def _ensure_template_manager(self):
        """Initialize template_manager lazily and return it (or None on error)."""
        if self.template_manager is None:
            try:
                from templates import TemplateManager
                self.template_manager = TemplateManager(self.db_manager)
            except Exception as e:
                print(f"[WARN] Could not load TemplateManager: {e}")
        return self.template_manager

    def show_terms_dialog(self):
        dialog = TermsAndPrivacyDialog(self, self.current_language, dark_mode=self.dark_mode)
        result = dialog.exec()
        if result == QDialog.Accepted:
            from datetime import datetime
            now = datetime.now().isoformat()

            self.config["accepted_terms"] = True
            self.config["accepted_privacy"] = True

            if self.config.get("terms_acceptance_timestamp") is not None:
                self.config["terms_reacceptance_timestamp"] = now
            else:
                self.config["terms_acceptance_timestamp"] = now

            self.config_manager.save_config(self.config)
            self.terms_accepted = True
        else:
            QMessageBox.information(
                self,
                self.translate_text("Conditions requises"),
                self.translate_text("Vous devez accepter les conditions d'utilisation et la politique de confidentialité pour utiliser cette application.")
            )
            sys.exit(0)

    def closeEvent(self, event):
        """Handle app closing: save config, close DB, stop threads, clean temp files."""
        try:
            self.db_manager.close()
        except Exception:
            pass
        if hasattr(self, "_watcher"):
            try:
                self._watcher.stop()
            except Exception:
                pass
        if hasattr(self, "_scheduler"):
            try:
                self._scheduler.stop()
            except Exception:
                pass
        super().closeEvent(event)

    def cleanup_temp_files(self):
        """Clean up temporary files"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    print(f"[DEBUG] Temporary file deleted: {temp_file}")
            except Exception as e:
                print(f"[ERROR] Could not delete temporary file {temp_file}: {e}")
        self.temp_files.clear()

    def create_temp_file(self, suffix=".tmp"):
        import tempfile
        fd, path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
        self.temp_files.append(path)
        return path

    def clear_file_list(self):
        """Clear the file list (alias for clear_files)"""
        self.clear_files()

