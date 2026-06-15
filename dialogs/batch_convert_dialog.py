"""BatchConvertDialog — Batch conversion format/quality selection."""

from PySide6.QtWidgets import QDialog, QFormLayout, QComboBox, QDialogButtonBox
from qss_helpers import _apply_dialog_btn

from utils import make_tm
from utils.translation_mixin import TranslationMixin


class BatchConvertDialog(TranslationMixin, QDialog):
    def __init__(self, parent=None, language="fr"):
        super().__init__(parent)
        self.language = language
        self._tm = make_tm(language)
        self.setWindowTitle(self.translate_text("Conversion par Lot"))
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout(self)

        self.format_combo = QComboBox()
        self.format_combo.addItems([
            self.translate_text("PDF"),
            self.translate_text("DOCX"),
            self.translate_text("Images PNG")
        ])

        self.quality_combo = QComboBox()
        self.quality_combo.addItems([
            self.translate_text("Haute qualité"),
            self.translate_text("Qualité standard"),
            self.translate_text("Compressé")
        ])

        layout.addRow(self.translate_text("Format cible:"), self.format_combo)
        layout.addRow(self.translate_text("Qualité:"), self.quality_combo)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        ok_button = buttons.button(QDialogButtonBox.Ok)
        cancel_button = buttons.button(QDialogButtonBox.Cancel)
        _apply_dialog_btn(ok_button, "BtnOK")
        _apply_dialog_btn(cancel_button, "BtnCancel")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
