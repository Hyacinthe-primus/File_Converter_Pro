"""SplitDialog — PDF splitting options (pages, ranges)."""

from PySide6.QtWidgets import (QDialog, QFormLayout, QComboBox, QSpinBox,
                               QDialogButtonBox)
from qss_helpers import _apply_dialog_btn

from utils import make_tm
from utils.translation_mixin import TranslationMixin


class SplitDialog(TranslationMixin, QDialog):

    def __init__(self, total_pages, parent=None, language="fr"):
        super().__init__(parent)
        self.total_pages = total_pages
        self.language = language
        self._tm = make_tm(language)
        self.setWindowTitle(self.translate_text("Diviser PDF"))
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout(self)

        self.split_method = QComboBox()
        self.split_method.addItems([
            self.translate_text("Par pages"),
            self.translate_text("Toutes les pages"),
            self.translate_text("Plage de pages")
        ])

        self.page_interval = QSpinBox()
        self.page_interval.setMinimum(1)
        self.page_interval.setMaximum(self.total_pages)
        self.page_interval.setValue(1)

        self.start_page = QSpinBox()
        self.start_page.setMinimum(1)
        self.start_page.setMaximum(self.total_pages)
        self.start_page.setValue(1)

        self.end_page = QSpinBox()
        self.end_page.setMinimum(1)
        self.end_page.setMaximum(self.total_pages)
        self.end_page.setValue(self.total_pages)

        layout.addRow(self.translate_text("Méthode de division:"), self.split_method)
        layout.addRow(self.translate_text("Intervalle (pages):"), self.page_interval)
        layout.addRow(self.translate_text("Page de début:"), self.start_page)
        layout.addRow(self.translate_text("Page de fin:"), self.end_page)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        ok_button = buttons.button(QDialogButtonBox.Ok)
        cancel_button = buttons.button(QDialogButtonBox.Cancel)
        _apply_dialog_btn(ok_button, "BtnOK")
        _apply_dialog_btn(cancel_button, "BtnCancel")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addRow(buttons)
