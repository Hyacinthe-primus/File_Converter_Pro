"""
Template Manager

System for saving and applying conversion presets to automate workflows.

Classes:
    EnhancedTemplatesDialog:
        - Master-detail interface for template management
        - Quick actions (Apply, Duplicate, Delete)
        - Contextual guides after applying templates
    
    CreateTemplateDialog → create_template_dialog.py
    TemplateEditorDialog  → template_editor_dialog.py

"""

import json
from pathlib import Path
from PySide6.QtWidgets import (QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QLabel, QListWidget, 
                               QListWidgetItem, QFileDialog, QMessageBox, 
                               QComboBox, QSplitter, QToolBar,
                               QGroupBox, QScrollArea, QLineEdit, QDialog, 
                               QDialogButtonBox, QFormLayout, QMenu, QInputDialog)
from PySide6.QtCore import (Qt, QSize, QTimer, Signal)
from PySide6.QtGui import ( QColor, QAction, QKeySequence, QShortcut, QIcon)
from datetime import datetime
import sqlite3

from qss_helpers import _load_qss, _apply_dialog_btn
from .template_manager import TemplateManager
from .create_template_dialog import CreateTemplateDialog
from .template_editor_dialog import TemplateEditorDialog
from utils.translation_mixin import TranslationMixin
from utils import make_tm


