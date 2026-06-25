"""SettingsDialog — Application preferences and configuration (multi-tab)."""

import sys
from pathlib import Path
from datetime import datetime

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QWidget,
                               QGroupBox, QFormLayout, QComboBox, QSpinBox,
                               QLineEdit, QPushButton, QTabWidget, QFrame,
                               QScrollArea, QLabel, QFileDialog, QMessageBox,
                               QDialogButtonBox)
from PySide6.QtCore import Qt, QTimer, QCoreApplication
from qss_helpers import _load_qss, _apply_dialog_btn, get_current_theme
from widgets import AnimatedCheckBox
from .terms_dialog import TermsAndPrivacyDialog

from utils import make_tm
from utils.translation_mixin import TranslationMixin
from theme_manager import (get_custom_themes, get_builtin_themes,
                           import_theme, remove_theme, CUSTOM_THEMES_DIR)
from PySide6.QtGui import QPixmap, QImage


class SettingsDialog(TranslationMixin, QDialog):
    def __init__(self, config, parent=None, language="fr"):
        super().__init__(parent)
        self.config = config
        self.language = language
        self._tm = make_tm(language)
        self.setWindowTitle(self.translate_text("Paramètres de l'application"))
        self.setModal(True)
        self.setMinimumSize(650, 550)
        self.setMaximumHeight(700)
        self.setup_ui()

    def setup_ui(self):

        ok_button_style = """
        QPushButton {
            background-color: #10B981;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-weight: bold;
        }
        QPushButton:hover { background-color: #059669; }
        QPushButton:pressed { background-color: #047857; }
        """

        browse_button_style = """
        QPushButton {
            background-color: #374151;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-weight: bold;
        }
        QPushButton:hover { background-color: #4B5563; }
        QPushButton:pressed { background-color: #1F2937; }
        """

        cancel_button_style = """
        QPushButton {
            background-color: transparent;
            color: #6B7280;
            border: 1px solid #D1D5DB;
            padding: 8px 16px;
            border-radius: 6px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #F3F4F6;
            color: #4B5563;
            border-color: #9CA3AF;
        }
        QPushButton:pressed {
            background-color: #E5E7EB;
            color: #1F2937;
        }
        """

        restore_button_style = """
        QPushButton {
            background-color: transparent;
            color: #EF4444;
            border: 1px solid #EF4444;
            padding: 8px 16px;
            border-radius: 6px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #FEF2F2;
            border-color: #DC2626;
            color: #DC2626;
        }
        QPushButton:pressed {
            background-color: #FEE2E2;
            color: #B91C1C;
            border-color: #B91C1C;
        }
        """

        main_layout = QVBoxLayout(self)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QFrame.NoFrame)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(5, 5, 5, 5)
        content_layout.setSpacing(10)

        self.tab_widget = QTabWidget()

        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        general_layout.setContentsMargins(5, 5, 5, 5)
        general_layout.setSpacing(15)

        interface_group = QGroupBox(self.translate_text("Interface"))
        interface_layout = QFormLayout(interface_group)
        interface_layout.setVerticalSpacing(10)

        self.auto_open_checkbox = AnimatedCheckBox(self.translate_text("Ouvrir automatiquement le dernier projet au démarrage"))
        self.auto_open_checkbox.setChecked(self.config.get("auto_open_last_project", False))

        self.notifications_checkbox = AnimatedCheckBox(self.translate_text("Activer les notifications"))
        self.notifications_checkbox.setChecked(self.config.get("enable_notifications", True))

        self.system_notifications_checkbox = AnimatedCheckBox(self.translate_text("Activer les notifications système"))
        self.system_notifications_checkbox.setChecked(self.config.get("enable_system_notifications", True))

        self.achievements_checkbox = AnimatedCheckBox(self.translate_text("Activer les succès et réalisations"))
        self.achievements_checkbox.setChecked(self.config.get("achievements_enabled", True))

        self.show_previews_checkbox = AnimatedCheckBox(self.translate_text("Afficher les aperçus des fichiers"))
        self.show_previews_checkbox.setChecked(self.config.get("show_file_previews", True))

        self.show_dashboard_checkbox = AnimatedCheckBox(self.translate_text("Afficher le tableau de bord au démarrage"))
        self.show_dashboard_checkbox.setChecked(self.config.get("show_dashboard_on_startup", True))

        self.separate_image_pdfs_checkbox = AnimatedCheckBox(self.translate_text("Créer un PDF séparé par image (au lieu de fusionner)"))
        self.separate_image_pdfs_checkbox.setChecked(self.config.get("separate_image_pdfs", False))

        interface_layout.addRow(self.auto_open_checkbox)
        interface_layout.addRow(self.notifications_checkbox)
        interface_layout.addRow(self.system_notifications_checkbox)
        interface_layout.addRow(self.achievements_checkbox)
        interface_layout.addRow(self.show_previews_checkbox)
        interface_layout.addRow(self.show_dashboard_checkbox)
        interface_layout.addRow(self.separate_image_pdfs_checkbox)

        self.use_system_theme_checkbox = AnimatedCheckBox(self.translate_text("Utiliser le thème système"))
        self.use_system_theme_checkbox.setChecked(self.config.get("use_system_theme", True))
        interface_layout.addRow(self.use_system_theme_checkbox)

        conversion_group = QGroupBox(self.translate_text("Conversion"))
        conversion_layout = QFormLayout(conversion_group)
        conversion_layout.setVerticalSpacing(12)
        conversion_layout.setHorizontalSpacing(15)

        self.quality_combo = QComboBox()
        self.quality_combo.addItems([
            self.translate_text("Haute qualité"),
            self.translate_text("Qualité standard"),
            self.translate_text("Compressé")
        ])
        quality_map = {"high": 0, "standard": 1, "compressed": 2}
        current_quality = self.config.get("conversion_quality", "standard")
        self.quality_combo.setCurrentIndex(quality_map.get(current_quality, 1))

        self.compression_level_combo = QComboBox()
        self.compression_level_combo.addItems([
            self.translate_text("Normal"),
            self.translate_text("Haute compression"),
            self.translate_text("Compression maximale")
        ])
        compression_map = {"normal": 0, "high": 1, "maximum": 2}
        current_compression = self.config.get("compression_level", "normal")
        self.compression_level_combo.setCurrentIndex(compression_map.get(current_compression, 0))

        self.pdf_to_word_mode_combo = QComboBox()
        self.pdf_to_word_mode_combo.addItems([
            self.translate_text("Conserver les images et la mise en page"),
            self.translate_text("Texte brut uniquement"),
            self.translate_text("Texte complet (texte + texte des images)")
        ])
        mode_map = {"with_images": 0, "text_only": 1, "text_with_image_text": 2}
        current_mode = self.config.get("pdf_to_word_mode", "with_images")
        self.pdf_to_word_mode_combo.setCurrentIndex(mode_map.get(current_mode, 0))

        self.default_output_input = QLineEdit()
        self.default_output_input.setText(self.config.get("default_output_folder", ""))
        self.browse_btn = QPushButton(self.translate_text("Parcourir"))
        self.browse_btn.setStyleSheet(browse_button_style)
        self.browse_btn.clicked.connect(self.browse_output_folder)

        output_layout = QHBoxLayout()
        output_layout.addWidget(self.default_output_input, 3)
        output_layout.addWidget(self.browse_btn, 1)
        output_layout.setSpacing(10)

        self.auto_clean_checkbox = AnimatedCheckBox(self.translate_text("Nettoyer automatiquement les fichiers temporaires"))
        self.auto_clean_checkbox.setChecked(self.config.get("auto_clean_temp_files", True))

        self.backup_checkbox = AnimatedCheckBox(self.translate_text("Créer une sauvegarde avant conversion"))
        self.backup_checkbox.setChecked(self.config.get("backup_before_conversion", False))

        self.keep_history_days_spin = QSpinBox()
        self.keep_history_days_spin.setRange(1, 3650)
        self.keep_history_days_spin.setValue(self.config.get("keep_history_days", 365))

        self.auto_save_templates_check = AnimatedCheckBox(self.translate_text("Sauvegarder automatiquement les configurations fréquentes"))
        self.auto_save_templates_check.setChecked(self.config.get("auto_save_templates", True))

        conversion_layout.addRow(self.translate_text("Qualité par défaut:"), self.quality_combo)
        conversion_layout.addRow(self.translate_text("Niveau compression:"), self.compression_level_combo)
        conversion_layout.addRow(self.translate_text("Mode PDF→Word:"), self.pdf_to_word_mode_combo)
        conversion_layout.addRow(self.translate_text("Dossier de sortie par défaut:"), output_layout)
        conversion_layout.addRow(self.translate_text("Conserver l'historique (jours):"), self.keep_history_days_spin)
        conversion_layout.addRow(self.auto_clean_checkbox)
        conversion_layout.addRow(self.backup_checkbox)
        conversion_layout.addRow(self.auto_save_templates_check)

        conversion_group.setMaximumHeight(400)

        general_layout.addWidget(interface_group)
        general_layout.addWidget(conversion_group)
        general_layout.addStretch()

        privacy_tab = QWidget()
        privacy_layout = QVBoxLayout(privacy_tab)
        privacy_layout.setContentsMargins(5, 5, 5, 5)
        privacy_layout.setSpacing(15)

        privacy_group = QGroupBox(self.translate_text("Confidentialité et Conditions"))
        privacy_group_layout = QVBoxLayout(privacy_group)
        privacy_group_layout.setSpacing(10)

        self.view_terms_btn = QPushButton("📄 " + self.translate_text("Voir les Conditions d'utilisation"))
        self.view_terms_btn.setMinimumHeight(33)
        self.view_privacy_btn = QPushButton("🔒 " + self.translate_text("Voir la Politique de confidentialité"))
        self.view_privacy_btn.setMinimumHeight(33)

        privacy_group_layout.addWidget(self.view_terms_btn)
        privacy_group_layout.addWidget(self.view_privacy_btn)

        privacy_layout.addWidget(privacy_group)
        privacy_layout.addStretch()

        self.tab_widget.addTab(general_tab,  self.translate_text("Général"))
        self.tab_widget.addTab(self._build_automation_tab(), self.translate_text("Automatisation"))
        self.tab_widget.addTab(privacy_tab,  self.translate_text("Confidentialité"))
        self.tab_widget.addTab(self._build_language_tab(), self.translate_text("Langue"))
        self.tab_widget.addTab(self._build_theme_tab(), self.translate_text("Thème"))

        content_layout.addWidget(self.tab_widget)

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

        ok_btn = QPushButton(self.translate_text("OK"))
        ok_btn.setStyleSheet(ok_button_style)
        cancel_btn = QPushButton(self.translate_text("Annuler"))
        cancel_btn.setStyleSheet(cancel_button_style)
        restore_btn = QPushButton(self.translate_text("Restaurer les paramètres par défaut"))
        restore_btn.setStyleSheet(restore_button_style)

        buttons = QDialogButtonBox()
        buttons.addButton(ok_btn, QDialogButtonBox.AcceptRole)
        buttons.addButton(cancel_btn, QDialogButtonBox.RejectRole)
        buttons.addButton(restore_btn, QDialogButtonBox.ResetRole)

        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        restore_btn.clicked.connect(self.restore_defaults)

        main_layout.addWidget(buttons)

        self.view_terms_btn.clicked.connect(self.show_terms)
        self.view_privacy_btn.clicked.connect(self.show_privacy)

        self.apply_scrollbar_style()

    def apply_scrollbar_style(self):
        dark = hasattr(self.parent(), 'dark_mode') and self.parent().dark_mode
        self.setStyleSheet(self.styleSheet() + _load_qss("scrollbar.qss", get_current_theme(dark)))

    def _lang_is_dark(self) -> bool:
        """Return True if the parent app is currently in dark mode."""
        p = self.parent()
        return bool(getattr(p, "dark_mode", False))

    def _build_language_tab(self) -> QWidget:
        """Build the Language settings tab with installed-language list + import."""
        dark = self._lang_is_dark()

        tab_bg        = "#0d1117" if dark else "#f8f9fa"
        group_bg      = "#161b22" if dark else "#ffffff"
        scroll_bg     = "#161b22" if dark else "#ffffff"
        text_primary  = "#e6edf3" if dark else "#1c2526"
        text_muted    = "#8b949e" if dark else "#6b7280"
        group_border  = "#30363d" if dark else "#dee2e6"
        active_green  = "#3fb950" if dark else "#10B981"

        tab = QWidget()
        tab.setStyleSheet(f"background-color: {tab_bg};")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 10, 8, 10)
        layout.setSpacing(12)

        active_row = QHBoxLayout()
        active_lbl_title = QLabel(self.translate_text("Langue active:"))
        active_lbl_title.setStyleSheet(f"color: {text_primary}; font-size: 12px;")
        active_row.addWidget(active_lbl_title)
        self._lang_active_lbl = QLabel()
        self._lang_active_lbl.setStyleSheet(
            f"font-weight: bold; font-size: 13px; color: {active_green};"
        )
        active_row.addWidget(self._lang_active_lbl)
        active_row.addStretch()
        layout.addLayout(active_row)

        list_group = QGroupBox(self.translate_text("Langues installées"))
        list_group.setStyleSheet(f"""
            QGroupBox {{
                color: {text_muted};
                background-color: {group_bg};
                border: 1px solid {group_border};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                font-size: 11px;
                font-weight: 600;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 6px;
                color: {text_muted};
            }}
        """)
        list_layout = QVBoxLayout(list_group)
        list_layout.setSpacing(6)
        list_layout.setContentsMargins(8, 8, 8, 8)

        self._lang_list = QScrollArea()
        self._lang_list.setWidgetResizable(True)
        self._lang_list.setFrameShape(QFrame.NoFrame)
        self._lang_list.setMinimumHeight(185)
        self._lang_list.setStyleSheet(_load_qss("lang_scroll.qss", "dark" if dark else "light"))
        self._lang_inner = QWidget()
        self._lang_inner.setStyleSheet(f"background: {scroll_bg};")
        self._lang_inner_layout = QVBoxLayout(self._lang_inner)
        self._lang_inner_layout.setSpacing(6)
        self._lang_inner_layout.setContentsMargins(4, 4, 4, 4)
        self._lang_list.setWidget(self._lang_inner)
        list_layout.addWidget(self._lang_list)
        layout.addWidget(list_group)

        import_btn = QPushButton("📥 " + self.translate_text("Importer un fichier .lang"))
        import_btn.setMinimumHeight(36)
        _apply_dialog_btn(import_btn, "BtnIndigo")
        import_btn.clicked.connect(self._import_lang_file)
        layout.addWidget(import_btn)

        hint = QLabel("ℹ️ " + self.translate_text("lang_restart_hint"))
        hint.setWordWrap(True)
        hint.setStyleSheet(
            f"color: {text_muted}; font-size: 10px; font-style: italic;"
        )
        layout.addWidget(hint)
        layout.addStretch()

        self._refresh_lang_list()
        return tab

    def _refresh_lang_list(self) -> None:
        """Re-populate the language cards list."""
        from translations import TranslationManager

        while self._lang_inner_layout.count():
            item = self._lang_inner_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        parent_app = self.parent()
        if hasattr(parent_app, "translation_manager"):
            tm = parent_app.translation_manager
        else:
            tm = TranslationManager()

        current = getattr(parent_app, "current_language", "fr")
        langs   = tm.get_available_languages()
        active_name = next((l["name"] for l in langs if l["code"] == current), current)
        self._lang_active_lbl.setText(active_name)

        for lang in langs:
            card = self._make_lang_card(lang, current)
            self._lang_inner_layout.addWidget(card)

        self._lang_inner_layout.addStretch()

    def _make_lang_card(self, lang: dict, current_code: str) -> QFrame:
        """Build one language card — fully theme-aware."""
        dark = self._lang_is_dark()

        is_active  = lang["code"] == current_code
        is_builtin = lang.get("builtin", False)

        if dark:
            if is_active:
                card_bg     = "#0f2a1e"
                border_col  = "#3fb950"
                name_col    = "#e6edf3"
                meta_col    = "#8b949e"
            else:
                card_bg     = "#1c2333"
                border_col  = "#30363d"
                name_col    = "#c9d1d9"
                meta_col    = "#8b949e"
        else:
            if is_active:
                card_bg     = "#f0fdf4"
                border_col  = "#10B981"
                name_col    = "#064e3b"
                meta_col    = "#6b7280"
            else:
                card_bg     = "#ffffff"
                border_col  = "#dee2e6"
                name_col    = "#1c2526"
                meta_col    = "#6b7280"

        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)
        card.setStyleSheet(f"""
            QFrame {{
                border: 2px solid {border_col};
                border-radius: 8px;
                background-color: {card_bg};
                padding: 2px;
            }}
        """)

        row = QHBoxLayout(card)
        row.setContentsMargins(10, 8, 10, 8)
        row.setSpacing(10)

        if is_active:
            badge_text  = self.translate_text("lang_active_badge")
            badge_bg    = "#3fb950" if dark else "#10B981"
            badge_fg    = "#ffffff"
        elif is_builtin:
            badge_text  = self.translate_text("lang_builtin_badge")
            badge_bg    = "#388bfd" if dark else "#6366F1"
            badge_fg    = "#ffffff"
        else:
            badge_text  = self.translate_text("lang_external_badge")
            badge_bg    = "#f0a030" if dark else "#f59e0b"
            badge_fg    = "#ffffff" if dark else "#1c2526"

        badge = QLabel(badge_text)
        badge.setStyleSheet(f"""
            background-color: {badge_bg};
            color: {badge_fg};
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 10px;
            font-weight: bold;
            border: none;
        """)
        row.addWidget(badge)

        info_col = QVBoxLayout()
        info_col.setSpacing(2)

        name_lbl = QLabel(lang["name"])
        name_lbl.setStyleSheet(
            f"font-weight: bold; font-size: 13px; color: {name_col}; border: none;"
        )
        info_col.addWidget(name_lbl)

        meta_parts = []
        if lang.get("author"):
            meta_parts.append(
                f"{self.translate_text('lang_author_label')} {lang['author']}"
            )
        if lang.get("version"):
            meta_parts.append(
                f"{self.translate_text('lang_version_label')} {lang['version']}"
            )
        desc = lang.get("description") or self.translate_text("lang_no_desc")
        meta_parts.append(desc)

        meta_lbl = QLabel("  •  ".join(meta_parts))
        meta_lbl.setStyleSheet(
            f"color: {meta_col}; font-size: 10px; border: none;"
        )
        meta_lbl.setWordWrap(True)
        info_col.addWidget(meta_lbl)
        row.addLayout(info_col, 1)

        if not is_active:
            if dark:
                apply_ss = """
                    QPushButton {
                        background-color: #1f3a6e; color: #79c0ff;
                        border: 1px solid #388bfd; padding: 5px 10px;
                        border-radius: 5px; font-size: 11px; font-weight: bold;
                    }
                    QPushButton:hover { background-color: #388bfd; color: #ffffff; }
                    QPushButton:pressed { background-color: #1158c7; color: #ffffff; }
                """
            else:
                apply_ss = """
                    QPushButton {
                        background-color: #eff6ff; color: #1d4ed8;
                        border: 1px solid #93c5fd; padding: 5px 10px;
                        border-radius: 5px; font-size: 11px; font-weight: bold;
                    }
                    QPushButton:hover { background-color: #1d4ed8; color: #ffffff; }
                    QPushButton:pressed { background-color: #1e40af; color: #ffffff; }
                """
            apply_btn = QPushButton(self.translate_text("Appliquer"))
            apply_btn.setFixedWidth(82)
            apply_btn.setStyleSheet(apply_ss)
            code = lang["code"]
            apply_btn.clicked.connect(lambda _, c=code: self._apply_language(c))
            row.addWidget(apply_btn)

        if not is_builtin:
            if dark:
                remove_ss = """
                    QPushButton {
                        background-color: #3d1a1a; color: #f85149;
                        border: 1px solid #6e1a1a; padding: 4px;
                        border-radius: 5px; font-size: 13px;
                    }
                    QPushButton:hover { background-color: #f85149; color: #ffffff; }
                """
            else:
                remove_ss = """
                    QPushButton {
                        background-color: #fef2f2; color: #ef4444;
                        border: 1px solid #fca5a5; padding: 4px;
                        border-radius: 5px; font-size: 13px;
                    }
                    QPushButton:hover { background-color: #ef4444; color: #ffffff; }
                """
            remove_btn = QPushButton("🗑")
            remove_btn.setFixedWidth(32)
            remove_btn.setToolTip(self.translate_text("Supprimer"))
            remove_btn.setStyleSheet(remove_ss)
            code = lang["code"]
            name = lang["name"]
            remove_btn.clicked.connect(
                lambda _, c=code, n=name: self._remove_language(c, n)
            )
            row.addWidget(remove_btn)

        return card

    def _import_lang_file(self) -> None:
        """Open file dialog to import a .lang file."""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            self.translate_text("Choisir un fichier .lang"),
            "",
            self.translate_text("Fichiers de langue (*.lang)"),
        )
        if not filepath:
            return

        parent_app = self.parent()
        if hasattr(parent_app, "translation_manager"):
            tm = parent_app.translation_manager
        else:
            from translations import TranslationManager
            tm = TranslationManager()

        ok, result = tm.load_lang_file(filepath)
        if ok:
            QMessageBox.information(
                self,
                self.translate_text("Langue importée"),
                self.translate_text("lang_import_ok").format(name=result),
            )
            self._refresh_lang_list()
        else:
            QMessageBox.warning(
                self,
                self.translate_text("Erreur"),
                self.translate_text("lang_import_err").format(error=result),
            )

    def _apply_language(self, code: str) -> None:
        """Switch the application language and refresh the card list."""
        parent_app = self.parent()
        if hasattr(parent_app, "translation_manager"):
            parent_app.translation_manager.set_language(code)
        if hasattr(parent_app, "current_language"):
            parent_app.current_language = code
        if hasattr(parent_app, "config"):
            parent_app.config["language"] = code
        if hasattr(parent_app, "config_manager"):
            parent_app.config_manager.save_config(parent_app.config)
        if hasattr(parent_app, "update_texts"):
            parent_app.update_texts()
        # Update language toolbar button text if present
        if hasattr(parent_app, "language_action"):
            if code == "fr":
                parent_app.language_action.setText("🇬🇧 English")
            elif code == "en":
                parent_app.language_action.setText("🇫🇷 Français")
            else:
                langs = parent_app.translation_manager.get_available_languages()
                name  = next((l["name"] for l in langs if l["code"] == code), code)
                parent_app.language_action.setText(f"🌐 {name}")
        self._refresh_lang_list()

    def _remove_language(self, code: str, name: str) -> None:
        """Confirm then remove an external language."""
        reply = QMessageBox.question(
            self,
            self.translate_text("Confirmation"),
            self.translate_text("lang_remove_confirm").format(name=name),
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        parent_app = self.parent()
        if hasattr(parent_app, "translation_manager"):
            tm = parent_app.translation_manager
        else:
            from translations import TranslationManager
            tm = TranslationManager()

        ok, error = tm.remove_lang_file(code)
        if ok:
            QMessageBox.information(
                self,
                self.translate_text("Langue supprimée"),
                self.translate_text("lang_remove_ok").format(code=code),
            )
            self._refresh_lang_list()
        else:
            QMessageBox.warning(
                self,
                self.translate_text("Erreur"),
                self.translate_text("lang_remove_err").format(error=error),
            )

    def _build_theme_tab(self) -> QWidget:
        dark = self._lang_is_dark()

        tab_bg = "#0d1117" if dark else "#f8f9fa"
        group_bg = "#161b22" if dark else "#ffffff"
        scroll_bg = "#161b22" if dark else "#ffffff"
        text_primary = "#e6edf3" if dark else "#1c2526"
        text_muted = "#8b949e" if dark else "#6b7280"
        group_border = "#30363d" if dark else "#dee2e6"
        active_green = "#3fb950" if dark else "#10B981"

        tab = QWidget()
        tab.setStyleSheet(f"background-color: {tab_bg};")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 10, 8, 10)
        layout.setSpacing(12)

        active_row = QHBoxLayout()
        active_lbl_title = QLabel(self.translate_text("Thème actif:"))
        active_lbl_title.setStyleSheet(f"color: {text_primary}; font-size: 12px;")
        active_row.addWidget(active_lbl_title)
        self._theme_active_lbl = QLabel()
        self._theme_active_lbl.setStyleSheet(
            f"font-weight: bold; font-size: 13px; color: {active_green};"
        )
        active_row.addWidget(self._theme_active_lbl)
        active_row.addStretch()
        layout.addLayout(active_row)

        list_group = QGroupBox(self.translate_text("Thèmes installés"))
        list_group.setStyleSheet(f"""
            QGroupBox {{
                color: {text_muted};
                background-color: {group_bg};
                border: 1px solid {group_border};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                font-size: 11px;
                font-weight: 600;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 6px;
                color: {text_muted};
            }}
        """)
        list_layout = QVBoxLayout(list_group)
        list_layout.setSpacing(6)
        list_layout.setContentsMargins(8, 8, 8, 8)

        self._theme_list = QScrollArea()
        self._theme_list.setWidgetResizable(True)
        self._theme_list.setFrameShape(QFrame.NoFrame)
        self._theme_list.setMinimumHeight(250)
        self._theme_list.setStyleSheet(_load_qss("lang_scroll.qss", get_current_theme(dark)))
        self._theme_inner = QWidget()
        self._theme_inner.setStyleSheet(f"background: {scroll_bg};")
        self._theme_inner_layout = QVBoxLayout(self._theme_inner)
        self._theme_inner_layout.setSpacing(6)
        self._theme_inner_layout.setContentsMargins(4, 4, 4, 4)
        self._theme_list.setWidget(self._theme_inner)
        list_layout.addWidget(self._theme_list)
        layout.addWidget(list_group)

        import_btn = QPushButton("📥 " + self.translate_text("Installer un thème (.fctheme)"))
        import_btn.setMinimumHeight(36)
        _apply_dialog_btn(import_btn, "BtnIndigo")
        import_btn.clicked.connect(self._import_theme_file)
        layout.addWidget(import_btn)

        hint = QLabel("ℹ️ " + self.translate_text(
            "Les fichiers .fctheme sont des archives ZIP contenant les fichiers QSS/CSS du thème et un metadata.ini."
        ))
        hint.setWordWrap(True)
        hint.setStyleSheet(
            f"color: {text_muted}; font-size: 10px; font-style: italic;"
        )
        layout.addWidget(hint)
        layout.addStretch()

        self._refresh_theme_list()
        return tab

    def _refresh_theme_list(self) -> None:
        dark = self._lang_is_dark()
        text_muted = "#8b949e" if dark else "#6b7280"

        while self._theme_inner_layout.count():
            item = self._theme_inner_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        parent_app = self.parent()
        current_theme = getattr(parent_app, "current_theme", "light") if parent_app else "light"
        self._theme_active_lbl.setText(current_theme)

        builtin = get_builtin_themes()
        custom = get_custom_themes()

        for name in builtin:
            card = self._make_theme_card_builtins(name, current_theme)
            self._theme_inner_layout.addWidget(card)

        for meta in custom:
            card = self._make_theme_card_custom(meta, current_theme)
            self._theme_inner_layout.addWidget(card)

        self._theme_inner_layout.addStretch()

    def _make_theme_card_builtins(self, name: str, current_theme: str) -> QFrame:
        dark = self._lang_is_dark()
        is_active = name == current_theme

        if dark:
            card_bg = "#0f2a1e" if is_active else "#161b22"
            border_col = "#3fb950" if is_active else "#30363d"
            name_col = "#e6edf3"
            meta_col = "#8b949e"
        else:
            card_bg = "#f0fdf4" if is_active else "#ffffff"
            border_col = "#10B981" if is_active else "#dee2e6"
            name_col = "#1c2526"
            meta_col = "#6b7280"

        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)
        card.setStyleSheet(f"""
            QFrame {{
                border: 2px solid {border_col};
                border-radius: 8px;
                background-color: {card_bg};
                padding: 2px;
            }}
        """)

        row = QHBoxLayout(card)
        row.setContentsMargins(10, 8, 10, 8)
        row.setSpacing(10)

        if is_active:
            badge_text = self.translate_text("lang_active_badge")
            badge_bg = "#3fb950" if dark else "#10B981"
        else:
            badge_text = self.translate_text("Intégré")
            badge_bg = "#388bfd" if dark else "#6366F1"
        badge_fg = "#ffffff"

        badge = QLabel(badge_text)
        badge.setStyleSheet(f"""
            background-color: {badge_bg};
            color: {badge_fg};
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 10px;
            font-weight: bold;
            border: none;
        """)
        row.addWidget(badge)

        info_col = QVBoxLayout()
        info_col.setSpacing(2)

        display_name = name.capitalize()
        name_lbl = QLabel(display_name)
        name_lbl.setStyleSheet(
            f"font-weight: bold; font-size: 13px; color: {name_col}; border: none;"
        )
        info_col.addWidget(name_lbl)

        meta_lbl = QLabel(self.translate_text("Thème intégré File Converter"))
        meta_lbl.setStyleSheet(
            f"color: {meta_col}; font-size: 10px; border: none;"
        )
        meta_lbl.setWordWrap(True)
        info_col.addWidget(meta_lbl)
        row.addLayout(info_col, 1)

        if not is_active:
            if dark:
                apply_ss = """
                    QPushButton {
                        background-color: #1f3a6e; color: #79c0ff;
                        border: 1px solid #388bfd; padding: 5px 10px;
                        border-radius: 5px; font-size: 11px; font-weight: bold;
                    }
                    QPushButton:hover { background-color: #388bfd; color: #ffffff; }
                    QPushButton:pressed { background-color: #1158c7; color: #ffffff; }
                """
            else:
                apply_ss = """
                    QPushButton {
                        background-color: #eff6ff; color: #1d4ed8;
                        border: 1px solid #93c5fd; padding: 5px 10px;
                        border-radius: 5px; font-size: 11px; font-weight: bold;
                    }
                    QPushButton:hover { background-color: #1d4ed8; color: #ffffff; }
                    QPushButton:pressed { background-color: #1e40af; color: #ffffff; }
                """
            apply_btn = QPushButton(self.translate_text("Appliquer"))
            apply_btn.setFixedWidth(82)
            apply_btn.setStyleSheet(apply_ss)
            apply_btn.clicked.connect(lambda _, n=name: self._apply_theme(n))
            row.addWidget(apply_btn)

        return card

    def _make_theme_card_custom(self, meta, current_theme: str) -> QFrame:
        dark = self._lang_is_dark()
        is_active = meta.folder_name == current_theme

        if dark:
            card_bg = "#0f2a1e" if is_active else "#1c2333"
            border_col = "#3fb950" if is_active else "#30363d"
            name_col = "#e6edf3"
            meta_col = "#8b949e"
            group_border = "#30363d"
        else:
            card_bg = "#f0fdf4" if is_active else "#ffffff"
            border_col = "#10B981" if is_active else "#dee2e6"
            name_col = "#1c2526"
            meta_col = "#6b7280"
            group_border = "#dee2e6"

        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)
        card.setStyleSheet(f"""
            QFrame {{
                border: 2px solid {border_col};
                border-radius: 8px;
                background-color: {card_bg};
                padding: 2px;
            }}
        """)

        main_row = QHBoxLayout(card)
        main_row.setContentsMargins(8, 5, 8, 5)
        main_row.setSpacing(8)

        preview_path = CUSTOM_THEMES_DIR / meta.folder_name / meta.preview if meta.preview else None
        if preview_path and preview_path.exists():
            img = QImage(str(preview_path))
            if not img.isNull():
                pixmap = QPixmap.fromImage(img).scaled(64, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                preview_lbl = QLabel()
                preview_lbl.setPixmap(pixmap)
                preview_lbl.setFixedSize(64, 48)
                preview_lbl.setStyleSheet(f"""
                    border: 1px solid {group_border};
                    border-radius: 6px;
                    background-color: {card_bg};
                """)
                main_row.addWidget(preview_lbl)

        info_col = QVBoxLayout()
        info_col.setSpacing(2)

        if is_active:
            badge_text = self.translate_text("lang_active_badge")
            badge_bg = "#3fb950" if dark else "#10B981"
        else:
            badge_text = self.translate_text("Personnalisé")
            badge_bg = "#f0a030" if dark else "#f59e0b"
        badge_fg = "#ffffff" if dark else "#1c2526"

        badge = QLabel(badge_text)
        badge.setStyleSheet(f"""
            background-color: {badge_bg};
            color: {badge_fg};
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 10px;
            font-weight: bold;
            border: none;
        """)
        info_col.addWidget(badge)

        name_lbl = QLabel(meta.name)
        name_lbl.setStyleSheet(
            f"font-weight: bold; font-size: 13px; color: {name_col}; border: none;"
        )
        info_col.addWidget(name_lbl)

        meta_parts = []
        if meta.author:
            meta_parts.append(f"{self.translate_text('lang_author_label')} {meta.author}")
        if meta.version:
            meta_parts.append(f"v{meta.version}")
        if meta.description:
            meta_parts.append(meta.description)
        meta_lbl = QLabel("  •  ".join(meta_parts) if meta_parts else "")
        meta_lbl.setStyleSheet(
            f"color: {meta_col}; font-size: 10px; border: none;"
        )
        meta_lbl.setWordWrap(True)
        info_col.addWidget(meta_lbl)
        main_row.addLayout(info_col, 1)

        btn_col = QHBoxLayout()
        btn_col.setSpacing(4)

        if not is_active:
            if dark:
                apply_ss = """
                    QPushButton {
                        background-color: #1f3a6e; color: #79c0ff;
                        border: 1px solid #388bfd; padding: 5px 10px;
                        border-radius: 5px; font-size: 11px; font-weight: bold;
                    }
                    QPushButton:hover { background-color: #388bfd; color: #ffffff; }
                    QPushButton:pressed { background-color: #1158c7; color: #ffffff; }
                """
            else:
                apply_ss = """
                    QPushButton {
                        background-color: #eff6ff; color: #1d4ed8;
                        border: 1px solid #93c5fd; padding: 5px 10px;
                        border-radius: 5px; font-size: 11px; font-weight: bold;
                    }
                    QPushButton:hover { background-color: #1d4ed8; color: #ffffff; }
                    QPushButton:pressed { background-color: #1e40af; color: #ffffff; }
                """
            apply_btn = QPushButton(self.translate_text("Appliquer"))
            apply_btn.setFixedWidth(82)
            apply_btn.setStyleSheet(apply_ss)
            apply_btn.clicked.connect(lambda _, n=meta.folder_name: self._apply_theme(n))
            btn_col.addWidget(apply_btn)

        if not is_active:
            if dark:
                remove_ss = """
                    QPushButton {
                        background-color: #3d1a1a; color: #f85149;
                        border: 1px solid #6e1a1a; padding: 4px;
                        border-radius: 5px; font-size: 13px;
                    }
                    QPushButton:hover { background-color: #f85149; color: #ffffff; }
                """
            else:
                remove_ss = """
                    QPushButton {
                        background-color: #fef2f2; color: #ef4444;
                        border: 1px solid #fca5a5; padding: 4px;
                        border-radius: 5px; font-size: 13px;
                    }
                    QPushButton:hover { background-color: #ef4444; color: #ffffff; }
                """
            remove_btn = QPushButton("🗑")
            remove_btn.setFixedWidth(32)
            remove_btn.setToolTip(self.translate_text("Supprimer"))
            remove_btn.setStyleSheet(remove_ss)
            remove_btn.clicked.connect(lambda _, n=meta.folder_name, nm=meta.name: self._remove_theme(n, nm))
            btn_col.addWidget(remove_btn)

        main_row.addLayout(btn_col)

        return card

    def _apply_theme(self, theme_name: str) -> None:
        from theme_manager import get_custom_theme_kind

        parent_app = self.parent()
        if not parent_app:
            return

        parent_app.current_theme = theme_name
        if theme_name in ("dark", "light"):
            parent_app.config.pop("custom_theme", None)
        else:
            parent_app.config["custom_theme"] = theme_name
        parent_app.config["use_system_theme"] = False

        if theme_name in ("dark", "light"):
            is_dark = theme_name == "dark"
        else:
            is_dark = get_custom_theme_kind(theme_name) == "dark"
        parent_app.dark_mode = is_dark
        parent_app.config["dark_mode"] = is_dark

        parent_app.config_manager.save_config(parent_app.config)

        if hasattr(self, 'use_system_theme_checkbox'):
            self.use_system_theme_checkbox.setChecked(False)

        parent_app.apply_theme(is_dark)
        parent_app.update_texts()
        self._refresh_theme_list()
        self.apply_scrollbar_style()

    def _import_theme_file(self) -> None:
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            self.translate_text("Choisir un fichier .fctheme"),
            "",
            self.translate_text("Thèmes (*.fctheme)"),
        )
        if not filepath:
            return

        ok, result = import_theme(filepath)
        if ok:
            QMessageBox.information(
                self,
                self.translate_text("Thème installé"),
                self.translate_text("Thème «{}» installé avec succès.").format(result),
            )
            self._refresh_theme_list()
        else:
            QMessageBox.warning(
                self,
                self.translate_text("Erreur"),
                self.translate_text("Impossible d'installer le thème : {}").format(result),
            )

    def _remove_theme(self, folder_name: str, display_name: str) -> None:
        reply = QMessageBox.question(
            self,
            self.translate_text("Confirmation"),
            self.translate_text("Supprimer le thème «{}» ?").format(display_name),
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        ok, result = remove_theme(folder_name)
        if ok:
            parent_app = self.parent()
            if parent_app and getattr(parent_app, "current_theme", None) == folder_name:
                parent_app.current_theme = "light"
                parent_app.config.pop("custom_theme", None)
                parent_app.config_manager.save_config(parent_app.config)
                parent_app.dark_mode = False
                parent_app.apply_theme(False)
            QMessageBox.information(
                self,
                self.translate_text("Thème supprimé"),
                self.translate_text("Thème «{}» supprimé.").format(display_name),
            )
            self._refresh_theme_list()
        else:
            QMessageBox.warning(
                self,
                self.translate_text("Erreur"),
                result,
            )

    def browse_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, self.translate_text("Sélectionner le dossier de sortie par défaut"))
        if folder:
            self.default_output_input.setText(folder)

    def show_terms(self):
        dark_mode = self.config.get("dark_mode", False)
        dialog = TermsAndPrivacyDialog(self, self.language, dark_mode=dark_mode)
        dialog.tab_widget.setCurrentIndex(0)
        dialog.from_settings = True
        result = dialog.exec()
        if dialog.closed_by_cross:
            return
        self.process_terms_result(result, dialog)

    def show_privacy(self):
        dark_mode = self.config.get("dark_mode", False)
        dialog = TermsAndPrivacyDialog(self, self.language, dark_mode=dark_mode)
        dialog.tab_widget.setCurrentIndex(1)
        dialog.from_settings = True
        result = dialog.exec()
        if dialog.closed_by_cross:
            return
        self.process_terms_result(result, dialog)

    def process_terms_result(self, result, dialog):
        parent_app = self.parent()
        if not hasattr(parent_app, 'config_manager'):
            return

        config = parent_app.config_manager.load_config()

        if result == QDialog.Accepted:
            config["accepted_terms"] = True
            config["accepted_privacy"] = True

            if config.get("terms_acceptance_timestamp") is not None:
                config["terms_reacceptance_timestamp"] = datetime.now().isoformat()
                print(f"[TERMS DEBUG] Re-acceptance detected - terms_reacceptance_timestamp added: {config['terms_reacceptance_timestamp']}")
            else:
                config["terms_acceptance_timestamp"] = datetime.now().isoformat()
                print(f"[TERMS DEBUG] First acceptance - terms_acceptance_timestamp set: {config['terms_acceptance_timestamp']}")

            parent_app.config_manager.save_config(config)
            parent_app.config.update(config)
            parent_app.terms_accepted = True

            QMessageBox.information(
                self,
                self.translate_text("Succès"),
                self.translate_text("Conditions et politique acceptées avec succès.")
            )

            self.accept()
        else:
            config["accepted_terms"] = False
            config["accepted_privacy"] = False
            config["terms_rejection_timestamp"] = datetime.now().isoformat()

            parent_app.config_manager.save_config(config)
            parent_app.config.update(config)

            QMessageBox.warning(
                self,
                self.translate_text("Attention"),
                self.translate_text("Vous avez refusé les conditions. L'application va se fermer.")
            )

            QTimer.singleShot(1500, QCoreApplication.quit)
            return

    def restore_defaults(self):
        self.auto_open_checkbox.setChecked(False)
        self.notifications_checkbox.setChecked(True)
        self.system_notifications_checkbox.setChecked(True)
        self.show_previews_checkbox.setChecked(True)
        self.show_dashboard_checkbox.setChecked(True)
        self.quality_combo.setCurrentIndex(1)
        self.compression_level_combo.setCurrentIndex(0)
        self.pdf_to_word_mode_combo.setCurrentIndex(0)
        self.default_output_input.clear()
        self.keep_history_days_spin.setValue(365)
        self.auto_clean_checkbox.setChecked(True)
        self.backup_checkbox.setChecked(False)
        self.auto_save_templates_check.setChecked(True)
        self.separate_image_pdfs_checkbox.setChecked(False)
        self.use_system_theme_checkbox.setChecked(True)

    def _build_automation_tab(self) -> QWidget:
        dark = self._lang_is_dark()

        tab_bg       = "#0d1117" if dark else "#f8f9fa"
        group_bg     = "#161b22" if dark else "#ffffff"
        group_border = "#30363d" if dark else "#dee2e6"
        text_muted   = "#8b949e" if dark else "#6b7280"

        tab = QWidget()
        tab.setStyleSheet(f"background-color: {tab_bg};")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 10, 8, 10)
        layout.setSpacing(12)

        from daemon import is_autostart_enabled

        autostart_group = QGroupBox(self.translate_text("Démon d'automatisation"))
        autostart_group.setStyleSheet(f"""
            QGroupBox {{
                color: {text_muted}; background-color: {group_bg};
                border: 1px solid {group_border}; border-radius: 8px;
                margin-top: 10px; padding-top: 10px;
                font-size: 11px; font-weight: 600;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin; left: 10px; padding: 0 6px; color: {text_muted};
            }}
        """)
        autostart_layout = QVBoxLayout(autostart_group)
        autostart_layout.setSpacing(8)

        self._autostart_check = AnimatedCheckBox(
            self.translate_text("Lancer le démon automatiquement au démarrage de Windows")
        )
        self._autostart_check.setProperty("i18n_key", "Lancer le démon automatiquement au démarrage de Windows")
        self._autostart_check.setChecked(is_autostart_enabled())
        self._autostart_check.stateChanged.connect(self._on_autostart_toggled)

        hint = QLabel("ℹ️ " + self.translate_text(
            "Le démon surveille vos dossiers et exécute les tâches planifiées même si l'application est fermée."
        ))
        hint.setProperty("i18n_key",
            "Le démon surveille vos dossiers et exécute les tâches planifiées même si l'application est fermée."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet(f"color: {text_muted}; font-size: 10px; font-style: italic; background: transparent;")

        autostart_layout.addWidget(self._autostart_check)
        autostart_layout.addWidget(hint)
        layout.addWidget(autostart_group)

        wf_group = QGroupBox(self.translate_text("Dossiers surveillés"))
        wf_group.setStyleSheet(autostart_group.styleSheet())
        wf_layout = QVBoxLayout(wf_group)
        wf_layout.setSpacing(6)
        wf_layout.setContentsMargins(8, 8, 8, 8)

        self._wf_inner_layout = QVBoxLayout()
        self._wf_inner_layout.setSpacing(5)
        wf_layout.addLayout(self._wf_inner_layout)
        layout.addWidget(wf_group)

        st_group = QGroupBox(self.translate_text("Tâches planifiées"))
        st_group.setStyleSheet(autostart_group.styleSheet())
        st_layout = QVBoxLayout(st_group)
        st_layout.setSpacing(6)
        st_layout.setContentsMargins(8, 8, 8, 8)

        self._st_inner_layout = QVBoxLayout()
        self._st_inner_layout.setSpacing(5)
        st_layout.addLayout(self._st_inner_layout)
        layout.addWidget(st_group)

        btn_row = QHBoxLayout()

        open_btn = QPushButton("📂 " + self.translate_text("Ouvrir le dossier automation/"))
        open_btn.setProperty("i18n_key", "Ouvrir le dossier automation/")
        open_btn.setMinimumHeight(32)
        _apply_dialog_btn(open_btn, "BtnOK")
        open_btn.clicked.connect(self._open_automation_dir)

        reload_btn = QPushButton("🔄 " + self.translate_text("Recharger"))
        reload_btn.setProperty("i18n_key", "Recharger")
        reload_btn.setMinimumHeight(32)
        _apply_dialog_btn(reload_btn, "BtnIndigo")
        reload_btn.clicked.connect(self._refresh_automation_tab)

        btn_row.addWidget(open_btn)
        btn_row.addWidget(reload_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)
        layout.addStretch()

        self._refresh_automation_tab()
        return tab

    def _refresh_automation_tab(self) -> None:
        """Reload watch folders and scheduled tasks from automation/*.toml."""
        from tasks.watcher   import get_all_watch_folder_configs
        from tasks.scheduler import get_all_scheduled_task_configs

        dark         = self._lang_is_dark()
        card_bg      = "#1c2333" if dark else "#ffffff"
        card_border  = "#30363d" if dark else "#dee2e6"
        text_primary = "#c9d1d9" if dark else "#1c2526"
        text_muted   = "#8b949e" if dark else "#6b7280"
        active_col   = "#3fb950" if dark else "#10B981"
        inactive_col = "#8b949e" if dark else "#9ca3af"

        def _clear(layout):
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

        def _make_card(name, path, enabled, extra_label=""):
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    border: 1px solid {card_border};
                    border-radius: 7px;
                    background-color: {card_bg};
                }}
            """)
            row = QHBoxLayout(card)
            row.setContentsMargins(10, 7, 10, 7)
            row.setSpacing(10)

            status_dot = QLabel("●")
            status_dot.setStyleSheet(
                f"color: {active_col if enabled else inactive_col}; font-size: 14px; border: none;"
            )
            row.addWidget(status_dot)

            info = QVBoxLayout()
            info.setSpacing(1)
            status_text = self.translate_text("Actif") if enabled else self.translate_text("Inactif")
            name_lbl = QLabel(f"{name}  –  {status_text}")
            name_lbl.setStyleSheet(
                f"font-weight: bold; font-size: 12px; color: {text_primary}; border: none;"
            )
            name_lbl.setWordWrap(True)
            path_lbl = QLabel(path + (f"  {extra_label}" if extra_label else ""))
            path_lbl.setStyleSheet(f"font-size: 10px; color: {text_muted}; border: none;")
            path_lbl.setWordWrap(True)
            info.addWidget(name_lbl)
            info.addWidget(path_lbl)
            row.addLayout(info, 1)

            return card

        # Watch Folders
        _clear(self._wf_inner_layout)
        wf_configs = get_all_watch_folder_configs()
        if not wf_configs:
            empty = QLabel(self.translate_text("Aucun dossier surveillé configuré."))
            empty.setStyleSheet(f"color: {text_muted}; font-size: 11px; font-style: italic;")
            self._wf_inner_layout.addWidget(empty)
        else:
            for cfg in wf_configs:
                rules_summary = ", ".join(
                    f".{ext}→{','.join(r['fmt'] if r['kind'] == 'convert' else r['action'] for r in fmts) if isinstance(fmts, list) else fmts}"
                    for ext, fmts in cfg["rules"].items()
                )
                card = _make_card(cfg["name"], cfg["path"], cfg["enabled"], f"({rules_summary})")
                self._wf_inner_layout.addWidget(card)

        # Scheduled Tasks
        _clear(self._st_inner_layout)
        st_configs = get_all_scheduled_task_configs()
        if not st_configs:
            empty = QLabel(self.translate_text("Aucune tâche planifiée configurée."))
            empty.setStyleSheet(f"color: {text_muted}; font-size: 11px; font-style: italic;")
            self._st_inner_layout.addWidget(empty)
        else:
            for cfg in st_configs:
                t = cfg["trigger"]
                trigger_str = (
                    f"cron – {t.get('day_of_week','*')} {t.get('hour',0):02d}:{t.get('minute',0):02d}"
                    if t.get("type") == "cron"
                    else f"interval – every {t.get('hours',0)}h {t.get('minutes',0)}min"
                )
                card = _make_card(cfg["name"], cfg["path"], cfg["enabled"], f"[{trigger_str}]")
                self._st_inner_layout.addWidget(card)

    def _on_autostart_toggled(self, state: int) -> None:
        import subprocess
        from daemon import set_autostart

        enabled = bool(state)
        set_autostart(enabled)

        if enabled:
            if getattr(sys, "frozen", False):
                cmd = [sys.executable, "--daemon"]
                flags = 0x08000000
            else:
                main_script = str(Path(__file__).resolve().parent.parent / "main.py")
                cmd = [sys.executable, main_script, "--daemon"]
                flags = 0x08000000 | 0x00000008

            subprocess.Popen(cmd, creationflags=flags)
        else:
            from daemon import AUTOMATION_DIR
            stop_flag = AUTOMATION_DIR / ".stop"
            stop_flag.touch()

    def _open_automation_dir(self) -> None:
        import subprocess
        from tasks.watcher import _get_automation_dir
        path = _get_automation_dir()
        path.mkdir(exist_ok=True)
        subprocess.Popen(["explorer", str(path)])

    def get_settings(self):
        quality_map = {0: "high", 1: "standard", 2: "compressed"}
        compression_map = {0: "normal", 1: "high", 2: "maximum"}
        mode_map = {0: "with_images", 1: "text_only", 2: "text_with_image_text"}
        return {
            "auto_open_last_project": self.auto_open_checkbox.isChecked(),
            "enable_notifications": self.notifications_checkbox.isChecked(),
            "enable_system_notifications": self.system_notifications_checkbox.isChecked(),
            "achievements_enabled": self.achievements_checkbox.isChecked(),
            "show_file_previews": self.show_previews_checkbox.isChecked(),
            "show_dashboard_on_startup": self.show_dashboard_checkbox.isChecked(),
            "conversion_quality": quality_map[self.quality_combo.currentIndex()],
            "compression_level": compression_map[self.compression_level_combo.currentIndex()],
            "pdf_to_word_mode": mode_map[self.pdf_to_word_mode_combo.currentIndex()],
            "default_output_folder": self.default_output_input.text(),
            "keep_history_days": self.keep_history_days_spin.value(),
            "auto_clean_temp_files": self.auto_clean_checkbox.isChecked(),
            "backup_before_conversion": self.backup_checkbox.isChecked(),
            "auto_save_templates": self.auto_save_templates_check.isChecked(),
            "separate_image_pdfs": self.separate_image_pdfs_checkbox.isChecked(),
            "use_system_theme": self.use_system_theme_checkbox.isChecked()
        }
