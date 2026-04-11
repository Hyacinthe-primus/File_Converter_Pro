"""
Template Manager - File Converter Pro

System for saving and applying conversion presets to automate workflows.

Classes:
    EnhancedTemplatesDialog:
        - Master-detail interface for template management
        - Quick actions (Apply, Duplicate, Delete)
        - Contextual guides after applying templates
    
    CreateTemplateDialog:
        - Dynamic form generation based on template type
        - Configuration capture from current app settings
    
    TemplateEditorDialog:
        - Metadata editing (Name, Type)
        - Read-only configuration display (Future: editable)

Note:
    TemplateManager has been extracted to template_manager.py

Supported Types:
    - Conversions (PDF↔Word, Images→PDF)
    - Operations (Merge, Split, Protect, Compress)
    - OPtimizations (docx, pdf, images, epub etc...)

Author: Hyacinthe
Version: 1.0
"""

import os
import json
from pathlib import Path
from PySide6.QtWidgets import (QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QLabel, QListWidget, 
                               QListWidgetItem, QFileDialog, QMessageBox, 
                               QComboBox, QSplitter, QToolBar,
                               QGroupBox, QScrollArea, QLineEdit, QDialog, 
                               QDialogButtonBox, QFormLayout, QSpinBox, QMenu, QInputDialog)
from PySide6.QtCore import (Qt, QSize, QTimer, Signal)
from PySide6.QtGui import ( QColor, QAction, QKeySequence, QShortcut)
from datetime import datetime
import sqlite3

from widgets import AnimatedCheckBox
import sys as _sys, os as _os
_PKG_DIR  = _os.path.dirname(_os.path.abspath(__file__))
_ROOT_DIR = _os.path.dirname(_PKG_DIR)
if _ROOT_DIR not in _sys.path:
    _sys.path.insert(0, _ROOT_DIR)

from .template_manager import TemplateManager
from translations import TranslationManager

def _make_tm(language):
    tm = TranslationManager()
    tm.set_language(language)
    return tm

