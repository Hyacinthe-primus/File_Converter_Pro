"""
TermsAndPrivacyDialog - File Converter Pro

Modal dialog for legal acceptance (Terms of Use / Privacy Policy).
Extracted from dialogs.py for better code organization.

Author: Hyacinthe
Version: 1.0
"""

import sys
import os
import re

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGroupBox, QTextBrowser, QTabWidget, QWidget, QMessageBox
)
from PySide6.QtGui import QIcon, QDesktopServices
import sys as _sys, os as _os
_PKG_DIR  = _os.path.dirname(_os.path.abspath(__file__))
_ROOT_DIR = _os.path.dirname(_PKG_DIR)
if _ROOT_DIR not in _sys.path:
    _sys.path.insert(0, _ROOT_DIR)

from widgets import AnimatedCheckBox
from translations import TranslationManager

def _make_tm(language):
    tm = TranslationManager()
    tm.set_language(language)
    return tm

class TermsAndPrivacyDialog(QDialog):
    def __init__(self, parent=None, language="fr", dark_mode=False):
        super().__init__(parent)
        self.language = language
        self.dark_mode = dark_mode
        self._tm = _make_tm(language)
        self.setWindowTitle(self.translate_text("Conditions d'utilisation et Politique de confidentialité"))
        self.setModal(True)
        self.setMinimumSize(800, 650)
        self.setWindowIcon(QIcon(self.get_icon_path()))
        self.closed_by_cross = False

        if self.dark_mode:
            self.setStyleSheet("""
                QDialog {
                    background-color: #1e1e1e;
                    color: #e0e0e0;
                }
                QWidget {
                    background-color: #1e1e1e;
                    color: #e0e0e0;
                }
                QLabel {
                    background-color: transparent;
                    color: #e0e0e0;
                }
            """)
        else:
            self.setStyleSheet("""
                QDialog {
                    background-color: #f5f6fa;
                    color: #212529;
                }
                QWidget {
                    background-color: #f5f6fa;
                    color: #212529;
                }
                QLabel {
                    background-color: transparent;
                    color: #212529;
                }
            """)

        self.setup_ui()

    def closeEvent(self, event):
        """Intercept closing via the X button to distinguish it from the Decline button"""
        self.closed_by_cross = True
        super().closeEvent(event)

    def get_icon_path(self):
        """Find icon.ico robustly (dev + PyInstaller)"""
        icon_name = "icon.ico"
        path = os.path.join(_ROOT_DIR, icon_name)
        if os.path.exists(path):
            return path
        path = os.path.join(os.getcwd(), icon_name)
        if os.path.exists(path):
            return path
        if getattr(sys, 'frozen', False):
            path = os.path.join(sys._MEIPASS, icon_name)
            if os.path.exists(path):
                return path
        return icon_name

    def get_legal_files_path(self):
        """Find the legal folder robustly (dev + PyInstaller)"""
        legal_dir = "legal"

        # PyInstaller mode
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
            path = os.path.join(base_path, legal_dir)
            if os.path.exists(path):
                return path

        # Dev mode - project root
        path = os.path.join(_ROOT_DIR, legal_dir)
        if os.path.exists(path):
            return path

        # Dev mode - current folder
        path = os.path.join(os.getcwd(), legal_dir)
        if os.path.exists(path):
            return path

        # Create dir and default HTML files
        os.makedirs(legal_dir, exist_ok=True)
        self.create_default_legal_files(legal_dir)
        return legal_dir

    def create_default_legal_files(self, legal_dir):
        """Create default HTML files if the folder is empty"""
        default_content_fr = """
        <h3 style="color: #e74c3c;">⚠️ Fichier non trouvé</h3>
        <p>Les fichiers complets doivent être placés dans le dossier 'legal'.</p>
        <p>Contactez le développeur pour obtenir les versions complètes.</p>
        """
        default_content_en = """
        <h3 style="color: #e74c3c;">⚠️ File not found</h3>
        <p>Complete files must be placed in the 'legal' folder.</p>
        <p>Contact the developer to obtain full versions.</p>
        """

        with open(os.path.join(legal_dir, "privacy_policy_fr.html"), 'w', encoding='utf-8') as f:
            f.write(default_content_fr)
        with open(os.path.join(legal_dir, "privacy_policy_en.html"), 'w', encoding='utf-8') as f:
            f.write(default_content_en)
        with open(os.path.join(legal_dir, "terms_conditions_fr.html"), 'w', encoding='utf-8') as f:
            f.write(default_content_fr.replace("Politique de confidentialité", "Conditions d'utilisation"))
        with open(os.path.join(legal_dir, "terms_conditions_en.html"), 'w', encoding='utf-8') as f:
            f.write(default_content_en.replace("Privacy Policy", "Terms of Use"))

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 20)
        layout.setSpacing(12)

        self.tab_widget = QTabWidget()
        if self.dark_mode:
            self.tab_widget.setStyleSheet("""
                QTabWidget::pane {
                    border: 1px solid #3a3a3a;
                    border-radius: 6px;
                    background: #2d2d2d;
                    margin-top: -5px;
                }
                QTabBar::tab {
                    background: #3a3a3a;
                    color: #e0e0e0;
                    padding: 10px 18px;
                    margin-right: 2px;
                    border-top-left-radius: 6px;
                    border-top-right-radius: 6px;
                    font-size: 11px;
                    font-weight: 500;
                }
                QTabBar::tab:selected {
                    background: #3498db;
                    color: #ffffff;
                }
                QTabBar::tab:hover:!selected {
                    background: #4a4a4a;
                }
            """)
        else:
            self.tab_widget.setStyleSheet("""
                QTabWidget::pane {
                    border: 1px solid #dee2e6;
                    border-radius: 6px;
                    background: #ffffff;
                    margin-top: -5px;
                }
                QTabBar::tab {
                    background: #e9ecef;
                    color: #495057;
                    padding: 10px 18px;
                    margin-right: 2px;
                    border-top-left-radius: 6px;
                    border-top-right-radius: 6px;
                    font-size: 11px;
                    font-weight: 500;
                }
                QTabBar::tab:selected {
                    background: #3498db;
                    color: #ffffff;
                }
                QTabBar::tab:hover:!selected {
                    background: #ced4da;
                }
            """)

        self.terms_tab = QWidget()
        self.terms_tab.setStyleSheet(f"background-color: {'#2d2d2d' if self.dark_mode else '#ffffff'};")
        terms_layout = QVBoxLayout(self.terms_tab)
        terms_layout.setContentsMargins(15, 12, 15, 15)

        title_color = "#ffffff" if self.dark_mode else "#212529"
        terms_title = QLabel(f"<h2 style='color: {title_color}; margin: 0 0 8px 0;'>{self.translate_text('Conditions d\'utilisation')}</h2>")
        terms_title.setStyleSheet(f"background-color: transparent; color: {title_color};")
        terms_layout.addWidget(terms_title)

        self.terms_text = QTextBrowser()
        self.terms_text.setReadOnly(True)
        self.terms_text.setOpenExternalLinks(False)
        self.terms_text.setOpenLinks(False)
        self.terms_text.setHtml(self.get_terms_content())
        if self.dark_mode:
            self.terms_text.setStyleSheet("""
                QTextBrowser {
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                    border: 1px solid #3a3a3a;
                    border-radius: 6px;
                    padding: 15px;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    font-size: 11px;
                }
                QScrollBar:vertical {
                    background: transparent;
                    width: 6px;
                    margin: 4px 2px 4px 0px;
                    border: none;
                }
                QScrollBar::handle:vertical {
                    background: #555d6b;
                    border-radius: 3px;
                    min-height: 32px;
                }
                QScrollBar::handle:vertical:hover {
                    background: #7a8699;
                }
                QScrollBar::handle:vertical:pressed {
                    background: #4dabf7;
                }
                QScrollBar::add-line:vertical,
                QScrollBar::sub-line:vertical {
                    height: 0px;
                    border: none;
                    background: none;
                }
                QScrollBar::add-page:vertical,
                QScrollBar::sub-page:vertical {
                    background: transparent;
                }
            """)
        else:
            self.terms_text.setStyleSheet("""
                QTextBrowser {
                    background-color: #ffffff;
                    color: #212529;
                    border: 1px solid #dee2e6;
                    border-radius: 6px;
                    padding: 15px;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    font-size: 11px;
                }
                QScrollBar:vertical {
                    background: transparent;
                    width: 6px;
                    margin: 4px 2px 4px 0px;
                    border: none;
                }
                QScrollBar::handle:vertical {
                    background: #c8cdd4;
                    border-radius: 3px;
                    min-height: 32px;
                }
                QScrollBar::handle:vertical:hover {
                    background: #9aa0ab;
                }
                QScrollBar::handle:vertical:pressed {
                    background: #3498db;
                }
                QScrollBar::add-line:vertical,
                QScrollBar::sub-line:vertical {
                    height: 0px;
                    border: none;
                    background: none;
                }
                QScrollBar::add-page:vertical,
                QScrollBar::sub-page:vertical {
                    background: transparent;
                }
            """)
        self.terms_text.document().setDefaultStyleSheet(self.get_html_theme_css())
        terms_layout.addWidget(self.terms_text)

        self.privacy_tab = QWidget()
        self.privacy_tab.setStyleSheet(f"background-color: {'#2d2d2d' if self.dark_mode else '#ffffff'};")
        privacy_layout = QVBoxLayout(self.privacy_tab)
        privacy_layout.setContentsMargins(15, 12, 15, 15)

        privacy_title = QLabel(f"<h2 style='color: {title_color}; margin: 0 0 8px 0;'>{self.translate_text('Politique de confidentialité')}</h2>")
        privacy_title.setStyleSheet(f"background-color: transparent; color: {title_color};")
        privacy_layout.addWidget(privacy_title)

        self.privacy_text = QTextBrowser()
        self.privacy_text.setReadOnly(True)
        self.privacy_text.setOpenExternalLinks(False)
        self.privacy_text.setOpenLinks(False)
        self.privacy_text.setHtml(self.get_privacy_content())
        if self.dark_mode:
            self.privacy_text.setStyleSheet("""
                QTextBrowser {
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                    border: 1px solid #3a3a3a;
                    border-radius: 6px;
                    padding: 15px;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    font-size: 11px;
                }
                QScrollBar:vertical {
                    background: transparent;
                    width: 6px;
                    margin: 4px 2px 4px 0px;
                    border: none;
                }
                QScrollBar::handle:vertical {
                    background: #555d6b;
                    border-radius: 3px;
                    min-height: 32px;
                }
                QScrollBar::handle:vertical:hover {
                    background: #7a8699;
                }
                QScrollBar::handle:vertical:pressed {
                    background: #4dabf7;
                }
                QScrollBar::add-line:vertical,
                QScrollBar::sub-line:vertical {
                    height: 0px;
                    border: none;
                    background: none;
                }
                QScrollBar::add-page:vertical,
                QScrollBar::sub-page:vertical {
                    background: transparent;
                }
            """)
        else:
            self.privacy_text.setStyleSheet("""
                QTextBrowser {
                    background-color: #ffffff;
                    color: #212529;
                    border: 1px solid #dee2e6;
                    border-radius: 6px;
                    padding: 15px;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    font-size: 11px;
                }
                QScrollBar:vertical {
                    background: transparent;
                    width: 6px;
                    margin: 4px 2px 4px 0px;
                    border: none;
                }
                QScrollBar::handle:vertical {
                    background: #c8cdd4;
                    border-radius: 3px;
                    min-height: 32px;
                }
                QScrollBar::handle:vertical:hover {
                    background: #9aa0ab;
                }
                QScrollBar::handle:vertical:pressed {
                    background: #3498db;
                }
                QScrollBar::add-line:vertical,
                QScrollBar::sub-line:vertical {
                    height: 0px;
                    border: none;
                    background: none;
                }
                QScrollBar::add-page:vertical,
                QScrollBar::sub-page:vertical {
                    background: transparent;
                }
            """)
        self.privacy_text.document().setDefaultStyleSheet(self.get_html_theme_css())
        privacy_layout.addWidget(self.privacy_text)

        self.tab_widget.addTab(self.terms_tab, self.translate_text("Conditions d'utilisation"))
        self.tab_widget.addTab(self.privacy_tab, self.translate_text("Politique de confidentialité"))

        layout.addWidget(self.tab_widget, 1)

        self.terms_text.anchorClicked.connect(self.handle_terms_link_click)
        self.privacy_text.anchorClicked.connect(self.handle_privacy_link_click)

        contact_group = QGroupBox(self.translate_text("Contact"))
        if self.dark_mode:
            contact_group.setStyleSheet("""
                QGroupBox {
                    font-weight: bold;
                    color: #808080;
                    border: 1px solid #3a3a3a;
                    border-radius: 6px;
                    margin-top: 12px;
                    padding-top: 8px;
                    background-color: #252525;
                    font-size: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px;
                    color: #5dade2;
                    background-color: transparent;
                    font-size: 10px;
                }
            """)
        else:
            contact_group.setStyleSheet("""
                QGroupBox {
                    font-weight: bold;
                    color: #6c757d;
                    border: 1px solid #dee2e6;
                    border-radius: 6px;
                    margin-top: 12px;
                    padding-top: 8px;
                    background-color: #f8f9fa;
                    font-size: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px;
                    color: #3498db;
                    background-color: transparent;
                    font-size: 10px;
                }
            """)
        contact_layout = QVBoxLayout(contact_group)
        contact_layout.setContentsMargins(12, 8, 12, 8)
        contact_layout.setSpacing(6)

        contact_links_html = self.get_compact_contact_links_html()
        contact_links = QTextBrowser()
        contact_links.setReadOnly(True)
        contact_links.setOpenExternalLinks(True)
        contact_links.setHtml(contact_links_html)
        contact_links.setMaximumHeight(70)
        if self.dark_mode:
            contact_links.setStyleSheet("""
                QTextBrowser {
                    background-color: #202020;
                    border: 1px solid #333333;
                    border-radius: 5px;
                    padding: 6px 8px;
                    font-size: 9px;
                    color: #b0b0b0;
                    margin: 0;
                }
                QScrollBar:vertical {
                    background: #202020;
                    width: 8px;
                }
                QScrollBar::handle:vertical {
                    background: #404040;
                    border-radius: 4px;
                }
            """)
            contact_links.document().setDefaultStyleSheet("""
                body { color: #b0b0b0; background-color: #202020; font-size: 9px; margin: 0; padding: 0; }
                a { color: #5dade2; text-decoration: none; font-weight: 500; }
                a:hover { color: #3498db; text-decoration: underline; }
                ul { margin: 2px 0; padding-left: 15px; }
                li { margin: 1px 0; }
                p { margin: 2px 0; line-height: 1.4; }
                strong { color: #5dade2; font-weight: 600; }
                .warning { color: #e74c3c !important; font-weight: 600; }
            """)
        else:
            contact_links.setStyleSheet("""
                QTextBrowser {
                    background-color: #ffffff;
                    border: 1px solid #dee2e6;
                    border-radius: 5px;
                    padding: 6px 8px;
                    font-size: 9px;
                    color: #212529;
                    margin: 0;
                }
                QScrollBar:vertical {
                    background: #f8f9fa;
                    width: 8px;
                }
                QScrollBar::handle:vertical {
                    background: #ced4da;
                    border-radius: 4px;
                }
            """)
            contact_links.document().setDefaultStyleSheet("""
                body { color: #212529; background-color: #ffffff; font-size: 9px; margin: 0; padding: 0; }
                a { color: #1c7ed6; text-decoration: none; font-weight: 600; }
                a:hover { color: #1864ab; text-decoration: underline; }
                ul { margin: 2px 0; padding-left: 15px; }
                li { margin: 1px 0; }
                p { margin: 2px 0; line-height: 1.4; color: #212529; }
                strong { color: #212529; font-weight: 700; }
                .warning { color: #dc3545 !important; font-weight: 600; }
            """)
        contact_layout.addWidget(contact_links)

        layout.addWidget(contact_group)

        checkbox_layout = QHBoxLayout()
        checkbox_layout.setSpacing(15)

        self.terms_checkbox = AnimatedCheckBox(self.translate_text("J'accepte les conditions d'utilisation"))
        self.terms_checkbox.setStyleSheet(self.get_checkbox_style())

        self.privacy_checkbox = AnimatedCheckBox(self.translate_text("J'accepte la politique de confidentialité"))
        self.privacy_checkbox.setStyleSheet(self.get_checkbox_style())

        checkbox_layout.addWidget(self.terms_checkbox)
        checkbox_layout.addWidget(self.privacy_checkbox)
        layout.addLayout(checkbox_layout)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)

        self.decline_button = QPushButton(self.translate_text("Refuser"))
        self.accept_button = QPushButton(self.translate_text("Accepter"))
        self.accept_button.setEnabled(False)

        self.accept_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #28a745;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: #218838;
            }}
            QPushButton:pressed {{
                background-color: #1e7e34;
            }}
            QPushButton:disabled {{
                background-color: {'#4a4a4a' if self.dark_mode else '#d1d5db'};
                color: {'#808080' if self.dark_mode else '#9ca3af'};
            }}
        """)

        self.decline_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #bd2130;
            }
        """)

        button_layout.addStretch()
        button_layout.addWidget(self.decline_button)
        button_layout.addWidget(self.accept_button)

        layout.addLayout(button_layout)

        self.terms_checkbox.stateChanged.connect(self.update_accept_button)
        self.privacy_checkbox.stateChanged.connect(self.update_accept_button)
        self.accept_button.clicked.connect(self.accept)
        self.decline_button.clicked.connect(self.reject)

    def handle_terms_link_click(self, url):
        """Handle link clicks in the Terms of Use tab"""
        url_str = url.toString()
        if "privacy_policy" in url_str or "politique_confidentialite" in url_str:
            self.tab_widget.setCurrentIndex(1)
        else:
            if url_str.startswith("mailto:") or url_str.startswith("http"):
                QDesktopServices.openUrl(url)

    def handle_privacy_link_click(self, url):
        """Handle link clicks in the Privacy Policy tab"""
        url_str = url.toString()
        if "terms_conditions" in url_str or "conditions_utilisation" in url_str:
            self.tab_widget.setCurrentIndex(0)
        else:
            if url_str.startswith("mailto:") or url_str.startswith("http"):
                QDesktopServices.openUrl(url)

    def get_html_theme_css(self):
        """CSS to style HTML content according to the current theme"""
        if self.dark_mode:
            return """
                body {
                    background-color: #2d2d2d !important;
                    color: #e0e0e0 !important;
                    margin: 0;
                    padding: 0;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    font-size: 11px;
                    line-height: 1.5;
                }
                h1, h2, h3, h4, h5, h6 {
                    color: #ffffff !important;
                    border-color: #3498db !important;
                    margin-top: 15px;
                    margin-bottom: 10px;
                }
                h1 { font-size: 20px; }
                h2 { font-size: 16px; }
                h3 { font-size: 14px; }
                h4 { font-size: 13px; }
                p, li, td, th, div, span {
                    color: #e0e0e0 !important;
                    margin: 8px 0;
                }
                a {
                    color: #5dade2 !important;
                    text-decoration: none;
                }
                a:hover {
                    color: #3498db !important;
                    text-decoration: underline;
                }
                strong, b {
                    color: #ffffff !important;
                    font-weight: 600;
                }
                em, i {
                    color: #b0b0b0 !important;
                }
                hr {
                    border: 0;
                    border-top: 1px solid #3a3a3a !important;
                    margin: 15px 0;
                }
                ul, ol {
                    color: #e0e0e0 !important;
                    padding-left: 20px;
                    margin: 10px 0;
                }
                li { margin-bottom: 5px; }
                * { background-color: transparent !important; }
                body, html { background-color: #2d2d2d !important; }
                .highlight {
                    background-color: #3a3a2d !important;
                    padding: 2px 4px;
                    border-radius: 3px;
                }
                .warning {
                    color: #e74c3c !important;
                    font-weight: bold;
                }
            """
        else:
            return """
                body {
                    background-color: #ffffff !important;
                    color: #212529 !important;
                    margin: 0;
                    padding: 0;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    font-size: 11px;
                    line-height: 1.5;
                }
                h1, h2, h3, h4, h5, h6 {
                    color: #1a1a2e !important;
                    border-color: #3498db !important;
                    margin-top: 15px;
                    margin-bottom: 10px;
                }
                h1 { font-size: 20px; }
                h2 { font-size: 16px; }
                h3 { font-size: 14px; }
                h4 { font-size: 13px; }
                p, li, td, th, div, span {
                    color: #212529 !important;
                    margin: 8px 0;
                }
                a {
                    color: #3498db !important;
                    text-decoration: none;
                }
                a:hover {
                    color: #1c7ed6 !important;
                    text-decoration: underline;
                }
                strong, b {
                    color: #1a1a2e !important;
                    font-weight: 600;
                }
                em, i { color: #6c757d !important; }
                hr {
                    border: 0;
                    border-top: 1px solid #dee2e6 !important;
                    margin: 15px 0;
                }
                ul, ol {
                    color: #212529 !important;
                    padding-left: 20px;
                    margin: 10px 0;
                }
                li { margin-bottom: 5px; }
                * { background-color: transparent !important; }
                body, html { background-color: #ffffff !important; }
                .highlight {
                    background-color: #fff3cd !important;
                    padding: 2px 4px;
                    border-radius: 3px;
                }
                .warning {
                    color: #dc3545 !important;
                    font-weight: bold;
                }
            """

    def get_html_dark_theme_css(self):
        return self.get_html_theme_css()

    def get_compact_contact_links_html(self):
        """Generate ultra-compact HTML for contact links"""
        if self.language == "fr":
            return """
            <p style="margin:2px 0;font-size:9px;">
                <strong>Développeur :</strong>
                <a href="mailto:hyacintheatho91@gmail.com" style="font-weight:500;color:#3498db;">hyacintheatho91@gmail.com</a>
            </p>
            <p style="margin:2px 0;font-size:9px;">
                <a href="https://github.com/Hyacinthe-primus" style="margin-right:8px;color:#7c5cbf;">💻 GitHub</a>
                <a href="https://www.instagram.com/___hyacinthe_" style="margin-right:8px;color:#7c5cbf;">📸 Instagram</a>
                <a href="https://www.reddit.com/user/___Hyacinthe_/" style="color:#7c5cbf;">🔴 Reddit</a>
            </p>
            <p style="margin:2px 0;font-size:9px;">
                <a href="mailto:hyacintheatho91@gmail.com?subject=Report%20Bug%20from%20File%20Converter%20Pro"
                   style="color:#e74c3c;font-weight:600;">
                   🐛 Signaler un bug
                </a>
            </p>
            """
        else:
            return """
            <p style="margin:2px 0;font-size:9px;">
                <strong>Developer:</strong>
                <a href="mailto:hyacintheatho91@gmail.com" style="font-weight:500;">hyacintheatho91@gmail.com</a>
            </p>
            <p style="margin:2px 0;font-size:9px;">
                <a href="https://github.com/Hyacinthe-primus" style="margin-right:8px;">💻 GitHub</a>
                <a href="https://www.instagram.com/___hyacinthe_" style="margin-right:8px;">📸 Instagram</a>
                <a href="https://www.reddit.com/user/___Hyacinthe_/">🔴 Reddit</a>
            </p>
            <p style="margin:2px 0;font-size:9px;">
                <a href="mailto:hyacintheatho91@gmail.com?subject=Report%20Bug%20from%20File%20Converter%20Pro"
                   style="color:#e74c3c;font-weight:600;">
                   🐛 Report a bug
                </a>
            </p>
            """

    def get_checkbox_style(self):
        """Compact style for checkboxes"""
        if self.dark_mode:
            return """
                QCheckBox {
                    color: #e0e0e0;
                    font-size: 11px;
                    spacing: 8px;
                    background-color: transparent;
                }
                QCheckBox::indicator {
                    width: 18px;
                    height: 18px;
                    border: 2px solid #3a3a3a;
                    border-radius: 4px;
                    background-color: #2d2d2d;
                }
                QCheckBox::indicator:checked {
                    background-color: #3498db;
                    border-color: #3498db;
                }
                QCheckBox::indicator:hover {
                    border-color: #5dade2;
                }
            """
        else:
            return """
                QCheckBox {
                    color: #212529;
                    font-size: 11px;
                    spacing: 8px;
                    background-color: transparent;
                }
                QCheckBox::indicator {
                    width: 18px;
                    height: 18px;
                    border: 2px solid #adb5bd;
                    border-radius: 4px;
                    background-color: #ffffff;
                }
                QCheckBox::indicator:checked {
                    background-color: #3498db;
                    border-color: #3498db;
                }
                QCheckBox::indicator:hover {
                    border-color: #3498db;
                }
            """

    def translate_text(self, text):
        return self._tm.translate_text(text)

    def _apply_theme_to_html(self, content: str) -> str:
        """
        Replace or inject the <style> block in an HTML file with the
        theme-appropriate CSS, so the file's own hardcoded colours are never used.
        """
        theme_css = self.get_html_theme_css()
        new_style = f"<style>\n{theme_css}\n</style>"

        if re.search(r'<style[\s>]', content, re.IGNORECASE):
            content = re.sub(
                r'<style[^>]*>.*?</style>',
                new_style,
                content,
                flags=re.IGNORECASE | re.DOTALL
            )
        elif '<head>' in content.lower():
            content = re.sub(
                r'(</head>)',
                f'{new_style}\n\\1',
                content,
                flags=re.IGNORECASE
            )
        else:
            content = new_style + "\n" + content
        return content

    def _get_legal_lang_code(self, prefix: str) -> str:
        """
        Returns the best available language code for a given legal file prefix.
        prefix is either 'terms_conditions' or 'privacy_policy'.
        Priority: exact match (e.g. 'it') -> 'en' fallback -> 'fr' fallback
        Each file type is checked independently, so having terms_conditions_it.html
        does not imply privacy_policy_it.html exists.
        """
        legal_path = self.get_legal_files_path()
        if os.path.exists(os.path.join(legal_path, f"{prefix}_{self.language}.html")):
            return self.language
        if os.path.exists(os.path.join(legal_path, f"{prefix}_en.html")):
            return "en"
        return "fr"

    def get_terms_content(self):
        """Load terms of use from an HTML file"""
        legal_path = self.get_legal_files_path()
        file_path = os.path.join(legal_path, f"terms_conditions_{self._get_legal_lang_code('terms_conditions')}.html")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return self._apply_theme_to_html(content)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return self.get_default_terms_content()

    def get_default_terms_content(self):
        if self.language == "fr":
            return """
            <h3 style="color: #e74c3c;">⚠️ Fichier non trouvé</h3>
            <p>Le fichier terms_conditions_fr.html est manquant dans le dossier 'legal'.</p>
            <p>Veuillez contacter le développeur ou réinstaller l'application.</p>
            """
        else:
            return """
            <h3 style="color: #e74c3c;">⚠️ File not found</h3>
            <p>The file terms_conditions_en.html is missing from the 'legal' folder.</p>
            <p>Please contact the developer or reinstall the application.</p>
            """

    def get_privacy_content(self):
        """Load privacy policy from an HTML file"""
        legal_path = self.get_legal_files_path()
        file_path = os.path.join(legal_path, f"privacy_policy_{self._get_legal_lang_code('privacy_policy')}.html")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return self._apply_theme_to_html(content)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return self.get_default_privacy_content()

    def get_default_privacy_content(self):
        if self.language == "fr":
            return """
            <h3 style="color: #e74c3c;">⚠️ Fichier non trouvé</h3>
            <p>Le fichier privacy_policy_fr.html est manquant dans le dossier 'legal'.</p>
            <p>Veuillez contacter le développeur ou réinstaller l'application.</p>
            """
        else:
            return """
            <h3 style="color: #e74c3c;">⚠️ File not found</h3>
            <p>The file privacy_policy_en.html is missing from the 'legal' folder.</p>
            <p>Please contact the developer or reinstall the application.</p>
            """

    def update_accept_button(self):
        self.accept_button.setEnabled(
            self.terms_checkbox.isChecked() and
            self.privacy_checkbox.isChecked()
        )

    def accept(self):
        if self.terms_checkbox.isChecked() and self.privacy_checkbox.isChecked():
            super().accept()

    def reject(self):
        """Handle click on Decline"""
        if hasattr(self, 'from_settings') and self.from_settings:
            super().reject()
        else:
            QMessageBox.information(
                self,
                self.translate_text("Conditions requises"),
                self.translate_text("Vous devez accepter les conditions d'utilisation et la politique de confidentialité pour utiliser cette application.")
            )
            super().reject()