class EnhancedTemplatesDialog(TranslationMixin, QDialog):
    """Enhanced dialog for template management"""

    template_applied = Signal(dict)

    def __init__(self, template_manager, parent=None, language="fr"):
        super().__init__(parent)
        self.template_manager = template_manager
        self.language = language
        self._tm = make_tm(language)
        self.parent_window = parent
        self.selected_template_id = None
        
        self.setWindowTitle(self.translate_text("🎨 Gestionnaire de Templates"))
        self.setModal(False)
        self.setMinimumSize(1000, 700)
        
        self.setup_ui()
        self.load_templates()
        self.setup_shortcuts()
        self.apply_theme_style()

    def apply_theme_style(self):
        """Apply style matching the main app theme (dark or light)."""
        dark = hasattr(self.parent_window, 'dark_mode') and self.parent_window.dark_mode

        self.setStyleSheet(_load_qss("templates.qss", "dark" if dark else "light"))
        self.details_header.setStyleSheet(
            f"font-size: 16px; font-weight: bold; color: {'#e6edf3' if dark else '#1f2328'};"
        )

    def setup_shortcuts(self):
        """Configure keyboard shortcuts"""
        # Ctrl+F: Search
        shortcut_search = QShortcut(QKeySequence("Ctrl+F"), self)
        shortcut_search.activated.connect(lambda: self.search_input.setFocus())
        
        # Ctrl+N: New template
        shortcut_new = QShortcut(QKeySequence("Ctrl+N"), self)
        shortcut_new.activated.connect(self.create_new_template_dialog)
        
        # Ctrl+A: Select all templates
        shortcut_select_all = QShortcut(QKeySequence("Ctrl+A"), self)
        shortcut_select_all.activated.connect(self.templates_list.selectAll)

        # Delete: Delete selected templates
        shortcut_delete = QShortcut(QKeySequence("Delete"), self)
        shortcut_delete.activated.connect(self.delete_selected_templates)

        # Esc: Close
        shortcut_escape = QShortcut(QKeySequence("Esc"), self)
        shortcut_escape.activated.connect(self.close)

    def create_from_current_settings(self):
        """Create a template from the current application settings"""
        dialog = QDialog(self)
        dialog.setWindowTitle(self.translate_text("Créer un template à partir des paramètres actuels"))
        layout = QVBoxLayout(dialog)
        
        layout.addWidget(QLabel(self.translate_text("Sélectionnez le type de template à créer:")))
        
        template_type_combo = QComboBox()
        template_type_combo.addItems([
            self.translate_text("Conversion PDF→Word"),
            self.translate_text("Conversion Word→PDF"),
            self.translate_text("Conversion Images→PDF"),
            self.translate_text("Fusion PDF"),
            self.translate_text("Fusion Word"),
            self.translate_text("Division PDF"),
            self.translate_text("Protection PDF"),
            self.translate_text("Compression"),
            self.translate_text("Optimisation de fichiers")
        ])
        layout.addWidget(template_type_combo)
        
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel(self.translate_text("Nom du template:")))
        name_input = QLineEdit()
        name_input.setPlaceholderText(self.translate_text("ex: Ma configuration habituelle"))
        name_layout.addWidget(name_input)
        layout.addLayout(name_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        ok_button = buttons.button(QDialogButtonBox.Ok)
        cancel_button = buttons.button(QDialogButtonBox.Cancel)
        _apply_dialog_btn(ok_button,     "BtnOK")
        _apply_dialog_btn(cancel_button, "BtnCancel")
        layout.addWidget(buttons)
        
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        
        if dialog.exec() == QDialog.Accepted:
            name = name_input.text().strip()
            template_type = template_type_combo.currentText()
            
            if not name:
                QMessageBox.warning(self, 
                                self.translate_text("Erreur"), 
                                self.translate_text("Veuillez entrer un nom pour le template."))
                return
            
            config = self.template_manager.create_template_from_current_settings(name, template_type, self.parent_window)
            
            if config:
                message = self.translate_text("Template '{name}' créé avec succès à partir des paramètres actuels!")
                message = message.replace("{name}", name)
                
                QMessageBox.information(
                    self,
                    self.translate_text("Succès"),
                    message
                )
                self.load_templates()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)
        
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(24, 24))
        
        self.create_template_action = QAction("➕ " + self.translate_text("Créer"), self)
        self.create_template_action.triggered.connect(self.create_new_template_dialog)
        
        self.create_from_current_action = QAction("📝 " + self.translate_text("Créer à partir des paramètres actuels"), self)
        self.create_from_current_action.triggered.connect(self.create_from_current_settings)
        
        self.import_action = QAction("📥 " + self.translate_text("Importer"), self)
        self.import_action.triggered.connect(self.import_templates)
        
        self.export_action = QAction("📤 " + self.translate_text("Exporter"), self)
        self.export_action.triggered.connect(self.export_templates)
        
        self.refresh_action = QAction("🔄 " + self.translate_text("Rafraîchir"), self)
        self.refresh_action.triggered.connect(self.load_templates)
        
        toolbar.addAction(self.create_template_action)
        toolbar.addAction(self.create_from_current_action)
        toolbar.addAction(self.import_action)
        toolbar.addAction(self.export_action)
        toolbar.addAction(self.refresh_action)
            
        main_layout.addWidget(toolbar)
        
        filter_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.translate_text("Rechercher un template..."))
        self.search_input.textChanged.connect(self.filter_templates)
        
        self.type_filter_combo = QComboBox()
        self.type_filter_combo.addItems([
            self.translate_text("Tous les types"),
            self.translate_text("Conversion PDF→Word"),
            self.translate_text("Conversion Word→PDF"),
            self.translate_text("Conversion Images→PDF"),
            self.translate_text("Fusion PDF"),
            self.translate_text("Fusion Word"),
            self.translate_text("Division PDF"),
            self.translate_text("Protection PDF"),
            self.translate_text("Compression"),
            self.translate_text("Optimisation de fichiers")
        ])
        self.type_filter_combo.currentIndexChanged.connect(self.filter_templates)
        
        filter_layout.addWidget(QLabel(self.translate_text("Recherche:")))
        filter_layout.addWidget(self.search_input, 2)
        filter_layout.addWidget(QLabel(self.translate_text("Type:")))
        filter_layout.addWidget(self.type_filter_combo, 1)
        
        main_layout.addLayout(filter_layout)
        
        splitter = QSplitter(Qt.Horizontal)
        
        self.templates_list = QListWidget()
        self.templates_list.setMinimumWidth(300)
        self.templates_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.templates_list.itemSelectionChanged.connect(self.show_template_details)
        self.templates_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.templates_list.customContextMenuRequested.connect(self.show_template_context_menu)
        
        self.details_widget = QWidget()
        self.details_layout = QVBoxLayout(self.details_widget)

        # Header row: optional icon pixmap + text label side by side
        self._header_row = QWidget()
        self._header_row_layout = QHBoxLayout(self._header_row)
        self._header_row_layout.setContentsMargins(0, 0, 0, 0)
        self._header_row_layout.setSpacing(6)

        self._header_icon_label = QLabel()
        self._header_icon_label.setFixedSize(20, 20)
        self._header_icon_label.setScaledContents(True)
        self._header_icon_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self._header_icon_label.hide()
        self._header_row_layout.addWidget(self._header_icon_label, 0, Qt.AlignVCenter)

        self.details_header = QLabel(self.translate_text("Sélectionnez un template pour voir ses détails"))
        self.details_header.setStyleSheet("font-size: 16px; font-weight: bold;")
        self._header_row_layout.addWidget(self.details_header, 0, Qt.AlignVCenter)
        self._header_row_layout.addStretch()

        self.details_layout.addWidget(self._header_row)
        
        self.details_scroll = QScrollArea()
        self.details_scroll.setWidgetResizable(True)
        self.details_content = QWidget()
        self.details_content_layout = QVBoxLayout(self.details_content)
        self.details_scroll.setWidget(self.details_content)
        
        self.details_layout.addWidget(self.details_scroll)
        
        self.details_buttons = QWidget()
        self.details_buttons_layout = QHBoxLayout(self.details_buttons)
        
        self.apply_btn = QPushButton("🚀 " + self.translate_text("Appliquer ce template"))
        self.apply_btn.setObjectName("TemplateApplyBtn")
        self.apply_btn.clicked.connect(self.apply_selected_template)
        self.apply_btn.setEnabled(False)
        
        self.edit_btn = QPushButton("✏️ " + self.translate_text("Modifier"))
        self.edit_btn.setObjectName("TemplateEditBtn")
        self.edit_btn.clicked.connect(self.edit_selected_template)
        self.edit_btn.setEnabled(False)
        
        self.delete_btn = QPushButton("🗑️ " + self.translate_text("Supprimer"))
        self.delete_btn.setObjectName("TemplateDeleteBtn")
        self.delete_btn.clicked.connect(self.delete_selected_template)
        self.delete_btn.setEnabled(False)
        
        self.details_buttons_layout.addWidget(self.apply_btn)
        self.details_buttons_layout.addWidget(self.edit_btn)
        self.details_buttons_layout.addWidget(self.delete_btn)
        self.details_buttons_layout.addStretch()
        
        self.details_layout.addWidget(self.details_buttons)
        
        splitter.addWidget(self.templates_list)
        splitter.addWidget(self.details_widget)
        splitter.setSizes([300, 700])
        
        main_layout.addWidget(splitter, 1)
        
        button_layout = QHBoxLayout()
        
        self.close_btn = QPushButton(self.translate_text("Fermer"))
        self.close_btn.setObjectName("TemplateCloseBtn")
        self.close_btn.clicked.connect(self.close)

        button_layout.addStretch()
        button_layout.addWidget(self.close_btn)
        
        main_layout.addLayout(button_layout)

    @staticmethod
    def _template_icon():
        """Return QIcon from icons/template.ico (sibling of templates/ folder), fallback None."""
        ico_path = Path(__file__).parent.parent / "icons" / "template.ico"
        if ico_path.exists():
            return QIcon(str(ico_path))
        return None

    def _make_template_label(self, name: str, is_default: bool) -> tuple:
        """Return (label_text, icon_or_None) for a template list item / header."""
        if is_default:
            return f"⭐ {name}", None
        icon = self._template_icon()
        # If the .ico is available: no emoji prefix anywhere.
        # The list uses setIcon(), the header uses _header_icon_label pixmap.
        # Fallback to 📋 only when ico is missing.
        label = name if icon else f"📋 {name}"
        return label, icon

    def load_templates(self):
        """Load all templates"""
        self.templates_list.clear()
        self.template_manager.load_templates()
        
        filter_type = self.type_filter_combo.currentText()
        
        for template_id, template in self.template_manager.current_templates.items():
            if filter_type != self.translate_text("Tous les types") and template['type'] != filter_type:
                continue
            
            is_default = template['config'].get('is_default', False)
            label, icon = self._make_template_label(template['name'], is_default)
            item = QListWidgetItem(label)
            if icon:
                item.setIcon(icon)
            item.setData(Qt.UserRole, template_id)
            item.setData(Qt.UserRole, template_id)
            
            tooltip = f"{template['type']}\n"
            tooltip += f"{self.translate_text('Créé le:')} {template['created_at']}\n"
            if template['last_used']:
                tooltip += f"{self.translate_text('Dernière utilisation:')} {template['last_used']}"
            else:
                tooltip += self.translate_text("Jamais utilisé")
            
            item.setToolTip(tooltip)
            self.templates_list.addItem(item)
        
        if self.templates_list.count() == 0:
            item = QListWidgetItem(self.translate_text("Aucun template disponible"))
            item.setFlags(Qt.NoItemFlags)
            item.setForeground(QColor(150, 150, 150))
            self.templates_list.addItem(item)

    def filter_templates(self):
        """Filter the template list with advanced search"""
        search_text = self.search_input.text().lower()
        filter_type = self.type_filter_combo.currentText()
        
        for i in range(self.templates_list.count()):
            item = self.templates_list.item(i)
            
            if item.flags() & Qt.NoItemFlags:
                continue
            
            template_id = item.data(Qt.UserRole)
            template = self.template_manager.get_template_by_id(template_id)
            
            show_item = True
            
            if filter_type != self.translate_text("Tous les types") and template['type'] != filter_type:
                show_item = False
            
            if search_text:
                search_terms = search_text.split()
                template_text = f"{template['name']} {template['type']} {json.dumps(template['config'])}".lower()
                
                all_terms_found = all(term in template_text for term in search_terms)
                
                if not all_terms_found:
                    show_item = False
            
            item.setHidden(not show_item)

    def show_template_details(self):
        """Display the selected template's details"""
        while self.details_content_layout.count():
            item = self.details_content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        selected_items = self.templates_list.selectedItems()
        if not selected_items:
            self.details_header.setText(self.translate_text("Sélectionnez un template pour voir ses détails"))
            self.apply_btn.setEnabled(False)
            self.edit_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            return
        
        item = selected_items[0]
        template_id = item.data(Qt.UserRole)
        template = self.template_manager.get_template_by_id(template_id)
        
        if not template:
            return
        
        self.selected_template_id = template_id

        is_default = template["config"].get("is_default", False)
        header_text, icon = self._make_template_label(template["name"], is_default)
        self.details_header.setText(header_text)
        # Show icon pixmap next to header text if available
        if icon and not icon.isNull():
            pixmap = icon.pixmap(20, 20)
            self._header_icon_label.setPixmap(pixmap)
            self._header_icon_label.show()
        else:
            self._header_icon_label.hide()

        self._default_btn = QPushButton(
            self.translate_text("✅ Template par défaut — Retirer") if is_default
            else self.translate_text("⭐ Définir comme template par défaut")
        )
        _dark_d = hasattr(self.parent_window, 'dark_mode') and self.parent_window.dark_mode
        if is_default:
            _bg, _bg_h, _col, _brd = (
                ("#196c2e", "#238636", "#3fb950", "#2ea043") if _dark_d
                else ("#dafbe1", "#ccffd8", "#1a7f37", "#1a7f37")
            )
        else:
            _bg, _bg_h, _col, _brd = (
                ("#2d2a0f", "#3a360f", "#e3b341", "#9e6a03") if _dark_d
                else ("#fff8c5", "#fef2a1", "#9a6700", "#d4a72c")
            )
        self._default_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {_bg}; color: {_col};
                border: 1px solid {_brd}; padding: 6px 14px;
                border-radius: 7px; font-weight: 700; font-size: 12px;
            }}
            QPushButton:hover {{ background-color: {_bg_h}; }}
        """)
        self._default_btn.clicked.connect(lambda: self._toggle_default(template_id, template['type']))
        self.details_content_layout.addWidget(self._default_btn)
        
        info_group = QGroupBox(self.translate_text("Informations générales"))
        info_layout = QFormLayout(info_group)
        
        info_layout.addRow(self.translate_text("Type:"), QLabel(template['type']))
        info_layout.addRow(self.translate_text("Créé le:"), QLabel(template['created_at']))
        
        last_used = template['last_used'] if template['last_used'] else self.translate_text("Jamais")
        info_layout.addRow(self.translate_text("Dernière utilisation:"), QLabel(last_used))
        
        self.details_content_layout.addWidget(info_group)
        
        config_group = QGroupBox(self.translate_text("Configuration"))
        config_layout = QVBoxLayout(config_group)
        
        config_text = self.format_config_for_display(template['config'], template['type'])
        config_label = QLabel(config_text)
        config_label.setWordWrap(True)
        _dark = hasattr(self.parent_window, 'dark_mode') and self.parent_window.dark_mode
        if _dark:
            config_label.setStyleSheet(
                "color: #c9d1d9; background-color: #161b22; padding: 10px;"
                "border: 1px solid #30363d; border-radius: 6px; font-size: 12px;"
            )
        else:
            config_label.setStyleSheet(
                "color: #1f2328; background-color: #f6f8fa; padding: 10px;"
                "border: 1px solid #d0d7de; border-radius: 6px; font-size: 12px;"
            )
        
        config_layout.addWidget(config_label)
        self.details_content_layout.addWidget(config_group)
        
        self.details_content_layout.addStretch()
        
        self.apply_btn.setEnabled(True)
        self.edit_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)

    def format_config_for_display(self, config, template_type):
        """Format the configuration for display — comparison uses normalized type (French canonical)."""
        _dark = hasattr(self.parent_window, 'dark_mode') and self.parent_window.dark_mode
        if _dark:
            style = ("color: #c9d1d9; background-color: #161b22; padding: 10px;"
                     "border: 1px solid #30363d; border-radius: 6px;")
        else:
            style = ("color: #1f2328; background-color: #f6f8fa; padding: 10px;"
                     "border: 1px solid #d0d7de; border-radius: 6px;")

        t = TemplateManager.normalize_type(template_type)

        oui = self.translate_text("Oui")
        non = self.translate_text("Non")
        ns  = self.translate_text("Non spécifié")

        def tv(val, fallback=None):
            if val is None:
                return fallback if fallback is not None else ns
            translated = self.translate_text(str(val))
            return translated if translated else str(val)

        def translate_name_template(tpl):
            if not tpl:
                return tpl
            return tpl.replace("{heure}", self.translate_text("{heure}"))

        if t == "Conversion PDF→Word":
            return f"""
            <div style="{style}">
            📋 <b>{self.translate_text("Mode de conversion:")}</b> {tv(config.get('mode'))}
            </div>
            """
        elif t == "Conversion Word→PDF":
            return f"""
            <div style="{style}">
            🔄 <b>{self.translate_text("Mode de conversion:")}</b> {tv(config.get('mode'))}<br>
            🎨 <b>{self.translate_text("Qualité d'image:")}</b> {tv(config.get('quality'))}<br>
            📝 <b>{self.translate_text("Inclure métadonnées:")}</b> {oui if config.get('include_metadata', False) else non}<br>
            🗜️ <b>{self.translate_text("Compresser le PDF:")}</b> {oui if config.get('compress_images', False) else non}
            </div>
            """
        elif t == "Conversion Images→PDF":
            separate = config.get('separate', False)
            return f"""
            <div style="{style}">
            📄 <b>{self.translate_text("Mode:")}</b> {self.translate_text("Un PDF par image") if separate else self.translate_text("Fusionner en un seul PDF")}
            </div>
            """
        elif t == "Fusion PDF":
            return f"""
            <div style="{style}">
            🔢 <b>{self.translate_text("Ordre de fusion:")}</b> {tv(config.get('merge_order'))}<br>
            📄 <b>{self.translate_text("Template de nom:")}</b> {translate_name_template(config.get('name_template', ns))}
            </div>
            """
        elif t == "Fusion Word":
            return f"""
            <div style="{style}">
            🔢 <b>{self.translate_text("Ordre de fusion:")}</b> {tv(config.get('merge_order'))}<br>
            📄 <b>{self.translate_text("Template de nom:")}</b> {translate_name_template(config.get('name_template', ns))}
            </div>
            """
        elif t == "Division PDF":
            return f"""
            <div style="{style}">
            ✂️ <b>{self.translate_text("Méthode de division:")}</b> {tv(config.get('split_method'))}<br>
            📄 <b>{self.translate_text("Pages par fichier:")}</b> {config.get('pages_per_file', 1)}
            </div>
            """
        elif t == "Protection PDF":
            return f"""
            <div style="{style}">
            🔒 <b>{self.translate_text("Mode:")}</b> {tv(config.get('mode'))}<br>
            🖨️ <b>{self.translate_text("Autoriser l'impression:")}</b> {oui if config.get('allow_printing', True) else non}<br>
            📋 <b>{self.translate_text("Autoriser la copie de texte:")}</b> {oui if config.get('allow_copying', True) else non}<br>
            ✏️ <b>{self.translate_text("Autoriser les modifications:")}</b> {oui if config.get('allow_modifications', False) else non}
            </div>
            """
        elif t == "Compression":
            encrypt     = config.get('encrypt', False)
            delete_orig = config.get('delete_originals', False)
            split_size  = config.get('split_size', 0)
            return f"""
            <div style="{style}">
            📦 <b>{self.translate_text("Format d'archive:")}</b> {tv(config.get('format'))}<br>
            🗜️ <b>{self.translate_text("Niveau de compression:")}</b> {tv(config.get('compression_level'))}<br>
            🔒 <b>{self.translate_text("Protéger par mot de passe:")}</b> {oui if encrypt else non}<br>
            🗑️ <b>{self.translate_text("Supprimer les originaux:")}</b> {oui if delete_orig else non}<br>
            📂 <b>{self.translate_text("Fractionnement:")}</b> {oui if split_size > 0 else non}<br>
            📏 <b>{self.translate_text("Taille par partie:")}</b> {split_size} Mo
            </div>
            """
        elif t == "Optimisation de fichiers":
            _mode_labels = {0: "Compression", 1: "Nettoyage", 2: "Compression + Nettoyage"}
            _ql_labels   = {0: "I — Haute qualité", 1: "II — Équilibré", 2: "III — Maximum"}
            return f"""
            <div style="{style}">
            🗜️ <b>{self.translate_text("Mode d'optimisation:")}</b> {_mode_labels.get(config.get('optimization_type', 2), '—')}<br>
            📊 <b>{self.translate_text("Niveau de compression:")}</b> {_ql_labels.get(config.get('quality_level', 1), '—')}<br>
            🗑️ <b>{self.translate_text("Supprimer métadonnées:")}</b> {'✓' if config.get('remove_metadata', True) else '✗'}<br>
            🖼️ <b>{self.translate_text("Recompresser images:")}</b> {'✓' if config.get('compress_images', True) else '✗'}<br>
            💾 <b>{self.translate_text("Garder copie originaux:")}</b> {'✓' if config.get('keep_backup', True) else '✗'}
            </div>
            """
        else:
            return json.dumps(config, indent=2, ensure_ascii=False)

    def show_template_context_menu(self, position):
        """Display the context menu for a template"""
        item = self.templates_list.itemAt(position)
        if not item or not item.flags() & Qt.ItemIsSelectable:
            return
        
        template_id = item.data(Qt.UserRole)
        template = self.template_manager.get_template_by_id(template_id)
        
        if not template:
            return
        
        menu = QMenu()
        
        apply_action = menu.addAction("🚀 " + self.translate_text("Appliquer"))
        duplicate_action = menu.addAction("📋 " + self.translate_text("Dupliquer"))
        export_single_action = menu.addAction("💾 " + self.translate_text("Exporter ce template"))
        delete_action = menu.addAction("🗑️ " + self.translate_text("Supprimer"))
        
        action = menu.exec(self.templates_list.mapToGlobal(position))
        
        if action == apply_action:
            self.apply_template(template_id)
        elif action == duplicate_action:
            self.duplicate_template(template_id, template)
        elif action == export_single_action:
            self.export_single_template(template_id, template)
        elif action == delete_action:
            self.delete_template(template_id)

    def apply_selected_template(self):
        """Apply the selected template"""
        if self.selected_template_id:
            self.apply_template(self.selected_template_id)

    def apply_template(self, template_id):
        """Apply the template and immediately launch the corresponding operation."""
        template = self.template_manager.get_template_by_id(template_id)
        if not template:
            QMessageBox.warning(self, self.translate_text("Erreur"),
                                self.translate_text("Template introuvable."))
            return

        t_type = template['type']
        ext_filter = self.get_file_extensions_for_template(t_type)
        compatible = self.get_compatible_files(t_type)

        success = self.template_manager.apply_template(template_id, self.parent_window)
        if not success:
            QMessageBox.warning(self, self.translate_text("Erreur"),
                                self.translate_text("Erreur lors de l'application du template."))
            return

        self.template_applied.emit(template)
        self.load_templates()

        ach = self._ach()
        if ach:
            try:
                ach.record_template_applied(str(template_id), t_type)
            except Exception:
                pass
        if compatible:
            msg = self.translate_text(
                "{n} fichier(s) compatible(s) trouvé(s) dans la liste.\n"
                "Appliquer sur ces fichiers ou en sélectionner d'autres ?"
            ).format(n=len(compatible))
        else:
            msg = self.translate_text(
                "Aucun fichier compatible dans la liste.\n"
                "Voulez-vous sélectionner des fichiers ?"
            )

        dialog = QDialog(self)
        dialog.setWindowTitle(self.translate_text("Appliquer le template"))
        dialog.setMinimumWidth(380)
        lay = QVBoxLayout(dialog)

        lbl = QLabel(msg)
        lbl.setWordWrap(True)
        lay.addWidget(lbl)
        lay.addSpacing(8)

        btn_row = QHBoxLayout()

        pw = self.parent_window

        _dark_at = hasattr(self.parent_window, 'dark_mode') and self.parent_window.dark_mode
        _ss_green = (
            "QPushButton { background-color:#238636; color:#ffffff; border:1px solid #2ea043;"
            " border-radius:7px; font-weight:700; padding:6px 14px; }"
            " QPushButton:hover { background-color:#2ea043; }"
            " QPushButton:pressed { background-color:#196c2e; }"
        ) if _dark_at else (
            "QPushButton { background-color:#1a7f37; color:#ffffff; border:none;"
            " border-radius:7px; font-weight:700; padding:6px 14px; }"
            " QPushButton:hover { background-color:#1c8b3c; }"
        )
        _ss_blue = (
            "QPushButton { background-color:#1f6feb; color:#ffffff; border:1px solid #388bfd;"
            " border-radius:7px; font-weight:700; padding:6px 14px; }"
            " QPushButton:hover { background-color:#388bfd; }"
        ) if _dark_at else (
            "QPushButton { background-color:#0969da; color:#ffffff; border:none;"
            " border-radius:7px; font-weight:700; padding:6px 14px; }"
            " QPushButton:hover { background-color:#0860ca; }"
        )
        _ss_grey = (
            "QPushButton { background-color:#21262d; color:#c9d1d9; border:1px solid #30363d;"
            " border-radius:7px; font-weight:700; padding:6px 14px; }"
            " QPushButton:hover { background-color:#30363d; color:#e6edf3; }"
        ) if _dark_at else (
            "QPushButton { background-color:#f6f8fa; color:#1f2328; border:1px solid #d0d7de;"
            " border-radius:7px; font-weight:700; padding:6px 14px; }"
            " QPushButton:hover { background-color:#eaeef2; }"
        )
        if compatible:
            btn_current = QPushButton("▶  " + self.translate_text("Fichiers actuels ({n})").format(n=len(compatible)))
            btn_current.setMinimumHeight(36)
            btn_current.setStyleSheet(_ss_green)
            def _use_current():
                dialog.accept()
                self.close()
                QTimer.singleShot(0, lambda: self._launch_operation(t_type))
            btn_current.clicked.connect(_use_current)
            btn_row.addWidget(btn_current)

        btn_select = QPushButton("📁  " + self.translate_text("Sélectionner des fichiers"))
        btn_select.setMinimumHeight(36)
        btn_select.setStyleSheet(_ss_blue)

        def _select():
            dialog.accept()
            files, _ = QFileDialog.getOpenFileNames(
                self, self.translate_text("Sélectionner des fichiers"), "", ext_filter)
            if files:
                pw.add_files_to_list(files)
                self.close()
                QTimer.singleShot(0, lambda: self._launch_operation(t_type))

        btn_select.clicked.connect(_select)
        btn_row.addWidget(btn_select)

        btn_cancel = QPushButton(self.translate_text("Annuler"))
        btn_cancel.setMinimumHeight(36)
        btn_cancel.setStyleSheet(_ss_grey)
        btn_cancel.clicked.connect(dialog.reject)
        btn_row.addWidget(btn_cancel)

        lay.addLayout(btn_row)
        dialog.exec()

    def _launch_operation(self, template_type):
        """Launch the operation matching the template type."""
        pw = self.parent_window
        tr = self.translate_text
        ops = {
            tr("Conversion PDF→Word"):   pw.convert_pdf_to_word,
            tr("Conversion Word→PDF"):   pw.convert_word_to_pdf,
            tr("Conversion Images→PDF"): pw.convert_images_to_pdf,
            tr("Fusion PDF"):            pw.merge_pdfs,
            tr("Fusion Word"):           pw.merge_word_docs,
            tr("Division PDF"):          pw.split_pdf,
            tr("Protection PDF"):        pw.protect_pdf,
            tr("Compression"):           pw.compress_files,
        }
        op = ops.get(template_type)
        if op:
            op()

    def get_compatible_files(self, template_type):
        """Return files compatible with the template type from the main list"""
        if not hasattr(self.parent_window, 'files_list'):
            return []
        
        file_extensions = {
            self.translate_text("Conversion PDF→Word"): ['.pdf'],
            self.translate_text("Conversion Word→PDF"): ['.docx', '.doc'],
            self.translate_text("Conversion Images→PDF"): ['.png', '.jpeg', '.jpg', '.bmp', '.heic', '.heif', '.gif', '.jpx',
                                                           '.webp', '.tiff', '.tif', '.psd', '.svg', '.avif', '.j2k', '.jp2',
                                                           '.dng', '.cr2', '.cr3', '.nef', '.arw', '.orf', '.rw2', '.raf', '.jfif'],
            self.translate_text("Fusion PDF"): ['.pdf'],
            self.translate_text("Fusion Word"): ['.docx', '.doc'],
            self.translate_text("Division PDF"): ['.pdf'],
            self.translate_text("Protection PDF"): ['.pdf'],
            self.translate_text("Compression"): ['.*']
        }
        
        extensions = file_extensions.get(template_type, [])
        compatible_files = []
        
        for file_path in self.parent_window.files_list:
            if template_type == self.translate_text("Compression"):
                compatible_files.append(file_path)
            else:
                file_ext = Path(file_path).suffix.lower()
                if file_ext in extensions:
                    compatible_files.append(file_path)
        
        return compatible_files

    def get_file_extensions_for_template(self, template_type):
        """Return file extensions for a given template type"""
        if template_type == self.translate_text("Conversion PDF→Word"):
            return "Fichiers PDF (*.pdf)"
        elif template_type == self.translate_text("Conversion Word→PDF"):
            return "Fichiers Word (*.docx *.doc)"
        elif template_type == self.translate_text("Conversion Images→PDF"):
            return "Images (*.jpg *.jpeg *.png *.bmp *.tiff *.tif *.webp *.heic *.heif *.avif *.psd *.svg *.dng)"
        elif template_type == self.translate_text("Fusion PDF"):
            return "Fichiers PDF (*.pdf)"
        elif template_type == self.translate_text("Fusion Word"):
            return "Fichiers Word (*.docx *.doc)"
        elif template_type == self.translate_text("Division PDF"):
            return "Fichiers PDF (*.pdf)"
        elif template_type == self.translate_text("Protection PDF"):
            return "Fichiers PDF (*.pdf)"
        elif template_type == self.translate_text("Compression"):
            return "Tous les fichiers (*.*)"
        else:
            return "Tous les fichiers (*.*)"

    def duplicate_template(self, template_id, template):
        """Duplicate a template"""
        dialog = QInputDialog(self)
        dialog.setWindowTitle(self.translate_text("Dupliquer le template"))
        dialog.setLabelText(self.translate_text("Nouveau nom pour le template:"))
        dialog.setTextValue(f"{template['name']} - Copie")
        
        if dialog.exec() == QDialog.Accepted:
            new_name = dialog.textValue().strip()
            if new_name:
                self.template_manager.db_manager.save_template(
                    new_name,
                    template['type'],
                    template['config']
                )
                
                QMessageBox.information(
                    self,
                    self.translate_text("Succès"),
                    self.translate_text("Template dupliqué avec succès!")
                )
                
                self.load_templates()

    def export_single_template(self, template_id, template):
        """Export a single template"""
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            self.translate_text("Exporter le template"),
            f"{template['name']}.json",
            "JSON (*.json)"
        )
        
        if filepath:
            template_data = {
                'name': template['name'],
                'type': template['type'],
                'config': template['config'],
                'export_date': datetime.now().isoformat()
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, indent=2, ensure_ascii=False)

            ach = self._ach()
            if ach:
                try: ach.record_template_exported()
                except Exception: pass

            QMessageBox.information(
                self,
                self.translate_text("Succès"),
                self.translate_text(f"Template exporté vers {filepath}")
            )

    def edit_selected_template(self):
        """Edit the selected template"""
        if self.selected_template_id:
            self.edit_template(self.selected_template_id)

    def edit_template(self, template_id):
        """Edit a template"""
        template = self.template_manager.get_template_by_id(template_id)
        if not template:
            return
        
        dialog = TemplateEditorDialog(template, self)
        if dialog.exec() == QDialog.Accepted:
            new_config = dialog.get_updated_config()
            
            try:
                new_name = dialog.name_input.text().strip() or template['name']
                conn = sqlite3.connect(self.template_manager.db_manager.db_path)
                cursor = conn.cursor()
                
                cursor.execute(
                    "UPDATE templates SET name = ?, config_data = ? WHERE id = ?",
                    (new_name, json.dumps(new_config), template_id)
                )
                conn.commit()
                conn.close()

                self.template_manager.load_templates()
                self.load_templates()

                QMessageBox.information(
                    self,
                    self.translate_text("Succès"),
                    self.translate_text("Template modifié avec succès!")
                )

                ach = self._ach()
                if ach:
                    try: ach.record_template_edited()
                    except Exception: pass

                self.load_templates()
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    self.translate_text("Erreur"),
                    self.translate_text(f"Erreur lors de la modification: {str(e)}")
                )

    def delete_selected_template(self):
        """Delete the selected template (single — kept for button compat)"""
        self.delete_selected_templates()

    def delete_selected_templates(self):
        """Delete all selected templates — supports multi-selection."""
        selected_items = self.templates_list.selectedItems()
        if not selected_items:
            return

        template_ids = []
        for item in selected_items:
            tid = item.data(Qt.UserRole)
            if tid is not None:
                template_ids.append(tid)

        if not template_ids:
            return

        count = len(template_ids)
        if count == 1:
            template = self.template_manager.get_template_by_id(template_ids[0])
            name = template['name'] if template else '?'
            msg = self.translate_text("template_deleted").format(name)
        else:
            msg = self.translate_text(
                "Voulez-vous vraiment supprimer {n} templates ?"
            ).format(n=count)

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(self.translate_text("Confirmation"))
        msg_box.setText(msg)
        msg_box.setIcon(QMessageBox.Question)

        yes_btn = msg_box.addButton(QMessageBox.Yes)
        no_btn  = msg_box.addButton(QMessageBox.No)
        msg_box.setDefaultButton(no_btn)
        yes_btn.setObjectName("BtnOK")
        no_btn.setObjectName("BtnCancel")
        msg_box.exec()

        if msg_box.clickedButton() == yes_btn:
            for tid in template_ids:
                self.template_manager.delete_template(tid)
            self.load_templates()
            self.selected_template_id = None
            self.show_template_details()

    def delete_template(self, template_id):
        """Delete a template"""
        template = self.template_manager.get_template_by_id(template_id)
        if not template:
            return

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(self.translate_text("Confirmation"))
        template_name = template['name']
        msg_box.setText(self.translate_text("template_deleted").format(template_name))
        msg_box.setIcon(QMessageBox.Question)

        yes_button = msg_box.addButton(QMessageBox.Yes)
        no_button = msg_box.addButton(QMessageBox.No)
        msg_box.setDefaultButton(no_button)
        yes_button.setObjectName("BtnOK")
        no_button.setObjectName("BtnCancel")

        msg_box.exec()

        if msg_box.clickedButton() == yes_button:
            self.template_manager.delete_template(template_id)
            self.load_templates()
            self.selected_template_id = None
            self.show_template_details()

    def create_new_template_dialog(self):
        """Open the template creation dialog"""
        dialog = CreateTemplateDialog(self.template_manager, self.parent_window, self)
        if dialog.exec() == QDialog.Accepted:
            self.load_templates()

    def import_templates(self):
        """Import templates from a file"""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            self.translate_text("Importer des templates"),
            "",
            "JSON (*.json)"
        )
        
        if filepath:
            imported_count = self.template_manager.import_templates(filepath)
            
            if imported_count > 0:
                ach = self._ach()
                if ach:
                    try: ach.record_template_imported(imported_count)
                    except Exception: pass
                QMessageBox.information(
                    self,
                    self.translate_text("Succès"),
                    self.translate_text(f"{imported_count} template(s) importé(s) avec succès!")
                )
                self.load_templates()
            else:
                QMessageBox.warning(
                    self,
                    self.translate_text("Information"),
                    self.translate_text("Aucun nouveau template importé (déjà existant ou fichier vide).")
                )

    def export_templates(self):
        """Export all templates"""
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            self.translate_text("Exporter tous les templates"),
            "templates_backup.json",
            "JSON (*.json)"
        )
        
        if filepath:
            exported_count = self.template_manager.export_templates(filepath)
            ach = self._ach()
            if ach:
                try: ach.record_template_exported()
                except Exception: pass
            QMessageBox.information(
                self,
                self.translate_text("Succès"),
                self.translate_text(f"{exported_count} template(s) exporté(s) vers {filepath}")
            )

    def _toggle_default(self, template_id, template_type):
        """Toggle the is_default flag for a template."""
        template = self.template_manager.get_template_by_id(template_id)
        if not template:
            return
        currently_default = template['config'].get('is_default', False)
        if currently_default:
            template['config']['is_default'] = False
            import json
            self.template_manager.db_manager.update_template_config(
                template_id, json.dumps(template['config']))
            self.template_manager.load_templates()
        else:
            self.template_manager.set_default_template(template_id, template_type)

        ach = self._ach()
        if ach:
            try: ach.record_template_default_set(self.template_manager)
            except Exception: pass

        self.load_templates()
        for i in range(self.templates_list.count()):
            if self.templates_list.item(i).data(Qt.UserRole) == template_id:
                self.templates_list.setCurrentRow(i)
                break

    def translate_text(self, text):
        """Translate text according to the current language"""
        return self._tm.translate_text(text)

    def _ach(self):
        """Return the achievement_system from parent_window, or None if disabled."""
        cfg = getattr(self.parent_window, 'config', {})
        if not cfg.get("achievements_enabled", True):
            return None
        return getattr(self.parent_window, 'achievement_system', None)

