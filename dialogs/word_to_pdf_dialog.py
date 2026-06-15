"""
Provides a modal dialog for configuring Word-to-PDF conversion settings,
including formatting preservation mode, image quality, metadata options,
and a live-updating preview panel that reflects the selected mode.

"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QGroupBox, QButtonGroup, QLabel,
    QFormLayout, QComboBox, QDialogButtonBox, QTextEdit, QSizePolicy
)

from widgets import AnimatedCheckBox
from qss_helpers import _load_qss, _apply_dialog_btn

from utils import make_tm
from utils.translation_mixin import TranslationMixin

_DARK = {
    "preview_bg":    "#0d1117",
    "preview_fg":    "#c9d1d9",
    "sb_bg":         "#161b22",
    "sb_handle":     "#30363d",
    "sb_handle_hv":  "#4dabf7",
    "title_active":  "#4dabf7",
    "title_accent":  "#74c0fc",
    "title_muted":   "#6c757d",
    "bullet_active": "#c9d1d9",
    "bullet_muted":  "#495057",
}

_LIGHT = {
    "preview_bg":    "#f8f9fa",
    "preview_fg":    "#212529",
    "sb_bg":         "#e9ecef",
    "sb_handle":     "#ced4da",
    "sb_handle_hv":  "#4dabf7",
    "title_active":  "#1971c2",
    "title_accent":  "#339af0",
    "title_muted":   "#adb5bd",
    "bullet_active": "#343a40",
    "bullet_muted":  "#ced4da",
}


class WordToPdfOptionsDialog(TranslationMixin, QDialog):
    """
    Modal dialog for Word to PDF conversion settings.

    Args:
        parent:      Parent widget (used to detect dark_mode).
        language:    UI language — "fr" (default) or "en".
        has_content: When True, displays an extra info line indicating the
                     document contains formatted content (images, tables...).
    """

    def __init__(self, parent=None, language: str = "fr", has_content: bool = False):
        super().__init__(parent)

        self.language     = language
        self.has_content  = has_content
        self._tm          = make_tm(language)
        self.is_dark_mode: bool = getattr(parent, "dark_mode", False) if parent else False

        self.setWindowTitle(self.translate_text("Options de conversion Word vers PDF"))
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Build and wire all top-level widgets into the dialog layout."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(14, 14, 14, 14)

        layout.addWidget(self._build_mode_group())
        layout.addWidget(self._build_preview_group(), stretch=1)
        layout.addWidget(self._build_buttons())

        self.preserve_all_radio.toggled.connect(self._on_mode_changed)
        self.text_only_radio.toggled.connect(self._on_mode_changed)

    def _build_mode_group(self) -> QGroupBox:
        """Create the conversion-mode section (radio buttons + advanced sub-group)."""
        group  = QGroupBox(self.translate_text("Mode de conversion"))
        layout = QVBoxLayout(group)
        layout.setSpacing(6)

        self.mode_group = QButtonGroup(self)

        self.preserve_all_radio = AnimatedCheckBox(
            self.translate_text("✅ Conserver toute la mise en forme (recommandé)")
        )
        self.preserve_all_radio.setChecked(True)

        self.text_only_radio = AnimatedCheckBox(
            self.translate_text("📝 Texte seulement (plus rapide)")
        )

        self.mode_group.addButton(self.preserve_all_radio, 1)
        self.mode_group.addButton(self.text_only_radio,    2)

        info_text = self.translate_text("📋 Sélectionnez le mode de conversion :")
        if self.has_content:
            info_text += "\n" + self.translate_text(
                "ℹ️ Ce document contient du contenu formaté, images, tableaux, etc."
            )

        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #007acc; font-size: 12.5px; margin: 4px 0;")

        self.advanced_group = self._build_advanced_group()

        layout.addWidget(info_label)
        layout.addWidget(self.preserve_all_radio)
        layout.addWidget(self.text_only_radio)
        layout.addSpacing(6)
        layout.addWidget(self.advanced_group)

        return group

    def _build_advanced_group(self) -> QGroupBox:
        """Create the collapsible advanced-options QGroupBox (quality, compression, metadata)."""
        group = QGroupBox(self.translate_text("Options avancées"))
        group.setCheckable(True)
        group.setChecked(False)

        group.setStyleSheet(
            _load_qss("advanced_group.qss", "dark" if self.is_dark_mode else "light")
        )

        form = QFormLayout(group)

        self.quality_combo = QComboBox()
        self.quality_combo.addItems([
            self.translate_text("Haute qualité (300 DPI)"),
            self.translate_text("Qualité standard (150 DPI)"),
            self.translate_text("Optimisé (96 DPI)"),
        ])

        self.compress_checkbox = AnimatedCheckBox(self.translate_text("Compresser les images"))
        self.compress_checkbox.setChecked(True)

        self.include_metadata_checkbox = AnimatedCheckBox(self.translate_text("Inclure les métadonnées"))
        self.include_metadata_checkbox.setChecked(True)

        form.addRow(self.translate_text("Qualité d'image:"), self.quality_combo)
        form.addWidget(self.compress_checkbox)
        form.addWidget(self.include_metadata_checkbox)

        return group

    def _build_preview_group(self) -> QGroupBox:
        """Create the preview-differences section with a themed, elastic QTextEdit."""
        group = QGroupBox(self.translate_text("Aperçu des différences"))
        group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(group)
        layout.setContentsMargins(8, 8, 8, 8)

        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.preview_text.setMinimumHeight(90)
        self.preview_text.setStyleSheet(self._build_preview_stylesheet())

        self._update_preview_html()

        layout.addWidget(self.preview_text)
        return group

    def _build_preview_stylesheet(self) -> str:
        """Return the QTextEdit + slim scrollbar stylesheet for the current theme."""
        c = _DARK if self.is_dark_mode else _LIGHT
        return f"""
            QTextEdit {{
                background-color: {c['preview_bg']};
                color: {c['preview_fg']};
                border: none;
                border-radius: 8px;
                padding: 8px;
                font-size: 12px;
            }}
            QScrollBar:vertical {{
                background: {c['sb_bg']}; width: 8px;
                border-radius: 4px; margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {c['sb_handle']};
                border-radius: 4px; min-height: 24px;
            }}
            QScrollBar::handle:vertical:hover  {{ background: {c['sb_handle_hv']}; }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical      {{ height: 0; }}
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical      {{ background: none; }}
            QScrollBar:horizontal {{
                background: {c['sb_bg']}; height: 8px;
                border-radius: 4px; margin: 0;
            }}
            QScrollBar::handle:horizontal {{
                background: {c['sb_handle']};
                border-radius: 4px; min-width: 24px;
            }}
            QScrollBar::handle:horizontal:hover {{ background: {c['sb_handle_hv']}; }}
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal     {{ width: 0; }}
            QScrollBar::add-page:horizontal,
            QScrollBar::sub-page:horizontal     {{ background: none; }}
        """

    def _build_buttons(self) -> QDialogButtonBox:
        """Create and style the OK / Cancel button box."""
        box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        _apply_dialog_btn(box.button(QDialogButtonBox.Ok), "BtnOK")
        _apply_dialog_btn(box.button(QDialogButtonBox.Cancel), "BtnCancelGlassy")

        box.accepted.connect(self.accept)
        box.rejected.connect(self.reject)
        return box

    def _on_mode_changed(self) -> None:
        """Show/hide advanced options and refresh the preview whenever the mode switches."""
        is_preserve = self.preserve_all_radio.isChecked()

        self.advanced_group.setVisible(is_preserve)

        self.preview_text.setMinimumHeight(90 if is_preserve else 110)

        self._update_preview_html()

    def _update_preview_html(self) -> None:
        """Rebuild the preview HTML, visually highlighting the active mode."""
        c           = _DARK if self.is_dark_mode else _LIGHT
        is_preserve = self.preserve_all_radio.isChecked()

        title_keep   = self.translate_text("Mode 'Conserver tout'")
        title_text   = self.translate_text("Mode 'Texte seulement'")

        keep_bullets = [
            self.translate_text("• Garde toutes les images, tableaux, couleurs"),
            self.translate_text("• Conserve la mise en page exacte"),
            self.translate_text("• Maintient les en-têtes et pieds de page"),
        ]
        text_bullets = [
            self.translate_text("• Extrait uniquement le texte"),
            self.translate_text("• Formatage minimal"),
            self.translate_text("• Plus rapide pour les longs documents"),
        ]

        if is_preserve:
            color_keep,  color_text   = c["title_active"], c["title_accent"]
            bullets_keep, bullets_text = c["bullet_active"], c["bullet_active"]
            prefix_text = ""
        else:
            color_keep,  color_text   = c["title_muted"], c["title_active"]
            bullets_keep, bullets_text = c["bullet_muted"], c["bullet_active"]
            prefix_text = "▶ "

        def _section(title: str, color: str, bullets: list, bc: str, bottom_gap: str = "10px") -> str:
            """Helper that renders one labeled bullet section."""
            rows = "".join(
                f'<p style="margin:0 0 2px 0; color:{bc};">{b}</p>'
                for b in bullets
            )
            return (
                f'<p style="margin:0 0 6px 0; color:{color}; font-weight:bold;">{title}</p>'
                f'{rows}'
                f'<p style="margin:0 0 {bottom_gap} 0;"></p>'
            )

        html = (
            _section(title_keep, color_keep, keep_bullets, bullets_keep)
            + _section(prefix_text + title_text, color_text, text_bullets, bullets_text, bottom_gap="0")
        )

        self.preview_text.setHtml(html)

    def get_conversion_mode(self) -> dict:
        """
        Return the user's selected conversion settings.

        Returns:
            dict with keys:
                mode (str):              "preserve_all" | "text_only"
                quality (str):           currently selected quality label
                compress_images (bool):  whether image compression is enabled
                include_metadata (bool): whether metadata inclusion is enabled
        """
        return {
            "mode":             "preserve_all" if self.preserve_all_radio.isChecked() else "text_only",
            "quality":          self.quality_combo.currentText(),
            "compress_images":  self.compress_checkbox.isChecked(),
            "include_metadata": self.include_metadata_checkbox.isChecked(),
        }