class EnhancedTemplatesDialog(QDialog):
    """Enhanced dialog for template management"""
    
    template_applied = Signal(dict)

    def __init__(self, template_manager, parent=None, language="fr"):
        super().__init__(parent)
        self.template_manager = template_manager
        self.language = language
        self._tm = _make_tm(language)
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

        if dark:
            style = """
            /* Base */
            QDialog, QWidget {
                background-color: #0d1117;
                color: #e6edf3;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
            }

            /* GroupBox */
            QGroupBox {
                font-weight: 700;
                font-size: 13px;
                border: 1px solid #30363d;
                border-radius: 10px;
                margin-top: 14px;
                padding-top: 10px;
                background-color: #161b22;
                color: #8b949e;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 6px;
                color: #8b949e;
            }

            /* Label */
            QLabel { color: #e6edf3; background: transparent; }

            /* Inputs */
            QLineEdit, QSpinBox, QTextEdit, QPlainTextEdit {
                background-color: #0d1117;
                color: #e6edf3;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 7px 10px;
                font-size: 13px;
                selection-background-color: #388bfd33;
            }
            QLineEdit:focus, QSpinBox:focus, QTextEdit:focus { border: 1px solid #388bfd; }
            QLineEdit:hover, QSpinBox:hover { border: 1px solid #484f58; }

            /* ComboBox */
            QComboBox {
                background-color: #21262d;
                color: #e6edf3;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 7px 10px;
                font-size: 13px;
                min-width: 120px;
            }
            QComboBox:hover { border: 1px solid #484f58; }
            QComboBox:focus { border: 1px solid #388bfd; }
            QComboBox::drop-down { border: none; width: 28px; }
            QComboBox::down-arrow {
                image: none; width: 0; height: 0;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #8b949e;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: #161b22;
                color: #e6edf3;
                border: 1px solid #30363d;
                border-radius: 6px;
                selection-background-color: #388bfd22;
                selection-color: #79c0ff;
                outline: none;
            }

            /* ListWidget */
            QListWidget {
                background-color: #161b22;
                color: #e6edf3;
                border: 1px solid #30363d;
                border-radius: 8px;
                font-size: 13px;
                outline: none;
            }
            QListWidget::item {
                padding: 9px 12px;
                border-bottom: 1px solid #21262d;
            }
            QListWidget::item:hover { background-color: #1f2937; }
            QListWidget::item:selected {
                background-color: #388bfd22;
                color: #79c0ff;
                border-left: 3px solid #388bfd;
                font-weight: 600;
            }

            /* Buttons (default) */
            QPushButton {
                background-color: #21262d;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 7px;
                font-weight: 700;
                font-size: 12px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #30363d;
                border-color: #8b949e;
                color: #e6edf3;
            }
            QPushButton:pressed { background-color: #161b22; border-color: #6e7681; }
            QPushButton:disabled { background-color: #161b22; color: #484f58; border-color: #21262d; }

            /* CheckBox */
            QCheckBox, QRadioButton {
                color: #e6edf3;
                spacing: 8px;
                font-size: 13px;
            }
            QCheckBox::indicator, QRadioButton::indicator {
                width: 16px; height: 16px;
                border: 2px solid #484f58;
                background-color: #0d1117;
            }
            QCheckBox::indicator   { border-radius: 4px; }
            QRadioButton::indicator { border-radius: 8px; }
            QCheckBox::indicator:hover, QRadioButton::indicator:hover { border-color: #388bfd; }
            QCheckBox::indicator:checked, QRadioButton::indicator:checked {
                background-color: #388bfd; border-color: #388bfd;
            }

            /* ScrollArea */
            QScrollArea, QScrollArea > QWidget, QScrollArea > QWidget > QWidget {
                background-color: transparent;
                border: none;
            }

            /* Scrollbars */
            QScrollBar:vertical {
                background: #0d1117; width: 8px; margin: 0; border: none;
            }
            QScrollBar::handle:vertical {
                background: #30363d; border-radius: 4px; min-height: 30px;
            }
            QScrollBar::handle:vertical:hover { background: #484f58; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
            QScrollBar:horizontal {
                background: #0d1117; height: 8px; margin: 0; border: none;
            }
            QScrollBar::handle:horizontal {
                background: #30363d; border-radius: 4px; min-width: 30px;
            }
            QScrollBar::handle:horizontal:hover { background: #484f58; }
            QScrollBar::add-page:vertical,  QScrollBar::sub-page:vertical,
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: transparent;
            }

            /* Toolbar */
            QToolBar {
                background-color: #161b22;
                border: none;
                border-bottom: 1px solid #30363d;
                spacing: 6px;
                padding: 6px;
            }
            QToolBar QToolButton {
                background: transparent; border: none;
                border-radius: 6px; padding: 6px;
                color: #e6edf3;
            }
            QToolBar QToolButton:hover   { background: #30363d; }
            QToolBar QToolButton:pressed { background: #21262d; }

            /* Splitter */
            QSplitter::handle { background: #30363d; width: 1px; height: 1px; }

            /* Menu */
            QMenu {
                background-color: #161b22; color: #e6edf3;
                border: 1px solid #30363d; border-radius: 8px; padding: 4px;
            }
            QMenu::item { padding: 7px 22px; border-radius: 5px; }
            QMenu::item:selected { background-color: #388bfd22; color: #79c0ff; }
            QMenu::separator { height: 1px; background: #30363d; margin: 4px 0; }

            /* Tooltip */
            QToolTip {
                background-color: #1e2330; color: #e6edf3;
                border: 1px solid #30363d; border-radius: 6px;
                padding: 7px 10px; font-size: 12px;
            }

            /* Table */
            QTableWidget {
                background-color: #161b22; color: #e6edf3;
                border: 1px solid #30363d; border-radius: 8px;
                gridline-color: #21262d;
                selection-background-color: #388bfd22;
                selection-color: #e6edf3; outline: none;
            }
            QTableWidget::item { padding: 7px 10px; border: none; }
            QTableWidget::item:hover { background-color: #1f2937; }
            QTableWidget::item:selected { background-color: #388bfd22; color: #79c0ff; }
            QHeaderView::section {
                background-color: #1e2330; color: #8b949e;
                border: none; border-right: 1px solid #30363d;
                border-bottom: 1px solid #30363d;
                padding: 8px 10px; font-weight: 700;
                font-size: 11px; letter-spacing: 0.4px;
            }
            """
        else:
            style = """
            /* Base */
            QDialog, QWidget {
                background-color: #f6f8fa;
                color: #1f2328;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
            }

            /* GroupBox */
            QGroupBox {
                font-weight: 700;
                font-size: 13px;
                border: 1px solid #d0d7de;
                border-radius: 10px;
                margin-top: 14px;
                padding-top: 10px;
                background-color: #ffffff;
                color: #57606a;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 6px;
                color: #57606a;
            }

            /* Label */
            QLabel { color: #1f2328; background: transparent; }

            /* Inputs */
            QLineEdit, QSpinBox, QTextEdit, QPlainTextEdit {
                background-color: #ffffff;
                color: #1f2328;
                border: 1px solid #d0d7de;
                border-radius: 6px;
                padding: 7px 10px;
                font-size: 13px;
                selection-background-color: #0969da33;
                selection-color: #0969da;
            }
            QLineEdit:focus, QSpinBox:focus, QTextEdit:focus { border: 1px solid #0969da; }
            QLineEdit:hover, QSpinBox:hover { border: 1px solid #8c959f; }

            /* ComboBox */
            QComboBox {
                background-color: #ffffff;
                color: #1f2328;
                border: 1px solid #d0d7de;
                border-radius: 6px;
                padding: 7px 10px;
                font-size: 13px;
                min-width: 120px;
            }
            QComboBox:hover { border: 1px solid #8c959f; }
            QComboBox:focus { border: 1px solid #0969da; }
            QComboBox::drop-down { border: none; width: 28px; }
            QComboBox::down-arrow {
                image: none; width: 0; height: 0;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #57606a;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                color: #1f2328;
                border: 1px solid #d0d7de;
                border-radius: 6px;
                selection-background-color: #0969da22;
                selection-color: #0969da;
                outline: none;
            }

            /* ListWidget */
            QListWidget {
                background-color: #ffffff;
                color: #1f2328;
                border: 1px solid #d0d7de;
                border-radius: 8px;
                font-size: 13px;
                outline: none;
            }
            QListWidget::item {
                padding: 9px 12px;
                border-bottom: 1px solid #f0f3f6;
            }
            QListWidget::item:hover { background-color: #f0f6ff; }
            QListWidget::item:selected {
                background-color: #0969da18;
                color: #0550ae;
                border-left: 3px solid #0969da;
                font-weight: 600;
            }

            /* Buttons (default) */
            QPushButton {
                background-color: #0969da;
                color: #ffffff;
                border: none;
                border-radius: 7px;
                font-weight: 700;
                font-size: 12px;
                padding: 8px 16px;
            }
            QPushButton:hover   { background-color: #0860ca; }
            QPushButton:pressed { background-color: #0757ba; }
            QPushButton:disabled { background-color: #d0d7de; color: #8c959f; }

            /* CheckBox */
            QCheckBox, QRadioButton {
                color: #1f2328;
                spacing: 8px;
                font-size: 13px;
            }
            QCheckBox::indicator, QRadioButton::indicator {
                width: 16px; height: 16px;
                border: 2px solid #d0d7de;
                background-color: #ffffff;
            }
            QCheckBox::indicator   { border-radius: 4px; }
            QRadioButton::indicator { border-radius: 8px; }
            QCheckBox::indicator:hover, QRadioButton::indicator:hover { border-color: #0969da; }
            QCheckBox::indicator:checked, QRadioButton::indicator:checked {
                background-color: #0969da; border-color: #0969da;
            }

            /* ScrollArea */
            QScrollArea, QScrollArea > QWidget, QScrollArea > QWidget > QWidget {
                background-color: transparent;
                border: none;
            }

            /* Scrollbars */
            QScrollBar:vertical {
                background: #f6f8fa; width: 8px; margin: 0; border: none;
            }
            QScrollBar::handle:vertical {
                background: #d0d7de; border-radius: 4px; min-height: 30px;
            }
            QScrollBar::handle:vertical:hover { background: #8c959f; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
            QScrollBar:horizontal {
                background: #f6f8fa; height: 8px; margin: 0; border: none;
            }
            QScrollBar::handle:horizontal {
                background: #d0d7de; border-radius: 4px; min-width: 30px;
            }
            QScrollBar::handle:horizontal:hover { background: #8c959f; }
            QScrollBar::add-page:vertical,  QScrollBar::sub-page:vertical,
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: transparent;
            }

            /* Toolbar */
            QToolBar {
                background-color: #eaeef2;
                border: none;
                border-bottom: 1px solid #d0d7de;
                spacing: 6px;
                padding: 6px;
            }
            QToolBar QToolButton {
                background: transparent; border: none;
                border-radius: 6px; padding: 6px;
                color: #1f2328;
            }
            QToolBar QToolButton:hover   { background: #d0d7de; }
            QToolBar QToolButton:pressed { background: #b8c0cc; }

            /* Splitter */
            QSplitter::handle { background: #d0d7de; width: 1px; height: 1px; }

            /* Menu */
            QMenu {
                background-color: #ffffff; color: #1f2328;
                border: 1px solid #d0d7de; border-radius: 8px; padding: 4px;
            }
            QMenu::item { padding: 7px 22px; border-radius: 5px; }
            QMenu::item:selected { background-color: #0969da18; color: #0550ae; }
            QMenu::separator { height: 1px; background: #d0d7de; margin: 4px 0; }

            /* Tooltip */
            QToolTip {
                background-color: #1f2328; color: #f0f6fc;
                border: none; border-radius: 6px;
                padding: 7px 10px; font-size: 12px;
            }

            /* Table */
            QTableWidget {
                background-color: #ffffff; color: #1f2328;
                border: 1px solid #d0d7de; border-radius: 8px;
                gridline-color: #f0f3f6;
                selection-background-color: #0969da18;
                selection-color: #1f2328; outline: none;
            }
            QTableWidget::item { padding: 7px 10px; border: none; }
            QTableWidget::item:hover { background-color: #f0f6ff; }
            QTableWidget::item:selected { background-color: #0969da18; color: #0550ae; }
            QHeaderView::section {
                background-color: #eaeef2; color: #57606a;
                border: none; border-right: 1px solid #d0d7de;
                border-bottom: 1px solid #d0d7de;
                padding: 8px 10px; font-weight: 700;
                font-size: 11px; letter-spacing: 0.4px;
            }
            QHeaderView::section:first { border-top-left-radius: 8px; }
            """

        self.setStyleSheet(style)

        self._refresh_inline_styles(dark)

    def _refresh_inline_styles(self, dark: bool):
        """Re-apply inline styles that depend on the current theme."""
        if dark:
            self.details_header.setStyleSheet(
                "font-size: 16px; font-weight: bold; margin-bottom: 15px; color: #e6edf3;")
            self.apply_btn.setStyleSheet("""
                QPushButton { background-color: #238636; color: #ffffff;
                    border: 1px solid #2ea043; border-radius: 7px;
                    font-weight: 700; padding: 8px 16px; }
                QPushButton:hover { background-color: #2ea043; border-color: #3fb950; }
                QPushButton:pressed { background-color: #196c2e; }
                QPushButton:disabled { background-color: #161b22; color: #484f58; border-color: #21262d; }
            """)
            self.edit_btn.setStyleSheet("""
                QPushButton { background-color: #1f6feb; color: #ffffff;
                    border: 1px solid #388bfd; border-radius: 7px;
                    font-weight: 700; padding: 8px 16px; }
                QPushButton:hover { background-color: #388bfd; }
                QPushButton:pressed { background-color: #1158c7; }
                QPushButton:disabled { background-color: #161b22; color: #484f58; border-color: #21262d; }
            """)
            self.delete_btn.setStyleSheet("""
                QPushButton { background-color: #b91c1c; color: #ffffff;
                    border: 1px solid #da3633; border-radius: 7px;
                    font-weight: 700; padding: 8px 16px; }
                QPushButton:hover { background-color: #da3633; }
                QPushButton:pressed { background-color: #991b1b; }
                QPushButton:disabled { background-color: #161b22; color: #484f58; border-color: #21262d; }
            """)
            self.close_btn.setStyleSheet("""
                QPushButton { background-color: #21262d; color: #c9d1d9;
                    border: 1px solid #30363d; border-radius: 7px;
                    font-weight: 700; padding: 8px 16px; }
                QPushButton:hover { background-color: #30363d; color: #e6edf3; border-color: #8b949e; }
                QPushButton:pressed { background-color: #161b22; }
            """)
        else:
            self.details_header.setStyleSheet(
                "font-size: 16px; font-weight: bold; margin-bottom: 15px; color: #1f2328;")
            self.apply_btn.setStyleSheet("""
                QPushButton { background-color: #1a7f37; color: #ffffff;
                    border: none; border-radius: 7px;
                    font-weight: 700; padding: 8px 16px; }
                QPushButton:hover { background-color: #1c8b3c; }
                QPushButton:pressed { background-color: #196f2f; }
                QPushButton:disabled { background-color: #d0d7de; color: #8c959f; }
            """)
            self.edit_btn.setStyleSheet("""
                QPushButton { background-color: #0969da; color: #ffffff;
                    border: none; border-radius: 7px;
                    font-weight: 700; padding: 8px 16px; }
                QPushButton:hover { background-color: #0860ca; }
                QPushButton:pressed { background-color: #0757ba; }
                QPushButton:disabled { background-color: #d0d7de; color: #8c959f; }
            """)
            self.delete_btn.setStyleSheet("""
                QPushButton { background-color: #cf222e; color: #ffffff;
                    border: none; border-radius: 7px;
                    font-weight: 700; padding: 8px 16px; }
                QPushButton:hover { background-color: #a40e26; }
                QPushButton:pressed { background-color: #82071e; }
                QPushButton:disabled { background-color: #d0d7de; color: #8c959f; }
            """)
            self.close_btn.setStyleSheet("""
                QPushButton { background-color: #f6f8fa; color: #1f2328;
                    border: 1px solid #d0d7de; border-radius: 7px;
                    font-weight: 700; padding: 8px 16px; }
                QPushButton:hover { background-color: #eaeef2; border-color: #8c959f; }
                QPushButton:pressed { background-color: #d0d7de; }
            """)

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
        _dark_c = hasattr(self.parent_window, 'dark_mode') and self.parent_window.dark_mode
        if ok_button:
            if _dark_c:
                ok_button.setStyleSheet("""
                    QPushButton { background-color: #238636; color: #ffffff;
                        border: 1px solid #2ea043; border-radius: 7px;
                        font-weight: 700; padding: 8px 16px; }
                    QPushButton:hover { background-color: #2ea043; }
                    QPushButton:pressed { background-color: #196c2e; }
                """)
            else:
                ok_button.setStyleSheet("""
                    QPushButton { background-color: #1a7f37; color: #ffffff;
                        border: none; border-radius: 7px;
                        font-weight: 700; padding: 8px 16px; }
                    QPushButton:hover { background-color: #1c8b3c; }
                    QPushButton:pressed { background-color: #196f2f; }
                """)
        cancel_button = buttons.button(QDialogButtonBox.Cancel)
        if cancel_button:
            if _dark_c:
                cancel_button.setStyleSheet("""
                    QPushButton { background-color: #21262d; color: #c9d1d9;
                        border: 1px solid #30363d; border-radius: 7px;
                        font-weight: 700; padding: 8px 16px; }
                    QPushButton:hover { background-color: #30363d; color: #e6edf3; }
                    QPushButton:pressed { background-color: #161b22; }
                """)
            else:
                cancel_button.setStyleSheet("""
                    QPushButton { background-color: #f6f8fa; color: #1f2328;
                        border: 1px solid #d0d7de; border-radius: 7px;
                        font-weight: 700; padding: 8px 16px; }
                    QPushButton:hover { background-color: #eaeef2; }
                    QPushButton:pressed { background-color: #d0d7de; }
                """)
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
        
        self.details_header = QLabel(self.translate_text("Sélectionnez un template pour voir ses détails"))
        self.details_header.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 15px;")
        self.details_layout.addWidget(self.details_header)
        
        self.details_scroll = QScrollArea()
        self.details_scroll.setWidgetResizable(True)
        self.details_content = QWidget()
        self.details_content_layout = QVBoxLayout(self.details_content)
        self.details_scroll.setWidget(self.details_content)
        
        self.details_layout.addWidget(self.details_scroll)
        
        self.details_buttons = QWidget()
        self.details_buttons_layout = QHBoxLayout(self.details_buttons)
        
        self.apply_btn = QPushButton("🚀 " + self.translate_text("Appliquer ce template"))
        self.apply_btn.setStyleSheet("""
        QPushButton {
            background-color: #a3e635;
            color: #1a1a1a;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #93d625;
        }
        QPushButton:pressed {
            background-color: #83c615;
        }
        QPushButton:disabled {
            background-color: #c1d8a0;
            color: #666666;
        }
        """)
        self.apply_btn.clicked.connect(self.apply_selected_template)
        self.apply_btn.setEnabled(False)
        
        self.edit_btn = QPushButton("✏️ " + self.translate_text("Modifier"))
        self.edit_btn.setStyleSheet("""
        QPushButton {
            background-color: #22d3ee;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #12c3de;
        }
        QPushButton:pressed {
            background-color: #02b3ce;
        }
        QPushButton:disabled {
            background-color: #80e4f4;
            color: #666666;
        }
        """)
        self.edit_btn.clicked.connect(self.edit_selected_template)
        self.edit_btn.setEnabled(False)
        
        self.delete_btn = QPushButton("🗑️ " + self.translate_text("Supprimer"))
        self.delete_btn.setStyleSheet("""
        QPushButton {
            background-color: #d946ef;  /* Rose Fuchsia/Magenta */
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #c936df;
        }
        QPushButton:pressed {
            background-color: #b926cf;
        }
        QPushButton:disabled {
            background-color: #e9a3f2;
            color: #666666;
        }
        """)
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
        self.close_btn.setStyleSheet("""
        QPushButton {
            background-color: #374151;
            color: #e5e7eb;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #475161;
        }
        QPushButton:pressed {
            background-color: #576171;
        }
        """)
        self.close_btn.clicked.connect(self.close)

        button_layout.addStretch()
        button_layout.addWidget(self.close_btn)
        
        main_layout.addLayout(button_layout)

    def load_templates(self):
        """Load all templates"""
        self.templates_list.clear()
        self.template_manager.load_templates()
        
        filter_type = self.type_filter_combo.currentText()
        
        for template_id, template in self.template_manager.current_templates.items():
            if filter_type != self.translate_text("Tous les types") and template['type'] != filter_type:
                continue
            
            is_default = template['config'].get('is_default', False)
            label = f"⭐ {template['name']}" if is_default else f"📋 {template['name']}"
            item = QListWidgetItem(label)
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

        is_default = template['config'].get('is_default', False)
        header_text = f"⭐ {template['name']}" if is_default else f"📋 {template['name']}"
        self.details_header.setText(header_text)

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
            self.translate_text("Conversion Images→PDF"): ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'],
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
            return "Images (*.jpg *.jpeg *.png *.bmp *.tiff *.webp)"
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
        yes_btn.setStyleSheet("""
            QPushButton { background:#28a745; color:white; border:none;
                          padding:6px 12px; border-radius:4px; font-weight:bold; }
            QPushButton:hover { background:#218838; }
        """)
        no_btn.setStyleSheet("""
            QPushButton { background:#B55454; color:white; border:none;
                          padding:6px 12px; border-radius:4px; font-weight:bold; }
            QPushButton:hover { background:#A04040; }
        """)
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

