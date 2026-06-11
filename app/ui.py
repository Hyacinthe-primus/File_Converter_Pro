"""
app/ui.py

Contains all Qt UI construction, theming, animations, and window-management
methods of FileConverterApp, extracted as a mixin.  Also houses dialogs that
are tightly coupled to the main window:
  - PdfProtectionDialog
  - MergeOrderDialog

"""


import sys
import os
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout,
                               QHBoxLayout, QPushButton, QLabel, QListWidget,
                               QListWidgetItem, QFileDialog, QMessageBox,
                               QProgressBar, QComboBox, QCheckBox, QToolBar, QStatusBar,
                               QGroupBox, QScrollArea, QLineEdit, QDialog, QFormLayout, QSpinBox,
                               QTextEdit, QTabWidget, QMenu, QRadioButton, QFrame, QButtonGroup,
                               QTableWidget, QTreeWidget, QInputDialog, QApplication, QMenuBar)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, QSize
from PySide6.QtGui import (QIcon, QPixmap, QFont, QColor, QAction, QPainter,
                           QKeySequence, QShortcut)
from datetime import datetime
import time

try:
    from pdf2docx import Converter as _Converter
    Converter = _Converter
except ImportError as _e:
    Converter = None
    print(f"[IMPORT] pdf2docx not available: {_e}")

from qss_helpers import _load_qss, _apply_dialog_btn
from translations import TranslationManager
from widgets import DraggableListWidget, AnimatedCheckBox
from dialogs import (SettingsDialog, BatchRenameDialog, ConversionOptionsDialog, PreviewDialog)
from achievements import AchievementsUI, AchievementPopup, RankPopup

def _get_StatisticsDashboard():
    from dashboard import StatisticsDashboard
    return StatisticsDashboard

def _get_HistoryDialog():
    from history import HistoryDialog
    return HistoryDialog

def _get_TemplateClasses():
    from templates import TemplateManager, EnhancedTemplatesDialog
    return TemplateManager, EnhancedTemplatesDialog
from app.logic import AppLogicMixin

class PdfProtectionDialog(QDialog):
    """Dialog for PDF protection options — Basic or Advanced."""

    def __init__(self, parent=None, language="fr"):
        super().__init__(parent)
        self._tm = TranslationManager()
        self._tm.set_language(language)
        self.setWindowTitle(self.tr_("Protéger PDF avec mot de passe"))
        self.setMinimumWidth(400)
        self._setup_ui()

    def tr_(self, text):
        return self._tm.translate_text(text)

    def _setup_ui(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(12)

        mode_lay = QHBoxLayout()
        mode_lay.addWidget(QLabel(self.tr_("Mode:")))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            self.tr_("Basique (restrictions uniquement)"),
            self.tr_("Avancé (mot de passe + restrictions)"),
        ])
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        mode_lay.addWidget(self.mode_combo)
        lay.addLayout(mode_lay)

        self._pwd_group = QGroupBox(self.tr_("Mot de passe"))
        pwd_lay = QFormLayout(self._pwd_group)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.Password)
        pwd_lay.addRow(self.tr_("Mot de passe:"), self.password_input)
        pwd_lay.addRow(self.tr_("Confirmer:"), self.confirm_input)
        self._pwd_group.setVisible(False)
        lay.addWidget(self._pwd_group)

        perm_group = QGroupBox(self.tr_("Permissions"))
        perm_lay = QVBoxLayout(perm_group)

        self.allow_print_check = AnimatedCheckBox(self.tr_("Autoriser l'impression"))
        self.allow_print_check.setChecked(True)
        self.allow_copy_check = AnimatedCheckBox(self.tr_("Autoriser la copie de texte"))
        self.allow_copy_check.setChecked(True)
        self.allow_copy_accessibility_check = AnimatedCheckBox(self.tr_("Autoriser la copie pour l'accessibilité"))
        self.allow_copy_accessibility_check.setChecked(True)
        self.allow_modify_check = AnimatedCheckBox(self.tr_("Autoriser les modifications du contenu"))
        self.allow_modify_check.setChecked(False)
        self.allow_annotations_check = AnimatedCheckBox(self.tr_("Autoriser les commentaires / annotations"))
        self.allow_annotations_check.setChecked(False)
        self.allow_forms_check = AnimatedCheckBox(self.tr_("Autoriser le remplissage de formulaires"))
        self.allow_forms_check.setChecked(False)
        self.allow_assemble_check = AnimatedCheckBox(self.tr_("Autoriser l'assemblage / signature"))
        self.allow_assemble_check.setChecked(False)

        perm_lay.addWidget(self.allow_print_check)
        perm_lay.addWidget(self.allow_copy_check)
        perm_lay.addWidget(self.allow_copy_accessibility_check)
        perm_lay.addWidget(self.allow_modify_check)
        perm_lay.addWidget(self.allow_annotations_check)
        perm_lay.addWidget(self.allow_forms_check)
        perm_lay.addWidget(self.allow_assemble_check)
        lay.addWidget(perm_group)

        btn_row = QHBoxLayout()
        ok_btn = QPushButton(self.tr_("Appliquer"))
        ok_btn.setMinimumHeight(36)
        ok_btn.setStyleSheet("""
            QPushButton { background:#28a745; color:white; border:none;
                          border-radius:6px; font-weight:bold; padding:6px 16px; }
            QPushButton:hover { background:#218838; }
        """)
        cancel_btn = QPushButton(self.tr_("Annuler"))
        cancel_btn.setMinimumHeight(36)
        _apply_dialog_btn(cancel_btn, "BtnCancelGlassy")
        ok_btn.clicked.connect(self._validate)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(ok_btn)
        lay.addLayout(btn_row)

    def _on_mode_changed(self, idx):
        self._pwd_group.setVisible(idx == 1)
        self.adjustSize()

    def is_advanced(self):
        return self.mode_combo.currentIndex() == 1

    def get_password(self):
        return self.password_input.text() if self.is_advanced() else None

    def get_permissions(self):
        """Return pypdf UserAccessPermissions flag."""
        from pypdf.constants import UserAccessPermissions
        flag = UserAccessPermissions(0)
        if self.allow_print_check.isChecked():
            flag |= UserAccessPermissions.PRINT
            flag |= UserAccessPermissions.PRINT_TO_REPRESENTATION
        if self.allow_copy_check.isChecked():
            flag |= UserAccessPermissions.EXTRACT
        if self.allow_copy_accessibility_check.isChecked():
            flag |= UserAccessPermissions.EXTRACT_TEXT_AND_GRAPHICS
        if self.allow_modify_check.isChecked():
            flag |= UserAccessPermissions.MODIFY
        if self.allow_annotations_check.isChecked():
            flag |= UserAccessPermissions.ADD_OR_MODIFY
        if self.allow_forms_check.isChecked():
            flag |= UserAccessPermissions.FILL_FORM_FIELDS
        if self.allow_assemble_check.isChecked():
            flag |= UserAccessPermissions.ASSEMBLE_DOC
        return flag

    def _validate(self):
        if self.is_advanced():
            pwd = self.password_input.text()
            if not pwd:
                QMessageBox.warning(self, self.tr_("Erreur"),
                                    self.tr_("Veuillez entrer un mot de passe"))
                return
            if self.password_input.text() != self.confirm_input.text():
                QMessageBox.warning(self, self.tr_("Erreur"),
                                    self.tr_("Les mots de passe ne correspondent pas"))
                return
        self.accept()


