"""PdfToWordDialog — Options for PDF to Word conversion mode selection."""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QGroupBox, QRadioButton,
                               QLabel, QDialogButtonBox, QButtonGroup)
from qss_helpers import _apply_dialog_btn

from utils import make_tm
from utils.translation_mixin import TranslationMixin


class PdfToWordDialog(TranslationMixin, QDialog):
    def __init__(self, parent=None, language="fr", current_mode="with_images", has_images=False):
        super().__init__(parent)
        self.language = language
        self._tm = make_tm(language)
        self.current_mode = current_mode
        self.has_images = has_images
        self.setWindowTitle(self.translate_text("Options de conversion PDF vers Word"))
        self.setModal(True)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        mode_group = QGroupBox(self.translate_text("Mode de conversion"))
        mode_layout = QVBoxLayout(mode_group)

        self.mode_group = QButtonGroup(self)

        self.with_images_radio = QRadioButton(self.translate_text("Conserver les images et la mise en page (recommandé)"))
        self.text_only_radio = QRadioButton(self.translate_text("Texte brut uniquement (plus rapide)"))
        self.text_with_image_text_radio = QRadioButton(self.translate_text("Texte complet (texte + texte des images)"))

        self.mode_group.addButton(self.with_images_radio, 1)
        self.mode_group.addButton(self.text_only_radio, 2)
        self.mode_group.addButton(self.text_with_image_text_radio, 3)

        if self.current_mode == "with_images":
            self.with_images_radio.setChecked(True)
        elif self.current_mode == "text_only":
            self.text_only_radio.setChecked(True)
        else:
            self.text_with_image_text_radio.setChecked(True)

        mode_layout.addWidget(self.with_images_radio)
        mode_layout.addWidget(self.text_only_radio)

        if self.has_images:
            mode_layout.addWidget(self.text_with_image_text_radio)
            self.image_info_label = QLabel(self.translate_text("ℹ️ Ce PDF contient des images. L'option 'Texte complet' extraira le texte des images."))
            self.image_info_label.setStyleSheet("color: #007acc; font-size: 11px; margin-top: 10px;")
            self.image_info_label.setWordWrap(True)
            mode_layout.addWidget(self.image_info_label)
        else:
            self.image_info_label = QLabel(self.translate_text("ℹ️ Ce PDF ne contient pas d'images détectées."))
            self.image_info_label.setStyleSheet("color: #28a745; font-size: 11px; margin-top: 10px;")
            self.image_info_label.setWordWrap(True)
            mode_layout.addWidget(self.image_info_label)

        layout.addWidget(mode_group)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        ok_button = buttons.button(QDialogButtonBox.Ok)
        cancel_button = buttons.button(QDialogButtonBox.Cancel)
        _apply_dialog_btn(ok_button, "BtnOK")
        _apply_dialog_btn(cancel_button, "BtnCancel")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

    def get_conversion_mode(self):
        if self.with_images_radio.isChecked():
            return "with_images"
        elif self.text_only_radio.isChecked():
            return "text_only"
        else:
            return "text_with_image_text"