class CreateTemplateDialog(QDialog):
    """Dialog for creating a new template"""

    def __init__(self, template_manager, parent_app, parent_dialog):
        super().__init__(parent_dialog)
        self.template_manager = template_manager
        self.parent_app = parent_app
        self.parent_dialog = parent_dialog
        
        self.setWindowTitle(self.parent_dialog.translate_text("Créer un nouveau template"))
        self.setMinimumSize(600, 520)
        
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(self.parent_dialog.translate_text("ex: Conversion Haute Qualité"))
        
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            self.parent_dialog.translate_text("Conversion PDF→Word"),
            self.parent_dialog.translate_text("Conversion Word→PDF"),
            self.parent_dialog.translate_text("Conversion Images→PDF"),  
            self.parent_dialog.translate_text("Fusion PDF"),
            self.parent_dialog.translate_text("Fusion Word"),
            self.parent_dialog.translate_text("Division PDF"), 
            self.parent_dialog.translate_text("Protection PDF"),  
            self.parent_dialog.translate_text("Compression"), 
            self.parent_dialog.translate_text("Optimisation de fichiers")
        ])
        self.type_combo.currentIndexChanged.connect(self.update_config_form)
        
        form_layout.addRow(self.parent_dialog.translate_text("Nom du template:"), self.name_input)
        form_layout.addRow(self.parent_dialog.translate_text("Type de template:"), self.type_combo)
        
        self.config_widget = QWidget()
        self.config_layout = QVBoxLayout(self.config_widget)
        
        form_layout.addRow(self.parent_dialog.translate_text("Configuration:"), self.config_widget)
        
        layout.addLayout(form_layout)
        
        self.advanced_group = QGroupBox(self.parent_dialog.translate_text("Options avancées"))
        advanced_layout = QVBoxLayout(self.advanced_group)
        
        self.memorize_check = AnimatedCheckBox(self.parent_dialog.translate_text("Mémoriser pour la prochaine fois"))
        self.memorize_check.setToolTip(self.parent_dialog.translate_text(
            "Si coché, les paramètres saisis ici seront pré-remplis à la prochaine ouverture de ce dialog."))
        _mem = getattr(self.parent_app, 'config', {}).get('last_template_creation_params', {})
        self.memorize_check.setChecked(_mem.get('memorize', False))

        self.set_as_default_check = AnimatedCheckBox(self.parent_dialog.translate_text("Définir comme template par défaut"))
        self.set_as_default_check.setToolTip(self.parent_dialog.translate_text(
            "Si coché, ce template s'applique silencieusement à chaque utilisation de cette opération, sans passer par le panel Templates."))
        self.set_as_default_check.setChecked(False)

        advanced_layout.addWidget(self.memorize_check)
        advanced_layout.addWidget(self.set_as_default_check)
        
        layout.addWidget(self.advanced_group)
        layout.addStretch()
        
        button_layout = QHBoxLayout()
        
        create_btn = QPushButton("💾 " + self.parent_dialog.translate_text("Créer le template"))
        create_btn.clicked.connect(self.create_template)
        
        cancel_btn = QPushButton(self.parent_dialog.translate_text("Annuler"))
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(create_btn)
        
        layout.addLayout(button_layout)
        
        self.update_config_form()
    
    def create_images_to_pdf_config(self):
        """Create the configuration form for Images to PDF — merge toggle only."""
        self.separate_images_check = AnimatedCheckBox(
            self.parent_dialog.translate_text("Un PDF par image (au lieu de tout fusionner)"))
        self.separate_images_check.setChecked(False)
        self.config_layout.addWidget(self.separate_images_check)

    def create_word_merge_config(self):
        """Create the configuration form for Word merge"""
        order_label = QLabel(self.parent_dialog.translate_text("Ordre de fusion:"))
        self.word_merge_order_combo = QComboBox()
        self.word_merge_order_combo.addItems([
            self.parent_dialog.translate_text("Ordre actuel (liste principale)"),
            self.parent_dialog.translate_text("Alphabétique (A→Z)"),
            self.parent_dialog.translate_text("Alphabétique (Z→A)"),
            self.parent_dialog.translate_text("Numérique (1→9)"),
            self.parent_dialog.translate_text("Numérique (9→1)"),
            self.parent_dialog.translate_text("Date (ancien→nouveau)"),
            self.parent_dialog.translate_text("Date (nouveau→ancien)"),
            self.parent_dialog.translate_text("Manuel (glisser-déposer)"),
        ])
        name_label = QLabel(self.parent_dialog.translate_text("Template de nom de fichier:"))
        self.word_merge_name_input = QLineEdit()
        self.word_merge_name_input.setText("fusion_word_{date}_{heure}")
        self.config_layout.addWidget(order_label)
        self.config_layout.addWidget(self.word_merge_order_combo)
        self.config_layout.addWidget(name_label)
        self.config_layout.addWidget(self.word_merge_name_input)

    def create_compression_config(self):
        """Create the configuration form for compression"""
        self.config_layout.setContentsMargins(0, 4, 0, 4)
        self.config_layout.setSpacing(4)

        format_label = QLabel(self.parent_dialog.translate_text("Format d'archive:"))

        self.compression_format_combo = QComboBox()
        self.compression_format_combo.addItems([
            self.parent_dialog.translate_text("ZIP"),
            self.parent_dialog.translate_text("TAR.GZ"),
            self.parent_dialog.translate_text("TAR"),
            self.parent_dialog.translate_text("RAR")
        ])
        self.compression_format_combo.setMinimumHeight(30)
        self.compression_format_combo.setMaximumHeight(35)

        level_label = QLabel(self.parent_dialog.translate_text("Niveau de compression:"))
        self.compression_level_combo = QComboBox()
        self.compression_level_combo.addItems([
            self.parent_dialog.translate_text("Normal"),
            self.parent_dialog.translate_text("Haute compression"),
            self.parent_dialog.translate_text("Compression maximale")
        ])
        self.compression_level_combo.setMinimumHeight(28)
        self.compression_level_combo.setMaximumHeight(32)

        self.encrypt_check = AnimatedCheckBox(self.parent_dialog.translate_text("Protéger par mot de passe"))
        self.encrypt_check.setChecked(False)

        self.delete_originals_check = AnimatedCheckBox(self.parent_dialog.translate_text("Supprimer les fichiers originaux après compression"))
        self.delete_originals_check.setChecked(False)

        self.split_check = AnimatedCheckBox(self.parent_dialog.translate_text("Fractionner l'archive en plusieurs parties"))
        self.split_check.setChecked(False)

        split_size_label = QLabel(self.parent_dialog.translate_text("Taille par partie (Mo):"))
        self.split_size_spin = QSpinBox()
        self.split_size_spin.setRange(1, 1000)
        self.split_size_spin.setValue(100)
        self.split_size_spin.setMinimumHeight(28)
        self.split_size_spin.setEnabled(False)

        self.split_check.stateChanged.connect(lambda state: self.split_size_spin.setEnabled(state))

        self.config_layout.addWidget(format_label)
        self.config_layout.addWidget(self.compression_format_combo)
        self.config_layout.addSpacing(8)

        self.config_layout.addWidget(level_label)
        self.config_layout.addWidget(self.compression_level_combo)
        self.config_layout.addSpacing(8)

        self.config_layout.addWidget(self.encrypt_check)
        self.config_layout.addWidget(self.delete_originals_check)
        self.config_layout.addWidget(self.split_check)
        self.config_layout.addSpacing(8)

        self.config_layout.addWidget(split_size_label)
        self.config_layout.addWidget(self.split_size_spin)

    def update_config_form(self):
        """Update the configuration form based on the template type"""
        while self.config_layout.count():
            item = self.config_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        template_type = self.type_combo.currentText()
        
        if template_type == self.parent_dialog.translate_text("Conversion PDF→Word"):
            self.create_pdf_to_word_config()
        elif template_type == self.parent_dialog.translate_text("Conversion Word→PDF"):
            self.create_word_to_pdf_config()
        elif template_type == self.parent_dialog.translate_text("Conversion Images→PDF"):
            self.create_images_to_pdf_config()  
        elif template_type == self.parent_dialog.translate_text("Fusion PDF"):
            self.create_pdf_merge_config()
        elif template_type == self.parent_dialog.translate_text("Fusion Word"):
            self.create_word_merge_config()  
        elif template_type == self.parent_dialog.translate_text("Division PDF"):
            self.create_pdf_split_config()  
        elif template_type == self.parent_dialog.translate_text("Protection PDF"):
            self.create_pdf_protection_config()
        elif template_type == self.parent_dialog.translate_text("Compression"):
            self.create_compression_config()
        elif template_type == self.parent_dialog.translate_text("Optimisation de fichiers"):
            self.create_optimization_config()

    def create_pdf_split_config(self):
        """Create the configuration form for PDF splitting.
        Note: 'Page range' will still open the dialog (start/end required).
        """
        method_label = QLabel(self.parent_dialog.translate_text("Méthode de division:"))
        self.split_method_combo = QComboBox()
        self.split_method_combo.addItems([
            self.parent_dialog.translate_text("Par pages"),
            self.parent_dialog.translate_text("Toutes les pages"),
            self.parent_dialog.translate_text("Plage de pages"),
        ])

        pages_label = QLabel(self.parent_dialog.translate_text("Pages par fichier:"))
        self.pages_per_file_spin = QSpinBox()
        self.pages_per_file_spin.setRange(1, 500)
        self.pages_per_file_spin.setValue(1)
        self.pages_per_file_spin.setMinimumHeight(28)

        self.config_layout.addWidget(method_label)
        self.config_layout.addWidget(self.split_method_combo)
        self.config_layout.addWidget(pages_label)
        self.config_layout.addWidget(self.pages_per_file_spin)

    def create_pdf_protection_config(self):
        """Create the configuration form for PDF protection.
        Basic mode — launches directly (permissions only).
        Advanced → prompts for a password before launching.
        """
        level_label = QLabel(self.parent_dialog.translate_text("Mode:"))
        self.protection_level_combo = QComboBox()
        self.protection_level_combo.addItems([
            self.parent_dialog.translate_text("Basique (restrictions uniquement)"),
            self.parent_dialog.translate_text("Avancé (mot de passe + restrictions)"),
        ])

        permissions_group = QGroupBox(self.parent_dialog.translate_text("Permissions"))
        permissions_layout = QVBoxLayout(permissions_group)

        self.allow_printing_check = AnimatedCheckBox(self.parent_dialog.translate_text("Autoriser l'impression"))
        self.allow_printing_check.setChecked(True)

        self.allow_copying_check = AnimatedCheckBox(self.parent_dialog.translate_text("Autoriser la copie de texte"))
        self.allow_copying_check.setChecked(True)

        self.allow_modifications_check = AnimatedCheckBox(self.parent_dialog.translate_text("Autoriser les modifications"))
        self.allow_modifications_check.setChecked(False)

        permissions_layout.addWidget(self.allow_printing_check)
        permissions_layout.addWidget(self.allow_copying_check)
        permissions_layout.addWidget(self.allow_modifications_check)

        self.config_layout.addWidget(level_label)
        self.config_layout.addWidget(self.protection_level_combo)
        self.config_layout.addWidget(permissions_group)

    def create_pdf_to_word_config(self):
        """Create the configuration form for PDF to Word — mode uniquement."""
        mode_label = QLabel(self.parent_dialog.translate_text("Mode de conversion:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            self.parent_dialog.translate_text("Conserver les images et la mise en page"),
            self.parent_dialog.translate_text("Texte brut uniquement"),
            self.parent_dialog.translate_text("Texte complet (texte + texte des images)"),
        ])
        self.config_layout.addWidget(mode_label)
        self.config_layout.addWidget(self.mode_combo)

    def create_word_to_pdf_config(self):
        """Create the configuration form for Word to PDF"""
        mode_label = QLabel(self.parent_dialog.translate_text("Mode de conversion:"))
        self.word_mode_combo = QComboBox()
        self.word_mode_combo.addItems([
            self.parent_dialog.translate_text("Conserver toute la mise en page"),
            self.parent_dialog.translate_text("Texte uniquement"),
        ])

        quality_label = QLabel(self.parent_dialog.translate_text("Qualité d'image:"))
        self.image_quality_combo = QComboBox()
        self.image_quality_combo.addItems([
            self.parent_dialog.translate_text("Haute (300 DPI)"),
            self.parent_dialog.translate_text("Standard (150 DPI)"),
            self.parent_dialog.translate_text("Basse (72 DPI)"),
        ])

        self.include_metadata_check = AnimatedCheckBox(
            self.parent_dialog.translate_text("Inclure les métadonnées"))
        self.include_metadata_check.setChecked(True)

        self.compress_images_check = AnimatedCheckBox(
            self.parent_dialog.translate_text("Compresser les images"))
        self.compress_images_check.setChecked(True)

        self.config_layout.addWidget(mode_label)
        self.config_layout.addWidget(self.word_mode_combo)
        self.config_layout.addWidget(quality_label)
        self.config_layout.addWidget(self.image_quality_combo)
        self.config_layout.addWidget(self.include_metadata_check)
        self.config_layout.addWidget(self.compress_images_check)
    
    def create_pdf_merge_config(self):
        """Create the configuration form for PDF merge"""
        order_label = QLabel(self.parent_dialog.translate_text("Ordre de fusion:"))
        self.merge_order_combo = QComboBox()
        self.merge_order_combo.addItems([
            self.parent_dialog.translate_text("Ordre actuel (liste principale)"),
            self.parent_dialog.translate_text("Alphabétique (A→Z)"),
            self.parent_dialog.translate_text("Alphabétique (Z→A)"),
            self.parent_dialog.translate_text("Numérique (1→9)"),
            self.parent_dialog.translate_text("Numérique (9→1)"),
            self.parent_dialog.translate_text("Date (ancien→nouveau)"),
            self.parent_dialog.translate_text("Date (nouveau→ancien)"),
            self.parent_dialog.translate_text("Manuel (glisser-déposer)"),
        ])
        name_label = QLabel(self.parent_dialog.translate_text("Template de nom de fichier:"))
        self.name_template_input = QLineEdit()
        self.name_template_input.setText("fusion_{date}_{heure}")
        self.config_layout.addWidget(order_label)
        self.config_layout.addWidget(self.merge_order_combo)
        self.config_layout.addWidget(name_label)
        self.config_layout.addWidget(self.name_template_input)

    def create_optimization_config(self):
        """Create the configuration form for office optimization presets"""
        tr = self.parent_dialog.translate_text

        self.config_layout.addWidget(QLabel(tr("Mode d'optimisation")))
        self.optim_mode_combo = QComboBox()
        self.optim_mode_combo.addItems([
            tr("Compression  —  réduit la taille du fichier"),
            tr("Nettoyage  —  supprime uniquement les métadonnées"),
            tr("Compression + Nettoyage  —  recommandé"),
        ])
        self.optim_mode_combo.setCurrentIndex(2)
        self.config_layout.addWidget(self.optim_mode_combo)

        self.config_layout.addWidget(QLabel(tr("Niveau de compression")))
        self.optim_quality_combo = QComboBox()
        self.optim_quality_combo.addItems([
            "I  —  " + tr("Haute qualité  (gain modéré)"),
            "II  —  " + tr("Équilibré  (recommandé)"),
            "III  —  " + tr("Maximum  (qualité réduite)"),
        ])
        self.optim_quality_combo.setCurrentIndex(1)
        self.config_layout.addWidget(self.optim_quality_combo)

        self.config_layout.addWidget(QLabel(tr("Options")))
        from PySide6.QtWidgets import QCheckBox as _QCB
        self.optim_metadata_check = _QCB(tr("Supprimer les métadonnées personnelles"))
        self.optim_metadata_check.setChecked(True)
        self.optim_images_check = _QCB(tr("Recompresser les images intégrées"))
        self.optim_images_check.setChecked(True)
        self.optim_backup_check = _QCB(tr("Garder une copie des originaux"))
        self.optim_backup_check.setChecked(True)
        self.config_layout.addWidget(self.optim_metadata_check)
        self.config_layout.addWidget(self.optim_images_check)
        self.config_layout.addWidget(self.optim_backup_check)

    def create_template(self):
        """Create the new template"""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(
                self,
                self.parent_dialog.translate_text("Erreur"),
                self.parent_dialog.translate_text("Veuillez entrer un nom pour le template.")
            )
            return
        
        template_type = self.type_combo.currentText()
        
        config_data = {}
        
        if template_type == self.parent_dialog.translate_text("Conversion PDF→Word"):
            config_data = {
                'mode': self.mode_combo.currentText()
            }
        elif template_type == self.parent_dialog.translate_text("Conversion Word→PDF"):
            config_data = {
                'mode':             self.word_mode_combo.currentText(),
                'quality':          self.image_quality_combo.currentText(),
                'include_metadata': self.include_metadata_check.isChecked(),
                'compress_images':  self.compress_images_check.isChecked(),
            }
        elif template_type == self.parent_dialog.translate_text("Conversion Images→PDF"):
            config_data = {
                'separate': self.separate_images_check.isChecked(),
            }
        elif template_type == self.parent_dialog.translate_text("Fusion PDF"):
            config_data = {
                'merge_order':  self.merge_order_combo.currentText(),
                'name_template': self.name_template_input.text(),
            }
        elif template_type == self.parent_dialog.translate_text("Fusion Word"):
            config_data = {
                'merge_order':  self.word_merge_order_combo.currentText(),
                'name_template': self.word_merge_name_input.text(),
            }
        elif template_type == self.parent_dialog.translate_text("Division PDF"):
            config_data = {
                'split_method':   self.split_method_combo.currentText(),
                'pages_per_file': self.pages_per_file_spin.value(),
            }
        elif template_type == self.parent_dialog.translate_text("Protection PDF"):
            config_data = {
                'mode':               self.protection_level_combo.currentText(),
                'allow_printing':     self.allow_printing_check.isChecked(),
                'allow_copying':      self.allow_copying_check.isChecked(),
                'allow_modifications': self.allow_modifications_check.isChecked(),
            }
        elif template_type == self.parent_dialog.translate_text("Compression"):
            config_data = {
                'format':            self.compression_format_combo.currentText(),
                'compression_level': self.compression_level_combo.currentText(),
                'encrypt':           self.encrypt_check.isChecked(),
                'delete_originals':  self.delete_originals_check.isChecked(),
                'split_archive':     self.split_check.isChecked(),
                'split_size':        self.split_size_spin.value() if self.split_check.isChecked() else 0,
            }
        elif template_type == self.parent_dialog.translate_text("Optimisation de fichiers"):
            _mode_map = {
                self.parent_dialog.translate_text("Compression  —  réduit la taille du fichier"): 0,
                self.parent_dialog.translate_text("Nettoyage  —  supprime uniquement les métadonnées"): 1,
                self.parent_dialog.translate_text("Compression + Nettoyage  —  recommandé"): 2,
            }
            config_data = {
                'optimization_type': _mode_map.get(self.optim_mode_combo.currentText(), 2),
                'quality_level':     self.optim_quality_combo.currentIndex(),
                'remove_metadata':   self.optim_metadata_check.isChecked(),
                'compress_images':   self.optim_images_check.isChecked(),
                'keep_backup':       self.optim_backup_check.isChecked(),
            }
        
        if self.memorize_check.isChecked() and hasattr(self.parent_app, 'config'):
            self.parent_app.config['last_template_creation_params'] = {
                'memorize': True, 'type': template_type,
            }
            try:
                self.parent_app.config_manager.save_config(self.parent_app.config)
            except Exception:
                pass
        elif hasattr(self.parent_app, 'config'):
            self.parent_app.config.pop('last_template_creation_params', None)
            try:
                self.parent_app.config_manager.save_config(self.parent_app.config)
            except Exception:
                pass

        if self.set_as_default_check.isChecked():
            config_data['is_default'] = True

        self.template_manager.db_manager.save_template(name, template_type, config_data)
        self.template_manager.load_templates()

        if self.set_as_default_check.isChecked():
            new_id = None
            for tid, tpl in self.template_manager.current_templates.items():
                if (tpl['name'] == name and
                        TemplateManager.normalize_type(tpl['type']) ==
                        TemplateManager.normalize_type(template_type)):
                    new_id = tid
                    break
            if new_id is not None:
                self.template_manager.set_default_template(new_id, template_type)

        QMessageBox.information(
            self,
            self.parent_dialog.translate_text("Succès"),
            self.parent_dialog.translate_text("template_created").format(name)
        )

        _cfg = getattr(self.parent_app, 'config', {})
        ach = getattr(self.parent_app, 'achievement_system', None) if _cfg.get("achievements_enabled", True) else None
        if ach:
            try: ach.record_template_created(template_type)
            except Exception: pass

        self.accept()

