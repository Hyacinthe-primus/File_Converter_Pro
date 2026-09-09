"""PdfToWordDialog - Options for PDF to Word conversion mode selection."""

from PySide6.QtWidgets import QButtonGroup, QDialog, QDialogButtonBox, QGroupBox, QRadioButton, QVBoxLayout

from qss_helpers import _apply_dialog_btn
from utils import make_tm
from utils.translation_mixin import TranslationMixin


class PdfToWordDialog(TranslationMixin, QDialog):
    def __init__(self, parent=None, language="fr", current_mode="with_images"):
        super().__init__(parent)
        self.language = language
        self._tm = make_tm(language)
        self.current_mode = current_mode
        self.setWindowTitle(self.translate_text("Options de conversion PDF vers Word"))
        self.setModal(True)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        mode_group = QGroupBox(self.translate_text("Mode de conversion"))
        mode_layout = QVBoxLayout(mode_group)

        self.mode_group = QButtonGroup(self)

        self.with_images_radio = QRadioButton(
            self.translate_text("Conserver les images et la mise en page (recommandé)")
        )
        self.text_only_radio = QRadioButton(self.translate_text("Texte brut uniquement (plus rapide)"))

        self.mode_group.addButton(self.with_images_radio, 1)
        self.mode_group.addButton(self.text_only_radio, 2)

        if self.current_mode == "text_only":
            self.text_only_radio.setChecked(True)
        else:
            self.with_images_radio.setChecked(True)

        mode_layout.addWidget(self.with_images_radio)
        mode_layout.addWidget(self.text_only_radio)

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
        return "text_only"
