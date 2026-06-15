"""
TermsAndPrivacyDialog

Modal dialog for legal acceptance (Terms of Use / Privacy Policy).
Extracted from dialogs.py for better code organization.

"""

import sys
import os
import re

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGroupBox, QTextBrowser, QTabWidget, QWidget, QMessageBox
)
from PySide6.QtGui import QIcon, QDesktopServices

from qss_helpers import _load_qss, _apply_dialog_btn
from widgets import AnimatedCheckBox

from utils import make_tm
from utils.translation_mixin import TranslationMixin


class TermsAndPrivacyDialog(TranslationMixin, QDialog):
    def __init__(self, parent=None, language="fr", dark_mode=False):
        super().__init__(parent)
        self.language = language
        self.dark_mode = dark_mode
        self._tm = make_tm(language)
        self.setWindowTitle(self.translate_text("Conditions d'utilisation et Politique de confidentialité"))
        self.setModal(True)
        self.setMinimumSize(800, 650)
        self.setWindowIcon(QIcon(self.get_icon_path()))
        self.closed_by_cross = False

        self.setStyleSheet(_load_qss("terms.qss", "dark" if self.dark_mode else "light"))

        self.setup_ui()

    def closeEvent(self, event):
        """Intercept closing via the X button to distinguish it from the Decline button"""
        self.closed_by_cross = True
        super().closeEvent(event)

    def get_icon_path(self):
        """Find icon.ico robustly (dev + PyInstaller)"""
        from utils import get_icon_path
        return get_icon_path("icon.ico")

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
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(root_dir, legal_dir)
        if os.path.exists(path):
            return path

        # Dev mode - current folder
        path = os.path.join(os.getcwd(), legal_dir)
        if os.path.exists(path):
            return path

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

        self.terms_tab = QWidget()
        self.terms_tab.setStyleSheet(f"background-color: {'#2d2d2d' if self.dark_mode else '#ffffff'};")
        terms_layout = QVBoxLayout(self.terms_tab)
        terms_layout.setContentsMargins(15, 12, 15, 15)

        title_color = "#ffffff" if self.dark_mode else "#212529"
        translated_msg = self.translate_text('Conditions d\'utilisation')
        terms_title = QLabel(f"<h2 style='color: {title_color}; margin: 0 0 8px 0;'>{translated_msg}</h2>")
        terms_title.setStyleSheet(f"background-color: transparent; color: {title_color};")
        terms_layout.addWidget(terms_title)

        self.terms_text = QTextBrowser()
        self.terms_text.setReadOnly(True)
        self.terms_text.setOpenExternalLinks(False)
        self.terms_text.setOpenLinks(False)
        self.terms_text.setHtml(self.get_terms_content())
        self.terms_text.setObjectName("TermsTextBrowser")
        self.terms_text.setStyleSheet(_load_qss("terms.qss", "dark" if self.dark_mode else "light"))
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
        self.privacy_text.setObjectName("TermsTextBrowser")
        self.privacy_text.setStyleSheet(_load_qss("terms.qss", "dark" if self.dark_mode else "light"))
        self.privacy_text.document().setDefaultStyleSheet(self.get_html_theme_css())
        privacy_layout.addWidget(self.privacy_text)

        self.tab_widget.addTab(self.terms_tab, self.translate_text("Conditions d'utilisation"))
        self.tab_widget.addTab(self.privacy_tab, self.translate_text("Politique de confidentialité"))

        layout.addWidget(self.tab_widget, 1)

        self.terms_text.anchorClicked.connect(self.handle_terms_link_click)
        self.privacy_text.anchorClicked.connect(self.handle_privacy_link_click)

        contact_group = QGroupBox(self.translate_text("Contact"))
        contact_group.setObjectName("ContactGroup")
        contact_group.setStyleSheet(_load_qss("terms.qss", "dark" if self.dark_mode else "light"))
        contact_layout = QVBoxLayout(contact_group)
        contact_layout.setContentsMargins(12, 8, 12, 8)
        contact_layout.setSpacing(6)

        contact_links_html = self.get_compact_contact_links_html()
        contact_links = QTextBrowser()
        contact_links.setReadOnly(True)
        contact_links.setOpenExternalLinks(True)
        contact_links.setHtml(contact_links_html)
        contact_links.setMaximumHeight(70)
        contact_links.setObjectName("ContactLinks")
        contact_links.setStyleSheet(_load_qss("terms.qss", "dark" if self.dark_mode else "light"))
        contact_links.document().setDefaultStyleSheet(
            _load_qss("contact_links.css", "dark" if self.dark_mode else "light")
        )
        contact_layout.addWidget(contact_links)

        layout.addWidget(contact_group)

        checkbox_layout = QHBoxLayout()
        checkbox_layout.setSpacing(15)

        self.terms_checkbox = AnimatedCheckBox(self.translate_text("J'accepte les conditions d'utilisation"))
        self.terms_checkbox.setObjectName("TermsCheckBox")
        self.terms_checkbox.setStyleSheet(_load_qss("terms.qss", "dark" if self.dark_mode else "light"))

        self.privacy_checkbox = AnimatedCheckBox(self.translate_text("J'accepte la politique de confidentialité"))
        self.privacy_checkbox.setObjectName("TermsCheckBox")
        self.privacy_checkbox.setStyleSheet(_load_qss("terms.qss", "dark" if self.dark_mode else "light"))

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

        _apply_dialog_btn(self.decline_button, "BtnDecline")

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

    def get_html_theme_css(self) -> str:
        """Load HTML theme CSS from styles/themes/dark/ or light/."""
        return _load_qss("terms_html.css", "dark" if self.dark_mode else "light")

    def get_compact_contact_links_html(self):
        """Generate ultra-compact HTML for contact links"""
        if self.language == "fr":
            return """
            <p style="margin:2px 0;font-size:9px;">
                <strong>Développeur :</strong>
                <a href="mailto:prime.enterprises.dev@gmail.com" style="font-weight:500;color:#3498db;">prime.enterprises.dev@gmail.com</a>
            </p>
            <p style="margin:2px 0;font-size:9px;">
                <a href="https://github.com/Hyacinthe-primus" style="margin-right:8px;color:#7c5cbf;">💻 GitHub</a>
                <a href="https://www.instagram.com/___hyacinthe_" style="margin-right:8px;color:#7c5cbf;">📸 Instagram</a>
                <a href="https://www.reddit.com/user/___Hyacinthe_/" style="color:#7c5cbf;">🔴 Reddit</a>
            </p>
            <p style="margin:2px 0;font-size:9px;">
                <a href="mailto:prime.enterprises.dev@gmail.com?subject=Report%20Bug%20from%20File%20Converter%20Pro"
                   style="color:#e74c3c;font-weight:600;">
                   🐛 Signaler un bug
                </a>
            </p>
            """
        else:
            return """
            <p style="margin:2px 0;font-size:9px;">
                <strong>Developer:</strong>
                <a href="mailto:prime.enterprises.dev@gmail.com" style="font-weight:500;color:#3498db;">prime.enterprises.dev@gmail.com</a>
            </p>
            <p style="margin:2px 0;font-size:9px;">
                <a href="https://github.com/Hyacinthe-primus" style="margin-right:8px;color:#7c5cbf;">💻 GitHub</a>
                <a href="https://www.instagram.com/___hyacinthe_" style="margin-right:8px;color:#7c5cbf;">📸 Instagram</a>
                <a href="https://www.reddit.com/user/___Hyacinthe_/" style="color:#7c5cbf;">🔴 Reddit</a>
            </p>
            <p style="margin:2px 0;font-size:9px;">
                <a href="mailto:prime.enterprises.dev@gmail.com?subject=Bug%20Report%20from%20File%20Converter%20Pro"
                style="color:#e74c3c;font-weight:600;">
                🐛 Report a Bug
                </a>
            </p>
            """

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
        Returns the best available language code for a given legal file prefix
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