class TemplateEditorDialog(QDialog):
    """Dialog for editing an existing template"""
    
    def __init__(self, template, parent_dialog):
        super().__init__(parent_dialog)
        self.template = template
        self.parent_dialog = parent_dialog
        
        self.setWindowTitle(self.parent_dialog.translate_text("Modifier le template"))
        self.setMinimumSize(500, 400)
        
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        info_group = QGroupBox(self.parent_dialog.translate_text("Informations"))
        info_layout = QFormLayout(info_group)
        
        self.name_input = QLineEdit(self.template['name'])
        info_layout.addRow(self.parent_dialog.translate_text("Nom:"), self.name_input)
        
        type_label = QLabel(self.template['type'])
        info_layout.addRow(self.parent_dialog.translate_text("Type:"), type_label)
        
        layout.addWidget(info_group)
        
        config_group = QGroupBox(self.parent_dialog.translate_text("Configuration"))
        config_layout = QVBoxLayout(config_group)
        
        config_text = self.parent_dialog.format_config_for_display(
            self.template['config'], 
            self.template['type']
        )
        config_label = QLabel(config_text)
        config_label.setWordWrap(True)
        
        config_layout.addWidget(config_label)
        
        note_label = QLabel(
            self.parent_dialog.translate_text("Note: L'édition avancée de la configuration sera disponible dans une future version.")
        )
        note_label.setStyleSheet("color: #666; font-style: italic;")
        config_layout.addWidget(note_label)
        
        layout.addWidget(config_group)
        layout.addStretch()
        
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 " + self.parent_dialog.translate_text("Sauvegarder les modifications"))
        save_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton(self.parent_dialog.translate_text("Annuler"))
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)

    def get_updated_config(self):
        """Return the updated configuration"""
        # For now, the only modification is: the name
        return self.template['config']