class MergeOrderDialog(QDialog):
    """Dialog for choosing merge order and optionally reordering files manually."""

    def __init__(self, files, file_type, parent=None, language="fr", pre_select_key=None):
        super().__init__(parent)
        self._tm = TranslationManager()
        self._tm.set_language(language)
        self.files = list(files)
        self.file_type = file_type
        self._pre_select_key = pre_select_key
        self.setWindowTitle(self.translate_text("Ordre de fusion"))
        self.setMinimumWidth(480)
        self.setMinimumHeight(400)
        self._setup_ui()
        if pre_select_key and pre_select_key in self._radio_map:
            self._radio_map[pre_select_key].setChecked(True)

    def translate_text(self, text):
        return self._tm.translate_text(text)

    def _setup_ui(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(10)

        order_group = QGroupBox(self.translate_text("Choisir l'ordre"))
        order_lay = QVBoxLayout(order_group)

        self.order_buttons = QButtonGroup(self)
        orders = [
            ("alpha_az",  "🔤 " + self.translate_text("Alphabétique (A→Z)")),
            ("alpha_za",  "🔤 " + self.translate_text("Alphabétique (Z→A)")),
            ("num_asc",   "🔢 " + self.translate_text("Numérique (1→9)")),
            ("num_desc",  "🔢 " + self.translate_text("Numérique (9→1)")),
            ("date_asc",  "📅 " + self.translate_text("Date (ancien→nouveau)")),
            ("date_desc", "📅 " + self.translate_text("Date (nouveau→ancien)")),
            ("manual",    "✋ " + self.translate_text("Manuel (glisser-déposer)")),
            ("current",   "📋 " + self.translate_text("Ordre actuel (liste principale)")),
        ]
        self._radio_map = {}
        for key, label in orders:
            rb = QRadioButton(label)
            self.order_buttons.addButton(rb)
            order_lay.addWidget(rb)
            self._radio_map[key] = rb
        self._radio_map["current"].setChecked(True)

        lay.addWidget(order_group)

        self._manual_group = QGroupBox(self.translate_text("Réordonner les fichiers"))
        manual_lay = QVBoxLayout(self._manual_group)
        hint = QLabel(self.translate_text("Glissez-déposez pour réordonner, puis cliquez sur Fusionner."))
        hint.setStyleSheet("color: gray; font-size: 11px;")
        manual_lay.addWidget(hint)

        self._manual_list = QListWidget()
        self._manual_list.setDragDropMode(QListWidget.InternalMove)
        self._manual_list.setSelectionMode(QListWidget.SingleSelection)
        for f in self.files:
            self._manual_list.addItem(QListWidgetItem(Path(f).name))
            self._manual_list.item(self._manual_list.count()-1).setData(Qt.UserRole, f)
        manual_lay.addWidget(self._manual_list)
        self._manual_group.setVisible(False)
        lay.addWidget(self._manual_group)

        self._radio_map["manual"].toggled.connect(self._manual_group.setVisible)

        btn_row = QHBoxLayout()
        merge_btn = QPushButton("🔗 " + self.translate_text("Fusionner"))
        merge_btn.setMinimumHeight(36)
        merge_btn.setStyleSheet("""
            QPushButton { background:#28a745; color:white; border:none;
                          border-radius:6px; font-weight:bold; padding:6px 16px; }
            QPushButton:hover { background:#218838; }
        """)
        cancel_btn = QPushButton(self.translate_text("Annuler"))
        cancel_btn.setMinimumHeight(36)
        _apply_dialog_btn(cancel_btn, "BtnCancelGlassy")
        merge_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(merge_btn)
        lay.addLayout(btn_row)

    def get_ordered_files(self):
        """Return files in the chosen order."""
        files = list(self.files)

        if self._radio_map["alpha_az"].isChecked():
            files.sort(key=lambda f: Path(f).name.lower())
        elif self._radio_map["alpha_za"].isChecked():
            files.sort(key=lambda f: Path(f).name.lower(), reverse=True)
        elif self._radio_map["num_asc"].isChecked():
            import re
            def num_key(f):
                nums = re.findall(r'\d+', Path(f).stem)
                return [int(n) for n in nums] if nums else [0]
            files.sort(key=num_key)
        elif self._radio_map["num_desc"].isChecked():
            import re
            def num_key_d(f):
                nums = re.findall(r'\d+', Path(f).stem)
                return [int(n) for n in nums] if nums else [0]
            files.sort(key=num_key_d, reverse=True)
        elif self._radio_map["date_asc"].isChecked():
            files.sort(key=lambda f: os.path.getmtime(f))
        elif self._radio_map["date_desc"].isChecked():
            files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
        elif self._radio_map["manual"].isChecked():
            files = [
                self._manual_list.item(i).data(Qt.UserRole)
                for i in range(self._manual_list.count())
            ]

        return files


class AppUIMixin(AppLogicMixin):
    """Mixin: Qt UI construction and theming for FileConverterApp."""

    def get_resource_path(self, relative_path):
        """Get the resource path"""
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def show_rank_popup(self, rank_data):
        """Queue the rank popup (will be displayed after achievements)"""
        if not self.config.get("achievements_enabled", True):
            return
        self.rank_queue.append(rank_data)
        self.process_rank_queue()

    def queue_achievement(self, achievement):
        """Add an achievement to the queue"""
        if not self.config.get("achievements_enabled", True):
            return
        self.achievement_queue.append(achievement)
        self.process_achievement_queue()

    def process_achievement_queue(self):
        """Process the achievement queue"""
        if self.is_showing_achievement or not self.achievement_queue:
            return

        self.is_showing_achievement = True

        next_achievement = self.achievement_queue.pop(0)

        self.show_achievement_popup_sequential(next_achievement)

    def process_rank_queue(self):
        """Display rank popups one by one, with 1s delay"""
        if self.is_showing_achievement or not self.rank_queue:
            return

        if hasattr(self, '_is_showing_rank') and self._is_showing_rank:
            return

        rank_data = self.rank_queue.pop(0)
        self._is_showing_rank = True

        popup = RankPopup(rank_data, self.achievement_system, self, language=self.current_language)
        popup.set_translator(self.translation_manager)

        def on_rank_finished():
            self._is_showing_rank = False
            QTimer.singleShot(1000, self.process_rank_queue)

        QTimer.singleShot(6000, on_rank_finished)
        popup.show()

    def show_achievement_popup_sequential(self, achievement):
        """Display the popup (internal method called by the queue)"""
        popup = AchievementPopup(achievement, self.achievement_system, self, language=self.current_language)
        popup.set_translator(self.translation_manager)
        popup.finished_display.connect(self.on_achievement_finished)
        popup.show()

    def on_achievement_finished(self):
        self.is_showing_achievement = False
        self.process_achievement_queue()
        if not self.achievement_queue:
            QTimer.singleShot(500, self.process_rank_queue)

    def setup_shortcuts(self):
        """Configure keyboard shortcuts"""

        shortcut_escape = QShortcut(QKeySequence("Esc"), self)
        shortcut_escape.activated.connect(self.close_secondary_windows)
        shortcut_word_mode = QShortcut(QKeySequence("Ctrl+W"), self)
        shortcut_word_mode.activated.connect(self.toggle_word_pdf_mode)

    def toggle_word_pdf_mode(self):
        """Toggle between Word to PDF conversion modes"""
        current_mode = self.config.get("word_to_pdf_mode", "preserve_all")
        new_mode = "text_only" if current_mode == "preserve_all" else "preserve_all"

        self.config["word_to_pdf_mode"] = new_mode
        self.config_manager.save_config(self.config)

        mode_name = self.translate_text("Conserver toute la mise en forme") if new_mode == "preserve_all" else self.translate_text("Texte seulement")
        self.status_bar.showMessage(f"Mode Word->PDF: {mode_name}", 3000)

    def setup_tooltips_with_shortcuts(self):
        """Configure tooltips with keyboard shortcuts"""

        self.add_files_btn.setToolTip(self.translate_text("Charger des fichiers (Ctrl+O)"))
        self.add_folder_btn.setToolTip(self.translate_text("Ajouter un dossier (Ctrl+P)"))
        self.remove_file_btn.setToolTip(self.translate_text("Supprimer les fichiers sélectionnés"))
        self.clear_all_btn.setToolTip(self.translate_text("Effacer toute la liste (Ctrl+Delete)"))

        self.pdf_to_word_btn.setToolTip(self.translate_text("Convertir PDF en Word (Ctrl+Shift+C)"))
        self.word_to_pdf_btn.setToolTip(self.translate_text("Convertir Word en PDF (Ctrl+Shift+C)"))
        self.image_to_pdf_btn.setToolTip(self.translate_text("Convertir des images en PDF (Ctrl+Shift+C)"))
        self.more_conversions_btn.setToolTip(self.translate_text("Plus d'options de conversion (Ctrl+Shift+C)"))

        self.merge_pdf_btn.setToolTip(self.translate_text("Fusionner des fichiers PDF"))
        self.merge_word_btn.setToolTip(self.translate_text("Fusionner des documents Word"))

        self.split_pdf_btn.setToolTip(self.translate_text("Diviser un PDF"))
        self.protect_pdf_btn.setToolTip(self.translate_text("Protéger un PDF avec mot de passe"))
        self.compress_files_btn.setToolTip(self.translate_text("Compresser des fichiers"))

        self.batch_convert_btn.setToolTip(self.translate_text("Conversion par lot"))
        self.batch_rename_btn.setToolTip(self.translate_text("Renommage par lot"))

        self.dashboard_btn.setToolTip(self.translate_text("Tableau de bord et statistiques"))
        self.history_btn.setToolTip(self.translate_text("Historique des conversions (Ctrl+H)"))
        self.templates_btn.setToolTip(self.translate_text("Modèles et templates"))
        self.achievements_btn.setToolTip(self.translate_text("Succès et réalisations"))

        self.settings_btn.setToolTip(self.translate_text("Paramètres de l'application (Ctrl+,)"))

        self.new_action.setToolTip(self.translate_text("Nouveau projet (Ctrl+N)"))
        self.open_action.setToolTip(self.translate_text("Ouvrir un projet existant (Ctrl+Shift+O)"))
        self.save_action.setToolTip(self.translate_text("Enregistrer le projet (Ctrl+S)"))
        self.theme_action.setToolTip(self.translate_text("Basculer entre mode clair et sombre"))
        self.language_action.setToolTip(self.translate_text("Changer la langue"))

    def launch_conversion_options(self):
        """
        Triggers the dialog to choose the conversion action.
        (This is the new function connected to Ctrl+Shift+C)
        """
        dialog = ConversionOptionsDialog(self)
        dialog.conversion_chosen.connect(self.execute_chosen_conversion)
        dialog.exec()

    def execute_chosen_conversion(self, method_name):
        """
        Dynamically executes the chosen conversion method (e.g. launch_pdf_to_word_conversion).
        """
        conversion_method = getattr(self, method_name, None)
        
        if conversion_method and callable(conversion_method):
            print(f"[DEBUG] Launching method: {method_name}")
            conversion_method()
        else:
            QMessageBox.warning(self, self.translate_text("Erreur Interne"), 
                                self.translate_text(f"Méthode de conversion '{method_name}' non trouvée ou non appelable."))

    def launch_pdf_to_word_conversion(self):
        """Launch PDF to Word conversion"""
        print("Launching PDF -> Word conversion")
        self.convert_pdf_to_word()

    def launch_word_to_pdf_conversion(self):
        """Launch Word to PDF conversion"""
        print("Launching Word -> PDF conversion")
        self.convert_word_to_pdf()

    def launch_image_to_pdf_conversion(self):
        """Launch Images to PDF conversion"""
        print("Launching Images -> PDF conversion")
        self.convert_images_to_pdf()
        
    def launch_merge_pdf(self):
        """Launch PDF merge"""
        print("Launching PDF merge")
        self.merge_pdfs()

    def launch_merge_word(self):
        """Launch Word merge"""
        print("Launching Word merge")
        self.merge_word_docs()

    def launch_office_optimization(self):
        """Launch file optimization for all supported types"""
        print("Launching file optimization")

        SUPPORTED_EXTS = {
            'office': ['.pdf', '.docx', '.doc', '.pptx', '.ppt', '.xlsx', '.xls'],
            'image':  ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp', '.gif'],
            'audio':  ['.mp3', '.wav', '.aac', '.flac', '.ogg'],
            'video':  ['.mp4', '.avi', '.mkv', '.mov', '.webm'],
            'web':    ['.json', '.html', '.htm'],
            'ebook':  ['.epub'],
        }
        ALL_SUPPORTED = [e for exts in SUPPORTED_EXTS.values() for e in exts]

        selected_items = self.files_list_widget.selectedItems()
        files_to_process = []

        if selected_items:
            for i in range(self.files_list_widget.count()):
                item = self.files_list_widget.item(i)
                if item.isSelected():
                    files_to_process.append(item.data(Qt.UserRole))
        else:
            files_to_process = self.files_list.copy()
        office_files = [f for f in files_to_process
                        if Path(f).suffix.lower() in ALL_SUPPORTED]

        if not office_files:
            if selected_items:
                msg = self.translate_text(
                    "Aucun fichier optimisable sélectionné. "
                    "Formats supportés : PDF, Word, PowerPoint, Excel, images, audio, vidéo, JSON, HTML, EPUB.")
            else:
                msg = self.translate_text(
                    "Aucun fichier optimisable dans la liste. "
                    "Ajoutez des fichiers PDF, Word, PowerPoint, Excel, images, audio, vidéo, JSON, HTML ou EPUB d'abord.")
            QMessageBox.warning(self, self.translate_text("Avertissement"), msg)
            return
        
        _def_id, _ = self.template_manager.get_default_template("Optimisation de fichiers") if self.template_manager is not None else (None, None)
        if _def_id:
            (self._ensure_template_manager() or object()).apply_template(_def_id, self)

        if hasattr(self, 'active_templates') and 'office_optimization' in self.active_templates:
            _t = self.active_templates['office_optimization']
            self.optimize_office_files(
                office_files,
                _t.get('optimization_type', 2),
                _t.get('quality_level', 1),
                _t.get('remove_metadata', True),
                _t.get('compress_images', True),
                _t.get('keep_backup', True),
            )
            return

        d = QDialog(self)
        d.setWindowTitle(self.translate_text("Optimiser les fichiers"))
        d.setMinimumWidth(430)
        root = QVBoxLayout(d)
        root.setSpacing(14)
        root.setContentsMargins(20, 20, 20, 20)

        _ext_cat = {}
        for cat, exts in SUPPORTED_EXTS.items():
            for e in exts:
                _ext_cat[e] = cat
        cat_counts = {}
        for f in office_files:
            cat = _ext_cat.get(Path(f).suffix.lower(), "autre")
            cat_counts[cat] = cat_counts.get(cat, 0) + 1
        cat_labels = {
            'office': self.translate_text("bureautique"),
            'image':  self.translate_text("image(s)"),
            'audio':  self.translate_text("audio"),
            'video':  self.translate_text("vidéo"),
            'web':    self.translate_text("web"),
            'ebook':  self.translate_text("ebook"),
        }
        summary_parts = [f"{v} {cat_labels.get(k, k)}" for k, v in cat_counts.items()]
        summary_text  = f"<b>{len(office_files)}</b> fichier(s) : {', '.join(summary_parts)}"

        summary_lbl = QLabel(summary_text)
        summary_lbl.setWordWrap(True)
        summary_lbl.setStyleSheet(
            "padding:10px 14px; border-radius:8px;"
            "background:rgba(110,190,255,0.10); color:#5b9bd5; font-size:12px;"
        )
        root.addWidget(summary_lbl)

        # Mode (radio buttons)
        mode_group = QGroupBox(self.translate_text("Mode d'optimisation"))
        mode_layout = QVBoxLayout(mode_group)
        mode_layout.setSpacing(6)

        radio_compress = QRadioButton("🗜  " + self.translate_text("Compression  —  réduit la taille du fichier"))
        radio_clean    = QRadioButton("🧹  " + self.translate_text("Nettoyage  —  supprime uniquement les métadonnées"))
        radio_both     = QRadioButton("⚡  " + self.translate_text("Compression + Nettoyage  —  recommandé"))
        radio_both.setChecked(True)

        for r in (radio_compress, radio_clean, radio_both):
            r.setStyleSheet("font-size:13px; padding:2px 0;")
            mode_layout.addWidget(r)
        root.addWidget(mode_group)

        # Quality slider
        quality_group = QGroupBox(self.translate_text("Niveau de compression"))
        quality_outer = QVBoxLayout(quality_group)

        quality_labels_list = [
            self.translate_text("Haute qualité  (gain modéré)"),
            self.translate_text("Équilibré  (recommandé)"),
            self.translate_text("Maximum  (qualité réduite)"),
        ]

        from PySide6.QtWidgets import QSlider

        _slider_colors = {
            0: ("#4caf82", "rgba(76,175,130,0.18)"),
            1: ("#5b9bd5", "rgba(91,155,213,0.18)"),
            2: ("#e07b54", "rgba(224,123,84,0.18)"),
        }

        def _slider_stylesheet(color, track_bg):
            return f"""
                QSlider::groove:horizontal {{
                    height: 3px;
                    background: transparent;
                    border: none;
                }}
                QSlider::sub-page:horizontal {{
                    background: {color};
                    height: 3px;
                    border-radius: 2px;
                }}
                QSlider::add-page:horizontal {{
                    background: {track_bg};
                    height: 3px;
                    border-radius: 2px;
                }}
                QSlider::handle:horizontal {{
                    background: {color};
                    border: 2px solid #ffffff;
                    width: 13px;
                    height: 13px;
                    margin: -5px 0;
                    border-radius: 7px;
                }}
                QSlider::handle:horizontal:hover {{
                    background: white;
                    border: 2px solid {color};
                }}
            """

        quality_slider = QSlider(Qt.Horizontal)
        quality_slider.setMinimum(0)
        quality_slider.setMaximum(2)
        quality_slider.setValue(1)
        quality_slider.setTickPosition(QSlider.NoTicks)
        quality_slider.setTickInterval(1)
        quality_slider.setPageStep(1)
        quality_slider.setStyleSheet(_slider_stylesheet(*_slider_colors[1]))

        quality_val_lbl = QLabel(quality_labels_list[1])
        quality_val_lbl.setAlignment(Qt.AlignCenter)
        quality_val_lbl.setStyleSheet(
            f"font-size:12px; font-weight:600; color:{_slider_colors[1][0]}; padding:2px 0;")

        tick_row = QHBoxLayout()
        tick_row.setContentsMargins(4, 0, 4, 0)
        roman_labels = []
        for roman in ["I", "II", "III"]:
            tl = QLabel(roman)
            tl.setAlignment(Qt.AlignCenter)
            tl.setStyleSheet(
                f"font-size:13px; font-weight:700; color:{_slider_colors[1][0]}; letter-spacing:1px;")
            tick_row.addWidget(tl)
            roman_labels.append(tl)

        def _on_slider(v):
            color, track_bg = _slider_colors[v]
            quality_val_lbl.setText(quality_labels_list[v])
            quality_val_lbl.setStyleSheet(
                f"font-size:12px; font-weight:600; color:{color}; padding:2px 0;")
            quality_slider.setStyleSheet(_slider_stylesheet(color, track_bg))
            for lbl in roman_labels:
                lbl.setStyleSheet(
                    f"font-size:13px; font-weight:700; color:{color}; letter-spacing:1px;")

        quality_slider.valueChanged.connect(_on_slider)

        def _on_mode_change():
            quality_group.setEnabled(not radio_clean.isChecked())

        radio_clean.toggled.connect(_on_mode_change)

        quality_outer.addWidget(quality_slider)
        quality_outer.addLayout(tick_row)
        quality_outer.addWidget(quality_val_lbl)
        root.addWidget(quality_group)

        options_group = QGroupBox(self.translate_text("Options"))
        options_layout = QVBoxLayout(options_group)
        options_layout.setSpacing(6)

        remove_metadata_check = AnimatedCheckBox(self.translate_text("Supprimer les métadonnées personnelles"))
        remove_metadata_check.setChecked(True)

        compress_images_check = AnimatedCheckBox(self.translate_text("Recompresser les images intégrées"))
        compress_images_check.setChecked(True)

        keep_backup_check = AnimatedCheckBox(self.translate_text("Garder une copie des originaux"))
        keep_backup_check.setChecked(True)

        for cb in (remove_metadata_check, compress_images_check, keep_backup_check):
            cb.setStyleSheet("font-size:12px;")
            options_layout.addWidget(cb)
        root.addWidget(options_group)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        btn_cancel = QPushButton(self.translate_text("Annuler"))
        btn_cancel.setMinimumHeight(38)
        _apply_dialog_btn(btn_cancel, "BtnCancelGlassy")

        btn_ok = QPushButton("✓  " + self.translate_text("Optimiser"))
        btn_ok.setMinimumHeight(38)
        btn_ok.setStyleSheet(
            "QPushButton{background:#28a745;color:white;border:none;"
            "border-radius:7px;font-weight:bold;padding:0 18px;}"
            "QPushButton:hover{background:#218838;}"
            "QPushButton:pressed{background:#1e7e34;}"
        )

        btn_cancel.clicked.connect(d.reject)
        btn_ok.clicked.connect(d.accept)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)
        root.addLayout(btn_row)

        if d.exec() == QDialog.Accepted:
            if radio_compress.isChecked():
                optimization_type = 0
            elif radio_clean.isChecked():
                optimization_type = 1
            else:
                optimization_type = 2

            quality_level   = quality_slider.value()
            remove_metadata = remove_metadata_check.isChecked()
            compress_images = compress_images_check.isChecked()
            keep_backup     = keep_backup_check.isChecked()

            self.optimize_office_files(
                office_files,
                optimization_type,
                quality_level,
                remove_metadata,
                compress_images,
                keep_backup
            )

    def select_all_files(self):
        """Select all files in the list"""
        self.files_list_widget.selectAll()

    def close_secondary_windows(self):
        """Close secondary windows (History, Dashboard, etc.) with Escape"""
        if self.dashboard_dialog and self.dashboard_dialog.isVisible():
            self.dashboard_dialog.close()
        elif self.history_dialog and self.history_dialog.isVisible():
            self.history_dialog.close()
        elif self.templates_dialog and self.templates_dialog.isVisible():
            self.templates_dialog.close()
        elif self.achievements_dialog and self.achievements_dialog.isVisible():
            self.achievements_dialog.close()
        elif self.preview_dialog and self.preview_dialog.isVisible():
            self.preview_dialog.close()

    def create_menu_bar(self):
        """Create the menu bar with shortcuts"""
        menubar = self.menuBar()
        menubar.clear()

        file_menu_title = self.translate_text("&Fichier")
        file_menu = menubar.addMenu(file_menu_title)
        
        new_action = QAction(self.translate_text("&Nouveau projet"), self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_project)
        new_action.setToolTip(self.translate_text("Créer un nouveau projet (Ctrl+N)"))
        file_menu.addAction(new_action)
        
        open_action = QAction(self.translate_text("&Ouvrir projet..."), self)
        open_action.setShortcut("Ctrl+Shift+O")
        open_action.triggered.connect(self.open_project)
        open_action.setToolTip(self.translate_text("Ouvrir un projet existant (Ctrl+Shift+O)"))
        file_menu.addAction(open_action)
        
        save_action = QAction(self.translate_text("&Enregistrer projet"), self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_project)
        save_action.setToolTip(self.translate_text("Enregistrer le projet courant (Ctrl+S)"))
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        add_files_action = QAction(self.translate_text("&Ajouter des fichiers..."), self)
        add_files_action.setShortcut("Ctrl+O")
        add_files_action.triggered.connect(self.add_files)
        add_files_action.setToolTip(self.translate_text("Ajouter des fichiers au projet (Ctrl+O)"))
        file_menu.addAction(add_files_action)
        
        add_folder_action = QAction(self.translate_text("Ajouter un &dossier..."), self)
        add_folder_action.setShortcut("Ctrl+P")
        add_folder_action.triggered.connect(self.add_folder)
        add_folder_action.setToolTip(self.translate_text("Ajouter un dossier complet (Ctrl+P)"))
        file_menu.addAction(add_folder_action)
        
        file_menu.addSeparator()
        
        select_all_action = QAction(self.translate_text("&Tout sélectionner"), self)
        select_all_action.setShortcut("Ctrl+A")
        select_all_action.triggered.connect(self.select_all_files)
        select_all_action.setToolTip(self.translate_text("Sélectionner tous les fichiers (Ctrl+A)"))
        file_menu.addAction(select_all_action)
        
        clear_action = QAction(self.translate_text("&Effacer la liste"), self)
        clear_action.setShortcut("Ctrl+Delete")
        clear_action.triggered.connect(self.clear_file_list)
        clear_action.setToolTip(self.translate_text("Effacer toute la liste de fichiers (Ctrl+Delete)"))
        file_menu.addAction(clear_action)
        
        file_menu.addSeparator()
        
        quit_action = QAction(self.translate_text("&Quitter"), self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        quit_action.setToolTip(self.translate_text("Quitter l'application (Ctrl+Q)"))
        file_menu.addAction(quit_action)
        
        edit_menu_title = self.translate_text("&Edition")
        edit_menu = menubar.addMenu(edit_menu_title)
        
        convert_action = QAction(self.translate_text("&Lancer la conversion"), self)
        convert_action.setShortcut("Ctrl+Shift+C")
        convert_action.triggered.connect(self.launch_conversion_options)
        convert_action.setToolTip(self.translate_text("Lancer la conversion des fichiers (Ctrl+Shift+C)"))
        edit_menu.addAction(convert_action)
        
        view_menu_title = self.translate_text("&Affichage")
        view_menu = menubar.addMenu(view_menu_title)
        
        settings_action = QAction(self.translate_text("&Paramètres..."), self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self.show_settings)
        settings_action.setToolTip(self.translate_text("Ouvrir les paramètres (Ctrl+,)"))
        view_menu.addAction(settings_action)
        
        history_action = QAction(self.translate_text("&Historique..."), self)
        history_action.setShortcut("Ctrl+H")
        history_action.triggered.connect(self.show_history)
        history_action.setToolTip(self.translate_text("Ouvrir l'historique des conversions (Ctrl+H)"))
        view_menu.addAction(history_action)
        
        dashboard_action = QAction(self.translate_text("&Tableau de bord..."), self)
        dashboard_action.triggered.connect(self.show_dashboard)
        dashboard_action.setToolTip(self.translate_text("Ouvrir le tableau de bord et statistiques"))
        view_menu.addAction(dashboard_action)
        
        templates_action = QAction(self.translate_text("&Modèles..."), self)
        templates_action.triggered.connect(self.show_templates)
        templates_action.setToolTip(self.translate_text("Ouvrir les modèles et templates"))
        view_menu.addAction(templates_action)
        
        achievements_action = QAction(self.translate_text("&Succès..."), self)
        achievements_action.triggered.connect(self.show_achievements)
        achievements_action.setToolTip(self.translate_text("Ouvrir les succès et réalisations"))
        view_menu.addAction(achievements_action)
        
        view_menu.addSeparator()
        
        theme_action = QAction(self.translate_text("&Basculer le thème"), self)
        theme_action.setShortcut("F2")
        theme_action.triggered.connect(self.toggle_theme)
        theme_action.setToolTip(self.translate_text("Basculer entre mode clair et sombre (F2)"))
        view_menu.addAction(theme_action)
        
        language_action = QAction(self.translate_text("&Changer la langue"), self)
        language_action.setShortcut("F3")
        language_action.triggered.connect(self.toggle_language)
        language_action.setToolTip(self.translate_text("Changer la langue de l'interface (F3)"))
        view_menu.addAction(language_action)
        
        help_action = QAction(self.translate_text("A&ide"), self)
        help_action.setShortcut("F1")
        help_action.triggered.connect(self.show_shortcuts_help)
        help_action.setToolTip(self.translate_text("Afficher la liste des raccourcis clavier (F1)"))
        menubar.addAction(help_action)

    def show_shortcuts_help(self):
        """Display a help window with all shortcuts"""
        t = self.translate_text
        
        shortcuts_text = f"""
        <h2>{t("Raccourcis clavier - File Converter Pro")}</h2>
        
        <h3>{t("Gestion de projets")}</h3>
        <ul>
        <li><b>Ctrl+N</b> : {t("Nouveau projet")}</li>
        <li><b>Ctrl+Shift+O</b> : {t("Ouvrir un projet")}</li>
        <li><b>Ctrl+S</b> : {t("Enregistrer le projet")}</li>
        </ul>
        
        <h3>{t("Gestion des fichiers")}</h3>
        <ul>
        <li><b>Ctrl+O</b> : {t("Ajouter des fichiers")}</li>
        <li><b>Ctrl+P</b> : {t("Ajouter un dossier")}</li>
        <li><b>Ctrl+A</b> : {t("Tout sélectionner")}</li>
        <li><b>Ctrl+Delete</b> : {t("Effacer la liste")}</li>
        </ul>
        
        <h3>{t("Conversions")}</h3>
        <ul>
        <li><b>Ctrl+Shift+C</b> : {t("Lancer la conversion")}</li>
        </ul>
        
        <h3>{t("Navigation")}</h3>
        <ul>
        <li><b>Ctrl+H</b> : {t("Historique")}</li>
        <li><b>Ctrl+,</b> : {t("Paramètres")}</li>
        <li><b>F2</b> : {t("Basculer le thème")}</li>
        <li><b>F3</b> : {t("Changer la langue")}</li>
        <li><b>{t("Échap")}</b> : {t("Fermer les fenêtres secondaires")}</li>
        </ul>
        
        <h3>{t("Application")}</h3>
        <ul>
        <li><b>Ctrl+Q</b> : {t("Quitter")}</li>
        <li><b>F1</b> : {t("Aide des raccourcis")}</li>
        </ul>
        <h3>{t("Support en ligne")}</h3>
        <p><a href="https://github.com/Hyacinthe-primus/File_Converter_Pro/wiki/How-To-Use">{t("Guide d'utilisation complet")}</a></p>
        """
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(t("Raccourcis clavier"))
        msg_box.setTextFormat(Qt.RichText)
        msg_box.setText(shortcuts_text)
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec()

    def setup_ui(self):
        self.setWindowTitle(self.translate_text("File Converter Pro - Convertisseur de Fichiers Professionnel"))
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1000, 680)

        self.set_application_icon()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        central_widget.installEventFilter(self)

        root = QHBoxLayout(central_widget)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        sidebar = QWidget()
        sidebar.setFixedWidth(64)
        sidebar.setObjectName("Sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        sidebar_layout.setAlignment(Qt.AlignTop)

        logo_lbl = QLabel("⾕")
        logo_lbl.setObjectName("LogoLabel")
        logo_lbl.setAlignment(Qt.AlignCenter)
        logo_lbl.setFixedHeight(64)
        sidebar_layout.addWidget(logo_lbl)

        div0 = QFrame()
        div0.setFrameShape(QFrame.HLine)
        div0.setFixedHeight(1)
        div0.setStyleSheet("background: rgba(255,255,255,0.07); margin: 0 12px;")
        sidebar_layout.addWidget(div0)
        sidebar_layout.addSpacing(8)

        def _nav_btn(icon, tip):
            b = QPushButton(icon)
            b.setFixedSize(48, 48)
            b.setToolTip(tip)
            b.setObjectName("NavBtn")
            return b

        self.nav_dashboard_btn  = _nav_btn("📊", self.translate_text("Tableau de Bord"))
        self.nav_history_btn    = _nav_btn("📋", self.translate_text("Historique"))
        self.nav_templates_btn  = _nav_btn("🎨", self.translate_text("Modèles"))
        self.nav_achievements_btn = _nav_btn("🏆", self.translate_text("Trophées"))
        self.nav_donate_btn = _nav_btn("❤️", self.translate_text("Soutenir le développement"))

        for b in [self.nav_dashboard_btn, self.nav_history_btn,
                  self.nav_templates_btn, self.nav_achievements_btn,
                  self.nav_donate_btn]:
            sidebar_layout.addWidget(b, alignment=Qt.AlignHCenter)

        sidebar_layout.addStretch()

        self.nav_settings_btn = _nav_btn("⚙️", self.translate_text("Paramètres"))
        sidebar_layout.addWidget(self.nav_settings_btn, alignment=Qt.AlignHCenter)
        sidebar_layout.addSpacing(12)

        root.addWidget(sidebar)

        main_area = QWidget()
        main_area.setObjectName("MainArea")
        main_col = QVBoxLayout(main_area)
        main_col.setContentsMargins(0, 0, 0, 0)
        main_col.setSpacing(0)

        topbar = QWidget()
        topbar.setFixedHeight(52)
        topbar.setObjectName("TopBar")
        topbar_layout = QHBoxLayout(topbar)
        topbar_layout.setContentsMargins(20, 0, 20, 0)
        topbar_layout.setSpacing(12)

        title_lbl = QLabel(self.translate_text("File Converter Pro"))
        title_lbl.setObjectName("TitleLabel")
        topbar_layout.addWidget(title_lbl)

        self.project_name_lbl = QLabel()
        self.project_name_lbl.setObjectName("ProjectNameLabel")
        self.project_name_lbl.setVisible(False)
        self.project_name_lbl.setCursor(Qt.PointingHandCursor)
        self.project_name_lbl.setToolTip(self.translate_text("Cliquez pour renommer / ajouter des notes"))
        self.project_name_lbl.mousePressEvent = lambda e: self.edit_project_info()
        topbar_layout.addWidget(self.project_name_lbl)

        topbar_layout.addStretch()

        self.file_counter = QLabel(self.translate_text("Aucun fichier sélectionné"))
        self.file_counter.setObjectName("FileCounter")
        topbar_layout.addWidget(self.file_counter)

        main_col.addWidget(topbar)

        accent_line = QFrame()
        accent_line.setFixedHeight(1)
        accent_line.setStyleSheet("background: rgba(232,255,107,0.15);")
        main_col.addWidget(accent_line)

        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(16, 16, 16, 16)
        content_layout.setSpacing(14)

        self.create_left_panel(content_layout)
        self.create_right_panel(content_layout)

        main_col.addWidget(content_widget, 1)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(self.translate_text("Prêt - Sélectionnez des fichiers pour commencer"))

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setFixedHeight(16)
        self.progress_bar.setFixedWidth(180)

        self.progress_pct_label = QLabel("0%")
        self.progress_pct_label.setObjectName("ProgressPctLabel")
        self.progress_pct_label.setVisible(False)
        self.progress_pct_label.setFixedWidth(36)
        self.progress_pct_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.progress_pct_label.setStyleSheet(
            "font-size: 11px; font-weight: 700; padding: 0 2px;"
        )
        self.progress_bar.valueChanged.connect(
            lambda v: self.progress_pct_label.setText(f"{v}%")
        )

        self.status_bar.addPermanentWidget(self.progress_pct_label)
        self.status_bar.addPermanentWidget(self.progress_bar)

        root.addWidget(main_area, 1)

        self.create_toolbar()
        self.connect_signals()
        self.create_menu_bar()
        self.setup_shortcuts()
        self.setup_tooltips_with_shortcuts()

        self.nav_dashboard_btn.clicked.connect(self.show_dashboard)
        self.nav_history_btn.clicked.connect(self.show_history)
        self.nav_templates_btn.clicked.connect(self.show_templates)
        self.nav_achievements_btn.clicked.connect(self.show_achievements)
        self.nav_donate_btn.clicked.connect(self.show_donate)
        self.nav_settings_btn.clicked.connect(self.show_settings)

        QTimer.singleShot(120, self._animate_startup)
        QTimer.singleShot(300, self._connect_button_animations)

    def closeEvent(self, event):
        """Override closeEvent to save window geometry and state"""
        if self.isMaximized():
            self.config["window_maximized"] = True
        else:
            self.config["window_maximized"] = False
            geom = self.geometry()
            self.config["window_geometry"] = {
                "x":      geom.x(),
                "y":      geom.y(),
                "width":  geom.width(),
                "height": geom.height(),
            }
        self.config_manager.save_config(self.config)
        super().closeEvent(event)


    def _animate_startup(self):
        """Fade in the entire window on startup — safe, no QPainter conflict."""
        try:
            from PySide6.QtCore import QPropertyAnimation, QEasingCurve
            self.setWindowOpacity(0.0)
            anim = QPropertyAnimation(self, b"windowOpacity")
            anim.setDuration(500)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.setEasingCurve(QEasingCurve.OutCubic)
            self._startup_window_anim = anim
            anim.start()
        except Exception as e:
            print(f"[ANIM] Startup error: {e}")
            self.setWindowOpacity(1.0)

        QTimer.singleShot(300, self._pulse_logo)

    def _pulse_logo(self):
        """Subtle pulse of the FC logo at startup only."""
        try:
            logo = self.findChild(QLabel, "LogoLabel")
            if not logo:
                return
            is_dark = getattr(self, 'dark_mode', True)
            normal_color = "#e8ff6b" if is_dark else "#2d2dc8"
            dim_color    = "rgba(232,255,107,0.3)" if is_dark else "rgba(45,45,200,0.3)"
            base = ("font-family:'Segoe UI','SF Pro Display',Arial,sans-serif;"
                    "font-size:16px;font-weight:900;"
                    "letter-spacing:1.5px;background:transparent;")

            def _dim():  logo.setStyleSheet(f"{base}color:{dim_color};")
            def _norm(): logo.setStyleSheet(f"{base}color:{normal_color};")

            QTimer.singleShot(0,   _dim)
            QTimer.singleShot(200, _norm)
            QTimer.singleShot(350, _dim)
            QTimer.singleShot(550, _norm)
        except Exception as e:
            print(f"[ANIM] Logo pulse error: {e}")

    def _animate_button_press(self, btn):
        """Micro-animation on click — does not touch the text color."""
        try:
            original = btn.styleSheet()
            btn.setStyleSheet(original + " QPushButton { opacity: 0.65; }")
            QTimer.singleShot(120, lambda: btn.setStyleSheet(original))
        except Exception:
            pass

    def _connect_button_animations(self):
        """Connect micro-animations to all action buttons."""
        try:
            action_btns = [
                self.pdf_to_word_btn, self.word_to_pdf_btn, self.image_to_pdf_btn,
                self.merge_pdf_btn, self.merge_word_btn,
                self.split_pdf_btn, self.protect_pdf_btn, self.compress_files_btn,
                self.batch_convert_btn, self.batch_rename_btn,
                self.more_conversions_btn,
            ]
            for btn in action_btns:
                btn.clicked.connect(lambda checked=False, b=btn: self._animate_button_press(b))
        except Exception as e:
            print(f"[ANIM] Button connect error: {e}")

    def set_application_icon(self):
        """Set the application icon with robust fallback handling."""
        try:
            possible_paths = [
                "icon.ico",
                os.path.join(os.path.dirname(__file__), "icon.ico"),
                os.path.join(os.getcwd(), "icon.ico")
            ]
            
            icon_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    icon_path = path
                    break
            
            if icon_path:
                self.setWindowIcon(QIcon(icon_path))
                QApplication.setWindowIcon(QIcon(icon_path))
            else:
                self.create_default_icon()
        except Exception as e:
            print(f"Error loading icon: {e}")
            self.create_default_icon()

    def create_default_icon(self):
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor(0, 120, 215))
        painter = QPainter(pixmap)
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Arial", 20, QFont.Bold))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "F")
        painter.end()
        self.setWindowIcon(QIcon(pixmap))
        QApplication.setWindowIcon(QIcon(pixmap))

    def eventFilter(self, source, event):
        """Event filter to detect clicks on empty spaces"""
        from PySide6.QtCore import QEvent
        from PySide6.QtGui import QMouseEvent
        
        if event.type() == QEvent.MouseButtonPress and isinstance(event, QMouseEvent):
            if self._is_empty_space_click(source, event):
                self.files_list_widget.clearSelection()
                return True
        
        return super().eventFilter(source, event)

    def _is_empty_space_click(self, source, event):
        """Check if the click is on an empty space of the application"""
        interactive_widgets = (
            QPushButton, QCheckBox, QRadioButton, QComboBox,
            QSpinBox, QLineEdit, QTextEdit, QTableWidget,
            QTreeWidget, QListWidget, QToolBar, QMenuBar,
            QStatusBar, QProgressBar, QTabWidget, QGroupBox
        )
        
        if isinstance(source, interactive_widgets):
            return False
        
        if source == self.files_list_widget:
            item = self.files_list_widget.itemAt(event.pos())
            if item is not None:
                return False
        
        return True

    def translate_text(self, text):
        return self.translation_manager.translate_text(text)

    def create_left_panel(self, parent_layout):
        left_panel = QGroupBox(self.translate_text("Gestion des Fichiers"))
        left_panel.setProperty("i18n_key", "Gestion des Fichiers")
        left_panel.setObjectName("FilePanel")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(10, 18, 10, 10)
        left_layout.setSpacing(10)

        hint_lbl = QLabel(self.translate_text("Fichiers sélectionnés (glissez-déposez depuis l'explorateur):"))
        hint_lbl.setProperty("i18n_key", "Fichiers sélectionnés (glissez-déposez depuis l'explorateur):")
        hint_lbl.setObjectName("HintLabel")
        hint_lbl.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(hint_lbl)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(0)
        scroll_area.setWidget(scroll_widget)

        self.files_list_widget = DraggableListWidget(translation_manager=self.translation_manager)
        self.files_list_widget.setMinimumHeight(200)
        self.files_list_widget.setSelectionMode(QListWidget.ExtendedSelection)
        self.files_list_widget.setIconSize(QSize(18, 18))
        scroll_layout.addWidget(self.files_list_widget)

        left_layout.addWidget(scroll_area, 1)

        def _file_btn(label, name):
            b = QPushButton(label)
            b.setMinimumHeight(34)
            b.setObjectName(name)
            return b

        self.add_files_btn   = _file_btn("📁 " + self.translate_text("Ajouter Fichiers"), "BtnFileAdd")
        self.add_folder_btn  = _file_btn("📂 " + self.translate_text("Ajouter Dossier"), "BtnFileFolder")
        self.remove_file_btn = _file_btn("🗑 "  + self.translate_text("Supprimer"), "BtnFileDel")
        self.clear_all_btn   = _file_btn("🧹 " + self.translate_text("Tout Effacer"), "BtnFileClear")
        self.add_files_btn.setProperty("i18n_key", "Ajouter Fichiers")
        self.add_folder_btn.setProperty("i18n_key", "Ajouter Dossier")
        self.remove_file_btn.setProperty("i18n_key", "Supprimer")
        self.clear_all_btn.setProperty("i18n_key", "Tout Effacer")

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        for b in [self.add_files_btn, self.add_folder_btn, self.remove_file_btn, self.clear_all_btn]:
            btn_row.addWidget(b)
        left_layout.addLayout(btn_row)

        parent_layout.addWidget(left_panel, 1)

    def create_right_panel(self, parent_layout):
        right_panel = QWidget()
        right_panel.setMinimumWidth(320)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(10)
        right_layout.setContentsMargins(0, 0, 0, 0)

        def _card(title):
            g = QGroupBox(title.upper())
            g.setObjectName("ActionCard")
            lay = QVBoxLayout(g)
            lay.setContentsMargins(8, 16, 8, 10)
            lay.setSpacing(8)
            return g, lay

        def _btn(label, name, h=36):
            b = QPushButton(label)
            b.setMinimumHeight(h)
            b.setObjectName(name)
            return b

        conv_card, conv_lay = _card(self.translate_text("Conversion de Fichiers"))
        conv_card.setProperty("i18n_key", "Conversion de Fichiers")

        ocr_row = QHBoxLayout()
        self.ocr_checkbox = QCheckBox(self.translate_text("Utiliser OCR pour les images dans les PDF"))
        self.ocr_checkbox.setProperty("i18n_key", "Utiliser OCR pour les images dans les PDF")
        self.ocr_checkbox.setChecked(False)
        self.ocr_checkbox.setEnabled(False)
        self.ocr_checkbox.setToolTip(self.translate_text("Cette fonctionnalité est en cours de développement"))
        self.ocr_checkbox.setObjectName("OcrCheckbox")
        ocr_row.addWidget(self.ocr_checkbox)
        ocr_row.addStretch()
        conv_lay.addLayout(ocr_row)

        conv_grid = QHBoxLayout()
        conv_grid.setSpacing(7)
        self.pdf_to_word_btn   = _btn("📄→📝 " + self.translate_text("PDF → Word"), "BtnBlue")
        self.word_to_pdf_btn   = _btn("📝→📄 " + self.translate_text("Word → PDF"), "BtnBlue")
        self.image_to_pdf_btn  = _btn("🖼→📄 "  + self.translate_text("Images → PDF"), "BtnBlue")
        self.pdf_to_word_btn.setProperty("i18n_key", "PDF → Word")
        self.word_to_pdf_btn.setProperty("i18n_key", "Word → PDF")
        self.image_to_pdf_btn.setProperty("i18n_key", "Images → PDF")
        for b in [self.pdf_to_word_btn, self.word_to_pdf_btn, self.image_to_pdf_btn]:
            conv_grid.addWidget(b)
        conv_lay.addLayout(conv_grid)

        self.more_conversions_btn = QPushButton("✦  " + self.translate_text("Plus de conversions"))
        self.more_conversions_btn.setProperty("i18n_key", "Plus de conversions")
        self.more_conversions_btn.setMinimumHeight(32)
        self.more_conversions_btn.setObjectName("BtnMoreConv")
        self.more_conversions_btn.clicked.connect(self.show_advanced_conversions)
        conv_lay.addWidget(self.more_conversions_btn)
        right_layout.addWidget(conv_card)

        merge_card, merge_lay = _card(self.translate_text("Fusion de Fichiers"))
        merge_card.setProperty("i18n_key", "Fusion de Fichiers")
        merge_row = QHBoxLayout()
        merge_row.setSpacing(7)
        self.merge_pdf_btn  = _btn("🔗 " + self.translate_text("Fusionner PDF"), "BtnTeal")
        self.merge_word_btn = _btn("🔗 " + self.translate_text("Fusionner Word"), "BtnTeal")
        self.merge_pdf_btn.setProperty("i18n_key", "Fusionner PDF")
        self.merge_word_btn.setProperty("i18n_key", "Fusionner Word")
        merge_row.addWidget(self.merge_pdf_btn)
        merge_row.addWidget(self.merge_word_btn)
        merge_lay.addLayout(merge_row)
        right_layout.addWidget(merge_card)

        adv_card, adv_lay = _card(self.translate_text("Fonctionnalités Avancées"))
        adv_card.setProperty("i18n_key", "Fonctionnalités Avancées")
        adv_row = QHBoxLayout()
        adv_row.setSpacing(7)
        self.split_pdf_btn      = _btn("✂️ " + self.translate_text("Diviser PDF"), "BtnOrange")
        self.protect_pdf_btn    = _btn("🔒 " + self.translate_text("Protéger PDF"), "BtnOrange")
        self.compress_files_btn = _btn("🗜 "  + self.translate_text("Compresser Fichiers"), "BtnOrange")
        self.split_pdf_btn.setProperty("i18n_key", "Diviser PDF")
        self.protect_pdf_btn.setProperty("i18n_key", "Protéger PDF")
        self.compress_files_btn.setProperty("i18n_key", "Compresser Fichiers")
        for b in [self.split_pdf_btn, self.protect_pdf_btn, self.compress_files_btn]:
            adv_row.addWidget(b)
        adv_lay.addLayout(adv_row)
        right_layout.addWidget(adv_card)

        batch_card, batch_lay = _card(self.translate_text("Opérations par Lots"))
        batch_card.setProperty("i18n_key", "Opérations par Lots")
        batch_row = QHBoxLayout()
        batch_row.setSpacing(7)
        self.batch_convert_btn = _btn("🔄 " + self.translate_text("Conversion par Lot"), "BtnViolet")
        self.batch_rename_btn  = _btn("📝 " + self.translate_text("Renommer par Lot"), "BtnViolet")
        self.batch_convert_btn.setProperty("i18n_key", "Conversion par Lot")
        self.batch_rename_btn.setProperty("i18n_key", "Renommer par Lot")
        batch_row.addWidget(self.batch_convert_btn)
        batch_row.addWidget(self.batch_rename_btn)
        batch_lay.addLayout(batch_row)
        right_layout.addWidget(batch_card)
        right_layout.addStretch()

        self.settings_btn = QPushButton("⚙  " + self.translate_text("Paramètres"))
        self.settings_btn.setProperty("i18n_key", "Paramètres")
        self.settings_btn.setMinimumHeight(38)
        self.settings_btn.setObjectName("BtnSettings")
        right_layout.addWidget(self.settings_btn)

        self.dashboard_btn    = self.nav_dashboard_btn
        self.history_btn      = self.nav_history_btn
        self.templates_btn    = self.nav_templates_btn
        self.achievements_btn = self.nav_achievements_btn
        self._apply_achievements_btn_state()

        parent_layout.addWidget(right_panel, 0)

    def show_advanced_conversions(self):
        """Show the advanced conversions dialog"""
        from advanced_conversions import AdvancedConversionsDialog
        
        if not hasattr(self, 'advanced_conversions_dialog') or not self.advanced_conversions_dialog.isVisible():
            self.advanced_conversions_dialog = AdvancedConversionsDialog(self, self.current_language)
            # Connect signal for future implementation
            self.advanced_conversions_dialog.conversion_requested.connect(self.handle_advanced_conversion)
        
        self.advanced_conversions_dialog.show()
        self.advanced_conversions_dialog.raise_()
        self.advanced_conversions_dialog.activateWindow()

    def handle_advanced_conversion(self, conversion_type):
        """Handle advanced conversion request (placeholder)"""
        print(f"[DEBUG] Advanced conversion requested: {conversion_type}")

    def create_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        self.theme_action = QAction("🌙 " + self.translate_text("Mode Sombre"), self)
        self.language_action = QAction(self._get_language_label(self.current_language), self)
        
        toolbar.addAction(self.theme_action)
        toolbar.addAction(self.language_action)
        toolbar.addSeparator()
        
        self.new_action = QAction("🆕 " + self.translate_text("Nouveau Projet"), self)
        self.open_action = QAction("📂 " + self.translate_text("Ouvrir Projet"), self)
        self.save_action = QAction("💾 " + self.translate_text("Enregistrer Projet"), self)
        
        toolbar.addAction(self.new_action)
        toolbar.addAction(self.open_action)
        toolbar.addAction(self.save_action)

    def connect_signals(self):
        self.add_files_btn.clicked.connect(self.add_files)
        self.add_folder_btn.clicked.connect(self.add_folder)
        self.remove_file_btn.clicked.connect(self.remove_files)
        self.clear_all_btn.clicked.connect(self.clear_files)
        
        self.pdf_to_word_btn.clicked.connect(self.convert_pdf_to_word)
        self.word_to_pdf_btn.clicked.connect(self.convert_word_to_pdf)
        self.image_to_pdf_btn.clicked.connect(self.convert_images_to_pdf)
        self.more_conversions_btn.clicked.connect(self.show_advanced_conversions)
        self.merge_pdf_btn.clicked.connect(self.merge_pdfs)
        self.merge_word_btn.clicked.connect(self.merge_word_docs)
        
        self.split_pdf_btn.clicked.connect(self.split_pdf)
        self.protect_pdf_btn.clicked.connect(self.protect_pdf)
        self.compress_files_btn.clicked.connect(self.compress_files)
        
        self.batch_convert_btn.clicked.connect(self.batch_convert)
        self.batch_rename_btn.clicked.connect(self.batch_rename)
        
        self.dashboard_btn.clicked.connect(self.show_dashboard)
        self.history_btn.clicked.connect(self.show_history)
        self.templates_btn.clicked.connect(self.show_templates)
        self.achievements_btn.clicked.connect(self.show_achievements)
        
        self.settings_btn.clicked.connect(self.show_settings)
        
        self.theme_action.triggered.connect(self.toggle_theme)
        self.language_action.triggered.connect(self.toggle_language)
        
        self.new_action.triggered.connect(self.new_project)
        self.open_action.triggered.connect(self.open_project)
        self.save_action.triggered.connect(self.save_project)
        
        self.files_list_widget.model().rowsMoved.connect(self.update_file_order)
        
        self.files_list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.files_list_widget.customContextMenuRequested.connect(self.show_context_menu)
        self.files_list_widget.itemDoubleClicked.connect(self.show_file_preview)

        admin_shortcut = QShortcut(QKeySequence("Ctrl+Shift+Alt+A"), self)
        admin_shortcut.activated.connect(self.show_achievements_admin)
        admin_full_shortcut = QShortcut(QKeySequence("Ctrl+Shift+Alt+M"), self)
        admin_full_shortcut.activated.connect(self.show_achievements_admin_full)

    def show_context_menu(self, position):
        item = self.files_list_widget.itemAt(position)
        if item:
            menu = QMenu(self)
            
            file_path = item.data(Qt.UserRole)
            
            preview_action = menu.addAction("👁️ " + self.translate_text("Aperçu du fichier"))
            remove_action = menu.addAction("🗑️ " + self.translate_text("Supprimer"))
            
            action = menu.exec(self.files_list_widget.mapToGlobal(position))
            
            if action == preview_action:
                self.show_file_preview(item)
            elif action == remove_action:
                self.remove_selected_files()

    def show_file_preview(self, item):
        if self.config.get("show_file_previews", True):
            if isinstance(item, QListWidgetItem):
                file_path = item.data(Qt.UserRole)
                if file_path and os.path.exists(file_path):
                    self.preview_dialog = PreviewDialog(file_path, self, self.current_language)
                    self.preview_dialog.show()
                    self.achievement_system.record_preview()
                else:
                    QMessageBox.warning(
                        self, 
                        self.translate_text("Fichier introuvable"), 
                        self.translate_text(f"Le fichier n'existe pas ou le chemin est invalide: {file_path}")
                    )

    def remove_selected_files(self):
        self.remove_files()

    def _update_project_label(self):
        """Refresh the project name badge in the topbar."""
        lbl = getattr(self, 'project_name_lbl', None)
        if lbl is None:
            return
        name = self._project_data.get('name', '') if self._project_data else ''
        notes = self._project_data.get('notes', '') if self._project_data else ''
        if name:
            lbl.setText(f'🗁  {name}')
            tip = name
            if notes:
                tip += f"\n\n{notes}"
            created = self._project_data.get('created_at', '')
            if created:
                tip += f"\n\n{self.translate_text('Créé :')} {created[:10]}"
            lbl.setToolTip(tip)
            lbl.setVisible(True)
        else:
            lbl.setVisible(False)

    def edit_project_info(self):
        """Dialog to rename the project and edit its notes."""
        if not self._project_data:
            return

        d = QDialog(self)
        d.setWindowTitle(self.translate_text("Informations du projet"))
        d.setMinimumWidth(380)
        lay = QVBoxLayout(d)
        lay.setSpacing(12)
        lay.setContentsMargins(18, 18, 18, 18)

        lay.addWidget(QLabel(self.translate_text("Nom du projet :")))
        name_input = QLineEdit(self._project_data.get('name', ''))
        name_input.setMinimumHeight(34)
        lay.addWidget(name_input)

        lay.addWidget(QLabel(self.translate_text("Notes :")))
        notes_input = QTextEdit()
        notes_input.setPlainText(self._project_data.get('notes', ''))
        notes_input.setFixedHeight(88)
        lay.addWidget(notes_input)

        created = self._project_data.get('created_at', '')[:16].replace('T', '  ')
        modified = self._project_data.get('modified_at', '')[:16].replace('T', '  ')
        if created:
            lbl_created  = self.translate_text("Créé :")
            lbl_modified = self.translate_text("Modifié :")
            lbl_files    = self.translate_text("fichier(s)")
            info_lbl = QLabel(
                f"<small style='color:gray;'>{lbl_created} {created}"
                + (f"&nbsp;&nbsp;&nbsp;{lbl_modified} {modified}" if modified else "")
                + f"&nbsp;&nbsp;&nbsp;{len(self.files_list)} {lbl_files}</small>")
            info_lbl.setTextFormat(Qt.RichText)
            lay.addWidget(info_lbl)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_cancel = QPushButton(self.translate_text("Annuler"))
        btn_cancel.setMinimumHeight(36)
        _apply_dialog_btn(btn_cancel, "BtnCancelGlassy")
        btn_ok = QPushButton(self.translate_text("✓  Enregistrer"))
        btn_ok.setMinimumHeight(36)
        btn_ok.setStyleSheet(
            "QPushButton{background:#0969da;color:white;border:none;"
            "border-radius:7px;font-weight:bold;padding:0 16px;}"
            "QPushButton:hover{background:#0860ca;}")
        btn_cancel.clicked.connect(d.reject)
        btn_ok.clicked.connect(d.accept)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)
        lay.addLayout(btn_row)

        if d.exec() == QDialog.Accepted:
            new_name  = name_input.text().strip() or self._project_data.get('name', '')
            new_notes = notes_input.toPlainText().strip()
            self._project_data['name']  = new_name
            self._project_data['notes'] = new_notes
            self._update_project_label()
            if self.current_project:
                self._save_project_to(self.current_project)

    def open_last_project(self):
        if self.current_project and os.path.exists(self.current_project):
            self.open_project_file(self.current_project)

    def open_project_file(self, file_path):
        try:
            import json as _json
            from datetime import datetime as _dt

            with open(file_path, 'r', encoding='utf-8') as f:
                raw = f.read().strip()

            # Detect format
            if raw.startswith('{'):
                # New JSON format
                data        = _json.loads(raw)
                file_entries = data.get('files', [])
                all_paths   = [e['path'] if isinstance(e, dict) else e for e in file_entries]
                self._project_data = data
                self._project_data['modified_at'] = _dt.now().isoformat(timespec='seconds')
            else:
                all_paths = [line for line in raw.splitlines() if line.strip()]
                now = _dt.now().isoformat(timespec='seconds')
                self._project_data = {
                    'version':     1,
                    'name':        Path(file_path).stem,
                    'notes':       '',
                    'created_at':  now,
                    'modified_at': now,
                    'files': [
                        {'path': p, 'added_at': now,
                         'size': os.path.getsize(p) if os.path.exists(p) else 0}
                        for p in all_paths
                    ],
                }

            existing_files = [p for p in all_paths if os.path.exists(p)]
            missing_count  = len(all_paths) - len(existing_files)

            self.files_list = existing_files
            self.files_list_widget.clear()

            for file in existing_files:
                icon         = self.get_file_icon(file)
                display_name = Path(file).name
                if isinstance(icon, QIcon):
                    item = QListWidgetItem(display_name)
                    item.setIcon(icon)
                else:
                    item = QListWidgetItem(icon + " " + display_name)
                item.setData(Qt.UserRole, file)
                item.setData(Qt.UserRole + 1, "file")
                item.setToolTip(file)
                if os.path.isfile(file):
                    item.setData(Qt.UserRole + 4, self.format_size(os.path.getsize(file)))
                self.files_list_widget.addItem(item)
                self._attach_preview_btn(item, file)

            self.current_project = file_path
            self._update_project_label()
            self.update_file_counter()

            proj_name = self._project_data.get('name', Path(file_path).stem)
            self.status_bar.showMessage(
                self.translate_text("project_opened_status").format(
                    proj_name=proj_name, n=len(existing_files)))

            if missing_count > 0:
                QMessageBox.warning(
                    self, self.translate_text("Fichiers manquants"),
                    self.translate_text("project_missing_files").format(n=missing_count))

        except Exception as e:
            QMessageBox.critical(
                self, self.translate_text("Erreur"),
                self.translate_text("project_open_error").format(error=str(e)))

    def show_dashboard(self):
        if self.dashboard_dialog is None or not self.dashboard_dialog.isVisible():
            StatisticsDashboard = _get_StatisticsDashboard()
            self.dashboard_dialog = StatisticsDashboard(self.db_manager, self.current_language, self)
            self.dashboard_dialog.show()
        else:
            self.dashboard_dialog.raise_()
            self.dashboard_dialog.activateWindow()

    def show_history(self):
        if self.history_dialog is None or not self.history_dialog.isVisible():
            HistoryDialog = _get_HistoryDialog()
            self.history_dialog = HistoryDialog(
                self.db_manager, self, self.current_language,
                adv_db_manager=self.adv_db_manager
            )
            self.history_dialog.show()
        else:
            self.history_dialog.raise_()
            self.history_dialog.activateWindow()

    def show_templates(self):
        """Display the enhanced template manager"""
        if not hasattr(self, 'template_manager') or self.template_manager is None:
            TemplateManager, EnhancedTemplatesDialog = _get_TemplateClasses()
            self.template_manager = TemplateManager(self.db_manager)
        
        if self.templates_dialog is None or not self.templates_dialog.isVisible():
            TemplateManager, EnhancedTemplatesDialog = _get_TemplateClasses()
            self.templates_dialog = EnhancedTemplatesDialog(self.template_manager, self, self.current_language)
            
            self.templates_dialog.template_applied.connect(self.on_template_applied)
            
            self.templates_dialog.show()
        else:
            self.templates_dialog.raise_()
            self.templates_dialog.activateWindow()

    def on_template_applied(self, template):
        """Called when a template is applied"""

        message = self.translate_text(f"Template '{template['name']}' appliqué")
        if template['type'] == self.translate_text("Fusion PDF"):
            message += self.translate_text(" - Ajoutez des fichiers PDF et lancez la fusion")
        elif template['type'] == self.translate_text("Conversion PDF→Word"):
            message += self.translate_text(" - Lancez une conversion PDF vers Word pour utiliser ces paramètres")
        
        self.status_bar.showMessage(message)
        
        if template['type'] == self.translate_text("Optimisation de fichiers"):
            message += self.translate_text(" - Lancez Optimiser les fichiers pour utiliser ces paramètres")

    def create_template_from_current_settings(self):
        """Create a template from the current settings"""
        if not hasattr(self, 'template_manager') or self.template_manager is None:
            TemplateManager, _ = _get_TemplateClasses()
            self.template_manager = TemplateManager(self.db_manager)
        
        dialog = QInputDialog(self)
        dialog.setWindowTitle(self.translate_text("Créer un template"))
        dialog.setLabelText(self.translate_text("Nom du template:"))
        dialog.setTextValue(self.translate_text("Template actuel"))
        
        if dialog.exec() == QDialog.Accepted:
            name = dialog.textValue().strip()
            if name:
                config = (self._ensure_template_manager() or object()).create_template_from_current_settings(
                    name,
                    self.translate_text("Conversion PDF→Word"),
                    self
                )
                
                QMessageBox.information(
                    self,
                    self.translate_text("Succès"),
                    self.translate_text(f"Template '{name}' créé à partir des paramètres actuels!")
                )

    def show_achievements(self):
            """Display the achievements interface."""
            try:
                if self.achievements_dialog is not None and self.achievements_dialog.isVisible():
                    self.achievements_dialog.raise_()
                    self.achievements_dialog.activateWindow()
                    return
            except RuntimeError:
                self.achievements_dialog = None

            self.achievements_dialog = AchievementsUI(
                self.achievement_system,
                self,
                self.current_language
            )
            self.achievements_dialog.show()

    def show_donate(self):
        """Open the donation dialog."""
        from donate import DonateDialog
        config_dir = os.path.dirname(os.path.abspath(self.config_manager.config_file))
        dlg = DonateDialog(parent=self, dark_mode=self.dark_mode, language=self.current_language, config_dir=config_dir)
        dlg.exec()

    def _check_donor_return(self):
        """
        Called once at startup (via QTimer.singleShot).
        If the user clicked Ko-fi in a previous session, a flag file was
        written by donate.py.  We pop it here and show the Thank You dialog.
        """
        try:
            from donate import pop_donor_flag, ThankYouDialog
            config_dir = os.path.dirname(os.path.abspath(self.config_manager.config_file))
            data = pop_donor_flag(config_dir)
            if data:
                dlg = ThankYouDialog(
                    parent=self,
                    dark_mode=self.dark_mode,
                    amount=data.get("amount", "")
                )
                dlg.exec()
        except Exception as e:
            print(f"[DONOR] Could not show thank-you dialog: {e}")

    def show_achievement_popup(self, achievement):
        """Display the achievement acquisition popup"""
        popup = AchievementPopup(achievement, self.achievement_system, self, language=self.current_language)
        popup.set_translator(self.translation_manager)
        popup.show()

    def show_achievements_admin(self):
        from achievements.achievements_manager import QuickAchievementsReset
        manager = QuickAchievementsReset("achievements.db", self, language=self.current_language)
        self._achievements_manager_ref = manager
        manager.exec()

    def show_achievements_admin_full(self):
        from achievements.achievements_manager import AchievementsManager
        manager = AchievementsManager("achievements.db", self, language=self.current_language)
        self._achievements_manager_ref = manager
        manager.exec()

    def show_settings(self):
        dialog = SettingsDialog(self.config, self, self.current_language)
        if dialog.exec() == QDialog.Accepted:
            new_settings = dialog.get_settings()
            self.config.update(new_settings)
            self._apply_achievements_btn_state()
            self.config_manager.save_config(self.config)
            
            QMessageBox.information(self, self.translate_text("Succès"), self.translate_text("Paramètres sauvegardés avec succès!"))

    def _apply_achievements_btn_state(self):
        enabled = self.config.get("achievements_enabled", True)
        btn = getattr(self, "nav_achievements_btn", None)
        if btn is None:
            return
        btn.setVisible(enabled)
        btn.setToolTip(
            self.translate_text("Succès et réalisations") if enabled
            else ""
        )

    def new_project(self):
        if self.files_list:
            reply = QMessageBox.question(
                self, self.translate_text("Nouveau Projet"),
                self.translate_text("Voulez-vous créer un nouveau projet ? Les fichiers actuels seront effacés."),
                QMessageBox.Yes | QMessageBox.No)
            if reply != QMessageBox.Yes:
                return

        d = QDialog(self)
        d.setWindowTitle(self.translate_text("Nouveau projet"))
        d.setMinimumWidth(360)
        lay = QVBoxLayout(d)
        lay.setSpacing(12)
        lay.setContentsMargins(18, 18, 18, 18)

        lay.addWidget(QLabel(self.translate_text("Nom du projet :")))
        name_input = QLineEdit()
        name_input.setPlaceholderText(self.translate_text("Mon projet"))
        name_input.setMinimumHeight(34)
        lay.addWidget(name_input)

        lay.addWidget(QLabel(self.translate_text("Notes (optionnel) :")))
        notes_input = QTextEdit()
        notes_input.setPlaceholderText(self.translate_text("Description, contexte…"))
        notes_input.setFixedHeight(72)
        lay.addWidget(notes_input)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_cancel = QPushButton(self.translate_text("Annuler"))
        btn_cancel.setMinimumHeight(36)
        _apply_dialog_btn(btn_cancel, "BtnCancelGlassy")
        btn_ok = QPushButton("✓  " + self.translate_text("Créer"))
        btn_ok.setMinimumHeight(36)
        btn_ok.setStyleSheet(
            "QPushButton{background:#0969da;color:white;border:none;"
            "border-radius:7px;font-weight:bold;padding:0 16px;}"
            "QPushButton:hover{background:#0860ca;}")
        btn_cancel.clicked.connect(d.reject)
        btn_ok.clicked.connect(d.accept)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)
        lay.addLayout(btn_row)

        from datetime import datetime as _dt
        now = _dt.now().isoformat(timespec='seconds')
        proj_name  = self.translate_text("Nouveau projet")
        proj_notes = ""

        if d.exec() == QDialog.Accepted:
            proj_name  = name_input.text().strip() or self.translate_text("Nouveau projet")
            proj_notes = notes_input.toPlainText().strip()

        self.files_list.clear()
        self.files_list_widget.clear()
        self.current_project = None
        self._project_data   = {
            "version":     1,
            "name":        proj_name,
            "notes":       proj_notes,
            "created_at":  now,
            "modified_at": now,
            "files":       [],
        }
        self._update_project_label()
        self.update_file_counter()
        self.status_bar.showMessage(
            self.translate_text("Nouveau projet créé") + ":" + f" {proj_name}" if proj_name else "")

    def open_project(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, self.translate_text("Ouvrir un projet"), "", self.translate_text("Projets File Converter (*.fcproj)")
        )
        if file_path:
            self.open_project_file(file_path)
            self.config["last_project"] = file_path
            self.config_manager.save_config(self.config)

    def save_project(self):
        if not self.files_list:
            QMessageBox.warning(self, self.translate_text("Avertissement"),
                                self.translate_text("Aucun fichier à sauvegarder dans le projet"))
            return

        if self.current_project and os.path.exists(self.current_project):
            self._save_project_to(self.current_project)
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, self.translate_text("Sauvegarder le projet"), "",
            self.translate_text("Projets File Converter (*.fcproj)"))

        if file_path:
            if not file_path.endswith('.fcproj'):
                file_path += '.fcproj'
            self._save_project_to(file_path)

    def _save_project_to(self, file_path):
        import json as _json
        from datetime import datetime as _dt

        now  = _dt.now().isoformat(timespec='seconds')
        data = dict(self._project_data) if self._project_data else {}
        data.setdefault('version',    1)
        data.setdefault('name',       Path(file_path).stem)
        data.setdefault('notes',      '')
        data.setdefault('created_at', now)
        data['modified_at'] = now

        existing_entries = {
            (e['path'] if isinstance(e, dict) else e): (e if isinstance(e, dict) else {})
            for e in data.get('files', [])
        }
        data['files'] = []
        for p in self.files_list:
            prev = existing_entries.get(p, {})
            data['files'].append({
                'path':     p,
                'added_at': prev.get('added_at', now),
                'size':     os.path.getsize(p) if os.path.exists(p) else prev.get('size', 0),
            })

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                _json.dump(data, f, ensure_ascii=False, indent=2)

            self._project_data   = data
            self.current_project = file_path
            self._update_project_label()
            self.config["last_project"] = file_path
            self.config_manager.save_config(self.config)
            self.status_bar.showMessage(
                self.translate_text(f"Projet sauvegardé : {data['name']}"))

        except Exception as e:
            QMessageBox.critical(self, self.translate_text("Erreur"),
                                 self.translate_text(f"Impossible de sauvegarder le projet: {str(e)}"))

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            self.translate_text("Sélectionner des fichiers"),
            "",
            self.translate_text(
                "Tous les fichiers supportés ("
                "*.pdf *.docx *.doc *.pptx *.ppt *.xlsx *.xls "
                "*.jpg *.jpeg *.png *.bmp *.tiff *.tif *.webp *.heic *.heif *.jfif "
                "*.avif *.psd *.svg *.dng *.j2k *.jp2 *.jpx *.cr2 *.cr3 *.nef *.arw *.orf *.rw2 "
                "*.mp3 *.wav *.aac *.flac *.ogg *.m4a "
                "*.mp4 *.avi *.mkv *.webm *.mov "
                "*.html *.htm *.epub *.rtf *.txt "
                "*.csv *.json "
                "*.zip *.rar *.tar *.gz);;"
                "Documents (*.pdf *.docx *.doc *.pptx *.ppt *.xlsx *.xls *.rtf *.txt *.epub *.html *.htm);;"
                "PDF Files (*.pdf);;"
                "Word / RTF (*.docx *.doc *.rtf *.txt);;"
                "PowerPoint (*.pptx *.ppt);;"
                "Excel (*.xlsx *.xls);;"
                "EPUB (*.epub);;"
                "HTML (*.html *.htm);;"
                "Images (*.jpg *.jpeg *.png *.bmp *.tiff *.tif *.webp *.heic *.heif *.jfif *.avif *.psd *.svg *.dng *.j2k *.jp2 *.jpx *.cr2 *.cr3 *.nef *.arw *.orf *.rw2);;"
                "Audio (*.mp3 *.wav *.aac *.flac *.ogg *.m4a);;"
                "Vidéo (*.mp4 *.avi *.mkv *.webm *.mov);;"
                "Données (*.csv *.json);;"
                "Archives (*.zip *.rar *.tar *.gz);;"
                "Tous les fichiers (*.*)"
            )
        )
        self.add_files_to_list(files)

    def add_folder(self):
        """Add a folder with two options"""
        dialog = QDialog(self)
        dialog.setWindowTitle(self.translate_text("Ajouter un dossier"))
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        title_label = QLabel(self.translate_text("Comment voulez-vous ajouter le dossier ?"))
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 10px;")
        layout.addWidget(title_label)
        
        option1_btn = QPushButton("📦 " + self.translate_text("Ajouter le dossier (pour compression)"))
        option1_btn.setMinimumHeight(45)

        _apply_dialog_btn(option1_btn, "BtnFolderAsItem")

        option1_btn.setToolTip(self.translate_text("Ajoute le dossier en tant qu'élément unique pour la compression"))
        
        option2_btn = QPushButton("📄 " + self.translate_text("Ajouter le contenu du dossier"))
        option2_btn.setMinimumHeight(45)

        _apply_dialog_btn(option2_btn, "BtnFolderContent")

        option2_btn.setToolTip(self.translate_text("Ajoute tous les fichiers du dossier individuellement"))
        
        cancel_btn = QPushButton(self.translate_text("Annuler"))
        cancel_btn.setMinimumHeight(35)

        _apply_dialog_btn(cancel_btn, "BtnCancelGlassy")
        
        layout.addWidget(option1_btn)
        layout.addWidget(option2_btn)
        layout.addSpacing(20)
        layout.addWidget(cancel_btn)
        
        option1_btn.clicked.connect(lambda: self.add_folder_as_item(dialog))
        option2_btn.clicked.connect(lambda: self.add_folder_contents(dialog))
        cancel_btn.clicked.connect(dialog.reject)
        
        dialog.exec()

    def add_folder_as_item(self, dialog=None):
        """Add the folder as a single item (for compression)"""
        if dialog:
            dialog.accept()
        
        folder = QFileDialog.getExistingDirectory(self, self.translate_text("Sélectionner un dossier à ajouter"))
        if folder:
            self.files_list.append(folder)
            
            folder_name = Path(folder).name
            icon = self.get_file_icon(folder)

            file_count = sum(len(files) for _, _, files in os.walk(folder))
            folder_size = self.calculate_folder_size(folder)

            if isinstance(icon, QIcon):
                item = QListWidgetItem(folder_name)
                item.setIcon(icon)
            else:
                item = QListWidgetItem(icon + " " + folder_name)

            item.setData(Qt.UserRole, folder)
            item.setData(Qt.UserRole + 4, self.format_size(folder_size))
            
            tooltip = (f"Folder: {folder}\n"
                    f"Size: {self.format_size(folder_size)}\n"
                    f"Files: {file_count}\n"
                    f"Full structure preserved during compression")
            
            item.setToolTip(tooltip)
            
            item.setForeground(QColor(0, 85, 255))
            item.setFont(QFont("Arial", 10, QFont.Bold))
            
            item.setData(Qt.UserRole + 1, "folder")
            item.setData(Qt.UserRole + 2, file_count)
            item.setData(Qt.UserRole + 3, folder_size)
            
            self.files_list_widget.addItem(item)
            
            self.update_file_counter()
            self.status_bar.showMessage(self.translate_text(f"Dossier ajouté: {folder_name} ({file_count} fichiers)"))

    def calculate_folder_size(self, folder_path):
        """Calculate the total size of a folder"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(folder_path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    try:
                        total_size += os.path.getsize(filepath)
                    except:
                        pass
        return total_size

    def format_size(self, size_bytes):
        """Format size in human-readable units"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

    def add_folder_contents(self, dialog=None):
        if dialog:
            dialog.accept()
        
        folder = QFileDialog.getExistingDirectory(self, self.translate_text("Sélectionner un dossier"))
        if not folder:
            return

        supported_extensions = {
            # Documents
            '.pdf', '.docx', '.doc', '.rtf', '.txt',
            '.pptx', '.ppt',
            '.xlsx', '.xls',
            '.epub', '.html', '.htm',
            '.csv', '.json',
            # Images
            '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp', '.gif',
            '.svg', '.ico', '.avif', '.heic', '.heif', '.psd', '.j2k', '.jp2', '.jfif',
            '.dng', '.cr2', '.cr3', '.nef', '.arw', '.orf', '.rw2', '.raf', '.jpx',
            # Audio
            '.mp3', '.wav', '.aac', '.flac', '.ogg',
            # Video
            '.mp4', '.avi', '.mkv', '.mov', '.webm',
            # Archives
            '.zip', '.rar', '.tar', '.gz',
        }
        files = []
        
        for root, dirs, filenames in os.walk(folder):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                file_ext = Path(file_path).suffix.lower()
                
                if file_ext in supported_extensions:
                    files.append(file_path)
        
        new_files = [f for f in files if f not in self.files_list]
        if not new_files:
            return

        self.files_list.extend(new_files)

        start_index = self.files_list_widget.count() + 1
        
        for i, file_path in enumerate(new_files):
            display_name = Path(file_path).name
            number = start_index + i
            numbered_text = f"{number} {display_name}"
            
            item = QListWidgetItem(numbered_text)
            item.setData(Qt.UserRole, file_path)
            
            icon = self.get_file_icon(file_path)
            if isinstance(icon, QIcon):
                item.setIcon(icon)
            else:
                item.setText(f"{number} {icon} {display_name}")
            
            if os.path.isfile(file_path):
                item.setData(Qt.UserRole + 4, self.format_size(os.path.getsize(file_path)))
            
            self.files_list_widget.addItem(item)
            self._attach_preview_btn(item, file_path)
        
        self.update_file_counter()

    def add_files_to_list(self, files):
        """Add files or folders to the list with numbering"""
        new_files = []
        for file in files:
            if str(file).lower().endswith('.fcproj'):
                continue
            if file not in self.files_list:
                if os.path.isdir(file):
                    new_files.append((file, "folder"))
                else:
                    new_files.append((file, "file"))
        
        start_index = self.files_list_widget.count() + 1
        for i, (file_path, file_type) in enumerate(new_files):
            self.files_list.append(file_path)
            icon = self.get_file_icon(file_path)
            display_name = Path(file_path).name
            number = start_index + i

            if isinstance(icon, QIcon):
                item = QListWidgetItem(f"{number} {display_name}")
                item.setIcon(icon)
            else:
                item = QListWidgetItem(f"{number} {icon} {display_name}")

            item.setData(Qt.UserRole, file_path)
            item.setData(Qt.UserRole + 1, file_type)
            if file_type == "file" and os.path.isfile(file_path):
                item.setData(Qt.UserRole + 4, self.format_size(os.path.getsize(file_path)))
            self.files_list_widget.addItem(item)
            self._attach_preview_btn(item, file_path)
        
        self.update_file_counter()

    def _attach_preview_btn(self, item, file_path):
        """Attach a real 👁 preview button as item widget, aligned right with margin for size label."""
        btn = QPushButton("👁")
        btn.setFixedSize(24, 22)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setToolTip(self.translate_text("Aperçu"))
        btn.setStyleSheet("""
            QPushButton {
                background: rgba(110,190,255,0.12);
                color: rgb(110,190,255);
                border: 1px solid rgba(110,190,255,0.25);
                border-radius: 5px;
                font-size: 13px;
            }
            QPushButton:hover { background: rgba(110,190,255,0.30); }
            QPushButton:pressed { background: rgba(110,190,255,0.45); }
        """)
        btn.clicked.connect(lambda: (self.files_list_widget.setCurrentItem(item), self.show_file_preview(item)))

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 38, 0)
        layout.addStretch()
        layout.addWidget(btn)

        self.files_list_widget.setItemWidget(item, container)

    ICON_MAPPING = {
        '.pdf': ('pdf.ico', '📄'),
        '.doc': ('word.ico', '📝'), '.docx': ('word.ico', '📝'),
        '.rtf': ('rtf.ico', '📝'), '.txt': ('txt.ico', '📝'),
        '.ppt': ('pptx.ico', '📎'), '.pptx': ('pptx.ico', '📎'),
        '.xlsx': ('xlsx.ico', '📎'), '.csv': ('csv.ico', '📎'),
        '.epub': ('epub.ico', '📎'), '.html': ('html.ico', '📎'),
        '.json': ('json.ico', '📎'), '.exe': ('exe.ico', '📎'),
        **{ext: ('img.ico', '🖼️') for ext in [
            '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif', '.heic', '.jfif', '.tif', 
            '.svg', '.ico', '.avif', '.heif', '.psd', '.j2k', '.jp2', '.jpx', '.dng', 
            '.cr2', '.cr3', '.nef', '.arw', '.orf', '.rw2', '.raf', '.webp'
        ]},
        **{ext: ('video.ico', '📎') for ext in ['.mp4', '.avi', '.mkv', '.mov', '.webm']},
        **{ext: ('audio.ico', '📎') for ext in ['.mp3', '.wav', '.aac', '.flac', '.ogg']},
        **{ext: ('archive.ico', '🗜️') for ext in ['.zip', '.rar', '.tar', '.gz', '.7z']},
        **{ext: ('database.ico', '📎') for ext in ['.db', '.sqlite', '.sql']}
    }

    _icon_cache: dict[str, QIcon | str] = {}

    def get_file_icon(self, file_path):
        p = Path(file_path)
        icons_dir = Path(self.get_resource_path("icons"))

        if p.is_dir():
            return self._load_icon(icons_dir / "folder.ico", "📁")

        ico_name, fallback = self.ICON_MAPPING.get(p.suffix.lower(), ("other.ico", "📎"))
        return self._load_icon(icons_dir / ico_name, fallback)

    def _load_icon(self, icon_path: Path, fallback: str):
        key = str(icon_path)
        if key not in self._icon_cache:
            self._icon_cache[key] = QIcon(key) if icon_path.exists() else fallback
        return self._icon_cache[key]

    def get_resource_path(self, relative_path):
        """Get the resource path"""
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def remove_files(self):
        selected_items = self.files_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, self.translate_text("Avertissement"), 
                                self.translate_text("Veuillez sélectionner au moins un fichier à supprimer"))
            return
        
        folder_count = 0
        file_count = 0
        
        valid_items = []
        for item in selected_items:
            file_path = item.data(Qt.UserRole)
            
            if file_path is None:
                file_path = item.toolTip()
            
            if file_path is None:
                continue
                
            valid_items.append((item, file_path))
            
            if os.path.isdir(file_path):
                folder_count += 1
            else:
                file_count += 1
        
        if not valid_items:
            QMessageBox.warning(self, self.translate_text("Avertissement"), 
                                self.translate_text("Aucun fichier valide sélectionné"))
            return
        
        if folder_count > 0:
            template = self.translate_text("confirm_remove_files_with_folders")
            message = template.format(folder_count, file_count)
        else:
            template = self.translate_text("confirm_remove_files_only")
            message = template.format(file_count)
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(self.translate_text("Confirmation"))
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Question)

        yes_button = msg_box.addButton(QMessageBox.Yes)
        no_button = msg_box.addButton(QMessageBox.No)
        msg_box.setDefaultButton(no_button)

        yes_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        no_button.setStyleSheet("""
            QPushButton {
                background-color: #B55454;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #A04040;
            }
            QPushButton:pressed {
                background-color: #8B3030;
            }
        """)

        msg_box.exec()

        if msg_box.clickedButton() == yes_button:
            for item, file_path in valid_items:
                if file_path in self.files_list:
                    self.files_list.remove(file_path)
                # Ensure item exists before deleting it
                row = self.files_list_widget.row(item)
                if row != -1:
                    self.files_list_widget.takeItem(row)
            
            self.update_file_counter()
            self.update_item_numbers()

    def animate_clear_button(self):
        """Visual animation for the Clear All button"""
        animation = QPropertyAnimation(self.clear_all_btn, b"geometry")
        animation.setDuration(300)
        
        original_geometry = self.clear_all_btn.geometry()
        
        animation.setKeyValueAt(0, original_geometry)
        animation.setKeyValueAt(0.5, original_geometry.adjusted(2, 2, -2, -2))
        animation.setKeyValueAt(1, original_geometry)
        
        animation.setEasingCurve(QEasingCurve.OutBounce)
        animation.start()

    def clear_files(self):
        """Clear all files from the list"""
        if not self.files_list:
            return
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(self.translate_text("Confirmation"))
        msg_box.setText(self.translate_text("confirm_delete_all").format(count=len(self.files_list)))
        msg_box.setIcon(QMessageBox.Question)
        
        # Create custom buttons
        yes_button = msg_box.addButton(QMessageBox.Yes)
        no_button = msg_box.addButton(QMessageBox.No)
        msg_box.setDefaultButton(no_button)
        
        yes_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        no_button.setStyleSheet("""
            QPushButton {
                background-color: #B55454;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #A04040;
            }
            QPushButton:pressed {
                background-color: #8B3030;
            }
        """)
        
        msg_box.exec()
        
        if msg_box.clickedButton() == yes_button:
            self.files_list.clear()
            self.files_list_widget.clear()
            
            self.update_file_counter()
            self.status_bar.showMessage(self.translate_text("Liste de fichiers effacée"))
            self.animate_clear_button()

    def update_file_order(self):
        """Update the file order and numbering after a move"""
        self.files_list.clear()
        for i in range(self.files_list_widget.count()):
            item = self.files_list_widget.item(i)
            self.files_list.append(item.data(Qt.UserRole))
        self.update_item_numbers()

    def update_item_numbers(self):
        """Update the numbering of all items in the list"""
        for i in range(self.files_list_widget.count()):
            item = self.files_list_widget.item(i)
            if item:
                file_path = item.data(Qt.UserRole)
                file_type = item.data(Qt.UserRole + 1)
                icon = self.get_file_icon(file_path)
                display_name = Path(file_path).name
                number = i + 1
                if isinstance(icon, QIcon):
                    item.setIcon(icon)
                    item.setText(f"{number} {display_name}")
                else:
                    item.setText(f"{number} {icon} {display_name}")

    def update_file_counter(self):
        count = len(self.files_list)
        folder_count = sum(1 for f in self.files_list if os.path.isdir(f))
        file_count = count - folder_count
        
        if count == 0:
            self.file_counter.setText(self.translate_text("Aucun fichier sélectionné"))
        else:
            text = ""
            if folder_count > 0:
                text += f"{folder_count} {self.translate_text('dossier(s)')}"
                if file_count > 0:
                    text += f", {file_count} {self.translate_text('fichier(s)')}"
            else:
                text = f"{file_count} {self.translate_text('fichier(s)')}"
            
            self.file_counter.setText(text)

        try:
            from PySide6.QtWidgets import QGraphicsOpacityEffect
            effect = QGraphicsOpacityEffect(self.file_counter)
            effect.setOpacity(0.15)
            self.file_counter.setGraphicsEffect(effect)
            QTimer.singleShot(110, lambda: self.file_counter.setGraphicsEffect(None))
        except Exception:
            pass

    def batch_rename(self):
        if not self.files_list:
            QMessageBox.warning(self, self.translate_text("Avertissement"),
                                self.translate_text("Aucun fichier sélectionné"))
            return

        dialog = BatchRenameDialog(self.files_list, self, self.current_language)
        if dialog.exec() != QDialog.Accepted:
            return

        rename_plan = dialog.get_rename_plan()

        start_time = datetime.now()
        total_size = sum(os.path.getsize(f) for f in self.files_list if os.path.exists(f))

        self.process_batch_rename(rename_plan)

        conversion_time = (datetime.now() - start_time).total_seconds()
        self.db_manager.add_conversion_record(
            source_file="Batch of files",
            source_format="Various",
            target_file="Rename",
            target_format="Same formats",
            operation_type="batch_rename",
            file_size=total_size,
            conversion_time=conversion_time,
            success=True,
            notes=f"{len(rename_plan)} files renamed"
        )

    def _set_ui_enabled(self, enabled: bool):
        """Disable/re-enable interactive controls during async conversion."""
        for btn in [
            getattr(self, "pdf_to_word_btn",    None),
            getattr(self, "word_to_pdf_btn",    None),
            getattr(self, "image_to_pdf_btn",   None),
            getattr(self, "batch_convert_btn",  None),
            getattr(self, "merge_pdf_btn",      None),
            getattr(self, "merge_word_btn",     None),
            getattr(self, "split_pdf_btn",      None),
            getattr(self, "more_conversions_btn", None),
        ]:
            if btn is not None:
                btn.setEnabled(enabled)

    def show_progress(self, show, message=""):
        self.progress_bar.setVisible(show)
        self.progress_pct_label.setVisible(show)
        if show:
            self.progress_bar.setValue(0)
            self.progress_pct_label.setText("0%")
            self.status_bar.showMessage(message)
        else:
            self.status_bar.showMessage(self.translate_text("Ready"))

    def toggle_theme(self):
        """Directly switch the application theme."""
        self._toggle_theme_actual()

    def _toggle_theme_actual(self):
        self.config["use_system_theme"] = False
        self.config_manager.save_config(self.config)
        if self.dark_mode:
            self.dark_mode_timer_start = time.time()
        else:
            # If leave dark, record time
            if self.dark_mode_timer_start is not None:
                elapsed = (time.time() - self.dark_mode_timer_start) / 60
                self.achievement_system.add_dark_mode_time(elapsed)
                self.dark_mode_timer_start = None
        
        self.dark_mode = not self.dark_mode
        self.apply_theme(self.dark_mode)
        self.theme_action.setText("☀️ " + self.translate_text("Mode Clair") if self.dark_mode else "🌙 " + self.translate_text("Mode Sombre"))
        
        self.config["dark_mode"] = self.dark_mode
        self.config_manager.save_config(self.config)

        logo = self.findChild(QLabel, "LogoLabel")
        if logo:
            logo_color = "#e8ff6b" if self.dark_mode else "#2d2dc8"
            logo.setStyleSheet(
                "font-family:'Segoe UI','SF Pro Display',Arial,sans-serif;"
                "font-size:16px;font-weight:900;"
                "letter-spacing:1.5px;background:transparent;"
                f"color:{logo_color};"
            )

    def update_dark_mode_time(self):
        """Update dark mode time"""
        if self.dark_mode:
            if self.dark_mode_timer_start is None:
                self.dark_mode_timer_start = time.time()
            else:
                elapsed = (time.time() - self.dark_mode_timer_start) / 60
                self.achievement_system.add_dark_mode_time(elapsed)
                self.dark_mode_timer_start = time.time()

    def _get_language_label(self, code: str) -> str:
        """Return the display label for the toolbar language button."""
        for lang in self.translation_manager.get_available_languages():
            if lang["code"] == code:
                name = lang["name"]
                if code == "fr":
                    return f"🇫🇷 {name}"
                elif code == "en":
                    return f"🇬🇧 {name}"
                else:
                    return f"🌐 {name}"
        return f"🌐 {code}"

    def toggle_language(self):
        available = [lang["code"] for lang in self.translation_manager.get_available_languages()]
        if not available:
            return
        try:
            idx = available.index(self.current_language)
        except ValueError:
            idx = 0
        new_language = available[(idx + 1) % len(available)]

        self.current_language = new_language
        self.translation_manager.set_language(new_language)
        self.system_notifier.set_language(new_language)
        if hasattr(self, 'files_list_widget'):
            self.files_list_widget.set_language(new_language)

        self.config["language"] = new_language
        self.config_manager.save_config(self.config)
        self.create_menu_bar()

        self.update_texts()

        self.language_action.setText(self._get_language_label(new_language))

    def update_texts(self):
        self.setWindowTitle("File Converter Pro - Professional File Converter")
        self.update_file_counter()
        self.status_bar.showMessage(self.translate_text("Prêt - Sélectionnez des fichiers pour commencer"))

        for widget in self.findChildren(QGroupBox):
            key = widget.property("i18n_key")
            if key:
                widget.setTitle(self.translate_text(key).upper())

        for widget in self.findChildren(QPushButton):
            key = widget.property("i18n_key")
            if key:
                parts = widget.text().split(" ", 1)
                prefix = parts[0] + " " if len(parts) == 2 else ""
                widget.setText(prefix + self.translate_text(key))

        for widget in self.findChildren(QLabel):
            key = widget.property("i18n_key")
            if key:
                widget.setText(self.translate_text(key))

        for widget in self.findChildren(QCheckBox):
            key = widget.property("i18n_key")
            if key:
                widget.setText(self.translate_text(key))

        self.theme_action.setText(("☀️ " if self.dark_mode else "🌙 ") + self.translate_text("Mode Clair" if self.dark_mode else "Mode Sombre"))
        self.new_action.setText("🆕 " + self.translate_text("Nouveau Projet"))
        self.open_action.setText("📂 " + self.translate_text("Ouvrir Projet"))
        self.save_action.setText("💾 " + self.translate_text("Enregistrer Projet"))
        self.setup_tooltips_with_shortcuts()

    def apply_theme(self, dark: bool) -> None:
        self.setStyleSheet(_load_qss("style.qss", "dark" if dark else "light"))
