"""BatchConvertDialog - Batch conversion format/quality selection."""

from PySide6.QtWidgets import QComboBox, QDialog, QDialogButtonBox, QFormLayout

from qss_helpers import _apply_dialog_btn
from utils import make_tm
from utils.translation_mixin import TranslationMixin


class BatchConvertDialog(TranslationMixin, QDialog):
    def __init__(self, parent=None, language="fr"):
        super().__init__(parent)
        self.language = language
        self._tm = make_tm(language)
        self.setWindowTitle(self.translate_text("batch_conversion"))
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout(self)

        self.format_combo = QComboBox()
        self.format_codes = ["pdf", "docx", "png"]
        self.format_combo.addItem(self.translate_text("PDF"), "pdf")
        self.format_combo.addItem(self.translate_text("DOCX"), "docx")
        self.format_combo.addItem(self.translate_text("png_images"), "png")

        self.quality_combo = QComboBox()
        self.quality_combo.addItems(
            [
                self.translate_text("high_quality"),
                self.translate_text("standard_quality_2"),
                self.translate_text("compressed"),
            ]
        )

        layout.addRow(self.translate_text("target_format"), self.format_combo)
        layout.addRow(self.translate_text("quality"), self.quality_combo)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        ok_button = buttons.button(QDialogButtonBox.Ok)
        cancel_button = buttons.button(QDialogButtonBox.Cancel)
        _apply_dialog_btn(ok_button, "BtnOK")
        _apply_dialog_btn(cancel_button, "BtnCancel")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def selected_format(self) -> str:
        """Return a stable format code ('pdf', 'docx' or 'png')."""
        data = self.format_combo.currentData()
        return data if isinstance(data, str) and data in self.format_codes else self.format_codes[0]
